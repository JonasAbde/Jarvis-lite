import pyaudio
import numpy as np
import threading
import queue
import logging
from danspeech import DanSpeechPrimary
from danspeech.audio import Recognizer

logger = logging.getLogger(__name__)

class DanSpeechVoice:
    """
    Voice system using DanSpeech for speech recognition.
    Sends recognized commands to a queue.
    """
    
    def __init__(self):
        """Initialize DanSpeech voice system"""
        logger.info("Initializing DanSpeech model...")
        try:
            self.model = DanSpeechPrimary()
            self.recognizer = Recognizer(model=self.model)
            
            # Audio settings
            self.sample_rate = 16000
            self.channels = 1
            self.chunk_size = 1024 # PA frames per buffer
            self.format = pyaudio.paInt16
            self.audio_queue = queue.Queue()
            self.command_queue = queue.Queue() # <<< TILFØJET KOMMANDO KØ
            self.is_listening = False
            self.recording_thread = None
            self.processing_thread = None
            
            # Initialize PyAudio
            self.p = pyaudio.PyAudio()
            
            logger.info("DanSpeech model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DanSpeech: {e}")
            raise

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio input"""
        if self.is_listening: # Kun tilføj til kø hvis vi lytter
            if status:
                logger.warning(f"Audio input status: {status}")
            # Konverter bytes til numpy array og normaliser
            audio_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
            self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)

    def process_audio(self):
        """Process audio data from queue"""
        logger.debug("Audio processing thread started.")
        accumulated_audio = []
        target_duration = 1.0 # Sekunder af lyd at behandle ad gangen
        target_frames = int(target_duration * self.sample_rate)
        
        while self.is_listening:
            try:
                # Hent lyd fra køen
                audio_chunk = self.audio_queue.get(timeout=0.5) # Vent max 0.5 sek
                if audio_chunk is None: # Stop signal
                    break 
                accumulated_audio.append(audio_chunk)
                
                # Tjek om vi har nok lyd
                current_frames = sum(len(chunk) for chunk in accumulated_audio)
                if current_frames >= target_frames:
                    audio_array = np.concatenate(accumulated_audio)
                    accumulated_audio = [] # Nulstil akkumulator
                    
                    # Perform speech recognition
                    try:
                        logger.debug(f"Processing {len(audio_array)/self.sample_rate:.2f}s of audio for recognition.")
                        text = self.recognizer.recognize(audio_array)
                        if text:
                            logger.info(f"Recognized: '{text}' - Putting in command queue.")
                            self.command_queue.put(text) # <<< LÆG I KOMMANDO KØ
                    except Exception as e:
                        # Undgå at spamme loggen ved stilhed eller korte lyde
                        if "Input tensor size" not in str(e) and "too short" not in str(e):
                             logger.error(f"Recognition error: {e}")
                        
            except queue.Empty:
                # Ingen lyd i køen, fortsæt loopet
                continue
            except Exception as e:
                logger.error(f"Processing thread error: {e}")
        logger.debug("Audio processing thread finished.")

    def start_listening(self):
        """Start listening for speech"""
        if not self.is_listening:
            logger.info("Attempting to start listening...")
            # Ryd gamle kommandoer før start
            while not self.command_queue.empty():
                try: self.command_queue.get_nowait() 
                except queue.Empty: break
            while not self.audio_queue.empty():
                try: self.audio_queue.get_nowait() 
                except queue.Empty: break
                
            self.is_listening = True
            try:
                self.stream = self.p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self.audio_callback
                )
                # Trådene bør startes *før* streamen for at være klar til data
                self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
                self.processing_thread.start()
                self.stream.start_stream() # Start streamen efter tråden er startet
                logger.info("Listening started successfully.")
            except Exception as e:
                logger.error(f"Error starting audio stream: {e}")
                self.is_listening = False # Sæt tilbage hvis fejl
                # Ryd op hvis stream blev oprettet men fejlede at starte
                if hasattr(self, 'stream') and self.stream:
                    if self.stream.is_active(): self.stream.stop_stream()
                    if not self.stream.is_stopped(): self.stream.close()
                # Sørg for at processeringstråd også stoppes
                if self.processing_thread and self.processing_thread.is_alive():
                    try: self.audio_queue.put(None, timeout=0.1) # Signal til at stoppe
                    except queue.Full: pass
                    self.processing_thread.join(timeout=1.0)
                raise # Re-raise fejlen så app.py kan fange den

    def stop_listening(self):
        """Stop listening for speech"""
        if self.is_listening:
            logger.info("Attempting to stop listening...")
            self.is_listening = False # Sæt flaget FØRST
            
            # Stop streamen
            if hasattr(self, 'stream') and self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    if not self.stream.is_stopped():
                        self.stream.close()
                    logger.debug("Audio stream stopped and closed.")
                except Exception as e:
                    logger.error(f"Error stopping/closing stream: {e}")
            
            # Signal processing thread to stop by putting None in the *audio* queue
            try: 
                logger.debug("Putting None in audio queue to signal processing thread stop.")
                self.audio_queue.put(None, timeout=0.5) 
            except queue.Full:
                logger.warning("Audio queue full, could not signal processing thread immediately.")
                pass
                
            # Vent på at processeringstråden stopper
            if self.processing_thread and self.processing_thread.is_alive():
                logger.debug("Waiting for processing thread to join...")
                self.processing_thread.join(timeout=2.0)
                if self.processing_thread.is_alive():
                    logger.warning("Processing thread did not join cleanly.")
                else:
                    logger.debug("Processing thread joined successfully.")
            
            logger.info("Listening stopped.")

    def __del__(self):
        """Cleanup when object is destroyed"""
        logger.debug("DanSpeechVoice __del__ called.")
        if self.is_listening:
            self.stop_listening()
        if hasattr(self, 'p'):
            self.p.terminate()
            logger.debug("PyAudio terminated.")

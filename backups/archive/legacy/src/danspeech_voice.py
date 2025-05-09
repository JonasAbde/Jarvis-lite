import pyaudio
import numpy as np
import torch
from danspeech import Recognizer
from danspeech.pretrained_models import DanSpeechPrimary
import queue
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DanSpeechVoice:
    """
    Voice system using DanSpeech for speech recognition.
    """
    
    def __init__(self):
        """Initialize DanSpeech voice system"""
        # Initialize DanSpeech model
        logger.info("Initializing DanSpeech model...")
        try:
            self.model = DanSpeechPrimary()
            self.recognizer = Recognizer(model=self.model)
            
            # Audio settings
            self.sample_rate = 16000
            self.channels = 1
            self.chunk_size = 1024
            self.format = pyaudio.paInt16
            self.audio_queue = queue.Queue()
            self.is_listening = False
            self.recording_thread = None
            self.processing_thread = None
            self.last_recognized_text = ""
            
            # Initialize PyAudio
            self.p = pyaudio.PyAudio()
            
            logger.info("DanSpeech model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DanSpeech: {e}")
            raise

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio input"""
        if status:
            logger.warning(f"Audio input status: {status}")
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        # Normalize to float32
        audio_data = audio_data.astype(np.float32) / 32768.0
        self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)

    def process_audio(self):
        """Process audio data from queue"""
        while self.is_listening:
            try:
                # Collect 1 second of audio
                audio_data = []
                for _ in range(int(self.sample_rate / self.chunk_size)):
                    audio_data.append(self.audio_queue.get(timeout=1.0))
                
                if audio_data:
                    # Convert to numpy array
                    audio_array = np.concatenate(audio_data)
                    
                    # Perform speech recognition
                    try:
                        text = self.recognizer.recognize(audio_array)
                        if text:
                            self.last_recognized_text = text
                            logger.info(f"Recognized: {text}")
                    except Exception as e:
                        logger.error(f"Recognition error: {e}")
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")

    def start_listening(self):
        """Start listening for speech"""
        if not self.is_listening:
            self.is_listening = True
            
            # Start audio recording thread
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self.audio_callback
            )
            self.stream.start_stream()
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.start()
            
            logger.info("Started listening...")

    def stop_listening(self):
        """Stop listening for speech"""
        if self.is_listening:
            self.is_listening = False
            
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            
            if self.processing_thread:
                self.processing_thread.join()
            
            logger.info("Stopped listening...")

    def get_last_recognized_text(self) -> str:
        """Get the last recognized text"""
        return self.last_recognized_text

    def clear_last_recognized_text(self):
        """Clear the last recognized text"""
        self.last_recognized_text = ""

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'p'):
            self.p.terminate() 
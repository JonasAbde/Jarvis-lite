"""
Wakeword-detektion for Jarvis Lite.
Lytter efter nøgleordet "Jarvis" for at aktivere assistenten.
"""

import os
import time
import wave
import logging
import asyncio
import pyaudio
import tempfile
import numpy as np
from typing import Optional, Tuple, Callable, List

# Logger
logger = logging.getLogger(__name__)

# Konfiguration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAKEWORD = "jarvis"
ACTIVATION_THRESHOLD = 0.6  # Konfidenstærskel for aktivering
HISTORY_SECONDS = 2  # Sekunder af lydhistorik at beholde

class WakewordDetector:
    """
    Klasse til detektering af wakeword "Jarvis" i lydstrøm
    """
    
    def __init__(self, activation_callback: Optional[Callable] = None):
        """
        Initialiserer wakeword detektoren
        
        Args:
            activation_callback: Callback-funktion der kaldes ved aktivering
        """
        self.activation_callback = activation_callback
        self.listening = False
        self.p = None
        self.stream = None
        self.is_activated = False
        self.audio_buffer = []  # Buffer til lydhistorik
        self.buffer_frames = int(HISTORY_SECONDS * RATE / CHUNK)  # Antal frames der skal gemmes
        self._load_whisper_model()
    
    def _load_whisper_model(self) -> None:
        """Indlæser Whisper-modellen til STT"""
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Whisper model indlæst for wakeword-detektion")
        except Exception as e:
            logger.error(f"Kunne ikke indlæse Whisper model: {e}")
            self.model = None
    
    def start(self) -> None:
        """Starter lytning efter wakeword"""
        if self.listening:
            return
        
        self.listening = True
        self.is_activated = False
        self.audio_buffer = []
        
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=self._audio_callback
            )
            logger.info("Wakeword detektion startet - lytter efter 'Jarvis'")
        except Exception as e:
            logger.error(f"Fejl ved start af wakeword detektion: {e}")
            self.listening = False
    
    def stop(self) -> None:
        """Stopper lytning efter wakeword"""
        self.listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.p:
            self.p.terminate()
            
        self.stream = None
        self.p = None
        logger.info("Wakeword detektion stoppet")
    
    def _audio_callback(self, in_data, frame_count, time_info, status) -> Tuple[bytes, int]:
        """
        Callback for lydstrøm
        
        Args:
            in_data: Lyddata
            frame_count: Antal frames
            time_info: Timing information
            status: Statusflag
            
        Returns:
            Tuple af (data, flag) for at fortsætte strømmen
        """
        if not self.listening:
            return (in_data, pyaudio.paComplete)
        
        # Tilføj den nye lyd til bufferen
        self.audio_buffer.append(in_data)
        
        # Begræns buffer-størrelsen
        if len(self.audio_buffer) > self.buffer_frames:
            self.audio_buffer.pop(0)
        
        # Tjek med jævne mellemrum for wakeword
        if len(self.audio_buffer) >= self.buffer_frames / 2:
            # Processer ikke hver gang for at spare CPU
            if not self.is_activated and np.random.random() < 0.2:  # 20% sandsynlighed
                asyncio.create_task(self._process_buffer())
        
        return (in_data, pyaudio.paContinue)
    
    async def _process_buffer(self) -> None:
        """
        Processer lydbufferen for at detektere wakeword
        """
        if not self.model or self.is_activated:
            return
        
        try:
            # Gem bufferen til en midlertidig fil
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            wf = wave.open(temp_filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.audio_buffer))
            wf.close()
            
            # Transcriber lyden
            audio, _ = self._load_audio(temp_filename)
            
            if audio is not None:
                # Transskriber med optimerede parametre for wakeword
                segments, _ = self.model.transcribe(
                    audio,
                    language="da",
                    beam_size=1,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=300,
                        speech_pad_ms=100
                    )
                )
                
                # Saml tekst
                transcription = " ".join([segment.text for segment in segments]).lower()
                
                # Tjek om wakeword findes i transskriptionen
                if WAKEWORD in transcription:
                    confidence = max(segment.avg_logprob for segment in segments) if segments else 0
                    # Konverter logprob til approksimeret konfidens mellem 0-1
                    confidence = 1.0 - (abs(confidence) / 10.0) if confidence < 0 else 0.9
                    
                    logger.info(f"Wakeword detekteret: '{transcription}' med konfidens {confidence:.2f}")
                    
                    # Aktiver hvis over tærskel
                    if confidence > ACTIVATION_THRESHOLD:
                        self.is_activated = True
                        logger.info("Jarvis aktiveret!")
                        
                        # Kald callback hvis defineret
                        if self.activation_callback:
                            asyncio.create_task(self._call_callback())
            
            # Ryd op efter midlertidig fil
            os.unlink(temp_filename)
            
        except Exception as e:
            logger.error(f"Fejl under wakeword-detektion: {e}")
    
    async def _call_callback(self) -> None:
        """Kalder activation callback og nulstiller aktivering"""
        try:
            if self.activation_callback:
                await self.activation_callback()
        except Exception as e:
            logger.error(f"Fejl i activation_callback: {e}")
        finally:
            # Nulstil aktivering efter et stykke tid
            await asyncio.sleep(5)
            self.is_activated = False
    
    def _load_audio(self, file_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Indlæser lydfil til numpy array
        
        Args:
            file_path: Sti til lydfilen
            
        Returns:
            Tuple af (lydarray, samplerate) eller (None, None) ved fejl
        """
        try:
            import soundfile as sf
            audio, sr = sf.read(file_path)
            
            # Konverter til float32 format
            audio = audio.astype(np.float32)
            
            # Normaliser lyddata
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))
            
            return audio, sr
        except Exception as e:
            logger.error(f"Fejl ved indlæsning af lydfil: {e}")
            return None, None

# Globalt objekt for nem import
detector = None

async def initialize_wakeword_detector(callback: Optional[Callable] = None) -> WakewordDetector:
    """
    Initialiserer og starter wakeword detektoren
    
    Args:
        callback: Funktion der kaldes når wakeword detekteres
        
    Returns:
        WakewordDetector objekt
    """
    global detector
    
    if detector is None:
        detector = WakewordDetector(callback)
    else:
        detector.activation_callback = callback
    
    detector.start()
    return detector

async def stop_wakeword_detector() -> None:
    """Stopper wakeword detektoren"""
    global detector
    
    if detector:
        detector.stop()
        detector = None
        logger.info("Wakeword detektor lukket ned") 
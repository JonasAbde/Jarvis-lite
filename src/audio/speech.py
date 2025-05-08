"""
Tale-til-tekst og tekst-til-tale funktioner for Jarvis Lite.
"""

import os
import wave
import hashlib
import pyaudio
import logging
import numpy as np
from gtts import gTTS
import playsound
import soundfile as sf
import asyncio
import tempfile
from typing import Optional, Tuple

# Konfiguration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
TEMP_WAV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_recording.wav")
TTS_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "tts")

# Logger
logger = logging.getLogger(__name__)

def load_whisper_model():
    """Indlæser Whisper-modellen til STT"""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper model indlæst (tiny version)")
        return model
    except Exception as e:
        logger.error(f"Kunne ikke indlæse Whisper model: {e}")
        return None

def transcribe_audio(file_path: str) -> Optional[str]:
    """
    Konverterer lydfil til tekst med Whisper
    
    Args:
        file_path: Sti til lydfilen
        
    Returns:
        Transkriberet tekst eller None ved fejl
    """
    model = load_whisper_model()
    if not model:
        return None
        
    try:
        # Indlæs lydfilen
        audio, _ = sf.read(file_path)
        
        # Konverter til float32 format
        audio = audio.astype(np.float32)
        
        # Normaliser lyddata
        audio = audio / np.max(np.abs(audio))
        
        logger.info(f"Lydfil indlæst: {len(audio)} samples")
        
        # Transskriber med optimerede parametre
        segments, _ = model.transcribe(
            audio,
            language="da",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=1000,
                speech_pad_ms=200
            )
        )
        
        # Saml tekst
        transcription = " ".join([segment.text for segment in segments])
        if transcription.strip():
            logger.info(f"Transskriberet tekst: {transcription}")
            return transcription.strip()
        else:
            logger.info("Ingen tekst transskriberet")
        return None

    except Exception as e:
        logger.error(f"Fejl under transskription: {e}")
        return None

def record_audio() -> Optional[str]:
    """
    Optager lyd fra mikrofonen og gemmer som wav-fil
    
    Returns:
        Sti til den gemte lydfil eller None ved fejl
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    logger.info("Optager lyd...")
    print("🎤 Lytter...")  # Visuel indikation for brugeren
    
    frames = []
    
    # Forbedret støjdetektering
    noise_samples = []
    for _ in range(5):
        data = stream.read(CHUNK)
        audio_data = np.frombuffer(data, dtype=np.int16)
        noise_samples.append(np.abs(audio_data).mean())
    noise_baseline = np.mean(noise_samples)
    silence_threshold = max(100, noise_baseline * 1.2)
    
    logger.info(f"Støj baseline: {noise_baseline}, tærskel: {silence_threshold}")
    
    silence_chunks = 0
    max_silence_chunks = int(1 * RATE / CHUNK)  # 1 sekund
    max_recording_chunks = int(5 * RATE / CHUNK)  # 5 sekunder
    chunk_count = 0
    listening = True
    has_sound = False
    sound_chunks = 0
    
    try:
        while listening:
            data = stream.read(CHUNK)
            frames.append(data)
            chunk_count += 1
            
            # Tjek lydstyrke
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.abs(audio_data).mean()
            
            if amplitude > silence_threshold:
                has_sound = True
                sound_chunks += 1
                silence_chunks = 0
            else:
                silence_chunks += 1
                if silence_chunks > max_silence_chunks and has_sound and sound_chunks > 1:
                    listening = False
                    logger.info("Stilhed detekteret, stopper optagelse")
            
            if chunk_count > max_recording_chunks:
                listening = False
                logger.info("Maksimal optagelsestid nået")
                
    except Exception as e:
        logger.error(f"Fejl under optagelse: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        if frames and has_sound and sound_chunks > 1:
            wf = wave.open(TEMP_WAV, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            logger.info(f"Lyd gemt til {TEMP_WAV}")
            return TEMP_WAV
        else:
            logger.info("Ingen lyd detekteret eller for kort lyd")
            return None

def danish_text_cleanup(text: str) -> str:
    """
    Renser og forbereder dansk tekst for tekst-til-tale
    
    Args:
        text: Input tekst
        
    Returns:
        Renset tekst optimeret for dansk TTS
    """
    # Erstat specifikke ord/forkortelser for bedre udtale
    replacements = {
        "f.eks.": "for eksempel",
        "bl.a.": "blandt andet",
        "osv.": "og så videre",
        "dvs.": "det vil sige",
        "etc.": "etcetera",
        "ca.": "cirka",
        "tlf.": "telefon",
        "nr.": "nummer",
        "kl.": "klokken",
    }
    
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    
    # Indsæt pauser ved kommaer og punktummer for mere naturlig tale
    text = text.replace(",", ", ")
    text = text.replace(".", ". ")
    
    # Fjern dobbelt-mellemrum
    while "  " in text:
        text = text.replace("  ", " ")
    
    return text

def speak(text: str, lang: str = 'da') -> None:
    """
    Konverterer tekst til tale og afspiller det med tydelig dansk udtale
    
    Args:
        text: Teksten der skal omdannes til tale
        lang: Sproget (default: 'da' for dansk)
    """
    try:
        # Forbered teksten til bedre TTS
        text = danish_text_cleanup(text)
        
        # Print output til konsollen (synlig feedback)
        print(f"🔊 Jarvis: {text}")
        
        # Tjek cache først
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        os.makedirs(TTS_CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")
        
        # Hvis allerede i cache, brug den
        if os.path.exists(cache_path):
            logger.info(f"Bruger cached TTS for: {text[:50]}...")
            playsound.playsound(cache_path, block=False)
            return
        
        # Generer ny TTS
        logger.info(f"Genererer ny TTS for: {text[:50]}...")
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Brug midlertidigt filnavn
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Gem til temp fil og flyt for at undgå race-conditions
        tts.save(temp_filename)
        os.replace(temp_filename, cache_path)
        
        # Afspil
        playsound.playsound(cache_path, block=False)
            
    except Exception as e:
        logger.error(f"TTS fejl: {e}")
        print(f"Fejl ved afspilning af tale: {e}")

# Async-versioner af funktionerne til brug med asyncio
async def transcribe_audio_async(file_path: str) -> Optional[str]:
    """Asynkron wrapper for transcribe_audio"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: transcribe_audio(file_path))

async def record_audio_async() -> Optional[str]:
    """Asynkron wrapper for record_audio"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, record_audio)

async def speak_async(text: str, lang: str = 'da') -> None:
    """Asynkron wrapper for speak"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: speak(text, lang)) 
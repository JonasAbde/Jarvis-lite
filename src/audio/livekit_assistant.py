"""
LiveKit-baseret voice assistant integration for Jarvis-lite.
"""

from dotenv import load_dotenv
import logging
import os
from pathlib import Path
from faster_whisper import WhisperModel
from gtts import gTTS
import torch
from transformers.models.auto.modeling_auto import AutoModelForCausalLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
import pyaudio
import wave
import keyboard
import threading
import time
import pygame
from tempfile import NamedTemporaryFile
import sounddevice as sd
import soundfile as sf
import numpy as np

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Indlæs miljøvariabler
load_dotenv()

class AudioRecorder:
    """Klasse til at håndtere lydoptagelse"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        
        # Lydindstillinger
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        
    def start_recording(self):
        """Start lydoptagelse"""
        self.frames = []
        self.is_recording = True
        
        # Vent lidt før optagelse starter
        time.sleep(0.1)
        
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        logger.info("Optager... Tryk MELLEMRUM for at stoppe.")
        
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                logger.error(f"Fejl under optagelse: {e}")
                break
        
    def stop_recording(self) -> str:
        """Stop lydoptagelse og gem filen"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        # Gem lydfil
        temp_file = NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            
        return temp_file.name
        
    def __del__(self):
        self.audio.terminate()

class AudioPlayer:
    """Klasse til at afspille lyd"""
    
    def __init__(self):
        pygame.mixer.init()
        
    def play(self, audio_file: str):
        """Afspil lydfil"""
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

class JarvisAssistant:
    """Jarvis assistent implementering"""
    
    def __init__(self) -> None:
        # Initialiser STT model (Faster Whisper)
        logger.info("Indlæser Whisper model...")
        self.stt_model = WhisperModel(
            model_size_or_path="small",
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16" if torch.cuda.is_available() else "int8"
        )
        
        # Initialiser LLM (DeepSeek-R1)
        logger.info("Indlæser DeepSeek-R1 model...")
        model_path = "deepseek-ai/deepseek-coder-1.3b-instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        
        # Lyd håndtering
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        
        # Cache mappe til TTS
        self.cache_dir = Path("cache/tts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Lydindstillinger
        self.sample_rate = 16000
        self.channels = 1
        
    def record_audio(self) -> str:
        """Optag lyd fra mikrofon"""
        logger.info("Optager... Tryk MELLEMRUM for at stoppe.")
        
        # Start optagelse
        recording = sd.rec(
            int(30 * self.sample_rate),  # Max 30 sekunder
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16
        )
        
        # Vent på at brugeren slipper MELLEMRUM
        while keyboard.is_pressed('space'):
            time.sleep(0.1)
        
        # Stop optagelse
        sd.stop()
        
        # Gem lydfil
        temp_file = NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(temp_file.name, recording[:sd.get_stream().active], self.sample_rate)
        
        return temp_file.name
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Konverter tale til tekst"""
        segments, _ = self.stt_model.transcribe(
            audio_path,
            language="da",
            beam_size=5
        )
        return " ".join([seg.text for seg in segments])
    
    def generate_response(self, text: str) -> str:
        """Generer svar med LLM"""
        if not text.strip():
            return "Jeg kunne ikke høre hvad du sagde. Kan du gentage det?"
            
        # Lav prompt template
        prompt = f"""Du er Jarvis, en dansk AI assistent. Du er hjælpsom, venlig og svarer altid på dansk med komplette sætninger.

Instruktioner:
1. Svar altid på dansk
2. Vær hjælpsom og venlig
3. Brug komplette sætninger
4. Hold svarene korte og præcise

Bruger: {text}

Jarvis: Lad mig hjælpe dig. """
        
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
            
        outputs = self.llm_model.generate(
            **inputs,
            max_length=200,
            min_length=20,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            top_k=50,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("Jarvis: Lad mig hjælpe dig. ")[-1].strip()
        
        if not response or len(response) < 10:
            return "Undskyld, jeg forstod ikke helt dit spørgsmål. Kan du omformulere det?"
            
        return response
    
    def speak_response(self, text: str) -> None:
        """Konverter tekst til tale og afspil"""
        if not text.strip():
            text = "Undskyld, jeg ved ikke hvad jeg skal svare. Kan du omformulere dit spørgsmål?"
            
        # Generer unik filsti i cache
        output_path = self.cache_dir / f"response_{hash(text)}.mp3"
        
        # Hvis ikke i cache, generer ny lydfil
        if not output_path.exists():
            tts = gTTS(text=text, lang="da")
            tts.save(str(output_path))
        
        # Afspil svar
        pygame.mixer.music.load(str(output_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    def run(self):
        """Kør assistenten"""
        logger.info("Jarvis er klar! Tryk MELLEMRUM for at tale, Q for at afslutte.")
        
        while True:
            try:
                # Vent på bruger input
                if keyboard.is_pressed('q'):
                    logger.info("Afslutter Jarvis...")
                    break
                    
                if keyboard.is_pressed('space'):
                    # Optag lyd
                    audio_path = self.record_audio()
                    
                    try:
                        # Konverter tale til tekst
                        text = self.transcribe_audio(audio_path)
                        logger.info(f"Du sagde: {text}")
                        
                        # Generer svar
                        response = self.generate_response(text)
                        logger.info(f"Jarvis svarer: {response}")
                        
                        # Afspil svar
                        self.speak_response(response)
                        
                    finally:
                        # Ryd op
                        if os.path.exists(audio_path):
                            os.unlink(audio_path)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Fejl i samtale loop: {e}")
                continue

def main():
    """Hovedfunktion til at køre assistenten"""
    assistant = JarvisAssistant()
    logger.info("Jarvis assistent er klar!")
    
    # Kør samtale loop direkte (ikke async)
    assistant.run()

if __name__ == "__main__":
    main() 
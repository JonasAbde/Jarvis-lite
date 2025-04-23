import pyttsx3
import logging
import json
import os
import asyncio
from typing import Optional, Dict, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisVoice:
    """
    Enhanced voice system for Jarvis with improved Danish support and async capabilities.
    """
    
    def __init__(self, preferred_voice: str = None, rate: int = 150, volume: float = 1.0):
        """
        Initialize the voice system.
        
        Args:
            preferred_voice (str, optional): Preferred voice name or language
            rate (int): Speech rate (default: 150)
            volume (float): Volume level between 0 and 1 (default: 1.0)
        """
        self.engine = None
        self.current_voice = None
        self.rate = rate
        self.volume = volume
        self.speaking = False
        self._load_config()
        self.init_engine(preferred_voice)
        
    def _load_config(self) -> None:
        """Load voice configuration from file if it exists."""
        config_path = Path("config/voice_config.json")
        self.danish_replacements = {
            'æ': 'ae',
            'ø': 'oe',
            'å': 'aa',
            'Æ': 'AE',
            'Ø': 'OE',
            'Å': 'AA',
            # Add more specific Danish word replacements
            'jeg': 'yai',
            'det': 'dat',
            'er': 'air'
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.danish_replacements.update(config.get('danish_replacements', {}))
            except Exception as e:
                logger.error(f"Error loading voice config: {e}")

    def init_engine(self, preferred_voice: Optional[str] = None) -> None:
        """
        Initialize the text-to-speech engine with error handling.
        
        Args:
            preferred_voice (str, optional): Preferred voice name or language
        """
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            voices = self.engine.getProperty('voices')
            logger.info(f"Found {len(voices)} voices:")
            for voice in voices:
                logger.info(f"Voice: {voice.name}")
                logger.info(f"  ID: {voice.id}")
                logger.info(f"  Languages: {voice.languages}")
            
            # Try to find Microsoft Helle specifically
            helle_id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_DA-DK_HELLE_11.0"
            selected_voice = None
            
            # First try to find Helle
            for voice in voices:
                if "helle" in voice.name.lower() or voice.id == helle_id:
                    selected_voice = voice
                    logger.info("Found Microsoft Helle voice")
                    break
            
            # If Helle wasn't found but a preferred voice was specified
            if not selected_voice and preferred_voice:
                logger.info(f"Searching for preferred voice: {preferred_voice}")
                for voice in voices:
                    # Check both name and ID for language indicators
                    voice_info = (voice.name + " " + voice.id).lower()
                    if any(lang in voice_info for lang in ['danish', 'dansk', 'da-dk', 'da_dk']):
                        selected_voice = voice
                        logger.info(f"Found Danish voice: {voice.name}")
                        break
                    elif preferred_voice.lower() in voice_info:
                        selected_voice = voice
                        logger.info(f"Found preferred voice: {voice.name}")
                        break
            
            if not selected_voice and voices:
                selected_voice = voices[0]
                logger.warning(f"No Danish voice found, using default: {selected_voice.name}")
                
            if selected_voice:
                self.engine.setProperty('voice', selected_voice.id)
                self.current_voice = selected_voice
                logger.info(f"Initialized voice: {selected_voice.name}")
            else:
                logger.error("No voices available at all!")
                
        except Exception as e:
            logger.error(f"Error initializing voice engine: {e}")
            raise

    async def speak_async(self, text: str, voice: str = None) -> None:
        """
        Speak text asynchronously.
        
        Args:
            text (str): Text to speak
            voice (str, optional): Specific voice to use
        """
        if voice:
            self.init_engine(voice)
            
        text = self._improve_danish_pronunciation(text)
        
        def speak_text():
            self.speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.speaking = False
            
        await asyncio.get_event_loop().run_in_executor(None, speak_text)

    def speak(self, text: str, voice: str = None) -> None:
        """
        Speak text synchronously.
        
        Args:
            text (str): Text to speak
            voice (str, optional): Specific voice to use
        """
        if voice:
            self.init_engine(voice)
            
        text = self._improve_danish_pronunciation(text)
        
        try:
            self.speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during speech: {e}")
        finally:
            self.speaking = False

    def _improve_danish_pronunciation(self, text: str) -> str:
        """
        Improve Danish pronunciation using replacement rules.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with improved pronunciation
        """
        for danish, phonetic in self.danish_replacements.items():
            text = text.replace(danish, phonetic)
        return text

    def stop(self) -> None:
        """Stop current speech."""
        try:
            self.engine.stop()
            self.speaking = False
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")

    def list_voices(self) -> List[Dict]:
        """
        Get list of available voices with details.
        
        Returns:
            List[Dict]: List of voice information dictionaries
        """
        voices = []
        try:
            for voice in self.engine.getProperty('voices'):
                voices.append({
                    'name': voice.name,
                    'id': voice.id,
                    'languages': voice.languages,
                    'gender': voice.gender,
                    'age': voice.age
                })
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
        return voices

    def set_voice_properties(self, rate: Optional[int] = None, 
                           volume: Optional[float] = None) -> None:
        """
        Set voice properties with validation.
        
        Args:
            rate (int, optional): Speech rate (0-400)
            volume (float, optional): Volume level (0-1)
        """
        try:
            if rate is not None:
                if 0 <= rate <= 400:
                    self.rate = rate
                    self.engine.setProperty('rate', rate)
                else:
                    raise ValueError("Rate must be between 0 and 400")
                    
            if volume is not None:
                if 0 <= volume <= 1:
                    self.volume = volume
                    self.engine.setProperty('volume', volume)
                else:
                    raise ValueError("Volume must be between 0 and 1")
                    
        except Exception as e:
            logger.error(f"Error setting voice properties: {e}")
            raise

    def get_current_voice(self) -> Optional[Dict]:
        """
        Get current voice information.
        
        Returns:
            Optional[Dict]: Current voice details or None
        """
        if self.current_voice:
            return {
                'name': self.current_voice.name,
                'id': self.current_voice.id,
                'languages': self.current_voice.languages,
                'gender': self.current_voice.gender,
                'age': self.current_voice.age
            }
        return None

    def is_speaking(self) -> bool:
        """
        Check if currently speaking.
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.speaking 
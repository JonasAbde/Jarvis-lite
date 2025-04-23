import win32com.client
import logging
from typing import Optional, Dict, List
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisVoiceWin32:
    """
    Enhanced voice system for Jarvis using win32com.client for better Windows voice support.
    """
    
    def __init__(self, preferred_voice: str = "Microsoft Helle", rate: int = 0, volume: int = 100):
        """
        Initialize the voice system.
        
        Args:
            preferred_voice (str): Preferred voice name (default: "Microsoft Helle")
            rate (int): Speech rate from -10 to 10 (default: 0)
            volume (int): Volume level from 0 to 100 (default: 100)
        """
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.rate = rate
        self.volume = volume
        self.speaking = False
        self._load_config()
        self.init_voice(preferred_voice)
        
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

    def init_voice(self, preferred_voice: str) -> None:
        """
        Initialize the voice with the preferred voice name.
        
        Args:
            preferred_voice (str): Name of the preferred voice
        """
        try:
            voices = self.speaker.GetVoices()
            logger.info(f"Found {voices.Count} voices:")
            
            selected_voice = None
            for i in range(voices.Count):
                voice = voices.Item(i)
                voice_name = voice.GetDescription()
                logger.info(f"Voice {i}: {voice_name}")
                
                if preferred_voice.lower() in voice_name.lower():
                    selected_voice = voice
                    logger.info(f"Selected voice: {voice_name}")
                    break
            
            if selected_voice:
                self.speaker.Voice = selected_voice
                logger.info(f"Initialized voice: {selected_voice.GetDescription()}")
            else:
                logger.warning(f"Could not find voice '{preferred_voice}', using default voice")
            
            # Set properties
            self.speaker.Rate = self.rate  # -10 to 10
            self.speaker.Volume = self.volume  # 0 to 100
            
        except Exception as e:
            logger.error(f"Error initializing voice: {e}")
            raise

    def speak(self, text: str) -> None:
        """
        Speak text synchronously.
        
        Args:
            text (str): Text to speak
        """
        try:
            text = self._improve_danish_pronunciation(text)
            self.speaking = True
            self.speaker.Speak(text, 1)  # 1 means synchronous
            self.speaking = False
        except Exception as e:
            logger.error(f"Error during speech: {e}")
            self.speaking = False

    def speak_async(self, text: str) -> None:
        """
        Speak text asynchronously.
        
        Args:
            text (str): Text to speak
        """
        try:
            text = self._improve_danish_pronunciation(text)
            self.speaking = True
            self.speaker.Speak(text, 0)  # 0 means asynchronous
        except Exception as e:
            logger.error(f"Error during async speech: {e}")
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
            self.speaker.Skip("Sentence", 2**31 - 1)  # Skip to end
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
            available_voices = self.speaker.GetVoices()
            for i in range(available_voices.Count):
                voice = available_voices.Item(i)
                voices.append({
                    'name': voice.GetDescription(),
                    'id': i
                })
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
        return voices

    def set_voice_properties(self, rate: Optional[int] = None, 
                           volume: Optional[int] = None) -> None:
        """
        Set voice properties with validation.
        
        Args:
            rate (int, optional): Speech rate (-10 to 10)
            volume (int, optional): Volume level (0 to 100)
        """
        try:
            if rate is not None:
                if -10 <= rate <= 10:
                    self.rate = rate
                    self.speaker.Rate = rate
                else:
                    raise ValueError("Rate must be between -10 and 10")
                    
            if volume is not None:
                if 0 <= volume <= 100:
                    self.volume = volume
                    self.speaker.Volume = volume
                else:
                    raise ValueError("Volume must be between 0 and 100")
                    
        except Exception as e:
            logger.error(f"Error setting voice properties: {e}")
            raise

    def is_speaking(self) -> bool:
        """
        Check if currently speaking.
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.speaking 
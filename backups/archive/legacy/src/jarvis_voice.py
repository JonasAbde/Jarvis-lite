import logging
import json
from typing import Optional, Dict, List
from pathlib import Path
from .danspeech_voice import DanSpeechVoice

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisVoice:
    """
    Voice system for Jarvis using DanSpeech for both speech recognition and synthesis.
    """
    
    def __init__(self):
        """Initialize the voice system"""
        self.danspeech = DanSpeechVoice()
        self._load_config()
        
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

    def start_listening(self):
        """Start listening for speech using DanSpeech"""
        self.danspeech.start_listening()

    def stop_listening(self):
        """Stop listening for speech"""
        self.danspeech.stop_listening()

    def get_last_recognized_text(self) -> str:
        """Get the last recognized text from DanSpeech"""
        return self.danspeech.get_last_recognized_text()

    def clear_last_recognized_text(self):
        """Clear the last recognized text"""
        self.danspeech.clear_last_recognized_text()

    def speak(self, text: str) -> None:
        """
        Speak the given text using DanSpeech.
        
        Args:
            text (str): Text to speak
        """
        try:
            # For now, we'll just print the text since DanSpeech doesn't have TTS
            # In the future, we can integrate a Danish TTS system
            print(f"Jarvis: {text}")
        except Exception as e:
            logger.error(f"Error speaking text: {e}")

    def stop(self) -> None:
        """Stop any ongoing speech"""
        pass  # No need to stop anything since we're just printing

    def is_speaking(self) -> bool:
        """
        Check if the voice is currently speaking.
        
        Returns:
            bool: Always False since we're just printing
        """
        return False 
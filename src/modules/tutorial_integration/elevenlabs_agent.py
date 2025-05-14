"""
ElevenLabs Agent Integration
Integrerer ElevenLabs Jarvis agent med vores web interface
"""

import os
import logging
from typing import Optional, Dict, Any
from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)

class ElevenLabsAgent:
    """ElevenLabs agent der håndterer kommunikation med Jarvis stemmen"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY ikke fundet i miljøvariablerne")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=self.api_key)
            
        self.voice_id = "yKTVnkrvUgAy3uf055zD"  # Agent ID
        self.model_id = "eleven_monolingual_v1"
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Initialiserer agenten"""
        if not self.api_key:
            logger.warning("Kan ikke initialisere ElevenLabs uden API nøgle")
            return False
            
        try:
            # Get voices er ikke en asynkron metode, så vi skal ikke bruge await
            voices = self.client.voices.get_all()
            voice = next((v for v in voices.voices if v.voice_id == self.voice_id), None)
            if voice:
                logger.info(f"ElevenLabs agent initialiseret med stemme: {voice.name}")
                self.is_initialized = True
                return True
            else:
                logger.warning(f"Stemme med ID '{self.voice_id}' ikke fundet.")
                # Brug default stemme hvis den angivne ikke findes
                if voices.voices:
                    self.voice_id = voices.voices[0].voice_id
                    logger.info(f"Bruger default stemme: {voices.voices[0].name}")
                    self.is_initialized = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Fejl ved initialisering af ElevenLabs agent: {e}")
            return False

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Konverterer tekst til tale (bytes)"""
        if not self.api_key or not self.client:
            logger.warning("Kan ikke lave text-to-speech uden API nøgle")
            return None
            
        try:
            # audio.generate er ikke asynkron, så ingen await
            audio = self.client.audio.generate(
                voice_id=self.voice_id,
                model_id=self.model_id,
                text=text,
                output_format="mp3"
            )
            return audio
        except Exception as e:
            logger.error(f"Fejl ved TTS: {e}")
            return None

    async def handle_websocket_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Håndterer WebSocket beskeder"""
        try:
            if message.get("type") == "chat":
                text = message.get("text", "").strip()
                if text:
                    audio_data = await self.text_to_speech(text)
                    if audio_data:
                        import base64
                        return {
                            "type": "response",
                            "text": text,
                            "audio": base64.b64encode(audio_data).decode('utf-8')
                        }
                    else:
                        return {
                            "type": "response",
                            "text": "Jeg kunne ikke konvertere teksten til tale. Kontroller din ElevenLabs API nøgle.",
                            "error": "TTS fejlede"
                        }

            elif message.get("type") == "status":
                return {
                    "type": "status",
                    "connected": self.is_initialized,
                    "agent_id": self.voice_id,
                    "api_key_valid": self.api_key is not None and self.is_initialized
                }

            return None

        except Exception as e:
            logger.error(f"Fejl ved håndtering af websocket besked: {e}")
            return {
                "type": "error", 
                "message": f"Der opstod en fejl: {str(e)}"
            } 
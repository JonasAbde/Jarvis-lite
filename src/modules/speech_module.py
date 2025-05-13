"""
Tale-modul til Jarvis
Håndterer text-to-speech og speech-to-text funktionalitet
"""
import asyncio
import logging
import tempfile
import os
from typing import Any, Dict, List

# Denne import metode forhindrer cirkulære imports
import sys
# Tilføj projekt root til sys.path hvis den ikke allerede er der
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
# Direkte import af kun basisklassen fra hovedprogrammet
from jarvis_main import JarvisModule

logger = logging.getLogger(__name__)

class SpeechModule(JarvisModule):
    """Tale-modul til Jarvis"""
    
    # Metadata
    name = "speech"
    description = "Tale-modul til Jarvis - håndterer TTS og STT"
    version = "1.0.0"
    dependencies = ["gtts", "playsound"]  # Simplere og lettere afhængigheder
    
    def __init__(self):
        super().__init__()
        self.tts_available = False
        self.stt_available = False
        self.mock_stt = True  # Brug mock STT indtil vi finder en bedre løsning
    
    async def initialize(self) -> bool:
        """Initialiserer tale-modulet"""
        logger.info("Initialiserer tale-modul")
        
        try:
            # Tjek tilgængeligheden af gTTS for tekst-til-tale
            try:
                from gtts import gTTS
                self.tts_available = True
                logger.info("gTTS tilgængelig for tekst-til-tale")
            except ImportError:
                logger.warning("gTTS ikke tilgængelig - tekst-til-tale er begrænset")
                self.tts_available = False
                
            # Tjek tilgængeligheden af playsound for lydafspilning
            try:
                from playsound import playsound
                logger.info("playsound tilgængelig for lydafspilning")
            except ImportError:
                logger.warning("playsound ikke tilgængelig - lydafspilning er begrænset")
            
            # For nu bruger vi mock STT (tale-til-tekst)
            logger.info("Bruger mock tale-til-tekst funktionalitet")
                
            self.active = True
            logger.info("Tale-modul initialiseret")
            return True
        except Exception as e:
            logger.error(f"Fejl ved initialisering af tale-modul: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Lukker tale-modulet"""
        logger.info("Lukker tale-modul")
        
        try:
            # Intet at lukke ned - vi frigører evt. resourcer
            self.active = False
            return True
        except Exception as e:
            logger.error(f"Fejl ved nedlukning af tale-modul: {e}")
            return False
    
    async def text_to_speech(self, text: str) -> bool:
        """Konverterer tekst til tale"""
        if not self.active:
            logger.warning("Tale-modul er ikke aktivt")
            return False
            
        logger.info(f"TTS: {text}")
        
        # gTTS baseret tekst-til-tale
        if self.tts_available:
            try:
                from gtts import gTTS
                from playsound import playsound
                
                # Opret midlertidig fil til lyd
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    temp_filename = f.name
                
                # Generer tale og gem til fil
                logger.info(f"Genererer tale med gTTS: '{text}'")
                tts = gTTS(text=text, lang='da', slow=False)
                tts.save(temp_filename)
                
                # Afspil lyden og fjern filen bagefter
                logger.info(f"Afspiller lydfil: {temp_filename}")
                playsound(temp_filename)
                os.unlink(temp_filename)
                
                return True
            except Exception as e:
                logger.error(f"Fejl ved brug af gTTS: {e}")
                return False
        else:
            logger.warning("TTS ikke tilgængelig - installler gtts og playsound")
            return False
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Konverterer tale til tekst"""
        if not self.active:
            logger.warning("Tale-modul er ikke aktivt")
            return ""
            
        if self.mock_stt:
            # For nu returnerer vi bare en mock-respons
            logger.info("Bruger mock STT - ingen reel tale-genkendelse udføres")
            return "Dette er en demo af tale-til-tekst"
        else:
            logger.warning("STT ikke tilgængelig - installér pakker for tale-genkendelse")
            return "STT ikke tilgængelig"
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Returnerer liste af API endpoints for dette modul"""
        return [
            {
                "path": "/api/speech/tts",
                "method": "POST",
                "handler": self.handle_tts_endpoint
            },
            {
                "path": "/api/speech/stt",
                "method": "POST",
                "handler": self.handle_stt_endpoint
            }
        ]
    
    def get_ui_components(self) -> List[Dict[str, Any]]:
        """Returnerer liste af UI komponenter for dette modul"""
        return [
            {
                "type": "button",
                "id": "mic-button",
                "label": "Mikrofon",
                "icon": "mic",
                "location": "toolbar"
            },
            {
                "type": "slider",
                "id": "volume-slider",
                "label": "Lydstyrke",
                "min": 0,
                "max": 100,
                "default": 50,
                "location": "settings"
            }
        ]
    
    async def handle_tts_endpoint(self, request):
        """API endpoint handler for TTS"""
        body = await request.json()
        text = body.get("text", "")
        success = await self.text_to_speech(text)
        return {"success": success}
    
    async def handle_stt_endpoint(self, request):
        """API endpoint handler for STT"""
        try:
            form = await request.form()
            audio = form.get("audio")
            if audio:
                text = await self.speech_to_text(audio.file.read())
                return {"text": text}
            return {"text": "", "error": "Ingen audio data modtaget"}
        except Exception as e:
            logger.error(f"Fejl i STT endpoint: {e}")
            return {"text": "", "error": str(e)} 
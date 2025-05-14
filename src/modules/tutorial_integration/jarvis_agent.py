"""
Jarvis Agent Integration
Integrerer ElevenLabs Jarvis agent med vores web interface
"""

import os
import json
import logging
import asyncio
import base64
from typing import Optional, Dict, Any, List
from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)

class JarvisAgent:
    """Jarvis agent der håndterer kommunikation med ElevenLabs"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY ikke fundet i miljøvariablerne")
            self.api_key = None
            
        self.agent_id = "yKTVnkrvUgAy3uf055zD"  # Jarvis agent ID
        self.client = ElevenLabs(api_key=self.api_key) if self.api_key else None
        self.conversation_id = None
        self.active_connections = []
        self.is_initialized = False
        
        # Fallback responses hvis elevenlabs fejler
        self.fallback_responses = [
            "Jeg forstår dit spørgsmål, men kan ikke generere audio-svar lige nu.",
            "Din besked er modtaget. Jeg kan desværre ikke afspille svar.",
            "Jeg arbejder på dit spørgsmål, men kan ikke levere audio-svar.",
            "Jeg kunne godt tænke mig at svare dig mundtligt, men har problemer med stemmen lige nu."
        ]
        self.fallback_index = 0
    
    async def initialize(self) -> bool:
        """Initialiserer Jarvis agenten"""
        if not self.api_key:
            logger.warning("Springer initialization over (ingen API nøgle)")
            return False
            
        try:
            # Forsøg at hente stemmer for at validere API-nøglen (ikke asynkron, så ingen await)
            if self.client:
                voices = self.client.voices.get_all()
                self.is_initialized = True
                logger.info("Jarvis agent initialization lykkedes")
                return True
            return False
        except Exception as e:
            logger.error(f"Fejl ved initialization af Jarvis agent: {e}")
            self.is_initialized = False
            return False
    
    async def register_connection(self, websocket):
        """Registrerer en ny WebSocket forbindelse"""
        try:
            # Accepter forbindelsen først (VIGTIGT for at undgå ASGI-fejl)
            await websocket.accept()
            
            self.active_connections.append(websocket)
            logger.info("Ny klient forbundet til Jarvis agent")
            
            # Send velkomstbesked
            await self._send_json_safely(websocket, {
                "type": "welcome",
                "message": "Hej, jeg er Jarvis! Din danske sprogassistent. Hvordan kan jeg hjælpe dig i dag?"
            })
        except Exception as e:
            logger.error(f"Fejl ved registrering af websocket: {e}")
    
    async def unregister_connection(self, websocket):
        """Afregistrerer en WebSocket forbindelse"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("Klient afkoblet fra Jarvis agent")
    
    async def send_message(self, text: str) -> Dict[str, Any]:
        """Sender en besked til ElevenLabs API og returnerer svaret"""
        if not self.api_key or not self.client:
            logger.warning("Kan ikke sende besked uden API-nøgle")
            return {"text": "Jeg kan ikke svare lige nu, da jeg ikke er forbundet til ElevenLabs API."}
            
        try:
            # Brug ElevenLabs text-to-speech i stedet for chat API,
            # da conversation API ikke er tilgængelig i den nye version
            # audio.generate er ikke asynkron, så ingen await
            tts_response = self.client.audio.generate(
                text=text,
                voice_id=self.agent_id,
                model_id="eleven_monolingual_v1",
                output_format="mp3"
            )
            
            # Simulér et svar baseret på brugerens spørgsmål
            responses = {
                "hej": "Hej med dig! Hvordan kan jeg hjælpe?",
                "goddag": "Goddag! Hvad kan jeg gøre for dig i dag?",
                "hvem er du": "Jeg er Jarvis, din danske AI-assistent. Jeg kan hjælpe dig med information og samtale.",
                "hvad kan du": "Jeg kan svare på spørgsmål, hjælpe med praktiske opgaver og føre en samtale på dansk.",
                "vejr": "Jeg kan desværre ikke tjekke vejret lige nu, men jeg arbejder på det!",
                "tid": f"Klokken er {asyncio.get_event_loop().time()} i computertid.",
                "dato": "Jeg kan desværre ikke tjekke datoen lige nu.",
                "hjælp": "Jeg kan hjælpe med at svare på spørgsmål, forklare koncepter eller bare føre en samtale. Hvad vil du gerne tale om?",
                "tak": "Det var så lidt! Jeg er her for at hjælpe.",
                "farvel": "Farvel! Det var hyggeligt at snakke med dig."
            }
            
            response_text = "Jeg forstår ikke dit spørgsmål. Kan du uddybe?"
            for keyword, response in responses.items():
                if keyword in text.lower():
                    response_text = response
                    break
            
            # Base64-encode audio data for at sende via JSON
            audio_b64 = base64.b64encode(tts_response).decode('utf-8')
            
            return {
                "text": response_text,
                "audio": audio_b64
            }
        except Exception as e:
            logger.error(f"Fejl ved sending af besked til ElevenLabs API: {e}")
            
            # Brug en fallback response ved fejl
            fallback = self.fallback_responses[self.fallback_index]
            self.fallback_index = (self.fallback_index + 1) % len(self.fallback_responses)
            
            return {"text": fallback}
    
    async def handle_websocket_message(self, websocket, message: Dict[str, Any]) -> None:
        """Håndterer WebSocket beskeder"""
        try:
            logger.info(f"Modtaget websocket besked: {message}")
            
            if message.get("type") == "chat":
                text = message.get("text", "").strip()
                if text:
                    logger.info(f"Modtaget chat besked: {text}")
                    
                    # Send beskeden til Jarvis og få svar
                    response = await self.send_message(text)
                    
                    # Send svaret tilbage til klienten
                    await self._send_json_safely(websocket, {
                        "type": "response",
                        "text": response.get("text", ""),
                        "audio": response.get("audio")
                    })
                    
                    # Log svaret til debugging
                    logger.info(f"Svar sendt: {response.get('text', '')[:50]}...")
            
            elif message.get("type") == "status":
                # Send status information til klienten
                status_data = {
                    "type": "status",
                    "connected": self.is_initialized,
                    "agent_id": self.agent_id
                }
                await self._send_json_safely(websocket, status_data)
                logger.info(f"Status sendt: {status_data}")
                
        except Exception as e:
            logger.error(f"Fejl ved håndtering af WebSocket besked: {e}")
            
            # Send fejlbesked til klienten
            try:
                await self._send_json_safely(websocket, {
                    "type": "error",
                    "message": f"Der opstod en fejl: {str(e)}"
                })
            except:
                logger.error("Kunne ikke sende fejlbesked til klienten")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcaster en besked til alle forbundne klienter"""
        disconnected = []
        
        for conn in self.active_connections:
            try:
                await self._send_json_safely(conn, message)
            except Exception as e:
                logger.error(f"Fejl ved broadcast til klient: {e}")
                disconnected.append(conn)
        
        # Fjern afbrudte forbindelser
        for conn in disconnected:
            await self.unregister_connection(conn)
            
    async def _send_json_safely(self, websocket, data):
        """Sender JSON data sikkert via websocket med fejlhåndtering"""
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Fejl ved sending af websocket data: {e}")
            return False 
"""
FastAPI server til at styre og overvåge Jarvis-lite.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
import logging
import time
import json
import threading
import uvicorn
from typing import Optional, List, Dict, Any, Set, Callable, Coroutine
import asyncio
import sys
import os

# Korriger imports med relativ sti
# Tilføj projektroden til Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Tilføjede projektroden til Python path: {project_root}")

# Tilføj src mappen til Python path
src_path = os.path.join(project_root, 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Tilføjede src mappen til Python path: {src_path}")

# Print Python path for debugging
print("Python søgesti (sys.path):")
for path in sys.path:
    print(f"  - {path}")

# Initialisér logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api-server")

# Definer stier
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Check om vi kan importere Jarvis core moduler
JARVIS_CORE_AVAILABLE = False
try:
    from src.core.jarvis import process_input_text
    JARVIS_CORE_AVAILABLE = True
    logger.info("Jarvis core moduler tilgængelige")
except ImportError as e:
    process_input_text = None
    logger.warning(f"Jarvis core moduler ikke tilgængelige, kører i standalone mode. Fejl: {str(e)}")
    logger.warning("Hvis du ønsker Jarvis core funktionalitet, kontrollér at src/core/ mappen eksisterer og indeholder jarvis.py")
    
    # Simuleret svar funktion - denne bruges når Jarvis core ikke er tilgængelig
    async def process_input_text(text):
        logger.info(f"Bruger fallback svarfunktion for: '{text}'")
        svar_oversigt = {
            "hej": "Hej! Hvordan kan jeg hjælpe dig?",
            "goddag": "Goddag! Hvad kan jeg gøre for dig?",
            "vejr": "Jeg kan desværre ikke tjekke vejret i standalone-tilstand.",
            "klokken": f"Klokken er {time.strftime('%H:%M')}.",
            "tid": f"Det er {time.strftime('%H:%M')} den {time.strftime('%d/%m/%Y')}.",
            "hvem er du": "Jeg er Jarvis, din digitale assistent. Jeg kører i standalone-tilstand.",
            "hvad kan du": "I standalone-tilstand kan jeg svare på simple spørgsmål og konversere. Jeg har dog begrænsede muligheder uden Jarvis core."
        }
        
        for nøgleord, svar in svar_oversigt.items():
            if nøgleord.lower() in text.lower():
                return svar
        
        return "Jeg kører i standalone-tilstand uden Jarvis core moduler, så jeg kan kun give begrænsede svar."

# Importér vores agenter
if __name__ == "__main__":
    # Når scriptet køres direkte
    import jarvis_agent
    import elevenlabs_agent
    JarvisAgent = jarvis_agent.JarvisAgent
    ElevenLabsAgent = elevenlabs_agent.ElevenLabsAgent
else:
    # Når importeret som modul
    from .jarvis_agent import JarvisAgent
    from .elevenlabs_agent import ElevenLabsAgent

# Pydantic modeller
class UserInput(BaseModel):
    text: str

class IntentFeedback(BaseModel):
    text: str
    correct_intent: str
    original_intent: Optional[str] = None
    confidence: Optional[float] = None

class PredictionResponse(BaseModel):
    text: str
    intent: str
    confidence: float
    needs_confirmation: bool = False

class ChatMessage(BaseModel):
    message: str
    voice: str = "default"

# Opret FastAPI app
app = FastAPI(title="Jarvis-Lite API", version="0.1.0")

# CORS-konfiguration (Cross Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisér agenter
jarvis_agent = JarvisAgent()
elevenlabs_agent = ElevenLabsAgent()

# Monter static filer
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
async def startup_event():
    # Initialiser agenter
    try:
        logger.info(f"Statiske filer serveres fra: {static_dir}")
        await jarvis_agent.initialize()
        await elevenlabs_agent.initialize()
        logger.info("Agenter initialiseret")
    except Exception as e:
        logger.error(f"Fejl ved initialisering af agenter: {e}")

@app.get("/")
async def get_index():
    """Omdirigerer til chat interfacet"""
    return RedirectResponse(url="/web/chat")

@app.get("/web/chat")
async def get_chat_page():
    """Serverer chat.html filen"""
    chat_path = os.path.join(static_dir, "chat.html")
    if os.path.exists(chat_path):
        return FileResponse(chat_path)
    else:
        logger.error(f"chat.html ikke fundet i {static_dir}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis-Lite - Chat</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
            </style>
        </head>
        <body>
            <h1>Fejl: Chat-siden kunne ikke findes</h1>
            <p>Check at filen chat.html findes i static mappen.</p>
        </body>
        </html>
        """)

@app.get("/web/training")
async def get_training_page():
    """Serverer training.html filen"""
    training_path = os.path.join(static_dir, "training.html")
    if os.path.exists(training_path):
        return FileResponse(training_path)
    else:
        logger.error(f"training.html ikke fundet i {static_dir}")
        return HTMLResponse(content="<h1>Træningssiden kunne ikke findes</h1>")

@app.get("/web/visualization")
async def get_visualization_page():
    """Serverer visualization.html filen"""
    viz_path = os.path.join(static_dir, "visualization.html")
    if os.path.exists(viz_path):
        return FileResponse(viz_path)
    else:
        logger.error(f"visualization.html ikke fundet i {static_dir}")
        return HTMLResponse(content="<h1>Visualiseringssiden kunne ikke findes</h1>")

@app.get("/status")
async def get_status():
    """Status endpoint til frontend"""
    return {
        "status": "connected" if JARVIS_CORE_AVAILABLE else "standalone",
        "time": time.time(),
        "listening_enabled": False,
        "modules": ["WebSocket", "ElevenLabs TTS", "Jarvis Agent"] if JARVIS_CORE_AVAILABLE else ["WebSocket", "ElevenLabs TTS"]
    }

@app.get("/api/status")
async def get_api_status():
    """Status endpoint til API"""
    return await get_status()

@app.get("/api/chat/history")
async def get_chat_history():
    """Returnerer chathistorik"""
    return {
        "status": "success",
        "history": []  # Tom historik - kunne hentes fra en database
    }

@app.post("/api/chat/send")
async def send_chat_message(message: ChatMessage):
    """Sender en chatbesked og returnerer svaret"""
    text = message.message.strip()
    voice = message.voice
    
    if not text:
        raise HTTPException(status_code=400, detail="Beskedtekst mangler")
    
    try:
        if voice == "default" and JARVIS_CORE_AVAILABLE:
            # Brug Jarvis core kun til tekstbehandling
            response_text = await process_input_text(text)
            
            # Generer tale via ElevenLabs i stedet for Google TTS
            jarvis_response = await jarvis_agent.send_message(response_text)
            response = {
                "status": "success",
                "text": response_text,
                "audio": jarvis_response.get("audio", None)
            }
        else:
            # Brug ElevenLabs agent direkte
            logger.info(f"Sender besked til Jarvis agent: {text}")
            jarvis_response = await jarvis_agent.send_message(text)
            response = {
                "status": "success",
                "text": jarvis_response.get("text", "Beklager, jeg kunne ikke forstå det."),
                "audio": jarvis_response.get("audio", None)
            }
            
        return response
            
    except Exception as e:
        logger.error(f"Fejl ved behandling af besked: {e}")
        raise HTTPException(status_code=500, detail=f"Der opstod en fejl: {str(e)}")

@app.post("/api/chat/clear_history")
async def clear_chat_history():
    """Rydder chathistorikken"""
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint til real-time kommunikation"""
    try:
        await jarvis_agent.register_connection(websocket)
        logger.info("Ny WebSocket-forbindelse etableret")
        
        while True:
            try:
                # Vent på besked fra klienten
                message_text = await websocket.receive_text()
                logger.debug(f"Modtaget WebSocket-besked: {message_text[:100]}...")
                
                # Parse JSON
                try:
                    message = json.loads(message_text)
                except json.JSONDecodeError:
                    logger.warning("Ugyldig JSON modtaget fra klient")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Ugyldig besked format (JSON forventet)"
                    })
                    continue
                
                # Håndter besked
                await jarvis_agent.handle_websocket_message(websocket, message)
                
            except WebSocketDisconnect:
                logger.info("WebSocket-forbindelse afbrudt af klient")
                break
            except Exception as e:
                logger.error(f"Fejl ved håndtering af WebSocket-besked: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Der opstod en serverfejl"
                    })
                except:
                    # Hvis vi ikke kan sende fejlbeskeden, er forbindelsen nok død
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket-forbindelse afbrudt under initialisering")
    except Exception as e:
        logger.error(f"WebSocket-fejl: {e}")
    finally:
        # Altid forsøg at afregistrere forbindelsen
        await jarvis_agent.unregister_connection(websocket)

# Tilføj en root-rute for at tjekke om server kører
@app.get("/health")
async def health_check():
    """Simpel health check"""
    return {"status": "healthy", "port": 8080}

@app.get("/api/nlu/intents")
async def get_intents():
    """Returnerer tilgængelige intents til træningssiden"""
    # Dette er en simpel mock-implementation
    intents = [
        {"name": "greeting", "description": "Hilsener", "examples": ["hej", "goddag", "hallo"]},
        {"name": "farewell", "description": "Farvel", "examples": ["farvel", "vi ses", "hej hej"]},
        {"name": "weather", "description": "Vejr-forespørgsler", "examples": ["hvordan bliver vejret", "er det regnvejr"]},
        {"name": "time", "description": "Tidsforespørgsler", "examples": ["hvad er klokken", "hvilken dag er det"]}
    ]
    return {"status": "success", "intents": intents}

@app.get("/training/status")
async def training_status():
    """Returnerer status for NLU træning"""
    # Mock-implementation
    return {
        "status": "success",
        "training": {
            "is_training": False,
            "progress": 100,
            "last_trained": "2025-05-14T10:00:00",
            "accuracy": 0.92
        }
    }

if __name__ == "__main__":
    logger.info("Starter Jarvis API server på port 8080")
    
    # Log alle tilgængelige endpoints
    logger.info("Tilgængelige endpoints:")
    for route in app.routes:
        if hasattr(route, "path"):
            logger.info(f"  - {route.path}")
    
    # Bind til localhost for at undgå firewall problemer
    logger.info("Server binder til 127.0.0.1:8080 - Åbn http://localhost:8080 i din browser")
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=False)
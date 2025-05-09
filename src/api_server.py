"""
FastAPI server til at styre og overvåge Jarvis-lite.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import logging
import time
import json
import threading
import uvicorn # Bruges til at køre FastAPI appen
from typing import Optional, List, Dict, Any, Set
import asyncio

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Tilføjet import af process_input_text fra jarvis-modulet ---
try:
    # Forsøg forskellige import-stier afhængigt af, hvordan scriptet er kørt
    try:
        # Hvis kørt direkte fra src-mappen
        from jarvis import process_input_text, speak_async, initialize_jarvis
    except ImportError:
        # Hvis kørt fra rod-mappen
        from src.jarvis import process_input_text, speak_async, initialize_jarvis
    
    # Initialiser Jarvis for at indlæse modellen
    JARVIS_INITIALIZED = initialize_jarvis()
    JARVIS_CORE_AVAILABLE = JARVIS_INITIALIZED
    
    if JARVIS_INITIALIZED:
        logger.info("Jarvis kernemodul initialiseret succesfuldt.")
    else:
        logger.warning("Jarvis kernemodul blev importeret, men initialisering fejlede.")
except ImportError as e:
    logger.warning(f"Kunne ikke importere Jarvis kernemoduler: {e}. Kører i simuleret tilstand.")
    JARVIS_CORE_AVAILABLE = False
    
    # Simuleret process_input_text funktion til test
    async def process_input_text(user_input: str) -> str:
        logger.info(f"Simulerer svar på: {user_input}")
        await asyncio.sleep(1)  # Simuler tænketid
        responses = {
            "hej": "Hej med dig! Hvordan kan jeg hjælpe?",
            "hvad kan du": "Jeg er Jarvis, din danske stemmeassistent. Jeg kan svare på spørgsmål, fortælle tiden, og meget mere.",
            "tid": "Klokken er " + time.strftime("%H:%M"),
            "dato": "I dag er det " + time.strftime("%d/%m/%Y"),
            "vejr": "Jeg kan desværre ikke tjekke vejret lige nu."
        }
        
        for keyword, response in responses.items():
            if keyword in user_input.lower():
                return response
                
        return f"Jeg forstod din besked: '{user_input}', men jeg ved ikke helt hvordan jeg skal hjælpe med det."
    
    async def speak_async(text: str, lang: str = 'da') -> None:
        logger.info(f"Simuleret tale: {text}")

# Dummy Jarvis Controller - erstat med din faktiske integration
class JarvisControllerPlaceholder:
    def __init__(self):
        self._is_listening = False
        self._model_loaded = True # Antag at modeller er loaded
        self._recent_logs: List[Dict[str, Any]] = []
        self._max_log_entries = 20
        self._chat_history: List[Dict[str, Any]] = []
        self._connected_websockets: Set[WebSocket] = set()
        self._start_time = time.time()

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "lytter" if self._is_listening else "inaktiv",
            "model_loaded": self._model_loaded,
            "active_threads": threading.active_count(), # Eksempel på yderligere info
            "uptime_seconds": int(time.time() - self._start_time)
        }

    def toggle_listening(self) -> bool:
        self._is_listening = not self._is_listening
        logger.info(f"API: Lytning sat til {self._is_listening}")
        # Her ville du kalde live_voice_ai.start_listening() eller stop_listening()
        
        # Broadcast til alle tilsluttede websockets
        asyncio.create_task(self.broadcast_message({
            "type": "listening_status",
            "listening": self._is_listening
        }))
        
        return self._is_listening

    def add_log_entry(self, entry_type: str, message: str, details: Optional[Dict] = None):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": entry_type, 
            "message": message,
            "details": details or {}
        }
        self._recent_logs.append(log_entry)
        if len(self._recent_logs) > self._max_log_entries:
            self._recent_logs = self._recent_logs[-self._max_log_entries:]
            
        # Broadcast logbeskeden til alle tilsluttede websockets
        asyncio.create_task(self.broadcast_message({
            "type": "log",
            "entry": log_entry
        }))

    def get_recent_logs(self) -> List[Dict[str, Any]]:
        return self._recent_logs

    def set_start_time(self):
        self._start_time = time.time()
        
    async def add_chat_message(self, user_message: str, jarvis_response: str) -> None:
        """Tilføjer en chat-besked til historikken"""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_message,
            "jarvis": jarvis_response
        }
        self._chat_history.append(entry)
        
        # Behold kun de seneste 100 beskeder
        if len(self._chat_history) > 100:
            self._chat_history = self._chat_history[-100:]
            
        # Broadcast til alle tilsluttede websockets
        await self.broadcast_message({
            "type": "chat_history_update",
            "entry": entry
        })
            
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Henter chat-historik"""
        return self._chat_history
    
    def clear_chat_history(self) -> None:
        """Rydder chat-historik"""
        self._chat_history = []
        
        # Broadcast til alle tilsluttede websockets
        asyncio.create_task(self.broadcast_message({
            "type": "chat_history_cleared"
        }))
    
    async def register_websocket(self, websocket: WebSocket) -> None:
        """Registrerer en ny WebSocket-forbindelse"""
        await websocket.accept()
        self._connected_websockets.add(websocket)
        logger.info(f"WebSocket client forbundet. Aktive forbindelser: {len(self._connected_websockets)}")
        
        # Send aktuel status til den nye klient
        await websocket.send_json({
            "type": "status",
            "status": "lytter" if self._is_listening else "inaktiv",
            "message": "Forbundet til Jarvis-Lite"
        })
    
    def unregister_websocket(self, websocket: WebSocket) -> None:
        """Afregistrerer en WebSocket-forbindelse"""
        self._connected_websockets.discard(websocket)
        logger.info(f"WebSocket client afbrudt. Tilbageværende forbindelser: {len(self._connected_websockets)}")
    
    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """Sender en besked til alle tilsluttede WebSocket-klienter"""
        disconnected_websockets = set()
        
        for websocket in self._connected_websockets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Fejl ved sending til WebSocket: {e}")
                disconnected_websockets.add(websocket)
        
        # Fjern afbrudte WebSockets
        for websocket in disconnected_websockets:
            self.unregister_websocket(websocket)

# Global instans af controlleren
jarvis_controller = JarvisControllerPlaceholder()

# Pydantic modeller for request/response bodies
class StatusResponse(BaseModel):
    status: str
    model_loaded: bool
    active_threads: Optional[int] = None
    uptime_seconds: Optional[int] = None

class CommandToggleResponse(BaseModel):
    listening_enabled: bool

class LogEntry(BaseModel):
    timestamp: str
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None

class RecentLogsResponse(BaseModel):
    logs: List[LogEntry]
    
# --- Nye modeller til chat-funktionalitet ---
class ChatMessage(BaseModel):
    message: str
    voice: Optional[str] = "david"
    
class ChatResponse(BaseModel):
    response: str
    
class ChatHistoryEntry(BaseModel):
    timestamp: str
    user: str
    jarvis: str
    
class ChatHistoryResponse(BaseModel):
    history: List[ChatHistoryEntry]

# Opret FastAPI app instans
app = FastAPI(
    title="Jarvis-Lite API",
    description="API til at styre og overvåge Jarvis-Lite stemmeassistenten.",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    # Denne funktion kaldes når FastAPI starter
    # Godt sted at initialisere ting, f.eks. din Jarvis controller hvis den ikke er global
    jarvis_controller.set_start_time()
    # Simuler en log entry ved opstart
    jarvis_controller.add_log_entry("system", "FastAPI server startet.")
    logger.info("FastAPI server startet. Jarvis controller initialiseret.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI server lukker ned.")
    # Her kan du frigøre ressourcer

@app.get("/status", response_model=StatusResponse, summary="Få Jarvis-lites status")
async def get_jarvis_status():
    """
    Returnerer Jarvis-lites nuværende status, såsom om den lytter aktivt,
    og om modellerne er indlæst.
    """
    try:
        status_data = jarvis_controller.get_status()
        return StatusResponse(**status_data)
    except Exception as e:
        logger.error(f"Fejl i /status endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved hentning af status")

@app.post("/command/listen_toggle", response_model=CommandToggleResponse, summary="Skift lytte-tilstand")
async def toggle_listening_mode():
    """
    Aktiverer eller deaktiverer Jarvis-lites aktive lytning.
    """
    try:
        is_now_listening = jarvis_controller.toggle_listening()
        # Log denne handling
        action = "startet" if is_now_listening else "stoppet"
        jarvis_controller.add_log_entry("control", f"Aktiv lytning manuelt {action} via API.")
        return CommandToggleResponse(listening_enabled=is_now_listening)
    except Exception as e:
        logger.error(f"Fejl i /command/listen_toggle endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved skift af lytte-tilstand")

@app.get("/logs/recent", response_model=RecentLogsResponse, summary="Få seneste log-entries")
async def get_recent_jarvis_logs():
    """
    Returnerer en liste over de seneste par genkendte kommandoer, interaktioner
    eller systemhændelser logget af Jarvis-lite (via API-controlleren).
    """
    try:
        logs = jarvis_controller.get_recent_logs()
        return RecentLogsResponse(logs=[LogEntry(**log) for log in logs])
    except Exception as e:
        logger.error(f"Fejl i /logs/recent endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved hentning af logs")

# --- Nye endpoints til chat-funktionalitet ---
@app.post("/api/chat/send", response_model=ChatResponse, summary="Send besked til Jarvis")
async def send_chat_message(message: ChatMessage):
    """
    Sender en besked til Jarvis og returnerer svaret.
    """
    try:
        logger.info(f"Chat besked modtaget: {message.message}")
        
        # Behandl beskeden med Jarvis kernelogik
        response = await process_input_text(message.message)
        
        # Gem beskeden og svaret i historikken
        await jarvis_controller.add_chat_message(message.message, response)
        
        # Log handlingen
        jarvis_controller.add_log_entry(
            "chat", 
            f"Besked håndteret via chat: '{message.message[:30]}...' hvis længere"
        )
        
        # Valgfrit: Læs svaret højt hvis Jarvis er i lyttetilstand
        if jarvis_controller._is_listening and JARVIS_CORE_AVAILABLE:
            # Kør asynkront for ikke at blokere API-kaldet
            asyncio.create_task(speak_async(response))
        
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Fejl i /api/chat/send endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved beskedbehandling")

@app.get("/api/chat/history", response_model=ChatHistoryResponse, summary="Hent chat-historik")
async def get_chat_history():
    """
    Henter historikken af beskeder og svar mellem bruger og Jarvis.
    """
    try:
        history = jarvis_controller.get_chat_history()
        return ChatHistoryResponse(history=[ChatHistoryEntry(**entry) for entry in history])
    except Exception as e:
        logger.error(f"Fejl i /api/chat/history endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved hentning af chat-historik")

@app.post("/api/chat/clear_history", summary="Ryd chat-historik")
async def clear_chat_history():
    """
    Rydder chat-historikken.
    """
    try:
        jarvis_controller.clear_chat_history()
        jarvis_controller.add_log_entry("chat", "Chat-historik ryddet.")
        return {"success": True, "message": "Chat-historik ryddet."}
    except Exception as e:
        logger.error(f"Fejl i /api/chat/clear_history endpoint: {e}")
        raise HTTPException(status_code=500, detail="Intern serverfejl ved rydning af chat-historik")

# --- WebSocket endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket forbindelse til Jarvis.
    Giver real-time kommunikation mellem klient og server.
    """
    await jarvis_controller.register_websocket(websocket)
    
    try:
        while True:
            # Modtag besked fra klienten
            data = await websocket.receive_text()
            
            try:
                # Parse JSON-besked
                message = json.loads(data)
                
                # Håndter forskellige beskedtyper
                if message.get("type") == "chat":
                    user_message = message.get("message", "")
                    voice = message.get("voice", "david")
                    
                    logger.info(f"WebSocket chat-besked modtaget: {user_message}")
                    
                    # Behandl besked
                    response = await process_input_text(user_message)
                    
                    # Gem i historik
                    await jarvis_controller.add_chat_message(user_message, response)
                    
                    # Læs svaret højt
                    if jarvis_controller._is_listening and JARVIS_CORE_AVAILABLE:
                        asyncio.create_task(speak_async(response))
                    
                    # Send svar
                    await websocket.send_json({
                        "type": "response",
                        "message": response
                    })
                
                elif message.get("type") == "status_request":
                    # Send aktuel status
                    status = jarvis_controller.get_status()
                    await websocket.send_json({
                        "type": "status",
                        "status": status["status"],
                        "model_loaded": status["model_loaded"],
                        "uptime_seconds": status["uptime_seconds"]
                    })
                
                elif message.get("type") == "toggle_listening":
                    # Skift lyttetilstand
                    is_listening = jarvis_controller.toggle_listening()
                    await websocket.send_json({
                        "type": "listening_status",
                        "listening": is_listening
                    })
                
            except json.JSONDecodeError:
                logger.warning(f"Ugyldig WebSocket-besked modtaget: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Ugyldig besked-format. Forventede JSON."
                })
            
    except WebSocketDisconnect:
        # Klienten er afbrudt
        jarvis_controller.unregister_websocket(websocket)
    
    except Exception as e:
        # Håndter andre fejl
        logger.error(f"WebSocket fejl: {e}")
        jarvis_controller.unregister_websocket(websocket)

# --- CORS opsætning (vigtigt for webapp) ---
from fastapi.middleware.cors import CORSMiddleware

# Tilføj CORS middleware til app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # I produktion: erstat med specifikke domæner
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Serve static files ---
from fastapi.staticfiles import StaticFiles
import os

# Definer stien til de statiske filer
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Tjek om mappen findes
if os.path.exists(static_dir):
    # Mount static files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Serverer statiske filer fra {static_dir}")
else:
    logger.warning(f"Statisk mappe '{static_dir}' findes ikke. Statiske filer vil ikke være tilgængelige.")

# --- Serve root path (index.html) ---
from fastapi.responses import FileResponse

@app.get("/")
async def get_index():
    """Serverer index.html filen"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        logger.warning(f"index.html ikke fundet i {static_dir}")
        # Returner en simpel HTML-streng i stedet for at fejle
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis-Lite</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>Jarvis-Lite API Server</h1>
            <p>Dine statiske filer blev ikke fundet. Sørg for at de er tilgængelige i 'static' mappen.</p>
        </body>
        </html>
        """

@app.get("/jarvis-logo.png")
async def get_logo():
    """Serverer logo-fil"""
    logo_path = os.path.join(static_dir, "jarvis-logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    else:
        # Generer en simpel placeholder i stedet for at fejle
        placeholder_path = os.path.join(static_dir, "placeholder-logo.png")
        if os.path.exists(placeholder_path):
            return FileResponse(placeholder_path)
        else:
            # Hvis ingen logo findes, returner en 404
            raise HTTPException(status_code=404, detail="Logo ikke fundet")

if __name__ == "__main__":
    port = 8000
    logger.info(f"Starter Jarvis-Lite API server på http://localhost:{port}")
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True) 
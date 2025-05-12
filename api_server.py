"""
FastAPI server til at styre og overvåge Jarvis-lite.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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
from src.audio.speech import speech_handler

# Tilføj src til Python path hvis den ikke allerede er der
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Import Jarvis Kernekomponenter ---
JARVIS_CORE_AVAILABLE = False
JARVIS_INITIALIZED = False

# Fast type-annotering på toppen
process_input_text: Optional[Callable[[str], Coroutine[Any, Any, str]]] = None
speak_async: Optional[Callable[[str, str], Coroutine[Any, Any, None]]] = None
initialize_jarvis: Optional[Callable[[], bool]] = None
nlu_classifier = None

# Konstant til auto-retrain
RETRAIN_THRESHOLD = 10  # Justér hvis du vil have flere/færre eksempler før gentræning

try:
    from src.jarvis import process_input_text as real_process_input_text, \
                          speak_async as real_speak_async, \
                          initialize_jarvis as real_initialize_jarvis
    from src.nlu.classifier import NLUClassifier
    
    logger.info("Imported Jarvis core from src.jarvis")
    
    # Initialiser NLU klassifikator
    nlu_classifier = NLUClassifier()
    
    # Forsøg initialisering
    logger.info("Attempting Jarvis core initialization...")
    JARVIS_INITIALIZED = real_initialize_jarvis()
    if JARVIS_INITIALIZED:
        JARVIS_CORE_AVAILABLE = True
        process_input_text = real_process_input_text
        speak_async = real_speak_async
        initialize_jarvis = real_initialize_jarvis
        logger.info("Jarvis kernemodul initialiseret succesfuldt.")
    else:
        logger.warning("Jarvis kernemodul blev importeret, men initialize_jarvis returnerede False.")
        JARVIS_CORE_AVAILABLE = False

except ImportError as e:
    logger.warning(f"Kunne ikke importere Jarvis kernemoduler: {e}. Kører i simuleret tilstand.")
    JARVIS_CORE_AVAILABLE = False
except Exception as e:
    logger.warning(f"Fejl under initialisering af Jarvis: {e}", exc_info=True)
    JARVIS_CORE_AVAILABLE = False

# Falback-NLU hvis Jarvis ikke kan loades
class SimulatedNLUClassifier:
    async def predict(self, text: str) -> Dict[str, Any]:
        return {"intent": "simulated", "confidence": 0.42}

    async def log_low_confidence(self, text: str, intent: str, confidence: float):
        logger.info(f"[Simuleret] Lav konfidens: {text=} {intent=} {confidence=}")

    async def add_confirmed_example(self, text: str, intent: str, confidence: float = 0.5):
        logger.info(f"[Simuleret] Eksempel gemt: {text=} {intent=} {confidence=}")

    @property
    def new_examples_count(self) -> int:
        return 0

    def get_available_intents(self) -> List[str]:
        return ["simulated"]

    async def auto_retrain(self):
        logger.info("[Simuleret] auto_retrain kaldt")

# Hvis kernen fejler, kobl fallbacks på
if not JARVIS_CORE_AVAILABLE:
    # ----- simuleret tekstbehandling -----
    async def _sim_process(user_input: str) -> str:
        logger.info(f"[Simuleret] Behandler: {user_input}")
        await asyncio.sleep(0.1)
        responses = {
            "hej": "Hej med dig! Hvordan kan jeg hjælpe?",
            "hvad kan du": "Jeg er Jarvis, din danske stemmeassistent. Jeg kan svare på spørgsmål, fortælle tiden, og meget mere.",
            "dato": "I dag er det " + time.strftime("%d/%m/%Y"),
            "vejr": "Jeg kan desværre ikke tjekke vejret lige nu.",
            "hvem er du": "Jeg er Jarvis, din danske stemmeassistent. Jeg er her for at hjælpe dig.",
            "tid": "Klokken er " + time.strftime("%H:%M")
        }

        for keyword, response in responses.items():
            if keyword in user_input.lower():
                return response

        return f"Jeg forstod din besked: '{user_input}', men jeg ved ikke helt hvordan jeg skal hjælpe med det."

    async def _sim_speak(text: str, lang: str = "da") -> None:
        logger.info(f"[Simuleret] Tale: {text}")

    def _sim_init() -> bool:
        logger.info("[Simuleret] initialize_jarvis kaldt")
        return False

    # >>> Bind navne så de ikke længere er None
    process_input_text = _sim_process
    speak_async       = _sim_speak
    initialize_jarvis = _sim_init

    # ----- fallback-NLU -----
    nlu_classifier = SimulatedNLUClassifier()

# Pydantic modeller til API requests
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

# FastAPI app
app = FastAPI(
    title="Jarvis-Lite API",
    description="API for Jarvis-Lite dansk stemmeassistent",
    version="1.0.0"
)

# Tilføj CORS middleware til app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # I produktion: erstat med specifikke domæner
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Serve static files ---
# Definer stien til de statiske filer relativt til api_server.py
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Tjek om mappen findes
if not os.path.exists(static_dir):
    logger.warning(f"Static mappe ikke fundet i {static_dir}, prøver at oprette den...")
    try:
        os.makedirs(static_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Kunne ikke oprette static mappe: {e}")
        raise

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")
logger.info(f"Serverer statiske filer fra {static_dir}")

@app.get("/")
async def get_index():
    """Serverer index.html filen"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        logger.error(f"index.html ikke fundet i {static_dir}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis-Lite</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: #721c24; background: #f8d7da; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Jarvis-Lite Fejl</h1>
            <div class="error">
                <p>Kunne ikke finde web interfacet. Kontroller at alle statiske filer er på plads.</p>
            </div>
        </body>
        </html>
        """)

@app.get("/")
async def root():
    """Root endpoint - returnerer status information."""
    return {
        "status": "active",
        "jarvis_core": JARVIS_CORE_AVAILABLE,
        "initialized": JARVIS_INITIALIZED
    }

@app.post("/process", response_model=PredictionResponse)
async def process_text(user_input: UserInput, background_tasks: BackgroundTasks):
    """
    Behandler bruger input og returnerer svar.
    Hvis konfidensen er lav, markeres svaret som usikkert.
    """
    if not JARVIS_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jarvis kerne ikke tilgængelig")
        
    if nlu_classifier is None:
        raise HTTPException(status_code=503, detail="NLU-modul ikke tilgængeligt")
        
    try:
        # Forudsig intent
        if hasattr(nlu_classifier, "predict"):
            if asyncio.iscoroutinefunction(nlu_classifier.predict):
                prediction = await nlu_classifier.predict(user_input.text)
            else:
                prediction = nlu_classifier.predict(user_input.text)
                
            if not isinstance(prediction, dict):
                prediction = {"intent": "unknown", "confidence": 0.0}
        else:
            raise ValueError("NLU classifier har ikke en predict-metode")
        
        confidence = float(prediction.get("confidence", 0))
        predicted_intent = str(prediction.get("intent", "unknown"))
        
        # Log lav konfidens i baggrunden hvis nødvendigt
        if confidence < 0.55:  # Brug samme threshold som i classifier
            if hasattr(nlu_classifier, "log_low_confidence"):
                if asyncio.iscoroutinefunction(nlu_classifier.log_low_confidence):
                    background_tasks.add_task(
                        run_async,
                        nlu_classifier.log_low_confidence(
                            user_input.text,
                            predicted_intent,
                            confidence
                        )
                    )
                else:
                    nlu_classifier.log_low_confidence(
                        user_input.text,
                        predicted_intent,
                        confidence
                    )
        
        return PredictionResponse(
            text=user_input.text,
            intent=predicted_intent,
            confidence=confidence,
            needs_confirmation=confidence < 0.55
        )
        
    except Exception as e:
        logger.error(f"Fejl under tekstbehandling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(feedback: IntentFeedback, background_tasks: BackgroundTasks):
    """
    Modtager bruger-feedback om korrekt intent og gemmer det som træningsdata.
    Starter automatisk gentræning hvis nødvendigt.
    """
    if nlu_classifier is None:
        raise HTTPException(status_code=503, detail="NLU-modul ikke tilgængeligt")
        
    try:
        if hasattr(nlu_classifier, "add_confirmed_example"):
            # Konverter confidence til float hvis den findes
            confidence = float(feedback.confidence) if feedback.confidence is not None else 0.5
            
            if asyncio.iscoroutinefunction(nlu_classifier.add_confirmed_example):
                background_tasks.add_task(
                    run_async,
                    nlu_classifier.add_confirmed_example(
                        feedback.text,
                        feedback.correct_intent,
                        confidence=confidence
                    )
                )
            else:
                nlu_classifier.add_confirmed_example(
                    feedback.text,
                    feedback.correct_intent,
                    confidence=confidence
                )
            
            # Tjek om vi skal starte gentræning
            if hasattr(nlu_classifier, "new_examples_count"):
                count = (
                    nlu_classifier.new_examples_count() 
                    if callable(nlu_classifier.new_examples_count)
                    else nlu_classifier.new_examples_count
                )
                
                if count >= RETRAIN_THRESHOLD:
                    if hasattr(nlu_classifier, "auto_retrain"):
                        if asyncio.iscoroutinefunction(nlu_classifier.auto_retrain):
                            background_tasks.add_task(run_async, nlu_classifier.auto_retrain())
                        else:
                            background_tasks.add_task(nlu_classifier.auto_retrain)
        
        return {"status": "success", "message": "Feedback modtaget og gemt"}
        
    except Exception as e:
        logger.error(f"Fejl under håndtering af feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/training/status")
async def get_training_status():
    """Returnerer status for træningsdata og automatisk træning."""
    if nlu_classifier is None:
        raise HTTPException(status_code=503, detail="NLU-modul ikke tilgængeligt")
        
    try:
        new_examples = 0
        available_intents = []
        
        # Hent new_examples_count hvis attributten findes
        if hasattr(nlu_classifier, "new_examples_count"):
            if callable(getattr(nlu_classifier, "new_examples_count")):
                new_examples = nlu_classifier.new_examples_count()
            else:
                new_examples = nlu_classifier.new_examples_count
                
        # Hent available_intents hvis metoden findes
        if hasattr(nlu_classifier, "get_available_intents") and callable(nlu_classifier.get_available_intents):
            available_intents = nlu_classifier.get_available_intents()
        
        return {
            "new_examples": new_examples,
            "examples_until_retrain": max(0, RETRAIN_THRESHOLD - new_examples),
            "available_intents": available_intents
        }
    except Exception as e:
        logger.error(f"Fejl under hentning af træningsstatus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/force")
async def force_retrain(background_tasks: BackgroundTasks):
    """Tvinger en gentræning af modellen med alle tilgængelige data."""
    if nlu_classifier is None:
        raise HTTPException(status_code=503, detail="NLU-modul ikke tilgængeligt")
        
    try:
        if hasattr(nlu_classifier, "auto_retrain"):
            if asyncio.iscoroutinefunction(nlu_classifier.auto_retrain):
                background_tasks.add_task(nlu_classifier.auto_retrain)
            else:
                # Start en background task som kalder den synkrone funktion
                async def run_sync_retrain():
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, nlu_classifier.auto_retrain)
                
                background_tasks.add_task(run_sync_retrain)
        else:
            logger.warning("NLU classifier mangler auto_retrain metode")
            
        return {"status": "success", "message": "Gentræning startet"}
    except Exception as e:
        logger.error(f"Fejl under start af tvungen gentræning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Event loop håndtering
def run_async(coro):
    """Kører en coroutine i en event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Opdater Jarvis initialisering
def initialize_jarvis_wrapper():
    """Wrapper til at initialisere Jarvis med event loop håndtering"""
    try:
        return run_async(initialize_jarvis())
    except Exception as e:
        logger.error(f"Fejl under Jarvis initialisering: {e}")
        return False

JARVIS_INITIALIZED = initialize_jarvis_wrapper()

class JarvisController:
    """Kontroller klasse til at håndtere Jarvis' tilstand og WebSocket forbindelser"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.chat_history: List[Dict[str, str]] = []
        self._is_listening: bool = True
        self._lock = asyncio.Lock()
    
    async def register_websocket(self, websocket: WebSocket):
        """Registrerer en ny WebSocket forbindelse"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Ny WebSocket forbindelse registreret")
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "status": {
                "is_listening": self._is_listening,
                "core_available": JARVIS_CORE_AVAILABLE,
                "speech_available": True,
                "nlu_available": True
            }
        })
    
    def unregister_websocket(self, websocket: WebSocket):
        """Afregistrerer en WebSocket forbindelse"""
        self.active_connections.discard(websocket)
        logger.info("WebSocket forbindelse afregistreret")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Sender en besked til alle forbundne klienter"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Fejl under broadcast til klient: {e}")
                disconnected.add(connection)
        
        # Fjern døde forbindelser
        for conn in disconnected:
            self.unregister_websocket(conn)
    
    async def handle_audio_chunk(self, audio_data: bytes) -> None:
        """Håndterer et lydstykke fra WebSocket"""
        try:
            # Gem lyden midlertidigt
            temp_file = "temp_audio.webm"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transskriber lyden
            text = await speech_handler.transcribe_audio(temp_file)
            
            if text and text.strip():
                # Behandl teksten
                if process_input_text:
                    response = await process_input_text(text)
                    await self.add_chat_message(text, response)
                    
                    # Send svar til alle klienter
                    await self.broadcast({
                        "type": "transcription",
                        "text": text,
                        "response": response
                    })
                    
                    # Læs svaret højt hvis aktiveret
                    if self._is_listening and JARVIS_CORE_AVAILABLE:
                        await speech_handler.speak_text(response)
            
            # Ryd op
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error(f"Fejl under håndtering af lyddata: {e}")
            await self.broadcast({
                "type": "error",
                "message": "Kunne ikke behandle lydoptagelse"
            })

# Opret global controller instans
jarvis_controller = JarvisController()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket forbindelse til Jarvis"""
    await jarvis_controller.register_websocket(websocket)
    
    try:
        while True:
            # Modtag data fra klienten
            message = await websocket.receive()
            
            if message["type"] == "websocket.receive":
                if "text" in message:
                    # Håndter JSON beskeder
                    try:
                        data = json.loads(message["text"])
                        message_type = data.get("type", "")
                        
                        if message_type == "chat":
                            text = data.get("message", "").strip()
                            if text and process_input_text:
                                response = await process_input_text(text)
                                await jarvis_controller.add_chat_message(text, response)
                                await websocket.send_json({
                                    "type": "response",
                                    "message": response
                                })
                        
                        elif message_type == "status_request":
                            await websocket.send_json({
                                "type": "status",
                                "status": {
                                    "is_listening": jarvis_controller._is_listening,
                                    "core_available": JARVIS_CORE_AVAILABLE,
                                    "speech_available": True,
                                    "nlu_available": True
                                }
                            })
                        
                        elif message_type == "toggle_listening":
                            async with jarvis_controller._lock:
                                jarvis_controller._is_listening = not jarvis_controller._is_listening
                                await jarvis_controller.broadcast({
                                    "type": "status",
                                    "status": {
                                        "is_listening": jarvis_controller._is_listening
                                    }
                                })
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Ugyldig JSON besked modtaget")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Ugyldig besked-format"
                        })
                
                elif "bytes" in message:
                    # Håndter binære lyddata
                    await jarvis_controller.handle_audio_chunk(message["bytes"])
            
    except WebSocketDisconnect:
        jarvis_controller.unregister_websocket(websocket)
    except Exception as e:
        logger.error(f"WebSocket fejl: {e}")
        jarvis_controller.unregister_websocket(websocket)

# Tilføj efter app definition men før andre endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "core": JARVIS_CORE_AVAILABLE,
            "nlu": nlu_classifier is not None,
            "speech": hasattr(speech_handler, 'stt_model')
        }
    }
    return status

# Tilføj port argument håndtering i main
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()
    
    # Start serveren
    logger.info(f"Starter Jarvis API server på port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
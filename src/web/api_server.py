from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import json
import asyncio
from typing import Optional, Dict, Any, List

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konstanter
RETRAIN_THRESHOLD = 10
NLU_CONFIDENCE_THRESHOLD = 0.55

# Initialiser FastAPI app
app = FastAPI(title="Jarvis Web Interface")

# Opsæt stier til statiske filer og templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Fallback NLU klasse
class SimulatedNLUClassifier:
    async def predict(self, text: str) -> Dict[str, Any]:
        return {
            "intent": "simulated_intent",
            "confidence": 0.8
        }
    
    async def log_low_confidence(self, text: str, intent: str, confidence: float) -> None:
        logger.warning(f"Lav confidence ({confidence}) for tekst: {text}, intent: {intent}")

# Initialiser NLU
nlu_classifier = SimulatedNLUClassifier()

# WebSocket forbindelser
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Ny WebSocket forbindelse etableret")

    async def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket forbindelse lukket")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Fejl ved broadcast: {e}")
                disconnected.append(connection)
        
        # Fjern døde forbindelser
        for conn in disconnected:
            await self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, background_tasks: BackgroundTasks):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message["type"] == "user_message":
                    # Predict intent
                    prediction_dict = await nlu_classifier.predict(message["content"])
                    confidence = float(prediction_dict.get("confidence", 0.0))
                    predicted_intent = prediction_dict.get("intent", "unknown")

                    # Log lav confidence i baggrunden
                    if confidence < NLU_CONFIDENCE_THRESHOLD:
                        # Kør log_low_confidence direkte som async funktion
                        background_tasks.add_task(
                            nlu_classifier.log_low_confidence,
                            message["content"],
                            predicted_intent,
                            confidence
                        )

                    # Send svar
                    await manager.broadcast({
                        "type": "message",
                        "content": f"Forstået intent '{predicted_intent}' med {confidence:.2%} sikkerhed",
                        "nlu_data": {
                            "intent": predicted_intent,
                            "confidence": confidence
                        }
                    })

            except json.JSONDecodeError:
                logger.error("Ugyldig JSON modtaget")
                continue
            except Exception as e:
                logger.error(f"Fejl under message processing: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": "Der skete en fejl under behandling af beskeden"
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Uventet fejl i websocket handler: {e}")
        await manager.disconnect(websocket)

@app.get("/")
async def root(request):
    """Render hovedsiden"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/training")
async def training(request):
    """Render træningssiden"""
    return templates.TemplateResponse(
        "training.html",
        {"request": request}
    )

@app.get("/visualization")
async def visualization(request):
    """Render visualiseringssiden"""
    return templates.TemplateResponse(
        "visualization.html",
        {"request": request}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
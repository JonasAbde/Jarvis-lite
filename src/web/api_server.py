import sys
from pathlib import Path

# Tilføj parent directory til Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import json
from src.nlu.handler import NLUHandler
from src.llm.handler import LLMHandler

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser FastAPI app og handlers
app = FastAPI(title="Jarvis Web Interface")
nlu_handler = NLUHandler()
llm_handler = LLMHandler()

# Opsæt stier til statiske filer og templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# WebSocket forbindelser
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Ny bruger forbundet til chat")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Bruger afbrudt fra chat")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialiser LLM ved startup"""
    logger.info("Starter Jarvis system...")
    await llm_handler.initialize()
    logger.info("Jarvis er klar til at chatte!")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Modtag besked fra bruger
            data = await websocket.receive_text()
            
            # Send "skriver" status
            await websocket.send_json({
                "type": "status",
                "content": "Jarvis tænker..."
            })
            
            # Først tjek for simple intents via NLU
            nlu_result = nlu_handler.classify_intent(data)
            
            if nlu_result["confidence"] >= 0.7:
                # Brug NLU svar for simple intents
                response_data = {
                    "type": "message",
                    "content": nlu_result["response"],
                    "nlu_data": {
                        "confidence": nlu_result["confidence"],
                        "intent": nlu_result["intent"]
                    }
                }
            else:
                # Brug LLM for mere komplekse forespørgsler
                llm_result = await llm_handler.generate_response(data)
                response_data = {
                    "type": "message",
                    "content": llm_result["response"],
                    "nlu_data": {
                        "confidence": llm_result["confidence"],
                        "model_name": llm_result["model_name"],
                        "system_load": llm_result["system_load"]
                    }
                }
            
            # Send svar til bruger
            await websocket.send_json(response_data)
            
            # Gem samtalen efter hver interaktion
            llm_handler.save_conversation()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Gem samtalen når brugeren afbryder
        llm_handler.save_conversation()
    except Exception as e:
        logger.error(f"Fejl i chat: {e}")
        await websocket.send_json({
            "type": "error",
            "content": "Der opstod en fejl. Prøv venligst igen."
        })

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

@app.get("/status")
async def get_status():
    """Hent system status"""
    llm_status = llm_handler.get_status()
    return {
        "llm_status": llm_status,
        "is_ready": llm_status["is_initialized"]
    }

@app.post("/clear-conversation")
async def clear_conversation():
    """Ryd den nuværende samtale"""
    llm_handler.clear_conversation()
    return {"status": "success", "message": "Samtale ryddet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
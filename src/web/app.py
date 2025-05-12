from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import json

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser FastAPI app
app = FastAPI(title="Jarvis Web Interface")

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

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Her tilføjer vi logik til at håndtere forskellige beskeder
            await manager.broadcast(json.dumps({
                "type": "message",
                "content": data
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
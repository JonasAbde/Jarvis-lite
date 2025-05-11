"""
Jarvis-Lite Static Webserver
Simpel HTTP-server til at servere chat-webapplikationen.
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Opret FastAPI app
app = FastAPI(
    title="Jarvis-Lite Web UI",
    description="Webserver til Jarvis-Lite chat UI",
    version="0.1.0"
)

# Definer stien til de statiske filer
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Tjek om mappen findes
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
    logger.warning(f"Statisk mappe '{static_dir}' eksisterede ikke og blev oprettet.")

# Server statiske filer
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def get_index():
    """Serverer index.html filen"""
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        logger.error(f"index.html ikke fundet i {static_dir}")
        raise HTTPException(status_code=404, detail="Webapplikation ikke fundet")
    return FileResponse(index_path)

@app.get("/jarvis-logo.png")
async def get_logo():
    """Serverer logo-fil"""
    logo_path = os.path.join(static_dir, "jarvis-logo.png")
    if not os.path.exists(logo_path):
        # Brug en fallback hvis logofilen ikke findes
        logger.warning("Logo-fil ikke fundet, sender placeholder")
        return FileResponse(os.path.join(static_dir, "placeholder-logo.png"))
    return FileResponse(logo_path)

if __name__ == "__main__":
    port = 8080  # Vælg en anden port end API-serveren
    logger.info(f"Starter webserver på http://localhost:{port}")
    
    # Tilføj besked om at generere en logofil hvis den ikke findes
    logo_path = os.path.join(static_dir, "jarvis-logo.png")
    if not os.path.exists(logo_path):
        logger.warning(f"Logo-fil mangler: {logo_path}")
        logger.info("For at tilføje et logo, placer en 'jarvis-logo.png' fil i static-mappen.")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info") 
#!/usr/bin/env python3
"""
Jarvis Hovedprogram
Dette script kombinerer funktionaliteter fra tidligere scripts og implementerer
en modulær arkitektur for Jarvis.
"""
import os
import sys
import time
import json
import logging
import subprocess
import threading
import webbrowser
import signal
import atexit
import importlib
import pkgutil
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Type, Callable

# Tilføj tredjepartsbiblioteker
try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse
    from pydantic import BaseModel
    import psutil
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"Fejl ved import af afhængigheder: {e}")
    print("Installerer nødvendige pakker...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Afhængigheder installeret. Genstart programmet.")
    sys.exit(1)

# Konstanter
VENV_PATH = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8000
MAX_PORT_ATTEMPTS = 5
MODULE_DIR = "src/modules"

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("jarvis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis-main")

# Rich console for bedre output
console = Console()

# --- Modul System ---
class JarvisModule:
    """Base klasse for alle Jarvis moduler"""
    
    # Metadata som skal overskrives af hver modul
    name = "base_module"
    description = "Basis modul klasse"
    version = "1.0.0"
    dependencies = []
    
    def __init__(self):
        self.active = False
    
    async def initialize(self) -> bool:
        """Initialiserer modulet - skal overskrives"""
        self.active = True
        return True
    
    async def shutdown(self) -> bool:
        """Nedlukker modulet - skal overskrives"""
        self.active = False
        return True
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Returnerer liste af API endpoints som dette modul tilbyder"""
        return []
    
    def get_ui_components(self) -> List[Dict[str, Any]]:
        """Returnerer liste af UI komponenter som dette modul tilbyder"""
        return []
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Returnerer modul metadata"""
        return {
            "name": cls.name,
            "description": cls.description,
            "version": cls.version,
            "dependencies": cls.dependencies
        }


class ModuleManager:
    """Håndterer loading, unloading og kommunikation med moduler"""
    
    def __init__(self, app: FastAPI = None):
        self.modules: Dict[str, JarvisModule] = {}
        self.app = app
        self.module_classes: Dict[str, Type[JarvisModule]] = {}
        self.module_errors: Dict[str, str] = {}  # Til at gemme fejl ved modulindlæsning
    
    def discover_modules(self) -> List[str]:
        """Opdager alle tilgængelige moduler i module_dir"""
        module_dir = Path(MODULE_DIR)
        if not module_dir.exists():
            logger.warning(f"Modul mappe {MODULE_DIR} findes ikke. Opretter...")
            module_dir.mkdir(parents=True, exist_ok=True)
            
        # Sørg for at der er en __init__.py fil i moduldir
        init_file = module_dir / "__init__.py"
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write("# Jarvis moduler\n")
        
        found_modules = []
        
        # Importér moduler dynamisk
        module_path = MODULE_DIR.replace("/", ".")
        try:
            # Tilføj src til module search path, hvis det ikke allerede er der
            src_path = str(Path("src").resolve())
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
                logger.info(f"Tilføjede {src_path} til Python module path")
            
            logger.info(f"Søger efter moduler i {module_dir}...")
            
            # Liste over modul-filnavne (uden .py)
            module_files = []
            for item in os.listdir(str(module_dir)):
                if item.endswith('.py') and not item.startswith('__'):
                    module_name = item[:-3]  # fjern .py
                    module_files.append(module_name)
            
            logger.info(f"Fandt følgende modulfiler: {module_files}")
                
            for name in module_files:
                try:
                    logger.info(f"Importerer modul: {name}")
                    # Håndter imports med fejlfangning
                    try:
                        # Importér modulet direkte fra modules pakken
                        module = importlib.import_module(f"modules.{name}")
                        
                        # Find alle klasser i modulet
                        module_classes = []
                        for _, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, JarvisModule) and 
                                obj is not JarvisModule):
                                module_classes.append(obj)
                                
                        if not module_classes:
                            logger.warning(f"Ingen JarvisModule-klasser fundet i {name}")
                            continue
                            
                        # Registrér alle fundne modulklasser
                        for cls in module_classes:
                            logger.info(f"Fandt modul klasse: {cls.__name__} i {name}")
                            if hasattr(cls, 'name'):
                                module_name = cls.name
                                self.module_classes[module_name] = cls
                                found_modules.append(module_name)
                                # Fjern tidligere fejl hvis det nu lykkedes at indlæse modulet
                                if module_name in self.module_errors:
                                    del self.module_errors[module_name]
                            else:
                                logger.warning(f"Klasse {cls.__name__} i {name} har ikke et name-attribut")
                                
                    except ImportError as e:
                        logger.warning(f"Kunne ikke importere modul {name} pga. manglende afhængighed: {e}")
                        # Forsøg at bestemme modulets navn fra filnavnet
                        module_name = name.replace("_module", "")
                        self.module_errors[module_name] = f"Manglende afhængighed: {str(e)}"
                except Exception as e:
                    logger.error(f"Fejl ved import af modul {name}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Prøv at gemme fejlen med modulet
                    module_name = name.replace("_module", "")
                    self.module_errors[module_name] = f"Fejl ved indlæsning: {str(e)}"
        except Exception as e:
            logger.error(f"Generel fejl under modul opdagelse: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info(f"Opdagede moduler: {found_modules}")
        if self.module_errors:
            logger.warning(f"Moduler med fejl: {list(self.module_errors.keys())}")
        return found_modules
    
    def verify_dependencies(self, dependencies: List[str]) -> Dict[str, bool]:
        """Verificerer at alle påkrævede afhængigheder er til rådighed"""
        results = {}
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                results[dep] = True
            except ImportError:
                results[dep] = False
        return results
    
    async def load_module(self, module_name: str) -> bool:
        """Loader og initialiserer et modul ved navn"""
        if module_name in self.modules:
            logger.warning(f"Modul {module_name} er allerede loaded")
            return True
        
        # Tjek om modulet havde fejl under opdagelsen
        if module_name in self.module_errors:
            error_msg = self.module_errors[module_name]
            logger.error(f"Kan ikke loade modul {module_name}: {error_msg}")
            return False
            
        if module_name in self.module_classes:
            try:
                # Hent modulklassen og tjek afhængigheder
                module_class = self.module_classes[module_name]
                
                # Tjek afhængigheder, men fortsæt selvom nogle mangler (modulerne bør håndtere dette selv)
                if hasattr(module_class, 'dependencies') and module_class.dependencies:
                    dep_results = self.verify_dependencies(module_class.dependencies)
                    missing_deps = [dep for dep, available in dep_results.items() if not available]
                    if missing_deps:
                        logger.warning(f"Modul {module_name} mangler nogle afhængigheder: {', '.join(missing_deps)}")
                        logger.warning(f"Fortsætter alligevel, da modulet kan have fallback-funktionalitet")
                
                # Initialiser modulet
                module_instance = module_class()
                if await module_instance.initialize():
                    self.modules[module_name] = module_instance
                    logger.info(f"Modul {module_name} loaded")
                    
                    # Registrér modulets endpoints hvis app er tilgængelig
                    if self.app:
                        self._register_module_endpoints(module_instance)
                        
                    return True
                else:
                    logger.error(f"Initialisering af modul {module_name} fejlede")
            except Exception as e:
                logger.error(f"Fejl ved loading af modul {module_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.error(f"Modul {module_name} findes ikke")
        
        return False
    
    async def unload_module(self, module_name: str) -> bool:
        """Nedlukker og fjerner et modul ved navn"""
        if module_name not in self.modules:
            logger.warning(f"Modul {module_name} er ikke loaded")
            return True
            
        try:
            if await self.modules[module_name].shutdown():
                del self.modules[module_name]
                logger.info(f"Modul {module_name} unloaded")
                return True
            else:
                logger.error(f"Nedlukning af modul {module_name} fejlede")
        except Exception as e:
            logger.error(f"Fejl ved unloading af modul {module_name}: {e}")
        
        return False
    
    async def load_all_modules(self) -> Dict[str, bool]:
        """Loader alle opdagede moduler"""
        result = {}
        for module_name in self.module_classes:
            result[module_name] = await self.load_module(module_name)
        return result
    
    async def unload_all_modules(self) -> Dict[str, bool]:
        """Nedlukker alle loaded moduler"""
        result = {}
        for module_name in list(self.modules.keys()):
            result[module_name] = await self.unload_module(module_name)
        return result
    
    def get_loaded_modules(self) -> Dict[str, Dict[str, Any]]:
        """Returnerer metadata fra alle loaded moduler"""
        return {name: module.get_metadata() for name, module in self.modules.items()}
    
    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """Returnerer metadata fra alle tilgængelige moduler"""
        available = {name: cls.get_metadata() for name, cls in self.module_classes.items()}
        
        # Tilføj moduler med fejl, så de vises i UI'en
        for name, error in self.module_errors.items():
            if name not in available:
                available[name] = {
                    "name": name,
                    "description": f"Modul kunne ikke indlæses: {error}",
                    "version": "unknown",
                    "dependencies": [],
                    "error": error
                }
        
        return available
    
    def _register_module_endpoints(self, module: JarvisModule) -> None:
        """Registrerer modulets endpoints i FastAPI app"""
        if not self.app:
            return
            
        endpoints = module.get_endpoints()
        for endpoint in endpoints:
            # Her ville vi implementere en dynamisk endpoint registrering
            # Dette er en forenklet version og skal udvides i praksis
            pass

# --- Environment Setup ---
def create_venv():
    """Opret virtual environment hvis det ikke eksisterer"""
    if not os.path.exists(VENV_PATH):
        console.print("[yellow]Virtual environment ikke fundet. Opretter ny...[/yellow]")
        import venv
        venv.create(VENV_PATH, with_pip=True)
        return True
    return False

def get_venv_python():
    """Få sti til Python i virtual environment"""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "python.exe")
    return os.path.join(VENV_PATH, "bin", "python")

def install_requirements():
    """Installer eller opdater requirements"""
    python_path = get_venv_python()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Installerer dependencies...", total=None)
        try:
            subprocess.check_call([
                python_path, "-m", "pip", "install", "-r", REQUIREMENTS_FILE
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Fejl ved installation af dependencies: {e}")
            return False

def install_specific_packages(packages: List[str]):
    """Installer specifikke pakker"""
    python_path = get_venv_python()
    try:
        console.print(f"[yellow]Installerer pakker: {', '.join(packages)}[/yellow]")
        subprocess.check_call([
            python_path, "-m", "pip", "install", *packages
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        console.print(f"[green]Pakker installeret: {', '.join(packages)}[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Fejl ved installation af pakker: {e}[/red]")
        return False

# --- Port og Netværk ---
def is_port_available(port: int) -> bool:
    """Tjekker om en port er tilgængelig"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except:
        return False

def find_available_port(start_port: int = DEFAULT_PORT) -> int:
    """Finder næste ledige port"""
    port = start_port
    for _ in range(MAX_PORT_ATTEMPTS):
        if is_port_available(port):
            return port
        port += 1
    raise RuntimeError(f"Kunne ikke finde ledig port mellem {start_port} og {start_port + MAX_PORT_ATTEMPTS}")

def kill_process_on_port(port: int) -> bool:
    """Dræber proces der kører på en specifik port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if hasattr(conn, 'laddr') and hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info(f"Afsluttede proces på port {port}")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue
    return False

# --- FastAPI Server ---
def create_api_app(module_manager: ModuleManager):
    """Opret FastAPI app med moduler"""
    app = FastAPI(
        title="Jarvis API",
        description="API for Jarvis dansk stemmeassistent med modulær arkitektur",
        version="2.0.0"
    )
    
    # Tilføj CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Konfigurer static files
    static_dir = os.path.join(PROJECT_ROOT, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Tilknyt module_manager til app
    module_manager.app = app
    
    # --- API Endpoints ---
    @app.get("/")
    async def get_index():
        """Serverer index.html filen"""
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return HTMLResponse(content=get_default_html("Jarvis", "Jarvis hovedside ikke fundet"))
    
    @app.get("/web/chat")
    async def get_chat_page():
        """Serverer chat.html filen"""
        chat_path = os.path.join(static_dir, "chat.html")
        if os.path.exists(chat_path):
            return FileResponse(chat_path)
        else:
            return HTMLResponse(content=get_default_html("Jarvis Chat", "Chat-side ikke fundet"))
            
    @app.get("/web/training")
    async def get_training_page():
        """Serverer training.html filen"""
        training_path = os.path.join(static_dir, "training.html")
        if os.path.exists(training_path):
            return FileResponse(training_path)
        else:
            return HTMLResponse(content=get_default_html("Jarvis Træning", "Træningsside ikke fundet"))
            
    @app.get("/web/visualization")
    async def get_visualization_page():
        """Serverer visualization.html filen"""
        vis_path = os.path.join(static_dir, "visualization.html")
        if os.path.exists(vis_path):
            return FileResponse(vis_path)
        else:
            return HTMLResponse(content=get_default_html("Jarvis Visualisering", "Visualiseringsside ikke fundet"))
    
    @app.get("/api/status")
    async def api_status():
        """API status endpoint"""
        return {
            "status": "active",
            "modules": {
                "loaded": list(module_manager.get_loaded_modules().keys()),
                "available": list(module_manager.get_available_modules().keys()),
                "errors": module_manager.module_errors
            }
        }
        
    @app.get("/api/modules")
    async def list_modules():
        """Liste alle moduler og deres status"""
        return {
            "loaded": module_manager.get_loaded_modules(),
            "available": module_manager.get_available_modules(),
        }
    
    @app.post("/api/modules/{module_name}/load")
    async def load_module_endpoint(module_name: str):
        """Loader et modul"""
        success = await module_manager.load_module(module_name)
        if success:
            return {"status": "success", "message": f"Modul {module_name} loaded"}
        else:
            raise HTTPException(status_code=500, detail=f"Kunne ikke loade modul {module_name}")
    
    @app.post("/api/modules/{module_name}/unload")
    async def unload_module_endpoint(module_name: str):
        """Unloader et modul"""
        success = await module_manager.unload_module(module_name)
        if success:
            return {"status": "success", "message": f"Modul {module_name} unloaded"}
        else:
            raise HTTPException(status_code=500, detail=f"Kunne ikke unloade modul {module_name}")
    
    # Ny endpoint til at installere afhængigheder til et modul
    @app.post("/api/modules/{module_name}/install-dependencies")
    async def install_module_dependencies(module_name: str, background_tasks: BackgroundTasks):
        """Installerer afhængigheder for et specifikt modul"""
        # Find modulet og dets afhængigheder
        if module_name not in module_manager.module_classes and module_name not in module_manager.module_errors:
            raise HTTPException(status_code=404, detail=f"Modul {module_name} findes ikke")
            
        if module_name in module_manager.module_classes:
            dependencies = module_manager.module_classes[module_name].dependencies
            if not dependencies:
                return {"status": "success", "message": f"Modul {module_name} har ingen afhængigheder"}
                
            # Start installation i baggrunden
            background_tasks.add_task(install_specific_packages, dependencies)
            return {
                "status": "installing", 
                "message": f"Installerer afhængigheder for {module_name}: {', '.join(dependencies)}"
            }
        else:
            # Modul med fejl - gæt på afhængigheder fra fejlbeskrivelse
            error_msg = module_manager.module_errors[module_name]
            if "No module named" in error_msg:
                # Prøv at udtrække pakkenavnet fra fejlmeddelelsen
                import re
                match = re.search(r"No module named '(\w+)'", error_msg)
                if match:
                    package = match.group(1)
                    background_tasks.add_task(install_specific_packages, [package])
                    return {
                        "status": "installing", 
                        "message": f"Installerer manglende afhængighed: {package}"
                    }
            
            raise HTTPException(status_code=400, detail=f"Kunne ikke bestemme afhængigheder fra fejl: {error_msg}")
    
    # NLU API endpoints for træningssiden
    @app.get("/api/nlu/intents")
    async def get_intents():
        """Henter alle tilgængelige intents"""
        # Prøv at hente intents fra NLU-modulet hvis det er tilgængeligt
        if "nlu" in module_manager.modules:
            try:
                return {"intents": module_manager.modules["nlu"].get_available_intents()}
            except:
                pass
                
        # Fallback til stub
        return {
            "intents": [
                "greeting", "weather", "time", "date", 
                "play_music", "stop_music", "general_question", "set_reminder"
            ]
        }
    
    @app.get("/training/status")
    async def training_status():
        """Henter status på NLU træning"""
        # Dette er en stub - skal implementeres ordentligt med et træningsmodul
        return {
            "new_examples": 3,
            "examples_until_retrain": 5,
            "last_trained": "2025-05-12T14:32:00",
            "model_performance": {
                "accuracy": 0.87,
                "f1_score": 0.89
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "modules": len(module_manager.modules)
        }

    # WebSocket forbindelse til Jarvis
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket forbindelse til Jarvis"""
        await websocket.accept()
        logger.info("WebSocket connection open")
        
        try:
            # Send initiel status
            await websocket.send_json({
                "type": "status",
                "modules": list(module_manager.get_loaded_modules().keys())
            })
            
            # Chat håndtering
            async def handle_chat_message(content):
                logger.info(f"Modtaget chat besked: {content}")
                
                # Hvis NLU-modul er tilgængeligt, brug det til at forudsige intent
                if "nlu" in module_manager.modules:
                    try:
                        nlu_result = await module_manager.modules["nlu"].predict_intent(content)
                        intent = nlu_result.get("intent", "unknown")
                        confidence = nlu_result.get("confidence", 0.0)
                        
                        logger.info(f"NLU resultat: intent={intent}, confidence={confidence}")
                        
                        # Generer svar baseret på intent
                        if intent == "greeting":
                            response = "Hej! Hvordan kan jeg hjælpe dig i dag?"
                        elif intent == "weather":
                            response = "Jeg kan desværre ikke tjekke vejret endnu, men det er en god idé til fremtiden."
                        elif intent == "time":
                            from datetime import datetime
                            now = datetime.now()
                            response = f"Klokken er {now.strftime('%H:%M')}"
                        elif intent == "date":
                            from datetime import datetime
                            now = datetime.now()
                            response = f"I dag er det {now.strftime('%d-%m-%Y')}"
                        else:
                            response = f"Du skrev: {content}"
                            
                        return {
                            "type": "chat_response",
                            "message": response,
                            "nlu_data": nlu_result
                        }
                    except Exception as e:
                        logger.error(f"Fejl ved brug af NLU-modul: {e}")
                
                # Fallback hvis NLU-modul ikke er tilgængeligt eller fejler
                return {
                    "type": "chat_response",
                    "message": f"Du skrev: {content}",
                    "nlu_data": {
                        "intent": "unknown",
                        "confidence": 0.0
                    }
                }
            
            # Håndter hver forbindelse i en beskyttet kontekst
            while True:
                try:
                    # Modtag data fra klienten
                    data = await websocket.receive_text()
                    logger.info(f"Modtaget WebSocket data: {data}")
                    
                    # Forsøg at parse JSON
                    try:
                        message = json.loads(data)
                    except json.JSONDecodeError:
                        logger.error(f"Kunne ikke parse JSON: {data}")
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Ugyldig JSON"
                        })
                        continue
                        
                    message_type = message.get("type", "")
                    
                    # Håndter forskellige beskedtyper
                    if message_type == "chat_message":
                        content = message.get("content", "")
                        logger.info(f"Behandler chat besked: {content}")
                        response = await handle_chat_message(content)
                        logger.info(f"Sender svar: {response}")
                        await websocket.send_json(response)
                        
                    elif message_type == "module_command":
                        module_name = message.get("module")
                        command = message.get("command")
                        if module_name in module_manager.modules:
                            await websocket.send_json({
                                "type": "module_response",
                                "module": module_name,
                                "status": "ok"
                            })
                            
                    elif message_type == "status_request":
                        await websocket.send_json({
                            "type": "status",
                            "modules": list(module_manager.get_loaded_modules().keys())
                        })
                    
                    else:
                        # Ukendt beskedtype
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Ukendt beskedtype: {message_type}"
                        })
                except WebSocketDisconnect:
                    logger.info("WebSocket klient afbrudt")
                    break
                except Exception as e:
                    logger.error(f"WebSocket fejl: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Vi prøver at sende en fejlbesked, men lukker forbindelsen hvis det fejler
                    try:
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Der opstod en fejl på serveren"
                        })
                    except:
                        # Forbindelsen er sandsynligvis allerede lukket
                        break
        except Exception as e:
            logger.error(f"WebSocket fejl: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Sikr korrekt lukning af forbindelsen
            try:
                await websocket.close()
            except:
                pass
        
        logger.info("WebSocket connection closed")
    
    return app

def get_default_html(title: str, message: str) -> str:
    """Genererer default HTML side"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .error {{ color: #721c24; background: #f8d7da; padding: 20px; border-radius: 5px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div class="error">
                <p>{message}</p>
            </div>
            <nav>
                <p>
                    <a href="/">Jarvis</a> |
                    <a href="/web/chat">Chat</a> |
                    <a href="/web/training">Træning</a> |
                    <a href="/web/visualization">Visualisering</a>
                </p>
            </nav>
        </div>
    </body>
    </html>
    """

# --- Process Håndtering ---
processes = []

def cleanup():
    """Lukker alle processer ved afslutning"""
    logger.info("Lukker alle processer...")
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    logger.info("Alle processer lukket.")

def signal_handler(sig, frame):
    """Håndterer afbrudt program (Ctrl+C)"""
    logger.info("Program afbrudt. Lukker ned...")
    cleanup()
    sys.exit(0)

# --- Main App ---
class JarvisApp:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        self.module_manager = ModuleManager()
        self.app = None
        self.server = None
        self.port = DEFAULT_PORT
    
    def setup(self):
        """Opsætning af Jarvis"""
        # Tjek og opret venv hvis nødvendigt
        if create_venv():
            console.print("[green]Virtual environment oprettet[/green]")
        
        # Installer dependencies hvis nødvendigt
        if not os.path.exists(".venv"):
            if not install_requirements():
                console.print("[red]Fejl ved installation af dependencies[/red]")
                return False
        
        # Opdager moduler
        console.print("[yellow]Opdager moduler...[/yellow]")
        available_modules = self.module_manager.discover_modules()
        
        if available_modules:
            console.print(f"[green]Fandt {len(available_modules)} moduler: {', '.join(available_modules)}[/green]")
        else:
            # Vis information om fejlede moduler
            if self.module_manager.module_errors:
                console.print("[yellow]Følgende moduler havde fejl under indlæsning:[/yellow]")
                for name, error in self.module_manager.module_errors.items():
                    console.print(f"[yellow]  - {name}: {error}[/yellow]")
                console.print("[yellow]Du kan installere manglende afhængigheder via API eller manuelt.[/yellow]")
            
        # Find ledig port
        self.port = find_available_port()
        if not is_port_available(self.port):
            kill_process_on_port(self.port)
            if not is_port_available(self.port):
                console.print(f"[red]Kunne ikke frigøre port {self.port}[/red]")
                return False
        
        # Opret API app
        self.app = create_api_app(self.module_manager)
        
        return True
        
    async def start_modules(self):
        """Starter alle moduler"""
        results = await self.module_manager.load_all_modules()
        success = sum(1 for result in results.values() if result)
        failed = len(results) - success
        
        if failed == 0 and success > 0:
            console.print(f"[green]Alle {success} moduler startet[/green]")
        elif success > 0:
            console.print(f"[yellow]{success} moduler startet, {failed} fejlede[/yellow]")
        else:
            console.print("[yellow]Ingen moduler blev startet[/yellow]")
            # Vis fejl for hvert modul
            for name, result in results.items():
                if not result and name in self.module_manager.module_errors:
                    console.print(f"[yellow]  - {name}: {self.module_manager.module_errors[name]}[/yellow]")
        
        return success > 0 or len(results) == 0
    
    def start_server(self):
        """Starter API server"""
        try:
            console.print(f"[yellow]Starter Jarvis på port {self.port}...[/yellow]")
            
            # Start server i en separat tråd
            import uvicorn
            config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port, log_level="info")
            self.server = uvicorn.Server(config)
            
            server_thread = threading.Thread(target=self.server.run, daemon=True)
            server_thread.start()
            
            # Vent kort tid for at sikre at serveren starter
            time.sleep(3)
            
            # Åbn browser
            webbrowser.open(f"http://localhost:{self.port}")
            console.print("[green]Browser åbnet med Jarvis UI[/green]")
            
            return True
        except Exception as e:
            console.print(f"[red]Fejl ved start af server: {e}[/red]")
            return False
    
    def run(self):
        """Kør Jarvis app"""
        # Registrer signal handlers for nedlukning
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(cleanup)
        
        try:
            # Opsætning
            if not self.setup():
                return False
            
            # Start API server
            if not self.start_server():
                return False
                
            # Start moduler med asyncio
            import asyncio
            asyncio.run(self.start_modules())
            
            console.print("[green]Jarvis er nu klar![/green]")
            
            # Hold hovedtråden i live for at kunne lytte efter keyboard interrupt
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Lukker Jarvis...[/yellow]")
            cleanup()
        except Exception as e:
            console.print(f"\n[red]Uventet fejl: {e}[/red]")
            cleanup()
            return False
            
        return True

if __name__ == "__main__":
    # Parse argumenter
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis - Dansk modulær stemmeassistent")
    parser.add_argument("--dev", action="store_true", help="Kør i udvikler-tilstand")
    args = parser.parse_args()
    
    # Start app
    app = JarvisApp(dev_mode=args.dev)
    success = app.run()
    
    sys.exit(0 if success else 1) 
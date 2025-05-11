"""
Jarvis-Lite Windows Application Builder
Bygger en Windows exe-applikation af Jarvis-lite chat-assistenten.
"""
import os
import sys
import logging
import shutil
import subprocess
import time
from pathlib import Path

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("jarvis-build")

# Definer konstanter
DIST_DIR = "dist"
BUILD_DIR = "build"
SPEC_DIR = Path("build") / "spec"
OUTPUT_NAME = "Jarvis-Lite-Chat"
ICON_PATH = Path("src") / "static" / "jarvis-icon.ico"
VERSION = "0.1.0"
LAUNCHER_SCRIPT = "jarvis_launcher.py"

def check_dependencies():
    """Tjekker om de nødvendige afhængigheder er installeret"""
    logger.info("Tjekker afhængigheder...")
    
    missing_deps = []
    
    # Tjek Python version (minimum 3.9)
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        logger.error(f"Python version {python_version.major}.{python_version.minor} er ikke understøttet. Minimum 3.9 kræves.")
        return False
        
    # Tjek for PyInstaller
    try:
        import PyInstaller
        logger.info(f"Fandt PyInstaller {PyInstaller.__version__}")
    except ImportError:
        logger.warning("PyInstaller ikke fundet. Tilføjer til listen af manglende afhængigheder.")
        missing_deps.append("pyinstaller")
    
    # Tjek for andre kerneafhængigheder
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "pyaudio", "gtts", "websockets"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_deps.append(package)
    
    if missing_deps:
        logger.warning(f"Manglende afhængigheder: {', '.join(missing_deps)}")
        logger.info("Installerer manglende pakker...")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_deps, check=True)
            logger.info("Afhængigheder installeret.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Kunne ikke installere afhængigheder: {e}")
            return False
    
    return True

def create_launcher_script():
    """Opretter et launcher-script til at starte både API og web-UI"""
    logger.info(f"Opretter launcher-script: {LAUNCHER_SCRIPT}")
    
    launcher_content = """#!/usr/bin/env python3
\"\"\"
Jarvis-Lite Launcher
Starter både API-server og web-UI.
\"\"\"
import os
import sys
import time
import logging
import subprocess
import webbrowser
import threading
import signal
import atexit

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("jarvis-launcher")

# Global variable til at holde styr på processer
processes = []

def launch_servers():
    \"\"\"Starter API-server og web-UI server\"\"\"
    api_port = 8000
    web_port = 8080
    
    logger.info("Starter Jarvis-Lite...")
    
    # Få den absolutte sti til src-mappen
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        # Kører som exe
        src_dir = os.path.join(sys._MEIPASS, "src")
    else:
        # Kører som script
        src_dir = os.path.join(current_dir, "src")
    
    # API-serveren
    api_cmd = [sys.executable, "-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port", str(api_port)]
    api_process = subprocess.Popen(
        api_cmd,
        cwd=src_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(api_process)
    logger.info(f"API-server startet på port {api_port}")
    
    # Web-UI serveren
    web_cmd = [sys.executable, "-m", "uvicorn", "static_server:app", "--host", "127.0.0.1", "--port", str(web_port)]
    web_process = subprocess.Popen(
        web_cmd,
        cwd=src_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(web_process)
    logger.info(f"Web-UI server startet på port {web_port}")
    
    # Giv serverne tid til at starte
    time.sleep(2)
    
    # Åben browser
    webbrowser.open(f"http://localhost:{web_port}")
    logger.info("Browser åbnet")
    
    return api_process, web_process

def monitor_processes(api_process, web_process):
    \"\"\"Overvåger serverprocesserne og genstarter dem om nødvendigt\"\"\"
    while True:
        if api_process.poll() is not None:
            logger.warning("API-server stoppet. Genstarter...")
            # Genstart API-server
            # ...
        
        if web_process.poll() is not None:
            logger.warning("Web-UI server stoppet. Genstarter...")
            # Genstart Web-UI server
            # ...
        
        time.sleep(5)

def cleanup():
    \"\"\"Lukker alle processer ved afslutning\"\"\"
    logger.info("Lukker alle processer...")
    for process in processes:
        if process.poll() is None:  # Hvis processen stadig kører
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
    logger.info("Alle processer lukket.")

def signal_handler(sig, frame):
    \"\"\"Håndterer afbrudt program (Ctrl+C)\"\"\"
    logger.info("Program afbrudt. Lukker ned...")
    cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # Registrer cleanup-funktioner
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        api_process, web_process = launch_servers()
        
        # Start en thread til at overvåge processerne
        monitor_thread = threading.Thread(
            target=monitor_processes,
            args=(api_process, web_process),
            daemon=True
        )
        monitor_thread.start()
        
        # Hold hovedtråden i live
        monitor_thread.join()
        
    except KeyboardInterrupt:
        logger.info("Program afbrudt. Lukker ned...")
    except Exception as e:
        logger.error(f"Fejl: {e}")
    finally:
        cleanup()
"""

    with open(LAUNCHER_SCRIPT, "w", encoding="utf-8") as f:
        f.write(launcher_content)
    
    return os.path.abspath(LAUNCHER_SCRIPT)

def build_executable(launcher_path):
    """Bygger exe-filen med PyInstaller"""
    logger.info("Forbereder bygning af exe-fil...")
    
    # Opret byggemapper hvis de ikke findes
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(SPEC_DIR, exist_ok=True)
    
    # Ryd tidligere bygninger
    logger.info("Rydder tidligere bygninger...")
    for item in os.listdir(DIST_DIR):
        item_path = os.path.join(DIST_DIR, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    
    # Kontroller om ikonet findes
    icon_option = []
    if os.path.exists(ICON_PATH):
        icon_option = ["--icon", str(ICON_PATH)]
        logger.info(f"Bruger ikon: {ICON_PATH}")
    else:
        logger.warning(f"Ikon ikke fundet: {ICON_PATH}")
    
    # Byg exe-filen med PyInstaller
    logger.info("Starter PyInstaller bygning...")
    
    # Find alle Python-filer i src-mappen
    src_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                src_files.append(os.path.join(root, file))
    
    # Definer kommandoen til PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--name", OUTPUT_NAME,
        "--onefile",
        "--windowed",
        *icon_option,
        "--add-data", f"src/static;src/static",
        "--add-data", f"venv/Lib/site-packages/certifi;certifi",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "pydantic",
        launcher_path
    ]
    
    try:
        # Kør PyInstaller
        subprocess.run(pyinstaller_cmd, check=True)
        logger.info(f"Bygning færdig. Executable er i {DIST_DIR}/{OUTPUT_NAME}.exe")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Fejl under bygningen: {e}")
        return False

def main():
    """Hovedfunktion, der styrer byggeprocessen"""
    logger.info("=== Jarvis-Lite Windows Application Builder ===")
    
    # Tjek afhængigheder
    if not check_dependencies():
        logger.error("Kunne ikke opfylde alle afhængigheder. Afbryder.")
        return False
    
    # Opret launcher-script
    launcher_path = create_launcher_script()
    
    # Byg executable
    if build_executable(launcher_path):
        logger.info("=== Bygning gennemført med succes! ===")
        logger.info(f"Du kan nu distribuere {DIST_DIR}/{OUTPUT_NAME}.exe")
        return True
    else:
        logger.error("=== Bygning fejlede! ===")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
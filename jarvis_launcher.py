#!/usr/bin/env python3
"""
Jarvis-Lite Launcher
Starter Jarvis-Lite API-serveren med moderne webinterface.
"""
import os
import sys
import time
import logging
import subprocess
import webbrowser
import threading
import signal
import atexit
import socket
import argparse
import requests
from typing import Optional, Tuple, Dict, Any, List
import psutil
from pathlib import Path

# Konfigurer logging med fil output
log_file = "jarvis.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis-launcher")

# Globale variabler
processes = []
DEFAULT_PORT = 8000
MAX_PORT_ATTEMPTS = 5
HEALTH_CHECK_INTERVAL = 5  # sekunder
STARTUP_TIMEOUT = 120  # sekunder

def is_port_available(port: int) -> bool:
    """Tjekker om en port er tilgængelig"""
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

def check_and_install_dependencies() -> Tuple[bool, str]:
    """Tjekker og installerer manglende dependencies"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'psutil',
        'transformers',
        'torch',
        'numpy',
        'nltk',
        'python-multipart',
        'pydantic',
        'accelerate'  # Tilføjet accelerate som er nødvendig for device_map
    ]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.info(f"Installerer manglende packages: {', '.join(missing)}")
        try:
            for package in missing:
                logger.info(f"Installerer {package}...")
                # Brug encoding og errors parameter for at undgå codec-fejl
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            
            # Særlig håndtering for nltk data
            if 'nltk' in missing:
                logger.info("Downloader nødvendig NLTK data...")
                import nltk
                nltk.download('punkt')
                nltk.download('averaged_perceptron_tagger')
                
            return True, "Alle dependencies er nu installeret"
        except Exception as e:
            return False, f"Kunne ikke installere dependencies: {str(e)}"
    
    return True, "Alle dependencies er allerede installeret"

def check_virtual_env() -> bool:
    """Tjekker om vi kører i et virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def health_check(port: int) -> bool:
    """Udfører health check på API serveren"""
    try:
        response = requests.get(f"http://localhost:{port}/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def kill_process_on_port(port: int) -> None:
    """Dræber proces der kører på en specifik port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if hasattr(conn, 'laddr') and hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info(f"Afsluttede proces på port {port}")
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

def parse_args() -> Dict[str, Any]:
    """Parse command line argumenter og returner en dictionary med værdier"""
    parser = argparse.ArgumentParser(description="Start Jarvis med konfigurerede indstillinger")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for API server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for API server")
    parser.add_argument("--model", type=str, default="facebook/opt-125m", help="LLM model navn")
    parser.add_argument("--device", type=str, default="cpu", help="Device for model (cpu eller cuda)")
    parser.add_argument("--offline", action="store_true", help="Kør uden LLM (offline mode)")
    parser.add_argument("--no-browser", action="store_true", help="Start ikke browser automatisk")
    
    return vars(parser.parse_args())

def build_api_command(api_server_path: Path, port: int, cli_args: Dict[str, Any]) -> List[str]:
    """Opbygger kommandoen til at starte API-serveren med alle argumenter"""
    cmd = [
        sys.executable,
        str(api_server_path),
        "--port", str(port)
    ]
    
    # Tilføj model hvis angivet
    if "model" in cli_args:
        cmd.extend(["--model", cli_args["model"]])
    
    # Tilføj device hvis angivet
    if "device" in cli_args:
        cmd.extend(["--device", cli_args["device"]])
    
    # Tilføj offline mode hvis aktiveret
    if cli_args.get("offline", False):
        cmd.append("--offline")
    
    # Tilføj host hvis angivet
    if "host" in cli_args and cli_args["host"] != "0.0.0.0":
        cmd.extend(["--host", cli_args["host"]])
        
    return cmd

def launch_server(cli_args: Dict[str, Any]) -> Tuple[Optional[subprocess.Popen], int]:
    """Starter Jarvis-Lite API-server"""
    # Tjek virtual environment
    if not check_virtual_env():
        raise RuntimeError("Jarvis skal køres i et virtual environment. Aktiver det først med: .\\venv\\Scripts\\activate")
    
    # Tjek og installer dependencies
    deps_ok, deps_msg = check_and_install_dependencies()
    if not deps_ok:
        raise RuntimeError(deps_msg)
    else:
        logger.info(deps_msg)
    
    # Find ledig port
    port = cli_args.get("port", DEFAULT_PORT)
    if not is_port_available(port):
        kill_process_on_port(port)
        if not is_port_available(port):
            port = find_available_port(port + 1)
            logger.info(f"Port {cli_args.get('port')} ikke tilgængelig, bruger port {port} i stedet")
    
    logger.info(f"Starter Jarvis-Lite på port {port}...")
    
    # Få den absolutte sti til api_server.py
    current_dir = Path(__file__).resolve().parent
    api_server_path = current_dir / "api_server.py"
    
    if not api_server_path.exists():
        raise RuntimeError(f"Kunne ikke finde api_server.py på stien: {api_server_path}")
    
    # Byg kommandoen med alle argumenter
    api_cmd = build_api_command(api_server_path, port, cli_args)
    
    # Opret log filer med korrekt encoding
    stdout_log = open("api_server_out.log", "w", encoding="utf-8")
    stderr_log = open("api_server_err.log", "w", encoding="utf-8")
    
    try:
        # Tilføj src til Python path
        env = os.environ.copy()
        env["PYTHONPATH"] = str(current_dir)
        
        # Start processen med korrekt encoding
        api_process = subprocess.Popen(
            api_cmd,
            stdout=stdout_log,
            stderr=stderr_log,
            text=True,
            env=env
        )
        processes.append(api_process)
        
        # Vent på at serveren starter
        start_time = time.time()
        while time.time() - start_time < STARTUP_TIMEOUT:
            if api_process.poll() is not None:
                stdout_log.close()
                stderr_log.close()
                
                with open("api_server_out.log", "r", encoding="utf-8", errors="replace") as f:
                    stdout = f.read()
                with open("api_server_err.log", "r", encoding="utf-8", errors="replace") as f:
                    stderr = f.read()
                    
                logger.error(f"API server stoppede uventet. Stdout:\n{stdout}\nStderr:\n{stderr}")
                raise RuntimeError("API server stoppede uventet")
                
            if health_check(port):
                logger.info(f"API-server startet og kører på port {port}")
                return api_process, port
            time.sleep(1)
        
        # Hvis vi når hertil, er serveren ikke startet korrekt
        stdout_log.close()
        stderr_log.close()
        
        with open("api_server_out.log", "r", encoding="utf-8", errors="replace") as f:
            stdout = f.read()
        with open("api_server_err.log", "r", encoding="utf-8", errors="replace") as f:
            stderr = f.read()
            
        logger.error(f"API server timeout. Stdout:\n{stdout}\nStderr:\n{stderr}")
        
        api_process.terminate()
        raise RuntimeError(f"API-server startede ikke inden for {STARTUP_TIMEOUT} sekunder")
        
    except Exception as e:
        stdout_log.close()
        stderr_log.close()
        if 'api_process' in locals() and api_process and api_process.poll() is None:
            api_process.terminate()
        raise RuntimeError(f"Fejl under opstart af server: {str(e)}")

def monitor_process(api_process: subprocess.Popen, port: int, cli_args: Dict[str, Any]) -> None:
    """Overvåger serverprocessen og genstarter den om nødvendigt"""
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        try:
            # Tjek proces status
            if api_process.poll() is not None:
                logger.warning("API-server stoppet uventet.")
                raise RuntimeError("Server proces stoppet")
            
            # Udfør health check
            if not health_check(port):
                logger.warning("Health check fejlede")
                raise RuntimeError("Health check fejlede")
            
            # Reset fejltæller ved succesfuld kørsel
            consecutive_failures = 0
            time.sleep(HEALTH_CHECK_INTERVAL)
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"Fejl i server monitoring: {e}")
            
            if consecutive_failures >= max_failures:
                logger.critical(f"For mange fejl ({consecutive_failures}). Genstarter komplet...")
                cleanup()
                try:
                    api_process, port = launch_server(cli_args)
                    consecutive_failures = 0
                except Exception as restart_error:
                    logger.critical(f"Kunne ikke genstarte server: {restart_error}")
                    raise SystemExit(1)
            
            time.sleep(HEALTH_CHECK_INTERVAL)

def cleanup() -> None:
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

if __name__ == "__main__":
    # Registrer cleanup-funktioner
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line argumenter
    cli_args = parse_args()
    
    try:
        # Tjek om virtual environment er aktiveret
        if not check_virtual_env():
            print("FEJL: Jarvis skal køres i et virtual environment.")
            print("Kør følgende kommandoer:")
            print("1. .\\venv\\Scripts\\activate")
            print("2. python jarvis_launcher.py")
            sys.exit(1)
        
        # Start server
        api_process, port = launch_server(cli_args)
        
        # Åbn browser medmindre det er fravalgt
        if not cli_args.get("no_browser", False):
            webbrowser.open(f"http://localhost:{port}")
            logger.info("Browser åbnet med Jarvis-Lite UI")
        
        # Start monitoring
        monitor_thread = threading.Thread(
            target=monitor_process,
            args=(api_process, port, cli_args),
            daemon=True
        )
        monitor_thread.start()
        
        # Hold hovedtråden i live og håndter fejl
        try:
            monitor_thread.join()
        except KeyboardInterrupt:
            logger.info("Program afbrudt af bruger")
        except Exception as e:
            logger.error(f"Uventet fejl i hovedtråd: {e}")
        finally:
            cleanup()
            
    except Exception as e:
        logger.critical(f"Kritisk fejl under opstart: {e}")
        cleanup()
        sys.exit(1)

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
import requests
from typing import Optional, Tuple
import psutil

# Konfigurer logging med fil output
log_file = "jarvis.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis-launcher")

# Globale variabler
processes = []
DEFAULT_PORT = 8000
MAX_PORT_ATTEMPTS = 5
HEALTH_CHECK_INTERVAL = 5  # sekunder
STARTUP_TIMEOUT = 30  # sekunder

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

def check_dependencies() -> Tuple[bool, str]:
    """Tjekker om alle nødvendige dependencies er installeret"""
    required_packages = ['fastapi', 'uvicorn', 'requests', 'psutil']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Manglende packages: {', '.join(missing)}"
    return True, "Alle dependencies er installeret"

def health_check(port: int) -> bool:
    """Udfører health check på API serveren"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def kill_process_on_port(port: int) -> None:
    """Dræber proces der kører på en specifik port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info(f"Afsluttede proces på port {port}")
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

def launch_server() -> Tuple[Optional[subprocess.Popen], int]:
    """Starter Jarvis-Lite API-server"""
    # Tjek dependencies først
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        raise RuntimeError(deps_msg)
    
    # Find ledig port
    port = find_available_port()
    if not is_port_available(port):
        kill_process_on_port(port)
        if not is_port_available(port):
            raise RuntimeError(f"Kunne ikke frigøre port {port}")
    
    logger.info(f"Starter Jarvis-Lite på port {port}...")
    
    # Få den absolutte sti til src-mappen
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        src_dir = os.path.join(sys._MEIPASS, "src")
    else:
        src_dir = os.path.join(current_dir, "src")
    
    # Start API-server med port parameter
    api_cmd = [
        sys.executable,
        "api_server.py",  # Ændret fra os.path.join(src_dir, "api_server.py")
        "--port", str(port)
    ]
    
    # Opret log filer
    stdout_log = open("api_server_out.log", "w")
    stderr_log = open("api_server_err.log", "w")
    
    api_process = subprocess.Popen(
        api_cmd,
        cwd=current_dir,
        stdout=stdout_log,
        stderr=stderr_log,
        text=True
    )
    processes.append(api_process)
    
    # Vent på at serveren starter
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        # Tjek om processen er stoppet
        if api_process.poll() is not None:
            stdout_log.close()
            stderr_log.close()
            
            # Læs logs
            with open("api_server_out.log", "r") as f:
                stdout = f.read()
            with open("api_server_err.log", "r") as f:
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
    
    # Læs logs
    with open("api_server_out.log", "r") as f:
        stdout = f.read()
    with open("api_server_err.log", "r") as f:
        stderr = f.read()
        
    logger.error(f"API server timeout. Stdout:\n{stdout}\nStderr:\n{stderr}")
    
    api_process.terminate()
    raise RuntimeError(f"API-server startede ikke inden for {STARTUP_TIMEOUT} sekunder")

def monitor_process(api_process: subprocess.Popen, port: int) -> None:
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
                    api_process, port = launch_server()
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
    
    try:
        # Start server
        api_process, port = launch_server()
        
        # Åbn browser
        webbrowser.open(f"http://localhost:{port}")
        logger.info("Browser åbnet med Jarvis-Lite UI")
        
        # Start monitoring
        monitor_thread = threading.Thread(
            target=monitor_process,
            args=(api_process, port),
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

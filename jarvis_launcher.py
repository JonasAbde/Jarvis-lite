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

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("jarvis-launcher")

# Global variable til at holde styr på processer
processes = []

def launch_server():
    """Starter Jarvis-Lite API-server"""
    port = 8000
    
    logger.info("Starter Jarvis-Lite...")
    
    # Få den absolutte sti til src-mappen
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        # Kører som exe
        src_dir = os.path.join(sys._MEIPASS, "src")
    else:
        # Kører som script
        src_dir = os.path.join(current_dir, "src")
    
    # API-server (der nu også serverer UI)
    api_cmd = [sys.executable, os.path.join(src_dir, "api_server.py")]
    api_process = subprocess.Popen(
        api_cmd,
        cwd=current_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(api_process)
    logger.info(f"API-server startet på port {port}")
    
    # Giv serveren tid til at starte
    time.sleep(2)
    
    # Åbn browser
    webbrowser.open(f"http://localhost:{port}")
    logger.info("Browser åbnet med Jarvis-Lite UI")
    
    return api_process

def monitor_process(api_process):
    """Overvåger serverprocessen og genstarter den om nødvendigt"""
    while True:
        if api_process.poll() is not None:
            logger.warning("API-server stoppet uventet. Forsøger genstart...")
            try:
                # Genstart API-server
                api_process = launch_server()
            except Exception as e:
                logger.error(f"Fejl ved genstart af API-server: {e}")
        
        time.sleep(5)

def cleanup():
    """Lukker alle processer ved afslutning"""
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
        api_process = launch_server()
        
        # Start en thread til at overvåge processen
        monitor_thread = threading.Thread(
            target=monitor_process,
            args=(api_process,),
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

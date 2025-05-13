#!/usr/bin/env python3
"""
Jarvis Startup Script
Dette script håndterer opstart af hele Jarvis systemet
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
import venv
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("jarvis_startup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis-startup")

# Konstanter
VENV_PATH = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
PROJECT_ROOT = Path(__file__).resolve().parent

# Rich console for bedre output
console = Console()

def create_venv():
    """Opret virtual environment hvis det ikke eksisterer"""
    if not os.path.exists(VENV_PATH):
        console.print("[yellow]Virtual environment ikke fundet. Opretter ny...[/yellow]")
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

def check_cuda():
    """Tjek CUDA tilgængelighed"""
    check_script = """
import torch
print(json.dumps({
    'cuda_available': torch.cuda.is_available(),
    'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
}))
"""
    python_path = get_venv_python()
    try:
        result = subprocess.check_output([python_path, "-c", check_script])
        return json.loads(result)
    except:
        return {'cuda_available': False, 'device_name': None, 'device_count': 0}

def start_services():
    """Start alle nødvendige services"""
    python_path = get_venv_python()
    processes = []
    
    try:
        # Start API server
        api_server = subprocess.Popen(
            [python_path, "src/web/api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("API Server", api_server))
        
        # Vent på at API server er klar
        time.sleep(2)
        
        # Start Jarvis main
        jarvis_main = subprocess.Popen(
            [python_path, "src/jarvis_main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("Jarvis Main", jarvis_main))
        
        return processes
    except Exception as e:
        logger.error(f"Fejl ved start af services: {e}")
        for name, process in processes:
            process.terminate()
        return []

def main():
    """Hovedfunktion"""
    try:
        # Print velkommen
        console.print("[bold green]Starter Jarvis...[/bold green]")
        
        # Tjek og opret venv
        if create_venv():
            console.print("[green]Virtual environment oprettet[/green]")
        
        # Installer dependencies
        if not install_requirements():
            console.print("[red]Fejl ved installation af dependencies[/red]")
            return
        
        # Tjek CUDA
        cuda_info = check_cuda()
        if cuda_info['cuda_available']:
            console.print(f"[green]CUDA tilgængelig: {cuda_info['device_name']}[/green]")
        else:
            console.print("[yellow]CUDA ikke tilgængelig - kører på CPU[/yellow]")
        
        # Start services
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Starter Jarvis services...", total=None)
            processes = start_services()
            
            if not processes:
                console.print("[red]Fejl ved start af services[/red]")
                return
            
            console.print("[green]Jarvis er startet og klar![/green]")
            
            # Hold hovedtråden i live og monitorer processer
            while all(p[1].poll() is None for p in processes):
                time.sleep(1)
            
            # Hvis vi når hertil er en af processerne stoppet
            for name, process in processes:
                if process.poll() is not None:
                    console.print(f"[red]{name} er stoppet uventet[/red]")
                    stdout, stderr = process.communicate()
                    logger.error(f"{name} output:\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Lukker Jarvis...[/yellow]")
    finally:
        # Ryd op
        if 'processes' in locals():
            for name, process in processes:
                process.terminate()
                process.wait()
        console.print("[green]Jarvis er lukket ned[/green]")

if __name__ == "__main__":
    main() 
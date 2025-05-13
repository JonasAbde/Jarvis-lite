#!/usr/bin/env python3
"""
Jarvis Development Launcher
Dette script er specifikt til udvikling af Jarvis
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil

# Konfigurer rich console
console = Console()

# Konfigurer logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("jarvis-dev")

class JarvisDevEnvironment:
    def __init__(self):
        self.config = self.load_config()
        self.processes = {}
        self.observer = None
        self.layout = self.setup_layout()
        
    def load_config(self):
        """Indlæs udviklingskonfiguration"""
        config_path = Path("config/development.json")
        if not config_path.exists():
            console.print("[red]Fejl: development.json ikke fundet[/red]")
            sys.exit(1)
        with open(config_path) as f:
            return json.load(f)
    
    def setup_layout(self):
        """Opsæt UI layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="status"),
            Layout(name="logs")
        )
        return layout
    
    def update_status(self):
        """Opdater status panel"""
        status = []
        for name, process in self.processes.items():
            if process and process.poll() is None:
                status.append(f"[green]{name}: Kører[/green]")
            else:
                status.append(f"[red]{name}: Stoppet[/red]")
        
        self.layout["status"].update(
            Panel("\n".join(status), title="Service Status")
        )
    
    def start_service(self, name: str, command: list):
        """Start en service med logging"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes[name] = process
            logger.info(f"Started {name}")
            return process
        except Exception as e:
            logger.error(f"Fejl ved start af {name}: {e}")
            return None
    
    def stop_service(self, name: str):
        """Stop en service"""
        if name in self.processes:
            process = self.processes[name]
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                logger.info(f"Stopped {name}")
            del self.processes[name]
    
    def restart_service(self, name: str, command: list):
        """Genstart en service"""
        self.stop_service(name)
        return self.start_service(name, command)
    
    class CodeChangeHandler(FileSystemEventHandler):
        def __init__(self, dev_env):
            self.dev_env = dev_env
            
        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                logger.info(f"Detected change in {event.src_path}")
                if self.dev_env.config["development"]["auto_reload"]:
                    self.dev_env.reload_services()
    
    def setup_file_watcher(self):
        """Opsæt file watcher for auto-reload"""
        self.observer = Observer()
        handler = self.CodeChangeHandler(self)
        self.observer.schedule(handler, "src", recursive=True)
        self.observer.start()
    
    def reload_services(self):
        """Genindlæs alle services"""
        logger.info("Reloading services...")
        python = sys.executable
        
        # Genstart API server med korrekt sti
        api_cmd = [python, "api_server.py"]
        self.restart_service("API Server", api_cmd)
        
        # Genstart Jarvis main med korrekt sti
        main_cmd = [python, "jarvis_main.py"]
        self.restart_service("Jarvis Main", main_cmd)
    
    def monitor_resources(self):
        """Monitor system ressourcer"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
        else:
            temps = {}
        
        resource_info = [
            f"CPU: {cpu_percent}%",
            f"Memory: {memory.percent}%",
            f"Temperature: {temps.get('coretemp', [{'current': 'N/A'}])[0]['current']}°C"
        ]
        
        self.layout["footer"].update(
            Panel("\n".join(resource_info), title="System Resources")
        )
    
    def run(self):
        """Kør development miljø"""
        try:
            # Start file watcher hvis auto-reload er aktiveret
            if self.config["development"]["auto_reload"]:
                self.setup_file_watcher()
            
            # Start services med korrekte stier
            python = sys.executable
            self.start_service("API Server", [python, "api_server.py"])
            time.sleep(2)  # Vent på API server
            self.start_service("Jarvis Main", [python, "jarvis_main.py"])
            
            # Hovedloop med live UI
            with Live(self.layout, refresh_per_second=1) as live:
                while True:
                    self.update_status()
                    self.monitor_resources()
                    
                    # Tjek for døde processer
                    for name, process in list(self.processes.items()):
                        if process.poll() is not None:
                            stdout, stderr = process.communicate()
                            logger.error(f"{name} stopped unexpectedly")
                            logger.error(f"stdout: {stdout}")
                            logger.error(f"stderr: {stderr}")
                            if self.config["development"]["auto_reload"]:
                                self.restart_service(name, process.args)
                    
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            # Stop alle services
            for name in list(self.processes.keys()):
                self.stop_service(name)
            
            # Stop file watcher
            if self.observer:
                self.observer.stop()
                self.observer.join()

if __name__ == "__main__":
    dev_env = JarvisDevEnvironment()
    dev_env.run() 
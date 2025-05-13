import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import hashlib

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("oprydning.log", mode="w"),  # Overskriv log fil
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_header(text):
    print("\n" + "="*50)
    print(text)
    print("="*50 + "\n")

def get_file_hash(file_path: Path) -> str:
    """Beregn hash af en fils indhold"""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def backup_file(file_path: Path, backup_dir: Path) -> Path:
    """Lav backup af en fil med timestamp hvis den allerede eksisterer"""
    rel_path = file_path.relative_to(file_path.parent)
    backup_path = backup_dir / rel_path
    
    # Hvis backup allerede eksisterer, tilføj timestamp
    if backup_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{rel_path.stem}_{timestamp}{rel_path.suffix}"
    
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, backup_path)
    return backup_path

def should_ignore_file(file_path: str) -> bool:
    """Tjek om en fil skal ignoreres i duplikatkontrollen"""
    ignore_patterns = [
        ".venv",
        "backup",
        "__pycache__",
        "__init__.py",
        "handler.py",  # Forskellige moduler kan have deres egen handler
        "model.py",    # Forskellige moduler kan have deres egen model
    ]
    return any(pattern in file_path for pattern in ignore_patterns)

def cleanup_project():
    print_header("Starter oprydning af Jarvis-lite projektet")
    
    # Definer hovedmapper
    root = Path(os.getcwd())
    src = root / "src"
    
    # Opret backup mappe
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Konsolider API server filer
        print("1. Håndterer API server filer...")
        api_server_path = root / "api_server.py"
        if api_server_path.exists():
            backup_file(api_server_path, backup_dir)
            logger.info("API server fil sikkerhedskopieret")
        
        # 2. Organiser static filer
        print("\n2. Organiserer static filer...")
        static_dirs = [root / "static", src / "static"]
        main_static = root / "static"
        main_static.mkdir(exist_ok=True)
        
        for static_dir in static_dirs:
            if static_dir != main_static and static_dir.exists():
                for item in static_dir.glob("**/*"):
                    if item.is_file():
                        # Backup før flytning
                        backup_file(item, backup_dir)
                        # Flyt til hovedmappen
                        rel_path = item.relative_to(static_dir)
                        dest_path = main_static / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest_path)
                        # Slet original hvis den ikke er i hovedmappen
                        if static_dir != main_static:
                            item.unlink()
                logger.info(f"Static filer fra {static_dir} flyttet")
                # Slet tom mappe
                if static_dir != main_static:
                    shutil.rmtree(static_dir)
        
        # 3. Organiser konfigurationsfiler
        print("\n3. Organiserer konfigurationsfiler...")
        config_dir = root / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_files = list(root.glob("*.ini")) + list(root.glob("*.conf")) + list(root.glob("*.json"))
        for config_file in config_files:
            if config_file.parent == root:
                backup_file(config_file, backup_dir)
                shutil.move(config_file, config_dir / config_file.name)
                logger.info(f"Konfigurationsfil {config_file.name} flyttet til config mappen")
        
        # 4. Fjern duplikerede Python-filer
        print("\n4. Tjekker for duplikerede Python-filer...")
        python_files = {}  # filename -> [(path, hash), ...]
        
        # Først indsaml alle Python filer og deres hashes
        for py_file in root.rglob("*.py"):
            if not should_ignore_file(str(py_file)):
                file_hash = get_file_hash(py_file)
                if py_file.name not in python_files:
                    python_files[py_file.name] = []
                python_files[py_file.name].append((py_file, file_hash))
        
        # Tjek for ægte duplikater (samme indhold)
        for filename, files in python_files.items():
            if len(files) > 1:
                # Grupper filer efter deres hash
                hash_groups = {}
                for path, file_hash in files:
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(path)
                
                # For hver gruppe af identiske filer
                for file_hash, paths in hash_groups.items():
                    if len(paths) > 1:
                        logger.warning(f"Fundet {len(paths)} identiske kopier af {filename}:")
                        for path in paths:
                            logger.warning(f"  - {path}")
                        
                        # Behold filen i roden eller den første fil, slet resten
                        keep_file = None
                        for path in paths:
                            if path.parent == root:
                                keep_file = path
                                break
                        if not keep_file:
                            keep_file = paths[0]
                        
                        # Slet duplikater
                        for path in paths:
                            if path != keep_file:
                                backup_file(path, backup_dir)
                                path.unlink()
                                logger.info(f"Slettet duplikat: {path}")
        
        # 5. Organiser logs
        print("\n5. Organiserer log filer...")
        log_dir = root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_files = list(root.glob("*.log"))
        for log_file in log_files:
            if log_file.parent == root and log_file.name != "oprydning.log":  # Ignorer den aktive log fil
                shutil.move(log_file, log_dir / log_file.name)
                logger.info(f"Log fil {log_file.name} flyttet til logs mappen")
        
        # 6. Ryd op i src mappen
        print("\n6. Rydder op i src mappen...")
        # Slet tomme mapper
        for dirpath, dirnames, filenames in os.walk(src, topdown=False):
            dir_path = Path(dirpath)
            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                logger.info(f"Slettet tom mappe: {dir_path}")
        
        print("\nOprydning færdig!")
        print("\nBemærk: Alle originale filer er gemt i backup mappen.")
        print("Gennemgå venligst ændringerne og slet backup mappen når alt virker.")
        
    except Exception as e:
        logger.error(f"Fejl under oprydning: {str(e)}")
        print(f"\nFejl under oprydning: {e}")
        print("Oprydning afbrudt. Nogle filer kan være blevet ændret.")
        print("Gendan fra backup mappen hvis nødvendigt.")

if __name__ == "__main__":
    cleanup_project() 
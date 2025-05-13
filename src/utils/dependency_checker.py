import pkg_resources
import logging
from typing import List, Tuple, Dict
import torch
import os
import sys
import time
from pathlib import Path
import subprocess
from tqdm import tqdm
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError

logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = {
    # Base dependencies
    "torch": "2.2.0",
    "transformers": "4.38.0",
    "fastapi": "0.95.0",
    "uvicorn": "0.21.1",
    "numpy": "1.24.3",
    "nltk": "3.9.0",
    "python-multipart": "0.0.6",
    "pydantic": "2.4.2",
    
    # LLM dependencies
    "accelerate": "0.27.0",
    "bitsandbytes": "0.45.0",
    "sentencepiece": "0.2.0",
    
    # Utility dependencies
    "tqdm": "4.65.0",
    "colorama": "0.4.6",
    "rich": "13.7.0"
}

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operationen tog for lang tid")

def run_with_timeout(cmd: List[str], timeout: int = 300) -> Tuple[bool, str]:
    """Kør en kommando med timeout"""
    try:
        # Sæt timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        # Kør kommando
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # Fjern timeout
        signal.alarm(0)
        
        success = process.returncode == 0
        message = stdout if success else stderr
        return success, message
        
    except TimeoutException:
        return False, "Kommandoen tog for lang tid"
    except Exception as e:
        return False, str(e)
    finally:
        signal.alarm(0)
        if 'process' in locals():
            process.kill()

def check_cuda() -> Tuple[bool, str]:
    """Tjek CUDA tilgængelighed og version"""
    if not torch.cuda.is_available():
        return False, "CUDA ikke tilgængelig"
    
    try:
        cuda_version = torch.version.cuda
        device_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
        
        if vram < 8:
            return False, f"For lidt VRAM: {vram:.1f}GB (minimum 8GB krævet)"
            
        return True, f"CUDA {cuda_version} tilgængelig på {device_name} med {vram:.1f}GB VRAM"
    except Exception as e:
        return False, f"Fejl ved CUDA tjek: {e}"

def check_disk_space(min_space_gb: float = 20.0) -> Tuple[bool, str]:
    """Tjek om der er nok diskplads"""
    try:
        if sys.platform == 'win32':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free_bytes))
            free_gb = free_bytes.value / (1024**3)
        else:
            total, used, free = os.statvfs('/').f_blocks, os.statvfs('/').f_bfree, os.statvfs('/').f_bavail
            free_gb = (free * os.statvfs('/').f_frsize) / (1024**3)
            
        if free_gb < min_space_gb:
            return False, f"Kun {free_gb:.1f}GB ledig diskplads. Minimum {min_space_gb}GB krævet."
        return True, f"{free_gb:.1f}GB ledig diskplads tilgængelig"
    except Exception as e:
        return False, f"Fejl ved diskplads tjek: {e}"

def check_dependencies() -> Tuple[bool, List[str]]:
    """Tjek alle dependencies med progress bar"""
    print("\nTjekker system krav og dependencies...")
    
    with tqdm(total=4, desc="System tjek", ncols=100) as pbar:
        missing = []
        outdated = []
        
        # Tjek CUDA
        cuda_ok, cuda_msg = check_cuda()
        if not cuda_ok:
            logger.warning(f"CUDA status: {cuda_msg}")
        else:
            logger.info(f"CUDA status: {cuda_msg}")
        pbar.update(1)
        
        # Tjek diskplads
        disk_ok, disk_msg = check_disk_space()
        if not disk_ok:
            logger.warning(f"Diskplads status: {disk_msg}")
        else:
            logger.info(f"Diskplads status: {disk_msg}")
        pbar.update(1)
        
        # Tjek pakkeversioner
        for package, min_version in tqdm(REQUIRED_PACKAGES.items(), desc="Tjekker pakker", leave=False):
            try:
                installed = pkg_resources.get_distribution(package)
                if pkg_resources.parse_version(installed.version) < pkg_resources.parse_version(min_version):
                    outdated.append(f"{package} (installeret: {installed.version}, krævet: {min_version})")
            except pkg_resources.DistributionNotFound:
                missing.append(package)
        pbar.update(1)
        
        # Tjek model cache
        cache_dir = Path.home() / ".cache" / "huggingface"
        if not cache_dir.exists():
            logger.warning("Huggingface cache directory ikke fundet")
        else:
            cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file()) / (1024**3)
            logger.info(f"Huggingface cache størrelse: {cache_size:.1f}GB")
        pbar.update(1)
    
    all_ok = not (missing or outdated) and cuda_ok and disk_ok
    
    if missing:
        logger.error("Manglende pakker: " + ", ".join(missing))
    if outdated:
        logger.warning("Forældede pakker: " + ", ".join(outdated))
    
    return all_ok, missing + outdated

def install_dependencies(missing: List[str]) -> bool:
    """Installer manglende dependencies med progress bar og timeout"""
    try:
        total_packages = len(missing)
        with tqdm(total=total_packages, desc="Installerer pakker", ncols=100) as pbar:
            for package in missing:
                if "==" in package:
                    package_name = package.split("==")[0]
                    version = package.split("==")[1]
                else:
                    package_name = package
                    version = REQUIRED_PACKAGES.get(package, "")
                
                cmd = [sys.executable, "-m", "pip", "install", f"{package_name}=={version}" if version else package]
                
                # Vis current package
                pbar.set_description(f"Installerer {package_name}")
                
                # Kør installation med timeout
                success, message = run_with_timeout(cmd, timeout=300)  # 5 minutter timeout
                
                if not success:
                    logger.error(f"Fejl ved installation af {package_name}: {message}")
                    return False
                
                pbar.update(1)
                
        return True
        
    except Exception as e:
        logger.error(f"Fejl ved installation af dependencies: {e}")
        return False 
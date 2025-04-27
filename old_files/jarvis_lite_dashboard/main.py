import sys
import os
import platform
import yaml
import subprocess

# Tilføj projektets rodmappe til sys.path for korrekte imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Nu kan vi importere fra vores egne moduler
from dashboard.web.app import start_web_dashboard
from dashboard.rpi.app import start_rpi_dashboard # Antaget sti for RPi

# Funktion til at indlæse indstillinger
def load_settings(config_path='config/settings.yaml'):
    try:
        with open(os.path.join(project_root, config_path), 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Advarsel: Konfigurationsfil ikke fundet: {config_path}. Bruger standardindstillinger.")
        return {'mode': 'pc'} # Standard til PC hvis fil mangler
    except Exception as e:
        print(f"Fejl ved indlæsning af konfigurationsfil: {e}")
        return {'mode': 'pc'}

# Funktion til at detektere hardware (simpel version)
def detect_hardware():
    if platform.system() == "Linux" and "raspberrypi" in platform.uname().nodename:
        return "rpi"
    return "pc"

if __name__ == "__main__":
    print("Velkommen til Jarvis Lite Dashboard!")
    settings = load_settings()
    
    # Bestem tilstand (auto, pc, rpi)
    mode = settings.get('mode', 'auto').lower()
    
    if mode == 'auto':
        detected_mode = detect_hardware()
        print(f"Automatisk detekteret hardware: {detected_mode.upper()}")
        mode = detected_mode
    elif mode not in ['pc', 'rpi']:
        print(f"Advarsel: Ukendt tilstand '{mode}' i settings.yaml. Bruger 'pc'.")
        mode = 'pc'
    else:
        print(f"Tvinger tilstand til: {mode.upper()}")

    # Start det relevante dashboard
    if mode == "pc":
        print("Starter Web Dashboard (PC Mode)...")
        # Kør Streamlit som en subproces, da start_web_dashboard() blokerer
        streamlit_path = os.path.join(sys.executable, '..', 'Scripts', 'streamlit.exe') # Find streamlit
        app_path = os.path.join(project_root, 'dashboard', 'web', 'app.py')
        
        # Tjek om streamlit eksisterer på den forventede sti
        if not os.path.exists(streamlit_path):
             print(f"FEJL: Kunne ikke finde streamlit på {streamlit_path}")
             print("Prøver at køre med 'python -m streamlit run'...")
             command = [sys.executable, "-m", "streamlit", "run", app_path]
        else:
            command = [streamlit_path, "run", app_path]
            
        try:
            # Start streamlit non-blocking
            process = subprocess.Popen(command, cwd=project_root)
            print(f"Streamlit proces startet med PID: {process.pid}")
            # Vi kan evt. vente på processen her, hvis nødvendigt, eller bare lade den køre
            # process.wait() # Uncomment for at vente
        except FileNotFoundError:
            print(f"FEJL: Kunne ikke starte Streamlit. Er det installeret og i PATH?")
        except Exception as e:
             print(f"Fejl under start af Streamlit: {e}")
             
    elif mode == "rpi":
        print("Starter Raspberry Pi Dashboard...")
        try:
            start_rpi_dashboard() # Antaget funktion for RPi dashboard
        except NameError:
            print("Fejl: RPi dashboard (start_rpi_dashboard) er ikke implementeret.")
        except Exception as e:
            print(f"Fejl under start af RPi dashboard: {e}")

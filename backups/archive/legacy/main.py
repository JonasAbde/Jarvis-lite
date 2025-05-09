import sys
import os
import threading
import time

# Monkey-patch scipy.signal for DanSpeech compatibility
import scipy.signal
from scipy.signal import windows as _win

# Recreate the old window functions
scipy.signal.hamming   = _win.hamming
scipy.signal.hann      = _win.hann
scipy.signal.blackman  = _win.blackman
scipy.signal.bartlett  = _win.bartlett
scipy.signal.flattop   = _win.flattop
scipy.signal.kaiser    = _win.kaiser

# Tilføj projektets rodmappe til Python-stien
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.jarvis_commands import JarvisCommands

def check_requirements():
    """Tjek om alle nødvendige filer og mapper eksisterer"""
    required_dirs = ['src', 'data']
    required_files = [
        'src/jarvis_core.py',
        'src/jarvis_commands.py',
        'src/jarvis_voice.py',
        'src/danspeech_voice.py'
    ]
    
    # Tjek mapper
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ Fejl: Mappen '{dir_name}' mangler!")
            return False
    
    # Tjek filer
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"❌ Fejl: Filen '{file_name}' mangler!")
            return False
    
    return True

def listen_for_commands(jarvis):
    """Lyt efter stemmekommandoer"""
    while True:
        try:
            # Hent den sidst genkendte tekst
            command = jarvis.voice.get_last_recognized_text()
            if command:
                print(f"\nGenkendt kommando: {command}")
                response = jarvis.handle_command(command)
                print(f"\nJarvis: {response}")
                jarvis.voice.clear_last_recognized_text()
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Fejl under lytning: {str(e)}")

def main():
    """Hovedfunktion der starter Jarvis Lite"""
    print("🔍 Starter Jarvis Lite...")
    
    # Tjek om alt er på plads
    if not check_requirements():
        print("\n❌ Programmet kunne ikke starte. Kontroller at alle filer er på plads.")
        return
    
    try:
        jarvis = JarvisCommands()
        
        print("\n🎉 Velkommen til Jarvis Lite! 🎉")
        print("\nJeg kan hjælpe dig med følgende:")
        print("1. Sige hej (prøv 'hej' eller 'goddag')")
        print("2. Fortælle tiden (prøv 'hvad er klokken?')")
        print("3. Åbne hjemmesider (prøv 'åbn google.com')")
        print("4. Gemme noter (prøv 'gem husk at købe mælk')")
        print("5. Vise dine noter (prøv 'vis mine noter')")
        print("6. Give motivation (prøv 'motiver mig')")
        print("\nDu kan altid skrive 'hjælp' for at se denne menu igen")
        print("\nSkriv 'afslut' for at lukke programmet")
        
        # Test stemmen ved opstart
        jarvis.voice.speak("Hej! Jeg er klar til at hjælpe dig!")
        
        # Start lytning efter stemmekommandoer
        jarvis.voice.start_listening()
        listen_thread = threading.Thread(target=listen_for_commands, args=(jarvis,))
        listen_thread.daemon = True
        listen_thread.start()
        
        while True:
            try:
                command = input("\nHvad kan jeg hjælpe dig med? > ")
                if command.lower() == 'afslut':
                    print("\nFarvel! Tak for denne gang.")
                    break
                response = jarvis.handle_command(command)
                print(f"\nJarvis: {response}")
            except KeyboardInterrupt:
                print("\nFarvel! Tak for denne gang.")
                break
            except Exception as e:
                print(f"\n❌ Fejl: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Fejl under opstart: {str(e)}")
    finally:
        if 'jarvis' in locals():
            jarvis.voice.stop_listening()

if __name__ == "__main__":
    main() 
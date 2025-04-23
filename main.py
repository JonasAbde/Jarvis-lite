import sys
import os

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
        'src/jarvis_voice.py'
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
        
        while True:
            try:
                command = input("\nHvad kan jeg hjælpe dig med? > ")
                
                if command.lower() == "afslut":
                    print("Farvel! Tak fordi du brugte Jarvis Lite! 👋")
                    jarvis.voice.speak("Farvel! På gensyn!")
                    break
                    
                response = jarvis.handle_command(command)
                print(f"\nJarvis: {response}")
                
            except KeyboardInterrupt:
                print("\n\nFarvel! Tak fordi du brugte Jarvis Lite! 👋")
                jarvis.voice.speak("Farvel! På gensyn!")
                break
            except Exception as e:
                print(f"\n❌ Der opstod en fejl: {str(e)}")
                print("Prøv igen eller skriv 'afslut' for at lukke programmet")
                
    except Exception as e:
        print(f"\n❌ Kritisk fejl: {str(e)}")
        print("Kontakt venligst en administrator")

if __name__ == "__main__":
    main() 
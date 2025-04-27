import os
import logging
import datetime
import webbrowser
import time
from gtts import gTTS
from playsound import playsound
import random

# Konfigurer simpel logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Funktion til at gemme noter
def save_note(note_text):
    """
    Gemmer en note i filen notes.txt.
    """
    try:
        with open("notes.txt", "a", encoding="utf-8") as file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"[{timestamp}] {note_text}\n")
        return f"Notatet er gemt: {note_text}"
    except Exception as e:
        logging.error(f"Fejl under gemning af note: {e}")
        return "Der opstod en fejl under gemning af notatet."

# TTS-indstillinger - kan justeres for andet sprog/køn
TTS_SETTINGS = {
    'dansk_kvinde': {'lang': 'da', 'description': 'Dansk (kvinde)'},
    'engelsk_mand': {'lang': 'en-uk', 'description': 'Engelsk (britisk mand)'},
    'tysk_mand': {'lang': 'de', 'description': 'Tysk (mand)'},
    'italiensk_mand': {'lang': 'it', 'description': 'Italiensk (mand)'}
}

# Aktuel TTS-indstilling (kan skiftes via kommandoer)
CURRENT_TTS = 'dansk_kvinde'  # Standard er dansk kvindelig stemme

# Funktion til at tale med gTTS
def speak_gtts(text, lang=None):
    """
    Bruger Google Text-to-Speech til at læse tekst højt.
    Returnerer teksten, hvis TTS fejler.
    """
    # Vis altid teksten i terminal
    print(f"\nJarvis: {text}")
    
    # Brug specificeret sprog eller standardindstillingen
    if lang is None:
        lang = TTS_SETTINGS[CURRENT_TTS]['lang']
    
    try:
        # Opret en unik filsti i samme mappe som skriptet
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_file = os.path.join(script_dir, f"temp_v1_speech_{random.randint(1, 10000)}.mp3")
        
        # Generer tale-fil
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_file)
        
        # Afspil filen
        try:
            playsound(temp_file)
        except Exception as e:
            logging.error(f"Afspilning fejlede: {e}")
            # Fortsæt alligevel, vi har allerede vist teksten
        
        # Fjern den midlertidige fil efter brug
        try:
            os.remove(temp_file)
        except:
            pass  # Ignorer hvis filen ikke kan slettes
            
        return text
    except Exception as e:
        # Log fejlen og returner teksten i stedet
        logging.error(f"Fejl under TTS: {e}", exc_info=True)
        print(f"(TTS Fejl - kun tekstoutput)")
        return text

# Funktion til at skifte stemme
def change_voice(voice_name):
    """Skifter til en anden TTS-stemme."""
    global CURRENT_TTS
    if voice_name in TTS_SETTINGS:
        CURRENT_TTS = voice_name
        return f"Stemmen er skiftet til {TTS_SETTINGS[voice_name]['description']}"
    else:
        voices_str = ", ".join([f"'{k}' ({v['description']})" for k, v in TTS_SETTINGS.items()])
        return f"Ugyldig stemme. Tilgængelige stemmer: {voices_str}"

# Funktion til at få klokken
def get_time():
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    
    if hour < 10:
        hour_text = f"0{hour}"
    else:
        hour_text = str(hour)
        
    if minute < 10:
        minute_text = f"0{minute}"
    else:
        minute_text = str(minute)
    
    return f"Klokken er {hour_text}:{minute_text}."

# Funktion til at åbne YouTube
def open_youtube():
    try:
        webbrowser.open("https://www.youtube.com")
        return "Åbner YouTube i din browser."
    except Exception as e:
        logging.error(f"Fejl under åbning af YouTube: {e}")
        return "Der opstod en fejl under åbning af YouTube."

# Funktion til at åbne DR
def open_dr():
    try:
        webbrowser.open("https://www.dr.dk")
        return "Åbner DR i din browser."
    except Exception as e:
        logging.error(f"Fejl under åbning af DR: {e}")
        return "Der opstod en fejl under åbning af DR."

# Funktion til at sige hej
def say_hello():
    current_hour = datetime.datetime.now().hour
    
    if current_hour < 5:
        greeting = "Godnat! Du er sent oppe."
    elif current_hour < 10:
        greeting = "Godmorgen! Jeg håber, du får en fantastisk dag."
    elif current_hour < 12:
        greeting = "God formiddag! Hvordan går det med din dag indtil videre?"
    elif current_hour < 15:
        greeting = "God eftermiddag! Jeg håber, du har haft en god dag indtil nu."
    elif current_hour < 18:
        greeting = "God eftermiddag! Hvordan har din dag været?"
    elif current_hour < 23:
        greeting = "Godaften! Jeg håber, du har haft en dejlig dag."
    else:
        greeting = "Godnat! Det er sent, har du overvejet at få lidt søvn?"
    
    return greeting

# Funktion til at fortælle om sig selv
def say_identity():
    return random.choice([
        "Jeg er Jarvis, din tekstbaserede assistent. Jeg er designet til at hjælpe dig med simple opgaver via tekstkommandoer.",
        "Mit navn er Jarvis, og jeg er en simpel if/else-baseret assistent. Jeg kan udføre simple kommandoer som du skriver til mig.",
        "Jeg hedder Jarvis. Jeg er en basisversion af en tekstbaseret assistent, som kan hjælpe dig med forskellige opgaver."
    ])

# Funktion til at sige farvel
def say_goodbye():
    return random.choice([
        "Farvel! Tak for nu.",
        "På gensyn! Det var hyggeligt at hjælpe dig.",
        "Farvel! Jeg er her, når du har brug for mig igen.",
        "Hej hej! God dag til dig.",
        "Farvel! Tak fordi du brugte Jarvis Lite i dag."
    ])

# Funktion til at håndtere kommandoer
def handle_text_command(command):
    """
    Håndterer tekstkommandoer ved at matche dem med if/else statements.
    """
    if not command:
        speak_gtts("Jeg forstod ikke kommandoen, prøv igen.")
        return True
        
    command = command.lower().strip()
    
    # Tid
    if "hvad er klokken" in command or "tid" in command:
        response = get_time()
        speak_gtts(response)
    
    # YouTube
    elif "åbn youtube" in command or "vis youtube" in command:
        response = open_youtube()
        speak_gtts(response)
    
    # DR
    elif "åbn dr" in command or "vis dr" in command:
        response = open_dr()
        speak_gtts(response)
    
    # Noter
    elif "gem note" in command or "gem notat" in command:
        # Isoler noten (tekst efter "gem note" eller "gem notat")
        if "gem note" in command:
            note_text = command.split("gem note", 1)[1].strip()
        else:
            note_text = command.split("gem notat", 1)[1].strip()
        
        if not note_text:
            speak_gtts("Hvad vil du gemme i noten?")
            try:
                note_text = input("Indtast note: ").strip()
            except:
                note_text = ""
                
        if note_text:
            response = save_note(note_text)
            speak_gtts(response)
        else:
            speak_gtts("Ingen note gemt.")
    
    # Skift stemme
    elif "skift stemme" in command or "skift sprog" in command:
        # Kommando: "skift stemme til [stemme_navn]"
        parts = command.split("til", 1)
        if len(parts) > 1 and parts[1].strip():
            voice_name = parts[1].strip()
            # Find det bedst matchende stemmenavn
            best_match = None
            for name in TTS_SETTINGS.keys():
                if voice_name in name or name in voice_name:
                    best_match = name
                    break
            
            if best_match:
                response = change_voice(best_match)
            else:
                response = change_voice(voice_name)  # Vil give fejlbesked med tilgængelige stemmer
        else:
            # Vis tilgængelige stemmer
            voices_str = ", ".join([f"'{k}' ({v['description']})" for k, v in TTS_SETTINGS.items()])
            response = f"Nuværende stemme: {TTS_SETTINGS[CURRENT_TTS]['description']}. Tilgængelige stemmer: {voices_str}"
        
        speak_gtts(response)
    
    # Hej/goddag
    elif "hej" in command or "goddag" in command or "godmorgen" in command:
        response = say_hello()
        speak_gtts(response)
    
    # Identitet
    elif "hvem er du" in command or "præsenter dig" in command:
        response = say_identity()
        speak_gtts(response)
    
    # Farvel
    elif "farvel" in command or "vi ses" in command or "hej hej" in command:
        response = say_goodbye()
        speak_gtts(response)
        return False
    
    # Afslut
    elif "afslut" in command or "luk" in command or "stop" in command:
        speak_gtts("Lukker Jarvis. Farvel!")
        return False
        
    # Hjælp
    elif "hjælp" in command or "help" in command:
        help_text = """
        Jeg kan hjælpe med følgende:
        - Fortælle hvad klokken er ('hvad er klokken', 'tid')
        - Åbne YouTube ('åbn youtube', 'vis youtube')
        - Åbne DR ('åbn dr', 'vis dr')
        - Gemme noter ('gem note [besked]')
        - Skifte stemme ('skift stemme til [stemme_navn]')
        - Hilse på dig ('hej', 'goddag')
        - Fortælle om mig selv ('hvem er du')
        - Sige farvel ('farvel', 'vi ses')
        - Lukke programmet ('afslut', 'luk', 'stop')
        """
        print(help_text)
        speak_gtts("Jeg har vist en liste over kommandoer. Hvad kan jeg hjælpe med?")
    
    # Ukendt kommando
    else:
        speak_gtts("Undskyld, jeg forstod ikke kommandoen. Prøv at sige 'hjælp' for at se mulige kommandoer.")
    
    return True

# Hovedprogram-løkke
def main():
    """
    Hovedprogram der kører Jarvis basis-versionen med if/else kommandohåndtering.
    """
    print("=" * 50)
    print("JARVIS LITE v1 (If/Else version)")
    print("=" * 50)
    print("BEMÆRK: Jarvis lytter IKKE efter mikrofon!")
    print("Du skal skrive kommandoer i terminalen og trykke Enter.")
    print("Skriv 'hjælp' for at se en liste over kommandoer")
    print("Skriv 'skift stemme til [stemme_navn]' for at ændre Jarvis' stemme")
    print("Skriv 'afslut' for at afslutte programmet")
    print("-" * 50)
    print(f"Nuværende stemme: {TTS_SETTINGS[CURRENT_TTS]['description']}")
    print("-" * 50)
    
    speak_gtts("Jarvis er klar til at hjælpe dig. Hvad kan jeg gøre for dig?")
    
    running = True
    while running:
        try:
            command = input("\nDin kommando > ").strip()
            if command:
                print(f"\n[Behandler kommando: '{command}']")
            running = handle_text_command(command)
                
        except KeyboardInterrupt:
            print("\nAfbrudt af bruger.")
            speak_gtts("Afbrudt af bruger. Lukker Jarvis. Farvel.")
            running = False
        except Exception as e:
            logging.error(f"Fejl opstod: {str(e)}")
            print(f"Der opstod en fejl: {str(e)}")
            print("Prøv igen eller genstart programmet.")
            speak_gtts("Der opstod en fejl. Prøv igen eller genstart programmet.")
    
    print("\nJarvis Lite er afsluttet. På gensyn!")

# Kør hovedprogrammet, hvis dette script køres direkte
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Uventet fejl opstod: {str(e)}", exc_info=True)
        print(f"En uventet fejl opstod: {str(e)}")
        print("Programmet afsluttes.")
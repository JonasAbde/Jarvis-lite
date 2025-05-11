#!/usr/bin/env python3

"""
Script til at rette indrykningsfejl i src/jarvis_main.py.
"""

def fix_youtube_block():
    # Læs filen
    with open('src/jarvis_main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find åbn-blokken og ret den
    in_block = False
    youtube_fixed = False
    
    for i in range(len(lines)):
        if 'elif "åbn" in command or "gå til" in command:' in lines[i]:
            in_block = True
            continue
            
        if in_block and 'if "youtube" in command:' in lines[i]:
            # Her starter YouTube-blokken
            indent = lines[i].index('if')  # Får indrykningsniveauet
            
            # Tjek næste linje for webbrowser.open
            if 'webbrowser.open' in lines[i+1]:
                new_indent = ' ' * (indent + 4)  # 4 spaces indrykning
                lines[i+1] = new_indent + lines[i+1].lstrip()
                
                # Tjek og ret respons-linjen
                if 'response =' in lines[i+2]:
                    lines[i+2] = new_indent + lines[i+2].lstrip()
                    youtube_fixed = True
                
        # Stop når vi når ud af åbn-blokken
        if in_block and lines[i].strip() and not lines[i].startswith(' '):
            in_block = False
    
    # Skriv de opdaterede linjer tilbage til filen
    if youtube_fixed:
        with open('src/jarvis_main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("YouTube-blokken er rettet!")
    else:
        print("Kunne ikke finde eller rette YouTube-blokken.")

def fix_note_block():
    # Læs filen
    with open('src/jarvis_main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find note-blokken og ret den
    in_block = False
    note_fixed = False
    
    for i in range(len(lines)):
        if 'elif "gem" in command and "note" in command:' in lines[i]:
            in_block = True
            continue
            
        if in_block and 'with open(NOTES_FILE, "a", encoding="utf-8") as f:' in lines[i]:
            indent = lines[i].index('with')  # Får indrykningsniveauet
            
            # Tjek næste linje 
            if 'f.write' in lines[i+1]:
                new_indent = ' ' * (indent + 4)  # 4 spaces indrykning
                lines[i+1] = new_indent + lines[i+1].lstrip()
                note_fixed = True
                
        # Stop når vi når ud af note-blokken
        if in_block and lines[i].strip() and not lines[i].startswith(' '):
            in_block = False
    
    # Skriv de opdaterede linjer tilbage til filen
    if note_fixed:
        with open('src/jarvis_main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Note-blokken er rettet!")
    else:
        print("Kunne ikke finde eller rette note-blokken.")

def create_clean_version():
    # Laver en ny version af filen med manuel rensning
    with open('src/jarvis_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Erstat problematiske blokke med korrekt indrykket kode
    youtube_block = """    elif "åbn" in command or "gå til" in command:
        if "youtube" in command:
            webbrowser.open("https://www.youtube.com")
            response = "Jeg åbner YouTube for dig. Hvad vil du se?"
        elif "google" in command:
            webbrowser.open("https://www.google.com")
            response = "Jeg åbner Google. Hvad vil du søge efter?"
        else:
            response = "Hvad vil du have mig til at åbne?"
"""
    
    note_block = """    elif "gem" in command and "note" in command:
        note = command.replace("gem", "").replace("note", "").strip()
        if note:
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(f"{note}\\n")
            response = f"Jeg har gemt din note. Skal jeg læse den op for dig?"
        else:
            response = "Hvad vil du have mig til at gemme som en note?"
"""
    
    # Søg efter blokkene i original indholdet og erstat dem
    try:
        start = content.index('elif "åbn" in command or "gå til" in command:')
        end = content.index('elif "gem" in command', start)
        
        # Erstat YouTube-blokken
        modified_content = content[:start] + youtube_block + content[end:]
        
        start = modified_content.index('elif "gem" in command and "note" in command:')
        end = modified_content.index('elif "hvem er du" in command', start)
        
        # Erstat note-blokken
        modified_content = modified_content[:start] + note_block + modified_content[end:]
        
        # Skriv den opdaterede fil
        with open('src/jarvis_main_clean.py', 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("En ny renset version er oprettet som src/jarvis_main_clean.py!")
        return True
    except ValueError as e:
        print(f"Kunne ikke oprette ren version: {e}")
        return False

if __name__ == "__main__":
    print("Forsøger at rette indrykningsfejl i jarvis_main.py...")
    
    # Prøv først at rette de enkelte blokke
    fix_youtube_block()
    fix_note_block()
    
    # Hvis det ikke virker, lav en ren version
    create_clean_version() 
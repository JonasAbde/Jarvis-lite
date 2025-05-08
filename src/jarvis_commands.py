"""
Kommando-modul for Jarvis-lite.
Indeholder alle kommandoer som Jarvis kan udføre.
"""

import datetime
import webbrowser
import os
import random
import pathlib
from typing import Optional, Callable

# Definer stier
ROOT = pathlib.Path(__file__).resolve().parent
NOTES_FILE = ROOT / "data" / "noter.txt"
JOKES_FILE = ROOT / "data" / "jokes.txt"

# Indlæs jokes
JOKES_LIST = (
    [l.strip() for l in JOKES_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if JOKES_FILE.exists()
    else ["Hvorfor gik kyllingen over vejen? For at komme over til den anden side!"]
)

def get_time() -> str:
    """Returner nuværende tid."""
    now = datetime.datetime.now()
    return f"Klokken er {now.strftime('%H:%M')}"

def open_youtube() -> str:
    """Åbn YouTube i standardbrowseren."""
    webbrowser.open("https://www.youtube.com", new=2)
    return "Åbner YouTube..."

def open_gmail() -> str:
    """Åbn Gmail i standardbrowseren."""
    webbrowser.open("https://mail.google.com", new=2)
    return "Åbner Gmail..."

def save_note(note_text: str) -> str:
    """Gem en note i noter.txt."""
    NOTES_FILE.parent.mkdir(exist_ok=True)
    with NOTES_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {note_text}\n")
    return "Noten er gemt."

def tell_joke() -> str:
    """Fortæl en tilfældig joke."""
    return random.choice(JOKES_LIST)

def stop_sound(tts_engine: Optional[object] = None) -> str:
    """Stop nuværende lydafspilning."""
    if tts_engine and hasattr(tts_engine, "stop"):
        tts_engine.stop()
    return "Stopper lyden..."

def open_website(url):
    webbrowser.open(url)
    return f"Åbner {url}..."

def save_message(message):
    with open("beskeder.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")
    return "Beskeden er gemt."

def list_notes():
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            notes = f.readlines()
        return "".join(notes) if notes else "Ingen noter fundet."
    except FileNotFoundError:
        return "Ingen noter fundet."

def get_date():
    now = datetime.datetime.now()
    return f"Dagen i dag er {now.strftime('%d/%m/%Y')}"

def open_file(file_path):
    if os.path.exists(file_path):
        os.startfile(file_path)
        return f"Åbner fil: {file_path}"
    else:
        return f"Fil ikke fundet: {file_path}"

def search_google(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Søger efter {query} på Google..."

def exit_program():
    return "Farvel! Jeg lukker nu..."

# Kommando-mapping
COMMANDS = {
    "klokken": get_time,
    "youtube": open_youtube,
    "gmail": open_gmail,
    "gem_note": save_note,
    "joke": tell_joke,
    "stop_lyd": stop_sound,
    "åbn hjemmeside": open_website,
    "gem besked": save_message,
    "liste noter": list_notes,
    "dato": get_date,
    "åbn fil": open_file,
    "søg google": search_google,
    "afslut": exit_program,
}

import datetime
import webbrowser
import os

NOTES_FILE = "noter.txt"

def get_time():
    now = datetime.datetime.now()
    return f"Klokken er {now.strftime('%H:%M')}"

def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Åbner YouTube..."

def save_note(note_text):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(note_text + "\n")
    return "Noten er gemt."

COMMANDS = {
    "klokken": get_time,
    "youtube": open_youtube,
    "gem note": save_note,
}
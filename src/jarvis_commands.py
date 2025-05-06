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

COMMANDS = {
    "klokken": get_time,
    "youtube": open_youtube,
    "gem note": save_note,
    "åbn hjemmeside": open_website,
    "gem besked": save_message,
    "liste noter": list_notes,
    "dato": get_date,
    "åbn fil": open_file,
    "søg google": search_google,
    "afslut": exit_program,
}

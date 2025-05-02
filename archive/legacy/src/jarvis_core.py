import datetime
import webbrowser
import os
from typing import List

class JarvisCore:
    def __init__(self):
        """Initialize Jarvis with basic settings"""
        self.notes_file = "data/notes.txt"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists("data"):
            os.makedirs("data")
    
    def get_time(self) -> str:
        """Get current time in a friendly format"""
        current_time = datetime.datetime.now()
        return f"Klokken er {current_time.strftime('%H:%M')}"
    
    def open_website(self, url: str) -> bool:
        """Open a website in the default browser"""
        try:
            # Clean up URL
            url = url.strip().lower()
            
            # Add https:// if no protocol is specified
            if not url.startswith(('http://', 'https://')):
                if not url.startswith('www.'):
                    url = 'www.' + url
                url = 'https://' + url
            
            print(f"Åbner URL: {url}")  # Debug information
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Kunne ikke åbne hjemmesiden: {e}")
            return False
    
    def save_note(self, note: str) -> bool:
        """Save a note to the notes file"""
        try:
            with open(self.notes_file, "a", encoding="utf-8") as file:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                file.write(f"[{timestamp}] {note}\n")
            return True
        except Exception as e:
            print(f"Kunne ikke gemme noten: {e}")
            return False
    
    def read_notes(self) -> List[str]:
        """Read all notes from the notes file"""
        try:
            if not os.path.exists(self.notes_file):
                return []
            
            with open(self.notes_file, "r", encoding="utf-8") as file:
                return file.readlines()
        except Exception as e:
            print(f"Kunne ikke læse noter: {e}")
            return []
    
    def motivate(self) -> str:
        """Return a motivational message"""
        motivations = [
            "Du er fantastisk! 💪",
            "Keep going! 🚀",
            "Du kan klare det! 🌟",
            "Smil til dig selv i spejlet! 😊",
            "Hver dag er en ny chance! 🌈"
        ]
        return motivations[datetime.datetime.now().second % len(motivations)] 
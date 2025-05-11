from .jarvis_core import JarvisCore
from .jarvis_voice import JarvisVoice

class JarvisCommands:
    def __init__(self):
        """Initialize Jarvis with core and voice functionality"""
        self.core = JarvisCore()
        self.voice = JarvisVoice()
    
    def handle_command(self, command: str) -> str:
        """Handle user commands and return appropriate response"""
        command = command.lower().strip()
        
        # Hilsner
        if any(word in command for word in ["hej", "goddag", "godmorgen", "godaften", "hallo"]):
            response = "Hej! Hvordan kan jeg hjælpe dig?"
            self.voice.speak(response)
            return response
        
        # Tid
        elif any(word in command for word in ["klokken", "tid", "tidspunkt"]):
            response = self.core.get_time()
            self.voice.speak(response)
            return response
        
        # Åbn hjemmeside    
        elif "åbn" in command:
            # Extract URL from command
            url = command.split("åbn")[-1].strip()
            
            if url:  # Only try to open if we got a URL
                if self.core.open_website(url):
                    response = f"Åbner {url}"
                    self.voice.speak(response)
                    return response
                else:
                    return "Kunne ikke åbne hjemmesiden"
            else:
                return "Jeg har brug for en hjemmeside at åbne. Prøv f.eks. 'åbn google.com'"
        
        # Gem note
        elif "gem" in command:
            # Extract note from command
            note = command.split("gem")[-1].strip()
            
            if note:  # Only save if we got a note
                if self.core.save_note(note):
                    response = "Noten er gemt!"
                    self.voice.speak(response)
                    return response
                else:
                    return "Kunne ikke gemme noten"
            else:
                return "Jeg har brug for en note at gemme. Prøv f.eks. 'gem husk at købe mælk'"
        
        # Vis noter
        elif any(phrase in command for phrase in ["vis noter", "læs noter", "mine noter"]):
            notes = self.core.read_notes()
            if notes:
                response = "Her er dine noter:\n" + "".join(notes)
                self.voice.speak("Her er dine noter")
                return response
            else:
                response = "Du har ingen noter endnu"
                self.voice.speak(response)
                return response
        
        # Motivation
        elif any(word in command for word in ["motiver", "motivation"]):
            response = self.core.motivate()
            self.voice.speak(response)
            return response
        
        # Hjælp
        elif "hjælp" in command:
            response = """Jeg kan hjælpe dig med følgende:
- Sige hej (prøv 'hej' eller 'goddag')
- Fortælle tiden (prøv 'hvad er klokken?')
- Åbne hjemmesider (prøv 'åbn google.com')
- Gemme noter (prøv 'gem husk at købe mælk')
- Vise dine noter (prøv 'vis mine noter')
- Give motivation (prøv 'motiver mig')"""
            return response
            
        # Ukendt kommando
        else:
            response = "Beklager, jeg forstod ikke kommandoen. Prøv at sige 'hjælp' for at se hvad jeg kan."
            self.voice.speak(response)
            return response 
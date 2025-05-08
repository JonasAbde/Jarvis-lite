"""
Kommandohåndtering for Jarvis Lite.
"""

import os
import datetime
import logging
import webbrowser
import random
from typing import Optional, Dict, List, Any

# Import NLU-modulet for intent klassificering
from src.nlu import analyze

# Logger
logger = logging.getLogger(__name__)

# Stier
NOTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "notes")
NOTES_FILE = os.path.join(NOTES_DIR, "noter.txt")

# Hjælpefunktioner
def save_note(text: str) -> bool:
    """
    Gemmer en note til en tekstfil
    
    Args:
        text: Teksten der skal gemmes
        
    Returns:
        True hvis noten blev gemt, ellers False
    """
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
        return True
    except Exception as e:
        logger.error(f"Fejl ved gem af note: {e}")
        return False

def get_time() -> str:
    """
    Returnerer et naturligt svar med det aktuelle klokkeslæt
    
    Returns:
        Streng med klokkeslæt
    """
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    
    if minute == 0:
        return f"Klokken er præcis {hour}"
    else:
        return f"Klokken er {hour} og {minute} minutter"

def get_date() -> str:
    """
    Returnerer et naturligt svar med den aktuelle dato
    
    Returns:
        Streng med dato
    """
    now = datetime.datetime.now()
    # Oversæt måneden til dansk
    month_names = {
        1: "januar", 2: "februar", 3: "marts", 4: "april", 
        5: "maj", 6: "juni", 7: "juli", 8: "august", 
        9: "september", 10: "oktober", 11: "november", 12: "december"
    }
    weekday_names = {
        0: "mandag", 1: "tirsdag", 2: "onsdag", 3: "torsdag",
        4: "fredag", 5: "lørdag", 6: "søndag"
    }
    
    day = now.day
    month = month_names[now.month]
    year = now.year
    weekday = weekday_names[now.weekday()]
    
    return f"I dag er det {weekday} den {day}. {month} {year}"

def get_joke() -> str:
    """
    Returnerer en tilfældig dansk joke
    
    Returns:
        Streng med en joke
    """
    jokes = [
        "Hvorfor gik computeren til lægen? Den havde en virus!",
        "Hvad kalder man en gruppe musikalske hvaler? Et orkester!",
        "Hvorfor kunne skelettet ikke gå til festen? Det havde ingen krop at gå med!",
        "Hvorfor er bier så gode til at lave honning? Fordi de er bie-specialister!",
        "Hvad kaldte vikingerne deres e-mails? Plyndr-e-mails!",
        "Hvad sagde den ene væg til den anden væg? Vi mødes i hjørnet!",
        "Hvorfor var tallerkenerne så trætte? Fordi de havde været oppe hele natten!",
        "Hvad får man hvis man krydser en elefant med en kænguru? Store huller i hele Australien!",
        "Hvad laver en citron når den keder sig? Den sur-fer på internettet!",
        "Hvorfor var blæksprutten så god til at træne? Den havde mange arme at løfte med!",
        "Hvorfor har blæksprutter så svært ved at tage beslutninger? De har for mange valgmuligheder!",
        "Hvad kalder man en hund, der kan trække vejret under vand? En sø-hund!",
        "Hvad får man hvis man krydser en elektriker med en filosof? En tænkende lampe!",
        "Hvorfor kan fisk ikke spille klaver? De drukner i tangenterne!",
        "Hvorfor flyver fugle sydpå om vinteren? Det er for langt at gå!",
    ]
    return random.choice(jokes)

def open_website(site: str) -> str:
    """
    Åbner en hjemmeside i browseren
    
    Args:
        site: Navnet på siden der skal åbnes
        
    Returns:
        Respons til brugeren
    """
    try:
        if "youtube" in site.lower():
            webbrowser.open("https://www.youtube.com")
            return "Jeg åbner YouTube for dig. Hvad vil du se?"
        elif "google" in site.lower():
            webbrowser.open("https://www.google.com")
            return "Jeg åbner Google. Hvad vil du søge efter?"
        elif "dr" in site.lower() or "nyheder" in site.lower():
            webbrowser.open("https://www.dr.dk")
            return "Jeg åbner DR for dig. Vil du se nyheder eller noget andet?"
        elif "facebook" in site.lower():
            webbrowser.open("https://www.facebook.com")
            return "Jeg åbner Facebook for dig."
        elif "netflix" in site.lower():
            webbrowser.open("https://www.netflix.com")
            return "Jeg åbner Netflix. God fornøjelse med at se film!"
        elif "tv2" in site.lower():
            webbrowser.open("https://www.tv2.dk")
            return "Jeg åbner TV2's hjemmeside for dig."
        elif "gmail" in site.lower() or "e-mail" in site.lower() or "mail" in site.lower():
            webbrowser.open("https://www.gmail.com")
            return "Jeg åbner Gmail for dig. Har du fået nogle spændende mails?"
        elif "wikipedia" in site.lower():
            webbrowser.open("https://da.wikipedia.org")
            return "Jeg åbner Wikipedia. Hvad vil du slå op?"
        elif "amazon" in site.lower():
            webbrowser.open("https://www.amazon.com")
            return "Jeg åbner Amazon for dig. Hvad leder du efter?"
        elif "instagram" in site.lower():
            webbrowser.open("https://www.instagram.com")
            return "Jeg åbner Instagram for dig."
        else:
            return "Jeg ved ikke, hvordan jeg skal åbne den side. Prøv at specifik 'youtube', 'google' eller en anden kendt hjemmeside."
    except Exception as e:
        logger.error(f"Fejl ved åbning af hjemmeside: {e}")
        return "Jeg kunne ikke åbne hjemmesiden. Der opstod en fejl."

def handle_greeting() -> str:
    """
    Returnerer en passende hilsen baseret på tidspunkt
    
    Returns:
        Hilsenbsvar
    """
    time_of_day = datetime.datetime.now().hour
    if 5 <= time_of_day < 10:
        return "Godmorgen! Hvordan har du det i dag?"
    elif 10 <= time_of_day < 12:
        return "God formiddag! Hvordan går det?"
    elif 12 <= time_of_day < 18:
        return "God eftermiddag! Hvordan kan jeg hjælpe dig?"
    elif 18 <= time_of_day < 22:
        return "Godaften! Hvordan går det med dig?"
    else:
        return "Godaften! Det er sent. Hvad kan jeg hjælpe med?"

def handle_about_you() -> str:
    """
    Returnerer information om Jarvis
    
    Returns:
        Information om Jarvis
    """
    responses = [
        "Jeg er Jarvis, din danske AI-assistent. Jeg kan hjælpe dig med at svare på spørgsmål, finde information og udføre simple opgaver.",
        "Mit navn er Jarvis, og jeg er en AI-assistent, der kører lokalt på din computer. Jeg er designet til at svare på dansk og hjælpe med forskellige opgaver.",
        "Jeg hedder Jarvis og er din personlige assistent. Jeg forstår dansk og kan hjælpe med daglige opgaver og svare på spørgsmål.",
        "Jeg er en dansk AI-assistent ved navn Jarvis. Jeg kan hjælpe med tidsstyring, noter, jokes og samtaler."
    ]
    return random.choice(responses)

def get_weather() -> str:
    """
    Simulerer en vejrudsigt (da vi ikke har en ægte vejrintegration endnu)
    
    Returns:
        Simuleret vejrudsigt
    """
    # Simulerede temperaturforudsigelser
    temp_low = random.randint(5, 15)
    temp_high = temp_low + random.randint(3, 10)
    
    # Simulerede vejrforhold
    conditions = random.choice([
        "solskin", "lettere skyet", "overskyet", 
        "let regn", "regn", "torden",
        "sne", "tåge", "blæsende"
    ])
    
    # Simuleret sandsynlighed for regn
    rain_chance = random.randint(0, 100)
    
    responses = [
        f"I dag bliver det {conditions} med temperaturer mellem {temp_low} og {temp_high} grader. Der er {rain_chance}% chance for regn.",
        f"Vejrudsigten viser {conditions} i dag. Temperaturen vil være omkring {temp_high} grader på det varmeste.",
        f"I dag forventes {conditions}. Temperaturen kommer til at ligge mellem {temp_low} og {temp_high} grader.",
        f"Vejret i dag bliver {conditions} med temperaturer op til {temp_high} grader. Husk en paraply, da der er {rain_chance}% chance for regn.",
    ]
    
    # Tilføj en note om at dette er simuleret
    note = "\n\nBemærk: Dette er en simuleret vejrudsigt, da Jarvis endnu ikke har integration med en rigtig vejrtjeneste."
    
    return random.choice(responses) + note

def play_music() -> str:
    """
    Simulerer musikafspilning (da vi ikke har en ægte musikintegration endnu)
    
    Returns:
        Besked om musikafspilning
    """
    genres = ["pop", "rock", "jazz", "klassisk", "elektronisk", "hiphop", "ambient", "folk"]
    artists = ["kunstner", "band", "orkester", "komponist", "musiker"]
    
    genre = random.choice(genres)
    artist = random.choice(artists)
    
    responses = [
        f"Jeg ville gerne spille noget {genre} musik for dig, men jeg har ikke musikafspilningsfunktionalitet endnu.",
        f"Jeg forstår du gerne vil høre musik. Desværre har jeg ikke adgang til en musikafspiller lige nu.",
        f"Jeg kan desværre ikke afspille musik endnu, men det vil være en af de næste funktioner, der bliver implementeret.",
        f"Jeg ville elske at spille din yndlings {genre}, men jeg mangler musikintegrationen. Den kommer snart!"
    ]
    
    # Tilføj en note om at dette er simuleret
    note = "\n\nBemærk: Dette er en simuleret funktion, da Jarvis endnu ikke har integration med en musikafspiller."
    
    return random.choice(responses) + note

def handle_command(command: str, history: List[Dict[str, str]] = None) -> str:
    """
    Håndterer en kommando/input fra brugeren
    
    Args:
        command: Brugerens kommando/input
        history: Tidligere samtalehistorik
    
    Returns:
        Svar til brugeren
    """
    if not command or command.isspace():
        return "Jeg kunne ikke forstå, hvad du sagde. Kan du prøve igen?"
    
    # Analyser brugerens input med NLU
    command = command.strip()
    nlu_result = analyze(command)
    
    intent = nlu_result["intent"]
    confidence = nlu_result["confidence"]
    entities = nlu_result["entities"]
    
    logger.info(f"NLU-analyse: Intent='{intent}', Konfidens={confidence:.2f}, Entiteter={entities}")
    
    # Håndter den detekterede intent
    return execute_intent(intent, entities, command)

def execute_intent(intent: str, entities: Dict[str, Any] = None, original_text: str = "") -> str:
    """
    Udfører en specifik intent med eventuelle entiteter
    
    Args:
        intent: Intentionen (f.eks. "get_time", "open_website")
        entities: Entiteter relateret til intentionen (f.eks. {"site": "youtube"})
        original_text: Den originale brugerforespørgsel
    
    Returns:
        Svar til brugeren
    """
    entities = entities or {}
    
    if intent == "get_time":
        return get_time()
    
    elif intent == "get_date":
        return get_date()
    
    elif intent == "open_website":
        site = entities.get("site", "")
        return open_website(site)
    
    elif intent == "save_note":
        note = entities.get("text", original_text)
        if note:
            success = save_note(note)
            if success:
                return f"Jeg har gemt din note: '{note}'. Skal jeg læse den op for dig?"
            else:
                return "Jeg kunne ikke gemme noten. Prøv igen."
        else:
            return "Jeg kunne ikke finde teksten til noten."
    
    elif intent == "tell_joke":
        return get_joke()
    
    elif intent == "get_help":
        return "Jeg kan fortælle dig klokken og datoen, åbne hjemmesider som YouTube og Google, gemme noter, fortælle jokes, give dig vejrudsigten og snart afspille musik. Hvad vil du gerne have hjælp med?"
    
    elif intent == "greeting":
        return handle_greeting()
        
    elif intent == "about_you":
        return handle_about_you()
        
    elif intent == "goodbye":
        return "Farvel! Det var hyggeligt at snakke med dig. Vi ses igen senere."
    
    elif intent == "get_weather":
        return get_weather()
        
    elif intent == "play_music":
        return play_music()
    
    elif intent == "unknown":
        # Simpel fallback
        fallbacks = [
            "Det forstod jeg ikke helt. Kan du omformulere dit spørgsmål?",
            "Jeg er ikke sikker på, hvad du mener. Prøv at spørge på en anden måde.",
            "Beklager, men jeg forstod ikke det. Kan du prøve at formulere det anderledes?",
            "Hmm, det er jeg ikke helt med på. Kan du være mere specifik?"
        ]
        return random.choice(fallbacks)
    
    else:
        return f"Jeg forstår din forespørgsel, men kan ikke håndtere '{intent}' lige nu." 
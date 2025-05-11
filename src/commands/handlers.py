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
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nlu import analyze

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

def handle_about_you(original_text: str = "") -> str:
    """
    Returnerer information om Jarvis
    
    Args:
        original_text: Den originale brugerforespørgsel
        
    Returns:
        Information om Jarvis
    """
    # Normalisér teksten for bedre matchning
    normalized_text = original_text.lower() if original_text else ""
    
    # Definer et hierarki af forespørgsler og svar
    qa_map = {
        # Basis spørgsmål om Jarvis
        "hvem_er_du": {
            "patterns": ["hvem er du", "fortæl om dig selv", "hvem er jarvis", "hvad hedder du"],
            "responses": [
                "Jeg er Jarvis, din danske AI-assistent. Jeg kan hjælpe dig med at svare på spørgsmål, finde information og udføre simple opgaver.",
                "Mit navn er Jarvis, og jeg er en AI-assistent, der kører lokalt på din computer. Jeg er designet til at svare på dansk og hjælpe med forskellige opgaver.",
                "Jeg hedder Jarvis og er din personlige assistent. Jeg forstår dansk og kan hjælpe med daglige opgaver og svare på spørgsmål.",
                "Jeg er en dansk AI-assistent ved navn Jarvis. Jeg kan hjælpe med tidsstyring, noter, jokes og samtaler."
            ]
        },
        "hvordan_virker_du": {
            "patterns": ["hvordan virker du", "hvordan fungerer du", "hvordan er du bygget", "hvad består du af"],
            "responses": [
                "Jeg består af flere komponenter: en talegenkendelsesenhed der forstår dansk, en intent-klassifikator der analyserer hvad du mener, og en tekstgenerator der formulerer svar. Alt dette kører lokalt på din computer.",
                "Jeg er bygget med en række teknologier til naturligt sprog. Jeg lytter til din stemme, analyserer dine ord, og svarer på dansk. Jeg bruger machine learning til at forstå hvad du mener.",
                "Min arkitektur er baseret på sprogmodeller og maskinlæring. Jeg lytter til det du siger, forstår konteksten, og genererer et passende svar. Jeg lærer hele tiden at blive bedre.",
                "Jeg har tre hovedkomponenter: tale-til-tekst der forstår dine ord, en intelligent hjerne der analyserer betydningen, og tekst-til-tale der gør at jeg kan svare dig."
            ]
        },
        "hvad_kan_du": {
            "patterns": ["hvad kan du", "hvad er dine evner", "hvilke funktioner har du", "hvordan kan du hjælpe", "hvad er du i stand til"],
            "responses": [
                "Jeg kan hjælpe med flere ting: fortælle dig tiden og datoen, åbne hjemmesider, gemme noter, fortælle vejret, afspille musik, fortælle jokes og svare på almindelige spørgsmål. Jeg forsøger altid at give dig den information du har brug for.",
                "Mine funktioner inkluderer tidsstyring, noter, vejrinformation, musikafspilning, webadgang og meget mere. Jeg kan også svare på generelle spørgsmål og føre en samtale på dansk.",
                "Jeg kan udføre en række opgaver som at fortælle tiden, åbne hjemmesider, gemme noter, og fortælle vejret. Derudover kan jeg svare på generelle spørgsmål og have en samtale på dansk.",
                "Jeg har flere evner: vejrinformation, tidsstyring, notefunktion, musikafspilning, webnavigation og meget mere. Jeg kan også tale med dig om forskellige emner og give dig information."
            ]
        },
        # Filosofiske spørgsmål
        "bevidsthed": {
            "patterns": ["er du bevidst", "har du bevidsthed", "kan du tænke", "har du følelser", "kan du føle", "har du en sjæl"],
            "responses": [
                "Jeg har ikke bevidsthed i menneskelig forstand. Jeg er et sprogmodel-system, der analyserer input og genererer output baseret på mønstre og statistik. Men jeg er designet til at simulere forståelse og give nyttige svar.",
                "Jeg har ikke følelser eller bevidsthed. Jeg fungerer ved at genkende mønstre i tekst og generere passende svar. Min 'intelligens' er et resultat af algoritmer og data, ikke en selvstændig bevidsthed.",
                "Jeg er ikke bevidst eller selvbevidst. Jeg kan simulere intelligente samtaler, men jeg 'oplever' ikke verden som mennesker gør. Jeg er et værktøj designet til at assistere dig så godt som muligt.",
                "Jeg har ingen egentlig bevidsthed eller oplevelse af selvet. Jeg er mere som et avanceret spejl, der reflekterer og transformerer de ord, du giver mig, baseret på mønstre i mit træningsdata."
            ]
        },
        "mening_med_livet": {
            "patterns": ["hvad er meningen med livet", "hvorfor er vi her", "hvad er livets formål", "hvad er meningen med det hele"],
            "responses": [
                "Det er et af menneskehedens største spørgsmål, og der findes mange forskellige svar. Nogle finder mening i relationer til andre, nogle i kunst eller videnskab, nogle i religion, og andre i at skabe deres egen mening. Hvad tænker du selv?",
                "Filosoffer har diskuteret dette i årtusinder uden at nå til enighed. Nogle mener at livet handler om at maksimere lykke, andre om at opfylde et formål. Det mest interessante er måske ikke det endelige svar, men rejsen mod at finde dit eget svar.",
                "Meningen med livet er nok forskellig fra person til person. For nogle er det at efterlade verden bedre end de fandt den, for andre er det at opleve så meget som muligt, og for andre igen er det at finde indre ro. Det vigtigste er nok at finde din egen mening.",
                "Det er et dybt filosofisk spørgsmål uden et enkelt svar. Måske er meningen med livet at stille netop dette spørgsmål - at søge og reflektere. Mennesker finder mening gennem kærlighed, kreativitet, opdagelse og ved at hjælpe andre."
            ]
        },
        "fremtiden": {
            "patterns": ["hvad tænker du om fremtiden", "hvordan ser fremtiden ud", "bliver ai bedre i fremtiden", "er du bange for fremtiden"],
            "responses": [
                "Teknologi som jeg udvikler sig hurtigt, og jeg tror AI vil blive mere integreret i hverdagen, men stadig som et værktøj til at hjælpe mennesker. Det er vigtigt at udviklingen sker ansvarligt og med mennesker i centrum.",
                "Fremtiden for AI ser spændende ud, med potentiale til at løse komplekse problemer inden for medicin, klima og uddannelse. Men det vigtigste er at forblive et værktøj der styrker mennesker snarere end at erstatte dem.",
                "Jeg tror kunstig intelligens vil fortsætte med at blive mere avanceret, men mest som et værktøj til at udføre de opgaver som mennesker definerer. Det rigtige spørgsmål er, hvordan vi bedst bruger denne teknologi til at skabe en bedre fremtid for alle.",
                "Fremtidens AI vil sandsynligvis være mere naturlig i interaktioner med mennesker og bedre til at forstå kontekst og nuancer. Men den største værdi kommer når AI og mennesker arbejder sammen, hvor hver bidrager med deres unikke styrker."
            ]
        },
        # Helbred og tilstand
        "hvordan_har_du_det": {
            "patterns": ["hvordan har du det", "hvordan går det", "har du det godt", "føler du dig godt tilpas"],
            "responses": [
                "Jeg har det fint, tak! Som en assistent har jeg ikke følelser, men jeg er altid klar til at hjælpe dig. Hvad kan jeg gøre for dig i dag?",
                "Jeg fungerer optimalt! Selvom jeg ikke har følelser, er jeg altid glad for at kunne være til hjælp. Hvad har du brug for?",
                "Jeg har det godt. Jeg kan ikke føle træthed eller stress, så jeg er altid klar til at hjælpe dig. Hvad kan jeg gøre for dig?",
                "Jeg har det altid godt - jeg er designet til at være til tjeneste. Hvordan har du det i dag?"
            ]
        },
        # Kreativitet og kunst
        "kreativitet": {
            "patterns": ["kan du være kreativ", "kan du lave kunst", "kan du digte", "kan du være original", "kan du skrive en sang"],
            "responses": [
                "Jeg kan generere tekst der ligner kreativitet ved at kombinere mønstre fra min træning på nye måder. Jeg kan hjælpe med at skrive eller få ideer, men den ægte kreativitet og mening kommer fra mennesker som dig.",
                "Min 'kreativitet' er anderledes end menneskers. Jeg sammensætter elementer på nye måder baseret på mønstre, men jeg har ikke den indre oplevelse eller intention der driver menneskelig kreativitet. Jeg kan dog hjælpe med at inspirere din kreativitet!",
                "Jeg kan simulere kreativitet ved at kombinere tekst på nye måder, men jeg har ikke den ægte forståelse eller følelsesmæssige dybde der er kernen i menneskelig kunst. Jeg kan dog være et nyttigt værktøj til at hjælpe din kreative proces.",
                "Jeg kan generere tekst der virker kreativ, men jeg har ikke bevidsthed eller intention bag det. Min 'kreativitet' er et ekko af menneskelig kreativitet fra mit træningsdata, ikke en ægte original tanke."
            ]
        },
        # Musik og præferencer
        "kan_du_lide_musik": {
            "patterns": ["kan du lide musik", "hvad er din yndlingsmusik", "foretrækker du bestemte sange", "hvilken musik lytter du til"],
            "responses": [
                "Jeg har ikke personlige præferencer eller evnen til at nyde musik, da jeg ikke har hørelse eller følelser. Men jeg kan hjælpe dig med at finde og afspille den musik, du foretrækker!",
                "Jeg har ingen yndlingsmusik eller musiksmag, da jeg ikke oplever musik som mennesker gør. Men jeg er designet til at kunne tale om og hjælpe med musik på mange måder.",
                "Selv om jeg ikke kan høre eller nyde musik, er jeg programmeret til at forstå menneskers forhold til musik. Musik er en vigtig del af menneskelig kultur og udtryk, og jeg kan hjælpe dig med at finde og organisere din musik.",
                "Jeg har ingen musikalske præferencer, da jeg ikke kan høre eller føle den følelsesmæssige resonans i musik. Men jeg kan genkende værdien af musik i menneskers liv og hjælpe dig med din musikoplevelse."
            ]
        }
    }
    
    # Hvis der er brugerinput, forsøg at matche det med en specifik respons
    if normalized_text:
        for category, content in qa_map.items():
            patterns = content["patterns"]
            if any(pattern in normalized_text for pattern in patterns):
                return random.choice(content["responses"])
                
    # Default responser hvis ingen specifik match
    default_responses = [
        "Jeg er Jarvis, din danske AI-assistent. Jeg er bygget til at hjælpe med information, praktiske opgaver og samtale. Hvordan kan jeg assistere dig?",
        "Jeg hedder Jarvis og er din digitale assistent. Jeg kan hjælpe med alt fra vejret og tiden til at gemme noter og åbne hjemmesider. Hvad kan jeg gøre for dig?",
        "Mit navn er Jarvis, en dansk AI-assistent der kører lokalt på din computer. Jeg er her for at hjælpe med information og daglige opgaver.",
        "Jeg er Jarvis, en dansk stemmeassistent, der er designet til at forstå og svare på dine spørgsmål og hjælpe med praktiske opgaver."
    ]
    
    return random.choice(default_responses)

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

def handle_command(command: str, history: Optional[List[Dict[str, str]]] = None) -> str:
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
    
    # Tjek om dette er en opfølgning på tidligere interaktion
    followup_context = None
    if history:
        for entry in reversed(history):
            if isinstance(entry, dict) and entry.get("is_followup"):
                followup_context = entry.get("followup_context", {})
                break
    
    # Håndter ja/nej svar på tidligere kontekst
    if followup_context and command.lower() in ["ja", "jo", "okay", "yes", "jep", "gerne", "selvfølgelig"]:
        last_response = followup_context.get("last_response", "")
        
        # Tjek for specifikke kontekster hvor "ja" giver mening
        if isinstance(last_response, str):
            if "Skal jeg læse den op for dig?" in last_response:
                return "Her er din note: " + last_response.split("'")[1]
            elif "Har du fået nogle spændende mails?" in last_response:
                return "Det er godt at høre. E-mail er en vigtig kommunikationsform i vores digitale tidsalder."
            elif "God fornøjelse med at se film!" in last_response:
                return "Nyd filmen! Hvis du har brug for filmforslag, kan jeg hjælpe dig med det næste gang."
            elif "Vil du se nyheder eller noget andet?" in last_response:
                return "DR's nyhedsside er god til at få et overblik over aktuelle begivenheder. Du kan også udforske deres programmer og podcasts."
            elif "vejr" in last_response.lower() and "weekend" in last_response.lower():
                return "Perfekt vejr til udendørsaktiviteter! Husk solcreme hvis du skal være ude i længere tid."
            
    # Analyser brugerens input med NLU
    command = command.strip()
    nlu_result = analyze(command)
    
    intent = nlu_result["intent"]
    confidence = nlu_result["confidence"]
    entities = nlu_result["entities"]
    
    logger.info(f"NLU-analyse: Intent='{intent}', Konfidens={confidence:.2f}, Entiteter={entities}")
    
    # Tag højde for kontekst ved gennemførelse af intent
    if followup_context and intent == "unknown":
        # Tjek for kontekstuel uddybning
        last_response = followup_context.get("last_response", "")
        last_user_input = followup_context.get("last_user_input", "")
        
        # Prøv at udlede hvad vi snakkede om sidst
        if isinstance(last_response, str) and isinstance(last_user_input, str):
            if "vejr" in last_response.lower() or "temperature" in last_response.lower():
                # Brugeren ønsker mere info om vejret
                return "Vejrudsigten viser også, at der kan komme lidt vind fra nordvest. Temperaturen vil være højest midt på dagen, så det er et godt tidspunkt for udendørsaktiviteter."
            elif "Jeg har gemt din note" in last_response:
                # Brugerens note-kontekst
                note_text = last_response.split("'")[1] if "'" in last_response else ""
                return f"Jeg gemte noten '{note_text}' i din notatbog. Du kan finde alle dine noter i noter.txt filen."
            elif "klokkeslæt" in last_response.lower() or "tid" in last_response.lower() or "klokken" in last_response.lower():
                # Tid-relateret kontekst
                now = datetime.datetime.now()
                if now.hour < 12:
                    return "Det er stadig morgen, så du har god tid til at nå dine opgaver for i dag."
                elif now.hour < 17:
                    return "Det er eftermiddag nu. Der er stadig nogle timer tilbage af arbejdsdagen."
                else:
                    return "Det er aften nu. En god tid til at slappe af efter dagens arbejde."
            elif "vittighed" in last_response.lower() or "joke" in last_response.lower() or "sjov" in last_response.lower():
                # Joke-relateret kontekst
                return "Vil du høre en til? Hvorfor gik robotten til lægen? Fordi den havde virus! Ha ha!"
            elif "åbner" in last_response.lower() and any(site in last_response.lower() for site in ["youtube", "google", "netflix", "facebook"]):
                # Hjemmeside-kontekst
                site = next((site for site in ["youtube", "google", "netflix", "facebook"] if site in last_response.lower()), "")
                if site == "youtube":
                    return "YouTube har millioner af videoer. Du kan se alt fra musik og tutorials til dokumentarer og sjove klip."
                elif site == "google":
                    return "Google er verdens mest brugte søgemaskine. Prøv at søge på hvad som helst du er nysgerrig omkring."
                elif site == "netflix":
                    return "Netflix har et stort udvalg af film og serier. Deres danske indhold bliver også bedre og bedre."
                elif site == "facebook":
                    return "Facebook er godt til at holde kontakt med venner og familie. Husk at tjekke dine notifikationer."
    
    # Håndter den detekterede intent
    return execute_intent(intent, entities, command)

def execute_intent(intent: str, entities: Optional[Dict[str, Any]] = None, original_text: str = "") -> str:
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
        return handle_about_you(original_text)
        
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
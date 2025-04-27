import streamlit as st
from datetime import datetime
import time
from core.speech import DanSpeechVoice, logger
from core.tts import TextToSpeech
import queue

# Initialiser DanSpeechVoice og TextToSpeech i session state hvis de ikke findes
if 'voice_system' not in st.session_state:
    try:
        st.session_state.voice_system = DanSpeechVoice()
        st.session_state.voice_error = None
    except Exception as e:
        st.session_state.voice_system = None
        st.session_state.voice_error = f"Fejl ved initialisering af DanSpeech: {e}"
        logger.error(f"DanSpeech init error: {e}")
if 'tts_system' not in st.session_state:
    st.session_state.tts_system = TextToSpeech()
if 'plugins' not in st.session_state:
    st.session_state.plugins = {
        "Noter": [],
        "Lys": {"status": "Slukket"},
        "Log": [f"{datetime.now().strftime('%H:%M:%S')}: Dashboard startet"],
        "Plugins": ["Noter", "Lys", "Log", "Plugins", "Indstillinger", "Stemme"]
    }
if 'status_message' not in st.session_state:
    st.session_state.status_message = ""

def handle_command(command):
    response = None
    tts = st.session_state.tts_system

    if not command:
        return

    # === DEBUG LOGGING START ===
    logger.debug(f"handle_command modtog rå tekst: '{command}'")
    # === DEBUG LOGGING SLUT ===
    command_lower = command.lower()
    # === DEBUG LOGGING START ===
    logger.debug(f"handle_command konverteret til lowercase: '{command_lower}'")
    # === DEBUG LOGGING SLUT ===
    log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Modtog kommando: '{command}'"
    logger.info(log_entry)
    st.session_state.plugins["Log"].append(log_entry)

    # Tjek for nøgleord i stedet for eksakte sætninger
    if "tænd" in command_lower and "lys" in command_lower:
        st.session_state.plugins["Lys"]["status"] = "Tændt"
        log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Lys tændt."
        response = "Okay, jeg tænder lyset."
        logger.info(log_entry)
        st.session_state.plugins["Log"].append(log_entry)
    elif "sluk" in command_lower and "lys" in command_lower:
        st.session_state.plugins["Lys"]["status"] = "Slukket"
        log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Lys slukket."
        response = "Okay, jeg slukker lyset."
        logger.info(log_entry)
        st.session_state.plugins["Log"].append(log_entry)
    # Bevar mere specifikke tjek for note, da vi skal udtrække indhold
    elif "tilføj note" in command_lower or "gem note" in command_lower:
        # Prøv at fange indholdet efter 'note'
        parts = command_lower.split("note", 1)
        note_content = ""
        if len(parts) > 1:
            note_content = parts[1].strip()
            
        # Fallback: Prøv at fange indhold efter 'tilføj' eller 'gem'
        if not note_content:
            if "tilføj" in command_lower:
                 parts = command_lower.split("tilføj", 1)
                 if len(parts) > 1: note_content = parts[1].strip()
            elif "gem" in command_lower:
                 parts = command_lower.split("gem", 1)
                 if len(parts) > 1: note_content = parts[1].strip()

        if note_content:
            # Brug den oprindelige case til noten, hvis muligt
            original_parts = command.split(re.search(r'(tilføj|gem)\s+note', command, re.IGNORECASE).group(0), 1)
            original_note = original_parts[1].strip() if len(original_parts) > 1 else note_content
            
            st.session_state.plugins["Noter"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {original_note}")
            log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Note tilføjet: '{original_note}'"
            response = f"Notat tilføjet: {original_note}"
            logger.info(log_entry)
            st.session_state.plugins["Log"].append(log_entry)
        else:
            log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Forsøgte at tilføje tom note (genkendt: '{command}')."
            response = "Hvad skal noten indeholde?"
            logger.warning(log_entry)
            st.session_state.plugins["Log"].append(log_entry)
    else:
        log_entry = f"{datetime.now().strftime('%H:%M:%S')}: Ukendt kommando: '{command}'"
        response = "Jeg forstod ikke kommandoen."
        logger.warning(log_entry)
        st.session_state.plugins["Log"].append(log_entry)

    if tts and response:
        tts.speak(response)
        st.session_state.status_message = response
    else:
        st.session_state.status_message = "Kommando behandlet (intet svar)." 

    st.rerun()

def sidebar_menu():
    st.sidebar.image("https://img.icons8.com/fluency/96/000000/jarvis.png", width=80)
    st.sidebar.title("Jarvis Lite")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Noter", "Lys", "Log", "Plugins", "Indstillinger", "Stemme"])
    
    st.sidebar.header("Stemmestyring")
    if st.session_state.voice_system:
        is_listening = st.session_state.voice_system.is_listening
        if is_listening:
            if st.sidebar.button("Stop Lytning ", key="stop_listen_btn"):
                st.session_state.voice_system.stop_listening()
                st.session_state.plugins["Log"].append(f"{datetime.now().strftime('%H:%M:%S')}: Stemmelytning stoppet.")
                st.rerun() 
            st.sidebar.caption("Status: Lytter...")
        else:
            if st.sidebar.button("Start Lytning ", key="start_listen_btn"):
                st.session_state.voice_system.start_listening()
                st.session_state.plugins["Log"].append(f"{datetime.now().strftime('%H:%M:%S')}: Stemmelytning startet.")
                st.rerun() 
            st.sidebar.caption("Status: Ikke aktiv")
            
    else:
        st.sidebar.error("Stemmestyring deaktiveret.")
        if st.session_state.voice_error:
             st.sidebar.error(st.session_state.voice_error)

    return page

def dashboard_page():
    st.header(":house: Smart Home Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Status", "Online", "+0")
        st.metric("Lys", st.session_state.plugins["Lys"]["status"])
    with col2:
        log_entry = st.session_state.plugins['Log'][-1] if st.session_state.plugins['Log'] else 'Ingen'
        st.success(f"Seneste aktivitet: {log_entry}")
    st.info("Styr dit hjem, se status og tilføj plugins!")

def notes_page():
    st.header(":memo: Noter")
    note = st.text_input("Tilføj en note")
    if st.button("Gem note"):
        st.session_state.plugins["Noter"].append(f"{datetime.now().strftime('%H:%M:%S')}: {note}")
        st.session_state.plugins["Log"].append(f"{datetime.now().strftime('%H:%M:%S')}: Note gemt: {note}")
        st.success("Note gemt!")
    st.subheader("Gemte noter:")
    for n in reversed(st.session_state.plugins["Noter"]):
        st.write(n)

def lights_page():
    st.header(":bulb: Lysstyring")
    if st.button("Tænd lys"):
        st.session_state.plugins["Lys"]["status"] = "Tændt"
        st.session_state.plugins["Log"].append(f"{datetime.now().strftime('%H:%M:%S')}: Lys tændt")
    if st.button("Sluk lys"):
        st.session_state.plugins["Lys"]["status"] = "Slukket"
        st.session_state.plugins["Log"].append(f"{datetime.now().strftime('%H:%M:%S')}: Lys slukket")
    st.metric("Status", st.session_state.plugins["Lys"]["status"])

def log_page():
    st.header(":scroll: Systemlog")
    for entry in reversed(st.session_state.plugins["Log"]):
        st.write(entry)

def plugins_page():
    st.header(":electric_plug: Plugins")
    st.write("Aktive plugins:")
    for p in st.session_state.plugins["Plugins"]:
        st.write(f"- {p}")
    st.info("Tilføj eller fjern plugins direkte i softwaren!")

def settings_page():
    st.header(":gear: Indstillinger")
    st.write("Her kan du ændre systemindstillinger (simuleret)")
    st.code("mode: auto\nhardware: ...\nplugins: ...", language="yaml")

def voice_page():
    st.header(":microphone: Stemmestyring")
    st.write("Aktiver/deaktiver stemmestyring fra sidebaren.")
    st.subheader("Sådan virker det:")
    st.write("1. Klik 'Start Lytning'.")
    st.write("2. Tal tydeligt dine kommandoer (f.eks. 'tænd lys', 'sluk lys', 'tilføj note husk mælk').")
    st.write("3. Systemet genkender kommandoen og udfører handlingen.")
    st.write("4. Se loggen for genkendte kommandoer.")
    st.subheader("Understøttede kommandoer (eksempel):")
    st.code("- Tænd lys\n- Sluk lys\n- Tilføj note [din note her]", language="text")


def start_web_dashboard():
    st.set_page_config(page_title='Jarvis Lite Dashboard', layout='wide')
    
    # Initialiser systemer hvis de mangler
    if 'voice_system' not in st.session_state:
        try:
            st.session_state.voice_system = DanSpeechVoice()
            st.session_state.voice_error = None
        except Exception as e:
            st.session_state.voice_system = None
            st.session_state.voice_error = f"Fejl: {e}"
            logger.error(f"DanSpeech init error: {e}")
            
    if 'tts_system' not in st.session_state:
        st.session_state.tts_system = TextToSpeech()
    if 'plugins' not in st.session_state:
        st.session_state.plugins = {
            "Noter": [],
            "Lys": {"status": "Slukket"},
            "Log": [f"{datetime.now().strftime('%H:%M:%S')}: Dashboard genstartet."]
        }
    if 'status_message' not in st.session_state:
         st.session_state.status_message = ""

    # Hent systemer fra session state
    voice = st.session_state.voice_system

    # Sidebar (kaldes nu kun for at få sidevalg og vise knapper)
    page = sidebar_menu()

    # --- FLYT TJEK FOR NYE KOMMANDOER HERHEN (Opdateret til Queue) ---
    command_to_process = None
    if voice and hasattr(voice, 'command_queue'):
        try:
            # Hent en kommando fra køen UDEN at blokere
            command_to_process = voice.command_queue.get_nowait()
            if command_to_process:
                logger.info(f"Kommando hentet fra kø: '{command_to_process}'")
        except queue.Empty:
            # Køen er tom, ingen ny kommando
            pass 
        except Exception as e:
             logger.error(f"Fejl ved hentning fra command_queue: {e}")
             command_to_process = None # Sørg for at vi ikke behandler en fejl

    # Behandl kommandoen HVIS der er en ny
    if command_to_process:
        handle_command(command_to_process)
        # handle_command kalder st.rerun() til sidst, så UI opdateres

    # Hovedindhold baseret på valgt side
    st.markdown("""
        <style>
            .stApp {background: linear-gradient(120deg, #232526, #414345 80%, #232526); color: #fff;}
            .css-1d391kg {color: #fff !important;}
            .css-1v0mbdj {background: #232526 !important;}
        </style>
    """, unsafe_allow_html=True)
    if st.session_state.status_message:
        st.info(st.session_state.status_message)
        st.session_state.status_message = "" 
    if page == "Dashboard":
        dashboard_page()
    elif page == "Noter":
        notes_page()
    elif page == "Lys":
        lights_page()
    elif page == "Log":
        log_page()
    elif page == "Plugins":
        plugins_page()
    elif page == "Indstillinger":
        settings_page()
    elif page == "Stemme":
        voice_page() 

if __name__ == '__main__':
    start_web_dashboard()

# Undertrykker TensorFlow og andre advarsler
import os
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Deaktiverer TensorFlow INFO og WARNING beskeder
# Deaktiverer warnings fra Keras/TensorFlow
import warnings
warnings.filterwarnings('ignore')

import datetime
import webbrowser
import time
from gtts import gTTS
from playsound import playsound
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import random

# Konfigurer simpel logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Funktion til at gemme noter
def save_note(note_text):
    notes_file = "notes.txt"
    try:
        with open(notes_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp}: {note_text}\n")
        logging.info(f"Note gemt: {note_text}")
        return "Noten er gemt."
    except Exception as e:
        logging.error(f"Fejl ved gemning af note: {e}")
        return "Beklager, jeg kunne ikke gemme noten."

# Funktion til at tale med gTTS
def speak_gtts(text, lang='da'):
    """Genererer tale med gTTS, gemmer som temp fil, afspiller og sletter."""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        temp_file = "temp_speech.mp3"
        tts.save(temp_file)
        logging.info(f"Afspiller tale: '{text}'")
        playsound(temp_file)
        # En lille pause kan forhindre problemer med hurtig filsletning
        time.sleep(0.1) 
        os.remove(temp_file)
        return True # Succes
    except Exception as e:
        logging.error(f"Fejl under gTTS/playsound: {e}", exc_info=True)
        # Fallback til print hvis tale fejler
        print(f"(gTTS Fejl - Svar): {text}") 
        return False # Fejl

# Funktion til at håndtere kommandoer
def handle_text_command(command):
    # ML-baseret intentgenkendelse
    intent = predict_intent(command)
    should_continue = True
    if intent == 'GetTime':
        response = get_time()
    elif intent == 'OpenYouTube':
        response = open_youtube()
    elif intent == 'OpenDR':
        response = open_dr()
    elif intent == 'SaveNote':
        speak_gtts(random.choice([
            "Hvad vil du gemme i noten?", 
            "Jeg er klar til at skrive. Hvad skal jeg notere?", 
            "Hvad skal der stå i noten? 📝"
        ]))
        note = input("Noten: ")
        response = save_note(note)
    elif intent == 'Greet':
        response = say_hello()
    elif intent == 'Identify':
        response = say_identity()
    elif intent == 'Goodbye':
        response = say_goodbye()
        should_continue = False
    else:
        response = random.choice([
            "Jeg forstod ikke kommandoen. Prøv igen.",
            "Undskyld, jeg er ikke sikker på, hvad du mener. Kan du omformulere det?",
            "Det forstod jeg desværre ikke. Prøv at sige det på en anden måde.",
            "Hmm, jeg er ikke sikker på, hvad du mener. Prøv igen? 🤔"
        ])
    
    # Tal svaret med gTTS
    speak_gtts(response) 

    return should_continue

# Funktion til at få klokken
def get_time():
    now = datetime.datetime.now()
    hour = int(now.strftime('%H'))
    
    # Forskellige svar baseret på tidspunkt på dagen
    if 5 <= hour < 10:
        greeting = "God morgen! "
    elif 10 <= hour < 18:
        greeting = random.choice(["Lige nu ", "På dette tidspunkt "])
    elif 18 <= hour < 23:
        greeting = "God aften! "
    else:
        greeting = "Selv på denne sene time er "
        
    return f"{greeting}Klokken er {now.strftime('%H:%M')} ⏰"

# Funktion til at åbne YouTube
def open_youtube():
    try:
        webbrowser.open("https://www.youtube.com")
        return random.choice([
            "Jeg har åbnet YouTube for dig.",
            "YouTube er nu klar til brug. God fornøjelse! 🎬",
            "YouTube åbnes nu. Hvad skal du se? 📺",
            "Jeg har startet YouTube til dig. Nyd det!"
        ])
    except Exception as e:
        logging.error(f"Fejl ved åbning af webbrowser: {e}")
        return "Beklager, jeg kunne ikke åbne YouTube. Er du forbundet til internettet? 🔌"

# Funktion til at åbne DR
def open_dr():
    try:
        webbrowser.open("https://www.dr.dk")
        return random.choice([
            "Jeg har åbnet DR for dig.",
            "DR's hjemmeside er nu åben. God fornøjelse! 📰",
            "DR åbnes nu. Måske er der spændende nyheder? 📺",
            "Jeg har startet DR til dig. Nyd indholdet!"
        ])
    except Exception as e:
        logging.error(f"Fejl ved åbning af webbrowser: {e}")
        return "Beklager, jeg kunne ikke åbne DR. Er din internetforbindelse aktiv? 🔌"

# Funktion til at sige hej
def say_hello():
    now = datetime.datetime.now()
    hour = int(now.strftime('%H'))
    
    # Tidspunkt-baseret hilsen
    if 5 <= hour < 10:
        time_greet = random.choice([
            "God morgen! Har du sovet godt? ☀️",
            "Godmorgen! Klar til en ny dag? 🌞",
            "Hej og godmorgen! Hvad kan jeg hjælpe med i dag? 🌅"
        ])
    elif 10 <= hour < 18:
        time_greet = random.choice([
            "Hej med dig! Hvordan kan jeg hjælpe? 😊",
            "Goddag! Hvad kan jeg gøre for dig i dag? 👋",
            "Hallo! Jeg er klar til at assistere dig. 👩‍💻"
        ])
    elif 18 <= hour < 23:
        time_greet = random.choice([
            "God aften! Hvordan går det? 🌙",
            "Hej! Hvordan har din dag været? 🌆",
            "Godaften! Kan jeg hjælpe dig med noget? 🌃"
        ])
    else:
        time_greet = random.choice([
            "Godnat! Du er stadig oppe? 🌜",
            "Hej, selv på denne sene time. Hvad kan jeg hjælpe med? 🌠",
            "Godaften - eller er det godnat? Hvordan kan jeg hjælpe? 🌙"
        ])
    
    return time_greet

# Funktion til at identificere sig selv
def say_identity():
    return random.choice([
        "Jeg er Jarvis Lite, en simpel AI-assistent. 🤖",
        "Mit navn er Jarvis Lite. Jeg er programmeret til at hjælpe dig med simple opgaver. 💻",
        "Jeg hedder Jarvis Lite, og jeg er din personlige digitale assistent. 🖥️",
        "Jarvis Lite er mit navn - din virtuelle hjælper i den digitale verden! 🌐"
    ])

# Funktion til at sige farvel
def say_goodbye():
    now = datetime.datetime.now()
    hour = int(now.strftime('%H'))
    
    if 22 <= hour or hour < 5:
        return random.choice([
            "Farvel og sov godt! 💤",
            "Godnat! Vi ses igen en anden dag. 🌙",
            "Sov godt! Jarvis lukker ned. 🌜"
        ])
    else:
        return random.choice([
            "Farvel! Hav en god dag. 👋",
            "Det var hyggeligt at snakke. Farvel for nu! 😊",
            "På gensyn! Jeg er her når du har brug for mig igen. ✨",
            "Farvel! Tak fordi du brugte Jarvis Lite i dag. 🤖"
        ])

# --- NLU med TensorFlow ---
intents = {
    'GetTime': ["hvad er klokken", "hvad tid er det", "vis mig tiden", "fortæl klokken", "tid nu", 
                "hvad lyder klokken", "kan du fortælle mig tiden", "hvor meget er klokken"],
    'OpenYouTube': ["åbn youtube", "start youtube", "gå til youtube", "vis youtube", 
                    "jeg vil se youtube", "youtube", "vil du åbne youtube", "vis mig youtube"],
    'OpenDR': ["åbn dr", "gå til dr", "vis dr", "dr", "jeg vil se dr", 
               "vil du åbne dr", "start dr", "vis mig dr"],
    'SaveNote': ["gem note", "tag en note", "skriv en note", "husk dette", 
                 "skriv ned", "noter", "lav en note", "gem dette"],
    'Greet': ["hej", "goddag", "hallo", "hej jarvis", "god morgen", "godaften", 
              "hejsa", "dav", "hey", "hi"],
    'Identify': ["hvem er du", "hvad hedder du", "hvad er dit navn", "fortæl om dig selv", 
                 "hvad kan du", "hvad er du", "introducér dig selv", "fortæl hvem du er"],
    'Goodbye': ["farvel", "slut", "exit", "luk ned", "vi ses", "hej hej", 
                "stop", "afslut", "på gensyn", "lukke", "godnat"]
}

# Forbered data
sentences, labels = [], []
label_map = {}
for idx, (intent, examples) in enumerate(intents.items()):
    label_map[idx] = intent
    for ex in examples:
        sentences.append(ex)
        labels.append(idx)
labels = np.array(labels)

# Tokenizer & sequences
tokenizer = Tokenizer(oov_token="<OOV>")
tokenizer.fit_on_texts(sentences)
sequences = tokenizer.texts_to_sequences(sentences)
max_len = max(len(seq) for seq in sequences)
padded = pad_sequences(sequences, maxlen=max_len, padding='post')

# Byg og træn model
vocab_size = len(tokenizer.word_index) + 1
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(vocab_size, 16, input_length=max_len),
    tf.keras.layers.GlobalAveragePooling1D(),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(len(intents), activation='softmax')
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
# Træn modellen (kører hurtigt med få datasæt)
model.fit(padded, labels, epochs=200, verbose=0)

def predict_intent(text):
    seq = tokenizer.texts_to_sequences([text.lower()])
    padded_seq = pad_sequences(seq, maxlen=max_len, padding='post')
    pred = model.predict(padded_seq)
    idx = np.argmax(pred)
    return label_map[idx]

# Hovedprogram-løkke
def main():
    logging.info("Jarvis Lite (Notebook version - gTTS) starter...")
    
    # Hils ved start med gTTS
    if not speak_gtts("Hej, jeg er Jarvis Lite. Hvad kan jeg hjælpe med?"):
         print("-> Start-hilsen printet pga. TTS fejl.") # Indikerer hvis TTS fejlede

    keep_running = True
    while keep_running:
        try:
            user_input = input("Du: ")
            if user_input:
                # Kald handle_text_command UDEN tts engine argument
                keep_running = handle_text_command(user_input)
        except KeyboardInterrupt:
            print("\nFarvel!")
            speak_gtts("Lukker ned. Farvel!")
            keep_running = False
        except Exception as e:
            logging.error(f"Der opstod en uventet fejl: {e}", exc_info=True) 
            print(f"\nFEJL: Der opstod en uventet fejl. Se log for detaljer. Stopper programmet.")
            speak_gtts("Der skete en uventet fejl. Programmet lukker.")
            keep_running = False 

    logging.info("Jarvis Lite lukker ned.")

if __name__ == "__main__":
    main()
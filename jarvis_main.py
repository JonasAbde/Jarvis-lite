import os
import time
import wave
import pyaudio
import numpy as np
import datetime
import webbrowser
import json
import requests
import whisper
from gtts import gTTS
import playsound
import traceback
import librosa
#import torch # Ikke længere direkte nødvendigt her
import uuid
import joblib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import keras
import pickle
from pathlib import Path

# Globale variabler
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
TEMP_WAV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_recording.wav")
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "noter.txt")
TEMP_MP3_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_response_")

# === Globale variabler for forudindlæste modeller ===
whisper_model = None
nlu_model = None
nlu_vectorizer = None
nn_model = None
nn_tokenizer = None
nn_le = None

# === Funktion til at indlæse alle modeller én gang ===
def load_all_models():
    global whisper_model, nlu_model, nlu_vectorizer, nn_model, nn_tokenizer, nn_le
    print("[INFO] Indlæser modeller...")
    try:
        try:
            whisper_model = whisper.load_model("small", device="cuda")
            print("[INFO] Whisper model ('small') indlæst på GPU (cuda).")
        except Exception as e:
            print(f"[ADVARSEL] Kunne ikke indlæse Whisper på GPU: {e}\nFalder tilbage til CPU...")
            whisper_model = whisper.load_model("small", device="cpu")
            print("[INFO] Whisper model ('small') indlæst på CPU.")
    except Exception as e:
        print(f"[FEJL] Kunne ikke indlæse Whisper model: {e}")

    try:
        nlu_model = joblib.load("models/nlu_model.joblib")
        nlu_vectorizer = joblib.load("models/vectorizer.joblib")
        print("[INFO] NLU model og vectorizer indlæst.")
    except Exception as e:
        print(f"[FEJL] Kunne ikke indlæse NLU model/vectorizer: {e}")

    try:
        nn_model = keras.models.load_model("models/nn_chatbot.h5")
        with open("models/nn_tokenizer.pkl", "rb") as f:
            nn_tokenizer = pickle.load(f)
        with open("models/nn_labelencoder.pkl", "rb") as f:
            nn_le = pickle.load(f)
        print("[INFO] NN chatbot model, tokenizer og labelencoder indlæst.")
    except Exception as e:
        print(f"[FEJL] Kunne ikke indlæse NN chatbot model/data: {e}")
    print("[INFO] Modelindlæsning færdig.")

def predict_intent(text):
    global nlu_model, nlu_vectorizer
    if not nlu_model or not nlu_vectorizer:
        print("[FEJL] NLU model eller vectorizer ikke indlæst!")
        return None
    try:
        text_vec = nlu_vectorizer.transform([text])
        prediction = nlu_model.predict(text_vec)
        return prediction[0]
    except Exception as e:
        print(f"Fejl under NLU intent forudsigelse: {e}")
        return None

def transcribe_audio(file_path):
    global whisper_model
    if not whisper_model:
        print("[FEJL] Whisper model ikke indlæst!")
        return None
    temp_path = Path(file_path).resolve()
    print(f"Indlæser og transskriberer {temp_path}...")
    if not temp_path.exists():
        print(f"[FEJL] Lydfilen findes ikke: {temp_path}")
        return None
    start_time = time.time()
    try:
        try:
            audio = whisper.load_audio(str(temp_path))
            print(f" - Lyd indlæst med whisper.load_audio ({len(audio)} samples, 16000Hz) på {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"Kunne ikke indlæse med whisper.load_audio: {e}\nPrøver med librosa i stedet...")
            audio, _ = librosa.load(str(temp_path), sr=16000, mono=True)
            print(f" - Lyd indlæst med librosa ({len(audio)} samples, 16000Hz) på {time.time() - start_time:.2f}s")
        result = whisper_model.transcribe(audio, language="da") # Brug global model
        transcription = result["text"].strip()
        print(f" - Transskription færdig på {time.time() - start_time:.2f}s: '{transcription}'")
        return transcription
    except Exception as e:
        print(f"Fejl under transskription: {e}")
        return None

def nn_chatbot_response(user_input):
    global nn_model, nn_tokenizer, nn_le
    if not nn_model or not nn_tokenizer or not nn_le:
        print("[FEJL] NN chatbot model/data ikke indlæst!")
        return None
    try:
        seq = nn_tokenizer.texts_to_sequences([user_input])
        seq = keras.preprocessing.sequence.pad_sequences(seq, maxlen=nn_model.input_shape[1], padding="post")
        pred = nn_model.predict(seq, verbose=0)
        idx = np.argmax(pred)
        return nn_le.inverse_transform([idx])[0]
    except Exception as e:
        print(f"[NN-Chatbot fejl]: {e}")
        return None

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Jarvis lytter... (Sig noget eller tryk Ctrl+C for at stoppe)")
    frames = []
    silence_threshold = 200 # Sænket fra 400
    silence_chunks = 0
    max_silence_chunks = int(4 * RATE / CHUNK)  # 4 sekunders stilhed før stop
    max_recording_chunks = int(20 * RATE / CHUNK)  # Max 20 sekunder optagelse
    chunk_count = 0
    listening = True
    max_amplitude_seen = 0

    try:
        while listening:
            data = stream.read(CHUNK)
            frames.append(data)
            chunk_count += 1
            audio_data = np.frombuffer(data, dtype=np.int16)
            # Udregn både gennemsnit og max rå værdi
            amplitude_mean = np.abs(audio_data).mean()
            amplitude_max_raw = np.abs(audio_data).max() if len(audio_data) > 0 else 0
            max_amplitude_seen = max(max_amplitude_seen, amplitude_mean) # Beholder gennemsnit her
            
            # Log max rå værdi for at se om der overhovedet er signal
            if chunk_count < 10 or chunk_count % 20 == 0: # Log lidt i starten og periodisk
                print(f"Lytter... (chunk {chunk_count}, mean_amp: {amplitude_mean:.2f}, max_raw: {amplitude_max_raw})")
                
            if amplitude_mean < silence_threshold:
                silence_chunks += 1
                if silence_chunks > max_silence_chunks:
                    # print(f"Stilhed detekteret i {silence_chunks} chunks, afslutter optagelse.")
                    listening = False
            else:
                # if silence_chunks > 10:
                #     print(f"*** Lyd detekteret igen (amplitude: {amplitude_mean:.2f}) ***")
                silence_chunks = 0
                
            if chunk_count > max_recording_chunks:
                # print("Maksimal optagetid nået, afslutter optagelse.")
                listening = False
    except KeyboardInterrupt:
        print("Optagelse afbrudt af bruger.")
        listening = False
    finally:
        print(f"Lytning afsluttet! Optog {chunk_count} chunks. Max amplitude: {max_amplitude_seen:.2f}")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        if not frames:
            print("Ingen lyd optaget.")
            return None
            
        try:
            wf = wave.open(TEMP_WAV, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            if os.path.exists(TEMP_WAV):
                size = os.path.getsize(TEMP_WAV)
                print(f"Lyd gemt midlertidigt i {TEMP_WAV} ({size} bytes)")
                return TEMP_WAV
            else:
                print(f"Fejl: Kunne ikke finde den gemte lydfil {TEMP_WAV}")
                return None
        except Exception as e:
            print(f"Fejl ved skrivning af lydfil: {e}")
            return None

def speak(text, lang="da"):
    response_mp3 = None  # Initialiser filnavn
    try:
        print(f"Jarvis siger: {text}")
        
        # Opret et unikt filnavn for hver TTS-response ved hjælp af uuid
        unique_id = uuid.uuid4()
        response_mp3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"jarvis_response_{unique_id}.mp3")
        
        # Generer og gem lydklip
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(response_mp3)
        print(f"Lydfil gemt til: {response_mp3}") # Tilføjet print for at se det unikke navn
        
        try:
            # Afspil lydklip
            playsound.playsound(response_mp3)
            print(f"Lydklip afspillet")
        except Exception as e:
            print(f"Fejl ved afspilning: {e}")
        
    except Exception as e:
        print(f"Fejl ved tekst-til-tale konvertering: {e}")
        print(traceback.format_exc())
    finally:
        # Slet altid filen, hvis den blev oprettet, uanset om afspilning lykkedes
        if response_mp3 and os.path.exists(response_mp3):
            try:
                # Vent et kort øjeblik for at give OS tid til at frigive filen
                time.sleep(0.5)
                os.remove(response_mp3)
                print(f"Midlertidig lydfil {os.path.basename(response_mp3)} slettet")
            except Exception as e:
                print(f"Kunne ikke slette lydfil {os.path.basename(response_mp3)}: {e}")
                # Ikke kritisk, fortsæt

def extract_website_name(text):
    """Forsøger at udtrække et websitenavn fra teksten."""
    if "google" in text.lower():
        return "google.com"
    elif "youtube" in text.lower():
        return "youtube.com"
    
    # Tjek for .com, .dk etc.
    words = text.split()
    for word in words:
        word = word.lower()
        if word.endswith(".com") or word.endswith(".dk") or word.endswith(".org"):
            return word
    return None

def get_gemini_response(text):
    """Få et intelligent svar fra Gemini API hvis tilgængeligt"""
    api_key = os.environ.get('GEMINI_API_KEY', None)
    
    if not api_key:
        return "Jeg forstår ikke, hvad du mener med \"{}\"? Kan du omformulere dit spørgsmål?".format(text)
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"Besvar dette spørgsmål kort og præcist på dansk: {text}"
                }]
            }]
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            response_data = response.json()
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                if "content" in response_data["candidates"][0]:
                    content = response_data["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        return content["parts"][0]["text"]
        
        return "Jeg forstår ikke spørgsmålet. Kan du omformulere det?"
    except Exception as e:
        print(f"Fejl ved Gemini API kald: {e}")
        return "Jeg kan ikke svare på det lige nu på grund af en teknisk fejl."

def load_conversations(path="conversation_pairs.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def find_best_response(user_input, pairs):
    # Simpel substring-match først
    for pair in pairs:
        if pair["user"] in user_input:
            return pair["jarvis"]
    # Hvis ikke substring, brug TF-IDF similarity
    questions = [pair["user"] for pair in pairs]
    if not questions:
        return None
    vectorizer = TfidfVectorizer().fit(questions + [user_input])
    X = vectorizer.transform(questions)
    X_user = vectorizer.transform([user_input])
    sims = cosine_similarity(X_user, X)[0]
    idx = sims.argmax()
    if sims[idx] > 0.4:
        return pairs[idx]["jarvis"]
    return None

def log_unknown_sentence(sentence, path="ukendte_sætninger.txt"):
    with open(path, "a", encoding="utf-8") as f:
        f.write(sentence.strip() + "\n")

def handle_command(command):
    command = command.lower().strip()
    nlu_intent = predict_intent(command)
    if nlu_intent == "get_time":
        current_time = datetime.datetime.now().strftime("%H:%M")
        return f"Klokken er {current_time}."
    elif nlu_intent == "get_date":
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return f"Dagens dato er {today}."
    elif nlu_intent == "open_app":
        if "notepad" in command or "notesblok" in command:
            os.system("start notepad")
            return "Åbner Notepad."
        elif "lommeregner" in command or "calculator" in command:
            os.system("start calc")
            return "Åbner lommeregner."
        elif "chrome" in command:
            os.system("start chrome")
            return "Åbner Chrome."
        else:
            return "Ukendt program."
    elif nlu_intent == "search_web":
        q = command.split("efter ")[-1] if "efter " in command else command
        webbrowser.open(f"https://www.google.com/search?q={q}")
        return f"Søger på nettet efter {q}."

    # === Retrieval-baseret samtale/chat ===
    pairs = load_conversations()
    response = find_best_response(command, pairs)
    if response:
        return response
    log_unknown_sentence(command)

    # === Neural net fallback ===
    nn_response = nn_chatbot_response(command)
    if nn_response:
        return nn_response

    # === Live learning ===
    speak("Det ved jeg ikke endnu. Vil du lære mig svaret? Sig 'ja' eller 'nej'.")
    user_reply = transcribe_audio(record_audio())
    if user_reply and 'ja' in user_reply.lower():
        speak("Hvad skal jeg svare næste gang nogen spørger om det?")
        new_answer = transcribe_audio(record_audio())
        if new_answer:
            add_conversation_pair(command, new_answer)
            speak("Tak! Jeg har lært noget nyt. Træner modellen nu...")
            os.system("python nn_chatbot_trainer.py")
            return "Nu har jeg lært noget nyt!"
        else:
            return "Jeg fik ikke fat i svaret. Prøv igen senere."
    else:
        return "Okay, spørg mig om noget andet."

def add_conversation_pair(question, answer, path="conversation_pairs.json"):
    import json
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    data.append({"user": question, "jarvis": answer})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # Indlæs alle modeller én gang ved start
    load_all_models()
    
    os.makedirs("data", exist_ok=True)
    # Ryd op i gamle temp mp3 filer ved start
    cleanup_temp_files(TEMP_MP3_BASE, ".mp3")
    
    print("=== Jarvis Lite er klar! ===")
    speak("Jarvis Lite er aktiveret og klar til at hjælpe")

    try:
        while True:
            # 1. Optag lyd
            audio_file_path = record_audio()
            
            if audio_file_path:
                # 2. Transskriber lyden
                user_input = transcribe_audio(audio_file_path)
                
                # 3. Håndter kommando hvis transskription lykkedes og ikke er tom
                if user_input: 
                    print(f"Bruger sagde: '{user_input}'") # Udskriv genkendt tekst
                    response = handle_command(user_input)
                    print(f"Jarvis svarer: {response}")
                    speak(response)
                else:
                    # Hvis transkription fejlede eller var tom (f.eks. for kort optagelse)
                    print("Ingen gyldig tekst genkendt. Prøv igen.")
                    # Vi kan evt. afspille en lyd her, men undlader for nu
                    # speak("Jeg opfattede ikke noget. Prøv igen.") 
            else:
                # Håndter hvis record_audio returnerede None (f.eks. ingen lyd optaget)
                print("Ingen lyd blev optaget. Prøv igen.")
                
            # Kort pause for at undgå at loope for hurtigt ved fejl
            # time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nJarvis Lite lukkes ned via tastaturafbrydelse.")
    finally:
        print("Rydder op...")
        # Sikrer at PyAudio lukkes hvis det ikke skete i record_audio
        try: 
            p = pyaudio.PyAudio()
            p.terminate()
        except:
            pass
        # Ryd op i eventuelle resterende temp-filer
        cleanup_temp_files(TEMP_WAV, "") # Slet specifik wav fil hvis den stadig findes
        cleanup_temp_files(TEMP_MP3_BASE, ".mp3")
        print("Jarvis Lite er lukket ned.")

# Funktion til at rydde op i midlertidige filer
def cleanup_temp_files(basename, extension):
    temp_dir = os.path.dirname(basename)
    base = os.path.basename(basename)
    for filename in os.listdir(temp_dir):
        if filename.startswith(base) and filename.endswith(extension):
            try:
                filepath = os.path.join(temp_dir, filename)
                os.remove(filepath)
                # print(f"Slettede gammel temp-fil: {filepath}") # Gør det mindre støjende
            except Exception as e:
                print(f"Kunne ikke slette gammel temp-fil {filename}: {e}")

if __name__ == "__main__":
    main()
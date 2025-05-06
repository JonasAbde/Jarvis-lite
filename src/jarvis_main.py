import os
# Undertryk TensorFlow INFO og WARNING beskeder
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Undgå oneDNN info (selvom det er harmløst)

import time
import wave
import pyaudio
import numpy as np
import datetime
import webbrowser
import json
import requests
from faster_whisper import WhisperModel
from gtts import gTTS
import playsound
import traceback
import librosa
import uuid
import joblib
import json
import asyncio
import concurrent.futures
from functools import partial
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Brug forsigtig import af keras og tensorflow for at undgå fejl
try:
    import keras
    KERAS_AVAILABLE = True
except ImportError:
    print("[ADVARSEL] Keras kunne ikke importeres. Neurale netværk deaktiveres.")
    KERAS_AVAILABLE = False
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    print("[ADVARSEL] TensorFlow kunne ikke importeres. Visse AI-funktioner deaktiveres.")
    TF_AVAILABLE = False
import pickle
from pathlib import Path
import threading
import torch
import soundfile as sf

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

# Thread pool til I/O-operationer
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# === Funktion til at indlæse alle modeller én gang ===
def load_all_models():
    global whisper_model, nlu_model, nlu_vectorizer, nn_model, nn_tokenizer, nn_le
    print("[INFO] Indlæser modeller...")
    try:
        try:
            # Bruger nu Faster-Whisper med int8 kvantisering for bedre hastighed
            whisper_model = WhisperModel("small", device="cuda", compute_type="int8")
            print("[INFO] Faster-Whisper model ('small') indlæst på GPU (cuda) med INT8 kvantisering.")
        except Exception as e:
            print(f"[ADVARSEL] Kunne ikke indlæse Whisper på GPU: {e}\nFalder tilbage til CPU...")
            # int8 er god for CPU-performance
            whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
            print("[INFO] Faster-Whisper model ('small') indlæst på CPU med INT8 kvantisering.")
    except Exception as e:
        print(f"[FEJL] Kunne ikke indlæse Whisper model: {e}")

    try:
        nlu_model = joblib.load("models/nlu_model.joblib")
        nlu_vectorizer = joblib.load("models/vectorizer.joblib")
        print("[INFO] NLU model og vectorizer indlæst.")
    except Exception as e:
        print(f"[FEJL] Kunne ikke indlæse NLU model/vectorizer: {e}")

    try:
        if KERAS_AVAILABLE:
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

# Asynkron version af transcribe_audio
async def transcribe_audio_async(file_path):
    """Asynkron wrapper til transskription"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(transcribe_audio, file_path))

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
        # Indlæs lydfilen med librosa (uændret)
        try:
            audio, _ = librosa.load(str(temp_path), sr=16000, mono=True)
            print(f" - Lyd indlæst med librosa ({len(audio)} samples, 16000Hz) på {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"[FEJL] Kunne ikke indlæse lyd med librosa: {e}")
            return None
            
        # Brug Faster-Whisper til transskription
        segments, info = whisper_model.transcribe(audio, language="da", beam_size=5)
        segments_list = list(segments)  # Konverter generator til liste
        
        if segments_list:
            # Saml tekst fra alle segmenter
            transcription = " ".join([segment.text for segment in segments_list])
            print(f" - Transskription færdig på {time.time() - start_time:.2f}s: '{transcription}'")
            return transcription.strip()
        else:
            print(f"[ADVARSEL] Ingen tekst blev genereret ved transskription.")
            return None
    except Exception as e:
        print(f"Fejl under transskription: {e}")
        traceback.print_exc()
        return None

def nn_chatbot_response(user_input):
    global nn_model, nn_tokenizer, nn_le
    if not KERAS_AVAILABLE:
        return None
    if not nn_model or not nn_tokenizer or not nn_le:
        print("[FEJL] NN chatbot model/data ikke indlæst!")
        return None
    try:
        seq = nn_tokenizer.texts_to_sequences([user_input])
        if KERAS_AVAILABLE and TF_AVAILABLE:
            seq = keras.preprocessing.sequence.pad_sequences(seq, maxlen=nn_model.input_shape[1], padding="post")
            pred = nn_model.predict(seq, verbose=0)
            idx = np.argmax(pred)
            return nn_le.inverse_transform([idx])[0]
        else:
            return None
    except Exception as e:
        print(f"[NN-Chatbot fejl]: {e}")
        return None

# Asynkron version af record_audio
async def record_audio_async():
    """Asynkron wrapper til lydoptagelse"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, record_audio)

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
            amplitude_mean = np.abs(audio_data).mean()
            amplitude_max_raw = np.abs(audio_data).max() if len(audio_data) > 0 else 0
            max_amplitude_seen = max(max_amplitude_seen, amplitude_mean) # Beholder gennemsnit her
            
            if chunk_count < 10 or chunk_count % 20 == 0: # Log lidt i starten og periodisk
                print(f"Lytter... (chunk {chunk_count}, mean_amp: {amplitude_mean:.2f}, max_raw: {amplitude_max_raw})")
                
            if amplitude_mean < silence_threshold:
                silence_chunks += 1
                if silence_chunks > max_silence_chunks:
                    listening = False
            else:
                silence_chunks = 0
                
            if chunk_count > max_recording_chunks:
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

# Asynkron TTS
async def speak_async(text, lang='da'):
    """Asynkron wrapper til TTS"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(speak, text, lang))

def speak(text, lang='da'):
    try:
        print(f"Jarvis svarer: {text}")
        
        unique_id = uuid.uuid4()
        response_mp3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"jarvis_response_{unique_id}.mp3")
        
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(response_mp3)
        print(f"Lydfil gemt til: {response_mp3}")
        
        try:
            # Gør lydafspilning non-blocking
            playsound.playsound(response_mp3, block=False)
            print(f"Lydklip afspilles (ikke-blokerende)")
        except Exception as e:
            print(f"Kunne ikke afspille lyd: {e}")
    except Exception as e:
        print(f"Fejl ved tekst-til-tale konvertering: {e}")
        print(traceback.format_exc())
    finally:
        if response_mp3 and os.path.exists(response_mp3):
            try:
                time.sleep(0.5)
                os.remove(response_mp3)
                print(f"Midlertidig lydfil {os.path.basename(response_mp3)} slettet")
            except:
                # Ikke kritisk, fortsæt
                pass

def extract_website_name(text):
    if "google" in text.lower():
        return "google.com"
    elif "youtube" in text.lower():
        return "youtube.com"
    
    words = text.split()
    for word in words:
        word = word.lower()
        if any(ext in word for ext in [".com", ".dk", ".org", ".net"]):
            return word
    return None

def get_gemini_response(text):
    api_key = os.environ.get('GEMINI_API_KEY', None)
    
    if not api_key:
        return None
        
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {'Content-Type': 'application/json'}
    params = {'key': api_key}
    
    payload = {
        "contents": [{"parts":[{"text": text}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        
        if response.status_code == 200:
            content = response.json()
            if 'candidates' in content and len(content['candidates']) > 0:
                parts = content['candidates'][0]['content']['parts']
                if len(parts) > 0:
                    return parts[0]['text']
        
        print(f"Gemini API-svar fejlede: {response.status_code} {response.text}")
        return None
    except Exception as e:
        print(f"Fejl under Gemini API-kald: {e}")
        return None

def load_conversations():
    try:
        with open('data/conversation_pairs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Kunne ikke indlæse samtalepar: {e}")
        return []

def find_best_response(user_input, pairs):
    for pair in pairs:
        if pair["user"] in user_input:
            return pair["jarvis"]
    questions = [pair["user"] for pair in pairs]
    if not questions:
        return None
        
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform(questions)
        user_tfidf = vectorizer.transform([user_input])
        
        cosine_similarities = cosine_similarity(user_tfidf, tfidf_matrix)
        best_match_index = cosine_similarities[0].argmax()
        
        # Et vist minimum af lighed kræves
        if cosine_similarities[0][best_match_index] >= 0.4:
            return pairs[best_match_index]["jarvis"]
    except Exception as e:
        print(f"Fejl i similarity beregning: {e}")
        
    return None

def log_unknown_sentence(sentence):
    if not sentence or sentence.isspace():
        return
    
    try:
        with open("ukendte_sætninger.txt", "a", encoding="utf-8") as f:
            f.write(f"{sentence}\n")
    except Exception as e:
        print(f"Kunne ikke logge ukendt sætning: {e}")

def handle_command(command):
    if not command or command.isspace():
        return "Jeg kunne ikke forstå, hvad du sagde. Prøv igen."
    
    command = command.strip().lower()
    
    intent = predict_intent(command)
    print(f"Intent: {intent}")
    
    if intent == "klokken":
        now = datetime.datetime.now()
        return f"Klokken er {now.strftime('%H:%M')}"
    
    if intent == "dato":
        now = datetime.datetime.now()
        return f"Dagens dato er {now.strftime('%d/%m/%Y')}"

    if intent == "vejr":
        return "Desværre har jeg ikke adgang til vejrudsigten lige nu."
    
    if intent == "website":
        website = extract_website_name(command)
        if website:
            if not website.startswith("http"):
                website = "https://" + website
            webbrowser.open(website)
            return f"Åbner {website}"
        return "Jeg kunne ikke finde et websted at åbne."
    
    if intent == "youtube" or "youtube" in command.lower():
        try:
            # Kør i en separat tråd for at undgå blokeringsproblemer
            def open_youtube():
                webbrowser.open("https://www.youtube.com")
                print("YouTube åbnet i browser")
            threading.Thread(target=open_youtube, daemon=True).start()
            return "Åbner YouTube..."
        except Exception as e:
            print(f"Fejl ved åbning af YouTube: {e}")
            return "Kunne ikke åbne YouTube på grund af en fejl"
    
    if intent == "gem_note":
        note_text = command.replace("gem", "", 1).replace("note", "", 1).strip()
        if not note_text:
            return "Hvad skal jeg gemme som note?"
        
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(note_text + "\n")
        return f"Jeg har gemt noten: {note_text}"
    
    if intent == "google":
        q = command.replace("søg", "", 1).replace("google", "", 1).strip()
        if not q:
            return "Hvad skal jeg søge efter?"
        webbrowser.open(f"https://www.google.com/search?q={q}")
        return f"Søger på nettet efter {q}."

    pairs = load_conversations()
    response = find_best_response(command, pairs)
    if response:
        return response
    log_unknown_sentence(command)

    if KERAS_AVAILABLE:
        nn_response = nn_chatbot_response(command)
        if nn_response:
            return nn_response
    
    speak("Det ved jeg ikke endnu. Vil du lære mig svaret? Sig 'ja' eller 'nej'.")
    user_reply = transcribe_audio(record_audio())
    if user_reply and 'ja' in user_reply.lower():
        speak("Hvad skal jeg svare, når nogen siger " + command + "?")
        answer = transcribe_audio(record_audio())
        if answer:
            add_conversation_pair(command, answer)
            return f"Tak, nu har jeg lært at svare: {answer}"
        else:
            return "Jeg forstod ikke dit svar. Vi prøver igen senere."
    
    # Fallback til Google API, hvis tilgængeligt
    gemini_response = get_gemini_response(command)
    if gemini_response:
        return gemini_response
    
    return "Det forstår jeg ikke endnu, men jeg har noteret det til senere læring."

def add_conversation_pair(user_text, jarvis_text):
    try:
        with open('data/conversation_pairs.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    
    data.append({"user": user_text, "jarvis": jarvis_text})
    
    with open('data/conversation_pairs.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Asynkron hoved-loop
async def main_async():
    """Asynkront hovedloop"""
    load_all_models()
    
    os.makedirs("data", exist_ok=True)
    cleanup_temp_files(TEMP_MP3_BASE, ".mp3")
    
    print("=== Jarvis Lite er klar! ===")
    await speak_async("Jarvis Lite er aktiveret og klar til at hjælpe")

    try:
        while True:
            # Optagelse (potentielt blokerende, men kører i thread pool)
            audio_file_path = await record_audio_async()
            
            if audio_file_path:
                # Transskription (CPU/GPU-intensiv, kører i thread pool)
                user_input = await transcribe_audio_async(audio_file_path)
                
                if user_input: 
                    print(f"Bruger sagde: '{user_input}'")
                    speak_text = f"Du sagde: {user_input}. "
                    
                    # Intent-håndtering (mindre intensiv, kører i hovedtråd)
                    response = handle_command(user_input)
                    # TTS (netværk + I/O, kører i thread pool)
                    await speak_async(speak_text + response)
                else:
                    print("Ingen gyldig tekst genkendt. Prøv igen.")
            else:
                print("Ingen lyd blev optaget. Prøv igen.")
                
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\nJarvis Lite lukkes ned via tastaturafbrydelse.")
    finally:
        print("Rydder op...")
        try: 
            p = pyaudio.PyAudio()
            p.terminate()
        except:
            pass
        cleanup_temp_files(TEMP_WAV, "") # Slet specifik wav fil hvis den stadig findes
        cleanup_temp_files(TEMP_MP3_BASE, ".mp3")
        print("Jarvis Lite er lukket ned.")

def cleanup_temp_files(basename, extension):
    temp_dir = os.path.dirname(basename)
    base = os.path.basename(basename)
    for filename in os.listdir(temp_dir):
        if filename.startswith(base) and filename.endswith(extension):
            try:
                filepath = os.path.join(temp_dir, filename)
                os.remove(filepath)
            except Exception as e:
                print(f"Kunne ikke slette gammel temp-fil {filename}: {e}")

def main():
    """Starter det asynkrone hovedloop"""
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        print("\nJarvis Lite lukkes ned via tastaturafbrydelse.")
        cleanup_temp_files(TEMP_WAV, "")
        cleanup_temp_files(TEMP_MP3_BASE, ".mp3")
        print("Jarvis Lite er lukket ned.")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
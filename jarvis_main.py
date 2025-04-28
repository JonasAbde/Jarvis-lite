import os
import time
import wave
import pyaudio
import whisper
import numpy as np
import soundfile as sf
from gtts import gTTS
from playsound import playsound
import requests
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI biblioteket er ikke installeret. Avancerede svar vil ikke være tilgængelige.")

# --- Gemini API-nøgle (valgfri) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAT8iLM_K7kBPBxhj303XguBzLe1Gh-qOU")
if not GEMINI_API_KEY:
    print("Advarsel: Gemini API-nøgle ikke fundet. Sæt den som miljøvariabel 'GEMINI_API_KEY' for intelligente svar.")

# --- Whisper opsætning ---
print("Indlæser Whisper sprogmodel...")
whisper_model = whisper.load_model("base")
print("Whisper model indlæst!")

# --- Lydoptagelse ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# --- Midlertidig fil til lyd ---
TEMP_WAV = "temp_recording.wav"

# --- Samtalehistorik ---
conversation_history = []

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Jarvis lytter...")
    frames = []
    silence_threshold = 400  # Sænk tærsklen for stilhedsdetektion
    silence_chunks = 0
    max_silence_chunks = int(5 * RATE / CHUNK)  # Forlæng til 5 sekunder stilhed før afslutning
    max_recording_chunks = int(30 * RATE / CHUNK)  # Maks 30 sekunder optagelse
    chunk_count = 0
    listening = True

    try:
        while listening:
            data = stream.read(CHUNK)
            frames.append(data)
            chunk_count += 1
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.abs(audio_data).mean()
            print(f"Amplitude: {amplitude:.2f}")  # Fejlsøgningslogning
            if amplitude < silence_threshold:
                silence_chunks += 1
                if silence_chunks > max_silence_chunks:
                    print("Stilhed detekteret, afslutter optagelse.")
                    listening = False
            else:
                silence_chunks = 0
            if chunk_count > max_recording_chunks:
                print("Maksimal optagetid nået, afslutter optagelse.")
                listening = False
    except KeyboardInterrupt:
        print("Afbrudt af bruger.")
        listening = False
    finally:
        print("Lytning afsluttet!")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if len(frames) > 0:
            wf = wave.open(TEMP_WAV, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            print(f"Lyd gemt som {TEMP_WAV}, størrelse: {os.path.getsize(TEMP_WAV)} bytes")
            return TEMP_WAV
        print("Ingen lyd optaget.")
        return None

def recognize_speech_with_whisper(audio_path):
    if not os.path.exists(audio_path):
        print(f"Fejl: Lydfilen {audio_path} findes ikke.")
        return ""
    try:
        print(f"Forsøger at transskribere {audio_path}...")
        audio = whisper.load_audio(audio_path)
        print("Lyd indlæst til transskription.")
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)
        options = whisper.DecodingOptions(language="da")
        result = whisper.decode(whisper_model, mel, options)
        print(f"Transskription færdig: {result.text}")
        return result.text
    except Exception as e:
        print(f"Fejl ved brug af Whisper: {e}")
        return ""

def speak(text, lang="da"):
    print(f"Jarvis siger: {text}")
    tts_file = "jarvis_response.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(tts_file)
    try:
        playsound(tts_file)
    except Exception as e:
        print(f"Fejl ved afspilning: {e}")
    finally:
        try:
            os.remove(tts_file)
        except Exception as e:
            print(f"Kunne ikke slette midlertidig fil: {e}")

def get_gemini_response(text):
    if not GEMINI_API_KEY:
        return "Jeg kan ikke svare intelligent, da Gemini API-nøglen ikke er sat."
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        # Byg samtalehistorik til prompten
        history_text = "Samtalehistorik:\n"
        for entry in conversation_history[-5:]:  # Begræns til de sidste 5 interaktioner
            history_text += f"Bruger: {entry['user']}\nJarvis: {entry['jarvis']}\n"
        prompt = f"Du er Jarvis, en hjælpsom AI-assistent. Svar kort og præcist på dansk. Brug samtalehistorikken til at give relevante svar:\n{history_text}\nBruger: {text}"
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        if 'candidates' in response_json and len(response_json['candidates']) > 0:
            answer = response_json['candidates'][0]['content']['parts'][0]['text']
            # Opdater samtalehistorik
            conversation_history.append({"user": text, "jarvis": answer})
            return answer
        else:
            return "Jeg kunne ikke få et svar fra Gemini API."
    except Exception as e:
        print(f"Fejl ved Gemini API: {e}")
        return "Jeg kunne ikke få et intelligent svar fra Gemini."

def main():
    # Sørg for at data-mappe eksisterer
    os.makedirs("data", exist_ok=True)

    print("Jarvis Lite er klar.")
    speak("Jarvis Lite er aktiveret og klar til at hjælpe")

    while True:
        # 1. Optag lyd
        wav_path = record_audio()
        if not wav_path:
            speak("Beklager, jeg hørte ikke noget.")
            continue

        # 2. Transskribér med Whisper direkte fra lyddata
        text = recognize_speech_with_whisper(wav_path)

        # Ryd op - slet midlertidig lydfil
        try:
            os.remove(wav_path)
        except:
            print(f"Kunne ikke slette midlertidig fil: {wav_path}")

        if not text:
            speak("Beklager, jeg forstod ikke hvad du sagde.")
            continue

        print(f"Du sagde: {text}")

        # 3. Få intelligent svar fra Gemini, hvis tilgængeligt
        response = get_gemini_response(text)
        speak(response)

        if "farvel" in text or "stop" in text or "luk ned" in text:
            speak("Farvel! Jarvis lukker ned.")
            break

if __name__ == "__main__":
    main()
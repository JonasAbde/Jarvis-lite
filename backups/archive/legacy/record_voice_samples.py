import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time

def record_voice_samples():
    # Konfiguration
    sample_rate = 16000
    seconds = 3
    users = ["jonas", "david", "elmedin", "mirac"]
    num_samples = 3  # Antal lydprøver pr. bruger
    
    for user in users:
        print(f"\n--- Optagelse af stemmeprøver for {user.upper()} ---")
        
        # Opret mappe til brugerens stemmeprøver
        user_dir = os.path.join("data", "voices", user)
        os.makedirs(user_dir, exist_ok=True)
        
        for i in range(num_samples):
            print(f"\nOptag prøve {i+1}/{num_samples} for {user}")
            print("Sig noget i 3 sekunder efter nedtælling")
            
            for j in range(3, 0, -1):
                print(f"{j}...")
                time.sleep(1)
                
            print("OPTAGER NU - TAL!")
            
            # Optag lyd
            audio_data = sd.rec(int(seconds * sample_rate), 
                                samplerate=sample_rate,
                                channels=1, 
                                dtype='float32')
            sd.wait()  # Vent til optagelsen er færdig
            
            # Gem lydfil
            filename = os.path.join(user_dir, f"{user}_sample_{i+1}.wav")
            sf.write(filename, audio_data, sample_rate)
            print(f"Gemt som: {filename}")
            
            if i < num_samples - 1:
                input("Tryk Enter for at fortsætte til næste optagelse...")
        
        if user != users[-1]:
            input(f"\nTryk Enter for at fortsætte til næste bruger ({users[users.index(user)+1]})...")
    
    print("\n--- Alle stemmeprøver er optaget! ---")
    print("Du kan nu køre jarvis_main.py for at starte Jarvis med taler-identifikation")

if __name__ == "__main__":
    print("=== STEMMEOPTAGER TIL JARVIS LITE ===")
    print("Dette program vil optage stemmeprøver til Jarvis' taler-identifikation")
    print("For hver bruger (Jonas, David, Elmedin, Mirac) optages 3 korte lydprøver")
    
    answer = input("Er du klar til at begynde optagelsen? (j/n): ")
    if answer.lower() in ["j", "ja", "y", "yes"]:
        record_voice_samples()
    else:
        print("Afbryder. Kør programmet igen når du er klar.")

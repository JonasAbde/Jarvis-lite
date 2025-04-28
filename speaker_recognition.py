import os
import numpy as np
import librosa
from sklearn.neighbors import KNeighborsClassifier
import joblib
import warnings
from sklearn.preprocessing import StandardScaler
import shutil

# Ignorer advarsler
warnings.filterwarnings('ignore')

SAMPLE_RATE = 16000
N_MFCC = 13

class SpeakerRecognizer:
    def __init__(self, voices_dir='data/voices', model_path='data/speaker_model.joblib', threshold=0.6):
        self.voices_dir = voices_dir
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.threshold = threshold  # Tærskel for konfidensværdi (0-1), kan nu sættes via parameter
        
        # Fjern eksisterende model for at sikre frisk træning
        if os.path.exists(model_path):
            try:
                os.remove(model_path)
            except:
                pass
        
        # Opret output-mappe
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        print("Træner stemmemodel...")
        self.train_model()

    def extract_features(self, file_path):
        """Udtræk simplere MFCC features"""
        try:
            y, sr = librosa.load(file_path, sr=SAMPLE_RATE)
            
            # Filtrering og beregn MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
            
            # Tag gennemsnittet over tid - dette giver en enkel repræsentation
            mfccs_mean = np.mean(mfccs, axis=1)
            
            return mfccs_mean
        except Exception as e:
            print(f"Fejl ved feature extraction for {file_path}: {e}")
            return None

    def train_model(self):
        """Træn simpel K-NN model på stemmeprøverne"""
        print("\n--- TRÆNER STEMMEMODEL ---")
        
        features = []
        labels = []
        
        # Gennemgå hver brugers stemmeprøver
        for person in os.listdir(self.voices_dir):
            person_dir = os.path.join(self.voices_dir, person)
            if not os.path.isdir(person_dir):
                continue
                
            wav_files = [f for f in os.listdir(person_dir) if f.endswith('.wav')]
            if not wav_files:
                print(f"Ingen stemmeprøver fundet for {person}")
                continue
                
            print(f"Behandler {len(wav_files)} lydprøver for {person.upper()}")
            
            for wav in wav_files:
                wav_path = os.path.join(person_dir, wav)
                feature_vector = self.extract_features(wav_path)
                
                if feature_vector is not None:
                    features.append(feature_vector)
                    labels.append(person)
        
        if len(features) == 0:
            print("FEJL: Ingen brugbare stemmeprøver fundet!")
            return
            
        print(f"Træner på {len(features)} stemmeprøver...")
        
        # Konverter til numpy arrays og skaler funktioner
        X = np.array(features)
        y = np.array(labels)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Træn model - K-NN er simpel og effektiv
        self.model = KNeighborsClassifier(n_neighbors=1)
        self.model.fit(X_scaled, y)
        
        # Gem model og skaler
        joblib.dump({'model': self.model, 'scaler': self.scaler}, self.model_path)
        print(f"Model og skaler gemt som {self.model_path}")
        print("--- TRÆNING AFSLUTTET ---\n")

    def predict(self, wav_file):
        """Forudsig taler og returner (bruger, konfidens)"""
        if self.model is None:
            print("FEJL: Ingen trænet model fundet")
            return "guest", 0.0
            
        features = self.extract_features(wav_file)
        if features is None:
            return "guest", 0.0
            
        # Skaler funktioner for forudsigelse
        features = np.array(features).reshape(1, -1)
        if self.scaler:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features
        
        # Forudsigelse og afstand til nærmeste nabo
        prediction = self.model.predict(features_scaled)[0]
        distances, indices = self.model.kneighbors(features_scaled)
        
        # Afstand konverteres til konfidens (0-1)
        # Jo mindre afstand, jo større konfidens
        confidence = 1.0 / (1.0 + distances[0][0])
        
        print(f"Genkendelse: {prediction} (konfidens: {confidence:.2f})")
        
        # Hvis konfidensen er for lav, returner gæst
        if confidence < self.threshold:
            print(f"Konfidens {confidence:.2f} under tærskel {self.threshold}. Kategoriseret som gæst.")
            return "guest", confidence
            
        return prediction, confidence

import sounddevice as sd
import numpy as np
import torch
from danspeech import Recognizer
from danspeech.pretrained_models import DanSpeechPrimary
import queue
import threading
import time

class SpeechRecognizer:
    def __init__(self):
        # Initialize DanSpeech model
        self.model = DanSpeechPrimary()
        self.recognizer = Recognizer(model=self.model)
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = np.float32
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.recording_thread = None
        self.processing_thread = None

    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio input"""
        if status:
            print(f"Audio input status: {status}")
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        """Process audio data from queue"""
        while self.is_listening:
            try:
                # Collect 1 second of audio
                audio_data = []
                for _ in range(int(self.sample_rate / 1024)):  # 1024 samples per chunk
                    audio_data.append(self.audio_queue.get(timeout=1.0))
                
                if audio_data:
                    # Convert to numpy array
                    audio_array = np.concatenate(audio_data)
                    
                    # Perform speech recognition
                    try:
                        text = self.recognizer.recognize(audio_array)
                        if text:
                            print(f"Recognized: {text}")
                            # Here you can add code to handle the recognized text
                    except Exception as e:
                        print(f"Recognition error: {e}")
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")

    def start_listening(self):
        """Start listening for speech"""
        if not self.is_listening:
            self.is_listening = True
            
            # Start audio recording thread
            self.recording_thread = threading.Thread(
                target=lambda: sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    callback=self.audio_callback
                ).__enter__()
            )
            self.recording_thread.start()
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.start()
            
            print("Started listening...")

    def stop_listening(self):
        """Stop listening for speech"""
        if self.is_listening:
            self.is_listening = False
            
            if self.recording_thread:
                self.recording_thread.join()
            if self.processing_thread:
                self.processing_thread.join()
                
            print("Stopped listening...")

if __name__ == "__main__":
    recognizer = SpeechRecognizer()
    try:
        recognizer.start_listening()
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recognizer.stop_listening() 
# Jarvis Lite – Overblik

Jarvis Lite er en **offline stemmeassistent på dansk** udviklet som studieprojekt.
Den kører lokalt på Windows-maskiner (GPU-acceleration hvis muligt) og kan
forstå, fortolke og udføre simple talekommandoer – helt uden internetforbindelse.

| Komponent | Teknologi |
|-----------|-----------|
| STT (speech-to-text) | OpenAI Whisper `small` |
| NLU (intent-klassificering) | scikit-learn TF-IDF + LogisticRegression |
| NN-chatbot fallback | Keras sequential-model |
| TTS (text-to-speech) | gTTS (kan skiftes til pyttsx3) |

## Funktioner
* Fortæller hvad klokken er
* Åbner udvalgte websites
* Gemmer noter til fil
* Motiverer brugeren
* Lærer løbende nye spørgsmål/svar (skrives til *ukendte_sætninger.txt*)

## Trimmet mappe-layout
```
Jarvis-lite/
├── jarvis_main.py            # hovedloop (record ➜ transcribe ➜ predict ➜ execute)
├── jarvis_commands.py        # helper-kommandoer (klokken, youtube, gem note …)
├── data/conversation_pairs.json
├── models/                   # .joblib, .h5, tokenizer- og label-encode-filer
├── nlu_trainer.py            # træner intents-model
├── nn_chatbot_trainer.py     # træner NN-chatbot
├── requirements.txt
└── docs/ (OVERVIEW, SETUP, USAGE)
```

Læs videre i **docs/SETUP.md** for installation og **docs/USAGE.md** for
afkørsel og træning.

# Jarvis Lite - Projekt Struktur

Dette dokument giver et komplet overblik over Jarvis Lite projektets struktur, komponenter og formål. Projektet demonstrerer forskellige tilgange til at implementere en personlig assistent, fra simple implementeringer til avancerede med Machine Learning.

## Projektets overordnede struktur

```
Jarvis-lite/
├── JarvisLite_Eksamen/      # Komplet eksamenspakke (ML-baseret)
├── jarvis_lite_dashboard/   # Dashboard og hardware-integration
├── notebooks/               # Jupyter Notebooks til demo og udvikling
├── src/                     # Kernekomponenter og moduler
├── tests/                   # Enhedstests
├── config/                  # Konfigurationsfiler
├── data/                    # Datafiler og noter
├── report/                  # Dokumentation og rapporter
├── main.py                  # Kommandolinjeversion (basis)
├── Jarvis_Lite_Eksamen.ipynb # Notebook-version (dictionary-baseret)
└── jarvis_lite_eksamen_ml.py # ML-version (standalone)
```

## Komponentbeskrivelser

### 1. Hovedversioner

#### `main.py`
**Anvendt tilgang:** Basis kommandohåndtering med if/else
- Simpel tekstbaseret assistent med grundlæggende kommandogenkendelse
- Bruger if/else-konstruktioner til at afgøre kommandoer
- Indeholder funktioner til at fortælle tid, åbne websites, gemme noter
- Bruger gTTS til talesyntese

#### `Jarvis_Lite_Eksamen.ipynb`
**Anvendt tilgang:** Dictionary-baseret kommandohåndtering
- Jupyter Notebook-version til undervisningsbrug
- Bruger `command_map` dictionary til at mappe kommandoer til funktioner
- Mere modulær og vedligeholdbar kode
- Indeholder samme kernefunktionalitet som main.py, men bedre struktureret

#### `jarvis_lite_eksamen_ml.py`
**Anvendt tilgang:** Machine Learning (TensorFlow)
- Avanceret version med intentgenkendelse via neuralt netværk
- Kan genkende naturligt sprog og variationer af kommandoer
- Bruger TensorFlow og Keras til at bygge og træne modellen
- Mere fleksibel og brugervenlig interaktion

### 2. JarvisLite_Eksamen (Eksamenspakke)

Komplet, selvstændig pakke klar til eksamen og præsentation:

```
JarvisLite_Eksamen/
├── notebooks/               # Notebook-versioner
├── scripts/                 # Python-scripts
│   └── jarvis_lite.py       # Hoveddelen af assistenten (ML-baseret)
├── README.md                # Projektdokumentation
├── requirements.txt         # Nødvendige pakker
├── setup.bat                # Automatisk installation
├── start_jarvis.bat         # Starter assistenten direkte
├── start_notebook.bat       # Starter Jupyter Notebook
└── VERSION_HISTORY.md       # Detaljeret versionshistorik
```

**Formål:** Selvstændig pakke til aflevering og evaluering. Indeholder alle nødvendige komponenter til at installere og køre programmet uden yderligere konfiguration.

### 3. jarvis_lite_dashboard (Avancerede funktioner)

Udvidet version med dashboard-funktionalitet og hardware-integration:

```
jarvis_lite_dashboard/
├── config/                  # Konfigurationsfiler
├── core/                    # Kernefunktionalitet
│   ├── speech.py            # Talegenkendelse
│   └── tts.py               # Text-to-Speech
├── dashboard/               # Dashboard-komponenter
│   ├── lcd/                 # LCD-displayfunktionalitet
│   └── web/                 # Webbaseret dashboard
│       ├── static/          # Statiske filer (CSS, JS)
│       ├── templates/       # HTML-skabeloner
│       └── app.py           # Flask-applikation
├── hardware/                # Hardware-integrationer
│   ├── button.py            # Knap-håndtering
│   ├── lcd.py               # LCD-skærm
│   ├── led.py               # LED-lys
│   └── mic.py               # Mikrofon-styring
├── plugins/                 # Udvidelsesmoduler
│   ├── lights.py            # Lyskontrol
│   ├── log.py               # Logging
│   ├── notes.py             # Noter
│   └── web.py               # Webintegration
├── tests/                   # Tests for dashboard
└── utils/                   # Hjælpefunktioner
    ├── helpers.py           # Generelle hjælpere
    └── logger.py            # Logging
```

**Formål:** Udvidet version, der viser hvordan Jarvis kan integreres med hardware og give en grafisk brugergrænseflade. Dette er mere avanceret end eksamenspakken og demonstrerer, hvordan assistenten kan bygges ud til en komplet IoT-løsning.

### 4. src (Kernekomponenter)

Kernebiblioteker og moduler:

```
src/
├── voice/                   # Stemmegenkendelse
│   └── danish_pronunciation.py # Dansk udtale
├── danspeech_voice.py       # Integration med DanSpeech
├── jarvis_commands.py       # Kommandohåndtering
├── jarvis_core.py           # Kernelogik
├── jarvis_voice.py          # Stemmegrænseflade
└── test_voice.py            # Test af stemmefunktionalitet
```

**Formål:** Genbrugelige moduler, der kan anvendes i forskellige versioner af Jarvis. Indeholder logik til stemmegenkendelse, kommandohåndtering og kernefunktionalitet.

### 5. notebooks (Jupyter Notebooks)

```
notebooks/
└── JarvisLiteDemo.ipynb     # Demonstrationsnotebook
```

**Formål:** Interaktive demonstrationer og udvikling af funktionalitet. Jupyter Notebooks er især nyttige til undervisningsformål.

### 6. Øvrige komponenter

- **tests/**: Enhedstests til at verificere funktionalitet
- **config/**: Konfigurationsfiler (f.eks. voice_config.json)
- **data/**: Data og noter (f.eks. notes.txt)
- **report/**: Dokumenter og rapporter (f.eks. rapport.md)

## Teknologier anvendt i projektet

### Sprog og frameworks
- **Python**: Hovedprogrammeringssprog
- **TensorFlow/Keras**: Machine Learning og neurale netværk
- **Flask**: Web-server til dashboard

### Biblioteker
- **gTTS**: Google Text-to-Speech
- **playsound**: Lydafspilning
- **DanSpeech**: Dansk talegenkendelse (i visse versioner)
- **NumPy**: Numeriske operationer
- **Jupyter**: Interaktive notebooks

### Maskinlæring
- **Tokenization**: Konvertering af tekst til tal-sekvenser
- **Embedding**: Vektor-repræsentation af ord
- **Neurale netværk**: Klassifikation af brugerintentioner
- **Feed-forward arkitektur**: Simpel model med input, hidden og output lag

### Hardware (i dashboard-versionen)
- **Mikrofon**: Lydindgang
- **LCD**: Displayoutput
- **LED**: Visuel feedback
- **Knapper**: Fysisk interaktion

## Implementeringsmetoder

Projektet demonstrerer tre fundamentalt forskellige implementeringsmetoder:

1. **Betingelses-baseret (if/else)**: Enkel, direkte implementering med betingelseslogik
2. **Dictionary-baseret**: Datastruktur-drevet tilgang med funktioner som objekter
3. **ML-baseret**: Avanceret tilgang med neuralt netværk til intentgenkendelse

Hver metode viser forskellige aspekter af programmering og AI, fra grundlæggende programmering til avanceret maskinlæring.

## Relateret til pensum

Projektet demonstrerer flere nøglekoncepter fra pensum:

- **Kunstig intelligens (AI)**: Intentgenkendelse, naturligt sprog forståelse
- **Machine Learning**: Træning af model til tekstklassifikation
- **Neurale netværk**: Embeddings, dense layers, aktivieringsfunktioner
- **Beslutningslogik**: if/else, dictionary-lookups, model-baseret
- **Datastrukturer**: Dictionaries, arrays, tokenization
- **Praktiske anvendelser**: Tale, webintegration, notater

---

*Udviklet som eksamensprojekt af [Gruppens navn/medlemmer]*

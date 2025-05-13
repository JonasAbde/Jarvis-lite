# Jarvis-lite

En dansk offline stemmeassistent.

## Installation

1. Opret et virtuelt miljø:
```bash
python -m venv .venv
```

2. Aktivér miljøet:
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

3. Installér afhængigheder:
```bash
pip install -r requirements.txt
```

## Konfiguration

### API Nøgler
For at bruge LiveKit voice assistant funktionaliteten skal du oprette en `.env` fil i roden af projektet med følgende variabler:

```
# LiveKit konfiguration
LIVEKIT_URL=din_livekit_url
LIVEKIT_API_KEY=din_livekit_api_key
LIVEKIT_API_SECRET=din_livekit_api_secret

# Deepgram API nøgle
DEEPGRAM_API_KEY=din_deepgram_api_key

# OpenAI API nøgle
OPENAI_API_KEY=din_openai_api_key
```

Du kan få disse API nøgler ved at:
1. Oprette en konto på [LiveKit](https://livekit.io)
2. Oprette en konto på [Deepgram](https://deepgram.com)
3. Oprette en konto på [OpenAI](https://platform.openai.com)

### Stemmer
Jarvis-lite understøtter både standard gTTS stemmer og brugerdefinerede stemmer. Se `data/voices/` mappen for eksempler.

## Brug

1. Start API serveren:
```bash
python api_server.py
```

2. Start Jarvis:
```bash
python jarvis_launcher.py
```

3. For at bruge LiveKit voice assistant:
```bash
python src/audio/livekit_assistant.py
```

## Udvikling

Se `docs/` mappen for udviklerdokumentation.

## Tests

Kør tests med:
```bash
pytest tests/
```

## Licens

Dette projekt er licenseret under MIT licensen.

# Jarvis-lite Projekt Status

## Aktuel Status
Vi har netop gennemført en større oprydning og omstrukturering af projektet:

### ✅ Gennemførte Opgaver
1. **Filstruktur Optimering**
   - Konsolideret API server filer
   - Fjernet duplikerede filer
   - Organiseret static filer i én mappe
   - Flyttet konfigurationsfiler til `config` mappen
   - Flyttet logs til `logs` mappen

2. **Kodebase Forbedringer**
   - Opdateret `api_server.py` med bedre CORS håndtering
   - Forbedret statisk fil håndtering
   - Implementeret mere robust NLU integration
   - Forbedret fejlhåndtering

3. **Launcher System**
   - `jarvis_launcher.py` som primær launcher
   - `dev_launcher.py` til udvikling med auto-reload
   - Fjernet forældede launcher scripts

### 🔄 Igangværende Arbejde
1. **Model Integration**
   - Arbejder på at skifte til mindre model (opt-125m)
   - Håndtering af danske tegn (æ,ø,å)
   - Forbedring af model konfiguration

2. **Web Interface**
   - Optimering af endpoints
   - Forbedring af static file serving
   - Arbejde på responsivt design

### 📁 Projektstruktur
```
Jarvis-lite/
├── api_server.py          # Hovedserver med API endpoints
├── jarvis_main.py         # Kernelogik og LLM integration
├── jarvis_launcher.py     # Produktions launcher
├── dev_launcher.py        # Udviklings launcher med hot-reload
├── config/                # Konfigurationsfiler
├── src/
│   ├── audio/            # Lydbehandling
│   ├── commands/         # Kommandohåndtering
│   ├── core/             # Kernefunktionalitet
│   ├── llm/             # LLM integration
│   ├── modules/         # Udvidelsesmoduler
│   └── nlu/             # Natural Language Understanding
├── static/               # Frontend filer
│   ├── css/
│   ├── js/
│   └── img/
└── logs/                 # Log filer
```

## 📋 Næste Skridt

### 1. Model Optimering
- [ ] Implementer caching af model output
- [ ] Tilføj mulighed for at skifte mellem forskellige modeller
- [ ] Optimér token håndtering for dansk tekst
- [ ] Implementer bedre fejlhåndtering ved model timeout

### 2. Frontend Forbedringer
- [ ] Implementer real-time chat opdateringer
- [ ] Tilføj loading indikatorer
- [ ] Forbedre mobile responsive design
- [ ] Implementer dark mode

### 3. Backend Udvikling
- [ ] Tilføj rate limiting
- [ ] Implementer session håndtering
- [ ] Forbedre error logging
- [ ] Tilføj health checks for alle services

### 4. Dokumentation
- [ ] Skriv API dokumentation
- [ ] Tilføj setup guide
- [ ] Dokumenter konfigurationsmuligheder
- [ ] Lav udvikler guide

### 5. Testing
- [ ] Skriv unit tests
- [ ] Implementer integration tests
- [ ] Tilføj performance tests
- [ ] Setup CI/CD pipeline

## 🐛 Kendte Problemer
1. Model bruger for meget hukommelse ved lange samtaler
2. Nogle danske tegn vises ikke korrekt i output
3. Frontend loader langsomt på mobile enheder
4. Manglende fejlhåndtering ved netværksproblemer

## 💡 Fremtidige Ideer
1. Implementer stemmegenkendelse
2. Tilføj support for flere sprog
3. Udvikl plugin system
4. Tilføj brugerspecifikke indstillinger

## 🔧 Setup Guide
1. Klon repository
2. Opret virtual environment: `python -m venv .venv`
3. Aktiver environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Installer dependencies: `pip install -r requirements.txt`
5. Start udviklings server: `python dev_launcher.py`
6. Start produktion: `python jarvis_launcher.py`

## 🤝 Bidrag
Hvis du vil bidrage til projektet:
1. Fork repository
2. Opret en feature branch
3. Commit dine ændringer
4. Push til branch
5. Opret Pull Request

## 📝 Noter
- Husk at køre tests før commit
- Følg PEP 8 style guide
- Dokumenter nye funktioner
- Hold dependencies opdateret

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

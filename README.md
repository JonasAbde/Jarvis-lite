# Jarvis Lite

**Jarvis Lite** er en dansk AI-assistent, der kører lokalt på din PC. Jarvis Lite kan lytte til din tale, forstå indholdet, udføre opgaver og svare med både tekst og stemme.

## Projektbeskrivelse

Jarvis Lite omfatter:
- Optagelse af lyd og omdannelse til tekst via tale-til-tekst (STT) med faster-whisper
- Forståelse af brugerens input med NLU-klassificering og en dansk LLM-model
- Generering af svar og afspilning via tekst-til-tale (TTS) med gTTS
- Lagring af samtalehistorik for bedre kontekst i dialogen
- Offline-kørsel med lokal model

## Formål

Formålet er at demonstrere, hvordan man bygger en dansk sprogbaseret AI-assistent med fuld offline-funktionalitet. Projektet fokuserer på at opnå naturlig dansk interaktion med brugeren.

## Projektstruktur

```
jarvis-lite/
├── src/                  # Kildekode
│   ├── audio/           # STT og TTS funktionalitet
│   ├── llm/             # Sprogmodel og inferens
│   ├── nlu/             # Intent-klassificering
│   ├── commands/        # Kommandohåndtering
│   ├── data/            # Datafiler
│   ├── training/        # Træningsscripts
│   ├── cache/           # Cache til modeller og TTS
│   ├── jarvis.py        # Hovedprogram
│   └── demo.py          # Demo-version uden afhængigheder
├── tests/                # Testfiler
├── docs/                 # Dokumentation
├── models/               # Gemte modeller
├── data/                 # Eksterne data (samtaler, stemmemodeller)
├── logs/                 # Logfiler
└── config/               # Konfigurationsfiler
```

## Installation

1. Klon repositoriet:
```bash
git clone https://github.com/din-bruger/jarvis-lite.git
cd jarvis-lite
```

2. Opret et virtuelt miljø:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Installer afhængigheder:
```bash
pip install -r requirements.txt
```

## Brug

Start Jarvis:
```bash
python src/jarvis.py
```

Jarvis lytter efter din stemme og forsøger at forstå og besvare dine spørgsmål eller udføre kommandoer.

## Funktioner

- Tale-til-tekst konvertering på dansk med faster-whisper
- Intent-genkendelse med TF-IDF og LogReg (konfidens-tærskel 0,55)
- GPT-2 dansk model til naturlige svar
- Tekst-til-tale med dansk optimering
- Kontekstbevarende samtaler
- Lydoptagelse med støjreduktion

## Udvikling

Se [udviklingsguiden](docs/development.rst) for detaljer om hvordan du bidrager til projektet.

## Licens

MIT License

### MCP-integration

1. Klon & start lokal MCP-server (se `mcp-server/` submodule).
2. Installer dep's: `pip install mcp`.
3. Definér dine tools i `mcp-server/python/tools/`.
4. Start server: `uvicorn mcp_server:app --reload`.
5. Jarvis-Lite initialiserer `JarvisMCP` til `http://127.0.0.1:8000` og bruger:
   - `push_context(...)`
   - `get_context()`
   - `invoke_tool(tool, args)`
   - `save_state/load_state`

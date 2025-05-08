# Jarvis-Lite

En dansk sprogbaseret AI assistent med tale-til-tekst og tekst-til-tale funktionalitet.

## Funktioner

- Tale-til-tekst konvertering på dansk
- Naturlig sprogforståelse
- Tekst-til-tale output
- Kommandohåndtering
- Kontekstbevarende samtaler

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

4. Opret en .env fil med dine API nøgler:
```
GOOGLE_API_KEY=din_google_api_nøgle
```

## Brug

Start Jarvis:
```bash
python src/jarvis_main.py
```

Aktiver Jarvis ved at sige "Jarvis" og derefter din kommando.

## Projektstruktur

```
jarvis-lite/
├── src/                    # Kildekode
│   ├── commands/          # Kommandohåndtering
│   ├── data/             # Datafiler
│   └── training/         # Træningsscripts
├── tests/                 # Testfiler
├── docs/                  # Dokumentation
├── models/               # Gemte modeller
└── config/               # Konfigurationsfiler
```

## Udvikling

Se [udviklingsguiden](docs/development.rst) for detaljer om hvordan du bidrager til projektet.

## Licens

MIT License

# Jarvis-Lite

En dansk offline stemmeassistent udviklet med Python.

## Status (Maj 2025)

Vi har arbejdet med Jarvis-Lite, en dansk offline stemmeassistent. Assistenten har udfordringer med NLU-genkendelse (Natural Language Understanding), hvor der er problemer med at finde den korrekte model.

### Hvad vi har lavet

1. Gentrænet NLU-modellen med 224 træningseksempler fordelt på 18 intentioner
2. Sikret at modellen gemmes i den korrekte mappe
3. Fikset importen mellem moduler ved at tilrette `_load_model` i classifier.py
4. Identificeret hovedproblemet: API-serveren kører i "simuleret tilstand" fordi den ikke kan indlæse kernemodulerne korrekt

### Aktuel status

- NLU-modellen trænes med ca. 47% nøjagtighed
- API-serveren kan startes, men kører stadig i simuleret tilstand
- Klassifikatoren forsøger at indlæse modellen, men får fejl med import
- Brugergrænsefladen viser standard-svar, når den ikke kan forstå forespørgsler

### Udestående opgaver

1. Fikse import-problemer i NLU-klassifikatoren
2. Forbedre NLU-modellens træningsdata (specielt for 'identity' intent)
3. Implementere korrekt integration mellem API-server og Jarvis kernemodulerne
4. Oprette config/commands.yaml til dynamiske kommandoer
5. Implementere fallback-logik når NLU-modellen ikke kan genkende intents

## Installation

### Forudsætninger

- Python 3.11 eller nyere
- pip (Python Package Manager)
- Windows 10 eller nyere (testet på Windows 10.0.26100)

### Trin-for-trin installation

1. **Klon repositoriet**
   ```bash
   git clone https://github.com/dit-username/Jarvis-lite.git
   cd Jarvis-lite
   ```

2. **Opsæt virtuelt miljø**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Installer dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Træn NLU-modellen**
   ```bash
   cd src/nlu/training
   python train_model.py
   cd ../../..
   ```

5. **Start API-serveren**
   ```bash
   python src/api_server.py
   ```

6. **Åbn web-grænsefladen**
   Besøg [http://localhost:8000](http://localhost:8000) i din webbrowser

## Arkitektur

### Hovedkomponenter
- **API-server (api_server.py)**: FastAPI-baseret server til frontend kommunikation
- **Jarvis (jarvis.py)**: Kernelogik for stemmeassistenten
- **NLU (nlu/classifier.py)**: Natural Language Understanding model
- **Audio (audio/speech.py)**: Stemmegengivelse og -genkendelse

### Kendte problemer
1. Import-cirkelreference mellem moduler
2. NLU-model indlæses ikke korrekt
3. Konfigurations-filer mangler eller indlæses ikke
4. Forkert sti til modelfilerne

## Bidrag til projektet

Vil du bidrage til projektet? Her er hvordan:

1. Fork repositoriet
2. Opret en feature branch (`git checkout -b feature/amazing-feature`)
3. Commit dine ændringer (`git commit -m 'feat: Tilføj en fantastisk feature'`)
4. Push til branchen (`git push origin feature/amazing-feature`)
5. Opret et Pull Request

## Licens

Dette projekt er licenseret under MIT-licensen - se LICENSE-filen for detaljer.

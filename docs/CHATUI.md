# Jarvis-Lite Chat Funktionalitet

Dette dokument beskriver chat-funktionaliteten i Jarvis-Lite, en dansk offline stemmeassistent.

## Arkitektur

Chat-funktionaliteten består af følgende komponenter:

1. **API-server** (`src/api_server.py`): Håndterer kommunikation mellem chatgrænsefladen og Jarvis-kernefunktionaliteten
2. **Webserver** (`src/static_server.py`): Serverer de statiske filer til chatgrænsefladen
3. **Chatgrænseflade** (`src/static/`): HTML, CSS og JavaScript til brugergrænsefladen
4. **Byggeværktøj** (`build_exe.py`): Pakker Jarvis som en Windows-applikation

## Dataflow

1. Brugeren interagerer med Jarvis via chat eller tale i webgrænsefladen
2. Webgrænsefladen sender brugerens input til API-serveren via HTTP POST
3. API-serveren kalder `process_input_text()` fra Jarvis' kernemodul
4. Jarvis behandler inputtet og genererer et svar
5. API-serveren returnerer svaret til webgrænsefladen
6. Webgrænsefladen viser svaret og kan også afspille det som tale

## API-endpoints

API-serveren tilbyder følgende endpoints:

- `GET /status`: Returnerer Jarvis' aktuelle status (lytter/inaktiv)
- `POST /command/listen_toggle`: Aktiverer/deaktiverer aktiv lytning
- `GET /logs/recent`: Henter de seneste loghændelser
- `POST /chat/send`: Sender en besked til Jarvis og modtager et svar
- `GET /chat/history`: Henter chat-historikken

## Start/Stop

Chat-funktionaliteten startes automatisk når du kører `start_jarvis.ps1`. Dette starter:

1. MCP-serveren på port 8000
2. API-serveren på port 8001 
3. Web-UI serveren på port 8080
4. Åbner en browser med chatgrænsefladen

For at stoppe chat-funktionaliteten, luk PowerShell-vinduerne eller tryk Ctrl+C i hovedvinduet.

## Installation som Windows-applikation

Du kan bygge Jarvis-Lite som en Windows-applikation ved at køre:

```
python build_exe.py
```

Dette opretter en eksekverbar fil i `dist/`-mappen, som brugere kan installere og køre uden at have Python installeret.

## Tilpasning

### Tilføj nye kommandoer

Nye kommandoer tilføjes til Jarvis' kernefunktionalitet og bliver automatisk tilgængelige via chatgrænsefladen.

### Ændre udseende

Du kan ændre chatgrænsefladens udseende ved at redigere `src/static/style.css`.

### Tilføj nye funktioner

Nye funktioner kan tilføjes til webgrænsefladen ved at redigere `src/static/app.js` og tilføje nye API-endpoints i `src/api_server.py`.

## Fejlfinding

### API-server starter ikke

- Tjek om portene er tilgængelige
- Tjek om alle afhængigheder er installeret (`pip install -r requirements.txt`)

### Chatgrænseflade viser ikke svar

- Tjek om API-serveren kører (`http://localhost:8001/status`)
- Tjek om CORS er konfigureret korrekt i API-serveren
- Tjek JavaScript-konsollen i browseren for fejl

### Tale virker ikke

- Tjek om PyAudio er installeret korrekt
- Prøv at køre `fix_pyaudio.ps1` for at løse lydproblemer

## Fremtidige udvidelser

- Integration med desktop-notifikationer
- Offline sprogmodel til talegenkendelse i browseren
- Tilføjelse af stemmevalg i brugergrænsefladen
- Mulighed for at gemme og eksportere samtaler 
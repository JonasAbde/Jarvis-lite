# Jarvis Lite - En Personlig AI-Assistent 🤖

## 1. Introduktion

### Projektoversigt
Jarvis Lite er en simpel personlig assistent, udviklet som eksamensprojekt i faget "Kunstig intelligens i praksis" (ITEK-F24V). Projektet er udviklet af fire studerende på 2. semester, der ønskede at skabe en praktisk og lærerig løsning inden for AI.

### Gruppemedlemmer
- Jonas Abde
- David Bashar Al-Basi
- Elmedin Babajic
- Mirac Dinc

### Projektbeskrivelse
Jarvis Lite er designet som en simpel, men funktionel AI-assistent, der kan hjælpe brugeren med daglige opgaver som at fortælle tiden, åbne hjemmesider, gemme noter og give motivation. Projektet demonstrerer grundlæggende AI-koncepter og programmeringsteknikker, der er relevante for 2. semester studerende.

## 2. Formål og Læringsmål

### Formål
Projektet har til formål at:
- Demonstrere praktisk anvendelse af AI-koncepter
- Implementere en funktionel AI-assistent
- Lære at arbejde med tekst-til-tale teknologi
- Øve filhåndtering og datastrukturer
- Forstå grundlæggende AI-logik

### Læringsmål (ITEK-F24V)
Projektet opfylder følgende læringsmål:
- Input/output-funktioner
- If-else beslutningsstruktur
- Datastrukturer og filhåndtering
- Præsentation i Jupyter
- Simpel AI-logik uden neurale netværk

## 3. Teknologi og Værktøjer

### Kerne-teknologier
- **Python 3**: Hovedprogrammeringssprog
- **Jupyter Notebook**: Præsentation og demonstration
- **pyttsx3**: Text-to-speech funktionalitet
- **webbrowser**: Åbning af hjemmesider
- **datetime**: Tidshåndtering
- **os**: Filsystemhåndtering

### Værktøjer til udvikling
- **VS Code**: Kodeudvikling
- **Git**: Versionskontrol
- **unittest**: Test af funktionalitet
- **Markdown**: Dokumentation

## 4. Funktioner i Jarvis Lite

### Core Funktionalitet
1. **get_time()**
   - Henter aktuel tid
   - Formaterer tidspunktet
   - Returnerer besked på dansk

2. **save_note()**
   - Gemmer noter i tekstfil
   - Tilføjer tidsstempel
   - Håndterer fejl

3. **read_notes()**
   - Læser alle gemte noter
   - Viser dem i kronologisk rækkefølge
   - Håndterer tomme filer

4. **motivate()**
   - Vælger tilfældig motiverende besked
   - Inkluderer emojis
   - Returnerer positiv feedback

5. **open_website()**
   - Åbner URL i standardbrowser
   - Validerer input
   - Håndterer fejl

### Kommando-tolkning
```python
if "klokken" in command:
    return get_time()
elif "gem" in command:
    return save_note(command)
# ... osv.
```

## 5. Udviklingsproces

### Samarbejde
- Daglige møder via Discord
- Opdeling af opgaver
- Code review sessions
- Fælles problemløsning

### Roller
- **Jonas**: Core funktionalitet
- **David**: Voice integration
- **Elmedin**: Test og dokumentation
- **Mirac**: UI og præsentation

## 6. Test og Validering

### Testmetoder
- Unit tests for hver funktion
- Manuelle tests af brugerinteraktion
- Fejlhåndteringstests
- Performance tests

### Testdækning
- 100% dækning af core funktioner
- Validering af input/output
- Fejlhåndtering verificeret
- Brugertests gennemført

## 7. Refleksion og Evaluering

### Læringspunkter
- Vigtigheden af god fejlhåndtering
- Værdien af test-drevet udvikling
- Samarbejde i grupper
- Dokumentations betydning

### Forbedringspunkter
- Tilføje flere funktioner
- Forbedre stemmegenkendelse
- Implementere machine learning
- Udvide sprogunderstøttelse

## 8. Konklusion

Jarvis Lite demonstrerer succesfuldt implementeringen af en simpel AI-assistent, der opfylder de grundlæggende krav for et 2. semester projekt. Projektet viser praktisk anvendelse af AI-koncepter og giver et solidt fundament for fremtidig udvikling.

<!-- Eksport til PDF kan gøres med:
1. Pandoc: `pandoc rapport.md -o rapport.pdf`
2. VS Code med Markdown PDF extension
3. Online Markdown til PDF konvertering --> 
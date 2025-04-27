# Jarvis Lite - Versionshistorik

Dette dokument beskriver de forskellige versioner af Jarvis Lite-projektet og deres funktionaliteter, udviklet som en del af eksamensprojektet.

## Oversigt over versioner

| Version               | Beskrivelse                                      | Nøgleteknologier                               |
|-----------------------|-------------------------------------------------|------------------------------------------------|
| **Basis**             | Grundlæggende kommandohåndtering med if/else    | Python core, webbrowser, datetime              |
| **Dictionary-baseret**| Forbedret kommandohåndtering med dictionary     | Python collections, funktioner som first-class |
| **ML-baseret**        | Intent-genkendelse med Machine Learning         | TensorFlow, NLU, neuralt netværk               |
| **Komplet aflevering**| Færdig eksamenspakke med alle komponenter       | Alt det ovenstående + automatisk installation  |

---

## Detaljeret beskrivelse af versioner

### 1. Basis version (`main.py`)

**Beskrivelse:**
Den grundlæggende version af Jarvis Lite implementerer en simpel personlig assistent med tekstbaseret input og output. Kommandohåndtering sker ved hjælp af `if/else`-betingelser.

**Funktionaliteter:**
- Grundlæggende kommandogenkendelse via tekstsammenligning
- Fortælle klokkeslæt
- Åbne YouTube og andre websider
- Gemme noter i en fil
- Tale-output via gTTS

**Teknisk implementation:**
- Direkte sammenligning af brugerinput med kendte kommandoer
- Betingelsesbaseret logik med `if/elif/else`
- Simpel teksthåndtering med `in` og `.startswith()`

**Styrker og svagheder:**
- ✅ Nem at forstå og implementere
- ✅ Fungerer pålideligt for præcist matchende kommandoer
- ❌ Ingen fleksibilitet ved varierende input
- ❌ Kræver præcis match af kommandoer

---

### 2. Dictionary-baseret version (`Jarvis_Lite_Eksamen.ipynb`)

**Beskrivelse:**
Denne version forbedrer kommandogenkendelsen ved at bruge et `command_map` dictionary til at mappe kommandoer til funktioner. Dette gør koden mere modulær og lettere at udvide.

**Funktionaliteter:**
- Alle basisfunktioner fra første version
- Forbedret kommandohåndtering med dictionary
- Flere forskellige måder at udtrykke samme kommando
- Mere struktureret kode med separate funktioner for hver handling

**Teknisk implementation:**
- `command_map` dictionary der mapper kommando-tekst til funktionsreferencer
- Funktioner behandles som first-class objekter
- Modulariseret kode med bedre separation af ansvar

**Styrker og svagheder:**
- ✅ Mere vedligeholdelig og udvidelig kodebase
- ✅ Klarere struktureret kode
- ✅ Nemmere at tilføje nye kommandoer
- ❌ Stadig begrænset til præcist definerede kommandoer
- ❌ Kræver manuel tilføjelse af hver kommandovariation

---

### 3. ML-baseret version (`scripts/jarvis_lite.py`)

**Beskrivelse:**
Den mest avancerede version bruger Machine Learning (TensorFlow) til at genkende brugerens intention (intent) bag kommandoer, selv når de er formuleret på forskellige måder.

**Funktionaliteter:**
- Intent-genkendelse via et trænet neuralt netværk
- Evne til at forstå varierende formuleringer af samme kommando
- Fleksibel håndtering af brugerinput
- Personaliserede svar med variation og emojis
- Tidspunktsbaserede svar (forskelligt om morgenen, dagen, aftenen)

**Teknisk implementation:**
- TensorFlow og Keras til at bygge og træne et neuralt netværk
- Tekstbehandling med tokenization og padding
- Intents og eksempler på udtryk for hver intent
- Embedding-lag til at omdanne ord til vektorer
- Feed-forward neuralt netværk til klassificering

**ML-model arkitektur:**
- **Input:** Tokeniseret og padded tekst
- **Embedding-lag:** Omdanner ordene til vektorer i et semantisk rum
- **GlobalAveragePooling1D:** Reducerer dimensionalitet
- **Dense-lag (16 neuroner, ReLU):** Første hidden layer
- **Dense-lag (antal intents, Softmax):** Output-lag der giver sandsynligheder

**Styrker og svagheder:**
- ✅ Kan genkende intentioner uden præcist match
- ✅ Mere naturlig og fleksibel brugeroplevelse
- ✅ Kan generalisere til nye formuleringer
- ✅ Demonstrerer ML-principper fra undervisningen
- ❌ Kræver installation af TensorFlow
- ❌ Mere kompleks at forstå og vedligeholde

---

### 4. Komplet aflevering (hele `JarvisLite_Eksamen`-mappen)

**Beskrivelse:**
Den komplette afleveringspakke indeholder ML-versionen, automatiske installationsscripts, dokumentation og justeringer for at gøre projektet nemt at distribuere og afprøve.

**Indhold:**
- **scripts/jarvis_lite.py:** Hovedprogrammet med ML-baseret intent-genkendelse
- **notebooks/:** Jupyter Notebook-version til undervisningsbrug
- **setup.bat:** Automatisk installationsscript
- **start_jarvis.bat:** Nem start af programmet
- **start_notebook.bat:** Nem åbning af Jupyter Notebook
- **requirements.txt:** Liste over nødvendige pakker
- **README.md:** Dokumentation og brugsanvisning

**Teknisk implementation:**
- Automatiseret installation med virtuelt miljø
- Struktureret mappeorganisation
- Batch-scripts til nem brug
- Omfattende dokumentation
- Klar pakke til aflevering og deling

**Styrker:**
- ✅ Professionel præsentation
- ✅ Nem installation og brug for modtageren
- ✅ Veldokumenteret kode og funktionalitet
- ✅ Demonstrerer både ML-teknikker og software engineering best practices

---

## Sammenligning af de tre implementeringsmetoder

| Aspekt                 | Basis (if/else)     | Dictionary           | ML (TensorFlow)       |
|------------------------|---------------------|----------------------|-----------------------|
| **Kompleksitet**       | Lav                 | Medium               | Høj                   |
| **Fleksibilitet**      | Lav                 | Medium               | Høj                   |
| **Vedligeholdelse**    | Svær ved udvidelse  | Moderat skalerbar    | God skalerbarhed      |
| **Brugeroplevelse**    | Rigid, præcis       | Struktureret         | Naturlig, fleksibel   |
| **Demonstrerer**       | Basis programmering | Datastrukturer       | ML og NLU-principper  |
| **Kodelinjer (ca.)**   | 100                 | 150                  | 300                   |

---

## Teknologier anvendt i projektet

Projektet viser anvendelse af følgende teknologier, som er relateret til pensum:

1. **Kunstig intelligens (AI)** - implementeret i ML-version via TensorFlow
2. **Machine Learning** - træning af model til intent-genkendelse
3. **Neuralt netværk** - struktur med input, hidden og output lag
4. **Datastrukturer** - dictionary, arrays, sequences
5. **Beslutningslogik** - if/elif/else, dictionary-lookups, model-baseret
6. **Text-to-Speech** - gTTS for taleoutput
7. **Filhåndtering** - gemme og læse noter i tekstfil

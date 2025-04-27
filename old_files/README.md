# Jarvis Lite 🤖

En simpel personlig assistent udviklet af studerende på 2. semester i faget "Kunstig intelligens i praksis (ITEK-F24V)".

## 👥 Gruppemedlemmer
- Jonas Abde
- David Bashar Al-Basi
- Elmedin Babajic
- Mirac Dinc

## 🚀 Funktioner
- Fortæller hvad klokken er ⏰
- Åbner hjemmesider 🌐
- Gemmer noter 📝
- Motiverer brugeren 💪

## 📋 Installation
1. Klon dette repository
2. Installer de nødvendige pakker:
```bash
pip install -r requirements.txt
```

## 💻 Brug
1. Åbn `notebooks/JarvisLiteDemo.ipynb` i Jupyter Notebook
2. Følg instruktionerne i notebook'en
3. Prøv forskellige kommandoer som:
   - "Hvad er klokken?"
   - "Åbn google.com"
   - "Gem Husk at lave lektier"
   - "Motiver mig"
   - "Vis mine noter"

## 🏗️ Projektstruktur
```
Jarvis-Lite/
├── README.md
├── requirements.txt
├── notebooks/
│   └── JarvisLiteDemo.ipynb
├── src/
│   ├── jarvis_core.py
│   ├── jarvis_commands.py
│   └── jarvis_voice.py
├── data/
│   └── notes.txt
```

## 📚 Teknologier
- Python 3
- Jupyter Notebook
- pyttsx3 (text-to-speech)
- webbrowser
- datetime
- file I/O

## 📝 Noter
- Noter gemmes i `data/notes.txt`
- Systemet bruger dansk tale, hvis tilgængeligt
- Alle fejl håndteres elegant med brugervenlige fejlmeddelelser

## 🤝 Bidrag
Dette projekt er udviklet som en del af undervisningen og er ikke åben for eksterne bidrag.

## 📄 Licens
Dette projekt er licenseret under MIT License - se [LICENSE](LICENSE) filen for detaljer.

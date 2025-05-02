# Jarvis Lite – Opsætning

Denne guide beskriver trin for trin, hvordan du installerer Jarvis Lite på en Windows-maskine.

## 1. Krav
* **Windows 10/11**
* **Python 3.11** *(64-bit)*
* **Git** (for at klone repo)
* **FFmpeg** i `PATH`
* *(Valgfrit)* NVIDIA GPU + CUDA 12 til hurtigere Whisper

## 2. Klon og opret virtuelt miljø
```powershell
# åbn PowerShell
cd C:\Sti\til\projekter
 git clone https://github.com/<dit>/Jarvis-lite.git
cd Jarvis-lite
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # aktiver venv
```

## 3. Installer system-afhængigheder
### FFmpeg
```powershell
winget install Gyan.FFmpeg --accept-package-agreements
```
(eller hent zip fra https://www.gyan.dev/ffmpeg/builds/, kopier `bin\ffmpeg.exe` til en mappe i `PATH`).

### CUDA-PyTorch (valgfrit, men stærkt anbefalet)
```powershell
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 4. Installer Python-pakker
```powershell
pip install --upgrade pip
pip install -r requirements.txt
# Sørg for korrekt Whisper-pakke
pip uninstall -y whisper openai-whisper
pip install git+https://github.com/openai/whisper.git
```

## 5. Første kørsel
```powershell
python jarvis_main.py
```
Du bør se:
```
[INFO] Whisper model ('small') indlæst på GPU (cuda).
=== Jarvis Lite er klar! ===
```

Tryk **Ctrl+C** for at stoppe.

## Fejlfinding
| Problem | Løsning |
|---------|---------|
| `whisper.load_audio` → *WinError 2* | FFmpeg mangler → installer/tilføj til PATH |
| Whisper kører på CPU | Installer CUDA-PyTorch |
| `torch.cuda.is_available()` = False | Kontroller GPU-driver + CUDA version |

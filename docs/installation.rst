Installation
============

Systemkrav
---------

* Python 3.9 eller nyere
* FFmpeg installeret
* CUDA-kompatibel GPU (valgfrit, men anbefalet)

Installation
-----------

1. Klon repository'et:

   .. code-block:: bash

      git clone https://github.com/your-username/jarvis-lite.git
      cd jarvis-lite

2. Opret og aktiver et virtuelt miljø:

   .. code-block:: bash

      python -m venv .venv
      # På Windows:
      .\.venv\Scripts\activate
      # På Linux/Mac:
      source .venv/bin/activate

3. Installer dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

4. Download Faster-Whisper modellen:

   .. code-block:: bash

      python -c "from faster_whisper import WhisperModel; WhisperModel('small')"

5. Træn NLU-modellen:

   .. code-block:: bash

      python src/nlu_trainer.py

Fejlfinding
----------

Hvis du oplever problemer med lydindlæsning, sørg for at FFmpeg er installeret:

* **Windows**: Download fra `ffmpeg.org` og tilføj til PATH
* **Linux**: ``sudo apt install ffmpeg``
* **Mac**: ``brew install ffmpeg``

For GPU-acceleration, installer CUDA og cuDNN:

* **Windows**: Download CUDA Toolkit fra NVIDIA's hjemmeside
* **Linux**: ``sudo apt install nvidia-cuda-toolkit``
* **Mac**: CUDA understøttes ikke på Mac 
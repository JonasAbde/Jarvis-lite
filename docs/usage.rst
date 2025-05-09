Brugerguide
===========

Dette dokument beskriver hvordan du bruger Jarvis-lite.

Kørsel
------

Start Jarvis ved at køre:

.. code-block:: bash

   python jarvis_main.py

Jarvis vil nu lytte efter kommandoer. Tryk Ctrl+C for at afslutte.

Kommandoer
---------

Jarvis forstår følgende kommandoer:

* **Tid**
  * "Hvad er klokken?"
  * "Klokken"

* **Web**
  * "Åbn YouTube"
  * "Åbn Gmail"

* **Noter**
  * "Gem en note"
  * "Skriv en note"

* **Underholdning**
  * "Fortæl en joke"
  * "Sig en joke"

* **System**
  * "Stop lyden"
  * "Hold mund"

Fejlfinding
----------

Hvis Jarvis ikke svarer:

1. Tjek at din mikrofon virker
2. Sørg for at du taler tydeligt
3. Kontroller internetforbindelsen (kræves for TTS)
4. Prøv at genstarte programmet

Hvis Jarvis ikke forstår:

1. Prøv at omformulere kommandoen
2. Tal langsommere og tydeligere
3. Undgå baggrundsstøj

Tekniske Detaljer
---------------

* STT: Faster-Whisper (small model)
* TTS: Google Text-to-Speech
* NLU: TF-IDF + LogisticRegression
* Konfidens-tærskel: 0.55 
Jarvis-lite Dokumentation
========================

.. toctree::
   :maxdepth: 2
   :caption: Indhold:

   installation
   usage
   api
   development

Indledning
---------

Jarvis-lite er en dansk, offline stemmeassistent bygget med moderne AI-teknologier.
Systemet bruger Faster-Whisper til tale-til-tekst, scikit-learn til intent-genkendelse,
og Google Text-to-Speech til tekst-til-tale.

Hovedfunktioner
~~~~~~~~~~~~~

* Tale-til-tekst konvertering med Faster-Whisper
* Intent-genkendelse med TF-IDF og LogisticRegression
* Kommando-udførelse (klokken, YouTube, Gmail, etc.)
* Text-to-speech svar med gTTS

Teknisk Stack
~~~~~~~~~~~~

* **STT**: Faster-Whisper (INT8 kvantisering)
* **TTS**: Google Text-to-Speech
* **NLU**: scikit-learn + TF-IDF
* **AI**: Kalibreret klassifikator

Indeks og tabeller
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 
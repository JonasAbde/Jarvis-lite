try:
    # Forsøg forskellige import-stier afhængigt af, hvordan scriptet er kørt
    try:
        from jarvis import process_input_text, speak_async
    except ImportError:
        from src.jarvis import process_input_text, speak_async
    
    JARVIS_CORE_AVAILABLE = True
    logger.info("Jarvis kernemodulimport lykkedes.")
except ImportError:
    logger.warning("Kunne ikke importere Jarvis kernemoduler. Kører i simuleret tilstand.")
    JARVIS_CORE_AVAILABLE = False
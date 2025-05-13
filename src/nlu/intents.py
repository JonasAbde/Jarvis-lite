from typing import Dict, List

# Grundlæggende hilsner og deres svar
GREETING_INTENTS: Dict[str, List[str]] = {
    "greeting": [
        "hej",
        "godmorgen",
        "goddag",
        "godaften",
        "hallo",
        "hi",
        "hey"
    ],
    "farewell": [
        "farvel",
        "vi ses",
        "hej hej",
        "goodbye",
        "tak for nu"
    ]
}

GREETING_RESPONSES: Dict[str, List[str]] = {
    "greeting": [
        "Hej! Hvordan kan jeg hjælpe dig i dag?",
        "Goddag! Hvad kan jeg gøre for dig?",
        "Hej med dig! Jeg er klar til at hjælpe.",
        "Velkommen! Hvad har du brug for hjælp til?"
    ],
    "farewell": [
        "Farvel! Hav en god dag.",
        "Vi ses! Tak for snakken.",
        "Hej hej! Det var hyggeligt at snakke med dig.",
        "Tak for nu! Sig til hvis du får brug for mere hjælp."
    ]
}

def get_greeting_response(intent: str) -> str:
    """Returner et tilfældigt svar baseret på intent"""
    import random
    if intent in GREETING_RESPONSES:
        return random.choice(GREETING_RESPONSES[intent])
    return "Jeg er ikke sikker på, hvordan jeg skal svare på det. Hvordan kan jeg hjælpe dig?" 
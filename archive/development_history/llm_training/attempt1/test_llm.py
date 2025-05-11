from src.llm.model import load_model, generate_response
import logging

# Konfigurer logging
logging.basicConfig(level=logging.INFO)

def main():
    # Indlæs modellen
    if not load_model():
        print("Kunne ikke indlæse modellen")
        return
    
    # Test prompt
    messages = [
        {"role": "user", "content": "Hvad er din holdning til kunstig intelligens?"}
    ]
    
    # Generer svar
    response = generate_response(messages)
    print("\nBruger:", messages[0]["content"])
    print("Assistent:", response)

if __name__ == "__main__":
    main() 
"""
Visualiseringsværktøjer til Jarvis' neurale netværk.
"""
import torch
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
import seaborn as sns
from transformers import AutoTokenizer
import logging

logger = logging.getLogger(__name__)

class ModelVisualizer:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        
    def visualize_attention(self, text: str, layer_index: int = -1) -> None:
        """
        Visualiserer attention weights for en given tekst.
        
        Args:
            text: Input tekst
            layer_index: Hvilket transformer lag der skal visualiseres (-1 for sidste lag)
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Kør model med output_attentions=True
            with torch.no_grad():
                outputs = self.model(**inputs, output_attentions=True)
            
            # Hent attention weights
            attention = outputs.attentions[layer_index]
            attention = attention.squeeze(0)  # Fjern batch dimension
            
            # Konverter tokens til læsbare ord
            tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            
            # Opret attention map
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                attention.mean(0).numpy(),  # Gennemsnit over attention heads
                xticklabels=tokens,
                yticklabels=tokens,
                cmap="YlOrRd"
            )
            plt.title(f"Attention Weights (Lag {layer_index})")
            plt.xticks(rotation=45, ha="right")
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Fejl under visualisering af attention: {e}")
    
    def visualize_token_probabilities(self, text: str, top_k: int = 5) -> None:
        """
        Visualiserer sandsynligheder for næste token.
        
        Args:
            text: Input tekst
            top_k: Antal top tokens der skal vises
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Kør model
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits[0, -1, :]  # Tag sidste token
                probs = torch.softmax(logits, dim=0)
            
            # Find top-k tokens
            top_probs, top_indices = torch.topk(probs, k=top_k)
            top_tokens = self.tokenizer.convert_ids_to_tokens(top_indices)
            
            # Plot resultater
            plt.figure(figsize=(10, 5))
            plt.bar(top_tokens, top_probs.numpy())
            plt.title("Top Token Sandsynligheder")
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Sandsynlighed")
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Fejl under visualisering af token sandsynligheder: {e}")
    
    def visualize_layer_activation(self, text: str, layer_name: str = "last_hidden_state") -> None:
        """
        Visualiserer aktivering i et specifikt lag.
        
        Args:
            text: Input tekst
            layer_name: Navnet på laget der skal visualiseres
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Kør model
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
            
            # Hent hidden states
            if layer_name == "last_hidden_state":
                activation = outputs.last_hidden_state[0]  # Fjern batch dimension
            else:
                activation = outputs.hidden_states[-1][0]  # Tag sidste hidden state
            
            # Plot aktiveringsmønster
            plt.figure(figsize=(12, 6))
            sns.heatmap(
                activation.numpy(),
                cmap="viridis",
                xticklabels=False,
                yticklabels=self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            )
            plt.title(f"Lag Aktivering ({layer_name})")
            plt.xlabel("Hidden Dimension")
            plt.ylabel("Tokens")
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Fejl under visualisering af lag aktivering: {e}")

def create_visualizer(model_path: str) -> Optional[ModelVisualizer]:
    """
    Opretter en ModelVisualizer instance.
    
    Args:
        model_path: Sti til den trænede model
    
    Returns:
        ModelVisualizer eller None hvis der opstår fejl
    """
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        return ModelVisualizer(model, tokenizer)
    except Exception as e:
        logger.error(f"Kunne ikke oprette visualizer: {e}")
        return None

if __name__ == "__main__":
    # Test visualiseringer
    model_path = "models/danish-gpt2-jarvis"
    visualizer = create_visualizer(model_path)
    
    if visualizer:
        test_text = "Hej Jarvis, hvordan har du det?"
        
        print("Visualiserer attention weights...")
        visualizer.visualize_attention(test_text)
        
        print("Visualiserer token sandsynligheder...")
        visualizer.visualize_token_probabilities(test_text)
        
        print("Visualiserer lag aktivering...")
        visualizer.visualize_layer_activation(test_text)
    else:
        print("Kunne ikke oprette visualizer") 
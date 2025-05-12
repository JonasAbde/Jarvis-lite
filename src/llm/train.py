"""
Script til at fine-tune GPT-2 modellen på dansk samtaledata.
"""
import os
import json
import logging
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from typing import Dict, List

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Konfiguration
BASE_MODEL = "KennethTM/gpt2-small-danish"  # Start med den mindre model
TRAIN_FILE = "data/training/conversations.json"
OUTPUT_DIR = "models/danish-gpt2-jarvis"
EPOCHS = 3
BATCH_SIZE = 4
LEARNING_RATE = 2e-5
MAX_LENGTH = 128

def load_conversations(file_path: str) -> List[Dict[str, str]]:
    """Indlæser samtaledata fra JSON fil."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["conversations"]

def format_conversation(conversation: Dict[str, str]) -> str:
    """Formaterer en samtale til træningsformat."""
    return f"Bruger: {conversation['human']}\nJarvis: {conversation['assistant']}\n"

def prepare_dataset(conversations: List[Dict[str, str]], tokenizer) -> Dataset:
    """Forbereder dataset til træning."""
    # Formater samtaler
    texts = [format_conversation(conv) for conv in conversations]
    
    # Tokenize tekster
    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
        return_tensors="pt"
    )
    
    # Opret dataset
    dataset = Dataset.from_dict({
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"]
    })
    
    return dataset

def train_model():
    """Træner modellen på samtaledata."""
    try:
        # Indlæs tokenizer og model
        logger.info(f"Indlæser base model: {BASE_MODEL}")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
        
        # Tilføj special tokens hvis nødvendigt
        special_tokens = {
            "pad_token": "<pad>",
            "sep_token": "<sep>",
            "additional_special_tokens": ["<bruger>", "<jarvis>"]
        }
        tokenizer.add_special_tokens(special_tokens)
        model.resize_token_embeddings(len(tokenizer))
        
        # Indlæs og forbered data
        logger.info("Indlæser træningsdata")
        conversations = load_conversations(TRAIN_FILE)
        dataset = prepare_dataset(conversations, tokenizer)
        
        # Opsæt træningsargumenter
        training_args = TrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            warmup_steps=100,
            logging_steps=10,
            save_steps=50,
            eval_steps=50,
            load_best_model_at_end=True,
            save_total_limit=2,
            evaluation_strategy="steps"
        )
        
        # Opret data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Initialiser trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            eval_dataset=dataset,  # Brug samme data til evaluering (ikke optimalt)
            data_collator=data_collator,
            evaluation_strategy="steps"
        )
        
        # Start træning
        logger.info("Starter træning")
        trainer.train()
        
        # Gem model og tokenizer
        logger.info(f"Gemmer model til {OUTPUT_DIR}")
        trainer.save_model()
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        logger.info("Træning færdig!")
        return True
        
    except Exception as e:
        logger.error(f"Fejl under træning: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Opret output mappe hvis den ikke findes
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Start træning
    success = train_model()
    
    if success:
        logger.info("Model trænet og gemt succesfuldt!")
    else:
        logger.error("Træning fejlede.") 
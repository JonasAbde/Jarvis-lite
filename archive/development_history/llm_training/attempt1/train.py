"""
Finjusterer Phi-2 modellen på dansk data.
"""

import os
import torch
import logging
import json
from pathlib import Path
from typing import List, Dict
from transformers.models.auto.modeling_auto import AutoModelForCausalLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.trainer import Trainer
from transformers.training_args import TrainingArguments
from transformers.data.data_collator import DataCollatorForLanguageModeling
from datasets import Dataset

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)

# Konfiguration
MODEL_NAME = "microsoft/phi-2"
OUTPUT_DIR = "models/danish-phi-2"
TRAIN_FILE = "src/llm/training/data/danish_conversations.jsonl"

def load_training_data(file_path: str) -> List[Dict]:
    """Indlæser træningsdata fra JSONL fil."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def format_conversation(conversation: Dict) -> str:
    """Formaterer en samtale til træning."""
    formatted = ""
    for msg in conversation["conversations"]:
        if msg["role"] == "system":
            formatted += f"System: {msg['content']}\n"
        elif msg["role"] == "human":
            formatted += f"Human: {msg['content']}\n"
        elif msg["role"] == "assistant":
            formatted += f"Assistant: {msg['content']}\n"
    return formatted

def prepare_dataset(data: List[Dict], tokenizer) -> Dataset:
    """Forbereder dataset til træning."""
    # Konverter samtaler til tekst
    texts = [format_conversation(item) for item in data]
    
    logger.info(f"Antal træningseksempler: {len(texts)}")
    
    # Tokenize data
    logger.info("Tokenizer input tekst...")
    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=128,  # Yderligere reduceret for CPU træning
        return_tensors="pt"
    )
    
    # Opret dataset
    dataset = Dataset.from_dict({
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"]
    })
    
    logger.info(f"Dataset oprettet med form: {dataset.shape}")
    return dataset

def train_model():
    """Finjusterer modellen på dansk data."""
    try:
        logger.info("Indlæser model og tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        # Tilføj padding token
        tokenizer.pad_token = tokenizer.eos_token
        
        # Indlæs model i float32 format for CPU
        logger.info("Indlæser model...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,  # Brug float32 for CPU
            low_cpu_mem_usage=True,  # Reducer CPU hukommelsesforbrug
            device_map="cpu"  # Tving CPU brug
        )
        
        # Konfigurer model til at bruge padding token
        model.config.pad_token_id = tokenizer.pad_token_id
        
        # Indlæs og forbered data
        logger.info("Forbereder træningsdata...")
        train_data = load_training_data(TRAIN_FILE)
        dataset = prepare_dataset(train_data, tokenizer)
        
        # Træningsargumenter
        training_args = TrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            learning_rate=1e-5,
            weight_decay=0.01,
            warmup_ratio=0.1,
            logging_steps=1,
            save_strategy="epoch",
            report_to="none",
            push_to_hub=False,
            no_cuda=True  # Deaktiver CUDA
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Initialiser trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator
        )
        
        # Start træning
        logger.info("Starter finjustering...")
        trainer.train()
        
        # Gem model og tokenizer
        logger.info(f"Gemmer model i {OUTPUT_DIR}...")
        trainer.save_model()
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        logger.info("Finjustering færdig!")
        
    except Exception as e:
        logger.error(f"Fejl under træning: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Opret output mappe
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Start træning
    train_model() 
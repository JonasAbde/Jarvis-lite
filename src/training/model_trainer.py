from typing import Dict, List, Optional
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

class JarvisDataset(Dataset):
    def __init__(self, tokenizer, data_path: str, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        
        # Load conversations
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            conversations = data.get("conversations", [])
        
        # Format data for training
        for conv in conversations:
            if "human" in conv and "assistant" in conv:
                text = f"Human: {conv['human']}\nAssistant: {conv['assistant']}\n"
                self.examples.append(text)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        text = self.examples[i]
        
        # Tokenize
        encodings = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )
        
        return {
            'input_ids': encodings['input_ids'].squeeze(),
            'attention_mask': encodings['attention_mask'].squeeze()
        }

class ModelTrainer:
    def __init__(
        self,
        base_model: str = "mistralai/Mistral-7B-v0.1",
        output_dir: str = "models/jarvis-danish",
        data_path: str = "data/training/conversations.json"
    ):
        self.base_model = base_model
        self.output_dir = Path(output_dir)
        self.data_path = Path(data_path)
        self.tokenizer = None
        self.model = None
        
    def setup(self):
        """Initialiser model og tokenizer med 4-bit kvantisering"""
        logger.info(f"Indlæser base model: {self.base_model}")
        
        # Konfigurer 4-bit kvantisering
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Indlæs tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        
        # Indlæs model med kvantisering
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        # Aktiver gradient checkpointing for at spare hukommelse
        self.model.gradient_checkpointing_enable()
        
        # Tilføj special tokens
        special_tokens = {
            "pad_token": "<pad>",
            "sep_token": "<sep>",
            "additional_special_tokens": ["<human>", "<assistant>"]
        }
        self.tokenizer.add_special_tokens(special_tokens)
        self.model.resize_token_embeddings(len(self.tokenizer))
        
    def prepare_dataset(self) -> JarvisDataset:
        """Forbered træningsdatasættet"""
        return JarvisDataset(
            tokenizer=self.tokenizer,
            data_path=str(self.data_path)
        )
    
    def train(
        self,
        epochs: int = 3,
        batch_size: int = 1,  # Reduceret batch size for mindre VRAM forbrug
        learning_rate: float = 2e-5,
        warmup_steps: int = 100,
        save_steps: int = 500
    ):
        """Start træningen af modellen med optimeret hukommelsesforbrug"""
        
        # Opret output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Forbered træningsargumenter
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=8,  # Øget for at kompensere for mindre batch size
            warmup_steps=warmup_steps,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=10,
            save_steps=save_steps,
            save_total_limit=2,
            weight_decay=0.01,
            logging_dir=str(self.output_dir / "logs"),
            gradient_checkpointing=True,  # Aktivér gradient checkpointing
            optim="paged_adamw_8bit"  # Brug 8-bit Adam optimizer
        )
        
        # Opret dataset og data collator
        dataset = self.prepare_dataset()
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Initialiser trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator
        )
        
        # Start træning
        logger.info("Starter træning...")
        trainer.train()
        
        # Gem den færdige model
        logger.info("Gemmer model...")
        trainer.save_model(str(self.output_dir / "final"))
        self.tokenizer.save_pretrained(str(self.output_dir / "final"))
        
        logger.info("Træning færdig!") 
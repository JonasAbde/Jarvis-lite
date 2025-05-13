import argparse
import logging
from pathlib import Path
from model_trainer import ModelTrainer
import torch

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_gpu_compatibility():
    """Tjek GPU kompatibilitet og hukommelse"""
    if not torch.cuda.is_available():
        logger.warning("Ingen CUDA-kompatibel GPU fundet!")
        return False
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
    
    logger.info(f"GPU: {gpu_name}")
    logger.info(f"Tilgængelig VRAM: {gpu_memory:.1f}GB")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Træn Jarvis custom model')
    
    parser.add_argument(
        '--base-model',
        type=str,
        default="mistralai/Mistral-7B-v0.1",
        help='Base model at fine-tune fra'
    )
    
    parser.add_argument(
        '--data-path',
        type=str,
        default="data/training/conversations.json",
        help='Sti til træningsdata'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default="models/jarvis-danish",
        help='Output directory til den trænede model'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Antal trænings epochs'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1,
        help='Batch størrelse for træning'
    )
    
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=2e-5,
        help='Learning rate for træning'
    )
    
    parser.add_argument(
        '--gradient-accumulation',
        type=int,
        default=8,
        help='Antal gradient accumulation steps'
    )
    
    parser.add_argument(
        '--max-length',
        type=int,
        default=512,
        help='Maksimal sekvenslængde for input'
    )
    
    args = parser.parse_args()
    
    # Tjek GPU
    if not check_gpu_compatibility():
        logger.warning("Fortsætter med CPU - dette vil være meget langsomt!")
        if not input("Vil du fortsætte? (j/n): ").lower().startswith('j'):
            return
    
    # Valider input stier
    data_path = Path(args.data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Kunne ikke finde træningsdata: {data_path}")
    
    # Initialiser trainer
    trainer = ModelTrainer(
        base_model=args.base_model,
        output_dir=args.output_dir,
        data_path=str(data_path)
    )
    
    # Setup model
    logger.info("Initialiserer model...")
    trainer.setup()
    
    # Start træning
    logger.info("Starter træning med følgende parametre:")
    logger.info(f"Base model: {args.base_model}")
    logger.info(f"Data sti: {args.data_path}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Learning rate: {args.learning_rate}")
    logger.info(f"Gradient accumulation: {args.gradient_accumulation}")
    logger.info(f"Max length: {args.max_length}")
    
    trainer.train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )

if __name__ == "__main__":
    main() 
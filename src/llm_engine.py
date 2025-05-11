"""llm_engine.py
Wrapper omkring en LoRA-finetunet dansk LLM (Transformers + PEFT).

Eksempel:
    from llm_engine import load_model, generate

    load_model(base_model="microsoft/phi-2", lora_path="models/danish_phi2_lora")
    print(generate("Hvad hedder du?"))
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftConfig, PeftModel  # type: ignore

_device = "cuda" if torch.cuda.is_available() else "cpu"
_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[torch.nn.Module] = None


def load_model(base_model: str, *, lora_path: Optional[str] = None, dtype: str = "float16") -> None:
    """Indlæs basis-LLM og (valgfrit) LoRA-vægte.

    Parameters
    ----------
    base_model : str
        HuggingFace-id eller lokal sti til basis-modellen.
    lora_path : str | None
        Sti til LoRA-checkpoint. Hvis None, indlæses kun basis-modellen.
    dtype : str
        "float16", "bfloat16" eller "float32".
    """
    global _tokenizer, _model

    if _model is not None:
        # Allerede indlæst
        return

    torch_dtype = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[dtype]

    print(f"[LLM] Laster tokenizer ({base_model}) ...")
    _tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)

    print(f"[LLM] Laster model ({base_model}) på {_device} ...")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch_dtype,
        device_map="auto" if _device == "cuda" else None,
    )

    if lora_path:
        print(f"[LLM] Anvender LoRA-vægte fra {lora_path} ...")
        cfg = PeftConfig.from_pretrained(lora_path)
        base = PeftModel.from_pretrained(base, lora_path, device_map="auto" if _device == "cuda" else None)

    _model = base.eval()
    print("[LLM] Klar!")


def generate(prompt: str, *, max_new_tokens: int = 128, temperature: float = 0.7, history: Optional[List[Tuple[str, str]]] = None) -> str:
    """Generér svar fra LLM.

    Parameters
    ----------
    prompt : str
        Brugerens input.
    history : List[(user, assistant)] | None
        Tidligere kontekst som vil blive indføjet i prompten.
    """
    if _model is None or _tokenizer is None:
        raise RuntimeError("LLM ikke indlæst. Kald load_model() først.")

    # Byg samtale-prompt
    messages: List[str] = []
    if history:
        for (user_msg, assistant_msg) in history[-5:]:  # begræns længde
            messages.append(f"Bruger: {user_msg}\nAssistent: {assistant_msg}")
    messages.append(f"Bruger: {prompt}\nAssistent:")
    full_prompt = "\n".join(messages)

    inputs = _tokenizer(full_prompt, return_tensors="pt").to(_device)
    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            pad_token_id=_tokenizer.eos_token_id,
        )
    generated = _tokenizer.decode(output_ids[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated.strip() 
"""
Module 3: Local LLM Engine
Loads google/gemma-4-E4B-it in bfloat16 with Flash Attention 2
and exposes it as a LangChain-compatible HuggingFacePipeline.
"""

import logging
from functools import lru_cache

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.language_models import BaseLLM

from config import (
    LLM_MODEL_ID,
    MAX_NEW_TOKENS as CONFIG_MAX_NEW_TOKENS,
    TEMPERATURE as CONFIG_TEMPERATURE,
    REPETITION_PENALTY as CONFIG_REPETITION_PENALTY,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_ID        = LLM_MODEL_ID
DO_SAMPLE       = True
TEMPERATURE     = CONFIG_TEMPERATURE
MAX_NEW_TOKENS  = CONFIG_MAX_NEW_TOKENS
REPETITION_PENALTY = CONFIG_REPETITION_PENALTY


# ---------------------------------------------------------------------------
# Model loader (cached so it is only loaded once per process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_pipeline() -> pipeline:
    """
    Load tokenizer + model and return a HuggingFace text-generation pipeline.
    Cached with lru_cache — subsequent calls return the same pipeline object.
    """
    if not torch.cuda.is_available():
        raise EnvironmentError(
            "CUDA is not available. This system requires an NVIDIA GPU (H100) to run "
            f"{MODEL_ID} in bfloat16."
        )

    logger.info(f"Loading tokenizer: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    logger.info(f"Loading model: {MODEL_ID} (bfloat16, Flash Attention 2, device_map=auto)")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    model.eval()

    logger.info("Building text-generation pipeline...")
    gen_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        do_sample=DO_SAMPLE,
        repetition_penalty=REPETITION_PENALTY,
        return_full_text=False,     # return only the generated portion, not the prompt
    )

    logger.info("LLM pipeline ready.")
    return gen_pipeline


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_llm() -> BaseLLM:
    """
    Return a LangChain-compatible HuggingFacePipeline wrapping Gemma-4.
    This is the primary entry point used by agent.py and other modules.
    """
    hf_pipeline = _load_pipeline()
    return HuggingFacePipeline(pipeline=hf_pipeline)


def get_raw_pipeline() -> pipeline:
    """
    Return the raw HuggingFace pipeline directly.
    Useful when you need fine-grained control over generation parameters
    outside of LangChain (e.g., streaming tokens manually).
    """
    return _load_pipeline()


def generate(prompt: str) -> str:
    """
    Convenience wrapper: run a single prompt through the model and return
    the generated text as a plain string.
    """
    gen_pipeline = _load_pipeline()
    outputs = gen_pipeline(prompt)
    return outputs[0]["generated_text"].strip()


# ---------------------------------------------------------------------------
# VRAM diagnostics
# ---------------------------------------------------------------------------

def print_vram_usage() -> None:
    """Log current VRAM allocation across all visible GPUs."""
    if not torch.cuda.is_available():
        logger.warning("No CUDA device found.")
        return
    for i in range(torch.cuda.device_count()):
        allocated = torch.cuda.memory_allocated(i) / 1e9
        reserved  = torch.cuda.memory_reserved(i) / 1e9
        total     = torch.cuda.get_device_properties(i).total_memory / 1e9
        logger.info(
            f"GPU {i} ({torch.cuda.get_device_name(i)}): "
            f"{allocated:.2f}GB allocated / {reserved:.2f}GB reserved / {total:.2f}GB total"
        )


# ---------------------------------------------------------------------------
# Entry point (smoke test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_vram_usage()

    TEST_PROMPT = (
        "You are a senior quantitative analyst. "
        "What is the Debt-to-Equity ratio if total debt is $50B and total equity is $25B? "
        "Show your reasoning."
    )

    print(f"\nPrompt:\n{TEST_PROMPT}\n")
    response = generate(TEST_PROMPT)
    print(f"Response:\n{response}")

    print()
    print_vram_usage()

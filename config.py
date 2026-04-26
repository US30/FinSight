"""
Central configuration loader.
Reads environment variables (from .env or shell) and exposes
typed constants used across all modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (no-op if missing)
load_dotenv()

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
SEC_DATA_PATH       = Path(os.getenv("SEC_DATA_PATH", "./data/SEC_Filings_Data"))
CHECKPOINT_FILE     = Path(os.getenv("CHECKPOINT_FILE", "./ingestion_checkpoint.json"))

# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------
QDRANT_PATH         = os.getenv("QDRANT_PATH", "./qdrant_db")
QDRANT_COLLECTION   = os.getenv("QDRANT_COLLECTION", "sec_filings")

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
LLM_MODEL_ID        = os.getenv("LLM_MODEL_ID", "google/gemma-4-E4B-it")
EMBEDDING_MODEL_ID  = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-large-en-v1.5")
EMBEDDING_DIM       = int(os.getenv("EMBEDDING_DIM", "1024"))

# ---------------------------------------------------------------------------
# LLM generation
# ---------------------------------------------------------------------------
MAX_NEW_TOKENS      = int(os.getenv("MAX_NEW_TOKENS", "1024"))
TEMPERATURE         = float(os.getenv("TEMPERATURE", "0.1"))
REPETITION_PENALTY  = float(os.getenv("REPETITION_PENALTY", "1.1"))

# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
CHUNK_SIZE          = int(os.getenv("CHUNK_SIZE", "2000"))
CHUNK_OVERLAP       = int(os.getenv("CHUNK_OVERLAP", "200"))
EMBEDDING_BATCH     = int(os.getenv("EMBEDDING_BATCH", "64"))

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
AGENT_STATE_DB      = os.getenv("AGENT_STATE_DB", "./agent_state.db")
AGENT_LOGS_DB       = os.getenv("AGENT_LOGS_DB", "./agent_logs.db")
TOP_K               = int(os.getenv("TOP_K", "8"))
MAX_RETRIES         = int(os.getenv("MAX_RETRIES", "2"))

# ---------------------------------------------------------------------------
# Sanity check (called on import in strict mode)
# ---------------------------------------------------------------------------

def validate() -> None:
    """Raise if critical paths or settings are misconfigured."""
    if not SEC_DATA_PATH.exists():
        raise FileNotFoundError(
            f"SEC_DATA_PATH not found: {SEC_DATA_PATH}\n"
            "Set the SEC_DATA_PATH environment variable in your .env file."
        )
    if EMBEDDING_DIM != 1024:
        raise ValueError(
            f"EMBEDDING_DIM should be 1024 for BAAI/bge-large-en-v1.5, got {EMBEDDING_DIM}."
        )


if __name__ == "__main__":
    print("=== FinSight Configuration ===")
    print(f"  SEC_DATA_PATH      : {SEC_DATA_PATH}")
    print(f"  QDRANT_PATH        : {QDRANT_PATH}")
    print(f"  QDRANT_COLLECTION  : {QDRANT_COLLECTION}")
    print(f"  LLM_MODEL_ID       : {LLM_MODEL_ID}")
    print(f"  EMBEDDING_MODEL_ID : {EMBEDDING_MODEL_ID}")
    print(f"  AGENT_STATE_DB     : {AGENT_STATE_DB}")
    print(f"  AGENT_LOGS_DB      : {AGENT_LOGS_DB}")
    print(f"  TOP_K              : {TOP_K}")
    print(f"  MAX_RETRIES        : {MAX_RETRIES}")

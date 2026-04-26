"""
Module 1: Document Ingestion & Parsing
Parses SEC 10-K/10-Q HTML/PDF filings, separates text from tables,
and chunks data semantically into LangChain Document objects.
"""

import os
import json
import logging
from pathlib import Path
from typing import List

from markdownify import markdownify as md
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SEC_DATA_PATH = Path(os.getenv("SEC_DATA_PATH", "./data/SEC_Filings_Data"))
CHECKPOINT_FILE = Path("./ingestion_checkpoint.json")
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", " ", ""],
)

# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint: dict) -> None:
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _infer_metadata(file_path: Path) -> dict:
    """
    Infer metadata from directory structure.
    Expected layout: SEC_Filings_Data/<TICKER>/<FILING_TYPE>/<YEAR>/<file>
    e.g. SEC_Filings_Data/AAPL/10-K/2023/filing.html
    Falls back to 'UNKNOWN' for any missing level.
    """
    parts = file_path.parts
    data_parts = list(SEC_DATA_PATH.parts)
    relative = parts[len(data_parts):]

    ticker      = relative[0] if len(relative) > 0 else "UNKNOWN"
    filing_type = relative[1] if len(relative) > 1 else "UNKNOWN"
    year_str    = relative[2] if len(relative) > 2 else "0"

    try:
        year = int(year_str)
    except ValueError:
        year = 0

    return {
        "company_ticker": ticker.upper(),
        "filing_type":    filing_type.upper(),
        "year":           year,
        "source_file":    str(file_path.resolve()),
    }


def _partition_file(file_path: Path) -> list:
    """Dispatch to the correct unstructured partition function by extension."""
    suffix = file_path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return partition_html(filename=str(file_path))
    elif suffix == ".pdf":
        return partition_pdf(filename=str(file_path))
    else:
        logger.warning(f"Unsupported file type: {file_path} — skipping.")
        return []


def _elements_to_documents(elements: list, base_metadata: dict) -> List[Document]:
    """
    Convert unstructured elements into LangChain Documents.
    - Table elements  → single atomic Document (not split)
    - Text elements   → collected and split with RecursiveCharacterTextSplitter
    """
    documents: List[Document] = []
    text_buffer: List[str] = []
    section_tracker = "Unknown"

    for element in elements:
        category = getattr(element, "category", "NarrativeText")
        text = str(element).strip()

        if not text:
            continue

        # Track section headings for metadata
        if category == "Title":
            section_tracker = text[:120]

        if category == "Table":
            # --- Atomic table chunk ---
            raw_html = getattr(element.metadata, "text_as_html", None)
            table_md = md(raw_html) if raw_html else text

            documents.append(Document(
                page_content=table_md,
                metadata={
                    **base_metadata,
                    "chunk_type": "table",
                    "section":    section_tracker,
                },
            ))
        else:
            # Accumulate narrative text
            text_buffer.append(text)

    # --- Split accumulated text chunks ---
    if text_buffer:
        combined_text = "\n\n".join(text_buffer)
        splits = TEXT_SPLITTER.split_text(combined_text)
        for split in splits:
            documents.append(Document(
                page_content=split,
                metadata={
                    **base_metadata,
                    "chunk_type": "text",
                    "section":    section_tracker,
                },
            ))

    return documents


# ---------------------------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------------------------

def ingest_filings() -> List[Document]:
    """
    Iterate through all SEC filing files under SEC_DATA_PATH,
    parse them, and return a list of LangChain Documents.
    Skips files already recorded in the checkpoint.
    """
    if not SEC_DATA_PATH.exists():
        raise FileNotFoundError(
            f"SEC_DATA_PATH does not exist: {SEC_DATA_PATH}. "
            "Set the SEC_DATA_PATH environment variable to the correct path."
        )

    checkpoint = load_checkpoint()
    all_documents: List[Document] = []
    supported_extensions = {".html", ".htm", ".pdf"}

    files = [
        f for f in SEC_DATA_PATH.rglob("*")
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    logger.info(f"Found {len(files)} files under {SEC_DATA_PATH}.")

    for file_path in files:
        file_key = str(file_path.resolve())

        if checkpoint.get(file_key, {}).get("processed"):
            logger.debug(f"Skipping (already processed): {file_path.name}")
            continue

        logger.info(f"Processing: {file_path}")
        try:
            elements = _partition_file(file_path)
            base_metadata = _infer_metadata(file_path)
            docs = _elements_to_documents(elements, base_metadata)
            all_documents.extend(docs)

            checkpoint[file_key] = {"processed": True, "doc_count": len(docs)}
            save_checkpoint(checkpoint)
            logger.info(f"  -> {len(docs)} chunks produced.")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            checkpoint[file_key] = {"processed": False, "error": str(e)}
            save_checkpoint(checkpoint)

    logger.info(f"Ingestion complete. Total chunks: {len(all_documents)}")
    return all_documents


if __name__ == "__main__":
    docs = ingest_filings()
    print(f"\nTotal documents produced: {len(docs)}")
    if docs:
        print("\nSample document:")
        print(f"  chunk_type : {docs[0].metadata['chunk_type']}")
        print(f"  ticker     : {docs[0].metadata['company_ticker']}")
        print(f"  year       : {docs[0].metadata['year']}")
        print(f"  content[:200]: {docs[0].page_content[:200]}")

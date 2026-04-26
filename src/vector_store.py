"""
Module 2: Vector Database Initialization
Embeds parsed LangChain Documents using BGE-large and stores them
in a local Qdrant instance with metadata filtering support.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
QDRANT_PATH         = os.getenv("QDRANT_PATH", "./qdrant_db")
COLLECTION_NAME     = os.getenv("QDRANT_COLLECTION", "sec_filings")
EMBEDDING_MODEL     = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM       = 1024          # bge-large-en-v1.5 output dimension
BATCH_SIZE          = 64            # documents per embedding batch


# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

def get_embeddings() -> HuggingFaceEmbeddings:
    """Load BGE-large onto CUDA with cosine-similarity normalization."""
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},  # required for BGE cosine similarity
    )


# ---------------------------------------------------------------------------
# Qdrant client & collection
# ---------------------------------------------------------------------------

def get_qdrant_client() -> QdrantClient:
    """Initialize a local persistent Qdrant client."""
    Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)
    logger.info(f"Connecting to local Qdrant at: {QDRANT_PATH}")
    return QdrantClient(path=QDRANT_PATH)


def ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it does not already exist."""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        logger.info(f"Creating collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM}, cosine).")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
    else:
        logger.info(f"Collection '{COLLECTION_NAME}' already exists — skipping creation.")


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def index_documents(documents: List[Document]) -> QdrantVectorStore:
    """
    Embed and upsert documents into Qdrant in batches.
    Returns a QdrantVectorStore ready for retrieval.
    """
    embeddings = get_embeddings()
    client     = get_qdrant_client()
    ensure_collection(client)

    logger.info(f"Indexing {len(documents)} documents in batches of {BATCH_SIZE}...")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        vector_store.add_documents(batch)
        logger.info(f"  Indexed batch {i // BATCH_SIZE + 1} / {-(-len(documents) // BATCH_SIZE)}")

    logger.info("Indexing complete.")
    return vector_store


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def load_vector_store() -> QdrantVectorStore:
    """
    Load an existing Qdrant collection as a LangChain vector store.
    Call this after indexing is complete, e.g. from agent.py.
    """
    embeddings = get_embeddings()
    client     = get_qdrant_client()
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )


def similarity_search(
    query: str,
    vector_store: QdrantVectorStore,
    k: int = 8,
    filter_ticker: Optional[str] = None,
    filter_filing_type: Optional[str] = None,
    filter_year: Optional[int] = None,
    prefer_tables: bool = False,
) -> List[Document]:
    """
    Retrieve top-k documents with optional metadata filtering.

    Args:
        query:              Natural language search query.
        vector_store:       Loaded QdrantVectorStore instance.
        k:                  Number of results to return.
        filter_ticker:      Restrict to a specific company ticker (e.g. "AAPL").
        filter_filing_type: Restrict to "10-K" or "10-Q".
        filter_year:        Restrict to a specific filing year.
        prefer_tables:      If True, fetch extra results and surface tables first.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

    conditions = []

    if filter_ticker:
        conditions.append(
            FieldCondition(key="metadata.company_ticker", match=MatchValue(value=filter_ticker.upper()))
        )
    if filter_filing_type:
        conditions.append(
            FieldCondition(key="metadata.filing_type", match=MatchValue(value=filter_filing_type.upper()))
        )
    if filter_year:
        conditions.append(
            FieldCondition(key="metadata.year", match=MatchValue(value=filter_year))
        )

    qdrant_filter = Filter(must=conditions) if conditions else None
    fetch_k = k * 2 if prefer_tables else k

    results = vector_store.similarity_search(
        query=query,
        k=fetch_k,
        filter=qdrant_filter,
    )

    if prefer_tables:
        tables = [d for d in results if d.metadata.get("chunk_type") == "table"]
        texts  = [d for d in results if d.metadata.get("chunk_type") != "table"]
        results = (tables + texts)[:k]

    return results


# ---------------------------------------------------------------------------
# Entry point (standalone indexing run)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ingestion import ingest_filings

    docs = ingest_filings()
    if not docs:
        print("No documents produced by ingestion. Exiting.")
    else:
        vs = index_documents(docs)
        print(f"\nIndexed {len(docs)} documents into collection '{COLLECTION_NAME}'.")

        # Quick smoke test
        results = similarity_search("total revenue", vs, k=3)
        print(f"\nSmoke test — top 3 results for 'total revenue':")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r.metadata.get('company_ticker')} "
                  f"{r.metadata.get('filing_type')} {r.metadata.get('year')} "
                  f"({r.metadata.get('chunk_type')}) — {r.page_content[:120]}")

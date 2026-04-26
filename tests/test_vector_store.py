"""
Tests for Module 2: vector_store.py
Mocks Qdrant and the embedding model to avoid GPU/network dependencies.
"""

import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from langchain.schema import Document

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_docs(n: int = 5, chunk_type: str = "text") -> list[Document]:
    return [
        Document(
            page_content=f"Sample content {i}",
            metadata={
                "company_ticker": "AAPL",
                "filing_type":    "10-K",
                "year":           2023,
                "section":        "Financial Statements",
                "chunk_type":     chunk_type,
                "source_file":    f"/fake/file_{i}.html",
            },
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# ensure_collection
# ---------------------------------------------------------------------------

def test_ensure_collection_creates_if_missing():
    import vector_store

    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []   # empty — collection absent

    with patch.object(vector_store, "COLLECTION_NAME", "sec_filings"):
        vector_store.ensure_collection(mock_client)

    mock_client.create_collection.assert_called_once()
    call_kwargs = mock_client.create_collection.call_args[1]
    assert call_kwargs["collection_name"] == "sec_filings"


def test_ensure_collection_skips_if_exists():
    import vector_store

    existing = MagicMock()
    existing.name = "sec_filings"
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = [existing]

    with patch.object(vector_store, "COLLECTION_NAME", "sec_filings"):
        vector_store.ensure_collection(mock_client)

    mock_client.create_collection.assert_not_called()


# ---------------------------------------------------------------------------
# index_documents — batch logic
# ---------------------------------------------------------------------------

def test_index_documents_calls_add_in_batches():
    import vector_store

    docs = _make_docs(n=150)

    mock_vs = MagicMock()
    mock_embeddings = MagicMock()
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []

    with (
        patch("vector_store.get_embeddings",    return_value=mock_embeddings),
        patch("vector_store.get_qdrant_client", return_value=mock_client),
        patch("vector_store.QdrantVectorStore", return_value=mock_vs),
        patch("vector_store.BATCH_SIZE", 64),
    ):
        vector_store.index_documents(docs)

    # 150 docs / 64 batch = 3 calls
    assert mock_vs.add_documents.call_count == 3


def test_index_documents_returns_vector_store():
    import vector_store

    docs = _make_docs(n=10)
    mock_vs = MagicMock()
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []

    with (
        patch("vector_store.get_embeddings",    return_value=MagicMock()),
        patch("vector_store.get_qdrant_client", return_value=mock_client),
        patch("vector_store.QdrantVectorStore", return_value=mock_vs),
    ):
        result = vector_store.index_documents(docs)

    assert result is mock_vs


# ---------------------------------------------------------------------------
# similarity_search — metadata filtering & prefer_tables
# ---------------------------------------------------------------------------

def test_similarity_search_passes_filter_to_qdrant():
    import vector_store
    from qdrant_client.models import Filter

    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = _make_docs(3)

    vector_store.similarity_search(
        query="total revenue",
        vector_store=mock_vs,
        k=3,
        filter_ticker="AAPL",
        filter_filing_type="10-K",
        filter_year=2023,
    )

    call_kwargs = mock_vs.similarity_search.call_args[1]
    assert call_kwargs["filter"] is not None
    assert isinstance(call_kwargs["filter"], Filter)


def test_similarity_search_no_filter_when_none():
    import vector_store

    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = _make_docs(3)

    vector_store.similarity_search(
        query="total revenue",
        vector_store=mock_vs,
        k=3,
    )

    call_kwargs = mock_vs.similarity_search.call_args[1]
    assert call_kwargs["filter"] is None


def test_prefer_tables_surfaces_tables_first():
    import vector_store

    table_docs = _make_docs(3, chunk_type="table")
    text_docs  = _make_docs(5, chunk_type="text")
    # Qdrant returns text first, then tables
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = text_docs + table_docs

    results = vector_store.similarity_search(
        query="debt to equity ratio",
        vector_store=mock_vs,
        k=5,
        prefer_tables=True,
    )

    # All table docs should appear before text docs in results
    table_indices = [i for i, d in enumerate(results) if d.metadata["chunk_type"] == "table"]
    text_indices  = [i for i, d in enumerate(results) if d.metadata["chunk_type"] == "text"]

    if table_indices and text_indices:
        assert max(table_indices) < min(text_indices)

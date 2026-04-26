"""
Tests for Module 1: ingestion.py
Uses temporary directories and mock files to avoid touching real SEC data.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_sec_dir(tmp_path):
    """
    Build a minimal fake SEC filing directory structure:
    tmp/AAPL/10-K/2023/filing.html
    tmp/JPM/10-Q/2022/filing.html
    """
    for ticker, ftype, year, filename in [
        ("AAPL", "10-K", "2023", "filing.html"),
        ("JPM",  "10-Q", "2022", "filing.html"),
    ]:
        p = tmp_path / ticker / ftype / year
        p.mkdir(parents=True)
        (p / filename).write_text(
            f"<html><body><h1>{ticker} Annual Report {year}</h1>"
            f"<p>Total revenue was $100 billion.</p>"
            f"<table><tr><td>Revenue</td><td>100B</td></tr></table>"
            f"</body></html>"
        )
    return tmp_path


@pytest.fixture
def checkpoint_file(tmp_path):
    return tmp_path / "ingestion_checkpoint.json"


# ---------------------------------------------------------------------------
# _infer_metadata
# ---------------------------------------------------------------------------

def test_infer_metadata_happy_path(tmp_sec_dir, monkeypatch):
    import ingestion
    monkeypatch.setattr(ingestion, "SEC_DATA_PATH", tmp_sec_dir)

    file_path = tmp_sec_dir / "AAPL" / "10-K" / "2023" / "filing.html"
    meta = ingestion._infer_metadata(file_path)

    assert meta["company_ticker"] == "AAPL"
    assert meta["filing_type"]    == "10-K"
    assert meta["year"]           == 2023
    assert "source_file" in meta


def test_infer_metadata_missing_levels(tmp_sec_dir, monkeypatch):
    """Files not matching the expected depth should fall back to UNKNOWN / 0."""
    import ingestion
    monkeypatch.setattr(ingestion, "SEC_DATA_PATH", tmp_sec_dir)

    shallow_file = tmp_sec_dir / "orphan.html"
    shallow_file.write_text("<html></html>")
    meta = ingestion._infer_metadata(shallow_file)

    assert meta["company_ticker"] == "UNKNOWN"
    assert meta["year"]           == 0


# ---------------------------------------------------------------------------
# _elements_to_documents — table handling
# ---------------------------------------------------------------------------

def test_table_kept_as_atomic_chunk():
    """Table elements must NOT be split — each becomes exactly one Document."""
    import ingestion

    # Build mock unstructured elements
    table_el = MagicMock()
    table_el.category = "Table"
    table_el.__str__ = lambda self: "Revenue | 100B\nNet Income | 20B"
    table_el.metadata.text_as_html = "<table><tr><td>Revenue</td><td>100B</td></tr></table>"

    base_meta = {
        "company_ticker": "AAPL",
        "filing_type":    "10-K",
        "year":           2023,
        "source_file":    "/fake/path.html",
    }

    docs = ingestion._elements_to_documents([table_el], base_meta)

    assert len(docs) == 1
    assert docs[0].metadata["chunk_type"] == "table"
    # Markdown conversion should have run
    assert "Revenue" in docs[0].page_content


def test_text_is_split():
    """Long narrative text must be chunked by RecursiveCharacterTextSplitter."""
    import ingestion

    long_text = "word " * 1000   # ~5000 chars, exceeds chunk_size=2000
    text_el = MagicMock()
    text_el.category = "NarrativeText"
    text_el.__str__ = lambda self: long_text
    text_el.metadata.text_as_html = None

    base_meta = {
        "company_ticker": "MSFT",
        "filing_type":    "10-K",
        "year":           2023,
        "source_file":    "/fake/path.html",
    }

    docs = ingestion._elements_to_documents([text_el], base_meta)

    assert len(docs) > 1
    for doc in docs:
        assert doc.metadata["chunk_type"] == "text"
        assert len(doc.page_content) <= ingestion.CHUNK_SIZE + ingestion.CHUNK_OVERLAP


def test_mixed_elements_produce_both_chunk_types():
    """A mix of table + text elements should produce both chunk_type values."""
    import ingestion

    table_el = MagicMock()
    table_el.category = "Table"
    table_el.__str__ = lambda self: "Revenue | 100B"
    table_el.metadata.text_as_html = "<table><tr><td>Revenue</td><td>100B</td></tr></table>"

    text_el = MagicMock()
    text_el.category = "NarrativeText"
    text_el.__str__ = lambda self: "This is a risk factor section with some text."
    text_el.metadata.text_as_html = None

    base_meta = {"company_ticker": "AAPL", "filing_type": "10-K", "year": 2023, "source_file": "/f"}
    docs = ingestion._elements_to_documents([table_el, text_el], base_meta)

    chunk_types = {d.metadata["chunk_type"] for d in docs}
    assert "table" in chunk_types
    assert "text"  in chunk_types


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def test_checkpoint_skip_processed_files(tmp_sec_dir, monkeypatch, tmp_path):
    """Files already in checkpoint with processed=True must be skipped."""
    import ingestion

    monkeypatch.setattr(ingestion, "SEC_DATA_PATH", tmp_sec_dir)
    monkeypatch.setattr(ingestion, "CHECKPOINT_FILE", tmp_path / "checkpoint.json")

    # Pre-populate checkpoint for all files
    all_files = list(tmp_sec_dir.rglob("*.html"))
    checkpoint_data = {str(f.resolve()): {"processed": True} for f in all_files}
    (tmp_path / "checkpoint.json").write_text(json.dumps(checkpoint_data))

    with patch("ingestion._partition_file") as mock_partition:
        docs = ingestion.ingest_filings()
        mock_partition.assert_not_called()

    assert docs == []


def test_checkpoint_written_after_processing(tmp_sec_dir, monkeypatch, tmp_path):
    """After processing a file, checkpoint must mark it as processed=True."""
    import ingestion

    monkeypatch.setattr(ingestion, "SEC_DATA_PATH", tmp_sec_dir)
    cp_path = tmp_path / "checkpoint.json"
    monkeypatch.setattr(ingestion, "CHECKPOINT_FILE", cp_path)

    mock_element = MagicMock()
    mock_element.category = "NarrativeText"
    mock_element.__str__ = lambda self: "Some text"
    mock_element.metadata.text_as_html = None

    with patch("ingestion._partition_file", return_value=[mock_element]):
        ingestion.ingest_filings()

    checkpoint = json.loads(cp_path.read_text())
    processed_flags = [v["processed"] for v in checkpoint.values()]
    assert all(processed_flags)


# ---------------------------------------------------------------------------
# Missing SEC_DATA_PATH
# ---------------------------------------------------------------------------

def test_missing_data_path_raises(monkeypatch, tmp_path):
    import ingestion
    monkeypatch.setattr(ingestion, "SEC_DATA_PATH", tmp_path / "nonexistent")

    with pytest.raises(FileNotFoundError, match="SEC_DATA_PATH"):
        ingestion.ingest_filings()

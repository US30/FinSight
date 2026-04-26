"""
pytest configuration — adds src/ to sys.path so all test files
can import ingestion, vector_store, agent, etc. without installing the package.
"""

import sys
import os

# Insert src/ at the front of the path once for the entire test session
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

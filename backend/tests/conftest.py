import sys
import os
from unittest.mock import MagicMock
import pytest

# Add the backend directory to sys.path so imports resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_config():
    """Minimal config object for unit tests."""
    cfg = MagicMock()
    cfg.CHUNK_SIZE = 500
    cfg.CHUNK_OVERLAP = 50
    cfg.CHROMA_PATH = "/tmp/chroma"
    cfg.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    cfg.MAX_RESULTS = 5
    cfg.ANTHROPIC_API_KEY = "test-key"
    cfg.ANTHROPIC_MODEL = "claude-test"
    cfg.MAX_HISTORY = 2
    return cfg


@pytest.fixture
def mock_rag():
    """
    A MagicMock standing in for the RAGSystem.

    Default return values match the shapes expected by app.py so that
    API tests can rely on sane defaults and only override what they care about.
    """
    rag = MagicMock()
    rag.query.return_value = ("Test answer", [])
    rag.get_course_analytics.return_value = {
        "total_courses": 0,
        "course_titles": [],
    }
    rag.session_manager.create_session.return_value = "test-session-id"
    return rag

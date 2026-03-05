"""
API endpoint tests for the FastAPI application.

app.py has two module-level side effects that break imports in the test environment:
  1. RAGSystem(config) — instantiates ChromaDB, sentence-transformers, etc.
  2. StaticFiles(directory="../frontend") — requires the frontend build directory.

We use contextlib.ExitStack to apply the necessary patches *before* app is
imported (so the module-level code runs against mocks), then close the patches
immediately afterward.  The resulting module-level `rag_system` object is a real
RAGSystem with mocked internals; each test replaces it entirely via monkeypatch.
"""

import contextlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Patch heavy components before importing app
# ---------------------------------------------------------------------------
_startup_patches = contextlib.ExitStack()
_startup_patches.enter_context(patch("rag_system.DocumentProcessor"))
_startup_patches.enter_context(patch("rag_system.VectorStore"))
_startup_patches.enter_context(patch("rag_system.AIGenerator"))
_startup_patches.enter_context(patch("rag_system.SessionManager"))
# Prevent StaticFiles from requiring the ../frontend directory at import time
_startup_patches.enter_context(patch("fastapi.staticfiles.StaticFiles"))

import app as app_module  # noqa: E402 — must come after patches are started

_startup_patches.close()

fastapi_app = app_module.app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(mock_rag, monkeypatch):
    """TestClient with rag_system replaced by the shared mock_rag fixture."""
    monkeypatch.setattr(app_module, "rag_system", mock_rag)
    with TestClient(fastapi_app, raise_server_exceptions=False) as tc:
        yield tc


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------


def test_query_returns_200_with_answer_and_sources(client, mock_rag):
    mock_rag.query.return_value = (
        "RAG stands for Retrieval-Augmented Generation.",
        [{"label": "MCP Course - Lesson 1", "link": "https://example.com"}],
    )
    mock_rag.session_manager.create_session.return_value = "sess-abc"

    resp = client.post(
        "/api/query",
        json={"query": "What is RAG?", "session_id": "sess-abc"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "RAG stands for Retrieval-Augmented Generation."
    assert body["session_id"] == "sess-abc"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["label"] == "MCP Course - Lesson 1"
    assert body["sources"][0]["link"] == "https://example.com"


def test_query_creates_session_when_none_provided(client, mock_rag):
    mock_rag.query.return_value = ("Answer", [])
    mock_rag.session_manager.create_session.return_value = "auto-sess"

    resp = client.post("/api/query", json={"query": "hello"})

    assert resp.status_code == 200
    assert resp.json()["session_id"] == "auto-sess"
    mock_rag.session_manager.create_session.assert_called_once()


def test_query_uses_provided_session_without_creating_new_one(client, mock_rag):
    mock_rag.query.return_value = ("Answer", [])

    resp = client.post(
        "/api/query", json={"query": "follow-up", "session_id": "existing-sess"}
    )

    assert resp.status_code == 200
    assert resp.json()["session_id"] == "existing-sess"
    mock_rag.session_manager.create_session.assert_not_called()


def test_query_forwards_query_and_session_to_rag(client, mock_rag):
    mock_rag.query.return_value = ("Answer", [])

    client.post("/api/query", json={"query": "explain MCP", "session_id": "s1"})

    mock_rag.query.assert_called_once_with("explain MCP", "s1")


def test_query_missing_query_field_returns_422(client):
    resp = client.post("/api/query", json={"session_id": "s1"})
    assert resp.status_code == 422


def test_query_rag_error_returns_500(client, mock_rag):
    mock_rag.query.side_effect = RuntimeError("upstream failure")

    resp = client.post("/api/query", json={"query": "anything"})

    assert resp.status_code == 500
    assert "upstream failure" in resp.json()["detail"]


def test_query_sources_without_link(client, mock_rag):
    mock_rag.query.return_value = (
        "Answer",
        [{"label": "Course A - Lesson 3", "link": None}],
    )
    mock_rag.session_manager.create_session.return_value = "s"

    resp = client.post("/api/query", json={"query": "q"})

    source = resp.json()["sources"][0]
    assert source["label"] == "Course A - Lesson 3"
    assert source["link"] is None


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------


def test_courses_returns_stats(client, mock_rag):
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Intro to AI", "Advanced RAG"],
    }

    resp = client.get("/api/courses")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_courses"] == 2
    assert body["course_titles"] == ["Intro to AI", "Advanced RAG"]


def test_courses_empty_catalog(client, mock_rag):
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 0,
        "course_titles": [],
    }

    resp = client.get("/api/courses")

    assert resp.status_code == 200
    assert resp.json() == {"total_courses": 0, "course_titles": []}


def test_courses_error_returns_500(client, mock_rag):
    mock_rag.get_course_analytics.side_effect = RuntimeError("DB unavailable")

    resp = client.get("/api/courses")

    assert resp.status_code == 500
    assert "DB unavailable" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/session/new
# ---------------------------------------------------------------------------


def test_new_session_returns_session_id(client, mock_rag):
    mock_rag.session_manager.create_session.return_value = "brand-new-sess"

    resp = client.post("/api/session/new", json={})

    assert resp.status_code == 200
    assert resp.json()["session_id"] == "brand-new-sess"


def test_new_session_clears_old_session_when_provided(client, mock_rag):
    mock_rag.session_manager.create_session.return_value = "new-sess"

    resp = client.post("/api/session/new", json={"old_session_id": "old-sess"})

    assert resp.status_code == 200
    mock_rag.session_manager.clear_session.assert_called_once_with("old-sess")


def test_new_session_does_not_clear_when_no_old_id(client, mock_rag):
    mock_rag.session_manager.create_session.return_value = "new-sess"

    resp = client.post("/api/session/new", json={})

    assert resp.status_code == 200
    mock_rag.session_manager.clear_session.assert_not_called()

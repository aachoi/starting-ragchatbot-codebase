import pytest
from unittest.mock import MagicMock, patch


def make_rag_system():
    """Build a RAGSystem with all heavy dependencies mocked out."""
    with (
        patch("rag_system.DocumentProcessor"),
        patch("rag_system.VectorStore"),
        patch("rag_system.AIGenerator"),
        patch("rag_system.SessionManager"),
    ):
        from rag_system import RAGSystem

        config = MagicMock()
        config.CHUNK_SIZE = 500
        config.CHUNK_OVERLAP = 50
        config.CHROMA_PATH = "/tmp/chroma"
        config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        config.MAX_RESULTS = 5
        config.ANTHROPIC_API_KEY = "test"
        config.ANTHROPIC_MODEL = "claude-test"
        config.MAX_HISTORY = 2

        rag = RAGSystem(config)

    return rag


def test_query_returns_response_and_sources():
    rag = make_rag_system()
    rag.ai_generator.generate_response.return_value = "Here is the answer"
    rag.tool_manager = MagicMock()
    rag.tool_manager.get_tool_definitions.return_value = []
    rag.tool_manager.get_last_sources.return_value = [{"label": "MCP Course - Lesson 2", "link": None}]

    response, sources = rag.query("What is lesson 2 about?")

    assert response == "Here is the answer"
    assert len(sources) == 1
    assert sources[0]["label"] == "MCP Course - Lesson 2"


def test_content_query_reaches_ai_generator():
    rag = make_rag_system()
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager = MagicMock()
    rag.tool_manager.get_tool_definitions.return_value = [{"name": "search_course_content"}]
    rag.tool_manager.get_last_sources.return_value = []

    rag.query("explain MCP")

    rag.ai_generator.generate_response.assert_called_once()
    call_kwargs = rag.ai_generator.generate_response.call_args[1]
    assert "tools" in call_kwargs
    assert call_kwargs["tools"] == [{"name": "search_course_content"}]


def test_session_history_passed_to_generator():
    rag = make_rag_system()
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager = MagicMock()
    rag.tool_manager.get_tool_definitions.return_value = []
    rag.tool_manager.get_last_sources.return_value = []
    rag.session_manager.get_conversation_history.return_value = "User: hi\nAssistant: hello"

    rag.query("follow-up question", session_id="sess-1")

    rag.session_manager.get_conversation_history.assert_called_once_with("sess-1")
    call_kwargs = rag.ai_generator.generate_response.call_args[1]
    assert call_kwargs["conversation_history"] == "User: hi\nAssistant: hello"


def test_query_exception_propagates():
    rag = make_rag_system()
    rag.ai_generator.generate_response.side_effect = RuntimeError("API down")
    rag.tool_manager = MagicMock()
    rag.tool_manager.get_tool_definitions.return_value = []

    with pytest.raises(RuntimeError, match="API down"):
        rag.query("anything")

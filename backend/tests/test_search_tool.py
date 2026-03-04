from unittest.mock import MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


def make_store(results=None, error=None):
    store = MagicMock()
    if results is None:
        results = SearchResults(documents=[], metadata=[], distances=[])
    if error:
        results.error = error
    store.search.return_value = results
    store.get_lesson_link.return_value = None
    return store


def test_execute_returns_formatted_results():
    results = SearchResults(
        documents=["Lesson content here"],
        metadata=[{"course_title": "MCP Course", "lesson_number": 2}],
        distances=[0.1],
    )
    store = make_store(results=results)
    tool = CourseSearchTool(store)
    output = tool.execute(query="what is MCP")
    assert "MCP Course" in output
    assert "Lesson 2" in output
    assert "Lesson content here" in output


def test_execute_propagates_vector_store_error():
    results = SearchResults(documents=[], metadata=[], distances=[], error="DB connection failed")
    store = make_store(results=results)
    tool = CourseSearchTool(store)
    output = tool.execute(query="anything")
    assert output == "DB connection failed"


def test_execute_empty_results():
    results = SearchResults(documents=[], metadata=[], distances=[])
    store = make_store(results=results)
    tool = CourseSearchTool(store)
    output = tool.execute(query="something obscure")
    assert "No relevant content found" in output


def test_execute_passes_course_filter():
    results = SearchResults(documents=[], metadata=[], distances=[])
    store = make_store(results=results)
    tool = CourseSearchTool(store)
    tool.execute(query="intro", course_name="MCP")
    store.search.assert_called_once_with(query="intro", course_name="MCP", lesson_number=None)


def test_execute_passes_lesson_filter():
    results = SearchResults(documents=[], metadata=[], distances=[])
    store = make_store(results=results)
    tool = CourseSearchTool(store)
    tool.execute(query="intro", lesson_number=3)
    store.search.assert_called_once_with(query="intro", course_name=None, lesson_number=3)

from unittest.mock import MagicMock, patch
from ai_generator import AIGenerator


TOOL_DEFS = [{"name": "search_course_content", "description": "...", "input_schema": {"type": "object", "properties": {}}}]


def make_generator():
    with patch("ai_generator.anthropic.Anthropic"):
        gen = AIGenerator(api_key="test-key", model="claude-test")
    return gen


def _text_response(text, stop_reason="end_turn"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = [block]
    return resp


def _tool_use_response(tool_name="search_course_content", tool_id="tu_1", tool_input=None):
    if tool_input is None:
        tool_input = {"query": "test"}
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = tool_id
    block.input = tool_input
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


def test_no_tool_use_returns_text():
    gen = make_generator()
    gen.client.messages.create.return_value = _text_response("Hello world")
    result = gen.generate_response(query="What is RAG?")
    assert result == "Hello world"


def test_tool_use_calls_tool_manager():
    gen = make_generator()
    tool_resp = _tool_use_response(tool_name="search_course_content", tool_input={"query": "mcp basics"})
    final_resp = _text_response("Final answer")
    gen.client.messages.create.side_effect = [tool_resp, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "search result text"

    gen.generate_response(query="tell me about MCP", tools=TOOL_DEFS, tool_manager=tool_manager)

    tool_manager.execute_tool.assert_called_once_with("search_course_content", query="mcp basics")


def test_final_request_includes_tools():
    """Regression test: follow-up API call must include 'tools' when tool_result blocks are present."""
    gen = make_generator()
    tool_resp = _tool_use_response()
    final_resp = _text_response("Done")
    gen.client.messages.create.side_effect = [tool_resp, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    gen.generate_response(query="query", tools=TOOL_DEFS, tool_manager=tool_manager)

    # The second call (index 1) must have 'tools' in its kwargs
    second_call_kwargs = gen.client.messages.create.call_args_list[1][1]
    assert "tools" in second_call_kwargs, (
        "Bug: follow-up API call is missing 'tools' — Anthropic API requires it when tool_result blocks are present"
    )


def test_final_request_returns_text():
    gen = make_generator()
    tool_resp = _tool_use_response()
    final_resp = _text_response("Final text response")
    gen.client.messages.create.side_effect = [tool_resp, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    result = gen.generate_response(query="query", tools=TOOL_DEFS, tool_manager=tool_manager)
    assert result == "Final text response"


def test_tools_added_to_api_params():
    gen = make_generator()
    gen.client.messages.create.return_value = _text_response("ok")

    gen.generate_response(query="q", tools=TOOL_DEFS)

    call_kwargs = gen.client.messages.create.call_args[1]
    assert "tools" in call_kwargs
    assert call_kwargs.get("tool_choice") == {"type": "auto"}


def test_two_sequential_tool_calls():
    gen = make_generator()
    tool_resp1 = _tool_use_response(tool_id="tu_1", tool_input={"query": "first"})
    tool_resp2 = _tool_use_response(tool_id="tu_2", tool_input={"query": "second"})
    final_resp = _text_response("Final answer")
    gen.client.messages.create.side_effect = [tool_resp1, tool_resp2, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    result = gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    assert tool_manager.execute_tool.call_count == 2
    assert gen.client.messages.create.call_count == 3
    assert result == "Final answer"


def test_second_round_api_call_includes_tools():
    gen = make_generator()
    tool_resp1 = _tool_use_response(tool_id="tu_1")
    tool_resp2 = _tool_use_response(tool_id="tu_2")
    final_resp = _text_response("Done")
    gen.client.messages.create.side_effect = [tool_resp1, tool_resp2, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    calls = gen.client.messages.create.call_args_list
    assert "tools" in calls[1][1], "Second call missing tools"
    assert "tools" in calls[2][1], "Third call missing tools"


def test_messages_accumulate_across_rounds():
    gen = make_generator()
    tool_resp1 = _tool_use_response(tool_id="tu_1", tool_input={"query": "first"})
    tool_resp2 = _tool_use_response(tool_id="tu_2", tool_input={"query": "second"})
    final_resp = _text_response("Done")
    gen.client.messages.create.side_effect = [tool_resp1, tool_resp2, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    third_call_messages = gen.client.messages.create.call_args_list[2][1]["messages"]
    # messages: user, assistant(round1), tool_result(round1), assistant(round2), tool_result(round2)
    assert len(third_call_messages) == 5
    assert third_call_messages[1]["role"] == "assistant"
    assert third_call_messages[2]["role"] == "user"
    tool_result_content = third_call_messages[2]["content"]
    assert any(b["type"] == "tool_result" and b["tool_use_id"] == "tu_1" for b in tool_result_content)


def test_hard_cap_at_two_rounds():
    gen = make_generator()
    # 4 staged responses: tool, tool, tool, text — loop should stop after 2 tool rounds
    gen.client.messages.create.side_effect = [
        _tool_use_response(tool_id="tu_1"),
        _tool_use_response(tool_id="tu_2"),
        _tool_use_response(tool_id="tu_3"),
        _text_response("Never reached"),
    ]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "result"

    gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    assert gen.client.messages.create.call_count == 3


def test_tool_error_does_not_raise():
    gen = make_generator()
    tool_resp = _tool_use_response(tool_id="tu_1")
    final_resp = _text_response("Recovered")
    gen.client.messages.create.side_effect = [tool_resp, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.side_effect = RuntimeError("search failed")

    result = gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    assert isinstance(result, str)


def test_tool_error_passed_to_claude():
    gen = make_generator()
    tool_resp = _tool_use_response(tool_id="tu_err", tool_input={"query": "bad"})
    final_resp = _text_response("Handled")
    gen.client.messages.create.side_effect = [tool_resp, final_resp]

    tool_manager = MagicMock()
    tool_manager.execute_tool.side_effect = RuntimeError("something broke")

    gen.generate_response(query="q", tools=TOOL_DEFS, tool_manager=tool_manager)

    second_call_messages = gen.client.messages.create.call_args_list[1][1]["messages"]
    tool_result_message = second_call_messages[2]
    assert tool_result_message["role"] == "user"
    error_block = tool_result_message["content"][0]
    assert error_block["type"] == "tool_result"
    assert "something broke" in error_block["content"]
    assert error_block.get("is_error") is True

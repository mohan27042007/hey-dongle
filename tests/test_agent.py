import unittest
from unittest.mock import patch
import os
import tempfile
import json
import hey_dongle.agent as agent

class TestAgent(unittest.TestCase):
    def test_1_parse_tool_call_extracts_valid_json(self):
        """_parse_tool_call extracts valid JSON."""
        result = agent._parse_tool_call('{"tool": "read_file", "args": {"path": "main.py"}}')
        self.assertIsNotNone(result)
        self.assertEqual(result["tool"], "read_file")
        self.assertEqual(result["args"]["path"], "main.py")

    def test_2_parse_tool_call_strips_markdown_fences(self):
        """_parse_tool_call strips markdown fences."""
        result = agent._parse_tool_call(
            '```json\n{"tool": "list_directory", "args": {"path": "."}}\n```'
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["tool"], "list_directory")

    def test_3_parse_tool_call_returns_none_for_plain_text(self):
        """_parse_tool_call returns None for plain text."""
        result = agent._parse_tool_call("Here is the answer to your question.")
        self.assertIsNone(result)

    def test_4_execute_tool_routes_read_file_correctly(self):
        """_execute_tool routes read_file correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            tmp_path = f.name
            
        try:
            result = agent._execute_tool("read_file", {"path": tmp_path}, prompt_fn=None)
            self.assertIn("hello", result)
        finally:
            os.unlink(tmp_path)

    def test_5_run_agent_loop_returns_string_when_model_returns_plain_text_immediately(self):
        """run_agent_loop returns string when model returns plain text immediately."""
        with patch("hey_dongle.agent.infer.chat_with_tools",
                   return_value="The answer is 42."):
            result = agent.run_agent_loop(
                user_message="What is 6 times 7?",
                conversation_history=[],
                context_summary="No project loaded.",
                prompt_fn=None,
                status_callback=None
            )
        self.assertEqual(result, "The answer is 42.")

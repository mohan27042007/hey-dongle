"""
Hey Dongle — TUI Tests
Tests for the Textual app shell (Issue #3).
"""

import unittest
from unittest.mock import patch
from hey_dongle.app import HeyDongleApp


class TestApp(unittest.IsolatedAsyncioTestCase):
    """Async tests using Textual's headless run_test() context manager."""

    async def test_1_app_initializes(self):
        with patch("hey_dongle.infer.load_model", return_value=None):
            async with HeyDongleApp().run_test() as pilot:
                pass  # just entering context verifies no crash

    async def test_2_required_widgets_exist(self):
        with patch("hey_dongle.infer.load_model", return_value=None):
            async with HeyDongleApp().run_test() as pilot:
                self.assertIsNotNone(pilot.app.query_one("#output-panel"))
                self.assertIsNotNone(pilot.app.query_one("#input-box"))
                self.assertIsNotNone(pilot.app.query_one("#status-bar"))

    async def test_3_input_submission(self):
        with patch("hey_dongle.infer.load_model", return_value=None):
            with patch("hey_dongle.agent.run_agent_loop", return_value="test response"):
                async with HeyDongleApp().run_test() as pilot:
                    await pilot.press("h", "i")
                    await pilot.press("enter")
                    input_box = pilot.app.query_one("#input-box")
                    self.assertEqual(input_box.value, "")


if __name__ == "__main__":
    unittest.main()

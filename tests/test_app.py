"""
Hey Dongle — TUI Tests
Tests for the Textual app shell (Issue #3).
"""

import unittest
from hey_dongle.app import HeyDongleApp


class TestApp(unittest.IsolatedAsyncioTestCase):
    """Async tests using Textual's headless run_test() context manager."""

    async def test_1_app_initializes(self):
        """App should start and render without raising any exceptions."""
        async with HeyDongleApp().run_test(headless=True) as pilot:
            # If we reach here without an exception, the app started fine.
            self.assertIsNotNone(pilot.app)

    async def test_2_required_widgets_exist(self):
        """All 3 required widget IDs must be present in the DOM."""
        async with HeyDongleApp().run_test(headless=True) as pilot:
            app = pilot.app

            output_panel = app.query_one("#output-panel")
            input_box    = app.query_one("#input-box")
            status_bar   = app.query_one("#status-bar")

            self.assertIsNotNone(output_panel)
            self.assertIsNotNone(input_box)
            self.assertIsNotNone(status_bar)

    async def test_3_input_submission(self):
        """Typing a message and pressing Enter should clear the input."""
        async with HeyDongleApp().run_test(headless=True) as pilot:
            app       = pilot.app
            input_box = app.query_one("#input-box")

            # Focus the input and type a test message
            await pilot.click("#input-box")
            await pilot.press("h", "e", "l", "l", "o")
            self.assertEqual(input_box.value, "hello")

            # Submit with Enter
            await pilot.press("enter")

            # Input value must be cleared after submission
            self.assertEqual(input_box.value, "")


if __name__ == "__main__":
    unittest.main()

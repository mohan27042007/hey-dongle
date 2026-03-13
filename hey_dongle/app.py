"""
Hey Dongle — Main Textual TUI Application
Full terminal UI shell for Hey Dongle.
"""

import time
import urllib.request
from pathlib import Path
from typing import Optional

import config
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Input, RichLog, Static
from textual import work

# ── WELCOME MESSAGE ────────────────────────────────────────────────────────────

WELCOME = """\
[bold #e94560]Hey Dongle 🔌  —  Offline AI Coding Assistant[/]
[#1e2430]────────────────────────────────────────────[/]
[#64748b]Type a message below to get started.
Your project files will be indexed automatically.[/]
"""

# ── STATUS BAR TEMPLATES ───────────────────────────────────────────────────────

STATUS_CHECKING  = "⏳ Checking connection..."
STATUS_OFFLINE   = "⚫ Offline Mode  |  Model: Qwen2.5-Coder 3B  |  Context: 8K  |  Ready"
STATUS_ENHANCED  = "🟢 Enhanced Mode  |  Model: Groq Compound  |  Context: 128K  |  Ready"
STATUS_NO_KEY    = "🟡 Online — No API Key  |  Model: Qwen2.5-Coder 3B  |  Context: 8K  |  Ready"
STATUS_THINKING  = "🔄 Thinking..."


# ── APP ────────────────────────────────────────────────────────────────────────

class HeyDongleApp(App):
    """Hey Dongle — Terminal UI."""

    TITLE        = "Hey Dongle 🔌  v0.1.0"
    CSS_PATH     = Path(__file__).parent / "styles.tcss"
    BINDINGS        = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    _current_status: str = STATUS_CHECKING  # tracks last status bar text

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield RichLog(id="output-panel", markup=True, highlight=False, wrap=True)
        yield Input(
            id="input-box",
            placeholder="Ask Hey Dongle anything about your code...",
        )
        yield Static(STATUS_CHECKING, id="status-bar")

    def on_mount(self) -> None:
        """Called once the DOM is ready and the screen has rendered."""
        # Print the welcome banner
        output = self.query_one("#output-panel", RichLog)
        output.write(WELCOME)

        # Focus the input immediately
        self.query_one("#input-box", Input).focus()

        # Start the non-blocking connectivity check
        self._check_connectivity()

    # ── Connectivity (background thread) ──────────────────────────────────────

    @work(thread=True)
    def _check_connectivity(self) -> None:
        """Ping the connectivity URL in a background thread — never blocks the UI."""
        online = False
        try:
            urllib.request.urlopen(
                config.CONNECTIVITY_CHECK_URL,
                timeout=config.CONNECTIVITY_TIMEOUT,
            )
            online = True
        except Exception:
            online = False

        self.call_from_thread(self._update_status_bar, online)

    def _update_status_bar(self, online: bool) -> None:
        """Update the status bar text from the main thread."""
        if online:
            has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
            text = STATUS_ENHANCED if has_key else STATUS_NO_KEY
        else:
            text = STATUS_OFFLINE

        self._current_status = text  # store so _restore_status can read it
        self.query_one("#status-bar", Static).update(text)

    # ── Input handling ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """User pressed Enter in the input box."""
        message = event.value.strip()
        if not message:
            return

        input_box = self.query_one("#input-box", Input)
        output    = self.query_one("#output-panel", RichLog)

        # Clear the input immediately
        input_box.value = ""

        # Display user message
        output.write(f"\n[bold #e94560]You →[/] {message}")

        # Disable input while responding
        input_box.disabled = True
        input_box.placeholder = "Thinking..."

        # Update status bar
        self.query_one("#status-bar", Static).update(STATUS_THINKING)

        # Stream the placeholder response in a background thread
        self._run_response(message)

    # ── Inference worker (background thread) ───────────────────────────────────

    @work(thread=True)
    def _run_response(self, message: str) -> None:
        """
        Placeholder streaming response — Issue #8 will wire this to infer.py.
        Streams word-by-word without blocking the UI thread.
        """
        placeholder = "Agent loop coming in Issue #8"

        # Accumulate chunks with word-by-word delay, then write at the end
        accumulated = ""
        for word in placeholder.split():
            accumulated += word + " "
            time.sleep(0.06)

        # Write the complete response from the main thread
        self.call_from_thread(self._write_full_response, accumulated.strip())

    def _write_full_response(self, text: str) -> None:
        """Write the complete assistant response to the output panel."""
        output = self.query_one("#output-panel", RichLog)
        output.write(f"\n[bold #10b981]🔌 Hey Dongle[/]  {text}")
        self._finish_response()

    def _finish_response(self) -> None:
        """Re-enable the input box and restore the status bar."""
        input_box = self.query_one("#input-box", Input)
        input_box.disabled = False
        input_box.placeholder = "Ask Hey Dongle anything about your code..."

        # Restore status bar (re-use the last known connectivity state)
        # We trigger another connectivity check to refresh state accurately
        self._restore_status()
        input_box.focus()

    def _restore_status(self) -> None:
        """Restore the status bar to the last known connectivity state."""
        # Read from the stored variable — Static.renderable doesn't exist in Textual 8.x
        text = self._current_status

        # If we're still showing "Thinking...", fall back to offline (connectivity
        # worker will correct it; Issue #13 adds a persistent online-state flag)
        if not text or text == STATUS_THINKING or text == STATUS_CHECKING:
            has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
            text = STATUS_ENHANCED if has_key else STATUS_OFFLINE

        self._current_status = text
        self.query_one("#status-bar", Static).update(text)

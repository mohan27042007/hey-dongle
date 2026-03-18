"""
Hey Dongle — Main Textual TUI Application
Full terminal UI shell for Hey Dongle.
"""

import threading
import urllib.request
from pathlib import Path

import config
import hey_dongle.memory as memory
import hey_dongle.indexer as indexer
import hey_dongle.infer as infer
import hey_dongle.agent as agent
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

STATUS_CHECKING = "⏳ Checking connection..."
STATUS_OFFLINE  = "⚫ Offline Mode  |  Model: Qwen2.5-Coder 3B  |  Context: 8K  |  Ready"
STATUS_ENHANCED = "🟢 Enhanced Mode  |  Model: Groq Compound  |  Context: 128K  |  Ready"
STATUS_NO_KEY   = "🟡 Online — No API Key  |  Model: Qwen2.5-Coder 3B  |  Context: 8K  |  Ready"
STATUS_THINKING = "🔄 Thinking..."


# ── APP ────────────────────────────────────────────────────────────────────────

class HeyDongleApp(App):
    """Hey Dongle — Terminal UI."""

    TITLE    = "Hey Dongle 🔌  v0.1.0"
    CSS_PATH = Path(__file__).parent / "styles.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]

    _current_status: str = STATUS_CHECKING
    _session_id: str = ""
    _index: dict = {}

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
        """Called once the DOM is ready. Returns immediately — all heavy work is in background."""
        output = self.query_one("#output-panel", RichLog)
        output.write(WELCOME)
        self.query_one("#input-box", Input).focus()
        self.query_one("#status-bar", Static).update("⏳ Starting up...")
        self._current_status = "⏳ Starting up..."
        # Launch ALL startup work in a single daemon thread
        threading.Thread(target=self._startup_worker, daemon=True).start()

    # ── Startup worker (background thread) ────────────────────────────────────

    def _startup_worker(self) -> None:
        """
        Runs entirely in a background thread.
        Does NOT call any Textual widget methods directly.
        Uses call_from_thread ONLY to post results back to the main thread.
        """
        try:
            # Step 1 — memory
            memory.init_db(config.DB_PATH)
            last = memory.get_last_session(config.DB_PATH)
            if last:
                self._session_id = last
            else:
                self._session_id = memory.new_session_id()

            # Step 2 — index
            self._index = indexer.build_index(config.PROJECT_DIR)
            file_count = self._index["total_files"]
            lang_count = len(self._index["languages"])
            index_msg = f"[dim]📁 Indexed {file_count} files across {lang_count} languages[/dim]"

            # Step 3 — post index results to UI (one safe call)
            self.call_from_thread(self._on_index_ready, last, index_msg)

            # Step 4 — load model (blocking, CPU-bound)
            infer.load_model()

            # Step 5 — connectivity check
            online = False
            try:
                urllib.request.urlopen(
                    config.CONNECTIVITY_CHECK_URL,
                    timeout=config.CONNECTIVITY_TIMEOUT
                )
                online = True
            except Exception:
                online = False

            # Step 6 — post final status to UI
            self.call_from_thread(self._on_startup_complete, online)

        except Exception as e:
            error_msg = f"❌ Startup failed: {str(e)}"
            self.call_from_thread(self._on_startup_error, error_msg)

    def _on_index_ready(self, last_session: str, index_msg: str) -> None:
        """Called on main thread after indexing completes."""
        output = self.query_one("#output-panel", RichLog)
        output.write(index_msg)
        if last_session:
            self._load_history_into_panel(last_session)
        self.query_one("#status-bar", Static).update("⏳ Loading model...")
        self._current_status = "⏳ Loading model..."

    def _on_startup_complete(self, online: bool) -> None:
        """Called on main thread after model loads and connectivity is checked."""
        has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
        if online and has_key:
            text = STATUS_ENHANCED
        elif online:
            text = STATUS_NO_KEY
        else:
            text = STATUS_OFFLINE
        self._current_status = text
        self.query_one("#status-bar", Static).update(text)

    def _on_startup_error(self, error_msg: str) -> None:
        """Called on main thread if startup fails."""
        self._current_status = error_msg
        self.query_one("#status-bar", Static).update(error_msg)

    def _load_history_into_panel(self, session_id: str) -> None:
        """Must be called from main thread only."""
        messages = memory.load_session(config.DB_PATH, session_id)
        if not messages:
            return
        output = self.query_one("#output-panel", RichLog)
        output.write("[dim]─── Previous session restored ───[/dim]")
        for msg in messages:
            if msg["role"] == "user":
                output.write(f"\n[bold #e94560]You →[/] {msg['content']}")
            else:
                output.write(f"\n[bold #10b981]🔌 Hey Dongle[/]  {msg['content']}")

    # ── Status bar ─────────────────────────────────────────────────────────────

    def _update_status_bar(self, online_or_text, status_text: bool = False) -> None:
        """Update status bar. Must be called from main thread."""
        if status_text:
            text = online_or_text
        elif online_or_text:
            has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
            text = STATUS_ENHANCED if has_key else STATUS_NO_KEY
        else:
            text = STATUS_OFFLINE
        self._current_status = text
        self.query_one("#status-bar", Static).update(text)

    # ── Input handling ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """User pressed Enter in the input box."""
        message = event.value.strip()
        if not message:
            return

        input_box = self.query_one("#input-box", Input)
        output    = self.query_one("#output-panel", RichLog)

        # Handle /clear command
        if message.lower() == "/clear":
            count = memory.clear_session(config.DB_PATH, self._session_id)
            self._session_id = memory.new_session_id()
            output.clear()
            output.write(
                f"[dim]Session cleared ({count} messages deleted). "
                f"New session started.[/dim]"
            )
            input_box.value = ""
            return

        input_box.value = ""
        output.write(f"\n[bold #e94560]You →[/] {message}")
        memory.save_message(config.DB_PATH, self._session_id, "user", message)

        input_box.disabled = True
        input_box.placeholder = "Thinking..."
        self.query_one("#status-bar", Static).update(STATUS_THINKING)

        self._run_response(message)

    # ── Inference worker ───────────────────────────────────────────────────────

    @work(thread=True)
    def _run_response(self, message: str) -> None:
        """Executes the ReAct agent loop in a background thread."""
        history = memory.load_session(config.DB_PATH, self._session_id)
        conv_history = [
            {"role": m["role"], "content": m["content"]}
            for m in history[:-1]
        ]

        context_summary = indexer.get_context_summary(self._index)

        def status_update(text: str):
            self.app.call_from_thread(
                self._update_status_bar, text, True
            )

        response = agent.run_agent_loop(
            user_message=message,
            conversation_history=conv_history,
            context_summary=context_summary,
            prompt_fn=None,
            status_callback=status_update
        )

        self.app.call_from_thread(self._write_full_response, response)

    def _write_full_response(self, text: str) -> None:
        """Write assistant response to panel. Called on main thread."""
        output = self.query_one("#output-panel", RichLog)
        output.write(f"\n[bold #10b981]🔌 Hey Dongle[/]  {text}")
        memory.save_message(config.DB_PATH, self._session_id, "assistant", text)
        self._finish_response()

    def _finish_response(self) -> None:
        """Re-enable input and restore status bar. Called on main thread."""
        input_box = self.query_one("#input-box", Input)
        input_box.disabled = False
        input_box.placeholder = "Ask Hey Dongle anything about your code..."

        text = self._current_status
        if not text or any(x in text for x in ["Thinking", "Starting", "Loading"]):
            has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
            text = STATUS_NO_KEY if config.GROQ_API_KEY else STATUS_OFFLINE
        self._current_status = text
        self.query_one("#status-bar", Static).update(text)
        input_box.focus()
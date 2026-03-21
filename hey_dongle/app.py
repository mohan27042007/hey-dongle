"""
Hey Dongle — Main Textual TUI Application
Clean rewrite — minimal, focused, proven architecture.
"""

import threading
import time
import urllib.request
from pathlib import Path

import config
import hey_dongle.memory as memory
import hey_dongle.indexer as indexer
import hey_dongle.infer as infer
import hey_dongle.agent as agent

from textual.app import App, ComposeResult, on
from textual.binding import Binding
from textual.widgets import Header, Input, RichLog, Static
from textual.message import Message

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

WELCOME = (
    "[bold #e94560]Hey Dongle 🔌  —  Offline AI Coding Assistant[/]\n"
    "[#1e2430]────────────────────────────────────────────[/]\n"
    "[#64748b]Type a message and press Enter to get started.[/]\n"
)

STATUS_ENHANCED = "🟢 Enhanced Mode  |  Model: Groq Compound  |  Context: 128K  |  Ready"
STATUS_THINKING = "🔄 Thinking..."
STATUS_STARTUP  = "⏳ Starting up..."
STATUS_LOADING  = "⏳ Loading model..."

def _get_model_display_name():
    return config.MODEL_FILENAME.split('-instruct')[0]

def _get_status_offline():
    ctx_k = config.N_CTX // 1024
    return f"⚫ Offline Mode  |  Model: {_get_model_display_name()}  |  Context: {ctx_k}K  |  Ready"

def _get_status_no_key():
    ctx_k = config.N_CTX // 1024
    return f"🟡 Online — No API Key  |  Model: {_get_model_display_name()}  |  Context: {ctx_k}K  |  Ready"


# ── CUSTOM MESSAGES (for thread → main thread communication) ──────────────────

class StatusUpdate(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

class AppendOutput(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

class ResponseReady(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

class StartupDone(Message):
    def __init__(self, online: bool, last_session: str, index_msg: str) -> None:
        super().__init__()
        self.online = online
        self.last_session = last_session
        self.index_msg = index_msg


# ── APP ────────────────────────────────────────────────────────────────────────

class HeyDongleApp(App):

    TITLE    = "Hey Dongle 🔌  v0.1.0"
    CSS_PATH = Path(__file__).parent / "styles.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self._session_id: str = ""
        self._index: dict = {}
        self._current_status: str = STATUS_STARTUP
        self._model_ready: bool = False  # True after model loads

    # ── Layout ─────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield RichLog(id="output-panel", markup=True, highlight=False, wrap=True)
        yield Input(id="input-box", placeholder="Ask Hey Dongle anything about your code...")
        yield Static(STATUS_STARTUP, id="status-bar")

    # ── Startup ────────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        # Write welcome message
        self.query_one("#output-panel", RichLog).write(WELCOME)
        # Focus input immediately — this is the ONLY focus call needed
        self.query_one("#input-box", Input).focus()
        # Launch ALL heavy work in background — on_mount returns instantly
        threading.Thread(target=self._startup_worker, daemon=True).start()

    def _startup_worker(self) -> None:
        """Background thread — does ALL blocking work. Never touches widgets directly."""
        try:
            # Memory
            memory.init_db(config.DB_PATH)
            last = memory.get_last_session(config.DB_PATH)
            if last:
                self._session_id = last
            else:
                self._session_id = memory.new_session_id()

            # Index
            self._index = indexer.build_index(config.PROJECT_DIR)
            fc = self._index["total_files"]
            lc = len(self._index["languages"])
            index_msg = f"[dim]📁 Indexed {fc} files across {lc} languages[/dim]"

            # Model — with pulsing indicator
            self.post_message(StatusUpdate(STATUS_LOADING))
            self._loading_pulse = True
            def pulse():
                dots = 1
                while self._loading_pulse:
                    time.sleep(5)
                    if self._loading_pulse:
                        self.post_message(StatusUpdate(f"⏳ Loading model{'.' * dots}"))
                        dots = (dots % 3) + 1
            threading.Thread(target=pulse, daemon=True).start()
            infer.load_model()
            self._loading_pulse = False
            self._model_ready = True

            # Connectivity
            online = False
            try:
                urllib.request.urlopen(
                    config.CONNECTIVITY_CHECK_URL,
                    timeout=config.CONNECTIVITY_TIMEOUT
                )
                online = True
            except Exception:
                online = False

            # Send everything to main thread in one message
            self.post_message(StartupDone(online, last or "", index_msg))

        except Exception as e:
            self.post_message(StatusUpdate(f"❌ Startup failed: {e}"))

    # ── Message handlers (run on main thread) ──────────────────────────────────

    def on_status_update(self, message: StatusUpdate) -> None:
        try:
            self._current_status = message.text
            self.query_one("#status-bar", Static).update(message.text)
        except Exception:
            pass

    def on_startup_done(self, message: StartupDone) -> None:
        try:
            output = self.query_one("#output-panel", RichLog)
            output.write(message.index_msg)

            # Load history if exists
            if message.last_session:
                msgs = memory.load_session(config.DB_PATH, message.last_session)
                if msgs:
                    output.write("[dim]─── Previous session restored ───[/dim]")
                    for msg in msgs:
                        if msg["role"] == "user":
                            output.write(f"\n[bold #e94560]You →[/] {msg['content']}")
                        else:
                            output.write(f"\n[bold #10b981]🔌 Hey Dongle[/]  {msg['content']}")

            # Set status bar
            has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())
            if message.online and has_key:
                status = STATUS_ENHANCED
            elif message.online:
                status = _get_status_no_key()
            else:
                status = _get_status_offline()
            self._current_status = status
            self.query_one("#status-bar", Static).update(status)

            # Refocus input after all writes are done
            self.query_one("#input-box", Input).focus()

        except Exception:
            pass

    def on_append_output(self, message: AppendOutput) -> None:
        try:
            self.query_one("#output-panel", RichLog).write(message.text)
        except Exception:
            pass

    def on_response_ready(self, message: ResponseReady) -> None:
        try:
            output = self.query_one("#output-panel", RichLog)
            output.write(f"\n[bold #10b981]🔌 Hey Dongle[/]  {message.text}")
            memory.save_message(
                config.DB_PATH, self._session_id, "assistant", message.text
            )
            # Re-enable input
            input_box = self.query_one("#input-box", Input)
            input_box.disabled = False
            input_box.placeholder = "Ask Hey Dongle anything about your code..."
            # Restore status
            self.query_one("#status-bar", Static).update(self._current_status)
            input_box.focus()
        except Exception:
            pass

    # ── Input ──────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message:
            return

        input_box = self.query_one("#input-box", Input)
        output    = self.query_one("#output-panel", RichLog)

        # /clear command
        if message.lower() == "/clear":
            count = memory.clear_session(config.DB_PATH, self._session_id)
            self._session_id = memory.new_session_id()
            output.clear()
            output.write(
                f"[dim]Session cleared ({count} messages deleted). "
                "New session started.[/dim]"
            )
            input_box.value = ""
            input_box.focus()
            return

        input_box.value = ""
        output.write(f"\n[bold #e94560]You →[/] {message}")
        memory.save_message(config.DB_PATH, self._session_id, "user", message)

        if not self._model_ready:
            output.write(
                "[dim]⏳ Model is still loading, please wait a moment...[/dim]"
            )
            input_box.focus()
            return

        input_box.disabled = True
        input_box.placeholder = "Thinking..."
        self.query_one("#status-bar", Static).update(STATUS_THINKING)

        threading.Thread(
            target=self._response_worker,
            args=(message,),
            daemon=True
        ).start()

    # ── Response worker ────────────────────────────────────────────────────────

    def _response_worker(self, message: str) -> None:
        """Background thread — runs agent loop."""
        try:
            history = memory.load_session(config.DB_PATH, self._session_id)
            conv_history = [
                {"role": m["role"], "content": m["content"]}
                for m in history[:-1]
            ]
            context_summary = indexer.get_context_summary(self._index)

            def status_update(text: str):
                self.post_message(StatusUpdate(text))

            response = agent.run_agent_loop(
                user_message=message,
                conversation_history=conv_history,
                context_summary=context_summary,
                prompt_fn=None,
                status_callback=status_update
            )
            self.post_message(ResponseReady(response))

        except Exception as e:
            self.post_message(ResponseReady(f"Error: {str(e)}"))
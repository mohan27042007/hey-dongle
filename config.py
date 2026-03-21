"""
Hey Dongle — Configuration
All settings live here. Edit this file to customize your setup.
"""

import os

# ── PATHS ────────────────────────────────────────────────────────────────────

# Root directory of the project (wherever this file lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Model directory — place your .gguf file here
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Data directory — SQLite session database lives here
DATA_DIR = os.path.join(BASE_DIR, "data")

# Session database path
DB_PATH = os.path.join(BASE_DIR, "data", "sessions.db")


# ── LOCAL MODEL ───────────────────────────────────────────────────────────────

# Path to your GGUF model file.
# To switch models:
#   1. Download any GGUF model and place it in the models/ folder
#   2. Change MODEL_FILENAME to match the filename
#   3. Restart Hey Dongle
#
# Recommended models (download from huggingface.co):
#   Fast (low RAM):  qwen2.5-coder-1.5b-instruct-q4_k_m.gguf  (~1 GB)
#   Balanced:        qwen2.5-coder-3b-q4_k_m.gguf              (~2 GB)
#   Best quality:    qwen2.5-coder-7b-q4_k_m.gguf              (~4.5 GB)

MODEL_FILENAME = "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
MODEL_PATH     = os.path.join(MODELS_DIR, MODEL_FILENAME)

# Context window size (tokens)
# Larger = more context but slower load and more RAM
# 2048  — fast, low RAM
# 4096  — balanced (recommended)
# 8192  — best for large codebases (needs 8GB+ RAM)
N_CTX = 4096

# Number of CPU threads for inference
# Set to your CPU core count for best performance
N_THREADS = 4

# Verbose llama.cpp output (set True to debug model loading)
VERBOSE = False


# ── GROQ API (OPTIONAL — ONLINE ENHANCED MODE) ───────────────────────────────

# Get your free API key at: https://console.groq.com
# Leave empty string "" to stay in offline-only mode
GROQ_API_KEY = ""

# Groq model to use in Enhanced Mode
# compound-beta gives you Llama 4 + web search + browser + code execution
GROQ_MODEL = "compound-beta"


# ── AGENT SETTINGS ────────────────────────────────────────────────────────────

# Maximum number of iterations in the agent loop before stopping
MAX_ITERATIONS = 10

# Maximum number of files to include in codebase context
MAX_CONTEXT_FILES = 20

# Maximum characters to read per file for context
MAX_CHARS_PER_FILE = 2000

# Codebase indexer settings
PROJECT_DIR = os.getcwd()  # directory to index — defaults to wherever app is launched from

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".c", ".cpp", ".h", ".hpp",
    ".java", ".go", ".rs", ".rb",
    ".php", ".swift", ".kt", ".cs",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".sh", ".bash",
    ".sql", ".r", ".m", ".lua",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "target", "out", ".idea", ".vscode", "coverage",
    ".pytest_cache", "eggs", ".eggs", "*.egg-info",
    ".mypy_cache", ".ruff_cache", "vendor", "vendors",
}

MAX_FILE_SIZE_KB = 100        # skip files larger than this — likely binary or generated
MAX_FILES_IN_INDEX = 200      # cap total files to prevent context explosion
MAX_LINES_PER_FILE = 200      # truncate files longer than this in the index
CONTEXT_BUDGET_CHARS = 6000   # max chars for the full index summary (leaves room for conversation)


# ── CODE EXECUTION ────────────────────────────────────────────────────────────

# Code execution settings
EXECUTION_TIMEOUT_SECONDS = 10      # kill process after this many seconds
MAX_OUTPUT_LENGTH_CHARS   = 5000    # truncate combined stdout+stderr to this
ALLOWED_LANGUAGES = {
    "python":     ["python",  "-c"],
    "python3":    ["python3", "-c"],
    "javascript": ["node",    "-e"],
    "js":         ["node",    "-e"],
    "bash":       ["bash",    "-c"],
    "sh":         ["sh",      "-c"],
}

# Dangerous patterns that must never appear in executed code
BLOCKED_PATTERNS = [
    "rm -rf", "rm -r", "rmdir /s", "del /f",    # recursive delete
    "format c", "mkfs",                           # disk format
    ":(){:|:&};:",                                # fork bomb
    "os.system", "subprocess.call",               # subprocess inside execution
    "shutil.rmtree",                              # recursive delete via Python
    "shutdown", "reboot", "halt",                 # system control
    "__import__('os').system",                    # obfuscated os.system
    "eval(", "exec(",                             # code injection vectors
    "open('/etc", "open('C:\\Windows",            # system file access
    "socket.connect", "urllib.request",           # network calls from executed code
    "requests.get", "requests.post",              # network calls
]


# ── CONNECTIVITY ──────────────────────────────────────────────────────────────

# Endpoint to ping for connectivity check (lightweight, no tracking)
CONNECTIVITY_CHECK_URL = "http://detectportal.firefox.com"

# Timeout in seconds for connectivity check
CONNECTIVITY_TIMEOUT = 3

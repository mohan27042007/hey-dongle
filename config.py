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

# Path to your GGUF model file
# Default: Qwen2.5-Coder 3B Q4_K_M (recommended for low-spec machines)
# You can swap this to any GGUF model file you have
MODEL_PATH = os.path.join(MODELS_DIR, "qwen2.5-coder-3b-q4_k_m.gguf")

# Context window size (tokens)
# Qwen2.5-Coder 3B supports up to 32768 — keep at 8192 for low RAM machines
N_CTX = 8192

# Number of CPU threads to use for inference
# Set to your machine's core count for best performance
N_THREADS = 4

# Verbose mode for llama.cpp (set True to debug model loading issues)
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

# Code execution timeout in seconds
EXECUTION_TIMEOUT = 10

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


# ── CONNECTIVITY ──────────────────────────────────────────────────────────────

# Endpoint to ping for connectivity check (lightweight, no tracking)
CONNECTIVITY_CHECK_URL = "http://detectportal.firefox.com"

# Timeout in seconds for connectivity check
CONNECTIVITY_TIMEOUT = 3

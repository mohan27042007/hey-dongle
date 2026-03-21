# Hey Dongle 🔌

> **A Zero-Setup, USB-Portable Agentic Coding Assistant for Offline Environments**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FOSS](https://img.shields.io/badge/FOSS-100%25-brightgreen)](https://opensource.org/licenses)
[![Offline](https://img.shields.io/badge/Internet-Not%20Required-blue)](.)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](.)

---

## The Problem

Over **2 billion people** face unreliable internet monthly. But the deeper problem for developers isn't just connectivity — it's *dependency*.

Every modern AI coding tool assumes:

- A working internet connection
- A pre-configured machine
- Ollama or a runtime pre-installed
- 16GB RAM minimum
- A cloud API key

Students in rural India, engineers on air-gapped corporate networks, developers at hackathon venues with broken WiFi — none of them fit that assumption.

Existing local tools like Goose, Cline, and Continue.dev solve the *privacy* problem. They do not solve the *accessibility and portability* problem. They still require a full local dev environment just to run.

**Hey Dongle solves a different problem: what if your entire AI coding assistant lived on a USB stick and just worked — on any machine — the moment you plugged it in?**

---

## What It Is

Hey Dongle is a **self-contained, agentic AI coding assistant that runs entirely from a USB drive** — no installation, no internet, no pre-configured environment required.

Plug it into any machine running Linux, macOS, or Windows with Python available, and within seconds you have a full agentic coding assistant that can read your codebase, write files, run code, and iterate — autonomously.

> It is not a chatbot. It is not a passive code explainer. It is an **agent** that takes instructions and acts on them.

---

## How It Differs From Existing Tools

|  | Hey Dongle | Goose / Cline / Aider |
|--|--|--|
| Requires installation | ❌ None | ✅ Yes |
| Requires Ollama / runtime | ❌ Bundled | ✅ Must be pre-installed |
| Works on CPU-only machines | ✅ Yes | ⚠️ Partial |
| Works on low-RAM (8GB) machines | ✅ Optimized for it | ⚠️ Struggles |
| Zero internet at any point | ✅ Fully air-gapped | ⚠️ Setup requires internet |
| Target user | Developers anywhere | Developers with good hardware |

---

## Core Agentic Capabilities

### 1. Codebase-Aware Context

Hey Dongle reads your project directory on startup and builds a lightweight index of your files. It doesn't just answer questions — it knows what you're working on.

### 2. Autonomous File Operations

The agent reads files, writes files, creates new ones, and applies targeted edits — with your confirmation before any destructive action. This is a real agentic loop, not suggestions you copy-paste manually.

### 3. Code Execution & Iteration

It runs your code, reads the output or error, and iterates — up to N steps — until the task is complete or it asks for your input.

```
"Fix this bug" → runs code → sees error → edits file → runs again → done.
```

### 4. Natural Language Task Interface

Describe what you want in plain English. Hey Dongle breaks it into steps, executes them, and reports back. No memorizing commands.

### 5. Persistent Conversation Memory

Session history is stored locally on the USB. Come back the next day, plug in, and it remembers exactly where you left off.

---

## Tech Stack

| Layer | Technology | Reason |
|--|--|--|
| Model | Qwen2.5-Coder 3B (Q4_K_M GGUF) | Best coding performance at small size, runs on 6GB RAM CPU-only |
| Inference Runtime | llama-cpp-python (bundled) | CPU-first, no GPU required, cross-platform, zero install |
| Agent Loop | Custom Python — no LangChain | Minimal ~200 line tool-calling loop; lean, fast, auditable |
| Interface | Textual (Python TUI) | Terminal UI, no browser, no server, works on any machine |
| Storage | SQLite (stdlib) | Session memory, file index, conversation history — zero extra deps |
| Packaging | PyInstaller + bundled model | Single folder on USB, one command to launch |

### Hardware Requirements

| Spec | Minimum | Recommended |
|--|--|--|
| RAM | 6 GB free | 8 GB+ |
| CPU | Any x86_64 (2015+) | 4+ cores |
| USB / Disk | 4 GB | 8 GB USB stick |
| GPU | ❌ Not required | Optional speedup |
| Internet | ❌ Not required | ❌ Not required |

---

## Switching Models

Hey Dongle works with any GGUF format model. To switch:

1. Download a GGUF model and place it in the `models/` folder
2. Open `config.py` and change `MODEL_FILENAME`:

```python
MODEL_FILENAME = "your-model-name.gguf"
```

3. Restart Hey Dongle

### Recommended Models

| Model | Size | RAM Required | Speed | Quality |
|-------|------|-------------|-------|---------|
| Qwen2.5-Coder 1.5B Q4 | ~1 GB | 4 GB | Fast | Good |
| Qwen2.5-Coder 3B Q4 | ~2 GB | 6 GB | Medium | Better |
| Qwen2.5-Coder 7B Q4 | ~4.5 GB | 10 GB | Slow | Best |

Download from: [huggingface.co/Qwen](https://huggingface.co/Qwen)

### Context Window

Adjust `N_CTX` in `config.py` based on your RAM:
- `2048` — 4 GB RAM machines
- `4096` — 6-8 GB RAM machines (recommended)
- `8192` — 12+ GB RAM machines

---

## USB Structure

```
HeyDongle/
├── hey_dongle          ← Linux / macOS executable
├── hey_dongle.exe      ← Windows executable
├── models/
│   └── qwen2.5-coder-3b-q4_k_m.gguf
├── data/
│   └── sessions.db     ← Local SQLite memory
└── README.txt
```

---

## Use Cases

- 🌾 Developers in rural or low-connectivity areas
- 🏢 Engineers on air-gapped corporate or government networks
- 🎓 Students at institutions with restricted or limited bandwidth
- 🏁 Competitive programmers at venues with unreliable WiFi
- 🔒 Anyone who needs a fully offline, privacy-first coding assistant

---

## Roadmap

### Phase 1 — FOSS Hack 2026 *(Current)*

- Zero-setup USB deployment
- Qwen2.5-Coder 3B bundled, fully offline
- Agentic loop: file read / write / execute / iterate
- TUI interface via Textual
- Persistent session memory via SQLite

### Phase 2 — Post Hackathon

- RAG over local codebase for larger projects
- User-swappable model support (bring your own GGUF)
- Multi-file refactor planning

### Phase 3 — Future

- MCP (Model Context Protocol) tool integration
- Support for even lower-spec hardware via further quantization
- Community model registry for offline download packs

---

## License

MIT License — fully open-source, no proprietary dependencies, no cloud, no tracking.

---

## Contributing

Hey Dongle is built for and by the FOSS community. Contributions welcome — see `CONTRIBUTING.md`.

---

Built for FOSS Hack 2026 🇮🇳

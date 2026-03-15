import os
import config

LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript",
    ".c": "C", ".cpp": "C++", ".h": "C Header", ".hpp": "C++ Header",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin", ".cs": "C#",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".md": "Markdown", ".sh": "Shell", ".bash": "Shell",
    ".sql": "SQL",
}

def _detect_language(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    return LANGUAGE_MAP.get(ext, "Text")

def _should_skip_dir(dirname: str) -> bool:
    return dirname in config.SKIP_DIRS or dirname.startswith(".")

def _read_file_preview(filepath: str, max_lines: int) -> tuple[str, bool]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    return "".join(lines), True
                lines.append(line)
            return "".join(lines), False
    except (OSError, PermissionError):
        return "[unreadable]", False

def build_index(project_dir: str) -> dict:
    index = {
        "root": project_dir,
        "total_files": 0,
        "languages": {},
        "files": []
    }

    for dirpath, dirnames, filenames in os.walk(project_dir):
        # Prune skip dirs IN PLACE — os.walk respects this
        dirnames[:] = [
            d for d in dirnames
            if not _should_skip_dir(d)
        ]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in config.SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, project_dir)

            # Skip large files
            try:
                size_kb = os.path.getsize(filepath) / 1024
            except OSError:
                continue
            if size_kb > config.MAX_FILE_SIZE_KB:
                continue

            # Cap total file count
            if len(index["files"]) >= config.MAX_FILES_IN_INDEX:
                break

            language = _detect_language(filename)
            preview, truncated = _read_file_preview(
                filepath, config.MAX_LINES_PER_FILE
            )

            file_entry = {
                "path": rel_path.replace("\\", "/"),  # normalise to forward slashes
                "language": language,
                "lines": preview.count("\n") + 1 if preview != "[unreadable]" else 0,
                "size_kb": round(size_kb, 1),
                "preview": preview,
                "truncated": truncated,
            }

            index["files"].append(file_entry)
            index["languages"][language] = \
                index["languages"].get(language, 0) + 1

    index["total_files"] = len(index["files"])
    return index

def get_context_summary(index: dict) -> str:
    lines = []
    lines.append(f"## Project: {os.path.basename(index['root'])}")
    lines.append(f"Files indexed: {index['total_files']}")

    lang_summary = ", ".join(
        f"{lang} ({count})"
        for lang, count in sorted(
            index["languages"].items(),
            key=lambda x: x[1], reverse=True
        )
    )
    lines.append(f"Languages: {lang_summary}")
    lines.append("")
    lines.append("### File Tree")

    total_chars = sum(len(l) for l in lines)

    for file in index["files"]:
        trunc_marker = " [truncated]" if file["truncated"] else ""
        entry = (
            f"{file['path']} "
            f"({file['language']}, {file['lines']} lines){trunc_marker}"
        )
        if total_chars + len(entry) > config.CONTEXT_BUDGET_CHARS:
            lines.append(f"... and {index['total_files'] - len(lines)} more files")
            break
        lines.append(entry)
        total_chars += len(entry)

    return "\n".join(lines)

def get_file_content(index: dict, filepath: str) -> str | None:
    # Normalise path separators for cross-platform lookup
    normalised = filepath.replace("\\", "/")
    for file in index["files"]:
        if file["path"] == normalised:
            return file["preview"]
    return None

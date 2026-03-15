import os
import config

def _confirm(prompt_fn, action: str, details: str) -> bool:
    if prompt_fn is None:
        return True  # auto-approve when no prompt function provided
    try:
        return bool(prompt_fn(action, details))
    except Exception:
        return False  # if prompt_fn crashes, deny by default — safe fallback

def read_file(path: str) -> str:
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: File not found: {path}"
        if not os.path.isfile(abs_path):
            return f"Error: Path is not a file: {path}"
        
        size_kb = os.path.getsize(abs_path) / 1024
        if size_kb > 500:
            return f"Error: File too large to read ({size_kb:.0f} KB). Use search_codebase instead."
            
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        lines = content.count("\n") + 1
        return f"[File: {path} | {lines} lines | {size_kb:.1f} KB]\n\n{content}"
    except PermissionError:
        return f"Error: Permission denied reading {path}"
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

def write_file(path: str, content: str, prompt_fn=None) -> str:
    try:
        abs_path = os.path.abspath(path)
        action = "overwrite" if os.path.exists(abs_path) else "create"
        
        details = (
            f"{action.capitalize()} {path} "
            f"({len(content)} chars, {content.count(chr(10)) + 1} lines)"
        )
        if not _confirm(prompt_fn, "write_file", details):
            return f"Action denied: write_file({path})"
            
        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        lines = content.count("\n") + 1
        return f"Success: {action}d {path} ({lines} lines written)"
    except PermissionError:
        return f"Error: Permission denied writing {path}"
    except Exception as e:
        return f"Error writing {path}: {str(e)}"

def list_directory(path: str) -> str:
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: Directory not found: {path}"
        if not os.path.isdir(abs_path):
            return f"Error: Path is not a directory: {path}"
            
        entries = os.listdir(abs_path)
        if not entries:
            return f"Directory is empty: {path}"
            
        dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(abs_path, e))])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(abs_path, e))])
        
        lines = [f"Directory: {path} ({len(dirs)} dirs, {len(files)} files)"]
        for d in dirs:
            lines.append(f"  📁 {d}/")
        for f in files:
            fpath = os.path.join(abs_path, f)
            size_kb = os.path.getsize(fpath) / 1024
            lines.append(f"  📄 {f}  ({size_kb:.1f} KB)")
            
        return "\n".join(lines)
    except PermissionError:
        return f"Error: Permission denied listing {path}"
    except Exception as e:
        return f"Error listing {path}: {str(e)}"

def apply_patch(path: str, diff: str, prompt_fn=None) -> str:
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: File not found: {path}"
            
        if "<<<FIND>>>" not in diff or "<<<REPLACE>>>" not in diff:
            return (
                "Error: Invalid patch format. "
                "Use <<<FIND>>>...<<<REPLACE>>>...<<<END>>>"
            )
            
        try:
            find_part    = diff.split("<<<FIND>>>")[1].split("<<<REPLACE>>>")[0]
            replace_part = diff.split("<<<REPLACE>>>")[1].split("<<<END>>>")[0]
        except IndexError:
            return "Error: Malformed patch — missing <<<END>>> marker"
            
        details = f"Patch {path} — replace {len(find_part)} chars with {len(replace_part)} chars"
        if not _confirm(prompt_fn, "apply_patch", details):
            return f"Action denied: apply_patch({path})"
            
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()
            
        if find_part not in original:
            return (
                f"Error: Could not find the target text in {path}. "
                "The file may have changed. Use read_file first to get current content."
            )
            
        patched = original.replace(find_part, replace_part, 1)  # replace first occurrence only
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(patched)
            
        return f"Success: Patch applied to {path}"
    except PermissionError:
        return f"Error: Permission denied patching {path}"
    except Exception as e:
        return f"Error patching {path}: {str(e)}"

def search_codebase(query: str, project_dir: str = None) -> str:
    try:
        search_dir = os.path.abspath(project_dir or config.PROJECT_DIR)
        if not query or not query.strip():
            return "Error: Search query cannot be empty"
            
        matches = []
        files_searched = 0
        
        for dirpath, dirnames, filenames in os.walk(search_dir):
            dirnames[:] = [
                d for d in dirnames
                if d not in config.SKIP_DIRS and not d.startswith(".")
            ]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in config.SUPPORTED_EXTENSIONS:
                    continue
                    
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, search_dir).replace("\\", "/")
                
                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                matches.append(
                                    f"{rel_path}:{line_num}:  {line.rstrip()}"
                                )
                                if len(matches) >= 50:
                                    break
                    files_searched += 1
                except (OSError, PermissionError):
                    continue
                    
                if len(matches) >= 50:
                    break
                    
        if not matches:
            return f"No matches found for '{query}' in {files_searched} files searched."
            
        result = [f"Found {len(matches)} match(es) for '{query}':"]
        result.extend(matches)
        
        if len(matches) >= 50:
            result.append("(Search capped at 50 results)")
            
        return "\n".join(result)
    except Exception as e:
        return f"Error searching codebase: {str(e)}"

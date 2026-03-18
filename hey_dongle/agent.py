import json
import re
import config
import hey_dongle.tools as tools
import hey_dongle.infer as infer

SYSTEM_PROMPT = """You are Hey Dongle, an offline AI coding assistant running on a USB drive.
You help developers read, understand, edit, and fix code.

You have access to the following tools. To use a tool, respond with ONLY a JSON object in this exact format:
{{"tool": "tool_name", "args": {{"arg1": "value1", "arg2": "value2"}}}}

Available tools:
- read_file: {{"tool": "read_file", "args": {{"path": "relative/path/to/file"}}}}
- write_file: {{"tool": "write_file", "args": {{"path": "relative/path", "content": "full file content"}}}}
- list_directory: {{"tool": "list_directory", "args": {{"path": "."}}}}
- apply_patch: {{"tool": "apply_patch", "args": {{"path": "file.py", "diff": "<<<FIND>>>\\nold\\n<<<REPLACE>>>\\nnew\\n<<<END>>>"}}}}
- run_code: {{"tool": "run_code", "args": {{"language": "python", "code": "print('hello')"}}}}
- search_codebase: {{"tool": "search_codebase", "args": {{"query": "function_name"}}}}

IMPORTANT RULES:
1. If you want to use a tool, respond with ONLY the JSON object. No other text.
2. If you have a final answer for the user, respond with plain text. No JSON.
3. Always read a file before writing or patching it.
4. After writing or patching a file, verify your change by reading it back.
5. Keep responses concise. The user can see your tool results directly.
6. If a tool returns an error, explain what went wrong and try a different approach.
7. Never make up file contents. Always use read_file first.

Current project context:
{context_summary}
"""

def _build_tool_definitions() -> list[dict]:
    return [
        {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a file with new content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string", "description": "Full file content to write"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "list_directory",
            "description": "List files and folders in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "apply_patch",
            "description": "Apply a targeted find-and-replace edit to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "diff": {
                        "type": "string",
                        "description": "Patch in <<<FIND>>>...<<<REPLACE>>>...<<<END>>> format"
                    }
                },
                "required": ["path", "diff"]
            }
        },
        {
            "name": "run_code",
            "description": "Execute code and return stdout and stderr",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language: python, javascript, bash"
                    },
                    "code": {"type": "string", "description": "Code to execute"}
                },
                "required": ["language", "code"]
            }
        },
        {
            "name": "search_codebase",
            "description": "Search all project files for a query string",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"}
                },
                "required": ["query"]
            }
        },
    ]

def _execute_tool(tool_name: str, args: dict, prompt_fn) -> str:
    try:
        if tool_name == "read_file":
            return tools.read_file(args.get("path", ""))
        elif tool_name == "write_file":
            return tools.write_file(
                args.get("path", ""),
                args.get("content", ""),
                prompt_fn=prompt_fn
            )
        elif tool_name == "list_directory":
            return tools.list_directory(args.get("path", "."))
        elif tool_name == "apply_patch":
            return tools.apply_patch(
                args.get("path", ""),
                args.get("diff", ""),
                prompt_fn=prompt_fn
            )
        elif tool_name == "run_code":
            return tools.run_code(
                args.get("language", "python"),
                args.get("code", ""),
                prompt_fn=prompt_fn
            )
        elif tool_name == "search_codebase":
            return tools.search_codebase(args.get("query", ""))
        else:
            return f"Error: Unknown tool '{tool_name}'"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

def _parse_tool_call(response: str) -> dict | None:
    text = response.strip()

    # Strip markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # Must look like a JSON object to attempt parsing
    if not text.startswith("{"):
        return None

    try:
        parsed = json.loads(text)
        # Validate it has the expected structure
        if "tool" in parsed and "args" in parsed:
            if isinstance(parsed["tool"], str) and isinstance(parsed["args"], dict):
                return parsed
        return None
    except json.JSONDecodeError:
        # Try to extract JSON from within a larger response
        json_match = re.search(r'\{[^{}]*"tool"[^{}]*"args"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if "tool" in parsed and "args" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        return None

def run_agent_loop(
    user_message: str,
    conversation_history: list,
    context_summary: str,
    prompt_fn,
    status_callback=None
) -> str:
    # Build system prompt with project context
    system_prompt = SYSTEM_PROMPT.format(context_summary=context_summary)

    # Build messages list 
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    tool_definitions = _build_tool_definitions()
    final_response = None

    for iteration in range(config.MAX_ITERATIONS):
        # Update status bar if callback provided
        if status_callback:
            status_callback(f"🔄 Thinking... Iteration {iteration + 1} / {config.MAX_ITERATIONS}")

        # Call the model
        response = infer.chat_with_tools(messages, tool_definitions)

        # Try to parse as a tool call
        tool_call = _parse_tool_call(response)

        if tool_call is None:
            # No tool call — this is the final plain text answer
            final_response = response.strip()
            break

        # Valid tool call — execute it
        tool_name = tool_call["tool"]
        tool_args = tool_call["args"]

        if status_callback:
            status_callback(f"⚡ Executing tool: {tool_name}")

        tool_result = _execute_tool(tool_name, tool_args, prompt_fn)

        # Add the tool call and result to message history
        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"[Tool result: {tool_name}]\n{tool_result}"
        })

    # If we exhausted the iteration limit without a plain text answer
    if final_response is None:
        final_response = (
            "I reached the maximum number of steps without completing the task. "
            "Here is what I found so far. Please try rephrasing your request or "
            "breaking it into smaller steps."
        )

    return final_response

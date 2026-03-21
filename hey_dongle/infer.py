import json
import re
from typing import List, Dict, Any, Optional, Union
import config
import os

_model = None

def _get_llama():
    try:
        from llama_cpp import Llama
        return Llama
    except ImportError:
        raise ImportError(
            "llama-cpp-python is not installed. "
            "Install it with: pip install llama-cpp-python"
        )

def validate_model() -> None:
    """
    Validates the model file exists and is a valid GGUF file.
    Raises FileNotFoundError with clear instructions if not found.
    """
    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(
            f"\n\n"
            f"Model file not found: {config.MODEL_PATH}\n\n"
            f"To fix this:\n"
            f"  1. Download a GGUF model from huggingface.co\n"
            f"  2. Place it in: {config.MODELS_DIR}\n"
            f"  3. Update MODEL_FILENAME in config.py to match\n\n"
            f"Recommended: qwen2.5-coder-1.5b-instruct-q4_k_m.gguf\n"
            f"Download:    huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"
        )

    if not config.MODEL_PATH.endswith('.gguf'):
        raise ValueError(
            f"Model file must be a .gguf file: {config.MODEL_PATH}\n"
            f"Download GGUF format models from huggingface.co"
        )

    size_mb = os.path.getsize(config.MODEL_PATH) / (1024 * 1024)
    if size_mb < 100:
        raise ValueError(
            f"Model file is too small ({size_mb:.0f} MB) — likely corrupted.\n"
            f"Re-download the model file."
        )

def load_model():
    """
    Loads the GGUF model from config.MODEL_PATH as a singleton.
    Forces CPU only and uses exact settings from config.
    """
    global _model
    if _model is not None:
        return _model

    validate_model()
    Llama = _get_llama()

    try:
        _model = Llama(
            model_path=config.MODEL_PATH,
            n_ctx=config.N_CTX,
            n_threads=config.N_THREADS,
            n_gpu_layers=0,  # Force CPU only
            verbose=config.VERBOSE
        )
        return _model
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {config.MODEL_PATH}: {str(e)}")

def chat(messages: List[Dict[str, str]]) -> str:
    """
    Takes a list of OpenAI-formatted messages and returns the raw text response.
    """
    model = load_model()
    
    try:
        response = model.create_chat_completion(
            messages=messages,
            temperature=0.1
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error during chat completion: {str(e)}"

def chat_with_tools(messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
    """
    Takes messages and tools, and returns either a plain string response,
    or a structured tool call dictionary: {"tool": "name", "args": {...}}
    """
    model = load_model()
    
    try:
        response = model.create_chat_completion(
            messages=messages,
            tools=tools,
            temperature=0.1
        )
        message = response["choices"][0]["message"]
        
        # Check if native tool calls exist in the response
        if "tool_calls" in message and message["tool_calls"]:
            tool_call = message["tool_calls"][0]
            if "function" in tool_call:
                name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                try:
                    args = json.loads(args_str)
                    return {"tool": name, "args": args}
                except json.JSONDecodeError:
                    pass # Fallback to text parsing
        
        # Fallback 1: Try to parse the content as JSON directly
        content = message.get("content", "")
        if not content:
            content = ""
            
        # Strip markdown logic as requested
        # First try to extract json from code fences
        cleaned_content = content.strip()
        cleaned_content = re.sub(r'^```(?:json)?\n?', '', cleaned_content)
        cleaned_content = re.sub(r'\n?```$', '', cleaned_content).strip()
        
        try:
            parsed = json.loads(cleaned_content)
            # If the model raw response happened to be exactly the JSON dict we want
            if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                return parsed
            # Or if it returned a function call style dict directly
            if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                 return {"tool": parsed["name"], "args": parsed["arguments"]}
        except json.JSONDecodeError:
            pass
            
        # Return plain text if no tool call was successfully parsed
        return content
        
    except Exception as e:
        return f"Error during chat completion with tools: {str(e)}"

def get_model_info() -> Dict[str, Any]:
    """
    Returns a simple dictionary containing current model settings.
    """
    return {
        "filename": config.MODEL_FILENAME,
        "path": config.MODEL_PATH,
        "n_ctx": config.N_CTX,
        "n_threads": config.N_THREADS,
        "loaded": _model is not None,
        "size_mb": round(
            os.path.getsize(config.MODEL_PATH) / (1024 * 1024), 1
        ) if os.path.exists(config.MODEL_PATH) else 0
    }

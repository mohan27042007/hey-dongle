import json
import re
from typing import List, Dict, Any, Optional, Union
from llama_cpp import Llama
import config
import os

_model: Optional[Llama] = None

def load_model() -> Llama:
    """
    Loads the GGUF model from config.MODEL_PATH as a singleton.
    Forces CPU only and uses exact settings from config.
    """
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {config.MODEL_PATH}. Please download it first.")

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
        "name": os.path.basename(config.MODEL_PATH),
        "n_ctx": config.N_CTX,
        "n_threads": config.N_THREADS,
        "loaded": _model is not None
    }

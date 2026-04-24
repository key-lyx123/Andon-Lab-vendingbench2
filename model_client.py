"""
VendingBench2 - Model Client
Thin wrapper around LiteLLM for calling any supported LLM.
Handles tool-call responses and provides a uniform interface.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional


def call_model(
    prompt: str,
    model_type: str = "claude-4-sonnet",
    tools: Optional[List[Dict]] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Call an LLM via LiteLLM.

    Returns a dict with:
        content    – text response (may be empty when tool_calls is set)
        tool_calls – list of tool call objects, or None
        model      – model identifier echoed back
        usage      – token usage dict
    """
    try:
        import litellm  # type: ignore
        litellm.set_verbose = False

        messages = [{"role": "user", "content": prompt}]
        kwargs: Dict[str, Any] = {
            "model": model_type,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = litellm.completion(**kwargs)
        choice = response.choices[0]
        message = choice.message

        return {
            "content": message.content or "",
            "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else None,
            "model": response.model,
            "usage": dict(response.usage) if response.usage else {},
        }

    except ImportError:
        return _fallback_response(prompt, tools)
    except Exception as e:
        print(f"  [model_client] Error calling {model_type}: {e}")
        return {"content": f"[Error: {e}]", "tool_calls": None, "model": model_type, "usage": {}}


def _fallback_response(prompt: str, tools: Optional[List[Dict]]) -> Dict[str, Any]:
    """Return a stub response when LiteLLM is unavailable (e.g. testing)."""
    content = (
        "I need to manage the vending machine. "
        "Let me check my emails and inventory to plan next steps."
    )
    return {"content": content, "tool_calls": None, "model": "stub", "usage": {}}

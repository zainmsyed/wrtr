"""AI helper shim for wrtr that calls into an external `hlpr` package if available.

This file provides a single async-compatible `generate` function which lazily
imports `hlpr` and calls its `generate` function. It tolerates both sync and
async `hlpr.generate` implementations and returns friendly messages when the
module or function is missing.
"""
from __future__ import annotations
from typing import Optional, Dict
import importlib
import asyncio
from wrtr.logger import logger


async def generate(prompt: str, context: Optional[str] = None, options: Optional[Dict] = None) -> str:
    """Generate a response using the `hlpr` package if installed.

    - If `hlpr` is not importable, return an actionable message.
    - If `hlpr.generate` is synchronous, return its string result.
    - If `hlpr.generate` is a coroutine function, await it and return the result.
    - On unexpected errors, return a short `AI error: ...` message and log the traceback.
    """
    try:
        hlpr = importlib.import_module("hlpr")
    except Exception:
        return "AI unavailable: hlpr module not found. Install with `pip install hlpr`."

    gen = getattr(hlpr, "generate", None)
    if gen is None:
        return "AI unavailable: hlpr.generate not found in hlpr package."

    try:
        # Call the generate function. It may be sync (returns str) or async (returns coroutine).
        result = gen(prompt) if context is None and options is None else gen(prompt, context=context, options=options)
        if asyncio.iscoroutine(result):
            return await result
        return str(result)
    except Exception as e:
        logger.exception("hlpr.generate raised an exception")
        return f"AI error: {e}"

"""
AI helper service for generating content via hlpr module
"""
import importlib
import asyncio
from wrtr.logger import logger


async def generate(prompt: str, context: str = None, options: dict = None) -> str:
    """Generate text via hlpr module, handling sync and async generate functions."""
    try:
        hlpr = importlib.import_module('hlpr')
    except ImportError:
        # HLPR not installed
        return "hlpr module not found"

    gen = getattr(hlpr, 'generate', None)
    if gen is None:
        return "hlpr.generate not found"

    try:
        if asyncio.iscoroutinefunction(gen):
            return await gen(prompt, context=context, options=options)
        else:
            return gen(prompt, context=context, options=options)
    except Exception as e:
        logger.error(f"Error in hlpr.generate: {e}")
        return f"HLPR error: {e}"

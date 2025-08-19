"""Service package initializer.

This module performs lightweight, idempotent initialization for services that
should be available when the application imports the `wrtr.services` package.

Currently it ensures the default slash commands are registered with the
SlashCommandService so the running UI has handlers available without test
fixtures or explicit calls from application startup code.

The registration is intentionally guarded so imports are safe and repeatable
in tests.
"""
"""Service package initializer.

Register editor default slash commands on import so the running UI has the
commands available without requiring tests or the application to call an
explicit initializer.

This initializer is defensive: it avoids raising on import failure and it is
idempotent (it checks for existing registrations before registering).
"""
from typing import Optional
import inspect
import importlib.util
from pathlib import Path

from wrtr.services.slash_command_service import SlashCommandService

# default_commands lives in the editor module, but importing the package
# (`wrtr.editor`) triggers optional dependencies (spellcheck/symspellpy). To
# avoid forcing those imports at service import time, attempt a normal import
# first and then fall back to loading the module directly from file if it
# fails.
try:
    from wrtr.editor.slash_commands import default_commands  # type: ignore
except Exception:
    # Fallback: load the file directly from src/wrtr/editor/slash_commands.py
    try:
        base = Path(__file__).resolve().parents[1]  # .../src/wrtr
        candidate = base / 'editor' / 'slash_commands.py'
        if candidate.exists():
            spec = importlib.util.spec_from_file_location('wrtr_editor_slash_commands', str(candidate))
            module = importlib.util.module_from_spec(spec)
            loader = spec.loader
            assert loader is not None
            loader.exec_module(module)
            default_commands = getattr(module, 'default_commands')
        else:
            default_commands = None
    except Exception:
        default_commands = None  # type: Optional[callable]


def _make_handler(fn):
    """Wrap a default insert_fn into the (args, full_line) handler signature.

    The wrapper supports both sync and async fn, and falls back to calling
    fn() if fn doesn't accept args to avoid TypeError.
    """
    if inspect.iscoroutinefunction(fn):
        async def handler(args: str, full_line: str, _fn=fn):
            try:
                return await _fn(args)
            except TypeError:
                return await _fn()

        return handler

    def handler(args: str, full_line: str, _fn=fn):
        try:
            return _fn(args)
        except TypeError:
            return _fn()

    return handler


def initialize_services() -> None:
    """Register default editor slash commands (idempotent).

    This function intentionally swallows exceptions to keep imports safe for
    test environments; tests can still register/clear the registry directly.
    """
    if not default_commands:
        return

    try:
        for cmd in default_commands():
            name = cmd.label.split()[0].lower()
            if name in SlashCommandService.get_commands():
                continue
            handler = _make_handler(cmd.insert_fn)
            # Use the public register API
            SlashCommandService.register(name, handler, help=cmd.help_text, description=getattr(cmd, 'description', ''))
    except Exception:
        # Don't break imports on failure; tests can manage registration.
        return


# Run initialization on import so the running app sees default commands.
try:
    initialize_services()
except Exception:
    pass
"""
Services package for core application logic.
"""

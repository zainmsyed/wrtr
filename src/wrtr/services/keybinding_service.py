"""Small service to centralize keybinding actions across the app.

Currently provides a registered action to load a Path into the secondary
editor pane (editor_b) in a background thread and update recent files.

This keeps screen code thin and ensures file I/O doesn't block the
Textual event loop.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from textual.app import App

logger = logging.getLogger(__name__)


class KeybindingService:
    """A tiny registry for semantic keybinding actions.

    Handlers must be callables that accept arbitrary args/kwargs and may be
    sync or async. Use :meth:`trigger` to invoke them.
    """

    _registry: Dict[str, Callable[..., Awaitable[None]]] = {}

    @classmethod
    def register(cls, name: str, handler: Callable[..., Awaitable[None]]) -> None:
        cls._registry[name] = handler

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._registry.pop(name, None)

    @classmethod
    async def trigger(cls, name: str, *args: Any, **kwargs: Any) -> None:
        handler = cls._registry.get(name)
        if not handler:
            logger.debug("No keybinding handler registered for %s", name)
            return
        try:
            result = handler(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            logger.exception("Error while running keybinding handler %s", name)


async def _load_path_into_editor_b(app: App, path: Path) -> None:
    """Load `path` into the secondary editor pane (editor_b).

    This reads the file in a background thread and then manipulates widgets
    on the main loop. Failures are logged; no exception is raised to callers.
    """
    try:
        content = await asyncio.to_thread(path.read_text, "utf-8")
    except Exception:
        logger.exception("Failed to read %s", path)
        return

    try:
        # Make sure editor panes are visible and resize layout if needed
        try:
            app.query_one("#editor_a").visible = True
            app.query_one("#editor_b").visible = True
            app.layout_manager.layout_resize()
        except Exception:
            # Best-effort; continue even if layout adjustments fail
            logger.debug("Could not ensure editor panes visible/resized")

        editor = app.query_one("#editor_b")
        # Editor API expected: load_text, set_path, focus
        try:
            editor.load_text(content)
            editor.set_path(path)
            editor.focus()
        except Exception:
            logger.exception("Failed to load content into editor_b for %s", path)

        # Update recent files list (import lazily to avoid cycles)
        try:
            from wrtr.services.recent_files_service import RecentFilesService

            RecentFilesService.add(path)
        except Exception:
            logger.debug("Failed to update RecentFilesService for %s", path)
    except Exception:
        logger.exception("Unexpected error loading %s into editor_b", path)


# Register the common action name so callers can use the semantic name.
KeybindingService.register("load_in_editor_b", _load_path_into_editor_b)

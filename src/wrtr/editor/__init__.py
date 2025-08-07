"""
Module: Editor Package
"""
from textual.widgets import TextArea
from wrtr.markdown_preview import MarkdownPreviewMixin
from textual.containers import Vertical
from textual.events import Key
from wrtr.logger import logger  # centralized logger
from pathlib import Path
from wrtr.status_bar import EditorStatusBar
from typing import Generator
from textual.widget import Widget
from tree_sitter_markdown import language
from wrtr.interfaces.spellcheck_service import SpellCheckService
from wrtr.services.spellcheck import MarkdownSpellchecker
import re

from .autosave import AutoSaveManager
from .keybindings import handle_key_event
from .buffer import TextBuffer
from .view import TextView


class MarkdownEditor(MarkdownPreviewMixin, Vertical):
    """
    Markdown editor widget with syntax highlighting, auto-save,
    and a status bar that does NOT overlap the last line.
    """
    BINDINGS = [
        ("ctrl+shift+m", "toggle_preview", "Toggle MD Preview"),
    ]

    def action_toggle_preview(self) -> None:
        """Toggle markdown preview in this editor pane."""
        self.toggle_markdown_preview()

    def __init__(self, id=None, spellchecker: SpellCheckService | None = None):
        super().__init__(id=id)
        # Saved file path
        self._saved_path = None
        # Initialize AutoSaveManager
        self.autosave = AutoSaveManager(self)
        # Spellchecker will be lazy-loaded when spellcheck is started (F7)
        # Dependency-injected spellchecker for testability
        self.spellchecker: SpellCheckService | None = spellchecker
        self._spellcheck_active = False
        # Initialize text buffer and conversion alias
        self.buffer = TextBuffer()
        self._convert_text_position_to_cursor = self.buffer.convert_text_position_to_cursor

    def compose(self) -> Generator[Widget, None, None]:
        """Inner composition: TextArea + StatusBar."""
        self.text_area = TextArea(text="", language="markdown")
        # Setup view helper for cursor movement and replacements
        self.view = TextView(self.text_area)
        self.text_area.styles.padding = (2, 3)
        self.status_bar = EditorStatusBar()
        yield self.text_area
        yield self.status_bar

    @property
    def text(self) -> str:
        # Delegate to buffer for authoritative text
        return self.buffer.get_text()

    @text.setter
    def text(self, value: str) -> None:
        # Update buffer and TextArea
        self.buffer.set_text(value)
        self.text_area.text = value

    def load_text(self, value: str) -> None:
        if hasattr(self, 'markdown_viewer'):
            self.restore_text_area()
        # Sync buffer and TextArea
        self.buffer.set_text(value)
        self.text_area.load_text(value)

    def set_path(self, path: Path) -> None:
        self._saved_path = path
        self.status_bar.file_path = path

    def clear_status(self) -> None:
        self.autosave.timer and self.autosave.timer.stop()
        self._saved_path = None
        self.status_bar.file_path = None
        self.status_bar.saved = True
        self.text_area.load_text("")
        self.status_bar.refresh_stats()

    def on_text_area_changed(self, event) -> None:
        # Update status bar and schedule autosave
        self.status_bar.refresh_stats()
        self.autosave.schedule()
        self.status_bar.saved = False
        # Sync buffer content and cursor position
        self.buffer.set_text(self.text_area.text)
        row, col = self.text_area.cursor_location
        self.buffer.cursor_row = row
        self.buffer.cursor_col = col

    async def on_key(self, event: Key) -> None:
        """Delegate key handling to extracted handler."""
        await handle_key_event(self, event)

    # ...existing spellcheck methods unchanged...
    
    def _show_notification(self, message: str):
        """Display a notification to the user via Textual's notification system."""
        try:
            self.app.notify(message, severity="info")
        except Exception:
            print(f"Notification: {message}")

    # ...remaining methods...

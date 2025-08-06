"""
Module: Editor Package
"""
from textual.widgets import TextArea
from markdown_preview import MarkdownPreviewMixin
from textual.containers import Vertical
from textual.events import Key
from logger import logger  # centralized logger
from pathlib import Path
from status_bar import EditorStatusBar
from typing import Generator
from textual.widget import Widget
from tree_sitter_markdown import language
from interfaces.spellcheck_service import SpellCheckService
from spellcheck import MarkdownSpellchecker
import re

from .autosave import AutoSaveManager
from .keybindings import handle_key_event


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

    def __init__(self, id=None):
        super().__init__(id=id)
        self._saved_path: Path | None = None
        # Initialize AutoSaveManager
        self.autosave = AutoSaveManager(self)

        # Spellchecker will be loaded on first use to speed up startup
        self.spellchecker: SpellCheckService | None = None
        self._spellcheck_active: bool = False

    def compose(self) -> Generator[Widget, None, None]:
        """Inner composition: TextArea + StatusBar."""
        self.text_area = TextArea(text="", language="markdown")
        self.text_area.styles.padding = (2, 3)
        self.status_bar = EditorStatusBar()
        yield self.text_area
        yield self.status_bar

    @property
    def text(self) -> str:
        return self.text_area.text

    @text.setter
    def text(self, value: str) -> None:
        self.text_area.text = value

    def load_text(self, value: str) -> None:
        if hasattr(self, 'markdown_viewer'):
            self.restore_text_area()
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
        self.status_bar.refresh_stats()
        self.autosave.schedule()
        self.status_bar.saved = False

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
    def _convert_text_position_to_cursor(self, text_pos: int) -> tuple[int, int]:
        """Convert absolute text index to (row, col) cursor position in the TextArea."""
        # Split text into lines
        lines = self.text.split('\n')
        current_pos = 0
        for line_num, line in enumerate(lines):
            line_end = current_pos + len(line)
            if text_pos <= line_end:
                col = text_pos - current_pos
                return (line_num, col)
            # Account for newline character
            current_pos = line_end + 1
        # If position beyond end, place at end of text
        if lines:
            return (len(lines) - 1, len(lines[-1]))
        return (0, 0)

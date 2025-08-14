"""
Module: Editor Package
"""
from textual.widgets import TextArea, Input
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
from .editor_search import SearchService

from .autosave import AutoSaveManager
from .keybindings import handle_key_event
from .buffer import TextBuffer
from .view import TextView
from textual.events import MouseDown
from wrtr.interfaces.backlink_interface import BacklinkClicked


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
        # Initialize search service and floating input widget
        self.searcher = SearchService(self)

    def compose(self) -> Generator[Widget, None, None]:
        """Inner composition: TextArea + StatusBar."""
        from .text_area_factory import make_markdown_text_area
        self.text_area = make_markdown_text_area(initial_text="", language="markdown")
        # Setup view helper for cursor movement and replacements
        self.view = TextView(self.text_area)
        self.text_area.styles.padding = (2, 3, 1, 3)
        self.text_area.styles.width = "100%"  # Ensure full width
        self.text_area.styles.height = "100%"  # Ensure full height
        self.status_bar = EditorStatusBar()
        yield self.text_area
        yield self.status_bar
    
    async def on_mount(self) -> None:
        """Mount floating widgets after editor is attached to DOM asynchronously."""
        # Mount the search input now that the editor is mounted
        await self.mount(self.searcher.input)

    @property
    def text(self) -> str:
        # Delegate to buffer for authoritative text
        return self.buffer.get_text()

    @text.setter
    def text(self, value: str) -> None:
        # Update buffer and TextArea (with backlink highlighting)
        self.buffer.set_text(value)
        # Use TextView to load text and highlight backlinks
        self.view.set_text(value)

    def load_text(self, value: str) -> None:
        if hasattr(self, 'markdown_viewer'):
            self.restore_text_area()
        # Sync buffer and TextArea (with backlink highlighting)
        self.buffer.set_text(value)
        self.view.set_text(value)

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
        # Recompute backlink highlights so color overlays follow edits
        try:
            self.view.highlight_backlinks()
        except Exception:
            pass
        try:
            self.view.refresh_custom_highlights()
        except Exception:
            pass

    async def on_key(self, event: Key) -> None:
        """Handle key events: delegate to editor search or default bindings."""
        # Activate search on Ctrl+F
        if event.key == "ctrl+f":
            # start search mode
            self._search_active = True
            self.searcher.activate()
            event.stop()
            return
        # If search mode active, handle search nav and exit
        if getattr(self, '_search_active', False):
            # Enter: perform search and move to first result
            if event.key == "enter":
                self.searcher.query = self.searcher.input.value.strip()
                self.searcher.find_matches()
                if not self.searcher.positions:
                    self._show_notification(f"No matches for '{self.searcher.query}'")
                else:
                    self.searcher.current_index = 0
                    self.searcher.move_to_current()
                # Keep input visible for navigation
                self.text_area.focus()
                event.stop()
                return
            # F3: next match
            if event.key == "f3":
                self.searcher.next()
                # refocus text for cursor visibility
                self.text_area.focus()
                event.stop()
                return
            # Shift+F3: previous match
            if event.key == "shift+f3":
                self.searcher.previous()
                # refocus text for cursor visibility
                self.text_area.focus()
                event.stop()
                return
            # Escape: exit search mode
            if event.key == "escape":
                self._search_active = False
                self.searcher.deactivate()
                event.stop()
                return
        # Handle Ctrl+Enter to open backlink references via keyboard
        if event.key == "ctrl+enter" and hasattr(self.view, 'backlink_regions'):
            # Map cursor to offset and emit BacklinkClicked if on a link
            row, col = self.text_area.cursor_location
            try:
                offset = self.buffer.rowcol_to_offset(row, col)
            except Exception:
                return
            for start, end, target in self.view.backlink_regions:
                if start <= offset < end:
                    self.post_message(BacklinkClicked(self, target))
                    event.stop()
                    return
        # Default handler
        await handle_key_event(self, event)

    async def on_input_changed(self, message: Input.Changed) -> None:
        """Update search as query changes and move to current match."""
        # Only handle our search service's input
        if message.input is not self.searcher.input:
            return
        # Update query and find matches
        self.searcher.query = message.value.strip()
        self.searcher.find_matches()
        self.searcher.move_to_current()
    
    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Trigger search when user presses Enter in search input."""
        if message.input is not self.searcher.input:
            return
        # Finalize query and jump to first match
        self.searcher.query = message.value.strip()
        self.searcher.find_matches()
        if not self.searcher.positions:
            # No matches: notify user and keep input open
            self._show_notification(f"No matches for '{self.searcher.query}'")
            return
        # Move to first match
        self.searcher.current_index = 0
        self.searcher.move_to_current()
        # Provide match count feedback
        total = len(self.searcher.positions)
        self._show_notification(
            f"Found {total} match{'es' if total != 1 else ''} for '{self.searcher.query}'"
        )
        # Return focus to text area so the cursor is visible and navigation works
        self.text_area.focus()

    # ...existing spellcheck methods unchanged...
    
    def _show_notification(self, message: str):
        """Display a notification to the user via Textual's notification system."""
        try:
            self.app.notify(message, severity="info")
        except Exception:
            print(f"Notification: {message}")

    # ...remaining methods...

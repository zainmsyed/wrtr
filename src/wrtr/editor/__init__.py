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
from wrtr.services.slash_commands import SlashCommandService
import asyncio
from wrtr.logger import logger


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
        # Create the text area
        self.text_area = make_markdown_text_area(initial_text="", language="markdown")
        # Setup view helper for cursor movement and replacements
        self.view = TextView(self.text_area)
        # Status bar below the text area
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
        prev_row = getattr(self, '_prev_row', None)
        self.buffer.set_text(self.text_area.text)
        row, col = self.text_area.cursor_location
        self.buffer.cursor_row = row
        self.buffer.cursor_col = col
        # Detect Enter/newline by observing a row increase. If the user pressed Enter
        # and moved to a new row, inspect the previous line for a slash command.
        try:
            if prev_row is not None and row > prev_row:
                # previous line is at index prev_row
                full_text = self.buffer.get_text()
                # compute start offset of previous line
                start_off = self.buffer.rowcol_to_offset(prev_row, 0)
                nl = full_text.find("\n", start_off)
                end_off = nl if nl != -1 else len(full_text)
                line = full_text[start_off:end_off]
                parsed = SlashCommandService.parse(line)
                if parsed:
                    # Run the command asynchronously (keep UI responsive)
                    placeholder = "…thinking (hlpr)…"
                    # Replace the previous line with placeholder
                    try:
                        start_rc = (prev_row, 0)
                        end_rc = (prev_row, len(line))
                        self.view.replace_range(start=start_rc, end=end_rc, insert=placeholder)
                    except Exception:
                        new_text = full_text[:start_off] + placeholder + full_text[end_off:]
                        self.view.set_text(new_text)

                    async def _run_cmd():
                        try:
                            result = await SlashCommandService.execute(line)
                        except Exception as e:
                            result = f"Command error: {e}"
                        logger.debug(f"Slash command result for line '{line}': {result}")
                        try:
                            cur_text = self.buffer.get_text()
                            start = self.buffer.rowcol_to_offset(prev_row, 0)
                            end = start + len(placeholder)
                            new_text = cur_text[:start] + str(result) + cur_text[end:]
                            self.view.set_text(new_text)
                            try:
                                self._show_notification(f"Command /{parsed[0]} inserted result",)
                            except Exception:
                                pass
                            new_row, new_col = self.buffer.convert_text_position_to_cursor(start + len(str(result)))
                            self.view.move_cursor(new_row, new_col, center=False)
                        except Exception:
                            pass

                    asyncio.create_task(_run_cmd())
        except Exception:
            pass
        # Save current row for next change event
        self._prev_row = row
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
        # Intercept Enter to run slash commands when present on the current line
        if event.key == "enter":
            try:
                # Obtain current buffer text and cursor position
                full_text = self.buffer.get_text()
                row, col = self.text_area.cursor_location
                start_off = self.buffer.rowcol_to_offset(row, 0)
                # end of current line
                next_newline = full_text.find("\n", start_off)
                end_off = next_newline if next_newline != -1 else len(full_text)
                line = full_text[start_off:end_off]
                parsed = SlashCommandService.parse(line)
                if parsed:
                    # Debug notification so users see the command was detected
                    try:
                        self._show_notification(f"Running command: /{parsed[0]}",)
                    except Exception:
                        pass
                    # Show placeholder while running command
                    placeholder = "…thinking (hlpr)…"
                    # compute start and end as (row,col) pairs for replace_range
                    start_rc = (row, 0)
                    end_rc = (row, len(line))
                    # Replace visible text in the TextArea
                    try:
                        self.view.replace_range(start=start_rc, end=end_rc, insert=placeholder)
                    except Exception:
                        # Fallback to direct load_text replace if replace_range isn't available
                        new_text = full_text[:start_off] + placeholder + full_text[end_off:]
                        self.view.set_text(new_text)

                    async def _run_command():
                        try:
                            result = await SlashCommandService.execute(line)
                        except Exception as e:
                            result = f"Command error: {e}"
                        logger.debug(f"Slash command result for line '{line}': {result}")
                        # Replace placeholder with result
                        try:
                            # refresh full_text because the underlying buffer may have changed
                            cur_text = self.buffer.get_text()
                            # find placeholder occurrence at expected location
                            start = self.buffer.rowcol_to_offset(row, 0)
                            end = start + len(placeholder)
                            # Build replacement text
                            new_text = cur_text[:start] + str(result) + cur_text[end:]
                            # Apply
                            self.view.set_text(new_text)
                            try:
                                self._show_notification(f"Command /{parsed[0]} inserted result",)
                            except Exception:
                                pass
                            # Move cursor to end of inserted result
                            new_row, new_col = self.buffer.convert_text_position_to_cursor(start + len(str(result)))
                            self.view.move_cursor(new_row, new_col, center=False)
                        except Exception:
                            # Best-effort: if anything fails, reload without change
                            pass

                    asyncio.create_task(_run_command())
                    event.stop()
                    # mark handled so child TextArea doesn't also process it
                    try:
                        setattr(event, '_handled', True)
                    except Exception:
                        pass
                    return
            except Exception:
                # On any error, fall back to default handling
                pass

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

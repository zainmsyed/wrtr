"""
Module: View rendering for MarkdownEditor.
Handles TextArea scrolling, syntax highlighting, and Rich integration.
"""
from textual.widgets import TextArea
from textual.containers import Vertical
from textual.events import Key

class TextView:
    """Encapsulates rendering and view-related utilities for TextArea."""

    def __init__(self, text_area: TextArea) -> None:
        self.text_area = text_area

    def move_cursor(self, row: int, col: int, center: bool = False) -> None:
        """Position cursor and optionally center the view."""
        self.text_area.cursor_location = (row, col)
        if center:
            self.text_area.scroll_cursor_visible(center=True)

    def focus(self) -> None:
        """Focus the TextArea for input."""
        self.text_area.focus()

    def set_text(self, text: str) -> None:
        """Load text into the TextArea and highlight backlinks."""
        self.text_area.load_text(text)
        # After loading, highlight any backlinks [[target]]
        self.highlight_backlinks()

    def replace_range(self, start: tuple[int, int], end: tuple[int, int], insert: str) -> None:
        """Replace text in the given range."""
        self.text_area.replace(start=start, end=end, insert=insert)

    def highlight_backlinks(self) -> None:
        """Highlight all [[target]] backlinks as link style."""
        import re
        # Prepare storage for clickable regions
        self.backlink_regions: list[tuple[int,int,str]] = []
        text = self.text_area.text
        # regex to match [[target]]
        pattern = re.compile(r"\[\[([^\]]+)\]\]")
        for m in pattern.finditer(text):
            start_off, end_off = m.span()
            target = m.group(1)
            # convert offsets to (row, col)
            start_pos = self._offset_to_cursor_pos(text, start_off)
            end_pos = self._offset_to_cursor_pos(text, end_off)
            # store region
            self.backlink_regions.append((start_off, end_off, target))
            # apply link style
            try:
                self.text_area.add_highlight(start_pos, end_pos, "link")
            except Exception:
                pass

    def _offset_to_cursor_pos(self, text: str, offset: int) -> tuple[int, int]:
        """Convert a character offset in text to (row, col) cursor position."""
        lines = text[:offset].splitlines(True)
        row = len(lines) - 1
        col = len(lines[-1]) if lines else 0
        return row, col

    # Future: integrate Rich syntax highlighting here

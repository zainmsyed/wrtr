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
        """Load text into the TextArea."""
        self.text_area.load_text(text)

    def replace_range(self, start: tuple[int, int], end: tuple[int, int], insert: str) -> None:
        """Replace text in the given range."""
        self.text_area.replace(start=start, end=end, insert=insert)

    # Future: integrate Rich syntax highlighting here

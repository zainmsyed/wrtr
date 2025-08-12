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
        """Overlay blue highlights for any [[target]] and store regions.

        Uses TextArea's internal _highlights to add custom per-line ranges with
        the name 'wikilink'. The active theme maps 'wikilink' to blue.
        """
        import re
        ta = self.text_area
        text = ta.text
        # Track regions for activation
        self.backlink_regions: list[tuple[int, int, str]] = []
        # Remove previous custom wikilink highlights
        try:
            for line_idx, items in list(getattr(ta, "_highlights", {}).items()):
                ta._highlights[line_idx] = [h for h in items if len(h) < 3 or h[2] != "wikilink"]
        except Exception:
            pass
        # Add current highlights
        lines = text.splitlines()
        pattern = re.compile(r"\[\[([^\]]+)\]\]")
        for m in pattern.finditer(text):
            start_off, end_off = m.span()
            target = m.group(1)
            self.backlink_regions.append((start_off, end_off, target))
            (start_row, start_col) = self._offset_to_cursor_pos(text, start_off)
            (end_row, end_col) = self._offset_to_cursor_pos(text, end_off)
            if start_row == end_row:
                try:
                    ta._highlights[start_row].append((start_col, end_col, "wikilink"))
                except Exception:
                    pass
            else:
                try:
                    ta._highlights[start_row].append((start_col, len(lines[start_row]), "wikilink"))
                    for row in range(start_row + 1, end_row):
                        ta._highlights[row].append((0, len(lines[row]), "wikilink"))
                    ta._highlights[end_row].append((0, end_col, "wikilink"))
                except Exception:
                    pass
        try:
            ta.refresh()
        except Exception:
            pass

    def _offset_to_cursor_pos(self, text: str, offset: int) -> tuple[int, int]:
        """Convert a character offset in text to (row, col) cursor position."""
        lines = text[:offset].splitlines(True)
        row = len(lines) - 1
        col = len(lines[-1]) if lines else 0
        return row, col

    # Future: integrate Rich syntax highlighting here

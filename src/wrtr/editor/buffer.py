"""
Module: Buffer management for MarkdownEditor.
Holds in-memory text, cursor position, and undo/redo functionality.
"""
from typing import Tuple, List

class TextBuffer:
    """Manages the text content, cursor position, and undo/redo stack."""

    def __init__(self, text: str = "") -> None:
        self._lines: List[str] = text.split("\n")
        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []

    def set_text(self, text: str) -> None:
        """Replace buffer content and reset cursor."""
        self._undo_stack.append(self.get_text())
        self._lines = text.split("\n")
        self.cursor_row = 0
        self.cursor_col = 0
        self._redo_stack.clear()

    def get_text(self) -> str:
        """Return full buffer text."""
        return "\n".join(self._lines)

    def convert_cursor_to_text_position(self) -> int:
        """Convert (cursor_row, cursor_col) to absolute text index."""
        pos = 0
        for i, line in enumerate(self._lines):
            if i < self.cursor_row:
                pos += len(line) + 1  # newline
            else:
                pos += min(self.cursor_col, len(line))
                break
        return pos

    def convert_text_position_to_cursor(self, text_pos: int) -> Tuple[int, int]:
        """Convert absolute text index to (row, col)."""
        current_pos = 0
        for line_num, line in enumerate(self._lines):
            end = current_pos + len(line)
            if text_pos <= end:
                return (line_num, text_pos - current_pos)
            current_pos = end + 1
        # End of buffer
        if self._lines:
            last = self._lines[-1]
            return (len(self._lines) - 1, len(last))
        return (0, 0)
    def rowcol_to_offset(self, row: int, col: int) -> int:
        """Convert (row, col) to absolute text position."""
        # Sum lengths of all previous lines (including newline)
        pos = 0
        for i, line in enumerate(self._lines):
            if i < row:
                pos += len(line) + 1
            else:
                pos += min(col, len(line))
                break
        return pos

    def undo(self) -> None:
        """Undo last text change."""
        if self._undo_stack:
            self._redo_stack.append(self.get_text())
            prev = self._undo_stack.pop()
            self._lines = prev.split("\n")

    def redo(self) -> None:
        """Redo last undone change."""
        if self._redo_stack:
            self._undo_stack.append(self.get_text())
            nxt = self._redo_stack.pop()
            self._lines = nxt.split("\n")

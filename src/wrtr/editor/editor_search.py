"""
Module: Editor search service for MarkdownEditor.
Handles activating/deactivating search, finding matches, and cursor navigation.
"""
import re
from rapidfuzz import process, fuzz
from textual.widgets import Input


class SearchService:
    """Provides simple fuzzy/exact search within an editor pane."""
    def __init__(self, editor):
        self.editor = editor
        self.query = ""
        self.positions: list[tuple[int, int]] = []
        self.current_index = 0
        # Floating input widget for search
        self.input = Input(placeholder="Search...", id="editor-search-input")
        self.input.styles.position = "absolute"  # Overlay widget
        self.input.styles.top = "0"  # Align at top
        self.input.styles.width = "100%"  # Full width
        self.input.styles.height = "auto"  # Auto height
        # Hide until activated
        self.input.visible = False

    def activate(self):
        """Show the input widget and prepare for a new search."""
        self.query = ""
        self.positions = []
        self.current_index = 0
        self.input.value = ""
        self.input.visible = True
        self.input.focus()

    def deactivate(self):
        """Hide the input widget and refocus the text area."""
        self.input.visible = False
        self.editor.text_area.styles.width = "100%"  # Ensure editor pane fills available space
        self.editor.text_area.focus()

    def find_matches(self):
        """Find all exact or fuzzy matches for the current query."""
        text = self.editor.text_area.text
        self.positions = []
        if self.query:
            lower_text = text.lower()
            q_low = self.query.lower()
            # exact substring matches
            start = 0
            while True:
                idx = lower_text.find(q_low, start)
                if idx == -1:
                    break
                self.positions.append(self.editor._convert_text_position_to_cursor(idx))
                start = idx + len(q_low)
            # fallback to fuzzy on words if no exact matches
            if not self.positions:
                words = set(re.findall(r"\w+", text))
                matches = process.extract(self.query, list(words), scorer=fuzz.WRatio, limit=3)
                for word, score, _ in matches:
                    if score < 80:  # Increase threshold to avoid irrelevant matches
                        continue
                    w_low = word.lower()
                    s2 = 0
                    while True:
                        idx2 = lower_text.find(w_low, s2)
                        if idx2 == -1:
                            break
                        self.positions.append(self.editor._convert_text_position_to_cursor(idx2))
                        s2 = idx2 + len(w_low)
        self.current_index = 0

    def move_to_current(self):
        """Move the editor cursor to the current match."""
        if self.positions:
            row, col = self.positions[self.current_index]
            self.editor.view.move_cursor(row, col, center=True)

    def next(self):
        """Navigate to the next match, wrapping around."""
        if self.positions:
            self.current_index = (self.current_index + 1) % len(self.positions)
            self.move_to_current()

    def previous(self):
        """Navigate to the previous match, wrapping around."""
        if self.positions:
            self.current_index = (self.current_index - 1) % len(self.positions)
            self.move_to_current()

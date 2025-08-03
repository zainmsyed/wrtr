"""
Module: Editor Status Bar
Shows filename, save status and word count.
"""
from textual.widgets import Static
from textual.reactive import reactive
from pathlib import Path
from typing import Optional, List

class EditorStatusBar(Static):
    """A tiny status bar that lives inside each MarkdownEditor."""

    file_path: reactive[Path | None] = reactive(None)
    saved: reactive[bool] = reactive(True)
    spellcheck_mode: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = 1
        self.styles.dock = "bottom"
        self.styles.background = "rgb(40,40,40)"
        self.styles.color = "rgb(220,220,220)"
        self.styles.padding = (0, 1)
        # Spellcheck state
        self.current_word: Optional[str] = None
        self.suggestions: List[str] = []
        self.progress: tuple[int, int] = (0, 0)

    def _word_count(self) -> int:
        """Naïve word counter."""
        return len(self.parent.text.split())

    def _render_spellcheck_text(self) -> str:
        """Compose the spellcheck status string."""
        if not self.current_word:
            return "Spellcheck: No misspelled words found | ESC to exit"

        current, total = self.progress
        suggestions_text = ", ".join(self.suggestions[:3]) if self.suggestions else "No suggestions"

        return (f"Misspelled: '{self.current_word}' ({current}/{total}) | "
                f"Suggestions: {suggestions_text} | "
                f"F3:Next Shift+F3:Prev A:Add I:Ignore ESC:Exit")

    def _render_text(self) -> str:
        """Compose the appropriate status string based on mode."""
        if self.spellcheck_mode:
            return self._render_spellcheck_text()
        else:
            name = self.file_path.name if self.file_path else "[No File]"
            status = "● Saved" if self.saved else "● Modified"
            words = self._word_count()
            return f"{name}  |  {status}  |  {words} words"

    def watch_file_path(self) -> None:
        self.update(self._render_text())

    def watch_saved(self) -> None:
        self.update(self._render_text())

    def watch_spellcheck_mode(self) -> None:
        # Adjust height based on mode
        self.styles.height = 15 if self.spellcheck_mode else 1
        self.update(self._render_text())

    def on_mount(self) -> None:
        self.update(self._render_text())

    def refresh_stats(self) -> None:
        """Recalculate everything and redraw."""
        self.update(self._render_text())

    def set_spellcheck_info(self, word: Optional[str], suggestions: List[str], progress: tuple[int, int]):
        """Update spellcheck information."""
        self.current_word = word
        self.suggestions = suggestions
        self.progress = progress
        if self.spellcheck_mode:
            self.update(self._render_text())

    def enter_spellcheck_mode(self):
        """Enter spellcheck mode."""
        self.spellcheck_mode = True

    def exit_spellcheck_mode(self):
        """Exit spellcheck mode."""
        self.spellcheck_mode = False
        self.current_word = None
        self.suggestions = []
        self.progress = (0, 0)

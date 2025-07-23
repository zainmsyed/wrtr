"""
Module: Editor Status Bar
Shows filename, save status and word count.
"""
from textual.widgets import Static
from textual.reactive import reactive
from pathlib import Path

class EditorStatusBar(Static):
    """A tiny status bar that lives inside each MarkdownEditor."""

    file_path: reactive[Path | None] = reactive(None)
    saved: reactive[bool] = reactive(True)

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = 1
        self.styles.dock = "bottom"
        self.styles.background = "rgb(40,40,40)"
        self.styles.color = "rgb(220,220,220)"
        self.styles.padding = (0, 1)

    def _word_count(self) -> int:
        """Naïve word counter."""
        return len(self.parent.text.split())

    def _render_text(self) -> str:
        """Compose the right-aligned status string."""
        name = self.file_path.name if self.file_path else "[No File]"
        status = "● Saved" if self.saved else "● Modified"
        words = self._word_count()
        return f"{name}  |  {status}  |  {words} words"

    def watch_file_path(self) -> None:
        self.update(self._render_text())

    def watch_saved(self) -> None:
        self.update(self._render_text())

    def on_mount(self) -> None:
        self.update(self._render_text())

    def refresh_stats(self) -> None:
        """Recalculate everything and redraw."""
        self.update(self._render_text())

"""
Module: Editor Pane
"""
from textual.widgets import TextArea
from textual.containers import Vertical
from textual.events import Key
from pathlib import Path
from textual.timer import Timer
from status_bar import EditorStatusBar
from typing import Generator
from textual.widget import Widget
from tree_sitter_markdown import language


class MarkdownEditor(Vertical):
    """
    Markdown editor widget with syntax highlighting, auto-save,
    and a status bar that does NOT overlap the last line.
    """
    def __init__(self, id=None):
        super().__init__(id=id)
        self._saved_path: Path | None = None
        self._save_timer: Timer | None = None
        self._debounce_delay: float = 5.0

    def compose(self) -> Generator[Widget, None, None]:
        """Inner composition: TextArea + StatusBar."""
        self.text_area = TextArea(text="", language="markdown")
        self.text_area.styles.padding = (1, 2)  # Add padding: 1 line vertical, 2 spaces horizontal
        self.status_bar = EditorStatusBar()
        yield self.text_area
        yield self.status_bar

    # ── forward the public helpers to the inner TextArea ------------
    @property
    def text(self) -> str:
        return self.text_area.text

    @text.setter
    def text(self, value: str) -> None:
        self.text_area.text = value

    def load_text(self, value: str) -> None:
        self.text_area.load_text(value)

    def set_path(self, path: Path) -> None:
        self._saved_path = path
        self.status_bar.file_path = path

    def clear_status(self) -> None:
        if self._save_timer:
            self._save_timer.stop()
            self._save_timer = None
        self._saved_path = None
        self.status_bar.file_path = None
        self.status_bar.saved = True
        self.text_area.load_text("")
        self.status_bar.refresh_stats()
    # ---------------------------------------------------------------

    def _schedule_auto_save(self) -> None:
        if self._save_timer:
            self._save_timer.stop()
        self._save_timer = self.set_timer(
            self._debounce_delay, self._auto_save, name="autosave"
        )

    def _auto_save(self) -> None:
        if self._saved_path:
            self._saved_path.write_text(self.text)
            self.status_bar.saved = True
            try:
                # Commented out auto-save notification for quieter operation
                # self.app.notify(f"Auto-saved {self._saved_path.name}")
                pass
            except Exception:
                pass
        else:
            # New file: mark as unsaved, but do not auto-launch Save As
            self.status_bar.saved = False

    def on_text_area_changed(self, event) -> None:
        self.status_bar.refresh_stats()
        self._schedule_auto_save()
        self.status_bar.saved = False

    async def on_key(self, event: Key) -> None:
        if event.key == "ctrl+w" or getattr(event, 'name', None) == "ctrl_w":
            self.clear_status()
            browser = self.app.query_one("#file-browser")
            editor_a = self.app.query_one("#editor_a")
            editor_b = self.app.query_one("#editor_b")

            if self.id == "editor_b":
                editor_b.visible = False
                editor_b.styles.display = 'none'
                editor_b.styles.width = '0%'
            elif self.id == "editor_a":
                if editor_b.visible:
                    content = editor_b.text
                    editor_a.text = content
                    editor_a.set_path(editor_b._saved_path)
                    editor_b.clear_status()
                    editor_b.visible = False
                    editor_b.styles.display = 'none'
                    editor_b.styles.width = '0%'
                else:
                    editor_a.clear_status()
                    editor_a.text = ''
            # layout recalculation ...
            editor_a.focus()
            event.stop()
            return

# Remove custom tree-sitter registration for now
# TextArea should handle markdown built-in or fall back gracefully

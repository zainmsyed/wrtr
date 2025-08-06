"""
Auto-save manager for MarkdownEditor.
Handles debounced saves of editor content.
"""
from textual.timer import Timer
from pathlib import Path

class AutoSaveManager:
    """Manages debounced auto-saving for a widget with a set_timer API."""
    def __init__(self, widget, debounce_delay: float = 1.0):
        self.widget = widget
        self.debounce_delay = debounce_delay
        self.timer: Timer | None = None

    def schedule(self) -> None:
        """Schedule or reschedule an auto-save event after debounce_delay seconds."""
        if self.timer:
            self.timer.stop()
        # set_timer returns a Timer that calls _do_save after delay
        self.timer = self.widget.set_timer(
            self.debounce_delay, self._do_save, name="autosave"
        )

    def _do_save(self) -> None:
        """Perform the actual save if the editor has a path."""
        if self.widget._saved_path:
            self.widget._saved_path.write_text(self.widget.text)
            self.widget.status_bar.saved = True
            # Notification suppressed by default
        else:
            # New file: mark as unsaved but do not prompt
            self.widget.status_bar.saved = False

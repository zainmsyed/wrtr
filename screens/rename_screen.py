from pathlib import Path
from typing import Iterable
from textual.widget import Widget
from textual.widgets import Input, Button, Label
from textual.containers import Vertical, Horizontal
from palette_dismiss_modal import PaletteDismissModal

class RenameScreen(PaletteDismissModal[str | None]):
    """Modal to prompt for renaming a file or folder."""
    def __init__(self, old_path: Path) -> None:
        super().__init__()
        self.old_path = old_path
        self.current_dir = old_path.parent
        self.filename = old_path.name

    def compose_modal(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(f"Rename {self.old_path.name} in {self.current_dir}", id="breadcrumb")
            yield Input(value=self.filename, placeholder="New name", id="filename_input")
            with Horizontal():
                yield Button("Rename", id="rename")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rename":
            new_name = self.query_one("#filename_input", Input).value
            self.dismiss(new_name)
        elif event.button.id == "cancel":
            self.dismiss(None)

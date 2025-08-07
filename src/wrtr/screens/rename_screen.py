from pathlib import Path
from typing import Iterable
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, Horizontal
from textual.widgets import Input, Button, Label
from textual import events
from wrtr.modals.modal_base import EscModal

class RenameScreen(EscModal, ModalScreen[str | None]):
    """Modal to rename a file or folder."""

    CSS = """
    RenameScreen { align: center middle; }

    #rename-box {
        width: auto;
        max-width: 70;
        height: auto;
        background: $background; /* Match the main background color */
        color: $text;
        border: tall $background; /* Blend border with background */
        padding: 1 2;
    }

    #breadcrumb { margin-bottom: 1; }
    #filename_input { width: 100%; margin-bottom: 1; }

    #buttons {
        width: 100%;
        height: auto;
    }
    #buttons Button {
        width: 1fr;
        margin-right: 1;
    }
    #buttons Button:last-of-type {
        margin-right: 0;
    }
    """

    def __init__(self, old_path: Path) -> None:
        super().__init__()
        self.old_path = old_path
        self.current_dir = old_path.parent
        self.filename = old_path.name

    def compose(self) -> Iterable:
        with Center():
            with Middle():
                with Vertical(id="rename-box"):
                    yield Label(
                        f"Rename {self.old_path.name} in {self.current_dir}",
                        id="breadcrumb"
                    )
                    yield Input(
                        value=self.filename,
                        placeholder="New name",
                        id="filename_input"
                    )
                    with Horizontal(id="buttons"):
                        yield Button("Rename (Ctrl+r)", id="rename")
                        yield Button("Cancel (Ctrl+c)", id="cancel")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "rename":
            self.dismiss(self.query_one("#filename_input", Input).value)
        else:
            self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+r":
            self.query_one("#rename").press()
        elif event.key == "ctrl+c":
            self.query_one("#cancel").press()

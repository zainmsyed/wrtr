from pathlib import Path
from typing import Iterable
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, Horizontal
from textual.widgets import Input, Button, Label, DirectoryTree
from textual import events
from modal_base import EscModal

class SaveAsScreen(EscModal, ModalScreen[Path | None]):
    """Save-as dialog with optional directory browser."""

    CSS = """
    SaveAsScreen { align: center middle; }

    #save-box {
        width: auto;
        max-width: 70;
        height: auto;
        background: $panel;
        color: $text;
        border: tall $background;
        padding: 1 2;
    }

    #breadcrumb    { margin-bottom: 1; }
    #filename_input { width: 100%; margin-bottom: 1; }

    #buttons {
        width: auto;
        height: auto;
    }
    #buttons Button {
        width: auto;
        margin-right: 1;
    }

    #tree {
        display: none;          /* start hidden */
        height: 15;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        default_filename: str = "untitled.md",
        default_dir: Path | None = None
    ) -> None:
        super().__init__()
        self.current_dir = default_dir or Path.cwd()
        if not Path(default_filename).suffix:
            default_filename = f"{default_filename}.md"
        self.filename = default_filename

    def compose(self) -> Iterable:
        with Center():
            with Middle():
                with Vertical(id="save-box"):
                    yield Label(f"New file in {self.current_dir}", id="breadcrumb")
                    yield Input(
                        value=self.filename,
                        placeholder="File name",
                        id="filename_input"
                    )
                    with Horizontal(id="buttons"):
                        yield Button("Save (Ctrl+s)", id="save")
                        yield Button("Cancel (Ctrl+c)", id="cancel")
                        yield Button("Browse… (Ctrl+b)", id="browse")

                    tree = DirectoryTree(self.current_dir, id="tree")
                    yield tree

    # ── same event handlers as before -----------------
    def on_button_pressed(self, event) -> None:
        if event.button.id == "save":
            name = self.query_one("#filename_input", Input).value
            if not Path(name).suffix:
                name = f"{name}.md"
            self.dismiss(self.current_dir / name)
        elif event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "browse":
            tree = self.query_one("#tree")
            tree.display = not tree.display
            if tree.display:
                tree.focus()

    def on_directory_tree_directory_selected(self, event) -> None:
        self.current_dir = event.path
        self.query_one("#breadcrumb").update(str(self.current_dir))
        tree = self.query_one("#tree")
        tree.display = False
        self.query_one("#filename_input").focus()

    def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+s":
            self.query_one("#save").press()
        elif event.key == "ctrl+c":
            self.query_one("#cancel").press()
        elif event.key == "ctrl+b":
            self.query_one("#browse").press()

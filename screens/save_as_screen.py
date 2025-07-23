from pathlib import Path
from typing import Iterable
from textual.widget import Widget
from textual.widgets import Input, Button, Label, DirectoryTree
from textual.containers import Vertical, Horizontal
from palette_dismiss_modal import PaletteDismissModal

class SaveAsScreen(PaletteDismissModal[Path | None]):
    def __init__(self, default_filename: str = "untitled.md", default_dir: Path | None = None) -> None:
        super().__init__()
        # Initialize starting directory for file creation
        self.current_dir = default_dir or Path.cwd()
        # Ensure default filename has .md extension
        if not Path(default_filename).suffix:
            default_filename = f"{default_filename}.md"
        self.filename = default_filename

    def compose_modal(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(f"New file in {self.current_dir}", id="breadcrumb")
            yield Input(value=self.filename, placeholder="File name", id="filename_input")
            with Horizontal():
                yield Button("Create", id="save")
                yield Button("Cancel", id="cancel")
                yield Button("Browse…", id="browse")

        # Tree starts hidden
        tree = DirectoryTree(self.current_dir, id="tree")
        tree.display = False
        yield tree

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            name = self.query_one("#filename_input", Input).value
            # Ensure filename has .md extension if none specified
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

from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Vertical
from pathlib import Path
from textual.events import Key
from wrtr.interfaces.backlink_interface import BacklinkClicked
from pathlib import Path

class ReferencesScreen(Screen):
    """Displays all references to a given backlink target."""

    BINDINGS = [("escape", "close", "Close")]

    def __init__(self, target: str, base_dir: Path | None = None) -> None:
        super().__init__()
        self.target = target
        self.base_dir = base_dir or Path.cwd() / "wrtr"
        self.references: list[tuple[Path, int, str]] = []

    def compose(self):
        yield Label(f"References for [[{self.target}]]", id="title")
        self.list_view = ListView()
        yield Vertical(self.list_view, id="refs-container")

    async def on_mount(self) -> None:
        # Search for target in all markdown files under base_dir
        for file in Path(self.base_dir).rglob("*.md"):
            try:
                lines = file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines, start=1):
                if self.target in line:
                    snippet = line.strip()
                    self.references.append((file, idx, snippet))
        # Populate list view
        for file_path, line_no, snippet in self.references:
            item = ListItem(Label(f"{file_path.name}:{line_no} → {snippet}"))
            await self.list_view.append(item)

    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        # Jump to the selected reference
        # Determine selected index from ListView
        idx = self.list_view.index
        path, line_no, _ = self.references[idx]
        # Suppress the next editor click to avoid re-triggering backlink handling
        setattr(self.app, '_suppress_backlink_clicks', True)
        # Close the ReferencesScreen
        self.app.pop_screen()
        # Open the selected file in the main editor
        await self.app.action_open_file(str(path))

    def action_close(self) -> None:
        self.app.pop_screen()

    async def on_key(self, event: Key) -> None:
        """Intercept Escape to close ReferencesScreen without navigating home."""
        if event.key == "escape":
            self.app.pop_screen()
            event.stop()

    async def on_key(self, event: Key) -> None:
        # Intercept Escape to only pop this ReferencesScreen
        if event.key == "escape":
            self.app.pop_screen()
            event.stop()

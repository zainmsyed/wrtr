from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Vertical
from pathlib import Path
from textual.events import Key
from wrtr.interfaces.backlink_interface import BacklinkClicked
from pathlib import Path
from wrtr.services.recent_files_service import RecentFilesService
from wrtr.services.keybinding_service import KeybindingService

class ReferencesScreen(Screen):
    """Displays all references to a given backlink target."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("enter", "select", "Open Reference"),
        ("ctrl+enter", "select", "Open Reference (Ctrl+Enter)"),
    ]

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
        from rich.text import Text

        def _trim(s: str, max_len: int = 100) -> str:
            s = s.strip().replace("\n", " ")
            return s if len(s) <= max_len else s[: max_len - 1].rstrip() + "…"

        for file_path, line_no, snippet in self.references:
            txt = Text()
            txt.append(f"{file_path.name}:{line_no}", style="bold")
            txt.append("\n")
            txt.append(_trim(snippet))
            txt.append("\n")
            txt.append(str(file_path.parent), style="dim")
            item = ListItem(Label(txt))
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

    async def action_select(self) -> None:
        """Open the currently highlighted reference."""
        idx = self.list_view.index
        path, line_no, _ = self.references[idx]
        # Suppress click echo in editor
        setattr(self.app, '_suppress_backlink_clicks', True)
        # Close this screen and open file
        self.app.pop_screen()
        await self.app.action_open_file(str(path))

    async def on_key(self, event: Key) -> None:
        """Handle Escape to close, and Enter/Ctrl+Enter to select reference."""
        key = event.key or getattr(event, 'name', None)

        if key == "escape":
            self.app.pop_screen()
            event.stop()
        elif key in ("enter", "ctrl+enter"):  # support keyboard navigation
            idx = self.list_view.index
            path, line_no, _ = self.references[idx]
            setattr(self.app, '_suppress_backlink_clicks', True)
            self.app.pop_screen()
            await self.app.action_open_file(str(path))
            event.stop()

        # Mirror RecentFilesScreen: allow Ctrl+M to load selected reference
        if key == "ctrl+m":
            try:
                lv = self.list_view
                idx = lv.index
                if idx is not None and 0 <= idx < len(lv.children):
                    # Determine path from the stored references list
                    path, line_no, _ = self.references[idx]
                    # Close this screen and trigger centralized loader
                    self.app.pop_screen()
                    await KeybindingService.trigger("load_in_editor_b", self.app, path)
                    event.stop()
                    return
            except Exception:
                try:
                    self.app.pop_screen()
                except Exception:
                    pass
                event.stop()
                return

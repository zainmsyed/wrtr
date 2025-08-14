"""
Module: Search Pane
"""
from pathlib import Path
import asyncio  # run blocking file I/O in background thread
from rapidfuzz import process, fuzz
from wrtr.favorite_manager import get as get_favorites
from textual.widgets import Input, ListView, ListItem, Static
from textual.containers import Vertical
from wrtr.modals.palette_dismiss_modal import PaletteDismissModal
from typing import Iterable
from textual.widget import Widget
from textual.events import Key

class GlobalSearchScreen(PaletteDismissModal[None]):
    """Global fuzzy search overlay for filenames and contents."""

    DEFAULT_CSS = """
    GlobalSearchScreen {
        align: center middle;      /* center the overlay itself */
        border: none;              /* remove border around GlobalSearchScreen */
        outline: none;             /* remove outline around GlobalSearchScreen */
    }

    #search-box {
        width: 80;                 /* fixed width (≈ 80 cols) */
        height: auto;
        max-height: 25;
    }

    #search-box Input {
        width: 100%;
        margin-bottom: 1;
    }

    #search-box #results {
        width: 100%;
        height: auto;
        max-height: 20;
    }
    #search-box #results ListItem {
        margin-bottom: 1;
        padding: 0 1;
    }
    """

    # Escape will dismiss with default None via PaletteDismissModal

    def __init__(self, placeholder: str = "Search...") -> None:
        super().__init__()
        # store placeholder text and runtime flags
        self.placeholder = placeholder
        # Whether to include favorites in the search index (toggleable at runtime)
        self.include_favorites = True

    def compose_modal(self) -> Iterable[Widget]:
        with Vertical(id="search-box"):
            yield Input(placeholder=self.placeholder)
            yield ListView(id="results")

    async def on_mount(self):
        """Build search index in a background thread to avoid blocking the UI."""
        titles, contents = await asyncio.to_thread(self._scan_files)
        self.titles = titles
        self.contents = contents

    async def on_input_changed(self, message: Input.Changed):
        query = message.value.strip()
        results = self.query_one(ListView)
        await results.clear()
        if not query:
            return
        # Fuzzy match against the string keys (filenames and content snippets)
        t_matches = process.extract(query, list(self.titles.keys()), scorer=fuzz.token_sort_ratio, limit=10)
        c_matches = process.extract(query, list(self.contents.keys()), scorer=fuzz.partial_ratio, limit=20)
        combined = sorted(t_matches + c_matches, key=lambda x: x[1], reverse=True)[:15]
        for label, score, _ in combined:
            path = self.titles.get(label) or self.contents.get(label)
            # Show label with its parent path for extra context
            display = f"{label} — {path.parent}"
            item = ListItem(Static(display))
            item.path = path
            await results.append(item)

    async def on_list_view_selected(self, message: ListView.Selected):
        # Open selected file in main app
        path = message.item.path
        # Dismiss search overlay first
        self.dismiss(None)
        # Then open the file
        await self.app.action_open_file(path)

    def on_key(self, event: Key) -> None:
        """Intercept keys to manage focus and navigation."""
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
        # Only hijack arrow keys when focus is on the search input
        elif event.key in ("down", "up") and isinstance(self.focused, Input):
            results = self.query_one(ListView)
            self.set_focus(results)
            if results.children:
                if event.key == "down":
                    results.index = 0
                else:
                    results.index = len(results.children) - 1
            event.stop()
        # Allow ListView to handle navigation when focused
        elif event.key in ("down", "up") and isinstance(self.focused, ListView):
            super().on_key(event)
        elif event.key == "tab":
            # Return focus to the search box when Tab is pressed
            search_box = self.query_one(Input)
            self.set_focus(search_box)
            event.stop()
        else:
            super().on_key(event)

        # Toggle inclusion of favorites in the index at runtime
        if event.key.lower() == "f":
            # flip the flag and rebuild the index in background
            self.include_favorites = not getattr(self, "include_favorites", True)
            asyncio.create_task(self._rebuild_index())
            event.stop()

    async def _rebuild_index(self) -> None:
        """Rebuild the search index in a background thread and refresh results."""
        titles, contents = await asyncio.to_thread(self._scan_files)
        self.titles = titles
        self.contents = contents

    def _scan_files(self) -> tuple[dict[str, Path], dict[str, Path]]:
        """Scan the workspace for .md files and index their names and content lines.

        Includes files from `wrtr/` and, when enabled, from favorite directories.
        """
        titles: dict[str, Path] = {}
        contents: dict[str, Path] = {}

        def _add_file_to_index(file: Path, source_tag: str) -> None:
            try:
                base_name = file.name
                label = base_name if base_name not in titles else f"{base_name} [{source_tag}]"
                titles[label] = file
                lines = file.read_text(encoding="utf-8").splitlines()
            except Exception:
                return
            for i, line in enumerate(lines, start=1):
                key = f"{label}:{i}:{line.strip()}"
                if key not in contents:
                    contents[key] = file

        # Scan markdown files in the Terminal Writer data directory (wrtr/)
        data_dir = Path.cwd() / "wrtr"
        if data_dir.exists():
            for file in data_dir.rglob("*.md"):
                _add_file_to_index(file, "wrtr")

        # Optionally scan favorites
        if getattr(self, "include_favorites", True):
            try:
                fav_dirs = get_favorites()
            except Exception:
                fav_dirs = []
            for fav in fav_dirs:
                if not fav.exists():
                    continue
                for file in fav.rglob("*.md"):
                    _add_file_to_index(file, "fav")

        return titles, contents

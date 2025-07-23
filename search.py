"""
Module: Search Pane
"""
from pathlib import Path
import asyncio  # run blocking file I/O in background thread
from rapidfuzz import process, fuzz
from textual.widgets import Input, ListView, ListItem, Static
from textual.containers import Vertical
from palette_dismiss_modal import PaletteDismissModal
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
        self.placeholder = placeholder

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
            # wrap label string in a Static widget for ListItem
            item = ListItem(Static(label))
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

    def _scan_files(self) -> tuple[dict[str, Path], dict[str, Path]]:
        """Scan the workspace for .md files and index their names and content lines."""
        titles: dict[str, Path] = {}
        contents: dict[str, Path] = {}
        for file in Path.cwd().rglob("*.md"):
            name = file.name
            titles[name] = file
            try:
                lines = file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, start=1):
                key = f"{name}:{i}:{line.strip()}"
                contents[key] = file
        return titles, contents

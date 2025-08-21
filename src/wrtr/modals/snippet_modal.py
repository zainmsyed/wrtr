"""
Snippet selection modal - mirrors TemplateModal behavior
"""
from __future__ import annotations

from typing import Iterable
from textual.widgets import Input, ListView, ListItem, Static
from textual.widget import Widget
from textual.events import Key
from rich.text import Text
from rapidfuzz import process, fuzz
from wrtr.modals.palette_dismiss_modal import PaletteDismissModal
from wrtr.services.snippet_service import SnippetService


class SnippetModal(PaletteDismissModal[str | None]):
    def __init__(self, placeholder: str = "Snippet...") -> None:
        super().__init__()
        self.placeholder = placeholder
        self.service = SnippetService()
        self.snippets = {}

    def compose(self) -> Iterable[Widget]:
        from textual.containers import Vertical

        with Vertical(id="dialog", classes="dialog-box search-dialog"):
            yield Input(placeholder=self.placeholder, id="snippet-input")
            yield ListView(id="snippet-results")

    async def on_mount(self) -> None:
        # Load snippets and populate list
        self.snippets = self.service.load_snippets()
        lv = self.query_one(ListView)
        await lv.clear()
        for name in sorted(self.snippets.keys()):
            txt = Text(name, style="bold")
            item = ListItem(Static(txt))
            item.snippet_name = name
            await lv.append(item)
        inp = self.query_one(Input)
        inp.focus()

    async def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id != "snippet-input":
            return
        query = message.value.strip()
        results = self.query_one(ListView)
        await results.clear()
        names = list(self.snippets.keys())
        if not query:
            items = sorted(names)
        else:
            matches = process.extract(query, names, scorer=fuzz.WRatio, limit=50)
            items = [name for name, score, _ in matches if score > 30]

        for name in items:
            txt = Text(name, style="bold")
            item = ListItem(Static(txt))
            item.snippet_name = name
            await results.append(item)

    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        name = getattr(message.item, "snippet_name", None)
        if name:
            self.dismiss(name)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.input.id != "snippet-input":
            return
        lv = self.query_one(ListView)
        if lv.index is not None and 0 <= lv.index < len(lv.children):
            item = lv.children[lv.index]
            name = getattr(item, "snippet_name", None)
            if name:
                self.dismiss(name)
                return
        v = message.value.strip()
        if v and v in self.snippets:
            self.dismiss(v)
            return

    def on_key(self, event: Key) -> None:
        # Dismiss on escape
        key = getattr(event, 'key', None) or getattr(event, 'name', None)
        if key == "escape":
            self.dismiss(None)
            event.stop()
            return

        # Arrow navigation: move focus to list when down pressed in input
        if key in ("down", "up") and isinstance(self.focused, Input):
            results = self.query_one(ListView)
            self.set_focus(results)
            if results.children:
                if key == "down":
                    results.index = 0
                else:
                    results.index = len(results.children) - 1
            event.stop()
            return

        # Let ListView handle navigation when focused
        if key in ("down", "up") and isinstance(self.focused, ListView):
            super().on_key(event)
            return

        # Tab returns focus to input
        if key == "tab":
            inp = self.query_one(Input)
            self.set_focus(inp)
            event.stop()
            return

        super().on_key(event)

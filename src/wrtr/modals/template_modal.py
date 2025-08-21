"""
Template selection modal

Shows a searchable list of templates discovered by TemplateService and returns
the selected template name (string) or None when dismissed.
"""
from __future__ import annotations

from typing import Iterable
from textual.widgets import Input, ListView, ListItem, Static
from textual.widget import Widget
from textual.events import Key
from rapidfuzz import process, fuzz
from wrtr.modals.palette_dismiss_modal import PaletteDismissModal
from wrtr.services.template_service import TemplateService
from rich.text import Text


class TemplateModal(PaletteDismissModal[str | None]):
    def __init__(self, placeholder: str = "Template...") -> None:
        super().__init__()
        self.placeholder = placeholder
        self.service = TemplateService()
        self.templates = {}  # name -> Template

    def compose(self) -> Iterable[Widget]:
        from textual.containers import Vertical

        with Vertical(id="dialog", classes="dialog-box search-dialog"):
            yield Input(placeholder=self.placeholder, id="template-input")
            yield ListView(id="template-results")

    async def on_mount(self) -> None:
        # Load templates and populate list
        self.templates = self.service.load_templates()
        lv = self.query_one(ListView)
        await lv.clear()
        for name in sorted(self.templates.keys()):
            txt = Text(name, style="bold")
            item = ListItem(Static(txt))
            item.template_name = name
            await lv.append(item)
        inp = self.query_one(Input)
        inp.focus()

    async def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id != "template-input":
            return
        query = message.value.strip()
        results = self.query_one(ListView)
        await results.clear()
        names = list(self.templates.keys())
        if not query:
            items = sorted(names)
        else:
            matches = process.extract(query, names, scorer=fuzz.WRatio, limit=50)
            items = [name for name, score, _ in matches if score > 30]

        for name in items:
            txt = Text(name, style="bold")
            item = ListItem(Static(txt))
            item.template_name = name
            await results.append(item)

    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        name = getattr(message.item, "template_name", None)
        if name:
            self.dismiss(name)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        # If user presses Enter and a result is highlighted, accept it
        if message.input.id != "template-input":
            return
        lv = self.query_one(ListView)
        if lv.index is not None and 0 <= lv.index < len(lv.children):
            item = lv.children[lv.index]
            name = getattr(item, "template_name", None)
            if name:
                self.dismiss(name)
                return
        # Fallback: if typed an exact template name, accept it
        v = message.value.strip()
        if v and v in self.templates:
            self.dismiss(v)
            return

    def on_key(self, event) -> None:
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

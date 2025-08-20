"""
Slash Command Palette Modal

Shows a centered input that filters available slash commands as the user types.
Selecting an item (Enter or double-click) or pressing Tab/Arrow keys navigates results.
Returns the selected command name (including leading '/') or None on dismiss.
"""
from typing import Iterable
from textual.widgets import Input, ListView, ListItem, Static
from textual.widget import Widget
from textual.events import Key
from rapidfuzz import process, fuzz
from wrtr.modals.palette_dismiss_modal import PaletteDismissModal
from wrtr.services.slash_command_service import SlashCommandService
from rich.text import Text


class SlashCommandModal(PaletteDismissModal[str | None]):
    """A centered palette for selecting slash commands.

    Dismisses with the chosen command string (e.g. '/today') or None.
    """

    def __init__(self, placeholder: str = "Slash command...") -> None:
        super().__init__()
        self.placeholder = placeholder
        self.commands = {}  # name -> CommandInfo

    def compose(self) -> Iterable[Widget]:
        from textual.containers import Vertical

        with Vertical(id="dialog", classes="dialog-box search-dialog"):
            yield Input(placeholder=self.placeholder, id="slash-input")
            yield ListView(id="slash-results")

    async def on_mount(self) -> None:
        # Load registered commands
        self.commands = SlashCommandService.get_commands()
        # Prepopulate the list with all commands
        lv = self.query_one(ListView)
        await lv.clear()
        for name, info in sorted(self.commands.items()):
            txt = Text()
            txt.append(f"/{name}", style="bold")
            if info.help_text:
                txt.append(" — ")
                txt.append(info.help_text)
            item = ListItem(Static(txt))
            item.command_name = name
            await lv.append(item)
        # Focus the input
        inp = self.query_one(Input)
        inp.focus()

    async def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id != "slash-input":
            return
        query = message.value.strip()
        results = self.query_one(ListView)
        await results.clear()
        if not query:
            # show all
            items = sorted(self.commands.items())
        else:
            names = list(self.commands.keys())
            matches = process.extract(query, names, scorer=fuzz.WRatio, limit=20)
            items = [(name, self.commands[name]) for name, score, _ in matches if score > 30]

        for name, info in items:
            txt = Text()
            txt.append(f"/{name}", style="bold")
            if info.help_text:
                txt.append(" — ")
                txt.append(info.help_text)
            item = ListItem(Static(txt))
            item.command_name = name
            await results.append(item)

    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        # Return the selected command (with leading slash)
        name = getattr(message.item, "command_name", None)
        if name:
            self.dismiss(f"/{name}")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        # If input submits and a result is highlighted, accept it, else if exact match found use it
        if message.input.id != "slash-input":
            return
        lv = self.query_one(ListView)
        if lv.index is not None and 0 <= lv.index < len(lv.children):
            item = lv.children[lv.index]
            name = getattr(item, "command_name", None)
            if name:
                self.dismiss(f"/{name}")
                return
        # Fallback: if typed an exact command name prefixed with '/', accept
        v = message.value.strip()
        if v.startswith('/'):
            cmd = v[1:].split()[0]
            if cmd in self.commands:
                self.dismiss(f"/{cmd}")

    def on_key(self, event: Key) -> None:
        # Dismiss on escape
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
            return

        # Arrow navigation: move focus to list when down pressed in input
        if event.key in ("down", "up") and isinstance(self.focused, Input):
            results = self.query_one(ListView)
            self.set_focus(results)
            if results.children:
                if event.key == "down":
                    results.index = 0
                else:
                    results.index = len(results.children) - 1
            event.stop()
            return

        # Let ListView handle navigation when focused
        if event.key in ("down", "up") and isinstance(self.focused, ListView):
            super().on_key(event)
            return

        # Tab returns focus to input
        if event.key == "tab":
            inp = self.query_one(Input)
            self.set_focus(inp)
            event.stop()
            return

        super().on_key(event)

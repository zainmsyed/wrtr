from __future__ import annotations
from typing import Iterable

from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static

class PaletteModal(Screen):
    """Visual shell only – no opinion on how it closes."""

    BINDINGS = [Binding("escape", "esc", "Close")]

    DEFAULT_CSS = """
    /* top-level dialog wrapper */
    #dialog {
        width: auto;
        height: auto;
        margin: 4 8;
        background: $panel;
        color: $text;
        border: tall $background;
        padding: 1 2;
    }

    /* stretch all buttons the same */
    #dialog Button {
        width: 1fr;
    }

    /* title/question text */
    .modal-title {
        text-style: bold;
        content-align: center middle;
    }

    /* bottom button-row */
    .buttons {
        width: 100%;
        height: auto;
        dock: bottom;
    }
    """

    def __init__(self, title: str | None = None) -> None:
        super().__init__()
        self.title = title

    def compose(self) -> Iterable[Widget]:
        # single wrapper with id="dialog" so our CSS applies
        with Vertical(id="dialog"):
            if self.title:
                yield Static(self.title, classes="modal-title")
            # your subclass will yield its own body (inputs, buttons, etc.)
            yield from self.compose_modal()

    def compose_modal(self) -> Iterable[Widget]:
        yield from ()

    def action_esc(self) -> None:
        """Override to decide what Escape does."""
        self.app.pop_screen()

    def on_key(self, event: "Key") -> None:
        """
        Handle key events.
        We need to handle escape here and stop it, otherwise it will
        bubble up to the app and trigger the global "to_home" action.
        """
        if event.key == "escape":
            self.action_esc()
            event.stop()
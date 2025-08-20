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

    def __init__(self, title: str | None = None) -> None:
        super().__init__()
        self.title = title
        # Apply modal screen styling
        self.add_class("modal-screen")

    def compose(self) -> Iterable[Widget]:
        # single wrapper with id="dialog" so our CSS applies
        with Vertical(id="dialog", classes="dialog-box"):
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
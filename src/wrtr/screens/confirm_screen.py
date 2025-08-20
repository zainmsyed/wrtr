from typing import Iterable
from wrtr.modals.common import ModalScreen, Center, Middle, Vertical, Horizontal, Button, Label, Key
from textual import events
from wrtr.modals.modal_base import EscModal

class ConfirmScreen(EscModal, ModalScreen[bool]):
    """Yes/No confirmation dialog."""

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question
        # Apply modal screen styling
        self.add_class("modal-screen")

    def compose(self) -> Iterable:
        with Center():
            with Middle():
                with Vertical(id="dialog", classes="dialog-box"):
                    yield Label(self.question, id="question", classes="modal-question")
                    with Horizontal(id="buttons", classes="button-row-full"):
                        yield Button("Yes (y)", id="yes")
                        yield Button("No (n)", id="no")

    def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.query_one("#yes").press()
        elif event.key == "n":
            self.query_one("#no").press()

    def on_button_pressed(self, event) -> None:
        self.dismiss(event.button.id == "yes")

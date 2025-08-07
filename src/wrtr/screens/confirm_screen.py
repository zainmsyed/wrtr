from typing import Iterable
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical, Horizontal
from textual.widgets import Button, Label
from textual import events
from wrtr.modals.modal_base import EscModal

class ConfirmScreen(EscModal, ModalScreen[bool]):
    """Yes/No confirmation dialog."""

    CSS = """
    ConfirmScreen { align: center middle; }

    #dialog {
        width: auto;
        max-width: 60;
        height: auto;           /* Prevent vertical stretching */
        background: $background; /* Match the main background color */
        color: $text;
        border: tall $background; /* Blend border with background */
        padding: 1 2;
    }

    #question {
        margin-bottom: 1;   /* 1-row gap above the buttons */
    }

    /* row of buttons: let it size itself */
    #buttons {
        width: auto;          /* shrink-wrap */
        height: auto;
    }

    /* each button only as wide as its text + padding */
    #buttons Button {
        width: auto;
        margin-right: 1;      /* 1-cell gap between buttons */
    }
    """

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question

    def compose(self) -> Iterable:
        with Center():
            with Middle():
                with Vertical(id="dialog"):
                    yield Label(self.question, id="question")
                    with Horizontal(id="buttons"):
                        yield Button("Yes (y)", id="yes")
                        yield Button("No (n)",  id="no")

    def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.query_one("#yes").press()
        elif event.key == "n":
            self.query_one("#no").press()

    def on_button_pressed(self, event) -> None:
        self.dismiss(event.button.id == "yes")

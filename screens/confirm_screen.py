from typing import Iterable
from textual.widget import Widget
from textual.widgets import Button, Label
from textual.containers import Horizontal, Vertical
from palette_dismiss_modal import PaletteDismissModal

class ConfirmScreen(PaletteDismissModal[bool]):
    """Yes/No confirmation – now palette-styled."""

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question

    def on_key(self, event):
        if event.key == "y":
            self.query_one("#yes").press()
        elif event.key == "n":
            self.query_one("#no").press()

    def compose_modal(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(self.question)
            with Horizontal():
                yield Button("Yes (y)", id="yes")
                yield Button("No (n)", id="no")

    def on_button_pressed(self, event) -> None:
        # Dismiss True if user clicked "Yes"
        self.dismiss(event.button.id == "yes")

    def action_esc(self) -> None:
        """Dismiss the modal without routing anywhere."""
        self.dismiss(None)

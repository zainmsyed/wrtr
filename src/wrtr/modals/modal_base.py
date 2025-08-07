from textual.screen import Screen
from textual.events import Key

class EscModal(Screen):
    """
    One-liner mixin: any modal that inherits from this pops itself
    when Esc is pressed.
    """
    def on_key(self, event: Key) -> None:
        """Handle key events."""
        if event.key == "escape":
            if len(self.app._screen_stack) > 1:  # Ensure there is more than one screen on the stack
                self.app.pop_screen()
            else:
                self.app.log("Cannot pop the last screen from the stack.")
            event.stop()  # Kill the event so nothing else sees it

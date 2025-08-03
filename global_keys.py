from textual.app import App
from textual.screen import Screen
from textual.events import Key

class GlobalKeyHandler:
    """
    Mixin that gives *every* screen the same Esc behaviour:
      - If a modal/screen is on top → pop it
      - Otherwise let the App decide (usually back to Home)
    """
    def on_key(self, event: Key) -> None:
        # Let the active screen handle the key first
        if isinstance(self, Screen) and self.app.screen is self:
            return

        if event.key == "escape":
            # Handle Escape key globally
            if isinstance(self, Screen) and self.app.screen is not self:
                self.app.pop_screen()
                event.stop()
                return

            if isinstance(self, App):
                # Check if spellcheck mode is active in the editor
                if hasattr(self.app, 'editor') and self.app.editor._spellcheck_active:
                    self.app.editor._exit_spellcheck()
                    event.stop()
                    return

                self.action_to_home()
                event.stop()
                return

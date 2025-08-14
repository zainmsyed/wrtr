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
            # If a modal/screen is pushed on top, pop it first
            try:
                if isinstance(self, App) and len(self.screen_stack) > 1:
                    self.pop_screen()
                    event.stop()
                    return
                # If we're in a Screen (and not the active one), pop it
                if isinstance(self, Screen) and self.app.screen is not self:
                    self.app.pop_screen()
                    event.stop()
                    return
            except Exception:
                # If popping fails, fall through to other handlers
                pass

            # Handle spellcheck exit if active (App-level)
            if isinstance(self, App):
                if hasattr(self, 'editor') and getattr(self.editor, '_spellcheck_active', False):
                    # Prefer the editor's own exit method if available
                    exit_fn = getattr(self.editor, '_exit_spellcheck', None)
                    if callable(exit_fn):
                        exit_fn()
                        event.stop()
                        return
            # No modal to pop and no spellcheck to exit: let App decide what to do next
            return

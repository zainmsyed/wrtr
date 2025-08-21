"""
Modal to collect values for snippet variables.

Follows the same behaviour as TemplateVariablesModal.
"""
from __future__ import annotations

from typing import Iterable, Dict, List
from textual.widgets import Input, Button, Label
from textual.containers import Vertical, Horizontal
from wrtr.modals.palette_dismiss_modal import PaletteDismissModal


class SnippetVariablesModal(PaletteDismissModal[Dict[str, str] | None]):
    def __init__(self, variables: List[str]) -> None:
        super().__init__()
        self.variables = variables

    def compose(self) -> Iterable:
        with Vertical(id="dialog", classes="dialog-box"):
            yield Label("Fill snippet variables:")
            # Create an Input per variable
            for v in self.variables:
                yield Label(v)
                yield Input(placeholder=v, id=f"snippet-var-{v}")

            with Horizontal(id="buttons", classes="button-row-full"):
                # use lower-case labels to match app conventions and show the shortcut
                yield Button("apply (ctrl+a)", id="apply")
                yield Button("cancel (ctrl+c)", id="cancel")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "apply":
            result = {}
            for v in self.variables:
                inp = self.query_one(f"#snippet-var-{v}", Input)
                result[v] = inp.value
            self.dismiss(result)
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        # Keep Escape behavior from PaletteDismissModal (dismiss)
        key = getattr(event, 'key', None) or getattr(event, 'name', None)
        # Some terminals set a 'control' attribute; handle common cases
        ctrl = bool(
            getattr(event, 'control', False)
            or getattr(event, 'ctrl', False)
            or getattr(event, 'control_key', False)
        )

        # Normalize the key/name to a lower-case string for matching
        key_str = (str(key).lower() if key is not None else '')
        # Normalize separators to underscores for patterns like 'ctrl_a' or 'ctrl+a'
        key_norm = key_str.replace('+', '_').replace('-', '_')

        def is_ctrl_letter(letter: str) -> bool:
            # Match when the event explicitly signals a control modifier + letter
            if ctrl and key_norm == letter:
                return True
            # Match common combined-name forms emitted by different terminals/runtimes
            if key_norm in (f'ctrl_{letter}', f'control_{letter}', f'ctrl{letter}'):
                return True
            if key_norm in (f'ctrl+{letter}', f'control+{letter}'):
                return True
            return False

        # Trigger apply only on Ctrl+A (no plain 'a' to avoid accidental submits)
        if is_ctrl_letter('a'):
            result = {}
            for v in self.variables:
                inp = self.query_one(f"#snippet-var-{v}", Input)
                result[v] = inp.value
            self.dismiss(result)
            try:
                event.stop()
            except Exception:
                pass
            return

        # Cancel only on Ctrl+C
        if is_ctrl_letter('c'):
            self.dismiss(None)
            try:
                event.stop()
            except Exception:
                pass
            return

        # Otherwise, fallback to default handling
        try:
            super().on_key(event)
        except Exception:
            pass

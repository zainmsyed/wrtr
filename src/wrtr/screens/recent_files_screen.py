from pathlib import Path
from textual.widgets import ListView, ListItem, Label, Static
from textual.screen import ModalScreen
from wrtr.services.recent_files_service import RecentFilesService
from wrtr.services.keybinding_service import KeybindingService
from textual.containers import Vertical, Center, Middle
from textual.events import Key

class RecentFilesScreen(ModalScreen[Path | None]):
    """Modal that shows ≤ 5 recent files."""

    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(self) -> None:
        super().__init__()
        # Apply modal screen styling
        self.add_class("modal-screen")

    def compose(self):
        """Build the list of up to MAX recent files."""
        items = []
        # Use get_recent to fetch up to MAX valid paths
        from rich.text import Text

        def _trim(s: str, max_len: int = 80) -> str:
            s = s.strip().replace("\n", " ")
            return s if len(s) <= max_len else s[: max_len - 1].rstrip() + "…"

        for p in RecentFilesService.get_recent():
            txt = Text()
            txt.append(p.name, style="bold")
            txt.append("\n")
            txt.append(str(p.parent), style="dim")
            item = ListItem(Static(txt))
            # mirror Search/References: attach path for selection logic
            item.path = p
            items.append(item)
        if not items:
            items.append(ListItem(Label("No recent files", classes="dim")))
        
        with Center():
            with Middle():
                yield Vertical(
                    ListView(*items, id="recent_list"),
                    id="recent-box",
                    classes="dialog-box-large"
                )

    def on_mount(self) -> None:
        """Remember the widget that had focus before the modal was shown.

        This lets us restore focus after dismissing the modal so app-level
        actions that depend on focus (like toggling preview) behave
        consistently.
        """
        try:
            self._previous_focus = self.app.focused
        except Exception:
            self._previous_focus = None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Prefer the attached Path object; fall back to name if present
        path = getattr(event.item, "path", None)
        if path:
            self.dismiss(Path(path))
            return
        if getattr(event.item, "name", None):
            self.dismiss(Path(event.item.name))

    async def on_key(self, event: Key) -> None:
        """Handle Escape explicitly so the modal dismisses and the key event
        does not propagate to the App/global handler (which could pop the
        HomeScreen underneath).

        Also support Ctrl+Shift+M here: dismiss the modal and toggle the
        markdown preview in the focused editor (mirrors global binding).
        """
        key = event.key or getattr(event, 'name', None)

        if key == "escape":
            # Dismiss with None (no selection) and stop propagation
            self.dismiss(None)
            event.stop()
            return

        # If the user pressed Ctrl+M while the recent-files modal is open,
        # close the modal and forward the request to load the selected file
        # into the secondary editor (editor_b) using the centralized
        # KeybindingService.
        if key == "ctrl+m":
            # If there's a selected item in the ListView, ask the
            # KeybindingService to load it into editor_b. This centralizes
            # the behavior and performs file I/O on a background thread.
            try:
                lv = self.query_one("#recent_list")
                idx = lv.index
                if idx is not None and 0 <= idx < len(lv.children):
                    item = lv.children[idx]
                    # Prefer the attached Path set on the item; fall back to name
                    path_obj = getattr(item, "path", None)
                    if path_obj:
                        # Ensure it's a Path instance
                        path = Path(path_obj) if not isinstance(path_obj, Path) else path_obj
                        # Close modal before manipulating editors
                        self.dismiss(None)
                        # Trigger the registered action (async)
                        await KeybindingService.trigger("load_in_editor_b", self.app, path)
                        event.stop()
                        return
                    name = getattr(item, "name", None)
                    if name:
                        path = Path(name)
                        self.dismiss(None)
                        await KeybindingService.trigger("load_in_editor_b", self.app, path)
                        event.stop()
                        return
            except Exception:
                try:
                    self.dismiss(None)
                except Exception:
                    pass
                event.stop()
                return

        # Do not call super().on_key (ModalScreen doesn't implement it).
        # Returning lets Textual continue normal event dispatching.
        return

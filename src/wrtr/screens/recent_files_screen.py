from pathlib import Path
from textual.widgets import ListView, ListItem, Label
from textual.screen import ModalScreen
from wrtr.services.recent_files_service import RecentFilesService
from wrtr.services.keybinding_service import KeybindingService
from textual.containers import Center, Vertical
from textual.events import Key

class RecentFilesScreen(ModalScreen[Path | None]):
    """Modal that shows ≤ 5 recent files."""

    BINDINGS = [("escape", "dismiss(None)")]
    CSS = """
    RecentFilesScreen {
        align: center middle;      /* center the modal */
        border: none;              /* remove border */
        outline: none;             /* remove outline */
    }

    #recent-box {
        width: 100;                /* increase width */
        height: auto;
        max-height: 30;
    }

    #recent-box ListView {
        width: 100%;
        height: auto;
        max-height: 25;
        padding: 2;                /* add padding to the file list */
    }
    #recent-box ListItem {
        margin-bottom: 1;
    }
    """

    def compose(self):
        """Build the list of up to MAX recent files."""
        items = []
        # Use get_recent to fetch up to MAX valid paths
        for p in RecentFilesService.get_recent():
            items.append(
                ListItem(
                    Label(str(p), classes="recent-item"),
                    name=str(p),
                )
            )
        if not items:
            items.append(ListItem(Label("No recent files", classes="dim")))
        yield Vertical(
            ListView(*items, id="recent_list"),
            id="recent-box"
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
        if event.item.name:
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

        # If the user pressed Ctrl+Shift+M while the recent-files modal is open,
        # close the modal and forward the request to the App-level preview
        # toggler so the preview state can be changed even when a modal is active.
        if key == "ctrl+shift+m":
            # If there's a selected item in the ListView, ask the
            # KeybindingService to load it into editor_b. This centralizes
            # the behavior and performs file I/O on a background thread.
            try:
                lv = self.query_one("#recent_list")
                idx = lv.index
                if idx is not None and 0 <= idx < len(lv.children):
                    item = lv.children[idx]
                    name = getattr(item, "name", None)
                    if name:
                        path = Path(name)
                        # Close modal before manipulating editors
                        self.dismiss(None)
                        # Trigger the registered action (async)
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

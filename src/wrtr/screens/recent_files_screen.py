from pathlib import Path
from textual.widgets import ListView, ListItem, Label
from textual.screen import ModalScreen
from wrtr.services.recent_files_service import RecentFilesService
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
            # If there's a selected item in the ListView, open it in editor_b
            try:
                lv = self.query_one("#recent_list")
                idx = lv.index
                # Defensive: ensure index is valid and the item has a name
                if idx is not None and 0 <= idx < len(lv.children):
                    item = lv.children[idx]
                    name = getattr(item, 'name', None)
                    if name:
                        path = Path(name)
                        try:
                            content = path.read_text(encoding="utf-8")
                        except Exception:
                            # If file unreadable, fall back to dismiss only
                            self.dismiss(None)
                            event.stop()
                            return

                        app = self.app
                        # Close modal before manipulating editors
                        self.dismiss(None)

                        # Ensure editor panes are visible and resized
                        try:
                            app.query_one("#editor_a").visible = True
                            app.query_one("#editor_b").visible = True
                            app.layout_manager.layout_resize()
                        except Exception:
                            pass

                        # Load into editor_b (mirror FileBrowser behavior)
                        try:
                            editor = app.query_one("#editor_b")
                            editor.load_text(content)
                            editor.set_path(path)
                            editor.focus()
                            RecentFilesService.add(path)
                        except Exception:
                            pass

                        event.stop()
                        return
            except Exception:
                # If anything goes wrong, just dismiss and stop the event
                try:
                    self.dismiss(None)
                except Exception:
                    pass
                event.stop()
                return

        # Do not call super().on_key (ModalScreen doesn't implement it).
        # Returning lets Textual continue normal event dispatching.
        return

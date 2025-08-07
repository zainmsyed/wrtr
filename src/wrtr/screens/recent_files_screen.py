from pathlib import Path
from textual.widgets import ListView, ListItem, Label
from textual.screen import ModalScreen
from wrtr.services.recent_files_service import RecentFilesService
from textual.containers import Center, Vertical

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

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name:
            self.dismiss(Path(event.item.name))

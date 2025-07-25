from pathlib import Path
from textual.widgets import ListView, ListItem, Label
from textual.screen import ModalScreen
from recent_manager import RecentManager

class RecentFilesScreen(ModalScreen[Path | None]):
    """Modal that shows ≤ 5 recent files."""

    BINDINGS = [("escape", "dismiss(None)")]

    def compose(self):
        """Build the list of up to MAX recent files."""
        items = []
        # Use get_recent to fetch up to MAX valid paths
        for p in RecentManager.get_recent():
            items.append(
                ListItem(
                    Label(str(p), classes="recent-item"),
                    name=str(p),
                )
            )
        if not items:
            items.append(ListItem(Label("No recent files", classes="dim")))
        yield ListView(*items, id="recent_list")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name:
            self.dismiss(Path(event.item.name))

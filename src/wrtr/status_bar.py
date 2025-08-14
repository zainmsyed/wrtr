"""
Module: Editor Status Bar
Shows filename, save status and word count.
"""
from textual.widgets import Static
from textual.reactive import reactive
from pathlib import Path
from typing import Optional, List
from rich.console import Group
from rich.panel import Panel
from rich import box
from rich.table import Table
from rich.text import Text

class EditorStatusBar(Static):
    """A tiny status bar that lives inside each MarkdownEditor."""

    file_path: reactive[Path | None] = reactive(None)
    saved: reactive[bool] = reactive(True)
    spellcheck_mode: reactive[bool] = reactive(False)
    loading: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = 1
        self.styles.dock = "bottom"
        self.styles.background = "rgb(40,40,40)"
        self.styles.color = "rgb(220,220,220)"
        self.styles.padding = (0, 1)
        # Spellcheck state
        self.current_word: Optional[str] = None
        self.suggestions: List[str] = []
        self.progress: tuple[int, int] = (0, 0)
        # Loading indicator for spellcheck
        self.loading = False

    def _word_count(self) -> int:
        """Naïve word counter."""
        return len(self.parent.text.split())

    def _render_spellcheck_text(self) -> Panel:
        """Compose the spellcheck status panel."""
        # If still loading, show a simple indicator
        if self.loading:
            from rich.text import Text as _Text
            return _Text("Checking spelling...", style="italic yellow")
        current, total = self.progress

        # Build a table of suggestions
        tbl = Table.grid(padding=(0, 1))
        tbl.add_column(justify="right", style="cyan", no_wrap=True)
        tbl.add_column(style="white")

        if self.suggestions:
            for idx, suggestion in enumerate(self.suggestions[:5], start=1):
                tbl.add_row(f"{idx}.", Text(f"{suggestion} (ctrl+{idx})", style="white"))
        else:
            tbl.add_row("-", Text("(no suggestions)", style="dim"))

        # Header with current word + progress
        header = Text(
            f"Misspelled: '{self.current_word}' ({current}/{total})",
            style="bold red",
        )

        # Navigation and actions hints
        nav_actions = Text.from_markup(
            "[bold green]Navigation:[/bold green]\n"
            "  f3 → next  |  shift+f3 → prev\n"
            "\n"
            "[bold cyan]Actions:[/bold cyan]\n"
            "  ctrl+a → add to dictionary |  ctrl+i → ignore\n"
            "  esc → exit",
            style="white",
        )

        # Combine all components into a Group with spacing
        group = Group(
            header,
            Text(""),  # spacer
            tbl,
            Text(""),  # spacer
            nav_actions,
        )

        # Return a Panel containing the Group
        return Panel(
            group,
            title="spellcheck",
            border_style="magenta",
            box=box.DOUBLE,
            padding=(1, 2),
            width=None,  # Dynamically adjust to full pane width
        )

    def _render_text(self) -> Panel | Text:
        """Compose the appropriate status renderable based on mode."""
        if self.spellcheck_mode:
            return self._render_spellcheck_text()
        # Else: return the plain string status wrapped in Text
        name = self.file_path.name if self.file_path else "[No File]"
        status = "● Saved" if self.saved else "● Modified"
        words = self._word_count()
        return Text(f"{name}  |  {status}  |  {words} words", style="white")

    def watch_file_path(self) -> None:
        self.update(self._render_text())

    def watch_saved(self) -> None:
        self.update(self._render_text())

    def watch_spellcheck_mode(self) -> None:
        # Adjust height based on mode
        self.styles.height = 20 if self.spellcheck_mode else 1
        self.update(self._render_text())

    def on_mount(self) -> None:
        self.update(self._render_text())

    def refresh_stats(self) -> None:
        """Recalculate everything and redraw."""
        self.update(self._render_text())

    def set_spellcheck_info(self, word: Optional[str], suggestions: List[str], progress: tuple[int, int]):
        """Update spellcheck information and clear loading state."""
        # Mark loading complete and update info
        self.loading = False
        self.current_word = word
        self.suggestions = suggestions
        self.progress = progress
        if self.spellcheck_mode:
            self.update(self._render_text())

    def enter_spellcheck_mode(self):
        """Enter spellcheck mode and show loading indicator."""
        self.spellcheck_mode = True
        self.loading = True  # start in loading state

    def exit_spellcheck_mode(self):
        """Exit spellcheck mode."""
        self.spellcheck_mode = False
        self.current_word = None
        self.suggestions = []
        self.progress = (0, 0)

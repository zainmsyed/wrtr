"""
Home Screen: initial menu for Terminal Writer Application
"""
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.app import ComposeResult
from wrtr.screens.recent_files_screen import RecentFilesScreen

ASCII_ART = r"""
██╗----██╗██████╗-████████╗██████╗-
██║----██║██╔══██╗╚══██╔══╝██╔══██╗
██║-█╗-██║██████╔╝---██║---██████╔╝
██║███╗██║██╔══██╗---██║---██╔══██╗
╚███╔███╔╝██║--██║---██║---██║--██║
-╚══╝╚══╝-╚═╝--╚═╝---╚═╝---╚═╝--╚═╝
"""

class HomeScreen(Screen):
    """The home screen with ASCII art and main menu options."""

    # 1. Tell Textual to center the screen’s own children
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }

    #logo {
        width: auto;          /* shrink-wrap the ASCII art */
        text-align: center;   /* center the text inside it */
        padding: 2 0;         /* 2 blank lines above & below the art */
    }

    HomeScreen Button {
        width: 35;           /* any fixed width you like */
        text-align: center;  /* center the label inside the button */
        content-align: center middle; /* fully centers in both axes */
    }
    """

    BINDINGS = [
        ("up",   "focus_previous",    "Focus Previous"),
        ("down", "focus_next",        "Focus Next"),
        ("n",    "new_file",          "New File"),
        ("r",    "recent_files",      "Recent Files"),
        ("b",    "browse_files",      "Browse Files"),
        ("q",    "quit",              "Quit"),
    ]

    def compose(self) -> ComposeResult:
        # 2. Yield the widgets directly – no extra containers
        yield Static(ASCII_ART, id="logo")
        yield Button("New File (n)", id="new_file")
        yield Button("Recent Files (r)", id="recent_files", classes="home_button")
        yield Button("Browse Files (b)", id="browse_files")
        yield Button("Quit (q)", id="quit")

    async def on_mount(self) -> None:
        """Focus the first button for keyboard navigation."""
        try:
            new_file_button = self.query_one("#new_file")
            self.set_focus(new_file_button)
        except Exception:
            # If button not found, just continue without focusing
            pass

    def action_focus_previous(self) -> None:
        """Move focus to the previous button."""
        self.focus_previous()

    def action_focus_next(self) -> None:
        """Move focus to the next button."""
        self.focus_next()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "new_file":
            self.app.action_new_file()
        elif button_id == "recent_files":
            # Show Recent Files modal in a worker and open chosen file
            async def show_recent() -> None:
                chosen = await self.app.push_screen_wait(RecentFilesScreen())
                if chosen:
                    await self.app.action_open_file(chosen)
            self.app.run_worker(show_recent(), exclusive=True)
        elif button_id == "browse_files":
            self.app.pop_screen()
        elif button_id == "quit":
            self.app.exit()

    # NEW: let the key do exactly what the button does
    def action_new_file(self)     -> None: self.query_one("#new_file").press()
    def action_recent_files(self) -> None: self.query_one("#recent_files").press()
    def action_browse_files(self) -> None: self.query_one("#browse_files").press()
    def action_quit(self)         -> None: self.query_one("#quit").press()

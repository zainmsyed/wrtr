"""
Entry point for Terminal Writer Application
"""
import sys
import os
from textual.app import App, ComposeResult, ScreenStackError  # for handling screen stack errors
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Button, DirectoryTree
from screens.home_screen import HomeScreen
from screens.recent_files_modal import RecentFilesModal  # NEW

from file_browser import FileBrowser
from editor import MarkdownEditor
from search import GlobalSearchScreen
from workspace import WorkspaceManager
from theme import ThemeManager
from clipboard import ClipboardManager
from pathlib import Path, PurePath                       # already imported

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Running in normal Python environment
        return os.path.join(os.path.dirname(__file__), relative_path)
from screens.save_as_screen import SaveAsScreen  # NEW
from textual.widgets import TextArea  # for save shortcut focus handling
from global_keys import GlobalKeyHandler
from recent_manager import RecentManager
import shutil


class wrtr(GlobalKeyHandler, App):
    """
    Main Textual application class for Terminal Writer.
    """
    # Use default styling; remove custom CSS_PATH to enable built-in widget styles
    # CSS_PATH = "styles.css"  # placeholder for styling
    BINDINGS = [
        ("ctrl+f", "show_search", "Search"),
        ("ctrl+1", "switch_workspace('1')", "Workspace 1"),
        ("ctrl+2", "switch_workspace('2')", "Workspace 2"),
        ("tab", "focus_next", "Cycle Pane"),
        ("ctrl+n", "new_file", "New File"),
        ("delete", "delete_item", "Delete"),
        ("escape", "to_home", "Back to Home"),
        ("ctrl+t", "toggle_browser", "Toggle Browser"),
        ("ctrl+w", "close_pane", "Close Pane"),
        ("ctrl+s", "save_file", "Save"),

        # keys that belong to the HomeScreen
        ("n", "home_new_file",     "New File"),
        ("r", "home_recent_files", "Recent Files"),
        ("b", "home_browse_files", "Browse Files"),
        ("q", "home_quit",         "Quit"),
    ]

    DEFAULT_DIR = Path(__file__).with_suffix('').parent / "wrtr"
    SEED_DIR = Path(get_resource_path("docs"))

    def __init__(self):
        super().__init__()
        self.workspace_manager = WorkspaceManager()
        self.theme_manager = ThemeManager()

    def compose(self) -> ComposeResult:
        yield Header()
        # three-column layout: file browser + two editor panes
        with Horizontal():
            yield FileBrowser(id="file-browser")
            yield MarkdownEditor(id="editor_a")
            yield MarkdownEditor(id="editor_b")
        yield Footer()

    def on_mount(self) -> None:
        # 1st-run folder creation
        self.DEFAULT_DIR.mkdir(exist_ok=True)

        # Copy seed documents if they exist
        if self.SEED_DIR.exists():
            for md_file in self.SEED_DIR.glob("*.md"):
                shutil.copy(md_file, self.DEFAULT_DIR / md_file.name)

        # Refresh the DirectoryTree to show the new folder
        tree = self.query_one(DirectoryTree)
        tree.path = self.DEFAULT_DIR

        # Restore saved theme (or stay on Textual default)
        saved = ThemeManager.load()
        if saved:
            self.theme = saved

        # Push a new HomeScreen instance to keep the stack valid
        self.push_screen(HomeScreen())
        # Default to two-pane layout: hide editor_b and size browser/editor_a
        browser = self.query_one("#file-browser")
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")
        editor_b.visible = False
        browser.styles.width = "25%"
        editor_a.styles.width = "75%"
        # ensure editors never collapse entirely on narrow terminals
        editor_a.styles.min_width = 1
        editor_b.styles.min_width = 1

    def watch_theme(self, new_theme: str) -> None:
        """Called by Textual every time `self.theme` changes."""
        ThemeManager.save(new_theme)

    async def action_show_search(self) -> None:
        """Show the global fuzzy search overlay."""
        await self.push_screen(GlobalSearchScreen())

    async def action_switch_workspace(self, number: str) -> None:
        # TODO: switch to workspace number
        pass

    def action_new_file(self) -> None:
        """Handle creation of a new file: collapse browser and show a full-width editor."""
        # Pop HomeScreen (if present) to reveal main layout
        try:
            self.pop_screen()
        except Exception:
            pass
        # Get layout widgets
        browser = self.query_one("#file-browser")
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")
        # Collapse file browser
        browser.visible = False
        browser.styles.display = "none"
        browser.styles.width = "0%"
        # Ensure primary editor is visible and properly reset for new file
        editor_a.visible = True
        editor_a.styles.width = "100%"
        editor_a.clear_status()  # This properly resets the file path and content
        # Hide secondary editor
        editor_b.visible = False
        editor_b.styles.display = "none"
        editor_b.styles.width = "0%"
        # Focus the primary editor
        editor_a.focus()

    async def action_delete_item(self) -> None:
        # TODO: delete selected file or folder
        pass

    def action_to_home(self) -> None:
        """Pop everything until we are back at the main view, then push a clean HomeScreen."""
        # Pop all screens to get back to the base
        while len(self.screen_stack) > 1:
            self.pop_screen()
        
        # Now, push a fresh HomeScreen
        self.push_screen(HomeScreen())

    def action_toggle_browser(self) -> None:
        """Toggle the visibility of the file browser pane."""
        # Query the browser and editors
        browser = self.query_one("#file-browser")
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")
        if not browser:
            return
        # Toggle visibility
        browser.visible = not browser.visible
        if not browser.visible:
            # Collapse browser entirely
            browser.styles.display = "none"
            browser.styles.width = "0%"
            # Expand editors to fill available space
            if editor_b.visible:
                editor_a.styles.width = "50%"
                editor_b.styles.width = "50%"
            elif editor_a.visible:
                editor_a.styles.width = "100%"
            return
        # Restore browser display and widths when shown
        browser.styles.display = "block"
        if editor_b.visible:
            browser.styles.width = "25%"
            editor_a.styles.width = "37.5%"
            editor_b.styles.width = "37.5%"
        elif editor_a.visible:
            browser.styles.width = "25%"
            editor_a.styles.width = "75%"
            # Hide second editor when it's unused
            editor_b.styles.display = "none"
            editor_b.styles.width = "0%"

    def _reflow_layout(self) -> None:
        """Resize exactly like Ctrl-T does."""
        browser   = self.query_one("#file-browser")
        editor_a  = self.query_one("#editor_a")
        editor_b  = self.query_one("#editor_b")

        # 1. Browser
        if not browser.visible:
            browser.styles.display = "none"
            browser.styles.width   = "0%"
        else:
            browser.styles.display = "block"
            browser.styles.width   = "25%"

        # 2. Hide invisible editors
        for e in (editor_a, editor_b):
            if not e.visible:
                e.styles.display = "none"
                e.styles.width   = "0%"
            else:
                e.styles.display = "block"

        # 3. Split the remaining space
        if editor_a.visible and editor_b.visible:
            editor_a.styles.width = editor_b.styles.width = "37.5%"
        elif editor_a.visible:
            editor_a.styles.width = "75%" if browser.visible else "100%"
        elif editor_b.visible:
            editor_b.styles.width = "75%" if browser.visible else "100%"

    def _collapse_editor(self, editor: MarkdownEditor) -> None:
        """Truly collapse the editor so the remaining one fills the row."""
        editor.styles.width  = "0%"
        editor.styles.display = "none"

    def _layout_resize(self) -> None:
        """Let Textual re-calculate widths cleanly."""
        browser = self.query_one("#file-browser")
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")

        # 1️⃣  Browser width
        browser.styles.width = "25%" if browser.visible else "0%"
        browser.styles.display = "block" if browser.visible else "none"

        # 2️⃣  Editors – collapse or expand
        for e in (editor_a, editor_b):
            e.styles.display = "block" if e.visible else "none"
            e.styles.width = (
                "37.5%" if editor_a.visible and editor_b.visible else
                ("75%" if browser.visible else "100%")
            )

    async def action_close_pane(self) -> None:
        """Close the focused pane and let the other fill the row."""
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")

        if self.focused is editor_b:
            editor_b.remove()
        elif self.focused is editor_a and editor_b.visible:
            editor_a.text = editor_b.text
            editor_a.set_path(editor_b._saved_path)
            editor_b.remove()
        else:
            editor_a.clear_status()

        editor_a.focus()

        # Force repaint to clear any ghost column
        self.app.refresh()

    async def on_file_browser_file_open(self, event: FileBrowser.FileOpen) -> None:
        path = event.path
        content = Path(path).read_text(encoding="utf-8")

        # 1️⃣  Always open into the **focused** editor
        focused = self.focused
        if isinstance(focused, MarkdownEditor):
            target_editor = focused
        else:
            target_editor = self.query_one("#editor_a")

        # 2️⃣  Load the file (no hiding anything)
        target_editor.load_text(content)
        target_editor.set_path(Path(path))
        target_editor.focus()

        # 🔑  single layout recalculation
        self._layout_resize()

        RecentManager.add(Path(path))

    async def action_open_file(self, path) -> None:
        """Open a file at given path in the focused editor."""
        # Dismiss HomeScreen if present to reveal main layout
        try:
            if hasattr(self, '_screen_stack') and len(self._screen_stack) > 1:
                await self.pop_screen()
        except Exception:
            pass
        
        from pathlib import Path as _Path
        p = _Path(path)
        # If file is missing, try the default data directory, then bundled docs
        if not p.exists():
            # 1. Check in the app's data folder (DEFAULT_DIR)
            default_path = self.DEFAULT_DIR / p.name
            if default_path.exists():
                p = default_path
            else:
                # 2. Fall back to bundled docs folder
                bundled = Path(__file__).parent / "docs" / p.name
                if bundled.exists():
                    p = bundled
        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            content = ""
        
        # Show browser and editors
        browser = self.query_one("#file-browser")
        editor_a = self.query_one("#editor_a")
        editor_b = self.query_one("#editor_b")
        
        browser.visible = True
        editor_a.visible = True
        
        # Load file into primary editor
        editor_a.load_text(content)
        editor_a.set_path(p)
        editor_a.focus()
        self._layout_resize()

        RecentManager.add(p)

    def action_save_file(self) -> None:
        """Save the focused editor’s content via Save-As dialog."""
        focused = self.focused
        # Determine MarkdownEditor instance from focus (editor or inner TextArea)
        if isinstance(focused, MarkdownEditor):
            editor = focused
        elif isinstance(focused, TextArea) and isinstance(focused.parent, MarkdownEditor):
            editor = focused.parent
        else:
            return

        # If the file is new (no saved path), trigger Save As dialog
        if editor._saved_path is None:
            self.run_worker(self._do_save(editor), exclusive=True)
        else:
            # Save directly if the file has a path
            editor._saved_path.write_text(editor.text)
            editor.status_bar.saved = True
            self.query_one("#file-browser").reload()
            RecentManager.add(editor._saved_path)

    async def _do_save(self, editor: MarkdownEditor) -> None:
        result = await self.switch_screen_wait(
            SaveAsScreen(
                default_filename=(editor._saved_path.name if editor._saved_path else "untitled.md")  # Default to .md extension
            )
        )
        if result is None:
            return

        try:
            result.write_text(editor.text, encoding="utf-8")

            # ⭐ keep the path & live word-count in the bar
            editor.set_path(result)
            editor.status_bar.refresh_stats()

            # Commented out save toast notification for quieter operation
            # self.notify(f"Saved → {result}", severity="information")
            self.query_one("#file-browser").reload()

            RecentManager.add(result)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    async def on_file_browser_file_create(self, event: FileBrowser.FileCreate) -> None:
        """Create the requested file and reload the tree."""
        target = event.parent_dir / event.name
        if target.exists():
            self.notify("File already exists!", severity="warning")
            return
        target.touch()                # create empty file
        target.write_text(f"# {event.name}\n\n", encoding="utf-8")
        self.notify(f"Created → {target.name}", severity="information")
        self.query_one("#file-browser").reload()
        RecentManager.add(target)

    async def on_file_browser_file_delete(self, event: FileBrowser.FileDelete) -> None:
        """Delete the requested file/folder and reload the tree."""
        path = event.path
        try:
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            self.notify(f"Deleted → {path.name}", severity="information")
            self.query_one("#file-browser").reload()
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")


    # ---------------------------------------------------------
    #  Home-screen helpers
    # ---------------------------------------------------------
    def _home_button_press(self, button_id: str) -> None:
        """Find the button inside the current HomeScreen and press it."""
        if isinstance(self.screen, HomeScreen):
            if button_id == "recent_files":
                async def _show():
                    chosen = await self.push_screen_wait(RecentFilesModal())
                    if chosen:
                        await self.action_open_file(chosen)
                self.run_worker(_show(), exclusive=True)
            else:
                button = self.screen.query_one(f"#{button_id}", Button)
                button.press()

    def action_home_new_file(self)     -> None: self._home_button_press("new_file")
    def action_home_recent_files(self) -> None: self._home_button_press("recent_files")
    def action_home_browse_files(self) -> None: self._home_button_press("browse_files")
    def action_home_quit(self)         -> None: self._home_button_press("quit")

    async def switch_screen_wait(self, screen):
        """Pop the current screen and push a new one atomically, waiting for its result."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
        return await self.push_screen_wait(screen)


if __name__ == "__main__":
    wrtr().run()

"""
layout_manager.py

This module defines `LayoutManager` to centralize layout logic for the Terminal Writer application.
"""

class LayoutManager:
    """Handles pane visibility and sizing for file browser and editor panes."""
    def __init__(self, app):
        self.app = app

    def initialize(self) -> None:
        """Initial two-pane layout on mount: hide secondary editor and size browser/editor A."""
        browser = self.app.query_one("#file-browser")
        editor_a = self.app.query_one("#editor_a")
        editor_b = self.app.query_one("#editor_b")
        # Hide secondary editor pane
        editor_b.visible = False
        # Set widths
        browser.styles.width = "25%"
        editor_a.styles.width = "75%"
        # Prevent collapse
        editor_a.styles.min_width = 1
        editor_b.styles.min_width = 1

    def new_file(self) -> None:
        """Layout for creating a new file: collapse browser and show full-width editor A."""
        browser = self.app.query_one("#file-browser")
        editor_a = self.app.query_one("#editor_a")
        editor_b = self.app.query_one("#editor_b")
        # Collapse file browser
        browser.visible = False
        browser.styles.display = "none"
        browser.styles.width = "0%"
        # Full-width primary editor
        editor_a.visible = True
        editor_a.styles.width = "100%"
        editor_a.clear_status()
        # Hide secondary editor
        editor_b.visible = False
        editor_b.styles.display = "none"
        editor_b.styles.width = "0%"
        # Focus editor A
        editor_a.focus()

    def toggle_browser(self) -> None:
        """Toggle the file browser pane visibility and adjust editor widths."""
        browser = self.app.query_one("#file-browser")
        editor_a = self.app.query_one("#editor_a")
        editor_b = self.app.query_one("#editor_b")
        if not browser:
            return
        # Toggle visibility
        browser.visible = not browser.visible
        if not browser.visible:
            # Collapse browser
            browser.styles.display = 'none'
            browser.styles.width = '0%'
            # Expand editors
            if editor_b.visible:
                editor_a.styles.width = '50%'
                editor_b.styles.width = '50%'
            elif editor_a.visible:
                editor_a.styles.width = '100%'
            return
        # Restore browser
        browser.styles.display = 'block'
        # Adjust sizes when shown
        if editor_b.visible:
            browser.styles.width = '25%'
            editor_a.styles.width = '37.5%'
            editor_b.styles.width = '37.5%'
        elif editor_a.visible:
            browser.styles.width = '25%'
            editor_a.styles.width = '75%'
            # Hide secondary editor pane
            editor_b.styles.display = 'none'
            editor_b.styles.width = '0%'

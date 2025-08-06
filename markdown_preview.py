"""
Module: Markdown preview mixin
Provides toggleable MarkdownViewer preview functionality.
"""
from textual.widgets import Markdown as BaseMarkdownViewer, Tree
from textual.events import Key

# Preview widget with exit key bindings registered at import time
class PreviewViewer(BaseMarkdownViewer):
    """Standalone Markdown viewer with exit-preview key bindings."""
    # Allow this widget to receive focus and handle key bindings
    can_focus = True
    BINDINGS = [
        ("escape", "exit_preview", "Exit preview"),
        ("ctrl+w", "exit_preview", "Exit preview"),
        ("ctrl+shift+m", "exit_preview", "Exit preview"),
        ("up", "scroll_up", "Scroll up"),
        ("down", "scroll_down", "Scroll down"),
        ("left", "scroll_left", "Scroll left"),
        ("right", "scroll_right", "Scroll right"),
    ]

    def action_exit_preview(self) -> None:
        """Action to exit the markdown preview."""
        if hasattr(self.parent, 'toggle_markdown_preview'):
            self.parent.toggle_markdown_preview()



class MarkdownPreviewMixin:
    """Mixin that adds markdown preview toggle to a TextArea-containing widget."""
    def load_markdown_viewer(self, markdown_text: str) -> None:
        """Hide TextArea and mount a MarkdownViewer with given text."""
        # Assume self.text_area exists
        self.text_area.visible = False
        # Collapse TextArea to free layout space
        self.text_area.styles.display = "none"
        # Use the standalone PreviewViewer that handles exit keys
        try:
            self.markdown_viewer = PreviewViewer(markdown_text, toc=True)
        except TypeError:
            # Fallback if toc not supported
            self.markdown_viewer = PreviewViewer(markdown_text)
        self.markdown_viewer.styles.width = "100%"
        self.markdown_viewer.styles.height = "100%"
        # Match TextArea padding: 1 line vertical, 2 spaces horizontal
        self.markdown_viewer.styles.margin = 0
        self.markdown_viewer.styles.padding = (1, 2)
        # Mount and then focus the TOC tree for navigation (fall back to viewer)
        self.mount(self.markdown_viewer)
        def focus_toc() -> None:
            try:
                # Focus the table of contents tree for scrolling/navigation
                toc_tree = self.markdown_viewer.query_one(Tree)
                toc_tree.focus()
            except Exception:
                # Fallback to focusing the viewer itself (for exit keys)
                try:
                    self.markdown_viewer.focus()
                except Exception:
                    pass
        # Delay focus until after mount cycle
        self.call_later(focus_toc)

    def restore_text_area(self) -> None:
        """Remove MarkdownViewer and show the TextArea."""
        if hasattr(self, 'markdown_viewer'):
            self.markdown_viewer.remove()
            del self.markdown_viewer
        # Restore TextArea visibility and layout
        self.text_area.styles.display = "block"
        self.text_area.visible = True
        # Focus the restored text area
        self.text_area.focus()

    def toggle_markdown_preview(self) -> None:
        """Toggle between TextArea and MarkdownViewer preview."""
        if hasattr(self, 'markdown_viewer'):
            self.restore_text_area()
        else:
            self.load_markdown_viewer(self.text_area.text)

    def on_key(self, event: Key) -> None:
        """Catch exit-preview keys even when focus is in the TOC tree."""
        # Only intercept when preview is active
        if hasattr(self, 'markdown_viewer'):
            key = event.key or getattr(event, 'name', None)
            if key in ('escape', 'ctrl+w', 'ctrl+shift+m'):
                self.restore_text_area()
                event.stop()
                return
        # Otherwise, allow normal event propagation
        # ...existing key handlers...

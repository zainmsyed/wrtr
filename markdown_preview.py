"""
Module: Markdown preview mixin
Provides toggleable MarkdownViewer preview functionality.
"""
from textual.widgets import MarkdownViewer as BaseMarkdownViewer, Tree
from textual.events import Key

class MarkdownPreviewMixin:
    """Mixin that adds markdown preview toggle to a TextArea-containing widget."""
    def load_markdown_viewer(self, markdown_text: str) -> None:
        """Hide TextArea and mount a MarkdownViewer with given text."""
        # Assume self.text_area exists
        self.text_area.visible = False
        # Collapse TextArea to free layout space
        self.text_area.styles.display = "none"
        # Use a custom viewer that handles Escape to restore editor
        class PreviewViewer(BaseMarkdownViewer):  # nested to capture parent
            def on_key(self, event: Key) -> None:
                # Treat Escape and Ctrl+W the same: exit preview
                if (event.key == "escape"
                        or event.key == "ctrl+w"
                        or getattr(event, 'name', None) == "ctrl_w"):
                    if hasattr(self.parent, 'toggle_markdown_preview'):
                        self.parent.toggle_markdown_preview()
                        event.stop()
                    return
                # Other keys: do nothing and bubble normally
                return
        # Enable table of contents if supported
        try:
            self.markdown_viewer = PreviewViewer(markdown_text, toc=True)
        except TypeError:
            # Fallback if toc not supported
            self.markdown_viewer = PreviewViewer(markdown_text)
        self.markdown_viewer.styles.width = "100%"
        self.markdown_viewer.styles.height = "100%"
        self.markdown_viewer.styles.margin = 0
        self.markdown_viewer.styles.padding = 0
        self.mount(self.markdown_viewer)
        # Schedule TOC focus to next cycle after mount
        def focus_toc() -> None:
            try:
                toc_tree = self.markdown_viewer.query_one(Tree)
                toc_tree.focus()
            except Exception:
                self.markdown_viewer.focus()
        # call_later ensures the tree is mounted before focusing
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

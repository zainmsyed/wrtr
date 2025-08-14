"""
Module: Markdown preview mixin
Provides toggleable MarkdownViewer preview functionality.
"""
from textual.widgets import MarkdownViewer as BaseMarkdownViewer, Tree
from textual.events import Key, Blur, Focus
from textual.widgets import Markdown as InnerMarkdown  # import inner markdown widget class

# Preview widget with exit key bindings registered at import time
class PreviewViewer(BaseMarkdownViewer):
    """Standalone Markdown viewer with exit-preview key bindings."""
    # Allow this widget to receive focus and handle key bindings
    can_focus = True
    BINDINGS = [
        ("t", "toggle_toc", "Toggle table of contents"),
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

    def action_toggle_toc(self) -> None:
        """Toggle visibility of the table of contents tree."""
        try:
            toc = self.query_one(Tree)
            # Toggle visibility and display style
            visible = toc.visible
            toc.visible = not visible
            toc.styles.display = "none" if visible else "block"
        except Exception:
            pass

    def on_blur(self, event: Blur) -> None:
        """Store current scroll offset when focus leaves the viewer."""
        try:
            self._saved_offset = (self.scroll_offset.x, self.scroll_offset.y)
        except Exception:
            self._saved_offset = (0, 0)
        # Call parent handler if exists
        try:
            return super().on_blur(event)
        except AttributeError:
            return None

    def on_focus(self, event: Focus) -> None:
        """No-op override to maintain current scroll position on focus."""
        # Do nothing to preserve scroll position when the widget gains focus.
        pass

    def on_mount(self) -> None:
        """Disable focus on inner Markdown widget so focus stays on PreviewViewer."""
        try:
            inner = self.query_one(InnerMarkdown)
            inner.can_focus = False
        except Exception:
            pass



class MarkdownPreviewMixin:
    """Mixin that adds markdown preview toggle to a TextArea-containing widget."""
    def load_markdown_viewer(self, markdown_text: str) -> None:
        """Hide TextArea and mount (or reuse) a MarkdownViewer with given text."""
        # Hide the editor TextArea
        self.text_area.visible = False
        self.text_area.styles.display = "none"

        # If preview exists, try fast in-place update
        if hasattr(self, "markdown_viewer"):
            updated = False
            # Fast path: widget-level update()
            try:
                self.markdown_viewer.update(markdown_text)
                updated = True
            except Exception:
                pass
            # Fallback: update inner Markdown child
            if not updated:
                try:
                    inner = self.markdown_viewer.query_one(lambda w: w.__class__.__name__ in ("Markdown", "InnerMarkdown"))
                    inner.update(markdown_text)
                    updated = True
                except Exception:
                    pass
            # Last resort: remove and rebuild once
            if not updated:
                try:
                    self.markdown_viewer.remove()
                except Exception:
                    pass
                del self.markdown_viewer

        # On first use or after fallback deletion, mount a new viewer
        if not hasattr(self, "markdown_viewer"):
            self.markdown_viewer = PreviewViewer(markdown_text, show_table_of_contents=True)
            self.markdown_viewer.styles.width = "100%"
            self.markdown_viewer.styles.height = "100%"
            self.markdown_viewer.styles.margin = 0
            self.markdown_viewer.styles.padding = (2, 3)
            self.mount(self.markdown_viewer)

        # Show the preview
        self.markdown_viewer.visible = True
        self.markdown_viewer.styles.display = "block"

        # Focus TOC or viewer after mount/layout
        def focus_toc() -> None:
            try:
                toc = self.markdown_viewer.query_one(Tree)
                toc.focus()
            except Exception:
                try:
                    self.markdown_viewer.focus()
                except Exception:
                    pass
        self.call_later(focus_toc)

    def restore_text_area(self) -> None:
        """Hide MarkdownViewer and show the TextArea fast (avoid remove())."""
        if hasattr(self, "markdown_viewer"):
            # Fast-hide instead of removal
            try:
                self.markdown_viewer.visible = False
                self.markdown_viewer.styles.display = "none"
            except Exception:
                # fallback to full removal
                try:
                    self.markdown_viewer.remove()
                    del self.markdown_viewer
                except Exception:
                    pass

        # Restore editor TextArea
        self.text_area.styles.display = "block"
        self.text_area.visible = True
        try:
            self.text_area.focus()
        except Exception:
            pass

    def toggle_markdown_preview(self) -> None:
        """Toggle between TextArea and MarkdownViewer preview."""
        if hasattr(self, "markdown_viewer") and self.markdown_viewer.visible:
            self.restore_text_area()
        else:
            self.load_markdown_viewer(self.text_area.text)

    def on_key(self, event: Key) -> None:
        """Catch exit-preview keys even when focus is in the TOC tree."""
        # Only intercept when preview is active (visible)
        if hasattr(self, 'markdown_viewer') and self.markdown_viewer.visible:
            key = event.key or getattr(event, 'name', None)
            if key in ('escape', 'ctrl+w', 'ctrl+shift+m'):
                self.restore_text_area()
                event.stop()
                return
        # Otherwise, allow normal event propagation
        # ...existing key handlers...

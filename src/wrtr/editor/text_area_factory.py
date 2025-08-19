"""
Factory utilities for constructing a TextArea configured for Markdown
with custom theming for link-like tokens.
"""
from rich.style import Style
from textual.widgets import TextArea
from textual.widgets.text_area import TextAreaTheme
from textual.events import Key


class ForwardingTextArea(TextArea):
    """TextArea subclass that forwards unhandled Key events to its parent.

    This lets the owning `MarkdownEditor` receive Enter and other keys even
    if the TextArea didn't fully handle them.
    """
    async def on_key(self, event: Key) -> None:  # type: ignore[override]
        # Let the normal TextArea processing run first
        try:
            await super().on_key(event)
        except Exception:
            # Some Textual versions may not implement async super().on_key
            try:
                super().on_key(event)
            except Exception:
                pass

        handled = getattr(event, 'handled', None)
        if handled is None:
            handled = getattr(event, '_handled', False)

        # If not handled, forward to parent editor if it exposes on_key
        if not handled:
            parent = getattr(self, 'parent', None)
            # climb up until an ancestor with on_key is found
            while parent is not None and not hasattr(parent, 'on_key'):
                parent = getattr(parent, 'parent', None)
            if parent is not None and hasattr(parent, 'on_key'):
                try:
                    await parent.on_key(event)
                except Exception:
                    # ignore errors during forwarding to avoid breaking typing
                    pass


def make_markdown_text_area(initial_text: str = "", language: str | None = "markdown") -> TextArea:
    """Create a TextArea configured for Markdown with custom link styling.

    - Enables tree-sitter syntax by setting language to "markdown".
    - Registers a small custom theme that colors links/wiki-links blue.
    - Keeps standard soft-wrap behavior suitable for writing.
    """
    ta = ForwardingTextArea(text=initial_text, language=language or "markdown")

    # Build a lightweight theme that maps link-ish captures to blue
    # Token names come from the markdown highlight query. We include a few
    # potential variants to be safe across grammar versions.
    link_blue_u = Style(color="#66D9EF", underline=True)  # hyperlinks: blue + underline
    wiki_blue = Style(color="#66D9EF")  # backlinks: blue only, no underline
    wrtr_theme = TextAreaTheme(
        name="wrtr",
        # Only override syntax styles we care about. Other styles fall back to CSS.
        syntax_styles={
            # Standard markdown links
            "link": link_blue_u,
            # Common variants for link parts across markdown grammars
            "link_text": link_blue_u,
            "link_label": link_blue_u,
            "link_destination": link_blue_u,
            "autolink": link_blue_u,
            "uri": link_blue_u,
            "url": link_blue_u,
            # Potential wiki-link capture names seen in some markdown grammars
            "wikilink": wiki_blue,
            "wiki_link": wiki_blue,
            # Some grammars capture the inner content separately
            "wikilink_text": wiki_blue,
            # Custom overlays from TextView
            "md_tag": Style(color="#ADD8E6"),  # blue
            "md_mention": Style(color="#AE81FF"),               # purple mentions
            "md_code": Style(color="#E6DB74"),                  # yellow inline code
            # Task list marker: unchecked colored, checked dim
            "md_checkbox": Style(color="#AE81FF"), # unchecked task marker (purple)
            "md_checkbox_checked": Style(color="#75715E"), # checked task marker (grey)
            "md_bold": Style(color="#FF1493", bold=True),       
            "md_italic": Style(italic=True),                      # italic
            "md_list_bullet": Style(color="#90908a"),           # grey bullet
            "md_list_number": Style(color="#90908a"),           # grey number marker
            # Link overlays for reference/inline and autolinks
            "md_link_text": link_blue_u,
            "md_link_def_url": link_blue_u,
            "md_link_def_label": Style(color="#90908a", italic=True),
            "md_autolink": link_blue_u,
            "md_email": link_blue_u,
            # Headings
            "md_heading_marker": Style(color="#90908a"),
            "md_heading_1": Style(color="#F92672", bold=True),
            "md_heading_2": Style(color="#F92672", bold=True),
            "md_heading_3": Style(color="#F92672", bold=True),
            "md_heading_4": Style(color="#F92672"),
            "md_heading_5": Style(color="#F92672"),
            # Strikethrough styling
            "md_strikethrough": Style(strike=True, color="#90908a"),
        },
    )
    # Make the theme available and activate it
    ta.register_theme(wrtr_theme)
    ta.theme = "wrtr"

    return ta

"""
Factory utilities for constructing a TextArea configured for Markdown
with custom theming for link-like tokens.
"""
from rich.style import Style
from textual.widgets import TextArea
from textual.widgets.text_area import TextAreaTheme


def make_markdown_text_area(initial_text: str = "", language: str | None = "markdown") -> TextArea:
    """Create a TextArea configured for Markdown with custom link styling.

    - Enables tree-sitter syntax by setting language to "markdown".
    - Registers a small custom theme that colors links/wiki-links blue.
    - Keeps standard soft-wrap behavior suitable for writing.
    """
    ta = TextArea(text=initial_text, language=language or "markdown")

    # Build a lightweight theme that maps link-ish captures to blue
    # Token names come from the markdown highlight query. We include a few
    # potential variants to be safe across grammar versions.
    link_blue = Style(color="#66D9EF")  # pleasant blue
    wrtr_theme = TextAreaTheme(
        name="wrtr",
        # Only override syntax styles we care about. Other styles fall back to CSS.
        syntax_styles={
            # Standard markdown links
            "link": link_blue,
            # Potential wiki-link capture names seen in some markdown grammars
            "wikilink": link_blue,
            "wiki_link": link_blue,
            # Some grammars capture the inner content separately
            "wikilink_text": link_blue,
        },
    )
    # Make the theme available and activate it
    ta.register_theme(wrtr_theme)
    ta.theme = "wrtr"

    return ta

"""
Module: View rendering for MarkdownEditor.
Handles TextArea scrolling, syntax highlighting, and Rich integration.
"""
from textual.widgets import TextArea
from textual.containers import Vertical
from textual.events import Key

class TextView:
    """Encapsulates rendering and view-related utilities for TextArea."""

    def __init__(self, text_area: TextArea) -> None:
        self.text_area = text_area

    def move_cursor(self, row: int, col: int, center: bool = False) -> None:
        """Position cursor and optionally center the view."""
        self.text_area.cursor_location = (row, col)
        if center:
            self.text_area.scroll_cursor_visible(center=True)

    def focus(self) -> None:
        """Focus the TextArea for input."""
        self.text_area.focus()

    def set_text(self, text: str) -> None:
        """Load text into the TextArea and highlight backlinks and custom md tokens."""
        self.text_area.load_text(text)
        self.refresh_custom_highlights()

    def replace_range(self, start: tuple[int, int], end: tuple[int, int], insert: str) -> None:
        """Replace text in the given range."""
        self.text_area.replace(start=start, end=end, insert=insert)

    def highlight_backlinks(self) -> None:
        """Overlay blue highlights for any [[target]] and store regions.

        Uses TextArea's internal _highlights to add custom per-line ranges with
        the name 'wikilink'. The active theme maps 'wikilink' to blue.
        """
        import re
        ta = self.text_area
        text = ta.text
        # Track regions for activation
        self.backlink_regions: list[tuple[int, int, str]] = []
        # Remove previous custom wikilink highlights
        try:
            for line_idx, items in list(getattr(ta, "_highlights", {}).items()):
                ta._highlights[line_idx] = [h for h in items if len(h) < 3 or h[2] != "wikilink"]
        except Exception:
            pass
        # Add current highlights
        lines = text.splitlines()
        pattern = re.compile(r"\[\[([^\]]+)\]\]")
        for m in pattern.finditer(text):
            start_off, end_off = m.span()
            target = m.group(1)
            self.backlink_regions.append((start_off, end_off, target))
            (start_row, start_col) = self._offset_to_cursor_pos(text, start_off)
            (end_row, end_col) = self._offset_to_cursor_pos(text, end_off)
            if start_row == end_row:
                try:
                    ta._highlights[start_row].append((start_col, end_col, "wikilink"))
                except Exception:
                    pass
            else:
                try:
                    ta._highlights[start_row].append((start_col, len(lines[start_row]), "wikilink"))
                    for row in range(start_row + 1, end_row):
                        ta._highlights[row].append((0, len(lines[row]), "wikilink"))
                    ta._highlights[end_row].append((0, end_col, "wikilink"))
                except Exception:
                    pass
        try:
            ta.refresh()
        except Exception:
            pass

    def refresh_custom_highlights(self) -> None:
        """Recompute all custom overlay highlights: backlinks + custom MD tokens.
        Uses TextArea._highlights per line; safe to call after any change.
        """
        # First, ensure _highlights dict exists
        ta = self.text_area
        try:
            _ = ta._highlights
        except Exception:
            return
        # Clear only our custom categories on every line before re-adding
        for line_idx, items in list(getattr(ta, "_highlights", {}).items()):
            ta._highlights[line_idx] = [
                h for h in items
                if len(h) < 3 or h[2] not in {
                    # backlinks
                    "wikilink",
                    # inline tokens
                    "md_tag", "md_mention", "md_code", "md_checkbox",
                    # emphasis
                    "md_bold", "md_italic",
                    # lists
                    "md_list_bullet", "md_list_number",
                    # links
                    "md_link_text", "md_link_def_url", "md_link_def_label", "md_autolink", "md_email",
                    # headings (present in some versions)
                    "md_heading_marker", "md_heading_1", "md_heading_2", "md_heading_3", "md_heading_4", "md_heading_5",
                }
            ]
        # Rebuild
        self.highlight_backlinks()
        self._highlight_custom_md_tokens()
        try:
            ta.refresh()
        except Exception:
            pass

    def _highlight_custom_md_tokens(self) -> None:
        """Find and overlay custom Markdown constructs:
        - #tags (word chars, dashes, underscores)
        - @mentions (same charset)
        - Inline code spans `code`
        - Task checkboxes [ ] and [x]/[X]
        - Bold (**text** or __text__)
        - Italic (*text* or _text_)
        - List markers: bullets (- + *) and numbered (1. / 1)
        """
        import re
        ta = self.text_area
        text = ta.text
        lines = text.splitlines()

        # Patterns
        tag_re = re.compile(r"(?<!\w)#([\w-]+)")
        mention_re = re.compile(r"(?<!\w)@([\w-]+)")
        code_re = re.compile(r"`([^`\n]+)`")
        checkbox_re = re.compile(r"^\s*[-*]\s+\[( |x|X)\]", re.MULTILINE)
        # Bold/Italic (avoid spanning newlines; avoid eating triple markers)
        bold_ast_re = re.compile(r"(?<!\*)\*\*([^\n*][^*]*?)\*\*(?!\*)")
        bold_und_re = re.compile(r"(?<!_)__([^\n_][^_]*?)__(?!_)")
        ital_ast_re = re.compile(r"(?<!\*)\*([^\n*]+?)\*(?!\*)")
        ital_und_re = re.compile(r"(?<!_)_([^\n_]+?)_(?!_)")
        # List markers
        bullet_re = re.compile(r"(?m)^(\s*)([-+*])(\s+)")
        number_re = re.compile(r"(?m)^(\s*)(\d+)([.)])(\s+)")

        def add_range(start_off: int, end_off: int, name: str) -> None:
            (sr, sc) = self._offset_to_cursor_pos(text, start_off)
            (er, ec) = self._offset_to_cursor_pos(text, end_off)
            if sr == er:
                try:
                    ta._highlights[sr].append((sc, ec, name))
                except Exception:
                    pass
            else:
                try:
                    ta._highlights[sr].append((sc, len(lines[sr]), name))
                    for r in range(sr + 1, er):
                        ta._highlights[r].append((0, len(lines[r]), name))
                    ta._highlights[er].append((0, ec, name))
                except Exception:
                    pass

        def overlaps_code(a: int, b: int, spans: list[tuple[int, int]]) -> bool:
            for cs, ce in spans:
                if a < ce and cs < b:
                    return True
            return False

        # Inline code first, and collect spans for exclusion
        code_spans: list[tuple[int, int]] = []
        for m in code_re.finditer(text):
            code_spans.append((m.start(), m.end()))
            add_range(m.start(), m.end(), "md_code")

        # Tags and mentions (skip if inside code)
        for m in tag_re.finditer(text):
            if not overlaps_code(m.start(), m.end(), code_spans):
                add_range(m.start(), m.end(), "md_tag")
        for m in mention_re.finditer(text):
            if not overlaps_code(m.start(), m.end(), code_spans):
                add_range(m.start(), m.end(), "md_mention")

        # Checkboxes (line start) — highlight marker segment only
        for m in checkbox_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            # Highlight the "- [ ]" part
            start = m.start()
            end = m.end()
            add_range(start, end, "md_checkbox")

        # Bold (skip inside code)
        for rx in (bold_ast_re, bold_und_re):
            for m in rx.finditer(text):
                if not overlaps_code(m.start(), m.end(), code_spans):
                    add_range(m.start(), m.end(), "md_bold")

        # Italic (skip inside code). Avoid upgrading bold matches: the regex excludes ** and __ contexts
        for rx in (ital_ast_re, ital_und_re):
            for m in rx.finditer(text):
                if not overlaps_code(m.start(), m.end(), code_spans):
                    add_range(m.start(), m.end(), "md_italic")

        # List markers (only the bullet/number token)
        for m in bullet_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            # highlight the bullet symbol + trailing space(s)
            sym_start = m.start(2)
            sym_end = m.end(3)
            add_range(sym_start, sym_end, "md_list_bullet")

        for m in number_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            num_start = m.start(2)
            num_end = m.end(4)
            add_range(num_start, num_end, "md_list_number")

        # Inline links: [text](url "title") — highlight the [text] content only
        inline_link_re = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\)")
        for m in inline_link_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            txt_start = m.start(1)
            txt_end = m.end(1)
            add_range(txt_start, txt_end, "md_link_text")

        # Reference links: [text][label]
        ref_link_re = re.compile(r"\[([^\]\n]{1,200})\]\s*\[([^\]\n]+)\]")
        for m in ref_link_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            txt_start = m.start(1)
            txt_end = m.end(1)
            add_range(txt_start, txt_end, "md_link_text")

        # Link definitions: [label]: URL "title" — highlight URL and optionally label
        link_def_re = re.compile(r"(?m)^\s*\[([^\]]+)\]:\s*(\S+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*$")
        for m in link_def_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            url_start = m.start(2)
            url_end = m.end(2)
            add_range(url_start, url_end, "md_link_def_url")
            # Subtle style for the label name
            lbl_start = m.start(1)
            lbl_end = m.end(1)
            add_range(lbl_start, lbl_end, "md_link_def_label")

        # Headings H1–H5: highlight marker and content separately
        # Examples: '# Title', '### Title ###' (trailing hashes are trimmed)
        heading_re = re.compile(r"(?m)^(\s*)(#{1,5})\s+(.+?)\s*(?:#+\s*)?$")
        for m in heading_re.finditer(text):
            hashes_start = m.start(2)
            hashes_end = m.end(2)
            # Marker style
            add_range(hashes_start, hashes_end, "md_heading_marker")
            # Content style by heading level
            level = min(5, max(1, len(m.group(2))))
            content_raw = m.group(3)
            content_len = len(content_raw.rstrip(" #"))
            if content_len > 0:
                content_start = m.start(3)
                content_end = content_start + content_len
                add_range(content_start, content_end, f"md_heading_{level}")

        # Autolinks and addresses: angle-bracket links, bare URLs, and emails
        # 1) Angle-bracket autolinks: <scheme:...>
        autolink_angle_re = re.compile(r"<([a-z][a-z0-9+.-]*:[^ >]+)>", re.IGNORECASE)
        for m in autolink_angle_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            add_range(m.start(1), m.end(1), "md_autolink")

        # 2) Bare URLs (http, https, www.) — trim trailing punctuation .,;:!?)\]} if present
        bare_url_re = re.compile(
            r"(?<![\w@])((?:https?://|www\.)[\w\-]+(?:\.[\w\-]+)+(?:/[\w\-\./?%&=+#~:@;,]*)?)",
            re.IGNORECASE,
        )
        trailing_punct = ".,;:!?)\\]}"
        for m in bare_url_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            s, e = m.start(1), m.end(1)
            # Trim trailing punctuation
            while e > s and text[e - 1] in trailing_punct:
                e -= 1
            if e > s:
                add_range(s, e, "md_autolink")

        # 3) Email addresses
        email_re = re.compile(r"(?<![/\w])([A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,24})")
        for m in email_re.finditer(text):
            if overlaps_code(m.start(), m.end(), code_spans):
                continue
            add_range(m.start(1), m.end(1), "md_email")

    def _offset_to_cursor_pos(self, text: str, offset: int) -> tuple[int, int]:
        """Convert a character offset in text to (row, col) cursor position.
        Uses splitlines(True) to preserve newline lengths for accurate columns.
        """
        lines = text[:offset].splitlines(True)
        row = len(lines) - 1
        col = len(lines[-1]) if lines else 0
        return row, col

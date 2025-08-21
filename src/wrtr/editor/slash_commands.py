"""
Default slash commands for the Wrtr editor
"""
import datetime
from dataclasses import dataclass

@dataclass
class DefaultCommand:
    label: str
    insert_fn: callable
    help_text: str


def default_commands():
    """Return list of default slash commands"""
    # Static placeholders; args from user are ignored in these defaults
    def today():
        return datetime.date.today().isoformat()

    def timestamp():
        # Return date and time in YYYY-MM-DD HH:MM:SS format
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def todo():
        return "- [ ] "

    def template():
        # Return a sentinel recognized by the editor to open the template UI flow
        return "__SHOW_TEMPLATE_MODAL__"

    def toc():
        return "## Table of Contents\n\n"

    def h1():
        return "# "

    def h2():
        return "## "

    def h3():
        return "### "

    def quote():
        return "> "

    def hr():
        return "---\n"

    def snippet():
        return "<!-- snippet: [name] -->"

    def table():
        # Default 2 columns, 3 rows
        header = "| Col1 | Col2 |"
        separator = "| ---- | ---- |"
        row = "|      |      |"
        return "\n".join([header, separator, row]) + "\n"

    def code():
        return "```language\n\n```"

    def link():
        return "[text](url)"

    # List of default commands
    return [
        DefaultCommand("today", today, "Insert today's date"),
    DefaultCommand("timestamp", timestamp, "Insert current date and time (YYYY-MM-DD HH:MM:SS)"),
        DefaultCommand("todo", todo, "Insert todo checkbox"),
        DefaultCommand("template", template, "Insert template placeholder"),
        DefaultCommand("toc", toc, "Insert table of contents"),
        DefaultCommand("h1", h1, "Insert H1 heading"),
        DefaultCommand("h2", h2, "Insert H2 heading"),
        DefaultCommand("h3", h3, "Insert H3 heading"),
        DefaultCommand("quote", quote, "Insert quote block"),
        DefaultCommand("hr", hr, "Insert horizontal rule"),
        DefaultCommand("snippet", snippet, "Insert snippet placeholder"),
        DefaultCommand("table", table, "Insert table"),
        DefaultCommand("code", code, "Insert code block"),
        DefaultCommand("link", link, "Insert link"),
    ]

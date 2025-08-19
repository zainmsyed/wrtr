"""
Slash command detection logic for the editor
"""
import re
from typing import Optional, Tuple

class SlashCommandDetector:
    """Detect slash commands at the start of a line before the cursor"""

    @staticmethod
    def extract_line_prefix_command(line: str, cursor_col: int) -> Optional[Tuple[str, int, int]]:
        """Extract a slash command from the start of the line up to cursor position

        Returns:
            Tuple (command_text, start_col, end_col) or None if no command
        """
        # Work only with prefix up to cursor
        prefix = line[:cursor_col]
        if not prefix.lstrip().startswith('/'):
            return None

        # Regex to capture leading spaces and only the command token (slash+word)
        # Optionally include the immediate following spaces so we replace '/cmd ' not '/cmdarg'
        # This preserves any further trailing text on the same line.
        pattern = re.compile(r'(\s*)(/\w+)(\s*)$')
        m = pattern.match(prefix)
        if not m:
            return None
        leading_spaces = m.group(1)
        command_text = m.group(2) + m.group(3)
        start_col = len(leading_spaces)
        end_col = start_col + len(command_text)
        return command_text, start_col, end_col

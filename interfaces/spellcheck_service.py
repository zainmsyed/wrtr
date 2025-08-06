"""
Protocol definitions for spellcheck service.
"""
from typing import Protocol, List, Tuple, Optional

class SpellCheckService(Protocol):
    """Defines the interface for a spell-checking service."""
    def check_text(self, text: str) -> List[Tuple[str, List, int]]:
        """Analyze text and return a list of (word, suggestions, position)."""
        ...

    def get_current_word(self) -> Optional[Tuple[str, List, int]]:
        """Return the current misspelled word and its suggestions, or None if none."""
        ...

    def next_word(self) -> Optional[Tuple[str, List, int]]:
        """Advance to the next misspelled word and return it."""
        ...

    def previous_word(self) -> Optional[Tuple[str, List, int]]:
        """Go to the previous misspelled word and return it."""
        ...

    def add_to_dictionary(self, word: str) -> None:
        """Add a word to the user dictionary."""
        ...

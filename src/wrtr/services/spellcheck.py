import importlib.resources
import re
from typing import List, Tuple, Optional
from symspellpy import SymSpell, Verbosity
from wrtr.interfaces.spellcheck_service import SpellCheckService

class SimpleSpellchecker(SpellCheckService):
    """Basic SymSpell-based spell checker."""
    # Implements SpellCheckService protocol

    def __init__(self, max_dictionary_edit_distance: int = 2, prefix_length: int = 7):
        self.symspell = SymSpell(max_dictionary_edit_distance=max_dictionary_edit_distance,
                                 prefix_length=prefix_length)
        # Use importlib.resources to load dictionary paths
        with importlib.resources.path("symspellpy", "frequency_dictionary_en_82_765.txt") as dict_path:
            self.symspell.load_dictionary(str(dict_path), term_index=0, count_index=1)
        with importlib.resources.path("symspellpy", "frequency_bigramdictionary_en_243_342.txt") as bigram_path:
            self.symspell.load_bigram_dictionary(str(bigram_path), term_index=0, count_index=2)

    def correct_word(self, word: str) -> str:
        """
        Return the most likely corrected form of a single word.

        Args:
            word (str): The word to correct.

        Returns:
            str: The top correction, or the original word if no suggestions.
        """
        suggestions = self.symspell.lookup(word, Verbosity.TOP,
                                          max_edit_distance=2,
                                          include_unknown=True)
        return suggestions[0].term if suggestions else word

    def correct_text(self, text: str) -> str:
        """
        Correct every word in the given text string.

        Args:
            text (str): The text to spell-check.

        Returns:
            str: A new string with each word corrected.
        """
        return " ".join(self.correct_word(w) for w in text.split())

    def add_to_dictionary(self, word: str) -> None:
        """Add a word to the SymSpell dictionary to prevent future flagging."""
        # Create a new entry with count=1; treat as input term
        try:
            self.symspell.create_dictionary_entry(word, 1)
        except Exception:
            pass


class MarkdownSpellchecker(SimpleSpellchecker):
    """Backward-compatible alias for the old MarkdownSpellchecker interface with basic check_text support."""
    def __init__(self, dictionary_path: str = None, user_dictionary_path: str = None,
                 max_dictionary_edit_distance: int = 2, prefix_length: int = 7):
        from pathlib import Path
        super().__init__(max_dictionary_edit_distance=max_dictionary_edit_distance,
                         prefix_length=prefix_length)
        self.user_terms: set[str] = set()
        # Determine user dictionary path: use provided or default project file
        if user_dictionary_path:
            self.user_dictionary_path = user_dictionary_path
        else:
            base = Path(__file__).parent.parent
            self.user_dictionary_path = str(
                base / "wrtr" / "data" / "dictionary" / "user_dictionary.txt"
            )
        # Load initial user dictionary terms
        try:
            with open(self.user_dictionary_path, 'r', encoding='utf-8') as uf:
                for line in uf:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    term = parts[0].lower()
                    self.user_terms.add(term)
                    # Also add to symspell dictionary to prevent flagging
                    self.symspell.create_dictionary_entry(term, 1)
        except Exception:
            pass
        self.misspelled_words: list[tuple[str, list, int]] = []
        self.current_index: int = -1

    def check_text(self, text: str) -> List[Tuple[str, List, int]]:
        """
        Analyze text and return details on misspelled words.

        Args:
            text (str): The markdown text to check.

        Returns:
            List[Tuple[str, List, int]]: A list of tuples (word, suggestions, position).
        """
        # Reload user dictionary terms each pass to ensure skips are up-to-date
        if getattr(self, 'user_dictionary_path', None):
            try:
                terms = set()
                with open(self.user_dictionary_path, 'r', encoding='utf-8') as uf:
                    for line in uf:
                        parts = line.strip().split()
                        if parts:
                            terms.add(parts[0].lower())
                self.user_terms = terms
                for term in self.user_terms:
                    self.symspell.create_dictionary_entry(term, 1)
            except Exception:
                pass

        self.misspelled_words = []
        # Normalize smart apostrophes to ASCII
        text = text.replace("’", "'").replace("‘", "'")

        # Regex patterns
        url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
        link_pattern = re.compile(r'\[.*?\]\(.*?\)')
        ordinal_pattern = re.compile(r'^\d+(st|nd|rd|th)$')

        # Identify spans to skip
        url_spans = [(u.start(), u.end()) for u in url_pattern.finditer(text)]
        link_spans = [(l.start(), l.end()) for l in link_pattern.finditer(text)]
        url_spans.extend(link_spans)

        # Check each word
        for m in re.finditer(r"\b[\w']+\b", text):
            word = m.group()
            pos = m.start()
            lw = word.lower()
            # Skip possessives and stray s
            if lw == "'s" or lw.endswith("'s") or lw == "s":
                continue
            # Skip user-defined terms
            if lw in self.user_terms:
                continue
            # Skip URLs or links
            if any(start <= pos < end for start, end in url_spans):
                continue
            # Skip numbers and ordinals
            if ordinal_pattern.match(word) or word.isdigit():
                continue
            # Skip capitalized words
            if word and word[0].isupper():
                continue

            # Get suggestions
            sugg = self.symspell.lookup(word, Verbosity.ALL, max_edit_distance=2, include_unknown=True)
            if sugg and sugg[0].term.lower() != lw:
                self.misspelled_words.append((word, sugg, pos))

        self.current_index = 0 if self.misspelled_words else -1
        return self.misspelled_words

    def add_to_dictionary(self, word: str) -> None:
        """Add a word to both SymSpell and the user dictionary file."""
        # add to symspell and in-memory set
        try:
            super().add_to_dictionary(word)
        except Exception:
            pass
        term = word.lower()
        if term not in self.user_terms:
            self.user_terms.add(term)
            # persist to user dictionary file
            if getattr(self, 'user_dictionary_path', None):
                try:
                    with open(self.user_dictionary_path, 'a', encoding='utf-8') as uf:
                        uf.write(f"{term}\n")
                except Exception:
                    pass

    def get_current_word(self) -> Optional[Tuple[str, List, int]]:
        """
        Get the current misspelled word entry if available.

        Returns:
            Optional[Tuple[str, List, int]]: The current (word, suggestions, position), or None.
        """
        if 0 <= self.current_index < len(self.misspelled_words):
            return self.misspelled_words[self.current_index]
        return None

    def next_word(self) -> Optional[Tuple[str, List, int]]:
        """Advance to next misspelled word and return it."""
        if not self.misspelled_words:
            return None
        self.current_index = (self.current_index + 1) % len(self.misspelled_words)
        return self.get_current_word()

    def previous_word(self) -> Optional[Tuple[str, List, int]]:
        """Go to previous misspelled word and return it."""
        if not self.misspelled_words:
            return None
        self.current_index = (self.current_index - 1) % len(self.misspelled_words)
        return self.get_current_word()

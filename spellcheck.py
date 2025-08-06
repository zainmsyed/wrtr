import importlib.resources
from symspellpy import SymSpell, Verbosity
from interfaces.spellcheck_service import SpellCheckService
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
        """Return the top correction for a single word."""
        suggestions = self.symspell.lookup(word, Verbosity.TOP,
                                          max_edit_distance=2,
                                          include_unknown=True)
        return suggestions[0].term if suggestions else word

    def correct_text(self, text: str) -> str:
        """Correct all words in a text string."""
        return " ".join(self.correct_word(w) for w in text.split())

    def add_to_dictionary(self, word: str) -> None:
        """Add a word to the SymSpell dictionary to prevent future flagging."""
        # Create a new entry with count=1; treat as input term
        try:
            self.symspell.create_dictionary_entry(word, 1)
        except Exception:
            pass

if __name__ == "__main__":
    sc = SimpleSpellchecker()
    print(sc.correct_word("tsting"))      # expect 'testing'
    print(sc.correct_text("th tsting words"))  # expect 'th testing words'
 
import re

class MarkdownSpellchecker(SimpleSpellchecker):
    """Backward-compatible alias for the old MarkdownSpellchecker interface with basic check_text support."""
    def __init__(self, dictionary_path: str = None, user_dictionary_path: str = None,
                 max_dictionary_edit_distance: int = 2, prefix_length: int = 7):
        # ignore provided paths in this simple implementation
        super().__init__(max_dictionary_edit_distance=max_dictionary_edit_distance,
                         prefix_length=prefix_length)
        self.user_terms: set[str] = set()
        # store user dictionary file path
        self.user_dictionary_path = user_dictionary_path
        # Load user dictionary if provided
        if user_dictionary_path:
            try:
                with open(user_dictionary_path, 'r', encoding='utf-8') as uf:
                    for line in uf:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        term = parts[0].lower()
                        self.user_terms.add(term)
                        # Also add to symspell dictionary
                        self.symspell.create_dictionary_entry(term, 1)
            except Exception:
                pass
        self.misspelled_words: list[tuple[str, list, int]] = []
        self.current_index: int = -1

    def check_text(self, text: str) -> list[tuple[str, list, int]]:
        """Find misspellings in text, record word, suggestions, and position."""
        self.misspelled_words = []
        # Regex to match URLs
        url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
        # Regex to match markdown links ([text](url))
        link_pattern = re.compile(r'\[.*?\]\(.*?\)')
        # Regex to match ordinal numbers (e.g., 1st, 2nd, 3rd, 4th)
        ordinal_pattern = re.compile(r'^\d+(st|nd|rd|th)$')
        # Identify spans of URLs to skip words within them
        url_spans = [(u.start(), u.end()) for u in url_pattern.finditer(text)]
        # Also skip spans of markdown links
        link_spans = [(l.start(), l.end()) for l in link_pattern.finditer(text)]
        url_spans.extend(link_spans)
        # Match words including apostrophes to handle contractions correctly
        for m in re.finditer(r"\b[\w']+\b", text):
            word = m.group()
            pos = m.start()
            # Skip user-defined terms
            if word.lower() in getattr(self, 'user_terms', set()):
                continue
            # Skip words that are part of a URL or markdown link
            if any(start <= pos < end for start, end in url_spans):
                continue
            # Skip ordinal numbers (e.g., 1st, 2nd)
            if ordinal_pattern.match(word):
                continue
            # Skip pure numeric tokens (e.g., 1234)
            if word.isdigit():
                continue
            # Ignore words that start with uppercase (nouns and sentence starts)
            if word and word[0].isupper():
                continue
            # Get all suggestions
            sugg = self.symspell.lookup(word, Verbosity.ALL, max_edit_distance=2, include_unknown=True)
            if sugg and sugg[0].term.lower() != word.lower():
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

    def get_current_word(self):
        """Return current word tuple or None."""
        if 0 <= self.current_index < len(self.misspelled_words):
            return self.misspelled_words[self.current_index]
        return None

    def next_word(self):
        """Advance to next misspelled word and return it."""
        if not self.misspelled_words:
            return None
        self.current_index = (self.current_index + 1) % len(self.misspelled_words)
        return self.get_current_word()

    def previous_word(self):
        """Go to previous misspelled word and return it."""
        if not self.misspelled_words:
            return None
        self.current_index = (self.current_index - 1) % len(self.misspelled_words)
        return self.get_current_word()

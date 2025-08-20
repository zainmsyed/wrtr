import importlib.resources
import re
from pathlib import Path
from typing import List, Tuple, Optional
from symspellpy import SymSpell, Verbosity
from wrtr.interfaces.spellcheck_service import SpellCheckService


class DictionaryLoader:
    """Utility class for loading SymSpell dictionaries."""
    
    @staticmethod
    def load_frequency_dictionary(symspell: SymSpell, dictionary_path: str | None = None) -> None:
        """Load frequency dictionary into SymSpell instance."""
        if dictionary_path:
            try:
                symspell.load_dictionary(str(dictionary_path), term_index=0, count_index=1)
                return
            except Exception:
                # Fallback to built-in if custom dictionary fails
                pass
        
        # Load built-in frequency dictionary
        with importlib.resources.path("symspellpy", "frequency_dictionary_en_82_765.txt") as dict_path_res:
            symspell.load_dictionary(str(dict_path_res), term_index=0, count_index=1)
    
    @staticmethod
    def load_bigram_dictionary(symspell: SymSpell, bigram_dictionary_path: str | None = None) -> None:
        """Load bigram dictionary into SymSpell instance (optional)."""
        try:
            if bigram_dictionary_path:
                symspell.load_bigram_dictionary(str(bigram_dictionary_path), term_index=0, count_index=2)
            else:
                # Load built-in bigram dictionary
                with importlib.resources.path("symspellpy", "frequency_bigramdictionary_en_243_342.txt") as bigram_path_res:
                    symspell.load_bigram_dictionary(str(bigram_path_res), term_index=0, count_index=2)
        except Exception:
            # If bigram loading fails, continue without it
            pass


class UserDictionary:
    """Utility class for managing user dictionary files."""
    
    def __init__(self, user_dictionary_path: str | None = None):
        if user_dictionary_path:
            self.path = Path(user_dictionary_path)
        else:
            self.path = Path.cwd() / "wrtr" / "data" / "dictionary" / "user_dictionary.txt"
        
        # Ensure directory exists and file is present
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.write_text("", encoding="utf-8")
        except Exception:
            pass
    
    def load_terms(self) -> set[str]:
        """Load user dictionary terms from file."""
        terms = set()
        try:
            with open(self.path, 'r', encoding='utf-8') as uf:
                for line in uf:
                    parts = line.strip().split()
                    if parts:
                        terms.add(parts[0].lower())
        except Exception:
            pass
        return terms
    
    def add_term(self, term: str) -> None:
        """Add a term to the user dictionary file."""
        term = term.lower()
        try:
            with open(self.path, 'a', encoding='utf-8') as uf:
                uf.write(f"{term}\n")
        except Exception:
            pass
    
    def add_terms_to_symspell(self, symspell: SymSpell, terms: set[str]) -> None:
        """Add terms to SymSpell dictionary to prevent flagging."""
        for term in terms:
            try:
                symspell.create_dictionary_entry(term, 1)
            except Exception:
                pass


class MarkdownSpellchecker(SpellCheckService):
    """Markdown-aware spell checker with user dictionary support."""
    
    def __init__(
        self,
        dictionary_path: str | None = None,
        user_dictionary_path: str | None = None,
        max_dictionary_edit_distance: int = 2,
        prefix_length: int = 7,
        load_bigrams: bool = False,  # Skip bigrams by default for performance
    ):
        # Initialize SymSpell
        self.symspell = SymSpell(
            max_dictionary_edit_distance=max_dictionary_edit_distance,
            prefix_length=prefix_length,
        )
        
        # Load frequency dictionary
        DictionaryLoader.load_frequency_dictionary(self.symspell, dictionary_path)
        
        # Load bigrams if requested (optional for performance)
        if load_bigrams:
            DictionaryLoader.load_bigram_dictionary(self.symspell)
        
        # Set up user dictionary
        self.user_dictionary = UserDictionary(user_dictionary_path)
        self.user_terms = self.user_dictionary.load_terms()
        self.user_dictionary.add_terms_to_symspell(self.symspell, self.user_terms)
        
        # Per-session ignored terms (skip all further occurrences)
        self.ignored_terms: set[str] = set()
        
        # State for tracking misspelled words
        self.misspelled_words: list[tuple[str, list, int]] = []
        self.current_index: int = -1

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

    def check_text(self, text: str) -> List[Tuple[str, List, int]]:
        """
        Analyze text and return details on misspelled words.

        Args:
            text (str): The markdown text to check.

        Returns:
            List[Tuple[str, List, int]]: A list of tuples (word, suggestions, position).
        """
        # Reload user dictionary terms each pass to ensure skips are up-to-date
        self.user_terms = self.user_dictionary.load_terms()
        self.user_dictionary.add_terms_to_symspell(self.symspell, self.user_terms)

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
            # If word has leading/trailing apostrophes (e.g., 'the or the'),
            # consider the base word without surrounding apostrophes; if that
            # base is correctly spelled, skip flagging to avoid false positives
            # from quotes.
            if (lw.startswith("'") or lw.endswith("'")) and len(lw) > 1:
                base = lw.strip("'")
                if base:
                    try:
                        base_sugg = self.symspell.lookup(base, Verbosity.TOP, max_edit_distance=2, include_unknown=True)
                        if base_sugg and base_sugg[0].term.lower() == base and getattr(base_sugg[0], 'distance', 0) == 0:
                            continue
                    except Exception:
                        pass
            # Skip user-defined terms
            if lw in self.user_terms:
                continue
            # Skip ignored words for the session
            if lw in getattr(self, 'ignored_terms', set()):
                continue
            # Skip URLs or links
            if any(start <= pos < end for start, end in url_spans):
                continue
            # Skip numbers and ordinals
            if ordinal_pattern.match(word) or word.isdigit():
                continue
            # Skip capitalized words only if they are correctly spelled
            if word and word[0].isupper():
                sugg = self.symspell.lookup(word.lower(), Verbosity.TOP, max_edit_distance=2, include_unknown=True)
                if sugg and sugg[0].term.lower() == lw and getattr(sugg[0], 'distance', 0) == 0:
                    continue

            # Get suggestions
            sugg = self.symspell.lookup(word, Verbosity.ALL, max_edit_distance=2, include_unknown=True)
            if sugg and sugg[0].term.lower() != lw:
                self.misspelled_words.append((word, sugg, pos))

        self.current_index = 0 if self.misspelled_words else -1
        return self.misspelled_words

    def add_to_dictionary(self, word: str) -> None:
        """Add a word to both SymSpell and the user dictionary file."""
        term = word.lower()
        
        # Add to SymSpell dictionary
        try:
            self.symspell.create_dictionary_entry(term, 1)
        except Exception:
            pass
        
        # Add to user dictionary if not already present
        if term not in self.user_terms:
            self.user_terms.add(term)
            self.user_dictionary.add_term(term)

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

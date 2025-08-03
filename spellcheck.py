import os
from symspellpy import SymSpell, Verbosity
from pathlib import Path
import requests

class MarkdownSpellchecker:
    """Spellchecker service for MarkdownEditor."""

    def __init__(self, dictionary_path: str, user_dictionary_path: str):
        self.dictionary_path = dictionary_path
        self.user_dictionary_path = user_dictionary_path
        self.symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self.misspelled_words = []  # Track misspelled words
        self.current_index = -1  # Track the current word index

        # Ensure dictionary folder and files exist
        self._ensure_dictionaries()

        # Load dictionaries
        self._load_dictionaries()

    def _ensure_dictionaries(self):
        """Ensure the dictionary folder and files exist."""
        dictionary_folder = Path(self.dictionary_path).parent
        dictionary_folder.mkdir(parents=True, exist_ok=True)

        # Check if frequency dictionary exists
        if not Path(self.dictionary_path).is_file():
            print(f"[INFO] Downloading frequency dictionary to {self.dictionary_path}...")
            url = "https://raw.githubusercontent.com/wolfgarbe/SymSpell/master/SymSpell/frequency_dictionary_en_82_765.txt"
            response = requests.get(url)
            if response.status_code == 200:
                with open(self.dictionary_path, "wb") as f:
                    f.write(response.content)
                print("[INFO] Frequency dictionary downloaded successfully.")
            else:
                raise FileNotFoundError(f"Failed to download frequency dictionary from {url}")

        # Ensure user dictionary exists
        if not Path(self.user_dictionary_path).is_file():
            Path(self.user_dictionary_path).write_text("")

    def _load_dictionaries(self):
        """Load the frequency and user dictionaries into SymSpell."""
        self.symspell.load_dictionary(self.dictionary_path, term_index=0, count_index=1)

        # Load user dictionary
        if Path(self.user_dictionary_path).stat().st_size > 0:
            self.symspell.load_dictionary(self.user_dictionary_path, term_index=0, count_index=1)

    def check_text(self, text: str):
        """Check text for misspelled words and record their positions."""
        words = text.split()
        self.misspelled_words = []  # Reset misspelled words
        current_pos = 0
        for word in words:
            # find actual position of this word starting from last position
            word_pos = text.find(word, current_pos)
            if word_pos == -1:
                continue
            # get suggestions: first strict, then fuzzy
            suggestions = self.symspell.lookup(word, Verbosity.CLOSEST, max_edit_distance=0)
            if not suggestions:
                suggestions = self.symspell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
                # store word, suggestion list, and absolute position
                self.misspelled_words.append((word, suggestions, word_pos))
            # advance search position
            current_pos = word_pos + len(word)
        self.current_index = 0 if self.misspelled_words else -1
        return self.misspelled_words

    def get_current_word(self):
        """Get the current misspelled word and its suggestions."""
        if 0 <= self.current_index < len(self.misspelled_words):
            return self.misspelled_words[self.current_index]
        return None

    def next_word(self):
        """Move to the next misspelled word without wrapping."""
        if self.misspelled_words and self.current_index < len(self.misspelled_words) - 1:
            self.current_index += 1
            return self.get_current_word()
        return None

    def previous_word(self):
        """Move to the previous misspelled word without wrapping."""
        if self.misspelled_words and self.current_index > 0:
            self.current_index -= 1
            return self.get_current_word()
        return None

    def add_to_dictionary(self, word: str):
        """Add a word to the user dictionary."""
        with open(self.user_dictionary_path, "a") as user_dict:
            user_dict.write(f"{word}\n")
        self.symspell.create_dictionary_entry(word, 1)

    def replace_word(self, old: str, suggestion: str, full_text: str) -> str:
        """Replace a misspelled word with a suggestion in the full text."""
        return full_text.replace(old, suggestion)

    def ignore_word(self, word: str):
        """Ignore a word for the current session."""
        self.symspell.create_dictionary_entry(word, 1)

# Example usage
if __name__ == "__main__":
    print("MarkdownSpellchecker is ready for integration.")

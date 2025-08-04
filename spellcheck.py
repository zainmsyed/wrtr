import os
import re
from symspellpy import SymSpell, Verbosity
from pathlib import Path
import requests

class MarkdownSpellchecker:
    """Spellchecker service for MarkdownEditor."""

    def __init__(self, dictionary_path: str = None, user_dictionary_path: str = None):
        # Default to the `wrtr` folder if paths are not provided
        base_path = Path(__file__).parent / "wrtr"
        self.dictionary_path = dictionary_path or str(base_path / "frequency_dictionary_en_82_765.txt")
        self.user_dictionary_path = user_dictionary_path or str(base_path / "user_dictionary.txt")
        self.symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self.misspelled_words = []  # Track misspelled words
        self.current_index = -1  # Track the current word index

        # Common words that shouldn't be flagged as misspelled
        self.common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'under', 'over',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'ours', 'theirs',
            'this', 'that', 'these', 'those', 'who', 'what', 'where', 'when', 'why', 'how',
            'is', 'am', 'are', 'was', 'were', 'be', 'being', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'get', 'got', 'go', 'going', 'gone', 'come', 'came', 'see', 'saw'
        }

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
        print(f"Loading dictionary: {self.dictionary_path}")
        self.symspell.load_dictionary(self.dictionary_path, term_index=0, count_index=1)

        # Load user dictionary
        if Path(self.user_dictionary_path).stat().st_size > 0:
            print(f"Loading user dictionary: {self.user_dictionary_path}")
            self.symspell.load_dictionary(self.user_dictionary_path, term_index=0, count_index=1)

    def _should_ignore_word(self, word: str) -> bool:
        """Determine if a word should be ignored during spell checking."""
        print(f"Checking ignore for: '{word}'")  # Debug output

        # Ignore empty strings
        if not word:
            return True

        # Ignore words that contain digits (e.g., 4th, HTML5, 3D)
        if re.search(r'\d', word):
            print(f"Ignoring word with digits: {word}")
            return True

        # Ignore all-caps acronyms (e.g., HTML, CSS)
        if re.fullmatch(r'[A-Z]{2,}', word):
            print(f"Ignoring acronym: {word}")
            return True

        # Ignore empty words or single characters
        if len(word) <= 1:
            return True
            
        # Ignore numbers
        if word.isdigit():
            return True
            
        # Ignore words that are mix of letters and numbers (like "HTML5", "4th")
        # Refine the rule to ignore mixed alphanumeric words (e.g., '4th', 'HTML5')
        if re.search(r'\d', word) and re.search(r'[A-Za-z]', word):
            print(f"Ignoring mixed alphanumeric word: {word}")
            return True
            
        # Ignore common words
        if word.lower() in self.common_words:
            print(f"Ignoring common word: {word}")
            return True
            
        # Ignore words that start with capital letter (likely proper nouns)
        # But be more intelligent about this
        # if word[0].isupper() and len(word) >= 3:
        #     return True
            
        # Ignore words with apostrophes (contractions, possessives)
        if "'" in word:
            return True
            
        # Ignore very short words (2 characters or less) unless they're common typos
        if len(word) <= 2 and word not in self.common_words:
            return False
            
        # Ensure short words are not ignored unless explicitly common
        if len(word) <= 3 and word not in self.common_words:
            return False
            
        # Ignore URLs, emails, file paths
        if re.match(r'^(https?|ftp|www)$', word) or '@' in word or '://' in word:
            return True
            
        # Ignore markdown syntax
        if re.match(r'^[#*_`\[\]()]+$', word):
            return True
            
        # Ignore words that are all uppercase (likely acronyms)
        if word.isupper() and len(word) >= 2:
            print(f"Word: {word}, Is Uppercase: {word.isupper()}, Length: {len(word)}")  # Debug output
            return True
            
        # Ignore contractions (e.g., don't, can't, you're)
        contraction_pattern = re.compile(r"^(?:[a-zA-Z]+(?:'t|'re|'ve|'ll|'d|'s|'m))$")
        if contraction_pattern.match(word):
            return True
            
        # Ensure numbers and mixed alphanumeric words are ignored
        if re.fullmatch(r'[A-Za-z]*\d+[A-Za-z]*', word):
            print(f"Ignoring mixed alphanumeric word: {word}")
            return True
            
        return False

    def check_text(self, text: str):
        """Check text for misspelled words and record their positions."""
        # First, let's identify and temporarily replace URLs, emails to avoid splitting them
        url_pattern = r'https?://[^\s]+'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Find URLs and emails to skip them entirely
        urls = list(re.finditer(url_pattern, text))
        emails = list(re.finditer(email_pattern, text))
        skip_ranges = [(m.start(), m.end()) for m in urls + emails]
        
        # Split text into words while preserving positions
        # Adjust word splitting to ensure all words, including short ones, are checked
        words = re.finditer(r'\b\w+\b', text)
        self.misspelled_words = []  # Reset misspelled words
        
        for match in words:
            word = match.group()
            word_pos = match.start()
            
            # Skip words that should be ignored early
            if self._should_ignore_word(word):
                print(f"Ignoring word: {word}")
                continue
            
            # Skip words that are within URL or email ranges
            if any(start <= word_pos < end for start, end in skip_ranges):
                continue
                
            # Clean the word for spell checking (remove punctuation but keep apostrophes)
            clean_word = re.sub(r'[^\w\']', '', word).lower()
            
            # First check: exact match (case-insensitive)
            suggestions = self.symspell.lookup(clean_word, Verbosity.CLOSEST, max_edit_distance=0)
            
            print(f"Processing word: {word}, Suggestions: {suggestions}, Ignored: {self._should_ignore_word(word)}")  # Debug output
            
            if not suggestions:
                # Second check: fuzzy match with edit distance
                all_suggestions = self.symspell.lookup(clean_word, Verbosity.ALL, max_edit_distance=2)
                
                if not all_suggestions:
                    # If no suggestions found, try the original word case
                    all_suggestions = self.symspell.lookup(word.lower(), Verbosity.ALL, max_edit_distance=2)
                
                # Limit to 5 suggestions and sort by edit distance
                suggestions = sorted(all_suggestions, key=lambda x: x.distance)[:5]
                
                if suggestions:  # Only add if we have suggestions
                    self.misspelled_words.append((word, suggestions, word_pos))
                else:
                    # Still record it as misspelled even when SymSpell has no replacement
                    self.misspelled_words.append((word, [], word_pos))
            
            # Ensure short words are checked even if ignored by `_should_ignore_word`
            if len(word) <= 3 and not suggestions:
                all_suggestions = self.symspell.lookup(word.lower(), Verbosity.ALL, max_edit_distance=2)
                suggestions = sorted(all_suggestions, key=lambda x: x.distance)[:5]

                if suggestions:
                    self.misspelled_words.append((word, suggestions, word_pos))
        
        self.current_index = 0 if self.misspelled_words else -1
        return self.misspelled_words

    def get_current_word(self):
        """Get the current misspelled word and its suggestions."""
        if 0 <= self.current_index < len(self.misspelled_words):
            return self.misspelled_words[self.current_index]
        return None

    def next_word(self):
        """Move to the next misspelled word, wrapping around to the start if at the end."""
        if self.misspelled_words:
            self.current_index = (self.current_index + 1) % len(self.misspelled_words)
            return self.get_current_word()
        return None

    def previous_word(self):
        """Move to the previous misspelled word, wrapping around to the end if at the start."""
        if self.misspelled_words:
            self.current_index = (self.current_index - 1) % len(self.misspelled_words)
            return self.get_current_word()
        return None

    def add_to_dictionary(self, word: str):
        """Add a word to the user dictionary."""
        # Clean the word before adding
        clean_word = re.sub(r'[^\w\']', '', word).lower()
        
        # Check if word is already in user dictionary
        try:
            with open(self.user_dictionary_path, "r") as user_dict:
                existing_words = user_dict.read().strip().split('\n')
                if clean_word in existing_words:
                    return  # Word already exists
        except FileNotFoundError:
            pass
            
        # Add to user dictionary file
        with open(self.user_dictionary_path, "a") as user_dict:
            user_dict.write(f"{clean_word} 1\n")  # Include frequency count
            
        # Add to SymSpell dictionary
        self.symspell.create_dictionary_entry(clean_word, 1)
        
        # Also add the original case version
        if clean_word != word.lower():
            self.symspell.create_dictionary_entry(word.lower(), 1)

    def replace_word(self, old: str, suggestion: str, full_text: str) -> str:
        """Replace a misspelled word with a suggestion in the full text."""
        return full_text.replace(old, suggestion)

    def ignore_word(self, word: str):
        """Ignore a word for the current session."""
        clean_word = re.sub(r'[^\w\']', '', word).lower()
        self.symspell.create_dictionary_entry(clean_word, 1)
        
        # Also ignore the original case version
        if clean_word != word.lower():
            self.symspell.create_dictionary_entry(word.lower(), 1)

# Example usage
if __name__ == "__main__":
    print("MarkdownSpellchecker is ready for integration.")

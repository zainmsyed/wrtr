import unittest
from spellcheck import MarkdownSpellchecker

class TestMarkdownSpellchecker(unittest.TestCase):

    def setUp(self):
        """Set up the spellchecker with test dictionaries."""
        self.spellchecker = MarkdownSpellchecker(
            dictionary_path="wrtr/data/dictionary/frequency_dictionary_en_82_765.txt",
            user_dictionary_path="wrtr/data/dictionary/user_dictionary.txt"
        )

    def test_ignore_contractions(self):
        """Test that contractions are ignored."""
        text = "I can't believe it's not butter."
        misspelled = self.spellchecker.check_text(text)
        self.assertEqual(len(misspelled), 0, "Contractions should not be flagged as misspelled.")

    def test_ignore_proper_nouns(self):
        """Test that proper nouns are ignored."""
        text = "New York is a bustling city."
        misspelled = self.spellchecker.check_text(text)
        self.assertEqual(len(misspelled), 0, "Proper nouns should not be flagged as misspelled.")

    def test_detect_misspelled_words(self):
        """Test that misspelled words are detected."""
        text = "This is a testng of mispelled words."
        misspelled = self.spellchecker.check_text(text)
        print(f"Misspelled words: {misspelled}")
        self.assertEqual(len(misspelled), 2, "Two misspelled words should be detected.")
        self.assertEqual(misspelled[0][0], "testng", "First misspelled word should be 'testng'.")
        self.assertEqual(misspelled[1][0], "mispelled", "Second misspelled word should be 'mispelled'.")

    def test_ignore_urls_and_emails(self):
        """Test that URLs and emails are ignored."""
        text = "Visit https://example.com or email test@example.com."
        misspelled = self.spellchecker.check_text(text)
        self.assertEqual(len(misspelled), 0, "URLs and emails should not be flagged as misspelled.")

    def test_ignore_acronyms(self):
        """Test that acronyms are ignored."""
        text = "HTML and CSS are acronyms."
        misspelled = self.spellchecker.check_text(text)
        self.assertEqual(len(misspelled), 0, "Acronyms should not be flagged as misspelled.")

    def test_ignore_numbers_and_mixed_words(self):
        """Test that numbers and mixed alphanumeric words are ignored."""
        text = "The 4th version of HTML5 is great."
        misspelled = self.spellchecker.check_text(text)
        print(f"Misspelled words: {misspelled}")
        self.assertEqual(len(misspelled), 0, "Numbers and mixed words should not be flagged as misspelled.")

    def test_detect_typical_typos(self):
        """Test that typical typos are detected."""
        text = "Ths is a typo."
        misspelled = self.spellchecker.check_text(text)
        self.assertEqual(len(misspelled), 1, "One typo should be detected.")
        self.assertEqual(misspelled[0][0], "Ths", "The typo should be 'Ths'.")

    def test_symspell_short_word(self):
        """Test SymSpell behavior for short words like 'Ths'."""
        text = "Ths"
        misspelled = self.spellchecker.check_text(text)
        print(f"SymSpell output for 'Ths': {misspelled}")
        self.assertEqual(len(misspelled), 1, "Short word 'Ths' should be flagged as misspelled.")

if __name__ == "__main__":
    unittest.main()

"""
Module: Spellcheck service for MarkdownEditor
Encapsulates spellcheck activation, deactivation, and display update.
"""
from pathlib import Path
from services.spellcheck import MarkdownSpellchecker
from interfaces.spellcheck_service import SpellCheckService


def start_spellcheck(editor):
    """Start spellcheck mode in the editor."""
    # Lazy-load spellchecker on first use
    if editor.spellchecker is None:
        # Lazy-load spellchecker on first use, with project dictionary paths
        base = Path(__file__).parent.parent
        dict_path = base / "wrtr" / "data" / "dictionary" / "frequency_dictionary_en_82_765.txt"
        user_dict = base / "wrtr" / "data" / "dictionary" / "user_dictionary.txt"
        editor.spellchecker = MarkdownSpellchecker(
            dictionary_path=str(dict_path),
            user_dictionary_path=str(user_dict)
        )
    editor._spellcheck_active = True
    misspelled = editor.spellchecker.check_text(editor.text)
    editor.status_bar.enter_spellcheck_mode()
    if misspelled:
        # Delegate display update to module function
        update_spellcheck_display(editor)


def exit_spellcheck(editor):
    """Exit spellcheck mode in the editor."""
    editor._spellcheck_active = False
    editor.status_bar.exit_spellcheck_mode()


def update_spellcheck_display(editor):
    """Update status bar and move cursor to current misspelled word."""
    misspelled = editor.spellchecker.misspelled_words
    if misspelled:
        idx = editor.spellchecker.current_index
        word, suggestions, pos = (
            misspelled[idx][0],
            [s.term for s in misspelled[idx][1]],
            misspelled[idx][2]
        )
        editor.status_bar.set_spellcheck_info(
            word=word,
            suggestions=suggestions,
            progress=(idx+1, len(misspelled))
        )
        # Move cursor using TextView helper
        row, col = editor._convert_text_position_to_cursor(pos)
        editor.view.move_cursor(row, col, center=True)
        editor.view.focus()
    else:
        editor.status_bar.set_spellcheck_info(None, [], (0, 0))

async def activate_and_focus_first_misspelled_word(editor):
    """Activate spellcheck and focus on the first misspelled word."""
    start_spellcheck(editor)
    # Re-run asynchronously
    await editor.app.run_in_thread(editor.spellchecker.check_text, editor.text)
    if editor.spellchecker.misspelled_words:
        editor.spellchecker.current_index = 0
        update_spellcheck_display(editor)

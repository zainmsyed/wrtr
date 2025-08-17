"""
Module: Spellcheck service for MarkdownEditor
Encapsulates spellcheck activation, deactivation, and display update.
"""
from pathlib import Path
from wrtr.logger import logger
from wrtr.services.spellcheck_service import get_spellchecker
from wrtr.interfaces.spellcheck_service import SpellCheckService


import asyncio

def start_spellcheck(editor):
    """Start spellcheck mode in the editor: activate UI then run load & check off main thread."""
    # Mark active and update UI immediately
    editor._spellcheck_active = True
    editor.status_bar.enter_spellcheck_mode()

    async def _spell_worker():
        """Background task to load dictionary and run check_text via executor."""
        loop = asyncio.get_running_loop()
        
        # Get singleton spellchecker (lazy-loaded and cached)
        if editor.spellchecker is None:
            editor.spellchecker = await get_spellchecker()
        
        # Perform the check_text in background
        misspelled = await loop.run_in_executor(
            None,
            editor.spellchecker.check_text,
            editor.text,
        )
        # Log number of issues found
        logger.debug(f"Spellcheck: found {len(misspelled)} issues")
        # Reset to first misspelled word and update UI
        if misspelled:
            editor.spellchecker.current_index = 0
        update_spellcheck_display(editor)

    # Schedule background worker
    asyncio.create_task(_spell_worker())


def exit_spellcheck(editor):
    """Exit spellcheck mode in the editor."""
    editor._spellcheck_active = False
    editor.status_bar.exit_spellcheck_mode()


def update_spellcheck_display(editor):
    """Update status bar and move cursor to current misspelled word."""
    misspelled = editor.spellchecker.misspelled_words
    logger.debug(f"update_spellcheck_display: spellcheck_mode={editor._spellcheck_active}, misspelled_words={len(misspelled)}")
    if misspelled:
        idx = editor.spellchecker.current_index
        word, suggestions, pos = (
            misspelled[idx][0],
            [s.term for s in misspelled[idx][1]],
            misspelled[idx][2]
        )
        logger.debug(f"Current misspelled word: {word}, suggestions: {suggestions}")
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

"""
Module: Keybindings for MarkdownEditor
This module contains the on_key handler logic extracted from the main editor class.
"""
from textual.events import Key
from logger import logger
from pathlib import Path
import re
from .spellcheck import start_spellcheck, exit_spellcheck, update_spellcheck_display

async def handle_key_event(editor, event: Key) -> None:
    """Handle key events for the MarkdownEditor."""
    # Exit markdown preview on Escape
    if hasattr(editor, 'markdown_viewer') and event.key == "escape":
        editor.restore_text_area()
        event.stop()
        return

    # Ctrl+W behavior: close panes
    if event.key == "ctrl+w" or getattr(event, 'name', None) == "ctrl_w":
        browser = editor.app.query_one("#file-browser")
        editor_a = editor.app.query_one("#editor_a")
        editor_b = editor.app.query_one("#editor_b")

        if editor.id == "editor_b":
            editor_b.visible = False
            editor_b.styles.display = 'none'
            editor_b.styles.width = '0%'
        elif editor.id == "editor_a":
            if editor_b.visible:
                editor_a.text = editor_b.text
                editor_a.set_path(editor_b._saved_path)
                editor_b.clear_status()
                editor_b.visible = False
                editor_b.styles.display = 'none'
                editor_b.styles.width = '0%'
            else:
                editor_a.clear_status()
                editor_a.text = ''
        # Recalculate layout
        editor.app.layout_manager.layout_resize()
        event.stop()
        return

    # F7 or Ctrl+F7 toggles spellcheck
    if event.key in ("f7", "ctrl+f7"):
        if not editor._spellcheck_active:
            start_spellcheck(editor)
        else:
            exit_spellcheck(editor)
        event.stop()
        return

    # Spellcheck navigation when active
    if editor._spellcheck_active:
        if event.key == "escape":
            exit_spellcheck(editor)
            event.stop()
            return
        if event.key == "f3":
            editor.spellchecker.next_word()
            update_spellcheck_display(editor)
            event.stop()
            return
        if event.key == "shift+f3":
            editor.spellchecker.previous_word()
            update_spellcheck_display(editor)
            event.stop()
            return
        if event.key in ("ctrl+a", getattr(event, 'name', None) == "ctrl_a"):
            current = editor.spellchecker.get_current_word()
            if current:
                editor.spellchecker.add_to_dictionary(current[0])
                editor._show_notification(f"'{current[0]}' added to dictionary.")
                misspelled = editor.spellchecker.check_text(editor.text)
                if misspelled:
                    editor.spellchecker.current_index = 0
                    update_spellcheck_display(editor)
                else:
                    exit_spellcheck(editor)
            event.stop()
            return
        if event.key == "ctrl+i":
            # Navigate to next misspelled word (ignore current)
            editor.spellchecker.next_word()
            update_spellcheck_display(editor)
            event.stop()
            return
    # No other handlers; let default processing occur

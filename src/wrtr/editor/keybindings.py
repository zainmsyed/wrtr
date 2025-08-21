"""
Module: Keybindings for MarkdownEditor
This module contains the on_key handler logic extracted from the main editor class.
"""
from textual.events import Key
from wrtr.logger import logger
from pathlib import Path
import re
from .spellcheck import start_spellcheck, exit_spellcheck, update_spellcheck_display
from wrtr.services.slash_command_service import SlashCommandService
from wrtr.services.template_service import TemplateService

async def process_slash_command(editor, event: Key) -> bool:
    """Process slash commands on Enter key"""
    if event.key != "enter":
        return False

    # Get current cursor position and document text (buffer is authoritative)
    row, col = editor.text_area.cursor_location
    if hasattr(editor.text_area, 'text') and getattr(editor.text_area, 'text') is not None:
        text = editor.text_area.text
    else:
        text = editor.buffer.get_text()

    lines = text.splitlines()
    if row >= len(lines):
        return False
    line = lines[row]

    # Parse the full line for a slash command and its args
    parsed = SlashCommandService.parse(line)
    if not parsed:
        return False
    command, args = parsed

    # Compute the command span (start_col .. end_col) to replace
    leading = re.match(r'^(\s*)', line).group(1)
    start_col = len(leading)

    # Handle dynamic multi-word date commands which occupy the whole phrase
    # e.g. '/next week', '/next month', '/4 days from today'
    if command == 'next' and args.lower() in ('week', 'month'):
        end_col = start_col + len(line.strip())
    elif re.match(r'^/\d+\s+days\s+from\s+today$', line.strip(), flags=re.IGNORECASE):
        end_col = start_col + len(line.strip())
    else:
        # For normal commands, replace only the command token and a single
        # following space (so '/today y' -> replace '/today ' and keep 'y')
        base = f"/{command}"
        end_col = start_col + len(base)
        # include one trailing space if present
        if len(line) > end_col and line[end_col] == ' ':
            end_col += 1

    # Only trigger when cursor is at or after the end of the command span
    if col < end_col:
        return False

    # Execute handler using the full line so handlers that expect args work
    replacement = await SlashCommandService.execute(line)
    if not replacement or replacement == line or replacement.startswith("Unknown command"):
        return False

    # Special sentinel triggers the UI template workflow
    if replacement == "__SHOW_TEMPLATE_MODAL__":
        # Show template selection modal, then variables modal, then insert
        try:
            from wrtr.modals.template_modal import TemplateModal
            from wrtr.modals.template_variables_modal import TemplateVariablesModal

            async def _show_and_apply():
                chosen = await editor.app.push_screen_wait(TemplateModal())
                if not chosen:
                    return
                ts = TemplateService()
                tpl = ts.get_template(chosen)
                if not tpl:
                    return
                # If template has variables, ask the user
                values = {}
                if tpl.variables:
                    vals = await editor.app.push_screen_wait(TemplateVariablesModal(tpl.variables))
                    if not vals:
                        return
                    values = vals
                rendered = ts.render(chosen, values)
                # Replace the original slash-command span (start_col..end_col)
                start_pos = (row, start_col)
                end_pos = (row, end_col)
                editor.view.replace_range(start_pos, end_pos, rendered)
                # Sync buffer
                if hasattr(editor.text_area, 'text') and getattr(editor.text_area, 'text') is not None:
                    try:
                        editor.buffer.set_text(editor.text_area.text)
                    except Exception:
                        pass
                # Move cursor after the replacement (keep same logic as below)
                rep_lines = rendered.splitlines()
                if len(rep_lines) == 1:
                    new_col = start_col + len(rep_lines[0])
                    editor.view.move_cursor(row, new_col)
                else:
                    new_row = row + len(rep_lines) - 1
                    new_col = len(rep_lines[-1])
                    editor.view.move_cursor(new_row, new_col)

            editor.app.run_worker(_show_and_apply(), exclusive=True)
            return True
        except Exception:
            # Fallback: do nothing and let normal handler proceed
            return False

    # Special sentinel triggers the UI snippet workflow
    if replacement == "__SHOW_SNIPPET_MODAL__":
        try:
            from wrtr.modals.snippet_modal import SnippetModal
            from wrtr.modals.snippet_variables_modal import SnippetVariablesModal
            from wrtr.services.snippet_service import SnippetService

            async def _show_and_apply_snippet():
                chosen = await editor.app.push_screen_wait(SnippetModal())
                if not chosen:
                    return
                ss = SnippetService()
                sn = ss.get_snippet(chosen)
                if not sn:
                    return
                values = {}
                if sn.variables:
                    vals = await editor.app.push_screen_wait(SnippetVariablesModal(sn.variables))
                    if not vals:
                        return
                    values = vals
                rendered = ss.render(chosen, values)
                # Replace the original slash-command span (start_col..end_col)
                start_pos = (row, start_col)
                end_pos = (row, end_col)
                editor.view.replace_range(start_pos, end_pos, rendered)
                # Sync buffer
                if hasattr(editor.text_area, 'text') and getattr(editor.text_area, 'text') is not None:
                    try:
                        editor.buffer.set_text(editor.text_area.text)
                    except Exception:
                        pass
                # Move cursor after the replacement
                rep_lines = rendered.splitlines()
                if len(rep_lines) == 1:
                    new_col = start_col + len(rep_lines[0])
                    editor.view.move_cursor(row, new_col)
                else:
                    new_row = row + len(rep_lines) - 1
                    new_col = len(rep_lines[-1])
                    editor.view.move_cursor(new_row, new_col)

            editor.app.run_worker(_show_and_apply_snippet(), exclusive=True)
            return True
        except Exception:
            return False

    # Replace only the command span; preserve the rest of the line
    start_pos = (row, start_col)
    end_pos = (row, end_col)
    editor.view.replace_range(start_pos, end_pos, replacement)

    # Sync buffer if TextArea exposes its text; tests' DummyView updates buffer directly
    if hasattr(editor.text_area, 'text') and getattr(editor.text_area, 'text') is not None:
        try:
            editor.buffer.set_text(editor.text_area.text)
        except Exception:
            pass

    # Move cursor after the replacement (keep it on same logical spot relative to replaced content)
    rep_lines = replacement.splitlines()
    if len(rep_lines) == 1:
        new_col = start_col + len(rep_lines[0])
        editor.view.move_cursor(row, new_col)
    else:
        new_row = row + len(rep_lines) - 1
        new_col = len(rep_lines[-1])
        editor.view.move_cursor(new_row, new_col)

    return True

async def handle_key_event(editor, event: Key) -> None:
    """Handle key events for the MarkdownEditor."""
    # Slash commands take priority
    if await process_slash_command(editor, event):
        if hasattr(event, 'stop') and callable(getattr(event, 'stop')):
            event.stop()
        return

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
                word = current[0].lower()
                editor.spellchecker.add_to_dictionary(word)
                editor.spellchecker.ignored_terms.add(word)  # Ignore the word for the session
                editor._show_notification(f"'{word}' added to dictionary and ignored.")
                prev_index = editor.spellchecker.current_index  # Save the current index
                misspelled = editor.spellchecker.check_text(editor.text)
                if misspelled:
                    # Restore the index and advance to the next word
                    editor.spellchecker.current_index = min(prev_index, len(misspelled) - 1)
                    editor.spellchecker.next_word()
                    update_spellcheck_display(editor)
                else:
                    exit_spellcheck(editor)
            event.stop()
            return
        # Ignore current spelling and skip all further occurrences
        if event.key == "ctrl+i":
            # Add current word to ignored terms for this session
            current = editor.spellchecker.get_current_word()
            if current:
                term = current[0].lower()
                editor.spellchecker.ignored_terms.add(term)
                prev_index = editor.spellchecker.current_index  # Save the current index
                misspelled = editor.spellchecker.check_text(editor.text)
                if misspelled:
                    # Restore the index and advance to the next word
                    editor.spellchecker.current_index = min(prev_index, len(misspelled) - 1)
                    editor.spellchecker.next_word()
                    update_spellcheck_display(editor)
                else:
                    exit_spellcheck(editor)
            event.stop()
            return
        # Suggestion keybindings: Ctrl+1 ... Ctrl+5 (normal)
        # Use Alt+1..5 (or alt+symbol variants) as the sole capitalization trigger.
        suggestion_keys = ("ctrl+1", "ctrl+2", "ctrl+3", "ctrl+4", "ctrl+5")
        alt_keys = ("alt+1", "alt+2", "alt+3", "alt+4", "alt+5")
        # Some terminals send alt with the shifted symbol instead of the number key
        alt_symbol_map = {
            "alt+!": 0,
            "alt+@": 1,
            "alt+#": 2,
            "alt+$": 3,
            "alt+%": 4,
        }

        if event.key in suggestion_keys or event.key in alt_keys or event.key in alt_symbol_map:
            capitalize = False
            if event.key in suggestion_keys:
                idx = int(event.key.split('+')[-1]) - 1
            elif event.key in alt_keys:
                idx = int(event.key.split('+')[-1]) - 1
                capitalize = True
            else:
                idx = alt_symbol_map.get(event.key)
                capitalize = True

            current = editor.spellchecker.get_current_word()
            if current and idx is not None and idx < len(current[1]):
                suggestion = current[1][idx].term
                if capitalize and suggestion:
                    suggestion = suggestion[0].upper() + suggestion[1:]
                word, _, pos = current
                word_start = pos
                word_end = pos + len(word)
                start = editor._convert_text_position_to_cursor(word_start)
                end = editor._convert_text_position_to_cursor(word_end)
                # Replace in TextArea and sync buffer
                editor.view.replace_range(start, end, suggestion)
                editor.buffer.set_text(editor.text_area.text)
                # Save the current index before rechecking
                prev_index = editor.spellchecker.current_index
                # Re-run spellcheck
                misspelled = editor.spellchecker.check_text(editor.text)
                if misspelled:
                    # If there are still misspelled words, move to the next one (or stay at last if at end)
                    if prev_index < len(misspelled) - 1:
                        editor.spellchecker.current_index = prev_index
                    else:
                        editor.spellchecker.current_index = len(misspelled) - 1
                    update_spellcheck_display(editor)
                else:
                    # No more misspelled words, exit spellcheck
                    exit_spellcheck(editor)
            event.stop()
            return
    # No other handlers; let default processing occur

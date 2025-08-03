"""
Module: Editor Pane
"""
from textual.widgets import TextArea
from textual.containers import Vertical
from textual.events import Key
from pathlib import Path
from textual.timer import Timer
from status_bar import EditorStatusBar
from typing import Generator
from textual.widget import Widget
from tree_sitter_markdown import language
from spellcheck import MarkdownSpellchecker


class MarkdownEditor(Vertical):
    """
    Markdown editor widget with syntax highlighting, auto-save,
    and a status bar that does NOT overlap the last line.
    """
    def __init__(self, id=None):
        super().__init__(id=id)
        self._saved_path: Path | None = None
        self._save_timer: Timer | None = None
        self._debounce_delay: float = 1.0

        # Inject spellchecker
        self.spellchecker = MarkdownSpellchecker(
            dictionary_path=str(Path(__file__).parent / "data" / "dictionary" / "frequency_dictionary_en_82_765.txt"),
            user_dictionary_path=str(Path(__file__).parent / "data" / "dictionary" / "user_dictionary.txt")
        )
        self._spellcheck_active = False  # Track spellcheck mode state

    def compose(self) -> Generator[Widget, None, None]:
        """Inner composition: TextArea + StatusBar."""
        self.text_area = TextArea(text="", language="markdown")
        self.text_area.styles.padding = (1, 2)  # Add padding: 1 line vertical, 2 spaces horizontal
        self.status_bar = EditorStatusBar()
        yield self.text_area
        yield self.status_bar

    # ── forward the public helpers to the inner TextArea ------------
    @property
    def text(self) -> str:
        return self.text_area.text

    @text.setter
    def text(self, value: str) -> None:
        self.text_area.text = value

    def load_text(self, value: str) -> None:
        self.text_area.load_text(value)

    def set_path(self, path: Path) -> None:
        self._saved_path = path
        self.status_bar.file_path = path

    def clear_status(self) -> None:
        if self._save_timer:
            self._save_timer.stop()
            self._save_timer = None
        self._saved_path = None
        self.status_bar.file_path = None
        self.status_bar.saved = True
        self.text_area.load_text("")
        self.status_bar.refresh_stats()
    # ---------------------------------------------------------------

    def _schedule_auto_save(self) -> None:
        if self._save_timer:
            self._save_timer.stop()
        self._save_timer = self.set_timer(
            self._debounce_delay, self._auto_save, name="autosave"
        )

    def _auto_save(self) -> None:
        if self._saved_path:
            self._saved_path.write_text(self.text)
            self.status_bar.saved = True
            try:
                # Commented out auto-save notification for quieter operation
                # self.app.notify(f"Auto-saved {self._saved_path.name}")
                pass
            except Exception:
                pass
        else:
            # New file: mark as unsaved, but do not auto-launch Save As
            self.status_bar.saved = False

    def on_text_area_changed(self, event) -> None:
        self.status_bar.refresh_stats()
        self._schedule_auto_save()
        self.status_bar.saved = False

    async def on_key(self, event: Key) -> None:
        """Handle key events for spellcheck functionality."""
        if event.key == "ctrl+f7":
            # Toggle spellcheck mode
            if not self._spellcheck_active:
                self._start_spellcheck()
            else:
                self._exit_spellcheck()
            event.stop()
        elif self._spellcheck_active:
            if event.key == "f3":
                # Navigate to next misspelled word
                current_word = self.spellchecker.next_word()
                print("Next word:", current_word)
                self._update_spellcheck_display()  # Update display
                event.stop()
            elif event.key == "shift+f3":
                # Navigate to previous misspelled word
                current_word = self.spellchecker.previous_word()
                print("Previous word:", current_word)
                self._update_spellcheck_display()  # Update display
                event.stop()
            elif event.key == "ctrl+a":
                # Add current word to dictionary
                current_word = self.spellchecker.get_current_word()
                if current_word:
                    self.spellchecker.add_to_dictionary(current_word[0])
                    print(f"Added '{current_word[0]}' to dictionary.")
                event.stop()
            elif event.key == "ctrl+i":
                # Ignore current word
                current_word = self.spellchecker.get_current_word()
                if current_word:
                    self.spellchecker.ignore_word(current_word[0])
                    print(f"Ignored '{current_word[0]}'.")
                event.stop()
            elif event.key.startswith("ctrl+") and event.key[-1].isdigit():
                # Replace current word with a suggestion using Ctrl+1 to Ctrl+5
                suggestion_index = int(event.key[-1]) - 1
                current_word = self.spellchecker.get_current_word()
                if current_word and suggestion_index < len(current_word[1]):
                    suggestion = current_word[1][suggestion_index].term
                    print(f"Replaced '{current_word[0]}' with '{suggestion}'.")

                    # Find the start and end positions of the current word
                    word_start = self.text.find(current_word[0])
                    word_end = word_start + len(current_word[0])

                    # Replace the word in the TextArea
                    self.text_area.replace(
                        start=self._convert_text_position_to_cursor(word_start),  # Start location
                        end=self._convert_text_position_to_cursor(word_end),      # End location
                        insert=suggestion                                         # Replacement text
                    )

                    # Refresh the TextArea to reflect changes
                    self.text_area.refresh()
                event.stop()
            elif event.key == "escape":
                # Exit spellcheck mode
                self._exit_spellcheck()
                event.stop()

    def _start_spellcheck(self):
        """Start spellcheck mode."""
        self._spellcheck_active = True
        print("Spellcheck mode activated.")

        # Check the current text for misspelled words
        misspelled_words = self.spellchecker.check_text(self.text)
        print("Misspelled words:", misspelled_words)

        # Update the status bar with spellcheck mode
        self.status_bar.enter_spellcheck_mode()
        if misspelled_words:
            current_word = self.spellchecker.get_current_word()
            self.status_bar.set_spellcheck_info(
                word=current_word[0],
                suggestions=[s.term for s in current_word[1]],
                progress=(1, len(misspelled_words))
            )
        else:
            self.status_bar.set_spellcheck_info(None, [], (0, 0))

    def _exit_spellcheck(self):
        """Exit spellcheck mode."""
        self._spellcheck_active = False
        print("Spellcheck mode deactivated.")

        # Reset the status bar
        self.status_bar.exit_spellcheck_mode()

    def _convert_cursor_to_text_position(self, cursor_row: int, cursor_col: int) -> int:
        """Convert TextArea cursor position to absolute text position."""
        lines = self.text.split('\n')
        pos = 0

        for i in range(min(cursor_row, len(lines))):
            if i < cursor_row:
                pos += len(lines[i]) + 1  # +1 for newline
            else:
                pos += min(cursor_col, len(lines[i]))
                break

        if cursor_row < len(lines):
            pos += min(cursor_col, len(lines[cursor_row]))

        return pos

    def _convert_text_position_to_cursor(self, text_pos: int) -> tuple[int, int]:
        """Convert absolute text position to TextArea cursor position."""
        lines = self.text.split('\n')
        current_pos = 0

        for line_num, line in enumerate(lines):
            line_end = current_pos + len(line)

            if text_pos <= line_end:
                col = text_pos - current_pos
                return (line_num, col)

            current_pos = line_end + 1  # +1 for newline

        # If position is beyond text, go to end
        if lines:
            return (len(lines) - 1, len(lines[-1]))
        return (0, 0)

    def _update_spellcheck_display(self):
        """Update the status bar with current spellcheck info and move cursor to the word."""
        current_word = self.spellchecker.get_current_word()
        if current_word:
            # Update status bar with current word and suggestions
            progress = (self.spellchecker.current_index + 1, len(self.spellchecker.misspelled_words))
            self.status_bar.set_spellcheck_info(
                word=current_word[0],
                suggestions=[s.term for s in current_word[1]],
                progress=progress
            )

            # Move cursor to the misspelled word
            word_start = self.text.find(current_word[0])
            if word_start != -1:
                cursor_row, cursor_col = self._convert_text_position_to_cursor(word_start)
                print(f"Calculated cursor position: row={cursor_row}, col={cursor_col}")
                self.text_area.cursor_location = (cursor_row, cursor_col)
                print(f"Cursor position set to: {self.text_area.cursor_location}")

                # Ensure the cursor is visible
                self.text_area.scroll_cursor_visible(center=True)

                # Ensure the TextArea is focused and refreshed
                self.text_area.focus()
                self.text_area.refresh()
        else:
            # Clear status bar if no misspelled words
            self.status_bar.set_spellcheck_info(None, [], (0, 0))

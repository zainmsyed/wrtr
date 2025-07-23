"""
Module: Theme Management
"""
from textual.app import ComposeResult
import json
from pathlib import Path

class ThemeManager:
    """
    Handle application theming using Textual's built-in themes.
    """
    CONFIG_DIR   = Path.home() / ".config" / "terminal-writer"
    SETTINGS     = CONFIG_DIR / "settings.json"

    def __init__(self):
        self.available_themes = ["dark", "light"]  # placeholders for Textual themes
        self.current_theme = "dark"

    def list_themes(self) -> list[str]:
        """Return a list of available theme names."""
        return self.available_themes

    def apply_theme(self, name: str) -> None:
        """Switch to the specified theme at runtime."""
        if name in self.available_themes:
            self.current_theme = name
            # TODO: trigger Textual theme update
        else:
            raise ValueError(f"Theme '{name}' not available")

    @classmethod
    def load(cls) -> str | None:
        """Return the last saved theme, or None if first run."""
        try:
            return json.loads(cls.SETTINGS.read_text())["theme"]
        except (FileNotFoundError, KeyError):
            return None

    @classmethod
    def save(cls, name: str) -> None:
        """Persist the chosen theme name."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.SETTINGS.write_text(json.dumps({"theme": name}))

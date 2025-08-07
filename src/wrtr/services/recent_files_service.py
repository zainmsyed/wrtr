from __future__ import annotations
import json
from pathlib import Path
from typing import List

class RecentFilesService:
    """Service to manage recent files list."""
    MAX = 10
    FILE = Path.home() / ".local/share/wrtr/recent.json"

    @classmethod
    def load(cls) -> List[Path]:
        """
        Load the list of recent files from persistent storage.

        Returns:
            List[Path]: A list of Paths for recent files, empty if none or on error.
        """
        if not cls.FILE.exists():
            return []
        try:
            with cls.FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return [Path(p) for p in data]
        except Exception:
            return []

    @classmethod
    def add(cls, path: Path) -> None:
        """
        Add a file to the recent list, ensuring it appears at the top, and persist.

        Args:
            path (Path): The file path to add to recents.
        """
        recents = cls.load()
        try:
            recents.remove(path)
        except ValueError:
            pass
        recents.insert(0, path)
        recents = recents[: cls.MAX]
        cls.FILE.parent.mkdir(parents=True, exist_ok=True)
        with cls.FILE.open("w", encoding="utf-8") as f:
            json.dump([str(p) for p in recents], f)

    @classmethod
    def exists(cls, path: Path) -> bool:
        """
        Check if a given path exists on the filesystem.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        return path.exists()

    @classmethod
    def get_recent(cls) -> List[Path]:
        """Return up to MAX existing recent files."""
        return [p for p in cls.load() if p.exists()][: cls.MAX]

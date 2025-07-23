from __future__ import annotations
import json
from pathlib import Path
from typing import List

class RecentManager:
    """Tiny wrapper around a JSON file that keeps N most-recent files."""
    MAX = 5
    FILE = Path.home() / ".local/share/wrtr/recent.json"

    @classmethod
    def load(cls) -> List[Path]:
        if not cls.FILE.exists():
            return []
        try:
            with cls.FILE.open() as f:
                return [Path(p) for p in json.load(f)]
        except Exception:
            return []

    @classmethod
    def add(cls, path: Path) -> None:
        """Add file to top, trim to MAX, persist atomically."""
        recents = cls.load()
        try:
            recents.remove(path)  # avoid duplicates
        except ValueError:
            pass
        recents.insert(0, path)
        recents = recents[: cls.MAX]
        cls.FILE.parent.mkdir(parents=True, exist_ok=True)
        with cls.FILE.open("w") as f:
            json.dump([str(p) for p in recents], f)

    @classmethod
    def exists(cls, path: Path) -> bool:
        return path.exists()
    
    @classmethod
    def get_recent(cls) -> List[Path]:
        """Return up to MAX existing recent files."""
        # Filter out paths that no longer exist
        return [p for p in cls.load() if p.exists()][: cls.MAX]

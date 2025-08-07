import json
from pathlib import Path
import tempfile

_FILE = Path.home() / ".wrtr" / "favorites.json"
_FILE.parent.mkdir(exist_ok=True)

def add(p: Path) -> None:
    favs = get()
    if p not in favs:
        favs.insert(0, p)
    _FILE.write_text(json.dumps([str(p) for p in favs[:15]]))

def remove(p: Path) -> None:
    favs = [x for x in get() if x != p]
    _FILE.write_text(json.dumps([str(p) for p in favs]))

def get() -> list[Path]:
    try:
        # Exclude any stale temp symlink directories (e.g. wrtr-fav-*)
        raw = json.loads(_FILE.read_text())
        favs: list[Path] = []
        for p in raw:
            path = Path(p)
            # Skip temp favorites folders
            if "wrtr-fav-" in str(path):
                continue
            if path.is_dir():
                favs.append(path)
        return favs
    except Exception:
        return []

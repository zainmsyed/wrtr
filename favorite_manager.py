import json
from pathlib import Path

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
        return [Path(p) for p in json.loads(_FILE.read_text()) if Path(p).is_dir()]
    except Exception:
        return []

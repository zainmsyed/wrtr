"""
Module: File Browser Pane
"""
from textual.widgets import DirectoryTree
from textual.events import Key
from textual.message import Message
from favorite_manager import get as get_favorites, add, remove   # NEW
from pathlib import Path
from dataclasses import dataclass
import tempfile, shutil

@dataclass
class _FakeEntry:
    path: Path
    def is_dir(self) -> bool:
        return self.path.is_dir()

class FileBrowser(DirectoryTree):
    """DirectoryTree with favorites (f) and 3-way root toggle (ctrl+o)."""

    class FileOpen(Message):
        def __init__(self, path: str, target: str) -> None:
            super().__init__()
            self.path = path
            self.target = target

    class FileCreate(Message):
        def __init__(self, parent_dir: Path, name: str) -> None:
            super().__init__()
            self.parent_dir = parent_dir
            self.name = name

    class FileDelete(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def __init__(self, path: str = ".", id: str = None) -> None:
        super().__init__(path, id=id)
        self._cycle = 1                       # 0=/  1=wrtr  2=favorites
        self._roots = [
            Path("/"),
            Path(__file__).with_suffix('').parent / "wrtr",
            None,                             # placeholder for favorites
        ]
        self._tmp_fav_dir = None        # Path to temp symlink dir

    # ---------------------------------------------------------
    # ctrl+o cycles root / wrtr / favorites
    # ---------------------------------------------------------
    def cycle_root(self) -> None:
        self._cycle = (self._cycle + 1) % 3

        # Clean up old temp dir if it exists
        if self._tmp_fav_dir and self._tmp_fav_dir.exists():
            shutil.rmtree(self._tmp_fav_dir)
            self._tmp_fav_dir = None

        if self._cycle == 2:            # favorites
            favs = get_favorites()
            if not favs:
                self.app.notify("No favorites yet", severity="warning")
                self._cycle = 0         # skip back to root
                self.cycle_root()
                return
            # create temp dir with symlinks
            self._tmp_fav_dir = Path(tempfile.mkdtemp(prefix="wrtr-fav-"))
            for fav in favs:
                if fav.is_dir():
                    (self._tmp_fav_dir / fav.name).symlink_to(fav.absolute())
            self.path = self._tmp_fav_dir
            self.reload()
            self.app.notify("Root → Favorites", severity="info")
        else:                           # normal folder
            self.path = self._roots[self._cycle]
            self.reload()
            self.app.notify(f"Root → {self.path}", severity="info")

    # ---------------------------------------------------------
    # f key toggles favorite
    # ---------------------------------------------------------
    async def on_key(self, event: Key) -> None:
        if event.key == "f":
            node = self.cursor_node
            if not node:
                return
            path = Path(node.data.path)
            if not path.is_dir():
                self.app.notify("Only folders can be favorited", severity="warning")
                event.stop()
                return
            if path in get_favorites():
                remove(path)
                self.app.notify(f"Removed favorite: {path.name}")
            else:
                add(path)
                self.app.notify(f"Marked favorite: {path.name}")
            # refresh if in favorites view
            if self._cycle == 2:
                self.cycle_root()
            event.stop()
            return
        # let the event continue to DirectoryTree

    # ---------------------------------------------------------
    # Forward DirectoryTree events to our own FileOpen
    # ---------------------------------------------------------
    async def on_directory_tree_file_selected(self, event):
        """Open any selected file in the focused editor."""
        event.stop()
        self.post_message(self.FileOpen(str(event.path), "editor_a"))

    async def on_directory_tree_directory_selected(self, event):
        """Let DirectoryTree expand folders normally."""
        # allow DirectoryTree to do its thing
        pass

"""
Module: File Browser Pane
"""
from textual.widgets import DirectoryTree
from textual.events import Key
from textual.message import Message
from textual.message_pump import MessagePump
from pathlib import Path
from screens.save_as_screen import SaveAsScreen
from screens.confirm_screen import ConfirmScreen
from screens.rename_screen import RenameScreen  # NEW import
from editor import MarkdownEditor
from screens.save_as_screen import SaveAsScreen
from screens.confirm_screen import ConfirmScreen
from recent_manager import RecentManager  # add import
from favorite_manager import get as get_favorites, add, remove
import tempfile
import shutil  # add near top imports
from logger import logger

class FileBrowser(DirectoryTree):
    """Custom file browser widget (list-based)"""
    def __init__(self, path: str = "/", id: str = None) -> None:
        """
        Initialize FileBrowser at the given root path.
        """
        super().__init__(path, id=id)
        self.current_path: str = path  # track currently highlighted path
        self._cycle = 0
        self._roots = [
            Path(__file__).with_suffix('').parent / "wrtr",  # wrtr folder
            None,  # Favorites view
            Path("/"),  # Computer root
        ]
        self._tmp_fav_dir = None
        self.reload()

    class FileOpen(Message):
        """Message sent when a file is requested to open in an editor pane"""
        def __init__(self, path: str, target: str) -> None:
            super().__init__()
            self.path = path
            self.target = target

    class FileCreate(Message):
        """Sent when user wants to create a new file."""
        def __init__(self, parent_dir: Path, name: str) -> None:
            super().__init__()
            self.parent_dir = parent_dir
            self.name = name

    class FileDelete(Message):
        """Sent when user wants to delete a file or folder."""
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path
    
    # Worker methods for screens
    async def _worker_create(self, parent_dir: Path) -> None:
        """Worker to show SaveAsScreen and post FileCreate."""
        result = await self.app.switch_screen_wait(
            SaveAsScreen(default_filename="untitled.md", default_dir=parent_dir)
        )
        if result:
            # Determine file name and default to .md extension if none provided
            filename = result.name
            if not Path(filename).suffix:
                filename += ".md"
            new_file = parent_dir / filename
            try:
                new_file.write_text("")
                self.reload()
                # Open in primary editor
                self.post_message(self.FileOpen(str(new_file), "editor_a"))
            except Exception as e:
                self.app.notify(f"File creation failed: {e}", severity="error")

    async def _worker_delete(self, path: Path) -> None:
        """Worker to show ConfirmScreen and post FileDelete if confirmed."""
        kind = "folder" if path.is_dir() else "file"
        confirmed = await self.app.switch_screen_wait(
            ConfirmScreen(f"Delete {kind} “{path.name}”?")
        )
        if confirmed:
            self.post_message(self.FileDelete(path))
    
    async def _worker_create_folder(self, parent_dir: Path) -> None:
        """Worker to prompt for new folder name and create it."""
        result = await self.app.switch_screen_wait(
            SaveAsScreen(
                default_filename="new_folder",
                default_dir=parent_dir,
                title="New folder",
                add_extension=False,
            )
        )
        if result:
            # Strip any '.md' extension that SaveAsScreen may have added
            name = result.name
            if name.lower().endswith('.md'):
                name = name[: -3]
            new_dir = parent_dir / name
            try:
                new_dir.mkdir(parents=True, exist_ok=False)
                self.app.notify(f"Created folder → {new_dir.name}")
                self.reload()
            except Exception as e:
                self.app.notify(f"Folder creation failed: {e}", severity="error")

    async def _worker_rename(self, old_path: Path) -> None:
        """Worker to show RenameScreen and perform rename."""
        # Ensure old_path is a Path and exists
        old_path = Path(old_path)
        if not old_path.exists():
            self.app.notify(f"Rename failed: source not found: {old_path}", severity="error")
            return
        new_name = await self.app.switch_screen_wait(
            RenameScreen(old_path)
        )
        if new_name:
            new_path = old_path.parent / new_name
            # Ensure target directory exists
            if not new_path.parent.exists():
                new_path.parent.mkdir(parents=True)
            try:
                old_path.rename(new_path)
                self.reload()
                self.app.notify(f"Renamed → {new_name}")
            except Exception as e:
                self.app.notify(f"Rename failed: {e}", severity="error")

    def cycle_root(self) -> None:
        # Advance cycle: 0=wrtr, 1=favorites, 2=computer root
        self._cycle = (self._cycle + 1) % 3
        # Handle favorites view (show empty view if no favorites)
        if self._cycle == 1:
            favs = get_favorites()
            # Prepare a consistent favorites folder in system temp
            fav_dir = Path(tempfile.gettempdir()) / "favorites"
            if fav_dir.exists():
                shutil.rmtree(fav_dir)
            fav_dir.mkdir()
            self._tmp_fav_dir = fav_dir
            # Populate symlinks for each favorite
            for fav in favs:
                if fav.is_dir():
                    link_path = fav_dir / fav.name
                    try:
                        link_path.symlink_to(fav.absolute())
                    except FileExistsError:
                        continue
            # Point tree at the 'favorites' temp folder
            self.path = fav_dir
            self.reload()
                # notification suppressed for root toggle
            return
        # Handle wrtr folder or computer root
        self.path = self._roots[self._cycle]
        self.reload()
            # notification suppressed for root toggle

    def _refresh_fav_view(self) -> None:
        """Clear old temp directory and reload favorites view."""
        if self._tmp_fav_dir and self._tmp_fav_dir.exists():
            shutil.rmtree(self._tmp_fav_dir)
        # Reset cycle index to point just before favorites
        self._cycle = 0
        self.cycle_root()

    async def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        """Handle tree node selection."""
        event.stop()
        path = event.node.data.path
        if path.is_file():
            # TODO: Add a way to detect Shift key or use a different keybind
            target = "editor_a"  # Default to editor_a for now
            logger.debug(f"post_message opening file {path} in {target}")
            self.post_message(self.FileOpen(str(path), target))

    async def on_node_highlighted(self, event) -> None:
        """Update and log current_path when a tree node is highlighted"""
        try:
            self.current_path = event.node.data
            logger.debug(f"on_node_highlighted new current_path={self.current_path}")
        except Exception as e:
            logger.debug(f"on_node_highlighted error: {e}")

    async def on_key(self, event: Key) -> None:
        """Handle new file (n), delete, rename (r), favorite (f), and file-open keys."""
        # Favorite/unfavorite folders
        if event.key == "f":
            node = self.cursor_node
            if not node:
                return
            folder = Path(node.data.path).resolve()
            if not folder.is_dir():
                self.app.notify("Only folders can be favorited", severity="warning")
                event.stop()
                return
            if folder in get_favorites():
                remove(folder)
                self.app.notify(f"Removed favorite: {folder.name}", severity="info")
            else:
                add(folder)
                self.app.notify(f"Marked favorite: {folder.name}", severity="info")
            # Refresh favorites view if active
            if self._cycle == 1:
                self._refresh_fav_view()
            event.stop()
            return
        # Rename file or folder
        if event.key == "r":
            node = self.cursor_node
            if not node:
                return
            path = node.data.path
            self.app.run_worker(self._worker_rename(path))
            event.stop()
            return

        # New file
        if event.key == "n":
            node = self.cursor_node
            if not node:
                return
            target_path = node.data.path
            parent_dir = target_path if target_path.is_dir() else target_path.parent
            # Run screen prompt in a worker
            self.app.run_worker(self._worker_create(parent_dir))
            event.stop()
            return

        # Shift+N → New folder
        if event.key == "N":
            node = self.cursor_node
            if not node:
                return
            target_path = node.data.path
            parent_dir = target_path if target_path.is_dir() else target_path.parent
            # Run folder-creation prompt in a worker
            self.app.run_worker(self._worker_create_folder(parent_dir))
            event.stop()
            return

        # Delete file or folder
        if event.key == "delete":
            node = self.cursor_node
            if not node:
                return
            path = node.data.path
            # Run delete confirmation in a worker
            self.app.run_worker(self._worker_delete(path))
            event.stop()
            return

        # Only handle file-open keystrokes (Enter and Ctrl+M) for file nodes
        if event.key not in ("enter", "ctrl+m"):
            return
        node = self.cursor_node
        if not node or not node.data.path.is_file():
            return
        path = node.data.path
        path_str = str(path)
        try:
            content = Path(path_str).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip binary or unreadable files
            self.app.notify(f"Cannot open non-text file: {path.name}", severity="warning")
            return
        app = self.app

        if event.key == "enter":
            # Enter → open in focused editor (or editor_a)
            focused = app.focused
            editor = focused if isinstance(focused, MarkdownEditor) else app.query_one("#editor_a")
            editor.load_text(content)
            editor.set_path(Path(path_str))
            editor.focus()
            RecentManager.add(Path(path_str))
            event.stop()
        elif event.key == "ctrl+m":
            # Ctrl+M → always open in editor_b
            editor = app.query_one("#editor_b")
            app.query_one("#editor_a").visible = True
            app.query_one("#editor_b").visible = True
            # Update layout via LayoutManager instead of deprecated method
            app.layout_manager.layout_resize()
            editor.load_text(content)
            editor.set_path(Path(path_str))
            editor.focus()
            RecentManager.add(Path(path_str))
            event.stop()
        else:
            return

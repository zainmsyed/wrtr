import time
from pathlib import Path
from wrtr.theme import ThemeManager
from wrtr.screens.home_screen import HomeScreen
from wrtr.file_browser import FileBrowser
from wrtr.editor import MarkdownEditor
from textual.app import App
from textual.widgets import Header, Footer
import warnings
import sys

# Suppress RuntimeWarning for unawaited coroutines
warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine '.*' was never awaited")

class StartupProfiler:
    """
    A utility class to profile the startup time of the application.
    """
    def __init__(self):
        self.timings = []

    def log(self, message):
        """Log the current time with a message."""
        self.timings.append((message, time.time()))

    def report(self):
        """Print a report of the timings."""
        print("\nStartup Profiling Report:")
        for i in range(1, len(self.timings)):
            prev_message, prev_time = self.timings[i - 1]
            message, current_time = self.timings[i]
            print(f"{prev_message} -> {message}: {current_time - prev_time:.4f} seconds")

class StartupProfilerApp(App):
    """
    A minimal Textual application to profile the startup process.
    """
    async def on_mount(self) -> None:
        profiler = StartupProfiler()

        # Start profiling
        print("Startup Profiler is running...")  # Debugging log
        profiler.log("Start application")

        # Simulate project-root wrtr directory creation
        DEFAULT_DIR = Path.cwd() / "wrtr"
        profiler.log("Before directory creation")
        DEFAULT_DIR.mkdir(exist_ok=True)
        profiler.log("After directory creation")

        # Simulate theme loading
        profiler.log("Before theme loading")
        ThemeManager.load()
        profiler.log("After theme loading")

        # Simulate HomeScreen initialization
        profiler.log("Before HomeScreen initialization")
        HomeScreen()
        profiler.log("After HomeScreen initialization")

        # Simulate widget layout setup
        profiler.log("Before widget layout setup")
        file_browser = FileBrowser(path=str(DEFAULT_DIR), id="file-browser")
        editor_a = MarkdownEditor(id="editor_a")
        editor_b = MarkdownEditor(id="editor_b")
        profiler.log("After widget layout setup")

        # Print the profiling report
        profiler.report()
        sys.stdout.flush()  # Ensure output is flushed before exiting

        # Exit the application after printing the report
        self.exit()

    def compose(self):
        """Override compose to prevent rendering any UI by returning an empty iterable."""
        return []

if __name__ == "__main__":
    StartupProfilerApp().run()

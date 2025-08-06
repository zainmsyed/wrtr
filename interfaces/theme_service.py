"""
Protocol definitions for theme management service.
"""
from typing import Protocol, Optional, List, runtime_checkable

@runtime_checkable
class ThemeService(Protocol):
    """Defines the interface for theming service."""
    def list_themes(self) -> List[str]:
        """Return a list of available theme names."""
        ...

    def apply_theme(self, name: str) -> None:
        """Apply the specified theme."""
        ...

    def load(self) -> Optional[str]:
        """Return the last saved theme name, or None if not set."""
        ...

    def save(self, name: str) -> None:
        """Persist the specified theme name."""
        ...

"""
Protocol definitions for workspace management service.
"""
from typing import Protocol, Any

class WorkspaceService(Protocol):
    """Defines the interface for managing multiple workspace states."""
    def save(self, number: int) -> Any:
        """
        Persist the given workspace slot to disk.

        Args:
            number (int): Workspace slot number to save.
        """
        ...

    def load(self, number: int) -> Any:
        """
        Load and return the workspace state for the given slot number.

        Args:
            number (int): Workspace slot number to load.

        Returns:
            Any: The workspace state object.
        """
        ...

    def switch(self, number: int) -> Any:
        """
        Persist current state, then switch and load the target workspace slot.

        Args:
            number (int): Workspace slot number to switch to.

        Returns:
            Any: The loaded workspace state.
        """
        ...

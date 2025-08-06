"""
Protocol definitions for workspace management service.
"""
from typing import Protocol, Any

class WorkspaceService(Protocol):
    """Defines the interface for managing multiple workspace states."""
    def save(self, number: int) -> Any:
        """Persist the workspace state identified by number."""
        ...

    def load(self, number: int) -> Any:
        """Load and return the workspace state identified by number."""
        ...

    def switch(self, number: int) -> Any:
        """Switch to the workspace identified by number."""
        ...

from __future__ import annotations
from typing import Generic, TypeVar

from textual.screen import ModalScreen
from wrtr.modals.palette_modal import PaletteModal

T = TypeVar("T")

class PaletteDismissModal(PaletteModal, ModalScreen[T], Generic[T]):
    """Same look, but Escape calls `self.dismiss`."""

    def action_esc(self) -> None:
        self.dismiss(self._default_dismiss_value())

    def _default_dismiss_value(self) -> T:
        """Override if you need a non-None default."""
        return None   # type: ignore
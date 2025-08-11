from textual.message import Message

class BacklinkClicked(Message):
    """Event emitted when a backlink [[target]] is clicked."""
    def __init__(self, sender, target: str) -> None:
        super().__init__()
        self.sender = sender
        self.target = target

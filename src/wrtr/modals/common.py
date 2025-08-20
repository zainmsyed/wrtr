"""
Common imports for modal screens to reduce import duplication.

This module consolidates frequently imported Textual components used across modal screens,
reducing import boilerplate and ensuring consistency.
"""

# Modal screen essentials
from textual.screen import ModalScreen

# Layout containers for modal centering and structure
from textual.containers import Center, Middle, Vertical, Horizontal

# Common widgets used in modals
from textual.widgets import Button, Label, Input, Static, ListView, ListItem

# Events handling
from textual.events import Key

# Export all commonly used components
__all__ = [
    # Screen types
    'ModalScreen',
    
    # Containers for layout
    'Center', 'Middle', 'Vertical', 'Horizontal',
    
    # Common widgets
    'Button', 'Label', 'Input', 'Static', 'ListView', 'ListItem',
    
    # Events
    'Key'
]

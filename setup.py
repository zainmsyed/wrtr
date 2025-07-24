import sys
import os
from cx_Freeze import setup, Executable
import tree_sitter_markdown

# Determine the location of the tree-sitter grammar binding
binding_src = os.path.join(os.path.dirname(tree_sitter_markdown.__file__), '_binding.abi3.so')

# Build options for cx_Freeze
build_exe_options = {
    'packages': ['textual', 'rapidfuzz', 'tree_sitter==0.24.0'],
    'include_files': [
        # Include the Tree-sitter Markdown binding
        (binding_src, os.path.join('tree_sitter_markdown', '_binding.abi3.so')),
        # Include CSS and docs
        ('styles.css', 'styles.css'),
        ('docs/Key_Binding_Cheat_Sheet.md', os.path.join('docs', 'Key_Binding_Cheat_Sheet.md')),
        ('docs/Markdown_Cheat_Sheet.md', os.path.join('docs', 'Markdown_Cheat_Sheet.md')),
        ('docs/Welcome.md', os.path.join('docs', 'Welcome.md')),
    ],
    'excludes': ['tkinter'],
}

# Base setting for console applications
base = None
if sys.platform == 'win32':
    base = 'Console'

setup(
    name='wrtr',
    version='0.1',
    description='Terminal Writing Application',
    options={'build_exe': build_exe_options},
    executables=[Executable('main.py', base=base)],
)

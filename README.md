# Terminal Writer

A terminal-based writing application built with the Textual Python framework. Terminal Writer provides a clean, distraction-free writing environment with dual-pane markdown editing, file management, and workspace organization.

## Features

- **Dual-Pane Editing**: Two synchronized markdown editors for side-by-side editing
- **File Browser**: Traditional tree-view file browser with keyboard navigation
- **Auto-Save**: Automatic saving with debounced writes (5 seconds after last edit)
- **Fuzzy Search**: Fast file and content search powered by RapidFuzz
- **Markdown Support**: Full syntax highlighting for markdown files
- **Theme Support**: Multiple built-in themes from Textual
- **Keyboard-First Design**: Comprehensive keyboard shortcuts for all operations

## Quick Start

### Install

Follow these steps to build and run the binary locally:

```bash
# Clone the repository
git clone https://github.com/zainmsyed/wrtr.git
cd wrtr

# Set up virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS
pip install -r requirements.txt

# Build the binary
pip install pyinstaller
env/bin/activate && pyinstaller --onefile main.py

# (On Linux/macOS) Make the binary executable and run it
chmod +x dist/main
./dist/main
```

## Documentation

- [Welcome Guide](docs/Welcome.md)
- [Markdown Cheat Sheet](docs/Markdown_Cheat_Sheet.md)
- [Key Bindings](docs/Key_Binding_Cheat_Sheet.md)

---

**Terminal Writer** - Write better, write faster, in your terminal.

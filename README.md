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

### Install UV (once per machine)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone & Install Dependencies

```bash
git clone https://github.com/zainmsyed/wrtr.git
cd wrtr
uv install
```

### Launch the App

```bash
uv run python main.py
```

### Build a Standalone Binary

If you still need a bundled binary:

```bash
pip install pyinstaller
pyinstaller main.spec
chmod +x dist/main
./dist/main
```

## Documentation

- [Welcome Guide](docs/Welcome.md)
- [Markdown Cheat Sheet](docs/Markdown_Cheat_Sheet.md)
- [Key Bindings](docs/Key_Binding_Cheat_Sheet.md)

---

**Terminal Writer** - Write better, write faster, in your terminal.

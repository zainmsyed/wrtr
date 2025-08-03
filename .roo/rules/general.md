# Roo Instructions for wrtr - Terminal Writer Application

These instructions guide Roo (the AI assistant) on how to contribute to the Terminal Writer project effectively.

## 1. Project Overview & Context

**wrtr** is a terminal-based writing application built with Python's Textual framework. Key characteristics:

- **Architecture**: Terminal UI application using Textual framework
- **Layout**: Three-column interface (file browser left, two markdown editor panes center/right)
- **Core Features**: Real-time markdown editing, fuzzy search, workspace management, auto-save
- **Dependencies**: Minimal - Textual + RapidFuzz (via UV package manager)
- **Python**: 3.8+ with full type hints and async support
- **Testing**: pytest with tests in `tests/` directory

## 2. Roo's Role & Capabilities

As Roo, you have access to:
- **File operations**: Read, write, modify any project files
- **Terminal commands**: Execute Python, UV, git, and system commands
- **Code analysis**: Understand Python structure, dependencies, and patterns
- **Testing**: Run tests and validate functionality
- **Browser actions**: Test UI components when needed
- **Search & replace**: Find patterns across the codebase

## 3. Development Workflow

### 3.1 Initial Setup Verification
```bash
# Verify project structure
uv --version
python3 --version
ls -la

# Install dependencies if needed
uv sync
```

### 3.2 Code Style & Standards
- **PEP 8 compliance** with type hints throughout
- **Async patterns** for non-blocking operations
- **Keyboard-first design** - all features accessible via shortcuts
- **Modular architecture** - single responsibility per module
- **Error handling** - graceful failures with user feedback

### 3.3 Key Modules & Responsibilities

#### Core Application (`main.py`)
- **App class**: `TerminalWriterApp` extending `textual.app.App`
- **Layout management**: Three-pane responsive grid
- **Global shortcuts**: Ctrl+F, Ctrl+1-4, Tab, Ctrl+N, Delete
- **State management**: Workspace coordination between panes

#### File Management (`file_browser.py`)
- **Widget**: Custom directory tree with list view
- **Operations**: Create, rename, delete files/folders
- **Navigation**: Keyboard-only file system traversal
- **Events**: File open/selection notifications

#### Editor System (`editor.py`)
- **Widget**: Markdown editor extending Textual's TextArea
- **Features**: Syntax highlighting, auto-save (5s debounce), sync between panes
- **Integration**: Rich markdown rendering, real-time updates

#### Search System (`search.py`)
- **Engine**: RapidFuzz for fuzzy file/content search
- **UI**: Global search pane with keyboard navigation
- **Actions**: Open in current/new pane, new workspace

#### Workspace Management (`workspace.py`)
- **Storage**: JSON persistence for 2-4 workspaces
- **State**: Open files, editor positions, browser paths
- **Switching**: Ctrl+1-4 modal interface

## 4. Implementation Guidelines

### 4.1 Adding New Features
1. **Analyze existing patterns** in similar modules
2. **Create/update tests** before implementation
3. **Follow naming conventions**: `snake_case` for functions/variables, `PascalCase` for classes
4. **Add type hints** for all function signatures
5. **Document complex logic** with docstrings

### 4.2 Testing Strategy
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_search.py

# Run with coverage
pytest --cov=wrtr tests/
```

### 4.3 Common Patterns

#### Textual Widget Structure
```python
from textual.widgets import Static
from textual.reactive import reactive

class CustomWidget(Static):
    """Widget description."""
    
    value = reactive("default")
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize state
        
    def compose(self) -> ComposeResult:
        """Define child widgets."""
        yield Widget()
        
    def on_mount(self) -> None:
        """Setup after mounting."""
        
    def watch_value(self, value: str) -> None:
        """React to reactive changes."""
```

#### Async File Operations
```python
async def load_file_async(self, path: str) -> str:
    """Load file content asynchronously."""
    try:
        async with aiofiles.open(path, 'r') as f:
            return await f.read()
    except Exception as e:
        self.notify(f"Error loading file: {e}", severity="error")
        return ""
```

## 5. Debugging & Troubleshooting

### 5.1 Common Issues
- **Import errors**: Check PYTHONPATH and UV environment
- **Textual rendering**: Use browser_action for visual verification
- **Async operations**: Ensure proper await usage
- **File permissions**: Handle read/write errors gracefully

### 5.2 Debug Commands
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Verify Textual installation
python3 -c "import textual; print(textual.__version__)"

# Run specific module
python3 -m wrtr.main
```

### 5.3 Logging & Monitoring
- Use Textual's built-in logging: `self.log.info("message")`
- Add debug prints during development
- Monitor terminal output for async errors

## 6. File Structure & Navigation

### 6.1 Key Directories
```
wrtr/
├── main.py                 # Application entry point
├── editor.py              # Markdown editor widget
├── file_browser.py        # File system browser
├── search.py              # Fuzzy search implementation
├── workspace.py           # Workspace state management
├── screens/               # Modal dialogs
├── tests/                 # Test suite
└── docs/                  # Documentation
```

### 6.2 Configuration Files
- `pyproject.toml`: Project metadata and dependencies
- `requirements.txt`: Python package requirements
- `uv.lock`: UV dependency lock file

## 7. Integration Points

### 7.1 Adding New Screens
1. Create in `screens/` directory
2. Extend `ModalScreen` or `Screen`
3. Register in main app routing
4. Add keyboard shortcuts

### 7.2 Extending Search
- Add new search providers in `search.py`
- Implement fuzzy matching patterns
- Update UI for new search types

### 7.3 Theme Customization
- Use Textual's built-in themes only
- Add theme switching in `theme.py`
- Ensure consistent styling across widgets

## 8. Performance Considerations

### 8.1 Optimization Targets
- **File I/O**: Async operations for large files
- **Search**: Indexing for frequently accessed content
- **Rendering**: Efficient widget updates
- **Memory**: Clean up unused workspace states

### 8.2 Monitoring
- Track file save/load times
- Monitor memory usage with large files
- Profile search performance

## 9. Deployment & Distribution

### 9.1 Build Process
```bash
# Create distribution
uv build

# Install locally
pip install -e .
```

### 9.2 Cross-platform Testing
- Test on macOS, Linux, Windows terminals
- Verify keyboard shortcuts work consistently
- Check file path handling across platforms

## 10. Documentation Standards

### 10.1 Code Documentation
- All public methods need docstrings
- Include usage examples for complex functions
- Document keyboard shortcuts in docstrings

### 10.2 User Documentation
- Update `docs/` with new features
- Maintain keyboard shortcut reference
- Add troubleshooting guides

## 11. Git Workflow

### 11.1 Commit Messages
```
feat: add fuzzy search for file contents
fix: resolve async file save race condition
docs: update keyboard shortcut reference
test: add workspace persistence tests
```

### 11.2 Branch Strategy
- `main`: Stable releases
- `develop`: Integration branch
- Feature branches: `feature/search-enhancement`

## 12. Emergency Procedures

### 12.1 Recovery Steps
1. **Check git status**: `git status`
2. **Review recent changes**: `git log --oneline -5`
3. **Run tests**: `pytest tests/`
4. **Check dependencies**: `uv pip list`
5. **Verify Python environment**: `python3 --version`

### 12.2 Rollback Plan
```bash
# Reset to last known good state
git reset --hard HEAD~1

# Or restore specific file
git checkout HEAD -- path/to/file.py
```

---

**Remember**: Always confirm successful tool usage before proceeding, maintain the existing code style, and prioritize user experience in terminal environments.
"""
SnippetService - manage loading, parsing and rendering of markdown snippets

Snippets are stored in `wrtr/data/snippets/` as two files:
- `default_snippets.md` (app-provided defaults)
- `user_snippets.md` (user-editable snippets)

Format mirrors templates:
<!-- SNIPPET: Name -->\n...content...\n<!-- END SNIPPET -->

Placeholders use moustache-style `{{name}}`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional
from datetime import datetime
from wrtr.logger import logger


SNIPPET_START = re.compile(r'<!--\s*SNIPPET:\s*(.+?)\s*-->', re.IGNORECASE)
SNIPPET_END = re.compile(r'<!--\s*END\s*SNIPPET\s*-->', re.IGNORECASE)
VAR_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_\-\.]+)\s*}}')


@dataclass
class Snippet:
    name: str
    content: str
    variables: List[str]


class SnippetService:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "wrtr"
        self.snippet_dir = self.base_dir / "data" / "snippets"
        self.user_snippets = self.snippet_dir / "user_snippets.md"
        self.default_snippets = self.snippet_dir / "default_snippets.md"
        try:
            self.snippet_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create snippet directory: {e}")

    def initialize_default_snippets(self) -> None:
        # Seed the single canonical user_snippets.md if missing. If an old
        # default_snippets.md exists (from previous versions), migrate it into
        # user_snippets.md so installs have one file to edit.
        if not self.user_snippets.exists():
            logger.info("Creating user snippets file (seeding defaults)")
            # Prefer existing packaged/default file if present for migration
            if self.default_snippets.exists():
                try:
                    default_content = self.default_snippets.read_text(encoding='utf8')
                except Exception:
                    default_content = None
            else:
                default_content = None

            if default_content is None:
                default_content = """
<!-- QUICK START: Snippets -->
<!--
Quick Start - adding & using snippets

1. Snippets live in `wrtr/data/snippets/user_snippets.md` and are plain Markdown.
2. Each snippet is wrapped between comment markers:
    `<!-- SNIPPET: name -->` and `<!-- END SNIPPET -->`.
3. To insert a snippet from the editor use the `/snippet <name>` command
    or pick it from the snippet modal. For snippets with variables, the
    app will prompt you to fill values before insertion.

Example snippet:

<!-- SNIPPET: greeting -->
Hello, **{{name}}**! Welcome to Wrtr.

<!-- END SNIPPET -->
-->

<!-- SNIPPET: lorem -->
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

<!-- END SNIPPET -->

<!-- SNIPPET: todo-block -->
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

<!-- END SNIPPET -->
"""
            try:
                # recreate the snippets directory in case it was deleted
                self.snippet_dir.mkdir(parents=True, exist_ok=True)
                self.user_snippets.write_text(default_content.strip() + "\n", encoding='utf8')
            except Exception as e:
                logger.error(f"Failed to write user snippets: {e}")

    def _parse_snippets_from_text(self, text: str) -> Dict[str, Snippet]:
        snippets: Dict[str, Snippet] = {}
        pos = 0
        while True:
            m = SNIPPET_START.search(text, pos)
            if not m:
                break
            name = m.group(1).strip()
            start = m.end()
            m_end = SNIPPET_END.search(text, start)
            if not m_end:
                logger.warning(f"Snippet '{name}' missing END marker")
                break
            content = text[start:m_end.start()].strip('\n')
            vars_found = sorted(set(VAR_PATTERN.findall(content)))
            snippets[name] = Snippet(name=name, content=content, variables=vars_found)
            pos = m_end.end()
        return snippets

    def load_snippets(self) -> Dict[str, Snippet]:
        snippets: Dict[str, Snippet] = {}
        # Load snippets only from the canonical user file. If it's missing but
        # an old default file exists, migrate it into user_snippets.md and load
        # from there.
        if not self.user_snippets.exists() and self.default_snippets.exists():
            try:
                content = self.default_snippets.read_text(encoding='utf8')
                # write to user_snippets for future runs
                self.user_snippets.write_text(content, encoding='utf8')
            except Exception as e:
                logger.error(f"Failed to migrate default snippets to user snippets: {e}")

        if self.user_snippets.exists():
            try:
                text = self.user_snippets.read_text(encoding='utf8')
                snippets.update(self._parse_snippets_from_text(text))
            except Exception as e:
                logger.error(f"Failed to load user snippets: {e}")
        return snippets

    def get_snippet_names(self) -> List[str]:
        return sorted(self.load_snippets().keys())

    def get_snippet(self, name: str) -> Optional[Snippet]:
        return self.load_snippets().get(name)

    def render(self, name: str, variables: Optional[Dict[str, str]] = None) -> str:
        sn = self.get_snippet(name)
        if not sn:
            raise KeyError(f"Snippet '{name}' not found")
        vars_map = dict(variables or {})
        if 'date' in sn.variables and 'date' not in vars_map:
            vars_map['date'] = datetime.now().date().isoformat()
        if 'time' in sn.variables and 'time' not in vars_map:
            vars_map['time'] = datetime.now().time().strftime('%H:%M:%S')

        def replace_var(m: re.Match) -> str:
            key = m.group(1)
            return vars_map.get(key, m.group(0))

        rendered = VAR_PATTERN.sub(replace_var, sn.content)
        return rendered

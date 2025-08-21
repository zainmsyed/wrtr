"""
TemplateService - manage loading, parsing and rendering of markdown templates

Templates are stored in `wrtr/data/templates/` as two files:
- `default_templates.md` (app-provided defaults)
- `user_templates.md` (user-editable templates)

Template format (single-file multiple templates):
<!-- TEMPLATE: Name -->\n...content...\n<!-- END TEMPLATE -->

Placeholders use moustache-style `{{name}}` and will be detected and
returned as variables that need values before rendering.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional
from datetime import datetime
from wrtr.logger import logger


TEMPLATE_START = re.compile(r'<!--\s*TEMPLATE:\s*(.+?)\s*-->', re.IGNORECASE)
TEMPLATE_END = re.compile(r'<!--\s*END\s*TEMPLATE\s*-->', re.IGNORECASE)
VAR_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_\-\.]+)\s*}}')


@dataclass
class Template:
    name: str
    content: str
    variables: List[str]


class TemplateService:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        # base_dir is the application default dir (where wrtr/data lives)
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "wrtr"
        self.template_dir = self.base_dir / "data" / "templates"
        self.user_templates = self.template_dir / "user_templates.md"
        self.default_templates = self.template_dir / "default_templates.md"
        # Ensure directories exist
        try:
            self.template_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create template directory: {e}")

    def initialize_default_templates(self) -> None:
        """Seed the canonical `user_templates.md` with defaults if missing.

        If an old `default_templates.md` exists, migrate it into
        `user_templates.md` so users have a single file to edit.
        """
        if not self.user_templates.exists():
            logger.info("Creating user templates file (seeding defaults)")
            # Prefer existing default file for migration
            if self.default_templates.exists():
                try:
                    default_content = self.default_templates.read_text(encoding='utf8')
                except Exception:
                    default_content = None
            else:
                default_content = None

                if default_content is None:
                     # Basic default templates with Quick Start (kept minimal here)
                     default_content = """
<!-- QUICK START: Templates -->
<!--
Quick Start - adding & using templates

1. Templates live in `wrtr/data/templates/user_templates.md` and are plain Markdown.
2. Each template is wrapped between comment markers:
    `<!-- TEMPLATE: name -->` and `<!-- END TEMPLATE -->`.
3. To insert a template from the editor use the template modal or
    the `/template <name>` slash command (if available).

Example template:

<!-- TEMPLATE: Simple Greeting -->
# Hello {{name}}

Welcome to your document, **{{name}}**!

<!-- END TEMPLATE -->
-->

<!-- TEMPLATE: Daily Journal -->
# Daily Journal - {{date}}

## Today's Goals
- [ ] 
- [ ] 
- [ ] 

## Notes


<!-- END TEMPLATE -->

<!-- TEMPLATE: Meeting Notes -->
# Meeting: {{title}}
**Date:** {{date}}  
**Time:** {{time}}  
**Attendees:** 

## Agenda


## Action Items
- [ ] 
- [ ] 

<!-- END TEMPLATE -->

<!-- TEMPLATE: Project Plan -->
# Project: {{title}}

## Overview

## Goals
- [ ] 
- [ ] 

<!-- END TEMPLATE -->
"""
            try:
                # ensure directory exists and write the canonical user file
                self.template_dir.mkdir(parents=True, exist_ok=True)
                self.user_templates.write_text(default_content.strip() + "\n", encoding='utf8')
            except Exception as e:
                logger.error(f"Failed to write user templates: {e}")

    def _parse_templates_from_text(self, text: str) -> Dict[str, Template]:
        """Parse multiple templates from a markdown string."""
        templates: Dict[str, Template] = {}
        # We'll scan sequentially for start/end markers
        pos = 0
        while True:
            m = TEMPLATE_START.search(text, pos)
            if not m:
                break
            name = m.group(1).strip()
            start = m.end()
            m_end = TEMPLATE_END.search(text, start)
            if not m_end:
                # malformed; stop parsing further
                logger.warning(f"Template '{name}' missing END marker")
                break
            content = text[start:m_end.start()].strip('\n')
            vars_found = sorted(set(VAR_PATTERN.findall(content)))
            templates[name] = Template(name=name, content=content, variables=vars_found)
            pos = m_end.end()
        return templates

    def load_templates(self) -> Dict[str, Template]:
        """Load templates from user file (if exists) falling back to defaults.

        Returns a dict mapping template name -> Template
        """
        templates: Dict[str, Template] = {}
        # Load only from the canonical user file. If missing but an old
        # default file exists, migrate it into user_templates.md first.
        if not self.user_templates.exists() and self.default_templates.exists():
            try:
                content = self.default_templates.read_text(encoding='utf8')
                self.user_templates.write_text(content, encoding='utf8')
            except Exception as e:
                logger.error(f"Failed to migrate default templates to user templates: {e}")

        if self.user_templates.exists():
            try:
                text = self.user_templates.read_text(encoding='utf8')
                templates.update(self._parse_templates_from_text(text))
            except Exception as e:
                logger.error(f"Failed to load user templates: {e}")

        return templates

    def get_template_names(self) -> List[str]:
        return sorted(self.load_templates().keys())

    def get_template(self, name: str) -> Optional[Template]:
        return self.load_templates().get(name)

    def render(self, name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """Render template by substituting variables.

        Auto-fills `date` and `time` if not provided.
        """
        tpl = self.get_template(name)
        if not tpl:
            raise KeyError(f"Template '{name}' not found")
        vars_map = dict(variables or {})
        if 'date' in tpl.variables and 'date' not in vars_map:
            vars_map['date'] = datetime.now().date().isoformat()
        if 'time' in tpl.variables and 'time' not in vars_map:
            vars_map['time'] = datetime.now().time().strftime('%H:%M:%S')

        def replace_var(m: re.Match) -> str:
            key = m.group(1)
            return vars_map.get(key, m.group(0))

        rendered = VAR_PATTERN.sub(replace_var, tpl.content)
        return rendered

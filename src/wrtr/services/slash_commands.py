from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Optional, Tuple

SlashHandler = Callable[[str, str], Awaitable[str] | str]


@dataclass
class SlashCommand:
    name: str
    handler: SlashHandler
    help: str = ""


class SlashCommandService:
    """Registry and executor for slash commands.

    Handlers may be synchronous (returning str) or asynchronous (coroutine that returns str).
    """

    _commands: Dict[str, SlashCommand] = {}

    @classmethod
    def register(cls, name: str, handler: SlashHandler, help: str = "") -> None:
        cls._commands[name.lower()] = SlashCommand(name=name.lower(), handler=handler, help=help)

    @classmethod
    def parse(cls, line: str) -> Optional[Tuple[str, str]]:
        """Return (cmd, args) if `line` is a slash command, else None.

        Accepts leading whitespace and extracts the first token after '/'.
        Examples:
          '/ai do this' -> ('ai', 'do this')
          '  /ai' -> ('ai', '')
        """
        if not line:
            return None
        s = line.lstrip()
        if not s.startswith("/"):
            return None
        rest = s[1:].strip()
        if not rest:
            return None
        parts = rest.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return (cmd, args)

    @classmethod
    async def execute(cls, line: str) -> str:
        parsed = cls.parse(line)
        if not parsed:
            raise ValueError("Not a slash command")
        cmd, args = parsed
        if cmd not in cls._commands:
            known = ", ".join(sorted(cls._commands.keys())) or "(none registered)"
            return f"Unknown command '/{cmd}'. Available: {known}"
        handler = cls._commands[cmd].handler
        res = handler(args, line)
        if isinstance(res, str):
            return res
        return await res

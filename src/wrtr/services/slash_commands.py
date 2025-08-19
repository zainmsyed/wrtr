"""
Slash Command Service - Central registry and execution engine for slash commands
"""
import asyncio
import re
import datetime
from datetime import timedelta
from typing import Dict, Callable, Optional, Tuple, Any
from dataclasses import dataclass
from wrtr.logger import logger

@dataclass
class CommandInfo:
    """Information about a registered slash command"""
    handler: Callable[[str, str], Any]  # (args, full_line) -> result
    help_text: str
    description: str = ""

class SlashCommandService:
    """Service for registering and executing slash commands"""
    _commands: Dict[str, CommandInfo] = {}

    @classmethod
    def register(cls, command: str, handler: Callable[[str, str], Any], help: str = "", description: str = "") -> None:
        """Register a new slash command

        Args:
            command: Command name (without the /)
            handler: Function that takes (args, full_line) and returns replacement text
            help: Short help text
            description: Longer description
        """
        cls._commands[command.lower()] = CommandInfo(handler, help, description)
        logger.debug(f"Registered slash command: /{command}")

    @classmethod
    def parse(cls, line: str) -> Optional[Tuple[str, str]]:
        """Parse a line to extract slash command and arguments

        Args:
            line: Text line to parse

        Returns:
            Tuple of (command, args) if slash command found, None otherwise
        """
        line = line.strip()
        if not line.startswith('/'):
            return None
        # Match /command followed by optional arguments
        match = re.match(r'^/(\w+)(?:\s+(.*))?$', line)
        if not match:
            return None

        command = match.group(1).lower()
        args = match.group(2) or ""
        return command, args.strip()

    @classmethod
    async def execute(cls, line: str) -> str:
        """Execute a slash command from a line

        Args:
            line: Full line containing the slash command

        Returns:
            Replacement text or error message
        """
        parsed = cls.parse(line)
        if not parsed:
            return line  # Not a slash command

        command, args = parsed
        # Dynamic date commands before registered ones
        # Handle "/next week" and "/next month"
        if command == 'next':
            if args.lower() == 'week':
                return (datetime.date.today() + timedelta(days=7)).isoformat()
            if args.lower() == 'month':
                return (datetime.date.today() + timedelta(days=30)).isoformat()
        # Handle "/<n> days from today", e.g. "/4 days from today"
        m_line = re.match(r'^/(\d+)\s+days\s+from\s+today$', line.strip(), flags=re.IGNORECASE)
        if m_line:
            days = int(m_line.group(1))
            return (datetime.date.today() + timedelta(days=days)).isoformat()
        # Not a dynamic date, proceed to registered commands
        if command not in cls._commands:
            available = ", ".join(sorted(cls._commands.keys()))
            return f"Unknown command '/{command}'. Available: {available}"

        try:
            cmd_info = cls._commands[command]
            # Execute handler (may be sync or async)
            if asyncio.iscoroutinefunction(cmd_info.handler):
                result = await cmd_info.handler(args, line)
            else:
                result = cmd_info.handler(args, line)

            logger.debug(f"Slash command result for line '{line}': {result}")
            return str(result) if result is not None else ""

        except Exception as e:
            logger.error(f"Error executing slash command '{command}': {e}")
            return f"Command error: {e}"

    @classmethod
    def get_commands(cls) -> Dict[str, CommandInfo]:
        """Get all registered commands"""
        return cls._commands.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered commands (useful for testing)"""
        cls._commands.clear()

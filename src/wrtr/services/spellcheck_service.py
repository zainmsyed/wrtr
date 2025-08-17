"""
Singleton spellchecker service for efficient dictionary loading.
"""
import asyncio
import threading
from typing import Optional
from pathlib import Path
from wrtr.services.spellcheck import MarkdownSpellchecker
from wrtr.logger import logger


class SpellCheckerService:
    """Singleton service for managing spellchecker instances."""
    
    _instance: Optional['SpellCheckerService'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._spellchecker: Optional[MarkdownSpellchecker] = None
        self._loading: bool = False
        self._load_event: Optional[asyncio.Event] = None
    
    @classmethod
    def get_instance(cls) -> 'SpellCheckerService':
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    async def get_spellchecker(self) -> MarkdownSpellchecker:
        """
        Get the spellchecker instance, loading it asynchronously if needed.
        Multiple calls during loading will wait for the same loading operation.
        """
        if self._spellchecker is not None:
            return self._spellchecker
        
        # If already loading, wait for completion
        if self._loading:
            if self._load_event:
                await self._load_event.wait()
            return self._spellchecker
        
        # Start loading
        self._loading = True
        self._load_event = asyncio.Event()
        
        try:
            logger.debug("Loading spellchecker dictionaries...")
            start_time = asyncio.get_event_loop().time()
            
            # Load in executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            
            # Use only built-in dictionaries for better performance
            # Custom dictionaries can be loaded separately if needed
            self._spellchecker = await loop.run_in_executor(
                None,
                self._create_spellchecker
            )
            
            load_time = asyncio.get_event_loop().time() - start_time
            logger.debug(f"Spellchecker loaded in {load_time:.3f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load spellchecker: {e}")
            # Create a minimal fallback
            self._spellchecker = MarkdownSpellchecker(
                dictionary_path=None,
                user_dictionary_path=None
            )
        finally:
            self._loading = False
            if self._load_event:
                self._load_event.set()
        
        return self._spellchecker
    
    def _create_spellchecker(self) -> MarkdownSpellchecker:
        """Create spellchecker instance (runs in thread executor)."""
        # Use built-in dictionaries with accurate spell checking parameters
        # Performance is optimized through singleton pattern and skipping bigrams
        app_dir = Path.cwd() / "wrtr"
        user_dict = app_dir / "data" / "dictionary" / "user_dictionary.txt"
        
        # Ensure user dictionary directory exists
        user_dict.parent.mkdir(parents=True, exist_ok=True)
        if not user_dict.exists():
            user_dict.write_text("", encoding="utf-8")
        
        # Create spellchecker with accurate parameters 
        # Restored edit distance 2 and prefix 7 for better accuracy
        return MarkdownSpellchecker(
            dictionary_path=None,  # Use built-in only
            user_dictionary_path=str(user_dict),
            max_dictionary_edit_distance=2,  # Restored for accuracy
            prefix_length=7,  # Restored for accuracy
        )
    
    def reset(self):
        """Reset the singleton (useful for testing)."""
        with self._lock:
            self._spellchecker = None
            self._loading = False
            self._load_event = None


# Convenience function for getting the spellchecker
async def get_spellchecker() -> MarkdownSpellchecker:
    """Get the singleton spellchecker instance."""
    service = SpellCheckerService.get_instance()
    return await service.get_spellchecker()

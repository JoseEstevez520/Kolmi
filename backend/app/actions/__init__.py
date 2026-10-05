from .registry import Action, action, get_registry

# Importing the modules registers their actions.
from . import chat, content, files, notes, passes, profile, schedule, settings  # noqa: F401

__all__ = ["Action", "action", "get_registry"]

from .registry import Action, action, get_registry

# Importing the modules registers their actions.
from . import content, notes, passes, profile, settings  # noqa: F401

__all__ = ["Action", "action", "get_registry"]

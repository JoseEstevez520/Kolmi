from .registry import Action, action, get_registry

# Importing the modules registers their actions.
from . import notes, profile  # noqa: F401

__all__ = ["Action", "action", "get_registry"]

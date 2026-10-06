from .registry import Action, action, get_action, get_registry, has_role, invoke

# Importing the modules registers their actions.
from . import chat, content, files, notes, pages, passes, profile, schedule, settings, users  # noqa: F401

__all__ = ["Action", "action", "get_action", "get_registry", "has_role", "invoke"]

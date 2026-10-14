"""Profile photos: the checks and the link. One public bucket, one random object per person."""

from __future__ import annotations

from typing import Any

from .config import get_settings

BUCKET = "avatars"
MAX_AVATAR_BYTES = 512 * 1024


def avatar_url(path: str | None) -> str | None:
    """The public link of a photo. Only members are ever handed it, and the name is random."""
    if not path:
        return None
    return f"{get_settings().supabase_url.rstrip('/')}/storage/v1/object/public/{BUCKET}/{path}"


def with_avatar(profile: dict[str, Any]) -> dict[str, Any]:
    """A profile row as the web gets it: the photo's link in place of its key."""
    out = {k: v for k, v in profile.items() if k != "avatar_path"}
    out["avatar_url"] = avatar_url(profile.get("avatar_path"))
    return out


def image_mime(data: bytes) -> str | None:
    """JPEG, PNG or WebP by the file's first bytes, not by its name or declared type."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None

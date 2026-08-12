#!/usr/bin/env python3
"""Shared release and verified-lyrics publication rules for SUZUKA."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable


RELEASE_STATUSES = {"draft", "upcoming", "published"}


def has_verified_lyrics(item: dict) -> bool:
    """Return whether the canonical record contains a complete verified lyric master."""
    return (
        item.get("lyricsAvailable") is True
        and item.get("lyricsVerified") is True
        and bool(str(item.get("lyricsVerifiedAt") or "").strip())
        and bool(str(item.get("lyricsText") or item.get("lyrics") or "").strip())
        and bool(str(item.get("lyricsSource") or "").strip())
    )


def is_publishable_lyrics(item: dict) -> bool:
    """The single canonical gate used by every Lyrics publication surface."""
    return item.get("status") == "published" and has_verified_lyrics(item)


def published_releases(items: Iterable[dict]) -> list[dict]:
    return [item for item in items if item.get("status") == "published"]


def publishable_lyrics(items: Iterable[dict]) -> list[dict]:
    return [item for item in items if is_publishable_lyrics(item)]


def verified_lyrics_waiting(items: Iterable[dict]) -> list[dict]:
    return [item for item in items if item.get("status") != "published" and has_verified_lyrics(item)]


def parse_iso8601(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Timezone is required: {value}")
    return parsed


def youtube_state_allows_publish(
    item: dict,
    evidence: dict,
    *,
    now: datetime,
    official_channel_id: str,
) -> bool:
    """Require public, elapsed, non-upcoming evidence from the official channel."""
    if evidence.get("channel_id") != official_channel_id:
        return False
    if evidence.get("availability") != "public":
        return False
    if evidence.get("live_status") in {"is_upcoming", "is_live", "post_live"}:
        return False
    published_at = evidence.get("release_timestamp") or evidence.get("actual_start_timestamp")
    if not published_at:
        return False
    if datetime.fromtimestamp(int(published_at), tz=now.tzinfo) > now:
        return False
    scheduled_at = item.get("scheduledAt")
    if scheduled_at and parse_iso8601(scheduled_at) > now:
        return False
    return bool(evidence.get("duration"))

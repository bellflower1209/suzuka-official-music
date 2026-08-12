#!/usr/bin/env python3
"""Exercise the Version 1.2 YouTube publication gate without network or writes."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from release_state import youtube_state_allows_publish


ROOT = Path(__file__).resolve().parents[1]
JST = ZoneInfo("Asia/Tokyo")


def main() -> int:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    item = cms["upcoming"][0]
    channel_id = cms["site"]["youtubeChannelId"]
    scheduled = datetime.fromisoformat(item["scheduledAt"])
    timestamp = int(scheduled.timestamp())
    base = {
        "channel_id": channel_id,
        "availability": "public",
        "release_timestamp": timestamp,
        "duration": 240,
    }
    cases = {
        "premiere_waiting": (
            {**base, "live_status": "is_upcoming"}, scheduled.replace(hour=max(0, scheduled.hour - 1)), False
        ),
        "published_official": (
            {**base, "live_status": "was_live"}, scheduled.replace(hour=min(23, scheduled.hour + 1)), True
        ),
        "wrong_channel": (
            {**base, "channel_id": "not-official", "live_status": "was_live"}, scheduled.replace(hour=min(23, scheduled.hour + 1)), False
        ),
        "no_duration": (
            {**base, "duration": None, "live_status": "was_live"}, scheduled.replace(hour=min(23, scheduled.hour + 1)), False
        ),
    }
    errors = []
    for name, (evidence, now, expected) in cases.items():
        actual = youtube_state_allows_publish(item, evidence, now=now.astimezone(JST), official_channel_id=channel_id)
        if actual is not expected:
            errors.append(f"{name}: expected={expected} actual={actual}")
    if errors:
        raise SystemExit("Release automation audit failed:\n- " + "\n- ".join(errors))
    print(json.dumps({"status": "PASS", "cases": len(cases), "prematurePublication": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

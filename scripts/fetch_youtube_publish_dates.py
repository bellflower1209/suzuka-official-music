#!/usr/bin/env python3
"""Fetch official YouTube evidence for published and scheduled CMS releases."""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

PLAYER_RE = re.compile(r"ytInitialPlayerResponse\s*=\s*({.+?});(?:var meta|</script>)")
JST = ZoneInfo("Asia/Tokyo")


def youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path.strip("/")
    return parse_qs(parsed.query).get("v", [""])[0]


def fetch(item: dict, expected_channel_id: str) -> dict:
    video_id = youtube_id(item.get("youtubeUrl", ""))
    result = {
        "releaseSlug": item["slug"],
        "youtubeId": video_id,
        "youtubeUrl": item.get("youtubeUrl", ""),
        "catalogReleaseDate": item.get("releaseDate", ""),
        "officialTitle": "",
        "channelId": "",
        "channelVerified": False,
        "youtubePublishDate": "",
        "youtubeUploadDate": "",
        "liveStartTimestamp": "",
        "playabilityStatus": "",
        "durationSeconds": 0,
        "verifiedPublishedAt": "",
        "verificationSource": "",
        "status": "unverified",
    }
    if not video_id:
        return result
    request = urllib.request.Request(
        f"https://www.youtube.com/watch?v={video_id}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        source = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
        match = PLAYER_RE.search(source)
        if not match:
            result["status"] = "player-response-missing"
            return result
        player = json.loads(match.group(1))
        details = player.get("videoDetails", {})
        microformat = player.get("microformat", {}).get("playerMicroformatRenderer", {})
        live = microformat.get("liveBroadcastDetails", {})
        playability = player.get("playabilityStatus", {}).get("status", "")
        result.update({
            "officialTitle": details.get("title", ""),
            "channelId": details.get("channelId", ""),
            "channelVerified": details.get("channelId", "") == expected_channel_id,
            "youtubePublishDate": microformat.get("publishDate", ""),
            "youtubeUploadDate": microformat.get("uploadDate", ""),
            "liveStartTimestamp": live.get("startTimestamp", ""),
            "playabilityStatus": playability,
            "durationSeconds": int(details.get("lengthSeconds") or 0),
        })
        publish_timestamp = live.get("startTimestamp") or microformat.get("publishDate") or microformat.get("uploadDate")
        if result["channelVerified"] and publish_timestamp:
            instant = datetime.fromisoformat(publish_timestamp.replace("Z", "+00:00"))
            if instant.tzinfo is None:
                result["status"] = "verified-date-only"
                result["verificationSource"] = "official-youtube-date-only"
                return result
            if live.get("startTimestamp") and instant > datetime.now(timezone.utc):
                result["verificationSource"] = "official-youtube-liveBroadcastDetails.startTimestamp"
                result["status"] = "scheduled"
                return result
            if playability != "OK":
                result["verificationSource"] = "official-youtube-playability-unavailable"
                result["status"] = "unavailable"
                return result
            result["verifiedPublishedAt"] = instant.astimezone(JST).isoformat(timespec="seconds")
            result["verificationSource"] = (
                "official-youtube-liveBroadcastDetails.startTimestamp"
                if live.get("startTimestamp")
                else "official-youtube-playerMicroformatRenderer.publishDate"
            )
            result["status"] = "verified-datetime"
        else:
            result["status"] = "channel-or-date-unverified"
    except Exception as error:
        result["status"] = f"fetch-error:{type(error).__name__}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    releases = [item for item in cms["releases"] if item.get("status") == "published"]
    upcoming = [item for item in cms.get("upcoming", []) if item.get("status") == "upcoming"]
    channel_id = cms["site"]["youtubeChannelId"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda item: fetch(item, channel_id), [*releases, *upcoming]))
    records.sort(key=lambda item: item["releaseSlug"])
    output = {
        "schemaVersion": "1.0",
        "checkedAt": datetime.now(JST).isoformat(timespec="seconds"),
        "officialChannelId": channel_id,
        "records": records,
    }
    if args.write:
        path = root / "assets/data/youtube-publish-dates.json"
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {status: sum(item["status"] == status for item in records) for status in sorted({item["status"] for item in records})}
    print(json.dumps({"records": len(records), "counts": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()

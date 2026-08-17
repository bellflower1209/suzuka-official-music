#!/usr/bin/env python3
"""Register the public Michiru Short verified on the official channel."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260817.json"
VERIFIED_AT = "2026-08-17T09:48:00+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"
VIDEO = {
    "videoId": "QG2KN01CsJ4",
    "title": "【8/20 MV解禁】friend like song / 妃みちる｜何年経っても、変わらないメンツがいる。🍺☀️",
    "artist": "妃みちる",
    "artistSlug": "michiru",
    "youtubeUrl": "https://www.youtube.com/shorts/QG2KN01CsJ4",
    "publishedAt": "2026-08-16T20:37:31+09:00",
    "relatedRelease": "friendlikesong",
    "thumbnail": "https://i.ytimg.com/vi/QG2KN01CsJ4/maxresdefault.jpg",
    "status": "published",
    "contentType": "short",
    "duration": 32,
    "description": "妃みちる『friendlikesong』の2026年8月20日MV解禁を案内する、SUZUKA公式YouTubeの公開済みShorts。",
}


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    snapshot = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    shorts[VIDEO["videoId"]] = VIDEO
    snapshot["officialVideos"] = 55
    snapshot["shorts"] = 34
    snapshot["verifiedAt"] = VERIFIED_AT
    snapshot["source"] = "公式YouTubeチャンネルのvideos/shortsタブと各動画をyt-dlpで照合"
    snapshot["shortVideos"] = sorted(
        shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True
    )
    write_json(CMS_PATH, cms)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {
        (item["releaseSlug"], item.get("youtubeId", "")): item
        for item in dates["records"]
    }
    records[(VIDEO["relatedRelease"], VIDEO["videoId"])] = {
        "releaseSlug": VIDEO["relatedRelease"],
        "youtubeId": VIDEO["videoId"],
        "youtubeUrl": VIDEO["youtubeUrl"],
        "catalogReleaseDate": VIDEO["publishedAt"][:10],
        "officialTitle": VIDEO["title"],
        "channelId": CHANNEL_ID,
        "channelVerified": True,
        "youtubePublishDate": VIDEO["publishedAt"],
        "youtubeUploadDate": VIDEO["publishedAt"],
        "liveStartTimestamp": "",
        "playabilityStatus": "OK",
        "durationSeconds": VIDEO["duration"],
        "verifiedPublishedAt": VIDEO["publishedAt"],
        "verificationSource": "official-youtube-timestamp-and-description",
        "status": "verified-datetime",
        "contentType": "short",
    }
    dates["checkedAt"] = VERIFIED_AT
    dates["records"] = sorted(
        records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", ""))
    )
    write_json(DATES_PATH, dates)

    catalog = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    catalog["verifiedAt"] = VERIFIED_AT
    catalog["channelSnapshot"] = {"officialVideos": 55, "shorts": 34}
    catalog_shorts = {item["videoId"]: item for item in catalog.get("shorts", [])}
    catalog_shorts[VIDEO["videoId"]] = VIDEO
    catalog["shorts"] = sorted(
        catalog_shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True
    )
    write_json(SNAPSHOT_PATH, catalog)

    print(json.dumps({"registeredShort": VIDEO["videoId"], "verifiedAt": VERIFIED_AT}, ensure_ascii=False))


if __name__ == "__main__":
    main()

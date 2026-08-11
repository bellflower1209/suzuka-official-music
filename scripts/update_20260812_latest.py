#!/usr/bin/env python3
"""Apply official YouTube evidence verified on 2026-08-12 to canonical data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def published_record(definition: dict, previous: dict, artist_type: str) -> dict:
    published_at = definition["publishedAt"]
    tags = list(dict.fromkeys([
        *definition["genres"], *definition["themes"], *definition["moods"],
    ]))
    return {
        **previous,
        "id": definition["slug"],
        "slug": definition["slug"],
        "title": definition["title"],
        "displayTitle": definition["title"],
        "englishTitle": definition["title"],
        "artist": definition["artist"],
        "artistSlug": definition["artistSlug"],
        "artistSlugs": [definition["artistSlug"]],
        "artistType": artist_type,
        "releaseAt": published_at,
        "releaseDate": published_at[:10],
        "releaseYear": int(published_at[:4]),
        "releaseType": "single",
        "genres": definition["genres"],
        "moods": definition["moods"],
        "themes": definition["themes"],
        "language": "ja",
        "coverImage": definition["coverImage"],
        "coverAlt": f'{definition["artist"]}「{definition["title"]}」公式YouTubeサムネイル',
        "releaseUrl": f'releases/{definition["slug"]}/',
        "youtubeUrl": definition["youtubeUrl"],
        "newsUrl": previous.get("newsUrl", ""),
        "duration": definition["duration"],
        "status": "published",
        "featured": bool(previous.get("featured", False)),
        "recommendationWeight": int(previous.get("recommendationWeight") or 1),
        "weeklyPickEligible": True,
        "analyticsEnabled": True,
        "upcomingPriority": 0,
        "relatedReleases": previous.get("relatedReleases", []),
        "searchKeywords": list(dict.fromkeys([
            definition["title"], definition["artist"], *tags,
        ])),
        "aiArtistType": "fictional AI artist",
        "description": definition["description"],
        "tags": tags,
        "lyrics": previous.get("lyrics", ""),
        "lyricsAvailable": bool(previous.get("lyricsAvailable", False)),
        "lyricsSource": previous.get("lyricsSource", ""),
        "lyricsText": previous.get("lyricsText", previous.get("lyrics", "")),
        "lyricsVerified": bool(previous.get("lyricsVerified", False)),
        "lyricsVerifiedAt": previous.get("lyricsVerifiedAt"),
        "introduction": definition["description"],
        "publishedAt": published_at,
        "instagramUrl": previous.get("instagramUrl", ""),
        "shortsUrl": previous.get("shortsUrl", ""),
        "galleryImages": previous.get("galleryImages", []),
        "galleryPublished": bool(previous.get("galleryPublished", False)),
        "productionNote": definition["description"],
        "seo": {
            "title": f'{definition["title"]}｜{definition["artist"]}｜SUZUKA Official Music',
            "description": f'{definition["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": published_at[:10],
        "videoPublishedAt": published_at,
        "videoPublishedAtSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "videoStructuredDataStatus": "published",
        "officialSource": definition["youtubeUrl"],
        "playlistPriority": int(previous.get("playlistPriority", 0)),
        "homeHero": previous.get("homeHero", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--catalog", type=Path,
        default=Path("assets/data/official-youtube-catalog-20260812.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    source_path = args.catalog if args.catalog.is_absolute() else root / args.catalog
    source = json.loads(source_path.read_text(encoding="utf-8"))
    cms_path = root / "assets/data/creator-cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    if source["officialChannelId"] != cms["site"]["youtubeChannelId"]:
        raise SystemExit("Official YouTube channel mismatch")

    releases = {item["slug"]: item for item in cms["releases"]}
    previous_upcoming = {item["slug"]: item for item in cms.get("upcoming", [])}
    artist_types = {item["slug"]: item["type"] for item in cms["artists"]}
    promoted = []
    for definition in source["published"]:
        previous = releases.get(definition["slug"], previous_upcoming.get(definition["slug"], {}))
        releases[definition["slug"]] = published_record(
            definition, previous, artist_types[definition["artistSlug"]],
        )
        promoted.append(definition["slug"])
    cms["releases"] = sorted(
        releases.values(),
        key=lambda item: (item.get("publishedAt", item.get("releaseDate", "")), item["slug"]),
        reverse=True,
    )

    upcoming = []
    for priority, definition in enumerate(source["upcoming"], 1):
        previous = previous_upcoming.get(definition["slug"], {})
        upcoming.append({
            **previous,
            "slug": definition["slug"],
            "title": definition["title"],
            "artist": definition["artist"],
            "artistSlug": definition["artistSlug"],
            "scheduledAt": definition["scheduledAt"],
            "youtubeUrl": definition["youtubeUrl"],
            "image": definition["image"],
            "description": definition["description"],
            "releaseAt": definition["scheduledAt"],
            "publishedAt": definition["scheduledAt"],
            "status": "upcoming",
            "note": "公式YouTubeで公開予定を確認済み。公開済み作品には含めていません。",
            "genres": [], "themes": [], "tags": [],
            "lyricsAvailable": bool(previous.get("lyricsAvailable", False)),
            "lyricsSource": previous.get("lyricsSource", ""),
            "lyricsText": previous.get("lyricsText", ""),
            "lyricsVerified": bool(previous.get("lyricsVerified", False)),
            "lyricsVerifiedAt": previous.get("lyricsVerifiedAt"),
            "featured": False, "recommendationWeight": None,
            "weeklyPickEligible": False, "analyticsEnabled": True,
            "upcomingPriority": priority,
        })
    cms["upcoming"] = upcoming

    for artist in cms["artists"]:
        works = [
            item for item in cms["releases"]
            if artist["slug"] in item.get("artistSlugs", [item.get("artistSlug")])
        ]
        artist["artistFeaturedTracks"] = [
            item["slug"] for item in sorted(
                works,
                key=lambda item: (
                    int(item.get("recommendationWeight") or 0),
                    item.get("publishedAt", item.get("releaseDate", "")),
                    item["slug"],
                ),
                reverse=True,
            )[:3]
        ]

    cms["updatedAt"] = source["verifiedAt"]
    cms["youtubeSnapshot"] = {
        **source["channelSnapshot"],
        "source": source["verificationMethod"],
    }
    write_json(cms_path, cms)

    evidence_path = root / "assets/data/youtube-publish-dates.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    records = {item["releaseSlug"]: item for item in evidence["records"]}
    for definition in source["published"]:
        records[definition["slug"]] = {
            "releaseSlug": definition["slug"],
            "youtubeId": definition["youtubeId"],
            "youtubeUrl": definition["youtubeUrl"],
            "catalogReleaseDate": definition["publishedAt"][:10],
            "officialTitle": definition["officialTitle"],
            "channelId": source["officialChannelId"],
            "channelVerified": True,
            "youtubePublishDate": definition["publishedAt"],
            "youtubeUploadDate": definition["publishedAt"],
            "liveStartTimestamp": definition["publishedAt"],
            "playabilityStatus": "OK",
            "durationSeconds": definition["duration"],
            "verifiedPublishedAt": definition["publishedAt"],
            "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
            "status": "verified-datetime",
        }
    for definition in source["upcoming"]:
        records[definition["slug"]] = {
            "releaseSlug": definition["slug"],
            "youtubeId": definition["youtubeId"],
            "youtubeUrl": definition["youtubeUrl"],
            "catalogReleaseDate": "",
            "officialTitle": definition["title"],
            "channelId": source["officialChannelId"],
            "channelVerified": True,
            "youtubePublishDate": "",
            "youtubeUploadDate": "",
            "liveStartTimestamp": definition["scheduledAt"],
            "playabilityStatus": "LIVE_STREAM_OFFLINE",
            "durationSeconds": 0,
            "verifiedPublishedAt": "",
            "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
            "status": "scheduled",
        }
    evidence["checkedAt"] = source["verifiedAt"]
    evidence["records"] = sorted(records.values(), key=lambda item: item["releaseSlug"])
    write_json(evidence_path, evidence)
    print(json.dumps({
        "published": len(cms["releases"]), "upcoming": len(cms["upcoming"]),
        "promoted": promoted,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply official YouTube evidence verified on 2026-08-08 to Creator CMS v3.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--catalog", type=Path,
        default=Path("assets/data/official-youtube-catalog-20260808.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = args.catalog if args.catalog.is_absolute() else root / args.catalog
    source = json.loads(catalog_path.read_text(encoding="utf-8"))
    cms_path = root / "assets/data/creator-cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))

    artists = {item["slug"]: item for item in cms["artists"]}
    for definition in source.get("artists", []):
        previous = artists.get(definition["slug"], {})
        artists[definition["slug"]] = {
            **previous,
            "slug": definition["slug"],
            "name": definition["name"],
            "reading": definition["reading"],
            "type": definition["type"],
            "artistType": definition["type"],
            "image": definition["image"],
            "world": definition["world"],
            "music": definition["music"],
            "profile": definition["profile"],
            "members": definition.get("members", []),
            "status": "published",
            "artistStatus": "published",
            "youtubeUrl": "https://www.youtube.com/@suzuka1209",
            "instagramUrl": "https://www.instagram.com/suzuka12090511/",
            "searchKeywords": list(dict.fromkeys([
                definition["name"], definition["reading"], "AIアイドル", "AIアーティスト"
            ])),
            "artistFeaturedTracks": ["anata-dake-no-savior"],
            "officialSource": definition["officialSource"],
            "seo": {
                "title": f'{definition["name"]}｜SUZUKA Official Music',
                "description": f'{definition["profile"]} SUZUKAの架空のAIアーティストです。',
            },
        }
    cms["artists"] = sorted(artists.values(), key=lambda item: item["slug"])
    artist_types = {item["slug"]: item["type"] for item in cms["artists"]}

    evidence_path = root / "assets/data/youtube-publish-dates.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    records = {item["releaseSlug"]: item for item in evidence["records"]}
    verified_records = {
        "mermaid-no-geboku": {
            "youtubeId": "uibakv4n2Dg", "officialTitle": "神代煌牙『マーメイドの下僕』― おしゃべりな人魚姫に、心まで奪われた。",
            "publishedAt": "2026-08-08T20:00:06+09:00", "duration": 351,
        },
        "anata-dake-no-savior": {
            "youtubeId": "Z_IFHEG4CJA", "officialTitle": "ASTERIA『あなただけのSAVIOR』Official Music",
            "publishedAt": "2026-08-06T20:48:22+09:00", "duration": 415,
        },
    }
    published_defs = {item["slug"]: item for item in source["published"]}
    for slug, verified in verified_records.items():
        definition = published_defs[slug]
        records[slug] = {
            "releaseSlug": slug,
            "youtubeId": verified["youtubeId"],
            "youtubeUrl": definition["youtubeUrl"],
            "catalogReleaseDate": verified["publishedAt"][:10],
            "officialTitle": verified["officialTitle"],
            "channelId": source["officialChannelId"],
            "channelVerified": True,
            "youtubePublishDate": verified["publishedAt"],
            "youtubeUploadDate": verified["publishedAt"],
            "liveStartTimestamp": verified["publishedAt"],
            "playabilityStatus": "OK",
            "durationSeconds": verified["duration"],
            "verifiedPublishedAt": verified["publishedAt"],
            "verificationSource": "official-youtube-playerMicroformatRenderer.publishDate",
            "status": "verified-datetime",
        }
    for definition in source["upcoming"]:
        video_id = definition["youtubeUrl"].split("=")[-1]
        previous = records.get(definition["slug"], {})
        records[definition["slug"]] = {
            **previous,
            "releaseSlug": definition["slug"],
            "youtubeId": video_id,
            "youtubeUrl": definition["youtubeUrl"],
            "catalogReleaseDate": "",
            "officialTitle": previous.get("officialTitle", definition["title"]),
            "channelId": source["officialChannelId"],
            "channelVerified": True,
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

    releases = {item["slug"]: item for item in cms["releases"]}
    for definition in source["published"]:
        verified = verified_records[definition["slug"]]
        published_at = verified["publishedAt"]
        tags = list(dict.fromkeys([
            *definition["genres"], *definition["themes"], *definition["moods"]
        ]))
        previous = releases.get(definition["slug"], {})
        releases[definition["slug"]] = {
            **previous,
            "id": definition["slug"],
            "slug": definition["slug"],
            "title": definition["title"],
            "displayTitle": definition["title"],
            "englishTitle": definition["englishTitle"],
            "artist": definition["artist"],
            "artistSlug": definition["artistSlug"],
            "artistSlugs": [definition["artistSlug"]],
            "artistType": artist_types[definition["artistSlug"]],
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
            "newsUrl": f'news/{definition["slug"]}-release/',
            "duration": verified["duration"],
            "status": "published",
            "featured": False,
            "recommendationWeight": int(previous.get("recommendationWeight", 1)),
            "weeklyPickEligible": True,
            "analyticsEnabled": True,
            "upcomingPriority": 0,
            "relatedReleases": previous.get("relatedReleases", []),
            "searchKeywords": list(dict.fromkeys([
                definition["title"], definition["englishTitle"], definition["artist"], *tags
            ])),
            "aiArtistType": "fictional AI artist",
            "description": definition["description"],
            "tags": tags,
            "lyrics": previous.get("lyrics", ""),
            "lyricsAvailable": bool(previous.get("lyrics", "").strip()),
            "lyricsSource": previous.get("lyricsSource", ""),
            "lyricsText": previous.get("lyrics", ""),
            "introduction": definition["description"],
            "publishedAt": published_at,
            "instagramUrl": "",
            "shortsUrl": definition.get("shortsUrl", ""),
            "galleryImages": [definition["coverImage"]],
            "productionNote": definition["description"],
            "seo": {
                "title": f'{definition["title"]}｜{definition["artist"]}｜SUZUKA Official Music',
                "description": f'{definition["description"]} SUZUKAの架空のAIアーティスト作品です。',
                "jsonLdEnabled": True,
            },
            "videoPublishDate": published_at[:10],
            "videoPublishedAt": published_at,
            "videoPublishedAtSource": "official-youtube-playerMicroformatRenderer.publishDate",
            "videoStructuredDataStatus": "published",
            "officialSource": definition["youtubeUrl"],
            "playlistPriority": int(previous.get("playlistPriority", 0)),
            "homeHero": previous.get("homeHero", {}),
        }

    for release in releases.values():
        release.setdefault("releaseAt", release.get("publishedAt", release.get("releaseDate", "")))
        release.setdefault("lyricsAvailable", bool(str(release.get("lyrics", "")).strip()))
        release.setdefault("lyricsSource", "")
        release.setdefault("lyricsText", release.get("lyrics", ""))
        release.setdefault("weeklyPickEligible", bool(
            release.get("status") == "published" and release.get("coverImage") and release.get("releaseUrl")
        ))
        release.setdefault("analyticsEnabled", True)
        release.setdefault("upcomingPriority", 0)
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt", item["releaseDate"]), item["slug"]), reverse=True
    )

    news = {item["slug"]: item for item in cms["news"]}
    for definition in source["published"]:
        release = releases[definition["slug"]]
        slug = f'{definition["slug"]}-release'
        news[slug] = {
            "slug": slug,
            "title": f'{definition["artist"]}「{definition["title"]}」公開',
            "artistSlug": definition["artistSlug"],
            "releaseSlug": definition["slug"],
            "publishedAt": release["publishedAt"],
            "description": definition["description"],
            "image": definition["coverImage"],
            "status": "published",
        }
    cms["news"] = sorted(
        news.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )

    cms["upcoming"] = []
    for priority, definition in enumerate(source["upcoming"], 1):
        cms["upcoming"].append({
            **definition,
            "releaseAt": definition["scheduledAt"],
            "status": "upcoming",
            "note": "公式YouTubeで公開予定を確認済み。公開済み作品には含めていません。",
            "genres": [], "themes": [], "tags": [],
            "publishedAt": definition["scheduledAt"],
            "lyricsAvailable": False, "lyricsSource": "", "lyricsText": "",
            "featured": False, "recommendationWeight": None,
            "weeklyPickEligible": False, "analyticsEnabled": True,
            "upcomingPriority": priority,
        })

    # AIアイドルは特定の既存アーティスト名ではなく、正本のジャンルで自動選定する。
    for definition in cms.get("featureDefinitions", []):
        if definition.get("slug") == "ai-idols":
            definition["match"] = {"genres": ["アイドルポップ"]}
    for definition in cms.get("playlistDefinitions", []):
        if definition.get("slug") == "ai-idols":
            definition["match"] = {"genres": ["アイドルポップ"]}

    for artist in cms["artists"]:
        works = [item for item in cms["releases"] if artist["slug"] in item.get("artistSlugs", [])]
        artist.setdefault("artistType", artist["type"])
        artist.setdefault("artistStatus", artist.get("status", "published"))
        artist["artistFeaturedTracks"] = [item["slug"] for item in sorted(
            works, key=lambda item: (-int(item.get("recommendationWeight") or 0), item["releaseDate"], item["slug"]), reverse=False
        )[:3]]

    cms["schemaVersion"] = "3.1"
    cms["updatedAt"] = source["verifiedAt"]
    cms["youtubeSnapshot"] = source["channelSnapshot"]
    write_json(cms_path, cms)
    print(json.dumps({
        "artists": len(cms["artists"]),
        "published": len(cms["releases"]),
        "upcoming": len(cms["upcoming"]),
        "promoted": [item["slug"] for item in source["published"]],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

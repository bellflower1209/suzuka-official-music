#!/usr/bin/env python3
"""Promote verified releases and refresh scheduled works from official YouTube evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("assets/data/official-youtube-catalog-20260803.json"),
        help="official YouTube catalog relative to the site root",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    cms_path = root / "assets/data/creator-cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    catalog_path = args.catalog if args.catalog.is_absolute() else root / args.catalog
    source = json.loads(catalog_path.read_text(encoding="utf-8"))
    evidence = json.loads(
        (root / "assets/data/youtube-publish-dates.json").read_text(encoding="utf-8")
    )
    verified = {item["releaseSlug"]: item for item in evidence["records"]}
    existing = {item["slug"]: item for item in cms["releases"]}
    artist_types = {item["slug"]: item["type"] for item in cms["artists"]}

    for definition in source["published"]:
        record = verified.get(definition["slug"], {})
        if record.get("status") != "verified-datetime" or not record.get("verifiedPublishedAt"):
            raise RuntimeError(f'{definition["slug"]}: official publish datetime is not verified')
        if record.get("youtubeUrl") != definition["youtubeUrl"]:
            raise RuntimeError(f'{definition["slug"]}: YouTube URL differs from official evidence')
        published_at = record["verifiedPublishedAt"]
        duration = int(record.get("durationSeconds") or 0)
        if duration <= 0:
            raise RuntimeError(f'{definition["slug"]}: official duration is missing')
        tags = list(dict.fromkeys([
            *definition["genres"], *definition["themes"], *definition["moods"]
        ]))
        item = {
            **existing.get(definition["slug"], {}),
            "id": definition["slug"],
            "slug": definition["slug"],
            "title": definition["title"],
            "displayTitle": definition["title"],
            "englishTitle": definition["englishTitle"],
            "artist": definition["artist"],
            "artistSlug": definition["artistSlug"],
            "artistSlugs": [definition["artistSlug"]],
            "artistType": artist_types[definition["artistSlug"]],
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
            "duration": duration,
            "status": "published",
            "featured": True,
            "recommendationWeight": 3,
            "relatedReleases": [],
            "searchKeywords": list(dict.fromkeys([
                definition["title"], definition["englishTitle"], definition["artist"], *tags
            ])),
            "aiArtistType": "fictional AI artist",
            "description": definition["description"],
            "tags": tags,
            "lyrics": "",
            "introduction": definition["description"],
            "publishedAt": published_at,
            "instagramUrl": "",
            "shortsUrl": "",
            "galleryImages": [definition["coverImage"]],
            "productionNote": definition["description"],
            "seo": {
                "title": f'{definition["title"]}｜{definition["artist"]}｜SUZUKA Official Music',
                "description": f'{definition["description"]} SUZUKAの架空のAIアーティスト作品です。',
                "jsonLdEnabled": True,
            },
            "videoPublishDate": published_at[:10],
            "videoPublishedAt": published_at,
            "videoPublishedAtSource": record["verificationSource"],
            "videoStructuredDataStatus": "published",
            "officialSource": definition["youtubeUrl"],
        }
        existing[item["slug"]] = item

    cms["releases"] = sorted(
        existing.values(), key=lambda item: (item["releaseDate"], item["slug"]), reverse=True
    )
    for replacement in source.get("assetReplacements", []):
        release = next(item for item in cms["releases"] if item["slug"] == replacement["slug"])
        release["coverImage"] = replacement["coverImage"]
        release["galleryImages"] = [replacement["coverImage"]]
        for news_item in cms.get("news", []):
            if news_item.get("releaseSlug") == replacement["slug"]:
                news_item["image"] = replacement["coverImage"]
    cms["upcoming"] = [
        {
            **item,
            "status": "upcoming",
            "image": f'https://i.ytimg.com/vi/{item["youtubeUrl"].split("=")[-1]}/maxresdefault.jpg',
            "note": "公式YouTubeで公開予定を確認済み。公開済み作品には含めていません。",
            "genres": [],
            "themes": [],
            "tags": [],
            "publishedAt": item["scheduledAt"],
        }
        for item in source["upcoming"]
    ]

    news_by_slug = {item["slug"]: item for item in cms["news"]}
    legacy_shadow_news = news_by_slug.pop("shadow-code-release", None)
    if legacy_shadow_news:
        news_by_slug["shadow-code-announcement"] = {
            **legacy_shadow_news,
            "slug": "shadow-code-announcement",
            "title": "デビューシングル「SHADOW//CODE」を発表。",
        }
    published_by_slug = {item["slug"]: item for item in cms["releases"]}
    for definition in source["published"]:
        release = published_by_slug[definition["slug"]]
        slug = f'{definition["slug"]}-release'
        news_by_slug[slug] = {
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
        news_by_slug.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )
    cms["updatedAt"] = source["verifiedAt"]
    cms_path.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mia_path = root / "assets/data/enomoto-mia-releases.json"
    mia = json.loads(mia_path.read_text(encoding="utf-8"))
    mia_by_slug = {item.get("slug"): item for item in mia["releases"] if item.get("slug")}
    if "smile-and-say-goodbye" in mia_by_slug:
        mia_by_slug["smile-and-say-goodbye"]["image"] = "images/youtube-smile-and-say-goodbye.jpg"
    without = next(item for item in cms["releases"] if item["slug"] == "without-worrying")
    mia_by_slug["without-worrying"] = {
        "title": without["title"],
        "titleEnglish": without["englishTitle"],
        "slug": without["slug"],
        "status": "published",
        "pageUrl": without["releaseUrl"],
        "youtubeUrl": without["youtubeUrl"],
        "youtubeId": without["youtubeUrl"].split("=")[-1],
        "youtubeVideoTitle": "Without Worrying／榎本魅愛｜あなたはひとりじゃない。",
        "image": without["coverImage"],
        "duration": without["duration"],
        "uploadDate": without["releaseDate"],
        "shortDescription": without["description"],
        "featured": True,
        "playerEnabled": False,
        "relatedSongs": ["mirai-no-watashi-ga-miteru", "moshimo-ashita-hajimemashite-ni-natte-mo", "hyakumankoku"],
    }
    unpublished = [item for item in mia["releases"] if not item.get("slug")]
    mia["releases"] = sorted(
        mia_by_slug.values(), key=lambda item: (item.get("uploadDate", ""), item["slug"]), reverse=True
    ) + unpublished
    mia["updatedAt"] = source["verifiedAt"][:10]
    mia_path.write_text(json.dumps(mia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "published": len(cms["releases"]),
        "upcoming": len(cms["upcoming"]),
        "promoted": [item["slug"] for item in source["published"]],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

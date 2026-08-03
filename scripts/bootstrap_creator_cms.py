#!/usr/bin/env python3
"""One-time migration from the existing catalogs to the Creator CMS source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_explorer_update import ARTISTS, FEATURES, UPDATED_AT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "assets/data/creator-cms.json"
    if output.exists() and not args.force:
        raise SystemExit(f"{output} already exists; use --force only for an intentional re-migration")

    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    links = json.loads((root / "assets/data/release-links.json").read_text(encoding="utf-8"))
    social = json.loads((root / "assets/data/social-links.json").read_text(encoding="utf-8"))
    link_by_slug = {item["slug"]: item for item in links["releases"]}
    releases = []
    for item in catalog["releases"]:
        source = link_by_slug.get(item["slug"], {})
        releases.append({
            **item,
            "tags": list(dict.fromkeys(item["genres"] + item["themes"] + item["moods"])),
            "lyrics": "",
            "introduction": item["description"],
            "publishedAt": f'{item["releaseDate"]}T20:00:00+09:00',
            "instagramUrl": "",
            "shortsUrl": source.get("shortsUrl", ""),
            "galleryImages": [item["coverImage"]],
            "productionNote": item["description"],
            "seo": {
                "title": f'{item["title"]}｜{item["artist"]}｜SUZUKA Official Music',
                "description": item["description"],
                "jsonLdEnabled": True,
            },
        })
    upcoming = [
        {
            **item,
            "genres": [],
            "themes": [],
            "tags": [],
            "description": item["note"],
            "publishedAt": item["scheduledAt"],
        }
        for item in catalog["upcoming"]
    ]
    artists = [
        {
            "slug": slug,
            **value,
            "status": "published",
            "youtubeUrl": "https://www.youtube.com/@suzuka1209",
            "instagramUrl": "https://www.instagram.com/suzuka12090511/",
            "searchKeywords": [value["name"], value["reading"]],
            "seo": {
                "title": f'{value["name"]}｜SUZUKA Official AI Artist',
                "description": f'{value["profile"]} SUZUKAの架空のAIアーティストです。',
                "jsonLdEnabled": True,
            },
        }
        for slug, value in ARTISTS.items()
    ]
    news = [
        {
            "slug": item["slug"] + "-release",
            "title": f'{item["artist"]}「{item["title"]}」公開',
            "artistSlug": item["artistSlug"],
            "releaseSlug": item["slug"],
            "publishedAt": item["publishedAt"],
            "description": item["description"],
            "image": item["coverImage"],
            "status": "published",
        }
        for item in releases if item.get("newsUrl")
    ]
    genres = sorted({genre for item in releases for genre in item["genres"]})
    themes = sorted({theme for item in releases for theme in item["themes"]})
    tags = sorted({tag for item in releases for tag in item["tags"]})
    feature_definitions = []
    for slug, (label, description, _) in FEATURES.items():
        rules = {
            "love-songs": {"themes": ["恋愛", "愛", "誓い"], "artistSlugs": ["enomoto-mia"]},
            "cheer-songs": {"themes": ["希望", "再生", "明日", "祈り"]},
            "tearjerkers": {"themes": ["別れ", "記憶", "痛み", "忘却"]},
            "summer-songs": {"themes": ["夏", "海"], "genres": ["サマーポップ"]},
            "winter-songs": {"themes": ["冬"]},
            "dark": {"moods": ["ダーク"], "genreContains": ["ダーク"]},
            "k-pop": {"genres": ["K-POP風"]},
            "enka": {"genres": ["演歌"]},
            "visual-kei": {"genres": ["V系"]},
            "ai-idols": {"artistSlugs": ["revive", "rangili"]},
            "ai-bands": {"artistSlugs": ["nox", "eclypse"]},
        }[slug]
        feature_definitions.append({"slug": slug, "label": label, "description": description, "match": rules})
    payload = {
        "schemaVersion": "3.0",
        "updatedAt": UPDATED_AT,
        "site": {
            "name": "SUZUKA",
            "baseUrl": "https://www.suzukaofficial.com",
            "description": "音楽から新しい物語を始めるオリジナルAIアーティスト総合プラットフォーム。",
            "youtubeUrl": "https://www.youtube.com/@suzuka1209",
            "youtubeChannelId": "UCVde75yhByGQMu3SkO-fzrA",
            "instagramUrl": next((x["url"] for x in social["links"] if x["platform"] == "instagram"), ""),
            "defaultLanguage": "ja",
            "supportedLanguages": ["ja", "en"],
        },
        "artists": artists,
        "releases": releases,
        "upcoming": upcoming,
        "news": news,
        "taxonomy": {"genres": genres, "themes": themes, "tags": tags},
        "featureDefinitions": feature_definitions,
        "playlistDefinitions": [
            {"slug": "love", "label": "恋愛", "match": {"themes": ["恋愛", "愛", "誓い"], "artistSlugs": ["enomoto-mia"]}},
            {"slug": "summer", "label": "夏", "match": {"themes": ["夏", "海"], "genres": ["サマーポップ"]}},
            {"slug": "winter", "label": "冬", "match": {"themes": ["冬"]}},
            {"slug": "cheer", "label": "応援", "match": {"themes": ["希望", "再生", "明日", "祈り"]}},
            {"slug": "tearjerkers", "label": "泣ける", "match": {"themes": ["別れ", "記憶", "痛み", "忘却"]}},
            {"slug": "ai-idols", "label": "AIアイドル", "match": {"artistSlugs": ["revive", "rangili"]}},
            {"slug": "k-pop", "label": "K-POP風", "match": {"genres": ["K-POP風"]}},
            {"slug": "visual-kei", "label": "V系", "match": {"genres": ["V系"]}},
            {"slug": "enka", "label": "演歌", "match": {"genres": ["演歌"]}},
            {"slug": "popular", "label": "人気曲", "sort": "popular"},
            {"slug": "latest", "label": "最新曲", "sort": "latest"},
            {"slug": "music-videos", "label": "MV付き", "match": {"hasYoutube": True}},
        ],
        "wiki": {
            "terms": [
                {"term": "SUZUKA", "description": "音楽から新しい物語を始めるオリジナルAI音楽プロジェクト。"},
                {"term": "AIアーティスト", "description": "SUZUKAの作品世界に登場する架空のアーティスト表現。"},
                {"term": "Weekly Pick", "description": "正本データから週ごとに決定的に選ばれるおすすめ作品。"},
                {"term": "recommendationWeight", "description": "ランキングとおすすめに利用する推薦値。"},
                {"term": "Official MV", "description": "公式YouTubeで公開確認した映像。"},
            ]
        },
        "universe": {
            "title": "SUZUKA UNIVERSE",
            "story": "異なる世界観を持つAIアーティストと作品が、音楽を通してひとつの宇宙を形づくる。",
            "keywords": ["恋", "誓い", "光と闇", "記憶", "再生", "文化", "宇宙"],
            "future": ["新アーティスト", "新作品", "物語連携", "イベント"],
        },
        "community": {
            "monthlyRankingSource": "recommendations",
            "polls": [{"id": "favorite-song", "question": "今月のおすすめ曲は？", "status": "open"}],
            "surveys": [{"id": "next-feature", "question": "次に読みたい特集は？", "status": "open"}],
            "events": [],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created Creator CMS source: {len(artists)} artists, {len(releases)} releases, {len(upcoming)} upcoming")


if __name__ == "__main__":
    main()

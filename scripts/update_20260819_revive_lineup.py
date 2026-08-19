#!/usr/bin/env python3
"""Apply the user-verified 2026-08-19 RE:VIVE lineup to the canonical CMS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


CURRENT_MEMBERS = [
    {
        "name": "白石 陽向",
        "reading": "しらいし ひなた",
        "stageName": "HINATA",
        "image": "images/revive-hinata-shiraishi-profile.png",
        "imageAlt": "RE:VIVE 白石陽向 公式プロフィール",
        "imageWidth": 1535,
        "imageHeight": 1024,
    },
    {
        "name": "天城 結衣",
        "reading": "あまぎ ゆい",
        "stageName": "YUI",
        "image": "images/revive-yui-amagi-profile.png",
        "imageAlt": "RE:VIVE 天城結衣 公式プロフィール",
        "imageWidth": 1536,
        "imageHeight": 1024,
    },
    {
        "name": "月城 蒼依",
        "reading": "つきしろ あおい",
        "stageName": "AOI",
        "image": "images/revive-aoi-tsukishiro-profile.png",
        "imageAlt": "RE:VIVE 月城蒼依 公式プロフィール",
        "imageWidth": 1536,
        "imageHeight": 1024,
    },
    {
        "name": "橘 紗良",
        "reading": "たちばな さら",
        "stageName": "SARA",
        "image": "images/revive-sara-tachibana-profile.png",
        "imageAlt": "RE:VIVE 橘紗良 公式プロフィール",
        "imageWidth": 1536,
        "imageHeight": 1024,
    },
    {
        "name": "星宮 羽音",
        "reading": "ほしみや はのん",
        "stageName": "HANON",
        "artistSlug": "hoshimiya-hanon",
        "role": "最年少／透明感ボーカル",
        "color": "スノーホワイト",
        "motif": "星と新しい羽",
        "image": "images/revive-hanon-hoshimiya-profile.png",
        "imageAlt": "RE:VIVE 星宮羽音 公式プロフィール",
        "imageWidth": 1448,
        "imageHeight": 1086,
    },
]


HANON = {
    "slug": "hoshimiya-hanon",
    "name": "星宮 羽音",
    "reading": "ほしみや はのん",
    "englishName": "Hoshimiya Hanon",
    "stageName": "HANON",
    "type": "Person",
    "artistType": "Person",
    "image": "images/revive-hanon-hoshimiya-profile.png",
    "imageAlt": "RE:VIVE 星宮羽音 公式プロフィール",
    "imageWidth": 1448,
    "imageHeight": 1086,
    "world": "RE:VIVEの希望と未来を照らす、星と新しい羽をモチーフとする存在。",
    "music": "透明感あふれる歌声でRE:VIVEの楽曲を支えるボーカル。",
    "profile": "透明感あふれる歌声で、RE:VIVEの希望と未来を照らす存在。素直で好奇心旺盛だが芯が強く、決めたことは曲げない。",
    "birthday": "12月24日",
    "age": 18,
    "hometown": "千葉県",
    "affiliation": "RE:VIVE",
    "role": "最年少／透明感ボーカル",
    "memberColor": "スノーホワイト",
    "motif": "星と新しい羽",
    "catchphrase": "小さな声でも、ちゃんと届くって信じてる。",
    "status": "published",
    "artistStatus": "published",
    "youtubeUrl": "https://www.youtube.com/@suzuka1209",
    "instagramUrl": "https://www.instagram.com/suzuka12090511/",
    "searchKeywords": ["星宮 羽音", "星宮羽音", "ほしみや はのん", "HANON", "Hoshimiya Hanon", "RE:VIVE"],
    "artistFeaturedTracks": [],
    "homeFeatured": True,
    "officialSource": "user-verified profile and official visual supplied 2026-08-19",
    "seo": {
        "title": "星宮羽音｜RE:VIVE｜SUZUKA Official Music",
        "description": "RE:VIVEの最年少・透明感ボーカル、星宮羽音の公式プロフィール。SUZUKAの架空のAIアーティストです。",
    },
}


MIU = {
    "slug": "hoshino-miu",
    "name": "星乃みう",
    "reading": "ほしの みう",
    "englishName": "Hoshino Miu",
    "stageName": "MIU",
    "type": "Person",
    "artistType": "Person",
    "image": "",
    "world": "RE:VIVEでの活動履歴を経て、現在はASTERIAに所属する。",
    "music": "ASTERIAではダンスリーダーを担当。",
    "profile": "星乃みうは、過去にRE:VIVEのメンバーとして活動し、現在はASTERIAに所属するAIアーティスト。",
    "affiliation": "ASTERIA",
    "formerAffiliations": ["RE:VIVE"],
    "role": "ダンスリーダー",
    "memberColor": "スカイブルー",
    "status": "published",
    "artistStatus": "published",
    "youtubeUrl": "https://www.youtube.com/@suzuka1209",
    "instagramUrl": "https://www.instagram.com/suzuka12090511/",
    "searchKeywords": ["星乃みう", "Hoshino Miu", "MIU", "ASTERIA", "RE:VIVE"],
    "artistFeaturedTracks": [],
    "homeFeatured": True,
    "officialSource": "user-verified current affiliation supplied 2026-08-19",
    "seo": {
        "title": "星乃みう｜ASTERIA｜SUZUKA Official Music",
        "description": "ASTERIA所属の星乃みう公式プロフィール。RE:VIVE在籍時の活動履歴も保持しています。SUZUKAの架空のAIアーティストです。",
    },
}


def upsert_artist(artists: list[dict], record: dict) -> None:
    for index, artist in enumerate(artists):
        if artist.get("slug") == record["slug"]:
            artists[index] = record
            return
    artists.append(record)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    path = root / "assets/data/creator-cms.json"
    cms = json.loads(path.read_text(encoding="utf-8"))
    artists = cms["artists"]

    revive = next(item for item in artists if item["slug"] == "revive")
    revive["members"] = CURRENT_MEMBERS
    revive["profile"] = "前へ進む力を届ける、現行5人体制のAIガールズグループ。"
    revive["searchKeywords"] = ["RE:VIVE", "リバイブ", "白石陽向", "天城結衣", "月城蒼依", "橘紗良", "星宮羽音", "HANON"]
    revive["currentLineupVerifiedAt"] = "2026-08-19"
    revive["seo"]["description"] = "白石陽向、天城結衣、月城蒼依、橘紗良、星宮羽音の5名で活動するAIガールズグループ。SUZUKAの架空のAIアーティストです。"

    asteria = next(item for item in artists if item["slug"] == "asteria")
    miu_member = next(item for item in asteria["members"] if item["name"] == "星乃みう")
    miu_member["artistSlug"] = "hoshino-miu"
    miu_member["currentAffiliation"] = "ASTERIA"

    upsert_artist(artists, HANON)
    upsert_artist(artists, MIU)
    artists.sort(key=lambda item: item["slug"])
    cms["updatedAt"] = "2026-08-19T00:00:00+09:00"
    path.write_text(json.dumps(cms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated canonical RE:VIVE lineup, Hoshimiya Hanon, and Hoshino Miu affiliation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

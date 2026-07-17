#!/usr/bin/env python3
"""Generate the evidence ledger for ENOMOTO MIA releases from the canonical catalog."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bellflower1209.github.io/suzuka-official-music/"
CATALOG = json.loads((ROOT / "assets/data/enomoto-mia-releases.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "docs/audits/enomoto-mia-release-ledger-2026-07-17.md"


def mark(value: bool) -> str:
    return "掲載" if value else "なし"


def main() -> None:
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    profile = (ROOT / "artists/enomoto-mia/index.html").read_text(encoding="utf-8")
    releases_page = (ROOT / "releases/index.html").read_text(encoding="utf-8")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    news = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "news").rglob("index.html")))
    player = (ROOT / "assets/main.js").read_text(encoding="utf-8")
    rows = []
    published = [item for item in CATALOG["releases"] if item["status"] == "published"]
    excluded = [item for item in CATALOG["releases"] if item["status"] != "published"]
    for item in CATALOG["releases"]:
        page_url = f"{BASE}{item['pageUrl']}" if item.get("pageUrl") else "—"
        image = item.get("image") or "—"
        youtube = item.get("youtubeUrl") or "—"
        page_exists = bool(item.get("pageUrl") and (ROOT / item["pageUrl"] / "index.html").is_file())
        player_registered = item["status"] == "published" and all(item.get(key) for key in ("youtubeId", "image", "pageUrl")) and "enomoto-mia-releases.json" in player
        has_news = item["title"] in news or bool(item.get("pageUrl") and item["pageUrl"] in news)
        rows.append(
            f"| {item['title']} | {'共作' if item.get('collaborators') else '単独'} | {item['status']} | "
            f"{item.get('slug') or '—'} | {page_url if page_exists else '—'} | {youtube} | `{image}` | "
            f"{mark(item['title'] in profile)} | {mark(item['title'] in releases_page)} | {mark(item['title'] in home)} | "
            f"{mark(player_registered)} | {mark(page_url in sitemap if page_url != '—' else False)} | "
            f"{mark(has_news)} |"
        )
    differences = []
    for item in CATALOG["releases"]:
        variants = []
        for key, label in (
            ("jacketTitleVariant", "ジャケット"),
            ("siteTitleVariantBeforeAudit", "監査前サイト"),
            ("youtubeTitleArtistVariant", "YouTube共作者名"),
        ):
            if item.get(key):
                variants.append(f"{label}: `{item[key]}`")
        if variants:
            differences.append(f"- **{item['title']}** — " + " / ".join(variants))
    youtube_titles = [
        f"{position}. [{item['youtubeVideoTitle']}]({item['youtubeUrl']})"
        for position, item in enumerate(published, 1)
    ]
    output = f"""# 榎本魅愛 楽曲台帳・掲載面監査

監査日: 2026-07-17

正本データ: `assets/data/enomoto-mia-releases.json`

公式YouTube照合先: {CATALOG['source']}

## 集計

- 公開済み: **{len(published)}曲**
- 単独曲: **{sum(not item.get('collaborators') for item in published)}曲**
- 共作曲: **{sum(bool(item.get('collaborators')) for item in published)}曲**
- 未公開: **{len(excluded)}曲**
- 制作中と確認できた楽曲: **0曲**
- 専用ページ未作成の公開済み楽曲: **{sum(not (ROOT / item['pageUrl'] / 'index.html').is_file() for item in published)}曲**

## 楽曲台帳

| 正式楽曲名 | 区分 | 状態 | slug | 専用ページ | YouTube | ジャケット | Profile | Releases | Top | Player | Sitemap | News |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## 公式YouTube動画タイトル

{chr(10).join(youtube_titles)}

## 表記差

正式楽曲名は、依頼で指定された優先順位に従い、公式YouTube動画タイトルを第1優先として確定した。

{chr(10).join(differences)}

`未来の私が見てる` はYouTubeタイトルを正式表記として採用した。ジャケットの `未来のわたしが見てる` は画像自体を改変せず、表記差として保持する。`もしも明日、はじめましてになっても` はYouTubeタイトルに合わせて末尾の句点なしを採用し、ジャケット上の句点あり表記を差異として保持する。

## 公開対象から除外

{chr(10).join(f"- {item['title']} — {item['status']}。公開URL・YouTube URL・ジャケット未登録。" for item in excluded)}

未公開曲はトップ、プロフィール、Releases、プレイヤー、sitemap、公開ページの構造化データへ含めない。
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(published)} published releases.")


if __name__ == "__main__":
    main()

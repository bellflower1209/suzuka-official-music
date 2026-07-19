#!/usr/bin/env python3
"""Keep locally confirmed release cards and artist discographies in generated pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://bellflower1209.github.io/suzuka-official-music"


def insert_grid_cards(path: Path, cards: str, slugs: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    if all(slug in text for slug in slugs):
        return
    missing = [card for slug, card in zip(slugs, cards.split("<!--CARD-->", 1)) if slug not in text]
    text = text.replace('<div class="release-grid">', '<div class="release-grid">' + "".join(missing), 1)
    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f"{match.group(1)}{number:02d}{match.group(2)}"

    text = re.sub(r'(<div class="release-row"><span>)\d+(</span>)', renumber, text)
    path.write_text(text, encoding="utf-8")


def insert_after(path: Path, marker: str, content: str, sentinel: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel not in text:
        text = text.replace(marker, marker + content, 1)
        path.write_text(text, encoding="utf-8")


def update_item_list(path: Path, items: list[dict]) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)(.*?)</script>', re.DOTALL)
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            nodes = [data]
        target = next((node for node in nodes if isinstance(node, dict) and node.get("@type") == "ItemList"), None)
        if not target:
            return match.group(0)
        target["numberOfItems"] = len(items)
        target["itemListElement"] = [
            {
                "@type": "ListItem",
                "position": index,
                "name": item["title"],
                "url": f"{PUBLIC_BASE}/{item['releasePage']}",
            }
            for index, item in enumerate(items, 1)
        ]
        changed = True
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"

    text = pattern.sub(replace, text)
    if changed:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    releases = json.loads((ROOT / "assets/data/release-links.json").read_text(encoding="utf-8"))["releases"]
    smile_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/smile-and-say-goodbye/" aria-label="SMILE AND SAY GOODBYEの詳細を見る"><img src="./images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><span class="card-wash wash-pink"></span></a><div class="release-info"><div class="release-row"><span>01</span><span>NEW RELEASE · OFFICIAL PAGE</span></div><h3>SMILE AND SAY GOODBYE</h3><p>大好きだから、笑ってさようなら。</p><p class="release-artist-credit">榎本魅愛</p><a class="release-card-cta release-card-cta-detail" href="./releases/smile-and-say-goodbye/">楽曲情報を見る <span aria-hidden="true">↗</span></a></div></article>'
    boukyaku_home = '<article class="release-card release-card-new"><a class="release-image" href="./releases/boukyaku-no-ikimono/" aria-label="忘却の生き物の詳細を見る"><img src="./images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><span class="card-wash wash-gold"></span></a><div class="release-info"><div class="release-row"><span>02</span><span>NEW RELEASE · OFFICIAL PAGE</span></div><h3>忘却の生き物</h3><p>時代のせいじゃない。忘れ去る人間の仕事だ。</p><p class="release-artist-credit">神代 煌牙</p><a class="release-card-cta release-card-cta-detail" href="./releases/boukyaku-no-ikimono/">楽曲情報を見る <span aria-hidden="true">↗</span></a></div></article>'
    insert_grid_cards(ROOT / "index.html", smile_home + "<!--CARD-->" + boukyaku_home, ("./releases/smile-and-say-goodbye/", "./releases/boukyaku-no-ikimono/"))

    smile_index = smile_home.replace('./releases/', './').replace('./images/', '../images/')
    boukyaku_index = boukyaku_home.replace('./releases/', './').replace('./images/', '../images/')
    insert_grid_cards(ROOT / "releases/index.html", smile_index + "<!--CARD-->" + boukyaku_index, ("./smile-and-say-goodbye/", "./boukyaku-no-ikimono/"))

    mia = ROOT / "artists/enomoto-mia/index.html"
    mia_featured = '<article class="artist-featured-card artist-featured-card-new"><a href="../../releases/smile-and-say-goodbye/" aria-label="SMILE AND SAY GOODBYEの楽曲情報を見る"><div class="artist-featured-image"><img src="../../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/></div><div class="artist-featured-copy"><span>01 / New Release</span><h3>SMILE AND SAY GOODBYE</h3><p>大好きだから、笑ってさようなら。</p></div></a></article>'
    insert_after(mia, '<div class="artist-featured-grid artist-featured-grid-expanded">', mia_featured, '../../releases/smile-and-say-goodbye/')
    mia_row = '<a class="artist-track-row artist-track-row-new" href="../../releases/smile-and-say-goodbye/"><span>01</span><img src="../../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><div><strong>SMILE AND SAY GOODBYE</strong><small>大好きだから、笑ってさようなら。</small></div><b aria-hidden="true">↗</b></a>'
    insert_after(mia, '<div class="artist-track-list">', mia_row, 'artist-track-row artist-track-row-new" href="../../releases/smile-and-say-goodbye/')

    koga = ROOT / "artists/koga-kamishiro/index.html"
    koga_row = '<a class="artist-track-row" href="../../releases/boukyaku-no-ikimono/"><span>01</span><img src="../../images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><div><strong>忘却の生き物</strong><small>Official release page</small></div><b aria-hidden="true">↗</b></a>'
    insert_after(koga, '<div class="artist-track-list">', koga_row, '../../releases/boukyaku-no-ikimono/')
    koga_text = koga.read_text(encoding="utf-8")
    if 'id="koga-release-itemlist"' not in koga_text:
        koga_items = [
            ("忘却の生き物", "boukyaku-no-ikimono"),
            ("My Queen, My Oath", "my-queen-my-oath"),
            ("OUR KINGDOM", "our-kingdom"),
        ]
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": f"{PUBLIC_BASE}/artists/koga-kamishiro/#releases",
            "name": "神代 煌牙 公開作品",
            "numberOfItems": len(koga_items),
            "itemListElement": [
                {"@type": "ListItem", "position": position, "name": title, "url": f"{PUBLIC_BASE}/releases/{slug}/"}
                for position, (title, slug) in enumerate(koga_items, 1)
            ],
        }
        script = '<script id="koga-release-itemlist" type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + "</script>"
        koga.write_text(koga_text.replace("</head>", script + "</head>", 1), encoding="utf-8")

    social = ROOT / "social/index.html"
    social_cards = '<a class="social-hub-card" href="../releases/smile-and-say-goodbye/"><img src="../images/mv-smile-and-say-goodbye.png" alt="榎本魅愛「SMILE AND SAY GOODBYE」公式ジャケット" width="1672" height="941" loading="lazy"/><div><small>ENOMOTO MIA</small><strong>SMILE AND SAY GOODBYE</strong><span>楽曲の物語を見る →</span></div></a><a class="social-hub-card" href="../releases/boukyaku-no-ikimono/"><img src="../images/mv-boukyaku-no-ikimono.png" alt="神代 煌牙「忘却の生き物」公式ジャケット" width="1672" height="940" loading="lazy"/><div><small>KOGA KAMISHIRO</small><strong>忘却の生き物</strong><span>楽曲の物語を見る →</span></div></a>'
    insert_after(social, '<div class="social-hub-grid">', social_cards, '../releases/smile-and-say-goodbye/')

    for path in (mia, koga):
        text = path.read_text(encoding="utf-8")
        number = 0
        def renumber(match: re.Match[str]) -> str:
            nonlocal number
            number += 1
            return f"{match.group(1)}{number:02d}{match.group(2)}"
        text = re.sub(r'(<a class="artist-track-row[^"]*"[^>]*><span>)\d+(</span>)', renumber, text)
        path.write_text(text, encoding="utf-8")

    update_item_list(ROOT / "releases/index.html", releases)
    update_item_list(mia, [item for item in releases if item["artistSlug"] == "enomoto-mia"])
    print(f"Updated static catalogs for {len(releases)} releases.")


if __name__ == "__main__":
    main()

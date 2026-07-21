#!/usr/bin/env python3
"""Apply SUZUKA Coming Soon artists and scheduled-release notices idempotently."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BASE = "https://bellflower1209.github.io/suzuka-official-music"
BOUKYAKU_YOUTUBE = "https://youtu.be/yREvkT9gEk4"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label}, found {count}.")
    return source.replace(old, new, 1)


def ensure_stylesheet(source: str, href: str) -> str:
    link = f'<link rel="stylesheet" href="{href}"/>'
    if link in source:
        return source
    return replace_once(source, "</head>", f"{link}</head>", "upcoming stylesheet insertion point")


def remove_article_for_route(source: str, route: str) -> str:
    pattern = rf'<article class="release-card[^"]*">(?:(?!</article>).)*?href="[^"]*{re.escape(route)}[^"]*"(?:(?!</article>).)*?</article>'
    return re.sub(pattern, "", source, flags=re.DOTALL)


def renumber_release_cards(source: str) -> str:
    number = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f'{match.group(1)}{number:02d}{match.group(2)}'

    return re.sub(r'(<div class="release-row"><span>)\d+(</span>)', repl, source)


def update_json_ld_item_list(source: str, item_list_id: str, additions: list[dict]) -> str:
    script_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)

    def update(match: re.Match[str]) -> str:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        changed = False
        for node in nodes:
            if node.get("@id") != item_list_id:
                continue
            items = node.setdefault("itemListElement", [])
            known = {item.get("url") for item in items}
            for addition in additions:
                if addition["url"] not in known:
                    items.append({"@type": "ListItem", "position": len(items) + 1, **addition})
            for position, item in enumerate(items, 1):
                item["position"] = position
            node["numberOfItems"] = len(items)
            changed = True
        if not changed:
            return match.group(0)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"

    return script_pattern.sub(update, source)


def remove_json_ld_item(source: str, item_list_id: str, url: str) -> str:
    script_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)

    def update(match: re.Match[str]) -> str:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        nodes = data.get("@graph", []) if isinstance(data, dict) else []
        changed = False
        for node in nodes:
            if node.get("@id") != item_list_id:
                continue
            items = [item for item in node.get("itemListElement", []) if item.get("url") != url]
            for position, item in enumerate(items, 1):
                item["position"] = position
            node["itemListElement"] = items
            node["numberOfItems"] = len(items)
            changed = True
        if not changed:
            return match.group(0)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"

    return script_pattern.sub(update, source)


def update_home(path: Path) -> None:
    source = ensure_stylesheet(path.read_text(encoding="utf-8"), "./assets/upcoming.css")
    if 'id="upcoming-artists"' not in source:
        section = (
            '<section class="upcoming-section" id="upcoming-artists" aria-labelledby="upcoming-title">'
            '<div class="upcoming-heading"><div><p class="section-kicker">05 / Coming Soon</p>'
            '<h2 id="upcoming-title">Upcoming Artists</h2></div><p>SUZUKAから始まる、次の物語。2組のアーティストがデビューへ向けて準備中です。</p></div>'
            '<div class="upcoming-grid">'
            '<article class="upcoming-card"><a href="./artists/rangili/"><div class="upcoming-card-image"><img src="./images/rangili-coming-soon.jpg" alt="RANGILI 3人組ガールグループ Coming Soon ビジュアル" width="1254" height="1254" loading="lazy"/></div><div class="upcoming-card-copy"><span class="coming-soon-badge">Coming Soon</span><h3>RANGILI<small>GIRL GROUP</small></h3><p>インドと日本、2つの文化が響き合う3人組ガールグループ。</p><b>Artist introduction ↗</b></div></a></article>'
            '<article class="upcoming-card"><a href="./artists/asagiri-shinobu/"><div class="upcoming-card-image"><img src="./images/asagiri-shinobu-coming-soon.jpg" alt="朝霧しのぶ 演歌歌手 Coming Soon ビジュアル" width="1254" height="1254" loading="lazy"/></div><div class="upcoming-card-copy"><span class="coming-soon-badge">Coming Soon</span><h3>朝霧しのぶ<small>演歌</small></h3><p>人生の喜びや別れ、家族の想いを歌い続ける演歌歌手。</p><b>Artist introduction ↗</b></div></a></article>'
            '</div></section>'
        )
        source = replace_once(source, '<section class="section about-section label-about-home"', section + '<section class="section about-section label-about-home"', "home About section")
    source = source.replace('05 / About SUZUKA', '06 / About SUZUKA').replace('06 / News', '07 / News').replace('07 / Official YouTube', '08 / Official YouTube')
    if './news/upcoming-artists/' not in source:
        card = '<article><a href="./news/upcoming-artists/" aria-label="SUZUKA Upcoming ArtistsのNews記事を見る"><time datetime="2026-07-22">2026.07.22</time><span>ARTIST NEWS</span><h3>SUZUKA Upcoming Artists — RANGILI・朝霧しのぶ</h3><b aria-hidden="true">↗</b></a></article>'
        source = replace_once(source, '<div class="news-list">', '<div class="news-list">' + card, "home News list")
    source = remove_article_for_route(source, 'releases/smile-and-say-goodbye/')
    source = renumber_release_cards(source)
    path.write_text(source, encoding="utf-8")


def update_artists_index(path: Path) -> None:
    source = ensure_stylesheet(path.read_text(encoding="utf-8"), "../assets/upcoming.css")
    if '../artists/rangili/' not in source:
        cards = (
            '<article class="artist-directory-card artist-coming-soon-card" style="--artist-primary:#ff62c8;--artist-secondary:#130a18;--artist-glow:rgba(255,98,200,.3)"><a href="../artists/rangili/" aria-label="RANGILIの紹介ページへ"><div class="artist-directory-image"><img src="../images/rangili-coming-soon.jpg" alt="RANGILI 3人組ガールグループ Coming Soon ビジュアル" width="1254" height="1254" loading="lazy"/><span class="artist-directory-number">04</span></div><div class="artist-directory-copy"><span class="coming-soon-badge">Coming Soon</span><h3>RANGILI<small>RANGILI</small></h3><p class="artist-directory-type">GIRL GROUP</p><p class="artist-directory-genre">公開作品 0</p><p>インドと日本、2つの文化が響き合う3人組ガールグループ。</p><div class="artist-directory-link">View introduction ↗</div></div></a></article>'
            '<article class="artist-directory-card artist-coming-soon-card" style="--artist-primary:#e3b982;--artist-secondary:#160f0c;--artist-glow:rgba(227,185,130,.28)"><a href="../artists/asagiri-shinobu/" aria-label="朝霧しのぶの紹介ページへ"><div class="artist-directory-image"><img src="../images/asagiri-shinobu-coming-soon.jpg" alt="朝霧しのぶ 演歌歌手 Coming Soon ビジュアル" width="1254" height="1254" loading="lazy"/><span class="artist-directory-number">05</span></div><div class="artist-directory-copy"><span class="coming-soon-badge">Coming Soon</span><h3>朝霧しのぶ<small>ASAGIRI SHINOBU</small></h3><p class="artist-directory-type">演歌</p><p class="artist-directory-genre">公開作品 0</p><p>人生の喜びや別れ、家族の想いを歌い続ける演歌歌手。</p><div class="artist-directory-link">View introduction ↗</div></div></a></article>'
        )
        source = re.sub(r'<div class="artist-coming-card".*?</div>', cards, source, count=1, flags=re.DOTALL)
    source = update_json_ld_item_list(source, f"{BASE}/artists/#artist-list", [
        {"name": "RANGILI", "url": f"{BASE}/artists/rangili/"},
        {"name": "朝霧しのぶ", "url": f"{BASE}/artists/asagiri-shinobu/"},
    ])
    path.write_text(source, encoding="utf-8")


def update_news_index(path: Path) -> None:
    source = ensure_stylesheet(path.read_text(encoding="utf-8"), "../assets/upcoming.css")
    if './upcoming-artists/' not in source:
        card = '<article class="news-directory-card"><a href="./upcoming-artists/"><span class="news-directory-image"><img src="../images/rangili-coming-soon.jpg" alt="SUZUKA Upcoming Artists News" width="1254" height="1254" loading="lazy"/></span><span class="news-directory-meta"><time datetime="2026-07-22">2026.07.22</time><em>ARTIST NEWS</em></span><h2>SUZUKA Upcoming Artists</h2><p>RANGILIと朝霧しのぶが、SUZUKAでデビュー準備中です。</p><b aria-hidden="true">記事を読む ↗</b></a></article>'
        source = replace_once(source, '<div class="news-list news-feature-list">', '<div class="news-list news-feature-list">' + card, "News directory list")
    source = update_json_ld_item_list(source, f"{BASE}/news/#itemlist", [
        {"name": "SUZUKA Upcoming Artists", "url": f"{BASE}/news/upcoming-artists/"},
    ])
    path.write_text(source, encoding="utf-8")


def update_social(path: Path) -> None:
    source = ensure_stylesheet(path.read_text(encoding="utf-8"), "../assets/upcoming.css")
    if '../artists/rangili/' not in source:
        links = '<a href="../artists/rangili/"><span>RANGILI · Coming Soon</span><b aria-hidden="true">→</b></a><a href="../artists/asagiri-shinobu/"><span>朝霧しのぶ · Coming Soon</span><b aria-hidden="true">→</b></a>'
        marker = '<a href="../artists/enomoto-mia/"><span>榎本魅愛</span><b aria-hidden="true">→</b></a>'
        source = replace_once(source, marker, marker + links, "social artist links")
    if '../news/upcoming-artists/' not in source:
        marker = '<div class="social-hub-heading"><div><p class="social-hub-kicker">03 / Latest News</p><h2 id="news-links">音楽を、言葉から読む。</h2></div><a href="../news/">News一覧 →</a></div>\n      <div class="social-hub-directory">'
        source = replace_once(source, marker, marker + '<a href="../news/upcoming-artists/"><span>SUZUKA Upcoming Artists</span><b aria-hidden="true">→</b></a>', "social News links")
    source = re.sub(r'<a class="social-hub-card" href="../releases/smile-and-say-goodbye/">.*?</a>', '', source, count=1, flags=re.DOTALL)
    path.write_text(source, encoding="utf-8")


def update_releases_index(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    source = remove_article_for_route(source, 'smile-and-say-goodbye/')
    source = renumber_release_cards(source)
    source = remove_json_ld_item(
        source,
        f"{BASE}/releases/#itemlist",
        f"{BASE}/releases/smile-and-say-goodbye/",
    )
    path.write_text(source, encoding="utf-8")


def update_mia_upcoming(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    source = source.replace('01 / New Release</span><h3>SMILE AND SAY GOODBYE', 'UPCOMING · 2026.07.22</span><h3>SMILE AND SAY GOODBYE')
    source = source.replace('<strong>SMILE AND SAY GOODBYE</strong><small>大好きだから、笑ってさようなら。</small>', '<strong>SMILE AND SAY GOODBYE</strong><small>Upcoming · 2026.07.22</small>')
    itemlist_pattern = re.compile(r'(<script id="mia-release-itemlist" type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)
    match = itemlist_pattern.search(source)
    if match:
        payload = json.loads(match.group(2))
        items = [
            item for item in payload.get("itemListElement", [])
            if not str(item.get("url", "")).endswith("/releases/smile-and-say-goodbye/")
        ]
        for position, item in enumerate(items, 1):
            item["position"] = position
        payload["name"] = "榎本魅愛 公開済み楽曲"
        payload["numberOfItems"] = len(items)
        payload["itemListElement"] = items
        source = source[:match.start()] + match.group(1) + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + match.group(3) + source[match.end():]
    path.write_text(source, encoding="utf-8")


def update_smile_upcoming(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    source = source.replace('OFFICIAL RELEASE PAGE', 'UPCOMING RELEASE · 2026.07.22')
    source = source.replace('<div><dt>VIDEO</dt><dd>未発表</dd></div>', '<div><dt>STATUS</dt><dd>公開予定 · 2026.07.22</dd></div>')
    path.write_text(source, encoding="utf-8")


def update_koga_and_boukyaku(root: Path) -> None:
    koga_path = root / "artists/koga-kamishiro/index.html"
    koga = koga_path.read_text(encoding="utf-8")
    koga = koga.replace('<strong>忘却の生き物</strong><small>Official release page</small>', '<strong>忘却の生き物</strong><small>Official MV · 公開中</small>')
    koga_path.write_text(koga, encoding="utf-8")

    release_path = root / "releases/boukyaku-no-ikimono/index.html"
    release = release_path.read_text(encoding="utf-8")
    release = release.replace('<a class="button button-ghost" href="../../social/">OFFICIAL LINKS</a>', f'<a class="button button-primary" href="{BOUKYAKU_YOUTUBE}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../social/">OFFICIAL LINKS</a>') if BOUKYAKU_YOUTUBE not in release else release
    release = release.replace('<div><dt>VIDEO</dt><dd>未発表</dd></div>', '<div><dt>VIDEO</dt><dd>Official MV · 公開中</dd></div>')
    release = release.replace('{"@type":"VideoObject","name":"忘却の生き物｜神代 煌牙 Official Music Video","embedUrl":"https://www.youtube.com/embed/yREvkT9gEk4","contentUrl":"https://www.youtube.com/watch?v=yREvkT9gEk4","thumbnailUrl":"https://bellflower1209.github.io/suzuka-official-music/images/mv-boukyaku-no-ikimono.png","description":"神代 煌牙「忘却の生き物」公式MV。"},', '')
    release_path.write_text(release, encoding="utf-8")


def update_data(root: Path) -> None:
    releases_path = root / "assets/data/release-links.json"
    data = json.loads(releases_path.read_text(encoding="utf-8"))
    for item in data["releases"]:
        if item.get("slug") == "boukyaku-no-ikimono":
            item["youtubeUrl"] = BOUKYAKU_YOUTUBE
            item["youtubeStatus"] = "published"
        if item.get("slug") == "smile-and-say-goodbye":
            item["status"] = "upcoming"
            item["publishedDate"] = "2026-07-22"
    releases_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mia_path = root / "assets/data/enomoto-mia-releases.json"
    mia = json.loads(mia_path.read_text(encoding="utf-8"))
    for item in mia["releases"]:
        if item.get("slug") == "smile-and-say-goodbye":
            item["status"] = "upcoming"
            item["uploadDate"] = "2026-07-22"
    mia_path.write_text(json.dumps(mia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    update_home(root / "index.html")
    update_artists_index(root / "artists/index.html")
    update_news_index(root / "news/index.html")
    update_social(root / "social/index.html")
    update_releases_index(root / "releases/index.html")
    update_mia_upcoming(root / "artists/enomoto-mia/index.html")
    update_smile_upcoming(root / "releases/smile-and-say-goodbye/index.html")
    update_koga_and_boukyaku(root)
    update_data(root)
    print("Updated Coming Soon artists, Upcoming release status, and KOGA official MV links.")


if __name__ == "__main__":
    main()

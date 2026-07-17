#!/usr/bin/env python3
"""Build directory pages and normalize static navigation across the SUZUKA site."""

from __future__ import annotations

import json
import html as html_lib
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bellflower1209.github.io/suzuka-official-music"
CHANNEL = "https://www.youtube.com/@bellflower5215"
CATALOG_PATH = ROOT / "assets/data/enomoto-mia-releases.json"
OTHER_RELEASES = {
    "SHADOW//CODE": {
        "slug": "shadow-code",
        "youtube": "https://www.youtube.com/watch?v=8VCL2IepjeM",
    },
    "My Queen, My Oath": {
        "slug": "my-queen-my-oath",
        "youtube": None,
    },
}


def release_catalog() -> list[dict[str, object]]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [release for release in data["releases"] if release["status"] == "published"]


def page_head(*, title: str, description: str, canonical: str, image: str, asset_prefix: str = "../") -> str:
    return f'''<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/><title>{title}</title><meta name="description" content="{description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{canonical}"/><meta property="og:type" content="website"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{title}"/><meta property="og:description" content="{description}"/><meta property="og:url" content="{canonical}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{title}"/><meta name="twitter:description" content="{description}"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="{asset_prefix}images/suzuka-channel.jpg"/><link rel="stylesheet" href="{asset_prefix}assets/styles.css"/><link rel="stylesheet" href="{asset_prefix}assets/engagement.css"/><link rel="stylesheet" href="{asset_prefix}assets/player.css"/></head>'''


def header(prefix: str = "../") -> str:
    return f'''<header class="site-header inner-site-header"><a class="brand" href="{prefix}" aria-label="SUZUKA トップページへ">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav" aria-label="メインナビゲーション"><a href="{prefix}">Home</a><a href="{prefix}artists/">Artists</a><a href="{prefix}releases/">Releases</a><a href="{prefix}news/">News</a><a href="{prefix}about/">About SUZUKA</a></nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a><details class="mobile-menu"><summary aria-label="メニューを開く">Menu</summary><nav aria-label="モバイルナビゲーション"><a href="{prefix}">Home</a><a href="{prefix}artists/">Artists</a><a href="{prefix}releases/">Releases</a><a href="{prefix}news/">News</a><a href="{prefix}about/">About SUZUKA</a><a href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a></nav></details></header>'''


def footer(prefix: str = "../") -> str:
    return f'''<footer class="site-footer inner-footer"><div class="footer-top"><a class="footer-brand" href="{prefix}">SUZUKA</a><p>Music Label / Creative Music Project</p></div><nav class="site-footer-nav" aria-label="フッターナビゲーション"><a href="{prefix}">Home</a><a href="{prefix}artists/">Artists</a><a href="{prefix}releases/">Releases</a><a href="{prefix}news/">News</a><a href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a></nav><div class="footer-bottom"><span>© 2026 SUZUKA LABEL</span><span>A new story begins with music.</span><a href="#top">Back to top ↑</a></div></footer>'''


def json_script(data: object) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"


def normalize_other_release_card(card: str, *, title: str, detail_prefix: str) -> str:
    release = OTHER_RELEASES[title]
    detail_href = f'{detail_prefix}{release["slug"]}/'
    card = re.sub(
        r'<a class="release-image"[^>]*>',
        f'<a class="release-image" href="{detail_href}" aria-label="{html_lib.escape(title)}の詳細を見る">',
        card,
        count=1,
    )
    detail = f'<a class="release-card-cta release-card-cta-detail" href="{detail_href}">詳細を見る <span aria-hidden="true">↗</span></a>'
    if release["youtube"]:
        actions = (
            f'<div class="release-card-actions">{detail}'
            f'<a class="release-card-cta" href="{release["youtube"]}" target="_blank" rel="noreferrer" '
            f'aria-label="{html_lib.escape(title)} — MVを見る">MVを見る <span aria-hidden="true">↗</span></a></div>'
        )
    else:
        actions = detail
    card = re.sub(
        r'(?:<div class="release-card-actions">.*?</div>|<a class="release-card-cta[^"]*"[^>]*>.*?</a>)(?=</div></article>)',
        actions,
        card,
        count=1,
        flags=re.DOTALL,
    )
    return card


def connect_other_release_pages() -> None:
    home_path = ROOT / "index.html"
    home = home_path.read_text(encoding="utf-8")

    def update_card(match: re.Match[str]) -> str:
        card = match.group(0)
        title_match = re.search(r"<h3>(.*?)</h3>", card, re.DOTALL)
        title = re.sub(r"<.*?>", "", title_match.group(1)).strip() if title_match else ""
        return normalize_other_release_card(card, title=title, detail_prefix="./releases/") if title in OTHER_RELEASES else card

    home = re.sub(r'<article class="release-card[^\"]*">.*?</article>', update_card, home, flags=re.DOTALL)
    home = home.replace('href="./artists/eclypse/#debut-single">曲を聴く', 'href="./releases/shadow-code/">楽曲情報を見る')
    home = home.replace('href="https://www.youtube.com/watch?v=8VCL2IepjeM" target="_blank" rel="noreferrer" aria-label="SHADOW//CODEを見る">SHADOW//CODEを見る', 'href="./releases/shadow-code/" aria-label="SHADOW//CODEの楽曲情報">SHADOW//CODEの楽曲情報')
    home = home.replace('href="./artists/koga-kamishiro/#debut-single" aria-label="My Queen, My Oathの楽曲情報">', 'href="./releases/my-queen-my-oath/" aria-label="My Queen, My Oathの楽曲情報">')
    home_path.write_text(home, encoding="utf-8")

    eclypse_path = ROOT / "artists/eclypse/index.html"
    eclypse = eclypse_path.read_text(encoding="utf-8")
    if '../../releases/shadow-code/' not in eclypse:
        eclypse = eclypse.replace(
            '<a class="button artist-primary-button eclypse-video-button"',
            '<a class="button artist-ghost-button" href="../../releases/shadow-code/">SHADOW//CODE 楽曲情報 ↗</a><a class="button artist-primary-button eclypse-video-button"',
            1,
        )
    eclypse_path.write_text(eclypse, encoding="utf-8")

    koga_path = ROOT / "artists/koga-kamishiro/index.html"
    koga = koga_path.read_text(encoding="utf-8")
    if '../../releases/my-queen-my-oath/' not in koga:
        koga = koga.replace(
            '<div class="koga-lyrics">',
            '<a class="button artist-primary-button" href="../../releases/my-queen-my-oath/">My Queen, My Oath 楽曲情報 ↗</a><div class="koga-lyrics">',
            1,
        )
    koga_path.write_text(koga, encoding="utf-8")


def add_home_feature_news() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    if './news/hyakumankoku-release/' in text:
        return
    cards = (
        '<article><a href="./news/hyakumankoku-release/" aria-label="百万告の公式News記事を見る"><time datetime="2026-07-18">2026.07.18</time><span>RELEASE STORY</span><h3>榎本魅愛「百万告」— 更新され続ける恋心。</h3><b aria-hidden="true">↗</b></a></article>'
        '<article><a href="./news/toriatsukai-chui-release/" aria-label="取り扱いチュー💋いの公式News記事を見る"><time datetime="2026-07-18">2026.07.18</time><span>RELEASE STORY</span><h3>「取り扱いチュー💋い」— 危険でも逃げたくない恋。</h3><b aria-hidden="true">↗</b></a></article>'
        '<article><a href="./news/moshimo-ashita-hajimemashite-ni-natte-mo-release/" aria-label="もしも明日、はじめましてになってもの公式News記事を見る"><time datetime="2026-07-18">2026.07.18</time><span>RELEASE STORY</span><h3>「もしも明日、はじめましてになっても」— 記憶を越える物語。</h3><b aria-hidden="true">↗</b></a></article>'
    )
    text = text.replace('<div class="news-list">', f'<div class="news-list">{cards}', 1)
    path.write_text(text, encoding="utf-8")


def add_release_news_links() -> None:
    links = {
        "hyakumankoku": (
            "hyakumankoku-news-title",
            "#ff72b8",
            "rgba(255,114,184,.18)",
            "「好き」が何度でも更新される理由を、News記事で読む。",
            "hyakumankoku-release",
            "百万告の物語を読む",
            "button button-primary",
            '<section class="toriatsukai-related"',
        ),
        "toriatsukai-chui": (
            "toriatsukai-news-title",
            "#ff4fac",
            "rgba(181,70,255,.2)",
            "警報と安全装置が恋の言葉に変わる、小悪魔な世界観を読む。",
            "toriatsukai-chui-release",
            "楽曲紹介記事を見る",
            "button toriatsukai-primary",
            '<section class="toriatsukai-related"',
        ),
        "moshimo-ashita-hajimemashite-ni-natte-mo": (
            "moshimo-news-title",
            "#f09abb",
            "rgba(128,103,255,.18)",
            "記憶を失っても、もう一度出会う。その物語の余韻をたどる。",
            "moshimo-ashita-hajimemashite-ni-natte-mo-release",
            "この楽曲の世界観を読む",
            "button release-youtube-button",
            '<section class="release-related-section"',
        ),
    }
    for slug, (heading_id, accent, soft, heading, news_slug, label, button_class, insertion) in links.items():
        path = ROOT / f"releases/{slug}/index.html"
        text = path.read_text(encoding="utf-8")
        if 'assets/news-feature.css' not in text:
            text = text.replace(
                '<link rel="stylesheet" href="../../assets/player.css"/>',
                '<link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/player.css"/>',
                1,
            )
        if f'id="{heading_id}"' not in text:
            section = (
                f'<section class="release-news-link" style="--story-accent:{accent};--story-soft:{soft}" aria-labelledby="{heading_id}">'
                f'<p>OFFICIAL NEWS · RELEASE STORY</p><h2 id="{heading_id}">{heading}</h2>'
                f'<a class="{button_class}" href="../../news/{news_slug}/">{label} ↗</a></section>'
            )
            text = text.replace(insertion, section + insertion, 1)
        path.write_text(text, encoding="utf-8")


def build_releases() -> None:
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<article class="release-card[^\"]*">.*?</article>', home, re.DOTALL)
    if not cards:
        raise RuntimeError("No release cards found on the homepage")
    catalog_titles = {str(release["title"]) for release in release_catalog()}
    other_cards = []
    for card in cards:
        match = re.search(r"<h3>(.*?)</h3>", card, re.DOTALL)
        title = re.sub(r"<.*?>", "", match.group(1)).strip() if match else ""
        if title not in catalog_titles:
            card = card.replace('href="./artists/', 'href="../artists/').replace('src="./images/', 'src="../images/')
            if title in OTHER_RELEASES:
                card = normalize_other_release_card(card, title=title, detail_prefix="./")
            other_cards.append(card)

    mia_cards = []
    for release in release_catalog():
        title = html_lib.escape(str(release["title"]))
        artist = "榎本魅愛 × " + " × ".join(release.get("collaborators", [])) if release.get("collaborators") else "榎本魅愛"
        date_label = str(release["uploadDate"]).replace("-", ".")
        duration = int(release.get("duration") or 0)
        duration_label = f"{duration // 60}:{duration % 60:02d}"
        mia_cards.append(
            f'<article class="release-card"><a class="release-image" href="./{release["slug"]}/" aria-label="{title}の詳細を見る">'
            f'<img src="../{release["image"]}" alt="榎本魅愛「{title}」公式ジャケット" width="886" height="886" loading="lazy"/>'
            f'<span class="card-wash wash-pink"></span><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span>'
            f'<span class="duration">{duration_label}</span></a><div class="release-info"><div class="release-row"><span>00</span><span>OFFICIAL · {date_label}</span></div>'
            f'<h3>{title}</h3><p>{html_lib.escape(str(release["shortDescription"]))}</p><p class="release-artist-credit">{html_lib.escape(artist)}</p>'
            f'<div class="release-card-actions"><a class="release-card-cta release-card-cta-detail" href="./{release["slug"]}/">詳細を見る <span aria-hidden="true">↗</span></a>'
            f'<a class="release-card-cta" href="{release["youtubeUrl"]}" target="_blank" rel="noreferrer" aria-label="{title} — MVを見る">MVを見る <span aria-hidden="true">↗</span></a></div></div></article>'
        )
    ordered_cards = mia_cards + other_cards
    numbered_cards = []
    for position, card in enumerate(ordered_cards, 1):
        card = re.sub(r'(<div class="release-row"><span>)\d+(</span>)', rf'\g<1>{position:02d}\2', card, count=1)
        numbered_cards.append(card)
    rendered = "".join(numbered_cards)
    canonical = f"{BASE}/releases/"
    description = "SUZUKA所属アーティストの公式リリース一覧。榎本魅愛、ECLYPSE、神代煌牙の楽曲情報、専用ページ、公式MVを紹介します。"
    items = []
    for position, card in enumerate(numbered_cards, 1):
        title = re.search(r"<h3>(.*?)</h3>", card, re.DOTALL)
        href = re.search(r'<a class="release-image" href="([^"]+)"', card)
        if title and href:
            url = href.group(1)
            if not urllib.parse.urlsplit(url).scheme:
                url = urllib.parse.urljoin(canonical, url)
            items.append({"@type": "ListItem", "position": position, "name": re.sub(r"<.*?>", "", title.group(1)), "url": url})
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": canonical, "url": canonical, "name": "Releases｜SUZUKA", "description": description, "isPartOf": {"@id": f"{BASE}/#website"}},
        {"@type": "ItemList", "@id": f"{canonical}#itemlist", "name": "SUZUKA リリース一覧", "numberOfItems": len(items), "itemListElement": items},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Releases", "item": canonical}]},
    ]}
    html = page_head(title="Releases｜SUZUKA 公式楽曲・MV一覧", description=description, canonical=canonical, image=f"{BASE}/images/eclypse-shadow-code-cover.webp")
    html += f'''<body><main id="top">{json_script(schema)}<a class="skip-link" href="#release-directory">本文へ移動</a>{header()}<section class="directory-hero"><p class="section-kicker">SUZUKA MUSIC CATALOG</p><h1>Releases</h1><p>所属アーティストが届ける音楽作品と、その物語。</p></section><section class="section music-section release-directory" id="release-directory" aria-labelledby="releases-title"><div class="section-heading music-heading"><div><p class="section-kicker">Official releases</p><h2 id="releases-title">Stories in sound.</h2></div><p>カードから楽曲専用ページまたは公式MVへ移動できます。</p></div><div class="release-grid">{rendered}</div></section>{footer()}</main><script defer src="../assets/main.js"></script></body></html>'''
    target = ROOT / "releases/index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


NEWS = [
    ("eclypse-joins-suzuka", "ARTIST", "ECLYPSE、SUZUKA所属アーティストとして始動。", "5人組男性K-POPグループECLYPSEが、SUZUKA所属アーティストとして始動しました。", "../../artists/eclypse/", "ECLYPSEプロフィール"),
    ("shadow-code-announcement", "RELEASE", "デビューシングル「SHADOW//CODE」を発表。", "ECLYPSEのデビューシングル「SHADOW//CODE」を発表しました。公式MVとアーティスト情報を紹介します。", "../../releases/shadow-code/", "SHADOW//CODE 公式楽曲ページ"),
]

FEATURE_NEWS = [
    {
        "slug": "hyakumankoku-release",
        "category": "RELEASE STORY",
        "date": "2026-07-18",
        "title": "榎本魅愛「百万告」公開｜百万回でも伝えたい、更新され続ける恋心",
        "summary": "「好き」は一回では足りない。榎本魅愛のデビュー曲「百万告」が描く、何度でも想いを届ける恋心と公式MV・Shortsの見どころを紹介します。",
        "image": "mv-hyakumankoku.jpg",
        "width": 1280,
        "height": 720,
    },
    {
        "slug": "toriatsukai-chui-release",
        "category": "RELEASE STORY",
        "date": "2026-07-18",
        "title": "榎本魅愛「取り扱いチュー💋い」｜危険でも逃げたくない、小悪魔ラブソング",
        "summary": "可愛さと危険さが同居する榎本魅愛「取り扱いチュー💋い」。警報や安全装置を恋に置き換えた世界観と、公式MV・Shortsの楽しみ方を紹介します。",
        "image": "mv-toriatsukai-chuui.jpg",
        "width": 886,
        "height": 886,
    },
    {
        "slug": "moshimo-ashita-hajimemashite-ni-natte-mo-release",
        "category": "RELEASE STORY",
        "date": "2026-07-18",
        "title": "榎本魅愛「もしも明日、はじめましてになっても」｜記憶を越えて、もう一度恋をする",
        "summary": "記憶を失っても、また同じ人を好きになれるのか。榎本魅愛「もしも明日、はじめましてになっても」の物語、公式Lyric VideoとShortsを紹介します。",
        "image": "mv-moshimo-ashita-hajimemashite-ni-natte-mo.png",
        "width": 1254,
        "height": 1254,
    },
]


def build_news() -> None:
    canonical = f"{BASE}/news/"
    description = "SUZUKAのアーティスト、リリース、公式MVに関する最新情報を掲載する公式News一覧です。"
    entries = FEATURE_NEWS + [
        {"slug": slug, "category": category, "date": "2026", "title": title, "summary": summary, "image": "eclypse-shadow-code-cover.webp", "width": 886, "height": 886}
        for slug, category, title, summary, _, _ in NEWS
    ]
    list_items = [{"@type": "ListItem", "position": i, "name": entry["title"], "url": f"{canonical}{entry['slug']}/"} for i, entry in enumerate(entries, 1)]
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": canonical, "url": canonical, "name": "News｜SUZUKA", "description": description, "isPartOf": {"@id": f"{BASE}/#website"}},
        {"@type": "ItemList", "@id": f"{canonical}#itemlist", "numberOfItems": len(list_items), "itemListElement": list_items},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "News", "item": canonical}]},
    ]}
    rows = "".join(
        f'''<article class="news-directory-card"><a href="./{entry['slug']}/"><span class="news-directory-image"><img src="../images/{entry['image']}" alt="{html_lib.escape(entry['title'])}の記事サムネイル" width="{entry['width']}" height="{entry['height']}" loading="lazy"/></span><span class="news-directory-meta"><time datetime="{entry['date']}">{entry['date'].replace('-', '.')}</time><em>{entry['category']}</em></span><h2>{entry['title']}</h2><p>{entry['summary']}</p><b aria-hidden="true">記事を読む ↗</b></a></article>'''
        for entry in entries
    )
    html = page_head(title="News｜SUZUKA 公式ニュース", description=description, canonical=canonical, image=f"{BASE}/images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png")
    html = html.replace("</head>", '<link rel="stylesheet" href="../assets/news-feature.css"/></head>', 1)
    html += f'''<body><main id="top">{json_script(schema)}<a class="skip-link" href="#news-directory">本文へ移動</a>{header()}<section class="directory-hero"><p class="section-kicker">OFFICIAL UPDATES</p><h1>News</h1><p>デビュー、リリース、アーティスト情報。</p></section><section class="section news-section news-directory" id="news-directory" aria-labelledby="news-list-title"><div class="section-heading"><p class="section-kicker">LATEST STORIES</p><h2 id="news-list-title">Music, words and stories.</h2></div><div class="news-list news-feature-list">{rows}</div></section>{footer()}</main><script defer src="../assets/main.js"></script></body></html>'''
    target = ROOT / "news/index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

    for slug, category, title, summary, related_href, related_label in NEWS:
        article_url = f"{canonical}{slug}/"
        article_schema = {"@context": "https://schema.org", "@graph": [
            {"@type": ["Article", "WebPage"], "@id": article_url, "url": article_url, "headline": title, "name": title, "description": summary, "mainEntityOfPage": {"@id": article_url}, "publisher": {"@id": f"{BASE}/#organization"}, "isPartOf": {"@id": f"{BASE}/#website"}},
            {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "News", "item": canonical}, {"@type": "ListItem", "position": 3, "name": title, "item": article_url}]},
        ]}
        body = page_head(title=f"{title}｜SUZUKA News", description=summary, canonical=article_url, image=f"{BASE}/images/eclypse-shadow-code-cover.webp", asset_prefix="../../")
        body += f'''<body><main id="top">{json_script(article_schema)}<a class="skip-link" href="#news-article">本文へ移動</a>{header("../../")}<article class="news-article" id="news-article"><nav class="release-breadcrumb" aria-label="パンくずリスト"><a href="../../">Home</a> / <a href="../">News</a> / {category}</nav><p class="section-kicker">{category} · 2026</p><h1>{title}</h1><p class="news-article-lead">{summary}</p><div class="news-article-actions"><a class="button button-primary" href="{related_href}">{related_label} <span aria-hidden="true">↗</span></a><a class="button button-ghost" href="../">News一覧へ</a><a class="button button-ghost" href="../../">SUZUKAトップへ</a></div></article>{footer("../../")}</main><script defer src="../../assets/main.js"></script></body></html>'''
        article_target = ROOT / f"news/{slug}/index.html"
        article_target.parent.mkdir(parents=True, exist_ok=True)
        article_target.write_text(body, encoding="utf-8")


def normalize_existing_pages() -> None:
    legacy = ROOT / "releases/toriatsukai-chuui/index.html"
    for path in ROOT.rglob("index.html"):
        if path == legacy or path.parts[-2] in {"news"} or path == ROOT / "releases/index.html":
            continue
        text = path.read_text(encoding="utf-8")
        depth = len(path.relative_to(ROOT).parent.parts)
        prefix = "./" if depth == 0 else "../" * depth
        if 'rel="icon"' not in text and 'rel="shortcut icon"' not in text:
            text = text.replace("</head>", f'<link rel="icon" href="{prefix}images/suzuka-channel.jpg"/></head>', 1)
        if depth == 0:
            text = text.replace('href="#releases"', 'href="./releases/"').replace('href="#news"', 'href="./news/"')
        else:
            text = text.replace(f'href="{prefix}#releases"', f'href="{prefix}releases/"').replace(f'href="{prefix}#news"', f'href="{prefix}news/"')
        text = text.replace('href="./artists/eclypse/" aria-label="ECLYPSEのアーティストページを見る"', 'href="./news/eclypse-joins-suzuka/" aria-label="ECLYPSE始動のNews記事を見る"')
        text = text.replace('href="./artists/eclypse/#debut-single" aria-label="SHADOW//CODEの楽曲情報を見る"', 'href="./news/shadow-code-announcement/" aria-label="SHADOW//CODE発表のNews記事を見る"')
        if "site-footer-nav" not in text:
            nav = f'''<nav class="site-footer-nav" aria-label="フッターナビゲーション"><a href="{prefix}">Home</a><a href="{prefix}artists/">Artists</a><a href="{prefix}releases/">Releases</a><a href="{prefix}news/">News</a><a href="{CHANNEL}" target="_blank" rel="noreferrer">YouTube <span aria-hidden="true">↗</span></a></nav>'''
            text = text.replace("</footer>", nav + "</footer>", 1)
        path.write_text(text, encoding="utf-8")


def add_profile_mv_links() -> None:
    path = ROOT / "artists/enomoto-mia/index.html"
    text = path.read_text(encoding="utf-8")
    links = "".join(
        f'<a href="{release["youtubeUrl"]}" target="_blank" rel="noreferrer"><span>{html_lib.escape(str(release["title"]))}</span><b>公式MV ↗</b></a>'
        for release in release_catalog()
    )
    section = f'''<section class="artist-mv-links" id="official-mvs" aria-labelledby="official-mvs-heading"><div class="artist-section-heading"><p>04 / Official videos</p><h2 id="official-mvs-heading">公式MV</h2></div><div class="artist-mv-link-grid">{links}</div></section>'''
    if 'id="official-mvs"' in text:
        text = re.sub(r'<section class="artist-mv-links" id="official-mvs".*?</section>', section, text, count=1, flags=re.DOTALL)
    else:
        text = text.replace('<section class="artist-youtube-cta">', section + '<section class="artist-youtube-cta">', 1)
    path.write_text(text, encoding="utf-8")


def add_profile_news_links() -> None:
    path = ROOT / "artists/enomoto-mia/index.html"
    text = path.read_text(encoding="utf-8")
    section = '''<section class="artist-news-feature" aria-labelledby="mia-news-heading"><div><p>05 / Recommended stories</p><h2 id="mia-news-heading">榎本魅愛の楽曲を、言葉から読む。</h2></div><div class="artist-news-grid"><a href="../../news/hyakumankoku-release/"><img src="../../images/mv-hyakumankoku.jpg" alt="榎本魅愛「百万告」公式News記事" width="1280" height="720" loading="lazy"/><div><span>百万告</span><strong>百万回でも伝えたい、更新され続ける恋心</strong><small>何度でも「好き」を届けるデビュー曲の世界観。</small><b>News記事を読む ↗</b></div></a><a href="../../news/toriatsukai-chui-release/"><img src="../../images/mv-toriatsukai-chuui.jpg" alt="榎本魅愛「取り扱いチュー💋い」公式News記事" width="886" height="886" loading="lazy"/><div><span>取り扱いチュー💋い</span><strong>危険でも逃げたくない、小悪魔ラブソング</strong><small>警報や安全装置が恋の言葉へ変わる瞬間。</small><b>News記事を読む ↗</b></div></a><a href="../../news/moshimo-ashita-hajimemashite-ni-natte-mo-release/"><img src="../../images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png" alt="榎本魅愛「もしも明日、はじめましてになっても」公式News記事" width="1254" height="1254" loading="lazy"/><div><span>もしも明日、はじめましてになっても</span><strong>記憶を越えて、もう一度恋をする</strong><small>忘れられても出会い直す、切なく優しい物語。</small><b>News記事を読む ↗</b></div></a></div></section>'''
    if 'class="artist-news-feature"' in text:
        text = re.sub(r'<section class="artist-news-feature".*?</section>', section, text, count=1, flags=re.DOTALL)
    else:
        text = text.replace('<section class="artist-youtube-cta">', section + '<section class="artist-youtube-cta">', 1)
    if 'assets/news-feature.css' not in text:
        text = text.replace(
            '<link rel="stylesheet" href="../../assets/player.css"/>',
            '<link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/player.css"/>',
            1,
        )
    path.write_text(text, encoding="utf-8")


def build_profile_track_list() -> None:
    path = ROOT / "artists/enomoto-mia/index.html"
    text = path.read_text(encoding="utf-8")
    rows = []
    for position, release in enumerate(release_catalog(), 1):
        title = html_lib.escape(str(release["title"]))
        collaborators = release.get("collaborators", [])
        label = "榎本魅愛 × " + " × ".join(collaborators) if collaborators else f"Official · {str(release['uploadDate']).replace('-', '.')}"
        rows.append(
            f'<a class="artist-track-row" href="../../{release["pageUrl"]}"><span>{position:02d}</span>'
            f'<img src="../../{release["image"]}" alt="榎本魅愛「{title}」公式ジャケット" width="886" height="886" loading="lazy"/>'
            f'<div><strong>{title}</strong><small>{html_lib.escape(label)}</small></div><b aria-hidden="true">↗</b></a>'
        )
    replacement = f'<div class="artist-track-list">{"".join(rows)}</div>'
    text, count = re.subn(r'<div class="artist-track-list">.*?</div></section>', replacement + '</section>', text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Profile track list was not found")
    path.write_text(text, encoding="utf-8")


def add_profile_release_itemlist() -> None:
    path = ROOT / "artists/enomoto-mia/index.html"
    text = path.read_text(encoding="utf-8")
    items = [
        {
            "@type": "ListItem",
            "position": position,
            "name": release["title"],
            "url": f"{BASE}/{release['pageUrl']}",
        }
        for position, release in enumerate(release_catalog(), 1)
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{BASE}/artists/enomoto-mia/#releases",
        "name": "榎本魅愛 公開済み楽曲",
        "numberOfItems": len(items),
        "itemListElement": items,
    }
    block = f'<script id="mia-release-itemlist" type="application/ld+json">{json.dumps(data, ensure_ascii=False, separators=(",", ":"))}</script>'
    text = re.sub(r'<script id="mia-release-itemlist" type="application/ld\+json">.*?</script>', "", text, flags=re.DOTALL)
    text = text.replace("</head>", block + "</head>", 1)
    path.write_text(text, encoding="utf-8")


def normalize_catalog_titles() -> None:
    replacements = {
        "もしも明日、はじめましてになっても。": "もしも明日、はじめましてになっても",
        "未来のわたしが見てる": "未来の私が見てる",
    }
    for path in [*ROOT.rglob("*.html"), ROOT / "scripts/sync_from_canonical.py"]:
        if path == ROOT / "releases/toriatsukai-chuui/index.html":
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        for release in release_catalog():
            text = text.replace(f"https://youtu.be/{release['youtubeId']}", str(release["youtubeUrl"]))
        text = text.replace(f"{BASE}/#releases", f"{BASE}/releases/")
        if path == ROOT / "index.html":
            text = text.replace("楽曲・MVを見る", "榎本魅愛の全楽曲を見る")
        path.write_text(text, encoding="utf-8")


def add_descriptive_alts() -> None:
    labels = {
        "mv-ai.jpg": "榎本魅愛「AIでもわからない」ジャケット",
        "mv-hanabi.jpg": "榎本魅愛「君は花火」ジャケット",
        "mv-hyakumankoku.jpg": "榎本魅愛「百万告」ジャケット",
        "mv-lastboss.jpg": "榎本魅愛「君とならラスボスまで」ジャケット",
        "mv-mahou.jpg": "榎本魅愛「解けない魔法を、愛と呼ぶ」ジャケット",
        "mv-mermaid-merman.jpg": "榎本魅愛「MERMAID×MERMAN」ジャケット",
        "mv-mia.jpg": "榎本魅愛「M・I・A」ジャケット",
        "mv-mirai-no-watashi-ga-miteru.jpg": "榎本魅愛「未来の私が見てる」ジャケット",
        "mv-muteki.jpg": "榎本魅愛「無敵時間、あと3秒」ジャケット",
        "mv-our-kingdom.jpg": "榎本魅愛・神代煌牙「OUR KINGDOM」ジャケット",
        "mv-sukitte-baretemo-ii.jpg": "榎本魅愛「好きってバレてもいい」ジャケット",
        "mv-toriatsukai-chuui.jpg": "榎本魅愛「取り扱いチュー💋い」ジャケット",
        "eclypse-shadow-code-cover.webp": "ECLYPSE「SHADOW//CODE」ジャケット",
    }
    for path in ROOT.rglob("index.html"):
        text = path.read_text(encoding="utf-8")
        for filename, label in labels.items():
            text = re.sub(rf'(<img\s+src="[^"]*{re.escape(filename)}")\s+alt=""', rf'\1 alt="{label}"', text)
        path.write_text(text, encoding="utf-8")


def complete_related_release_links() -> None:
    additions = {
        "moshimo-ashita-hajimemashite-ni-natte-mo": ("mia", "mv-mia.jpg", "M・I・A"),
        "suki-ga-kyou-mo-fueteiku": ("hyakumankoku", "mv-hyakumankoku.jpg", "百万告"),
    }
    for current, (slug, image, title) in additions.items():
        path = ROOT / f"releases/{current}/index.html"
        text = path.read_text(encoding="utf-8")
        href = f'../{slug}/'
        section = re.search(r'<section class="release-related-section".*?</section>', text, re.DOTALL)
        if not section or f'href="{href}"' in section.group(0):
            continue
        card = f'<a href="{href}"><span><img src="../../images/{image}" alt="榎本魅愛「{title}」ジャケット" width="640" height="360" loading="lazy"/></span><strong>{title}</strong><small>NEXT LISTEN</small><b>VIEW ↗</b></a>'
        updated = section.group(0).replace('</div>\n  </section>', f'{card}</div>\n  </section>', 1)
        text = text[:section.start()] + updated + text[section.end():]
        path.write_text(text, encoding="utf-8")


def sync_catalog_sitemap() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_sitemap.py"), "--write"], check=True)


def main() -> None:
    normalize_catalog_titles()
    normalize_existing_pages()
    connect_other_release_pages()
    add_home_feature_news()
    add_release_news_links()
    build_profile_track_list()
    add_profile_mv_links()
    add_profile_news_links()
    add_profile_release_itemlist()
    add_descriptive_alts()
    complete_related_release_links()
    build_releases()
    build_news()
    sync_catalog_sitemap()
    print("Internal navigation pages and links repaired.")


if __name__ == "__main__":
    main()

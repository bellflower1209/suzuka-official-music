#!/usr/bin/env python3
"""Refresh the local static site from the canonical GitHub Pages deployment."""

from __future__ import annotations

import argparse
import html as html_lib
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path


PUBLIC_CANONICAL_BASE_URL = "https://bellflower1209.github.io/suzuka-official-music"
CONTENT_SOURCE_URL = PUBLIC_CANONICAL_BASE_URL
SOURCE_ROUTES = {
    "/": Path("index.html"),
    "/artists": Path("artists/index.html"),
    "/artists/eclypse": Path("artists/eclypse/index.html"),
    "/artists/koga-kamishiro": Path("artists/koga-kamishiro/index.html"),
    "/artists/enomoto-mia": Path("artists/enomoto-mia/index.html"),
    "/about": Path("about/index.html"),
    "/releases/mirai-no-watashi-ga-miteru": Path("releases/mirai-no-watashi-ga-miteru/index.html"),
    "/releases/our-kingdom": Path("releases/our-kingdom/index.html"),
    "/releases/toriatsukai-chui": Path("releases/toriatsukai-chui/index.html"),
    "/releases/mia": Path("releases/mia/index.html"),
    "/releases/hyakumankoku": Path("releases/hyakumankoku/index.html"),
    "/releases/muteki-jikan-ato-3byou": Path("releases/muteki-jikan-ato-3byou/index.html"),
    "/releases/tokenai-mahou-wo-ai-to-yobu": Path("releases/tokenai-mahou-wo-ai-to-yobu/index.html"),
    "/releases/kimi-to-nara-last-boss-made": Path("releases/kimi-to-nara-last-boss-made/index.html"),
    "/releases/ai-demo-wakaranai": Path("releases/ai-demo-wakaranai/index.html"),
    "/releases/kimi-wa-hanabi": Path("releases/kimi-wa-hanabi/index.html"),
    "/releases/sukitte-baretemo-ii": Path("releases/sukitte-baretemo-ii/index.html"),
    "/releases/mermaid-merman": Path("releases/mermaid-merman/index.html"),
}
SUKI_RELEASE_ROUTE = "/releases/suki-ga-kyou-mo-fueteiku"
MOSHIMO_RELEASE_ROUTE = "/releases/moshimo-ashita-hajimemashite-ni-natte-mo"
LOCAL_ROUTES = {
    SUKI_RELEASE_ROUTE: Path("releases/suki-ga-kyou-mo-fueteiku/index.html"),
    MOSHIMO_RELEASE_ROUTE: Path("releases/moshimo-ashita-hajimemashite-ni-natte-mo/index.html"),
}
LOCAL_REQUIRED_ASSETS = {
    Path("images/mv-suki-ga-kyou-mo-fueteiku.jpg"),
    Path("images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png"),
    Path("images/mv-toriatsukai-chuui.jpg"),
    Path("images/mv-mia.jpg"),
    Path("images/mv-hyakumankoku.jpg"),
    Path("images/mv-muteki.jpg"),
    Path("images/mv-mahou.jpg"),
    Path("images/mv-lastboss.jpg"),
    Path("images/mv-ai.jpg"),
    Path("images/mv-hanabi.jpg"),
    Path("images/mv-sukitte-baretemo-ii.jpg"),
    Path("images/mv-mermaid-merman.jpg"),
}
LOCAL_RELEASE_LASTMOD = {route: "2026-07-16" for route in LOCAL_ROUTES}
SOURCE_RELEASE_LASTMOD = {
    "/releases/toriatsukai-chui": "2026-07-17",
    "/releases/mia": "2026-07-17",
    "/releases/hyakumankoku": "2026-07-17",
    "/releases/muteki-jikan-ato-3byou": "2026-07-17",
    "/releases/tokenai-mahou-wo-ai-to-yobu": "2026-07-17",
    "/releases/kimi-to-nara-last-boss-made": "2026-07-17",
    "/releases/ai-demo-wakaranai": "2026-07-17",
    "/releases/kimi-wa-hanabi": "2026-07-17",
    "/releases/sukitte-baretemo-ii": "2026-07-17",
    "/releases/mermaid-merman": "2026-07-17",
}
ROUTE_LASTMOD = {**SOURCE_RELEASE_LASTMOD, **LOCAL_RELEASE_LASTMOD}
ROUTES = {**SOURCE_ROUTES, **LOCAL_ROUTES}

SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
MODULE_PRELOAD_RE = re.compile(r"<link\b[^>]*rel=[\"']modulepreload[\"'][^>]*?/?>", re.IGNORECASE)
STYLESHEET_RE = re.compile(r"<link\b[^>]*rel=[\"']stylesheet[\"'][^>]*?/?>", re.IGNORECASE)
ASSET_ATTR_RE = re.compile(r'(?P<attr>href|src)="(?P<value>/[^\"]*)"')
IMAGE_RE = re.compile(r'(?:src|href)="(?P<value>/(?:images/[^\"]+|og\.png))"')
CSS_RE = re.compile(r'<link\b[^>]*rel="stylesheet"[^>]*href="(?P<value>/assets/[^\"]+\.css)"', re.IGNORECASE)

CHANNEL_URL = "https://www.youtube.com/@bellflower5215"
SHADOW_CODE_URL = "https://www.youtube.com/watch?v=8VCL2IepjeM"
RELEASE_ENGAGEMENT = {
    "SHADOW//CODE": ("ECLYPSE", "DEBUT SINGLE · 2026", SHADOW_CODE_URL, "WATCH MV", True),
    "My Queen, My Oath": ("神代 煌牙", "DEBUT SINGLE · 2026", "./artists/koga-kamishiro/#debut-single", "楽曲情報を見る", False),
    "無敵時間、あと3秒": ("榎本魅愛", "5TH SINGLE", "./releases/muteki-jikan-ato-3byou/", "楽曲情報を見る", False),
    "M・I・A": ("榎本魅愛", "OFFICIAL MV", "./releases/mia/", "楽曲情報を見る", False),
    "解けない魔法を、愛と呼ぶ": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=CAFQ-d7YHPQ", "WATCH MV", True),
    "君とならラスボスまで": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=YVNs3I-KaHI", "WATCH MV", True),
    "AIでもわからない": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=5jmTo3Jb5sI", "WATCH MV", True),
    "君は花火": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=ohylad3AWYI", "WATCH MV", True),
    "百万告": ("榎本魅愛", "DEBUT SONG", "./releases/hyakumankoku/", "楽曲情報を見る", False),
    "好きってバレてもいい": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=XP8yXMKFHVI", "WATCH MV", True),
    "MERMAID×MERMAN": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=29fpeNtUqfY", "WATCH MV", True),
    "未来の私が見てる": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=fgAW1njpSxM", "WATCH MV", True),
    "OUR KINGDOM": ("榎本魅愛 × 神代煌牙", "COLLABORATION", "https://www.youtube.com/watch?v=y26XVRkpfjw", "WATCH MV", True),
    "取り扱いチュー💋い": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=QXvpLCnyoOw", "WATCH MV", True),
}
RELEASE_DETAIL_ROUTES = {
    "解けない魔法を、愛と呼ぶ": "./releases/tokenai-mahou-wo-ai-to-yobu/",
    "君とならラスボスまで": "./releases/kimi-to-nara-last-boss-made/",
    "AIでもわからない": "./releases/ai-demo-wakaranai/",
    "君は花火": "./releases/kimi-wa-hanabi/",
    "好きってバレてもいい": "./releases/sukitte-baretemo-ii/",
    "MERMAID×MERMAN": "./releases/mermaid-merman/",
}


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "SUZUKA-GitHub-Pages-Sync/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def page_prefix(output_path: Path) -> str:
    return "./" if output_path.parent == Path(".") else "../" * len(output_path.parent.parts)


def relative_asset(value: str, prefix: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    path = parsed.path
    suffix = urllib.parse.urlunsplit(("", "", "", parsed.query, parsed.fragment))

    if path == "/":
        return prefix + suffix
    if path == "" and parsed.fragment:
        return value
    if path == "/" and parsed.fragment:
        return prefix + f"#{parsed.fragment}"

    route_path = path.rstrip("/")
    if route_path in ROUTES and route_path != "/":
        return f"{prefix}{route_path.lstrip('/')}/{suffix}"
    return f"{prefix}{path.lstrip('/')}{suffix}"


def public_page_url(route: str) -> str:
    """Return the self-referencing GitHub Pages URL for a public route."""
    return f"{PUBLIC_CANONICAL_BASE_URL}/" if route == "/" else f"{PUBLIC_CANONICAL_BASE_URL}{route}/"


def normalize_public_seo_urls(source: str, route: str) -> str:
    """Keep every public SEO reference on the canonical GitHub Pages origin."""
    normalized = source

    # GitHub Pages serves directory indexes with a trailing slash. Normalize all
    # known internal page URLs, including JSON-LD @id fragments, to that form.
    for known_route in sorted((item for item in ROUTES if item != "/"), key=len, reverse=True):
        old_url = f"{PUBLIC_CANONICAL_BASE_URL}{known_route}"
        normalized = re.sub(
            rf"{re.escape(old_url)}(?=[#\"])",
            f"{old_url}/",
            normalized,
        )

    expected_url = public_page_url(route)
    canonical = f'<link rel="canonical" href="{expected_url}"/>'
    og_url = f'<meta property="og:url" content="{expected_url}"/>'
    if canonical not in normalized:
        raise RuntimeError(f"The normalized canonical URL is missing for {route}.")
    if og_url not in normalized:
        raise RuntimeError(f"The normalized og:url is missing for {route}.")
    return normalized


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"Expected one {label} insertion point, found {source.count(old)}.")
    return source.replace(old, new, 1)


def enhance_release_cards(source: str) -> str:
    def enhance(match: re.Match[str]) -> str:
        card = match.group(0)
        title_match = re.search(r"<h3>(.*?)</h3>", card, re.DOTALL)
        if not title_match:
            return card
        title = re.sub(r"<!--.*?-->", "", title_match.group(1)).strip()
        details = RELEASE_ENGAGEMENT.get(title)
        if not details:
            raise RuntimeError(f"Release engagement data is missing for {title!r}.")
        artist, release_info, href, action, external = details
        card = re.sub(
            r'(<div class="release-row"><span>\d+</span><span>).*?(</span></div>)',
            rf"\g<1>{html_lib.escape(release_info)}\g<2>",
            card,
            count=1,
            flags=re.DOTALL,
        )
        attributes = ' target="_blank" rel="noreferrer"' if external else ""
        detail_route = RELEASE_DETAIL_ROUTES.get(title)
        if detail_route:
            actions = (
                '<div class="release-card-actions">'
                f'<a class="release-card-cta release-card-cta-detail" href="{detail_route}">詳細を見る <span aria-hidden="true">↗</span></a>'
                f'<a class="release-card-cta" href="{html_lib.escape(href)}"{attributes}'
                f' aria-label="{html_lib.escape(title)} — MVを見る">MVを見る <span aria-hidden="true">↗</span></a>'
                '</div>'
            )
        else:
            actions = (
                f'<a class="release-card-cta" href="{html_lib.escape(href)}"{attributes}'
                f' aria-label="{html_lib.escape(title)} — {html_lib.escape(action)}">{html_lib.escape(action)} <span aria-hidden="true">↗</span></a>'
            )
        engagement = f'<p class="release-artist-credit">{html_lib.escape(artist)}</p>{actions}'
        return card.replace("</div></article>", f"{engagement}</div></article>", 1)

    enhanced, count = re.subn(r'<article class="release-card">.*?</article>', enhance, source, flags=re.DOTALL)
    if count != len(RELEASE_ENGAGEMENT):
        raise RuntimeError(f"Expected {len(RELEASE_ENGAGEMENT)} release cards, found {count}.")
    return enhanced


def add_new_release_to_home(source: str) -> str:
    moshimo_card = (
        '<article class="release-card release-card-new">'
        '<a class="release-image" href="./releases/moshimo-ashita-hajimemashite-ni-natte-mo/" '
        'aria-label="もしも明日、はじめましてになってもの詳細を見る">'
        '<img src="./images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png" '
        'alt="榎本魅愛「もしも明日、はじめましてになっても」公式ジャケット" width="1254" height="1254" loading="lazy"/>'
        '<span class="card-wash wash-pink"></span><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span></a>'
        '<div class="release-info"><div class="release-row"><span>01</span><span>NEW RELEASE · 2026.07.16</span></div>'
        '<h3>もしも明日、はじめましてになっても</h3><p>忘れられても、愛は終わらない。</p>'
        '<p class="release-artist-credit">榎本魅愛</p>'
        '<a class="release-card-cta" href="https://www.youtube.com/watch?v=GN6eoBDRm3w" target="_blank" '
        'rel="noreferrer" aria-label="もしも明日、はじめましてになっても — WATCH MV">'
        'WATCH MV <span aria-hidden="true">↗</span></a></div></article>'
    )
    suki_card = (
        '<article class="release-card release-card-new">'
        '<a class="release-image" href="./releases/suki-ga-kyou-mo-fueteiku/" '
        'aria-label="好きが、今日も増えていく。の詳細を見る">'
        '<img src="./images/mv-suki-ga-kyou-mo-fueteiku.jpg" '
        'alt="榎本魅愛「好きが、今日も増えていく。」公式ジャケット" width="886" height="886" loading="lazy"/>'
        '<span class="card-wash wash-pink"></span><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span></a>'
        '<div class="release-info"><div class="release-row"><span>01</span><span>NEW RELEASE · 2026.07.16</span></div>'
        '<h3>好きが、今日も増えていく。</h3>'
        '<p>昨日より今日、今日より明日へ。「好き」が止まらない王道ラブソング。</p>'
        '<p class="release-artist-credit">榎本魅愛</p>'
        '<a class="release-card-cta" href="https://www.youtube.com/watch?v=XAZy5k9Q4rE" target="_blank" '
        'rel="noreferrer" aria-label="好きが、今日も増えていく。 — WATCH MV">'
        'WATCH MV <span aria-hidden="true">↗</span></a></div></article>'
    )
    source = replace_once(
        source,
        '<div class="release-grid">',
        f'<div class="release-grid">{moshimo_card}{suki_card}',
        "local release cards",
    )

    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f'{match.group(1)}{number:02d}{match.group(2)}'

    source, count = re.subn(
        r'(<div class="release-row"><span>)\d+(</span>)',
        renumber,
        source,
    )
    expected = len(RELEASE_ENGAGEMENT) + len(LOCAL_ROUTES)
    if count != expected:
        raise RuntimeError(f"Expected {expected} numbered release cards after adding local releases, found {count}.")
    return source


def enhance_artist_cards(source: str) -> str:
    actions = {
        "./artists/eclypse/": (
            (SHADOW_CODE_URL, "SHADOW//CODEを見る", True),
            ("./artists/eclypse/", "ECLYPSEプロフィール", False),
        ),
        "./artists/koga-kamishiro/": (
            ("./artists/koga-kamishiro/#debut-single", "My Queen, My Oathの楽曲情報", False),
            ("./artists/koga-kamishiro/", "神代煌牙プロフィール", False),
        ),
        "./artists/enomoto-mia/": (
            ("./artists/enomoto-mia/#artist-music", "楽曲・MVを見る", False),
            ("./artists/enomoto-mia/", "榎本魅愛プロフィール", False),
        ),
    }

    def enhance(match: re.Match[str]) -> str:
        card = match.group(0)
        href_match = re.search(r'<a href="([^"]+)"', card)
        if not href_match or href_match.group(1) not in actions:
            return card
        links = []
        for href, label, external in actions[href_match.group(1)]:
            attributes = ' target="_blank" rel="noreferrer"' if external else ""
            links.append(
                f'<a href="{href}"{attributes} aria-label="{html_lib.escape(label)}">{html_lib.escape(label)} <span aria-hidden="true">↗</span></a>'
            )
        return card.replace("</article>", f'<div class="home-artist-actions">{"".join(links)}</div></article>', 1)

    enhanced, count = re.subn(r'<article class="home-artist-card[^>]*>.*?</article>', enhance, source, flags=re.DOTALL)
    if count != 3:
        raise RuntimeError(f"Expected 3 home artist cards, found {count}.")
    return enhanced


def enhance_home(source: str) -> str:
    hero_actions = (
        '<div class="hero-release-actions reveal-up delay-4" aria-label="最新リリース SHADOW//CODEのメニュー">'
        '<p><span>LATEST RELEASE</span><strong>ECLYPSE — SHADOW//CODE</strong></p>'
        f'<a class="button button-primary" href="{SHADOW_CODE_URL}" target="_blank" rel="noreferrer">MVを見る <span aria-hidden="true">↗</span></a>'
        '<a class="button button-ghost" href="./artists/eclypse/#debut-single">曲を聴く <span aria-hidden="true">▶</span></a>'
        f'<a class="button button-youtube" href="{CHANNEL_URL}" target="_blank" rel="noreferrer">YouTubeでSUZUKAをフォロー <span aria-hidden="true">↗</span></a>'
        '</div>'
    )
    source, count = re.subn(
        r'<div class="hero-actions reveal-up delay-4">.*?</div>',
        hero_actions,
        source,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("The hero action group was not found.")

    source = enhance_artist_cards(source)
    source = enhance_release_cards(source)
    source = add_new_release_to_home(source)
    source = replace_once(
        source,
        '<article><time dateTime="2026">2026</time><span>ARTIST</span><h3>ECLYPSE、SUZUKA所属アーティストとして始動。</h3></article>',
        '<article><a href="./news/eclypse-joins-suzuka/" aria-label="ECLYPSE始動のNews記事を見る"><time dateTime="2026">2026</time><span>ARTIST</span><h3>ECLYPSE、SUZUKA所属アーティストとして始動。</h3><b aria-hidden="true">↗</b></a></article>',
        "ECLYPSE news link",
    )
    source = replace_once(
        source,
        '<article><time dateTime="2026">2026</time><span>RELEASE</span><h3>デビューシングル「SHADOW//CODE」を発表。</h3></article>',
        '<article><a href="./news/shadow-code-announcement/" aria-label="SHADOW//CODE発表のNews記事を見る"><time dateTime="2026">2026</time><span>RELEASE</span><h3>デビューシングル「SHADOW//CODE」を発表。</h3><b aria-hidden="true">↗</b></a></article>',
        "SHADOW//CODE news link",
    )
    youtube_section = (
        '<section class="youtube-growth-section" aria-labelledby="youtube-growth-title">'
        '<div><p class="section-kicker">07 / Official YouTube</p><h2 id="youtube-growth-title">新曲・MVを最速で。</h2>'
        '<span>SUZUKAの新しい物語をYouTubeで。</span></div>'
        f'<a class="button button-youtube" href="{CHANNEL_URL}" target="_blank" rel="noreferrer">SUZUKAをYouTubeでフォロー <span aria-hidden="true">↗</span></a>'
        '</section>'
    )
    return replace_once(source, '<footer class="site-footer">', f'{youtube_section}<footer class="site-footer">', "YouTube CTA")


def enhance_artist_page(source: str) -> str:
    navigation = (
        '<nav class="artist-next-actions" aria-label="SUZUKAサイト内のおすすめ">'
        '<div><p>Keep exploring</p><h2>次の物語へ。</h2></div>'
        '<a href="../../artists/">他のアーティストを見る <span aria-hidden="true">↗</span></a>'
        '<a href="../../releases/">Releasesを見る <span aria-hidden="true">↗</span></a>'
        f'<a href="{SHADOW_CODE_URL}" target="_blank" rel="noreferrer">最新MVを見る <span aria-hidden="true">↗</span></a>'
        '</nav>'
    )
    return replace_once(source, '<footer class="artist-profile-footer">', f'{navigation}<footer class="artist-profile-footer">', "artist navigation")


def add_new_release_to_enomoto(source: str) -> str:
    moshimo_featured_card = (
        '<article class="artist-featured-card artist-featured-card-new"><a href="https://www.youtube.com/watch?v=GN6eoBDRm3w" '
        'target="_blank" rel="noreferrer" aria-label="もしも明日、はじめましてになってものMusic Videoを観る">'
        '<div class="artist-featured-image"><img src="../../images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png" '
        'alt="榎本魅愛「もしも明日、はじめましてになっても」公式ジャケット" width="1254" height="1254" loading="lazy"/>'
        '<span class="artist-featured-play"><span class="play-mark" aria-hidden="true"></span></span></div>'
        '<div class="artist-featured-copy"><span>01 / New Release</span><h3>もしも明日、はじめましてになっても</h3>'
        '<p>忘れられても、愛は終わらない。</p></div></a></article>'
    )
    suki_featured_card = (
        '<article class="artist-featured-card artist-featured-card-new"><a href="https://www.youtube.com/watch?v=XAZy5k9Q4rE" '
        'target="_blank" rel="noreferrer" aria-label="好きが、今日も増えていく。のMusic Videoを観る">'
        '<div class="artist-featured-image"><img src="../../images/mv-suki-ga-kyou-mo-fueteiku.jpg" '
        'alt="榎本魅愛「好きが、今日も増えていく。」公式ジャケット" width="886" height="886" loading="lazy"/>'
        '<span class="artist-featured-play"><span class="play-mark" aria-hidden="true"></span></span></div>'
        '<div class="artist-featured-copy"><span>01 / New Release</span><h3>好きが、今日も増えていく。</h3>'
        '<p>昨日より今日、今日より明日へ。「好き」が止まらない王道ラブソング。</p></div></a></article>'
    )
    source = replace_once(
        source,
        '<div class="artist-featured-grid">',
        f'<div class="artist-featured-grid artist-featured-grid-expanded">{moshimo_featured_card}{suki_featured_card}',
        "local featured releases",
    )

    featured_number = 0

    def renumber_featured(match: re.Match[str]) -> str:
        nonlocal featured_number
        featured_number += 1
        return f'{match.group(1)}{featured_number:02d}{match.group(2)}'

    source, featured_count = re.subn(
        r'(<div class="artist-featured-copy"><span>)\d+(.*?</span>)',
        renumber_featured,
        source,
        flags=re.DOTALL,
    )
    if featured_count != 5:
        raise RuntimeError(f"Expected 5 featured ENOMOTO MIA releases, found {featured_count}.")

    moshimo_row = (
        '<a class="artist-track-row artist-track-row-new" href="../../releases/moshimo-ashita-hajimemashite-ni-natte-mo/">'
        '<span>01</span><img src="../../images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png" '
        'alt="榎本魅愛「もしも明日、はじめましてになっても」公式ジャケット" width="1254" height="1254" loading="lazy"/>'
        '<div><strong>もしも明日、はじめましてになっても</strong><small>New Release · 2026.07.16</small></div>'
        '<b aria-hidden="true">↗</b></a>'
    )
    suki_row = (
        '<a class="artist-track-row artist-track-row-new" href="../../releases/suki-ga-kyou-mo-fueteiku/">'
        '<span>01</span><img src="../../images/mv-suki-ga-kyou-mo-fueteiku.jpg" '
        'alt="榎本魅愛「好きが、今日も増えていく。」公式ジャケット" width="886" height="886" loading="lazy"/>'
        '<div><strong>好きが、今日も増えていく。</strong><small>New Release · 2026.07.16</small></div>'
        '<b aria-hidden="true">↗</b></a>'
    )
    source = replace_once(
        source,
        '<div class="artist-track-list">',
        f'<div class="artist-track-list">{moshimo_row}{suki_row}',
        "local artist tracks",
    )

    section_match = re.search(r'<div class="artist-track-list">.*?</div></section>', source, flags=re.DOTALL)
    if not section_match:
        raise RuntimeError("The ENOMOTO MIA track list was not found.")
    number = 0

    def renumber(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f'{match.group(1)}{number:02d}{match.group(2)}'

    section, count = re.subn(
        r'(<a class="artist-track-row[^"]*"[^>]*><span>)\d+(</span>)',
        renumber,
        section_match.group(0),
    )
    if count != 14:
        raise RuntimeError(f"Expected 14 ENOMOTO MIA tracks after adding the local releases, found {count}.")
    return source[: section_match.start()] + section + source[section_match.end() :]


def enhance_html(source: str, output_path: Path) -> str:
    if output_path == Path("index.html"):
        return enhance_home(source)
    if output_path == Path("artists/enomoto-mia/index.html"):
        return enhance_artist_page(add_new_release_to_enomoto(source))
    if output_path in {
        Path("artists/eclypse/index.html"),
        Path("artists/koga-kamishiro/index.html"),
    }:
        return enhance_artist_page(source)
    return source


def sanitize_html(html: str, output_path: Path, route: str) -> str:
    prefix = page_prefix(output_path)
    html = SCRIPT_RE.sub(
        lambda match: match.group(0) if 'type="application/ld+json"' in match.group(0) else "",
        html,
    )
    html = MODULE_PRELOAD_RE.sub("", html)
    html = STYLESHEET_RE.sub("", html)
    html = re.sub(r"\sdata-rsc-[a-z-]+=(?:\"[^\"]*\"|'[^']*')", "", html, flags=re.IGNORECASE)
    html = re.sub(
        rf'(<link\b[^>]*rel="(?:shortcut icon|icon)"[^>]*href="){re.escape(CONTENT_SOURCE_URL)}(/images/[^\"]+)(")',
        lambda match: f"{match.group(1)}{relative_asset(match.group(2), prefix)}{match.group(3)}",
        html,
        flags=re.IGNORECASE,
    )

    def rewrite(match: re.Match[str]) -> str:
        value = match.group("value")
        return f'{match.group("attr")}="{relative_asset(value, prefix)}"'

    html = ASSET_ATTR_RE.sub(rewrite, html)
    html = normalize_public_seo_urls(html, route)
    detailed_mia_releases = {
        Path("releases/toriatsukai-chui/index.html"),
        Path("releases/mia/index.html"),
        Path("releases/hyakumankoku/index.html"),
        Path("releases/muteki-jikan-ato-3byou/index.html"),
        Path("releases/tokenai-mahou-wo-ai-to-yobu/index.html"),
        Path("releases/kimi-to-nara-last-boss-made/index.html"),
        Path("releases/ai-demo-wakaranai/index.html"),
        Path("releases/kimi-wa-hanabi/index.html"),
        Path("releases/sukitte-baretemo-ii/index.html"),
        Path("releases/mermaid-merman/index.html"),
    }
    page_styles = (
        f'<link rel="stylesheet" href="{prefix}assets/toriatsukai-chui.css"/>'
        if output_path in detailed_mia_releases
        else ""
    )
    styles = (
        f'<link rel="stylesheet" href="{prefix}assets/styles.css"/>'
        f'<link rel="stylesheet" href="{prefix}assets/engagement.css"/>'
        f"{page_styles}"
        f'<link rel="stylesheet" href="{prefix}assets/player.css"/>'
    )
    html = html.replace("</head>", f"{styles}</head>", 1)
    html = html.replace("</body>", f'<script defer src="{prefix}assets/main.js"></script></body>', 1)
    return enhance_html(html, output_path).strip() + "\n"


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    output = args.output.resolve()

    for asset_path in LOCAL_REQUIRED_ASSETS:
        if not (output / asset_path).exists():
            raise RuntimeError(f"A required local-only asset is missing: {asset_path}")

    pages = {route: fetch_text(f"{CONTENT_SOURCE_URL}{route}") for route in SOURCE_ROUTES}
    root_html = pages["/"]
    css_match = CSS_RE.search(root_html)
    if not css_match:
        raise RuntimeError("The canonical stylesheet URL was not found.")

    write_bytes(output / "assets/styles.css", fetch_bytes(f"{CONTENT_SOURCE_URL}{css_match.group('value')}"))

    public_assets = {match.group("value") for html in pages.values() for match in IMAGE_RE.finditer(html)}
    public_assets.add("/images/suzuka-channel.jpg")
    for asset_path in sorted(public_assets):
        write_bytes(output / asset_path.lstrip("/"), fetch_bytes(f"{CONTENT_SOURCE_URL}{asset_path}"))

    for route, output_path in SOURCE_ROUTES.items():
        write_bytes(output / output_path, sanitize_html(pages[route], output_path, route).encode("utf-8"))

    for route, output_path in LOCAL_ROUTES.items():
        local_page = output / output_path
        if not local_page.exists():
            raise RuntimeError(f"The local-only page for {route} is missing: {output_path}")
        normalize_public_seo_urls(local_page.read_text(encoding="utf-8"), route)

    robots = (
        "User-agent: *\n"
        "Allow: /suzuka-official-music/\n\n"
        f"Sitemap: {PUBLIC_CANONICAL_BASE_URL}/sitemap.xml\n"
    )
    write_bytes(output / "robots.txt", robots.encode("utf-8"))
    sitemap_urls = "".join(
        (
            f"  <url><loc>{public_page_url(route)}</loc><lastmod>{ROUTE_LASTMOD[route]}</lastmod></url>\n"
            if route in ROUTE_LASTMOD
            else f"  <url><loc>{public_page_url(route)}</loc></url>\n"
        )
        for route in ROUTES
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap_urls}</urlset>\n"
    )
    write_bytes(output / "sitemap.xml", sitemap.encode("utf-8"))

    source_player = output / "assets/player.css"
    source_engagement = output / "assets/engagement.css"
    source_toriatsukai = output / "assets/toriatsukai-chui.css"
    source_script = output / "assets/main.js"
    if not source_player.exists() or not source_engagement.exists() or not source_toriatsukai.exists() or not source_script.exists():
        raise RuntimeError("Existing engagement and fixed-player assets are required before syncing.")

    shutil.copyfile(output / "images/suzuka-channel.jpg", output / "suzuka-channel.jpg")
    print(
        f"Synced {len(SOURCE_ROUTES)} source pages and preserved {len(LOCAL_ROUTES)} local pages; "
        f"downloaded {len(public_assets)} public assets from the canonical deployment; "
        f"canonicalized {len(ROUTES)} routes to {PUBLIC_CANONICAL_BASE_URL}"
    )


if __name__ == "__main__":
    main()

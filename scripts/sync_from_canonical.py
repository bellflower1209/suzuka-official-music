#!/usr/bin/env python3
"""Export the public SUZUKA site into GitHub Pages-compatible static files."""

from __future__ import annotations

import argparse
import html as html_lib
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path


CANONICAL_ORIGIN = "https://suzuka-official-music.ria20210815.chatgpt.site"
PAGES_ORIGIN = "https://bellflower1209.github.io/suzuka-official-music"
ROUTES = {
    "/": Path("index.html"),
    "/artists": Path("artists/index.html"),
    "/artists/eclypse": Path("artists/eclypse/index.html"),
    "/artists/koga-kamishiro": Path("artists/koga-kamishiro/index.html"),
    "/artists/enomoto-mia": Path("artists/enomoto-mia/index.html"),
    "/about": Path("about/index.html"),
    "/releases/mirai-no-watashi-ga-miteru": Path("releases/mirai-no-watashi-ga-miteru/index.html"),
    "/releases/our-kingdom": Path("releases/our-kingdom/index.html"),
    "/releases/toriatsukai-chuui": Path("releases/toriatsukai-chuui/index.html"),
}

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
    "無敵時間、あと3秒": ("榎本魅愛", "5TH SINGLE", "https://www.youtube.com/watch?v=DPnFtRFnH5c", "WATCH MV", True),
    "M・I・A": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=WzcXyuAI_FM", "WATCH MV", True),
    "解けない魔法を、愛と呼ぶ": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=CAFQ-d7YHPQ", "WATCH MV", True),
    "君とならラスボスまで": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=YVNs3I-KaHI", "WATCH MV", True),
    "AIでもわからない": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=5jmTo3Jb5sI", "WATCH MV", True),
    "君は花火": ("榎本魅愛", "OFFICIAL MV", "https://www.youtube.com/watch?v=ohylad3AWYI", "WATCH MV", True),
    "百万告": ("榎本魅愛", "DEBUT SONG", "https://www.youtube.com/watch?v=QteunhFn9Dk", "WATCH MV", True),
    "好きってバレてもいい": ("榎本魅愛", "OFFICIAL MUSIC", "https://youtu.be/XP8yXMKFHVI", "WATCH MV", True),
    "MERMAID×MERMAN": ("榎本魅愛", "OFFICIAL MUSIC", "https://youtu.be/29fpeNtUqfY", "WATCH MV", True),
    "未来のわたしが見てる": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=fgAW1njpSxM", "WATCH MV", True),
    "OUR KINGDOM": ("榎本魅愛 × 神代煌牙", "COLLABORATION", "https://www.youtube.com/watch?v=y26XVRkpfjw", "WATCH MV", True),
    "取り扱いチュー💋い": ("榎本魅愛", "OFFICIAL MUSIC", "https://www.youtube.com/watch?v=QXvpLCnyoOw", "WATCH MV", True),
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
        engagement = (
            f'<p class="release-artist-credit">{html_lib.escape(artist)}</p>'
            f'<a class="release-card-cta" href="{html_lib.escape(href)}"{attributes}'
            f' aria-label="{html_lib.escape(title)} — {html_lib.escape(action)}">{html_lib.escape(action)} <span aria-hidden="true">↗</span></a>'
        )
        return card.replace("</div></article>", f"{engagement}</div></article>", 1)

    enhanced, count = re.subn(r'<article class="release-card">.*?</article>', enhance, source, flags=re.DOTALL)
    if count != len(RELEASE_ENGAGEMENT):
        raise RuntimeError(f"Expected {len(RELEASE_ENGAGEMENT)} release cards, found {count}.")
    return enhanced


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
    source = replace_once(
        source,
        '<article><time dateTime="2026">2026</time><span>ARTIST</span><h3>ECLYPSE、SUZUKA所属アーティストとして始動。</h3></article>',
        '<article><a href="./artists/eclypse/" aria-label="ECLYPSEのアーティストページを見る"><time dateTime="2026">2026</time><span>ARTIST</span><h3>ECLYPSE、SUZUKA所属アーティストとして始動。</h3><b aria-hidden="true">↗</b></a></article>',
        "ECLYPSE news link",
    )
    source = replace_once(
        source,
        '<article><time dateTime="2026">2026</time><span>RELEASE</span><h3>デビューシングル「SHADOW//CODE」を発表。</h3></article>',
        '<article><a href="./artists/eclypse/#debut-single" aria-label="SHADOW//CODEの楽曲情報を見る"><time dateTime="2026">2026</time><span>RELEASE</span><h3>デビューシングル「SHADOW//CODE」を発表。</h3><b aria-hidden="true">↗</b></a></article>',
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
        '<a href="../../#releases">Releasesを見る <span aria-hidden="true">↗</span></a>'
        f'<a href="{SHADOW_CODE_URL}" target="_blank" rel="noreferrer">最新MVを見る <span aria-hidden="true">↗</span></a>'
        '</nav>'
    )
    return replace_once(source, '<footer class="artist-profile-footer">', f'{navigation}<footer class="artist-profile-footer">', "artist navigation")


def enhance_html(source: str, output_path: Path) -> str:
    if output_path == Path("index.html"):
        return enhance_home(source)
    if output_path in {
        Path("artists/eclypse/index.html"),
        Path("artists/koga-kamishiro/index.html"),
        Path("artists/enomoto-mia/index.html"),
    }:
        return enhance_artist_page(source)
    return source


def sanitize_html(html: str, output_path: Path) -> str:
    prefix = page_prefix(output_path)
    html = SCRIPT_RE.sub(
        lambda match: match.group(0) if 'type="application/ld+json"' in match.group(0) else "",
        html,
    )
    html = MODULE_PRELOAD_RE.sub("", html)
    html = STYLESHEET_RE.sub("", html)
    html = re.sub(r"\sdata-rsc-[a-z-]+=(?:\"[^\"]*\"|'[^']*')", "", html, flags=re.IGNORECASE)
    html = re.sub(
        rf'(<link\b[^>]*rel="(?:shortcut icon|icon)"[^>]*href="){re.escape(CANONICAL_ORIGIN)}(/images/[^\"]+)(")',
        lambda match: f"{match.group(1)}{relative_asset(match.group(2), prefix)}{match.group(3)}",
        html,
        flags=re.IGNORECASE,
    )

    def rewrite(match: re.Match[str]) -> str:
        value = match.group("value")
        return f'{match.group("attr")}="{relative_asset(value, prefix)}"'

    html = ASSET_ATTR_RE.sub(rewrite, html)
    styles = (
        f'<link rel="stylesheet" href="{prefix}assets/styles.css"/>'
        f'<link rel="stylesheet" href="{prefix}assets/engagement.css"/>'
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

    pages = {route: fetch_text(f"{CANONICAL_ORIGIN}{route}") for route in ROUTES}
    root_html = pages["/"]
    css_match = CSS_RE.search(root_html)
    if not css_match:
        raise RuntimeError("The canonical stylesheet URL was not found.")

    write_bytes(output / "assets/styles.css", fetch_bytes(f"{CANONICAL_ORIGIN}{css_match.group('value')}"))

    public_assets = {match.group("value") for html in pages.values() for match in IMAGE_RE.finditer(html)}
    public_assets.add("/images/suzuka-channel.jpg")
    for asset_path in sorted(public_assets):
        write_bytes(output / asset_path.lstrip("/"), fetch_bytes(f"{CANONICAL_ORIGIN}{asset_path}"))

    for route, output_path in ROUTES.items():
        write_bytes(output / output_path, sanitize_html(pages[route], output_path).encode("utf-8"))

    robots = f"User-agent: *\nAllow: /\n\nSitemap: {PAGES_ORIGIN}/sitemap.xml\n"
    write_bytes(output / "robots.txt", robots.encode("utf-8"))
    sitemap_urls = "".join(
        f"  <url><loc>{PAGES_ORIGIN}{route if route != '/' else '/'}</loc></url>\n"
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
    source_script = output / "assets/main.js"
    if not source_player.exists() or not source_engagement.exists() or not source_script.exists():
        raise RuntimeError("Existing engagement and fixed-player assets are required before syncing.")

    shutil.copyfile(output / "images/suzuka-channel.jpg", output / "suzuka-channel.jpg")
    print(f"Synced {len(ROUTES)} pages and {len(public_assets)} public assets from {CANONICAL_ORIGIN}")


if __name__ == "__main__":
    main()

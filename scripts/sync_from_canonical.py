#!/usr/bin/env python3
"""Export the public SUZUKA site into GitHub Pages-compatible static files."""

from __future__ import annotations

import argparse
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
        f'<link rel="stylesheet" href="{prefix}assets/player.css"/>'
    )
    html = html.replace("</head>", f"{styles}</head>", 1)
    html = html.replace("</body>", f'<script defer src="{prefix}assets/main.js"></script></body>', 1)
    return html.strip() + "\n"


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
    source_script = output / "assets/main.js"
    if not source_player.exists() or not source_script.exists():
        raise RuntimeError("Existing fixed-player assets are required before syncing.")

    shutil.copyfile(output / "images/suzuka-channel.jpg", output / "suzuka-channel.jpg")
    print(f"Synced {len(ROUTES)} pages and {len(public_assets)} public assets from {CANONICAL_ORIGIN}")


if __name__ == "__main__":
    main()

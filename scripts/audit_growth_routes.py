#!/usr/bin/env python3
"""Audit Version 1.1 Discovery & Growth conversion routes."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CHANNEL = "https://www.youtube.com/@suzuka1209"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    catalog = json.loads(text(ROOT / "assets/data/releases-catalog.json"))
    cms = json.loads(text(ROOT / "assets/data/creator-cms.json"))
    releases = [item for item in catalog["releases"] if item.get("status") == "published"]
    verified = {
        item["slug"] for item in releases
        if item.get("lyricsAvailable") is True
        and item.get("lyricsVerified") is True
        and (ROOT / f'lyrics/{item["slug"]}/index.html').is_file()
    }
    artists = {
        item["slug"] for item in cms["artists"]
        if item.get("status") == "published" and (ROOT / f'artists/{item["slug"]}/index.html').is_file()
    }
    news = {
        item["releaseSlug"]: item["slug"] for item in cms["news"]
        if item.get("status") == "published" and item.get("releaseSlug")
        and (ROOT / "news" / item["slug"] / "index.html").is_file()
    }
    errors: list[str] = []
    counts = {
        "releaseGallery": 0, "galleryArtist": 0, "galleryLyrics": 0,
        "newsLyrics": 0, "newsGallery": 0, "galleryNews": 0,
    }

    for item in releases:
        slug = item["slug"]
        release_path = ROOT / item["releaseUrl"] / "index.html"
        gallery_path = ROOT / "gallery" / slug / "index.html"
        if not release_path.is_file():
            errors.append(f"{slug}: published Release missing")
            continue
        release_html = text(release_path)
        gallery_expected = item.get("galleryPublished", True)
        gallery_html = text(gallery_path) if gallery_path.is_file() else ""
        if gallery_expected:
            if not gallery_html:
                errors.append(f"{slug}: confirmed Gallery missing")
                continue
            if f'../../gallery/{slug}/' not in release_html:
                errors.append(f"{slug}: Release -> Gallery missing")
            else:
                counts["releaseGallery"] += 1
            if f'../../{item["releaseUrl"]}' not in gallery_html:
                errors.append(f"{slug}: Gallery -> Release missing")
            if item["artistSlug"] in artists:
                if f'../../artists/{item["artistSlug"]}/' not in gallery_html:
                    errors.append(f"{slug}: Gallery -> Artist missing")
                else:
                    counts["galleryArtist"] += 1
        else:
            if gallery_html:
                errors.append(f"{slug}: unconfirmed Gallery must not be published")
            if f'../../gallery/{slug}/' in release_html:
                errors.append(f"{slug}: unconfirmed Gallery CTA must not be displayed")
        lyrics_link = f'../../lyrics/{slug}/'
        if gallery_expected and (lyrics_link in gallery_html) != (slug in verified):
            errors.append(f"{slug}: Gallery Lyrics condition mismatch")
        if gallery_expected and slug in verified:
            counts["galleryLyrics"] += 1
        if slug in news:
            news_html = text(ROOT / "news" / news[slug] / "index.html")
            gallery_link = f'../../gallery/{slug}/'
            if (gallery_link in news_html) != gallery_expected:
                errors.append(f"{slug}: News Gallery condition mismatch")
            if gallery_expected:
                counts["newsGallery"] += 1
                news_link = f'../../news/{news[slug]}/'
                if news_link not in gallery_html:
                    errors.append(f"{slug}: Gallery -> News missing")
                else:
                    counts["galleryNews"] += 1
            if (lyrics_link in news_html) != (slug in verified):
                errors.append(f"{slug}: News Lyrics condition mismatch")
            if slug in verified:
                counts["newsLyrics"] += 1

    page_groups = {
        "lyrics_subscribe": [ROOT / "lyrics/index.html", *sorted(ROOT.glob("lyrics/*/index.html"))],
        "release_subscribe": [ROOT / item["releaseUrl"] / "index.html" for item in releases],
        "playlist_subscribe": [ROOT / "playlists/index.html", *sorted(ROOT.glob("playlists/*/index.html"))],
    }
    subscribe_counts = {}
    for source, pages in page_groups.items():
        public_pages = [path for path in dict.fromkeys(pages) if path.is_file() and 'content="noindex' not in text(path)]
        subscribe_counts[source] = len(public_pages)
        for path in public_pages:
            value = text(path)
            if value.count(f'data-source-section="{source}"') != 1 or value.count("data-subscribe-cta") < 1:
                errors.append(f"{path.relative_to(ROOT)}: {source} CTA missing or duplicated")
            if CHANNEL not in value:
                errors.append(f"{path.relative_to(ROOT)}: verified YouTube channel missing")

    home = text(ROOT / "index.html")
    if 'data-source-section="home_subscribe"' not in home or "data-subscribe-cta" not in home:
        errors.append("index.html: home_subscribe missing")
    for path in sorted(ROOT.glob("**/index.html")):
        value = text(path)
        if 'class="header-channel"' in value and 'data-source-section="header_channel"' not in value:
            errors.append(f"{path.relative_to(ROOT)}: header_channel missing")
        for tag in re.findall(r'<a\b[^>]*href=["\']https?://[^"\']+["\'][^>]*>', value, re.I):
            href = re.search(r'href=["\']([^"\']+)', tag, re.I).group(1)
            if urlparse(href).hostname == "www.suzukaofficial.com":
                continue
            if not re.search(r'target=["\']_blank["\']', tag, re.I):
                errors.append(f"{path.relative_to(ROOT)}: external target missing: {href}")
            rel = re.search(r'rel=["\']([^"\']+)', tag, re.I)
            if not rel or not {"noopener", "noreferrer"}.issubset(set(rel.group(1).split())):
                errors.append(f"{path.relative_to(ROOT)}: external rel missing: {href}")

    analytics = text(ROOT / "assets/analytics.js")
    for required in (
        'send("youtube_subscribe_click", details)',
        'else if (youtubeChannel) send("youtube_click", details)',
        'else if (youtubeVideo) send("official_mv_click", details)',
    ):
        if required not in analytics:
            errors.append(f"assets/analytics.js missing: {required}")

    if errors:
        print("Growth route audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", **counts, **subscribe_counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

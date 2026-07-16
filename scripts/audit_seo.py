#!/usr/bin/env python3
"""Audit SUZUKA static pages for crawlability, metadata, and JSON-LD consistency."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE_URL = "https://bellflower1209.github.io/suzuka-official-music"
PUBLIC_PATH_PREFIX = "/suzuka-official-music/"
PUBLIC_HOST = "bellflower1209.github.io"
SITEMAP_URL = f"{PUBLIC_BASE_URL}/sitemap.xml"
LEGACY_REDIRECTS = {
    Path("releases/toriatsukai-chuui/index.html"): f"{PUBLIC_BASE_URL}/releases/toriatsukai-chui/",
}
MIA_DEDICATED_RELEASES = {
    "無敵時間、あと3秒": "../../releases/muteki-jikan-ato-3byou/",
    "M・I・A": "../../releases/mia/",
    "解けない魔法を、愛と呼ぶ": "../../releases/tokenai-mahou-wo-ai-to-yobu/",
    "君とならラスボスまで": "../../releases/kimi-to-nara-last-boss-made/",
    "AIでもわからない": "../../releases/ai-demo-wakaranai/",
    "君は花火": "../../releases/kimi-wa-hanabi/",
    "百万告": "../../releases/hyakumankoku/",
    "好きってバレてもいい": "../../releases/sukitte-baretemo-ii/",
    "MERMAID×MERMAN": "../../releases/mermaid-merman/",
    "取り扱いチュー💋い": "../../releases/toriatsukai-chui/",
}
NEW_RELEASE_DETAILS = {
    "解けない魔法を、愛と呼ぶ": ("./releases/tokenai-mahou-wo-ai-to-yobu/", "https://www.youtube.com/watch?v=CAFQ-d7YHPQ"),
    "君とならラスボスまで": ("./releases/kimi-to-nara-last-boss-made/", "https://www.youtube.com/watch?v=YVNs3I-KaHI"),
    "AIでもわからない": ("./releases/ai-demo-wakaranai/", "https://www.youtube.com/watch?v=5jmTo3Jb5sI"),
    "君は花火": ("./releases/kimi-wa-hanabi/", "https://www.youtube.com/watch?v=ohylad3AWYI"),
    "好きってバレてもいい": ("./releases/sukitte-baretemo-ii/", "https://youtu.be/XP8yXMKFHVI"),
    "MERMAID×MERMAN": ("./releases/mermaid-merman/", "https://youtu.be/29fpeNtUqfY"),
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.h1_count = 0
        self.images: list[tuple[str, bool, str]] = []
        self.anchors: list[str] = []
        self.references: list[str] = []
        self.json_ld_blocks: list[str] = []
        self._in_title = False
        self._in_json_ld = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            content = values.get("content")
            if key and content is not None:
                self.meta.setdefault(key, []).append(content)
        elif tag == "link":
            href = values.get("href")
            if href:
                self.references.append(href)
                if "canonical" in (values.get("rel") or "").split():
                    self.canonicals.append(href)
        elif tag == "a":
            href = values.get("href")
            if href:
                self.anchors.append(href)
                self.references.append(href)
        elif tag == "img":
            src = values.get("src") or ""
            self.images.append((src, "alt" in values, values.get("alt") or ""))
            if src:
                self.references.append(src)
        elif tag in {"script", "iframe"}:
            src = values.get("src")
            if src:
                self.references.append(src)
            if tag == "script" and values.get("type") == "application/ld+json":
                self._in_json_ld = True
                self._json_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_json_ld:
            self.json_ld_blocks.append("".join(self._json_parts).strip())
            self._in_json_ld = False
            self._json_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_json_ld:
            self._json_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def content_pages() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("index.html")
        if ".git" not in path.parts
        and "node_modules" not in path.parts
        and path.relative_to(ROOT) not in LEGACY_REDIRECTS
    )


def public_url(path: Path) -> str:
    relative = path.relative_to(ROOT)
    if relative == Path("index.html"):
        return f"{PUBLIC_BASE_URL}/"
    return f"{PUBLIC_BASE_URL}/{relative.parent.as_posix()}/"


def local_path_from_url(url: str) -> Path | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.netloc != PUBLIC_HOST:
        return None
    path = parsed.path
    if not path.startswith(PUBLIC_PATH_PREFIX):
        return None
    relative = path[len(PUBLIC_PATH_PREFIX) :]
    if not relative or relative.endswith("/"):
        relative += "index.html"
    return ROOT / urllib.parse.unquote(relative)


def singleton(values: list[str] | None, label: str, page: Path, errors: list[str]) -> str:
    if not values or len(values) != 1:
        errors.append(f"{page}: expected one {label}, found {len(values or [])}")
        return ""
    return values[0]


def collect_types(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            found.add(item_type)
        elif isinstance(item_type, list):
            found.update(item for item in item_type if isinstance(item, str))
        for child in value.values():
            collect_types(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_types(child, found)


def collect_strings(value: Any, found: list[str]) -> None:
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            collect_strings(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_strings(child, found)


def collect_nodes(value: Any, found: dict[str, dict[str, Any]]) -> None:
    if isinstance(value, dict):
        node_id = value.get("@id")
        if isinstance(node_id, str):
            found.setdefault(node_id, {}).update(value)
        for child in value.values():
            collect_nodes(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_nodes(child, found)


def required_schema_types(relative: Path) -> set[str]:
    route = relative.as_posix()
    if route == "index.html":
        return {"Organization", "WebSite", "WebPage"}
    if route == "about/index.html":
        return {"AboutPage", "BreadcrumbList"}
    if route == "artists/index.html":
        return {"CollectionPage", "ItemList", "BreadcrumbList"}
    if route == "artists/eclypse/index.html":
        return {"MusicGroup", "ProfilePage", "BreadcrumbList"}
    if route.startswith("artists/"):
        return {"Person", "ProfilePage", "BreadcrumbList"}
    if route.startswith("releases/"):
        return {"MusicRecording", "VideoObject", "BreadcrumbList", "WebPage"}
    return set()


def audit() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    pages = content_pages()
    expected_urls = {public_url(path): path for path in pages}
    parsed_pages: dict[str, PageParser] = {}
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}

    for relative, target_url in LEGACY_REDIRECTS.items():
        redirect_path = ROOT / relative
        if not redirect_path.is_file():
            errors.append(f"legacy redirect is missing: {relative}")
            continue
        redirect_html = redirect_path.read_text(encoding="utf-8")
        redirect_parser = PageParser()
        redirect_parser.feed(redirect_html)
        if redirect_parser.canonicals != [target_url]:
            errors.append(f"{relative}: redirect canonical must be {target_url}")
        robots = redirect_parser.meta.get("robots", [])
        if robots != ["noindex, follow"]:
            errors.append(f"{relative}: redirect must use noindex, follow")
        target_path = local_path_from_url(target_url)
        if target_path is None or not target_path.is_file():
            errors.append(f"{relative}: redirect target is missing: {target_url}")
        if "../toriatsukai-chui/" not in redirect_html:
            errors.append(f"{relative}: redirect target is not linked in the HTML")

    for path in pages:
        relative = path.relative_to(ROOT)
        page_url = public_url(path)
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parsed_pages[page_url] = parser

        if not parser.title:
            errors.append(f"{relative}: title is missing")
        elif parser.title in titles:
            errors.append(f"{relative}: title duplicates {titles[parser.title]}")
        else:
            titles[parser.title] = relative.as_posix()

        description = singleton(parser.meta.get("description"), "meta description", relative, errors)
        if description:
            if description in descriptions:
                errors.append(f"{relative}: description duplicates {descriptions[description]}")
            descriptions[description] = relative.as_posix()

        canonical = singleton(parser.canonicals, "canonical", relative, errors)
        og_url = singleton(parser.meta.get("og:url"), "og:url", relative, errors)
        og_image = singleton(parser.meta.get("og:image"), "og:image", relative, errors)
        twitter_image = singleton(parser.meta.get("twitter:image"), "twitter:image", relative, errors)
        if canonical and canonical != page_url:
            errors.append(f"{relative}: canonical {canonical!r} != {page_url!r}")
        if og_url and og_url != page_url:
            errors.append(f"{relative}: og:url {og_url!r} != {page_url!r}")
        if og_image and twitter_image and og_image != twitter_image:
            errors.append(f"{relative}: og:image and twitter:image differ")
        for label, image_url in (("og:image", og_image), ("twitter:image", twitter_image)):
            if not image_url:
                continue
            image_path = local_path_from_url(image_url)
            if image_path is None or not image_path.is_file():
                errors.append(f"{relative}: {label} does not resolve to a local public image: {image_url}")

        if parser.h1_count != 1:
            errors.append(f"{relative}: expected one h1, found {parser.h1_count}")
        for src, has_alt, _alt in parser.images:
            if not has_alt:
                errors.append(f"{relative}: image is missing alt: {src}")

        schema_types: set[str] = set()
        schema_strings: list[str] = []
        schema_nodes: dict[str, dict[str, Any]] = {}
        for index, block in enumerate(parser.json_ld_blocks, start=1):
            try:
                data = json.loads(block)
            except json.JSONDecodeError as error:
                errors.append(f"{relative}: JSON-LD block {index} is invalid: {error}")
                continue
            collect_types(data, schema_types)
            collect_strings(data, schema_strings)
            collect_nodes(data, schema_nodes)
        missing_types = required_schema_types(relative) - schema_types
        if missing_types:
            errors.append(f"{relative}: missing schema types: {', '.join(sorted(missing_types))}")
        for value in schema_strings:
            if value.startswith("https://bellflower1209.github.io/") and not value.startswith(PUBLIC_BASE_URL):
                errors.append(f"{relative}: JSON-LD points outside the canonical project path: {value}")
        if relative.as_posix().startswith("releases/"):
            video_id = f"{page_url}#video"
            video = schema_nodes.get(video_id, {})
            required_video_fields = {"name", "description", "thumbnailUrl", "uploadDate", "contentUrl", "embedUrl"}
            missing_video_fields = required_video_fields - set(video)
            if missing_video_fields:
                errors.append(
                    f"{relative}: VideoObject is missing: {', '.join(sorted(missing_video_fields))}"
                )
            upload_date = video.get("uploadDate")
            if isinstance(upload_date, str):
                try:
                    datetime.fromisoformat(upload_date)
                except ValueError:
                    errors.append(f"{relative}: VideoObject uploadDate is not ISO 8601: {upload_date}")

        for reference in parser.references:
            if reference.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            absolute = urllib.parse.urljoin(page_url, reference)
            parsed_reference = urllib.parse.urlsplit(absolute)
            if parsed_reference.netloc != PUBLIC_HOST:
                continue
            local_path = local_path_from_url(absolute)
            if local_path is None or not local_path.exists():
                errors.append(f"{relative}: broken internal reference: {reference}")

    artist_html = (ROOT / "artists/enomoto-mia/index.html").read_text(encoding="utf-8")
    track_list_match = re.search(r'<div class="artist-track-list">(.*?)</div></section>', artist_html, re.DOTALL)
    if not track_list_match:
        errors.append("artists/enomoto-mia/index.html: discography list is missing")
    else:
        track_rows = re.findall(
            r'<a class="artist-track-row[^"]*" href="([^"]+)"><span>(\d+)</span>.*?<strong>(.*?)</strong>',
            track_list_match.group(1),
            re.DOTALL,
        )
        track_titles = [re.sub(r"<!--.*?-->", "", title).strip() for _, _, title in track_rows]
        track_numbers = [int(number) for _, number, _ in track_rows]
        if track_numbers != list(range(1, len(track_numbers) + 1)):
            errors.append("artists/enomoto-mia/index.html: discography numbering is not sequential")
        if len(track_titles) != len(set(track_titles)):
            errors.append("artists/enomoto-mia/index.html: discography contains duplicate songs")
        tracks_by_title = {title: href for (href, _, _), title in zip(track_rows, track_titles)}
        for title, expected_href in MIA_DEDICATED_RELEASES.items():
            if tracks_by_title.get(title) != expected_href:
                errors.append(
                    f"artists/enomoto-mia/index.html: {title} must link to {expected_href}"
                )

    homepage_html = (ROOT / "index.html").read_text(encoding="utf-8")
    release_cards = re.findall(r'<article class="release-card[^"]*">.*?</article>', homepage_html, re.DOTALL)
    release_titles = []
    cards_by_title: dict[str, str] = {}
    for card in release_cards:
        title_match = re.search(r"<h3>(.*?)</h3>", card, re.DOTALL)
        if not title_match:
            continue
        title = re.sub(r"<!--.*?-->", "", title_match.group(1)).strip()
        release_titles.append(title)
        cards_by_title[title] = card
    if len(release_titles) != len(set(release_titles)):
        errors.append("index.html: release list contains duplicate song cards")
    for title, (detail_href, mv_href) in NEW_RELEASE_DETAILS.items():
        card = cards_by_title.get(title, "")
        if not card:
            errors.append(f"index.html: release card is missing for {title}")
            continue
        for expected in (detail_href, mv_href, "詳細を見る", "MVを見る"):
            if expected not in card:
                errors.append(f"index.html: {title} card is missing {expected}")

    graph: dict[str, set[str]] = {url: set() for url in expected_urls}
    for page_url, parser in parsed_pages.items():
        for href in parser.anchors:
            absolute = urllib.parse.urldefrag(urllib.parse.urljoin(page_url, href)).url
            if absolute in expected_urls:
                graph[page_url].add(absolute)

    reachable: set[str] = set()
    queue = deque([f"{PUBLIC_BASE_URL}/"])
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(graph.get(current, set()) - reachable)
    orphaned = sorted(set(expected_urls) - reachable)
    for url in orphaned:
        errors.append(f"orphaned page: {url}")

    homepage_links = graph.get(f"{PUBLIC_BASE_URL}/", set())
    missing_home_links = sorted(set(expected_urls) - homepage_links - {f"{PUBLIC_BASE_URL}/"})
    for url in missing_home_links:
        errors.append(f"homepage does not link directly to important page: {url}")

    try:
        sitemap_root = ET.parse(ROOT / "sitemap.xml").getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = [element.text or "" for element in sitemap_root.findall("sm:url/sm:loc", namespace)]
        if len(sitemap_urls) != len(set(sitemap_urls)):
            errors.append("sitemap.xml contains duplicate URLs")
        if set(sitemap_urls) != set(expected_urls):
            missing = sorted(set(expected_urls) - set(sitemap_urls))
            extra = sorted(set(sitemap_urls) - set(expected_urls))
            if missing:
                errors.append(f"sitemap.xml is missing: {', '.join(missing)}")
            if extra:
                errors.append(f"sitemap.xml has unexpected URLs: {', '.join(extra)}")
        lastmods = [element.text or "" for element in sitemap_root.findall("sm:url/sm:lastmod", namespace)]
        if len(lastmods) == len(expected_urls) and len(set(lastmods)) == 1:
            errors.append("sitemap.xml mechanically assigns one lastmod date to every page")
    except (ET.ParseError, OSError) as error:
        errors.append(f"sitemap.xml is invalid: {error}")
        sitemap_urls = []

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "User-agent: *" not in robots:
        errors.append("robots.txt is missing the default user-agent rule")
    if "Disallow:" in robots:
        errors.append("robots.txt contains a Disallow rule")
    if "Allow: /suzuka-official-music/" not in robots:
        errors.append("robots.txt does not explicitly allow the GitHub Pages project path")
    if f"Sitemap: {SITEMAP_URL}" not in robots:
        errors.append("robots.txt does not contain the absolute sitemap URL")

    summary = {
        "pages": len(pages),
        "sitemap_urls": len(sitemap_urls),
        "reachable_pages": len(reachable & set(expected_urls)),
        "json_ld_blocks": sum(len(parser.json_ld_blocks) for parser in parsed_pages.values()),
    }
    return errors, summary


def main() -> int:
    errors, summary = audit()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"SEO audit failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(
        "SEO audit passed: "
        f"{summary['pages']} pages, {summary['sitemap_urls']} sitemap URLs, "
        f"{summary['reachable_pages']} reachable pages, {summary['json_ld_blocks']} JSON-LD blocks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

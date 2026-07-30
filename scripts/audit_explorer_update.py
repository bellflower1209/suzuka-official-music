#!/usr/bin/env python3
"""Audit the generated SUZUKA Explorer Update and its source-backed counts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


NEW_ROOTS = ("rankings", "features", "gallery", "universe", "wiki")
NAV_ROUTES = ("rankings/", "features/", "gallery/", "universe/", "wiki/")


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.canonical: list[str] = []
        self.meta: dict[str, list[str]] = {}
        self.links: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.json_blocks: list[str] = []
        self._json = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        elif tag == "link" and "canonical" in (values.get("rel") or "").split():
            if values.get("href"):
                self.canonical.append(values["href"] or "")
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key and values.get("content") is not None:
                self.meta.setdefault(key, []).append(values["content"] or "")
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        elif tag == "img":
            self.images.append(values)
        elif tag == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._json:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json:
            self.json_blocks.append("".join(self._parts).strip())
            self._json = False


def collect_types(value: object, found: set[str]) -> None:
    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            found.add(item_type)
        elif isinstance(item_type, list):
            found.update(str(item) for item in item_type)
        for child in value.values():
            collect_types(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_types(child, found)


def parse(path: Path) -> tuple[Parser, set[str], list[str]]:
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8"))
    types: set[str] = set()
    errors: list[str] = []
    for block in parser.json_blocks:
        try:
            collect_types(json.loads(block), types)
        except json.JSONDecodeError as error:
            errors.append(f"{path}: invalid JSON-LD: {error}")
    return parser, types, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []

    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    rankings = json.loads((root / "assets/data/rankings.json").read_text(encoding="utf-8"))
    releases = catalog["releases"]
    upcoming = catalog["upcoming"]
    artist_slugs = sorted({slug for item in releases for slug in item["artistSlugs"]})
    feature_pages = sorted((root / "features").glob("*/index.html"))
    gallery_pages = sorted((root / "gallery").glob("*/index.html"))
    wiki_pages = sorted((root / "wiki").glob("*/index.html"))
    new_pages = sorted(path for name in NEW_ROOTS for path in (root / name).rglob("index.html"))

    expected = {
        "published": 25,
        "upcoming": 5,
        "artists": 7,
        "rankings": 9,
        "features": 10,
        "galleryWorks": 25,
        "wikiPages": 7,
        "universePages": 1,
    }
    actual = {
        "published": len(releases),
        "upcoming": len(upcoming),
        "artists": len(artist_slugs),
        "rankings": len(rankings["rankings"]),
        "features": len(feature_pages),
        "galleryWorks": len(gallery_pages),
        "wikiPages": len(wiki_pages) + 1,
        "universePages": len(list((root / "universe").glob("index.html"))),
    }
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            errors.append(f"{key}: expected {expected_value}, found {actual[key]}")

    if (root / "features/winter-songs/index.html").exists():
        errors.append("zero-work winter feature must not be generated")

    for path in new_pages:
        relative = path.relative_to(root)
        parsed, types, json_errors = parse(path)
        errors.extend(json_errors)
        if parsed.h1 != 1:
            errors.append(f"{relative}: expected one h1, found {parsed.h1}")
        if len(parsed.canonical) != 1:
            errors.append(f"{relative}: expected one canonical, found {len(parsed.canonical)}")
        for key in ("description", "twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if len(parsed.meta.get(key, [])) != 1:
                errors.append(f"{relative}: expected one {key}")
        for key in ("og:title", "og:description", "og:url", "og:image"):
            if len(parsed.meta.get(key, [])) != 1:
                errors.append(f"{relative}: expected one {key}")
        if "AI" not in (parsed.meta.get("description") or [""])[0]:
            errors.append(f"{relative}: meta description must retain AI disclosure")
        if "BreadcrumbList" not in types:
            errors.append(f"{relative}: BreadcrumbList missing")
        if not parsed.json_blocks:
            errors.append(f"{relative}: JSON-LD missing")
        for image in parsed.images:
            if not (image.get("alt") or "").strip():
                errors.append(f"{relative}: image without alt")
            if relative.parts[0] == "gallery" and image.get("loading") != "lazy":
                errors.append(f"{relative}: gallery image must use lazy loading")
        source = path.read_text(encoding="utf-8")
        if "assets/main.js" not in source:
            errors.append(f"{relative}: fixed player loader missing")
        if re.search(r"(?:autoplay=1|autoplay:\s*1)", source):
            errors.append(f"{relative}: autoplay enabled")

    for path in sorted(root.glob("**/index.html")):
        relative = path.relative_to(root)
        if relative == Path("releases/toriatsukai-chuui/index.html"):
            continue
        source = path.read_text(encoding="utf-8")
        if "desktop-nav" in source and relative.parts[0] != "en":
            for route in NAV_ROUTES:
                if route not in source:
                    errors.append(f"{relative}: navigation missing {route}")

    for slug in artist_slugs:
        path = root / f"artists/{slug}/index.html"
        source = path.read_text(encoding="utf-8")
        for marker in (
            "LATEST MV / PUBLIC RELEASE", "AUTOMATIC TOP 3", "最新News",
            "公開作品一覧", "SUZUKA Original AI Artist", "Instagram",
        ):
            if marker not in source:
                errors.append(f"artists/{slug}: missing {marker}")

    if errors:
        print("Explorer Update audit failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", **actual, "newPages": len(new_pages)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

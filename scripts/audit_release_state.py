#!/usr/bin/env python3
"""Audit canonical release state separation and official-source fields."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_state import RELEASE_STATUSES, parse_iso8601


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    errors = []
    collections = {"releases": cms.get("releases", []), "upcoming": cms.get("upcoming", [])}
    slugs = [item["slug"] for values in collections.values() for item in values]
    if len(slugs) != len(set(slugs)):
        errors.append("duplicate canonical release slug")
    for collection, items in collections.items():
        expected = "published" if collection == "releases" else "upcoming"
        for item in items:
            if item.get("status") not in RELEASE_STATUSES or item.get("status") != expected:
                errors.append(f'{item["slug"]}: invalid state for {collection}: {item.get("status")}')
            timestamp = item.get("publishedAt") if expected == "published" else item.get("scheduledAt")
            try:
                parse_iso8601(timestamp)
            except (TypeError, ValueError) as error:
                errors.append(f'{item["slug"]}: invalid timestamp: {error}')
            if expected != "upcoming" or not item.get("releaseDate"):
                if not str(item.get("youtubeUrl", "")).startswith("https://www.youtube.com/watch?v="):
                    errors.append(f'{item["slug"]}: official YouTube URL missing')
    catalog_published = {item["slug"] for item in catalog["releases"]}
    catalog_upcoming = {item["slug"] for item in catalog["upcoming"]}
    if catalog_published != {item["slug"] for item in collections["releases"]}:
        errors.append("published catalog differs from Creator CMS")
    if catalog_upcoming != {item["slug"] for item in collections["upcoming"]}:
        errors.append("upcoming catalog differs from Creator CMS")
    for item in collections["upcoming"]:
        path = root / f'releases/{item["slug"]}/index.html'
        if not path.is_file() or 'content="noindex, follow"' not in path.read_text(encoding="utf-8"):
            errors.append(f'{item["slug"]}: upcoming page missing or indexable')
        if (root / f'lyrics/{item["slug"]}/index.html').exists():
            errors.append(f'{item["slug"]}: upcoming Lyrics leaked')
    for item in collections["releases"]:
        path = root / f'releases/{item["slug"]}/index.html'
        if not path.is_file():
            errors.append(f'{item["slug"]}: published page missing')
            continue
        if 'content="noindex' in path.read_text(encoding="utf-8").lower():
            errors.append(f'{item["slug"]}: published page remains noindex')
    if errors:
        raise SystemExit("Release state audit failed:\n- " + "\n- ".join(errors))
    print(json.dumps({
        "status": "PASS", "published": len(collections["releases"]),
        "upcoming": len(collections["upcoming"]), "duplicateSlugs": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

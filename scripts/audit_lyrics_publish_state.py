#!/usr/bin/env python3
"""Audit every Version 1.2 consumer against the shared Lyrics publication gate."""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from release_state import publishable_lyrics, verified_lyrics_waiting


SITEMAP = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    eligible = publishable_lyrics(cms["releases"])
    expected = {item["slug"] for item in eligible}
    waiting = verified_lyrics_waiting(cms.get("upcoming", []))
    actual = {path.parent.name for path in (root / "lyrics").glob("*/index.html")}
    sitemap = ET.parse(root / "sitemap.xml").getroot()
    sitemap_lyrics = {
        node.text.rstrip("/").rsplit("/", 1)[-1]
        for node in sitemap.findall("s:url/s:loc", SITEMAP)
        if node.text and "/lyrics/" in node.text.rstrip("/") and node.text.rstrip("/").rsplit("/", 1)[-1] != "lyrics"
    }
    search = json.loads((root / "assets/data/search-v31.json").read_text(encoding="utf-8"))["documents"]
    search_lyrics = {
        item["url"].strip("/").rsplit("/", 1)[-1]
        for item in search if item.get("contentType") == "lyrics" and item.get("url") != "lyrics/"
    }
    feed = ET.parse(root / "feed.xml").getroot()
    feed_lyrics = {
        node.find("a:id", ATOM).text.rstrip("/").rsplit("/", 1)[-1]
        for node in feed.findall("a:entry", ATOM)
        if (category := node.find("a:category", ATOM)) is not None and category.get("term") == "lyrics"
    }
    errors = []
    for label, values in (("details", actual), ("sitemap", sitemap_lyrics), ("search", search_lyrics), ("feed", feed_lyrics)):
        if values != expected:
            errors.append(f'{label}: expected={sorted(expected)} actual={sorted(values)}')
    home = (root / "index.html").read_text(encoding="utf-8")
    match = re.search(r'data-public-count="lyrics"[^>]*>(\d+)', home)
    if not match or int(match.group(1)) != len(expected):
        errors.append("Home Lyrics count mismatch")
    for artist in cms["artists"]:
        count = sum(item.get("artistSlug") == artist["slug"] for item in eligible)
        page = (root / f'artists/{artist["slug"]}/index.html').read_text(encoding="utf-8")
        visible = re.search(r'公式歌詞（(\d+)件）', page)
        if (int(visible.group(1)) if visible else 0) != count:
            errors.append(f'{artist["slug"]}: Artist Lyrics count mismatch')
    if errors:
        raise SystemExit("Lyrics publish-state audit failed:\n- " + "\n- ".join(errors))
    print(json.dumps({
        "status": "PASS", "publishedLyrics": len(expected),
        "verifiedWaiting": len(waiting), "sharedGateConsumers": 8,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare all visible public counts and freshness labels with canonical data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    books = json.loads((ROOT / "assets/data/photobooks.json").read_text(encoding="utf-8"))["photobooks"]
    releases = [item for item in catalog["releases"] if item.get("status") == "published"]
    upcoming = [item for item in cms["upcoming"] if item.get("status") == "upcoming"]
    artists = [item for item in cms["artists"] if item.get("status") == "published"]
    lyrics = [item for item in releases if item.get("lyricsAvailable") is True and item.get("lyricsVerified") is True and item.get("lyricsVerifiedAt") and item.get("lyricsText")]
    photobooks = [item for item in books if item.get("status") == "published"]
    counts = {"lyrics": len(lyrics), "artists": len(artists), "releases": len(releases), "upcoming": len(upcoming), "photobooks": len(photobooks)}
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    errors = []
    for key, expected in counts.items():
        match = re.search(rf'data-public-count="{key}"[^>]*>(\d+)', home)
        if not match or int(match.group(1)) != expected:
            errors.append(f"Home {key}: expected={expected}, visible={match.group(1) if match else 'missing'}")
    if len(re.findall(r"data-lyrics-entry", (ROOT / "lyrics/index.html").read_text(encoding="utf-8"))) != len(lyrics):
        errors.append("Lyrics hub count mismatch")
    for artist in artists:
        expected = sum(artist["slug"] in item.get("artistSlugs", []) and item in lyrics for item in releases)
        text = (ROOT / f'artists/{artist["slug"]}/index.html').read_text(encoding="utf-8")
        match = re.search(rf'公式歌詞（(\d+)件）', text)
        visible = int(match.group(1)) if match else 0
        if visible != expected:
            errors.append(f'{artist["slug"]}: lyrics expected={expected}, visible={visible}')
    if '<strong data-dashboard="lyrics">' not in (ROOT / "admin/dashboard/index.html").read_text(encoding="utf-8"):
        errors.append("Dashboard Lyrics tile missing")
    dashboard_js = (ROOT / "assets/creator-dashboard.js").read_text(encoding="utf-8")
    if 'x.status==="published"&&x.lyricsAvailable===true&&x.lyricsVerified===true' not in dashboard_js:
        errors.append("Dashboard Lyrics canonical filter missing")
    latest = max(releases, key=lambda item: (item.get("publishedAt", item["releaseDate"]), item["slug"]))
    if not re.search(rf'id="latest-title">{re.escape(latest["displayTitle"])}<', home):
        errors.append(f'Latest Release mismatch: {latest["slug"]}')
    if upcoming:
        next_item = min(upcoming, key=lambda item: (item["scheduledAt"], item["slug"]))
        if f'data-release-slug="{next_item["slug"]}"' not in home:
            errors.append(f'Next Release mismatch: {next_item["slug"]}')
    if "0 LYRICS" in home:
        errors.append("stale 0 LYRICS remains")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"status": "PASS", **counts, "staleZeroLyrics": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

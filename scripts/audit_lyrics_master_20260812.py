#!/usr/bin/env python3
"""Audit the 2026-08-12 user-confirmed lyric master import and publication gates."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from import_official_lyrics_20260812 import SOURCES


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "assets/data/lyrics-sources.json").read_text(encoding="utf-8"))
    holds = json.loads((ROOT / "assets/data/lyrics-holds.json").read_text(encoding="utf-8"))
    source_rows = {item["filename"]: item for item in manifest["sources"]}
    canonical = {
        item["slug"]: item
        for collection in ("releases", "upcoming")
        for item in cms[collection]
    }
    held_rows = {item["filename"]: item for item in holds["holds"]}
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    feed = (ROOT / "feed.xml").read_text(encoding="utf-8")
    search = (ROOT / "assets/data/search-v31.json").read_text(encoding="utf-8")
    errors = []
    registered = published = upcoming = held = 0

    for definition in SOURCES:
        source = source_rows.get(definition["filename"])
        if not source or source.get("sha256") != definition["sha256"]:
            errors.append(f'{definition["filename"]}: source manifest/hash mismatch')
            continue
        slug = definition.get("slug")
        if not slug:
            held += 1
            hold = held_rows.get(definition["filename"])
            if not hold or hold.get("status") != "held-unmatched":
                errors.append(f'{definition["filename"]}: unmatched hold missing')
                continue
            digest = hashlib.sha256(hold.get("lyricsText", "").encode("utf-8")).hexdigest()
            if digest != source.get("lyricsTextSha256"):
                errors.append(f'{definition["filename"]}: held lyric text hash mismatch')
            if definition["sourceTitle"] in sitemap or definition["sourceTitle"] in feed or definition["sourceTitle"] in search:
                errors.append(f'{definition["filename"]}: unmatched lyric leaked to public discovery')
            continue
        registered += 1
        item = canonical.get(slug)
        if not item or item.get("title") != definition["title"]:
            errors.append(f"{slug}: canonical title missing or mismatched")
            continue
        digest = hashlib.sha256(item.get("lyricsText", "").encode("utf-8")).hexdigest()
        if digest != source.get("lyricsTextSha256"):
            errors.append(f"{slug}: canonical lyric text hash mismatch")
        for field in ("lyricsAvailable", "lyricsVerified"):
            if item.get(field) is not True:
                errors.append(f"{slug}: {field} must be true")
        if not item.get("lyricsSource") or not item.get("lyricsVerifiedAt"):
            errors.append(f"{slug}: source/verifiedAt missing")
        page = ROOT / f"lyrics/{slug}/index.html"
        public_url = f"https://www.suzukaofficial.com/lyrics/{slug}/"
        search_url = f'"url": "lyrics/{slug}/"'
        if item.get("status") == "published":
            published += 1
            if not page.is_file() or public_url not in sitemap or search_url not in search:
                errors.append(f"{slug}: published lyric discovery mismatch")
        else:
            upcoming += 1
            if page.exists() or public_url in sitemap or public_url in feed or search_url in search:
                errors.append(f"{slug}: upcoming lyric leaked before publication")

    if len(held_rows) != 2:
        errors.append(f"held lyric count must be 2, found {len(held_rows)}")
    if errors:
        print("2026-08-12 lyric master audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS", "masters": len(SOURCES), "registered": registered,
        "published": published, "upcomingHeld": upcoming, "unmatchedHeld": held,
        "guessedLyrics": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

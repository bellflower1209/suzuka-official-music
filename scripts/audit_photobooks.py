#!/usr/bin/env python3
"""Audit source-verified note photobook data and generated pages."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

FIELDS = (
    "id", "slug", "title", "artistSlug", "coverImage", "noteUrl", "publishedAt",
    "status", "description", "relatedReleaseSlugs", "featured", "isPaid", "priceLabel",
    "coverAlt", "coverWidth", "coverHeight", "contentType", "sourceVerifiedAt",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    data = json.loads((root / "assets/data/photobooks.json").read_text(encoding="utf-8"))
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    books = data.get("photobooks", [])
    published = [item for item in books if item.get("status") == "published"]
    errors = []
    slugs = set()
    artist_slugs = {item["slug"] for item in cms["artists"]}
    release_slugs = {item["slug"] for item in cms["releases"]}
    for item in books:
        missing = [field for field in FIELDS if field not in item]
        if missing:
            errors.append(f"{item.get('slug', '?')}: missing fields {missing}")
        if item.get("slug") in slugs:
            errors.append(f"duplicate slug: {item.get('slug')}")
        slugs.add(item.get("slug"))
        if item.get("artistSlug") not in artist_slugs:
            errors.append(f"{item.get('slug')}: unknown artistSlug")
        if any(slug not in release_slugs for slug in item.get("relatedReleaseSlugs", [])):
            errors.append(f"{item.get('slug')}: unknown related release")
        if item.get("status") == "published":
            parsed = urlparse(str(item.get("noteUrl") or ""))
            if parsed.scheme != "https" or parsed.hostname not in {"note.com", "www.note.com"}:
                errors.append(f"{item.get('slug')}: published noteUrl is not a verified note.com HTTPS URL")
            cover = root / str(item.get("coverImage") or "")
            if not cover.is_file():
                errors.append(f"{item.get('slug')}: cover image missing")
            if not str(item.get("publishedAt") or "").endswith("+09:00"):
                errors.append(f"{item.get('slug')}: publishedAt must include +09:00")
            if item.get("isPaid") is True and not item.get("priceLabel"):
                errors.append(f"{item.get('slug')}: paid item missing verified priceLabel")
            if item.get("isPaid") is False and item.get("priceLabel"):
                errors.append(f"{item.get('slug')}: free item must not have a priceLabel")
    hub = (root / "photobooks/index.html").read_text(encoding="utf-8")
    for marker in ("SUZUKA公式AIアーティストの写真集・Visual Collection一覧。", "BreadcrumbList", "ItemList"):
        if marker not in hub:
            errors.append(f"photobooks hub missing {marker}")
    actual = {path.parent.name for path in (root / "photobooks").glob("*/index.html")}
    expected = {item["slug"] for item in published}
    if actual != expected:
        errors.append(f"detail mismatch: expected={sorted(expected)} actual={sorted(actual)}")
    analytics = (root / "assets/analytics.js").read_text(encoding="utf-8")
    for event in ("lyrics_click", "photobook_click", "note_click"):
        if f'"{event}"' not in analytics:
            errors.append(f"analytics missing {event}")
    for parameter in ("photobook_title", "artist", "source_section", "destination_url", "current_page"):
        if parameter not in analytics:
            errors.append(f"analytics missing photobook parameter: {parameter}")
    for item in published:
        for release_slug in item.get("relatedReleaseSlugs", []):
            for linked_page in (root / f"gallery/{release_slug}/index.html", root / f"news/{release_slug}-release/index.html"):
                if not linked_page.is_file():
                    continue
                linked_text = linked_page.read_text(encoding="utf-8")
                for attribute in (f'data-slug="{item["slug"]}"', f'data-title="{item["title"]}"', 'data-artist="'):
                    if attribute not in linked_text:
                        errors.append(f"{linked_page.relative_to(root)}: photobook analytics context missing {attribute}")
    if re.search(r'https?://[^\s\"\']*note\.com', json.dumps(books, ensure_ascii=False)) and not published:
        errors.append("note URL exists without a published record")
    if errors:
        print("Photobook audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Photobook audit passed: {len(published)} verified note photobooks; guessed URLs=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

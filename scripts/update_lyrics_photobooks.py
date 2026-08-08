#!/usr/bin/env python3
"""Add source-safe lyrics and photobook fields without inventing content."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

UPDATED_AT = "2026-08-08T22:40:00+09:00"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()

    for relative in ("assets/data/creator-cms.json", "assets/data/releases-catalog.json"):
        path = root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data["releases"]:
            item.setdefault("lyricsAvailable", False)
            item.setdefault("lyricsSource", "")
            item.setdefault("lyricsText", "")
            item.setdefault("lyricsVerified", False)
            item.setdefault("lyricsVerifiedAt", None)
        data["updatedAt"] = UPDATED_AT
        write_json(path, data)

    cms_path = root / "assets/data/creator-cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    cms["photobooks"] = {
        "source": "assets/data/photobooks.json",
        "managedFields": [
            "id", "slug", "title", "artistSlug", "coverImage", "noteUrl",
            "publishedAt", "status", "description", "relatedReleaseSlugs",
            "featured", "isPaid", "priceLabel",
        ],
    }
    write_json(cms_path, cms)

    photobooks_path = root / "assets/data/photobooks.json"
    if not photobooks_path.exists():
        write_json(photobooks_path, {
            "schemaVersion": "1.0",
            "updatedAt": UPDATED_AT,
            "photobooks": [],
        })


if __name__ == "__main__":
    main()

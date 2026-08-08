#!/usr/bin/env python3
"""Audit data-driven solo/group artist profiles."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    artists = [item for item in cms["artists"] if item.get("status") == "published"]
    errors = []
    for artist in artists:
        path = root / f'artists/{artist["slug"]}/index.html'
        if not path.exists():
            errors.append(f'{artist["slug"]}: page missing')
            continue
        source = path.read_text(encoding="utf-8")
        label = "Group" if artist["type"] == "MusicGroup" else "Solo"
        for marker in (f'AI Artist / {label}', '"@type":"ProfilePage"', '"mainEntity"', f'"@type":"{artist["type"]}"', "公開作品一覧", "Upcoming", "Official MV / Shorts / News / Gallery"):
            if marker not in source:
                errors.append(f'{artist["slug"]}: missing {marker}')
        for member in artist.get("members", []):
            if member["name"] not in source:
                errors.append(f'{artist["slug"]}: verified member missing: {member["name"]}')
    directory = (root / "artists/index.html").read_text(encoding="utf-8")
    if directory.count("v31-artist-directory-card") != len(artists):
        errors.append("artist directory count does not match CMS")
    if errors:
        print("Artist V3.1 audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Artist V3.1 audit passed: {len(artists)} CMS-driven artist profiles.")
    return 0

if __name__ == "__main__": raise SystemExit(main())

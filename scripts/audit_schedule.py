#!/usr/bin/env python3
"""Audit official-JST schedule and noindex upcoming pages."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    schedule = (root / "schedule/index.html").read_text(encoding="utf-8")
    errors = []
    for item in cms["upcoming"]:
        if item["scheduledAt"] not in schedule or item["slug"] not in schedule:
            errors.append(f'schedule missing {item["slug"]} exact JST timestamp')
        page = root / f'releases/{item["slug"]}/index.html'
        if not page.exists():
            errors.append(f'upcoming page missing {item["slug"]}')
            continue
        source = page.read_text(encoding="utf-8")
        if 'content="noindex, follow"' not in source:
            errors.append(f'{item["slug"]}: noindex missing')
        if '"@type":"VideoObject"' in source or '"@type": "VideoObject"' in source:
            errors.append(f'{item["slug"]}: scheduled video must not expose VideoObject')
        if item["scheduledAt"] not in source or "data-countdown-output" not in source:
            errors.append(f'{item["slug"]}: countdown evidence missing')
    if not re.search(r'2026-\d\d-\d\dT\d\d:\d\d:\d\d\+09:00', schedule):
        errors.append("schedule has no timezone-aware JST datetime")
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    for item in cms["upcoming"]:
        if f'/releases/{item["slug"]}/' in sitemap:
            errors.append(f'{item["slug"]}: noindex upcoming URL leaked into sitemap')
    if errors:
        print("Schedule audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f'Schedule audit passed: {len(cms["upcoming"])} confirmed upcoming releases, all noindex and excluded from sitemap.')
    return 0

if __name__ == "__main__": raise SystemExit(main())

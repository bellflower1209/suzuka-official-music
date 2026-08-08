#!/usr/bin/env python3
"""Audit Creator Platform 3.1 cross-surface invariants."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    home = (root / "index.html").read_text(encoding="utf-8")
    rankings = (root / "rankings/index.html").read_text(encoding="utf-8")
    analytics = (root / "assets/analytics.js").read_text(encoding="utf-8")
    errors = []
    for marker in ('data-home-hero', '>花言葉</h1>', './images/enomoto-mia-hanakotoba.jpg', 'マーメイドの下僕', '君にかかった魔法', './schedule/', './lyrics/'):
        if marker not in home:
            errors.append(f'home missing {marker}')
    for marker in ('A. SUZUKAおすすめ', 'B. サイト人気', 'C. YouTube人気', 'D. 今週の注目', 'データ準備中'):
        if marker not in rankings:
            errors.append(f'rankings missing {marker}')
    for event in ('next_release_click', 'schedule_click', 'lyrics_click', 'ranking_click', 'shorts_click', 'news_click'):
        if f'"{event}"' not in analytics:
            errors.append(f'analytics missing {event}')
    if 'autoplay=1' in home or re.search(r'autoplay\s*:\s*1', home):
        errors.append('home enables autoplay')
    player = json.loads((root / 'assets/data/enomoto-mia-releases.json').read_text(encoding='utf-8'))
    tracks = [item for item in player['releases'] if item.get('status') == 'published' and all(item.get(key) for key in ('youtubeId', 'image', 'pageUrl')) and item.get('playerEnabled', True)]
    if len(tracks) != 14:
        errors.append(f'fixed player must remain 14 tracks, found {len(tracks)}')
    if cms.get('schemaVersion') != '3.1' or len(cms.get('artists', [])) != 8 or len(cms.get('releases', [])) != 36 or len(cms.get('upcoming', [])) != 3:
        errors.append('CMS V3.1 counts/schema mismatch')
    if errors:
        print("V3.1 audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("V3.1 audit passed: flower Hero, latest/next release, four ranking surfaces, GA4 events and fixed player invariants.")
    return 0

if __name__ == "__main__": raise SystemExit(main())

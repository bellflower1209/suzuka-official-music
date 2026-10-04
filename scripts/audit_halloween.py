#!/usr/bin/env python3
"""Regression gate for the October edition and removal of onsite music playback."""
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
errors=[]
for p in ROOT.rglob('*.html'):
    source=p.read_text()
    if not re.search(r"<html\b",source,re.I): continue
    if re.search(r'<(?:audio|iframe)\b',source,re.I): errors.append(f'{p.relative_to(ROOT)}: onsite media remains')
    if 'assets/player.css' in source: errors.append(f'{p}: player stylesheet remains')
    if 'assets/halloween-2026.css' not in source: errors.append(f'{p}: season stylesheet missing')
for p in (ROOT/'assets').glob('*.js'):
    if re.search(r'new Audio\s*\(|YT\.Player|playVideo\s*\(|pauseVideo\s*\(|iframe_api|suzuka-music-player',p.read_text()): errors.append(f'{p}: playback code remains')
a=next(x for x in cms['artists'] if x['slug']=='tetsuhige')
if a['image'] or [x['name'] for x in a['members']]!=['源治','虎徹']: errors.append('TETSUHIGE canonical facts incorrect')
for a in cms['artists']:
    page=ROOT/f'artists/{a["slug"]}/index.html'
    if not page.exists(): errors.append(f'{a["slug"]}: missing artist page')
    if a.get('image'):
        image=ROOT/a['image']
        if not image.exists(): errors.append(f'{a["slug"]}: local official image missing')
if not (ROOT/'images/michiru-official-channel-note.jpg').exists(): errors.append('Michiru official visual missing')
if errors: raise SystemExit('\n'.join(errors))
print(f'Halloween audit passed: {len(cms["artists"])} artists; no onsite music playback; existing official Michiru image restored.')

#!/usr/bin/env python3
"""Check canonical coverage, unique gate markup and authorized presentation assets."""
import json, re
from pathlib import Path
from xml.etree import ElementTree as ET
from build_celestial_gate import validate
ROOT=Path(__file__).resolve().parents[1]

def main():
    cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    config=json.loads((ROOT/'assets/data/celestial-gate.json').read_text())
    artists=[a for a in cms['artists'] if a.get('status')=='published']
    validate(ROOT,config,artists)
    errors=[];pages=0
    for p in [*ROOT.rglob('index.html'),ROOT/'404.html']:
        s=p.read_text();pages+=1
        if s.count('CELESTIAL-GATE:ASSETS:START')!=1 or s.count('id="cg-config"')!=1 or s.count('CELESTIAL-GATE:SETTINGS:START')!=1: errors.append(str(p.relative_to(ROOT)))
        expected='infernal' if p.relative_to(ROOT).as_posix()=='artists/nox/index.html' else 'celestial'
        if f'data-cg-realm="{expected}"' not in s:errors.append(f'{p}: wrong realm')
    for a in artists:
        p=ROOT/'artists'/a['slug']/'index.html';s=p.read_text()
        if a.get('image') and '../../'+a['image'] not in s: errors.append(f'{a["slug"]}: official visual missing')
        if not a.get('image') and 'IMAGE PENDING' not in s:errors.append(f'{a["slug"]}: pending visual lost')
    home=(ROOT/'index.html').read_text()
    for a in artists:
        if home.count(f'data-cg-world="{a["slug"]}"')!=1:errors.append(f'{a["slug"]}: unique home gate missing')
    nox=(ROOT/'artists/nox/index.html').read_text()
    if 'data-cg-return' not in nox or '天界へ帰還する' not in nox:errors.append('NOX return missing')
    for name in ['celestial-palace.svg','nox-citadel.svg','celestial-emblems.svg']:ET.parse(ROOT/'assets'/name)
    css=(ROOT/'assets/celestial-gate.css').read_text();js=(ROOT/'assets/celestial-gate.js').read_text()
    for marker in ['prefers-reduced-motion','@media print','.cg-door-left','.cg-door-right']:assert marker in css
    for marker in ['pagehide','pageshow','showModal','musicIsActive','AudioContext','config.doorAudio']:assert marker in js
    if errors:raise SystemExit('\n'.join(errors))
    print(json.dumps({'status':'PASS','htmlPages':pages,'artists':len(artists),'officialArtistImages':sum(bool(a.get('image')) for a in artists),'pendingArtistImages':[a['slug'] for a in artists if not a.get('image')],'audio':'verified' if config['doorAudio'] else 'MISSING FORMAL V2 - SILENT FALLBACK'},ensure_ascii=False))
if __name__=='__main__':main()

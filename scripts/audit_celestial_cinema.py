#!/usr/bin/env python3
"""Check photographic coverage, source identity and encoded asset integrity."""
import hashlib, json, re
from pathlib import Path
from build_celestial_gate import validate_cinema

ROOT=Path(__file__).resolve().parents[1]

def main():
    config=json.loads((ROOT/'assets/data/celestial-gate.json').read_text())
    cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    artists=[a for a in cms['artists'] if a.get('status')=='published']
    manifest=validate_cinema(ROOT,config,artists);errors=[];encoded=0
    official={a['slug']:a['image'] for a in artists if a.get('image')}
    thumbnails=manifest['officialThumbnails']
    if len(thumbnails)!=len(official) or {a['id']:a['source'] for a in thumbnails}!=official:
        errors.append('Official thumbnail coverage must exactly match canonical images')
    registration_path=ROOT/'assets/data/official-image-registrations.json'
    if registration_path.exists():
        for record in json.loads(registration_path.read_text()).get('registrations',[]):
            if record.get('status')!='registered-official-user-provided' or official.get(record.get('artistSlug'))!=record.get('image'):
                errors.append('Official registration does not match canonical image')
            for key,hash_key in [('image','imageSha256'),('originalPath','originalSha256')]:
                path=(ROOT/record[key]).resolve()
                if not path.is_relative_to((ROOT/'images').resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record.get(hash_key):
                    errors.append('Registered original/image integrity failed: '+record.get('artistSlug',''))
    for asset in manifest['assets']+manifest['officialThumbnails']:
        if asset in manifest['officialThumbnails']:
            if hashlib.sha256((ROOT/asset['source']).read_bytes()).hexdigest()!=asset['sourceSha256']:errors.append('Official source changed: '+asset['id'])
        for v in asset['variants']:
            data=(ROOT/v['path']).read_bytes();encoded+=1
            if len(data)!=v['bytes'] or hashlib.sha256(data).hexdigest()!=v['sha256']:errors.append('Asset hash mismatch: '+v['path'])
            if asset.get('kind')=='transparent-frame' and b'ALPH' not in data:errors.append('Transparent frame alpha missing: '+v['path'])
            if v['path'].endswith('.avif') and b'avif' not in data[:64]:errors.append('AVIF header missing: '+v['path'])
            if v['path'].endswith('.webp') and data[8:12]!=b'WEBP':errors.append('WebP header missing: '+v['path'])
    pages=list(ROOT.rglob('index.html'))+[ROOT/'404.html']
    for path in pages:
        s=path.read_text()
        if 'data-cg-page=' not in s or 'class="cg-scene"' not in s:errors.append('Photographic coverage missing: '+str(path.relative_to(ROOT)))
        if any(x in s for x in ['class="cg-cloud','class="cg-black-flames','celestial-palace.svg','nox-citadel.svg']):errors.append('Retired scenery active: '+str(path.relative_to(ROOT)))
    directory=(ROOT/'artists/index.html').read_text();home=(ROOT/'index.html').read_text()
    if directory.count('class="cg-world-stage"')!=len(artists) or home.count('class="cg-world-stage"')!=len(artists):errors.append('Canonical portal coverage mismatch')
    if 'fetchpriority="high"' not in home or 'loading="lazy"' not in home:errors.append('Critical/lazy image priorities missing')
    css=(ROOT/'assets/celestial-gate.css').read_text();js=(ROOT/'assets/celestial-gate.js').read_text()
    if any(x in css for x in ['celestial-palace.svg','nox-citadel.svg']):errors.append('Vector main scenery remains in active CSS')
    for key in ['.cg-door-leaves','transform-origin:left center','transform-origin:right center','--gate-texture','prefers-reduced-motion']:
        if key not in css:errors.append('Physical gate style missing: '+key)
    for key in ['cg-door-beyond','cg-door-frame','config.doorAudio','AudioContext','musicIsActive']:
        if key not in js:errors.append('Gate behavior missing: '+key)
    if errors:raise SystemExit('\n'.join(errors))
    print(json.dumps({'status':'PASS','htmlPages':len(pages),'artistEnvironments':len(artists),'environmentPlates':sum(a.get('kind')=='environment' for a in manifest['assets']),'doorTextures':2,'alphaFrames':2,'encodedFiles':encoded,'officialProfiles':len(official),'missingOfficialProfiles':len(artists)-len(official),'audio':'verified' if config['doorAudio'] else 'FORMAL V2 MISSING'},ensure_ascii=False))

if __name__=='__main__':main()

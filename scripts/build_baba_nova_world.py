#!/usr/bin/env python3
"""Add one approved world to the verified cf092e8 package without rebuilding twelve worlds."""
import argparse
import copy
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from build_music_production_release import package, sha
from build_official_sync_20261026 import build as previous_build
from official_activity_sections import track_html, shorts_html
from verify_public_release import read_release, verify_private_audio, write_output

ROOT=Path(__file__).resolve().parents[1]
BASE='cf092e8dc879069b6bbbbaf188e8e2ea160026a1'
DIGEST='fced8961770e273492e83fd3d04c426fa0e0b2dd7ae1e8ce57a202811cf50868'
MANIFEST='suzuka-v6-candidate-manifest.json'
WORLD_ROUTE='worlds/baba-nova/index.html'
CONFIG=re.compile(r'(<script type="application/json" id="v6-config">)(.*?)(</script>)',re.S)
def scene(cls='scene'):
    return '<picture class="'+cls+'" aria-hidden="true"><img src="/assets/baba-nova/scene.svg" width="1600" height="1000" alt="" loading="lazy" decoding="async"></picture>'
def template():
    return '<template id="v6-scene-baba-nova">'+scene()+'</template>'
def world_link():
    return '<a href="/worlds/baba-nova/" data-world-slug="baba-nova" data-world-route="worlds/baba-nova/">BABA NOVA <span aria-hidden="true">↗</span></a>'
def counts(s):
    return s.replace('十二の世界','十三の世界').replace('12の世界','13の世界').replace('TWELVE WORLDS','THIRTEEN WORLDS').replace(' / 12 ·',' / 13 ·')
def extend(s,world):
    m=CONFIG.search(s);assert m is not None
    c=json.loads(m[2]);assert len(c['worlds'])==12 and world['slug'] not in {w['slug'] for w in c['worlds']}
    c['worlds'].append({k:world[k] for k in ['slug','name','label','world','route','tint','drift','music','door']})
    s=s[:m.start(2)]+json.dumps(c,ensure_ascii=False,separators=(',',':'))+s[m.end(2):]
    s=s.replace('<template id="v6-scene-asagiri-shinobu">',template()+'<template id="v6-scene-asagiri-shinobu">',1)
    nav=re.search(r'<nav aria-label="他のアーティストの世界">.*?</nav>',s,re.S)
    if nav:s=s[:nav.end()-6]+world_link()+s[nav.end()-6:]
    return counts(s)
def build(root=ROOT):
    info,original=read_release(root,BASE)
    assert info['artifactDigest']==DIGEST and len(original)==802,'Reviewed baseline changed'
    # Retain the preceding release's reproducibility gate instead of silently
    # replacing its historical builder with a new source baseline.
    _,reproduced,_=previous_build(root)
    assert reproduced==original,'Previous source generation changed'
    source=root/'site-content/baba-nova';world=json.loads((source/'world.json').read_text())
    assert world['slug']=='baba-nova' and world['music']['releaseId']=='salad-chicken-baa'
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    assert len(cms['artists'])==13 and len(cms['releases'])==104
    artist=next(a for a in cms['artists'] if a['slug']=='baba-nova')
    files=dict(original);manifest=json.loads(original[MANIFEST]);routes=manifest['v6Routes']
    for route in routes:files[route]=extend(original[route].decode(),world).encode()
    # Only a bounded additional card; the original twelve cards remain intact.
    home=files['index.html'].decode();cards=list(re.finditer(r'<a class="world-card".*?</a>',home,re.S));assert len(cards)==12
    card='<a class="world-card" href="/worlds/baba-nova/" data-world-slug="baba-nova" data-world-route="worlds/baba-nova/" data-realm="celestial">'+scene('card-scene')+'<span class="card-shade"></span><div class="card-copy"><span class="eyebrow">WORLD 13 · '+escape(world['label'])+'</span><h3>BABA NOVA</h3><p>'+escape(world['world'])+'</p><span class="card-link">この世界へ <span aria-hidden="true">↗</span></span></div></a>'
    at=cards[-1].end();home=home[:at]+card+home[at:]
    selectors=list(re.finditer(r'<button[^>]*data-world-choice=.*?</button>',home,re.S));assert len(selectors)==12
    at=selectors[-1].end();home=home[:at]+'<button type="button" class="world-select" data-world-choice="baba-nova" aria-pressed="false"><span>13</span>BABA NOVA</button>'+home[at:]
    # The additional-artist invitation predates the thirteenth world. Keep its
    # profile and add a real world link without duplicating the artist record.
    ld=re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)',home,re.S);assert ld
    graph=json.loads(ld[2]);listing=next(n for n in graph['@graph'] if n.get('@id')=='https://www.suzukaofficial.com/#worlds');assert len(listing['itemListElement'])==12
    listing['itemListElement'].append({'@type':'ListItem','position':13,'name':'BABA NOVA','url':'https://www.suzukaofficial.com/worlds/baba-nova/'})
    home=home[:ld.start(2)]+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+home[ld.end(2):]
    files['index.html']=home.encode()
    page=files['worlds/rangili/index.html'].decode()
    head_end=page.index('</head>');head=page[:head_end]
    head=head.replace('worlds/rangili/','worlds/baba-nova/').replace('artists/rangili/','artists/baba-nova/').replace('RANGILI','BABA NOVA').replace('インドと日本、地上と宇宙を鮮やかな色彩で結ぶ祝祭の世界。',world['world']).replace('https://www.suzukaofficial.com/images/rangili-namaste-galaxy.jpg','https://www.suzukaofficial.com/'+world['officialImage']['path'])
    # Keep the independently approved controls, templates and portal dialog.
    controls=page[head_end+7:page.index('<main id="main">')]
    controls=controls.replace('data-artist="rangili"','data-artist="baba-nova"').replace('--world-glow:#88621d;--world-drift:14s','--world-glow:#bd483c;--world-drift:24s')
    petals=''.join('<i style="--left:'+str((i*17+5)%100)+'%;--time:'+str(19+i*2)+'s;--delay:-'+str(i*3)+'s"></i>' for i in range(10))
    lamps=''.join('<i class="baba-lantern" style="--left:'+str(x)+'%;--time:'+str(5+i)+'s"></i>' for i,x in enumerate([8,46,88,25,70]))
    img=world['officialImage'];image='<img src="/'+img['path']+'" alt="'+escape(img['alt'])+'" width="1280" height="720" decoding="async">'
    hero='<section class="hero world-hero" aria-labelledby="hero-title">'+scene().replace('loading="lazy"','loading="eager" fetchpriority="high"')+'<div class="hero-shade"></div><div class="baba-gold" aria-hidden="true"></div><div class="baba-lanterns" aria-hidden="true">'+lamps+'</div><div class="baba-petals" aria-hidden="true">'+petals+'</div><figure class="baba-poster">'+image+'<figcaption>OFFICIAL AUDIO · サラダチキン婆</figcaption></figure><div class="hero-copy"><p class="eyebrow">WORLD 13 / 13 · '+escape(world['label'])+'</p><h1 id="hero-title">BABA NOVA</h1><p class="world-intro">'+escape(world['world'])+'</p><a class="primary-link" href="#music">音楽と物語へ <span aria-hidden="true">↓</span></a></div></section>'
    story='<section class="artist-story" aria-labelledby="artist-story-title"><picture class="official-picture">'+image.replace('decoding="async"','loading="lazy" decoding="async"')+'</picture><div><p class="eyebrow">THE ARTIST</p><h2 id="artist-story-title">BABA NOVA</h2><p>'+escape(artist['profile'])+'</p><p>'+escape(artist['music'])+'</p><div class="story-links"><a href="/artists/baba-nova/">公式プロフィール ↗</a><a href="'+escape(artist['youtubeUrl'])+'">YouTube ↗</a><a href="/releases/salad-chicken-baa/">サラダチキン婆 ↗</a></div></div></section>'
    tracks=sorted([r for r in cms['releases'] if r['artistSlug']=='baba-nova'],key=lambda r:r['publishedAt'],reverse=True)
    music='<section class="music-section" id="music" aria-labelledby="music-title"><div class="section-heading"><div><p class="eyebrow">MUSIC & STORIES</p><h2 id="music-title">この世界に、響く音楽。</h2></div><p>2 WORKS · 作品、映像、配信へ。</p></div><div class="music-grid">'+''.join(track_html(r,'/',i==0,root) for i,r in enumerate(tracks))+'</div></section>'
    shorts=[s for s in cms['youtubeSnapshot']['shortVideos'] if s.get('artistSlug')=='baba-nova']
    end=page[page.index('<aside class="journey"'):]
    end=end.replace(world_link(),'')
    old_link='<a href="/worlds/rangili/" data-world-slug="rangili" data-world-route="worlds/rangili/">RANGILI <span aria-hidden="true">↗</span></a>'
    end=end.replace('<nav aria-label="他のアーティストの世界">','<nav aria-label="他のアーティストの世界">'+old_link,1)
    files[WORLD_ROUTE]=(head+'</head>'+controls+'<main id="main">'+hero+story+music+shorts_html(shorts,artist,'/')+end).encode()
    # New artist link is an additive package decoration; canonical profile,
    # artwork status, video history and all 104 release records stay untouched.
    name='artists/baba-nova/index.html';p=original[name].decode();assert '<main' in p
    pos=p.index('>',p.index('<main'))+1;p=p[:pos]+'<p class="container"><a href="/worlds/baba-nova/">CELESTIAL V6 · 宵桜の花街へ ↗</a></p>'+p[pos:];files[name]=p.encode()
    js=original['assets/cinematic-universe-v6.js'].decode()
    old="if (!Array.isArray(value.worlds) || value.worlds.length !== 12 || new Set(value.worlds.map(w => w.slug)).size !== 12) throw new Error('Invalid worlds');"
    assert js.count(old)==1
    new="const expected = ['asagiri-shinobu','asteria','eclypse','enomoto-mia','koga-kamishiro','michiru','nox','rangili','revive','veilfang','tetsuhige','leon-vail','baba-nova'];\n    if (!Array.isArray(value.worlds) || ![12,13].includes(value.worlds.length) || value.worlds.some((w,i) => w.slug !== expected[i]) || new Set(value.worlds.map(w => w.slug)).size !== value.worlds.length) throw new Error('Invalid worlds');"
    files['assets/cinematic-universe-v6.js']=js.replace(old,new).encode()
    files['assets/cinematic-universe-v6.css']=original['assets/cinematic-universe-v6.css']+b'\n'+(source/'world.css').read_bytes()
    for name in ['scene.svg','door.svg','salad-chicken-baa-official.jpg']:files['assets/baba-nova/'+name]=(source/name).read_bytes()
    # A separate symbol, leaving every original emblem byte-for-byte unchanged.
    emblem=original['assets/celestial-emblems.svg'].decode();assert emblem.endswith('</svg>') or emblem.endswith('</svg>\n')
    emblem=emblem.replace('</svg>','<symbol id="baba-nova" viewBox="0 0 100 100"><path d="M20 18h60M30 18v64m40-64v64M25 36h50M25 68h50" stroke="currentColor" fill="none" stroke-width="3"/><circle cx="50" cy="51" r="13" stroke="currentColor" fill="none" stroke-width="2"/></symbol></svg>');files['assets/celestial-emblems.svg']=emblem.encode()
    sitemap=original['sitemap.xml'].decode();assert 'worlds/baba-nova/' not in sitemap
    files['sitemap.xml']=sitemap.replace('</urlset>','<url><loc>https://www.suzukaofficial.com/worlds/baba-nova/</loc></url></urlset>').encode()
    manifest['v6Routes']=routes+[WORLD_ROUTE]
    manifest['thirteenthWorld']={'source':'site-content/baba-nova/world.json','baselineCommit':BASE,'artist':'baba-nova','releaseId':'salad-chicken-baa','officialImageRole':img['role']}
    info=copy.deepcopy(info);info['privateAudioApproval']['tracks'].append({'releaseId':'salad-chicken-baa','title':'サラダチキン婆','trackId':'baba-nova'})
    info['privateAudioApproval']['extensionApproval']={'source':'explicit-user-message','recordedAt':'2026-10-28','trackId':'baba-nova','releaseId':'salad-chicken-baa'}
    verify_private_audio(info,files,manifest['v6Routes'])
    assert set(original)<=set(files) and len(files)==806
    for n,d in original.items():
        if n.startswith(('assets/cinema/','assets/v6-media/','releases/')) or n in ['assets/v6-protected-audio.js','v6-audio-worker.js','music-production/index.html','assets/data/creator-cms.json']:assert files[n]==d,n
    manifest['files']={p:sha(d) for p,d in sorted(files.items()) if p!=MANIFEST}
    files[MANIFEST]=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    return info,files
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);m=p.add_mutually_exclusive_group(required=True);m.add_argument('--write',action='store_true');m.add_argument('--check',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    info,files=build(a.root);chunks=package(info,files)
    for n,d in chunks.items():
        path=a.root/'public-release'/n
        if a.check:assert path.read_bytes()==d,'Non-reproducible package: '+n
        else:path.write_bytes(d)
    if a.output:write_output(a.output,files)
    print(json.dumps({'status':'PASS','worlds':13,'artists':13,'works':104,'files':len(files),'deletions':0,'reproducible':bool(a.check)}))
if __name__=='__main__':main()

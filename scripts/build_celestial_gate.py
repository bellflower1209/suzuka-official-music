#!/usr/bin/env python3
"""Apply the presentation layer after canonical builders; never alter content records."""
from __future__ import annotations
import argparse, hashlib, html, json, re
from pathlib import Path


def e(value): return html.escape(str(value), quote=True)

def block(name, value):
    return f'<!-- CELESTIAL-GATE:{name}:START -->{value}<!-- CELESTIAL-GATE:{name}:END -->'

def clear(text):
    return re.sub(r'<!-- CELESTIAL-GATE:[A-Z-]+:START -->.*?<!-- CELESTIAL-GATE:[A-Z-]+:END -->', '', text, flags=re.S)


def validate(root, config, artists):
    if not 1500 <= config['durationMs'] <= 2500 or not 0 <= config['defaultVolume'] <= .5 or not 100 <= config['shortDurationMs'] <= 500:
        raise ValueError('Door timing or volume is outside the supported range.')
    if not all(re.fullmatch(r'[a-z0-9-]+', a['slug']) for a in artists):
        raise ValueError('Canonical artist slug is not URL-safe.')
    if set(config['themes']) != {a['slug'] for a in artists}:
        raise ValueError('Every canonical artist requires one presentation theme.')
    for slug, theme in config['themes'].items():
        if theme['realm'] != ('infernal' if slug == 'nox' else 'celestial'):
            raise ValueError('Only NOX can use the infernal realm.')
        for key in ['accent','tint']:
            if not re.fullmatch(r'#[0-9a-fA-F]{6}',theme[key]): raise ValueError('Invalid theme color')
    audio = config.get('doorAudio')
    if audio:
        path = (root / audio).resolve()
        if not path.is_relative_to(root.resolve()) or path.name != 'door-heavy-v2.wav':
            raise ValueError('Only the approved door-heavy-v2.wav is allowed inside the site.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != config.get('doorAudioSha256'):
            raise ValueError('Approved original audio hash is required.')
    return audio


def art(a, prefix):
    if a.get('image'):
        return f'<img src="{e(prefix+a["image"])}" alt="{e(a.get("imageAlt",a["name"]+" 公式ビジュアル"))}" width="{a.get("imageWidth",1280)}" height="{a.get("imageHeight",720)}" loading="lazy" decoding="async"/>'
    return f'<div class="cg-visual-pending"><span>OFFICIAL VISUAL</span><strong>IMAGE PENDING</strong><small>{e(a["name"])}の公式画像は確認中です。</small></div>'


def atlas(artists, config, prefix):
    cards=[]
    for i,a in enumerate(artists,1):
        t=config['themes'][a['slug']]
        cards.append(f'<a class="cg-world-card" href="{prefix}artists/{e(a["slug"])}/" data-cg-world="{e(a["slug"])}" data-cg-card-realm="{t["realm"]}" style="--world-accent:{t["accent"]};--world-tint:{t["tint"]}"><span class="cg-world-arch">{art(a,prefix)}<span class="cg-world-number">{i:02d} / {len(artists):02d}</span></span><span class="cg-world-copy"><small>{e(t["label"])}</small><strong>{e(a["name"])}</strong><span>{e(a["world"])}</span><b>扉を開く <span aria-hidden="true">↗</span></b></span></a>')
    return '<section class="cg-atlas" id="celestial-worlds" aria-labelledby="cg-worlds-title"><div class="cg-section-heading"><div><p class="cg-kicker">THE WORLDS BEYOND</p><h2 id="cg-worlds-title">音楽の、その先へ。</h2></div><p>ひとつの扉から、ひとつの世界へ。<br/>あなたの心に響くアーティストを見つけて。</p></div><div class="cg-world-grid">'+''.join(cards)+'</div></section>'


def settings(audio):
    label='音声 OFF' if audio else '音源未登録'
    return '<details class="cg-settings"><summary>体験設定 <span aria-hidden="true">✧</span></summary><div class="cg-settings-panel"><p>GATE EXPERIENCE</p><button type="button" data-cg-sound aria-pressed="false"'+('' if audio else ' disabled')+'>'+label+'</button><label>効果音の音量<input type="range" data-cg-volume min="0" max="0.5" step="0.01" value="0.24" aria-label="扉の効果音の音量"/></label><label class="cg-check"><input type="checkbox" data-cg-short/>演出を短くする</label><small data-cg-sound-note>'+('音声は選択した扉でのみ再生します。楽曲再生中は効果音を抑えます。' if audio else '正式な重低音Ver.2が未登録です。扉は無音で開きます。')+'</small></div></details>'


def build(root):
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    config=json.loads((root/'assets/data/celestial-gate.json').read_text())
    artists=[a for a in cms['artists'] if a.get('status')=='published']
    audio=validate(root,config,artists)
    by_slug={a['slug']:a for a in artists}
    runtime={k:config[k] for k in ['durationMs','shortDurationMs','defaultVolume','doorAudio']}
    runtime['artists']={a['slug']:{'name':a['name'],'slug':a['slug'],**config['themes'][a['slug']]} for a in artists}
    encoded=json.dumps(runtime,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    count=0
    for path in sorted(root.rglob('*.html')):
        if path.name not in {'index.html', '404.html'}: continue
        if any(x in path.parts for x in ['.git','_site','node_modules']): continue
        text=path.read_text(encoding='utf-8')
        if '<body' not in text: continue
        relative=path.relative_to(root); prefix='../'*(len(relative.parts)-1) or './'
        slug=relative.parts[1] if len(relative.parts)==3 and relative.parts[0]=='artists' else None
        theme=config['themes'].get(slug,{})
        realm=theme.get('realm','celestial')
        text=clear(text)
        text=re.sub(r'\sdata-cg-(?:realm|artist)="[^"]*"','',text)
        text=re.sub(r'\sstyle="--cg-accent:[^"]*"','',text)
        attrs=f' data-cg-realm="{realm}"'
        if slug in by_slug:
            attrs+=f' data-cg-artist="{slug}" style="--cg-accent:{theme["accent"]};--cg-tint:{theme["tint"]}"'
        text=re.sub(r'<body\b', '<body'+attrs,text,count=1)
        text=text.replace('</head>', block('ASSETS',f'<link rel="icon" type="image/jpeg" href="{prefix}images/suzuka-channel.jpg"/><link rel="stylesheet" href="{prefix}assets/celestial-gate.css"/><script defer src="{prefix}assets/celestial-gate.js"></script><script type="application/json" id="cg-config">{encoded}</script>')+'</head>',1)
        scenery='<div class="cg-atmosphere" aria-hidden="true"><div class="cg-rays"></div><div class="cg-cloud cg-cloud-one"></div><div class="cg-cloud cg-cloud-two"></div>'+('<div class="cg-red-moon"></div><div class="cg-black-flames"></div>' if realm=='infernal' else '')+'</div>'
        text=re.sub(r'(<body\b[^>]*>)',lambda m:m[0]+block('ATMOSPHERE',scenery),text,count=1)
        text=text.replace('</header>','</header>'+block('SETTINGS',settings(audio)),1)
        if relative.as_posix()=='index.html':
            hero=f'<section class="cg-home-hero" aria-labelledby="cg-title"><div class="cg-hero-copy"><p class="cg-kicker">AN ORIGINAL MUSIC UNIVERSE</p><p class="cg-wordmark" id="cg-title">SUZUKA</p><p class="cg-gate-title">CELESTIAL GATE</p><h2>{e(config["concept"])}</h2><p class="cg-hero-lead">雲の向こうに、まだ知らない音楽がある。<br/>光の扉を開いて、あなたの物語へ。</p><div class="cg-hero-actions"><a href="#celestial-worlds" class="cg-primary">世界を選ぶ <span aria-hidden="true">↓</span></a><a href="./search/">音楽を探す <span aria-hidden="true">↗</span></a></div></div><div class="cg-coordinate" aria-hidden="true"><span>CELESTIAL REALM / EST. SUZUKA</span><span>{len(artists):02d} WORLDS · ONE UNIVERSE</span></div></section>'
            # Retain the canonical release H1 and full latest-release Hero below the new gateway.
            text=text.replace(block('SETTINGS',settings(audio)),block('SETTINGS',settings(audio))+block('HOME',hero+atlas(artists,config,prefix)),1)
        if slug in by_slug:
            return_link=f'<a class="cg-return" data-cg-return href="{prefix}">← '+('天界へ帰還する' if realm=='infernal' else '天界の入口へ')+'</a>'
            emblem=f'<svg class="cg-domain-emblem" viewBox="0 0 64 64" aria-hidden="true"><use href="{prefix}assets/celestial-emblems.svg#{slug}"/></svg>'
            intro=f'<aside class="cg-realm-intro" aria-label="アーティストの領域">{return_link}<span>{e(theme["label"])} / '+('INFERNAL REALM' if realm=='infernal' else 'CELESTIAL REALM')+f'</span><small>{e(theme["motif"])}</small>{emblem}</aside>'
            text=text.replace('<section class="explorer-hero"',block('REALM',intro)+'<section class="explorer-hero"',1)
        if relative.as_posix()=='artists/index.html':
            intro='<section class="cg-directory-intro"><p class="cg-kicker">CHOOSE YOUR GATE</p><h2>扉の向こうで、音楽が待っている。</h2><p>公式アーティストの世界へ。NOXの扉だけは、深紅の魔界につながっています。</p></section>'
            text=text.replace('<section class="v31-artist-directory"',block('DIRECTORY',intro)+'<section class="v31-artist-directory"',1)
            # Decorate canonical directory cards without replacing their contents or links.
            for a in artists:
                t=config['themes'][a['slug']]
                marker=f'<article class="v31-artist-directory-card"><a href="./{a["slug"]}/">'
                decorated=f'<article class="v31-artist-directory-card" data-cg-card-realm="{t["realm"]}" style="--world-accent:{t["accent"]};--world-tint:{t["tint"]}"><a href="./{a["slug"]}/"><span class="cg-directory-label">{e(t["label"])}</span>'
                text=text.replace(marker,decorated)
        footer=f'<p class="cg-footer-signature">{e(config["name"])} <span>{e(config["concept"])}</span></p>'
        text=text.replace('</footer>',block('SIGNATURE',footer)+'</footer>',1)
        # Cover static pages without a legacy header too.
        if 'CELESTIAL-GATE:SETTINGS:START' not in text:
            text=text.replace('</body>',block('SETTINGS',settings(audio))+'</body>')
        path.write_text(text,encoding='utf-8');count+=1
    print(f'Celestial Gate: {count} HTML pages, {len(artists)} canonical worlds, audio '+('verified' if audio else 'pending (silent fallback)')+'.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);build(p.parse_args().root.resolve())

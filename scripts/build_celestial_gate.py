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
    if not 3500 <= config['durationMs'] <= 6000 or not 0 <= config['defaultVolume'] <= .5 or not 100 <= config['shortDurationMs'] <= 500:
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
    candidate = config.get('candidateAudio')
    if candidate:
        path = (root / candidate).resolve()
        if not path.is_relative_to(root.resolve()) or path.name != 'door-heavy-candidate-v4.wav' or config.get('candidateAudioStatus') != 'new-candidate-not-adopted':
            raise ValueError('Candidate must remain explicitly unadopted and separate from Ver.2.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != config.get('candidateAudioSha256'):
            raise ValueError('Candidate audio hash mismatch.')
    times = list(config['timeline'].values())
    if times != sorted(set(times)) or times[0] <= 0 or times[-1] >= config['durationMs']:
        raise ValueError('Portal phases must be ordered inside the total duration.')
    return audio or candidate


def art(a, prefix):
    if a.get('image'):
        variants=f'{prefix}assets/cinema/official/{a["slug"]}-480.webp 480w, {prefix}assets/cinema/official/{a["slug"]}-960.webp 960w'
        return f'<img class="cg-official-image" src="{e(prefix+a["image"])}" srcset="{e(variants)}" sizes="(max-width:640px) 60vw, 260px" alt="{e(a.get("imageAlt",a["name"]+" 公式ビジュアル"))}" width="{a.get("imageWidth",1280)}" height="{a.get("imageHeight",720)}" loading="lazy" decoding="async"/>'
    return f'<div class="cg-visual-pending"><span>OFFICIAL VISUAL</span><strong>IMAGE PENDING</strong><small>{e(a["name"])}の公式画像は確認中です。</small></div>'


def scenery(key, prefix, *, portal=False, priority=False, label=None):
    base=f'{prefix}assets/cinema/{key}'
    attrs='loading="eager" fetchpriority="high"' if priority else 'loading="lazy" fetchpriority="low"'
    if portal:
        sources=f'<source type="image/avif" srcset="{base}-mobile.avif"/>'
        src=f'{base}-mobile.webp';width,height=628,941
    else:
        sources=''.join(f'<source media="(max-width:640px)" type="image/{fmt}" srcset="{base}-mobile.{fmt}"/>' for fmt in ['avif','webp'])
        sources+=f'<source type="image/avif" srcset="{base}-768.avif 768w, {base}-1280.avif 1280w, {base}-1600.avif 1600w" sizes="100vw"/>'
        src=f'{base}-1600.webp';width,height=1600,900
    description=label or ('黒曜石の城と深紅の月' if key=='nox' else '雲海に浮かぶ天空宮殿' if key=='hero' else '音楽の世界を表現した宮殿')
    return f'<picture class="cg-scene" aria-hidden="true">{sources}<img src="{src}" alt="{e(description)}の装飾背景（AI生成）" width="{width}" height="{height}" {attrs} decoding="async"/></picture>'


def portal(a, theme, prefix, portrait=None):
    # The threshold, hinges, floor and world are photographed in one plate.
    # Avoid a detached arch cutout or a portrait composited as a fictional actor.
    return f'<span class="cg-world-stage">{scenery(theme["background"],prefix,label=theme["label"])}</span><span class="cg-official-inset">{portrait or art(a,prefix)}</span>'


def validate_cinema(root, config, artists):
    manifest=json.loads((root/config['cinema']['manifest']).read_text())
    items={i['id']:i for i in manifest['assets']}
    expected={'hero','gallery-hall','door-celestial','door-infernal','frame-celestial','frame-infernal',*(a['slug'] for a in artists)}
    if set(items)!=expected:raise ValueError('Every artist and physical gate requires its own cinematic asset.')
    for a in artists:
        if config['themes'][a['slug']]['background']!=a['slug']:raise ValueError('Artist background must match its recorded asset.')
    for item in [*items.values(),*manifest['officialThumbnails']]:
        for v in item['variants']:
            path=(root/v['path']).resolve()
            if not path.is_relative_to((root/'assets/cinema').resolve()) or not path.is_file():raise ValueError('Cinematic asset missing or outside its asset folder.')
    return manifest


def atlas(artists, config, prefix):
    cards=[]
    for i,a in enumerate(artists,1):
        t=config['themes'][a['slug']]
        cards.append(f'<a class="cg-world-card" href="{prefix}artists/{e(a["slug"])}/" data-cg-world="{e(a["slug"])}" data-cg-card-realm="{t["realm"]}" style="--world-accent:{t["accent"]};--world-tint:{t["tint"]}"><span class="cg-world-number">WORLD {i:02d} / {len(artists):02d}</span>{portal(a,t,prefix)}<span class="cg-world-copy"><small>{e(t["label"])}</small><strong>{e(a["name"])}</strong><span>{e(a["world"])}</span><b>扉を開く <span aria-hidden="true">↗</span></b></span></a>')
    return '<section class="cg-atlas" id="celestial-worlds" aria-labelledby="cg-worlds-title"><div class="cg-hall">'+scenery('gallery-hall',prefix)+'<div class="cg-section-heading"><div><p class="cg-kicker">THE WORLDS BEYOND</p><h2 id="cg-worlds-title">音楽の、その先へ。</h2></div><p>ひとつの扉から、ひとつの世界へ。<br/>あなたの心に響くアーティストを見つけて。</p></div></div><div class="cg-world-grid">'+''.join(cards)+'</div></section>'


def settings(audio):
    label=('音声 OFF' if audio.endswith('door-heavy-v2.wav') else '候補音声 OFF') if audio else '音源未登録'
    return '<details class="cg-settings"><summary>体験設定 <span aria-hidden="true">✧</span></summary><div class="cg-settings-panel"><p>GATE EXPERIENCE</p><button type="button" data-cg-sound aria-pressed="false"'+('' if audio else ' disabled')+'>'+label+'</button><label>効果音の音量<input type="range" data-cg-volume min="0" max="0.5" step="0.01" value="0.24" aria-label="扉の効果音の音量"/></label><label class="cg-check"><input type="checkbox" data-cg-short/>演出を短くする</label><small data-cg-sound-note>'+(('音声は選択した扉でのみ再生します。楽曲再生中は効果音を抑えます。' if audio.endswith('door-heavy-v2.wav') else '正式Ver.2は未登録です。新規候補の試聴は任意です。正式採用済みではありません。') if audio else '正式な重低音Ver.2が未登録です。扉は無音で開きます。')+'</small></div></details>'


def build(root):
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    config=json.loads((root/'assets/data/celestial-gate.json').read_text())
    artists=[a for a in cms['artists'] if a.get('status')=='published']
    audio=validate(root,config,artists)
    validate_cinema(root,config,artists)
    by_slug={a['slug']:a for a in artists}
    runtime={k:config[k] for k in ['durationMs','shortDurationMs','defaultVolume','doorAudio','doorAudioStatus','candidateAudio','candidateAudioStatus','timeline','arrivalMs']}
    runtime['artists']={a['slug']:{'name':a['name'],'slug':a['slug'],**config['themes'][a['slug']]} for a in artists}
    runtime['cinema']=config['cinema']
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
        if path.name == '404.html':
            # Pages serves this document at arbitrary missing URL depths.
            # Relative resources would resolve below that missing directory.
            prefix='/'
            text=re.sub(r'((?:href|src)=")(?!(?:[a-z]+:|/|#))([^"\s]+)', r'\1/\2', text, flags=re.I)
        if relative.as_posix() == 'index.html':
            # These belong to the former first viewport, now below the twelve-world atlas.
            # Retain the artwork/MV in content while reserving preload bandwidth for the palace.
            text=re.sub(r'<link\b(?=[^>]*rel="preload")(?=[^>]*as="image")(?=[^>]*href="(?:https://i\.ytimg\.com/|\./images/))[^>]*>', '', text, flags=re.I)
            def below_fold_image(match):
                tag=re.sub(r'\s(?:loading|fetchpriority)="[^"]*"', '', match[0], flags=re.I)
                return re.sub(r'/?>$', ' loading="lazy" fetchpriority="low"/>', tag)
            text=re.sub(r'<img\b[^>]*>', below_fold_image, text, flags=re.I)
        text=re.sub(r'\sdata-cg-(?:realm|artist|page)="[^"]*"','',text)
        text=re.sub(r'\sstyle="--cg-accent:[^"]*"','',text)
        page_kind='home' if relative.as_posix()=='index.html' else 'artist' if slug in by_slug else 'directory' if relative.as_posix()=='artists/index.html' else 'content'
        attrs=f' data-cg-realm="{realm}" data-cg-page="{page_kind}"'
        if slug in by_slug:
            attrs+=f' data-cg-artist="{slug}" style="--cg-accent:{theme["accent"]};--cg-tint:{theme["tint"]}"'
        text=re.sub(r'<body\b', '<body'+attrs,text,count=1)
        environment='gallery-hall' if page_kind=='directory' else theme.get('background','hero')
        preload=block('PRELOAD',f'<link rel="preload" as="style" href="{prefix}assets/celestial-gate.css"/><link rel="preload" as="image" type="image/avif" media="(max-width:640px)" href="{prefix}assets/cinema/{environment}-mobile.avif" fetchpriority="high"/><link rel="preload" as="image" type="image/avif" media="(min-width:641px)" imagesrcset="{prefix}assets/cinema/{environment}-768.avif 768w, {prefix}assets/cinema/{environment}-1280.avif 1280w, {prefix}assets/cinema/{environment}-1600.avif 1600w" imagesizes="100vw" fetchpriority="high"/>')
        if '<!-- SUZUKA:GA4:END -->' in text:
            # The analytics builder adds a trailing newline when it refreshes its
            # block. Normalize only that boundary so repeated builds stay identical.
            text=re.sub(r'<!-- SUZUKA:GA4:END -->\s*',lambda m:'<!-- SUZUKA:GA4:END -->'+preload+'\n',text,count=1)
        else:
            text=text.replace('<head>','<head>'+preload,1)
        text=text.replace('</head>', block('ASSETS',f'<script>(function(){{try{{var k="suzuka.cg.arrival",s=JSON.parse(sessionStorage.getItem(k)||"null");sessionStorage.removeItem(k);if(s&&s.path===location.pathname&&Date.now()-s.time<15000&&s.time<=Date.now()&&/^[a-z0-9-]+$/.test(s.background)){{window.__cgArrival=s;document.documentElement.dataset.cgArrival=s.realm==="infernal"?"infernal":"celestial";}}}}catch(e){{}}}})();</script><link rel="icon" type="image/jpeg" href="{prefix}images/suzuka-channel.jpg"/><link rel="stylesheet" href="{prefix}assets/celestial-gate.css"/><script defer src="{prefix}assets/celestial-gate.js"></script><script type="application/json" id="cg-config">{encoded}</script>')+'</head>',1)
        atmosphere='<div class="cg-atmosphere" aria-hidden="true"></div>'
        text=re.sub(r'(<body\b[^>]*>)',lambda m:m[0]+block('ATMOSPHERE',atmosphere),text,count=1)
        text=text.replace('</header>','</header>'+block('SETTINGS',settings(audio)),1)
        primary_nav=re.search(r'<nav class="desktop-nav"[^>]*>(.*?)</nav>',text,re.S)
        if primary_nav:
            menu=re.search(r'(<nav aria-label="(?:モバイルナビゲーション|サイト全体のナビゲーション)">)(.*?)(</nav>)',text,re.S)
            if menu:
                links=re.findall(r'<a\b[^>]*>.*?</a>',menu[2],re.S)
                hrefs={re.search(r'href="([^"]+)"',a)[1] for a in links}
                for link in re.findall(r'<a\b[^>]*>.*?</a>',primary_nav[1],re.S):
                    if re.search(r'href="([^"]+)"',link)[1] not in hrefs:links.append(link)
                text=text[:menu.start()]+'<nav aria-label="サイト全体のナビゲーション">'+''.join(links)+'</nav>'+text[menu.end():]
        if relative.as_posix()=='index.html':
            hero=f'<section class="cg-home-hero" aria-labelledby="cg-title">{scenery("hero",prefix,priority=True)}<div class="cg-hero-copy"><p class="cg-kicker">AN ORIGINAL MUSIC UNIVERSE</p><p class="cg-wordmark" id="cg-title">SUZUKA</p><p class="cg-gate-title">CELESTIAL GATE</p><h2>{e(config["concept"])}</h2><div class="cg-hero-actions"><a href="#celestial-worlds" class="cg-primary">十二の世界へ <span aria-hidden="true">↓</span></a><a href="./search/">音楽を探す <span aria-hidden="true">↗</span></a></div></div><div class="cg-coordinate" aria-hidden="true"><span>CELESTIAL REALM</span><span>{len(artists):02d} WORLDS · ONE UNIVERSE</span></div></section>'
            # Retain the canonical release H1 and full latest-release Hero below the new gateway.
            text=text.replace(block('SETTINGS',settings(audio)),block('SETTINGS',settings(audio))+block('HOME',hero+atlas(artists,config,prefix)),1)
        if page_kind in {'artist','directory'}:
            season=re.search(r'<!-- SUZUKA:HALLOWEEN:START -->.*?<!-- SUZUKA:HALLOWEEN:END -->',text,re.S)
            if season and '<div id="content">' in text:
                notice=season[0]
                text=text[:season.start()]+text[season.end():]
                text=text.replace('<div id="content">','<div id="content">'+notice,1)
        if slug in by_slug:
            # Keep existing release/karaoke announcements intact, below the world
            # entrance. Their canonical generator may insert them before the hero.
            announcement=re.search(r'<!-- streaming-release:start -->.*?<!-- streaming-release:end -->',text,re.S)
            if announcement and '<div id="content">' in text:
                notice=announcement[0]
                text=text[:announcement.start()]+text[announcement.end():]
                text=text.replace('<div id="content">','<div id="content">'+notice,1)
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
                pattern=rf'(<article class="v31-artist-directory-card"[^>]*><a href="\./{re.escape(a["slug"])}/">)(.*?)(</a></article>)'
                def directory_portal(match):
                    contents=match[2]
                    image=re.search(r'<img\b[^>]*>',contents)
                    if image:
                        portrait=image[0].replace(' src=',f' srcset="{prefix}assets/cinema/official/{a["slug"]}-480.webp 480w, {prefix}assets/cinema/official/{a["slug"]}-960.webp 960w" sizes="(max-width:640px) 60vw, 260px" src=',1)
                        contents=contents[:image.start()]+contents[image.end():]
                    else:
                        pending=re.search(r'<div class="v31-artist-image-placeholder".*?</div>',contents,re.S)
                        portrait=pending[0] if pending else None
                        if pending:contents=contents.replace(pending[0],'',1)
                    return match[1]+portal(a,t,prefix,portrait)+contents+match[3]
                text=re.sub(pattern,directory_portal,text,flags=re.S)
        # Photographic hero environments keep all canonical headings and copy.
        environment=slug if slug in by_slug else 'gallery-hall' if page_kind=='directory' else 'hero'
        priority=relative.parts[0]!='gallery'
        text=re.sub(r'(<section class="(?:explorer-hero|directory-hero|artists-index-hero|artist-profile-hero)"[^>]*>)',lambda m:m[0]+block('SCENE',scenery(environment,prefix,priority=priority,label=theme.get('label'))),text,count=1)
        text=text.replace('<p class="section-kicker">SUZUKA EXPLORER UPDATE</p>','<p class="section-kicker">SUZUKA MUSIC UNIVERSE</p>')
        if 'CELESTIAL-GATE:SCENE:START' not in text and page_kind!='home':
            band=block('CINEMA-BAND','<div class="cg-film-masthead" aria-hidden="true">'+scenery('hero',prefix,priority=priority)+'</div>')
            if '<main' in text:text=re.sub(r'(<main\b[^>]*>)',lambda m:m[0]+band,text,count=1)
            else:text=text.replace(block('SETTINGS',settings(audio)),block('SETTINGS',settings(audio))+band,1)
        footer=f'<p class="cg-footer-signature">{e(config["name"])} <span>{e(config["concept"])}</span></p>'
        text=text.replace('</footer>',block('SIGNATURE',footer)+'</footer>',1)
        # Cover static pages without a legacy header too.
        if 'CELESTIAL-GATE:SETTINGS:START' not in text:
            text=text.replace('</body>',block('SETTINGS',settings(audio))+'</body>')
        path.write_text(text,encoding='utf-8');count+=1
    print(f'Celestial Gate: {count} HTML pages, {len(artists)} canonical worlds, audio '+('formal Ver.2 verified' if config.get('doorAudio') else 'new candidate available; formal Ver.2 pending' if audio else 'pending (silent fallback)')+'.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);build(p.parse_args().root.resolve())

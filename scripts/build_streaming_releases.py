#!/usr/bin/env python3
"""Render verified streaming metadata without replacing existing MV publication history."""
import html
import json
import re
from pathlib import Path

BASE = 'https://www.suzukaofficial.com/'
MARKER = re.compile(r'<!-- streaming-release:start -->.*?<!-- streaming-release:end -->', re.S)


def panel(item, prefix):
    s = item['streamingRelease']
    esc = html.escape
    year, month, day = map(int, s['releaseDate'].split('-'))
    japanese_date = f'{year}年{month}月{day}日'
    display_date = s['releaseDate'].replace('-', '.')
    return ('<!-- streaming-release:start --><section class="streaming-release" aria-label="Streaming Release">'
            '<div><p class="streaming-kicker">STREAMING RELEASE</p>'
            f'<p class="streaming-status" data-streaming-date="{esc(s["releaseDate"])}" aria-live="polite">{japanese_date}リリース</p>'
            f'<h2>{esc(item["title"])}</h2><p class="streaming-artist">{esc(item["artist"])}</p>'
            f'<p><time datetime="{s["releaseDate"]}">{display_date}</time> — {japanese_date} 配信開始</p>'
            f'<p class="streaming-credit">Label：{esc(s["label"])}<br>Distributed via {esc(s["distributor"])}</p></div>'
            '<div class="streaming-actions">'
            f'<a class="streaming-primary" href="{esc(s["linkcoreUrl"])}" target="_blank" rel="noopener noreferrer">配信サービスで聴く ↗</a>'
            f'<a href="{prefix}{item["releaseUrl"]}">作品情報・MVを見る</a>'
            '<p>各サービスで順次配信予定。<br>配信状況はLinkCoreでご確認ください。</p></div>'
            '</section><!-- streaming-release:end -->')


def build_news(item, artist, release, renderer):
    text = renderer(item, artist)
    # The news uses the site brand OGP; no unverified jacket is presented.
    text = re.sub(r'<section><img[^>]+/></section>', panel(release, '../../'), text, count=1)
    return text


def build(root):
    cms = json.loads((root / 'assets/data/creator-cms.json').read_text())
    releases = {r['title']: r for r in cms['releases'] if r.get('streamingRelease')}
    for item in releases.values():
        routes = ['index.html', item['releaseUrl']+'index.html',
                  'artists/'+item['artistSlug']+'/index.html', 'releases/index.html',
                  'news/'+item['slug']+'-streaming-release/index.html']
        for route in routes:
            path = root / route
            prefix = '../' * (len(Path(route).parts)-1) or './'
            text = MARKER.sub('', path.read_text())
            if route == item['releaseUrl']+'index.html':
                text = re.sub(r'OFFICIAL RELEASE · \d{4}-\d{2}-\d{2}', 'STREAMING RELEASE · '+item['streamingRelease']['releaseDate'], text)
                description = html.escape(item['seo']['description'], quote=True)
                text = re.sub(r'(<meta (?:name="(?:description|twitter:description)"|property="og:description") content=")[^"]*("/?>)', lambda m:m[1]+description+m[2], text)
            block = panel(item, prefix)
            if route == 'index.html':
                text, count = re.subn(r'(<section\b[^>]*data-home-hero[^>]*>.*?</section>)', lambda m:m[0]+block, text, count=1, flags=re.S)
            elif route == item['releaseUrl']+'index.html':
                text, count = re.subn(r'(<section class="release-detail-hero")', block+r'\1', text, count=1)
                if count != 1:
                    raise ValueError(f'Missing streaming insertion point: {route}')
                credits = '<section class="release-credit-section" aria-label="作品クレジット"><h2>CREDITS</h2><dl><div><dt>作詞</dt><dd>JUN</dd></div><div><dt>作曲</dt><dd>SUNO×JUN</dd></div><div><dt>アーティスト</dt><dd>榎本魅愛</dd></div></dl></section>'
                if 'release-credit-section' in text:
                    text = re.sub(r'<section class="release-credit-section".*?</section>', credits, text, count=1, flags=re.S)
                else:
                    text, count = re.subn(r'(<section class="v31-release-lyrics-link")', credits+r'\1', text, count=1)
                    if count != 1:
                        raise ValueError(f'Missing credits insertion point: {route}')
            elif route.startswith('news/'):
                text, count = re.subn(r'(<div class="news-article-body">)', lambda m:m[0]+block, text, count=1)
            else:
                text, count = re.subn(r'(<section\b)', lambda m:block+m[0], text, count=1)
            if count != 1:
                raise ValueError(f'Missing streaming insertion point: {route}')
            for asset in ['streaming-release.css', 'streaming-release.js']:
                if f'assets/{asset}' not in text:
                    tag = (f'<link rel="stylesheet" href="{prefix}assets/{asset}"/>' if asset.endswith('.css')
                           else f'<script defer src="{prefix}assets/{asset}"></script>')
                    text = text.replace('</head>', tag+'</head>', 1)
            path.write_text(text)
    # Update each existing recording node consistently, retaining its canonical entity ID.
    def patch(match):
        data = json.loads(match[1])
        def walk(node):
            if isinstance(node, list):
                for child in node: walk(child)
            elif isinstance(node, dict):
                if node.get('@type') == 'MusicRecording' and node.get('name') in releases:
                    item = releases[node['name']]; s = item['streamingRelease']
                    node.update(datePublished=s['releaseDate'], genre=s['genre'],
                                recordLabel={'@id':BASE+'#organization','name':s['label']})
                    node.pop('sameAs', None)
                    node.setdefault('byArtist', {})['name'] = item['artist']
                for child in node.values(): walk(child)
        walk(data)
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(',',':'))+'</script>'
    for path in sorted(root.rglob('index.html')):
        if 'admin' in path.relative_to(root).parts: continue
        text = path.read_text()
        text = re.sub(r'<script type="application/ld\+json">(.*?)</script>', patch, text, flags=re.S)
        path.write_text(text)

"""Canonical activity sections, using the existing published cinematic markup only."""
import html
import re
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

class Dimensions(HTMLParser):
    def __init__(self, source):super().__init__();self.source=source;self.size=None
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='img' and d.get('src')==self.source and d.get('width') and d.get('height'):
            self.size=(int(d['width']),int(d['height']))

def content_image(image,alt,prefix,root,images=None,*,cls='',sizes='',reference=None):
    image=safe_url(image)
    if urlsplit(image).scheme:
        parser=Dimensions(image);parser.feed((root/reference).read_text())
        if not parser.size:raise ValueError('Missing verified image dimensions: '+image)
        width,height=parser.size;src=image
    else:
        with Image.open(root/image) as original:width,height=original.size
        src=prefix+image
    return f'<picture class="official-picture"><img src="{e(src)}" alt="{e(alt)}" width="{width}" height="{height}" style="aspect-ratio:{width}/{height}" loading="lazy" decoding="async"></picture>'

def e(value):
    return html.escape(str(value or ''), quote=True)

def safe_url(value):
    value = str(value or '')
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme != 'https':
        raise ValueError(f'Unsupported public link scheme: {parsed.scheme}')
    if not parsed.scheme and (value.startswith('//') or '..' in Path(parsed.path).parts):
        raise ValueError('Unsafe relative content path')
    return value

def link(url, label, prefix='', cls='', world=None):
    url = safe_url(url)
    if not url:
        return ''
    href = url if urlsplit(url).scheme or url.startswith('#') else prefix + url
    return f'<a href="{e(href)}"' + (f' data-world-slug="{e(world)}" data-world-route="v6/worlds/{e(world)}.html"' if world else '') + (f' class="{cls}"' if cls else '') + f'>{e(label)} <span aria-hidden="true">↗</span></a>'

def track_html(r, prefix, latest=False, root=ROOT, images=None):
    slug = r['slug']
    route = safe_url(r.get('releaseUrl') or f'releases/{slug}/')
    image = r.get('coverImage') or r.get('image')
    cover = content_image(image,r.get('coverAlt',r['title']+' 登録作品画像'),prefix,root,images,reference=route+'index.html') if image else '<span class="image-pending">作品画像確認中</span>'
    links = [link(route, '作品ページ', prefix)]
    if r.get('youtubeUrl'):
        links.append(link(r['youtubeUrl'], r.get('videoButtonLabel') or r.get('videoCtaLabel') or 'YouTube'))
    seen = {r.get('youtubeUrl')}
    for v in r.get('videoVersions', []):
        if v.get('youtubeUrl') and v['youtubeUrl'] not in seen:
            links.append(link(v['youtubeUrl'], v.get('label') or '関連映像'))
            seen.add(v['youtubeUrl'])
    if r.get('shortsUrl'):
        links.append(link(r['shortsUrl'], 'Shorts'))
    if r.get('lyricsAvailable') and (root / 'lyrics' / slug / 'index.html').is_file():
        links.append(link(f'lyrics/{slug}/', '歌詞', prefix))
    stream = r.get('scheduledStreamingRelease') or r.get('streamingRelease') or {}
    if stream.get('linkcoreUrl'):
        links.append(link(stream['linkcoreUrl'], '配信サービス' if stream.get('status') == 'published' else '配信情報'))
    date = (r.get('publishedAt') or '')[:10] or r.get('releaseDate') or ''
    date_label = '配信開始日' if r.get('publicationEvidenceType') == 'verified-streaming-only' else ('公開日' if r.get('publishedAt') else '登録日付')
    note = ('<span class="latest-label">最新の公開作品</span>' if latest else '')
    if r.get('imageRole') == 'official-youtube-thumbnail':
        note += '<span class="release-state">映像サムネイル'+(' · 正式ジャケット確認待ち' if r.get('artworkStatus') == 'pending-formal-jacket' else '')+'</span>'
    if stream.get('status') in {'scheduled', 'upcoming'}:
        note += f'<span class="release-state">配信予定：{e(stream.get("releaseDate"))}</span>'
    elif stream.get('status') == 'published':
        note += '<span class="release-state">配信中'+(f' · {e(stream["releaseDate"])}' if stream.get('releaseDate') else '')+'</span>'
    return f'<article class="track" data-release-id="{e(r["id"])}"><a class="cover" href="{e(prefix + route)}">{cover}</a><div class="track-copy">{note}<h3>{link(route,r.get("displayTitle") or r["title"],prefix)}</h3><p class="track-meta">{e(r["artist"])}'+(f' · {date_label} <time datetime="{e(date)}">{e(date)}</time>' if date else '')+f'</p><div class="track-links">{"".join(links)}</div></div></article>'

def note_news_html(news, prefix, root, *, title_id):
    """Only explicitly published canonical note announcements; no identity inference."""
    if not news:
        return ''
    cards = []
    for item in news:
        slug = item['slug']
        if not re.fullmatch(r'[a-z0-9-]+', slug) or not (root/'news'/slug/'index.html').is_file():
            raise ValueError('Published note announcement requires its existing canonical news page')
        date = (item.get('publishedAt') or '')[:10]
        cards.append(f'<article class="track-copy" data-note-news="{e(slug)}"><p class="eyebrow">OFFICIAL NOTE</p><h3>{link("news/"+slug+"/",item["title"],prefix)}</h3>'+(f'<p class="track-meta">公開日 <time datetime="{e(date)}">{e(date)}</time></p>' if date else '')+f'<div class="track-links">{link(item["noteUrl"],"noteで読む")}{link("news/"+slug+"/","公式NEWS",prefix)}</div></article>')
    return f'<section class="music-section" aria-labelledby="{title_id}"><div class="section-heading"><div><p class="eyebrow">NEWS & STORIES</p><h2 id="{title_id}">音楽の、その先の物語。</h2></div><p>{link("news/","すべての公式NEWS",prefix)}</p></div><div class="music-grid">{"".join(cards)}</div></section>'

def shorts_html(shorts, artist, prefix):
    if not shorts:
        return ''
    cards = []
    for item in shorts:
        video_id = item['videoId']
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise ValueError('Canonical Shorts ID is invalid')
        date = (item.get('publishedAt') or '')[:10]
        cards.append(f'<article class="track-copy" data-short-id="{e(video_id)}"><p class="eyebrow">OFFICIAL SHORTS</p><h3>{link(item["youtubeUrl"],item["title"])}</h3>'+(f'<p class="track-meta">公開日 <time datetime="{e(date)}">{e(date)}</time></p>' if date else '')+f'<div class="track-links">{link(item["youtubeUrl"],"YouTubeで見る")}{link("artists/"+artist["slug"]+"/","公式アーティストページ",prefix)}</div></article>')
    return '<section class="music-section" aria-labelledby="shorts-title"><div class="section-heading"><div><p class="eyebrow">MOMENTS FROM THIS WORLD</p><h2 id="shorts-title">音楽と出会う、短い物語。</h2></div>'+f'<p>{len(shorts)} OFFICIAL SHORTS</p></div><div class="music-grid">{"".join(cards)}</div></section>'

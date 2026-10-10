#!/usr/bin/env python3
"""Final seasonal presentation pass; preserves canonical music facts and external links."""
import html
import json
import re
from pathlib import Path

START = '<!-- SUZUKA:HALLOWEEN:START -->'
END = '<!-- SUZUKA:HALLOWEEN:END -->'

def restore_pending_markup(text: str, root: Path, path: Path, prefix: str) -> str:
    """Repair retained legacy cards using their explicit work/artist association."""
    from html.parser import HTMLParser
    from urllib.parse import urlsplit
    from PIL import Image
    cms = json.loads((root / 'assets/data/creator-cms.json').read_text())
    allowed = {'enomoto-mia', 'koga-kamishiro', 'michiru'}
    works = {w['slug']: w for w in cms['releases'] if w['artistSlug'] in allowed}
    artists = {a['name']: a for a in cms['artists'] if a['slug'] in allowed}
    news = {n['slug']: n for n in cms['news'] if n.get('artistSlug') in allowed}
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    edits = []
    class Restore(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
        def handle_starttag(self, tag, pairs):
            attrs = dict(pairs)
            if tag == 'img' and (attrs.get('src') or '').endswith('/official-image-pending.svg'):
                work = None
                artist = None
                for _, context in reversed(self.stack):
                    slug = context.get('data-slug')
                    match = re.search(r'/releases/([^/]+)/?', context.get('href') or '')
                    candidate = works.get(slug or (match.group(1) if match else ''))
                    if candidate:
                        work = candidate
                        break
                    artist = artist or artists.get(context.get('data-artist'))
                    link = urlsplit(context.get('href') or '').path
                    item = news.get(link.rstrip('/').split('/')[-1])
                    if item:
                        artist = next(a for a in artists.values() if a['slug'] == item['artistSlug'])
                if not artist and not work and path.parent.parent.name == 'releases' and path.parent.name in works:
                    work = works[path.parent.name]
                if not artist and not work and path.parent.name in news:
                    artist = next(a for a in artists.values() if a['slug'] == news[path.parent.name]['artistSlug'])
                if work:
                    artist = next(a for a in artists.values() if a['slug'] == work['artistSlug'])
                image = work.get('coverImage') if work else None
                if not image or not image.startswith('images/') or not (root / image).is_file():
                    image = artist['image'] if artist else None
                    alt = artist['name'] + ' 公式アーティスト画像（元の動画画像は配信停止）' if artist else None
                else:
                    alt = work['coverAlt']
                if image and (root / image).is_file():
                    with Image.open(root / image) as im:
                        dimensions = im.size
                    raw = self.get_starttag_text()
                    new = re.sub(r'src=["\'][^"\']*["\']', lambda _: 'src="' + prefix + image + '"', raw)
                    new = re.sub(r'alt=["\'][^"\']*["\']', lambda _: 'alt="' + html.escape(alt, quote=True) + '"', new)
                    for key, value in zip(['width', 'height'], dimensions):
                        new = re.sub(key + r'=["\'][^"\']*["\']', key + '="' + str(value) + '"', new)
                    line, column = self.getpos()
                    start = offsets[line - 1] + column
                    edits.append((start, start + len(raw), new))
            if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
                self.stack.append((tag, attrs))
        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    self.stack = self.stack[:i]
                    break
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)
    Restore().feed(text)
    for start, end, new in reversed(edits):
        text = text[:start] + new + text[end:]
    return text

def official_image_replacements(root: Path) -> dict:
    """Restore work-specific official art, never borrow another artist's portrait."""
    from PIL import Image
    cms = json.loads((root / 'assets/data/creator-cms.json').read_text())
    registrations = json.loads((root / 'assets/data/official-image-restorations.json').read_text())
    missing = {x['url'] for x in json.loads((root / 'assets/data/image-availability.json').read_text())['unavailable']}
    replacements = {}
    for work in cms['releases']:
        if work['artistSlug'] not in {'enomoto-mia', 'koga-kamishiro', 'michiru'}:
            continue
        image = work.get('coverImage', '')
        if not image.startswith('images/') or not (root / image).is_file():
            continue
        urls = [work.get('youtubeUrl', ''), work.get('shortsUrl', '')]
        urls += [v.get('youtubeUrl', '') for v in work.get('videoVersions', [])]
        ids = set()
        for url in urls:
            if not isinstance(url, str):
                continue
            match = re.search(r'(?:[?&]v=|/shorts/|youtu\.be/)([\w-]{11})(?:[?&#/]|$)', url)
            if match:
                ids.add(match.group(1))
        with Image.open(root / image) as visual:
            entry = {'image': image, 'alt': work['coverAlt'], 'width': visual.width, 'height': visual.height, 'slug': work['slug'], 'artistSlug': work['artistSlug']}
        for url in missing:
            if any('/' + video + '/' in url for video in ids):
                replacements[url] = entry
        for registration in registrations['registrations']:
            if registration['slug'] == work['slug']:
                assert registration['image'] == image
                replacements[registration['replacedUnavailableUrl']] = entry
    works = {w['slug']: w for w in cms['releases']}
    artists = {a['slug']: a for a in cms['artists']}
    # Announcement/Shorts art with no surviving work image uses the associated
    # registered artist image, explicitly labelled as such, never as a jacket.
    for item in cms['youtubeSnapshot'].get('shortVideos', []) + cms['news']:
        artist = artists.get(item.get('artistSlug'))
        if not artist or artist['slug'] not in {'enomoto-mia', 'koga-kamishiro', 'michiru'}:
            continue
        url = item.get('thumbnail') or item.get('image')
        if url not in missing or url in replacements:
            continue
        work = works.get(item.get('relatedRelease') or item.get('releaseSlug'))
        image = work.get('coverImage') if work else None
        if image and image.startswith('images/') and (root / image).is_file():
            alt = work['coverAlt']
        else:
            image = artist['image']
            alt = artist['name'] + ' 公式アーティスト画像（元の動画画像は配信停止）'
        if not (root / image).is_file():
            continue
        with Image.open(root / image) as visual:
            replacements[url] = {'image': image, 'alt': alt, 'width': visual.width, 'height': visual.height, 'slug': work['slug'] if work else None, 'artistSlug': artist['slug']}
    return replacements

def prepare(root: Path) -> None:
    # Remove the prior season block before other builders insert content at <section>.
    for path in root.rglob('*.html'):
        text = path.read_text()
        updated = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
        if updated != text:
            path.write_text(updated)

def build(root: Path) -> None:
    season = json.loads((root / 'assets/data/site-season.json').read_text())
    (root / 'assets/season-2026.js').write_text(
        "(() => {\nconst day = new Intl.DateTimeFormat('en-CA', {timeZone:" + json.dumps(season['timezone']) +
        ",year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());\n" +
        "const header=document.querySelector('.site-header');const offset=()=>document.documentElement.style.setProperty('--season-header-offset',((header&&['fixed','absolute'].includes(getComputedStyle(header).position))?header.getBoundingClientRect().height:0)+'px');offset();if(header&&typeof ResizeObserver!=='undefined')new ResizeObserver(offset).observe(header);\n" +
        "document.documentElement.classList.toggle('halloween-2026', " + str(season['enabled']).lower() +
        " && day >= " + json.dumps(season['start']) + " && day < " + json.dumps(season['endExclusive']) + ");\n})();\n"
    )
    unavailable = json.loads((root / 'assets/data/image-availability.json').read_text())
    missing = {x['url'] for x in unavailable['unavailable']}
    restored = official_image_replacements(root)
    # Explicit textual placeholder, never a substitute artist/work illustration.
    for path in root.rglob('*.html'):
        if '.git' in path.parts:
            continue
        text = path.read_text()
        prefix = '../' * (len(path.relative_to(root).parts) - 1)
        text = re.sub(r'<link\b[^>]*href=["\'][^"\']*assets/player\.css["\'][^>]*>', '', text)
        text = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
        text = re.sub(r'<link\b[^>]*data-halloween[^>]*>', '', text)
        text = re.sub(r'<script\b[^>]*data-season[^>]*>.*?</script>', '', text, flags=re.S)
        def external_video(match):
            source = re.search(r'src=["\']([^"\']+)', match.group())
            if not source:
                return match.group()
            src = source.group(1)
            if 'youtube' not in src:
                return match.group()
            video_id = src.split('/embed/')[-1].split('?')[0]
            return ('<div class="external-video-link"><p>Official Video</p>'
                    f'<a href="https://www.youtube.com/watch?v={html.escape(video_id)}" '
                    'target="_blank" rel="noopener noreferrer">YouTubeで視聴 ↗</a></div>')
        text = re.sub(r'<iframe\b.*?</iframe>', external_video, text, flags=re.S)
        text = re.sub(r'<audio\b.*?</audio>', '', text, flags=re.S)
        def fix_image(match):
            tag = match.group()
            src = re.search(r'src=["\']([^"\']+)', tag)
            if src and html.unescape(src.group(1)) in missing:
                entry = restored.get(html.unescape(src.group(1)))
                tag = tag.replace(src.group(1), prefix + (entry['image'] if entry else 'images/official-image-pending.svg'))
                alt = html.escape(entry['alt'], quote=True) if entry else '公式画像確認中（元画像の配信停止）'
                tag = re.sub(r'alt=["\'][^"\']*["\']', lambda _: f'alt="{alt}"', tag)
                if entry:
                    for dimension in ['width', 'height']:
                        tag = re.sub(dimension + r'=["\'][^"\']*["\']', dimension + '="' + str(entry[dimension]) + '"', tag)
            return tag
        text = re.sub(r'<img\b[^>]*>', fix_image, text)
        text = restore_pending_markup(text, root, path, prefix)
        for url in missing:
            text = text.replace('data-lightbox-src="' + url + '"', 'data-lightbox-src="' + prefix + (restored[url]['image'] if url in restored else 'images/official-image-pending.svg') + '"')
        banner = (START + '<section class="season-banner" aria-label="SUZUKA Halloween 2026">'
                  '<div class="season-copy"><p>OCTOBER LIMITED · MUSIC &amp; NIGHT</p>'
                  f'<h2>{html.escape(season["label"])}</h2><span>音楽と物語が響く、10月の夜。</span></div>'
                  '<div class="season-art" aria-hidden="true"><i class="season-moon"></i>'
                  '<i class="season-bat bat-one"></i><i class="season-bat bat-two"></i>'
                  '<i class="season-pumpkin"><b></b></i><i class="season-stars"></i></div></section>' + END)
        if '</header>' in text:
            text = text.replace('</header>', '</header>' + banner, 1)
        else:
            text = text.replace('<body>', '<body>' + banner, 1)
        text = text.replace('</head>', f'<link data-halloween rel="stylesheet" href="{prefix}assets/halloween-2026.css"/>'
                            f'<script data-season defer src="{prefix}assets/season-2026.js"></script></head>', 1)
        text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        path.write_text(text)
    # Derived catalogs drive client-rendered cards. Canonical evidence URLs remain intact.
    for path in (root / 'assets/data').glob('*.json'):
        if path.name in {'creator-cms.json', 'image-availability.json', 'site-season.json'} or any(x in path.name for x in ['verification','official-','youtube-publish']):
            continue
        value = json.loads(path.read_text())
        def normalize(value, key=''):
            if isinstance(value, dict):
                updated = {k: normalize(v, k) for k,v in value.items()}
                entry = restored.get(value.get('coverImage', ''))
                if entry:
                    updated.update(coverAlt=entry['alt'], coverWidth=entry['width'], coverHeight=entry['height'])
                for image_key, alt_key in [('thumbnail', 'thumbnailAlt'), ('image', 'imageAlt')]:
                    entry = restored.get(value.get(image_key, ''))
                    if entry:
                        updated[alt_key] = entry['alt']
                return updated
            if isinstance(value, list):
                return [normalize(v,key) for v in value]
            if key in {'image','coverImage','thumbnail','thumbnailUrl','heroImage'} and isinstance(value,str) and value in missing:
                return restored[value]['image'] if value in restored else 'images/official-image-pending.svg'
            return value
        updated = normalize(value)
        if updated != value:
            path.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')
    print('Season presentation applied; onsite playback removed; unavailable official images explicitly marked.')

if __name__ == '__main__':
    build(Path(__file__).resolve().parents[1])

"""Capture public, read-only evidence for the explicitly approved November 1 scope.

No authentication, cookies, YouTube API writes or automatic publication changes.
Run once into a NEW directory; the captured evidence is reviewed and committed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import urllib.request
from zoneinfo import ZoneInfo

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VIDEOS = {
    'dh6g1Ae_rRo': ('redline-heartbeat', 'REDLINE HEARTBEAT', 'asteria', 'audio'),
    'X0IxtHJCt8E': ('outrun-the-night', 'OUTRUN THE NIGHT！', 'asteria', 'audio'),
    'FMq30041id4': ('five-gears-one-sky', 'FIVE GEARS // ONE SKY', 'asteria', 'audio'),
    'sIlMyiDFJ-Y': ('midnight-ignition', 'MIDNIGHT IGNITION', 'asteria', 'mv'),
    'tLhuhEHLvaA': ('last-ignition', 'LAST IGNITION', 'asteria', 'upcoming'),
    'qVJsL2XEjwM': ('midnight-ignition', '', 'asteria', 'short'),
    'ITQ7tvx2DJo': ('redline-heartbeat', '', 'asteria', 'short'),
    'GNoGoEU3g54': ('outrun-the-night', '', 'asteria', 'short'),
    'Fyx__xLfyjg': ('ikusen-no-yoru-wo-koete', '', 'nox', 'short'),
    'gTfnAUf2E1A': ('anata-dake-ni-okuru-happy-birthday', '', 'enomoto-mia', 'short'),
    '6bMysrub3LU': ('michiru-line-stickers', '', 'michiru', 'product-short'),
}
NOTES = {
    'n885587771cac': ('asteria', 'redline-heartbeat'),
    'n99830c3fa397': ('asteria', 'outrun-the-night'),
    'nd9934fc1bcb5': ('enomoto-mia', 'anata-dake-ni-okuru-happy-birthday'),
    'n13198a43a755': ('nox', 'ikusen-no-yoru-wo-koete'),
}
CHANNELS = {'asteria': 'UCVde75yhByGQMu3SkO-fzrA', 'nox': 'UCVde75yhByGQMu3SkO-fzrA',
            'enomoto-mia': 'UCRwW7smDoEB-UOHMQJJ1Jyg', 'michiru': 'UCDqoQCLOp0lWb1bZ6vWEM3g'}
STORES = {'apple_music': 'Apple Music', 'spotify': 'Spotify', 'youtube_music_key': 'YouTube Music',
          'line': 'LINE MUSIC', 'amazon_music_unlimited': 'Amazon Music', 'awa': 'AWA', 'deezer': 'Deezer'}


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ja-JP,ja'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), response.url


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta = {}; self.links = []; self.previews = []; self.text = []; self.jacket = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {'script', 'style'}: self.skip += 1
        if tag == 'meta': self.meta[a.get('property', a.get('name', ''))] = a.get('content', '')
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'img' and 'ジャケット写真' in (a.get('alt') or '') and not self.jacket:
            self.jacket = a.get('src')
        if tag == 'li' and 'FnStickerPreviewItem' in a.get('class', ''):
            self.previews.append(json.loads(a['data-preview'])['staticUrl'])

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}: self.skip -= 1

    def handle_data(self, value):
        if not self.skip: self.text.append(value)


def capture(output, resume=False):
    if output.exists():
        allowed = {v[0] + '.webp' for v in VIDEOS.values() if v[3] in {'audio', 'mv'}} | {k + '.webp' for k in NOTES}
        if not resume or (output / 'verified-sources.json').exists() or any(
                p.is_file() and not (p.parent.name == 'images' and p.name in allowed) and
                p.name not in {'v6-growth.css', 'analytics-extension.js'} for p in output.rglob('*')):
            raise ValueError('Evidence destination already exists; refusing to overwrite')
    output.mkdir(parents=True, exist_ok=True)
    image_dir = output / 'images'; image_dir.mkdir(exist_ok=True)
    captured = datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')
    images = []

    def image(url, name):
        raw, _ = get(url)
        with Image.open(io.BytesIO(raw)) as im:
            im.load(); im.thumbnail((1000, 1000))
            if im.mode not in {'RGB', 'RGBA'}: im = im.convert('RGBA')
            buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90)
            data = buf.getvalue(); width, height = im.size
        path = 'images/' + name + '.webp'; (output / path).write_bytes(data)
        result = {'path': path, 'publicPath': 'images/v6-growth/' + name + '.webp', 'source': url.split('?')[0],
                  'width': width, 'height': height, 'sha256': hashlib.sha256(data).hexdigest()}
        images.append(result)
        return result['publicPath']

    def video(item):
        vid, (slug, title, artist, kind) = item
        raw, _ = get('https://www.youtube.com/watch?v=' + vid)
        text = raw.decode(); match = re.search(r'(?:var )?ytInitialPlayerResponse\s*=\s*', text)
        if not match: raise ValueError('Missing public player metadata: ' + vid)
        data = json.JSONDecoder().raw_decode(text[match.end():])[0]
        details = data.get('videoDetails', {}); micro = data.get('microformat', {}).get('playerMicroformatRenderer', {})
        state = data.get('playabilityStatus', {}).get('status')
        if details.get('channelId') != CHANNELS[artist] or details.get('isPrivate') or micro.get('isUnlisted'):
            raise ValueError('Unverified channel/public identity: ' + vid)
        published = state == 'OK' and int(details.get('lengthSeconds', 0)) > 0
        if kind != 'upcoming' and not published: raise ValueError('Approved public item unavailable: ' + vid)
        # Upcoming stays upcoming even if the player changed: require a separate reviewed promotion.
        date = micro.get('publishDate') if published else None
        return {'videoId': vid, 'slug': slug, 'workTitle': title, 'title': details['title'], 'artistSlug': artist,
                'kind': kind, 'status': 'upcoming' if kind == 'upcoming' else 'published',
                'playability': state, 'channelId': details['channelId'], 'duration': int(details.get('lengthSeconds', 0)),
                'publishedAt': datetime.fromisoformat(date).astimezone(ZoneInfo('Asia/Tokyo')).isoformat() if date else None,
                'scheduledAt': (micro.get('liveBroadcastDetails') or {}).get('startTimestamp') if kind == 'upcoming' else None,
                'source': 'https://www.youtube.com/watch?v=' + vid, 'verifiedAt': captured}

    with ThreadPoolExecutor(max_workers=4) as pool: videos = list(pool.map(video, VIDEOS.items()))
    for v in videos:
        if v['kind'] in {'mv', 'audio'}:
            v['image'] = image('https://i.ytimg.com/vi/' + v['videoId'] + '/hqdefault.jpg', v['slug'])
    news = []
    for key, (artist, slug) in NOTES.items():
        raw, _ = get('https://note.com/api/v3/notes/' + key)
        n = json.loads(raw)['data']
        # Only the official title, publication time and cover; never copy article/lyrics text.
        news.append({'slug': 'official-note-' + key, 'title': n['name'], 'publishedAt': n['publish_at'],
                     'artistSlug': artist, 'relatedRelease': slug, 'noteUrl': 'https://note.com/1209bellflower/n/' + key,
                     'image': image(n['eyecatch'], key), 'verifiedAt': captured})

    cms = json.loads((ROOT / 'assets/data/creator-cms.json').read_text())
    codes = set(re.findall(r'https://linkco.re/([A-Za-z0-9]{8})', json.dumps(cms['releases']))) | {'aU8rN04N'}

    def stream(code):
        url = 'https://linkco.re/' + code + '?lang=ja'; raw, _ = get(url)
        p = Page(); p.feed(raw.decode()); text = ' '.join(p.text)
        date = re.search(r'リリース日:\s*(\d{4}/\d{2}/\d{2})', text)
        if not date: raise ValueError('Missing streaming release date: ' + code)
        stores = []
        for link in p.links:
            match = re.fullmatch(r'https://www.tunecore.co.jp/to/([^/]+)/([0-9]+)(?:\?.*)?', link)
            if match and match[1] in STORES:
                stores.append({'id': match[1], 'name': STORES[match[1]], 'url': link})
        return {'code': code, 'url': url.split('?')[0], 'title': p.meta.get('og:title'),
                'releaseDate': date[1].replace('/', '-'), 'stores': stores, 'jacketSource': p.meta.get('og:image'),
                '_jacketDownload': p.jacket,
                'verifiedAt': captured, 'verificationScope': 'official LinkCore listed stores; subscription playback not tested'}
    with ThreadPoolExecutor(max_workers=5) as pool: streams = list(pool.map(stream, sorted(codes)))
    for s in streams:
        if s['code'] in {'aU8rN04N', 'vvasqg5z'}:
            # Independently confirm the two newly promoted streaming records in Japan Apple Music.
            apple = next(x for x in s['stores'] if x['id'] == 'apple_music')
            raw, final = get(apple['url']); p = Page(); p.feed(raw.decode())
            if 'music.apple.com/jp/album/' not in final: raise ValueError('Missing Japan Apple listing')
            s['appleMusicUrl'] = final.split('?')[0]
            # The public page's actual jacket image may use a temporary CDN URL.
            # Use it in memory only; never store its query/signature in evidence.
            s['jacket'] = image(s['_jacketDownload'] or s['jacketSource'], 'linkcore-' + s['code'])
    for s in streams: s.pop('_jacketDownload', None)

    stickers = []
    for product, artist, expected in [('37544868', 'enomoto-mia', 8), ('37581772', 'michiru', 16)]:
        url = 'https://store.line.me/stickershop/product/' + product + '/ja'
        raw, _ = get(url); p = Page(); p.feed(raw.decode()); text = ' '.join(p.text)
        if len(p.previews) != expected or not re.search(r'￥190|¥190', text) or 'SUZUKA' not in text:
            raise ValueError('Sticker product changed; review required: ' + product)
        title = p.meta['og:title'].split(' - LINE')[0]
        stickers.append({'id': artist + '-line-stickers', 'artistSlug': artist, 'productId': product, 'title': title,
                         'status': 'published', 'url': url, 'price': 190, 'currency': 'JPY', 'count': expected,
                         'image': image(p.meta['og:image'], 'stickers-' + product),
                         'previews': [image(u, 'sticker-' + product + '-' + str(i + 1)) for i, u in enumerate(p.previews)],
                         'verifiedAt': captured, 'source': url})
    stickers.append({'id': 'eclypse-line-stickers', 'artistSlug': 'eclypse', 'title': 'ECLYPSE',
                     'status': 'in-review', 'url': None, 'price': None, 'currency': None, 'count': None,
                     'image': None, 'previews': [], 'source': 'explicit-user-approval-2026-11-01'})
    result = {'schemaVersion': 1, 'verifiedAt': captured, 'videos': videos, 'news': news, 'streaming': streams,
              'stickers': stickers, 'images': sorted(images, key=lambda x: x['path'])}
    (output / 'verified-sources.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'videos': len(videos), 'news': len(news), 'linkcore': len(streams), 'products': 2,
                      'images': len(images), 'youtubeWrites': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Resume only the known incomplete first capture')
    args = parser.parse_args()
    capture(args.output, args.resume)

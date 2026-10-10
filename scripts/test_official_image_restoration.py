#!/usr/bin/env python3
"""Provenance and negative regression checks for restored work-specific visuals."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from build_halloween import official_image_replacements, restore_pending_markup

root = Path(__file__).resolve().parents[1]
cms = json.loads((root / 'assets/data/creator-cms.json').read_text())
artists = {a['slug']: a for a in cms['artists']}
registrations = json.loads((root / 'assets/data/official-image-restorations.json').read_text())['registrations']
assert len(registrations) == 7
for entry in registrations:
    work = next(w for w in cms['releases'] if w['slug'] == entry['slug'])
    assert entry['status'] == 'verified-official-video-thumbnail'
    assert entry['channelId'] == artists[work['artistSlug']]['officialYoutubeChannelId']
    assert entry['artistName'] == work['artist']
    assert work['coverImage'] == entry['image']
    for field, digest in [('image', 'imageSha256'), ('originalPath', 'originalSha256')]:
        assert hashlib.sha256((root / entry[field]).read_bytes()).hexdigest() == entry[digest]
        with Image.open(root / entry[field]) as image:
            assert image.size == (entry['width'], entry['height'])
mapping = official_image_replacements(root)
for entry in registrations:
    assert mapping[entry['replacedUnavailableUrl']]['image'] == entry['image']
assert 'https://i.ytimg.com/vi/unknown0000/maxresdefault.jpg' not in mapping
unknown = '<article data-artist="未確認"><img src="../images/official-image-pending.svg" alt="公式画像確認中"/></article>'
assert restore_pending_markup(unknown, root, root / 'unknown/index.html', '../') == unknown
known = '<article data-artist="神代煌牙"><a href="../releases/updown/"><img src="../images/official-image-pending.svg" alt="公式画像確認中" width="1280" height="720"/></a></article>'
restored = restore_pending_markup(known, root, root / 'social/index.html', '../')
assert registrations[0]['image'] in restored and '妃みちる' in restored and '神代煌牙「' not in restored, 'Explicit work identity takes priority over a broader container'
for entry in mapping.values():
    if entry['image'] in {a['image'] for a in cms['artists']}:
        assert entry['image'] == artists[entry['artistSlug']]['image'], 'No borrowed identity'
        if '元の動画画像' in entry['alt']:
            assert '公式アーティスト画像（元の動画画像は配信停止）' in entry['alt'], 'Never mislabel a profile as a jacket'
        else:
            work = next(w for w in cms['releases'] if w['slug'] == entry['slug'])
            assert entry['image'] == work['coverImage'] and entry['alt'] == work['coverAlt']
target = registrations[0]['image']
original_is_file = Path.is_file
with patch.object(Path, 'is_file', lambda path: False if path == root / target else original_is_file(path)):
    reduced = official_image_replacements(root)
    assert all(entry['image'] != target for entry in reduced.values()), 'Missing work image must never be rendered'
    fallback = reduced.get(registrations[0]['replacedUnavailableUrl'])
    if fallback:
        assert fallback['image'] == artists[registrations[0]['artistSlug']]['image']
        assert '元の動画画像は配信停止' in fallback['alt']
print(json.dumps({'status': 'PASS', 'newOfficialThumbnails': len(registrations), 'restoredUnavailableUrls': len(mapping), 'unverifiedImageNotRegistered': True}))

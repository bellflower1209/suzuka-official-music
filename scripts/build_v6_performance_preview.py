"""Build a review-only overlay on the exact 71ea739 production package.

Never changes public-release/, stages Pages or adopts publication approval.
The four variants support isolated, paired performance comparisons.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urljoin, urlparse

from build_music_production_release import sha
from verify_public_release import read_release, verify_private_audio, write_output

ROOT = Path(__file__).resolve().parents[1]
BASE = '71ea73944d72fadef5d186a5346a65f1a1609511'
DIGEST = '41074d98fd29675f0bdc223a55d25a9a96bb40921516a4d0225cdeb132f00b11'
MANIFEST = 'suzuka-v6-candidate-manifest.json'
IMAGE = 'images/enomoto-mia-amaterasu-official-jacket.png'
IMAGE_HASH = '22dc21412a1af458c731'
IMAGE_ROUTES = ('index.html', 'worlds/enomoto-mia/index.html')
STYLE_ROUTES = ('artists/index.html', 'artists/enomoto-mia/index.html',
                'releases/anata-dake-ni-okuru-happy-birthday/index.html')
SIZES = '(max-width: 560px) calc(100vw - 42px), (max-width: 900px) 45vw, 400px'


def asset_path(page, href):
    parsed = urlparse(urljoin('https://www.suzukaofficial.com/' + page, href))
    if parsed.netloc != 'www.suzukaofficial.com' or parsed.query or parsed.fragment:
        raise ValueError('Only unversioned same-origin legacy CSS is supported')
    return parsed.path.lstrip('/')


def optimize_card(page, files):
    pattern = r'<img\b[^>]*\bsrc="/' + re.escape(IMAGE) + r'"[^>]*>'
    matches = list(re.finditer(pattern, page))
    if len(matches) != 1:
        raise ValueError('Expected exactly one existing Amaterasu growth card')
    old = matches[0].group()
    if not all(value in old for value in ('width="1254"', 'height="1254"', 'loading="lazy"', 'decoding="async"')) or 'srcset=' in old:
        raise ValueError('Unexpected card geometry or loading attributes')
    if sha(files[IMAGE])[:20] != IMAGE_HASH:
        raise ValueError('Official original changed')
    variants = [f'/assets/v6-media/official/{IMAGE_HASH}-{size}.webp {size}w' for size in (320, 640)]
    if any(url.split()[0].lstrip('/') not in files for url in variants):
        raise ValueError('Existing approved WebP variant is missing')
    variants.append(f'/{IMAGE} 1254w')
    # Keep the original src, intrinsic square dimensions, lazy loading and all
    # semantics. High-DPR displays can still select the full-resolution PNG.
    new = old[:-1] + ' srcset="' + ', '.join(variants) + '" sizes="' + SIZES + '">'
    return page.replace(old, new, 1)


def bundle_styles(name, page, files):
    links = []
    for match in re.finditer(r'<link\b[^>]*>', page):
        tag = match.group()
        if 'rel="stylesheet"' not in tag:
            continue
        href = re.search(r'\bhref="([^"]+)"', tag)
        if href is None:
            raise ValueError('Stylesheet URL missing')
        path = asset_path(name, href[1])
        # main.js detects this original URL to avoid appending it again.
        if path == 'assets/social.css':
            continue
        if Path(path).parent.as_posix() != 'assets' or path not in files:
            raise ValueError('Unsupported stylesheet location')
        links.append((tag, path))
    if len(links) not in (11, 13, 15) or len({p for _, p in links}) != len(links):
        raise ValueError('Legacy stylesheet inventory changed')
    chunks = []
    for _, path in links:
        content = files[path]
        if re.search(rb'@(?:charset|import)\b|sourceMappingURL', content):
            raise ValueError('CSS needs a separate import/charset/source-map review')
        chunks.append(b'/* ' + path.encode() + b' */\n' + content + b'\n')
    data = b''.join(chunks)
    bundle = 'assets/v6-performance-' + sha(data)[:16] + '.css'
    files[bundle] = data
    # Same directory => relative url() paths keep exactly the same meaning.
    # Retain every byte and cascade order; this is not an unused-CSS purge.
    page = page.replace(links[0][0], f'<link rel="stylesheet" href="/{bundle}">', 1)
    for tag, _ in links[1:]:
        page = page.replace(tag, '', 1)
    paths = {path for _, path in links}
    def preload(match):
        tag = match.group()
        href = re.search(r'\bhref="([^"]+)"', tag)
        if 'rel="preload"' in tag and 'as="style"' in tag and href and asset_path(name, href[1]) in paths:
            return ''
        return tag
    page = re.sub(r'<link\b[^>]*>', preload, page)
    return page, {'bundle': bundle, 'sources': [p for _, p in links], 'bytes': len(data)}


def build(variant='combined', root=ROOT):
    if variant not in ('baseline', 'images', 'styles', 'combined'):
        raise ValueError('Unknown preview variant')
    info, baseline = read_release(root, BASE)
    if info['artifactDigest'] != DIGEST or len(baseline) != 863:
        raise ValueError('Production baseline changed; STOP')
    # Current public-release must also remain byte-for-byte the production base.
    current_info, current = read_release(root)
    if current != baseline or current_info != info:
        raise ValueError('Public package changed; STOP')
    files = dict(baseline)
    bundles = {}
    if variant in ('images', 'combined'):
        for name in IMAGE_ROUTES:
            files[name] = optimize_card(files[name].decode(), files).encode()
    if variant in ('styles', 'combined'):
        for name in STYLE_ROUTES:
            page, bundles[name] = bundle_styles(name, files[name].decode(), files)
            files[name] = page.encode()
    changed = sorted(n for n in baseline if files[n] != baseline[n])
    added = sorted(set(files) - set(baseline))
    allowed = set(IMAGE_ROUTES if variant in ('images', 'combined') else ()) | set(STYLE_ROUTES if variant in ('styles', 'combined') else ())
    if set(changed) != allowed or not set(baseline) <= set(files):
        raise ValueError('Unexpected content changes')
    manifest = json.loads(files[MANIFEST])
    if variant != 'baseline':
        manifest['performancePreview'] = {'baselineCommit': BASE, 'baselineDigest': DIGEST,
            'variant': variant, 'status': 'draft-preview-only', 'publicationApproved': False,
            'imageRoutes': list(IMAGE_ROUTES) if variant in ('images', 'combined') else [], 'styleBundles': bundles}
        manifest['files'] = {n: sha(b) for n, b in sorted(files.items()) if n != MANIFEST}
        files[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    verify_private_audio(info, files, manifest['v6Routes'])
    return copy.deepcopy(info), files, {'variant': variant, 'baselineCommit': BASE, 'baselineDigest': DIGEST,
        'files': len(files), 'changedHtml': changed, 'addedFiles': added, 'bundles': bundles,
        'artists': 13, 'works': 109, 'publicationApproved': False, 'publicPackageUnchanged': True}


def review_output_allowed(output, root=ROOT):
    output, root = output.resolve(), root.resolve()
    allowed = [Path('/tmp').resolve(), Path(tempfile.gettempdir()).resolve()]
    if (os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_REPOSITORY') == 'bellflower1209/suzuka-official-music'
            and os.environ.get('RUNNER_TEMP')):
        allowed.append(Path(os.environ['RUNNER_TEMP']).resolve())
    return (not output.is_relative_to(root)
            and any(output != d and output.is_relative_to(d) for d in allowed)
            and not any((p / '.git').exists() for p in (output, *output.parents)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant', choices=('baseline', 'images', 'styles', 'combined'), default='combined')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    output = args.output.resolve()
    if not review_output_allowed(output):
        raise ValueError('Review output must be in an external temporary directory')
    _, files, report = build(args.variant)
    write_output(output, files)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

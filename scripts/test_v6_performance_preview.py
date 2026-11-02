"""Regression boundaries for the review-only performance overlay."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

from PIL import Image

from build_v6_performance_preview import (
    BASE, DIGEST, IMAGE, IMAGE_HASH, IMAGE_ROUTES, MANIFEST, ROOT, STYLE_ROUTES,
    build, bundle_styles, review_output_allowed,
)
from verify_public_release import read_release


class Semantics(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag in ('a', 'meta', 'script'):
            self.items.append((tag, attrs))


class PerformancePreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info, cls.before = read_release(ROOT, BASE)
        _, cls.after, cls.report = build()

    def test_historical_production_baseline_is_sealed(self):
        info, files = read_release(ROOT, BASE)
        self.assertEqual(info['artifactDigest'], DIGEST)
        self.assertEqual(files, self.before)
        self.assertEqual(len(files), 863)
        self.assertFalse(self.report['publicationApproved'])
        self.assertEqual(build('baseline')[1], files)

    def test_review_output_handles_ci_temp_without_allowing_git_or_production(self):
        self.assertFalse(review_output_allowed(ROOT / 'public-release' / 'candidate'))
        self.assertFalse(review_output_allowed(Path('/')))
        with patch.dict('os.environ', {'GITHUB_ACTIONS': 'true',
                'GITHUB_REPOSITORY': 'bellflower1209/suzuka-official-music',
                'RUNNER_TEMP': '/nonstandard-github-runner-temp'}):
            self.assertTrue(review_output_allowed(Path('/nonstandard-github-runner-temp/candidate')))
            self.assertFalse(review_output_allowed(Path('/nonstandard-github-runner-temp')))
        with patch.dict('os.environ', {'GITHUB_ACTIONS': 'false',
                'RUNNER_TEMP': '/nonstandard-github-runner-temp'}):
            self.assertFalse(review_output_allowed(Path('/nonstandard-github-runner-temp/candidate')))

    def test_only_reviewed_html_and_manifest_change(self):
        self.assertTrue(set(self.before) <= set(self.after))
        changed = {n for n in self.before if self.before[n] != self.after[n]}
        self.assertEqual(changed, set(IMAGE_ROUTES) | set(STYLE_ROUTES) | {MANIFEST})
        self.assertEqual(len(self.after), 866)
        self.assertTrue(all(re.fullmatch(r'assets/v6-performance-[a-f0-9]{16}\.css', n)
                            for n in set(self.after) - set(self.before)))

    def test_all_original_images_worlds_audio_and_scripts_unchanged(self):
        for n, data in self.before.items():
            if not n.endswith('.html') and n != MANIFEST:
                self.assertEqual(self.after[n], data, n)
        manifest = json.loads(self.after[MANIFEST])
        self.assertEqual(manifest['v6Routes'], json.loads(self.before[MANIFEST])['v6Routes'])
        self.assertEqual(len(manifest['v6Routes']), 14)
        cms = json.loads(self.after['assets/data/creator-cms.json'])
        self.assertEqual((len(cms['artists']), len(cms['releases'])), (13, 109))
        self.assertNotIn('last-ignition', {r['slug'] for r in cms['releases']})
        self.assertFalse(any(Path(n).suffix.lower() in {'.mp3','.wav','.m4a','.aac','.ogg','.flac','.m3u8','.ts'}
                             for n in self.after))

    def test_card_preserves_original_full_resolution_and_square_ratio(self):
        import io
        for size in (320, 640):
            data = self.after[f'assets/v6-media/official/{IMAGE_HASH}-{size}.webp']
            self.assertEqual(Image.open(io.BytesIO(data)).size, (size, size))
        self.assertEqual(Image.open(io.BytesIO(self.after[IMAGE])).size, (1254, 1254))
        for name in IMAGE_ROUTES:
            text = self.after[name].decode()
            tag = re.search(r'<img[^>]*src="/' + re.escape(IMAGE) + r'"[^>]*>', text)[0]
            self.assertIn('1254w', tag)
            self.assertIn('width="1254" height="1254"', tag)
            self.assertIn('loading="lazy" decoding="async"', tag)
            restored_tag = re.sub(r' srcset="[^"]+" sizes="[^"]+"', '', tag)
            restored = text.replace(tag, restored_tag, 1)
            self.assertEqual(restored, self.before[name].decode())
        # High-resolution artwork pages and their existing URLs are untouched.
        self.assertEqual(self.after['releases/amaterasu/index.html'], self.before['releases/amaterasu/index.html'])

    def test_css_bytes_order_urls_and_social_detection_are_preserved(self):
        for name, record in self.report['bundles'].items():
            expected = b''.join(b'/* ' + p.encode() + b' */\n' + self.before[p] + b'\n'
                                for p in record['sources'])
            self.assertEqual(self.after[record['bundle']], expected)
            self.assertEqual(Path(record['bundle']).parent.as_posix(), 'assets')
            text = self.after[name].decode()
            self.assertNotIn('as="style"', text)
            count = text.count('rel="stylesheet"')
            self.assertEqual(count, 2 if name.startswith('releases/') else 1)
            if name.startswith('releases/'):
                self.assertIn('<link rel="stylesheet" href="/assets/social.css">', text)

    def test_css_with_import_or_changed_inventory_fails_closed(self):
        modified = dict(self.before)
        modified['assets/styles.css'] += b'\n@import "unexpected.css";'
        with self.assertRaises(ValueError):
            bundle_styles(STYLE_ROUTES[0], self.before[STYLE_ROUTES[0]].decode(), modified)

    def test_links_metadata_schemas_and_analytics_attributes_are_unchanged(self):
        for name in set(IMAGE_ROUTES) | set(STYLE_ROUTES):
            parsers = [Semantics(), Semantics()]
            parsers[0].feed(self.before[name].decode())
            parsers[1].feed(self.after[name].decode())
            self.assertEqual(parsers[0].items, parsers[1].items, name)
            schemas = r'<script type="application/ld\+json">(.*?)</script>'
            self.assertEqual(re.findall(schemas, self.before[name].decode(), re.S),
                             re.findall(schemas, self.after[name].decode(), re.S), name)

    def test_sitemaps_contacts_stickers_and_all_unmodified_routes_are_unchanged(self):
        for n in ['sitemap.xml', 'image-sitemap.xml', 'video-sitemap.xml', 'robots.txt',
                  'line-stickers/index.html', 'music-production/index.html']:
            self.assertEqual(self.before[n], self.after[n], n)
        self.assertFalse(json.loads(self.after[MANIFEST])['performancePreview']['publicationApproved'])

    def test_every_html_internal_reference_and_fragment_still_resolves(self):
        from test_v6_growth_preview import HTML
        parsed = {}
        for name, data in self.after.items():
            if name.endswith('.html'):
                parser = HTML()
                parser.feed(data.decode())
                parsed[name] = parser
        checked = 0
        for name, parser in parsed.items():
            for ref in parser.refs:
                url = urlsplit(urljoin('https://www.suzukaofficial.com/' + name, ref))
                if url.netloc != 'www.suzukaofficial.com' or url.scheme != 'https':
                    continue
                destination = unquote(url.path.lstrip('/'))
                if not destination or destination.endswith('/'):
                    destination += 'index.html'
                elif not Path(destination).suffix:
                    destination += '/index.html'
                self.assertIn(destination, self.after, (name, ref))
                if url.fragment and destination in parsed:
                    self.assertIn(unquote(url.fragment), parsed[destination].anchors, (name, ref))
                checked += 1
        self.assertGreater(checked, 30000)


if __name__ == '__main__':
    unittest.main(verbosity=2)

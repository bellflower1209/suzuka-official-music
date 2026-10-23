#!/usr/bin/env python3
"""Prove the service extension preserves the approved V6 package."""
from __future__ import annotations

import json
import re
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from build_music_production_release import (
    BASE_COMMIT, MAIL_FIELDS, MANIFEST, ROOT, SERVICE_URL, build_files,
)
from verify_public_release import read_release
from build_official_sync_package import build as historical_sync_build


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.hrefs.append(href)


class ReleaseExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.baseline = read_release(ROOT, BASE_COMMIT)
        _, cls.candidate, _ = build_files(ROOT)

    def test_all_approved_files_remain_and_non_html_assets_are_identical(self):
        self.assertEqual(len(self.baseline), 781)
        self.assertEqual(len(self.candidate), 784)
        self.assertTrue(set(self.baseline) <= set(self.candidate))
        for name, data in self.baseline.items():
            if name in {MANIFEST, 'sitemap.xml'} or name.endswith('.html'):
                continue
            self.assertEqual(self.candidate[name], data, name)

    def test_old_html_diff_is_only_navigation_and_home_invitation(self):
        for name, original in self.baseline.items():
            if not name.endswith('.html'):
                continue
            text = self.candidate[name].decode('utf-8')
            text = text.replace('<a href="/music-production/">楽曲制作</a>', '')
            text = re.sub(r'<a href="(?:\.\./)*music-production/">(?:楽曲制作|Music Production)</a>', '', text)
            if name == 'index.html':
                text = re.sub(r'<section class="mp-home-link".*?</section>', '', text, count=1, flags=re.S)
                text = text.replace('<link rel="stylesheet" href="/assets/music-production.css">', '')
            self.assertEqual(text.encode('utf-8'), original, name)

    def test_sitemap_retains_all_old_urls_and_adds_one(self):
        ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
        def urls(data):
            return [item.findtext(ns + 'loc') for item in ET.fromstring(data)]
        old = urls(self.baseline['sitemap.xml'])
        new = urls(self.candidate['sitemap.xml'])
        self.assertEqual(len(old), 354)
        self.assertEqual(new, old + [SERVICE_URL])

    def test_service_email_link_and_policy(self):
        page = self.candidate['music-production/index.html'].decode('utf-8')
        links = Links()
        links.feed(page)
        consultation = [link for link in links.hrefs if link.startswith('mailto:') and '?' in link]
        self.assertEqual(len(consultation), 2)
        for link in consultation:
            parsed = urllib.parse.urlsplit(link)
            self.assertEqual(parsed.path, '1209bellflower@gmail.com')
            query = urllib.parse.parse_qs(parsed.query)
            self.assertEqual(query['subject'], ['SUZUKA 楽曲制作のご相談'])
            self.assertTrue(all(field in query['body'][0] for field in MAIL_FIELDS))
        for phrase in ('個別にお見積もり', '著作権と利用許諾', '商用利用', '依頼者の許可', 'AI音声・音楽生成サービス'):
            self.assertIn(phrase, page)
        self.assertNotIn('{{MAILTO}}', page)
        self.assertIn('<!-- SUZUKA:GA4:START -->', page)

    def test_manifest_keeps_v6_routes_and_existing_structured_data(self):
        previous = json.loads(self.baseline[MANIFEST])
        current = json.loads(self.candidate[MANIFEST])
        self.assertEqual(current['v6Routes'], previous['v6Routes'])
        self.assertEqual(len(current['v6Routes']), 13)
        self.assertEqual(current['measurementId'], previous['measurementId'])
        self.assertEqual(current['v6ProtectedDelivery'], previous['v6ProtectedDelivery'])
        self.assertEqual(set(current['files']), set(self.candidate) - {MANIFEST})

    def test_historical_builder_refuses_newer_release(self):
        with self.assertRaisesRegex(ValueError, 'baseline is stale'):
            historical_sync_build(ROOT, Path('/private/tmp/unused-music-production-output'),
                                  Path('/private/tmp/unused-music-production-package'))


if __name__ == '__main__':
    unittest.main()

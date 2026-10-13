#!/usr/bin/env python3
"""Verify the added public videos against generated links and JSON-LD."""
import json
from html.parser import HTMLParser
from pathlib import Path
from structured_data_dates import JSONLD_RE, iter_nodes, types_of, youtube_id

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.targets = set()
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.targets.add(dict(attrs).get('href', ''))

def page(path):
    text = (ROOT / path).read_text()
    nodes = [node for block in JSONLD_RE.finditer(text)
             for node in iter_nodes(json.loads(block.group(2)))
             if 'VideoObject' in types_of(node)]
    return Links(text).targets, nodes

def main():
    cms = json.loads((ROOT / 'assets/data/creator-cms.json').read_text())
    report = json.loads((ROOT / 'docs/official-sync-20261012.json').read_text())
    evidence = json.loads((ROOT / 'assets/data/youtube-publish-dates.json').read_text())
    dates = {item['youtubeId']: item for item in evidence['records']}
    shorts = {item['videoId']: item for item in cms['youtubeSnapshot']['shortVideos']}
    releases = {item['slug']: item for item in cms['releases']}
    errors = []
    def verified_node(nodes, url, title=None):
        identifier = youtube_id(url)
        proof = dates.get(identifier, {})
        matches = [node for node in nodes if node.get('contentUrl') == url]
        if not matches or not proof.get('verifiedPublishedAt'):
            errors.append('Missing verified VideoObject: ' + url)
            return
        for node in matches:
            if node.get('uploadDate') != proof['verifiedPublishedAt']:
                errors.append('Wrong uploadDate: ' + url)
            if title and node.get('name') != title:
                errors.append('Wrong video title: ' + url)
            if not node.get('thumbnailUrl'):
                errors.append('Missing official thumbnail: ' + url)
    for identifier in report['mutations']['addedShorts']:
        short = shorts[identifier]
        targets, nodes = page(f'artists/{short["artistSlug"]}/index.html')
        if short['youtubeUrl'] not in targets:
            errors.append('Missing Shorts link: ' + identifier)
        verified_node(nodes, short['youtubeUrl'], short['title'])
    for change in report['mutations']['addedVideoVersions']:
        item = releases[change['releaseSlug']]
        targets, nodes = page(item['releaseUrl'] + 'index.html')
        if change['youtubeUrl'] not in targets:
            errors.append('Missing related video link: ' + change['youtubeUrl'])
        if not dates.get(youtube_id(change['youtubeUrl']), {}).get('verifiedPublishedAt'):
            errors.append('Missing version datetime evidence: ' + change['youtubeUrl'])
        version = next(v for v in item['videoVersions'] if v['youtubeUrl'] == change['youtubeUrl'])
        verified_node(nodes, change['youtubeUrl'], version['title'])
    for slug in report['mutations']['addedReleases'] + report['mutations'].get('addedYouTubeReleases20261013', []):
        release = releases[slug]
        if release.get('youtubeUrl'):
            _, nodes = page(release['releaseUrl'] + 'index.html')
            verified_node(nodes, release['youtubeUrl'])
    result = {'status': 'FAIL' if errors else 'PASS', 'shorts': len(report['mutations']['addedShorts']),
              'versions': len(report['mutations']['addedVideoVersions']), 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))

if __name__ == '__main__':
    main()

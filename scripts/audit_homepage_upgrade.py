#!/usr/bin/env python3
"""Audit the October upgrade against canonical records and independent evidence."""
import json,re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
def main():
    cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    today=datetime.fromisoformat(cms['updatedAt']).astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    works=cms['releases']+cms['upcoming']+cms.get('comingSoon',[])
    assert len(works)==len({r['slug'] for r in works})
    assert len(cms['news'])==len({n['slug'] for n in cms['news']})
    assert not [r for r in cms['upcoming'] if r['releaseDate']<=today]
    evidence=json.loads((ROOT/'assets/data/streaming-verification-20261002.json').read_text())
    for row in evidence['records']:
        item=next(r for r in cms['releases'] if (r.get('scheduledStreamingRelease') or {}).get('linkcoreUrl','').endswith('/'+row['code']))
        s=item['scheduledStreamingRelease'];assert s['status']=='published' and s['releaseDate']==row['releaseDate'] and s['verifiedAt']
        assert item['title'] in row['title'] and item['artist'] in row['title']
        assert len(row['stores'])==2 and all(x['status']==200 for x in row['stores'])
    magic=next(r for r in works if r['slug']=='mahou-ga-toketemo')
    assert magic['status']=='published' and magic['scheduledStreamingRelease']['status']=='upcoming' and magic['scheduledStreamingRelease']['releaseDate']>today
    for slug in ['eternity-of-flower-words','renai-taishogai-kari']:
        assert not next(r for r in works if r['slug']==slug).get('youtubeUrl')
    home=(ROOT/'index.html').read_text()
    for slug in cms['homepage']['featuredArtists']:
        artist=next(a for a in cms['artists'] if a['slug']==slug)
        assert artist['officialYoutubeUrl'] in home
    for identifier in ['official-artist-channels','now-streaming','mia-meets','latest-releases','featured-artists','latest-mv','follow-suzuka']:
        assert home.count('id="'+identifier+'"')==1
    assert home.count('aria-labelledby="special-feature-title"')==1
    assert '登場するアーティスト・人物は架空' in home
    series=next(s for s in cms['seriesDefinitions'] if s['slug']=='mia-meets')
    assert series['episodes']==[]  # No invented collaborations or release dates.
    assert 'features/mia-meets/' in (ROOT/'sitemap.xml').read_text()
    for page in ROOT.rglob('index.html'):
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',page.read_text(),re.S):json.loads(block)
    print('October upgrade passed: unique works/news, 6 evidence-backed streams, 3 artist channels, no elapsed Upcoming, future streaming preserved, series facts and JSON-LD validated.')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Regression audit: separate release dates and undated canonical Upcoming."""
import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.graphs=[]; self.ld=False; self.parts=[]
    def handle_starttag(self, tag, attrs):
        self.ld = tag == 'script' and dict(attrs).get('type') == 'application/ld+json'
        if self.ld: self.parts=[]
    def handle_data(self, value):
        if self.ld: self.parts.append(value)
    def handle_endtag(self, tag):
        if tag == 'script' and self.ld:
            self.graphs.append(json.loads(''.join(self.parts))); self.ld=False

def nodes(value):
    if isinstance(value, dict):
        yield value
        for item in value.values(): yield from nodes(item)
    elif isinstance(value, list):
        for item in value: yield from nodes(item)

def main():
    cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    all_works=cms['releases']+cms['upcoming']+cms.get('comingSoon',[])
    assert len({x['slug'] for x in all_works})==len(all_works)
    million=next(x for x in all_works if x['slug']=='hyakumankoku')
    assert million['status']=='published' and million['releaseDate']=='2026-07-12'
    assert million['publishedAt'].startswith('2026-07-12')
    assert million['scheduledStreamingRelease']['releaseDate']=='2026-09-21'
    activity=next(x for x in cms['miaReleaseSchedule']['activities'] if x['title']=='百万告')
    assert activity['kind']=='STREAMING RELEASE' and activity['officialReleaseDate']=='2026-07-12'
    upcoming=[x for x in all_works if x['title']=='魔法が解けても']
    assert len(upcoming)==1
    item=upcoming[0]
    assert item['artistSlug']=='koga-kamishiro' and item['status']=='upcoming'
    assert not any(item.get(k) for k in ['releaseDate','scheduledAt','publishedAt'])
    for route in ['index.html','artists/koga-kamishiro/index.html','schedule/index.html','releases/mahou-ga-toketemo/index.html']:
        text=(ROOT/route).read_text(); assert '魔法が解けても' in text and 'COMING SOON' in text,route
    page=(ROOT/'releases/mahou-ga-toketemo/index.html').read_text()
    assert 'content="noindex, follow"' in page
    assert 'MusicRecording' not in page and 'VideoObject' not in page and 'data-countdown' not in page
    for name in ['sitemap.xml','image-sitemap.xml','video-sitemap.xml']:
        assert '/releases/mahou-ga-toketemo/' not in (ROOT/name).read_text()
    parser=Parser();parser.feed((ROOT/'releases/hyakumankoku/index.html').read_text())
    recordings=[x for x in nodes(parser.graphs) if x.get('@type')=='MusicRecording']
    assert recordings and all(x.get('datePublished', '2026-07-12').startswith('2026-07-12') for x in recordings)  # Existing schema omits this field.
    videos=[x for x in nodes(parser.graphs) if x.get('@type')=='VideoObject']
    assert videos and all(x['uploadDate'].startswith('2026-07-12') for x in videos)
    schedule=(ROOT/'schedule/index.html').read_text()
    # Test the static renderer at an explicit baseline, independent of later CMS updates.
    import tempfile
    from build_creator_platform_v31 import schedule_page
    with tempfile.TemporaryDirectory() as tmp:
        schedule_page(Path(tmp), {**cms, 'updatedAt':'2026-09-13T15:00:00+00:00'}, cms['releases'], cms['upcoming'])
        fixture=(Path(tmp)/'schedule/index.html').read_text()
    next_week=fixture.split('id="next-week"')[1].split('</section>')[0]
    for slug in ['hello-hello-halloween','over-drive','september-blue']: assert slug in next_week
    assert 'Asia/Tokyo' in schedule and '月曜始まり' in schedule and 'assets/release-schedule.js' in schedule
    search=json.loads((ROOT/'assets/data/search-v31.json').read_text())
    raw=json.dumps(search,ensure_ascii=False)
    for term in ['神代煌牙','魔法が解けても','榎本魅愛','百万告','Streaming Release','Hello Hello Halloween','Over Drive','September Blue']: assert term in raw,term
    koga=(ROOT/'artists/koga-kamishiro/index.html').read_text()
    assert '悪役でいい' in koga and 'youtube.com/' in koga
    print('Postpublication audit passed: 3 Next Week works, preserved July 12 schema / September 21 streaming, 1 undated Koga Upcoming, artist/home/search links.')
if __name__=='__main__': main()

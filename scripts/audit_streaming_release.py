#!/usr/bin/env python3
"""Check the official streaming date, unique work, linkage and generated metadata."""
import json
import re
from pathlib import Path
from structured_data_dates import JSONLD_RE, iter_nodes, types_of
ROOT=Path(__file__).resolve().parents[1]
def main():
    for name in ['creator-cms','releases-catalog']:
        data=json.loads((ROOT/f'assets/data/{name}.json').read_text())
        records=[r for r in data['releases'] if r['slug']=='hanakotoba' or r['title']=='花言葉']
        assert len(records)==1, (name,'duplicate')
        r=records[0]; s=r['streamingRelease']
        assert r['releaseDate']==s['releaseDate']=='2026-09-11'
        assert r['originalReleaseDate']=='2026-08-07'
        assert r['artistSlug']=='enomoto-mia' and r['artist']=='榎本魅愛'
        assert s['linkcoreUrl']=='https://linkco.re/0xHr8N9e'
        assert s['releaseId']=='TCJPR0001951259' and s['artistId']=='1153013'
        assert s['distributionPeriod']=={'start':'2026-09-10','end':'2027-09-09'}
        assert s['coverImage'] is None
    c=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    assert len([n for n in c['news'] if n['slug']=='hanakotoba-streaming-release'])==1
    assert all(any(r['slug']==slug for r in c['releases']) for slug in ['yume-to-kaigo-to-watashitachi','sedai-wo-koete-mama-e'])
    assert (ROOT/'features/suzuka-with-care/index.html').is_file()
    routes=['index.html','releases/index.html','releases/hanakotoba/index.html','artists/enomoto-mia/index.html','news/hanakotoba-streaming-release/index.html']
    for route in routes:
        text=(ROOT/route).read_text()
        assert text.count('class="streaming-release"')==1, route
        assert '2026年9月11日' in text and 'https://linkco.re/0xHr8N9e' in text
        block=re.search(r'<!-- streaming-release:start -->.*?<!-- streaming-release:end -->',text,re.S)[0]
        assert '<img' not in block and '2026.09.10' not in block
        assert 'Label：SUZUKA' in block and 'Distributed via TuneCore Japan' in block
    recordings=0
    for path in ROOT.rglob('index.html'):
        if 'admin' in path.relative_to(ROOT).parts: continue
        for match in JSONLD_RE.finditer(path.read_text()):
            for node in iter_nodes(json.loads(match[2])):
                if 'MusicRecording' in types_of(node) and node.get('name')=='花言葉':
                    recordings+=1
                    assert node['datePublished']=='2026-09-11',path
                    assert node['genre']=='J-Pop' and node['recordLabel']['name']=='SUZUKA',path
                    assert node['byArtist']['name']=='榎本魅愛',path
    assert recordings>0
    print(f'Streaming release audit passed: one work, 5 announcement placements, {recordings} MusicRecording nodes.')
if __name__=='__main__': main()

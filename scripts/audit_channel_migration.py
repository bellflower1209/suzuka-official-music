"""Check identity, history, inaccessible playback and public structured data."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from video_migration import video_id,CHANGE_FIELDS,NOTICE

ROOT=Path(__file__).resolve().parents[1]
class Active(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=='a' and a.get('href'):self.urls.append(a['href'])
        if t=='iframe' and a.get('src'):self.urls.append(a['src'])
def main(root):
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    proof_root=ROOT
    migration=json.loads((proof_root/'docs/channel-migration-20261026.json').read_text())
    works={r['slug']:r for r in cms['releases']};artists={a['slug']:a for a in cms['artists']}
    assert (len(cms['artists']),len(works))==(13,104)
    assert migration['counts']=={'total':36,'migrated':27,'inProgress':9}
    blocked={r['previousVideoId'] for r in migration['records']};assert len(blocked)==36
    for row in migration['records']:
        r=works[row['releaseSlug']]
        assert row['oldWatchStatus']['reason']=='非公開動画' and set(row['changes'])<=CHANGE_FIELDS
        assert r['videoMigration']['status']==row['status']
        protected={k:v for k,v in r.items() if k not in CHANGE_FIELDS}
        assert hashlib.sha256(json.dumps(protected,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==row['protectedFieldsSha256']
        history=next(x for x in r['videoHistory'] if x['youtubeId']==row['previousVideoId'])
        assert history['youtubeUrl']==row['previousUrl'] and history['historicalPublicationPreserved']
        page=(root/r['releaseUrl']/'index.html').read_text()
        if row['status']=='migrated':
            v=row['replacement'];assert r['youtubeUrl']==v['url'] and v['channelId']==artists[r['artistSlug']]['officialYoutubeChannelId']
            assert v['availability']=='public' and v['liveStatus']=='not_live' and v['playabilityStatus']=='OK' and v['isUnlisted'] is False and v['listedOnOfficialChannel']
            assert v['url'] in page and r['videoPublishedAt']==v['publishedAt']
        else:
            assert not r['youtubeUrl'] and r['videoStructuredDataStatus']=='channel-migration'
            assert NOTICE in page and row['officialChannelUrl'] in page
    pages=list(root.glob('**/index.html'))
    # A materialized public package also includes historical numbered HTML.
    if root!=ROOT:pages=list(root.rglob('*.html'))
    active_count=0
    for p in pages:
        if p.relative_to(root).parts[0]=='admin':continue
        s=p.read_text();parser=Active();parser.feed(s)
        wrong=[u for u in parser.urls if video_id(u) in blocked]
        assert not wrong, str(p)+': inaccessible play link '+str(wrong)
        active_count+=len(parser.urls)
        for m in re.finditer(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',s,re.S):
            data=json.loads(m[1])
            def walk(v):
                if isinstance(v,dict):
                    types=v.get('@type',[]);types=[types] if isinstance(types,str) else types
                    if 'VideoObject' in types:
                        assert not any(video_id(v.get(k,'')) in blocked for k in ['contentUrl','embedUrl','url']),str(p)+': private VideoObject'
                    for x in v.values():walk(x)
                elif isinstance(v,list):
                    for x in v:walk(x)
            walk(data)
    sitemap=ET.parse(root/'video-sitemap.xml')
    assert not any(video_id(n.text or '') in blocked for n in sitemap.iter())
    print(json.dumps({'status':'PASS','migrationTotal':36,'publicReplacements':27,'inProgress':9,'historyPreserved':36,'htmlPages':len(pages),'inaccessibleActiveLinks':0,'privateVideoObjects':0,'checkedActiveLinks':active_count}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);main(p.parse_args().root.resolve())

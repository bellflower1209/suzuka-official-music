"""Render verified channel migrations while retaining canonical publication history."""
from __future__ import annotations
import html
import json
from pathlib import Path
import re
from urllib.parse import parse_qs,urlsplit

NOTICE='公式アーティストチャンネルで順次公開予定'
CHANGE_FIELDS=frozenset({'youtubeUrl','youtubeVideoTitle','videoPublishDate','videoPublishedAt','videoPublishedAtSource','videoStructuredDataStatus','youtubeThumbnailUrl','videoLabel','videoButtonLabel','videoCtaLabel','videoVersions','videoMigration','videoHistory'})
JSONLD_RE=re.compile(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',re.I|re.S)
def video_id(value):
    if not isinstance(value,str):return ''
    u=urlsplit(html.unescape(value));host=(u.hostname or '').removeprefix('www.')
    if host=='youtu.be':return u.path.strip('/').split('/')[0]
    if host not in {'youtube.com','youtube-nocookie.com','m.youtube.com'}:return ''
    if u.path=='/watch':return parse_qs(u.query).get('v',[''])[0]
    m=re.match(r'/(?:embed|shorts)/([A-Za-z0-9_-]{11})(?:/|$)',u.path)
    return m[1] if m else ''

def migration_notice(release,*,link=True):
    m=release.get('videoMigration',{})
    if m.get('status')!='in-progress':return ''
    channel=html.escape(m['officialChannelUrl'],quote=True)
    result='<span class="video-migration-notice" data-video-migration="in-progress">'+NOTICE+'。</span>'
    if link:result+=f'<a href="{channel}" target="_blank" rel="noopener noreferrer">公式アーティストチャンネル ↗</a>'
    return result

def undo_migration(release,record):
    """Projection for the dated baseline audit; no unrelated field may change."""
    current=dict(release)
    assert set(record['changes'])<=CHANGE_FIELDS
    for field,change in record['changes'].items():
        assert (field in current)==change['after']['present'],field
        if change['after']['present']:assert current[field]==change['after']['value'],field
        if change['before']['present']:current[field]=change['before']['value']
        else:current.pop(field,None)
    return current

def transform_html(text,records):
    by_old={r['previousVideoId']:r for r in records}
    def resolution(url):return by_old.get(video_id(url))
    def href(match):
        tag=match[0];attrs=re.search(r'\bhref\s*=\s*(["\'])(.*?)\1',tag,re.I|re.S)
        if not attrs:return tag
        record=resolution(attrs[2])
        if not record:return tag
        if record['status']=='migrated':
            start,end=attrs.span(2)
            return tag[:start]+html.escape(record['replacement']['url'],quote=True)+tag[end:]
        # The inaccessible old video is retained in canonical history, not as a play CTA.
        release={'videoMigration':{'status':'in-progress','officialChannelUrl':record['officialChannelUrl']}}
        return '<span data-migration-replaces-link="'+record['releaseSlug']+'">'+migration_notice(release)+'</span>'
    text=re.sub(r'<a\b[^>]*>.*?</a>',href,text,flags=re.I|re.S)
    def frame(match):
        tag=match[0];attrs=re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1',tag,re.I|re.S)
        if not attrs:return tag
        record=resolution(attrs[2])
        if not record:return tag
        if record['status']=='migrated':
            return tag[:attrs.start(2)]+'https://www.youtube-nocookie.com/embed/'+record['replacement']['id']+tag[attrs.end(2):]
        return '<aside class="creator-copy" aria-label="公式動画のチャンネル移行">'+migration_notice({'videoMigration':{'status':'in-progress','officialChannelUrl':record['officialChannelUrl']}})+'</aside>'
    text=re.sub(r'<iframe\b[^>]*>.*?</iframe>',frame,text,flags=re.I|re.S)
    def schema(match):
        data=json.loads(match[2]);removed=set()
        def visit(v):
            if isinstance(v,list):
                for x in v:visit(x)
            elif isinstance(v,dict):
                types=v.get('@type',[]);types=[types] if isinstance(types,str) else types
                record=resolution(v.get('contentUrl','')) or resolution(v.get('embedUrl',''))
                if 'VideoObject' in types and record and record['status']=='in-progress' and v.get('@id'):removed.add(v['@id'])
                for x in v.values():visit(x)
        visit(data)
        def clean(v):
            if isinstance(v,list):return [x for item in v if (x:=clean(item)) is not None]
            if not isinstance(v,dict):return v
            if set(v)=={'@id'} and v['@id'] in removed:return None
            types=v.get('@type',[]);types=[types] if isinstance(types,str) else types
            record=resolution(v.get('contentUrl','')) or resolution(v.get('embedUrl',''))
            if 'VideoObject' in types and record:
                if record['status']=='in-progress':return None
                proof=record['replacement'];v={**v,'contentUrl':proof['url'],'embedUrl':'https://www.youtube.com/embed/'+proof['id'],'name':proof['title'],'uploadDate':proof['publishedAt'],'duration':'PT'+str(proof['duration'])+'S','thumbnailUrl':proof['thumbnail']}
            return {k:x for k,item in v.items() if (x:=clean(item)) is not None}
        result=clean(data)
        if result in [None,[]] or isinstance(result,dict) and result.get('@graph')==[]:return ''
        return match[1]+json.dumps(result,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+match[3]
    return JSONLD_RE.sub(schema,text)

def apply(root):
    report_path=root/'docs/channel-migration-20261026.json'
    if not report_path.is_file():return
    report=json.loads(report_path.read_text());cms=json.loads((root/'assets/data/creator-cms.json').read_text());works={r['slug']:r for r in cms['releases']}
    for p in root.rglob('*.html'):
        if '.git' in p.parts or p.relative_to(root).parts[0]=='admin':continue
        text=p.read_text();text=re.sub(r'<!-- CHANNEL-MIGRATION:START -->.*?<!-- CHANNEL-MIGRATION:END -->','',text,flags=re.S)
        updated=transform_html(text,report['records'])
        for record in report['records']:
            work=works[record['releaseSlug']]
            rel=p.relative_to(root).as_posix()
            if rel not in [work['releaseUrl']+'index.html',work.get('newsUrl','')+'index.html']:continue
            old_id=html.escape(record['previousVideoId'])
            if record['status']=='in-progress':
                block='<aside class="creator-copy" aria-label="公式動画のチャンネル移行"><h2>公式動画のご案内</h2><p>チャンネル移行中です。'+NOTICE+'。作品情報とこれまでの公開履歴は引き続き掲載しています。</p><p>旧動画ID：<code>'+old_id+'</code>（非公開・チャンネル移行）</p><div class="explore-actions">'+migration_notice(work)+'</div></aside>'
            else:
                v=record['replacement']
                block='<aside class="creator-copy" aria-label="公式動画のチャンネル移行"><h2>公式アーティストチャンネルで公開中</h2><p>作品の初公開日・この記事の掲載日は、これまでの公開履歴として保持しています。</p><p>旧動画ID：<code>'+old_id+'</code>（非公開・チャンネル移行）</p><p>新公式動画の公開日：<time datetime="'+html.escape(v['publishedAt'])+'">'+html.escape(v['publishedAt'][:10])+'</time></p><div class="explore-actions"><a href="'+html.escape(v['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">公式アーティストチャンネル版を見る ↗</a></div></aside>'
            # Some historical release pages do not load creator-platform.css.
            # Keep this local panel readable without changing frozen V6 styles.
            if record['status']=='in-progress':block=block.replace(migration_notice(work,link=False),'')
            block=block.replace('class="creator-copy"','class="creator-copy video-migration-panel" style="max-width:70rem;width:calc(100% - 2rem);margin:1.5rem auto;padding:1.25rem;overflow-wrap:anywhere;font-family:var(--cg-sans,sans-serif)"',1)
            block=block.replace('<h2>','<h2 style="font-size:clamp(1.1rem,3vw,1.6rem);line-height:1.4;margin-bottom:.75rem">',1)
            block=block.replace('<p>','<p style="margin:.75rem 0;line-height:1.8">')
            updated=updated.replace('</main>','<!-- CHANNEL-MIGRATION:START -->'+block+'<!-- CHANNEL-MIGRATION:END --></main>',1)
        if updated!=p.read_text():p.write_text(updated)

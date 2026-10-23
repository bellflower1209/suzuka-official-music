"""Regenerate activity content in the frozen public site without adopting V6 changes."""
import argparse, gzip, hashlib, io, json, re, tarfile
from pathlib import Path
import xml.etree.ElementTree as ET
from verify_public_release import read_release, write_output
from official_activity_sections import track_html, note_news_html, shorts_html

BASELINE='2f6c97b206232a69bd2b50d7e628eab2ad9af731'
BASELINE_ARTIFACT='f13be24fa6e42afc0ff8e60dc78220fc3bc413fe7ed322fe7290c807e39c9518'
MANIFEST='suzuka-v6-candidate-manifest.json'
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def section(text, marker, replacement):
    matches=[m for m in re.finditer(r'<section\b[^>]*>',text) if marker in m.group()]
    if len(matches)!=1:raise ValueError('Expected one published section: '+marker)
    start=matches[0].start();depth=0
    for tag in re.finditer(r'</?section\b[^>]*>',text[start:]):
        depth+=-1 if tag.group().startswith('</') else 1
        if depth==0:return text[:start]+replacement+text[start+tag.end():]
    raise ValueError('Unclosed section')

def build(root, output, package):
    # This historical activity-only builder starts from an older V6 archive.
    # Refuse newer public releases: replaying that archive would discard later
    # audio-startup repairs and any new service routes.
    current=json.loads((root/'public-release/release.json').read_text())
    if current.get('artifactDigest')!=BASELINE_ARTIFACT:
        raise ValueError('Historical official-sync baseline is stale; preserve the current verified release and use a current-base builder')
    _,frozen=read_release(root,BASELINE);files=dict(frozen)
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    report=json.loads((root/'docs/official-sync-20261018.json').read_text())
    manifest=json.loads(files[MANIFEST]);routes=set(manifest['v6Routes'])
    for relative in list(files):
        if relative in routes or relative==MANIFEST:continue
        path=root/relative
        if path.is_file() and (relative.endswith('.html') or relative.startswith('assets/data/') and relative.endswith('.json') or relative in {'feed.xml','sitemap.xml','image-sitemap.xml','video-sitemap.xml'}):
            files[relative]=path.read_bytes()
    for slug in report['addedReleases']+report['addedStreamingReleases']:
        for group in ['releases','news']:
            relative=f'{group}/{slug}{"-release" if group=="news" else ""}/index.html'
            files[relative]=(root/relative).read_bytes()
    for slug in report['addedNews']:
        relative=f'news/{slug}/index.html';files[relative]=(root/relative).read_bytes()
    for r in cms['releases']:
        if r['slug'] in report['addedStreamingReleases']:files[r['coverImage']]=(root/r['coverImage']).read_bytes()
    releases=sorted(cms['releases'],key=lambda r:(r.get('publishedAt') or r.get('releaseDate') or '',r['slug']),reverse=True)
    notes=sorted([n for n in cms['news'] if n.get('status')=='published' and n.get('noteUrl')],key=lambda n:(n['publishedAt'],n['slug']),reverse=True)
    shorts=sorted([s for s in cms['youtubeSnapshot']['shortVideos'] if s.get('status')=='published' and s.get('contentType')=='short'],key=lambda s:(s['publishedAt'],s['videoId']),reverse=True)
    for route in manifest['v6Routes']:
        text=frozen[route].decode();original=text
        if route=='index.html':
            replacement='<section class="music-section" id="latest-releases" aria-labelledby="latest-releases-title"><div class="section-heading"><div><p class="eyebrow">LATEST MUSIC & STORIES</p><h2 id="latest-releases-title">いま、響く音楽。</h2></div><a href="/releases/">すべての作品 ↗</a></div><div class="music-grid">'+''.join(track_html(r,'/',i==0,root) for i,r in enumerate(releases[:6]))+'</div></section>'
            text=section(text,'id="latest-releases"',replacement)
            text=section(text,'aria-labelledby="official-news-title"',note_news_html(notes,'/',root,title_id='official-news-title'))
        else:
            slug=route.split('/')[1];artist=next(a for a in cms['artists'] if a['slug']==slug)
            tracks=[r for r in releases if slug in r.get('artistSlugs',[r['artistSlug']])]
            replacement='<section class="music-section" id="music" aria-labelledby="music-title"><div class="section-heading"><div><p class="eyebrow">MUSIC & STORIES</p><h2 id="music-title">この世界に、響く音楽。</h2></div><p>'+str(len(tracks))+' WORKS · 作品、映像、歌詞、配信へ。</p></div><div class="music-grid">'+''.join(track_html(r,'/',i==0,root) for i,r in enumerate(tracks))+'</div></section>'
            text=section(text,'id="music"',replacement)
            selected=[s for s in shorts if s['artistSlug']==slug]
            if selected:
                block=shorts_html(selected,artist,'/')
                text=section(text,'aria-labelledby="shorts-title"',block) if 'aria-labelledby="shorts-title"' in text else text.replace('<section class="next-worlds"',block+'<section class="next-worlds"',1)
            selected=[n for n in notes if n.get('artistSlug')==slug]
            if selected:text=section(text,'aria-labelledby="artist-note-title"',note_news_html(selected,'/',root,title_id='artist-note-title'))
        # All headers, hero imagery, animation config, JS, CSS, audio policy and SEO stay frozen.
        def mask(t):
            for marker in ['id="latest-releases"','aria-labelledby="official-news-title"','id="music"','aria-labelledby="shorts-title"','aria-labelledby="artist-note-title"']:
                if re.search(r'<section\b[^>]*'+re.escape(marker),t):t=section(t,marker,'')
            return t
        assert mask(text)==mask(original),'Non-activity V6 change: '+route
        files[route]=text.encode()
    for name in ['sitemap.xml','image-sitemap.xml','video-sitemap.xml']:
        old=ET.fromstring(frozen[name]);current=ET.fromstring(files[name]);ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        existing={n.findtext('s:loc',namespaces=ns) for n in current}
        for n in old:
            if n.findtext('s:loc',namespaces=ns) not in existing:current.append(n)
        for prefix,uri in [('',ns['s']),('image','http://www.google.com/schemas/sitemap-image/1.1'),('video','http://www.google.com/schemas/sitemap-video/1.1')]:ET.register_namespace(prefix,uri)
        ET.indent(current,space='  ');files[name]=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(current,encoding='utf-8',xml_declaration=False)+b'\n'
    assert set(frozen)<=set(files),'Existing public URL removed'
    for name,data in frozen.items():
        if name.startswith('images/') or name.endswith(('.css','.js')):assert files[name]==data,'Existing official image or runtime changed: '+name
    assert not any(name.endswith(('.mp3','.wav','.m4a')) or name.startswith('v6/') for name in files)
    manifest['sourceCanonicalSha256']=sha(files['assets/data/creator-cms.json'])
    manifest['officialSync']={'verifiedAt':report['verifiedAt'],'sourceMain':BASELINE,'scope':'official-activity-only; published V6 presentation/runtime unchanged'}
    manifest['files']={p:sha(data) for p,data in sorted(files.items()) if p!=MANIFEST}
    manifest['sourceV5Sha256']={p:sha((root/p).read_bytes()) for p in manifest['sourceV5Sha256'] if (root/p).exists()}
    files[MANIFEST]=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    write_output(output,files)
    def archive():
        out=io.BytesIO()
        with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as tar:
                for name,data in sorted(files.items()):
                    member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o644;member.mtime=0;tar.addfile(member,io.BytesIO(data))
        return out.getvalue()
    data=archive();assert data==archive();package.mkdir(parents=True,exist_ok=True)
    chunks=[];size=45*1024*1024
    for i,start in enumerate(range(0,len(data),size)):
        chunk=data[start:start+size];name=f'site-{i:02d}.tar.gz.part';(package/name).write_bytes(chunk)
        chunks.append({'path':'public-release/'+name,'bytes':len(chunk),'sha256':sha(chunk)})
    hashes={p:sha(b) for p,b in files.items()}
    descriptor={'format':'suzuka-public-release-v1','artifactDigest':sha(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()),'fileCount':len(files),'contentBytes':sum(map(len,files.values())),'archiveBytes':len(data),'archiveSha256':sha(data),'chunks':chunks}
    (package/'release.json').write_text(json.dumps(descriptor,indent=2)+'\n')
    print(json.dumps({'status':'PASS','files':len(files),'preservedFiles':len(frozen),'deleted':0,'changed':sum(files[p]!=v for p,v in frozen.items()),'added':len(files)-len(frozen),'deterministicArchive':True,'artifactDigest':descriptor['artifactDigest']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--package',type=Path,required=True)
    args=parser.parse_args();build(args.root.resolve(),args.output.resolve(),args.package.resolve())

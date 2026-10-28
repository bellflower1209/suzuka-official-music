"""Update activity from the verified 934a63b package; preserve V6 and services."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
from build_official_sync_package import section
from build_music_production_release import add_navigation, package, sha
from html import escape
from official_activity_sections import track_html, note_news_html, shorts_html
from verify_public_release import read_release, verify_private_audio, write_output
from video_migration import transform_html

ROOT=Path(__file__).resolve().parents[1]
BASE='934a63b79a7bdda85f4839aa77d3576a2987ee0a'
DIGEST='f04e74f41c742321aec555e06c990a05efa96ec9781529624755841f87956fa1'
MANIFEST='suzuka-v6-candidate-manifest.json'
def mask(text):
    for marker in ['id="latest-releases"','aria-labelledby="official-news-title"','id="music"','aria-labelledby="shorts-title"','aria-labelledby="artist-note-title"','aria-labelledby="additional-artists-title"']:
        if re.search(r'<section\b[^>]*'+re.escape(marker),text):text=section(text,marker,'')
    return text
def build(root):
    info,original=read_release(root,BASE)
    if info['artifactDigest']!=DIGEST or info['fileCount']!=784:raise ValueError('Baseline changed; review required')
    files=dict(original);manifest=json.loads(original[MANIFEST]);routes=set(manifest['v6Routes'])
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    report=json.loads((root/'docs/official-sync-20261026.json').read_text())
    migrations=json.loads((root/'docs/channel-migration-20261026.json').read_text())
    for name in original:
        if name in routes or name==MANIFEST or name=='music-production/index.html':continue
        path=root/name
        if path.is_file() and (name.endswith('.html') or name.startswith('assets/data/') and name.endswith('.json') or name in ['feed.xml','sitemap.xml','image-sitemap.xml','video-sitemap.xml']):
            data=path.read_bytes()
            if name.endswith('.html') and name!='404.html':data=add_navigation(name,data.decode()).encode()
            files[name]=data
    # Only the search/display renderer needs a public JS change. V6, audio,
    # service worker, cinematic assets and the service page stay byte-frozen.
    files['assets/explore.js']=(root/'assets/explore.js').read_bytes()
    for slug in report['addedReleases']:
        for name in [f'releases/{slug}/index.html',f'news/{slug}-release/index.html']:
            files[name]=add_navigation(name,(root/name).read_text()).encode()
    for slug in report['addedNews']:
        name=f'news/{slug}/index.html';files[name]=add_navigation(name,(root/name).read_text()).encode()
    for artist in report['addedArtists']:
        name=f'artists/{artist["slug"]}/index.html';files[name]=add_navigation(name,(root/name).read_text()).encode()
    for image in report['addedImages']:
        data=(root/image['path']).read_bytes()
        if sha(data)!=image['sha256']:raise ValueError('Official note image changed')
        files[image['path']]=data
    releases=sorted(cms['releases'],key=lambda r:(r.get('publishedAt') or r.get('releaseDate') or '',r['slug']),reverse=True)
    notes=sorted([n for n in cms['news'] if n.get('status')=='published' and n.get('noteUrl')],key=lambda n:(n['publishedAt'],n['slug']),reverse=True)
    shorts=sorted([s for s in cms['youtubeSnapshot']['shortVideos'] if s.get('status')=='published' and s.get('contentType')=='short'],key=lambda s:(s['publishedAt'],s['videoId']),reverse=True)
    for name in manifest['v6Routes']:
        old=original[name].decode();text=old
        if name=='index.html':
            block='<section class="music-section" id="latest-releases" aria-labelledby="latest-releases-title"><div class="section-heading"><div><p class="eyebrow">LATEST MUSIC & STORIES</p><h2 id="latest-releases-title">いま、響く音楽。</h2></div><a href="/releases/">すべての作品 ↗</a></div><div class="music-grid">'+''.join(track_html(r,'/',i==0,root) for i,r in enumerate(releases[:6]))+'</div></section>'
            text=section(text,'id="latest-releases"',block)
            artist_cards=''.join('<article class="track-copy"><p class="eyebrow">NEW ARTIST</p><h3><a href="/artists/'+escape(a['slug'])+'/">'+escape(a['name'])+' ↗</a></h3><p>'+escape(a['profile'])+'</p><div class="track-links"><a href="/artists/'+escape(a['slug'])+'/">公式アーティストページ ↗</a></div></article>' for a in report['addedArtists'])
            addition='<section class="music-section" aria-labelledby="additional-artists-title"><div class="section-heading"><div><p class="eyebrow">MORE MUSIC, MORE STORIES</p><h2 id="additional-artists-title">新たな音楽との出会い。</h2></div></div><div class="music-grid">'+artist_cards+'</div></section>'
            text=text.replace('<section class="music-section" id="latest-releases"',addition+'<section class="music-section" id="latest-releases"',1)
            text=section(text,'aria-labelledby="official-news-title"',note_news_html(notes,'/',root,title_id='official-news-title'))
        else:
            slug=name.split('/')[1];artist=next(a for a in cms['artists'] if a['slug']==slug)
            tracks=[r for r in releases if slug in r.get('artistSlugs',[r['artistSlug']])]
            block='<section class="music-section" id="music" aria-labelledby="music-title"><div class="section-heading"><div><p class="eyebrow">MUSIC & STORIES</p><h2 id="music-title">この世界に、響く音楽。</h2></div><p>'+str(len(tracks))+' WORKS · 作品、映像、歌詞、配信へ。</p></div><div class="music-grid">'+''.join(track_html(r,'/',i==0,root) for i,r in enumerate(tracks))+'</div></section>'
            text=section(text,'id="music"',block)
            selected=[s for s in shorts if s['artistSlug']==slug]
            if selected:
                block=shorts_html(selected,artist,'/')
                text=section(text,'aria-labelledby="shorts-title"',block) if 'aria-labelledby="shorts-title"' in text else text.replace('<section class="next-worlds"',block+'<section class="next-worlds"',1)
            selected=[n for n in notes if n.get('artistSlug')==slug]
            if selected:
                block=note_news_html(selected,'/',root,title_id='artist-note-title')
                if 'aria-labelledby="artist-note-title"' in text:
                    text=section(text,'aria-labelledby="artist-note-title"',block)
                else:
                    if text.count('<section class="next-worlds"')!=1:raise ValueError('Missing insertion point: '+name)
                    text=text.replace('<section class="next-worlds"',block+'<section class="next-worlds"',1)
        if mask(old)!=mask(text):raise ValueError('V6 presentation changed: '+name)
        files[name]=text.encode()
    for name,data in list(files.items()):
        if name.endswith('.html'):files[name]=transform_html(data.decode(),migrations['records']).encode()
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for name in ['sitemap.xml','image-sitemap.xml','video-sitemap.xml']:
        previous=ET.fromstring(original[name]);current=ET.fromstring(files[name])
        existing={n.findtext('s:loc',namespaces=ns) for n in current}
        for n in previous:
            if n.findtext('s:loc',namespaces=ns) not in existing:current.append(n)
        if name=='video-sitemap.xml':
            video_ns='{http://www.google.com/schemas/sitemap-video/1.1}'
            blocked={r['previousVideoId']:r for r in migrations['records']}
            from video_migration import video_id
            for entry in list(current):
                for video in list(entry.findall(video_ns+'video')):
                    record=next((blocked.get(video_id(video.findtext(video_ns+k,''))) for k in ['content_loc','player_loc'] if blocked.get(video_id(video.findtext(video_ns+k,'')))),None)
                    if not record:continue
                    if record['status']=='in-progress':entry.remove(video);continue
                    v=record['replacement']
                    for key,value in {'content_loc':v['url'],'player_loc':'https://www.youtube.com/embed/'+v['id'],'publication_date':v['publishedAt'],'duration':str(v['duration']),'title':v['title'][:100],'thumbnail_loc':v['thumbnail']}.items():
                        node=video.find(video_ns+key)
                        if node is not None:node.text=value
                if not entry.findall(video_ns+'video'):current.remove(entry)
        for prefix,uri in [('',ns['s']),('image','http://www.google.com/schemas/sitemap-image/1.1'),('video','http://www.google.com/schemas/sitemap-video/1.1')]:ET.register_namespace(prefix,uri)
        ET.indent(current,space='  ');files[name]=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(current,encoding='utf-8')+b'\n'
    if not set(original)<=set(files):raise ValueError('Existing public URL removed')
    for name,data in original.items():
        if name.startswith('images/') or name.endswith(('.css','.js')) and name!='assets/explore.js' or name.startswith('music-production/'):
            if files[name]!=data:raise ValueError('Protected media/runtime/service changed: '+name)
    verify_private_audio(info,files,manifest['v6Routes'])
    manifest['sourceCanonicalSha256']=sha(files['assets/data/creator-cms.json'])
    manifest['officialSync']={'verifiedAt':migrations['verifiedAt'],'sourceMain':BASE,'scope':'official activity and verified channel migration; V6/audio runtime, imagery and MUSIC PRODUCTION unchanged'}
    manifest['channelMigration']={'total':36,'migrated':27,'inProgress':9,'oldIdsAndPublicationHistoryPreserved':True}
    manifest['sourceV5Sha256']={p:sha((root/p).read_bytes()) for p in manifest['sourceV5Sha256'] if (root/p).is_file()}
    manifest['files']={name:sha(data) for name,data in sorted(files.items()) if name!=MANIFEST}
    files[MANIFEST]=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    modified=[n for n in original if files[n]!=original[n]]
    summary={'files':len(files),'preservedFiles':len(original),'deletedFiles':[],'addedFiles':sorted(set(files)-set(original)),'changedFiles':sorted(modified),'byteIdenticalFiles':len(original)-len(modified),'sitemapUrls':len(ET.fromstring(files['sitemap.xml']))}
    return info,files,summary
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args();root=args.root.resolve()
    info,files,summary=build(root);chunks=package(info,files)
    if args.check:
        if {p.name for p in (root/'public-release').iterdir()}!=set(chunks):raise ValueError('Chunk inventory changed')
        for name,data in chunks.items():
            if (root/'public-release'/name).read_bytes()!=data:raise ValueError('Non-reproducible package: '+name)
    else:
        with tempfile.TemporaryDirectory(prefix='official-sync-20261026-') as tmp:
            for name,data in chunks.items():
                p=Path(tmp)/name;p.write_bytes(data)
                # Only current branch's generated chunks are replaced.
                (root/'public-release'/name).write_bytes(p.read_bytes())
    if args.output:write_output(args.output,files)
    print(json.dumps({'status':'PASS','mode':'check' if args.check else 'write','artifactDigest':json.loads(chunks['release.json'])['artifactDigest'],**summary},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

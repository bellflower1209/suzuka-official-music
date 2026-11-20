"""Render verified November activity on the approved production package."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

from build_official_sync_package import section
from build_v6_growth_preview import SITE, e, encoded, link, music_section, page
from verify_public_release import MANIFEST, ROOT, digest, materialize, read_release, verify_private_audio

SOURCE = ROOT / 'site-content/activity-20261121'
BASE_DIGEST = 'af64886f0eb95704cb475864eb2467ea0aaf54947a6029b76a84f0ce0e432d8b'
ARTISTS = {'enomoto-mia': '榎本魅愛', 'koga-kamishiro': '神代煌牙', 'asteria': 'ASTERIA'}
UPDATED = '2026-11-21T00:00:00+09:00'
NEWS_ROUTE = 'news/november-music-20261121/'


def activity_section(heading, rows):
    items = []
    for date, label, url in rows:
        items.append('<article><time datetime="' + e(date) + '">' + e(date[:10]) + '</time><h3>' +
                     link(url, label, cls='growth-text-link') + '</h3></article>')
    return ('<section class="growth-section"><div class="growth-heading"><h2>' + e(heading) +
            '</h2></div><div class="growth-news">' + ''.join(items) + '</div></section>')


def build():
    info, original = read_release(ROOT)
    if info['artifactDigest'] != BASE_DIGEST:
        raise ValueError('Review the changed production base before applying this release')
    files = dict(original)
    activity = json.loads((SOURCE / 'activity.json').read_text())
    streams = {item['slug']: item for item in activity['streams']}
    videos = defaultdict(list)
    for video in activity['videos']:
        videos[video['slug']].append(video)
    plan = activity['scheduled']
    cms = json.loads(files['assets/data/creator-cms.json'])
    works = {r['slug']: r for r in cms['releases']}
    new = []
    sources = json.loads((ROOT / 'site-content/v6-growth/verified-sources.json').read_text())
    policy = json.loads((ROOT / 'site-content/v6-growth/store-link-policy.json').read_text())
    sources['_suppressedStores'] = {(x['linkcoreCode'],x['service']) for x in policy['suppressed']}
    for path in sorted(SOURCE.glob('*.webp')):
        files['images/november-2026/' + path.name] = path.read_bytes()

    def change(route, transform):
        files[route] = transform(files[route].decode()).encode()

    def after(route, marker, block):
        def insert(text):
            if text.count(marker) != 1:
                raise ValueError('Missing or ambiguous insert point: ' + route + ' ' + marker)
            return text.replace(marker, marker + block, 1)
        change(route, insert)

    def before_end(route, block):
        change(route, lambda text: text.replace('</main>', block + '</main>', 1))

    for slug in dict.fromkeys([*streams, *videos]):
        stream = streams.get(slug)
        events = videos.get(slug, [])
        item = stream or events[0]
        artist_slug, title = item['artistSlug'], item['title']
        artist = ARTISTS[artist_slug]
        route = f'releases/{slug}/'
        full = next((v for v in events if v['kind'] != 'Shorts'), None)
        image = f'images/november-2026/{slug}.webp'
        initial = slug not in works
        if initial:
            dates = [v['publishedAt'] for v in events] + ([stream['date']] if stream else [])
            published = min(dates)
            r = dict(id=slug, slug=slug, title=title, displayTitle=title, artist=artist, artistSlug=artist_slug,
                     artistSlugs=[artist_slug], artistType='MusicGroup' if artist_slug=='asteria' else 'Person',
                     status='published', releaseDate=published[:10], publishedAt=published, releaseYear=2026,
                     releaseUrl=route, genres=[], themes=[], tags=[title,artist], searchKeywords=[title,artist],
                     youtubeUrl='', duration=0, lyricsAvailable=False, lyricsVerified=False, relatedReleases=[],
                     coverImage=image, coverAlt=f'{artist}「{title}」公式映像サムネイル',
                     imageRole='official-youtube-thumbnail', artworkStatus='pending-formal-jacket',
                     releaseType='medley' if full and full['kind']=='5曲メドレー' else 'single')
            if full:
                r.update(youtubeUrl=full['url'], videoPublishedAt=full['publishedAt'], duration=full['seconds'],
                         videoCtaLabel=full['kind']+'を聴く')
            elif stream:
                r['publicationEvidenceType']='verified-streaming-only'
            works[slug]=r
            cms['releases'].append(r)
            new.append(r)
        r = works[slug]
        lines, actions = [], []
        if stream:
            date=stream['date']
            s=dict(status='published',releaseDate=date,linkcoreUrl=stream['url'],timezone='Asia/Tokyo',verifiedAt=UPDATED)
            r.update(scheduledStreamingRelease=s, formalJacketImage=image, coverImage=image,
                     coverAlt=f'{artist}「{title}」配信ジャケット', artworkStatus='verified-public-linkcore',
                     imageRole='official-linkcore-artwork', coverSource=stream['artwork'])
            sources['streaming'].append(dict(code=stream['url'].rsplit('/',1)[1],url=stream['url'],releaseDate=date,stores=[]))
            lines.append(date+' ストリーミング配信開始')
            actions.append(link(stream['url'],'配信サービスで聴く',action='streaming',slug=slug,artist=artist_slug,service='linkcore'))
        if slug==plan['slug']:
            r['scheduledStreamingRelease']=dict(status='scheduled',releaseDate=plan['date'],linkcoreUrl=plan['url'],timezone='Asia/Tokyo',verifiedAt=UPDATED)
            lines.append('2026年12月9日 ストリーミング配信予定')
            actions.append(link(plan['url'],'配信予定を見る'))
        if slug==plan['slug']:
            r.update(videoCtaLabel='告知Shortsを見る')
        for v in events:
            dt=v['publishedAt']
            lines.append(dt[:10]+' '+dt[11:16]+'（JST） '+v['kind']+'公開')
            actions.append(link(v['url'],v['kind']+'を'+('見る' if v['kind']=='Shorts' else '聴く')))
            if v['kind']=='Shorts':
                shorts=r.setdefault('relatedShorts',[])
                if v['url'] not in shorts: shorts.append(v['url'])
                if not r.get('shortsUrl'): r['shortsUrl']=v['url']
                cms['youtubeSnapshot']['shortVideos'].append(dict(videoId=v['videoId'],title=title,artist=artist,artistSlug=artist_slug,
                    publishedAt=dt,duration=v['seconds'],youtubeUrl=v['url'],relatedRelease=slug,contentType='short',status='published',
                    thumbnail=f"https://i.ytimg.com/vi/{v['videoId']}/hqdefault.jpg",officialChannelId=v['channelId'],verifiedAt=UPDATED))
            elif not initial:
                versions=r.setdefault('videoVersions',[])
                if not any(x.get('youtubeUrl')==v['url'] for x in versions):
                    versions.append(dict(youtubeUrl=v['url'],label=v['kind'],publishedAt=dt))
        summary='。'.join(lines)+'。'
        info_html='<ul>'+''.join('<li>'+e(line)+'</li>' for line in lines)+'</ul><div class="growth-actions">'+''.join(actions)+'</div>'
        if initial:
            r['description']=artist+'「'+title+'」。'+summary
            src='/'+image
            content='<section class="growth-section growth-release"><h1>'+e(title)+'</h1><p>'+e(artist)+'</p><div class="growth-release-grid"><img src="'+src+'" alt="'+e(r['coverAlt'])+'"><div>'+info_html+link('/worlds/'+artist_slug+'/','アーティストの作品一覧')+'</div></div></section>'
            files[route+'index.html']=page(title+'｜'+artist,r['description'],route,content,original,image=image,
                graph={'@type':'MusicRecording','@id':SITE+'/'+route+'#recording','name':title,'url':SITE+'/'+route,
                       'byArtist':{'@id':SITE+'/artists/'+artist_slug+'/#artist'},'image':SITE+src,'datePublished':r['publishedAt']})
        else:
            block='<section class="growth-section"><h2>最新の配信・動画</h2>'+info_html+'</section>'
            change(route+'index.html',lambda text:text.replace('</h1>','</h1>'+block,1))
    pending=dict(id=plan['slug'],slug=plan['slug'],title=plan['title'],artist='榎本魅愛',artistSlug=plan['artistSlug'],
                 status='scheduled',releaseDate=plan['date'],dateType='scheduled-streaming',linkcoreUrl=plan['url'],
                 officialSource=plan['source'],requiresPublicReverification=True)
    cms['upcoming']=[x for x in cms['upcoming'] if x['slug']!='last-ignition']+[pending]
    cms['updatedAt']=UPDATED
    cms['youtubeSnapshot']['registeredShortsCount']=len(cms['youtubeSnapshot']['shortVideos'])
    files['assets/data/creator-cms.json']=encoded(cms)
    cat=json.loads(files['assets/data/releases-catalog.json'])
    cat['releases']=[{**x,**works[x['slug']]} for x in cat['releases']]+new
    cat.update(updatedAt=UPDATED,upcoming=cms['upcoming'])
    files['assets/data/releases-catalog.json']=encoded(cat)
    upcoming=json.loads(files['assets/data/upcoming-releases.json'])
    upcoming.update(updatedAt=UPDATED,releases=cms['upcoming'])
    files['assets/data/upcoming-releases.json']=encoded(upcoming)
    links=json.loads(files['assets/data/release-links.json'])
    records={r['slug']:r for r in links['releases']}
    for slug in set(streams)|set(videos):
        r=works[slug]
        if slug not in records:
            entry=dict(slug=slug,title=r['title'],artist=r['artist'],artistSlug=r['artistSlug'],releasePage=r['releaseUrl'],
                       status='published',playerEnabled=False,youtubeUrl=r.get('youtubeUrl',''),image=r['coverImage'])
            records[slug]=entry; links['releases'].append(entry)
        if slug in streams: records[slug]['linkcoreUrl']=streams[slug]['url']
        if r.get('shortsUrl'): records[slug]['shortsUrl']=r['shortsUrl']
    links['releases'].sort(key=lambda v:v['slug'])
    links['updatedAt']=UPDATED
    files['assets/data/release-links.json']=encoded(links)
    search=json.loads(files['assets/data/search-v31.json'])
    for r in new:
        search['documents'].append(dict(type='Release',contentType='release',title=r['title'],description=r['description'],url=r['releaseUrl'],keywords=r['tags']))
    search['updatedAt']=UPDATED
    files['assets/data/search-v31.json']=encoded(search)
    ordered=[works[k] for k in streams]
    recent=sorted(new,key=lambda x:x['publishedAt'],reverse=True)
    home='index.html'
    def grid(title,subtitle,rows,**kw):
        return music_section(title,subtitle,rows,sources,files,**kw)
    change(home,lambda s:section(s,'id="listen"',grid('LISTEN TO SUZUKA','最新配信作品',ordered[:6],section_id='listen',streaming=True)))
    change(home,lambda s:section(s,'id="latest-releases"',grid('NEW RELEASE','最新の公開作品',recent[:6],section_id='latest-releases')))
    # A Shorts-first release has only a teaser available; its card links to the actual published version.
    for a in ARTISTS:
        subset=[r for r in works.values() if r['artistSlug']==a]
        subset.sort(key=lambda r:max([r['releaseDate']]+[v['publishedAt'] for v in videos.get(r['slug'],[])]+([streams[r['slug']]['date']] if r['slug'] in streams else [])),reverse=True)
        route='worlds/'+a+'/index.html'
        change(route,lambda s:section(s,'id="music"',grid('この世界に、響く音楽。',str(len(subset))+' WORKS',subset,section_id='music')))
        rows=[(v['publishedAt'],v['title']+'（'+v['kind']+'）',v['url']) for v in activity['videos'] if v['artistSlug']==a]
        block=activity_section('11月の公式動画',rows)
        before_end(route,block)
        artist_route='artists/'+a+'/index.html'
        if a=='asteria':change(artist_route,lambda s:section(s,'id="growth-upcoming"',''))
        others=[r for r in ordered if r['artistSlug']==a]
        if others:
            block_stream=grid('配信サービスで聴く','最新配信作品',others,section_id='listen-artist',streaming=True)
            if 'id="listen-artist"' in files[artist_route].decode():
                change(artist_route,lambda s:section(s,'id="listen-artist"',block_stream))
            else:before_end(artist_route,block_stream)
        latest_marker='<section class="v31-artist-facts"'
        change(artist_route,lambda s:s.replace(latest_marker,block+latest_marker,1))
    all_streams=[(x['date'],ARTISTS[x['artistSlug']]+'「'+x['title']+'」','/releases/'+x['slug']+'/') for x in activity['streams']]
    all_vids=[(x['publishedAt'],ARTISTS[x['artistSlug']]+'「'+x['title']+'」 '+x['kind'],x['url']) for x in activity['videos']]
    notes=[(x['publishedAt'],x['title'],x['url']) for x in activity['notes']]
    notice='榎本魅愛『本当の言葉』は12月9日配信予定。11月20日に公開した15秒のShortsを作品ページでご覧いただけます。'
    upcoming_block='<section class="growth-section"><h2>12月9日 配信予定</h2><p>'+notice+'</p>'+link('/releases/hontou-no-kotoba/','本当の言葉')+'</section>'
    news_title='SUZUKA 11月の配信・公式動画'
    news_body='<section class="growth-section"><h1>'+news_title+'</h1><p>2026年11月21日更新</p></section>'+upcoming_block+activity_section('11月の配信作品',all_streams)+activity_section('公式動画・Shorts',all_vids)+activity_section('公式note',notes)
    files[NEWS_ROUTE+'index.html']=page(news_title,notice,NEWS_ROUTE,news_body,original)
    for route in ['news/index.html',home]:
        marker='<div class="growth-news">'
        after(route,marker,'<article><time datetime="2026-11-21">2026-11-21</time><h3>'+link('/'+NEWS_ROUTE,news_title)+'</h3></article>')
    highlights=grid('11月の公開作品','NEW RELEASE',recent)+activity_section('11月のストリーミング配信',all_streams)
    for route, marker in [('releases/index.html','<section class="section music-section release-directory"'),
                          ('discography/index.html','<section class="explore-shell"')]:
        change(route,lambda s:s.replace(marker,highlights+marker,1))
    change('news/index.html',lambda s:s.replace('<section class="section news-section news-directory"',activity_section('最新のお知らせ',[(UPDATED,news_title,'/'+NEWS_ROUTE)])+'<section class="section news-section news-directory"',1))
    schedule='schedule/index.html'
    change(schedule,lambda s:section(s,'id="growth-upcoming"',''))
    after(schedule,'<section class="v31-schedule-group" id="later"><h2>Later</h2>',upcoming_block)
    before_end(schedule,activity_section('11月の配信開始',all_streams))
    # Keep only public evidence in the published index.
    files['assets/data/official-activity-20261121.json']=encoded(activity)
    added_routes=[x['releaseUrl'] for x in new]+[NEWS_ROUTE]
    sm=files['sitemap.xml'].decode()
    files['sitemap.xml']=sm.replace('</urlset>',''.join('  <url><loc>'+SITE+'/'+r+'</loc></url>\n' for r in added_routes)+'</urlset>').encode()
    a='{http://www.w3.org/2005/Atom}'
    feed=ET.fromstring(files['feed.xml']);feed.find(a+'updated').text=UPDATED
    entry=ET.Element(a+'entry')
    for k,v in {'id':SITE+'/'+NEWS_ROUTE,'title':news_title,'updated':UPDATED,'summary':notice}.items():ET.SubElement(entry,a+k).text=v
    ET.SubElement(entry,a+'link',{'href':SITE+'/'+NEWS_ROUTE})
    feed.insert(list(feed).index(feed.find(a+'entry')),entry)
    ET.register_namespace('',a[1:-1]);files['feed.xml']=ET.tostring(feed,encoding='utf-8',xml_declaration=True)
    # Retain the complete signed-off base inventory and bind every new byte to the reviewed release.
    manifest=json.loads(original[MANIFEST])
    manifest['novemberActivity']={'date':activity['verifiedOn'],'baseDigest':BASE_DIGEST,'works':len(works)}
    manifest['files']={p:digest(data) for p,data in files.items() if p!=MANIFEST}
    files[MANIFEST]=encoded(manifest)
    verify_private_audio(info,files,manifest['v6Routes'])
    for slug in set(streams)|set(videos):
        r=works[slug];detail=files[r['releaseUrl']+'index.html'].decode()
        if any(v['url'] not in detail for v in videos.get(slug,[])) or (slug in streams and streams[slug]['url'] not in detail):
            raise ValueError('Missing work source: '+slug)
    if not all(x['releaseUrl'] in files['releases/index.html'].decode() for x in new):
        raise ValueError('Release directory is incomplete')
    return files


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',type=Path)
    args=p.parse_args()
    files=build()
    hash_map={path:digest(data) for path,data in files.items()}
    actual=digest(json.dumps(hash_map,sort_keys=True,separators=(',',':')).encode())
    expected=(SOURCE/'release.sha256').read_text().strip()
    if actual!=expected:raise ValueError('Rendered output differs from approved digest: '+actual)
    materialize(ROOT,args.output,files,args.stage)
    print('Verified November release:',actual,len(files),'files')


if __name__=='__main__':
    main()

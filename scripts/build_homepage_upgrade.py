#!/usr/bin/env python3
"""Generate current label, streaming, official channels and verified series surfaces."""
from __future__ import annotations
import html
import json
import re
from pathlib import Path
from build_explorer_update import shell
from build_creator_platform import analytics
from build_creator_platform_v31 import analytics_v31
from build_brand_discovery_v11 import normalize_graph, standardize_channel_links, youtube_channel_url

E = html.escape
START = '<!-- HOME-UPGRADE:START -->'
END = '<!-- HOME-UPGRADE:END -->'


def link(url: str, label: str) -> str:
    if not url:
        return ''
    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith('https://') else ''
    return f'<a href="{E(url, quote=True)}"{external}>{E(label)}</a>'


def streaming(item: dict) -> dict:
    value = item.get('scheduledStreamingRelease') or item.get('streamingRelease') or {}
    confirmed = value.get('status') == 'published' and value.get('verifiedAt')
    # Legacy streamingRelease is a user-confirmed release, separate from a scheduled plan.
    if value.get('linkcoreUrl') and (confirmed or item.get('streamingRelease') is value):
        return value
    return {}


def visual(root: Path, image: str, alt: str, prefix='./', square=False) -> str:
    if not image:
        return ''
    external = image.startswith('https://')
    if not external and not (root / image).is_file():
        raise FileNotFoundError(f'Canonical image missing: {image}')
    return f'<img src="{E(image if external else prefix+image)}" alt="{E(alt)}" width="{400 if square else 1280}" height="{400 if square else 720}" loading="lazy"/>'


def work_card(root: Path, item: dict, *, listen=False, video=False, prefix="./") -> str:
    s=streaming(item)
    media_label=item.get('videoButtonLabel') or ('WATCH MV' if 'MV' in item.get('videoLabel','') else 'WATCH VIDEO')
    actions=link(prefix+item['releaseUrl'], '作品情報')
    if listen:actions += link(s.get('linkcoreUrl',''), 'LISTEN NOW ↗')
    if item.get('youtubeUrl'):actions += link(item['youtubeUrl'],media_label+' ↗')
    date=s['releaseDate'] if listen else item.get('videoPublishDate') or item['releaseDate']
    return (f'<article class="upgrade-card" data-work-slug="{E(item["slug"])}">'
            +visual(root,item['coverImage'],item['coverAlt'],prefix=prefix,square=item.get('coverWidth')==item.get('coverHeight'))
            +f'<div><p>{E(item["artist"])}</p><h3>{E(item["title"])}</h3><p>{"配信開始" if listen else "動画公開" if video else "作品公開"} <time datetime="{date}">{date.replace("-", ".")}</time></p><div class="explore-actions">{actions}</div></div></article>')


def section(id: str, title: str, body: str, subtitle='') -> str:
    return f'<section class="upgrade-section" id="{id}" aria-labelledby="{id}-title"><p class="section-kicker">SUZUKA / MUSIC × AI × STORY</p><h2 id="{id}-title">{E(title)}</h2>'+ (f'<p>{E(subtitle)}</p>' if subtitle else '')+body+'</section>'


def build(root: Path) -> None:
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    config=cms['homepage'];artists={a['slug']:a for a in cms['artists']}
    releases=[r for r in cms['releases'] if r.get('status')=='published']
    channels=[];featured=[]
    for slug in config['featuredArtists']:
        a=artists[slug];url=a.get('officialYoutubeUrl','')
        actions=link('./artists/'+slug+'/', 'PROFILE')+link('./search/?artist='+slug,'MUSIC')
        videos=sorted([r for r in releases if slug in r.get('artistSlugs',[]) and r.get('youtubeUrl')],key=lambda r:r.get('videoPublishedAt',''),reverse=True)
        streams=sorted([r for r in releases if slug in r.get('artistSlugs',[]) and streaming(r)],key=lambda r:streaming(r)['releaseDate'],reverse=True)
        if videos:actions+=link(videos[0]['youtubeUrl'],videos[0].get('videoButtonLabel','WATCH VIDEO'))
        if streams:actions+=link(streaming(streams[0])['linkcoreUrl'],'STREAMING')
        if url:actions+=link(url,'YOUTUBE ↗')
        image=visual(root,a.get('image',''),a['name']+' 公式Artist画像')
        featured.append(f'<article class="upgrade-card">{image}<div><h3>{E(a["name"])}</h3><div class="explore-actions">{actions}</div></div></article>')
        if url: channels.append(f'<article class="upgrade-card">{image}<div><p>{E(config["artistLabels"].get(slug,a.get("reading") or a["name"]))}</p><h3>{E(a["name"])}</h3><p>Music Video / Shorts / 楽曲・作品コンテンツ</p><div class="explore-actions">'+(link(url,'公式チャンネル ↗') if url else '<p>公式チャンネル情報は確認中です。</p>')+'</div></div></article>')
    channels.append('<article class="upgrade-card upgrade-label"><div><p>LABEL / PROJECT OFFICIAL</p><h3>SUZUKA</h3><p>総合公式 / レーベル・プロジェクト情報 / ティザー・予告</p><div class="explore-actions">'+link(cms['site']['youtubeUrl'],'SUZUKA YouTube ↗')+'</div></div></article>')
    streams=sorted([r for r in releases if streaming(r)],key=lambda r:(streaming(r)['releaseDate'],r['slug']),reverse=True)
    channel_html=section('official-artist-channels','OFFICIAL ARTIST CHANNELS','<div class="upgrade-grid upgrade-channels">'+''.join(channels)+'</div>')
    stream_html=section('now-streaming','NOW STREAMING','<div class="upgrade-grid">'+''.join(work_card(root,r,listen=True) for r in streams[:config['streamingLimit']])+'</div>'+link('./discography/','全作品を見る ↗'),'Listen to SUZUKA everywhere.')
    series_html=''
    for series in cms.get('seriesDefinitions',[]):
        slug=series['slug'];artist=artists[series['artistSlug']]
        episodes=[]
        for episode in series['episodes']:
            if episode.get('status')!='published' or not episode.get('verifiedAt'):continue
            release=next(r for r in releases if r['slug']==episode['releaseSlug'])
            episodes.append(f'<h2>{E(series["name"])} #{int(episode["number"]):02d}</h2>'+work_card(root,release,prefix='../../'))
        body='<section class="upgrade-section"><p>'+E(series['tagline'])+'</p><p>'+E(series['description'])+'</p>'+link('../../artists/'+artist['slug']+'/',artist['name']+' PROFILE')+''.join(episodes)+'</section>'
        page=shell('features/'+slug+'/',series['name']+'｜'+artist['name']+'｜SUZUKA',series['description'],series['name'],body,[{'@type':'ItemList','numberOfItems':len(episodes),'itemListElement':[{'@type':'ListItem','position':i+1,'name':ep['name'] if 'name' in ep else series['name']+' #'+str(ep['number']),'url':cms['site']['baseUrl']+'/'+next(r['releaseUrl'] for r in releases if r['slug']==ep['releaseSlug'])} for i,ep in enumerate(series['episodes']) if ep.get('status')=='published' and ep.get('verifiedAt')]}],page_type='CollectionPage')
        page=page.replace('</head>','<link rel="stylesheet" href="../../assets/homepage-upgrade.css"/></head>')
        brand=json.loads((root/'assets/data/brand.json').read_text())
        page=standardize_channel_links(page,youtube_channel_url(brand))
        page=normalize_graph(page,cms['site']['baseUrl']+'/features/'+slug+'/',Path('features')/slug/'index.html',brand,{r['slug']:r for r in releases},artists)
        out=root/'features'/slug/'index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(page)
        series_html+=section(slug,series['name'],'<p>'+E(artist['name'])+'</p><p>'+E(series['description'])+'</p><div class="explore-actions">'+link('./features/'+slug+'/','シリーズを見る ↗')+'</div>',series['tagline'])
    latest=sorted(releases,key=lambda r:(r['releaseDate'],r['slug']),reverse=True)
    latest_html=section('latest-releases','LATEST RELEASES','<div class="upgrade-grid">'+''.join(work_card(root,r,listen=bool(streaming(r))) for r in latest[:config['latestReleaseLimit']])+'</div>')
    artist_html=section('featured-artists','FEATURED ARTISTS','<div class="upgrade-grid">'+''.join(featured)+'</div>'+link('./artists/','すべての所属Artistを見る ↗'))
    videos=[r for r in releases if r.get('youtubeUrl') and r.get('videoStructuredDataStatus')=='published' and 'MV' in r.get('videoLabel','')]
    for r in releases:
        for v in r.get('videoVersions',[]):
            if v['label']=='OFFICIAL MV':videos.append({**r,'youtubeUrl':v['youtubeUrl'],'videoLabel':v['label'],'videoButtonLabel':'WATCH MV','videoPublishDate':v['publishedAt'][:10],'videoPublishedAt':v['publishedAt']})
    videos=sorted(videos,key=lambda r:(r.get('videoPublishedAt',''),r['slug']),reverse=True)
    video_html=section('latest-mv','LATEST MV / VIDEO','<div class="upgrade-grid">'+''.join(work_card(root,r,video=True) for r in videos[:config['latestVideoLimit']])+'</div>'+link('./gallery/','Galleryを見る ↗'))
    follow=section('follow-suzuka','FOLLOW SUZUKA','<div class="explore-actions">'+link(cms['site']['youtubeUrl'],'YouTube ↗')+link(cms['site']['instagramUrl'],'Instagram ↗')+link(cms['site']['noteUrl'],'note ↗')+link('#now-streaming','Streaming')+'</div>')
    home=root/'index.html';text=home.read_text()
    # Remove only this generator's owned sections; insertion is deterministic.
    text=re.sub(r'<!-- HOME-UPGRADE:[A-Z-]+:START -->.*?<!-- HOME-UPGRADE:[A-Z-]+:END -->','',text,flags=re.S)
    def insert(name,content,anchor):
        nonlocal text
        if anchor not in text:raise ValueError('Missing home anchor: '+anchor)
        text=text.replace(anchor,f'<!-- HOME-UPGRADE:{name}:START -->{content}<!-- HOME-UPGRADE:{name}:END -->'+anchor,1)
    # The legacy one-work panel is fully represented in NOW STREAMING.
    text=re.sub(r'<!-- streaming-release:start -->.*?<!-- streaming-release:end -->','',text,flags=re.S)
    insert('DISCOVERY',latest_html+channel_html+stream_html+series_html,'<!-- V31:HOME-NEXT:START -->')
    insert('ARTISTS',artist_html,'<section class="section home-artists-section"')
    insert('VIDEO',video_html,'<section class="section news-section"')
    care=re.search(r'<section class="suzuka-special-feature".*?</section>',text,re.S)
    if care:
        content=care[0];text=re.sub(r'<section class="suzuka-special-feature".*?</section>','',text,flags=re.S);text=text.replace('<section class="section news-section"',content+'<section class="section news-section"',1)
    insert('FOLLOW',follow,'<footer class="site-footer">')
    text=re.sub(r'<link rel="stylesheet" href="\./assets/homepage-upgrade.css"/?>','',text)
    text=text.replace('</head>','<link rel="stylesheet" href="./assets/homepage-upgrade.css"/></head>')
    home.write_text(text)
    for slug in config['featuredArtists']:
        p=root/'artists'/slug/'index.html';text=p.read_text();block=section('artist-official-links','MUSIC / OFFICIAL CHANNELS','<div class="explore-actions">'+link('../../search/?artist='+slug,'MUSIC')+link(artists[slug].get('officialYoutubeUrl',''),'YOUTUBE ↗')+''.join(link(streaming(r)['linkcoreUrl'],r['title']+' · STREAMING ↗') for r in streams if slug in r.get('artistSlugs',[]))+'</div>')
        text=re.sub(r'<!-- HOME-UPGRADE:ARTIST-LINKS:START -->.*?<!-- HOME-UPGRADE:ARTIST-LINKS:END -->','',text,flags=re.S)
        text=text.replace('</main>','<!-- HOME-UPGRADE:ARTIST-LINKS:START -->'+block+'<!-- HOME-UPGRADE:ARTIST-LINKS:END --></main>')
        text=text.replace('</head>','<link rel="stylesheet" href="../../assets/homepage-upgrade.css"/></head>');p.write_text(text)
    features=root/'features/index.html';text=features.read_text();text=re.sub(r'<!-- HOME-UPGRADE:SERIES:START -->.*?<!-- HOME-UPGRADE:SERIES:END -->','',text,flags=re.S)
    series_links=''.join(link('./'+s['slug']+'/',s['name']) for s in cms.get('seriesDefinitions',[]))
    text=text.replace('</main>','<!-- HOME-UPGRADE:SERIES:START --><section class="creator-copy"><h2>SERIES</h2><div class="explore-actions">'+series_links+'</div></section><!-- HOME-UPGRADE:SERIES:END --></main>');features.write_text(text)

    for r in releases:
        if not r.get('videoVersions'):continue
        p=root/r['releaseUrl']/'index.html';text=p.read_text()
        text=re.sub(r'<!-- HOME-UPGRADE:VERSIONS:START -->.*?<!-- HOME-UPGRADE:VERSIONS:END -->','',text,flags=re.S)
        body='<section class="creator-copy"><h2>ARTIST CHANNEL / VIDEO VERSIONS</h2>'
        for v in sorted(r['videoVersions'],key=lambda v:v['publishedAt'],reverse=True):
            body+='<p>'+E(v['label'])+' · '+v['publishedAt'][:10]+' · '+str(v['duration'])+'秒</p><div class="explore-actions">'+link(v['youtubeUrl'],v['title']+' ↗')+'</div>'
        body+='</section>'
        text=text.replace('</main>','<!-- HOME-UPGRADE:VERSIONS:START -->'+body+'<!-- HOME-UPGRADE:VERSIONS:END --></main>');p.write_text(text)

    analytics(root)
    analytics_v31(root)

"""Build the approved growth candidate from frozen main; NEVER stage or deploy it.

Historical source files and public-release/ remain the approved 104-work baseline.
This additive overlay is the source for the separately generated 109-work preview.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from build_music_production_release import sha
from build_official_sync_package import section
from verify_public_release import read_release, verify_private_audio, write_output

ROOT = Path(__file__).resolve().parents[1]
BASE = '39aebc4e116b09823dc2567dd8f7e6433312fb12'
DIGEST = '36477d62f8bbaac84bef7590d6e24a2d9d8be4fa7f3c9315f772da8631f05df7'
SITE = 'https://www.suzukaofficial.com'
MANIFEST = 'suzuka-v6-candidate-manifest.json'
SOURCE = Path('site-content/v6-growth')
NAMES = {'asteria': 'ASTERIA', 'michiru': '妃みちる', 'enomoto-mia': '榎本魅愛', 'nox': 'NOX'}
NEW_SLUGS = {'redline-heartbeat', 'outrun-the-night', 'five-gears-one-sky', 'midnight-ignition', 'onaji-josei-e'}
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()


def e(value):
    return escape(str(value or ''), quote=True)


def safe_url(value):
    p = urlsplit(value)
    if p.scheme != 'https' or not p.netloc or p.username or p.password:
        raise ValueError('Unverified external URL')
    return value


def stream_for(release, sources):
    value = release.get('scheduledStreamingRelease') or release.get('streamingRelease') or {}
    if value.get('status') != 'published': return None
    code = value.get('linkcoreUrl', '').split('/')[-1].split('?')[0]
    return next((s for s in sources['streaming'] if s['code'] == code), None)


def canonical(sources, original):
    cms = copy.deepcopy(original)
    if len(cms['artists']) != 13 or len(cms['releases']) != 104:
        raise ValueError('The reviewed 13-artist/104-work baseline changed')
    now = sources['verifiedAt']; old_by = {r['slug']: r for r in cms['releases']}
    for v in sources['videos']:
        if v['kind'] not in {'audio', 'mv'}: continue
        if v['status'] != 'published' or v['playability'] != 'OK' or v['duration'] <= 0:
            raise ValueError('New recording is not verified publicly playable')
        slug = v['slug']; title = v['workTitle']; artist = NAMES[v['artistSlug']]
        if slug in old_by: raise ValueError('New work collides with an existing identity')
        desc = f'{artist}「{title}」の' + ('公式MV' if v['kind'] == 'mv' else '公式音源') + 'をYouTubeで公開。'
        cms['releases'].append({
            'id': slug, 'slug': slug, 'title': title, 'displayTitle': title,
            'artist': artist, 'artistSlug': v['artistSlug'], 'artistSlugs': [v['artistSlug']], 'artistType': 'MusicGroup',
            'releaseDate': v['publishedAt'][:10], 'releaseYear': 2026, 'releaseType': 'single',
            'publishedAt': v['publishedAt'], 'videoPublishedAt': v['publishedAt'], 'videoPublishDate': v['publishedAt'][:10],
            'videoPublishedAtSource': 'official-youtube-public-player-metadata', 'status': 'published',
            'youtubeUrl': v['source'], 'youtubeVideoTitle': v['title'], 'duration': v['duration'],
            'videoLabel': 'OFFICIAL MV' if v['kind'] == 'mv' else 'OFFICIAL AUDIO',
            'videoCtaLabel': '公式MVを見る' if v['kind'] == 'mv' else '公式音源を聴く',
            'videoStructuredDataStatus': 'published', 'description': desc, 'introduction': desc,
            'releaseUrl': f'releases/{slug}/', 'newsUrl': '', 'coverImage': v['image'],
            'coverAlt': f'{artist}「{title}」公式YouTubeサムネイル（正式ジャケット確認待ち）',
            'imageRole': 'official-youtube-thumbnail', 'artworkStatus': 'pending-formal-jacket',
            'lyricsAvailable': False, 'lyricsVerified': False, 'genres': [], 'themes': [], 'tags': [title, artist],
            'searchKeywords': [title, artist], 'relatedReleases': [], 'officialSource': v['source'],
            'verifiedAt': now, 'analyticsEnabled': True, 'galleryPublished': False,
        })
    stream = next(s for s in sources['streaming'] if s['code'] == 'aU8rN04N')
    if not stream.get('appleMusicUrl') or stream['releaseDate'] != '2026-10-27':
        raise ValueError('New streaming release requires independently verified Apple Music evidence')
    slug = 'onaji-josei-e'; title = '同じ女性へ 〜これから母になる人へ〜'
    cms['releases'].append({
        'id': slug, 'slug': slug, 'title': title, 'displayTitle': title, 'artist': '妃みちる',
        'artistSlug': 'michiru', 'artistSlugs': ['michiru'], 'artistType': 'Person', 'releaseType': 'single',
        'status': 'published', 'releaseDate': stream['releaseDate'], 'publishedAt': stream['releaseDate'],
        'publicationDatePrecision': 'day', 'publicationEvidenceType': 'verified-streaming-only',
        'releaseUrl': f'releases/{slug}/', 'newsUrl': '', 'youtubeUrl': '', 'duration': 0,
        'description': f'妃みちる「{title}」。2026年10月27日ストリーミング配信開始。',
        'coverImage': stream['jacket'], 'formalJacketImage': stream['jacket'],
        'coverAlt': f'妃みちる「{title}」TuneCore Japan正式ジャケット',
        'imageRole': 'official-linkcore-artwork', 'artworkStatus': 'verified-public-linkcore',
        'lyricsAvailable': False, 'lyricsVerified': False, 'genres': [], 'themes': [], 'tags': [title, '妃みちる'],
        'searchKeywords': [title, '妃みちる'], 'relatedReleases': [], 'officialSource': stream['url'],
        'scheduledStreamingRelease': {'status': 'published', 'releaseDate': stream['releaseDate'],
            'timezone': 'Asia/Tokyo', 'linkcoreUrl': stream['url'], 'verifiedAt': now,
            'availableStoreUrls': [stream['appleMusicUrl']], 'verificationSource': 'official-linkcore-and-japan-apple-music'},
        'analyticsEnabled': True, 'galleryPublished': False,
    })
    birthday = old_by['anata-dake-ni-okuru-happy-birthday']
    stream = next(s for s in sources['streaming'] if s['code'] == 'vvasqg5z')
    if not stream.get('appleMusicUrl') or stream['releaseDate'] != '2026-10-31':
        raise ValueError('Birthday streaming release evidence changed')
    birthday['scheduledStreamingRelease'].update(status='published', verifiedAt=now,
        verificationSource='official-linkcore-and-japan-apple-music', availableStoreUrls=[stream['appleMusicUrl']])
    birthday.update(coverImage=stream['jacket'], formalJacketImage=stream['jacket'],
        coverAlt='榎本魅愛「あなただけに送るHappy Birthday」TuneCore Japan正式ジャケット',
        imageRole='official-linkcore-artwork', artworkStatus='verified-public-linkcore', coverSource=stream['url'])
    by_slug = {r['slug']: r for r in cms['releases']}
    for v in sources['videos']:
        if v['kind'] not in {'short', 'product-short'}: continue
        s = {'videoId': v['videoId'], 'title': v['title'], 'artist': NAMES[v['artistSlug']], 'artistSlug': v['artistSlug'],
             'publishedAt': v['publishedAt'], 'duration': v['duration'], 'youtubeUrl': 'https://www.youtube.com/shorts/' + v['videoId'],
             'thumbnail': 'https://i.ytimg.com/vi/' + v['videoId'] + '/hqdefault.jpg', 'status': 'published',
             'contentType': 'short', 'officialChannelId': v['channelId'], 'verifiedAt': now}
        if v['kind'] == 'product-short': s['relatedProduct'] = v['slug']
        else:
            s['relatedRelease'] = v['slug']
            r = by_slug[v['slug']]
            r.setdefault('relatedShorts', []).append(s['youtubeUrl'])
            if not r.get('shortsUrl'): r['shortsUrl'] = s['youtubeUrl']
        if any(x['videoId'] == s['videoId'] for x in cms['youtubeSnapshot']['shortVideos']):
            raise ValueError('Duplicate Shorts identity')
        cms['youtubeSnapshot']['shortVideos'].append(s)
    pending = next(v for v in sources['videos'] if v['kind'] == 'upcoming')
    scheduled=datetime.fromisoformat(pending['scheduledAt']).astimezone(ZoneInfo('Asia/Tokyo')).isoformat()
    cms['upcoming'].append({'id': pending['slug'], 'slug': pending['slug'], 'title': pending['workTitle'],
        'artist': 'ASTERIA', 'artistSlug': 'asteria', 'status': 'upcoming', 'releaseAt': scheduled, 'scheduledAt': scheduled,
        'youtubeUrl': pending['source'], 'verifiedAt': now, 'verificationState': pending['playability'],
        'dateType': 'scheduled-youtube-premiere', 'requiresPublicReverification': True})
    for n in sources['news']:
        cms['news'].append({**n, 'description': 'SUZUKA公式noteの記事です。全文はnoteでご覧ください。',
            'relatedReleaseUrl': 'releases/' + n['relatedRelease'] + '/', 'officialSource': n['noteUrl'],
            'status': 'published', 'homeFeatured': True, 'siteAnnouncement': False})
    if len(cms['releases']) != 109 or {r['slug'] for r in cms['releases']} - set(old_by) != NEW_SLUGS:
        raise ValueError('Unexpected catalog change')
    cms['updatedAt'] = now
    return cms


def image_tag(path, alt, sources, original):
    item = next((x for x in sources['images'] if x['publicPath'] == path), None)
    if item: width, height = item['width'], item['height']
    else:
        # Existing official images are preserved; dimensions read from the bytes.
        from PIL import Image
        import io
        if path.startswith('https://'): return f'<img src="{e(path)}" alt="{e(alt)}" width="480" height="360" loading="lazy" decoding="async">'
        with Image.open(io.BytesIO(original[path])) as im: width, height = im.size
    return f'<img src="/{e(path)}" alt="{e(alt)}" width="{width}" height="{height}" loading="lazy" decoding="async">'


def link(url, label, *, action='', slug='', artist='', service='', product='', cls='growth-button'):
    attrs = ''
    for k, v in {'growth-action': action, 'release-slug': slug, 'artist-slug': artist,
                 'service': service, 'product-id': product}.items():
        if v: attrs += f' data-{k}="{e(v)}"'
    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith('https://') else ''
    return f'<a class="{cls}" href="{e(url)}"{attrs}{external}>{e(label)}<span aria-hidden="true"> ↗</span></a>'


def streaming_buttons(r, sources, *, stores=False):
    stream = stream_for(r, sources)
    if not stream: return ''
    result = link(stream['url'], '配信サービスで聴く', action='streaming', slug=r['slug'], artist=r['artistSlug'], service='linkcore')
    if stores:
        result += '<div class="growth-stores">' + ''.join(link(safe_url(s['url']), s['name'], action='streaming',
            slug=r['slug'], artist=r['artistSlug'], service=s['id'], cls='growth-store') for s in stream['stores']) + '</div>'
    return result


def card(r, sources, original, streaming=False):
    stream = stream_for(r, sources)
    date = stream['releaseDate'] if streaming and stream else r['releaseDate']
    label = '配信開始' if streaming and stream or r.get('publicationEvidenceType') == 'verified-streaming-only' else 'YouTube公開'
    formal = r.get('formalJacketImage') or r.get('imageRole') == 'official-linkcore-artwork' or ('正式ジャケット' in r.get('coverAlt','') and '確認待ち' not in r.get('coverAlt',''))
    desc = '正式ジャケット' if formal else '映像サムネイル・正式ジャケット確認待ち'
    cta = streaming_buttons(r, sources, stores=streaming) if streaming or not r.get('youtubeUrl') else ''
    if not cta and r.get('youtubeUrl'): cta = link(r['youtubeUrl'], r.get('videoCtaLabel', '公式動画を見る'))
    return f'<article class="growth-card" data-release-id="{e(r["slug"])}" data-source-section="growth_music"><a class="growth-cover" href="/{e(r["releaseUrl"])}">{image_tag(r["coverImage"],r["coverAlt"],sources,original)}</a><div class="growth-card-copy"><p class="growth-kicker">{label} · <time datetime="{e(date)}">{e(date)}</time></p><h3><a href="/{e(r["releaseUrl"])}">{e(r["title"])}</a></h3><p>{e(r["artist"])}</p><p class="growth-caption">{desc}</p><div class="growth-actions">{cta}{link("/"+r["releaseUrl"],"作品ページ",cls="growth-text-link")}</div></div></article>'


def music_section(title, subtitle, releases, sources, original, *, section_id='', streaming=False):
    identity = f' id="{section_id}"' if section_id else ''
    return f'<section class="growth-section"{identity} data-source-section="{e(section_id or "music")}"><div class="growth-heading"><p class="growth-kicker">{e(subtitle)}</p><h2>{e(title)}</h2></div><div class="growth-grid">'+''.join(card(r,sources,original,streaming) for r in releases)+'</div></section>'


def stickers_section(products, sources, original, *, full=False):
    cards = []
    for s in products:
        published = (s['status'] == 'published' and bool(s.get('url')) and
            type(s.get('price')) is int and s['price'] >= 0 and s.get('currency') == 'JPY' and
            type(s.get('count')) is int and s['count'] > 0 and
            len(s.get('previews', [])) == s['count'] and bool(s.get('image')) and bool(s.get('verifiedAt')))
        image = image_tag(s['image'], s['title']+' メイン画像', sources, original) if s.get('image') else '<div class="growth-coming" aria-label="審査中">COMING<br>SOON</div>'
        preview = ''
        if full and published:
            preview = '<details class="growth-previews"><summary>全'+str(s['count'])+'種類のスタンプを見る</summary><div>'+''.join(image_tag(p,s['title']+' プレビュー '+str(i+1),sources,original) for i,p in enumerate(s['previews']))+'</div></details>'
        price = f'{s["count"]}種類 · 日本向け表示 {s["price"]}円' if published else '審査中 · 販売開始をお待ちください'
        cta = link(safe_url(s['url']), 'LINE STOREで購入', action='sticker', artist=s['artistSlug'], product=s['id']) if published else '<p class="growth-status">COMING SOON</p>'
        name = next(a['name'] for a in original_cms(original)['artists'] if a['slug']==s['artistSlug'])
        cards.append('<article class="growth-card growth-sticker" data-source-section="line_stickers">'+image+'<div class="growth-card-copy"><p class="growth-kicker">'+('NOW AVAILABLE' if published else 'COMING SOON')+'</p><h3>'+e(s['title'])+'</h3><p>'+e(price)+'</p><div class="growth-actions">'+cta+link('/artists/'+s['artistSlug']+'/',name+'の音楽',cls='growth-text-link')+'</div>'+preview+'</div></article>')
    return '<section class="growth-section" id="line-stickers"><div class="growth-heading"><p class="growth-kicker">MUSIC IN YOUR EVERYDAY</p><h2>'+('公式スタンプ一覧' if full else 'SUZUKA LINE STICKERS')+'</h2><p>音楽の世界から、毎日の会話へ。</p></div><div class="growth-grid growth-sticker-grid">'+''.join(cards)+'</div><p class="growth-caption">価格・販売状況の最終情報はLINE STOREでご確認ください。'+('確認日：'+e(sources['verifiedAt'][:10]) if full else '')+'</p>'+('' if full else link('/line-stickers/','スタンプをすべて見る'))+'</section>'


def original_cms(files):
    return json.loads(files['assets/data/creator-cms.json'])


def page(title, description, route, content, original, *, image='', graph=None):
    template = original['music-production/index.html'].decode()
    ga = re.search(r'<!-- SUZUKA:GA4:START -->.*?<!-- SUZUKA:GA4:END -->',template,re.S)[0]
    header = re.search(r'<header\b.*?</header>',template,re.S)[0]
    footer = re.search(r'<footer\b.*?</footer>',template,re.S)[0]
    header=header.replace('12の世界','13の世界')
    footer=footer.replace('TWELVE WORLDS','THIRTEEN WORLDS')
    url = SITE+'/'+route; image = image or 'images/suzuka-channel.jpg'
    image_url = image if image.startswith('https://') else SITE+'/'+image
    graph = graph or {'@type':'WebPage','@id':url+'#webpage','url':url,'name':title,'description':description}
    breadcrumb = {'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[
        {'@type':'ListItem','position':1,'name':'SUZUKA','item':SITE+'/'},
        {'@type':'ListItem','position':2,'name':title,'item':url}]}
    ld = json.dumps({'@context':'https://schema.org','@graph':[graph,breadcrumb]},ensure_ascii=False).replace('<','\\u003c')
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'+ga+
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'｜SUZUKA Official</title>'+
        '<meta name="description" content="'+e(description)+'"><link rel="canonical" href="'+e(url)+'">'+
        '<meta property="og:type" content="website"><meta property="og:site_name" content="SUZUKA Official">'+
        '<meta property="og:title" content="'+e(title)+'"><meta property="og:description" content="'+e(description)+'">'+
        '<meta property="og:url" content="'+e(url)+'"><meta property="og:image" content="'+e(image_url)+'">'+
        '<meta property="og:image:alt" content="'+e(title)+'"><meta name="twitter:card" content="summary_large_image">'+
        '<meta name="twitter:title" content="'+e(title)+'"><meta name="twitter:description" content="'+e(description)+'">'+
        '<meta name="twitter:image" content="'+e(image_url)+'"><link rel="stylesheet" href="/assets/cinematic-universe-v6.css">'+
        '<link rel="stylesheet" href="/assets/music-production.css"><link rel="stylesheet" href="/assets/social.css">'+
        '<link rel="stylesheet" href="/assets/v6-growth.css"><script type="application/ld+json">'+ld+'</script>'+
        '<script defer src="/assets/social.js"></script></head><body class="growth-page"><a class="skip-link" href="#main">本文へ移動</a>'+
        header+'<main id="main">'+content+'</main>'+footer+'</body></html>').encode()


def release_page(r, cms, sources, original):
    url=SITE+'/'+r['releaseUrl']; video=r.get('youtubeUrl'); stream=stream_for(r,sources)
    details = '<p>作品公開：<time datetime="'+e(r['publishedAt'])+'">'+e(r['releaseDate'])+'</time></p>'
    if stream: details += '<p>ストリーミング配信開始：'+e(stream['releaseDate'])+'</p>'
    content='<section class="growth-section growth-release"><p class="growth-kicker">'+e(r.get('videoLabel','STREAMING RELEASE'))+'</p><h1>'+e(r['title'])+'</h1><p>'+e(r['artist'])+'</p><div class="growth-release-grid">'+image_tag(r['coverImage'],r['coverAlt'],sources,original)+'<div><p>'+e(r['description'])+'</p>'+details+'<div class="growth-actions">'+streaming_buttons(r,sources,stores=True)
    if video:content+=link(video,r.get('videoCtaLabel','公式動画を見る'))
    content+=link('/artists/'+r['artistSlug']+'/','アーティストを見る',cls='growth-text-link')+'</div>'
    for u in r.get('relatedShorts',[]):content+=link(u,'公式Shortsを見る',cls='growth-text-link')
    content+='</div></div></section>'
    related=[x for x in cms['releases'] if x['artistSlug']==r['artistSlug'] and x['slug']!=r['slug']][-3:]
    content+=music_section('次に聴くなら','MORE FROM '+r['artist'],related,sources,original)
    graph={'@type':'MusicRecording','@id':url+'#recording','name':r['title'],'url':url,'datePublished':r['publishedAt'],
           'description':r['description'],'image':SITE+'/'+r['coverImage'],'byArtist':{'@id':SITE+'/artists/'+r['artistSlug']+'/#artist'}}
    if stream:graph['sameAs']=stream['url']
    # VideoObject is included only for a verified playable, already-public full video.
    if video:
        vid=video.split('v=')[-1]
        graph['subjectOf']={'@type':'VideoObject','@id':url+'#video','name':r['youtubeVideoTitle'],
            'description':r['description'],'uploadDate':r['videoPublishedAt'],'duration':'PT'+str(r['duration'])+'S',
            'thumbnailUrl':'https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg','embedUrl':'https://www.youtube.com/embed/'+vid,'url':video}
    return page(r['title'],r['description'],r['releaseUrl'],content,original,image=r['coverImage'],graph=graph)


def decorate_links(text, cms, sources):
    releases={}
    for r in cms['releases']:
        s=stream_for(r,sources)
        if s:
            releases[s['code']]=r
            for store in s['stores']:releases[store['url']]=r
    def anchor(m):
        tag=m[0]
        if 'data-growth-action=' in tag:return tag
        h=re.search(r'\bhref=["\']([^"\']+)',tag)
        if not h:return tag
        from html import unescape
        url=unescape(h[1]);p=urlsplit(url);attrs={}
        if p.hostname=='linkco.re':
            r=releases.get(p.path.strip('/'))
            if r:attrs={'growth-action':'streaming','release-slug':r['slug'],'artist-slug':r['artistSlug'],'service':'linkcore'}
        elif p.hostname=='www.tunecore.co.jp' and url in releases:
            r=releases[url];attrs={'growth-action':'streaming','release-slug':r['slug'],'artist-slug':r['artistSlug'],'service':p.path.split('/')[2]}
        elif p.scheme=='mailto' and 'mp-button' in tag:
            attrs={'growth-action':'production-contact'}
        elif not p.scheme and p.path.rstrip('/').endswith('music-production'):
            attrs={'growth-action':'production-visit'}
        return tag[:-1]+''.join(' data-'+k+'="'+e(v)+'"' for k,v in attrs.items())+'>'
    return re.sub(r'<a\b[^>]*>',anchor,text)


def update_birthday_html(text, r, sources):
    old='https://i.ytimg.com/vi/MLmc3jVZ7-M/hqdefault.jpg';new=SITE+'/'+r['coverImage']
    def image(m):
        tag=m[0]
        if old not in tag:return tag
        tag=tag.replace(old,'/'+r['coverImage'])
        dims=next(x for x in sources['images'] if x['publicPath']==r['coverImage'])
        for key in ['width','height']:
            tag=re.sub(r'\b'+key+r'="[0-9]+"',key+'="'+str(dims[key])+'"',tag)
        tag=re.sub(r'aspect-ratio:\s*[0-9]+\s*/\s*[0-9]+','aspect-ratio:'+str(dims['width'])+'/'+str(dims['height']),tag)
        tag=tag.replace('公式YouTubeサムネイル（正式ジャケット確認待ち）','TuneCore Japan正式ジャケット')
        return tag
    text=re.sub(r'<img\b[^>]*>',image,text)
    text=re.sub(r'<meta\b[^>]*>',lambda m:m[0].replace(old,new) if old in m[0] and re.search('og:image|twitter:image',m[0]) else m[0],text)
    def graph(m):
        d=json.loads(m[1])
        def walk(x):
            if isinstance(x,dict):
                if x.get('@type')=='MusicRecording' and x.get('name')==r['title']:x['image']=new
                for a in x.values():walk(a)
            elif isinstance(x,list):
                for a in x:walk(a)
        walk(d)
        return '<script type="application/ld+json">'+json.dumps(d,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>',graph,text,flags=re.S)


def build(root=ROOT):
    info,original=read_release(root,BASE)
    if info['artifactDigest']!=DIGEST or len(original)!=814:raise ValueError('Reviewed public baseline changed; STOP')
    sources=json.loads((root/SOURCE/'verified-sources.json').read_text())
    cms=canonical(sources,original_cms(original));files=dict(original)
    for item in sources['images']:
        source_path=(root/SOURCE/item['path']).resolve()
        if not source_path.is_relative_to((root/SOURCE/'images').resolve()) or not re.fullmatch(r'images/v6-growth/[A-Za-z0-9-]+\.webp',item['publicPath']):
            raise ValueError('Unsafe image evidence path')
        data=source_path.read_bytes()
        if sha(data)!=item['sha256']:raise ValueError('Official image evidence changed')
        if item['publicPath'] in original:raise ValueError('Refusing to overwrite an existing image')
        files[item['publicPath']]=data
    for name in ['v6-growth.css']:
        files['assets/'+name]=(root/SOURCE/name).read_bytes()
    files['assets/data/creator-cms.json']=encoded(cms)
    files['assets/data/line-stickers.json']=encoded({'verifiedAt':sources['verifiedAt'],'products':sources['stickers']})
    upcoming_data=json.loads(original['assets/data/upcoming-releases.json'])
    upcoming_data.update(updatedAt=cms['updatedAt'],releases=cms['upcoming'])
    files['assets/data/upcoming-releases.json']=encoded(upcoming_data)
    evidence=json.loads(original['assets/data/youtube-publish-dates.json'])
    for v in sources['videos']:
        if v['status']!='published':continue
        if any(x['youtubeId']==v['videoId'] for x in evidence['records']):raise ValueError('Duplicate video evidence')
        evidence['records'].append({'releaseSlug':v['slug'] if v['kind']!='product-short' else '',
            'youtubeId':v['videoId'],'youtubeUrl':v['source'],'officialTitle':v['title'],
            'channelId':v['channelId'],'channelVerified':True,'verifiedPublishedAt':v['publishedAt'],
            'youtubePublishDate':v['publishedAt'],'playabilityStatus':v['playability'],
            'durationSeconds':v['duration'],'status':'verified-datetime','currentAvailability':'public',
            'currentAvailabilityVerifiedAt':v['verifiedAt'],'verificationSource':'official-youtube-public-player-metadata',
            'contentType':'short' if v['kind'] in {'short','product-short'} else v['kind'],
            'thumbnailUrl':'https://i.ytimg.com/vi/'+v['videoId']+'/hqdefault.jpg'})
    evidence['checkedAt']=sources['verifiedAt'];files['assets/data/youtube-publish-dates.json']=encoded(evidence)
    birthday=next(r for r in cms['releases'] if r['slug']=='anata-dake-ni-okuru-happy-birthday')
    new=[r for r in cms['releases'] if r['slug'] in NEW_SLUGS]
    for r in new:files[r['releaseUrl']+'index.html']=release_page(r,cms,sources,original)
    for n in sources['news']:
        body='<section class="growth-section"><p class="growth-kicker">OFFICIAL NOTE</p><h1>'+e(n['title'])+'</h1><p>記事公開日：'+e(n['publishedAt'][:10])+'</p>'+image_tag(n['image'],n['title'],sources,original)+'<p>SUZUKA公式noteの記事です。全文は公式記事でご覧ください。</p><div class="growth-actions">'+link(n['noteUrl'],'noteで記事を読む')+link('/releases/'+n['relatedRelease']+'/','関連作品を見る')+'</div></section>'
        route='news/'+n['slug']+'/'
        graph={'@type':'NewsArticle','@id':SITE+'/'+route+'#article','headline':n['title'],'url':SITE+'/'+route,
            'datePublished':n['publishedAt'],'image':SITE+'/'+n['image'],'author':{'@id':SITE+'/#organization'},'isBasedOn':n['noteUrl']}
        files[route+'index.html']=page(n['title'],'SUZUKA公式noteの記事をご案内します。',route,body,original,image=n['image'],graph=graph)
    full=stickers_section(sources['stickers'],sources,original,full=True)
    graph={'@type':'CollectionPage','@id':SITE+'/line-stickers/#webpage','name':'SUZUKA LINE STICKERS',
        'url':SITE+'/line-stickers/','description':'榎本魅愛・妃みちるの公式LINEスタンプ。ECLYPSEはCOMING SOON。'}
    body='<div class="growth-section growth-page-intro"><p class="growth-kicker">SUZUKA OFFICIAL</p><h1>SUZUKA LINE STICKERS</h1><p>音楽を、毎日の会話へ。</p></div>'+full
    files['line-stickers/index.html']=page('SUZUKA LINE STICKERS','SUZUKA公式LINEスタンプ。榎本魅愛と妃みちるの販売中商品、ECLYPSEの新作情報。','line-stickers/',body,original,image=sources['stickers'][0]['image'],graph=graph)
    streams=sorted([r for r in cms['releases'] if stream_for(r,sources)],key=lambda r:(stream_for(r,sources)['releaseDate'],r['slug']),reverse=True)
    home=files['index.html'].decode()
    featured=[next(r for r in cms['releases'] if r['slug']==s) for s in ['anata-dake-ni-okuru-happy-birthday','onaji-josei-e','mirai-no-ashioto']]
    listen=music_section('LISTEN TO SUZUKA','Discover the Sound. Feel the Story.',streams[:6],sources,original,section_id='listen',streaming=True)
    listen=listen.replace('<div class="growth-grid">','<p>最新配信作品</p><div class="growth-grid">',1)
    listen+='<section class="growth-section growth-featured"><h2>FEATURED MUSIC</h2><p>いま聴いてほしい、SUZUKAの選曲。</p><div class="growth-actions">'+''.join(link('/'+r['releaseUrl'],r['title']) for r in featured)+'</div><h3>アーティストから探す</h3><div class="growth-actions">'+''.join(link('/artists/'+a['slug']+'/#listen-artist',a['name']) for a in cms['artists'] if any(r['artistSlug']==a['slug'] for r in streams))+'</div></section>'
    # Insert immediately after the original hero, before the existing exploration.
    hero=re.search(r'<section\b[^>]*aria-labelledby="hero-title".*?</section>',home,re.S)
    if not hero:raise ValueError('Missing reviewed home hero')
    home=home[:hero.end()]+listen+home[hero.end():]
    cta='<div class="growth-hero-actions">'+link('#listen','音楽を聴く',cls='growth-button growth-primary')+link('/line-stickers/','LINEスタンプ',cls='growth-button')+link('/music-production/','楽曲制作のご相談',action='production-visit',cls='growth-text-link')+'</div>'
    m=re.search(r'<a\b[^>]*href="#explore".*?</a>',home,re.S)
    if not m:raise ValueError('Missing existing gate navigation')
    home=home[:m.end()]+cta+home[m.end():]
    latest=sorted(cms['releases'],key=lambda r:(r.get('publishedAt') or r['releaseDate'],r['slug']),reverse=True)
    home=section(home,'id="latest-releases"',music_section('NEW RELEASE','いま、響く音楽。',latest[:6],sources,original,section_id='latest-releases'))
    home=home.replace('<section class="mp-home-link"',stickers_section(sources['stickers'],sources,original)+'<section class="mp-home-link"',1)
    mp_match=re.search(r'<section class="mp-home-link".*?</section>',home,re.S)
    home=home[:mp_match.start()]+home[mp_match.end():]
    at=home.index('</section>',home.index('id="listen"'))+len('</section>')
    home=home[:at]+'<div class="growth-production-invitation">'+link('/music-production/','あなたの物語を、世界にひとつだけの音楽へ。',action='production-visit')+'</div>'+home[at:]
    home=home.replace('</main>',mp_match[0]+'</main>',1)
    files['index.html']=home.encode()
    # Add current releases to the existing directory, preserving every original card.
    for name in ['releases/index.html','discography/index.html']:
        s=files[name].decode();s=s.replace('</main>',music_section('NEW RELEASE','新しく公開された5作品',new,sources,original)+'</main>',1)
        files[name]=s.encode()
    # Add explicit verified upcoming state; no MusicRecording/VideoObject publication claims.
    pending=cms['upcoming'][-1]
    pending_html='<section class="growth-section" id="growth-upcoming"><p class="growth-kicker">UPCOMING · YOUTUBE PREMIERE</p><h2>LAST IGNITION — ASTERIA</h2><p>YouTube公開予定：2026年11月1日 20:00（日本時間）</p><p>公式公開状態の再確認後に公開済みへ切り替えます。</p>'+link(pending['youtubeUrl'],'YouTubeの公開予定を見る')+'</section>'
    name='artists/asteria/index.html'
    files[name]=files[name].decode().replace('</main>',pending_html+'</main>',1).encode()
    calendar_card=pending_html.replace('id="growth-upcoming"','id="growth-upcoming" data-release-slug="last-ignition" data-release-at="'+e(pending['scheduledAt'])+'"')
    schedule=section(files['schedule/index.html'].decode(),'id="today"','<section class="v31-schedule-group" id="today"><h2>Today</h2><div class="v31-schedule-list">'+calendar_card+'</div></section>')
    # Preserve every previously listed streaming work, with its verified current state.
    rows=[]
    for r in streams:
        stream=stream_for(r,sources)
        rows.append('<article class="v31-countdown-card" data-streaming-slug="'+e(r['slug'])+'"><div><p class="section-kicker">NOW STREAMING</p><time datetime="'+e(stream['releaseDate'])+'">'+e(stream['releaseDate'])+'</time></div><div><h3>'+e(r['title'])+'</h3><p>'+e(r['artist'])+'</p><div class="growth-actions">'+link('/'+r['releaseUrl'],'作品情報',cls='growth-text-link')+streaming_buttons(r,sources)+'</div></div></article>')
    schedule=section(schedule,'id="streaming-releases"','<section class="v31-schedule-group" id="streaming-releases"><h2>Streaming Release</h2><p>作品公開日と配信開始日は別に管理しています。</p><div class="v31-schedule-list">'+''.join(rows)+'</div></section>')
    files['schedule/index.html']=schedule.encode()
    for artist in cms['artists']:
        slug=artist['slug'];rlist=[r for r in latest if r['artistSlug']==slug];slist=[r for r in streams if r['artistSlug']==slug]
        block=''
        if slist:block+=music_section('配信サービスで聴く','LATEST STREAMING',slist[:3],sources,original,section_id='listen-artist',streaming=True)
        if any(r['slug'] in NEW_SLUGS for r in rlist):block+=music_section('最新の公開作品','NEW MUSIC',rlist[:6],sources,original)
        products=[s for s in sources['stickers'] if s['artistSlug']==slug]
        if products:block+=stickers_section(products,sources,original)
        name='artists/'+slug+'/index.html'
        if block:files[name]=files[name].decode().replace('</main>',block+'</main>',1).encode()
    # Refresh only music/Shorts/news panels in all 13 worlds; imagery/config/audio stay frozen.
    manifest=json.loads(original[MANIFEST])
    for route in manifest['v6Routes'][1:]:
        slug=route.split('/')[1];s=files[route].decode();tracks=[r for r in latest if r['artistSlug']==slug]
        s=section(s,'id="music"',music_section('この世界に、響く音楽。',str(len(tracks))+' WORKS',tracks,sources,original,section_id='music'))
        new_shorts=[v for v in sources['videos'] if v['artistSlug']==slug and v['kind'] in {'short','product-short'}]
        if new_shorts:
            block='<section class="growth-section"><h2>NEW SHORTS</h2><div class="growth-actions">'+''.join(link('https://www.youtube.com/shorts/'+v['videoId'],v['title']) for v in new_shorts)+'</div></section>'
            s=s.replace('</main>',block+'</main>',1)
        files[route]=s.encode()
    notes=sorted([n for n in cms['news'] if n.get('noteUrl') and n.get('status')=='published'],key=lambda n:n['publishedAt'],reverse=True)
    news_block='<section class="growth-section" aria-labelledby="official-news-title"><div class="growth-heading"><p class="growth-kicker">NEWS & STORIES</p><h2 id="official-news-title">音楽の、その先の物語。</h2></div><div class="growth-news">'+''.join('<article><time datetime="'+e(n['publishedAt'])+'">'+e(n['publishedAt'][:10])+'</time><h3>'+link('/news/'+n['slug']+'/',n['title'],cls='growth-text-link')+'</h3>'+link(n['noteUrl'],'noteで読む',cls='growth-text-link')+'</article>' for n in notes)+'</div></section>'
    files['index.html']=section(files['index.html'].decode(),'aria-labelledby="official-news-title"',news_block).encode()
    files['news/index.html']=files['news/index.html'].decode().replace('</main>',news_block+'</main>',1).encode()
    # Update the shared catalog/search/link records without replaying historical generators.
    catalog=json.loads(original['assets/data/releases-catalog.json']);by={r['slug']:r for r in cms['releases']}
    catalog['releases']=[{**r,**by[r['slug']]} for r in catalog['releases']]+new
    catalog['upcoming']=cms['upcoming'];catalog['updatedAt']=cms['updatedAt'];files['assets/data/releases-catalog.json']=encoded(catalog)
    search=json.loads(original['assets/data/search-v31.json'])
    for r in new:search['documents'].append({'type':'Release','contentType':'release','title':r['title'],'description':r['description'],'url':r['releaseUrl'],'keywords':r['tags']})
    for n in sources['news']:search['documents'].append({'type':'News','contentType':'news','title':n['title'],'description':'SUZUKA公式note','url':'news/'+n['slug']+'/','keywords':[NAMES[n['artistSlug']]]})
    search['documents'].append({'type':'Collection','contentType':'stickers','title':'SUZUKA LINE STICKERS','description':'公式LINEスタンプ','url':'line-stickers/','keywords':['榎本魅愛','妃みちる','ECLYPSE','LINEスタンプ']})
    search['updatedAt']=cms['updatedAt'];files['assets/data/search-v31.json']=encoded(search)
    links=json.loads(original['assets/data/release-links.json']);link_by={r['slug']:r for r in links['releases']}
    for r in cms['releases']:
        if r['slug'] in NEW_SLUGS:
            entry={k:r.get(k,'') for k in ['slug','title','artist','artistSlug','coverImage','coverAlt','youtubeUrl','description','duration']}
            entry.update(releasePage=r['releaseUrl'],newsPage='',newsStatus='unconfirmed',status='published',
                         youtubeStatus='published' if r.get('youtubeUrl') else 'unconfirmed',playerEnabled=False)
            links['releases'].append(entry);link_by[r['slug']]=entry
        entry=link_by[r['slug']]
        if r.get('shortsUrl'):entry.update(shortsUrl=r['shortsUrl'],shortsStatus='published')
        if r['slug']==birthday['slug']:entry.update(image=r['coverImage'],coverImage=r['coverImage'],coverAlt=r['coverAlt'])
    links['updatedAt']=cms['updatedAt'];files['assets/data/release-links.json']=encoded(links)
    atom='http://www.w3.org/2005/Atom';feed=ET.fromstring(original['feed.xml'])
    feed.find('{'+atom+'}updated').text=cms['updatedAt']
    for item in [*new,*sources['news']]:
        is_news=item in sources['news'];route='news/'+item['slug']+'/' if is_news else item['releaseUrl']
        url=SITE+'/'+route;entry=ET.SubElement(feed,'{'+atom+'}entry')
        fields={'id':url,'title':item['title'],'updated':cms['updatedAt'],
                'summary':'SUZUKA公式noteの記事です。' if is_news else item['description']}
        if len(item['publishedAt'])>10:fields['published']=item['publishedAt']
        for key,value in fields.items():ET.SubElement(entry,'{'+atom+'}'+key).text=value
        ET.SubElement(entry,'{'+atom+'}link',{'href':url});ET.SubElement(entry,'{'+atom+'}category',{'term':'news' if is_news else 'release'})
    entries=feed.findall('{'+atom+'}entry')
    for entry in entries:feed.remove(entry)
    for entry in sorted(entries,key=lambda x:x.findtext('{'+atom+'}published') or x.findtext('{'+atom+'}updated'),reverse=True):feed.append(entry)
    ET.register_namespace('',atom);ET.indent(feed,space='  ')
    files['feed.xml']=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(feed,encoding='utf-8')+b'\n'
    # Single analytics listener owns growth actions and returns before generic outbound counting.
    extension=(root/SOURCE/'analytics-extension.js').read_text()
    js=original['assets/analytics.js'].decode();needle='  document.addEventListener("click", event => {'
    if js.count(needle)!=1:raise ValueError('Analytics insertion point changed')
    js=js.replace(needle,extension+'\n'+needle).replace('    if (!anchor) return;','    if (!anchor) return;\n    if (reportGrowth(anchor)) return;',1)
    js=js.replace('(() => {','(() => {\n  if (window.__suzukaGrowthAnalyticsInstalled) return;\n  window.__suzukaGrowthAnalyticsInstalled = true;',1)
    files['assets/analytics.js']=js.encode()
    social=original['assets/social.js'].decode();needle='      makeLink("LINEで送る",'
    pos=social.index(needle)
    social=social[:pos]+'      makeLink("Facebookでシェア", `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`, "social-share-button", true),\n'+social[pos:]
    social=social.replace('".artist-profile-footer, .site-footer"','".artist-profile-footer, .site-footer, .mp-footer"')
    social=social.replace('    if (footer && !document.querySelector(".social-context-section")) footer.before(section);',
        '''    const share = section.matches(".social-share") ? section : section.querySelector(".social-share");
    const currentShare = document.querySelector(".social-share");
    if (currentShare) {
      const facebook = share?.querySelector('a[href*="facebook.com/sharer"]');
      if (facebook && !currentShare.querySelector('a[href*="facebook.com/sharer"]')) currentShare.append(facebook);
      return;
    }
    const existing = document.querySelector(".social-context-section");
    if (existing && share) existing.append(share);
    else if (footer) footer.before(section);
    else document.querySelector("main")?.append(section);''')
    social=social.replace('  const enhanceCurrentPage = (releases) => {','''  const enhanceCurrentPage = (releases) => {
    if (route === "line-stickers" || (route.startsWith("news/") && !releases.some(item => item.newsPage?.replace(/\\/$/, "") === route))) {
      const title = document.querySelector("h1")?.textContent.trim() || "SUZUKA";
      const canonical = document.querySelector('link[rel="canonical"]')?.href || location.href.split("?")[0].split("#")[0];
      insertBeforeFooter(buildShareButtons(title, canonical));
      return;
    }''')
    social=social.replace('location.href.split("?")[0].split("#")[0]));','(document.querySelector(\'link[rel="canonical"]\')?.href || location.href.split("?")[0].split("#")[0])));')
    social=social.replace('(() => {','(() => {\n  if (window.__suzukaGrowthSocialInstalled) return;\n  window.__suzukaGrowthSocialInstalled = true;',1)
    files['assets/social.js']=social.encode()
    gated_ga=re.search(r'<!-- SUZUKA:GA4:START -->.*?<!-- SUZUKA:GA4:END -->',original['music-production/index.html'].decode(),re.S)[0]
    for name,data in list(files.items()):
        if not name.endswith('.html'):continue
        s=data.decode()
        # Local review must not emit production GA4 page views. One guarded listener
        # also handles pages that historically included a static analytics script.
        s=re.sub(r'<!-- SUZUKA:GA4:START -->.*?<!-- SUZUKA:GA4:END -->',lambda _:gated_ga,s,flags=re.S)
        if name not in {'404.html'}:
            s=s.replace('</head>','<link rel="stylesheet" href="/assets/v6-growth.css"></head>',1) if '/assets/v6-growth.css' not in s else s
        if name.startswith('releases/') and name.count('/')==2:
            if 'assets/social.js' not in s:s=s.replace('</body>','<script defer src="/assets/social.js"></script></body>',1)
            if 'assets/social.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="/assets/social.css"></head>',1)
            slug=name.split('/')[1];r=by.get(slug)
            if r and stream_for(r,sources) and slug not in NEW_SLUGS:
                block='<div class="growth-inline" data-source-section="release_listen">'+streaming_buttons(r,sources,stores=True)+'</div>'
                s=s.replace('</h1>','</h1>'+block,1)
            if slug==birthday['slug']:
                s=s.replace('配信予定','配信中').replace('STREAMING RELEASE / COMING SOON','STREAMING RELEASE / NOW STREAMING')
                s=s.replace('data-streaming-state="upcoming"','data-streaming-state="published"')
        if 'MLmc3jVZ7-M/hqdefault.jpg' in s:s=update_birthday_html(s,birthday,sources)
        s=decorate_links(s,cms,sources)
        # Scoped string updates only where the thirteen-world navigation is displayed.
        if name=='music-production/index.html':s=s.replace('12の世界','13の世界').replace('TWELVE WORLDS','THIRTEEN WORLDS')
        if name=='index.html':s=s.replace('TWELVE ARTISTS, TWELVE STORIES','THIRTEEN ARTISTS, THIRTEEN STORIES')
        if '<nav aria-label="公式サイトのコンテンツ"' in s and 'href="/line-stickers/"' not in s:
            s=re.sub(r'(<nav aria-label="公式サイトのコンテンツ"[^>]*>)',r'\1<a href="/line-stickers/">LINEスタンプ</a>',s,count=1)
        files[name]=s.encode()
    # Preserve every old indexed URL and only add verified public pages.
    sitemap=ET.fromstring(original['sitemap.xml']);existing={x.findtext('{'+NS+'}loc') for x in sitemap}
    new_pages=sorted(n for n in set(files)-set(original) if n.endswith('/index.html'))
    for name in new_pages:
        url=SITE+'/'+name.removesuffix('index.html')
        if url not in existing:ET.SubElement(ET.SubElement(sitemap,'{'+NS+'}url'),'{'+NS+'}loc').text=url
    ET.register_namespace('',NS);ET.indent(sitemap,space='  ')
    files['sitemap.xml']=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(sitemap,encoding='utf-8')+b'\n'
    for name in ['image-sitemap.xml','video-sitemap.xml']:
        tree=ET.fromstring(original[name])
        if name=='image-sitemap.xml':
            ext='http://www.google.com/schemas/sitemap-image/1.1';ET.register_namespace('image',ext)
            for r in new+[birthday]:
                url=SITE+'/'+r['releaseUrl']
                entry=next((x for x in tree if x.findtext('{'+NS+'}loc')==url),None)
                if entry is None:
                    entry=ET.SubElement(tree,'{'+NS+'}url');ET.SubElement(entry,'{'+NS+'}loc').text=url
                im=ET.SubElement(entry,'{'+ext+'}image');ET.SubElement(im,'{'+ext+'}loc').text=SITE+'/'+r['coverImage']
        else:
            ext='http://www.google.com/schemas/sitemap-video/1.1';ET.register_namespace('video',ext)
            for r in new:
                if not r.get('youtubeUrl'):continue
                entry=ET.SubElement(tree,'{'+NS+'}url');ET.SubElement(entry,'{'+NS+'}loc').text=SITE+'/'+r['releaseUrl'];v=ET.SubElement(entry,'{'+ext+'}video')
                for k,val in {'thumbnail_loc':'https://i.ytimg.com/vi/'+r['youtubeUrl'].split('v=')[-1]+'/hqdefault.jpg','title':r['title'],
                    'description':r['description'],'content_loc':r['youtubeUrl'],'player_loc':'https://www.youtube.com/embed/'+r['youtubeUrl'].split('v=')[-1],
                    'duration':str(r['duration']),'publication_date':r['videoPublishedAt']}.items():ET.SubElement(v,'{'+ext+'}'+k).text=val
        ET.indent(tree,space='  ');files[name]=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='utf-8')+b'\n'
    # Fail closed before writing a single preview file if the protected baseline drifts.
    if not set(original)<=set(files):raise ValueError('Existing public path removed; STOP')
    for name,data in original.items():
        protected=name.startswith(('assets/cinema/','assets/baba-nova/','assets/v6-media/','images/','lyrics/')) or name in {
            'assets/cinematic-universe-v6.js','assets/cinematic-universe-v6.css','assets/v6-protected-audio.js','v6-audio-worker.js',
            'assets/celestial-gate.js','assets/main.js','assets/music-production.js','assets/music-production.css'}
        # Lyrics HTML only gains the common CSS/tag decoration; lyrics text itself is separately tested.
        if protected and not name.endswith('.html') and files[name]!=data:raise ValueError('Protected asset changed: '+name)
    verify_private_audio(info,files,manifest['v6Routes'])
    manifest['growthPreview']={'baselineCommit':BASE,'baselineDigest':DIGEST,'approvedScopeDate':'2026-11-01',
        'sourceSha256':sha((root/SOURCE/'verified-sources.json').read_bytes()),'status':'draft-preview-only',
        'publicationApproved':False,'artists':13,'publishedWorks':109,'upcomingWorks':1}
    manifest['sourceCanonicalSha256']=sha(files['assets/data/creator-cms.json'])
    manifest['files']={n:sha(d) for n,d in sorted(files.items()) if n!=MANIFEST}
    files[MANIFEST]=encoded(manifest)
    report={'status':'PASS','baselineCommit':BASE,'baselineFiles':len(original),'files':len(files),'artists':13,'works':109,
        'newWorks':sorted(NEW_SLUGS),'upcoming':pending,'addedFiles':sorted(set(files)-set(original)),
        'changedFiles':sorted(n for n in original if original[n]!=files[n]),'deletedFiles':[],
        'deploymentPerformed':False,'publicationApproved':False,'approvedPackageUnchanged':True}
    return info,files,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path)
    a=p.parse_args();output=a.output.resolve()
    if output==ROOT or output.is_relative_to(ROOT) or 'public-release' in output.parts or output==Path('/'):
        raise ValueError('Preview must be outside the repository/public-release')
    _,files,report=build();write_output(output,files)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes(encoded(report))
    print(json.dumps({k:v for k,v in report.items() if k not in {'addedFiles','changedFiles','upcoming'}},ensure_ascii=False,indent=2))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Verify the five supplied LinkCore pages, then update existing canonical works."""
import copy
import hashlib
import json
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'september-blue': ('HCvApf7V', 'September Blue', '榎本魅愛', '2026-09-22', 'published'),
    'over-drive': ('3tHVbvXs', 'Over Drive', '榎本魅愛', '2026-09-22', 'published'),
    'friendlikesong': ('QFNB1r1u', 'friend like song', '妃みちる', '2026-09-20', 'published'),
    'tatta-hitori-no-kimi-e': ('3Z3vDYPG', 'たった1人の君へ', '妃みちる', '2026-09-20', 'published'),
    'mahou-ga-toketemo': ('tSpMyUFE', '魔法が解けても ― Pumpkin Carriage ―', '神代煌牙', '2026-10-03', 'upcoming'),
}

class Source(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.stores=[]
    def handle_data(self, data):
        if data.strip(): self.text.append(data.strip())
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='a' and attrs.get('id','').startswith('store_id'):
            self.stores.append({'label':attrs.get('title',''), 'url':attrs.get('href','')})

def main():
    now=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')
    evidence=[]
    for slug,(code,title,artist,date,status) in TARGETS.items():
        url='https://linkco.re/'+code
        with urllib.request.urlopen(url+'?lang=ja',timeout=30) as response:
            raw=response.read(); http=response.status
        source=raw.decode(); parsed=Source(); parsed.feed(source)
        assert f'{title} by {artist}' in source, (slug,'title/artist mismatch')
        plain=' | '.join(parsed.text)
        assert date in plain or date.replace('-','/') in plain, (slug,'date mismatch')
        assert ('リリース予定日以降' in plain)==(status=='upcoming'), (slug,'state mismatch')
        destinations=[]
        if status=='published':
            for store in parsed.stores[:4]:
                if '/to/' not in store['url']: continue
                try:
                    with urllib.request.urlopen(store['url'],timeout=25) as response:
                        destinations.append({'url':response.url,'httpStatus':response.status})
                    break
                except Exception: continue
            assert destinations, (slug,'no accessible store destination')
        evidence.append({'slug':slug,'source':url,'title':title,'artist':artist,'releaseDate':date,
                         'status':status,'httpStatus':http,'sourceSha256':hashlib.sha256(raw).hexdigest(),
                         'storeLinks':parsed.stores,'checkedDestinations':destinations})
    path=ROOT/'assets/data/creator-cms.json'; cms=json.loads(path.read_text())
    artists_before=copy.deepcopy(cms['artists'])
    releases={r['slug']:r for r in cms['releases']}
    upcoming={r['slug']:r for r in cms['upcoming']}
    for slug in ('september-blue','over-drive'):
        if slug not in releases:
            old=upcoming[slug]
            video=next(v for v in cms['youtubeSnapshot']['promotionalVideos'] if v['releaseSlug']==slug)
            releases[slug]={
                'id':slug,'slug':slug,'title':old['title'],'displayTitle':old['title'],
                'englishTitle':old['title'],'artist':old['artist'],'artistSlug':old['artistSlug'],
                'artistSlugs':[old['artistSlug']],'artistType':'Person','releaseDate':old['releaseDate'],
                'publishedAt':old['scheduledAt'],'releaseAt':old['scheduledAt'],'releaseYear':2026,
                'releaseType':'single','status':'published','language':'ja','genres':[],'moods':[],'themes':[],
                'tags':[],'coverImage':old['image'],'coverAlt':old['imageAlt'],'coverWidth':886,'coverHeight':886,
                'releaseUrl':f'releases/{slug}/','youtubeUrl':video['youtubeUrl'],'youtubeVideoTitle':video['title'],
                'duration':video['duration'],'videoLabel':'OFFICIAL AUDIO','videoCtaLabel':'先行公開の公式音源を聴く',
                'videoButtonLabel':'LISTEN','videoPublishedAt':video['publishedAt'],
                'videoPublishDate':video['publishedAt'][:10],'videoStructuredDataStatus':'published',
                'videoPublishedAtSource':'official-youtube-videos-or-shorts-tab-and-player-metadata',
                'officialSource':old['linkcoreUrl'],'promotionVerifiedAt':now,'featured':False,
                'recommendationWeight':1,'weeklyPickEligible':True,'analyticsEnabled':True,'upcomingPriority':0,
                'relatedReleases':['hello-hello-halloween','hyakumankoku','hanakotoba'],
                'searchKeywords':old['searchKeywords'],'aiArtistType':'fictional AI artist',
                'galleryImages':[],'galleryPublished':False,'lyricsAvailable':False,'lyricsVerified':False,
                'lyricsSource':'','lyricsText':'','lyricsVerifiedAt':None,
                'shortsUrl':next(v['youtubeUrl'] for v in cms['youtubeSnapshot']['shortVideos'] if v.get('relatedRelease')==slug),
            }
    news={n['slug']:n for n in cms['news']}
    for slug,(code,title,artist,date,status) in TARGETS.items():
        r=releases[slug]
        r['title']=r['displayTitle']=title
        if slug=='friendlikesong': r['englishTitle']=title
        if slug=='tatta-hitori-no-kimi-e': r['englishTitle']='To the Only One'
        r['scheduledStreamingRelease']={
            'releaseDate':date,'timezone':'Asia/Tokyo','status':status,'linkcoreUrl':'https://linkco.re/'+code,
            'source':'user-provided-official-linkcore','verifiedAt':now,
            'verificationSource':'official-linkcore-release-date-and-store-links',
        }
        label='配信開始' if status=='published' else '配信予定'
        description=f'{artist}「{title}」は{date}ストリーミング{label}。公式LinkCoreと作品の動画をご案内します。'
        r['seo']={'title':f'{title}｜{artist}｜SUZUKA Official Music','description':description,'jsonLdEnabled':True}
        if slug in ('september-blue','over-drive'):
            r['description']=r['introduction']=r['productionNote']=description
        r['searchKeywords']=list(dict.fromkeys(r.get('searchKeywords',[])+[title,r['englishTitle'],'LinkCore',label,date]))
        if slug!='mahou-ga-toketemo':
            news_slug=slug+'-streaming-release'
            r.update(newsUrl=f'news/{news_slug}/',newsPublishedAt=now,
                     newsTitle=f'{artist}「{title}」ストリーミング配信開始',
                     newsDescription=f'{date}に配信開始した{artist}「{title}」の公式配信リンクをSUZUKA Newsでお知らせします。',
                     newsBodyParagraphs=[f'{date}よりストリーミング配信を開始しました。各サービスへのリンクはLinkCoreをご確認ください。'])
            news[news_slug]={'slug':news_slug,'title':r['newsTitle'],'artistSlug':r['artistSlug'],
                             'releaseSlug':slug,'publishedAt':now,'description':r['newsDescription'],
                             'image':r['coverImage'],'status':'published'}
        else:
            r['newsBodyParagraphs']=['2026年9月14日公開のOfficial MVに加え、2026年10月3日のストリーミング配信が決定しました。LinkCoreで予約・配信情報をご確認いただけます。']
            r['newsDescription']='神代煌牙「魔法が解けても ― Pumpkin Carriage ―」Official MV公開中。10月3日のストリーミング配信予定と公式LinkCoreを追加しました。'
            r['newsModifiedAt']=now
            n=news['mahou-ga-toketemo-release']; n['description']=r['newsDescription']; n['modifiedAt']=now
    cms['releases']=sorted(releases.values(),key=lambda r:(r['publishedAt'],r['slug']),reverse=True)
    cms['upcoming']=[r for r in cms['upcoming'] if r['slug'] not in ('september-blue','over-drive')]
    cms['news']=sorted(news.values(),key=lambda n:(n['publishedAt'],n['slug']),reverse=True)
    for activity in cms['miaReleaseSchedule']['activities']:
        if activity['title'] in ('September Blue','Over Drive'): activity['status']='published'
    cms['updatedAt']=now
    assert cms['artists']==artists_before, 'Artist canon must remain unchanged'
    path.write_text(json.dumps(cms,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'assets/data/streaming-verification-20260922.json').write_text(json.dumps({'verifiedAt':now,'releases':evidence},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'publishedWorks':len(releases),'upcomingWorks':len(cms['upcoming']),'verified':[(r['slug'],r['status'],r['releaseDate']) for r in evidence]},ensure_ascii=False))

if __name__=='__main__': main()

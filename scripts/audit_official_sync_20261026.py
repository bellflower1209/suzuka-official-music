"""Validate all preserved canonical fields and new 2026-10-26 evidence."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from video_migration import undo_migration

ROOT=Path(__file__).resolve().parents[1]
def main():
    baseline=(ROOT/'docs/official-sync-20261026-baseline.json').read_bytes()
    prior=json.loads(baseline)
    cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
    report=json.loads((ROOT/'docs/official-sync-20261026.json').read_text())
    assert hashlib.sha256(baseline).hexdigest()==report['baselineCmsSha256']
    assert cms['artists'][:12]==prior['artists'] and len(cms['artists'])==13
    assert cms['artists'][12:]==report['addedArtists']
    baba=cms['artists'][-1]
    assert baba['slug']=='baba-nova' and baba['presentationStatus']=='catalog-only' and not baba['image']
    releases={r['slug']:r for r in cms['releases']}
    assert len(releases)==len(cms['releases'])==104
    assert len({r['id'] for r in cms['releases']})==104
    changes={r['releaseSlug']:r for r in report['streamingFieldChanges']}
    migration_path=ROOT/'docs/channel-migration-20261026.json'
    migrations={r['releaseSlug']:r for r in json.loads(migration_path.read_text())['records']} if migration_path.exists() else {}
    for original in prior['releases']:
        current=dict(releases[original['slug']])
        if original['slug'] in migrations:current=undo_migration(current,migrations[original['slug']])
        if original['slug'] in changes:
            change=changes[original['slug']]
            assert current['scheduledStreamingRelease']==change['newValue']
            assert original['scheduledStreamingRelease']==change['previousValue']
            current['scheduledStreamingRelease']=change['previousValue']
        assert current==original, 'Protected release changed: '+original['slug']
    news={x['slug']:x for x in cms['news']}
    assert all(news[x['slug']]==x for x in prior['news'])
    assert len(news)==len(cms['news'])==len(prior['news'])+len(report['addedNews'])
    assert set(news)-{x['slug'] for x in prior['news']}==set(report['addedNews'])
    shorts={s['videoId']:s for s in cms['youtubeSnapshot']['shortVideos']}
    assert len(shorts)==len(cms['youtubeSnapshot']['shortVideos'])==98
    assert cms['youtubeSnapshot']['shortVideos'][:92]==prior['youtubeSnapshot']['shortVideos']
    videos={v['id']:v for v in report['videos']}
    allowed={cms['site']['youtubeChannelId']}|{a.get('officialYoutubeChannelId') for a in cms['artists']}
    dates={x['youtubeId']:x for x in json.loads((ROOT/'assets/data/youtube-publish-dates.json').read_text())['records']}
    for v in videos.values():
        assert v['availability']=='public' and v['live_status']=='not_live' and v['channel_id'] in allowed
        assert v['timestamp']<=datetime.fromisoformat(report['verifiedAt']).timestamp()
        assert datetime.fromisoformat(dates[v['id']]['verifiedPublishedAt']).timestamp()==v['timestamp']
    for slug in report['addedReleases']:
        r=releases[slug];v=videos[r['youtubeUrl'].split('v=')[1]]
        assert r['duration']==v['duration'] and r['youtubeVideoTitle']==v['title']
        assert datetime.fromisoformat(r['publishedAt']).timestamp()==v['timestamp']
        assert r['releaseDate']==r['publishedAt'][:10]
        assert r['formalJacketImage'] is None and not r['lyricsAvailable'] and not r['lyricsVerified']
        assert r['imageRole']=='official-youtube-thumbnail' and r['artworkStatus']=='pending-formal-jacket'
        text=(ROOT/r['releaseUrl']/'index.html').read_text()
        assert r['youtubeUrl'] in text and r['title'] in text
    for identifier in report['addedShorts']:
        s=shorts[identifier];v=videos[identifier]
        assert s['title']==v['title'] and s['duration']==v['duration'] and s['officialChannelId']==v['channel_id']
        assert datetime.fromisoformat(s['publishedAt']).timestamp()==v['timestamp']
        assert s['artistSlug']==releases[s['relatedRelease']]['artistSlug']
    for record in report['noteRecords']:
        n=next(x for x in cms['news'] if x.get('noteUrl')==record['url'])
        assert n['title']==record['title'] and n['publishedAt']==record['publishedAt']
        assert (ROOT/'news'/n['slug']/'index.html').is_file()
    amaterasu=releases['amaterasu']['scheduledStreamingRelease']
    assert amaterasu['status']=='published' and amaterasu['releaseDate']=='2026-10-17'
    assert amaterasu['availableStoreUrls']==['https://music.apple.com/jp/album/amaterasu-single/6818970044']
    birthday=releases['anata-dake-ni-okuru-happy-birthday']
    assert birthday['releaseDate']=='2026-10-25' and birthday['scheduledStreamingRelease']['releaseDate']=='2026-10-31'
    assert birthday['scheduledStreamingRelease']['status']=='upcoming'
    assert not birthday['scheduledStreamingRelease']['availableStoreUrls']
    nox=releases['ikusen-no-yoru-wo-koete']
    assert nox['publishedAt']=='2026-10-26T20:00:06+09:00' and nox['duration']==277
    config=json.loads((ROOT/'assets/data/celestial-gate.json').read_text())
    assert len(config['themes'])==12 and 'baba-nova' not in config['themes']
    assert report['artistScopeApproval']['source']=='explicit-user-message'
    for image in report['addedImages']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256']
    print(json.dumps({'status':'PASS','artists':13,'publishedWorks':104,'shorts':98,'news':len(cms['news']),'protectedPriorWorks':99,'newAudioWorks':5,'newShorts':6,'newNoteNews':len(report['noteRecords']),'streamingPromotions':1,'preservedWorlds':12}))
if __name__=='__main__':main()

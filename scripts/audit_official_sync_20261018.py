"""Validate current official activity and preservation against the prior source."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

def main(cms_path=None):
    cms=json.loads((cms_path or ROOT/'assets/data/creator-cms.json').read_text())
    prior=json.loads((ROOT/'docs/official-sync-20261018-baseline.json').read_text())
    report=json.loads((ROOT/'docs/official-sync-20261018.json').read_text())
    releases={r['slug']:r for r in cms['releases']}
    assert len(releases)==len(cms['releases'])==99
    assert cms['artists']==prior['artists'] and len(cms['artists'])==12
    assert len({r['id'] for r in cms['releases']})==99
    for original in prior['releases']:
        current=releases[original['slug']]
        permitted={'videoVersions'} if original['slug']=='hyakumankoku' else set()
        if original['slug'] in report['additionalStreamingUpdates']:
            permitted|={'scheduledStreamingRelease','streamingTracks'}
        if original['slug']=='ame-nochi-anata':
            permitted|={'scheduledStreamingRelease','description','introduction','productionNote','seo'}
        assert {k:v for k,v in original.items() if k not in permitted}=={k:v for k,v in current.items() if k not in permitted}, original['slug']
        if 'videoVersions' in permitted:
            assert current['videoVersions'][:-1]==original.get('videoVersions',[])
    allowed={a.get('officialYoutubeChannelId') for a in cms['artists']}|{cms['site']['youtubeChannelId']}
    videos={v['id']:v for v in report['videos']}
    assert len(videos)==18
    for v in videos.values():
        assert v['channel_id'] in allowed and v['availability']=='public' and v['live_status']=='not_live'
        assert v['timestamp']<=datetime.fromisoformat(report['verifiedAt']).timestamp()
    for slug in report['addedReleases']:
        item=releases[slug];vid=item['youtubeUrl'].split('v=')[1];v=videos[vid]
        assert item['duration']==v['duration'] and item['youtubeVideoTitle']==v['title']
        assert item['videoPublishedAt']==item['publishedAt'] and item['releaseDate']==item['publishedAt'][:10]
        assert datetime.fromisoformat(item['publishedAt']).timestamp()==v['timestamp']
        assert item['videoLabel']=='OFFICIAL AUDIO' and not item['lyricsAvailable'] and not item['lyricsVerified']
        assert item['formalJacketImage'] is None and item['artworkStatus']=='pending-formal-jacket'
        assert not item.get('streamingRelease')
        if slug not in report['additionalStreamingUpdates']:assert not item.get('scheduledStreamingRelease')
    for slug in report['promotedStreaming']+report['updatedStreaming']:
        item=releases[slug];stream=item['scheduledStreamingRelease']
        assert stream['status']=='published' and stream['releaseDate']<=report['verifiedAt'][:10]
        assert stream['availableStoreUrls'] and all(urlsplit(u).hostname in {'music.apple.com','open.spotify.com'} and '/search' not in u for u in stream['availableStoreUrls'])
        assert not any(x['slug']==slug for x in cms['comingSoon'])
    assert len(report['stores'])==3 and all(x['status']==200 and urlsplit(x['finalUrl']).hostname=='music.apple.com' for x in report['stores'])
    for source in report['additionalStreamingEvidence']:
        if 'releaseSlug' not in source:continue
        item=releases[source['releaseSlug']];stream=item['scheduledStreamingRelease']
        assert source['httpStatus']==200 and source['listenAction'] and source['previewMetadata']
        assert source['date']==source['releaseDate']==stream['releaseDate']<=report['verifiedAt'][:10]
        assert stream['availableStoreUrls']==[source['finalUrl']] and stream['linkcoreUrl']==source['linkcore']
        assert source['artist'][0]['name']==item['artist'] and stream['officialStreamingTitle']+' by '+item['artist']==source['title']
    for slug in report['addedStreamingReleases']:
        item=releases[slug]
        assert not item.get('youtubeUrl') and not item['lyricsAvailable'] and item['artworkStatus']=='verified-public-linkcore'
        assert item['coverImage']==item['formalJacketImage'] and (ROOT/item['coverImage']).is_file()
    for group in ['news']:
        current={x['slug']:x for x in cms[group]}
        assert all(current[x['slug']]==x for x in prior[group])
    shorts=cms['youtubeSnapshot']['shortVideos'];ids=[x['videoId'] for x in shorts]
    assert len(ids)==len(set(ids))==92
    assert shorts[:len(prior['youtubeSnapshot']['shortVideos'])]==prior['youtubeSnapshot']['shortVideos']
    for s in shorts:
        if s['videoId'] not in report['addedShorts']:continue
        v=videos[s['videoId']]
        assert s['officialChannelId']==v['channel_id'] and s['duration']==v['duration'] and s['title']==v['title']
        assert datetime.fromisoformat(s['publishedAt']).timestamp()==v['timestamp']
        if s['relatedRelease']:assert s['artistSlug']==releases[s['relatedRelease']]['artistSlug']
    assert not cms['comingSoon'] and not cms['upcoming']
    print(json.dumps({'status':'PASS','publishedWorks':99,'artists':12,'addedAudioWorks':6,'addedStreamingWorks':2,'addedMVVersions':1,'addedShorts':11,'addedNoteNews':1,'promotedStreamingPlans':2,'additionalStreamingUpdates':6,'unmatchedOfficialTitlesHeld':1}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cms',type=Path,help='Explicit historical snapshot for this dated audit')
    main(parser.parse_args().cms)

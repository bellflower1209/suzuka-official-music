#!/usr/bin/env python3
"""Audit the 2026-10-12 official sync evidence and immutable catalog fields."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text())
    report = json.loads((ROOT / "docs/official-sync-20261012.json").read_text())
    releases = {item["slug"]: item for item in cms["releases"]}
    artists = {item["slug"]: item for item in cms["artists"]}
    assert len(releases) == len(cms["releases"]), "Duplicate release slug"
    assert len(artists) == 12, "Artist inventory changed"
    for slug, expected in report["protectedBaseline"]["artists"].items():
        assert digest(artists[slug]) == expected, f"Protected Artist changed: {slug}"
    for slug, expected in report["protectedBaseline"]["releases"].items():
        original = {k: v for k, v in releases[slug].items() if k != "videoVersions"}
        for change in report.get('approvedFieldChanges', []):
            if change['releaseSlug'] != slug:
                continue
            assert change['field'] == 'scheduledStreamingRelease', "Only the evidence-backed secondary streaming field may change"
            assert original.get(change['field']) == change['newValue'], f"Unapproved streaming value: {slug}"
            if change['previouslyPresent']:
                original[change['field']] = change['previousValue']
            else:
                original.pop(change['field'], None)
        assert digest(original) == expected, f"Protected release fields changed: {slug}"
    records = {r["sourceUrl"]: r for r in report["records"] if "videoId" in r}
    now = datetime.fromisoformat(report["verifiedAt"])
    allowed = {"UCVde75yhByGQMu3SkO-fzrA", "UCRwW7smDoEB-UOHMQJJ1Jyg", "UCtRwFzemyx508t7yXnpCVKA", "UCDqoQCLOp0lWb1bZ6vWEM3g"}

    def verify(url):
        record = records[url]
        assert record["playabilityStatus"] == "OK", f"Unverified playability: {url}"
        assert record["isUnlisted"] is False, f"Non-public video: {url}"
        assert record["channelId"] == record["expectedChannelId"] and record["channelId"] in allowed, f"Wrong Artist channel: {url}"
        assert datetime.fromisoformat(record["publishedOrScheduledAtJst"]) <= now, f"Future premiere: {url}"
        return record

    for slug in report["mutations"]["addedReleases"]:
        item = releases[slug]
        source = verify(item["youtubeUrl"])
        assert item["duration"] == source["duration"]
        assert item["publishedAt"] == source["publishedOrScheduledAtJst"]
        assert item["releaseDate"] == item["publishedAt"][:10]
        if slug in report.get('updatedNewArtwork', {}):
            assert item['imageRole'] == 'official-linkcore-artwork' and item['artworkStatus'] == 'verified-public-linkcore'
            assert item['formalJacketImage'] == item['coverImage'] and item['coverSource'] == report['updatedNewArtwork'][slug]
        else:
            assert item["imageRole"] == "official-youtube-thumbnail" and item["artworkStatus"] == "pending-formal-jacket"
            assert item["formalJacketImage"] is None and item["coverImage"] == item["youtubeThumbnailUrl"]
            assert "公式YouTubeサムネイル" in item["coverAlt"] and "正式ジャケット確認待ち" in item["coverAlt"]
        assert item["lyricsAvailable"] is False and item["lyricsVerified"] is False
        assert not item.get("streamingRelease")
    for change in report["mutations"]["addedVideoVersions"]:
        source = verify(change["youtubeUrl"])
        versions = [v for v in releases[change["releaseSlug"]]["videoVersions"] if v["youtubeUrl"] == change["youtubeUrl"]]
        assert len(versions) == 1, f"Duplicate video variant: {change}"
        assert versions[0]["title"] == source["officialTitle"]
        assert versions[0]["publishedAt"] == source["publishedOrScheduledAtJst"]
        assert versions[0]["duration"] == source["duration"]
    shorts = {v["videoId"]: v for v in cms["youtubeSnapshot"]["shortVideos"]}
    assert len(shorts) == len(cms["youtubeSnapshot"]["shortVideos"]), "Duplicate Shorts"
    for video_id in report["mutations"]["addedShorts"]:
        item = shorts[video_id]
        source = verify(item["youtubeUrl"])
        assert item["title"] == source["officialTitle"] and item["publishedAt"] == source["publishedOrScheduledAtJst"]
        assert item["duration"] == source["duration"]
        if item["relatedRelease"]:
            assert item["artistSlug"] == releases[item["relatedRelease"]]["artistSlug"]
        assert item["officialChannelId"] == source["channelId"]
    public_video_urls = {r.get("youtubeUrl") for r in cms["releases"]}
    public_video_urls |= {v["youtubeUrl"] for r in cms["releases"] for v in r.get("videoVersions", [])}
    public_video_urls |= {v["youtubeUrl"] for v in shorts.values()}
    for record in records.values():
        if record["classification"] == "確認待ち":
            assert record["sourceUrl"] not in public_video_urls, f"Pending source published: {record['sourceUrl']}"
    note_records = {r["sourceUrl"]: r for r in report["records"] if r["service"] == "note"}
    news = {n["slug"]: n for n in cms["news"]}
    for slug in report["mutations"]["addedNews"]:
        item = news[slug]; source = note_records[item["noteUrl"]]
        assert item["title"] == source["officialTitle"] and item["publishedAt"] == source["publishedAt"]
    if report.get('publicStreamingReverification'):
        streaming_sources = {r['sourceUrl'].split('?')[0]: r for r in report['publicStreamingReverification']}
        destinations = {r['sourceUrl']: r for r in report['publicStoreDestinationReverification']}
        today = now.date().isoformat()
        stream_items = [releases[change['releaseSlug']] for change in report.get('approvedFieldChanges', [])]
        stream_items += [releases[slug] for key in ['addedStreamingReleases', 'addedYouTubeReleases20261013'] for slug in report['mutations'].get(key, [])]
        stream_items += [releases[slug] for slug in report.get('updatedNewArtwork', {})]
        stream_items += [p for p in cms.get('comingSoon', []) if p['slug'] in report['mutations'].get('addedStreamingPlans', [])]
        for item in stream_items:
            value = item['scheduledStreamingRelease']; source = streaming_sources[value['linkcoreUrl']]
            assert source['httpStatus'] == 200 and value['releaseDate'] == source['releaseDate']
            assert value['officialStreamingTitle'] == source['officialTitle'].split(' by ')[0]
            assert item['artist'] in source['officialTitle']
            if value['status'] == 'published':
                assert value['releaseDate'] <= today and source['storeUrls']
                for url in source['storeUrls']:
                    destination = destinations[url]
                    assert destination['httpStatus'] == 200 and urlparse(destination['finalUrl']).hostname in {'music.apple.com', 'open.spotify.com'}
            else:
                assert value['status'] == 'upcoming' and value['releaseDate'] > today
        for slug in report['mutations'].get('addedStreamingReleases', []):
            item = releases[slug]; assert item['status'] == 'published' and not item['youtubeUrl']
            assert item['releaseDate'] == item['scheduledStreamingRelease']['releaseDate'] and not item['lyricsAvailable']
        for slug in report['mutations'].get('addedYouTubeReleases20261013', []):
            item = releases[slug]; source = verify(item['youtubeUrl'])
            assert item['publishedAt'] == source['publishedOrScheduledAtJst'] and item['duration'] == source['duration']
            assert item['releaseDate'] == item['publishedAt'][:10] and not item['lyricsAvailable']
        for item in stream_items:
            if item.get('imageRole') == 'official-linkcore-artwork':
                source = streaming_sources[item['coverSource'].split('?')[0]]
                assert hashlib.sha256((ROOT / item['coverImage']).read_bytes()).hexdigest() == source['jacketVerification']['sha256']
        for item in cms.get('comingSoon', []):
            assert item['datePrecision'] == 'day' and item['announcementPublic'] is True and not item.get('scheduledAt')
            assert item['status'] == 'upcoming' and not item.get('youtubeUrl') and item['slug'] not in releases
        assert report['finalCounts']['publishedWorks'] == len(releases) == 89
        assert report['finalCounts']['publicStreamingPlans'] == len(cms.get('comingSoon', [])) == 2
    assert artists["enomoto-mia"]["officialYoutubeChannelId"] == "UCRwW7smDoEB-UOHMQJJ1Jyg"
    assert artists["koga-kamishiro"]["officialYoutubeChannelId"] == "UCtRwFzemyx508t7yXnpCVKA"
    assert artists["michiru"]["officialYoutubeChannelId"] == "UCDqoQCLOp0lWb1bZ6vWEM3g"
    print(json.dumps({"status": "PASS", "protectedArtists": 12, "protectedReleases": len(report["protectedBaseline"]["releases"]),
                      **{key: len(value) for key, value in report["mutations"].items()},
                      "pendingVideosExcluded": sum(r['classification'] == '確認待ち' for r in records.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()

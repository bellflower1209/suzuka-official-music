#!/usr/bin/env python3
"""Apply official YouTube publication evidence verified on 2026-08-28."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
MIA_RELEASES_PATH = ROOT / "assets/data/enomoto-mia-releases.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260828.json"
NOW = "2026-08-28T00:37:35+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


NEW_RELEASE = {
    "slug": "updown",
    "title": "UPdown",
    "artist": "妃みちる",
    "artistSlug": "michiru",
    "releaseAt": "2026-08-27T22:48:02+09:00",
    "youtubeId": "SKUMF7ZhpRM",
    "youtubeUrl": "https://www.youtube.com/watch?v=SKUMF7ZhpRM",
    "duration": 245,
    "officialTitle": "【新曲】UPdown｜好きな子の前じゃ、平常心なんて無理。🎆💓｜妃みちる",
    "description": "夏祭りの夜、好きな人への告白で上がったり下がったりする心を、コミカルかつまっすぐに歌う妃みちるの新曲。",
    "genres": ["J-POP"],
    "moods": ["明るい", "コミカル"],
    "themes": ["恋愛", "告白", "夏祭り"],
    "tags": ["妃みちる", "UPdown", "恋愛ソング", "告白ソング", "夏祭り", "花火", "青春"],
}


UPDATED_VIDEOS = [
    {
        "releaseSlug": "kimi-to-nara-last-boss-made",
        "videoId": "VyFAFnfn5dc",
        "youtubeUrl": "https://www.youtube.com/watch?v=VyFAFnfn5dc",
        "publishedAt": "2026-08-26T20:00:06+09:00",
        "duration": 328,
        "title": "【MV】榎本魅愛「君とならラスボスまで」｜伝説の剣なんて、なくてもいい。",
        "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "audioUrl": "https://www.youtube.com/watch?v=YVNs3I-KaHI",
    },
    {
        "releaseSlug": "ashita-wa-kitto",
        "videoId": "HKm8cUorTOs",
        "youtubeUrl": "https://www.youtube.com/watch?v=HKm8cUorTOs",
        "publishedAt": "2026-08-26T21:13:36+09:00",
        "duration": 217,
        "title": "【MV解禁】榎本魅愛『明日は、きっと。』｜君はひとりじゃない。希望をつなぐ歌",
        "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "audioUrl": "https://www.youtube.com/watch?v=5MkQZT5qiGA",
    },
]


NEW_SHORT = {
    "videoId": "YqXpqb19crM",
    "title": "泣いてもいい。それでも明日は、きっと来る。｜榎本魅愛 #shorts",
    "artist": "榎本魅愛",
    "artistSlug": "enomoto-mia",
    "publishedAt": "2026-08-26T21:19:39+09:00",
    "relatedRelease": "ashita-wa-kitto",
    "duration": 61,
    "description": "榎本魅愛「明日は、きっと。」Official Music Videoの希望を伝える公式Shorts。",
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_release(artist_type: str) -> dict:
    item = NEW_RELEASE
    release_at = item["releaseAt"]
    cover = f'https://i.ytimg.com/vi/{item["youtubeId"]}/maxresdefault.jpg'
    tags = list(dict.fromkeys([*item["tags"], *item["genres"], *item["themes"], *item["moods"]]))
    return {
        "slug": item["slug"], "id": item["slug"], "title": item["title"],
        "displayTitle": item["title"], "englishTitle": item["title"],
        "artist": item["artist"], "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]], "artistType": artist_type,
        "releaseAt": release_at, "publishedAt": release_at,
        "releaseDate": release_at[:10], "releaseYear": 2026, "releaseType": "single",
        "genres": item["genres"], "moods": item["moods"], "themes": item["themes"],
        "tags": tags, "language": "ja", "coverImage": cover,
        "coverAlt": "妃みちる「UPdown」公式YouTubeサムネイル",
        "youtubeUrl": item["youtubeUrl"], "videoLabel": "OFFICIAL VIDEO",
        "youtubeVideoTitle": item["officialTitle"],
        "videoCtaLabel": "公式動画を見る", "videoButtonLabel": "WATCH VIDEO",
        "shortsUrl": "", "releaseUrl": "releases/updown/", "newsUrl": "",
        "duration": item["duration"], "status": "published", "featured": True,
        "recommendationWeight": 3, "weeklyPickEligible": True,
        "analyticsEnabled": True, "upcomingPriority": 0, "relatedReleases": [],
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist", "description": item["description"],
        "introduction": item["description"], "galleryImages": [],
        "galleryPublished": False, "productionNote": item["description"],
        "seo": {
            "title": "UPdown｜妃みちる｜SUZUKA Official Music",
            "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": release_at[:10], "videoPublishedAt": release_at,
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "videoStructuredDataStatus": "published", "officialSource": item["youtubeUrl"],
        "promotionVerifiedAt": NOW, "lyricsAvailable": False, "lyricsSource": "",
        "lyricsText": "", "lyricsVerified": False, "lyricsVerifiedAt": None,
    }


def short_record(item: dict) -> dict:
    video_id = item["videoId"]
    return {
        **item,
        "youtubeUrl": f"https://www.youtube.com/shorts/{video_id}",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
    }


def evidence_record(item: dict, *, content_type: str = "video") -> dict:
    video_id = item["videoId"]
    published_at = item["publishedAt"]
    source = item.get(
        "verificationSource",
        "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
    )
    url = f"https://www.youtube.com/{'shorts/' if content_type == 'short' else 'watch?v='}{video_id}"
    return {
        "releaseSlug": item["releaseSlug"], "youtubeId": video_id,
        "youtubeUrl": url, "catalogReleaseDate": published_at[:10],
        "officialTitle": item["title"], "channelId": CHANNEL_ID,
        "channelVerified": True, "youtubePublishDate": published_at,
        "youtubeUploadDate": published_at,
        "liveStartTimestamp": published_at if "liveBroadcastDetails" in source else "",
        "playabilityStatus": "OK", "durationSeconds": item["duration"],
        "verifiedPublishedAt": published_at, "verificationSource": source,
        "status": "verified-datetime",
        **({"contentType": "short"} if content_type == "short" else {}),
    }


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}
    releases[NEW_RELEASE["slug"]] = create_release(artists["michiru"]["type"])

    for update in UPDATED_VIDEOS:
        release = releases[update["releaseSlug"]]
        release.update({
            "audioUrl": update["audioUrl"], "youtubeUrl": update["youtubeUrl"],
            "youtubeVideoTitle": update["title"],
            "duration": update["duration"], "videoPublishDate": update["publishedAt"][:10],
            "videoPublishedAt": update["publishedAt"],
            "videoPublishedAtSource": update["verificationSource"],
            "videoStructuredDataStatus": "published", "officialSource": update["youtubeUrl"],
            "promotionVerifiedAt": NOW,
        })
    releases["ashita-wa-kitto"]["shortsUrl"] = "https://www.youtube.com/shorts/YqXpqb19crM"
    releases["ashita-wa-kitto"]["promotionVerifiedAt"] = NOW
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )
    cms["upcoming"] = [item for item in cms.get("upcoming", []) if item["slug"] != "updown"]
    artists["michiru"]["artistFeaturedTracks"] = [
        "updown",
        *[slug for slug in artists["michiru"].get("artistFeaturedTracks", []) if slug != "updown"],
    ][:3]

    snapshot = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    shorts[NEW_SHORT["videoId"]] = short_record(NEW_SHORT)
    snapshot.update({
        "officialVideos": 63, "shorts": 42, "totalPublishedVideos": 105,
        "verifiedAt": NOW,
        "source": "公式YouTube Atomフィード・videos/shortsタブ・各動画のytInitialPlayerResponseを照合",
        "shortVideos": sorted(
            shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True
        ),
        "scheduledVideos": [],
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    # Keep the legacy 榎本魅愛 catalog aligned because SEO/card audits still
    # consume it as a compatibility source.  Preserve the original audio URL
    # separately while promoting the confirmed full MV as the primary video.
    mia_catalog = json.loads(MIA_RELEASES_PATH.read_text(encoding="utf-8"))
    mia_releases = {item["slug"]: item for item in mia_catalog["releases"]}
    for update in UPDATED_VIDEOS:
        release = mia_releases.get(update["releaseSlug"])
        if not release:
            continue
        release.update({
            "audioUrl": update["audioUrl"],
            "youtubeUrl": update["youtubeUrl"],
            "youtubeId": update["videoId"],
            "youtubeVideoTitle": update["title"],
            "duration": update["duration"],
            "uploadDate": update["publishedAt"],
        })
    write_json(MIA_RELEASES_PATH, mia_catalog)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    evidence_inputs = [
        {
            "releaseSlug": NEW_RELEASE["slug"], "videoId": NEW_RELEASE["youtubeId"],
            "title": NEW_RELEASE["officialTitle"], "publishedAt": NEW_RELEASE["releaseAt"],
            "duration": NEW_RELEASE["duration"],
        },
        *UPDATED_VIDEOS,
    ]
    for item in evidence_inputs:
        record = evidence_record(item)
        records[(record["releaseSlug"], record["youtubeId"])] = record
    short_evidence = evidence_record(
        {**NEW_SHORT, "releaseSlug": NEW_SHORT["relatedRelease"]}, content_type="short"
    )
    records[(short_evidence["releaseSlug"], short_evidence["youtubeId"])] = short_evidence
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state_evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    state_inputs = [
        {"slug": "updown", "videoId": "SKUMF7ZhpRM", "releaseTimestamp": NEW_RELEASE["releaseAt"], "liveStatus": "not_live"},
        {"slug": "kimi-to-nara-last-boss-made", "videoId": "VyFAFnfn5dc", "releaseTimestamp": "2026-08-26T20:00:06+09:00", "liveStatus": "was_live"},
        {"slug": "ashita-wa-kitto", "videoId": "HKm8cUorTOs", "releaseTimestamp": "2026-08-26T21:13:36+09:00", "liveStatus": "was_live"},
    ]
    for item in state_inputs:
        state_evidence[(item["slug"], item["videoId"])] = {
            **item, "availability": "public", "channelId": CHANNEL_ID,
        }
    state.update({
        "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "promoted": sorted(set(state.get("promoted", [])) | {"updown"}),
        "evidence": sorted(state_evidence.values(), key=lambda item: (item["slug"], item["videoId"])),
        "upcomingHeld": [],
    })
    write_json(STATE_PATH, state)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィード、videos/shortsタブ、各動画のytInitialPlayerResponseを照合",
        "channelSnapshot": {"officialVideos": 63, "shorts": 42, "totalPublishedVideos": 105},
        "published": [NEW_RELEASE],
        "updatedVideos": [{**item, "status": "published", "playabilityStatus": "OK"} for item in UPDATED_VIDEOS],
        "shorts": snapshot["shortVideos"], "upcomingHeld": [],
    })
    print(json.dumps({
        "publishedRelease": "updown",
        "updatedVideos": [item["releaseSlug"] for item in UPDATED_VIDEOS],
        "newShorts": [NEW_SHORT["videoId"]], "releaseCount": len(cms["releases"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

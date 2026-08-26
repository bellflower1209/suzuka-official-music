#!/usr/bin/env python3
"""Apply official YouTube publication evidence verified on 2026-08-26."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260826.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
NOW = "2026-08-26T18:16:37+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"


NEW_RELEASE = {
    "slug": "re-sonance",
    "title": "RE:SONANCE",
    "artist": "RE:VIVE",
    "artistSlug": "revive",
    "releaseAt": "2026-08-22T22:13:44+09:00",
    "youtubeId": "EZp_Mtxt4G4",
    "youtubeUrl": "https://www.youtube.com/watch?v=EZp_Mtxt4G4",
    "duration": 329,
    "description": "星宮羽音を迎えた現行5人体制のRE:VIVEが、小さな声が5つの光へ変わる瞬間を描く新体制初のシングル。",
    "genres": ["J-POP", "アイドルポップ"],
    "moods": ["希望", "温かい"],
    "themes": ["希望", "再生", "つながり"],
    "tags": ["RE:VIVE", "RE:SONANCE", "新生RE:VIVE", "星宮羽音", "JPOP", "EmoJPop"],
}


UPDATED_VIDEOS = [
    {
        "releaseSlug": "watashi-no-eranda-michi",
        "videoId": "FC1D7-0SeBc",
        "youtubeUrl": "https://www.youtube.com/watch?v=FC1D7-0SeBc",
        "publishedAt": "2026-08-23T20:00:06+09:00",
        "duration": 343,
        "title": "【MV】妃みちる『私の選んだ道』｜好きだから、追わない道を選んだ。",
        "verificationSource": "official-youtube-liveBroadcastDetails.startTimestamp",
    },
    {
        "releaseSlug": "chimpanzee-no-rakuen",
        "videoId": "eSRxfGqzYOk",
        "youtubeUrl": "https://www.youtube.com/watch?v=eSRxfGqzYOk",
        "publishedAt": "2026-08-24T00:44:44+09:00",
        "duration": 149,
        "title": "百年後、人間は檻の中。｜NOX「チンパンジーの楽園」Official MV",
        "verificationSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
    },
]


NEW_SHORTS = [
    {
        "videoId": "rOuv1KMQCL8",
        "title": "「人間が主役の動物園」｜NOX「チンパンジーの楽園」 #shorts",
        "artist": "NOX",
        "artistSlug": "nox",
        "publishedAt": "2026-08-24T00:48:48+09:00",
        "relatedRelease": "chimpanzee-no-rakuen",
        "duration": 51,
        "description": "NOX「チンパンジーの楽園」Official MVの世界を紹介する公式Shorts。",
    },
    {
        "videoId": "ERC1LArVpEk",
        "title": "【制作中】RANGILI「Namaste Galaxy」MV制作中！✨",
        "artist": "RANGILI",
        "artistSlug": "rangili",
        "publishedAt": "2026-08-24T20:35:00+09:00",
        "relatedRelease": "namaste-galaxy",
        "duration": 49,
        "description": "RANGILI「NAMASTE☆GALAXY」MVの制作中映像を紹介する公式Shorts。",
    },
    {
        "videoId": "5cWf76QSruU",
        "title": "【MV Teaser】伝説の剣なんて、なくてもいい。｜榎本魅愛「君とならラスボスまで」#shorts",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-08-25T00:33:13+09:00",
        "relatedRelease": "kimi-to-nara-last-boss-made",
        "duration": 76,
        "description": "榎本魅愛「君とならラスボスまで」新作MVの公式ティザーShorts。",
    },
    {
        "videoId": "14sVB_BZ3sU",
        "title": "剣も魔法もない。それでも君となら。｜榎本魅愛「君とならラスボスまで」1番先行公開",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "publishedAt": "2026-08-25T22:21:55+09:00",
        "relatedRelease": "kimi-to-nara-last-boss-made",
        "duration": 120,
        "description": "榎本魅愛「君とならラスボスまで」新作MVの1番を公開した公式Shorts。",
    },
]


SCHEDULED_HELD = {
    "videoId": "VyFAFnfn5dc",
    "title": "【本日解禁】君となら、ラスボスまで行ける。｜榎本魅愛「君とならラスボスまで」MV",
    "scheduledAt": "2026-08-27T20:00:00+09:00",
    "relatedRelease": "kimi-to-nara-last-boss-made",
    "status": "upcoming",
    "playabilityStatus": "LIVE_STREAM_OFFLINE",
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def short_record(item: dict) -> dict:
    video_id = item["videoId"]
    return {
        **item,
        "youtubeUrl": f"https://www.youtube.com/shorts/{video_id}",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        "status": "published",
        "contentType": "short",
    }


def evidence_record(
    slug: str,
    video_id: str,
    title: str,
    published_at: str,
    duration: int,
    *,
    content_type: str = "video",
    source: str = "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
) -> dict:
    url = f"https://www.youtube.com/{'shorts/' if content_type == 'short' else 'watch?v='}{video_id}"
    return {
        "releaseSlug": slug,
        "youtubeId": video_id,
        "youtubeUrl": url,
        "catalogReleaseDate": published_at[:10],
        "officialTitle": title,
        "channelId": CHANNEL_ID,
        "channelVerified": True,
        "youtubePublishDate": published_at,
        "youtubeUploadDate": published_at,
        "liveStartTimestamp": published_at if video_id == "FC1D7-0SeBc" else "",
        "playabilityStatus": "OK",
        "durationSeconds": duration,
        "verifiedPublishedAt": published_at,
        "verificationSource": source,
        "status": "verified-datetime",
        **({"contentType": "short"} if content_type == "short" else {}),
    }


def create_release(artist_type: str) -> dict:
    item = NEW_RELEASE
    release_at = item["releaseAt"]
    cover = f'https://i.ytimg.com/vi/{item["youtubeId"]}/maxresdefault.jpg'
    tags = list(dict.fromkeys([*item["tags"], *item["genres"], *item["themes"], *item["moods"]]))
    return {
        "slug": item["slug"],
        "id": item["slug"],
        "title": item["title"],
        "displayTitle": item["title"],
        "englishTitle": item["title"],
        "artist": item["artist"],
        "artistSlug": item["artistSlug"],
        "artistSlugs": [item["artistSlug"]],
        "artistType": artist_type,
        "releaseAt": release_at,
        "publishedAt": release_at,
        "releaseDate": release_at[:10],
        "releaseYear": 2026,
        "releaseType": "single",
        "genres": item["genres"],
        "moods": item["moods"],
        "themes": item["themes"],
        "tags": tags,
        "language": "ja",
        "coverImage": cover,
        "coverAlt": 'RE:VIVE「RE:SONANCE」公式YouTubeサムネイル',
        "youtubeUrl": item["youtubeUrl"],
        "videoLabel": "OFFICIAL VIDEO",
        "videoCtaLabel": "公式動画を見る",
        "videoButtonLabel": "WATCH VIDEO",
        "shortsUrl": "",
        "releaseUrl": "releases/re-sonance/",
        "newsUrl": "",
        "duration": item["duration"],
        "status": "published",
        "featured": True,
        "recommendationWeight": 3,
        "weeklyPickEligible": True,
        "analyticsEnabled": True,
        "upcomingPriority": 0,
        "relatedReleases": [],
        "searchKeywords": list(dict.fromkeys([item["title"], item["artist"], *tags])),
        "aiArtistType": "fictional AI artist",
        "description": item["description"],
        "introduction": item["description"],
        "galleryImages": [],
        "galleryPublished": False,
        "productionNote": item["description"],
        "seo": {
            "title": "RE:SONANCE｜RE:VIVE｜SUZUKA Official Music",
            "description": f'{item["description"]} SUZUKAの架空のAIアーティスト作品です。',
            "jsonLdEnabled": True,
        },
        "videoPublishDate": release_at[:10],
        "videoPublishedAt": release_at,
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "videoStructuredDataStatus": "published",
        "officialSource": item["youtubeUrl"],
        "promotionVerifiedAt": NOW,
        "lyricsAvailable": False,
        "lyricsSource": "",
        "lyricsText": "",
        "lyricsVerified": False,
        "lyricsVerifiedAt": None,
    }


def update_release_videos(releases: dict[str, dict]) -> None:
    watashi = releases["watashi-no-eranda-michi"]
    watashi.update({
        "audioUrl": "https://www.youtube.com/watch?v=rsrkmzJM1kk",
        "youtubeUrl": "https://www.youtube.com/watch?v=FC1D7-0SeBc",
        "coverImage": "https://i.ytimg.com/vi/FC1D7-0SeBc/maxresdefault.jpg",
        "duration": 343,
        "videoPublishDate": "2026-08-23",
        "videoPublishedAt": "2026-08-23T20:00:06+09:00",
        "videoPublishedAtSource": "official-youtube-liveBroadcastDetails.startTimestamp",
        "officialSource": "https://www.youtube.com/watch?v=FC1D7-0SeBc",
        "promotionVerifiedAt": NOW,
    })

    chimpanzee = releases["chimpanzee-no-rakuen"]
    chimpanzee.update({
        "audioUrl": "https://www.youtube.com/watch?v=EJJLBOo103I",
        "youtubeUrl": "https://www.youtube.com/watch?v=eSRxfGqzYOk",
        "shortsUrl": "https://www.youtube.com/shorts/rOuv1KMQCL8",
        "duration": 149,
        "videoPublishDate": "2026-08-24",
        "videoPublishedAt": "2026-08-24T00:44:44+09:00",
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "officialSource": "https://www.youtube.com/watch?v=eSRxfGqzYOk",
        "promotionVerifiedAt": NOW,
    })

    releases["namaste-galaxy"]["shortsUrl"] = "https://www.youtube.com/shorts/ERC1LArVpEk"
    releases["namaste-galaxy"]["promotionVerifiedAt"] = NOW
    releases["kimi-to-nara-last-boss-made"]["shortsUrl"] = "https://www.youtube.com/shorts/14sVB_BZ3sU"
    releases["kimi-to-nara-last-boss-made"]["promotionVerifiedAt"] = NOW


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    releases = {item["slug"]: item for item in cms["releases"]}
    releases[NEW_RELEASE["slug"]] = create_release(artists["revive"]["type"])
    update_release_videos(releases)
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )
    cms["upcoming"] = [item for item in cms.get("upcoming", []) if item["slug"] != NEW_RELEASE["slug"]]
    artists["revive"]["artistFeaturedTracks"] = ["re-sonance", "still-alive", "heal-you-again"]

    snapshot = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in snapshot.get("shortVideos", [])}
    shorts.update({item["videoId"]: short_record(item) for item in NEW_SHORTS})
    snapshot.update({
        "officialVideos": 61,
        "shorts": 41,
        "totalPublishedVideos": 102,
        "verifiedAt": NOW,
        "source": "公式YouTube Atomフィード・videos/shortsタブ・各動画のytInitialPlayerResponseを照合",
        "shortVideos": sorted(shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
        "scheduledVideos": [SCHEDULED_HELD],
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    new_release_evidence = evidence_record(
        NEW_RELEASE["slug"], NEW_RELEASE["youtubeId"],
        "【新章開幕】RE:VIVE『RE:SONANCE』｜星宮羽音 加入、新体制初の新曲｜MV近日解禁",
        NEW_RELEASE["releaseAt"], NEW_RELEASE["duration"],
    )
    records[(new_release_evidence["releaseSlug"], new_release_evidence["youtubeId"])] = new_release_evidence
    for item in UPDATED_VIDEOS:
        record = evidence_record(
            item["releaseSlug"],
            item["videoId"],
            item["title"],
            item["publishedAt"],
            item["duration"],
            source=item["verificationSource"],
        )
        records[(record["releaseSlug"], record["youtubeId"])] = record
    for item in NEW_SHORTS:
        record = evidence_record(
            item["relatedRelease"], item["videoId"], item["title"], item["publishedAt"], item["duration"],
            content_type="short",
        )
        records[(record["releaseSlug"], record["youtubeId"])] = record
    dates["checkedAt"] = NOW
    dates["records"] = sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    promoted = set(state.get("promoted", [])) | {NEW_RELEASE["slug"]}
    evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    for item in [
        {"slug": "re-sonance", "videoId": "EZp_Mtxt4G4", "releaseTimestamp": NEW_RELEASE["releaseAt"]},
        {"slug": "watashi-no-eranda-michi", "videoId": "FC1D7-0SeBc", "releaseTimestamp": "2026-08-23T20:00:06+09:00"},
        {"slug": "chimpanzee-no-rakuen", "videoId": "eSRxfGqzYOk", "releaseTimestamp": "2026-08-24T00:44:44+09:00"},
    ]:
        evidence[(item["slug"], item["videoId"])] = {
            **item,
            "availability": "public",
            "liveStatus": "was_live" if item["videoId"] == "FC1D7-0SeBc" else "not_live",
            "channelId": CHANNEL_ID,
        }
    state.update({
        "verifiedAt": NOW,
        "officialChannelId": CHANNEL_ID,
        "promoted": sorted(promoted),
        "evidence": sorted(evidence.values(), key=lambda item: (item["slug"], item["videoId"])),
        "upcomingHeld": [SCHEDULED_HELD],
    })
    write_json(STATE_PATH, state)

    snapshot_payload = {
        "schemaVersion": "1.2",
        "verifiedAt": NOW,
        "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィード、videos/shortsタブ、各動画のytInitialPlayerResponseを照合",
        "channelSnapshot": {"officialVideos": 61, "shorts": 41, "totalPublishedVideos": 102},
        "published": [NEW_RELEASE],
        "updatedVideos": [
            {**item, "status": "published", "playabilityStatus": "OK"} for item in UPDATED_VIDEOS
        ],
        "shorts": snapshot["shortVideos"],
        "upcomingHeld": [SCHEDULED_HELD],
    }
    write_json(SNAPSHOT_PATH, snapshot_payload)
    print(json.dumps({
        "publishedRelease": NEW_RELEASE["slug"],
        "updatedVideos": [item["releaseSlug"] for item in UPDATED_VIDEOS],
        "newShorts": [item["videoId"] for item in NEW_SHORTS],
        "upcomingHeld": SCHEDULED_HELD["videoId"],
        "releaseCount": len(cms["releases"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

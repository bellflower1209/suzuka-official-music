#!/usr/bin/env python3
"""Apply the confirmed title, artist-only credit, lyrics, MV and Short."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
SOURCES_PATH = ROOT / "assets/data/lyrics-sources.json"
LYRICS_PATH = ROOT / "assets/data/lyrics-masters/yume_to_kaigo_to_watashitachi_official_lyrics.txt"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260906.json"

SLUG = "yume-to-kaigo-to-watashitachi"
TITLE = "夢と、介護と、私たち。"
OLD_TITLE = "夢と、介護と、わたしたち。"
NOW = "2026-09-06T23:56:37+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"
MV = {
    "videoId": "giTYuKyIk3c",
    "title": "【MV】榎本魅愛「夢と、介護と、私たち。」｜介護職だって、夢を持っていい。",
    "sourceTitle": "【MV】榎本魅愛「夢と、介護と、わたしたち。」｜介護職だって、夢を持っていい。",
    "youtubeUrl": "https://www.youtube.com/watch?v=giTYuKyIk3c",
    "publishedAt": "2026-09-06T23:21:54+09:00",
    "duration": 315,
}
SHORT = {
    "videoId": "8Heg7Aomqwk",
    "title": "「介護職だって、夢を持っていい。」榎本魅愛『夢と、介護と、私たち。』#shorts",
    "sourceTitle": "「介護職だって、夢を持っていい。」榎本魅愛『夢と、介護と、わたしたち。』#shorts",
    "artist": "榎本魅愛",
    "artistSlug": "enomoto-mia",
    "youtubeUrl": "https://www.youtube.com/shorts/8Heg7Aomqwk",
    "publishedAt": "2026-09-06T23:43:52+09:00",
    "relatedRelease": SLUG,
    "thumbnail": "https://i.ytimg.com/vi/8Heg7Aomqwk/maxresdefault.jpg",
    "status": "published",
    "contentType": "short",
    "duration": 89,
    "description": "榎本魅愛「夢と、介護と、私たち。」Official Music Videoの公式Shorts。",
}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_title(value: object) -> object:
    if isinstance(value, str):
        return value.replace(OLD_TITLE, TITLE)
    if isinstance(value, list):
        return [replace_title(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_title(item) for key, item in value.items()}
    return value


def video_evidence(video: dict, content_type: str = "video") -> dict:
    return {
        "releaseSlug": SLUG,
        "youtubeId": video["videoId"],
        "youtubeUrl": video["youtubeUrl"],
        "catalogReleaseDate": video["publishedAt"][:10],
        "officialTitle": video.get("sourceTitle", video["title"]),
        "channelId": CHANNEL_ID,
        "channelVerified": True,
        "youtubePublishDate": video["publishedAt"],
        "youtubeUploadDate": video["publishedAt"],
        "liveStartTimestamp": "",
        "playabilityStatus": "OK",
        "durationSeconds": video["duration"],
        "verifiedPublishedAt": video["publishedAt"],
        "verificationSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "status": "verified-datetime",
        **({"contentType": "short"} if content_type == "short" else {}),
    }


def main() -> None:
    raw = LYRICS_PATH.read_bytes()
    source_text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    source_title, separator, lyrics = source_text.partition("\n")
    lyrics = lyrics.rstrip("\n")
    if not separator or source_title != TITLE or not lyrics.strip():
        raise SystemExit("Official lyric master title/body mismatch")

    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    releases = {item["slug"]: item for item in cms["releases"]}
    release = replace_title(releases[SLUG])
    release.update({
        "title": TITLE,
        "displayTitle": TITLE,
        "englishTitle": TITLE,
        "credits": {"artist": "榎本魅愛"},
        "lyricsAvailable": True,
        "lyricsSource": "ユーザー提供・SUZUKA公式歌詞正本（2026-09-06確定）",
        "lyricsText": lyrics,
        "lyricsVerified": True,
        "lyricsVerifiedAt": NOW,
        "youtubeUrl": MV["youtubeUrl"],
        "youtubeVideoTitle": MV["title"],
        "videoLabel": "OFFICIAL MV",
        "videoCtaLabel": "Official MVを見る",
        "videoButtonLabel": "WATCH MV",
        "videoPublishDate": MV["publishedAt"][:10],
        "videoPublishedAt": MV["publishedAt"],
        "videoPublishedAtSource": "official-youtube-atom-feed-and-playerMicroformatRenderer.publishDate",
        "duration": MV["duration"],
        "officialSource": MV["youtubeUrl"],
        "shortsUrl": SHORT["youtubeUrl"],
        "officialAudioUrl": "https://www.youtube.com/watch?v=PVX_5_MybgM",
        "officialAudioVideoId": "PVX_5_MybgM",
        "officialAudioPublishedAt": "2026-09-04T21:22:14+09:00",
        "officialAudioDuration": 315,
        "promotionVerifiedAt": NOW,
    })
    requested_keywords = [
        TITLE, "介護", "WITH", "WITH OUR DREAMS",
        "支える人も輝ける", "好きなことを好きなままで",
    ]
    release.pop("lyricist", None)
    release.pop("composer", None)
    release["tags"] = list(dict.fromkeys([
        TITLE if value == OLD_TITLE else value for value in release.get("tags", [])
        if value not in {"JUN", "SUNO"}
    ] + requested_keywords))
    release["searchKeywords"] = list(dict.fromkeys([
        TITLE if value == OLD_TITLE else value for value in release.get("searchKeywords", [])
        if value not in {"JUN", "SUNO"}
    ] + requested_keywords))
    hero = release.setdefault("homeHero", {})
    hero.update({
        "title": f'SUZUKA Official | 榎本魅愛「{TITLE}」公開中',
        "description": f'榎本魅愛「{TITLE}」公式MVと歌詞を公開中。介護の現場で働く人へ贈る応援歌です。',
        "subtitle": "ENOMOTO MIA · Official MV",
        "primaryLabel": "Official MVを見る",
        "lyricsLabel": "公式Lyrics",
    })
    releases[SLUG] = release
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True
    )
    cms["news"] = [
        replace_title(item) if item.get("releaseSlug") == SLUG else item
        for item in cms.get("news", [])
    ]
    cms["specialFeatures"] = [
        replace_title(item) if item.get("releaseSlug") == SLUG else item
        for item in cms.get("specialFeatures", [])
    ]
    for feature in cms.get("specialFeatures", []):
        if feature.get("releaseSlug") == SLUG:
            feature["keyPhrases"] = [
                "好きなことを　好きなままで",
                "誰かを支えるその手で\n自分の未来もつかんでいい",
                "支える人も　輝ける",
                "夢と介護は　つながってる",
            ]
    youtube = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in youtube.get("shortVideos", [])}
    shorts[SHORT["videoId"]] = SHORT
    youtube.update({
        "officialVideos": 71,
        "shorts": 47,
        "totalPublishedVideos": 118,
        "verifiedAt": NOW,
        "source": "公式YouTube Atomフィード・videos/shortsタブ・各動画の公開メタデータを照合",
        "shortVideos": sorted(
            shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True
        ),
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    records = {item.get("slug") or item.get("sourceKey"): item for item in sources.get("sources", [])}
    records[SLUG] = {
        "slug": SLUG,
        "title": TITLE,
        "sourceTitle": TITLE,
        "artist": "榎本魅愛",
        "filename": LYRICS_PATH.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "lyricsTextSha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
        "registrationStatus": "registered",
        "publishedAtImport": True,
        "holdReason": "",
    }
    sources.update({"verifiedAt": NOW, "sources": sorted(records.values(), key=lambda item: item.get("slug") or item["sourceKey"])})
    write_json(SOURCES_PATH, sources)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    date_records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for video, kind in ((MV, "video"), (SHORT, "short")):
        evidence = video_evidence(video, kind)
        date_records[(SLUG, evidence["youtubeId"])] = evidence
    dates.update({"checkedAt": NOW, "records": sorted(date_records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))})
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    evidence = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    evidence[(SLUG, MV["videoId"])] = {
        "slug": SLUG, "videoId": MV["videoId"], "releaseTimestamp": MV["publishedAt"],
        "availability": "public", "liveStatus": "not_live", "channelId": CHANNEL_ID,
    }
    state.update({
        "verifiedAt": NOW,
        "evidence": sorted(evidence.values(), key=lambda item: (item["slug"], item["videoId"])),
    })
    write_json(STATE_PATH, state)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2",
        "verifiedAt": NOW,
        "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube Atomフィードと各動画のplayerMicroformatRendererを照合",
        "channelSnapshot": {"officialVideos": 71, "shorts": 47, "totalPublishedVideos": 118},
        "published": [],
        "updatedReleaseVideos": [{"releaseSlug": SLUG, **MV}],
        "promotionalVideos": [],
        "shorts": [SHORT],
        "upcomingHeld": [],
    })
    print(json.dumps({
        "title": TITLE,
        "lyricsTextSha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
        "officialMv": MV["videoId"],
        "officialShort": SHORT["videoId"],
        "youtubeTotal": 118,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Register the verified Michiru release, official lyrics, MV and Short."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
DATES_PATH = ROOT / "assets/data/youtube-publish-dates.json"
STATE_PATH = ROOT / "assets/data/official-youtube-release-state.json"
SOURCES_PATH = ROOT / "assets/data/lyrics-sources.json"
LYRICS_PATH = ROOT / "assets/data/lyrics-masters/sedai-wo-koete-mama-e_official_lyrics.txt"
SNAPSHOT_PATH = ROOT / "assets/data/official-youtube-catalog-20260908.json"

SLUG = "sedai-wo-koete-mama-e"
TITLE = "世代を超えてママへ"
NOW = "2026-09-08T01:05:00+09:00"
CHANNEL_ID = "UCVde75yhByGQMu3SkO-fzrA"
MV = {
    "videoId": "Hho3xHOw8pg",
    "title": "【MV】世代を超えてママへ / 妃みちる｜誕生日に贈る、すべてのママへの歌",
    "youtubeUrl": "https://www.youtube.com/watch?v=Hho3xHOw8pg",
    "publishedAt": "2026-09-08T00:22:28+09:00",
    "duration": 178,
}
SHORT = {
    "videoId": "Fw-JEWaKwdM",
    "title": "今日、妃みちるは誕生日を迎えました。🎂｜『世代を超えてママへ』MV公開",
    "artist": "妃みちる",
    "artistSlug": "michiru",
    "youtubeUrl": "https://www.youtube.com/shorts/Fw-JEWaKwdM",
    "publishedAt": "2026-09-08T00:29:53+09:00",
    "relatedRelease": SLUG,
    "thumbnail": "https://i.ytimg.com/vi/Fw-JEWaKwdM/maxresdefault.jpg",
    "status": "published",
    "contentType": "short",
    "duration": 60,
    "description": "妃みちる「世代を超えてママへ」Official MV公開を伝える公式Shorts。",
}
SHORT_DESCRIPTION = "怒ってしまった夜も、眠れなかった朝も、すべては愛の中にある。妃みちるが、子育ての真ん中にいるママ、そして子育てを終えたすべてのママへ贈る楽曲。"
LONG_DESCRIPTION = """「世代を超えてママへ」は、子育ての中にある喜びだけではなく、怒ってしまった夜、涙を流した日、自分を責めてしまった瞬間までを描いた作品です。

朝の「おはよう」から始まる慌ただしい毎日。

散らかった部屋も、眠れない夜も、子どもと過ごした時間は、やがてかけがえのない記憶へ変わっていく。

今まさに子育てをしているママへ。

そして、かつて小さな手を握って歩いたママへ。

妃みちるが、世代を超えて「ありがとう」を届けます。"""
NEWS_TITLE = "妃みちる「世代を超えてママへ」公開──今を生きるママ、そしてすべての世代のママへ"
NEWS_DESCRIPTION = "妃みちるの新曲「世代を超えてママへ」を公開。今子育てをしている人、子育てを終えた人、家族を支えてきたすべてのママへ感謝を届けます。"
NEWS_PARAGRAPHS = [
    "妃みちるの新曲「世代を超えてママへ」を公開しました。",
    "朝から走り続ける日。思うようにいかず、怒ってしまった夜。子どもの寝顔を見ながら、自分を責めてしまった瞬間。",
    "子育てには、きれいな場面だけでは語れない毎日があります。",
    "それでも、いつかその時間は記憶になり、小さかった子どもは成長し、手を離れていきます。",
    "「世代を超えてママへ」は、今子育ての真ん中にいるママだけでなく、子育てを終えたママ、そして家族を支えてきたすべてのママへ届ける楽曲です。",
    "ママはすごい。その言葉を、当たり前にせず、ちゃんと声にして伝えるために。妃みちるが歌います。",
    "本作はママへの称賛とともに、家族や周囲が子育てを支えることの大切さも伝えています。",
]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def evidence(video: dict, content_type: str = "video") -> dict:
    result = {
        "releaseSlug": SLUG,
        "youtubeId": video["videoId"],
        "youtubeUrl": video["youtubeUrl"],
        "catalogReleaseDate": video["publishedAt"][:10],
        "officialTitle": video["title"],
        "channelId": CHANNEL_ID,
        "channelVerified": True,
        "youtubePublishDate": video["publishedAt"],
        "youtubeUploadDate": video["publishedAt"],
        "liveStartTimestamp": "",
        "playabilityStatus": "OK",
        "durationSeconds": video["duration"],
        "verifiedPublishedAt": video["publishedAt"],
        "verificationSource": "official-youtube-videos-or-shorts-tab-and-player-metadata",
        "status": "verified-datetime",
    }
    if content_type == "short":
        result["contentType"] = "short"
    return result


def main() -> None:
    raw = LYRICS_PATH.read_bytes()
    source = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    source_title, separator, lyrics = source.partition("\n")
    lyrics = lyrics.rstrip("\n\0")
    if not separator or source_title != TITLE or not lyrics.strip():
        raise SystemExit("Official lyric master title/body mismatch")

    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    artists = {item["slug"]: item for item in cms["artists"]}
    artist = artists["michiru"]
    artist["artistFeaturedTracks"] = [SLUG, *[slug for slug in artist.get("artistFeaturedTracks", []) if slug != SLUG]][:3]
    artist["music"] = "最新曲「世代を超えてママへ」をはじめ、人生、家族、恋や友情の物語を届ける。"
    cms["artists"] = sorted(artists.values(), key=lambda item: item["slug"])

    tags = [
        TITLE, "妃みちる", "ママ", "母", "子育て", "家族", "応援歌", "ありがとうママ",
        "J-POP", "感謝", "人生", "親子", "育児",
    ]
    release = {
        "slug": SLUG, "id": SLUG, "title": TITLE, "displayTitle": TITLE, "englishTitle": TITLE,
        "artist": "妃みちる", "artistSlug": "michiru", "artistSlugs": ["michiru"], "artistType": "Person",
        "releaseAt": MV["publishedAt"], "publishedAt": MV["publishedAt"], "releaseDate": "2026-09-08",
        "releaseYear": 2026, "releaseType": "single", "genres": ["J-POP", "応援歌"],
        "moods": ["温かい"], "themes": ["家族", "感謝", "人生"], "tags": tags, "language": "ja",
        "coverImage": "https://i.ytimg.com/vi/Hho3xHOw8pg/maxresdefault.jpg",
        "coverAlt": "妃みちる「世代を超えてママへ」公式YouTube MVサムネイル",
        "youtubeUrl": MV["youtubeUrl"], "youtubeVideoTitle": MV["title"], "videoLabel": "OFFICIAL MV",
        "videoCtaLabel": "Official MVを見る", "videoButtonLabel": "WATCH MV", "shortsUrl": SHORT["youtubeUrl"],
        "releaseUrl": f"releases/{SLUG}/", "newsUrl": f"news/{SLUG}-release/", "duration": MV["duration"],
        "status": "published", "featured": True, "recommendationWeight": 5, "weeklyPickEligible": True,
        "analyticsEnabled": True, "upcomingPriority": 0, "relatedReleases": [], "searchKeywords": tags,
        "aiArtistType": "fictional AI artist", "description": SHORT_DESCRIPTION, "introduction": LONG_DESCRIPTION,
        "galleryImages": [], "galleryPublished": False, "productionNote": SHORT_DESCRIPTION,
        "seo": {
            "title": f"{TITLE} | 妃みちる | SUZUKA Official",
            "description": f"妃みちる「{TITLE}」。子育ての喜びも、怒ってしまった夜も、涙の日も抱きしめながら、今を生きるママとすべての世代のママへ届ける楽曲。",
            "jsonLdEnabled": True,
        },
        "videoPublishDate": "2026-09-08", "videoPublishedAt": MV["publishedAt"],
        "videoPublishedAtSource": "official-youtube-videos-tab-and-player-metadata",
        "videoStructuredDataStatus": "published", "officialSource": MV["youtubeUrl"], "promotionVerifiedAt": NOW,
        "lyricsAvailable": True,
        "lyricsSource": "ユーザー提供・SUZUKA公式歌詞正本（2026-09-08確定）",
        "lyricsText": lyrics, "lyricsVerified": True, "lyricsVerifiedAt": NOW,
        "newsTitle": NEWS_TITLE, "newsDescription": NEWS_DESCRIPTION, "newsBodyParagraphs": NEWS_PARAGRAPHS,
        "homeHero": {
            "title": f"SUZUKA Official | 妃みちる「{TITLE}」公開中",
            "description": f"妃みちるの最新曲「{TITLE}」を公開中。Official MV・作品情報・公式歌詞はこちら。",
            "subtitle": "MICHIRO / 妃みちる", "status": "NEW RELEASE",
            "lead": "すべてのママへ。\nそして、いつかママだったあなたへ。",
            "projectLabel": "SUZUKA Official · Original AI Music Project",
            "primaryLabel": "MVを見る", "secondaryLabel": "作品を見る", "lyricsLabel": "歌詞を読む",
        },
    }
    releases = {item["slug"]: item for item in cms["releases"]}
    releases[SLUG] = release
    cms["releases"] = sorted(releases.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    news = {item["slug"]: item for item in cms.get("news", [])}
    news[f"{SLUG}-release"] = {
        "slug": f"{SLUG}-release", "title": NEWS_TITLE, "artistSlug": "michiru", "releaseSlug": SLUG,
        "publishedAt": MV["publishedAt"], "description": NEWS_DESCRIPTION,
        "image": release["coverImage"], "status": "published",
    }
    cms["news"] = sorted(news.values(), key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)

    youtube = cms.setdefault("youtubeSnapshot", {})
    shorts = {item["videoId"]: item for item in youtube.get("shortVideos", [])}
    shorts[SHORT["videoId"]] = SHORT
    youtube.update({
        "officialVideos": 72, "shorts": 48, "totalPublishedVideos": 120, "verifiedAt": NOW,
        "source": "公式YouTube videos/shortsタブ・各動画の公開メタデータを照合",
        "shortVideos": sorted(shorts.values(), key=lambda item: (item["publishedAt"], item["videoId"]), reverse=True),
    })
    cms["updatedAt"] = NOW
    write_json(CMS_PATH, cms)

    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    source_records = {item.get("slug") or item.get("sourceKey"): item for item in sources.get("sources", [])}
    source_records[SLUG] = {
        "slug": SLUG, "title": TITLE, "sourceTitle": TITLE, "artist": "妃みちる",
        "filename": LYRICS_PATH.name, "sha256": hashlib.sha256(raw).hexdigest(),
        "lyricsTextSha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
        "registrationStatus": "registered", "publishedAtImport": True, "holdReason": "",
    }
    sources.update({"verifiedAt": NOW, "sources": sorted(source_records.values(), key=lambda item: item.get("slug") or item["sourceKey"])})
    write_json(SOURCES_PATH, sources)

    dates = json.loads(DATES_PATH.read_text(encoding="utf-8"))
    records = {(item["releaseSlug"], item.get("youtubeId", "")): item for item in dates["records"]}
    for video, kind in ((MV, "video"), (SHORT, "short")):
        row = evidence(video, kind)
        records[(SLUG, row["youtubeId"])] = row
    dates.update({"checkedAt": NOW, "records": sorted(records.values(), key=lambda item: (item["releaseSlug"], item.get("youtubeId", "")))})
    write_json(DATES_PATH, dates)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state_rows = {(item["slug"], item["videoId"]): item for item in state.get("evidence", [])}
    state_rows[(SLUG, MV["videoId"])] = {
        "slug": SLUG, "videoId": MV["videoId"], "releaseTimestamp": MV["publishedAt"],
        "availability": "public", "liveStatus": "not_live", "channelId": CHANNEL_ID,
    }
    state.update({"verifiedAt": NOW, "evidence": sorted(state_rows.values(), key=lambda item: (item["slug"], item["videoId"]))})
    write_json(STATE_PATH, state)

    write_json(SNAPSHOT_PATH, {
        "schemaVersion": "1.2", "verifiedAt": NOW, "officialChannelId": CHANNEL_ID,
        "channelUrl": "https://www.youtube.com/@suzuka1209",
        "verificationMethod": "公式YouTube videos/shortsタブと各動画の公開メタデータを照合",
        "channelSnapshot": {"officialVideos": 72, "shorts": 48, "totalPublishedVideos": 120},
        "published": [{"releaseSlug": SLUG, **MV}], "updatedReleaseVideos": [],
        "promotionalVideos": [], "shorts": [SHORT], "upcomingHeld": [],
    })
    print(json.dumps({
        "slug": SLUG, "lyricsTextSha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
        "officialMv": MV["videoId"], "officialShort": SHORT["videoId"], "youtubeTotal": 120,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

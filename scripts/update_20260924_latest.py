#!/usr/bin/env python3
"""Apply the 2026-09-24 TuneCore / Instagram / note verification snapshot."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CMS_PATH = ROOT / "assets/data/creator-cms.json"
PHOTOBOOKS_PATH = ROOT / "assets/data/photobooks.json"
TUNECORE_PATH = ROOT / "assets/data/tunecore-catalog-20260924.json"
NOW = datetime.now(ZoneInfo("Asia/Tokyo")).replace(microsecond=0).isoformat()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def streaming(date: str, url: str, status: str) -> dict:
    value = {
        "releaseDate": date,
        "timezone": "Asia/Tokyo",
        "status": status,
        "linkcoreUrl": url,
        "source": "authenticated-tunecore-dashboard-and-public-linkcore",
        "verifiedAt": NOW,
        "verificationSource": "tunecore-dashboard-status-and-official-linkcore-release-date",
    }
    return value


def distribution_release(
    *, slug: str, title: str, release_type: str, linkcore: str, cover: str,
    description: str, keywords: list[str], duration: int = 0,
) -> dict:
    return {
        "id": slug,
        "slug": slug,
        "title": title,
        "displayTitle": title,
        "englishTitle": title,
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "artistSlugs": ["enomoto-mia"],
        "artistType": "Person",
        "releaseAt": "2026-09-23T00:00:00+09:00",
        "publishedAt": "2026-09-23T00:00:00+09:00",
        "releaseDate": "2026-09-23",
        "releaseYear": 2026,
        "releaseType": release_type,
        "genres": ["J-POP"],
        "moods": [],
        "themes": ["恋愛"],
        "tags": keywords,
        "language": "ja",
        "coverImage": cover,
        "coverAlt": f'榎本魅愛「{title}」TuneCore公式ジャケット',
        "coverWidth": 400,
        "coverHeight": 400,
        "youtubeUrl": "",
        "releaseUrl": f"releases/{slug}/",
        "newsUrl": "",
        "duration": duration,
        "status": "published",
        "featured": False,
        "recommendationWeight": 1,
        "weeklyPickEligible": False,
        "analyticsEnabled": True,
        "upcomingPriority": 0,
        "relatedReleases": [],
        "searchKeywords": ["榎本魅愛", "ENOMOTO MIA", title, "TuneCore", "LinkCore", "2026-09-23", *keywords],
        "aiArtistType": "fictional AI artist",
        "description": description,
        "introduction": description,
        "galleryImages": [],
        "galleryPublished": False,
        "productionNote": description,
        "seo": {
            "title": f"{title}｜榎本魅愛｜SUZUKA Official Music",
            "description": description,
            "jsonLdEnabled": True,
        },
        "videoStructuredDataStatus": "unavailable",
        "officialSource": linkcore,
        "promotionVerifiedAt": NOW,
        "lyricsAvailable": False,
        "lyricsSource": "",
        "lyricsText": "",
        "lyricsVerified": False,
        "lyricsVerifiedAt": None,
        "scheduledStreamingRelease": streaming("2026-09-23", linkcore, "published"),
    }


def upcoming(
    *, slug: str, title: str, artist: str, artist_slug: str, date: str,
    linkcore: str, image: str,
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "artist": artist,
        "artistSlug": artist_slug,
        "scheduledAt": f"{date}T00:00:00+09:00",
        "releaseDate": date,
        "status": "upcoming",
        "source": "authenticated-tunecore-dashboard-and-public-linkcore",
        "linkcoreUrl": linkcore,
        "verifiedAt": NOW,
        "verificationSource": "tunecore-dashboard-scheduled-status-and-official-linkcore-release-date",
        "description": f'{artist}「{title}」は{date}ストリーミング配信予定です。',
        "searchKeywords": [artist, title, "TuneCore", "LinkCore", "配信予定", date],
        "image": image,
        "imageAlt": f'{artist}「{title}」TuneCore公式ジャケット',
        "imageWidth": 400,
        "imageHeight": 400,
        "imageSource": linkcore,
    }


def upsert_by_slug(values: list[dict], record: dict) -> None:
    for index, value in enumerate(values):
        if value.get("slug") == record["slug"]:
            values[index] = record
            return
    values.append(record)


def main() -> None:
    cms = json.loads(CMS_PATH.read_text(encoding="utf-8"))
    cms["updatedAt"] = NOW

    releases = {item["slug"]: item for item in cms["releases"]}
    releases["natsu-ga-owaru-made-soba-ni-ite"]["scheduledStreamingRelease"] = streaming(
        "2026-09-23", "https://linkco.re/EQtNSDgr", "published"
    )
    releases["caramel"]["scheduledStreamingRelease"] = streaming(
        "2026-09-23", "https://linkco.re/GVzS1dUY", "published"
    )
    releases["taipa-nante-shiranakatta"]["scheduledStreamingRelease"] = streaming(
        "2026-09-23", "https://linkco.re/uYYFxG62", "published"
    )
    releases["toriatsukai-chui"]["scheduledStreamingRelease"] = streaming(
        "2026-09-21", "https://linkco.re/9r6szVDg", "published"
    )
    releases["kimi-to-nara-last-boss-made"]["scheduledStreamingRelease"] = streaming(
        "2026-10-01", "https://linkco.re/0X3neT7N", "upcoming"
    )
    releases["sedai-wo-koete-mama-e"]["scheduledStreamingRelease"] = streaming(
        "2026-10-02", "https://linkco.re/u07vdbbg", "upcoming"
    )
    releases["mahou-ga-toketemo"]["scheduledStreamingRelease"] = streaming(
        "2026-10-03", "https://linkco.re/tSpMyUFE", "upcoming"
    )

    mata = distribution_release(
        slug="mata-kimi-ni-koi-wo-suru",
        title="また、君に恋をする。",
        release_type="single",
        linkcore="https://linkco.re/5acNsXS6",
        cover="images/enomoto-mia-mata-kimi-ni-koi-wo-suru.png",
        description="榎本魅愛「また、君に恋をする。」は2026年9月23日にストリーミング配信を開始しました。",
        keywords=["また君に恋をする", "I Fall in Love With You Again"],
    )
    album = distribution_release(
        slug="koisuru-subete-no-shunkan",
        title="恋するすべての瞬間",
        release_type="album",
        linkcore="https://linkco.re/rGeEn03r",
        cover="images/enomoto-mia-koisuru-subete-no-shunkan.png",
        description="榎本魅愛の5曲入りアルバム「恋するすべての瞬間」は2026年9月23日にストリーミング配信を開始しました。収録曲は「Over Drive」「キャラメ〜ル」「取り扱いチューい」「百万告」「花言葉」です。",
        keywords=["アルバム", "All the Moments We Fall in Love", "Over Drive", "キャラメ〜ル", "取り扱いチューい", "百万告", "花言葉"],
    )
    releases[mata["slug"]] = mata
    releases[album["slug"]] = album
    cms["releases"] = sorted(
        releases.values(), key=lambda item: (item.get("publishedAt") or item["releaseDate"], item["slug"]), reverse=True
    )

    cms["upcoming"] = sorted([
        upcoming(
            slug="eternity-of-flower-words", title="Eternity of Flower Words", artist="榎本魅愛",
            artist_slug="enomoto-mia", date="2026-09-26", linkcore="https://linkco.re/r01YHhrv",
            image="images/enomoto-mia-eternity-of-flower-words.png",
        ),
        upcoming(
            slug="renai-taishogai-kari", title="恋愛対象外 (仮)", artist="榎本魅愛",
            artist_slug="enomoto-mia", date="2026-09-26", linkcore="https://linkco.re/TYNMGrUr",
            image="images/enomoto-mia-renai-taishogai-kari.png",
        ),
        upcoming(
            slug="nando-umarekawattemo-reborn-oath", title="何度生まれ変わっても - RE:BORN OATH -", artist="神代煌牙",
            artist_slug="koga-kamishiro", date="2026-09-26", linkcore="https://linkco.re/00FG1Rd6",
            image="images/koga-nando-umarekawattemo-reborn-oath.png",
        ),
        upcoming(
            slug="kokoro-ni-nokoru-takaramono", title="心に残る宝モノ", artist="妃みちる",
            artist_slug="michiru", date="2026-09-29", linkcore="https://linkco.re/C7nAndeS",
            image="images/michiru-kokoro-ni-nokoru-takaramono.png",
        ),
    ], key=lambda item: (item["scheduledAt"], item["slug"]))

    michiru = next(item for item in cms["artists"] if item["slug"] == "michiru")
    michiru["instagramUrl"] = "https://www.instagram.com/suzuka12090511/"
    michiru["officialNoteUrl"] = "https://note.com/1209bellflower/n/nce756dc6090e"

    activities = [
        {"date": "2026-09-11", "title": "花言葉", "kind": "NOW STREAMING", "url": "releases/hanakotoba/", "status": "published"},
        {"date": "2026-09-18", "title": "花言葉", "kind": "KARAOKE / JOYSOUND", "url": "news/hanakotoba-joysound-karaoke/"},
        {"date": "2026-09-21", "title": "百万告", "kind": "STREAMING RELEASE", "url": "releases/hyakumankoku/", "officialReleaseDate": "2026-07-12", "status": "published"},
        {"date": "2026-09-21", "title": "Hello Hello Halloween", "kind": "STREAMING RELEASE", "url": "releases/hello-hello-halloween/", "officialReleaseDate": "2026-09-16", "status": "published"},
        {"date": "2026-09-21", "title": "取り扱いチュー💋い", "kind": "STREAMING RELEASE", "url": "releases/toriatsukai-chui/", "officialReleaseDate": "2026-07-14", "status": "published"},
        {"date": "2026-09-22", "title": "September Blue", "kind": "NEW RELEASE", "url": "releases/september-blue/", "status": "published"},
        {"date": "2026-09-22", "title": "Over Drive", "kind": "NEW RELEASE", "url": "releases/over-drive/", "status": "published"},
        {"date": "2026-09-23", "title": "恋するすべての瞬間", "kind": "ALBUM RELEASE", "url": "releases/koisuru-subete-no-shunkan/", "status": "published"},
        {"date": "2026-09-23", "title": "また、君に恋をする。", "kind": "NEW RELEASE", "url": "releases/mata-kimi-ni-koi-wo-suru/", "status": "published"},
        {"date": "2026-09-23", "title": "夏が終わるまで、そばにいて。", "kind": "STREAMING RELEASE", "url": "releases/natsu-ga-owaru-made-soba-ni-ite/", "officialReleaseDate": "2026-08-14", "status": "published"},
        {"date": "2026-09-23", "title": "キャラメ〜ル", "kind": "STREAMING RELEASE", "url": "releases/caramel/", "officialReleaseDate": "2026-08-13", "status": "published"},
        {"date": "2026-09-23", "title": "タイパなんて知らなかった", "kind": "STREAMING RELEASE", "url": "releases/taipa-nante-shiranakatta/", "officialReleaseDate": "2026-08-16", "status": "published"},
        {"date": "2026-09-26", "title": "Eternity of Flower Words", "kind": "NEW RELEASE", "url": "releases/eternity-of-flower-words/", "status": "upcoming"},
        {"date": "2026-09-26", "title": "恋愛対象外 (仮)", "kind": "NEW RELEASE", "url": "releases/renai-taishogai-kari/", "status": "upcoming"},
    ]
    cms["miaReleaseSchedule"]["activities"] = activities

    news = cms["news"]
    news_records = [
        {
            "slug": "michiru-arinomama-photobook",
            "title": "妃みちる 1st Digital Photo Book『ありのまま。 — Just As I Am. —』公開",
            "artistSlug": "michiru",
            "publishedAt": "2026-09-24T00:33:51+09:00",
            "description": "妃みちるの1st Digital Photo Book『ありのまま。 — Just As I Am. —』がnoteで公開されました。",
            "image": "images/michiru-arinomama-note.png",
            "noteUrl": "https://note.com/1209bellflower/n/n599c9798e768",
            "instagramUrl": "https://www.instagram.com/p/DdoqSqJCY-0/",
            "photobookSlug": "michiru-arinomama-just-as-i-am",
            "status": "published",
            "searchKeywords": ["妃みちる", "ありのまま", "Just As I Am", "Digital Photo Book", "note"],
        },
        {
            "slug": "michiru-official-channel-open",
            "title": "妃みちる Official Channelオープン",
            "artistSlug": "michiru",
            "publishedAt": "2026-09-21T01:19:19+09:00",
            "description": "妃みちるの音楽を届けるYouTube「妃みちる Official Channel」のオープンがnoteで公式発表されました。チャンネルの直接URLは確認できた時点で追加します。",
            "image": "images/michiru-official-channel-note.jpg",
            "noteUrl": "https://note.com/1209bellflower/n/nce756dc6090e",
            "status": "published",
            "searchKeywords": ["妃みちる", "Official Channel", "YouTube", "note"],
        },
        {
            "slug": "enomoto-mia-three-streaming-releases",
            "title": "榎本魅愛「百万告」「取り扱いチューい」「Hello Hello Halloween」3曲同時リリース",
            "artistSlug": "enomoto-mia",
            "publishedAt": "2026-09-21T01:16:08+09:00",
            "description": "榎本魅愛の「百万告」「取り扱いチューい」「Hello Hello Halloween」が2026年9月21日に各音楽配信サービスで配信開始されました。",
            "image": "images/enomoto-mia-three-streaming-note.jpg",
            "noteUrl": "https://note.com/1209bellflower/n/n203229d0d986",
            "instagramUrl": "https://www.instagram.com/p/Ddg9cUvpq-J/",
            "status": "published",
            "searchKeywords": ["榎本魅愛", "百万告", "取り扱いチューい", "Hello Hello Halloween", "Streaming Release"],
        },
        {
            "slug": "koisuru-subete-no-shunkan-streaming-release",
            "title": "榎本魅愛「恋するすべての瞬間」アルバム配信開始",
            "artistSlug": "enomoto-mia",
            "publishedAt": "2026-09-23T00:00:00+09:00",
            "description": "榎本魅愛の5曲入りアルバム「恋するすべての瞬間」が2026年9月23日にストリーミング配信を開始しました。",
            "image": album["coverImage"],
            "linkcoreUrl": "https://linkco.re/rGeEn03r",
            "relatedReleaseUrl": album["releaseUrl"],
            "status": "published",
            "searchKeywords": ["榎本魅愛", "恋するすべての瞬間", "アルバム", "TuneCore", "LinkCore"],
        },
        {
            "slug": "mata-kimi-ni-koi-wo-suru-streaming-release",
            "title": "榎本魅愛「また、君に恋をする。」配信開始",
            "artistSlug": "enomoto-mia",
            "publishedAt": "2026-09-23T00:00:00+09:00",
            "description": "榎本魅愛「また、君に恋をする。」が2026年9月23日にストリーミング配信を開始しました。",
            "image": mata["coverImage"],
            "linkcoreUrl": "https://linkco.re/5acNsXS6",
            "relatedReleaseUrl": mata["releaseUrl"],
            "status": "published",
            "searchKeywords": ["榎本魅愛", "また君に恋をする", "TuneCore", "LinkCore"],
        },
    ]
    for record in news_records:
        upsert_by_slug(news, record)
    for slug, instagram_url in {
        "friendlikesong-streaming-release": "https://www.instagram.com/p/Dddw4lapFDE/",
        "tatta-hitori-no-kimi-e-streaming-release": "https://www.instagram.com/p/Dddw4lapFDE/",
    }.items():
        item = next((value for value in news if value.get("slug") == slug), None)
        if item:
            item["instagramUrl"] = instagram_url
    cms["news"] = sorted(news, key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)
    write_json(CMS_PATH, cms)

    photobooks = json.loads(PHOTOBOOKS_PATH.read_text(encoding="utf-8"))
    upsert_by_slug(photobooks["photobooks"], {
        "id": "michiru-arinomama-just-as-i-am",
        "slug": "michiru-arinomama-just-as-i-am",
        "title": "妃みちる 1st Digital Photo Book『ありのまま。 — Just As I Am. —』",
        "artistSlug": "michiru",
        "coverImage": "images/michiru-arinomama-note.png",
        "coverAlt": "妃みちる 1st Digital Photo Book『ありのまま。 — Just As I Am. —』公式表紙",
        "coverWidth": 1672,
        "coverHeight": 875,
        "noteUrl": "https://note.com/1209bellflower/n/n599c9798e768",
        "instagramUrl": "https://www.instagram.com/p/DdoqSqJCY-0/",
        "publishedAt": "2026-09-24T00:33:51+09:00",
        "status": "published",
        "description": "日常の中にある小さな幸せを描く、妃みちるの1st Digital Photo Book。note公式記事で50カットを収録。",
        "relatedReleaseSlugs": [],
        "featured": True,
        "isPaid": True,
        "priceLabel": "¥300",
        "contentType": "Digital Photo Book",
        "sourceVerifiedAt": NOW,
    })
    photobooks["updatedAt"] = NOW
    photobooks["photobooks"].sort(key=lambda item: (item.get("publishedAt", ""), item["slug"]), reverse=True)
    write_json(PHOTOBOOKS_PATH, photobooks)

    tunecore = {
        "schemaVersion": "1.0",
        "verifiedAt": NOW,
        "timezone": "Asia/Tokyo",
        "source": "authenticated TuneCore Japan dashboard plus public LinkCore pages",
        "summary": {"total": 21, "published": 13, "scheduled": 7, "underReview": 1},
        "releases": [
            {"releaseId":"1972974","title":"夢と、介護と、わたしたち","artist":"榎本魅愛","type":"single","status":"under-review","dashboardLabel":"審査中","releaseDate":None,"linkcoreUrl":None},
            {"releaseId":"1970337","title":"世代を超えてママへ","artist":"妃みちる","type":"single","status":"scheduled","dashboardLabel":"配信中 / 10/02 リリース予定","releaseDate":"2026-10-02","linkcoreUrl":"https://linkco.re/u07vdbbg"},
            {"releaseId":"1957717","title":"夏が終わるまで、そばにいて。","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-14","releaseDate":"2026-09-23","linkcoreUrl":"https://linkco.re/EQtNSDgr"},
            {"releaseId":"1957206","title":"恋するすべての瞬間","artist":"榎本魅愛","type":"album","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-14","releaseDate":"2026-09-23","linkcoreUrl":"https://linkco.re/rGeEn03r","tracks":["Over Drive","キャラメ〜ル","取り扱いチューい","百万告","花言葉"]},
            {"releaseId":"1957176","title":"キャラメ〜ル","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-14","releaseDate":"2026-09-23","linkcoreUrl":"https://linkco.re/GVzS1dUY"},
            {"releaseId":"1957040","title":"タイパなんて知らなかった。","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-14","releaseDate":"2026-09-23","linkcoreUrl":"https://linkco.re/uYYFxG62"},
            {"releaseId":"1956870","title":"また、君に恋をする。","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-14","releaseDate":"2026-09-23","linkcoreUrl":"https://linkco.re/5acNsXS6"},
            {"releaseId":"1969247","title":"君とならラスボスまで","artist":"榎本魅愛","type":"single","status":"scheduled","dashboardLabel":"配信中 / 10/01 リリース予定","releaseDate":"2026-10-01","linkcoreUrl":"https://linkco.re/0X3neT7N"},
            {"releaseId":"1969058","title":"何度生まれ変わっても - RE:BORN OATH -","artist":"神代煌牙","type":"single","status":"scheduled","dashboardLabel":"配信中 / 09/26 リリース予定","releaseDate":"2026-09-26","linkcoreUrl":"https://linkco.re/00FG1Rd6"},
            {"releaseId":"1969089","title":"心に残る宝モノ","artist":"妃みちる","type":"single","status":"scheduled","dashboardLabel":"配信中 / 09/29 リリース予定","releaseDate":"2026-09-29","linkcoreUrl":"https://linkco.re/C7nAndeS"},
            {"releaseId":"1963735","title":"魔法が解けても ― Pumpkin Carriage ―","artist":"神代煌牙","type":"single","status":"scheduled","dashboardLabel":"配信中 / 10/03 リリース予定","releaseDate":"2026-10-03","linkcoreUrl":"https://linkco.re/tSpMyUFE"},
            {"releaseId":"1955863","title":"Over Drive","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-22","linkcoreUrl":"https://linkco.re/3tHVbvXs"},
            {"releaseId":"1955123","title":"September Blue","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-22","linkcoreUrl":"https://linkco.re/HCvApf7V"},
            {"releaseId":"1954742","title":"取り扱いチューい","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-21","linkcoreUrl":"https://linkco.re/9r6szVDg"},
            {"releaseId":"1954597","title":"百万告","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-21","linkcoreUrl":"https://linkco.re/Qd5Tzb0q"},
            {"releaseId":"1954551","title":"Hello Hello Halloween","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-21","linkcoreUrl":"https://linkco.re/QfzZUy6f"},
            {"releaseId":"1963697","title":"たった1人の君へ","artist":"妃みちる","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-20","linkcoreUrl":"https://linkco.re/3Z3vDYPG"},
            {"releaseId":"1963488","title":"friend like song","artist":"妃みちる","type":"single","status":"published","dashboardLabel":"配信中","releaseDate":"2026-09-20","linkcoreUrl":"https://linkco.re/QFNB1r1u"},
            {"releaseId":"1960949","title":"恋愛対象外 (仮)","artist":"榎本魅愛","type":"single","status":"scheduled","dashboardLabel":"配信中 / 09/26 リリース予定","releaseDate":"2026-09-26","linkcoreUrl":"https://linkco.re/TYNMGrUr"},
            {"releaseId":"1960708","title":"Eternity of Flower Words","artist":"榎本魅愛","type":"single","status":"scheduled","dashboardLabel":"配信中 / 09/26 リリース予定","releaseDate":"2026-09-26","linkcoreUrl":"https://linkco.re/r01YHhrv"},
            {"releaseId":"1951259","title":"花言葉","artist":"榎本魅愛","type":"single","status":"published","dashboardLabel":"配信中","dashboardDistributionPeriodStart":"2026-09-10","releaseDate":"2026-09-11","linkcoreUrl":"https://linkco.re/0xHr8N9e"},
        ],
        "notes": [
            "TuneCore管理画面の配信期間開始日とLinkCoreの公開リリース日が異なる場合は、別フィールドとして保存した。",
            "『夢と、介護と、わたしたち』は審査中のため、配信予定として公開サイトには掲載しない。",
        ],
    }
    write_json(TUNECORE_PATH, tunecore)
    print(json.dumps({
        "updatedAt": NOW,
        "releases": len(cms["releases"]),
        "upcoming": len(cms["upcoming"]),
        "news": len(cms["news"]),
        "photobooks": len(photobooks["photobooks"]),
        "tunecore": tunecore["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

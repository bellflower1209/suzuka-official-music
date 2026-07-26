#!/usr/bin/env python3
"""Generate the verified 2026-07-26 SUZUKA publication state."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BASE = "https://bellflower1209.github.io/suzuka-official-music"
CHANNEL = "https://www.youtube.com/@suzuka1209"
INSTAGRAM = "https://www.instagram.com/suzuka12090511/"
RELEASES = [
    {
        "slug": "namaste-galaxy",
        "title": "NAMASTE☆GALAXY",
        "artist": "RANGILI",
        "artistSlug": "rangili",
        "date": "2026-07-24",
        "youtube": "https://www.youtube.com/watch?v=CQ0bfdXVrck",
        "videoId": "CQ0bfdXVrck",
        "duration": 163,
        "image": "images/rangili-namaste-galaxy.jpg",
        "width": 1254,
        "height": 1254,
        "alt": "RANGILI「NAMASTE☆GALAXY」公式ジャケット",
        "description": "インドの情熱と日本のメロディが響き合う、RANGILIの公式デビュー作品。",
        "genres": ["J-POP", "Indian Pop", "Dance Pop"],
        "news": "news/namaste-galaxy-release/",
    },
    {
        "slug": "wasurenai-kokoro",
        "title": "忘れない心",
        "artist": "朝霧しのぶ",
        "artistSlug": "asagiri-shinobu",
        "date": "2026-07-23",
        "youtube": "https://www.youtube.com/watch?v=YxZWABTJBGk",
        "videoId": "YxZWABTJBGk",
        "duration": 311,
        "image": "images/asagiri-wasurenai-kokoro.jpg",
        "width": 1254,
        "height": 1254,
        "alt": "朝霧しのぶ「忘れない心」公式ジャケット",
        "description": "認知症、家族、記憶、人生をテーマに、忘れても残る愛を歌う朝霧しのぶの演歌作品。",
        "genres": ["演歌"],
        "news": "news/wasurenai-kokoro-release/",
    },
    {
        "slug": "smile-and-say-goodbye",
        "title": "SMILE AND SAY GOODBYE ― 大好きだから、笑ってさようなら。―",
        "cardTitle": "SMILE AND SAY GOODBYE",
        "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia",
        "date": "2026-07-22",
        "youtube": "https://www.youtube.com/watch?v=b2n8gcpen58",
        "videoId": "b2n8gcpen58",
        "duration": 497,
        "image": "images/mv-smile-and-say-goodbye.png",
        "width": 1672,
        "height": 941,
        "alt": "榎本魅愛「SMILE AND SAY GOODBYE ― 大好きだから、笑ってさようなら。―」公式ジャケット",
        "description": "好きだからこそ相手を手放し、最後は笑顔で別れたいと願う切ないバラード。",
        "genres": ["J-POP", "Romantic Pop", "Ballad"],
        "news": "news/smile-and-say-goodbye-release/",
    },
]


def compact(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8")


def stylesheet(source: str, href: str) -> str:
    link = f'<link rel="stylesheet" href="{href}"/>'
    return source if link in source else source.replace("</head>", link + "</head>", 1)


def replace_section(source: str, start: str, next_start: str, replacement: str) -> str:
    pattern = re.compile(rf'<section class="{re.escape(start)}".*?(?=<section class="{re.escape(next_start)}")', re.DOTALL)
    updated, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError(f"Section not found: {start}")
    return updated


def jsonld_release(item: dict) -> dict:
    url = f"{BASE}/releases/{item['slug']}/"
    artist_url = f"{BASE}/artists/{item['artistSlug']}/"
    image = f"{BASE}/{item['image']}"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": f"{item['title']}｜{item['artist']}｜SUZUKA",
                "description": item["description"],
                "mainEntity": {"@id": f"{url}#recording"},
                "breadcrumb": {"@id": f"{url}#breadcrumb"},
                "primaryImageOfPage": {"@type": "ImageObject", "url": image},
                "inLanguage": "ja",
            },
            {
                "@type": "MusicRecording",
                "@id": f"{url}#recording",
                "name": item["title"],
                "url": url,
                "image": image,
                "datePublished": item["date"],
                "duration": f"PT{item['duration'] // 60}M{item['duration'] % 60}S",
                "genre": item["genres"],
                "description": item["description"],
                "byArtist": {
                    "@type": "MusicGroup" if item["artist"] == "RANGILI" else "Person",
                    "name": item["artist"],
                    "url": artist_url,
                },
                "mainEntityOfPage": {"@id": url},
                "subjectOf": {"@id": f"{url}#video"},
            },
            {
                "@type": "VideoObject",
                "@id": f"{url}#video",
                "name": f"{item['title']}｜{item['artist']} Official Music Video",
                "description": item["description"],
                "thumbnailUrl": f"https://i.ytimg.com/vi/{item['videoId']}/maxresdefault.jpg",
                "uploadDate": item["date"],
                "duration": f"PT{item['duration'] // 60}M{item['duration'] % 60}S",
                "embedUrl": f"https://www.youtube.com/embed/{item['videoId']}",
                "contentUrl": item["youtube"],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Releases", "item": f"{BASE}/releases/"},
                    {"@type": "ListItem", "position": 3, "name": item["cardTitle"] if item.get("cardTitle") else item["title"], "item": url},
                ],
            },
        ],
    }


def release_page(item: dict) -> str:
    url = f"{BASE}/releases/{item['slug']}/"
    image = f"{BASE}/{item['image']}"
    mins, secs = divmod(item["duration"], 60)
    related = {
        "namaste-galaxy": [("red-moon-rising", "RED MOON // RISING", "images/eclypse-red-moon-rising-cover.png"), ("toriatsukai-chui", "取り扱いチュー💋い", "images/mv-toriatsukai-chuui.jpg"), ("mia", "M・I・A", "images/mv-mia.jpg")],
        "wasurenai-kokoro": [("boukyaku-no-ikimono", "忘却の生き物", "images/mv-boukyaku-no-ikimono.png"), ("mirai-no-watashi-ga-miteru", "未来の私が見てる", "images/mv-mirai-no-watashi-ga-miteru.jpg"), ("smile-and-say-goodbye", "SMILE AND SAY GOODBYE", "images/mv-smile-and-say-goodbye.png")],
        "smile-and-say-goodbye": [("suki-ga-kyou-mo-fueteiku", "好きが、今日も増えていく。", "images/mv-suki-ga-kyou-mo-fueteiku.jpg"), ("mirai-no-watashi-ga-miteru", "未来の私が見てる", "images/mv-mirai-no-watashi-ga-miteru.jpg"), ("kimi-wa-hanabi", "君は花火", "images/mv-hanabi.jpg")],
    }[item["slug"]]
    related_html = "".join(
        f'<a href="../{slug}/"><img src="../../{img}" alt="{title} ジャケット" width="886" height="886" loading="lazy"/><strong>{title}</strong><b>VIEW ↗</b></a>'
        for slug, title, img in related
    )
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{item['title']}｜{item['artist']}｜SUZUKA</title><meta name="description" content="{item['description']}"/><meta name="robots" content="index, follow"/>
<link rel="canonical" href="{url}"/><meta property="og:type" content="music.song"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{item['title']}｜{item['artist']}"/><meta property="og:description" content="{item['description']}"/><meta property="og:url" content="{url}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{item['title']}｜{item['artist']}"/><meta name="twitter:description" content="{item['description']}"/><meta name="twitter:image" content="{image}"/>
<link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/official-release.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/>
<script type="application/ld+json">{compact(jsonld_release(item))}</script></head><body><main><a class="skip-link" href="#release-detail">本文へ移動</a>
<header class="site-header inner-site-header"><a class="brand" href="../../">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../releases/">Releases</a><a href="../../news/">News</a><a href="../../about/">About SUZUKA</a></nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></header>
<section class="release-detail-hero" id="release-detail"><div class="release-detail-copy"><p class="release-breadcrumb"><a href="../../releases/">Releases</a> / {item['title']}</p><span>OFFICIAL RELEASE · {item['date'].replace('-', '.')}</span><h1>{item['title']}</h1><div class="release-artist-links"><a class="release-artist-link" href="../../artists/{item['artistSlug']}/">{item['artist']}</a></div><div><a class="button button-primary" href="{item['youtube']}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../social/">OFFICIAL LINKS</a></div></div><div class="release-detail-artwork"><img src="../../{item['image']}" alt="{item['alt']}" width="{item['width']}" height="{item['height']}" fetchpriority="high"/></div></section>
<section class="release-detail-video" aria-label="{item['title']}公式動画"><iframe src="https://www.youtube-nocookie.com/embed/{item['videoId']}" title="{item['title']} Official Music Video" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></section>
<section class="release-story-section"><div><p>Official release</p><h2>{item['title']}</h2></div><div><p>{item['description']}</p><dl class="release-facts"><div><dt>ARTIST</dt><dd>{item['artist']}</dd></div><div><dt>RELEASE</dt><dd>{item['date']}</dd></div><div><dt>DURATION</dt><dd>{mins}:{secs:02d}</dd></div><div><dt>LABEL</dt><dd>SUZUKA</dd></div></dl></div></section>
<section class="release-related-section"><div><p>Related music</p><h2>次の物語へ。</h2></div><div class="release-related-grid">{related_html}</div></section>
<nav class="artist-next-actions"><div><p>Keep exploring</p><h2>SUZUKAの音楽へ。</h2></div><a href="../../artists/{item['artistSlug']}/">アーティストを見る ↗</a><a href="../../news/{Path(item['news']).parts[1]}/">Newsを読む ↗</a><a href="../../releases/">Releasesを見る ↗</a></nav>
<footer class="artist-profile-footer"><a href="../../">SUZUKA</a><span>{item['title']} · {item['artist']}</span><a href="../../releases/">Back to releases ↑</a></footer></main><script defer src="../../assets/main.js"></script></body></html>"""


def artist_page(slug: str) -> str:
    if slug == "rangili":
        item = RELEASES[0]
        name, english, kind = "RANGILI", "RANGILI", "3人組ガールグループ"
        profile = "インドと日本、2つの文化が響き合う3人組ガールグループ。メインボーカルはインド育ちの日本人、ほか2名はインド人。インドの情熱とJ-POPのメロディを融合し、カラフルで明るい世界を描きます。"
        schema_type = "MusicGroup"
    else:
        item = RELEASES[1]
        name, english, kind = "朝霧しのぶ", "ASAGIRI SHINOBU", "演歌歌手"
        profile = "人生の喜びや別れ、高齢化社会や家族の想いを歌い続ける演歌歌手。認知症、記憶、家族、人生を見つめ、心に寄り添う歌を届けます。"
        schema_type = "Person"
    url = f"{BASE}/artists/{slug}/"
    image = f"{BASE}/{item['image']}"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "ProfilePage", "@id": url, "url": url, "name": f"{name}｜SUZUKA", "mainEntity": {"@id": f"{url}#artist"}, "breadcrumb": {"@id": f"{url}#breadcrumb"}, "inLanguage": "ja"},
            {"@type": schema_type, "@id": f"{url}#artist", "name": name, "alternateName": english, "description": profile, "image": image, "url": url, "memberOf": {"@type": "Organization", "name": "SUZUKA", "url": f"{BASE}/"}},
            {"@type": "ItemList", "@id": f"{url}#releases", "name": f"{name} 公開作品", "numberOfItems": 1, "itemListElement": [{"@type": "ListItem", "position": 1, "name": item["title"], "url": f"{BASE}/releases/{item['slug']}/"}]},
            {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{BASE}/artists/"}, {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
        ],
    }
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{name}｜{kind}｜SUZUKA</title><meta name="description" content="{profile}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{url}"/><meta property="og:type" content="profile"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{name}｜SUZUKA"/><meta property="og:description" content="{profile}"/><meta property="og:url" content="{url}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{name}｜SUZUKA"/><meta name="twitter:description" content="{profile}"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/upcoming.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main><a class="skip-link" href="#profile">本文へ移動</a><header class="site-header inner-site-header"><a class="brand" href="../../">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../releases/">Releases</a><a href="../../news/">News</a><a href="../../about/">About SUZUKA</a></nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></header><section class="upcoming-artist-hero" id="profile"><div class="upcoming-artist-copy"><p class="section-kicker">A SUZUKA Artist</p><h1>{name}<small>{english} · {kind}</small></h1><span class="coming-soon-badge">NOW ACTIVE</span><p>{profile}</p></div><div class="upcoming-artist-image"><img src="../../{item['image']}" alt="{item['alt']}" width="1254" height="1254" fetchpriority="high"/></div></section><section class="section"><article class="artist-release-feature"><img src="../../{item['image']}" alt="{item['alt']}" width="1254" height="1254" loading="lazy"/><div><p class="section-kicker">01 / Official release</p><h2>{item['title']}</h2><p>{item['description']}</p><a class="button button-primary" href="{item['youtube']}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../releases/{item['slug']}/">作品ページ ↗</a></div></article></section><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>次の物語へ。</h2></div><a href="../../artists/">他のアーティストを見る ↗</a><a href="../../releases/">Releasesを見る ↗</a><a href="../../social/">Official Links ↗</a></nav><footer class="artist-profile-footer"><a href="../../">SUZUKA</a><span>{name} · PUBLIC RELEASES 1</span><a href="../../artists/">Back to artists ↑</a></footer></main><script defer src="../../assets/main.js"></script></body></html>"""


def revive_page() -> str:
    url = f"{BASE}/artists/revive/"
    image = f"{BASE}/images/revive-heal-you-again.jpg"
    description = "応援、回復、再生をテーマに、傷ついた心に寄り添い、前へ進む力を届ける5人組ガールズグループ。"
    graph = {"@context": "https://schema.org", "@graph": [{"@type": "ProfilePage", "@id": url, "url": url, "name": "RE:VIVE｜SUZUKA", "mainEntity": {"@id": f"{url}#artist"}, "breadcrumb": {"@id": f"{url}#breadcrumb"}, "inLanguage": "ja"}, {"@type": "MusicGroup", "@id": f"{url}#artist", "name": "RE:VIVE", "description": description, "image": image, "url": url, "member": [{"@type": "Person", "name": "結衣", "description": "センター"}, {"@type": "Person", "name": "紗良"}], "memberOf": {"@type": "Organization", "name": "SUZUKA", "url": f"{BASE}/"}}, {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{BASE}/artists/"}, {"@type": "ListItem", "position": 3, "name": "RE:VIVE", "item": url}]}]}
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>RE:VIVE｜5人組ガールズグループ｜SUZUKA</title><meta name="description" content="{description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{url}"/><meta property="og:type" content="profile"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="RE:VIVE｜SUZUKA"/><meta property="og:description" content="{description}"/><meta property="og:url" content="{url}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/upcoming.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main><header class="site-header inner-site-header"><a class="brand" href="../../">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../releases/">Releases</a><a href="../../news/">News</a><a href="../../about/">About SUZUKA</a></nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></header><section class="upcoming-artist-hero"><div class="upcoming-artist-copy"><p class="section-kicker">NEW ARTIST</p><h1>RE:VIVE<small>5-MEMBER GIRLS GROUP</small></h1><span class="coming-soon-badge">Coming Soon</span><p>{description}</p><div class="upcoming-notice"><strong>DEBUT · 2026.07.27 20:00 JST</strong><p>Heal You Again — 公式YouTubeプレミア公開予定</p></div><a class="button button-primary" href="https://www.youtube.com/watch?v=XHjDSEoFcXE" target="_blank" rel="noopener noreferrer">予約動画を見る ↗</a></div><div class="upcoming-artist-image"><img src="../../images/revive-heal-you-again.jpg" alt="RE:VIVE「Heal You Again」公式YouTube公開予定ビジュアル" width="1280" height="720" fetchpriority="high"/></div></section><section class="upcoming-artist-about"><div><p class="section-kicker">Confirmed members</p><h2>結衣 <small>Center</small><br/>紗良</h2></div><div><p>確認済みのメンバー情報のみ掲載しています。ほか3名の名前は未確認のため掲載していません。</p><div class="upcoming-status-panel"><strong>STATUS</strong><span>Coming Soon · 2026.07.27 20:00 JST</span><strong>PUBLIC RELEASES</strong><span>0作品</span></div></div></section><nav class="artist-next-actions"><div><p>Keep exploring</p><h2>次の物語へ。</h2></div><a href="../../artists/">Artistsを見る ↗</a><a href="../../news/upcoming-artists/">Upcoming News ↗</a><a href="../../social/">Official Links ↗</a></nav><footer class="artist-profile-footer"><a href="../../">SUZUKA</a><span>RE:VIVE · COMING SOON</span><a href="../../artists/">Back to artists ↑</a></footer></main><script defer src="../../assets/main.js"></script></body></html>"""


def news_page(item: dict) -> str:
    url = f"{BASE}/{item['news']}"
    image = f"{BASE}/{item['image']}"
    title = f"{item['artist']}「{item['cardTitle'] if item.get('cardTitle') else item['title']}」公開"
    news_description = f"{item['artist']}の公式作品「{item.get('cardTitle', item['title'])}」公開情報。作品ページ、公式MV、アーティスト情報への導線をまとめました。"
    graph = {"@context": "https://schema.org", "@graph": [{"@type": "NewsArticle", "@id": f"{url}#article", "headline": title, "description": news_description, "datePublished": item["date"], "dateModified": "2026-07-26", "mainEntityOfPage": {"@id": url}, "image": image, "author": {"@type": "Organization", "name": "SUZUKA", "url": f"{BASE}/"}, "publisher": {"@type": "Organization", "name": "SUZUKA", "url": f"{BASE}/"}, "url": url}, {"@type": "WebPage", "@id": url, "url": url, "name": title, "breadcrumb": {"@id": f"{url}#breadcrumb"}, "inLanguage": "ja"}, {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "News", "item": f"{BASE}/news/"}, {"@type": "ListItem", "position": 3, "name": title, "item": url}]}]}
    return f"""<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{title}｜SUZUKA</title><meta name="description" content="{news_description}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{url}"/><meta property="og:type" content="article"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:locale" content="ja_JP"/><meta property="og:title" content="{title}"/><meta property="og:description" content="{news_description}"/><meta property="og:url" content="{url}"/><meta property="og:image" content="{image}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/><link rel="icon" href="../../images/suzuka-channel.jpg"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/current-status.css"/><link rel="stylesheet" href="../../assets/player.css"/><script type="application/ld+json">{compact(graph)}</script></head><body><main><header class="site-header inner-site-header"><a class="brand" href="../../">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav"><a href="../../">Home</a><a href="../../artists/">Artists</a><a href="../../releases/">Releases</a><a href="../../news/">News</a><a href="../../about/">About SUZUKA</a></nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></header><article class="news-article"><header class="news-article-hero"><p class="news-breadcrumb"><a href="../../news/">News</a> / Release</p><div class="news-article-meta"><time datetime="{item['date']}">{item['date'].replace('-', '.')}</time><span>OFFICIAL RELEASE</span></div><h1>{title}</h1><p class="news-article-lead">{news_description}</p></header><div class="news-article-body"><section><img src="../../{item['image']}" alt="{item['alt']}" width="{item['width']}" height="{item['height']}" loading="lazy"/><h2>公式作品を公開</h2><p>{item['description']}</p><div class="news-feature-actions"><a class="button button-primary" href="{item['youtube']}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a class="button button-ghost" href="../../releases/{item['slug']}/">作品ページ ↗</a><a class="button button-ghost" href="../../artists/{item['artistSlug']}/">アーティストページ ↗</a><a class="button button-ghost" href="../../social/">公式リンク一覧</a></div></section></div></article><footer class="artist-profile-footer"><a href="../../">SUZUKA</a><span>OFFICIAL NEWS</span><a href="../../news/">Back to News ↑</a></footer></main><script defer src="../../assets/main.js"></script></body></html>"""


def release_card(item: dict, asset_prefix: str = "./", page_prefix: str = "./") -> str:
    title = item.get("cardTitle", item["title"])
    mins, secs = divmod(item["duration"], 60)
    return f'<article class="release-card release-card-new"><a class="release-image" href="{page_prefix}{item["slug"]}/" aria-label="{title}の詳細を見る"><img src="{asset_prefix}{item["image"]}" alt="{item["alt"]}" width="{item["width"]}" height="{item["height"]}" loading="lazy"/><span class="card-play"><span class="play-mark" aria-hidden="true"></span></span><span class="duration">{mins}:{secs:02d}</span></a><div class="release-info"><div class="release-row"><span>00</span><span>OFFICIAL MV · {item["date"].replace("-", ".")}</span></div><h3>{title}</h3><p class="release-artist-credit">{item["artist"]}</p><div class="release-card-actions"><a class="release-card-cta release-card-cta-detail" href="{page_prefix}{item["slug"]}/">詳細を見る ↗</a><a class="release-card-cta" href="{item["youtube"]}" target="_blank" rel="noopener noreferrer">MVを見る ↗</a></div></div></article>'


def renumber_cards(source: str) -> str:
    number = 0
    def repl(match: re.Match[str]) -> str:
        nonlocal number
        number += 1
        return f"{match.group(1)}{number:02d}{match.group(2)}"
    return re.sub(r'(<div class="release-row"><span>)\d+(</span>)', repl, source)


def update_itemlist(source: str, itemlist_id: str, additions: list[dict], prepend: bool = True) -> str:
    pattern = re.compile(r'<script(?: id="[^"]+")? type="application/ld\+json">(.*?)</script>', re.DOTALL)
    def repl(match: re.Match[str]) -> str:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        graph = data.get("@graph", []) if isinstance(data, dict) else []
        if not graph and isinstance(data, dict) and data.get("@type") == "ItemList":
            graph = [data]
        changed = False
        for node in graph:
            if node.get("@id") != itemlist_id:
                continue
            existing = [x for x in node.get("itemListElement", []) if x.get("url") not in {a["url"] for a in additions}]
            items = additions + existing if prepend else existing + additions
            node["itemListElement"] = [{"@type": "ListItem", "position": i, **{k: v for k, v in x.items() if k not in {"@type", "position"}}} for i, x in enumerate(items, 1)]
            node["numberOfItems"] = len(items)
            changed = True
        if not changed:
            return match.group(0)
        attrs = match.group(0).split(">", 1)[0] + ">"
        return attrs + compact(data) + "</script>"
    return pattern.sub(repl, source)


def update_data(root: Path) -> None:
    release_path = root / "assets/data/release-links.json"
    data = json.loads(release_path.read_text(encoding="utf-8"))
    by_slug = {x["slug"]: x for x in data["releases"]}
    for item in RELEASES:
        payload = {
            "slug": item["slug"], "title": item["title"], "artist": item["artist"], "artistSlug": item["artistSlug"],
            "status": "published", "releaseType": "single", "image": item["image"], "coverImage": item["image"],
            "coverAlt": item["alt"], "releasePage": f"releases/{item['slug']}/", "youtubeUrl": item["youtube"],
            "youtubeStatus": "published", "shortsUrl": None, "shortsStatus": "unconfirmed", "publishedDate": item["date"],
            "duration": item["duration"], "description": item["description"], "playerEnabled": False, "newsPage": item["news"],
            "newsUrl": item["news"], "newsStatus": "published", "relatedReleases": [], "credits": None, "lyricsStatus": "unconfirmed",
        }
        if item.get("cardTitle"):
            payload["cardTitle"] = item["cardTitle"]
            payload["titleEnglish"] = item["cardTitle"]
            payload["subtitle"] = "大好きだから、笑ってさようなら。"
        if item["slug"] in by_slug:
            by_slug[item["slug"]].update(payload)
        else:
            data["releases"].append(payload)
    # OUR KINGDOM is one release page shared by two artists. Keep one catalog
    # row while allowing artist attribution counts to include both performers.
    if "our-kingdom" in by_slug:
        by_slug["our-kingdom"]["artistSlugs"] = ["enomoto-mia", "koga-kamishiro"]
    release_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mia_path = root / "assets/data/enomoto-mia-releases.json"
    mia = json.loads(mia_path.read_text(encoding="utf-8"))
    smile = next(x for x in mia["releases"] if x["slug"] == "smile-and-say-goodbye")
    smile.update({"status": "published", "youtubeUrl": RELEASES[2]["youtube"], "youtubeId": RELEASES[2]["videoId"], "youtubeVideoTitle": "【Official MV】榎本魅愛「SMILE AND SAY GOODBYE ― 大好きだから、笑ってさようなら。―」", "duration": RELEASES[2]["duration"], "uploadDate": RELEASES[2]["date"]})
    mia_path.write_text(json.dumps(mia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    social_path = root / "assets/data/social-links.json"
    social = json.loads(social_path.read_text(encoding="utf-8"))
    for item in social["links"]:
        if item["platform"] == "youtube":
            item.update({"url": CHANNEL, "status": "published"})
        if item["platform"] == "instagram":
            item.update({"url": INSTAGRAM, "status": "published"})
    social["updatedAt"] = "2026-07-26"
    social_path.write_text(json.dumps(social, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_home(root: Path) -> None:
    path = root / "index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "./assets/current-status.css")
    latest = RELEASES[0]
    hero_actions = f'<div class="hero-release-actions reveal-up delay-4" aria-label="最新リリース {latest["title"]}のメニュー"><p><span>LATEST RELEASE</span><strong>{latest["artist"]} — {latest["title"]}</strong></p><a class="button button-primary" href="{latest["youtube"]}" target="_blank" rel="noopener noreferrer">MVを見る <span aria-hidden="true">↗</span></a><a class="button button-ghost" href="./releases/{latest["slug"]}/">楽曲情報を見る <span aria-hidden="true">▶</span></a><a class="button button-youtube" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTubeでSUZUKAをフォロー <span aria-hidden="true">↗</span></a><a class="button button-ghost" data-home-social-link="true" href="./social/" aria-label="YouTube・楽曲・Newsをまとめた公式リンク一覧を見る">公式リンク一覧</a></div>'
    source = re.sub(r'<div class="hero-release-actions reveal-up delay-4".*?</div>', hero_actions, source, count=1, flags=re.DOTALL)
    latest_section = f'<section class="section latest-section label-latest" id="latest" aria-labelledby="latest-title"><div class="section-heading section-heading-split"><div><p class="section-kicker">01 / Latest release</p><h2 id="latest-title">{latest["title"]}</h2></div><p>{latest["artist"]}<br/>Official Music Video</p></div><article class="featured-release"><div class="featured-media square-release-media"><img src="./{latest["image"]}" alt="{latest["alt"]}" width="1254" height="1254"/><div class="featured-glow"></div></div><div class="featured-copy"><div class="track-number">01</div><p class="featured-label">{latest["artist"]} · OFFICIAL MV · 2026.07.24</p><h3>{latest["title"]}</h3><p class="featured-description">{latest["description"]}</p><div class="release-card-actions"><a class="text-link" href="{latest["youtube"]}" target="_blank" rel="noopener noreferrer">WATCH OFFICIAL VIDEO ↗</a><a class="text-link" href="./releases/{latest["slug"]}/">VIEW RELEASE ↗</a></div></div></article></section>'
    source = replace_section(source, "section latest-section label-latest", "section eclypse-home-section", latest_section)
    upcoming = '<section class="upcoming-section" id="upcoming-artists" aria-labelledby="upcoming-title"><div class="upcoming-heading"><div><p class="section-kicker">05 / Next releases</p><h2 id="upcoming-title">Upcoming</h2></div><p>公開済み作品と分けて、次の公開予定をお知らせします。</p></div><div class="status-strip-grid"><article class="status-card"><img src="./images/koga-kamishiro.webp" alt="神代煌牙 アーティストビジュアル" width="1122" height="1402" loading="lazy"/><div><time datetime="2026-07-26T20:00:00+09:00">2026.07.26 20:00 JST</time><h3>Echoes of You</h3><p>神代 煌牙 · 公式予約URLと正式画像は未確認</p><div class="status-actions"><a href="./artists/koga-kamishiro/">Artist page ↗</a></div></div></article><article class="status-card is-wide"><img src="./images/revive-heal-you-again.jpg" alt="RE:VIVE「Heal You Again」公式YouTube公開予定ビジュアル" width="1280" height="720" loading="lazy"/><div><time datetime="2026-07-27T20:00:00+09:00">2026.07.27 20:00 JST</time><h3>Heal You Again</h3><p>RE:VIVE · Official YouTube Premiere</p><div class="status-actions"><a href="https://www.youtube.com/watch?v=XHjDSEoFcXE" target="_blank" rel="noopener noreferrer">予約動画を見る ↗</a><a href="./artists/revive/">Artist page ↗</a></div></div></article></div></section>'
    source = replace_section(source, "upcoming-section", "section about-section label-about-home", upcoming)
    for item in RELEASES:
        source = re.sub(rf'<article class="release-card[^"]*">(?:(?!</article>).)*?href="[^"]*{re.escape(item["slug"])}/"(?:(?!</article>).)*?</article>', '', source, count=1, flags=re.DOTALL)
    for item in reversed(RELEASES):
        source = source.replace('<div class="release-grid">', '<div class="release-grid">' + release_card(item, "./", "./releases/"), 1)
    if './artists/asagiri-shinobu/' not in source:
        source = source.replace('</article></section><section class="section eclypse-home-section"', '</article><nav class="status-actions" aria-label="最新公開アーティスト"><a href="./artists/rangili/">RANGILI ↗</a><a href="./artists/asagiri-shinobu/">朝霧しのぶ ↗</a></nav></section><section class="section eclypse-home-section"', 1)
    for item in RELEASES:
        news_slug = Path(item["news"]).parts[1]
        source = re.sub(
            rf'<article><a href="\./news/{re.escape(news_slug)}/".*?</article>',
            "",
            source,
            count=1,
            flags=re.DOTALL,
        )
    for item in reversed(RELEASES):
        news_slug = Path(item["news"]).parts[1]
        card = f'<article><a href="./news/{news_slug}/"><time datetime="{item["date"]}">{item["date"].replace("-", ".")}</time><span>OFFICIAL RELEASE</span><h3>{item["artist"]}「{item.get("cardTitle", item["title"])}」公開</h3><b>↗</b></a></article>'
        source = source.replace('<div class="news-list">', '<div class="news-list">' + card, 1)
    source = source.replace("SUZUKA Upcoming Artists — RANGILI・朝霧しのぶ", "SUZUKA Latest & Upcoming — 2026.07.26")
    source = source.replace('<time datetime="2026-07-22">2026.07.22</time><span>ARTIST NEWS</span><h3>SUZUKA Latest &amp; Upcoming', '<time datetime="2026-07-26">2026.07.26</time><span>ARTIST NEWS</span><h3>SUZUKA Latest &amp; Upcoming')
    source = source.replace('<time datetime="2026-07-22">2026.07.22</time><span>ARTIST NEWS</span><h3>SUZUKA Latest & Upcoming', '<time datetime="2026-07-26">2026.07.26</time><span>ARTIST NEWS</span><h3>SUZUKA Latest & Upcoming')
    source = renumber_cards(source)
    path.write_text(source, encoding="utf-8")


def update_releases(root: Path) -> None:
    path = root / "releases/index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "../assets/current-status.css")
    source = source.replace("榎本魅愛、ECLYPSE、神代煌牙の楽曲情報", "榎本魅愛、ECLYPSE、神代煌牙、RANGILI、朝霧しのぶの楽曲情報")
    for item in RELEASES:
        source = re.sub(rf'<article class="release-card[^"]*">(?:(?!</article>).)*?href="[^"]*{re.escape(item["slug"])}/"(?:(?!</article>).)*?</article>', '', source, count=1, flags=re.DOTALL)
    for item in reversed(RELEASES):
        source = source.replace('<div class="release-grid">', '<div class="release-grid">' + release_card(item, "../", "./"), 1)
    source = renumber_cards(source)
    additions = [{"name": x.get("cardTitle", x["title"]), "url": f"{BASE}/releases/{x['slug']}/"} for x in RELEASES]
    source = update_itemlist(source, f"{BASE}/releases/#itemlist", additions)
    path.write_text(source, encoding="utf-8")


def update_artists_index(root: Path) -> None:
    path = root / "artists/index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "../assets/current-status.css")
    source = re.sub(r'<article class="artist-directory-card artist-coming-soon-card"[^>]*><a href="../artists/rangili/".*?</article>', '<article class="artist-directory-card" style="--artist-primary:#ff62c8;--artist-secondary:#130a18;--artist-glow:rgba(255,98,200,.3)"><a href="../artists/rangili/"><div class="artist-directory-image"><img src="../images/rangili-namaste-galaxy.jpg" alt="RANGILI「NAMASTE☆GALAXY」公式ジャケット" width="1254" height="1254" loading="lazy"/><span class="artist-directory-number">04</span></div><div class="artist-directory-copy"><span>A SUZUKA Artist</span><h3>RANGILI<small>RANGILI</small></h3><p class="artist-directory-type">3人組ガールグループ</p><p class="artist-directory-genre">公開作品 1</p><p>インドと日本の文化を融合したカラフルなガールグループ。</p><div class="artist-directory-link">View profile ↗</div></div></a></article>', source, count=1, flags=re.DOTALL)
    source = re.sub(r'<article class="artist-directory-card artist-coming-soon-card"[^>]*><a href="../artists/asagiri-shinobu/".*?</article>', '<article class="artist-directory-card" style="--artist-primary:#e3b982;--artist-secondary:#160f0c;--artist-glow:rgba(227,185,130,.28)"><a href="../artists/asagiri-shinobu/"><div class="artist-directory-image"><img src="../images/asagiri-wasurenai-kokoro.jpg" alt="朝霧しのぶ「忘れない心」公式ジャケット" width="1254" height="1254" loading="lazy"/><span class="artist-directory-number">05</span></div><div class="artist-directory-copy"><span>A SUZUKA Artist</span><h3>朝霧しのぶ<small>ASAGIRI SHINOBU</small></h3><p class="artist-directory-type">演歌歌手</p><p class="artist-directory-genre">公開作品 1</p><p>家族、記憶、人生に寄り添う歌を届ける演歌歌手。</p><div class="artist-directory-link">View profile ↗</div></div></a></article>', source, count=1, flags=re.DOTALL)
    if '../artists/revive/' not in source:
        card = '<article class="artist-directory-card artist-coming-soon-card" style="--artist-primary:#72e5dc;--artist-secondary:#09141a;--artist-glow:rgba(114,229,220,.3)"><a href="../artists/revive/"><div class="artist-directory-image"><img src="../images/revive-heal-you-again.jpg" alt="RE:VIVE「Heal You Again」公式YouTube公開予定ビジュアル" width="1280" height="720" loading="lazy"/><span class="artist-directory-number">06</span></div><div class="artist-directory-copy"><span class="coming-soon-badge">Coming Soon</span><h3>RE:VIVE<small>RE:VIVE</small></h3><p class="artist-directory-type">5人組ガールズグループ</p><p class="artist-directory-genre">公開作品 0</p><p>傷ついた心に寄り添い、前へ進む力を届ける。</p><div class="artist-directory-link">View introduction ↗</div></div></a></article>'
        source = source.replace('</div></section><footer', card + '</div></section><footer', 1)
    source = update_itemlist(source, f"{BASE}/artists/#artist-list", [{"name": "RE:VIVE", "url": f"{BASE}/artists/revive/"}], prepend=False)
    path.write_text(source, encoding="utf-8")


def update_mia(root: Path) -> None:
    path = root / "artists/enomoto-mia/index.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace('UPCOMING · 2026.07.22', 'OFFICIAL MV · 2026.07.22').replace('Upcoming · 2026.07.22', 'Official · 2026.07.22')
    source = update_itemlist(source, f"{BASE}/artists/enomoto-mia/#releases", [{"name": RELEASES[2]["title"], "url": f"{BASE}/releases/smile-and-say-goodbye/"}])
    if RELEASES[2]["youtube"] not in source:
        marker = '<div class="artist-mv-link-grid">'
        source = source.replace(marker, marker + f'<a href="{RELEASES[2]["youtube"]}" target="_blank" rel="noopener noreferrer"><span>SMILE AND SAY GOODBYE</span><b>公式MV ↗</b></a>', 1)
    path.write_text(source, encoding="utf-8")


def update_koga(root: Path) -> None:
    path = root / "artists/koga-kamishiro/index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "../../assets/current-status.css")
    if "Echoes of You" not in source:
        notice = '<section class="section"><div class="upcoming-notice"><strong>UPCOMING · 2026.07.26 20:00 JST</strong><p>Echoes of You — 公式予約URLと正式画像は未確認のため、公開済み作品には含めていません。</p></div></section>'
        source = source.replace('<nav class="artist-next-actions"', notice + '<nav class="artist-next-actions"', 1)
    path.write_text(source, encoding="utf-8")


def update_news(root: Path) -> None:
    path = root / "news/index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "../assets/current-status.css")
    source = source.replace("RANGILIと朝霧しのぶが、SUZUKAでデビュー準備中です。", "RANGILIと朝霧しのぶの正式公開、神代煌牙とRE:VIVEの公開予定をお知らせします。")
    cards = []
    for item in RELEASES:
        slug = Path(item["news"]).parts[1]
        if f'./{slug}/' not in source:
            title = f'{item["artist"]}「{item.get("cardTitle", item["title"])}」公開'
            cards.append(f'<article class="news-directory-card"><a href="./{slug}/"><span class="news-directory-image"><img src="../{item["image"]}" alt="{title} News" width="{item["width"]}" height="{item["height"]}" loading="lazy"/></span><span class="news-directory-meta"><time datetime="{item["date"]}">{item["date"].replace("-", ".")}</time><em>OFFICIAL RELEASE</em></span><h2>{title}</h2><p>{item["description"]}</p><b>記事を読む ↗</b></a></article>')
    if cards:
        source = source.replace('<div class="news-list news-feature-list">', '<div class="news-list news-feature-list">' + "".join(cards), 1)
    additions = [
        {
            "name": "SUZUKA Latest & Upcoming｜2026.07.26",
            "url": f"{BASE}/news/upcoming-artists/",
        },
        *[
            {
                "name": f'{x["artist"]}「{x.get("cardTitle", x["title"])}」公開',
                "url": f"{BASE}/{x['news']}",
            }
            for x in RELEASES
        ],
    ]
    source = update_itemlist(source, f"{BASE}/news/#itemlist", additions)
    path.write_text(source, encoding="utf-8")


def update_social(root: Path) -> None:
    path = root / "social/index.html"
    source = stylesheet(path.read_text(encoding="utf-8"), "../assets/current-status.css")
    source = source.replace('RANGILI · Coming Soon', 'RANGILI · 公開作品 1').replace('朝霧しのぶ · Coming Soon', '朝霧しのぶ · 公開作品 1')
    if '../artists/revive/' not in source:
        marker = '<a href="../artists/asagiri-shinobu/"><span>朝霧しのぶ · 公開作品 1</span><b aria-hidden="true">→</b></a>'
        source = source.replace(marker, marker + '<a href="../artists/revive/"><span>RE:VIVE · Coming Soon</span><b aria-hidden="true">→</b></a>', 1)
    directory_marker = '<div class="social-hub-directory">'
    links = ''.join(f'<a href="../releases/{x["slug"]}/"><span>{x.get("cardTitle", x["title"])} · {x["artist"]}</span><b aria-hidden="true">→</b></a>' for x in RELEASES)
    if '../releases/namaste-galaxy/' not in source:
        source = source.replace(directory_marker, directory_marker + links, 1)
    if 'Heal You Again · 2026.07.27' not in source:
        source = source.replace('<section class="social-hub-footer-cta"', '<section class="status-strip"><div class="upcoming-notice"><strong>NEXT · 2026.07.27 20:00 JST</strong><p>RE:VIVE「Heal You Again」 <a href="https://www.youtube.com/watch?v=XHjDSEoFcXE" target="_blank" rel="noopener noreferrer">公式予約動画 ↗</a></p></div></section><section class="social-hub-footer-cta"', 1)
    if INSTAGRAM not in source:
        source = source.replace('<section class="social-hub-footer-cta"', f'<section class="status-strip"><div class="status-actions"><a href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">SUZUKA Official Instagram ↗</a></div></section><section class="social-hub-footer-cta"', 1)
    path.write_text(source, encoding="utf-8")


def update_upcoming_news(root: Path) -> None:
    path = root / "news/upcoming-artists/index.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace("<title>SUZUKA Upcoming Artists｜RANGILI・朝霧しのぶ</title>", "<title>SUZUKA Latest &amp; Upcoming｜2026.07.26</title>")
    source = source.replace('content="SUZUKA Upcoming Artists"', 'content="SUZUKA Latest &amp; Upcoming｜2026.07.26"')
    source = source.replace('"headline":"SUZUKA Upcoming Artists"', '"headline":"SUZUKA Latest & Upcoming｜2026.07.26"')
    source = source.replace('"name":"SUZUKA Upcoming Artists"', '"name":"SUZUKA Latest & Upcoming｜2026.07.26"')
    source = source.replace('"description":"RANGILIと朝霧しのぶがデビュー準備中であることを紹介するSUZUKA公式News。"', '"description":"RANGILIと朝霧しのぶの正式公開、神代煌牙とRE:VIVEの公開予定を伝えるSUZUKA公式News。"')
    source = source.replace('<nav class="artist-next-actions">', '<nav class="artist-next-actions social-context-section">')
    source = source.replace("RANGILIと朝霧しのぶがデビュー準備中。", "RANGILIと朝霧しのぶの正式公開、神代煌牙とRE:VIVEの公開予定をお知らせします。")
    source = source.replace("新たにRANGILIと朝霧しのぶが、SUZUKAでデビュー準備を進めています。", "RANGILIと朝霧しのぶは正式公開を迎えました。次の公開予定は神代煌牙とRE:VIVEです。")
    source = source.replace("<strong>Coming Soon — 現在デビュー準備中</strong>", "<strong>NOW ACTIVE — 公開作品 1</strong>", 2)
    source = source.replace('<span class="coming-soon-badge">公開予定</span><p>本作品はUpcoming情報です。公開済み作品としては掲載していません。</p>', '<span class="coming-soon-badge">公開済み</span><p>公式MV公開を確認し、正式リリースへ更新しました。</p>')
    if "Heal You Again" not in source:
        block = '<section class="upcoming-schedule"><div class="upcoming-schedule-inner"><div><p class="section-kicker">Upcoming releases</p><h2>Next stories</h2></div><div><h2>Echoes of You</h2><p>神代 煌牙 · 2026.07.26 20:00 JST<br/>公式予約URL・正式画像は未確認</p><h2>Heal You Again</h2><p>RE:VIVE · 2026.07.27 20:00 JST</p><a class="button button-primary" href="https://www.youtube.com/watch?v=XHjDSEoFcXE" target="_blank" rel="noopener noreferrer">公式予約動画 ↗</a></div></div></section>'
        source = source.replace('</div></article>', block + '</div></article>', 1)
    source = source.replace('"dateModified":"2026-07-22"', '"dateModified":"2026-07-26"')
    path.write_text(source, encoding="utf-8")


def normalize_official_links(root: Path) -> None:
    """Keep the current official handle after every content-source sync."""
    for path in root.rglob("*.html"):
        if ".git" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        updated = source.replace("https://www.youtube.com/@bellflower5215", CHANNEL)
        if updated != source:
            path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    update_data(root)
    for item in RELEASES:
        write(root / "releases" / item["slug"] / "index.html", release_page(item))
        write(root / item["news"] / "index.html", news_page(item))
    write(root / "artists/rangili/index.html", artist_page("rangili"))
    write(root / "artists/asagiri-shinobu/index.html", artist_page("asagiri-shinobu"))
    write(root / "artists/revive/index.html", revive_page())
    update_home(root)
    update_releases(root)
    update_artists_index(root)
    update_mia(root)
    update_koga(root)
    update_news(root)
    update_social(root)
    update_upcoming_news(root)
    normalize_official_links(root)
    print("Generated verified SUZUKA publication state for 2026-07-26.")


if __name__ == "__main__":
    main()

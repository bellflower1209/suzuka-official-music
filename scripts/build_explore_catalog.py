#!/usr/bin/env python3
"""Generate SUZUKA's release catalog, discovery pages and shared exploration links."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bellflower1209.github.io/suzuka-official-music"
CHANNEL = "https://www.youtube.com/@suzuka1209"

DATES = {
    "heal-you-again": ("2026-07-27", 105), "echoes-of-you": ("2026-07-26", 484),
    "my-queen-my-oath": ("2026-07-20", 297), "red-moon-rising": ("2026-07-18", 364),
    "smile-and-say-goodbye": ("2026-07-22", 497), "boukyaku-no-ikimono": ("2026-07-21", 284),
    "moshimo-ashita-hajimemashite-ni-natte-mo": ("2026-07-16", 417),
    "suki-ga-kyou-mo-fueteiku": ("2026-07-16", 351), "toriatsukai-chui": ("2026-07-14", 324),
    "our-kingdom": ("2026-07-14", 377), "mirai-no-watashi-ga-miteru": ("2026-07-14", 484),
    "muteki-jikan-ato-3byou": ("2026-07-13", 232), "mia": ("2026-07-13", 328),
    "tokenai-mahou-wo-ai-to-yobu": ("2026-07-13", 380), "kimi-to-nara-last-boss-made": ("2026-07-13", 329),
    "ai-demo-wakaranai": ("2026-07-13", 315), "kimi-wa-hanabi": ("2026-07-12", 280),
    "mermaid-merman": ("2026-07-12", 340), "sukitte-baretemo-ii": ("2026-07-12", 274),
    "hyakumankoku": ("2026-07-12", 295), "shadow-code": ("2026-07-14", 181),
    "namaste-galaxy": ("2026-07-24", 163), "wasurenai-kokoro": ("2026-07-23", 311),
    "ashita-wa-kitto": ("2026-07-28", 215), "chimpanzee-no-rakuen": ("2026-07-29", 148),
}

META = {
    "enomoto-mia": {"type": "Person", "genres": ["J-POP", "ロマンティックポップ"], "moods": ["明るい", "切ない"], "aliases": ["榎本魅愛", "えのもとみあ", "ENOMOTO MIA", "MIA"]},
    "koga-kamishiro": {"type": "Person", "genres": ["J-POP", "ロック", "ダークポップ"], "moods": ["力強い", "シネマティック"], "aliases": ["神代煌牙", "神代 煌牙", "かみしろこうが", "KOGA KAMISHIRO"]},
    "eclypse": {"type": "MusicGroup", "genres": ["K-POP風", "ダークポップ"], "moods": ["ダーク", "力強い"], "aliases": ["ECLYPSE", "エクリプス"]},
    "rangili": {"type": "MusicGroup", "genres": ["J-POP", "インド×J-POP"], "moods": ["華やか", "エネルギッシュ"], "aliases": ["RANGILI", "ランギリ"]},
    "asagiri-shinobu": {"type": "Person", "genres": ["演歌", "歌謡曲"], "moods": ["切ない", "温かい"], "aliases": ["朝霧しのぶ", "あさぎりしのぶ"]},
    "revive": {"type": "MusicGroup", "genres": ["J-POP", "アイドルポップ"], "moods": ["希望", "力強い"], "aliases": ["RE:VIVE", "リバイブ"]},
    "nox": {"type": "MusicGroup", "genres": ["V系", "ダークロック"], "moods": ["ダーク", "挑発的"], "aliases": ["NOX", "ノクス"]},
}

OVERRIDES = {
    "red-moon-rising": (["K-POP風", "ダークポップ", "サイバーパンク"], ["覚醒", "反逆", "運命"]),
    "shadow-code": (["K-POP風", "ダークポップ", "EDM"], ["運命", "反逆", "未来"]),
    "wasurenai-kokoro": (["演歌", "歌謡曲"], ["家族", "記憶", "人生"]),
    "chimpanzee-no-rakuen": (["V系", "ダークロック"], ["社会", "本能", "問い"]),
    "namaste-galaxy": (["J-POP", "インド×J-POP"], ["文化", "宇宙", "出会い"]),
    "heal-you-again": (["J-POP", "アイドルポップ"], ["再生", "希望", "癒やし"]),
    "my-queen-my-oath": (["J-POP", "ロック", "シネマティック"], ["誓い", "愛", "運命"]),
    "boukyaku-no-ikimono": (["ロック", "ダークポップ"], ["忘却", "社会", "痛み"]),
    "our-kingdom": (["J-POP", "シネマティック"], ["愛", "王国", "誓い"]),
    "mermaid-merman": (["J-POP", "ファンタジーポップ"], ["恋愛", "海", "異世界"]),
    "kimi-wa-hanabi": (["J-POP", "サマーポップ"], ["恋愛", "夏", "記憶"]),
    "ashita-wa-kitto": (["J-POP", "バラード"], ["希望", "祈り", "明日"]),
    "smile-and-say-goodbye": (["J-POP", "バラード"], ["別れ", "愛", "笑顔"]),
}

NEW = [
    {
        "slug": "ashita-wa-kitto", "title": "明日は、きっと。", "artist": "榎本魅愛",
        "artistSlug": "enomoto-mia", "image": "images/mv-ashita-wa-kitto.jpg",
        "coverAlt": "榎本魅愛「明日は、きっと。」公式YouTubeサムネイル",
        "youtubeUrl": "https://www.youtube.com/watch?v=5MkQZT5qiGA",
        "description": "不安な夜を越え、明日への希望と無事を祈る榎本魅愛の楽曲。",
        "newsPage": "news/ashita-wa-kitto-release/",
    },
    {
        "slug": "chimpanzee-no-rakuen", "title": "チンパンジーの楽園", "artist": "NOX",
        "artistSlug": "nox", "image": "images/nox-chimpanzee-no-rakuen.jpg",
        "coverAlt": "NOX「チンパンジーの楽園」公式YouTubeサムネイル",
        "youtubeUrl": "https://www.youtube.com/watch?v=EJJLBOo103I",
        "description": "人間の本能と社会への問いを、ダークなバンドサウンドと物語で描くNOXのデビュー作品。",
        "newsPage": "news/chimpanzee-no-rakuen-release/",
    },
]

UPCOMING = [
    ("koisuru-maharaja", "恋するマハラジャ", "RANGILI", "rangili", "2026-07-30T20:00:00+09:00", "V3DOM83zeLk"),
    ("without-worrying", "Without Worrying", "榎本魅愛", "enomoto-mia", "2026-07-31T20:00:00+09:00", "lMeYWn4Sqgk"),
    ("lost-signal", "LOST SIGNAL", "ECLYPSE", "eclypse", "2026-08-01T20:00:00+09:00", "CbpvpKllc6c"),
    ("one-more-kiss", "One More Kiss", "神代煌牙", "koga-kamishiro", "2026-08-02T20:00:00+09:00", "EP7NAPlGhuo"),
    ("zennin-saiban", "善人裁判", "NOX", "nox", "2026-08-03T20:00:00+09:00", "8BjnnX3xeGw"),
]

GENRES = {
    "j-pop": ("J-POP", "恋愛曲、青春曲、ポップバラードなど、日本語ポップスを中心に紹介します。"),
    "enka": ("演歌", "人生、家族、記憶に寄り添う演歌・歌謡曲作品を紹介します。"),
    "k-pop-inspired": ("K-POP風", "K-POPの構成、ダンス、サウンド、ビジュアル要素を取り入れた作品です。"),
    "visual-kei": ("V系", "ヴィジュアル系、ダークロック、心理的世界観を持つ作品です。"),
}


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def prefix(path: Path) -> str:
    return "../" * len(path.relative_to(ROOT).parent.parts)


def header(p: str) -> str:
    nav = f'<a href="{p}">Home</a><a href="{p}artists/">Artists</a><a href="{p}releases/">Releases</a><a href="{p}search/">Search</a><a href="{p}rankings/">Ranking</a><a href="{p}features/">Features</a><a href="{p}gallery/">Gallery</a><a href="{p}universe/">Universe</a><a href="{p}wiki/">Wiki</a><a href="{p}playlists/">Playlists</a><a href="{p}community/">Community</a><a href="{p}genres/">Genres</a><a href="{p}discography/">Discography</a><a href="{p}news/">News</a><a href="{p}social/">Social</a>'
    return f'<header class="site-header inner-site-header"><a class="brand" href="{p}">SUZUKA<span class="brand-dot">●</span></a><nav class="desktop-nav" aria-label="メインナビゲーション">{nav}</nav><a class="header-channel" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a><details class="mobile-menu"><summary>Menu</summary><nav>{nav}</nav></details></header>'


def footer(p: str) -> str:
    return f'<footer class="site-footer inner-footer"><div class="footer-top"><a class="footer-brand" href="{p}">SUZUKA</a><p>Original AI Music Project</p><a href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube ↗</a></div><nav class="site-footer-nav" aria-label="フッターナビゲーション"><a href="{p}search/">Search</a><a href="{p}genres/">Genres</a><a href="{p}discography/">Discography</a><a href="{p}artists/">Artists</a><a href="{p}releases/">Releases</a><a href="{p}news/">News</a><a href="{p}social/">Social</a></nav><p class="ai-footer-disclosure">SUZUKAに登場するアーティスト・人物は架空です。本プロジェクトではAIを制作支援に活用しています。</p></footer>'


def shell(route: str, title: str, description: str, h1: str, body: str, schema: dict, script: bool = False) -> str:
    depth = len([x for x in route.split("/") if x])
    p = "../" * depth
    canonical = f"{BASE}/{route.strip('/') + '/' if route.strip('/') else ''}"
    js = f'<script defer src="{p}assets/explore.js"></script>' if script else ""
    data = f' data-catalog-url="{p}assets/data/releases-catalog.json" data-site-base="{p}"' if script else ""
    return f'<!doctype html><html lang="ja"{data}><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{html.escape(title)}</title><meta name="description" content="{html.escape(description)}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{canonical}"/><meta property="og:type" content="website"/><meta property="og:site_name" content="SUZUKA"/><meta property="og:title" content="{html.escape(title)}"/><meta property="og:description" content="{html.escape(description)}"/><meta property="og:url" content="{canonical}"/><meta property="og:image" content="{BASE}/images/suzuka-channel.jpg"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{html.escape(title)}"/><meta name="twitter:description" content="{html.escape(description)}"/><meta name="twitter:image" content="{BASE}/images/suzuka-channel.jpg"/><link rel="stylesheet" href="{p}assets/styles.css"/><link rel="stylesheet" href="{p}assets/explore.css"/><link rel="stylesheet" href="{p}assets/player.css"/><link rel="stylesheet" href="{p}assets/ai-disclosure.css"/><script type="application/ld+json">{dump(schema)}</script></head><body><main><a class="skip-link" href="#content">本文へ移動</a>{header(p)}<section class="explore-hero"><p class="section-kicker">SUZUKA / MUSIC DISCOVERY</p><h1>{h1}</h1><p>{html.escape(description)}</p><p class="ai-project-note">SUZUKAの架空のAIアーティストによるオリジナル作品を紹介しています。</p></section><div id="content">{body}</div>{footer(p)}</main><script defer src="{p}assets/main.js"></script>{js}</body></html>\n'


def catalog(root: Path) -> dict:
    cms_path = root / "assets/data/creator-cms.json"
    if cms_path.exists():
        cms = json.loads(cms_path.read_text(encoding="utf-8"))
        items = [dict(item) for item in cms["releases"] if item.get("status") == "published"]
        items.sort(key=lambda x: (x["releaseDate"], x["slug"]), reverse=True)
        upcoming = [dict(item) for item in cms.get("upcoming", []) if item.get("status") == "upcoming"]
        return {"updatedAt": cms["updatedAt"], "releases": items, "upcoming": upcoming}
    source = json.loads((root / "assets/data/release-links.json").read_text(encoding="utf-8"))
    records = {item["slug"]: item for item in source["releases"]}
    for item in NEW:
        records[item["slug"]] = {**item, "status": "published", "releaseType": "single"}
    items = []
    for slug, item in records.items():
        artist_slug = item.get("artistSlug") or "enomoto-mia"
        artist = item.get("artist", "榎本魅愛")
        artist_slugs = ["enomoto-mia", "koga-kamishiro"] if slug == "our-kingdom" else [artist_slug]
        genre, themes = OVERRIDES.get(slug, (META[artist_slug]["genres"], ["恋愛"] if artist_slug == "enomoto-mia" else ["物語"]))
        date, duration = DATES[slug]
        cover = item.get("coverImage") or item.get("image")
        desc = item.get("description") or f'{artist}「{item["title"]}」のSUZUKA公式作品ページ。'
        alt = item.get("coverAlt") or f'{artist}「{item["title"]}」公式ジャケット'
        news = item.get("newsPage") or item.get("newsUrl")
        release_path = item.get("releasePage") or f"releases/{slug}/"
        aliases = sum((META[x]["aliases"] for x in artist_slugs), [])
        items.append({
            "id": slug, "slug": slug, "title": item["title"], "displayTitle": item.get("subtitle") and f'{item["title"]}｜{item["subtitle"]}' or item["title"],
            "artist": artist, "artistSlug": artist_slug, "artistSlugs": artist_slugs, "artistType": META[artist_slug]["type"],
            "releaseDate": date, "releaseYear": int(date[:4]), "releaseType": item.get("releaseType") or "single",
            "genres": genre, "moods": META[artist_slug]["moods"], "themes": themes, "language": "ja",
            "coverImage": cover, "coverAlt": alt, "releaseUrl": release_path,
            "youtubeUrl": item["youtubeUrl"], "newsUrl": news or "", "duration": duration,
            "status": "published", "featured": slug in {"chimpanzee-no-rakuen", "ashita-wa-kitto", "heal-you-again"},
            "recommendationWeight": 2 if slug not in {"chimpanzee-no-rakuen", "ashita-wa-kitto"} else 1,
            "relatedReleases": item.get("relatedReleases", []),
            "searchKeywords": list(dict.fromkeys(aliases + genre + themes + [artist, item["title"]])),
            "aiArtistType": "fictional AI artist",
            "description": desc,
        })
    items.sort(key=lambda x: (x["releaseDate"], x["slug"]), reverse=True)
    upcoming = [{"slug": s, "title": t, "artist": a, "artistSlug": asl, "scheduledAt": dt, "status": "upcoming", "youtubeUrl": f"https://www.youtube.com/watch?v={vid}", "image": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", "note": "公式YouTubeプレミア公開予定。公開済み作品には含めていません。"} for s,t,a,asl,dt,vid in UPCOMING]
    return {"updatedAt": "2026-07-30T00:00:00+09:00", "releases": items, "upcoming": upcoming}


def search_page(data: dict) -> str:
    desc = "SUZUKAの公開作品を、曲名・アーティスト・ジャンル・テーマ・タグ・歌詞・年代・作品タイプからAI補完検索できます。"
    schema = {"@context":"https://schema.org","@graph":[{"@type":"WebPage","url":f"{BASE}/search/","name":"楽曲検索｜SUZUKA Official Music","description":desc},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"楽曲検索","item":f"{BASE}/search/"}]}]}
    body = '<section class="explore-shell"><form class="explore-toolbar" data-search-form role="search"><div class="explore-field"><label for="song-search">曲名・キーワード（AI補完）</label><input id="song-search" name="q" type="search" autocomplete="off" placeholder="恋、榎本魅愛、ECLYPSE…"/></div><div class="explore-field"><label for="artist-filter">アーティスト</label><select id="artist-filter" name="artist"><option value="">すべて</option></select></div><div class="explore-field"><label for="genre-filter">ジャンル</label><select id="genre-filter" name="genre"><option value="">すべて</option></select></div><div class="explore-field"><label for="theme-filter">テーマ</label><select id="theme-filter" name="theme"><option value="">すべて</option></select></div><div class="explore-field"><label for="year-filter">公開年</label><select id="year-filter" name="year"><option value="">すべて</option></select></div><div class="explore-field"><label for="type-filter">作品タイプ</label><select id="type-filter" name="type"><option value="">すべて</option></select></div><div class="explore-field"><label for="sort-filter">並び順</label><select id="sort-filter" name="sort"><option value="newest">新しい順</option><option value="oldest">古い順</option><option value="title">曲名順</option></select></div><button class="explore-clear" type="reset">条件をクリア</button></form><p class="explore-count" aria-live="polite">検索結果 <strong data-search-count>0</strong>件</p><div class="explore-grid" data-search-results></div><p class="explore-empty" data-search-empty hidden>条件に一致する楽曲がありません。検索語やジャンルを変更してください。</p></section>'
    return shell("search/", "楽曲検索｜SUZUKA Official Music", desc, "SEARCH", body, schema, True)


def genre_pages(root: Path, data: dict) -> None:
    cards = []
    for slug, (name, description) in GENRES.items():
        matches = [x for x in data["releases"] if name in x["genres"]]
        if not matches:
            continue
        cards.append(f'<a class="genre-card" href="./{slug}/"><img src="../{matches[0]["coverImage"]}" alt="{html.escape(matches[0]["coverAlt"])}" width="1280" height="720" loading="lazy"/><div><small>{len(matches)}作品</small><h2>{html.escape(name)}</h2><p>{html.escape(description)}</p></div></a>')
        elements = [{"@type":"ListItem","position":i,"name":x["displayTitle"],"url":f'{BASE}/{x["releaseUrl"]}',"image":f'{BASE}/{x["coverImage"]}'} for i,x in enumerate(matches,1)]
        artist_names = " / ".join(dict.fromkeys(x["artist"] for x in matches))
        grid = "".join(render_card(x, "../../") for x in matches)
        related = "".join(f'<a class="explore-tag" href="../{other}/">{html.escape(v[0])}</a>' for other,v in GENRES.items() if other != slug and any(v[0] in x["genres"] for x in data["releases"]))
        body = f'<section class="explore-shell"><p>{len(matches)}作品 · {html.escape(artist_names)}</p><div class="explore-grid">{grid}</div><h2>関連ジャンル</h2><div class="explore-tags">{related}</div><div class="explore-actions"><a href="../../search/?genre={html.escape(name)}">このジャンルを検索</a><a href="../../releases/">全Releasesを見る</a></div></section>'
        schema = {"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","url":f"{BASE}/genres/{slug}/","name":f"{name}作品｜SUZUKA Official Music","description":description},{"@type":"ItemList","numberOfItems":len(elements),"itemListElement":elements},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"Genres","item":f"{BASE}/genres/"},{"@type":"ListItem","position":3,"name":name,"item":f"{BASE}/genres/{slug}/"}]}]}
        write(root / "genres" / slug / "index.html", shell(f"genres/{slug}/", f"{name}作品｜SUZUKA Official Music", f"SUZUKAの音楽作品を{name}で紹介します。{description}", html.escape(name), body, schema))
    desc = "SUZUKAの音楽作品を、世界観とジャンルから探せます。"
    schema = {"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","url":f"{BASE}/genres/","name":"ジャンルから探す｜SUZUKA Official Music","description":desc},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"Genres","item":f"{BASE}/genres/"}]}]}
    write(root / "genres/index.html", shell("genres/", "ジャンルから探す｜SUZUKA Official Music", desc, "GENRES", f'<section class="explore-shell"><div class="genre-directory">{"".join(cards)}</div><div class="explore-actions"><a href="../search/">条件から楽曲を探す</a><a href="../releases/">全Releasesを見る</a></div></section>', schema))


def render_card(item: dict, p: str) -> str:
    news = f'<a href="{p}{item["newsUrl"]}">News</a>' if item["newsUrl"] else ""
    return f'<article class="explore-card"><img src="{p}{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/><div class="explore-card-copy"><time datetime="{item["releaseDate"]}">{item["releaseDate"].replace("-",".")}</time><h2>{html.escape(item["displayTitle"])}</h2><p>{html.escape(item["artist"])}</p><div class="explore-tags">{"".join(f"<span class=explore-tag>{html.escape(g)}</span>" for g in item["genres"])}</div><div class="explore-actions"><a href="{p}{item["releaseUrl"]}">作品ページ</a><a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式MV ↗</a>{news}</div></div></article>'


def discography_page(data: dict) -> str:
    items = data["releases"]
    timeline = []
    current = None
    for item in items:
        ym = item["releaseDate"][:7]
        if ym != current:
            if current is None or current[:4] != ym[:4]:
                timeline.append(f'<h2 class="timeline-year">{ym[:4]}</h2>')
            timeline.append(f'<h3 class="timeline-month">{int(ym[5:])}月</h3><div class="timeline-list">')
            if current is not None:
                timeline.insert(-1, "</div>")
            current = ym
        timeline.append(f'<article class="timeline-item" data-release-date="{item["releaseDate"]}"><time datetime="{item["releaseDate"]}">{item["releaseDate"][5:].replace("-",".")}</time><img src="../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/><div><h3>{html.escape(item["displayTitle"])}</h3><p>{html.escape(item["artist"])} · {" / ".join(map(html.escape,item["genres"]))}</p></div><a href="../{item["releaseUrl"]}">作品を見る ↗</a></article>')
    timeline.append("</div>")
    upcoming = "".join(f'<li><time datetime="{x["scheduledAt"]}">{x["scheduledAt"][:10].replace("-",".")} 20:00</time> {html.escape(x["artist"])}「{html.escape(x["title"])}」 <a href="{x["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">予約動画 ↗</a></li>' for x in data["upcoming"])
    elements = [{"@type":"ListItem","position":i,"name":x["displayTitle"],"url":f'{BASE}/{x["releaseUrl"]}'} for i,x in enumerate(items,1)]
    desc = "SUZUKA所属アーティストが発表した作品を、公開日順に紹介します。"
    schema = {"@context":"https://schema.org","@graph":[{"@type":"CollectionPage","url":f"{BASE}/discography/","name":"ディスコグラフィー｜SUZUKA Official Music","description":desc},{"@type":"ItemList","numberOfItems":len(items),"itemListElement":elements},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"Discography","item":f"{BASE}/discography/"}]}]}
    body = f'<section class="explore-shell"><div class="discography-controls" aria-label="並び順"><button type="button" aria-pressed="true" data-timeline-sort="newest">新しい順</button><button type="button" aria-pressed="false" data-timeline-sort="oldest">古い順</button></div><div data-timeline>{"".join(timeline)}</div><section class="upcoming-timeline"><p class="section-kicker">UPCOMING</p><h2>公開予定</h2><p>公開済み年表とは分けて表示しています。</p><ul>{upcoming}</ul></section></section><script>document.querySelectorAll("[data-timeline-sort]").forEach(b=>b.addEventListener("click",()=>{{document.querySelectorAll("[data-timeline-sort]").forEach(x=>x.setAttribute("aria-pressed",x===b));const root=document.querySelector("[data-timeline]");const cards=[...root.querySelectorAll(".timeline-item")].sort((a,c)=>(b.dataset.timelineSort==="oldest"?1:-1)*a.dataset.releaseDate.localeCompare(c.dataset.releaseDate));cards.forEach(x=>root.append(x))}}))</script>'
    return shell("discography/", "ディスコグラフィー｜SUZUKA Official Music", desc, "DISCOGRAPHY", body, schema)


def release_page(item: dict) -> str:
    page = f"{BASE}/{item['releaseUrl']}"
    p = "../../"
    graph = {"@context":"https://schema.org","@graph":[{"@type":"WebPage","@id":page,"url":page,"name":f"{item['title']}｜{item['artist']}｜SUZUKA","description":item["description"]},{"@type":"MusicRecording","@id":f"{page}#recording","name":item["title"],"url":page,"datePublished":item["releaseDate"],"duration":f'PT{item["duration"]//60}M{item["duration"]%60}S',"image":f'{BASE}/{item["coverImage"]}',"description":item["description"],"byArtist":{"@type":item["artistType"],"name":item["artist"],"description":"SUZUKAのオリジナルAI音楽プロジェクトに登場する架空のAIアーティストです。"}},{"@type":"VideoObject","@id":f"{page}#video","name":f'{item["title"]} Official Video',"description":item["description"],"thumbnailUrl":f'https://i.ytimg.com/vi/{item["youtubeUrl"].split("=")[-1]}/maxresdefault.jpg',"uploadDate":item["releaseDate"],"duration":f'PT{item["duration"]//60}M{item["duration"]%60}S',"embedUrl":f'https://www.youtube.com/embed/{item["youtubeUrl"].split("=")[-1]}',"contentUrl":item["youtubeUrl"]},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"Releases","item":f"{BASE}/releases/"},{"@type":"ListItem","position":3,"name":item["title"],"item":page}]}]}
    tags = "".join(f'<a class="explore-tag" href="../../search/?genre={html.escape(g)}">{html.escape(g)}</a>' for g in item["genres"])
    related = "".join(f'<a href="../{x}/">{html.escape(x.replace("-"," "))} ↗</a>' for x in ("mia","shadow-code","my-queen-my-oath"))
    return f'<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{html.escape(item["title"])}｜{html.escape(item["artist"])}｜SUZUKA Official Music</title><meta name="description" content="{html.escape(item["description"])}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="music.song"/><meta property="og:title" content="{html.escape(item["title"])}｜{html.escape(item["artist"])}"/><meta property="og:description" content="{html.escape(item["description"])}"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{BASE}/{item["coverImage"]}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{BASE}/{item["coverImage"]}"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/official-release.css"/><link rel="stylesheet" href="../../assets/explore.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{dump(graph)}</script></head><body><main>{header(p)}<section class="release-detail-hero"><div class="release-detail-copy"><p>OFFICIAL RELEASE · {item["releaseDate"]}</p><h1>{html.escape(item["title"])}</h1><p>{html.escape(item["description"])}</p><div class="explore-actions"><a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式MVを見る ↗</a><a href="../../artists/{item["artistSlug"]}/">アーティストを見る</a></div></div><div class="release-detail-artwork"><img src="../../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720"/></div></section><section class="release-detail-video"><iframe src="https://www.youtube-nocookie.com/embed/{item["youtubeUrl"].split("=")[-1]}" title="{html.escape(item["title"])} Official Video" loading="lazy" allowfullscreen></iframe></section><section class="release-related-section"><h2>関連作品</h2><div class="explore-actions">{related}</div></section><section class="release-genre-tags"><strong>GENRES / THEMES</strong>{tags}</section><section class="social-context-section" aria-label="作品の関連リンク"><h2>作品をもっと楽しむ</h2><div class="explore-actions"><a href="../../news/{item["slug"]}-release/">Newsを読む</a><a href="../../social/">公式SNS・リンク</a><a href="../../search/?artist={item["artistSlug"]}">同じアーティストの曲を探す</a></div></section><aside class="ai-work-disclosure">本作品は、SUZUKAのオリジナルAIアーティストによる架空の音楽プロジェクト作品です。</aside>{footer(p)}</main><script defer src="../../assets/main.js"></script></body></html>\n'


def news_page(item: dict) -> str:
    page = f"{BASE}/news/{item['slug']}-release/"
    p = "../../"
    news_desc = f'{item["artist"]}「{item["title"]}」の公開情報。公式MV、作品ページ、アーティスト情報を紹介します。'
    graph = {"@context":"https://schema.org","@graph":[{"@type":["NewsArticle","Article"],"headline":f'{item["artist"]}「{item["title"]}」公開',"datePublished":item["releaseDate"],"mainEntityOfPage":page,"image":f'{BASE}/{item["coverImage"]}',"description":news_desc},{"@type":"WebPage","url":page,"name":f'{item["artist"]}「{item["title"]}」公開｜SUZUKA News',"description":news_desc},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"{BASE}/"},{"@type":"ListItem","position":2,"name":"News","item":f"{BASE}/news/"},{"@type":"ListItem","position":3,"name":item["title"],"item":page}]}]}
    return f'<!doctype html><html lang="ja"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{html.escape(item["artist"])}「{html.escape(item["title"])}」公開｜SUZUKA News</title><meta name="description" content="{html.escape(news_desc)}"/><meta name="robots" content="index, follow"/><link rel="canonical" href="{page}"/><meta property="og:type" content="article"/><meta property="og:title" content="{html.escape(item["artist"])}「{html.escape(item["title"])}」公開"/><meta property="og:url" content="{page}"/><meta property="og:image" content="{BASE}/{item["coverImage"]}"/><meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{BASE}/{item["coverImage"]}"/><link rel="stylesheet" href="../../assets/styles.css"/><link rel="stylesheet" href="../../assets/news-feature.css"/><link rel="stylesheet" href="../../assets/explore.css"/><link rel="stylesheet" href="../../assets/player.css"/><link rel="stylesheet" href="../../assets/ai-disclosure.css"/><script type="application/ld+json">{dump(graph)}</script></head><body><main>{header(p)}<article class="news-article"><header class="news-article-hero"><p>OFFICIAL RELEASE · {item["releaseDate"]}</p><h1>{html.escape(item["artist"])}<br/>「{html.escape(item["title"])}」公開</h1><p>{html.escape(item["description"])}</p><p class="ai-news-disclosure">SUZUKAのオリジナルAIアーティストによる公式リリース情報です。</p></header><div class="news-article-body"><section><img src="../../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/><div class="explore-actions"><a href="../../releases/{item["slug"]}/">作品ページ</a><a href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式MV ↗</a><a href="../../artists/{item["artistSlug"]}/">Artist</a></div></section><section class="social-context-section" aria-label="関連リンク"><h2>作品の関連情報</h2><div class="explore-actions"><a href="../../releases/{item["slug"]}/">作品ページ</a><a href="../../social/">公式SNS・リンク</a><a href="../../artists/{item["artistSlug"]}/">アーティストページ</a></div></section></div></article>{footer(p)}</main><script defer src="../../assets/main.js"></script></body></html>\n'


def upsert_card(path: Path, item: dict, p: str) -> None:
    text = path.read_text(encoding="utf-8")
    href = f'{p}releases/{item["slug"]}/'
    if href in text:
        return
    card = f'<article class="release-card release-card-new"><a class="release-image" href="{href}"><img src="{p}{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/></a><div class="release-info"><div class="release-row"><span>01</span><span>OFFICIAL RELEASE · {item["releaseDate"]}</span></div><h3>{html.escape(item["title"])}</h3><p>{html.escape(item["description"])}</p><p class="release-artist-credit">{html.escape(item["artist"])}</p><div class="release-card-actions"><a class="release-card-cta release-card-cta-detail" href="{href}">詳細を見る ↗</a><a class="release-card-cta" href="{item["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">MVを見る ↗</a></div></div></article>'
    text = text.replace('<div class="release-grid">', '<div class="release-grid">' + card, 1)
    path.write_text(text, encoding="utf-8")


def update_directories(root: Path, data: dict) -> None:
    newest = [next(x for x in data["releases"] if x["slug"] == slug) for slug in ("chimpanzee-no-rakuen", "ashita-wa-kitto")]
    news_path = root / "news/index.html"
    news = news_path.read_text(encoding="utf-8")
    for item in reversed(newest):
        href = f'./{item["slug"]}-release/'
        if href not in news:
            card = f'<article class="news-directory-card"><a href="{href}"><span class="news-directory-image"><img src="../{item["coverImage"]}" alt="{html.escape(item["title"])}公開News" width="1280" height="720" loading="lazy"/></span><span class="news-directory-meta"><time datetime="{item["releaseDate"]}">{item["releaseDate"].replace("-",".")}</time><em>OFFICIAL RELEASE</em></span><h2>{html.escape(item["artist"])}「{html.escape(item["title"])}」公開</h2><p>{html.escape(item["description"])}</p><b>記事を読む ↗</b></a></article>'
            news = news.replace('<div class="news-list news-feature-list">', '<div class="news-list news-feature-list">' + card, 1)
    news_path.write_text(news, encoding="utf-8")
    social_path = root / "social/index.html"
    social = social_path.read_text(encoding="utf-8")
    for item in reversed(newest):
        href = f'../releases/{item["slug"]}/'
        if href not in social:
            card = f'<a class="social-hub-card" href="{href}"><img src="../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/><div><small>{html.escape(item["artist"])} · OFFICIAL MV</small><strong>{html.escape(item["title"])}</strong><span>作品と公式MVを見る →</span></div></a>'
            social = social.replace('<div class="social-hub-grid">', '<div class="social-hub-grid">' + card, 1)
    social_path.write_text(social, encoding="utf-8")
    artists_path = root / "artists/index.html"
    artists = artists_path.read_text(encoding="utf-8")
    artists = re.sub(
        r'(<article class="artist-directory-card )artist-coming-soon-card("[^>]*>.*?<a href="\.\./artists/nox/".*?<span class="coming-soon-badge">)Coming Soon(</span>.*?<p class="artist-directory-genre">)公開作品 0(</p>)',
        r'\1\2NOW ACTIVE\3公開作品 1\4',
        artists,
        count=1,
        flags=re.DOTALL,
    )
    artists_path.write_text(artists, encoding="utf-8")
    mia = root / "artists/enomoto-mia/index.html"
    text = mia.read_text(encoding="utf-8")
    item = next(x for x in data["releases"] if x["slug"] == "ashita-wa-kitto")
    if "../../releases/ashita-wa-kitto/" not in text:
        row = f'<a class="artist-track-row artist-track-row-new" href="../../releases/ashita-wa-kitto/"><span>01</span><img src="../../{item["coverImage"]}" alt="{html.escape(item["coverAlt"])}" width="1280" height="720" loading="lazy"/><div><strong>{html.escape(item["title"])}</strong><small>Official release · {item["releaseDate"]}</small></div><b aria-hidden="true">↗</b></a>'
        text = text.replace('<div class="artist-track-list">', '<div class="artist-track-list">' + row, 1)
    track_list = re.search(r'<div class="artist-track-list">.*?</div>\s*</section>', text, re.DOTALL)
    if track_list:
        number = 0
        def renumber(match: re.Match[str]) -> str:
            nonlocal number
            number += 1
            return f"{match.group(1)}{number:02d}{match.group(2)}"
        updated = re.sub(r'(<a class="artist-track-row[^"]*"[^>]*><span>)\d+(</span>)', renumber, track_list.group(0))
        text = text[:track_list.start()] + updated + text[track_list.end():]
    text = re.sub(r'(公開作品\s*)15', r'\g<1>16', text)
    mia.write_text(text, encoding="utf-8")


def update_docs(root: Path, data: dict) -> None:
    path = root / "docs/youtube/youtube-seo-master.md"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        marker = "## 2026-07-30 公式公開確認"
        published = [x for x in data["releases"] if x["slug"] in {"ashita-wa-kitto", "chimpanzee-no-rakuen"}]
        rows = "\n".join(f'| 公開済み | {x["title"]} | {x["artist"]} | {x["releaseDate"]} | {x["duration"]//60}:{x["duration"]%60:02d} | {x["youtubeUrl"]} |' for x in published)
        upcoming = "\n".join(f'| 公開予定 | {x["title"]} | {x["artist"]} | {x["scheduledAt"].replace("T"," ")} | 未確定 | {x["youtubeUrl"]} |' for x in data["upcoming"])
        section = f"""{marker}

公式チャンネル `UCVde75yhByGQMu3SkO-fzrA` を一次情報として、一般視聴可否・公開日・時間を確認。

| 状態 | 作品 | アーティスト | 公開日／予定 | 時間 | 正式URL |
| --- | --- | --- | --- | --- | --- |
{rows}
{upcoming}

予約中の作品は公開済み作品数・MusicRecordingへ含めない。
"""
        if marker in text:
            text = text[:text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    note = "\n- `assets/data/releases-catalog.json`：検索・ジャンル・年表・Weekly Pickが共通利用する公開作品の正本\n- `search/` / `genres/` / `discography/`：作品を探すための静的ページ\n- `scripts/build_explore_catalog.py`：正本データと探索ページを再生成するスクリプト"
    if "releases-catalog.json" not in text:
        text = text.replace("- `robots.txt` / `sitemap.xml`：検索エンジン向けファイル", "- `robots.txt` / `sitemap.xml`：検索エンジン向けファイル" + note)
    readme.write_text(text, encoding="utf-8")


def inject_shared(root: Path, data: dict) -> None:
    for path in root.glob("**/index.html"):
        text = path.read_text(encoding="utf-8")
        p = prefix(path)
        text = re.sub(r'(?:\.\./){6,10}(?=(?:assets/explore\.css|search/|genres/|discography/))', p, text)
        if "assets/explore.css" not in text:
            text = text.replace("</head>", f'<link rel="stylesheet" href="{p}assets/explore.css"/></head>', 1)
        for nav_match in list(re.finditer(r'<nav class="(?:desktop-nav|site-footer-nav)"[^>]*>(.*?)</nav>', text, re.DOTALL))[::-1]:
            block = nav_match.group(0)
            if "search/" in block:
                continue
            links = f'<a href="{p}search/">Search</a><a href="{p}genres/">Genres</a><a href="{p}discography/">Discography</a>'
            text = text[:nav_match.end()-6] + links + text[nav_match.end()-6:]
        if path.parts[-3:-2] == ("artists",) and path.parent.name in META and "artist-explore-links" not in text:
            slug = path.parent.name
            count = sum(slug in x["artistSlugs"] for x in data["releases"])
            genres = sorted({g for x in data["releases"] if slug in x["artistSlugs"] for g in x["genres"]})
            links = f'<nav class="artist-explore-links" aria-label="このアーティストの作品を探す"><a href="../../search/?artist={slug}">このアーティストの曲を検索（{count}作品）</a><a href="../../discography/">ディスコグラフィー</a>{"".join(f"""<a href="../../search/?genre={html.escape(g)}">{html.escape(g)}</a>""" for g in genres[:3])}</nav>'
            text = text.replace("</main>", links + "</main>", 1)
        if path.parts[-3:-2] == ("releases",) and path.parent.name != "toriatsukai-chuui":
            item = next((x for x in data["releases"] if x["slug"] == path.parent.name), None)
            if item and "release-genre-tags" not in text:
                tags = "".join(f'<a class="explore-tag" href="../../search/?genre={html.escape(g)}">{html.escape(g)}</a>' for g in item["genres"])
                text = text.replace('<aside class="ai-work-disclosure"', f'<section class="release-genre-tags"><strong>GENRES / THEMES</strong>{tags}</section><aside class="ai-work-disclosure"', 1)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    ROOT = parser.parse_args().root.resolve()
    data = catalog(ROOT)
    write(ROOT / "assets/data/releases-catalog.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    release_links = json.loads((ROOT / "assets/data/release-links.json").read_text(encoding="utf-8"))
    existing = {x["slug"]: x for x in release_links["releases"]}
    generated_links = []
    for item in data["releases"]:
        previous = existing.get(item["slug"], {})
        generated_links.append({
            **previous,
            "slug": item["slug"],
            "title": item["title"],
            "artist": item["artist"],
            "artistSlug": item["artistSlug"],
            "coverImage": item["coverImage"],
            "coverAlt": item["coverAlt"],
            "youtubeUrl": item["youtubeUrl"],
            "shortsUrl": item.get("shortsUrl", previous.get("shortsUrl", "")),
            "newsPage": item.get("newsUrl", ""),
            "description": item["description"],
            "status": "published",
            "releaseType": item.get("releaseType", "single"),
            "publishedDate": item["releaseDate"],
            "duration": item.get("duration", 0),
            "releasePage": item["releaseUrl"],
            "playerEnabled": previous.get("playerEnabled", False),
            "youtubeStatus": "published",
            "newsStatus": "published" if item.get("newsUrl") else "unconfirmed",
            "shortsStatus": "published" if item.get("shortsUrl") else "unconfirmed",
        })
    release_links["updatedAt"] = data["updatedAt"][:10]
    release_links["releases"] = generated_links
    write(ROOT / "assets/data/release-links.json", json.dumps(release_links, ensure_ascii=False, indent=2) + "\n")
    write(ROOT / "assets/data/upcoming-releases.json", json.dumps({"updatedAt":"2026-07-30T00:00:00+09:00","releases":data["upcoming"]}, ensure_ascii=False, indent=2) + "\n")
    write(ROOT / "search/index.html", search_page(data))
    genre_pages(ROOT, data)
    write(ROOT / "discography/index.html", discography_page(data))
    for item in data["releases"]:
        release_path = ROOT / item["releaseUrl"] / "index.html"
        if not release_path.exists():
            write(release_path, release_page(item))
        if item.get("newsUrl"):
            news_path = ROOT / item["newsUrl"] / "index.html"
            if not news_path.exists():
                write(news_path, news_page(item))
    for slug in ("ashita-wa-kitto", "chimpanzee-no-rakuen"):
        item = next(x for x in data["releases"] if x["slug"] == slug)
        write(ROOT / item["releaseUrl"] / "index.html", release_page(item))
        write(ROOT / "news" / f"{slug}-release/index.html", news_page(item))
        upsert_card(ROOT / "index.html", item, "./")
        upsert_card(ROOT / "releases/index.html", item, "../")
    home = ROOT / "index.html"
    text = home.read_text(encoding="utf-8")
    if 'data-weekly-pick' not in text:
        fallback = next(x for x in data["releases"] if x["slug"] == "mia")
        weekly = f'<section class="weekly-pick" data-weekly-pick><div class="weekly-pick-grid"><img src="./{fallback["coverImage"]}" alt="{html.escape(fallback["coverAlt"])}" width="1280" height="720" loading="lazy"/><div><p class="section-kicker">WEEKLY PICK / 今週のおすすめ曲</p><h2 data-pick-title>{html.escape(fallback["title"])}</h2><strong data-pick-artist>{html.escape(fallback["artist"])}</strong><p data-pick-description>{html.escape(fallback["description"])}</p><p data-pick-genres>{" · ".join(fallback["genres"])}</p><div class="explore-actions"><a data-pick-release href="./{fallback["releaseUrl"]}">作品ページ</a><a data-pick-youtube href="{fallback["youtubeUrl"]}" target="_blank" rel="noopener noreferrer">公式MV ↗</a><a data-pick-news href="./{fallback["newsUrl"]}">News</a><a href="./search/">ほかの曲を探す</a></div></div></div></section>'
        text = text.replace('<section class="section about-section', weekly + '<section class="section about-section', 1)
    if 'data-catalog-url' not in text:
        text = text.replace("<html lang=\"ja\">", '<html lang="ja" data-catalog-url="./assets/data/releases-catalog.json" data-site-base="./">', 1)
    if 'assets/explore.js' not in text:
        text = text.replace("</body>", '<script defer src="./assets/explore.js"></script></body>', 1)
    if 'class="explore-links home-explore-links"' not in text:
        text = text.replace("</footer>", '<nav class="explore-links home-explore-links" aria-label="音楽を探す"><a href="./search/">楽曲を探す</a><a href="./genres/">ジャンル</a><a href="./genres/j-pop/">J-POP</a><a href="./genres/enka/">演歌</a><a href="./genres/k-pop-inspired/">K-POP風</a><a href="./genres/visual-kei/">V系</a><a href="./discography/">ディスコグラフィー</a><a href="./news/ashita-wa-kitto-release/">「明日は、きっと。」News</a><a href="./news/chimpanzee-no-rakuen-release/">「チンパンジーの楽園」News</a></nav></footer>', 1)
    home.write_text(text, encoding="utf-8")
    rel = ROOT / "releases/index.html"
    text = rel.read_text(encoding="utf-8")
    if "explore-links" not in text:
        text = text.replace('<section class="section releases-section', '<nav class="explore-links" aria-label="作品の探し方"><a href="../search/">条件から探す</a><a href="../genres/">ジャンルから探す</a><a href="../discography/">公開順でたどる</a></nav><section class="section releases-section', 1)
    rel.write_text(text, encoding="utf-8")
    nox = ROOT / "artists/nox/index.html"
    text = nox.read_text(encoding="utf-8").replace("Coming Soon", "NOW ACTIVE").replace("DEBUT PREPARATION", "DEBUT RELEASE").replace("公開予定", "公開済み")
    if "../../releases/chimpanzee-no-rakuen/" not in text:
        text = text.replace("</main>", '<nav class="artist-explore-links"><a href="../../releases/chimpanzee-no-rakuen/">チンパンジーの楽園を見る</a><a href="https://www.youtube.com/watch?v=EJJLBOo103I" target="_blank" rel="noopener noreferrer">公式MV ↗</a></nav></main>', 1)
    nox.write_text(text, encoding="utf-8")
    update_directories(ROOT, data)
    update_docs(ROOT, data)
    inject_shared(ROOT, data)
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().with_name("build_explorer_update.py")), "--root", str(ROOT)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().with_name("build_creator_platform.py")), "--root", str(ROOT)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().with_name("validate_sitemap.py")), "--root", str(ROOT), "--write"],
        cwd=ROOT,
        check=True,
    )
    print(f"Generated exploration catalog with {len(data['releases'])} published releases and {len(data['upcoming'])} upcoming releases.")


if __name__ == "__main__":
    main()

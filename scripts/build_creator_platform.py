#!/usr/bin/env python3
"""Generate SUZUKA Creator Platform 3.0 from creator-cms.json."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from datetime import date
from pathlib import Path

from build_explorer_update import BASE, card, dump, matches_rule, shell, write
from structured_data_dates import apply_evidence_to_cms, normalize as normalize_structured_dates

GA4_MEASUREMENT_ID = "G-LS3PCRB60D"


def marker_upsert(path: Path, name: str, content: str, anchor: str = "</main>") -> None:
    text = path.read_text(encoding="utf-8")
    block = f"<!-- CREATOR:{name}:START -->{content}<!-- CREATOR:{name}:END -->"
    pattern = rf"<!-- CREATOR:{re.escape(name)}:START -->.*?<!-- CREATOR:{re.escape(name)}:END -->"
    if re.search(pattern, text, flags=re.DOTALL):
        text = re.sub(pattern, block, text, flags=re.DOTALL)
    elif anchor in text:
        text = text.replace(anchor, block + anchor, 1)
    path.write_text(text, encoding="utf-8")


def deterministic_recommendations(releases: list[dict]) -> dict[str, dict[str, list[str]]]:
    """Score related works without randomness, with stable slug tie-breaking."""
    result: dict[str, dict[str, list[str]]] = {}
    for current in releases:
        others = [item for item in releases if item["slug"] != current["slug"]]
        same_artist = [x for x in others if x["artistSlug"] == current["artistSlug"]]
        same_genre = [x for x in others if set(x.get("genres", [])) & set(current.get("genres", []))]
        same_theme = [x for x in others if set(x.get("themes", [])) & set(current.get("themes", []))]
        popular = sorted(others, key=lambda x: (-int(x.get("recommendationWeight", 0)), x["slug"]))
        recent = sorted(others, key=lambda x: (x["releaseDate"], x["slug"]), reverse=True)

        def score(item: dict) -> tuple[int, str]:
            value = int(item.get("recommendationWeight", 0))
            value += 30 * len(set(item.get("genres", [])) & set(current.get("genres", [])))
            value += 24 * len(set(item.get("themes", [])) & set(current.get("themes", [])))
            value += 18 if item["artistSlug"] == current["artistSlug"] else 0
            value += max(0, 12 - abs((date.fromisoformat(item["releaseDate"]) - date.fromisoformat(current["releaseDate"])).days))
            return (-value, item["slug"])

        ranked = sorted(others, key=score)
        result[current["slug"]] = {
            "sameArtist": [x["slug"] for x in same_artist[:6]],
            "sameGenre": [x["slug"] for x in sorted(same_genre, key=score)[:6]],
            "sameTheme": [x["slug"] for x in sorted(same_theme, key=score)[:6]],
            "popular": [x["slug"] for x in popular[:6]],
            "recent": [x["slug"] for x in recent[:6]],
            "aiRecommended": [x["slug"] for x in ranked[:6]],
        }
    return result


def recommendation_pages(root: Path, releases: list[dict], recommendations: dict) -> None:
    by_slug = {item["slug"]: item for item in releases}
    labels = (
        ("aiRecommended", "AIおすすめ"),
        ("sameGenre", "同ジャンル"),
        ("sameTheme", "同テーマ"),
        ("sameArtist", "同アーティスト"),
        ("popular", "人気作品"),
        ("recent", "最近公開"),
    )
    for item in releases:
        sections = []
        for key, label in labels:
            works = [by_slug[slug] for slug in recommendations[item["slug"]][key] if slug in by_slug][:3]
            if works:
                sections.append(
                    f'<section class="creator-rec-group"><h3>{label}</h3>'
                    f'<div class="explorer-card-grid">{"".join(card(x, "../../") for x in works)}</div></section>'
                )
        body = (
            '<section class="creator-recommendations"><p class="section-kicker">RECOMMENDATION ENGINE</p>'
            '<h2>この作品から広がるおすすめ</h2><p>ジャンル、テーマ、アーティスト、公開日、人気度を使って決定的に選出しています。</p>'
            + "".join(sections) + "</section>"
        )
        page = root / item["releaseUrl"] / "index.html"
        if page.exists():
            marker_upsert(page, "RECOMMENDATIONS", body)


def playlist_items(definition: dict, releases: list[dict]) -> list[dict]:
    items = [item for item in releases if matches_rule(item, definition.get("rule", definition.get("match", {})))]
    if definition["slug"] == "popular":
        items = sorted(items or releases, key=lambda x: (-int(x.get("recommendationWeight", 0)), x["slug"]))
    elif definition["slug"] == "latest":
        items = sorted(items or releases, key=lambda x: (x["releaseDate"], x["slug"]), reverse=True)
    elif definition["slug"] in {"with-mv", "music-videos"}:
        items = [x for x in releases if x.get("youtubeUrl")]
    else:
        items = sorted(items, key=lambda x: (
            -int(x.get("playlistPriority", 0)),
            -int(x.get("recommendationWeight", 0)),
            x["slug"],
        ))
    return items[:20]


def playlists(root: Path, cms: dict, releases: list[dict]) -> list[dict]:
    generated = []
    index_cards = []
    for definition in cms["playlistDefinitions"]:
        definition = {
            **definition,
            "name": definition.get("name", definition.get("label", definition["slug"])),
            "description": definition.get("description", f'{definition.get("label", definition["slug"])}をテーマに選んだSUZUKA作品。'),
        }
        items = playlist_items(definition, releases)
        generated.append({**definition, "releaseSlugs": [x["slug"] for x in items], "count": len(items)})
        index_cards.append(
            f'<article class="creator-link-card"><p>{len(items)} TRACKS</p><h2>{html.escape(definition["name"])}</h2>'
            f'<p>{html.escape(definition["description"])}</p><a href="./{definition["slug"]}/">プレイリストを見る</a></article>'
        )
        cards = "".join(card(item, "../../", rank) for rank, item in enumerate(items, 1))
        empty = '<p class="creator-empty">該当作品は今後追加予定です。</p>' if not items else ""
        graph = [{
            "@type": "ItemList",
            "name": definition["name"],
            "numberOfItems": len(items),
            "itemListElement": [
                {"@type": "ListItem", "position": n, "url": f"{BASE}/{item['releaseUrl']}", "name": item["title"]}
                for n, item in enumerate(items, 1)
            ],
        }]
        body = (
            f'<section class="creator-copy"><p>{html.escape(definition["description"])}</p>'
            '<div class="explore-actions"><a href="../../search/">条件を変えて検索</a>'
            '<a href="../../rankings/">ランキング</a><a href="../../features/">特集</a></div></section>'
            f'<section class="explorer-card-grid">{cards}</section>{empty}'
        )
        write(
            root / f"playlists/{definition['slug']}/index.html",
            shell(f"playlists/{definition['slug']}/", f"{definition['name']}｜SUZUKA Playlist", definition["description"],
                  definition["name"], body, graph, ("playlists", "Playlists")),
        )
    index_graph = [{
        "@type": "ItemList",
        "numberOfItems": len(generated),
        "itemListElement": [
            {"@type": "ListItem", "position": n, "url": f"{BASE}/playlists/{x['slug']}/", "name": x["name"]}
            for n, x in enumerate(generated, 1)
        ],
    }]
    write(
        root / "playlists/index.html",
        shell("playlists/", "Playlists｜SUZUKA", "気分やテーマから選べるAIアーティスト作品のプレイリスト。",
              "Playlists", f'<section class="creator-link-grid">{"".join(index_cards)}</section>', index_graph),
    )
    write(root / "assets/data/playlists.json", json.dumps({"updatedAt": cms["updatedAt"], "playlists": generated}, ensure_ascii=False, indent=2) + "\n")
    return generated


def universe(root: Path, cms: dict, releases: list[dict]) -> None:
    artists = cms["artists"]
    universe_data = cms["universe"]
    overview = universe_data.get("overview", universe_data.get("story", "SUZUKAの作品とアーティストが形づくる音楽世界。"))
    ai_project = universe_data.get("aiProject", cms["site"]["description"])
    future_value = universe_data.get("future", [])
    future = "、".join(future_value) if isinstance(future_value, list) else str(future_value)
    newest = sorted(releases, key=lambda x: (x["releaseDate"], x["slug"]), reverse=True)
    artist_cards = "".join(
        f'<article class="creator-universe-node"><img src="../{a["image"]}" alt="{html.escape(a["name"])}の代表画像" loading="lazy"/>'
        f'<h3>{html.escape(a["name"])}</h3><p>{html.escape(a["world"])}</p><strong>{html.escape(a["music"])}</strong>'
        f'<a href="../artists/{a["slug"]}/">アーティストページ</a></article>' for a in artists
    )
    timeline = "".join(
        f'<li><time datetime="{x["releaseDate"]}">{x["releaseDate"]}</time><a href="../{x["releaseUrl"]}">{html.escape(x["title"])}</a>'
        f'<span>{html.escape(x["artist"])}</span></li>' for x in sorted(releases, key=lambda x: x["releaseDate"])
    )
    terms = "".join(f'<li><strong>{html.escape(x["term"])}</strong><span>{html.escape(x["description"])}</span></li>' for x in cms["wiki"]["terms"])
    representative = "".join(card(x, "../") for x in sorted(releases, key=lambda x: (-int(x.get("recommendationWeight", 0)), x["slug"]))[:7])
    map_nodes = "".join(f'<a class="creator-map-node" href="../artists/{a["slug"]}/">{html.escape(a["name"])}</a>' for a in artists)
    graph = [
        {"@type": "ItemList", "name": "SUZUKA artists", "itemListElement": [
            {"@type": "ListItem", "position": n, "url": f"{BASE}/artists/{a['slug']}/", "name": a["name"]}
            for n, a in enumerate(artists, 1)
        ]},
    ]
    body = f"""
<section class="creator-copy"><h2>SUZUKAとは</h2><p>{html.escape(overview)}</p>
<h2>AI音楽プロジェクト</h2><p>{html.escape(ai_project)}</p></section>
<section><p class="section-kicker">WORLD TIMELINE</p><h2>世界年表</h2><ol class="creator-timeline">{timeline}</ol></section>
<section><p class="section-kicker">RELATIONSHIP</p><h2>アーティスト相関図</h2>
<p>同じSUZUKA世界で、恋愛・誓い・闇・祝祭・記憶・再生の物語が互いに響き合います。</p>
<div class="creator-map" aria-label="アーティスト相関図">{map_nodes}</div></section>
<section><h2>作品相関図・世界MAP</h2><p>作品はジャンルとテーマを接点に結ばれ、各アーティストの領域を横断します。</p>
<div class="creator-link-grid"><a class="creator-link-card" href="../genres/">ジャンルMAP</a>
<a class="creator-link-card" href="../features/">テーマMAP</a><a class="creator-link-card" href="../wiki/timeline/">公開年表</a></div></section>
<section><p class="section-kicker">STORY</p><h2>ストーリーとアーティスト</h2><div class="creator-universe-grid">{artist_cards}</div></section>
<section><h2>キーワード・用語</h2><ul class="creator-term-list">{terms}</ul></section>
<section><h2>代表作品・おすすめ順</h2><div class="explorer-card-grid">{representative}</div></section>
<section><h2>今後追加予定</h2><p>{html.escape(future)}</p></section>"""
    write(root / "universe/index.html", shell("universe/", "SUZUKA Universe 2.0｜世界観", "AI音楽プロジェクトSUZUKAの世界観、相関図、年表、物語。",
                                             "SUZUKA Universe 2.0", body, graph, page_type="WebPage"))


def community(root: Path, releases: list[dict]) -> None:
    options = "".join(f'<option value="{html.escape(x["slug"])}">{html.escape(x["title"])} / {html.escape(x["artist"])}</option>' for x in releases)
    graph = [{"@type": "WebPage", "name": "SUZUKA Community"}]
    body = f"""
<section class="creator-copy"><h2>みんなで選ぶSUZUKA</h2><p>人気投票、アンケート、おすすめ曲、コメントを端末内で楽しめるコミュニティ試行版です。</p>
<p class="creator-notice">入力内容はこの端末のブラウザだけに保存され、外部サーバーへ送信されません。</p></section>
<section class="creator-form-grid">
<form data-community-form="vote"><h2>人気投票</h2><label>おすすめ曲<select name="release" required>{options}</select></label><button>この端末で投票</button><p data-community-result="vote"></p></form>
<form data-community-form="survey"><h2>アンケート</h2><label>今後聴きたいテーマ<input name="theme" maxlength="80" required/></label><button>回答を保存</button><p data-community-result="survey"></p></form>
<form data-community-form="recommend"><h2>おすすめ曲</h2><label>曲<select name="release" required>{options}</select></label><label>おすすめ理由<textarea name="reason" maxlength="240"></textarea></label><button>おすすめを保存</button><p data-community-result="recommend"></p></form>
<form data-community-form="comment"><h2>コメント募集</h2><label>コメント<textarea name="comment" maxlength="240" required></textarea></label><button>コメントを保存</button><p data-community-result="comment"></p></form>
</section>
<section><h2>月間ランキング</h2><ol data-community-ranking class="creator-ranking-list"></ol></section>
<section><h2>イベント</h2><p>オンライン企画や投票イベントを追加できるイベント枠です。現在、公開中のイベントはありません。</p></section>"""
    page = shell("community/", "Community｜SUZUKA", "AIアーティストSUZUKAの人気投票、アンケート、おすすめ曲コミュニティ。",
                 "Community", body, graph, page_type="WebPage")
    page = page.replace("</body>", '<script defer src="../assets/creator-platform.js"></script></body>')
    write(root / "community/index.html", page)


def admin_pages(root: Path, cms: dict) -> None:
    fields = [
        "アーティスト", "作品", "News", "ジャケット", "MV", "Shorts", "Gallery", "Universe", "Wiki",
        "ジャンル", "テーマ", "タグ", "歌詞", "紹介文", "公開日時", "YouTube", "Instagram", "検索キーワード",
        "関連作品", "英語表記", "JSON-LD", "SEO", "Feed",
    ]
    field_html = "".join(f"<li>{x}</li>" for x in fields)
    raw = html.escape(json.dumps(cms, ensure_ascii=False, indent=2))
    body = f"""
<section class="creator-copy"><h2>Creator CMS</h2><p>公開サイトの正本データを編集し、検証済みJSONとして書き出します。</p>
<p class="creator-notice">GitHub Pages上では安全なリポジトリ書き込みを行いません。JSONをダウンロード後、ローカルの同期コマンドで公開してください。</p></section>
<section><h2>管理対象</h2><ul class="creator-field-list">{field_html}</ul></section>
<section class="creator-cms">
<label>正本JSON<textarea id="cms-json" spellcheck="false">{raw}</textarea></label>
<div class="explore-actions"><button id="cms-validate">検証</button><button id="cms-save">下書き保存</button>
<button id="cms-download">JSONを書き出す</button><label class="creator-file">JSONを読み込む<input id="cms-import" type="file" accept="application/json"/></label></div>
<output id="cms-status" aria-live="polite"></output></section>
<section><h2>公開手順</h2><ol><li>JSONを検証</li><li><code>assets/data/creator-cms.json</code>へ反映</li>
<li><code>python3 scripts/build_explore_catalog.py</code>を2回実行</li><li>sitemap・画像・動画・feed監査後に公開</li></ol></section>"""
    page = shell("admin/", "Creator CMS｜SUZUKA Admin", "SUZUKA AIアーティスト総合プラットフォームの正本データ管理画面。",
                 "Creator CMS", body, [], page_type="WebPage")
    page = page.replace('content="index, follow"', 'content="noindex, nofollow"').replace(
        "</body>", '<script defer src="../assets/creator-admin.js"></script></body>')
    write(root / "admin/index.html", page)

    checks = [
        ("公開作品", "published"), ("Upcoming", "upcoming"), ("公開予定", "scheduled"), ("MV不足", "mv"),
        ("News不足", "news"), ("Gallery不足", "gallery"), ("Wiki不足", "wiki"), ("Universe不足", "universe"),
        ("画像不足", "image"), ("SEO不足", "seo"), ("JSON-LD不足", "jsonld"), ("Search Console登録候補", "searchconsole"),
        ("YouTube未設定", "youtube"), ("Instagram未設定", "instagram"), ("公開日時未設定", "publishedat"),
        ("おすすめ未設定", "recommendations"),
    ]
    tiles = "".join(f'<article class="creator-dashboard-tile"><h2>{label}</h2><strong data-dashboard="{key}">—</strong><ul data-dashboard-list="{key}"></ul></article>' for label, key in checks)
    dashboard = shell("admin/dashboard/", "Creator Dashboard｜SUZUKA Admin", "SUZUKA AIアーティスト作品の公開状態と不足項目を監査するダッシュボード。",
                      "Creator Dashboard", f'<section class="creator-copy"><p>正本データから公開状況と不足項目をリアルタイム集計します。</p></section><section class="creator-dashboard">{tiles}</section>',
                      [], ("admin", "Creator CMS"), page_type="WebPage")
    dashboard = dashboard.replace('content="index, follow"', 'content="noindex, nofollow"').replace(
        "</body>", '<script defer src="../../assets/creator-dashboard.js"></script></body>')
    write(root / "admin/dashboard/index.html", dashboard)


def english_pages(root: Path, cms: dict, releases: list[dict]) -> None:
    artists = cms["artists"]
    sections = {
        "": ("Home", "Discover SUZUKA", "An original AI artist platform where music opens new stories."),
        "artists": ("Artists", "AI Artists", "Meet SUZUKA's seven fictional AI artists and groups."),
        "releases": ("Releases", "Releases", "Explore all officially released SUZUKA works."),
        "search": ("Search", "Search", "Search by title, artist, genre, theme, tag, year and work type."),
        "genres": ("Genres", "Genres", "Explore SUZUKA music by genre."),
        "discography": ("Discography", "Discography", "Follow the SUZUKA release timeline."),
        "universe": ("Universe", "Universe", "Explore the connected worlds and stories of SUZUKA's AI artists."),
        "news": ("News", "News", "Official release news from SUZUKA."),
    }
    for route, (title, heading, description) in sections.items():
        depth = 1 if not route else 2
        p = "../" * depth
        artist_links = "".join(f'<a class="creator-link-card" href="{p}artists/{a["slug"]}/"><h2>{html.escape(a["name"])}</h2><p>{html.escape(a["reading"])}</p></a>' for a in artists)
        release_cards = "".join(
            f'<article class="creator-link-card"><time>{x["releaseDate"]}</time><h2>{html.escape(x["title"])}</h2>'
            f'<p>{html.escape(x["artist"])}</p><a href="{p}{x["releaseUrl"]}">Release page</a></article>' for x in releases
        )
        canonical_path = "en/" if not route else f"en/{route}/"
        if route == "artists":
            content = f'<section class="creator-link-grid">{artist_links}</section>'
        elif route in {"releases", "discography", "news", "search"}:
            content = f'<section class="creator-link-grid">{release_cards}</section>'
        elif route == "genres":
            genres = sorted({g for x in releases for g in x.get("genres", [])})
            content = '<section class="creator-link-grid">' + "".join(f'<a class="creator-link-card" href="../../search/?genre={html.escape(g)}">{html.escape(g)}</a>' for g in genres) + "</section>"
        elif route == "universe":
            content = f'<section class="creator-copy"><p>{html.escape(cms["universe"].get("overview", cms["universe"].get("story", "")))}</p></section><section class="creator-link-grid">{artist_links}</section>'
        else:
            content = f'<section class="creator-link-grid">{artist_links}</section><section class="creator-link-grid">{release_cards[:6000]}</section>'
        graph = {"@context": "https://schema.org", "@graph": [
            {"@type": "CollectionPage" if route in {"artists", "releases", "genres", "discography", "news"} else "WebPage",
             "url": f"{BASE}/{canonical_path}", "name": f"{title} | SUZUKA", "description": description,
             "inLanguage": "en"},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "English", "item": f"{BASE}/en/"},
                {"@type": "ListItem", "position": 2, "name": title, "item": f"{BASE}/{canonical_path}"},
            ]},
        ]}
        page = f"""<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} | SUZUKA AI Artist Platform</title><meta name="description" content="{html.escape(description)} Fictional AI artists; AI supports the creative process."/>
<meta name="robots" content="index, follow"/><link rel="canonical" href="{BASE}/{canonical_path}"/>
<link rel="alternate" hreflang="en" href="{BASE}/{canonical_path}"/><link rel="alternate" hreflang="ja" href="{BASE}/{route + '/' if route else ''}"/>
<link rel="alternate" hreflang="x-default" href="{BASE}/{route + '/' if route else ''}"/>
<meta property="og:type" content="website"/><meta property="og:title" content="{title} | SUZUKA"/><meta property="og:description" content="{html.escape(description)}"/>
<meta property="og:url" content="{BASE}/{canonical_path}"/><meta property="og:image" content="{BASE}/images/suzuka-channel.jpg"/>
<meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{title} | SUZUKA"/>
<meta name="twitter:description" content="{html.escape(description)}"/><meta name="twitter:image" content="{BASE}/images/suzuka-channel.jpg"/>
<link rel="stylesheet" href="{p}assets/styles.css"/><link rel="stylesheet" href="{p}assets/explore.css"/>
<link rel="stylesheet" href="{p}assets/explorer-update.css"/><link rel="stylesheet" href="{p}assets/creator-platform.css"/>
<link rel="stylesheet" href="{p}assets/player.css"/><link rel="stylesheet" href="{p}assets/ai-disclosure.css"/><script type="application/ld+json">{dump(graph)}</script></head><body><main>
<header class="site-header inner-site-header"><a class="brand" href="../">SUZUKA<span class="brand-dot">●</span></a>
<nav class="desktop-nav"><a href="{p}en/">Home</a><a href="{p}en/artists/">Artists</a><a href="{p}en/releases/">Releases</a>
<a href="{p}en/search/">Search</a><a href="{p}en/genres/">Genres</a><a href="{p}en/discography/">Discography</a>
<a href="{p}en/universe/">Universe</a><a href="{p}en/news/">News</a>
<a href="{p}artists/">Artists JP</a><a href="{p}releases/">Releases JP</a><a href="{p}news/">News JP</a>
<a href="https://www.youtube.com/@suzuka1209">YouTube</a><a href="{p}">日本語</a></nav></header>
<section class="explorer-hero"><p class="section-kicker">SUZUKA CREATOR PLATFORM 3.0</p><h1>{heading}</h1><p>{description}</p></section>
<nav class="explorer-breadcrumb"><a href="{p}en/">English</a><b>/</b><span>{title}</span></nav><div id="content">{content}</div>
<footer class="site-footer inner-footer"><p class="ai-footer-disclosure">SUZUKA Original AI Music Project. All artists and characters are fictional. AI supports the creative process.</p></footer></main>
<script defer src="{p}assets/main.js"></script></body></html>\n"""
        write(root / canonical_path / "index.html", page)

    # Reciprocal hreflang for Japanese landing pages.
    for route in sections:
        target = root / (f"{route}/index.html" if route else "index.html")
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        jp_path = f"{route}/" if route else ""
        en_path = f"en/{route}/" if route else "en/"
        tags = (f'<link rel="alternate" hreflang="ja" href="{BASE}/{jp_path}"/>'
                f'<link rel="alternate" hreflang="en" href="{BASE}/{en_path}"/>'
                f'<link rel="alternate" hreflang="x-default" href="{BASE}/{jp_path}"/>')
        text = re.sub(r'<link rel="alternate" hreflang="(?:ja|en|x-default)"[^>]+/?>', "", text)
        text = text.replace("</head>", tags + "</head>", 1)
        target.write_text(text, encoding="utf-8")


def top_and_nav(root: Path, playlists_data: list[dict]) -> None:
    links = (
        '<a href="./playlists/">Playlists</a><a href="./community/">Community</a>'
        '<a href="./en/" lang="en">English</a>'
    )
    home = root / "index.html"
    content = (
        '<section class="creator-home"><p class="section-kicker">CREATOR PLATFORM 3.0</p><h2>AIアーティストの物語をもっと深く</h2>'
        '<div class="creator-link-grid"><a class="creator-link-card" href="./playlists/"><h3>人気プレイリスト</h3><p>テーマや気分から作品を選ぶ</p></a>'
        '<a class="creator-link-card" href="./community/"><h3>Community</h3><p>人気投票とおすすめ曲</p></a>'
        '<a class="creator-link-card" href="./universe/"><h3>Universe 2.0</h3><p>年表・相関図・世界MAP</p></a>'
        '<a class="creator-link-card" href="./en/" lang="en"><h3>English</h3><p>Explore SUZUKA in English</p></a></div></section>'
    )
    marker_upsert(home, "HOME", content)
    for path in root.glob("**/index.html"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        depth = len(path.relative_to(root).parts) - 1
        p = "../" * depth
        if "explorer-primary-nav" in text and "playlists/" not in text:
            text = text.replace(f'<a href="{p}social/">Social</a>', f'<a href="{p}playlists/">Playlists</a><a href="{p}community/">Community</a><a href="{p}social/">Social</a>', 1)
        path.write_text(text, encoding="utf-8")


def normalize_generated_assets(root: Path, cms: dict) -> None:
    """Replace retired generated references using the current CMS cover mapping."""
    current = {item["slug"]: item.get("coverImage", "") for item in cms["releases"]}
    replacements = {
        "images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png":
            current.get("moshimo-ashita-hajimemashite-ni-natte-mo", "images/mv-mia.jpg"),
        "images/mv-boukyaku-no-ikimono.png":
            current.get("boukyaku-no-ikimono", "images/youtube-boukyaku-no-ikimono.jpg"),
        "images/mv-smile-and-say-goodbye.png":
            current.get("smile-and-say-goodbye", "images/youtube-smile-and-say-goodbye.jpg"),
    }
    for path in root.glob("**/index.html"):
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def analytics(root: Path) -> None:
    """Install one GA4 tag on public pages and keep admin pages unmeasured."""
    script = f"""
<!-- SUZUKA:GA4:START -->
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA4_MEASUREMENT_ID}', {{
  page_location: window.location.origin + window.location.pathname,
  page_referrer: document.referrer ? new URL(document.referrer).origin + new URL(document.referrer).pathname : ''
}});
</script>
<!-- SUZUKA:GA4:END -->
""".strip()
    event_source = """
(() => {
  const safePageUrl = window.location.origin + window.location.pathname;
  const send = (name, parameters = {}) => {
    if (typeof window.gtag !== "function") return;
    window.gtag("event", name, {...parameters, page_location: safePageUrl});
  };
  const clean = value => String(value || "").replace(/\\s+/g, " ").trim().slice(0, 300);
  const safeLink = value => {
    const url = new URL(value, location.href);
    if (url.origin === location.origin) return url.origin + url.pathname;
    return url.href;
  };
  const pageRelease = location.pathname.match(/\\/releases\\/([^/]+)\\/?$/)?.[1] || "";
  const pageArtist = location.pathname.match(/\\/artists\\/([^/]+)\\/?$/)?.[1] || "";
  const schemas = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach(node => {
    try {
      const walk = value => {
        if (!value || typeof value !== "object") return;
        if (Array.isArray(value)) return value.forEach(walk);
        schemas.push(value);
        Object.values(value).forEach(walk);
      };
      walk(JSON.parse(node.textContent));
    } catch (_) {}
  });
  const recording = schemas.find(item => {
    const type = item["@type"];
    return type === "MusicRecording" || (Array.isArray(type) && type.includes("MusicRecording"));
  }) || {};
  const schemaArtist = clean(recording.byArtist?.name || recording.byArtist?.[0]?.name);
  const schemaTitle = clean(recording.name);
  const contextFor = anchor => anchor.closest(
    "[data-weekly-pick],.explorer-release-card,.explore-card,.release-card,.timeline-item,.gallery-card,article,section"
  ) || document.body;
  const detailsFor = anchor => {
    const context = contextFor(anchor);
    const linkedPath = new URL(anchor.href, location.href).pathname;
    const releaseLink = context.querySelector('a[href*="/releases/"]');
    const releaseUrl = new URL(releaseLink?.href || location.href, location.href);
    const slug = releaseUrl.pathname.match(/\\/releases\\/([^/]+)\\/?/)?.[1] || pageRelease;
    const title = clean(
      context.querySelector("[data-pick-title],h1,h2,h3")?.textContent || schemaTitle || document.querySelector("h1")?.textContent
    );
    const artist = clean(
      context.querySelector("[data-pick-artist],.release-card-artist,.artist-name")?.textContent ||
      schemaArtist || (pageArtist ? document.querySelector("h1")?.textContent : "")
    );
    return {
      work_title: title,
      release_slug: clean(slug),
      artist_name: artist,
      link_url: safeLink(anchor.href),
      content_type: clean(
        anchor.closest("[data-weekly-pick]") ? "weekly_pick" :
        linkedPath.includes("/releases/") ? "release" :
        linkedPath.includes("/news/") ? "news" :
        linkedPath.includes("/gallery/") ? "gallery" :
        linkedPath.includes("/wiki/") ? "wiki" :
        linkedPath.includes("/universe/") ? "universe" :
        linkedPath.includes("/community/") ? "community" :
        linkedPath.includes("/playlists/") ? "playlist" : "link"
      ),
    };
  };
  document.addEventListener("click", event => {
    const anchor = event.target.closest("a[href]");
    if (!anchor) return;
    const url = new URL(anchor.href, location.href);
    const path = url.pathname;
    const host = url.hostname.replace(/^www\\./, "");
    const isYoutube = host === "youtube.com" || host === "youtu.be";
    const youtubeChannel = isYoutube &&
      (path.includes("/@suzuka1209") || path.includes("/channel/UCVde75yhByGQMu3SkO-fzrA"));
    const youtubeVideo = isYoutube && !youtubeChannel &&
      (path === "/watch" || host === "youtu.be" || path.includes("/shorts/"));
    const details = detailsFor(anchor);
    if (anchor.closest("[data-weekly-pick]")) send("weekly_pick_click", details);
    if (youtubeChannel) send("youtube_click", details);
    else if (youtubeVideo && path.includes("/shorts/")) send("shorts_click", details);
    else if (youtubeVideo) send("official_mv_click", details);
    if (url.hostname.includes("instagram.com")) send("instagram_click", details);
    if (url.origin === location.origin && /\\/releases\\/[^/]+\\/?$/.test(path)) send("release_click", details);
    if (url.origin === location.origin && /\\/playlists\\/(?:[^/]+\\/?)?$/.test(path)) send("playlist_click", details);
    if (url.origin === location.origin && /\\/artists\\/[^/]+\\/?$/.test(path)) send("artist_click", details);
    if (url.origin === location.origin && /\\/news\\/[^/]+\\/?$/.test(path)) send("news_click", details);
    if (url.origin === location.origin && /\\/gallery\\/(?:[^/]+\\/?)?$/.test(path)) send("gallery_click", details);
    if (url.origin === location.origin && /\\/wiki\\/(?:[^/]+\\/?)?$/.test(path)) send("wiki_click", details);
    if (url.origin === location.origin && /\\/universe\\/?$/.test(path)) send("universe_click", details);
    if (url.origin === location.origin && /\\/community\\/?$/.test(path)) send("community_click", details);
    if (url.origin !== location.origin) send("outbound_click", details);
  });
  const form = document.querySelector("[data-search-form]");
  if (form) {
    let timer = 0, lastSignature = "";
    const reportSearch = () => {
      clearTimeout(timer);
      timer = window.setTimeout(() => {
        const data = Object.fromEntries(new FormData(form));
        const active = Object.values(data).filter(Boolean).length;
        const signature = Object.keys(data).filter(key => data[key]).sort().join("|") + ":" + active;
        if (!active || signature === lastSignature) return;
        lastSignature = signature;
        send("search_use", {
          has_search_query: Boolean(data.q),
          active_filter_count: active,
          result_count: Number(document.querySelector("[data-search-count]")?.textContent || 0),
        });
      }, 800);
    };
    form.addEventListener("input", reportSearch);
    form.addEventListener("change", reportSearch);
    form.addEventListener("submit", reportSearch);
  }
})();
""".strip() + "\n"
    write(root / "assets/analytics.js", event_source)

    ga_pattern = re.compile(
        r"\s*<!-- SUZUKA:GA4:START -->.*?<!-- SUZUKA:GA4:END -->\s*",
        flags=re.DOTALL,
    )
    event_pattern = re.compile(
        r'\s*<script\s+defer\s+src="(?:\.\./)*assets/analytics\.js"></script>\s*'
    )
    for path in root.glob("**/index.html"):
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        text = ga_pattern.sub("", text)
        text = event_pattern.sub("", text)
        if relative.parts[0] != "admin":
            depth = len(relative.parts) - 1
            prefix = "../" * depth
            text = text.replace("<head>", f"<head>\n{script}\n", 1)
            text = text.replace(
                "</body>",
                f'<script defer src="{prefix}assets/analytics.js"></script></body>',
                1,
            )
        path.write_text(text, encoding="utf-8")

    about_path = root / "about/index.html"
    about = about_path.read_text(encoding="utf-8")
    privacy = (
        '<!-- SUZUKA:ANALYTICS-NOTICE:START -->'
        '<section class="ai-about-section analytics-notice" aria-labelledby="analytics-title">'
        '<div><p class="section-kicker">Site analytics</p>'
        '<h2 id="analytics-title">Google Analyticsの利用について</h2>'
        '<p>SUZUKAでは、サイトの利用状況を把握し、内容や使いやすさを改善するためにGoogle Analyticsを利用しています。'
        'GoogleがCookieなどを利用して閲覧情報を収集する場合があります。収集した情報はサイト改善の目的で利用します。</p>'
        '<p><a href="https://policies.google.com/privacy?hl=ja" target="_blank" rel="noopener noreferrer">'
        'Googleのプライバシーポリシー ↗</a></p></div></section>'
        '<!-- SUZUKA:ANALYTICS-NOTICE:END -->'
    )
    indexnow_notice = (
        '<!-- SUZUKA:INDEXNOW-NOTICE:START -->'
        '<section class="ai-about-section indexnow-notice" aria-labelledby="indexnow-title">'
        '<div><p class="section-kicker">Search engine updates</p>'
        '<h2 id="indexnow-title">検索エンジンへの更新通知について</h2>'
        '<p>SUZUKAでは、新規公開・更新・削除された公開ページを検索エンジンへ速やかに知らせるため、IndexNowを利用しています。'
        '通知対象は公開ページのURLに限り、検索条件や個人情報は送信しません。IndexNowへの通知は、検索結果への掲載を保証するものではありません。</p>'
        '</div></section>'
        '<!-- SUZUKA:INDEXNOW-NOTICE:END -->'
    )
    about = re.sub(
        r"<!-- SUZUKA:ANALYTICS-NOTICE:START -->.*?<!-- SUZUKA:ANALYTICS-NOTICE:END -->",
        "",
        about,
        flags=re.DOTALL,
    )
    about = re.sub(
        r"<!-- SUZUKA:INDEXNOW-NOTICE:START -->.*?<!-- SUZUKA:INDEXNOW-NOTICE:END -->",
        "",
        about,
        flags=re.DOTALL,
    )
    about = about.replace(
        '<section class="about-label-values"',
        privacy + indexnow_notice + '<section class="about-label-values"',
        1,
    )
    about_path.write_text(about, encoding="utf-8")


def assets(root: Path) -> None:
    write(root / "assets/creator-platform.css", """
.creator-link-grid,.creator-form-grid,.creator-dashboard,.creator-universe-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:1rem;margin:1.5rem 0}
.creator-link-card,.creator-dashboard-tile,.creator-universe-node,.creator-form-grid form,.creator-copy,.creator-cms{display:block;padding:1.2rem;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.045);border-radius:1rem}
.creator-universe-node img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:.7rem}
.creator-map{display:flex;flex-wrap:wrap;justify-content:center;gap:.8rem;padding:2rem;background:radial-gradient(circle,rgba(190,50,255,.18),transparent 65%)}
.creator-map-node{padding:1rem;border:1px solid currentColor;border-radius:999px}
.creator-timeline,.creator-term-list,.creator-ranking-list{display:grid;gap:.65rem}.creator-timeline li,.creator-term-list li{display:grid;grid-template-columns:minmax(7rem,auto) 1fr auto;gap:1rem;padding:.8rem;border-bottom:1px solid rgba(255,255,255,.12)}
.creator-form-grid label{display:grid;gap:.4rem;margin:.8rem 0}.creator-form-grid input,.creator-form-grid select,.creator-form-grid textarea{width:100%;padding:.75rem;color:#111;background:#fff;border-radius:.4rem}
.creator-form-grid button,.creator-cms button{padding:.75rem 1rem;border:0;border-radius:999px;font-weight:700}.creator-notice{padding:1rem;border-left:4px solid #e74cff;background:rgba(231,76,255,.1)}
.creator-field-list{display:flex;flex-wrap:wrap;gap:.6rem;list-style:none;padding:0}.creator-field-list li{padding:.4rem .75rem;border:1px solid rgba(255,255,255,.18);border-radius:999px}
#cms-json{width:100%;min-height:55vh;padding:1rem;font:12px/1.5 ui-monospace,monospace;color:#111;background:#fff}.creator-file{display:inline-flex;align-items:center}.creator-file input{max-width:12rem}
.creator-dashboard-tile strong{font-size:2.2rem}.creator-empty{padding:2rem;text-align:center}.creator-recommendations{margin-top:4rem}
@media(max-width:600px){.creator-timeline li,.creator-term-list li{grid-template-columns:1fr}.creator-map{padding:1rem}.creator-dashboard{grid-template-columns:1fr 1fr}}
body{overflow-x:hidden}
""".strip() + "\n")
    write(root / "assets/creator-platform.js", """
(() => {
  const key = "suzuka-community-v1";
  const state = JSON.parse(localStorage.getItem(key) || '{"votes":{},"entries":[]}');
  const save = () => localStorage.setItem(key, JSON.stringify(state));
  const render = () => {
    const list = document.querySelector("[data-community-ranking]");
    if (!list) return;
    const rows = Object.entries(state.votes).sort((a,b)=>b[1]-a[1] || a[0].localeCompare(b[0]));
    list.innerHTML = rows.length ? rows.map(([slug,count],i)=>`<li><strong>${i+1}</strong> ${slug} <span>${count}票</span></li>`).join("") : "<li>この端末の投票はまだありません。</li>";
  };
  document.querySelectorAll("[data-community-form]").forEach(form => form.addEventListener("submit", event => {
    event.preventDefault();
    const type = form.dataset.communityForm;
    const data = Object.fromEntries(new FormData(form));
    if (type === "vote") state.votes[data.release] = (state.votes[data.release] || 0) + 1;
    state.entries.push({type, data, savedAt: new Date().toISOString()});
    save(); render();
    const output = document.querySelector(`[data-community-result="${type}"]`);
    if (output) output.textContent = "この端末に保存しました。";
    form.reset();
  }));
  render();
})();
""".strip() + "\n")
    write(root / "assets/creator-admin.js", """
(() => {
  const area = document.querySelector("#cms-json"), status = document.querySelector("#cms-status");
  const validate = () => {
    const data = JSON.parse(area.value);
    const required = ["artists","releases","upcoming","news","taxonomy","playlistDefinitions"];
    const missing = required.filter(key => !Array.isArray(data[key]) && typeof data[key] !== "object");
    if (data.schemaVersion !== "3.0" || missing.length) throw new Error("必須項目不足: " + missing.join(", "));
    return data;
  };
  document.querySelector("#cms-validate").onclick = () => { try { const d=validate(); status.textContent=`検証OK: ${d.releases.length}作品 / ${d.artists.length}アーティスト`; } catch(e){ status.textContent="検証エラー: "+e.message; } };
  document.querySelector("#cms-save").onclick = () => { try { validate(); localStorage.setItem("suzuka-creator-cms-draft",area.value); status.textContent="下書きをこの端末に保存しました。"; } catch(e){ status.textContent="保存できません: "+e.message; } };
  document.querySelector("#cms-download").onclick = () => { try { validate(); const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([area.value+"\\n"],{type:"application/json"})); a.download="creator-cms.json"; a.click(); URL.revokeObjectURL(a.href); } catch(e){ status.textContent="書き出せません: "+e.message; } };
  document.querySelector("#cms-import").onchange = async e => { const file=e.target.files[0]; if(file){area.value=await file.text(); document.querySelector("#cms-validate").click();} };
  const draft=localStorage.getItem("suzuka-creator-cms-draft"); if(draft) area.value=draft;
})();
""".strip() + "\n")
    write(root / "assets/creator-dashboard.js", """
(async () => {
  const root="../../", cms=await fetch(root+"assets/data/creator-cms.json").then(r=>r.json());
  const rec=await fetch(root+"assets/data/recommendations.json").then(r=>r.json());
  const set=(key,items)=>{const value=document.querySelector(`[data-dashboard="${key}"]`),list=document.querySelector(`[data-dashboard-list="${key}"]`);value.textContent=Array.isArray(items)?items.length:items; if(list&&Array.isArray(items))list.innerHTML=items.slice(0,8).map(x=>`<li>${x}</li>`).join("")};
  const releases=cms.releases, artists=cms.artists, newsSlugs=new Set(cms.news.map(x=>x.releaseSlug).filter(Boolean));
  set("published",releases.length); set("upcoming",cms.upcoming.length); set("scheduled",cms.upcoming.map(x=>x.title));
  set("mv",releases.filter(x=>!x.youtubeUrl).map(x=>x.title)); set("news",releases.filter(x=>!newsSlugs.has(x.slug)).map(x=>x.title));
  set("gallery",releases.filter(x=>!(x.galleryImages||[]).length).map(x=>x.title)); set("wiki",artists.filter(x=>!x.world).map(x=>x.name));
  set("universe",artists.filter(x=>!x.world||!x.music).map(x=>x.name)); set("image",releases.filter(x=>!x.coverImage).map(x=>x.title));
  set("seo",releases.filter(x=>!x.seo?.title||!x.seo?.description).map(x=>x.title)); set("jsonld",releases.filter(x=>x.seo?.jsonLdEnabled===false).map(x=>x.title));
  set("searchconsole",["/playlists/","/community/","/universe/","/en/"]); set("youtube",releases.filter(x=>!x.youtubeUrl).map(x=>x.title));
  set("instagram",artists.filter(x=>!x.instagramUrl).map(x=>x.name)); set("publishedat",releases.filter(x=>!x.publishedAt).map(x=>x.title));
  set("recommendations",releases.filter(x=>!rec.recommendations[x.slug]?.aiRecommended?.length).map(x=>x.title));
})().catch(error=>{document.body.dataset.dashboardError=error.message});
""".strip() + "\n")


def youtube_ledger(root: Path, cms: dict) -> None:
    path = root / "docs/youtube/youtube-seo-creator.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["status", "publish_at", "title", "artist", "youtube_url", "description", "keywords"])
        for item in [*cms["releases"], *cms["upcoming"]]:
            writer.writerow([
                item.get("status", "published"), item.get("publishedAt", item.get("releaseDate", "")),
                item["title"], item["artist"], item.get("youtubeUrl", ""),
                item.get("description", ""), ", ".join(item.get("searchKeywords", [])),
            ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    evidence, evidence_by_slug = apply_evidence_to_cms(root, cms)
    catalog_path = root / "assets/data/releases-catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    releases = catalog["releases"]
    recommendations = deterministic_recommendations(releases)
    for item in releases:
        item["recommendations"] = recommendations[item["slug"]]
    write(catalog_path, json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    write(root / "assets/data/recommendations.json", json.dumps({"updatedAt": cms["updatedAt"], "recommendations": recommendations}, ensure_ascii=False, indent=2) + "\n")
    recommendation_pages(root, releases, recommendations)
    playlist_data = playlists(root, cms, releases)
    universe(root, cms, releases)
    community(root, releases)
    admin_pages(root, cms)
    english_pages(root, cms, releases)
    assets(root)
    top_and_nav(root, playlist_data)
    normalize_generated_assets(root, cms)
    analytics(root)
    normalize_structured_dates(root, evidence, evidence_by_slug)
    youtube_ledger(root, cms)
    print(f"Creator Platform generated: {len(releases)} releases, {len(cms['artists'])} artists, {len(playlist_data)} playlists.")


if __name__ == "__main__":
    main()

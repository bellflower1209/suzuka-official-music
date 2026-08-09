#!/usr/bin/env python3
"""Generate Brand Discovery & Growth 1.1 from canonical SUZUKA data."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from build_creator_platform_v31 import discovery_recommendations, eligible_lyrics
from build_explorer_update import BASE, card

JSONLD_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)
PAGE_TYPES = {"WebPage", "AboutPage", "CollectionPage", "ProfilePage", "SearchResultsPage", "ItemPage"}


def types_of(node: dict) -> set[str]:
    value = node.get("@type", [])
    return {value} if isinstance(value, str) else set(value)


def marker_upsert(text: str, name: str, content: str, anchor: str) -> str:
    block = f"<!-- BRAND-V11:{name}:START -->{content}<!-- BRAND-V11:{name}:END -->"
    pattern = rf"<!-- BRAND-V11:{re.escape(name)}:START -->.*?<!-- BRAND-V11:{re.escape(name)}:END -->"
    if re.search(pattern, text, re.DOTALL):
        return re.sub(pattern, block, text, count=1, flags=re.DOTALL)
    return text.replace(anchor, block + anchor, 1)


def canonical_of(text: str) -> str | None:
    match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', text, re.I)
    return match.group(1) if match else None


def set_meta(text: str, selector: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    if selector == "title":
        return re.sub(r"<title>.*?</title>", f"<title>{html.escape(value)}</title>", text, count=1, flags=re.S | re.I)
    if selector.startswith("property:"):
        name = selector.split(":", 1)[1]
        pattern = rf'<meta\b(?=[^>]*property=["\']{re.escape(name)}["\'])[^>]*>'
        tag = f'<meta property="{name}" content="{escaped}"/>'
    else:
        name = selector.split(":", 1)[-1]
        pattern = rf'<meta\b(?=[^>]*name=["\']{re.escape(name)}["\'])[^>]*>'
        tag = f'<meta name="{name}" content="{escaped}"/>'
    if re.search(pattern, text, re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    return text.replace("</head>", tag + "</head>", 1)


def consolidate_jsonld(text: str) -> str:
    """Publish one graph per page and merge repeated canonical entities."""
    matches = list(JSONLD_RE.finditer(text))
    if not matches:
        return text
    nodes: list[object] = []
    by_id: dict[str, dict] = {}
    for match in matches:
        data = json.loads(match.group(2))
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        if not isinstance(graph, list):
            continue
        for raw in graph:
            if not isinstance(raw, dict):
                nodes.append(raw)
                continue
            node = dict(raw)
            node.pop("@context", None)
            node_id = node.get("@id")
            if not node_id:
                nodes.append(node)
                continue
            if node_id not in by_id:
                by_id[node_id] = node
                nodes.append(node)
                continue
            for key, value in node.items():
                by_id[node_id].setdefault(key, value)
    payload = json.dumps(
        {"@context": "https://schema.org", "@graph": nodes},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    first = matches[0]
    replacement = first.group(1) + payload + first.group(3)
    chunks = [text[:first.start()], replacement]
    cursor = first.end()
    for match in matches[1:]:
        chunks.append(text[cursor:match.start()])
        cursor = match.end()
    chunks.append(text[cursor:])
    return "".join(chunks)


def normalize_brand_references(value: object, brand: dict, *, top_level: bool = False) -> object:
    if isinstance(value, list):
        return [normalize_brand_references(item, brand) for item in value]
    if not isinstance(value, dict):
        return value
    node_types = types_of(value)
    if not top_level and "Organization" in node_types and value.get("name") in {"SUZUKA", brand["brandName"]}:
        return {"@id": brand["organizationId"]}
    result = {key: normalize_brand_references(item, brand) for key, item in value.items()}
    if node_types & {"Person", "MusicGroup"}:
        same_as = result.get("sameAs")
        brand_profiles = {item["url"] for item in brand["sameAs"]}
        if isinstance(same_as, list) and set(same_as).issubset(brand_profiles):
            result.pop("sameAs", None)
    return result


def normalize_graph(text: str, canonical: str, relative: Path, brand: dict, releases: dict, artists: dict) -> str:
    is_home = canonical == brand["officialUrl"]
    route_parts = relative.parts
    release = None
    if len(route_parts) >= 3 and route_parts[0] in {"releases", "lyrics"}:
        release = releases.get(route_parts[1])

    def replace(match: re.Match) -> str:
        data = json.loads(match.group(2))
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        if not isinstance(graph, list):
            return match.group(0)
        cleaned = []
        for raw in graph:
            if not isinstance(raw, dict):
                cleaned.append(raw)
                continue
            node = normalize_brand_references(raw, brand, top_level=True)
            node_types = types_of(node)
            if not is_home and ("WebSite" in node_types or (
                "Organization" in node_types and node.get("name") in {"SUZUKA", brand["brandName"]}
            )):
                continue
            if node_types & PAGE_TYPES:
                node["@id"] = brand["homeWebPageId"] if is_home and "WebPage" in node_types else f"{canonical}#webpage"
                node["url"] = canonical
                node["isPartOf"] = {"@id": brand["websiteId"]}
                node["publisher"] = {"@id": brand["organizationId"]}
                if is_home or "AboutPage" in node_types:
                    node["about"] = {"@id": brand["organizationId"]}
            cleaned.append(node)

        page_nodes = [node for node in cleaned if isinstance(node, dict) and types_of(node) & PAGE_TYPES]
        if len(page_nodes) > 1:
            primary = next((node for node in page_nodes if "WebPage" not in types_of(node)), page_nodes[0])
            for node in page_nodes:
                if node is primary:
                    continue
                for key, value in node.items():
                    primary.setdefault(key, value)
            cleaned = [node for node in cleaned if node not in page_nodes or node is primary]

        # A work can be referenced from Release, Lyrics and News pages. Keep
        # its core identity identical wherever it is defined.
        for node in cleaned:
            if not isinstance(node, dict) or "MusicRecording" not in types_of(node):
                continue
            node_id = str(node.get("@id", ""))
            node_url = str(node.get("url", ""))
            work = next(
                (
                    item for item in releases.values()
                    if item.get("title") == node.get("name")
                    or f'/{item["releaseUrl"]}#recording' in node_id
                    or f'/{item["releaseUrl"]}' in node_url
                ),
                None,
            )
            if not work:
                continue
            recording_id = f'{BASE}/{work["releaseUrl"]}#recording'
            node["@id"] = recording_id
            node["name"] = work["title"]
            node["url"] = f'{BASE}/{work["releaseUrl"]}'
            node["description"] = work["description"]
            node["byArtist"] = {"@id": f'{BASE}/artists/{work["artistSlug"]}/#artist'}

        # Some legacy release templates emitted a second standalone recording
        # in the same graph. Merge, rather than publish duplicate definitions.
        merged: list[object] = []
        by_id: dict[str, dict] = {}
        for node in cleaned:
            if not isinstance(node, dict) or not node.get("@id"):
                merged.append(node)
                continue
            node_id = node["@id"]
            if node_id not in by_id:
                by_id[node_id] = node
                merged.append(node)
                continue
            existing = by_id[node_id]
            for key, value in node.items():
                existing.setdefault(key, value)
        cleaned = merged

        if is_home:
            cleaned = [node for node in cleaned if not (isinstance(node, dict) and types_of(node) & {"WebSite", "Organization"})]
            organization = {
                "@type": "Organization", "@id": brand["organizationId"],
                "name": brand["brandName"], "alternateName": brand["shortName"],
                "url": brand["officialUrl"], "description": brand["description"],
                "logo": {"@type": "ImageObject", "url": brand["logo"], "contentUrl": brand["logo"]},
                "sameAs": [item["url"] for item in brand["sameAs"]],
            }
            website = {
                "@type": "WebSite", "@id": brand["websiteId"], "url": brand["officialUrl"],
                "name": brand["brandName"], "alternateName": brand["alternateNames"],
                "publisher": {"@id": brand["organizationId"]}, "inLanguage": "ja",
            }
            cleaned = [organization, website, *cleaned]

            # The Home hero is a second representation of a canonical release.
            # Resolve it to the same MusicRecording/VideoObject IDs used on the
            # release page so crawlers do not see two different works.
            for node in cleaned:
                if not isinstance(node, dict) or "MusicRecording" not in types_of(node):
                    continue
                hero_release = next(
                    (item for item in releases.values() if item.get("title") == node.get("name")),
                    None,
                )
                if not hero_release:
                    continue
                recording_id = f'{BASE}/{hero_release["releaseUrl"]}#recording'
                video_id = f'{BASE}/{hero_release["releaseUrl"]}#video'
                previous_video_id = (
                    node.get("subjectOf", {}).get("@id")
                    if isinstance(node.get("subjectOf"), dict)
                    else None
                )
                node["@id"] = recording_id
                node["url"] = f'{BASE}/{hero_release["releaseUrl"]}'
                node["description"] = hero_release["description"]
                node["byArtist"] = {
                    "@id": f'{BASE}/artists/{hero_release["artistSlug"]}/#artist'
                }
                if "subjectOf" in node:
                    node["subjectOf"] = {"@id": video_id}
                for candidate in cleaned:
                    if not isinstance(candidate, dict):
                        continue
                    if types_of(candidate) & PAGE_TYPES:
                        candidate["mainEntity"] = {"@id": recording_id}
                    if "VideoObject" in types_of(candidate) and (
                        candidate.get("@id") == previous_video_id
                        or candidate.get("contentUrl") == hero_release.get("youtubeUrl")
                    ):
                        candidate["@id"] = video_id
                        candidate["about"] = {"@id": recording_id}
                break

        if release:
            recording_id = f'{BASE}/{release["releaseUrl"]}#recording'
            artist_id = f'{BASE}/artists/{release["artistSlug"]}/#artist'
            for node in cleaned:
                if not isinstance(node, dict):
                    continue
                node_types = types_of(node)
                if node_types & PAGE_TYPES:
                    node["mainEntity"] = {"@id": recording_id}
                if "MusicRecording" in node_types:
                    node["@id"] = recording_id
                    node["name"] = release["title"]
                    node["url"] = f'{BASE}/{release["releaseUrl"]}'
                    node["description"] = release["description"]
                    node["byArtist"] = {"@id": artist_id}
                if "VideoObject" in node_types:
                    node["about"] = {"@id": recording_id}

        if len(route_parts) >= 3 and route_parts[0] == "artists":
            artist = artists.get(route_parts[1])
            if artist:
                artist_id = f'{BASE}/artists/{artist["slug"]}/#artist'
                for node in cleaned:
                    if not isinstance(node, dict):
                        continue
                    if types_of(node) & {"Person", "MusicGroup"} and node.get("name") == artist["name"]:
                        node["@type"] = artist["type"]
                        node["@id"] = artist_id
                        node["url"] = f'{BASE}/artists/{artist["slug"]}/'
                        node.pop("sameAs", None)
                    if "ProfilePage" in types_of(node):
                        node["mainEntity"] = {"@id": artist_id}

        output = {"@context": "https://schema.org", "@graph": cleaned}
        return match.group(1) + json.dumps(output, ensure_ascii=False, separators=(",", ":")) + match.group(3)

    return consolidate_jsonld(JSONLD_RE.sub(replace, text))


def related_section(item: dict, releases: list[dict]) -> str:
    recommended = discovery_recommendations(item, releases)
    cards = "".join(card(candidate, "../../") for candidate in recommended).replace(
        'class="explorer-release-card"',
        'class="explorer-release-card" data-source-section="related"',
    )
    return (
        '<section class="v11-next-listen" data-source-section="related">'
        '<p class="section-kicker">SUZUKAおすすめ</p><h2>次に聴くなら</h2>'
        '<p>同じアーティスト、正本の関連作品、テーマ、ジャンル、recommendationWeightの順で決定的に選出しています。実人気順位ではありません。</p>'
        f'<div class="explorer-card-grid">{cards}</div></section>'
    )


def enhance_visible_pages(root: Path, brand: dict, cms: dict, releases: list[dict], lyrics: list[dict], photobooks: list[dict]) -> None:
    home_path = root / "index.html"
    home = home_path.read_text(encoding="utf-8")
    home = set_meta(home, "title", "SUZUKA Official | Original AI Music Project")
    home_description = "SUZUKA Officialは、架空のAIアーティストによるオリジナル音楽・MV・公式歌詞・ビジュアル・物語を公開するAI音楽プロジェクトです。"
    for selector in ("name:description", "property:og:description", "name:twitter:description"):
        home = set_meta(home, selector, home_description)
    home = set_meta(home, "property:og:title", "SUZUKA Official | Original AI Music Project")
    home = set_meta(home, "name:twitter:title", "SUZUKA Official | Original AI Music Project")
    home = home.replace("SUZUKA Original AI Music Project</p>", "SUZUKA Official · Original AI Music Project</p>")
    home = home.replace(
        "SUZUKAは、ジャンルや国境にとらわれず、独自の世界観を持つアーティストと音楽作品を発信する音楽レーベルです。",
        "SUZUKA Officialは、AIを活用してオリジナルの音楽・MV・ビジュアル・歌詞・物語を制作・公開する音楽プロジェクトです。",
    )
    counts = {
        "lyrics": len(lyrics), "artists": len([item for item in cms["artists"] if item.get("status") == "published"]),
        "releases": len(releases), "upcoming": len([item for item in cms["upcoming"] if item.get("status") == "upcoming"]),
        "photobooks": len(photobooks),
    }
    home = re.sub(r'<span>\d+ LYRICS</span>', f'<span data-public-count="lyrics">{counts["lyrics"]} LYRICS</span>', home)
    home = re.sub(r'<span>\d+ BOOKS</span>', f'<span data-public-count="photobooks">{counts["photobooks"]} BOOKS</span>', home)
    summary = (
        '<section class="v11-brand-summary" aria-labelledby="brand-summary-title"><p class="section-kicker">SUZUKA Official</p>'
        '<h2 id="brand-summary-title">Original AI Music Project</h2><p>SUZUKAは、AIを制作支援に活用し、架空のAIアーティストによるオリジナル作品を公開しています。</p>'
        f'<dl><div><dt>Artists</dt><dd data-public-count="artists">{counts["artists"]}</dd></div>'
        f'<div><dt>Releases</dt><dd data-public-count="releases">{counts["releases"]}</dd></div>'
        f'<div><dt>Lyrics</dt><dd>{counts["lyrics"]}</dd></div><div><dt>Upcoming</dt><dd data-public-count="upcoming">{counts["upcoming"]}</dd></div></dl>'
        '<a class="v31-readable-cta" href="./about/">SUZUKAについて ↗</a></section>'
    )
    home = marker_upsert(home, "HOME-BRAND", summary, '<div class="word-ribbon"')
    home_path.write_text(home, encoding="utf-8")

    about_path = root / "about/index.html"
    about = about_path.read_text(encoding="utf-8")
    about = set_meta(about, "title", "SUZUKAとは | Original AI Music Project | SUZUKA Official")
    about_description = "SUZUKA Officialは、AIを活用して音楽・MV・ビジュアル・歌詞・物語を制作・公開するオリジナルAI音楽プロジェクトです。"
    for selector in ("name:description", "property:og:description", "name:twitter:description"):
        about = set_meta(about, selector, about_description)
    about = about.replace("Music Label / Creative Music Project", "Original AI Music Project")
    about = about.replace("SUZUKA LABEL", "SUZUKA Official")
    source = (
        '<section class="v11-about-entity" aria-labelledby="v11-about-title"><p class="section-kicker">SUZUKA Official</p>'
        '<h2 id="v11-about-title">SUZUKAとは</h2><p>SUZUKAは、AIを活用して音楽・MV・ビジュアル・歌詞・物語を制作・公開するオリジナルAI音楽プロジェクトです。</p>'
        '<p>所属アーティストと登場人物は架空のAIアーティストです。公開作品は、音楽、映像、公式歌詞、Visual Collectionを通してそれぞれの作品世界を描きます。</p>'
        '<nav class="explore-actions" aria-label="SUZUKAの公式コンテンツ"><a href="../artists/">Artists</a><a href="../releases/">Releases</a>'
        '<a href="../lyrics/">Lyrics</a><a href="https://www.youtube.com/@suzuka1209" target="_blank" rel="noopener noreferrer">Official YouTube ↗</a>'
        '<a href="../photobooks/">Photobooks</a></nav><p class="v11-disambiguation">本サイトのSUZUKAは、音楽・ビジュアル・物語を展開する独立したオリジナルAI音楽プロジェクトです。</p></section>'
    )
    about = marker_upsert(about, "ABOUT-ENTITY", source, '<section class="about-label-story">')
    about_path.write_text(about, encoding="utf-8")

    for item in releases:
        path = root / item["releaseUrl"] / "index.html"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        context = (
            '<section class="v11-work-context"><p>「' + html.escape(item["title"]) + '」は、SUZUKA所属AIアーティスト'
            + html.escape(item["artist"]) + 'のオリジナル楽曲です。</p><a href="../../about/">SUZUKAについて ↗</a></section>'
        )
        text = marker_upsert(text, "WORK-CONTEXT", context, '<section class="social-context-section"')
        new_related = related_section(item, releases)
        if re.search(r'<section class="release-related-section">.*?</section>', text, re.S):
            text = re.sub(r'<section class="release-related-section">.*?</section>', new_related, text, count=1, flags=re.S)
        else:
            text = marker_upsert(text, "NEXT-LISTEN", new_related, '<section class="social-context-section"')
        path.write_text(text, encoding="utf-8")

    release_map = {item["slug"]: item for item in releases}
    artist_map = {item["slug"]: item for item in cms["artists"]}
    for item in photobooks:
        path = root / f'photobooks/{item["slug"]}/index.html'
        if not path.exists():
            continue
        artist = artist_map[item["artistSlug"]]
        text = path.read_text(encoding="utf-8")
        context = f'<section class="v11-work-context"><p>「{html.escape(item["title"])}」は、SUZUKA所属AIアーティスト{html.escape(artist["name"])}の公式Visual Collectionです。</p><a href="../../about/">SUZUKAについて ↗</a></section>'
        text = marker_upsert(text, "PHOTOBOOK-CONTEXT", context, '<article class="v31-photobook-detail"')
        path.write_text(text, encoding="utf-8")


def install_shared_assets(root: Path, brand: dict) -> None:
    manifest = {
        "name": brand["brandName"], "short_name": brand["shortName"],
        "description": brand["description"], "start_url": "/", "scope": "/",
        "display": "standalone", "background_color": "#070408", "theme_color": "#070408",
        "icons": [{"src": "/images/suzuka-channel.jpg", "sizes": "900x900", "type": "image/jpeg", "purpose": "any"}],
    }
    (root / "site.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    css = """/* SUZUKA Brand Discovery & Growth 1.1 */
.v11-brand-summary,.v11-about-entity,.v11-work-context,.v11-next-listen{margin:clamp(2rem,6vw,6rem) auto;padding:clamp(1.25rem,4vw,3rem);max-width:74rem;color:var(--text-on-dark,#fff7fb);border:1px solid var(--border-contrast,#746c78);border-radius:1.2rem;background:linear-gradient(145deg,#15111a,#08070a)}
.v11-brand-summary dl{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.8rem}.v11-brand-summary dl>div{padding:1rem;border:1px solid var(--border-contrast,#746c78);border-radius:.8rem;background:#0d0b10}.v11-brand-summary dt{color:var(--text-secondary,#ddd3df)}.v11-brand-summary dd{margin:.35rem 0 0;font-size:clamp(1.5rem,4vw,2.8rem);font-weight:800}.v11-about-entity>p,.v11-work-context>p,.v11-next-listen>p{max-width:62rem;line-height:1.9}.v11-work-context a,.v11-disambiguation,.v31-brand-return a{color:var(--link-color,#ffd1eb)}.v11-artist-discovery{padding:clamp(2rem,6vw,6rem) clamp(1rem,6vw,7rem)}
@media(max-width:760px){.v11-brand-summary,.v11-about-entity,.v11-work-context,.v11-next-listen{margin-left:1rem;margin-right:1rem}.v11-brand-summary dl{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""
    (root / "assets/brand-discovery-v11.css").write_text(css, encoding="utf-8")
    for path in sorted([*root.glob("**/index.html"), root / "404.html"]):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        depth = len(path.relative_to(root).parts) - 1
        prefix = "../" * depth
        text = text.replace('content="SUZUKA"', 'content="SUZUKA Official"')
        text = text.replace("SUZUKA LABEL", "SUZUKA Official")
        text = text.replace("Music Label / Creative Music Project", "Original AI Music Project")
        if "brand-discovery-v11.css" not in text:
            text = text.replace("</head>", f'<link rel="stylesheet" href="{prefix}assets/brand-discovery-v11.css"/></head>', 1)
        text = re.sub(r'<link rel="manifest"[^>]*>', "", text, flags=re.I)
        text = re.sub(r'<link rel="apple-touch-icon"[^>]*>', "", text, flags=re.I)
        text = text.replace("</head>", f'<link rel="manifest" href="{prefix}site.webmanifest"/><link rel="apple-touch-icon" href="{prefix}images/suzuka-channel.jpg"/></head>', 1)
        canonical = canonical_of(text)
        if canonical:
            text = normalize_graph(text, canonical, path.relative_to(root), brand, {}, {})
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    brand = json.loads((root / "assets/data/brand.json").read_text(encoding="utf-8"))
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    photobook_source = json.loads((root / "assets/data/photobooks.json").read_text(encoding="utf-8"))
    releases = [item for item in catalog["releases"] if item.get("status") == "published"]
    lyrics = eligible_lyrics(releases)
    photobooks = [item for item in photobook_source["photobooks"] if item.get("status") == "published"]
    enhance_visible_pages(root, brand, cms, releases, lyrics, photobooks)
    install_shared_assets(root, brand)

    release_map = {item["slug"]: item for item in releases}
    artist_map = {item["slug"]: item for item in cms["artists"] if item.get("status") == "published"}
    for path in sorted([*root.glob("**/index.html"), root / "404.html"]):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        canonical = canonical_of(text)
        if not canonical:
            continue
        text = set_meta(text, "property:og:site_name", brand["brandName"])
        text = normalize_graph(text, canonical, path.relative_to(root), brand, release_map, artist_map)
        text = re.sub(r"[ \t]+(?=\r?\n)", "", text)
        path.write_text(text, encoding="utf-8")
    print(json.dumps({
        "version": "1.1", "brand": brand["brandName"], "artists": len(artist_map),
        "releases": len(releases), "lyrics": len(lyrics), "photobooks": len(photobooks),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

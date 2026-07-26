#!/usr/bin/env python3
"""Apply consistent fictional AI-artist disclosure copy across the static site."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FULL_PROJECT_COPY = (
    "SUZUKAは、AIを活用して音楽・ビジュアル・物語を制作する"
    "オリジナルAI音楽プロジェクトです。"
    "個性豊かな架空のAIアーティストたちが、それぞれの世界を歌います。"
)
FOOTER_COPY = (
    "SUZUKAに登場するアーティスト・人物は架空です。"
    "本プロジェクトではAIを制作支援に活用しています。"
)
ARTIST_BADGE = "SUZUKA Original AI Artist"
ARTIST_SCHEMA_COPY = (
    "SUZUKAのオリジナルAI音楽プロジェクトに登場する"
    "架空のAIアーティストです。"
)
PROJECT_SCHEMA_COPY = (
    "AIを活用して音楽・ビジュアル・物語を制作する"
    "オリジナルAI音楽プロジェクトです。登場するアーティスト・人物は架空です。"
)


def write(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")


def relative_prefix(path: Path, root: Path) -> str:
    depth = len(path.parent.relative_to(root).parts)
    return "./" if depth == 0 else "../" * depth


def inject_stylesheet(source: str, href: str) -> str:
    link = f'<link rel="stylesheet" href="{href}"/>'
    if link not in source:
        source = source.replace("</head>", link + "</head>", 1)
    return source


def update_json_ld(source: str) -> str:
    pattern = re.compile(
        r'(<script(?: id="[^"]+")? type="application/ld\+json">)(.*?)(</script>)',
        re.DOTALL,
    )

    def walk(value: object) -> None:
        if isinstance(value, dict):
            schema_type = value.get("@type")
            schema_types = schema_type if isinstance(schema_type, list) else [schema_type]
            if any(item in {"Person", "MusicGroup"} for item in schema_types):
                if not value.get("name"):
                    if value.get("description") == ARTIST_SCHEMA_COPY:
                        value.pop("description")
                else:
                    description = str(value.get("description", "")).strip()
                    if "架空" not in description and "fictional" not in description.lower():
                        value["description"] = f"{description} {ARTIST_SCHEMA_COPY}".strip()
            if "Organization" in schema_types and value.get("name") == "SUZUKA":
                description = str(value.get("description", "")).strip()
                if "オリジナルAI音楽プロジェクト" not in description:
                    value["description"] = f"{description} {PROJECT_SCHEMA_COPY}".strip()
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    def replace(match: re.Match[str]) -> str:
        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)
        walk(data)
        return match.group(1) + json.dumps(
            data, ensure_ascii=False, separators=(",", ":")
        ) + match.group(3)

    return pattern.sub(replace, source)


def add_footer_disclosure(source: str) -> str:
    if "ai-footer-disclosure" in source or "</footer>" not in source:
        return source
    note = f'<p class="ai-footer-disclosure">{FOOTER_COPY}</p>'
    return source.replace("</footer>", note + "</footer>", 1)


def update_top(root: Path) -> None:
    path = root / "index.html"
    source = path.read_text(encoding="utf-8")
    if "ai-project-note" not in source:
        marker = (
            '<p class="about-lead">SUZUKAは、ジャンルや国境にとらわれず、'
            "独自の世界観を持つアーティストと音楽作品を発信する音楽レーベルです。</p>"
        )
        source = source.replace(
            marker,
            marker + f'<p class="ai-project-note">{FULL_PROJECT_COPY}</p>',
            1,
        )
    write(path, source)


def update_about(root: Path) -> None:
    path = root / "about/index.html"
    source = path.read_text(encoding="utf-8")
    if "ai-about-section" not in source:
        section = (
            '<section class="ai-about-section" aria-labelledby="ai-artists-title"><div>'
            '<p class="section-kicker">Original AI music project</p>'
            '<h2 id="ai-artists-title">SUZUKAのAIアーティストについて</h2>'
            "<p>SUZUKAに所属するアーティストおよび登場人物は、"
            "AIを活用して制作されたオリジナルの架空の存在です。"
            "AIを制作工程の一部として活用し、楽曲、歌詞、ビジュアル、映像、"
            "物語を組み合わせて、ひとつの作品世界を制作しています。</p>"
            "<p>実在する人物・音楽グループ・団体とは関係ありません。"
            "それぞれの音楽と物語を、オリジナル作品として楽しんでいただくことを"
            "目的としています。</p></div></section>"
        )
        source = source.replace(
            '<section class="about-label-values"',
            section + '<section class="about-label-values"',
            1,
        )
    write(path, source)


def update_artists_index(root: Path) -> None:
    path = root / "artists/index.html"
    source = path.read_text(encoding="utf-8")
    if "ai-project-note" not in source:
        marker = "<p>音楽レーベルSUZUKAに所属するアーティストを紹介します。</p>"
        source = source.replace(
            marker,
            marker
            + '<p class="ai-project-note">SUZUKAに所属するアーティストは、'
            "AIを活用して制作されたオリジナルの架空アーティストです。</p>",
            1,
        )
    write(path, source)


def update_social(root: Path) -> None:
    path = root / "social/index.html"
    source = path.read_text(encoding="utf-8")
    if "ai-project-note" not in source:
        marker = re.search(r'<p class="social-hub-lead">.*?</p>', source, re.DOTALL)
        if marker:
            note = (
                '<p class="ai-project-note">AIアーティストによる'
                "オリジナル楽曲・MV・物語を発信しています。"
                "登場するアーティスト・人物は架空です。</p>"
            )
            source = (
                source[: marker.end()] + note + source[marker.end() :]
            )
    write(path, source)


def update_artist_page(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    if "ai-artist-note" not in source:
        source = source.replace(
            "</h1>",
            f'</h1><p class="ai-artist-note">{ARTIST_BADGE}</p>',
            1,
        )
    write(path, source)


def update_release_page(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    if "ai-work-disclosure" not in source:
        note = (
            '<aside class="ai-work-disclosure" aria-label="作品について">'
            "本作品は、SUZUKAのオリジナルAIアーティストによる"
            "架空の音楽プロジェクト作品です。</aside>"
        )
        source = source.replace("<footer", note + "<footer", 1)
    write(path, source)


def news_copy(path: Path) -> str:
    slug = path.parent.name
    if slug == "namaste-galaxy-release":
        return (
            "SUZUKAのオリジナルAIアーティスト、RANGILIによる公式リリース情報です。"
            "登場するアーティスト・人物は架空です。"
        )
    if slug == "wasurenai-kokoro-release":
        return (
            "AI演歌歌手・朝霧しのぶによる公式リリース情報です。"
            "登場するアーティスト・人物は架空です。"
        )
    if slug == "upcoming-artists":
        return (
            "5人組AIガールズグループ・RE:VIVEを含む、"
            "SUZUKAのオリジナルAIアーティストに関する公式情報です。"
        )
    return (
        "SUZUKAのオリジナルAIアーティストに関する公式情報です。"
        "登場するアーティスト・人物は架空です。"
    )


def update_news_page(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    if "ai-news-disclosure" not in source:
        note = f'<p class="ai-news-disclosure">{news_copy(path)}</p>'
        lead = re.search(r'<p class="news-article-lead">.*?</p>', source, re.DOTALL)
        if lead:
            source = source[: lead.end()] + note + source[lead.end() :]
        else:
            source = source.replace("<footer", note + "<footer", 1)
    write(path, source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    update_top(root)
    update_about(root)
    update_artists_index(root)
    update_social(root)

    for path in sorted((root / "artists").glob("*/index.html")):
        update_artist_page(path)
    for path in sorted((root / "releases").glob("*/index.html")):
        update_release_page(path)
    for path in sorted((root / "news").glob("*/index.html")):
        update_news_page(path)

    pages = [root / "index.html", *sorted(root.glob("*/index.html"))]
    pages.extend(sorted(root.glob("*/*/index.html")))
    seen: set[Path] = set()
    for path in pages:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        source = path.read_text(encoding="utf-8")
        prefix = relative_prefix(path, root)
        source = inject_stylesheet(source, f"{prefix}assets/ai-disclosure.css")
        source = add_footer_disclosure(source)
        source = update_json_ld(source)
        write(path, source)

    print(f"Applied AI artist disclosures to {len(seen)} pages.")


if __name__ == "__main__":
    main()

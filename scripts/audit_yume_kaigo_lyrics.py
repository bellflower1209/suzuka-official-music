#!/usr/bin/env python3
"""Audit the confirmed title, artist-only credit and byte-faithful lyrics."""
from __future__ import annotations

import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLUG = "yume-to-kaigo-to-watashitachi"
TITLE = "夢と、介護と、私たち。"
OLD_TITLE = "夢と、介護と、わたしたち。"


class LyricsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.active = False
        self.depth = 0
        self.paragraphs = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if not self.active and tag == "div" and "v31-lyrics-text" in (values.get("class") or "").split():
            self.active = True
            self.depth = 1
            return
        if not self.active:
            return
        if tag == "div":
            self.depth += 1
        elif tag == "p":
            if self.paragraphs:
                self.parts.append("\n\n")
            self.paragraphs += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.active and tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.active and tag == "div":
            self.depth -= 1
            if self.depth == 0:
                self.active = False

    def handle_data(self, data: str) -> None:
        if self.active:
            self.parts.append(data)


def main() -> int:
    errors: list[str] = []
    master = (ROOT / "assets/data/lyrics-masters/yume_to_kaigo_to_watashitachi_official_lyrics.txt").read_text(encoding="utf-8")
    source_title, separator, source_lyrics = master.partition("\n")
    source_lyrics = source_lyrics.rstrip("\n")
    if not separator or source_title != TITLE:
        errors.append("official lyric master title mismatch")

    cms = json.loads((ROOT / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    release = next((item for item in cms["releases"] if item["slug"] == SLUG), None)
    if not release:
        errors.append("canonical release missing")
    else:
        expected = {
            "title": TITLE,
            "lyricsAvailable": True,
            "lyricsVerified": True,
            "youtubeUrl": "https://www.youtube.com/watch?v=giTYuKyIk3c",
            "shortsUrl": "https://www.youtube.com/shorts/8Heg7Aomqwk",
        }
        for key, value in expected.items():
            if release.get(key) != value:
                errors.append(f"canonical {key} mismatch")
        if release.get("credits") != {"artist": "榎本魅愛"}:
            errors.append("canonical artist-only credit mismatch")
        if release.get("lyricist") or release.get("composer"):
            errors.append("removed lyricist/composer remains in canonical release")
        if release.get("lyricsText") != source_lyrics:
            errors.append("canonical lyric text differs from master")

    lyrics_path = ROOT / f"lyrics/{SLUG}/index.html"
    if not lyrics_path.is_file():
        errors.append("published Lyrics page missing")
    else:
        source = lyrics_path.read_text(encoding="utf-8")
        parser = LyricsParser()
        parser.feed(source)
        rendered = "".join(parser.parts)
        if rendered != source_lyrics:
            errors.append("rendered Lyrics text differs from master")
        for marker in (TITLE, "アーティスト：榎本魅愛", "SUZUKA WITH CARE", "giTYuKyIk3c"):
            if marker not in source:
                errors.append(f"Lyrics page marker missing: {marker}")
        for removed in ("作詞：JUN", "作曲：SUNO"):
            if removed in source:
                errors.append(f"removed credit remains on Lyrics page: {removed}")

    required_pages = {
        "index.html": (TITLE, f"lyrics/{SLUG}/", "giTYuKyIk3c"),
        f"releases/{SLUG}/index.html": (TITLE, "<dt>アーティスト</dt><dd>榎本魅愛</dd>"),
        "features/suzuka-with-care/index.html": (TITLE, f"lyrics/{SLUG}/", "夢と介護は　つながってる"),
        "artists/enomoto-mia/index.html": (TITLE, f"lyrics/{SLUG}/"),
        "discography/index.html": (TITLE,),
        f"news/{SLUG}-release/index.html": (TITLE,),
    }
    for relative, markers in required_pages.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative}: marker missing: {marker}")
        if relative in {f"releases/{SLUG}/index.html", "features/suzuka-with-care/index.html"}:
            for removed in ("作詞：JUN", "作曲：SUNO"):
                if removed in text:
                    errors.append(f"{relative}: removed credit remains: {removed}")

    public_old = []
    for path in ROOT.rglob("*.html"):
        if path.relative_to(ROOT).parts[0] == "admin":
            continue
        if OLD_TITLE in path.read_text(encoding="utf-8", errors="ignore"):
            public_old.append(str(path.relative_to(ROOT)))
    for relative in ("assets/data/search-v31.json", "assets/data/releases-catalog.json"):
        if OLD_TITLE in (ROOT / relative).read_text(encoding="utf-8"):
            public_old.append(relative)
    if public_old:
        errors.append("old public title remains: " + ", ".join(public_old))

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    if f"https://www.suzukaofficial.com/lyrics/{SLUG}/" not in sitemap:
        errors.append("Lyrics URL missing from sitemap")

    if errors:
        print("Yume/Kaigo Lyrics audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS",
        "title": TITLE,
        "oldPublicTitleOccurrences": 0,
        "lyricsCharacters": len(source_lyrics),
        "lyricsTextSha256": hashlib.sha256(source_lyrics.encode("utf-8")).hexdigest(),
        "officialMv": "giTYuKyIk3c",
        "officialShort": "8Heg7Aomqwk",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

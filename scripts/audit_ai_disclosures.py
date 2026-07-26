#!/usr/bin/env python3
"""Validate visible and structured AI-artist disclosures."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE_CLASSES = (
    "ai-footer-disclosure",
    "ai-artist-note",
    "ai-work-disclosure",
    "ai-news-disclosure",
)
SEO_EXCLUDED_PHRASES = (
    "AIアーティスト",
    "オリジナルAI音楽プロジェクト",
    "架空のアーティスト",
)
ALLOWED_SAME_AS_HOSTS = {
    "bellflower1209.github.io",
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "www.instagram.com",
    "instagram.com",
}


def walk(value: object, errors: list[str], page: Path) -> None:
    if isinstance(value, dict):
        schema_type = value.get("@type")
        schema_types = schema_type if isinstance(schema_type, list) else [schema_type]
        if any(item in {"Person", "MusicGroup"} for item in schema_types) and value.get("name"):
            description = str(value.get("description", ""))
            if "架空" not in description and "fictional" not in description.lower():
                errors.append(f"{page}: Person/MusicGroup description lacks fictional AI context")
        if "sameAs" in value:
            same_as = value["sameAs"]
            urls = same_as if isinstance(same_as, list) else [same_as]
            for url in urls:
                host = urllib.parse.urlsplit(str(url)).netloc.lower()
                if host and host not in ALLOWED_SAME_AS_HOSTS:
                    errors.append(f"{page}: unsupported sameAs host: {host}")
        for child in value.values():
            walk(child, errors, page)
    elif isinstance(value, list):
        for child in value:
            walk(child, errors, page)


def main() -> int:
    errors: list[str] = []
    pages = [
        ROOT / "index.html",
        *sorted(ROOT.glob("*/index.html")),
        *sorted(ROOT.glob("*/*/index.html")),
    ]
    pages = list(dict.fromkeys(path for path in pages if path.is_file()))
    for path in pages:
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        is_noindex_redirect = bool(
            re.search(
                r'<meta name="robots" content="[^"]*noindex',
                source,
                re.IGNORECASE,
            )
        )
        if is_noindex_redirect:
            continue
        for required in ("ai-disclosure.css", "ai-footer-disclosure"):
            if required not in source:
                errors.append(f"{relative}: missing {required}")
        expected_counts = {"ai-footer-disclosure": 1}
        if relative.parts[0] == "artists" and len(relative.parts) == 3:
            if "ai-artist-note" not in source:
                errors.append(f"{relative}: missing AI artist badge")
            expected_counts["ai-artist-note"] = 1
        if relative.parts[0] == "releases" and len(relative.parts) == 3:
            if "ai-work-disclosure" not in source:
                errors.append(f"{relative}: missing release disclosure")
            expected_counts["ai-work-disclosure"] = 1
        if relative.parts[0] == "news" and len(relative.parts) == 3:
            if "ai-news-disclosure" not in source:
                errors.append(f"{relative}: missing News disclosure")
            expected_counts["ai-news-disclosure"] = 1
        for class_name, expected in expected_counts.items():
            actual = len(
                re.findall(
                    rf'class="[^"]*\b{re.escape(class_name)}\b[^"]*"',
                    source,
                )
            )
            if actual != expected:
                errors.append(
                    f"{relative}: {class_name} appears {actual} time(s), expected {expected}"
                )

        seo_fields = {
            "title": re.findall(r"<title>(.*?)</title>", source, re.DOTALL | re.IGNORECASE),
            "meta description": re.findall(
                r'<meta\s+name="description"\s+content="([^"]*)"',
                source,
                re.IGNORECASE,
            ),
            "og:title": re.findall(
                r'<meta\s+property="og:title"\s+content="([^"]*)"',
                source,
                re.IGNORECASE,
            ),
        }
        for field_name, values in seo_fields.items():
            for value in values:
                if any(phrase in value for phrase in SEO_EXCLUDED_PHRASES):
                    errors.append(
                        f"{relative}: AI disclosure phrase leaked into {field_name}"
                    )
        for raw in re.findall(
            r'<script(?: id="[^"]+")? type="application/ld\+json">(.*?)</script>',
            source,
            re.DOTALL,
        ):
            try:
                walk(json.loads(raw), errors, relative)
            except json.JSONDecodeError as error:
                errors.append(f"{relative}: invalid JSON-LD: {error}")

    checks = {
        ROOT / "index.html": "オリジナルAI音楽プロジェクト",
        ROOT / "about/index.html": "SUZUKAのAIアーティストについて",
        ROOT / "artists/index.html": "オリジナルの架空アーティスト",
        ROOT / "social/index.html": "AIアーティストによるオリジナル楽曲",
    }
    for path, phrase in checks.items():
        if phrase not in path.read_text(encoding="utf-8"):
            errors.append(f"{path.relative_to(ROOT)}: missing required phrase: {phrase}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"AI disclosure audit failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"AI disclosure audit passed: {len(pages)} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

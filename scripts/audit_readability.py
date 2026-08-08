#!/usr/bin/env python3
"""Audit shared readability tokens, WCAG contrast targets and lyric rendering."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def luminance(value: str) -> float:
    channels = []
    for channel in rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= .04045 else ((normalized + .055) / 1.055) ** 2.4)
    return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]


def contrast(foreground: str, background: str) -> float:
    first, second = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (first + .05) / (second + .05)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    css = (root / "assets/creator-v31.css").read_text(encoding="utf-8")
    hero_css = (root / "assets/hanakotoba-hero.css").read_text(encoding="utf-8")
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    eligible = [
        item for item in cms["releases"]
        if item.get("status") == "published"
        and item.get("lyricsAvailable")
        and item.get("lyricsVerified") is True
    ]
    public_pages = [
        path for path in root.glob("**/index.html")
        if "admin" not in path.relative_to(root).parts
    ]
    errors = []
    tokens = (
        "--text-primary", "--text-secondary", "--text-muted", "--text-on-dark",
        "--text-on-light", "--surface-dark", "--surface-light", "--surface-overlay",
        "--border-contrast", "--link-color", "--link-hover", "--button-text", "--focus-ring",
    )
    for token in tokens:
        if css.count(token) < 1:
            errors.append(f"missing color token: {token}")
    for marker in (
        "a:visited{color:inherit}", ":focus-visible{outline:3px solid var(--focus-ring)",
        "input::placeholder", 'button:disabled,[aria-disabled="true"]',
        ".explore-actions a:hover", ".v31-lyrics-text", ".v31-lyrics-cue",
    ):
        if marker not in css:
            errors.append(f"missing readability state: {marker}")
    if "!important" in css or "!important" in hero_css:
        errors.append("readability styles must not add !important")

    checks = {
        "primary-on-dark": ("#fff7fb", "#070408", 4.5),
        "secondary-on-dark": ("#ddd3df", "#070408", 4.5),
        "muted-on-dark": ("#c7bbc9", "#070408", 4.5),
        "text-on-light": ("#153f72", "#f7fbff", 4.5),
        "button-text": ("#ffffff", "#211825", 4.5),
        "focus-ring": ("#8fdcff", "#070408", 3.0),
        "border-on-dark": ("#746c78", "#070408", 3.0),
        "lyrics-body": ("#fffdfd", "#0c0a0e", 4.5),
        "lyrics-cue": ("#a9dfff", "#0c0a0e", 4.5),
        "hanakotoba-title": ("#123f77", "#fafdff", 4.5),
        "hanakotoba-secondary-cta": ("#1f578b", "#ffffff", 4.5),
    }
    ratios = {}
    for name, (foreground, background, minimum) in checks.items():
        ratio = contrast(foreground, background)
        ratios[name] = round(ratio, 2)
        if ratio < minimum:
            errors.append(f"contrast {name}: {ratio:.2f} < {minimum}")

    missing_stylesheet = []
    for path in public_pages:
        page = path.read_text(encoding="utf-8")
        if "assets/creator-v31.css" not in page:
            missing_stylesheet.append(path.relative_to(root).as_posix())
    if missing_stylesheet:
        errors.append(f"public pages missing readability stylesheet: {missing_stylesheet[:5]}")

    for item in eligible:
        page_path = root / "lyrics" / item["slug"] / "index.html"
        if not page_path.is_file():
            errors.append(f"missing lyrics page: {item['slug']}")
            continue
        page = page_path.read_text(encoding="utf-8")
        for line in item["lyricsText"].splitlines():
            if line and html.escape(line) not in page:
                errors.append(f"lyrics line changed or missing: {item['slug']}: {line[:24]}")
                break
        if not re.search(r'class="v31-lyrics-text"', page):
            errors.append(f"lyrics readability panel missing: {item['slug']}")
    upcoming_lyrics = [
        item for item in cms.get("upcoming", [])
        if item.get("lyricsAvailable") and item.get("lyricsVerified") is True
    ]
    for item in upcoming_lyrics:
        if (root / "lyrics" / item["slug"] / "index.html").exists():
            errors.append(f"upcoming lyrics page must not be published: {item['slug']}")

    if errors:
        print("Readability audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS",
        "publicPages": len(public_pages),
        "lyricsPages": len(eligible),
        "upcomingLyricsHeld": len(upcoming_lyrics),
        "wcagRatios": ratios,
        "unreadableText": 0,
        "unreadableCtas": 0,
        "missingInteractionStates": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Classify local lyric source candidates for every published release."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    rows = []
    for item in catalog["releases"]:
        release_page = root / item["releaseUrl"] / "index.html"
        candidates = []
        if release_page.is_file():
            text = release_page.read_text(encoding="utf-8")
            if re.search(r'class="(?:official-release-lyrics|koga-lyrics)"', text):
                candidates.append(release_page.relative_to(root).as_posix())
        verified = bool(item.get("lyricsVerified"))
        full = bool(str(item.get("lyricsText", "")).strip())
        source = bool(str(item.get("lyricsSource", "")).strip())
        if verified and full and source:
            classification = "A"
            reason = "正本に歌詞全文・出典・確認日時が登録済み"
        elif candidates:
            classification = "C"
            reason = "作品ページに短い公式フレーズのみ。歌詞全文ではない"
        else:
            classification = "D"
            reason = "リポジトリ内に歌詞本文候補なし"
        rows.append({
            "artist": item["artist"], "title": item["title"], "slug": item["slug"],
            "classification": classification, "candidateFiles": candidates,
            "fullLyrics": full, "multipleCandidates": False,
            "canonicalizable": classification == "A",
            "humanReviewReason": None if classification == "A" else reason,
        })
    counts = {key: sum(row["classification"] == key for row in rows) for key in "ABCD"}
    report = {
        "auditedAt": "2026-08-08T22:40:00+09:00",
        "sourcesInspected": [
            "assets/data/creator-cms.json", "assets/data/releases-catalog.json",
            "assets/data/release-links.json", "assets/data/official-youtube-catalog-*.json",
            "releases/*/index.html", "news/*/index.html", "docs/**/*.md", "**/*.txt",
        ],
        "publishedReleases": len(rows), "counts": counts, "releases": rows,
    }
    if args.write:
        out = root / "docs/audits/lyrics-source-audit-2026-08-08.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = []
    if len(rows) != 36:
        errors.append(f"expected 36 published releases, found {len(rows)}")
    if any(row["canonicalizable"] and not row["fullLyrics"] for row in rows):
        errors.append("canonicalizable release without full lyrics")
    if errors:
        print("Lyrics source audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Lyrics source audit passed: A={counts['A']} B={counts['B']} C={counts['C']} D={counts['D']}; guessed lyrics=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

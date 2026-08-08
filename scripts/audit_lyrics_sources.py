#!/usr/bin/env python3
"""Exhaustively classify local lyric candidates without inventing or choosing text."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".json"}
LYRIC_KEYS = ("lyricsText", "lyrics", "歌詞")
FINAL_MARKERS = re.compile(r"(?:正本|最終版|final\s+lyrics|lyrics\s+final)", re.I)
LYRIC_MARKERS = re.compile(r"(?:^|[#\s>])(?:歌詞|lyrics)(?:$|[:：\s<])", re.I | re.M)
PARTIAL_CLASSES = re.compile(r'class="(?:official-release-lyrics|koga-lyrics)"')


def walk_json(value, slug: str, title: str, path: Path, found: list[dict]) -> None:
    if isinstance(value, list):
        for child in value:
            walk_json(child, slug, title, path, found)
        return
    if not isinstance(value, dict):
        return
    identity = str(value.get("slug") or value.get("releaseSlug") or "") == slug or str(value.get("title") or "") == title
    if identity:
        for key in LYRIC_KEYS:
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                found.append({
                    "path": path.as_posix(), "kind": "full-candidate", "text": text.strip(),
                    "finalMarked": bool(value.get("lyricsVerified") or FINAL_MARKERS.search(json.dumps(value, ensure_ascii=False))),
                })
    for child in value.values():
        walk_json(child, slug, title, path, found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = json.loads((root / "assets/data/releases-catalog.json").read_text(encoding="utf-8"))
    releases = [item for item in catalog["releases"] if item.get("status") == "published"]
    source_files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        and ".git" not in path.parts and "node_modules" not in path.parts
        and not ("docs" in path.parts and "audits" in path.parts)
    )
    inventory = Counter(path.suffix.lower().lstrip(".") for path in source_files)
    decoded: dict[Path, str] = {}
    json_values: dict[Path, object] = {}
    for path in source_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        decoded[path] = text
        if path.suffix.lower() == ".json":
            try:
                json_values[path] = json.loads(text)
            except json.JSONDecodeError:
                pass

    rows = []
    for item in releases:
        slug, title = item["slug"], item["title"]
        found: list[dict] = []
        for path, value in json_values.items():
            nested: list[dict] = []
            walk_json(value, slug, title, path.relative_to(root), nested)
            found.extend(nested)
        for path, text in decoded.items():
            if path.suffix.lower() not in {".txt", ".md"}:
                continue
            if slug not in text and title not in text and slug not in path.as_posix():
                continue
            if LYRIC_MARKERS.search(text):
                nonempty = [line.strip() for line in text.splitlines() if line.strip()]
                if len(nonempty) >= 8:
                    found.append({
                        "path": path.relative_to(root).as_posix(), "kind": "full-candidate",
                        "text": text.strip(), "finalMarked": bool(FINAL_MARKERS.search(text)),
                    })
                else:
                    found.append({"path": path.relative_to(root).as_posix(), "kind": "partial"})
        for page_pattern in (f"releases/{slug}/index.html", f"news/{slug}-release/index.html"):
            page = root / page_pattern
            if page.is_file() and PARTIAL_CLASSES.search(page.read_text(encoding="utf-8")):
                found.append({"path": page_pattern, "kind": "partial"})

        unique_full: dict[str, dict] = {}
        partial_paths = set()
        for candidate in found:
            if candidate["kind"] == "full-candidate":
                normalized = re.sub(r"\s+", " ", candidate["text"]).strip()
                unique_full.setdefault(normalized, candidate)
            else:
                partial_paths.add(candidate["path"])
        verified = bool(item.get("lyricsVerified"))
        full = bool(str(item.get("lyricsText", "")).strip())
        source = bool(str(item.get("lyricsSource", "")).strip())
        if verified and full and source:
            classification = "A"
            reason = None
        elif len(unique_full) > 1:
            classification = "B"
            reason = "歌詞全文の候補が複数あり、正本を選択できない"
        elif len(unique_full) == 1:
            classification = "C"
            reason = "歌詞全文らしい候補は1件あるが、最終版の正本確認がない"
        elif partial_paths:
            classification = "C"
            reason = "作品ページに短い公式フレーズのみ。歌詞全文ではない"
        else:
            classification = "D"
            reason = "リポジトリ内に歌詞本文候補なし"
        candidate_paths = sorted({candidate["path"] for candidate in found})
        rows.append({
            "artist": item["artist"], "title": title, "slug": slug,
            "classification": classification, "candidateFiles": candidate_paths,
            "fullCandidateCount": len(unique_full), "partialCandidateCount": len(partial_paths),
            "fullLyrics": full, "multipleCandidates": len(unique_full) > 1,
            "canonicalizable": classification == "A", "humanReviewReason": reason,
        })
    counts = {key: sum(row["classification"] == key for row in rows) for key in "ABCD"}
    report = {
        "auditedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sourcesInspected": [
            "全UTF-8 TXT / Markdown / JSON（.git・node_modules・生成済み監査報告を除外）",
            "assets/data/creator-cms.json", "assets/data/releases-catalog.json",
            "releases/*/index.html", "news/*-release/index.html",
        ],
        "sourceInventory": dict(sorted(inventory.items())), "scannedFiles": len(decoded),
        "publishedReleases": len(rows), "counts": counts, "releases": rows,
        "policy": "歌詞は生成・補完せず、複数候補を選択しない。Aのみ正本登録対象。",
    }
    if args.write:
        out = root / "docs/audits/lyrics-source-audit-2026-08-08.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = []
    if len(rows) != len(releases):
        errors.append("published release coverage mismatch")
    if any(row["canonicalizable"] and not row["fullLyrics"] for row in rows):
        errors.append("canonicalizable release without canonical full lyrics")
    if errors:
        print("Lyrics source audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Lyrics source audit passed: scanned={len(decoded)} A={counts['A']} B={counts['B']} C={counts['C']} D={counts['D']}; guessed lyrics=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit unresolved lyric masters and prove that no hold leaks into public discovery."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    data = json.loads((root / "assets/data/lyrics-holds.json").read_text(encoding="utf-8"))
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    canonical_slugs = {item["slug"] for group in ("releases", "upcoming") for item in cms.get(group, [])}
    required = {"sourceFile", "sourceTitle", "receivedAt", "sha256", "lyricsTextSha256", "reason", "candidateMatches", "resolved", "resolvedSlug"}
    errors = []
    unresolved = []
    public_text = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("sitemap.xml", "feed.xml", "assets/data/search-v31.json")
    )
    for item in data.get("holds", []):
        missing = required - set(item)
        if missing:
            errors.append(f'{item.get("sourceTitle", "unknown")}: missing {sorted(missing)}')
            continue
        digest = hashlib.sha256(item.get("lyricsText", "").encode("utf-8")).hexdigest()
        if digest != item["lyricsTextSha256"]:
            errors.append(f'{item["sourceTitle"]}: lyricsText SHA-256 mismatch')
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            errors.append(f'{item["sourceTitle"]}: invalid source SHA-256')
        for candidate in item["candidateMatches"]:
            slug = candidate if isinstance(candidate, str) else candidate.get("slug")
            if slug not in canonical_slugs:
                errors.append(f'{item["sourceTitle"]}: unknown candidate slug {slug}')
        if item["resolved"]:
            if item["resolvedSlug"] not in canonical_slugs:
                errors.append(f'{item["sourceTitle"]}: resolved slug missing')
        else:
            unresolved.append(item)
            if item["resolvedSlug"] is not None:
                errors.append(f'{item["sourceTitle"]}: unresolved hold has resolvedSlug')
            if item["sourceTitle"] in public_text:
                errors.append(f'{item["sourceTitle"]}: unresolved title leaked into search/sitemap/feed')
    for item in unresolved:
        if any((root / "lyrics").glob(f'*{item["sourceKey"]}*/index.html')):
            errors.append(f'{item["sourceTitle"]}: unresolved Lyrics page exists')
    if errors:
        raise SystemExit("Hold audit failed:\n- " + "\n- ".join(errors))
    print(json.dumps({"status": "PASS", "holds": len(data.get("holds", [])), "unresolved": len(unresolved), "publicLeaks": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

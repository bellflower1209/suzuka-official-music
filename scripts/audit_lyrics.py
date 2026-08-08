#!/usr/bin/env python3
"""Audit source-verified lyrics publication."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    cms = json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))
    eligible = {item["slug"] for item in cms["releases"] if item.get("lyricsAvailable") and item.get("lyricsVerified") is True and str(item.get("lyricsVerifiedAt", "")).strip() and str(item.get("lyricsText", "")).strip() and str(item.get("lyricsSource", "")).strip()}
    actual = {path.parent.name for path in (root / "lyrics").glob("*/index.html")}
    errors = []
    if eligible != actual:
        errors.append(f"lyrics detail mismatch: eligible={sorted(eligible)} actual={sorted(actual)}")
    hub = (root / "lyrics/index.html").read_text(encoding="utf-8")
    for marker in ("公式歌詞", "BreadcrumbList", "CollectionPage", "data-lyrics-filter"):
        if marker not in hub:
            errors.append(f"lyrics hub missing {marker}")
    if errors:
        print("Lyrics audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Lyrics audit passed: {len(eligible)} verified detail pages; unverified lyrics are not published.")
    return 0

if __name__ == "__main__": raise SystemExit(main())

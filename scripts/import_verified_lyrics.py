#!/usr/bin/env python3
"""Attach a user-confirmed lyric master to an existing canonical release slug."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def atomic_json(path: Path, data: dict) -> None:
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def records(data: dict) -> dict[str, dict]:
    return {
        item["slug"]: item
        for collection in ("releases", "upcoming")
        for item in data.get(collection, [])
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--slug", required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--verified-at")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    raw = args.file.resolve().read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    source_title, separator, body = text.partition("\n")
    body = body.rstrip("\n")
    if not separator or not body.strip():
        raise SystemExit("The lyric file must contain a title line followed by the complete lyric body")
    if any(line.strip().startswith(("作詞：", "作曲：", "アーティスト：")) for line in body.splitlines()):
        raise SystemExit("Credit metadata must not be mixed into lyricsText")
    verified_at = args.verified_at or datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    paths = [root / "assets/data/creator-cms.json", root / "assets/data/releases-catalog.json"]
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    found = []
    for data in documents:
        item = records(data).get(args.slug)
        if not item:
            raise SystemExit(f"Unknown canonical slug: {args.slug}")
        if source_title != item["title"]:
            raise SystemExit(
                f"Title mismatch for {args.slug}: file={source_title!r} canonical={item['title']!r}. "
                "Do not infer or rewrite the title."
            )
        item.update({
            "lyricsAvailable": True,
            "lyricsVerified": True,
            "lyricsSource": f"user_confirmed_official_lyrics ({args.file.name})",
            "lyricsText": body,
            "lyricsVerifiedAt": verified_at,
        })
        found.append(item)
    result = {
        "status": "dry-run" if args.dry_run else "registered",
        "slug": args.slug,
        "title": found[0]["title"],
        "artist": found[0]["artist"],
        "releaseStatus": found[0]["status"],
        "publishable": found[0]["status"] == "published",
        "sourceSha256": source_sha,
        "lyricsTextSha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    if not args.dry_run:
        for path, data in zip(paths, documents):
            atomic_json(path, data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

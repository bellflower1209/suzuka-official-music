#!/usr/bin/env python3
"""Import the user-confirmed 2026-08-12 lyric masters without guessing metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCES = [
    {"filename": "lost_signal_suzuka_master.txt", "sourceTitle": "LOST SIGNAL", "slug": "lost-signal", "title": "LOST SIGNAL", "sha256": "0851c773bda6413610115e074a7e92cbf8c05f632b9d648db957058fe2bfc0f4"},
    {"filename": "caramel_suzuka_master.txt", "sourceTitle": "キャラメ〜ル", "slug": "caramel", "title": "キャラメ〜ル", "sha256": "b857070a1826bf1a03e498944d65aa8fbc4902fb948872124b3c47979a975020"},
    {"filename": "hajimemashite_kiseki_suzuka_master.txt", "sourceTitle": "はじめまして、奇跡", "slug": "hajimemashite-kiseki", "title": "はじめまして、奇跡", "sha256": "e46147fc0c9f30bf97009daba05545cd7b513fdf6e868e4d758f2ae74c8139af"},
    {"filename": "kamisama_wa_rusu_suzuka_master.txt", "sourceTitle": "神様は留守", "slug": "kamisama-wa-rusu", "title": "神様は留守", "sha256": "560e9d002b79ce5ba31d41f41a4d546cfceef8dac34b74f7f014e894a5bb1cca"},
    {"filename": "last_dance_tonight_suzuka_master.txt", "sourceTitle": "LAST DANCE TONIGHT", "slug": "last-dance-tonight", "title": "LAST DANCE TONIGHT", "sha256": "6fe12d4c3f275d150fcac95bd9fcecf329eeff33106724ac520db6c45a8748b4"},
    {"filename": "shadow_code_suzuka_master.txt", "sourceTitle": "SHADOW//CODE", "slug": "shadow-code", "title": "SHADOW//CODE", "sha256": "d4148bbc70057e52e008e91bd276d39f3ec54dd3f92201f7c5625286a2384ea9"},
    {"filename": "leo_rise_again_suzuka_master.txt", "sourceTitle": "LEO-Rise Again-", "slug": "leo-rise-again", "title": "LEO — Rise Again —", "sha256": "fdcc74fb2375e75b31312f49d03d719bdbfaaf914b12740ecfa0e89d81dd51c9"},
    {"filename": "monsoon_promise_suzuka_master.txt", "sourceTitle": "Monsoon Promise", "slug": "monsoon-promise", "title": "Monsoon Promise", "sha256": "52416d49e54bf161f5d2846a1f449fc4f58957a79547170aec0bf97090405c69"},
    {"filename": "false_dentity_suzuka_master.txt", "sourceTitle": "FALSE//DENTITY", "sourceKey": "false-dentity-unmatched", "sha256": "907bf439455a715e1735c7b1d85aaa602fa6ea967593be77ce294fa11060d651"},
    {"filename": "our_generation_suzuka_master.txt", "sourceTitle": "OUR GENERATION", "sourceKey": "our-generation-unmatched", "sha256": "6be2fa0dd8d9f87f844696eb67484659321a8a98bab2359662e60432b727af9a"}
]

CONFIRMED_HOLD_METADATA = {
    "our-generation-unmatched": {
        "artist": "ASTERIA",
        "confirmedMetadata": {
            "artist": "ASTERIA", "lyricist": "JUN", "composer": "SUNO",
            "source": "user_confirmed",
        },
        "reason": "Artist=ASTERIAはユーザー確認済みだが、既存Release・公式YouTube・Scheduleに同名作品がない",
    },
    "false-dentity-unmatched": {
        "artist": "",
        "reason": "公式YouTubeにFALSE//IDENTITYが公開されたが、提供正本の表記FALSE//DENTITYと同一作品かは未確認",
    },
}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_source(source_dir: Path, definition: dict) -> dict:
    path = source_dir / definition["filename"]
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != definition["sha256"]:
        raise SystemExit(f"SHA-256 mismatch: {path.name}: {digest}")
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    first, separator, body = text.partition("\n")
    if first != definition["sourceTitle"] or not separator:
        raise SystemExit(f"Title mismatch: {path.name}: {first!r}")
    lyrics = body.rstrip("\n")
    if not lyrics.strip():
        raise SystemExit(f"Empty lyrics: {path.name}")
    metadata_lines = [
        line for line in lyrics.splitlines()
        if line.strip().startswith(("作詞：", "作曲：", "アーティスト："))
    ]
    if metadata_lines:
        raise SystemExit(f"Metadata line remains in lyric body: {path.name}")
    return {
        **definition,
        "lyricsText": lyrics,
        "lyricsTextSha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
    }


def update_canonical(data: dict, loaded: list[dict], verified_at: str) -> dict[str, dict]:
    items = {
        item["slug"]: item
        for collection in ("releases", "upcoming")
        for item in data.get(collection, [])
    }
    attached = {}
    for source in loaded:
        slug = source.get("slug")
        if not slug:
            continue
        item = items.get(slug)
        if not item:
            raise SystemExit(f"Canonical release missing: {slug}")
        if item.get("title") != source["title"]:
            raise SystemExit(
                f'Canonical title mismatch: {slug}: {item.get("title")} != {source["title"]}'
            )
        item.update({
            "lyricsAvailable": True,
            "lyricsSource": f'ユーザー提供・SUZUKA公式歌詞正本（{source["filename"]}）',
            "lyricsText": source["lyricsText"],
            "lyricsVerified": True,
            "lyricsVerifiedAt": verified_at,
        })
        attached[slug] = item
    data["updatedAt"] = verified_at
    return attached


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verified-at", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    loaded = [load_source(args.source_dir.resolve(), definition) for definition in SOURCES]

    attached_sets = []
    attached_records = {}
    for relative in ("assets/data/creator-cms.json", "assets/data/releases-catalog.json"):
        path = root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        attached = update_canonical(data, loaded, args.verified_at)
        attached_sets.append(set(attached))
        if relative.endswith("creator-cms.json"):
            attached_records = attached
        write_json(path, data)
    expected = {source["slug"] for source in loaded if source.get("slug")}
    if any(value != expected for value in attached_sets):
        raise SystemExit(f"Canonical coverage mismatch: expected={sorted(expected)} actual={attached_sets}")

    manifest_path = root / "assets/data/lyrics-sources.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = {
        item.get("slug") or item.get("sourceKey"): item
        for item in manifest.get("sources", [])
    }
    for source in loaded:
        key = source.get("slug") or source["sourceKey"]
        item = attached_records.get(source.get("slug", ""))
        existing[key] = {
            **({"slug": source["slug"]} if source.get("slug") else {"sourceKey": source["sourceKey"]}),
            "title": item["title"] if item else source["sourceTitle"],
            "sourceTitle": source["sourceTitle"],
            "artist": item["artist"] if item else CONFIRMED_HOLD_METADATA.get(source.get("sourceKey", ""), {}).get("artist", ""),
            "filename": source["filename"],
            "sha256": source["sha256"],
            "lyricsTextSha256": source["lyricsTextSha256"],
            "registrationStatus": "registered" if item else "held-unmatched",
            "publishedAtImport": bool(item and item.get("status") == "published"),
            "holdReason": "" if item else CONFIRMED_HOLD_METADATA.get(source.get("sourceKey", ""), {}).get("reason", "既存正本と公式YouTubeに一致作品がないため保留"),
        }
    manifest.update({
        "schemaVersion": "1.1",
        "verifiedAt": args.verified_at,
        "policy": "ユーザー本人が提供した公式歌詞正本のみ。本文の生成・補完・改変は禁止。作品照合できない歌詞は原文ハッシュを保持し公開しない。",
        "sources": sorted(existing.values(), key=lambda item: item.get("slug") or item["sourceKey"]),
    })
    write_json(manifest_path, manifest)
    holds = []
    for source in loaded:
        if source.get("slug"):
            continue
        metadata = CONFIRMED_HOLD_METADATA.get(source["sourceKey"], {})
        holds.append({
            "sourceKey": source["sourceKey"],
            "sourceTitle": source["sourceTitle"],
            "sourceFile": source["filename"],
            "filename": source["filename"],
            "receivedAt": verified_at,
            "sha256": source["sha256"],
            "lyricsTextSha256": source["lyricsTextSha256"],
            "lyricsText": source["lyricsText"],
            "status": "held-unmatched",
            "reason": metadata.get("reason", "既存正本と公式YouTubeに一致作品がないため保留"),
            "holdReason": metadata.get("reason", "既存正本と公式YouTubeに一致作品がないため保留"),
            **({"confirmedMetadata": metadata["confirmedMetadata"]} if metadata.get("confirmedMetadata") else {}),
            "candidateMatches": [],
            "resolved": False,
            "resolvedSlug": None,
        })
    write_json(root / "assets/data/lyrics-holds.json", {
        "schemaVersion": "1.2",
        "verifiedAt": args.verified_at,
        "publicationPolicy": "作品・Artist・slugの正本照合完了まで公開、検索、sitemap、feedへ含めない。",
        "holds": holds,
    })
    held = [source["sourceTitle"] for source in loaded if not source.get("slug")]
    published = [slug for slug, item in attached_records.items() if item.get("status") == "published"]
    print(json.dumps({
        "masters": len(loaded), "registered": len(expected), "heldUnmatched": held,
        "publishedEligible": len(published), "upcomingHeld": len(expected) - len(published),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

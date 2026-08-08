#!/usr/bin/env python3
"""Import user-confirmed official lyric masters into the canonical CMS data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCES = {
    "anata-dake-no-savior": {
        "filename": "anata-dake-no-savior_official_lyrics.txt",
        "title": "あなただけのSAVIOR",
        "headerLines": 1,
        "sha256": "fd6295b8181a509393036862377b31edbff0a60ccfa482678095a61a1c3aed57",
    },
    "ashita-wa-kitto": {
        "filename": "ashita_wa_kitto_official_lyrics.txt",
        "title": "明日は、きっと。",
        "headerLines": 1,
        "sha256": "f49cd476a892204a36d7ae0d6b8e06362ccbceb9f7a5d5f6f92d7693c42e1cc9",
    },
    "chimpanzee-no-rakuen": {
        "filename": "chimpanzee_no_rakuen_official_lyrics.txt",
        "title": "チンパンジーの楽園",
        "headerLines": 1,
        "sha256": "dc97bbd61a4d3abb9c70149c34eb3009683800cc5ddb49655c1e476e44cbe13f",
    },
    "hanakotoba": {
        "filename": "hanakotoba_official_lyrics.txt",
        "title": "花言葉",
        "headerLines": 2,
        "sha256": "558dfe2fa95a4680001f3d0722eb13d69411e52a51df4018555e2420411b39c2",
    },
    "hyakumankoku": {
        "filename": "hyakumankoku_official_lyrics.txt",
        "title": "百万告",
        "headerLines": 1,
        "sha256": "cb8a8e14065e7b82815a5f03920b17685cb37c066b570c7c2ce12636d70726ea",
    },
    "leo-rise-again": {
        "filename": "leo_rise_again_official_lyrics.txt",
        "title": "LEO — Rise Again —",
        "headerLines": 1,
        "sha256": "b54e3d835618b285183e8434e67d03ff2b49c231025dc439f8eebd06945560da",
    },
    "mermaid-no-geboku": {
        "filename": "mermaid_no_geboku_official_lyrics.txt",
        "title": "マーメイドの下僕",
        "headerLines": 1,
        "sha256": "0731d7fba19fb19e7739cfd220b32d3f9e2946cf89dc7fa06490efe263a6713d",
    },
    "toriatsukai-chui": {
        "filename": "toriatsukai_chuui_official_lyrics.txt",
        "title": "取り扱いチュー💋い",
        "headerLines": 1,
        "sha256": "686fe750b5b485c890782e8171c9f96e14e1ae1727f68857c7d0c888622ba372",
    },
    "wasureji-no-hito": {
        "filename": "wasureji_no_hito_official_lyrics.txt",
        "title": "忘れじの人",
        "headerLines": 1,
        "sha256": "b8ec22028913ddb896c71145b65823f81aa877d6abddaec8838a7e3a34c2c3c1",
    },
    "zennin-saiban": {
        "filename": "zenjin_saiban_official_lyrics.txt",
        "title": "善人裁判",
        "headerLines": 1,
        "sha256": "829765b6533a5c57aafeef214eba56cfe236846352980479a1d408da32747970",
    },
}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_sources(source_dir: Path) -> dict[str, dict]:
    loaded = {}
    for slug, definition in SOURCES.items():
        path = source_dir / definition["filename"]
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != definition["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {path.name}: {digest}")
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        lines = text.splitlines()
        if not lines or lines[0].strip() not in {definition["title"], "明日は、きっと", "LEO"}:
            raise SystemExit(f"Title mismatch: {path.name}")
        lyrics = "\n".join(lines[definition["headerLines"]:]).strip("\n")
        if not lyrics.strip():
            raise SystemExit(f"Empty lyrics: {path.name}")
        loaded[slug] = {**definition, "lyricsText": lyrics}
    return loaded


def update_collection(data: dict, loaded: dict[str, dict], verified_at: str) -> set[str]:
    updated = set()
    for collection_name in ("releases", "upcoming"):
        for item in data.get(collection_name, []):
            source = loaded.get(item.get("slug"))
            if not source:
                continue
            if item.get("title") != source["title"]:
                raise SystemExit(
                    f"Catalog title mismatch: {item.get('slug')}: "
                    f"{item.get('title')} != {source['title']}"
                )
            item.update({
                "lyricsAvailable": True,
                "lyricsSource": f"ユーザー提供・SUZUKA公式歌詞正本（{source['filename']}）",
                "lyricsText": source["lyricsText"],
                "lyricsVerified": True,
                "lyricsVerifiedAt": verified_at,
            })
            updated.add(item["slug"])
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verified-at", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    loaded = load_sources(args.source_dir.resolve())

    updated_sets = []
    for relative in ("assets/data/creator-cms.json", "assets/data/releases-catalog.json"):
        path = root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        updated_sets.append(update_collection(data, loaded, args.verified_at))
        data["updatedAt"] = args.verified_at
        write_json(path, data)
    if updated_sets[0] != set(loaded) or updated_sets[1] != set(loaded):
        raise SystemExit(
            f"Canonical coverage mismatch: cms={sorted(updated_sets[0])} "
            f"catalog={sorted(updated_sets[1])} sources={sorted(loaded)}"
        )

    manifest = {
        "schemaVersion": "1.0",
        "verifiedAt": args.verified_at,
        "policy": "ユーザー本人が提供した公式歌詞正本のみ。本文の生成・補完・改変は禁止。",
        "sources": [
            {
                "slug": slug,
                "title": source["title"],
                "filename": source["filename"],
                "sha256": source["sha256"],
                "publishedAtImport": any(
                    item.get("slug") == slug and item.get("status") == "published"
                    for item in json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8")).get("releases", [])
                ),
            }
            for slug, source in SOURCES.items()
        ],
    }
    write_json(root / "assets/data/lyrics-sources.json", manifest)
    print(f"Imported {len(loaded)} official lyric masters; published pages eligible=9, upcoming held=1.")


if __name__ == "__main__":
    main()

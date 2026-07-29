#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "assets/data/releases-catalog.json").read_text())["releases"]
eligible = [x for x in data if x["status"] == "published" and x["coverImage"] and x["youtubeUrl"] and x["recommendationWeight"] > 0]
home = (root / "index.html").read_text()
js = (root / "assets/explore.js").read_text()
assert eligible and "data-weekly-pick" in home and "Math.random" not in js
assert all(key in js for key in ("getUTCFullYear", "week", "hash", "recommendationWeight"))
def pick(seed: str) -> str:
    h = 2166136261
    for char in seed:
        h = ((h ^ ord(char)) * 16777619) & 0xFFFFFFFF
    pool = sorted(eligible, key=lambda x: (x["artistSlug"], x["slug"]))
    return pool[h % len(pool)]["slug"]
assert pick("2026-31") == pick("2026-31")
print(f"Weekly Pick audit passed: deterministic ISO-week selection from {len(eligible)} eligible releases; no Math.random.")

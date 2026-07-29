#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "assets/data/releases-catalog.json").read_text())["releases"]
genres = {"j-pop": "J-POP", "enka": "演歌", "k-pop-inspired": "K-POP風", "visual-kei": "V系"}
for slug, name in genres.items():
    count = sum(name in x["genres"] for x in data)
    text = (root / "genres" / slug / "index.html").read_text()
    assert count > 0 and f'"numberOfItems":{count}' in text
    assert text.count('"@type":"ListItem"') >= count
print("Genre audit passed: " + ", ".join(f"{name}={sum(name in x['genres'] for x in data)}" for name in genres.values()))

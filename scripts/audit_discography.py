#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
catalog = json.loads((root / "assets/data/releases-catalog.json").read_text())
published = catalog["releases"]
assert len({x["slug"] for x in published}) == len(published)
assert [x["releaseDate"] for x in published] == sorted((x["releaseDate"] for x in published), reverse=True)
page = (root / "discography/index.html").read_text()
assert page.count('class="timeline-item"') == len(published)
assert "公開予定" in page and all(x["slug"] in page or x["title"] in page for x in catalog["upcoming"])
print(f"Discography audit passed: {len(published)} published releases, {len(catalog['upcoming'])} upcoming releases separated.")

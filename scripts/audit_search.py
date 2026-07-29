#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "assets/data/releases-catalog.json").read_text())["releases"]
page = (root / "search/index.html").read_text()
js = (root / "assets/explore.js").read_text()
assert data and all(x["status"] == "published" for x in data)
assert all(key in page for key in ("data-search-form", "data-search-results", "data-search-count", "aria-live"))
assert all(key in js for key in ("normalize(\"NFKC\")", "popstate", "URLSearchParams"))
assert "条件に一致" in page
for term in ("榎本魅愛", "えのもとみあ", "ECLYPSE", "演歌", "V系", "K-POP"):
    assert any(term.casefold() in " ".join(map(str, x["searchKeywords"] + x["genres"])).casefold() for x in data), term
print(f"Search audit passed: {len(data)} published releases are catalogued; normalization, URL state and empty state are present.")

#!/usr/bin/env python3
"""Sync approved canonical artwork into retained release and News templates."""
import html
import json
import re
from pathlib import Path

BASE = "https://www.suzukaofficial.com/"

def sync(root: Path) -> None:
    manifest = root / "assets/data/official-music-assets-20261007.json"
    if not manifest.exists():
        return
    rows = json.loads(manifest.read_text(encoding="utf-8"))["materials"]
    releases = {x["slug"]: x for x in json.loads((root / "assets/data/creator-cms.json").read_text(encoding="utf-8"))["releases"]}
    for row in rows:
        item = releases[row["slug"]]
        image = item["coverImage"]
        img = (f'<img src="../../{html.escape(image)}" alt="{html.escape(item["coverAlt"])}" '
               f'width="{item["coverWidth"]}" height="{item["coverHeight"]}"/>')
        for route in (item["releaseUrl"], item.get("newsUrl")):
            if not route:
                continue
            path = root / route / "index.html"
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            primary = re.search(r'<div class="release-detail-artwork">\s*<img\b[^>]*src="([^"]+)"', text)
            if not primary and route.startswith("news/"):
                primary = re.search(r'<div class="news-article-body[^"]*">\s*<section>\s*<img\b[^>]*src="([^"]+)"', text)
            previous_images = {row.get("previousCoverImage", "")}
            if primary:
                previous_images.add(primary[1])
            previous_images |= {BASE + value.removeprefix("../../").lstrip("/") for value in list(previous_images) if value and not value.startswith(("https://", "http://"))}
            previous_images.discard("")
            def update_graph(match):
                graph = json.loads(match[2])
                def visit(value, key=""):
                    if isinstance(value, dict):
                        return {name: visit(child, name) for name, child in value.items()}
                    if isinstance(value, list):
                        return [visit(child, key) for child in value]
                    if isinstance(value, str) and key in {"image", "thumbnailUrl", "url", "contentUrl"} and value in previous_images:
                        return BASE + image
                    return value
                return match[1] + json.dumps(visit(graph), ensure_ascii=False, separators=(",", ":")) + match[3]
            text = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', update_graph, text, flags=re.S)
            # Existing editorial text and links remain intact.
            text = re.sub(r'(<div class="release-detail-artwork">)\s*<img\b[^>]*>', lambda m: m[1] + img, text, count=1)
            if route.startswith("news/"):
                text = re.sub(r'(<div class="news-article-body[^"]*">\s*<section>)\s*<img\b[^>]*>', lambda m: m[1] + img, text, count=1)
            for attribute in ('property="og:image"', 'name="twitter:image"'):
                text = re.sub(r'(<meta ' + re.escape(attribute) + r' content=")[^"]*("/?>)', lambda m: m[1] + BASE + image + m[2], text)
            path.write_text(text, encoding="utf-8")

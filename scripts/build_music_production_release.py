#!/usr/bin/env python3
"""Extend the verified b355cf4 public V6 artifact with MUSIC PRODUCTION.

This builder starts from the release package deployed by Pages, never from the
older root HTML or the older official-sync baseline. It deliberately changes
only navigation, one independent home invitation, sitemap, and the three new
service files. No V6 runtime, artist data, or media is regenerated.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import io
import json
import os
import re
import tarfile
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from verify_public_release import read_release, verify_private_audio

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "b355cf47690bf3fe3fdc3c2863fd56108565f3dc"
BASE_URL = "https://www.suzukaofficial.com"
SERVICE_URL = BASE_URL + "/music-production/"
MANIFEST = "suzuka-v6-candidate-manifest.json"
SOURCE = Path("site-content/music-production")
NEW_FILES = {
    "music-production/index.html": SOURCE / "page.html.template",
    "assets/music-production.css": SOURCE / "music-production.css",
    "assets/music-production.js": SOURCE / "music-production.js",
}
MAIL_FIELDS = (
    "お名前・活動名", "依頼区分（個人・企業・施設・アーティスト）", "希望制作内容",
    "楽曲用途", "音楽ジャンル", "AI歌唱希望", "希望納期", "予算", "その他の要望",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mailto() -> str:
    body = "\n".join(f"{label}：\n" for label in MAIL_FIELDS)
    query = urllib.parse.urlencode({
        "subject": "SUZUKA 楽曲制作のご相談", "body": body,
    }, quote_via=urllib.parse.quote)
    return "mailto:1209bellflower@gmail.com?" + query


def insert_in_nav(page: str, pattern: str, link: str, *, required: bool = False) -> str:
    matches = list(re.finditer(pattern, page, flags=re.S))
    if not matches:
        if required:
            raise ValueError("Expected navigation is missing")
        return page
    if len(matches) != 1:
        raise ValueError("Navigation is ambiguous")
    match = matches[0]
    old = match.group(0)
    if 'href="/music-production/"' in old or 'href="../music-production/"' in old or 'href="../../music-production/"' in old:
        return page
    new = old.replace("</nav>", link + "</nav>", 1)
    return page[:match.start()] + new + page[match.end():]


def add_navigation(name: str, page: str) -> str:
    if name == "music-production/index.html":
        return page
    label = "Music Production" if name.startswith("en/") else "楽曲制作"
    depth = len(Path(name).parts) - 1
    href = "../" * depth + "music-production/"
    if name == "index.html" or name.startswith("worlds/") and name.count("/") == 2:
        link = '<a href="/music-production/">楽曲制作</a>'
        # V6 CSS hides the header's last link below 760px. Keep its existing
        # "公式サイト" link last so the new service remains visible on mobile.
        nav = re.search(r'<nav aria-label="主要ナビゲーション">.*?</nav>', page, re.S)
        if nav is None or nav.group(0).count('<a href="/">公式サイト</a>') != 1:
            raise ValueError("Expected V6 header navigation is missing")
        page = page[:nav.start()] + nav.group(0).replace(
            '<a href="/">公式サイト</a>', link + '<a href="/">公式サイト</a>', 1
        ) + page[nav.end():]
        page = insert_in_nav(page, r'<nav aria-label="公式サイトのコンテンツ" class="content-navigation">.*?</nav>', link, required=True)
        return page
    link = f'<a href="{href}">{label}</a>'
    page = insert_in_nav(page, r'<nav class="desktop-nav[^\"]*"[^>]*>.*?</nav>', link)
    page = insert_in_nav(page, r'<nav class="site-footer-nav[^\"]*"[^>]*>.*?</nav>', link)
    mobile = re.search(r'<details class="mobile-menu".*?</details>', page, re.S)
    if mobile:
        updated = insert_in_nav(mobile.group(0), r'<nav[^>]*>.*?</nav>', link, required=True)
        page = page[:mobile.start()] + updated + page[mobile.end():]
    return page


def add_home_invitation(page: str) -> str:
    marker = '<section class="mp-home-link"'
    if marker in page:
        raise ValueError("Base release already contains a service invitation")
    section = (
        '<section class="mp-home-link" aria-labelledby="mp-home-title">'
        '<p class="mp-eyebrow">SUZUKA MUSIC PRODUCTION</p>'
        '<h2 id="mp-home-title">あなたの物語を、世界にひとつだけの音楽へ。</h2>'
        '<p>作詞・作曲からAIアーティストによる歌唱まで。楽曲制作のご相談を承ります。</p>'
        '<a href="/music-production/">楽曲制作のご依頼を見る <span aria-hidden="true">↗</span></a>'
        '</section>'
    )
    if page.count('</main>') != 1 or page.count('</head>') != 1:
        raise ValueError("Unexpected V6 home structure")
    page = page.replace('</main>', section + '</main>', 1)
    page = page.replace('</head>', '<link rel="stylesheet" href="/assets/music-production.css"></head>', 1)
    return page


def add_sitemap_url(data: bytes) -> bytes:
    text = data.decode("utf-8")
    if SERVICE_URL in text:
        raise ValueError("Base sitemap already contains the service URL")
    if text.count("</urlset>") != 1:
        raise ValueError("Unexpected sitemap structure")
    addition = f"  <url>\n    <loc>{SERVICE_URL}</loc>\n  </url>\n"
    result = text.replace("</urlset>", addition + "</urlset>")
    before = ET.fromstring(data)
    after = ET.fromstring(result.encode("utf-8"))
    if len(after) != len(before) + 1:
        raise ValueError("Sitemap URL count changed unexpectedly")
    return result.encode("utf-8")


def build_files(root: Path) -> tuple[dict, dict[str, bytes], dict]:
    info, original = read_release(root, BASE_COMMIT)
    if len(original) != 781:
        raise ValueError("Expected 781 approved baseline files")
    files = dict(original)
    manifest = json.loads(files[MANIFEST])
    if len(manifest["v6Routes"]) != 13:
        raise ValueError("Expected 13 approved V6 routes")
    analytics = re.search(r'<!-- SUZUKA:GA4:START -->.*?<!-- SUZUKA:GA4:END -->',
                          original['index.html'].decode('utf-8'), re.S)
    if analytics is None:
        raise ValueError("Approved V6 analytics block is missing")
    for name, source in NEW_FILES.items():
        if name in files:
            raise ValueError("Service file already exists in approved baseline: " + name)
        data = (root / source).read_bytes()
        if name.endswith(".html"):
            template = data.decode("utf-8")
            if template.count("{{MAILTO}}") != 2:
                raise ValueError("Expected exactly two consultation buttons")
            if template.count('<meta charset="utf-8">') != 1:
                raise ValueError("Unexpected service head")
            template = template.replace('<meta charset="utf-8">',
                                        '<meta charset="utf-8">' + analytics.group(0), 1)
            data = template.replace("{{MAILTO}}", html.escape(mailto(), quote=True)).encode("utf-8")
        files[name] = data
    for name, data in original.items():
        if not name.endswith(".html") or name == "404.html":
            continue
        text = data.decode("utf-8")
        changed = add_navigation(name, text)
        if name == "index.html":
            changed = add_home_invitation(changed)
        if changed != text:
            files[name] = changed.encode("utf-8")
    files["sitemap.xml"] = add_sitemap_url(original["sitemap.xml"])
    # The 13 V6 routes, protected audio runtime, artists, releases and media remain
    # present. The only old-file modifications must be HTML navigation/home or sitemap.
    modified = sorted(name for name in original if files[name] != original[name])
    if not modified or any(name != "sitemap.xml" and not name.endswith(".html") for name in modified):
        raise ValueError("Unexpected change to an existing approved file")
    if len(files) != len(original) + len(NEW_FILES) or not set(original) <= set(files):
        raise ValueError("Approved public file removed or overwritten")
    verify_private_audio(info, files, manifest["v6Routes"])
    manifest["musicProduction"] = {"baselineCommit": BASE_COMMIT, "path": "music-production/index.html"}
    manifest["files"] = {name: sha(data) for name, data in sorted(files.items()) if name != MANIFEST}
    files[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return info, files, {"modifiedExisting": modified, "added": sorted(NEW_FILES), "sitemapUrls": 355}


def package(info: dict, files: dict[str, bytes]) -> dict[str, bytes]:
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as archive:
            for name, data in sorted(files.items()):
                item = tarfile.TarInfo(name)
                item.size, item.mode, item.mtime = len(data), 0o644, 0
                archive.addfile(item, io.BytesIO(data))
    archive_data = raw.getvalue()
    descriptor = dict(info)
    descriptor.update({
        "artifactDigest": sha(json.dumps({p: sha(d) for p, d in files.items()}, sort_keys=True, separators=(",", ":")).encode()),
        "fileCount": len(files), "contentBytes": sum(map(len, files.values())),
        "archiveBytes": len(archive_data), "archiveSha256": sha(archive_data),
    })
    chunks = {}
    descriptor["chunks"] = []
    for number, start in enumerate(range(0, len(archive_data), 45 * 1024 * 1024)):
        data = archive_data[start:start + 45 * 1024 * 1024]
        name = f"site-{number:02d}.tar.gz.part"
        chunks[name] = data
        descriptor["chunks"].append({"path": "public-release/" + name, "bytes": len(data), "sha256": sha(data)})
    chunks["release.json"] = (json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    info, files, report = build_files(root)
    chunks = package(info, files)
    destination = root / "public-release"
    if args.check:
        if {p.name for p in destination.iterdir()} != set(chunks):
            raise ValueError("Public release chunk inventory differs")
        for name, data in chunks.items():
            if (destination / name).read_bytes() != data:
                raise ValueError("Public release is not reproducible: " + name)
    else:
        with tempfile.TemporaryDirectory(prefix="music-production-release-", dir=root) as temporary:
            staged = Path(temporary)
            for name, data in chunks.items():
                (staged / name).write_bytes(data)
            for name in chunks:
                os.replace(staged / name, destination / name)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "files": len(files),
                      "artifactDigest": json.loads(chunks["release.json"])["artifactDigest"],
                      "modifiedExistingCount": len(report["modifiedExisting"]),
                      "added": report["added"], "sitemapUrls": report["sitemapUrls"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

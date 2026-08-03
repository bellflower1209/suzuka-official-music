#!/usr/bin/env python3
"""Audit IndexNow key, configuration, exclusions, dry-run, workflow and log."""
from __future__ import annotations

import argparse
import json
import re
import runpy
import subprocess
import sys
from pathlib import Path

BASE = "https://bellflower1209.github.io/suzuka-official-music/"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    errors: list[str] = []
    config_path = root / "assets/data/indexnow.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    key = str(config.get("key", ""))
    if not re.fullmatch(r"[A-Fa-f0-9]{8,128}", key):
        errors.append("key must be 8-128 hexadecimal characters")
    key_path = root / str(config.get("keyFile", ""))
    if key_path.name != f"{key}.txt" or not key_path.is_file():
        errors.append("key file name or location is invalid")
    else:
        expected = key.encode("ascii")
        if key_path.read_bytes() not in {expected, expected + b"\n"}:
            errors.append("key file body must contain only the key")
    expected_location = f"{BASE}{key}.txt"
    if config.get("keyLocation") != expected_location:
        errors.append("keyLocation does not match the GitHub Pages project URL")
    if config.get("endpoint") != "https://api.indexnow.org/indexnow":
        errors.append("IndexNow endpoint is invalid")
    if config.get("maximumUrlsPerRequest") != 10000:
        errors.append("maximumUrlsPerRequest must be 10000")

    command = [
        sys.executable, str(root / "scripts/submit_indexnow.py"), "--dry-run",
        "--urls", BASE, "--root", str(root),
    ]
    dry = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dry.returncode != 0:
        errors.append(f"dry-run failed: {dry.stderr.strip()}")
    else:
        payload = json.loads(dry.stdout)
        if payload.get("submitted") is not False or payload.get("urlCount") != 1:
            errors.append("dry-run submitted data or returned an incorrect count")
        request = payload.get("payloads", [{}])[0]
        if request.get("host") != "bellflower1209.github.io":
            errors.append("dry-run host is invalid")
        if request.get("keyLocation") != expected_location:
            errors.append("dry-run keyLocation is invalid")
        if request.get("urlList") != [BASE]:
            errors.append("dry-run URL list is invalid")

    rejected = [
        f"{BASE}admin/", f"{BASE}admin/dashboard/", f"{BASE}assets/styles.css",
        f"{BASE}?utm_source=test", f"{BASE}search/?q=test",
    ]
    for url in rejected:
        result = subprocess.run(
            [sys.executable, str(root / "scripts/submit_indexnow.py"), "--dry-run", "--urls", url, "--root", str(root)],
            cwd=root, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            errors.append(f"excluded URL was accepted: {url}")

    workflow_path = root / ".github/workflows/indexnow.yml"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else ""
    required_workflow_markers = (
        "branches: [main]", "pages/deployments/$GITHUB_SHA", "environment=github-pages",
        "scripts/submit_indexnow.py --submit", "actions/cache/restore@v4",
        "actions/cache/save@v4", "actions/upload-artifact@v4", "urlCount",
    )
    for marker in required_workflow_markers:
        if marker not in workflow:
            errors.append(f"workflow is missing: {marker}")
    submit_source = (root / "scripts/submit_indexnow.py").read_text(encoding="utf-8")
    for status in (200, 202, 400, 403, 422, 429):
        if f"{status}:" not in submit_source:
            errors.append(f"submit script is missing HTTP {status} handling")
    module = runpy.run_path(str(root / "scripts/submit_indexnow.py"))
    changed, reasons = module["diff_snapshots"](
        {"https://example/new/": "a", "https://example/updated/": "new"},
        {"https://example/deleted/": "b", "https://example/updated/": "old"},
    )
    if changed != [
        "https://example/deleted/", "https://example/new/", "https://example/updated/",
    ] or reasons != {
        "added": ["https://example/new/"],
        "updated": ["https://example/updated/"],
        "deleted": ["https://example/deleted/"],
    }:
        errors.append("added, updated and deleted URL diff logic is invalid")
    if "インデックス登録を保証しません" not in (root / "README.md").read_text(encoding="utf-8"):
        errors.append("README must state that IndexNow does not guarantee indexing")
    log = json.loads((root / "docs/indexnow/submission-log.json").read_text(encoding="utf-8"))
    if log.get("schemaVersion") != 1 or not isinstance(log.get("submissions"), list):
        errors.append("submission log schema is invalid")

    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    if expected_location in sitemap:
        errors.append("keyLocation must not be included in sitemap.xml")
    if errors:
        print("IndexNow audit failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"IndexNow audit passed: key {key_path.name}, project keyLocation, exclusions, dry-run and workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

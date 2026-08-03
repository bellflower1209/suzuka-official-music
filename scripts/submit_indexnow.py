#!/usr/bin/env python3
"""Submit only added, updated, or deleted indexable pages to IndexNow."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("assets/data/indexnow.json")
DEFAULT_LOG_PATH = Path("docs/indexnow/submission-log.json")
SITEMAP_NAMESPACE = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
KEY_PATTERN = re.compile(r"[A-Za-z0-9-]{8,128}")
SUCCESS_STATUSES = {200, 202}
STATUS_MESSAGES = {
    200: "送信成功",
    202: "受付済み・キー検証待ち",
    400: "形式不正",
    403: "キー検証失敗",
    422: "ホスト・URL・キー不一致",
    429: "送信過多",
}
JST = timezone(timedelta(hours=9))


class IndexNowError(RuntimeError):
    """Raised when local data or an IndexNow response is unsafe."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_config(root: Path) -> dict[str, Any]:
    config = json.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))
    required = {
        "endpoint", "host", "siteBase", "key", "keyFile", "keyLocation",
        "maximumUrlsPerRequest",
    }
    missing = required - set(config)
    if missing:
        raise IndexNowError(f"IndexNow config is missing: {sorted(missing)}")
    key = str(config["key"])
    if not KEY_PATTERN.fullmatch(key):
        raise IndexNowError("IndexNow key must be 8-128 letters, numbers, or dashes")
    if config["keyFile"] != f"{key}.txt":
        raise IndexNowError("keyFile must use the IndexNow key as its filename")
    expected_location = f'{config["siteBase"]}{config["keyFile"]}'
    if config["keyLocation"] != expected_location:
        raise IndexNowError(f"keyLocation mismatch: {config['keyLocation']} != {expected_location}")
    key_data = (root / config["keyFile"]).read_bytes()
    if key_data not in {key.encode("ascii"), key.encode("ascii") + b"\n"}:
        raise IndexNowError("Key file must contain only the key and an optional final newline")
    if config["endpoint"] != "https://api.indexnow.org/indexnow":
        raise IndexNowError("Unexpected IndexNow endpoint")
    if int(config["maximumUrlsPerRequest"]) != 10000:
        raise IndexNowError("maximumUrlsPerRequest must be 10000")
    return config


def parse_sitemap(data: bytes, config: dict[str, Any]) -> list[str]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise IndexNowError(f"Invalid sitemap XML: {error}") from error
    urls = [
        (node.text or "").strip()
        for node in root.findall("s:url/s:loc", SITEMAP_NAMESPACE)
    ]
    if not urls:
        raise IndexNowError("sitemap.xml does not contain indexable URLs")
    if len(urls) != len(set(urls)):
        raise IndexNowError("sitemap.xml contains duplicate URLs")
    for url in urls:
        validate_url(url, config)
    return urls


def validate_url(url: str, config: dict[str, Any]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != config["host"]:
        raise IndexNowError(f"Non-production URL rejected: {url}")
    if not url.startswith(config["siteBase"]):
        raise IndexNowError(f"URL is outside keyLocation scope: {url}")
    if parsed.query or parsed.fragment:
        raise IndexNowError(f"Query strings and fragments are not submitted: {url}")
    relative = parsed.path.removeprefix("/suzuka-official-music/")
    if relative.startswith("admin/") or relative in {"admin", "admin/dashboard"}:
        raise IndexNowError(f"Admin URL rejected: {url}")
    if Path(relative).suffix.lower() in {
        ".css", ".js", ".json", ".xml", ".txt", ".jpg", ".jpeg", ".png",
        ".webp", ".gif", ".svg", ".ico", ".mp3", ".mp4", ".csv",
    }:
        raise IndexNowError(f"Non-page asset URL rejected: {url}")


def url_to_html_path(url: str, config: dict[str, Any]) -> Path:
    validate_url(url, config)
    relative = url.removeprefix(config["siteBase"]).strip("/")
    return Path("index.html") if not relative else Path(relative) / "index.html"


def git_bytes(root: Path, reference: str, path: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{reference}:{path.as_posix()}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise IndexNowError(f"Could not read {path} at {reference}: {detail}")
    return result.stdout


def current_snapshot(root: Path, config: dict[str, Any]) -> dict[str, str]:
    urls = parse_sitemap((root / "sitemap.xml").read_bytes(), config)
    snapshot: dict[str, str] = {}
    for url in urls:
        path = root / url_to_html_path(url, config)
        if not path.is_file():
            raise IndexNowError(f"Indexable page is missing: {path.relative_to(root)}")
        data = path.read_bytes()
        if re.search(br'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', data, re.I):
            raise IndexNowError(f"sitemap.xml contains a noindex page: {url}")
        snapshot[url] = sha256(data)
    return snapshot


def git_snapshot(root: Path, reference: str, config: dict[str, Any]) -> dict[str, str]:
    sitemap = git_bytes(root, reference, Path("sitemap.xml"))
    urls = parse_sitemap(sitemap, config)
    return {
        url: sha256(git_bytes(root, reference, url_to_html_path(url, config)))
        for url in urls
    }


def changed_urls(
    root: Path, config: dict[str, Any], base_ref: str
) -> tuple[list[str], dict[str, list[str]]]:
    current = current_snapshot(root, config)
    previous = git_snapshot(root, base_ref, config)
    return diff_snapshots(current, previous)


def diff_snapshots(
    current: dict[str, str], previous: dict[str, str]
) -> tuple[list[str], dict[str, list[str]]]:
    added = sorted(set(current) - set(previous))
    deleted = sorted(set(previous) - set(current))
    updated = sorted(
        url for url in set(current) & set(previous) if current[url] != previous[url]
    )
    reasons = {"added": added, "updated": updated, "deleted": deleted}
    return sorted({*added, *updated, *deleted}), reasons


def load_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schemaVersion": 1, "submissions": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or not isinstance(value.get("submissions"), list):
        raise IndexNowError(f"Invalid submission log: {path}")
    return value


def write_log(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".indexnow-log-",
        suffix=".json", delete=False,
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(path)


def verify_public_key(config: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        config["keyLocation"],
        headers={"User-Agent": "SUZUKA-IndexNow/1.0", "Cache-Control": "no-cache"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError) as error:
        raise IndexNowError(f"Could not verify public key: {error}") from error
    if status != 200:
        raise IndexNowError(f"Public key returned HTTP {status}")
    if not content_type.lower().startswith(("text/plain", "application/octet-stream")):
        raise IndexNowError(f"Unexpected key Content-Type: {content_type}")
    expected = config["key"].encode("ascii")
    if data not in {expected, expected + b"\n"}:
        raise IndexNowError("Public key body does not match the configured key")
    return {"status": status, "contentType": content_type, "sha256": sha256(data)}


def payload_for(urls: list[str], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": config["host"],
        "key": config["key"],
        "keyLocation": config["keyLocation"],
        "urlList": urls,
    }


def submit_batch(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        config["endpoint"],
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "SUZUKA-IndexNow/1.0",
        },
    )
    status = 0
    response_body = ""
    error_text = ""
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            response_body = response.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as error:
        status = error.code
        response_body = error.read().decode("utf-8", errors="replace")[:2000]
        error_text = f"HTTP {error.code}: {error.reason}"
    except (urllib.error.URLError, TimeoutError) as error:
        error_text = str(error)
    return {
        "urlCount": len(payload["urlList"]),
        "urls": payload["urlList"],
        "httpStatus": status,
        "statusMeaning": STATUS_MESSAGES.get(status, "通信エラー" if status == 0 else "未定義の応答"),
        "success": status in SUCCESS_STATUSES,
        "responseBody": response_body,
        "error": error_text,
    }


def current_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "worktree"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print the payload without sending")
    mode.add_argument("--submit", action="store_true", help="verify the public key and send the payload")
    parser.add_argument("--urls", nargs="+", help="explicit production page URLs; defaults to changed URLs")
    parser.add_argument("--base-ref", help="previous successful Pages deployment commit")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--force", action="store_true", help="allow re-submitting an identical successful payload")
    args = parser.parse_args()

    root = args.root.resolve()
    config = load_config(root)
    base_ref = args.base_ref or os.environ.get("INDEXNOW_BASE_REF") or "HEAD^"
    reasons: dict[str, list[str]]
    if args.urls:
        urls = sorted(set(args.urls))
        for url in urls:
            validate_url(url, config)
        reasons = {"manual": urls}
    else:
        urls, reasons = changed_urls(root, config, base_ref)
    maximum = int(config["maximumUrlsPerRequest"])
    batches = [urls[index:index + maximum] for index in range(0, len(urls), maximum)]
    preview = {
        "mode": "submit" if args.submit else "dry-run",
        "submitted": False,
        "baseRef": base_ref,
        "targetCommit": current_commit(root),
        "urlCount": len(urls),
        "changes": reasons,
        "keyLocation": config["keyLocation"],
        "payloads": [payload_for(batch, config) for batch in batches],
    }
    if not args.submit:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    log_path = args.log_file if args.log_file.is_absolute() else root / args.log_file
    log = load_log(log_path)
    payload_hash = sha256(json.dumps(preview["payloads"], sort_keys=True).encode("utf-8"))
    duplicate = next((
        item for item in reversed(log["submissions"])
        if item.get("targetCommit") == preview["targetCommit"]
        and item.get("payloadSha256") == payload_hash
        and item.get("success") is True
    ), None)
    if duplicate and not args.force:
        preview.update({"skipped": True, "skipReason": "identical successful payload already logged"})
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    key_check = verify_public_key(config)
    results = [submit_batch(payload, config) for payload in preview["payloads"]]
    success = all(result["success"] for result in results)
    skipped = not urls
    record = {
        "submittedAt": datetime.now(JST).isoformat(timespec="seconds"),
        "targetCommit": preview["targetCommit"],
        "baseRef": base_ref,
        "urlCount": len(urls),
        "urls": urls,
        "changes": reasons,
        "keyLocation": config["keyLocation"],
        "keyVerification": key_check,
        "payloadSha256": payload_hash,
        "batches": results,
        "httpStatus": results[0]["httpStatus"] if len(results) == 1 else None,
        "success": success,
        "skipped": skipped,
        "error": "; ".join(result["error"] for result in results if result["error"]),
    }
    log["submissions"].append(record)
    write_log(log_path, log)
    preview.update({
        "submitted": bool(urls), "skipped": skipped, "success": success,
        "keyVerification": key_check, "results": results, "logFile": str(log_path),
    })
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IndexNowError as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)

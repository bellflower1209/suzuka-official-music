#!/usr/bin/env python3
"""Crawl the GitHub Pages-compatible static site and report broken internal URLs."""

from __future__ import annotations

import argparse
import collections
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"img", "script", "iframe"} else None
        if attribute and values.get(attribute):
            self.links.append(values[attribute] or "")


def fetch(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "SUZUKA-Static-Check/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.headers.get_content_type(), response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/") + "/"
    parsed_base = urllib.parse.urlsplit(base_url)
    allowed_prefix = parsed_base.path
    queue = collections.deque([base_url])
    checked: dict[str, int] = {}
    failures: list[tuple[str, str]] = []

    while queue:
        url = queue.popleft()
        clean_url = urllib.parse.urldefrag(url).url
        if clean_url in checked:
            continue
        try:
            status, content_type, body = fetch(clean_url)
            checked[clean_url] = status
        except Exception as error:  # noqa: BLE001 - command-line validator must report all URL failures.
            failures.append((clean_url, str(error)))
            continue

        if content_type != "text/html":
            continue
        parser_instance = LinkParser()
        parser_instance.feed(body.decode("utf-8", errors="replace"))
        for link in parser_instance.links:
            if not link or link.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            absolute = urllib.parse.urljoin(clean_url, link)
            parsed = urllib.parse.urlsplit(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc != parsed_base.netloc or not parsed.path.startswith(allowed_prefix):
                continue
            queue.append(absolute)

    for url, status in sorted(checked.items()):
        print(f"{status} {url}")
    if failures:
        for url, error in failures:
            print(f"ERROR {url}: {error}", file=sys.stderr)
        return 1
    print(f"Checked {len(checked)} internal URLs; no broken links found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

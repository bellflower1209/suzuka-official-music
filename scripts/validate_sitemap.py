#!/usr/bin/env python3
"""Generate and validate SUZUKA's minimal XML sitemap.

The local validation is deterministic and has no network dependency. Pass
``--remote`` after deployment to verify the GitHub Pages response with a
Googlebot user agent, including every sitemap URL and its canonical.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://bellflower1209.github.io/suzuka-official-music"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
OLD_DOMAIN = "suzuka-official-music.ria20210815.chatgpt.site"
UNPUBLISHED_MARKERS = ("たった1人の君へ",)
LEGACY_REDIRECTS = {Path("releases/toriatsukai-chuui/index.html")}
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonicals: list[str] = []
        self.robots: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonicals.append(values.get("href", ""))
        if tag.lower() == "meta" and values.get("name", "").lower() in {"robots", "googlebot"}:
            self.robots.append(values.get("content", ""))


def public_url(path: Path) -> str:
    relative = path.relative_to(ROOT)
    if relative == Path("index.html"):
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{relative.parent.as_posix()}/"


def parse_head(text: str) -> HeadParser:
    parser = HeadParser()
    parser.feed(text)
    return parser


def expected_pages() -> tuple[dict[str, Path], list[str]]:
    pages: dict[str, Path] = {}
    errors: list[str] = []
    for path in sorted(ROOT.rglob("index.html")):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts or "node_modules" in relative.parts or relative in LEGACY_REDIRECTS:
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            errors.append(f"{relative}: HTML is not valid UTF-8: {error}")
            continue
        head = parse_head(text)
        directives = ",".join(head.robots).lower()
        if "noindex" in directives:
            continue
        url = public_url(path)
        if len(head.canonicals) != 1:
            errors.append(f"{relative}: expected one canonical, found {len(head.canonicals)}")
            continue
        if head.canonicals[0] != url:
            errors.append(f"{relative}: canonical mismatch: {head.canonicals[0]} != {url}")
            continue
        pages[url] = path
    return pages, errors


def render_sitemap(urls: list[str]) -> bytes:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<urlset xmlns="{NAMESPACE}">']
    for url in urls:
        lines.extend(("  <url>", f"    <loc>{url}</loc>", "  </url>"))
    lines.append("</urlset>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def extract_urls(data: bytes) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if data.startswith(b"\xef\xbb\xbf"):
        errors.append("sitemap.xml contains a UTF-8 BOM")
    declaration = b'<?xml version="1.0" encoding="UTF-8"?>'
    if not data.startswith(declaration):
        errors.append("sitemap.xml must begin with the standard UTF-8 XML declaration")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        return [], [f"sitemap.xml is not valid UTF-8: {error}"]
    invalid_controls = [character for character in text if ord(character) < 32 and character not in "\t\n\r"]
    if invalid_controls:
        errors.append("sitemap.xml contains invalid control characters")
    if "<!--" in text or "```" in text or "<html" in text.lower():
        errors.append("sitemap.xml contains a comment, Markdown, or HTML markup")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        return [], errors + [f"XML parse error: {error}"]
    expected_root = f"{{{NAMESPACE}}}urlset"
    if root.tag != expected_root:
        errors.append(f"incorrect sitemap namespace/root: {root.tag}")
    urls: list[str] = []
    for child in list(root):
        if child.tag != f"{{{NAMESPACE}}}url":
            errors.append(f"unexpected sitemap child element: {child.tag}")
            continue
        children = list(child)
        if len(children) != 1 or children[0].tag != f"{{{NAMESPACE}}}loc":
            errors.append("each url element must contain exactly one loc element")
            continue
        loc = (children[0].text or "").strip()
        if not loc:
            errors.append("sitemap.xml contains an empty loc")
            continue
        urls.append(loc)
    return urls, errors


def validate_urls(urls: list[str], expected: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    if len(urls) != len(set(urls)):
        duplicates = sorted({url for url in urls if urls.count(url) > 1})
        errors.append(f"duplicate loc values: {duplicates}")
    for url in urls:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "bellflower1209.github.io":
            errors.append(f"loc is not an HTTPS GitHub Pages URL: {url}")
        if not url.startswith(f"{BASE_URL}/"):
            errors.append(f"loc is outside the project subdirectory: {url}")
        if parsed.query or parsed.fragment:
            errors.append(f"loc contains query parameters or a fragment: {url}")
        if OLD_DOMAIN in url:
            errors.append(f"loc contains the old domain: {url}")
    actual = set(urls)
    wanted = set(expected)
    if missing := sorted(wanted - actual):
        errors.append(f"indexable pages missing from sitemap: {missing}")
    if extra := sorted(actual - wanted):
        errors.append(f"unwanted sitemap URLs: {extra}")
    return errors


def validate_robots(text: str) -> list[str]:
    errors: list[str] = []
    if "User-agent: *" not in text:
        errors.append("robots.txt is missing User-agent: *")
    if not re.search(r"(?mi)^Allow:\s*/\s*$", text):
        errors.append("robots.txt must explicitly allow /")
    if re.search(r"(?mi)^Disallow:\s*/\s*$", text):
        errors.append("robots.txt blocks the entire site")
    sitemap_lines = re.findall(r"(?mi)^Sitemap:\s*(\S+)\s*$", text)
    if sitemap_lines != [SITEMAP_URL]:
        errors.append(f"robots.txt Sitemap must be exactly {SITEMAP_URL}")
    if OLD_DOMAIN in text:
        errors.append("robots.txt contains the old domain")
    return errors


def fetch(url: str) -> tuple[bytes, str, str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": GOOGLEBOT, "Accept": "application/xml,text/html;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(), response.headers.get("Content-Type", ""), response.geturl(), response.status


def validate_remote(local_data: bytes, urls: list[str]) -> list[str]:
    errors: list[str] = []
    try:
        remote_data, content_type, final_url, status = fetch(SITEMAP_URL)
    except (urllib.error.URLError, TimeoutError) as error:
        return [f"could not fetch production sitemap: {error}"]
    if status != 200:
        errors.append(f"production sitemap returned HTTP {status}")
    if final_url != SITEMAP_URL:
        errors.append(f"production sitemap redirected to {final_url}")
    if not content_type.lower().startswith(("application/xml", "text/xml")):
        errors.append(f"production sitemap has incorrect Content-Type: {content_type}")
    if remote_data != local_data:
        errors.append("production sitemap bytes do not match the repository")
    _, remote_xml_errors = extract_urls(remote_data)
    errors.extend(f"production {error}" for error in remote_xml_errors)
    try:
        robots_data, content_type, final_url, status = fetch(ROBOTS_URL)
        robots_text = robots_data.decode("utf-8")
        if status != 200:
            errors.append(f"production robots.txt returned HTTP {status}")
        if final_url != ROBOTS_URL:
            errors.append(f"production robots.txt redirected to {final_url}")
        if not content_type.lower().startswith("text/plain"):
            errors.append(f"production robots.txt has incorrect Content-Type: {content_type}")
        errors.extend(f"production {error}" for error in validate_robots(robots_text))
    except (urllib.error.URLError, UnicodeDecodeError, TimeoutError) as error:
        errors.append(f"could not validate production robots.txt: {error}")
    for url in urls:
        try:
            page_data, content_type, final_url, status = fetch(url)
        except (urllib.error.URLError, TimeoutError) as error:
            errors.append(f"could not fetch sitemap URL {url}: {error}")
            continue
        if status != 200:
            errors.append(f"sitemap URL returned HTTP {status}: {url}")
        if final_url != url:
            errors.append(f"sitemap URL redirected: {url} -> {final_url}")
        if not content_type.lower().startswith("text/html"):
            errors.append(f"sitemap URL is not HTML ({content_type}): {url}")
        try:
            head = parse_head(page_data.decode("utf-8"))
        except UnicodeDecodeError as error:
            errors.append(f"sitemap URL is not UTF-8 HTML ({url}): {error}")
            continue
        if head.canonicals != [url]:
            errors.append(f"production canonical mismatch for {url}: {head.canonicals}")
        if "noindex" in ",".join(head.robots).lower():
            errors.append(f"production sitemap includes noindex page: {url}")
        decoded = page_data.decode("utf-8", errors="replace")
        if OLD_DOMAIN in decoded:
            errors.append(f"production page contains the old domain: {url}")
        if any(marker in decoded for marker in UNPUBLISHED_MARKERS):
            errors.append(f"production page exposes an unpublished marker: {url}")
    return errors


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT, help="site root to validate or update")
    parser.add_argument("--write", action="store_true", help="regenerate sitemap.xml after candidate validation")
    parser.add_argument("--remote", action="store_true", help="also validate the deployed GitHub Pages site")
    args = parser.parse_args()
    ROOT = args.root.resolve()

    expected, errors = expected_pages()
    ordered_urls = sorted(expected, key=lambda url: (url != f"{BASE_URL}/", url))
    candidate = render_sitemap(ordered_urls)
    if args.write:
        candidate_urls, candidate_errors = extract_urls(candidate)
        errors.extend(candidate_errors)
        errors.extend(validate_urls(candidate_urls, expected))
        if errors:
            print("Sitemap generation aborted:\n- " + "\n- ".join(errors), file=sys.stderr)
            return 1
        with tempfile.NamedTemporaryFile(dir=ROOT, prefix=".sitemap-", suffix=".xml", delete=False) as temporary:
            temporary.write(candidate)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, ROOT / "sitemap.xml")

    local_data = (ROOT / "sitemap.xml").read_bytes()
    urls, xml_errors = extract_urls(local_data)
    errors.extend(xml_errors)
    errors.extend(validate_urls(urls, expected))
    try:
        robots_text = (ROOT / "robots.txt").read_text(encoding="utf-8")
        errors.extend(validate_robots(robots_text))
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"robots.txt could not be read as UTF-8: {error}")
    if any(marker.encode("utf-8") in local_data for marker in UNPUBLISHED_MARKERS):
        errors.append("sitemap.xml contains an unpublished title")
    if args.remote and not errors:
        errors.extend(validate_remote(local_data, urls))

    if errors:
        print("Sitemap validation failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    scope = "local and production" if args.remote else "local"
    print(f"Sitemap validation passed ({scope}): {len(urls)} indexable URLs, no duplicates or canonical mismatches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

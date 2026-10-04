#!/usr/bin/env python3
"""Final seasonal presentation pass; preserves canonical music facts and external links."""
import html
import json
import re
from pathlib import Path

START = '<!-- SUZUKA:HALLOWEEN:START -->'
END = '<!-- SUZUKA:HALLOWEEN:END -->'

def prepare(root: Path) -> None:
    # Remove the prior season block before other builders insert content at <section>.
    for path in root.rglob('*.html'):
        text = path.read_text()
        updated = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
        if updated != text:
            path.write_text(updated)

def build(root: Path) -> None:
    season = json.loads((root / 'assets/data/site-season.json').read_text())
    (root / 'assets/season-2026.js').write_text(
        "(() => {\nconst day = new Intl.DateTimeFormat('en-CA', {timeZone:" + json.dumps(season['timezone']) +
        ",year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());\n" +
        "const header=document.querySelector('.site-header');const offset=()=>document.documentElement.style.setProperty('--season-header-offset',((header&&['fixed','absolute'].includes(getComputedStyle(header).position))?header.getBoundingClientRect().height:0)+'px');offset();if(header&&typeof ResizeObserver!=='undefined')new ResizeObserver(offset).observe(header);\n" +
        "document.documentElement.classList.toggle('halloween-2026', " + str(season['enabled']).lower() +
        " && day >= " + json.dumps(season['start']) + " && day < " + json.dumps(season['endExclusive']) + ");\n})();\n"
    )
    unavailable = json.loads((root / 'assets/data/image-availability.json').read_text())
    missing = {x['url'] for x in unavailable['unavailable']}
    # Explicit textual placeholder, never a substitute artist/work illustration.
    for path in root.rglob('*.html'):
        if '.git' in path.parts:
            continue
        text = path.read_text()
        prefix = '../' * (len(path.relative_to(root).parts) - 1)
        text = re.sub(r'<link\b[^>]*href=["\'][^"\']*assets/player\.css["\'][^>]*>', '', text)
        text = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', text, flags=re.S)
        text = re.sub(r'<link\b[^>]*data-halloween[^>]*>', '', text)
        text = re.sub(r'<script\b[^>]*data-season[^>]*>.*?</script>', '', text, flags=re.S)
        def external_video(match):
            source = re.search(r'src=["\']([^"\']+)', match.group())
            if not source:
                return match.group()
            src = source.group(1)
            if 'youtube' not in src:
                return match.group()
            video_id = src.split('/embed/')[-1].split('?')[0]
            return ('<div class="external-video-link"><p>Official Video</p>'
                    f'<a href="https://www.youtube.com/watch?v={html.escape(video_id)}" '
                    'target="_blank" rel="noopener noreferrer">YouTubeで視聴 ↗</a></div>')
        text = re.sub(r'<iframe\b.*?</iframe>', external_video, text, flags=re.S)
        text = re.sub(r'<audio\b.*?</audio>', '', text, flags=re.S)
        def fix_image(match):
            tag = match.group()
            src = re.search(r'src=["\']([^"\']+)', tag)
            if src and html.unescape(src.group(1)) in missing:
                tag = tag.replace(src.group(1), prefix + 'images/official-image-pending.svg')
                tag = re.sub(r'alt=["\'][^"\']*["\']', 'alt="公式画像確認中（元画像の配信停止）"', tag)
            return tag
        text = re.sub(r'<img\b[^>]*>', fix_image, text)
        for url in missing:
            text = text.replace('data-lightbox-src="' + url + '"', 'data-lightbox-src="' + prefix + 'images/official-image-pending.svg"')
        banner = (START + '<section class="season-banner" aria-label="SUZUKA Halloween 2026">'
                  '<div class="season-copy"><p>OCTOBER LIMITED · MUSIC &amp; NIGHT</p>'
                  f'<h2>{html.escape(season["label"])}</h2><span>音楽と物語が響く、10月の夜。</span></div>'
                  '<div class="season-art" aria-hidden="true"><i class="season-moon"></i>'
                  '<i class="season-bat bat-one"></i><i class="season-bat bat-two"></i>'
                  '<i class="season-pumpkin"><b></b></i><i class="season-stars"></i></div></section>' + END)
        if '</header>' in text:
            text = text.replace('</header>', '</header>' + banner, 1)
        else:
            text = text.replace('<body>', '<body>' + banner, 1)
        text = text.replace('</head>', f'<link data-halloween rel="stylesheet" href="{prefix}assets/halloween-2026.css"/>'
                            f'<script data-season defer src="{prefix}assets/season-2026.js"></script></head>', 1)
        text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        path.write_text(text)
    # Derived catalogs drive client-rendered cards. Canonical evidence URLs remain intact.
    for path in (root / 'assets/data').glob('*.json'):
        if path.name in {'creator-cms.json', 'image-availability.json', 'site-season.json'} or any(x in path.name for x in ['verification','official-','youtube-publish']):
            continue
        value = json.loads(path.read_text())
        def normalize(value, key=''):
            if isinstance(value, dict):
                return {k: normalize(v, k) for k,v in value.items()}
            if isinstance(value, list):
                return [normalize(v,key) for v in value]
            if key in {'image','coverImage','thumbnail','thumbnailUrl','heroImage'} and isinstance(value,str) and value in missing:
                return 'images/official-image-pending.svg'
            return value
        updated = normalize(value)
        if updated != value:
            path.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')
    print('Season presentation applied; onsite playback removed; unavailable official images explicitly marked.')

if __name__ == '__main__':
    build(Path(__file__).resolve().parents[1])

"""Render user-confirmed karaoke announcements on existing works, without new releases."""
import html
import json
import re
from pathlib import Path

MARKER = re.compile(r'<!-- karaoke:start -->.*?<!-- karaoke:end -->', re.S)
esc = html.escape


def paragraphs(values):
    return ''.join('<p>'+esc(p).replace('\n', '<br>')+'</p>' for p in values)


def panel(item, prefix):
    k = item['karaoke']
    return ('<!-- karaoke:start --><section class="karaoke-panel" aria-label="KARAOKE / JOYSOUND">'
            '<p class="section-kicker">KARAOKE / JOYSOUND</p>'
            f'<h2>{esc(item["artist"])}「{esc(item["title"])}」</h2>'
            f'<p><time datetime="{k["startDate"]}">{k["startDate"].replace("-", ".")}～</time><br>{esc(k["availability"])} · {esc(k["audio"])}</p>'
            f'<div class="explore-actions"><a href="{prefix}{k["newsUrl"]}">JOYSOUNDカラオケ配信NEWSを見る</a></div>'
            '</section><!-- karaoke:end -->')


def build_news(news, artist, item, renderer):
    text = renderer(news, artist)
    k = item['karaoke']
    content = (f'<section class="karaoke-news"><img class="karaoke-promo" src="../../{news["image"]}" alt="榎本魅愛 花言葉 JOYSOUNDカラオケ配信決定 公式告知画像" width="360" height="360"/>'
               + paragraphs(news['bodyParagraphs'])
               + '<h2>配信情報</h2><p>アーティスト：榎本魅愛 / ENOMOTO MIA<br>楽曲：花言葉<br>配信開始：2026年9月18日（金）～<br>配信：JOYSOUND対応機種<br>音源：公式音源</p>'
               + '<h2>特別クーポン</h2><p>カラオケ配信を記念して、<br>「カラオケショップ JOYSOUND」で利用できる特別クーポンをご案内します。条件・詳細はリンク先をご確認ください。</p>'
               + f'<div class="explore-actions"><a href="{esc(k["couponUrl"],quote=True)}" target="_blank" rel="noopener noreferrer">JOYSOUND特別クーポンを見る</a></div>'
               + paragraphs(news['closingParagraphs'])
               + f'<div class="explore-actions"><a href="../../{item["releaseUrl"]}">「花言葉」作品ページ</a><a href="../hanakotoba-streaming-release/">Streaming Release：2026.09.11</a></div></section>')
    text, count = re.subn(r'<section><img[^>]+/></section>', lambda m: content, text, count=1)
    if count != 1:
        raise ValueError('Missing karaoke news insertion point')
    return text.replace('</head>', '<link rel="stylesheet" href="../../assets/karaoke.css"/></head>', 1)


def build(root):
    cms = json.loads((root/'assets/data/creator-cms.json').read_text())
    for item in cms['releases']:
        if not item.get('karaoke'):
            continue
        for route in [item['releaseUrl']+'index.html', 'artists/'+item['artistSlug']+'/index.html']:
            path = root/route
            text = MARKER.sub('', path.read_text())
            text, count = re.subn(r'(<section\b)', lambda m:panel(item, '../../')+m[0], text, count=1)
            if count != 1:
                raise ValueError(f'Missing karaoke panel insertion point: {route}')
            if 'assets/karaoke.css' not in text:
                text = text.replace('</head>', '<link rel="stylesheet" href="../../assets/karaoke.css"/></head>', 1)
            path.write_text(text)
        path = root/'discography/index.html'
        text = path.read_text()
        target = f'<a href="../{item["releaseUrl"]}">作品を見る ↗</a>'
        link = f'<a href="../{item["karaoke"]["newsUrl"]}">KARAOKE / JOYSOUND · 2026.09.18～ NEWS ↗</a>'
        if text.count(target) != 1:
            raise ValueError('Expected one existing discography work')
        path.write_text(text.replace(target, target+link, 1))

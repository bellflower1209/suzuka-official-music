#!/usr/bin/env python3
"""Ensure the exact video-title exception cannot hide old work titles or lyrics."""
from pathlib import Path
import contextlib, importlib.util, io, json, shutil, tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='cg-audit-regression-') as directory:
    stage = Path(directory)
    paths = ['assets/data/creator-cms.json', 'assets/data/search-v31.json', 'assets/data/releases-catalog.json',
             'assets/data/lyrics-masters/yume_to_kaigo_to_watashitachi_official_lyrics.txt', 'sitemap.xml', '404.html',
             'index.html', 'lyrics/yume-to-kaigo-to-watashitachi/index.html', 'releases/yume-to-kaigo-to-watashitachi/index.html',
             'features/suzuka-with-care/index.html', 'artists/enomoto-mia/index.html', 'discography/index.html',
             'news/yume-to-kaigo-to-watashitachi-release/index.html']
    for name in paths:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    spec=importlib.util.spec_from_file_location('lyrics_audit',ROOT/'scripts/audit_yume_kaigo_lyrics.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit);audit.ROOT=stage
    def run():
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return audit.main()
    assert run()==0, 'verified video title must pass without altering lyrics'
    page=stage/'releases/yume-to-kaigo-to-watashitachi/index.html';original=page.read_text()
    page.write_text(original+'<p>'+audit.OLD_TITLE+'</p>');assert run()==1,'unrelated visible old title must fail';page.write_text(original)
    mv_page=stage/'lyrics/yume-to-kaigo-to-watashitachi/index.html';mv_original=mv_page.read_text();mv_page.write_text(mv_original.replace('giTYuKyIk3c','INVALID'));assert run()==1,'missing official MV must fail';mv_page.write_text(mv_original)
    catalog=stage/'assets/data/releases-catalog.json';original=catalog.read_text();data=json.loads(original)
    release=next(r for r in data['releases'] if r['slug']==audit.SLUG);release['title']=audit.OLD_TITLE
    catalog.write_text(json.dumps(data,ensure_ascii=False));assert run()==1,'old catalog work title must fail';catalog.write_text(original)
    lyrics=stage/'lyrics/yume-to-kaigo-to-watashitachi/index.html';original=lyrics.read_text();lyrics.write_text(original.replace('夢と介護は','夢と介護に',1));assert run()==1,'changed lyric text must fail';lyrics.write_text(original)
    assert run()==0
print('PASS: exact official video exception, old work-title rejection, MV preservation and byte-faithful lyrics.')

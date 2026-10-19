#!/usr/bin/env python3
"""Verify a frozen public Pages package; never generates content or deploys."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = Path('public-release/release.json')
MANIFEST = 'suzuka-v6-candidate-manifest.json'
BASE = 'https://www.suzukaofficial.com'
PRIVATE_AUDIO_ENDPOINT = 'https://suzuka-official-music.ria20210815.chatgpt.site/v1/'

def verify_private_audio(info, files, routes, allow_pending=False):
    configs=[]
    for route in routes:
        match=re.search(r'<script type="application/json" id="v6-config">(.*?)</script>',files[route].decode(),re.S)
        if match is None:
            require(route=='index.html' and info.get('artifactDigest')=='27af5422d65a9647fcbce73da30800ca1a3579b2dc17b8ff86300594d48aacab','Missing V6 configuration')
            continue  # Verified historical V5 top; its 12 existing world URLs stay silent.
        configs.append(json.loads(match[1]))
    enabled=any(w.get('music',{}).get('approved') for c in configs for w in c.get('worlds',[]))
    if not enabled:return  # Preserve verified historical silent V6/V5 rollback packages.
    approval=info.get('privateAudioApproval',{})
    require(approval.get('scope')=='website-playback-with-private-audio-only' and approval.get('publicGitAudioAllowed') is False,'Private audio scope required')
    require(approval.get('status')=='approved' or allow_pending and approval.get('status')=='pending-final-gate','Private audio final gate has not passed')
    require(approval.get('source')=='explicit-user-conditional-approval' and approval.get('recordedAt'),'Explicit conditional approval record required')
    approved={t['trackId']:t for t in approval.get('tracks',[])}
    require(len(approved)==len(approval.get('tracks',[]))==12 and all(re.fullmatch(r'[a-z0-9-]+',k) and isinstance(v.get('title'),str) and v['title'] and re.fullmatch(r'[a-z0-9-]+',v.get('releaseId') or '') for k,v in approved.items()),'Exactly 12 approved track identities required')
    require(all('sha256' not in t and 'source' not in t for t in approval.get('tracks',[])),'Private audio fingerprints/paths cannot enter Public Git')
    expected={'mode':'signed-worker-v1','endpoint':PRIVATE_AUDIO_ENDPOINT,'sessionMode':'sha256-proof-v1'}
    for config in configs:
        require(config.get('publicationMode')=='public-candidate' and config.get('audioDelivery')==expected,'Unapproved or local audio endpoint')
        worlds=config.get('worlds',[])
        require(len(worlds)==12 and {w['slug'] for w in worlds}==set(approved),'Missing/extra audio world')
        for w in worlds:
            m=w.get('music',{})
            require(m.get('approved') is True and m.get('source') is None and m.get('delivery')=='signed-worker-v1' and m.get('trackId')==w['slug'] and m.get('title')==approved[w['slug']]['title'] and m.get('releaseId')==approved[w['slug']]['releaseId'] and 'sha256' not in m,'Direct/unapproved audio source')
        require(not any(x in files[r].decode() for r in routes for x in ['assets/v6-music/','v6/music/approved/','.mp3','.wav']),'Static audio link leaked')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_release(root, reference=None, allow_pending=False):
    """Read current files or Public Git history only, verifying every byte."""
    root = root.resolve()
    if reference:
        require(bool(__import__('re').fullmatch(r'[0-9a-f]{40}',reference)), 'Use a full Public commit SHA')
    def read(relative):
        if reference:
            return subprocess.run(['git','show',reference+':'+relative],cwd=root,check=True,capture_output=True).stdout
        path = root/relative
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),'Unsafe package file: '+relative)
        return path.read_bytes()
    info = json.loads(read(DESCRIPTOR.as_posix()))
    require(info['format']=='suzuka-public-release-v1','Unknown public package format')
    compressed = bytearray()
    for number,item in enumerate(info['chunks']):
        require(item['path']==f'public-release/site-{number:02d}.tar.gz.part','Unexpected package chunk')
        data = read(item['path'])
        require(len(data)==item['bytes'] and digest(data)==item['sha256'],'Package chunk SHA mismatch')
        compressed.extend(data)
    require(len(compressed)==info['archiveBytes'] and digest(compressed)==info['archiveSha256'],'Archive SHA mismatch')
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(compressed),mode='r:gz') as archive:
        for member in archive:
            name = member.name
            require(member.isfile() and not member.issym() and not member.islnk(),'Only regular public files are allowed')
            path = PurePosixPath(name)
            require(not path.is_absolute() and str(path)==name and '..' not in path.parts and '\\' not in name and name not in files,'Unsafe/duplicate archive path')
            require(not any(p in {'.git','.github','scripts','docs','admin','v6','__pycache__'} for p in path.parts),'Development path in public artifact')
            require(path.name!='AGENTS.md' and not name.endswith(('.pyc','.pyo','.wav','.mp3')),'Private rules/cache/unapproved audio')
            require(path.suffix.lower() not in {'.mp3','.wav','.m4a','.aac','.ogg','.flac','.m3u8','.ts'},'Audio must never enter Public Git/Pages archives')
            require(not any(x in name for x in ['lyrics-holds','portal-audio','dashboard-status']),'Held/internal data in public artifact')
            total += member.size
            require(total <= info['contentBytes'] and len(files)<info['fileCount'],'Public package size/count exceeded')
            stream = archive.extractfile(member)
            require(stream is not None,'Unreadable archive member')
            data = stream.read(member.size+1)
            require(len(data)==member.size,'Archive member size mismatch')
            require(not(data[:3]==b'ID3' or data[:4]==b'OggS' or data[:4]==b'RIFF' and data[8:12]==b'WAVE'),'Disguised audio in public archive')
            files[name] = data
    require(total==info['contentBytes'] and len(files)==info['fileCount'],'Package inventory mismatch')
    hashes = {p:digest(data) for p,data in files.items()}
    actual = digest(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode())
    require(actual==info['artifactDigest'],'Approved public artifact SHA mismatch')
    manifest = json.loads(files[MANIFEST])
    require(set(hashes)==set(manifest['files'])|{MANIFEST},'Unexpected/missing published file')
    require(all(hashes[p]==h for p,h in manifest['files'].items()),'Public manifest SHA mismatch')
    require(manifest['baseUrl']==BASE and manifest['measurementId']=='G-LS3PCRB60D','Incorrect origin/analytics identity')
    require(len(manifest['v6Routes'])==13 and manifest['v6Routes'][0]=='index.html','Top and 12 worlds required')
    for route in manifest['v6Routes']:
        require(route in files,'Missing public world')
        text = files[route].decode('utf-8')
        url = BASE+'/'+('' if route=='index.html' else route.removesuffix('index.html'))
        require(f'<link rel="canonical" href="{url}">' in text and 'noindex' not in text,'Incorrect public SEO')
        require('location.origin !== '+json.dumps(BASE) in text,'Production analytics must be origin-gated')
    verify_private_audio(info,files,manifest['v6Routes'],allow_pending)
    return info,files


def verify_output(destination, files):
    require(not any(p.is_symlink() for p in destination.rglob('*')),'Symlink in output')
    actual = {p.relative_to(destination).as_posix():digest(p.read_bytes()) for p in destination.rglob('*') if p.is_file()}
    require(actual=={p:digest(v) for p,v in files.items()},'Extracted/staged artifact SHA mismatch')


def write_output(destination, files):
    if destination.exists() and any(destination.iterdir()):
        verify_output(destination,files)
        return
    destination.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        path = destination/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    verify_output(destination,files)


def materialize(root, output, files, stage=None):
    root,output = root.resolve(),output.resolve()
    allowed = [Path(tempfile.gettempdir()).resolve(), Path('/tmp').resolve()]
    if os.environ.get('RUNNER_TEMP'):
        allowed.append(Path(os.environ['RUNNER_TEMP']).resolve())
    require(not output.is_relative_to(root) and any(output!=p and output.is_relative_to(p) for p in allowed),'Use an external temporary output')
    require(not any((p/'.git').exists() for p in [output,*output.parents]),'Output must not be another Git worktree')
    write_output(output,files)
    if stage is not None:
        stage = stage.resolve()
        require(stage==root/'_site' and os.environ.get('GITHUB_ACTIONS')=='true'
                and os.environ.get('GITHUB_REPOSITORY')=='bellflower1209/suzuka-official-music'
                and os.environ.get('GITHUB_REF')=='refs/heads/main'
                and os.environ.get('GITHUB_EVENT_NAME') in {'push','workflow_dispatch'},'Production stage requires the Public main workflow')
        require(not stage.exists(),'Refusing an existing staging folder')
        shutil.copytree(output,stage)
        verify_output(stage,files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--stage',type=Path)
    parser.add_argument('--local-review',action='store_true')
    args = parser.parse_args()
    try:
        require(not(args.local_review and args.stage is not None),'A local review must never stage production')
        info,files = read_release(args.root,allow_pending=args.local_review)
        require(args.output is not None or args.stage is None,'Staging requires verified extraction')
        if args.output:materialize(args.root,args.output,files,args.stage)
        print(json.dumps({'status':'PASS','files':len(files),'artifactDigest':info['artifactDigest'],'bytes':sum(map(len,files.values())),'deploymentPerformed':False},indent=2))
    except (OSError,ValueError,KeyError,tarfile.TarError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'FAIL','error':str(error)}))
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())

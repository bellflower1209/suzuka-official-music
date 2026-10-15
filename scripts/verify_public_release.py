#!/usr/bin/env python3
"""Verify a frozen public Pages package; never generates content or deploys."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = Path('public-release/release.json')
MANIFEST = 'suzuka-v6-candidate-manifest.json'
BASE = 'https://www.suzukaofficial.com'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_release(root, reference=None):
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
            require(not any(x in name for x in ['lyrics-holds','portal-audio','dashboard-status']),'Held/internal data in public artifact')
            total += member.size
            require(total <= info['contentBytes'] and len(files)<info['fileCount'],'Public package size/count exceeded')
            stream = archive.extractfile(member)
            require(stream is not None,'Unreadable archive member')
            data = stream.read(member.size+1)
            require(len(data)==member.size,'Archive member size mismatch')
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
    args = parser.parse_args()
    try:
        info,files = read_release(args.root)
        require(args.output is not None or args.stage is None,'Staging requires verified extraction')
        if args.output:materialize(args.root,args.output,files,args.stage)
        print(json.dumps({'status':'PASS','files':len(files),'artifactDigest':info['artifactDigest'],'bytes':sum(map(len,files.values())),'deploymentPerformed':False},indent=2))
    except (OSError,ValueError,KeyError,tarfile.TarError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'FAIL','error':str(error)}))
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())

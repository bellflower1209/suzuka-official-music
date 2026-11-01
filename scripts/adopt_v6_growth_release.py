"""Adopt the explicitly approved PR #15 bytes using the existing frozen-package format.

No deployment or staging here. The normal main-only workflow verifies/extracts
public-release/ and remains the only production delivery path.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

from build_music_production_release import package, sha
from build_v6_growth_preview import BASE, DIGEST, MANIFEST, ROOT, build as preview, encoded
from verify_public_release import read_release, verify_private_audio, write_output

REVIEWED = 'bc80e5656738d97587a527a703d5dde41c18ea42'
REVIEWED_DIGEST = '53ad9c07bb419510d24ef0cd15de507ae1f1022d75070d3dc2333bd35533c28e'
APPROVAL = {
    'source': 'explicit-user-production-authorization',
    'approvedDate': '2026-11-01',
    'reviewedCommit': REVIEWED,
    'reviewedCandidateDigest': REVIEWED_DIGEST,
    'rollbackCommit': BASE,
    'rollbackArtifactDigest': DIGEST,
    'artists': 13,
    'publishedWorks': 109,
}


def build(root=ROOT):
    subprocess.run(['git', 'merge-base', '--is-ancestor', REVIEWED, 'HEAD'], cwd=root, check=True, capture_output=True)
    info, files, report = preview(root)
    actual = sha(json.dumps({p: sha(b) for p, b in files.items()}, sort_keys=True, separators=(',', ':')).encode())
    if actual != REVIEWED_DIGEST or len(files) != 863:
        raise ValueError('Candidate differs from the explicitly approved bc80e56 bytes; STOP')
    # All 862 served content/assets remain byte-for-byte the reviewed candidate.
    # Only the internal manifest records the explicit production authorization.
    manifest = json.loads(files[MANIFEST])
    manifest['growthPreview'].update(status='approved-public-release', publicationApproved=True)
    manifest['publicRelease'] = copy.deepcopy(APPROVAL)
    files[MANIFEST] = encoded(manifest)
    info = copy.deepcopy(info)
    info['growthReleaseApproval'] = copy.deepcopy(APPROVAL)
    verify_private_audio(info, files, manifest['v6Routes'])
    return info, files, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output.resolve() if args.output else None
    allowed = [Path(tempfile.gettempdir()).resolve(),Path('/tmp').resolve()]
    if output and (output.is_relative_to(ROOT) or not any(output!=p and output.is_relative_to(p) for p in allowed)):
        raise ValueError('Review output must be an external temporary directory')
    info, files, _ = build()
    chunks = package(info, files)
    destination = ROOT / 'public-release'
    if {p.name for p in destination.iterdir()} != set(chunks):
        raise ValueError('Unexpected package chunk inventory; STOP')
    current = json.loads((destination / 'release.json').read_text())
    approved = json.loads(chunks['release.json'])
    if current['artifactDigest'] not in {DIGEST, approved['artifactDigest']}:
        raise ValueError('Published-package base changed unexpectedly; STOP')
    if args.check:
        if any((destination / name).read_bytes() != data for name, data in chunks.items()):
            raise ValueError('Approved production package does not reproduce exactly; STOP')
    else:
        # Stage all bytes first. This modifies only this PR's working copy.
        with tempfile.TemporaryDirectory(prefix='growth-release-stage-', dir=ROOT) as temporary:
            staged = Path(temporary)
            for name, data in chunks.items():
                (staged / name).write_bytes(data)
            for name in chunks:
                os.replace(staged / name, destination / name)
    verified_info, verified_files = read_release(ROOT)
    if verified_files != files or verified_info['artifactDigest'] != approved['artifactDigest']:
        raise ValueError('Package verification failed; STOP')
    if output:
        write_output(output, files)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'write',
        'files': len(files), 'artists': 13, 'publishedWorks': 109,
        'artifactDigest': approved['artifactDigest'], 'reviewedCandidateDigest': REVIEWED_DIGEST,
        'reviewedContentUnchanged': True, 'deploymentPerformed': False}, indent=2))


if __name__ == '__main__':
    main()

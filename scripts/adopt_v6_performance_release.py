"""Prepare the reviewed PR #16 bytes in the frozen package, without publication.

Only --write changes this worktree's public-release/. No browser, stage, deploy,
main checkout or remote write is performed here. Publication remains on HOLD.
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
from build_v6_performance_preview import (
    BASE, DIGEST, MANIFEST, ROOT, build as preview, review_output_allowed,
)
from verify_public_release import read_release, verify_private_audio, write_output

REVIEWED = '0687a55981004b119eafaa77db4905b3ca180f58'
REVIEWED_DIGEST = 'b4946384f87e676038c281287208af7a2fe535da61da08e2ae61b7a30d2d1ff9'
PREPARATION = {
    'source': 'explicit-user-package-preparation-authorization',
    'approvedDate': '2026-11-02',
    'reviewedCommit': REVIEWED,
    'reviewedCandidateDigest': REVIEWED_DIGEST,
    'baselineCommit': BASE,
    'baselineArtifactDigest': DIGEST,
    'packagePreparationApproved': True,
    'publicationApproved': False,
    'status': 'prepared-publication-hold',
    'artists': 13,
    'publishedWorks': 109,
    'files': 866,
}


def artifact_digest(files):
    hashes = {name: sha(data) for name, data in files.items()}
    return sha(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode())


def build(root=ROOT):
    subprocess.run(['git', 'merge-base', '--is-ancestor', REVIEWED, 'HEAD'],
                   cwd=root, check=True, capture_output=True)
    info, files, report = preview(root=root)
    if artifact_digest(files) != REVIEWED_DIGEST or len(files) != 866:
        raise ValueError('Candidate differs from the reviewed 0687a55 bytes; STOP')
    # Served HTML, CSS, images, scripts and data remain exactly the measured bytes.
    # Only internal provenance records this package-preparation authorization.
    manifest = json.loads(files[MANIFEST])
    manifest['performancePreview']['status'] = 'adopted-release-candidate'
    manifest['performanceReleaseCandidate'] = copy.deepcopy(PREPARATION)
    files[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    info = copy.deepcopy(info)
    info['performanceReleaseCandidate'] = copy.deepcopy(PREPARATION)
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
    if output and not review_output_allowed(output):
        raise ValueError('Review output must be an external temporary directory')
    info, files, report = build()
    chunks = package(info, files)
    expected = json.loads(chunks['release.json'])
    destination = ROOT / 'public-release'
    if {p.name for p in destination.iterdir()} != set(chunks):
        raise ValueError('Unexpected package chunk inventory; STOP')
    current, _ = read_release(ROOT)
    if current['artifactDigest'] not in {DIGEST, expected['artifactDigest']}:
        raise ValueError('Public package has unexpected changes; STOP')
    if args.check:
        if any((destination / name).read_bytes() != data for name, data in chunks.items()):
            raise ValueError('Prepared package does not reproduce exactly; STOP')
    else:
        with tempfile.TemporaryDirectory(prefix='performance-package-stage-', dir=ROOT) as temporary:
            staged = Path(temporary) / 'public-release'
            staged.mkdir()
            for name, data in chunks.items():
                (staged / name).write_bytes(data)
            checked, checked_files = read_release(staged.parent)
            if checked_files != files or checked != expected:
                raise ValueError('Staged candidate failed verification; STOP')
            for name in chunks:
                os.replace(staged / name, destination / name)
    checked, checked_files = read_release(ROOT)
    if checked_files != files or checked != expected:
        raise ValueError('Prepared package verification failed; STOP')
    if output:
        write_output(output, files)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'write',
        'artifactDigest': expected['artifactDigest'], 'reviewedCandidateDigest': REVIEWED_DIGEST,
        'files': len(files), 'artists': 13, 'publishedWorks': 109,
        'changedHtml': report['changedHtml'], 'addedFiles': report['addedFiles'],
        'reviewedContentUnchanged': True, 'publicationApproved': False,
        'browserLaunches': 0, 'deploymentPerformed': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

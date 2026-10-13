#!/usr/bin/env python3
"""Secondary-video evidence must never replace a work's primary video date."""
import json
import tempfile
from pathlib import Path
from structured_data_dates import apply_evidence_to_cms

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    (root / 'assets/data').mkdir(parents=True)
    evidence = {'records': [
        {'releaseSlug': 'work', 'youtubeId': 'secondary', 'contentType': 'version',
         'verifiedPublishedAt': '2026-10-13T20:00:08+09:00',
         'youtubePublishDate': '2026-10-13', 'verificationSource': 'official-player'},
        {'releaseSlug': 'work', 'youtubeId': 'short', 'contentType': 'short',
         'verifiedPublishedAt': '2026-10-14T20:00:00+09:00',
         'youtubePublishDate': '2026-10-14', 'verificationSource': 'official-player'},
    ]}
    (root / 'assets/data/youtube-publish-dates.json').write_text(json.dumps(evidence))
    for url in ['', 'https://www.youtube.com/watch?v=primary']:
        cms = {'releases': [{'slug': 'work', 'youtubeUrl': url, 'releaseDate': '2026-09-01', 'publishedAt': '2026-09-01'}]}
        _, selected = apply_evidence_to_cms(root, cms)
        assert not selected and cms['releases'][0]['videoPublishedAt'] == ''
        assert cms['releases'][0]['publishedAt'] == '2026-09-01'
    cms = {'releases': [{'slug': 'work', 'youtubeUrl': 'https://www.youtube.com/watch?v=secondary', 'releaseDate': '2026-09-01'}]}
    _, selected = apply_evidence_to_cms(root, cms)
    assert selected['work']['youtubeId'] == 'secondary'
    assert cms['releases'][0]['videoPublishedAt'] == '2026-10-13T20:00:08+09:00'
print('PASS: missing/unverified primary keeps its date; explicitly selected verified variant receives its own date.')

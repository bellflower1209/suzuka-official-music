"""Equality, preservation and publication-HOLD gates for the prepared package."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adopt_v6_performance_release import (
    APPROVED, APPROVED_DIGEST, BASE, DIGEST, MANIFEST, ROOT, PREPARATION,
    REVIEWED_DIGEST, artifact_digest, build,
)
from build_v6_performance_preview import IMAGE_ROUTES, STYLE_ROUTES, build as preview
from verify_public_release import materialize, read_release


class PreparedPerformancePackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info, cls.files = read_release(ROOT)
        cls.expected_info, cls.expected, cls.report = build()
        cls.baseline_info, cls.baseline = read_release(ROOT, BASE)

    def test_exact_prepared_content_and_reviewed_bytes(self):
        self.assertEqual(self.files, self.expected)
        self.assertEqual(self.info['performanceReleaseCandidate'], PREPARATION)
        self.assertEqual(json.loads(self.files[MANIFEST])['performanceReleaseCandidate'], PREPARATION)
        self.assertEqual(artifact_digest(preview()[1]), REVIEWED_DIGEST)
        # The entire measured candidate, except its internal manifest, is unchanged.
        reviewed = preview()[1]
        self.assertEqual({n: b for n, b in self.files.items() if n != MANIFEST},
                         {n: b for n, b in reviewed.items() if n != MANIFEST})

    def test_only_approved_html_and_new_css_are_adopted(self):
        self.assertEqual(self.baseline_info['artifactDigest'], DIGEST)
        self.assertEqual(len(self.baseline), 863)
        self.assertEqual(len(self.files), 866)
        self.assertTrue(set(self.baseline) <= set(self.files))
        changed = {n for n, data in self.baseline.items() if self.files[n] != data}
        self.assertEqual(changed, set(IMAGE_ROUTES) | set(STYLE_ROUTES) | {MANIFEST})
        self.assertEqual(set(self.files) - set(self.baseline), set(self.report['addedFiles']))

    def test_audio_approvals_worlds_catalog_and_backgrounds_are_preserved(self):
        self.assertEqual(self.info['privateAudioApproval'], self.baseline_info['privateAudioApproval'])
        self.assertEqual(self.info['growthReleaseApproval'], self.baseline_info['growthReleaseApproval'])
        old = json.loads(self.baseline[MANIFEST])
        new = json.loads(self.files[MANIFEST])
        for key, value in old.items():
            if key != 'files':
                self.assertEqual(new[key], value)
        for name, data in self.baseline.items():
            if name not in set(IMAGE_ROUTES) | set(STYLE_ROUTES) | {MANIFEST}:
                self.assertEqual(self.files[name], data, name)
        cms = json.loads(self.files['assets/data/creator-cms.json'])
        self.assertEqual((len(cms['artists']), len(cms['releases'])), (13, 109))
        self.assertFalse(any(Path(n).suffix.lower() in
            {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.m3u8', '.ts'} for n in self.files))

    def test_publication_requires_the_explicit_a8e9083_authorization(self):
        self.assertTrue(PREPARATION['packagePreparationApproved'])
        self.assertTrue(PREPARATION['publicationApproved'])
        self.assertEqual(PREPARATION['source'], 'explicit-user-production-authorization')
        self.assertEqual(PREPARATION['approvedCommit'], APPROVED)
        info, approved = read_release(ROOT, APPROVED)
        self.assertEqual(info['artifactDigest'], APPROVED_DIGEST)
        self.assertEqual({n: b for n, b in self.files.items() if n != MANIFEST},
                         {n: b for n, b in approved.items() if n != MANIFEST})
        self.assertFalse(json.loads(self.files[MANIFEST])['performancePreview']['publicationApproved'])
        pending_files = dict(self.files)
        pending = json.loads(pending_files[MANIFEST])
        pending['performanceReleaseCandidate']['publicationApproved'] = False
        pending_files[MANIFEST] = json.dumps(pending).encode()
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root, output = parent / 'repo', parent / 'output'
            root.mkdir()
            with patch.dict('os.environ', {'GITHUB_ACTIONS': 'true',
                    'GITHUB_REPOSITORY': 'bellflower1209/suzuka-official-music',
                    'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'push'}):
                with self.assertRaisesRegex(ValueError, 'publication approval required'):
                    materialize(root, output, pending_files, stage=root / '_site')
            self.assertFalse(output.exists())
            self.assertFalse((root / '_site').exists())

    def test_approved_package_staging_still_requires_the_public_main_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root, output = parent / 'repo', parent / 'output'
            root.mkdir()
            with patch.dict('os.environ', {'GITHUB_ACTIONS': 'true',
                    'GITHUB_REPOSITORY': 'bellflower1209/suzuka-official-music',
                    'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'push'}):
                materialize(root, output, self.files, stage=root / '_site')
                self.assertTrue((root / '_site' / 'index.html').is_file())
                with patch.dict('os.environ', {'GITHUB_REF': 'refs/heads/unapproved-branch'}):
                    with self.assertRaisesRegex(ValueError, 'Public main workflow'):
                        materialize(root, output, self.files, stage=root / '_site')


if __name__ == '__main__':
    unittest.main(verbosity=2)

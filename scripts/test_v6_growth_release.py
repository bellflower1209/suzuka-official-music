"""Production adoption must equal the approved candidate, with a verified rollback base."""
import json
import unittest
from adopt_v6_growth_release import APPROVAL, BASE, DIGEST, MANIFEST, ROOT, build
from verify_public_release import read_release


class Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the original 109-work adoption gate pinned to its deployed bytes.
        # The successor package has a separate performance-adoption equality gate.
        cls.info,cls.files=read_release(ROOT,'71ea73944d72fadef5d186a5346a65f1a1609511')
        cls.expected_info,cls.expected,_=build()
        cls.baseline_info,cls.baseline=read_release(ROOT,BASE)

    def test_exact_approved_package_and_authorization(self):
        self.assertEqual(self.files,self.expected)
        self.assertEqual(self.info['growthReleaseApproval'],APPROVAL)
        self.assertEqual(json.loads(self.files[MANIFEST])['publicRelease'],APPROVAL)
        self.assertEqual(self.info['privateAudioApproval'],self.baseline_info['privateAudioApproval'])

    def test_verified_rollback_and_all_existing_paths_and_visuals(self):
        self.assertEqual(self.baseline_info['artifactDigest'],DIGEST)
        self.assertEqual(len(self.baseline),814)
        self.assertTrue(set(self.baseline)<=set(self.files))
        for name,data in self.baseline.items():
            if name.startswith(('assets/cinema/','assets/baba-nova/','assets/v6-media/','images/')) or name in {
                'assets/cinematic-universe-v6.js','assets/cinematic-universe-v6.css','assets/v6-protected-audio.js','v6-audio-worker.js'}:
                self.assertEqual(self.files[name],data,name)

    def test_public_inventory_and_no_static_audio(self):
        cms=json.loads(self.files['assets/data/creator-cms.json'])
        self.assertEqual((len(self.files),len(cms['artists']),len(cms['releases'])),(863,13,109))
        self.assertNotIn('last-ignition',{r['slug']for r in cms['releases']})
        self.assertFalse(any(p.endswith(('.mp3','.wav','.m4a','.aac','.ogg','.flac','.m3u8','.ts'))for p in self.files))


if __name__=='__main__':unittest.main(verbosity=2)

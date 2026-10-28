"""Protect existing worlds when a catalog artist has no approved world assets."""
import copy
import json
from pathlib import Path
import unittest
from build_celestial_gate import presentation_artists

ROOT=Path(__file__).resolve().parents[1]
class CatalogArtistGate(unittest.TestCase):
    def setUp(self):
        self.cms=json.loads((ROOT/'assets/data/creator-cms.json').read_text())
        self.config=json.loads((ROOT/'assets/data/celestial-gate.json').read_text())
    def test_explicit_catalog_artist_retains_twelve_worlds(self):
        worlds=presentation_artists(self.config,self.cms['artists'])
        self.assertEqual({a['slug'] for a in worlds},set(self.config['themes']))
        self.assertEqual(len(worlds),12)
        self.assertEqual(len(self.cms['artists']),13)
    def test_missing_world_cannot_silently_become_catalog_only(self):
        config=copy.deepcopy(self.config);config['themes'].pop('nox')
        with self.assertRaises(ValueError):presentation_artists(config,self.cms['artists'])
    def test_catalog_only_cannot_disable_existing_world(self):
        artists=copy.deepcopy(self.cms['artists']);artists[0]['presentationStatus']='catalog-only'
        with self.assertRaises(ValueError):presentation_artists(self.config,artists)
    def test_missing_opt_out_rejects_new_unregistered_artist(self):
        artists=copy.deepcopy(self.cms['artists']);artists[-1].pop('presentationStatus')
        with self.assertRaises(ValueError):presentation_artists(self.config,artists)
if __name__=='__main__':unittest.main()

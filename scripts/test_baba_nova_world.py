#!/usr/bin/env python3
"""Boundary and preservation tests for the approved thirteenth world."""
import copy,json,re,unittest
from build_baba_nova_world import ROOT,BASE,MANIFEST,CONFIG,build,WORLD_ROUTE
from verify_public_release import read_release,verify_private_audio
class BabaWorld(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.info,cls.files=read_release(ROOT);_,cls.old=read_release(ROOT,BASE)
  cls.manifest=json.loads(cls.files[MANIFEST]);cls.routes=cls.manifest['v6Routes']
 def test_world_inventory_and_catalog(self):
  self.assertEqual(len(self.routes),14);self.assertEqual(len(self.files),814)
  home=self.files['index.html'].decode();self.assertEqual(home.count('data-world-choice='),13)
  graph=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',home,re.S)[1]);listing=next(n for n in graph['@graph'] if n.get('@id')=='https://www.suzukaofficial.com/#worlds');self.assertEqual(len(listing['itemListElement']),13)
  cms=json.loads(self.files['assets/data/creator-cms.json']);self.assertEqual(len(cms['artists']),13);self.assertEqual(len(cms['releases']),104)
  self.assertEqual(self.files['assets/data/creator-cms.json'],self.old['assets/data/creator-cms.json'])
 def test_existing_worlds_configs_scenes_and_stories_unchanged(self):
  for route in self.routes[:-1]:
   old=self.old[route].decode();new=self.files[route].decode()
   a=json.loads(CONFIG.search(old)[2]);b=json.loads(CONFIG.search(new)[2]);self.assertEqual(a['worlds'],b['worlds'][:12]);self.assertEqual(a['audioDelivery'],b['audioDelivery'])
   for m in re.findall(r'<template id="v6-scene-[^"]+">.*?</template>',old,re.S):self.assertIn(m,new)
   for pat in [r'<section class="hero.*?</section>',r'<section class="artist-story.*?</section>',r'<section class="music-section" id="music".*?</section>']:
    if route=='index.html':continue
    a=re.search(pat,old,re.S);b=re.search(pat,new,re.S)
    self.assertEqual(a[0].replace(' / 12 ·',' / 13 ·'),b[0])
 def test_audio_controls_and_approved_protection_retained(self):
  for name in ['assets/v6-protected-audio.js','v6-audio-worker.js','music-production/index.html']:
   self.assertEqual(self.files[name],self.old[name])
  original=self.old['assets/cinematic-universe-v6.js'].decode();current=self.files['assets/cinematic-universe-v6.js'].decode()
  # Only the configuration identity guard changes. All playback and navigation
  # functions below initial config acceptance remain exactly the old runtime.
  self.assertEqual(original.split('  // Preference is separate',1)[1],current.split('  // Preference is separate',1)[1])
 def test_new_track_and_official_main_image(self):
  page=self.files[WORLD_ROUTE].decode();c=json.loads(CONFIG.search(page)[2]);w=c['worlds'][-1]
  self.assertEqual(w['music']['title'],'サラダチキン婆');self.assertEqual(w['music']['trackId'],'baba-nova');self.assertIsNone(w['music']['source'])
  self.assertEqual(self.files['assets/baba-nova/salad-chicken-baa-official.jpg'],(ROOT/'site-content/baba-nova/salad-chicken-baa-official.jpg').read_bytes())
  self.assertIn('/artists/baba-nova/',page);self.assertIn('/releases/salad-chicken-baa/',page)
  self.assertNotIn('rangili',re.sub(r'<template.*?</template>','',page,flags=re.S).split('<main id="main">')[1].split('<aside')[0])
 def test_extra_track_without_owner_extension_is_rejected(self):
  i=copy.deepcopy(self.info);i['privateAudioApproval'].pop('extensionApproval')
  with self.assertRaises(ValueError):verify_private_audio(i,self.files,self.routes)
 def test_missing_or_wrong_track_identity_rejected(self):
  for mutation in ['missing','wrong','source']:
   f=dict(self.files);page=f[WORLD_ROUTE].decode();m=CONFIG.search(page);c=json.loads(m[2])
   if mutation=='missing':c['worlds'].pop()
   if mutation=='wrong':c['worlds'][-1]['music']['trackId']='asagiri-shinobu'
   if mutation=='source':c['worlds'][-1]['music']['source']='https://example.invalid/audio.mp3'
   f[WORLD_ROUTE]=(page[:m.start(2)]+json.dumps(c)+page[m.end(2):]).encode()
   with self.assertRaises(ValueError):verify_private_audio(self.info,f,self.routes)
 def test_reproducible_and_no_deletions(self):
  _,new=build(ROOT);self.assertEqual(new,self.files);self.assertTrue(set(self.old)<=set(new))
if __name__=='__main__':unittest.main()

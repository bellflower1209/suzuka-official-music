#!/usr/bin/env python3
"""Protect the official original and both responsive image placements.

Rendered ratios are additionally tested in Chrome/WebKit with mobile emulation;
these CI guards prevent dropping the required intrinsic-size treatment again.
"""
from html.parser import HTMLParser
import io,re,unittest,json,hashlib
from PIL import Image
from build_baba_nova_world import ROOT,BASE,WORLD_ROUTE
from verify_public_release import read_release

class Images(HTMLParser):
 def __init__(self,text):super().__init__();self.images=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='img' and d.get('src','').endswith('/salad-chicken-baa-official.jpg'):self.images.append(d)

class Ratio(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  _,cls.files=read_release(ROOT)
 def test_exact_official_original_unchanged(self):
  _,old=read_release(ROOT,'e3e0c9d0f22c5517a81698b6a2b2d29b88e8851d');name='assets/baba-nova/salad-chicken-baa-official.jpg'
  self.assertEqual(self.files[name],old[name]);im=Image.open(io.BytesIO(self.files[name]));self.assertEqual(im.size,(1280,720));self.assertIn(im.getexif().get(274),[None,1])
 def test_both_placements_have_intrinsic_metadata_and_responsive_height(self):
  images=Images(self.files[WORLD_ROUTE].decode()).images;self.assertEqual(len(images),2)
  for image in images:
   self.assertIn('baba-official-image',image.get('class','').split());self.assertEqual((image['width'],image['height']),('1280','720'))
  css=self.files['assets/cinematic-universe-v6.css'].decode();match=re.search(r'body\[data-artist="baba-nova"\] \.baba-official-image\s*\{([^}]+)\}',css);self.assertIsNotNone(match)
  rules=dict(re.findall(r'([a-z-]+)\s*:\s*([^;]+)',match[1]));self.assertEqual(rules['height'],'auto');self.assertEqual(rules['aspect-ratio'],'16/9');self.assertEqual(rules['object-fit'],'contain');self.assertEqual(rules['max-height'],'none')
 def test_responsive_background_is_approved_raster(self):
  source=ROOT/'site-content/baba-nova';data=json.loads((source/'backgrounds.json').read_text());self.assertEqual(data['approval']['scope'],'new-night-background-no-people-no-text');self.assertTrue(data['notHistoricalPhotograph']);self.assertEqual(len(data['files']),8)
  for item in data['files']:
   raw=self.files[item['publicPath']];self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256']);im=Image.open(io.BytesIO(raw));self.assertEqual(im.size,(item['width'],item['height']));self.assertLess(len(raw),300000)
  hero=re.search(r'<section class="hero world-hero".*?</section>',self.files[WORLD_ROUTE].decode(),re.S)[0]
  self.assertIn('/assets/baba-nova/mobile-768.avif',hero);self.assertIn('/assets/baba-nova/landscape-1600.webp',hero);self.assertNotIn('/assets/baba-nova/scene.svg',hero);self.assertNotIn('baba-lantern',hero)
if __name__=='__main__':unittest.main()

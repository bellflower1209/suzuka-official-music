"""Regression gates for the preview overlay, evidence and frozen production assets."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

from build_v6_growth_preview import BASE, DIGEST, MANIFEST, NEW_SLUGS, ROOT, SITE, SOURCE, build, canonical, stickers_section
from verify_public_release import read_release


class HTML(HTMLParser):
    def __init__(self):
        super().__init__();self.refs=[];self.anchors=set();self.schemas=[];self.ld=False;self.skip=0;self.text=[];self.images=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if a.get('id'):self.anchors.add(a['id'])
        if t in {'script','style'}:self.skip+=1
        if t=='script' and a.get('type')=='application/ld+json':self.ld=True
        for k in ['href','src','poster']:
            if a.get(k):self.refs.append(a[k])
        if t=='img':self.images.append(a)
    def handle_endtag(self,t):
        if t in {'script','style'}:self.skip-=1
        if t=='script':self.ld=False
    def handle_data(self,d):
        if self.ld:self.schemas.append(json.loads(d))
        if not self.skip:self.text.append(d)


class GrowthPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline_info,cls.old=read_release(ROOT,BASE)
        cls.info,cls.files,cls.report=build()
        cls.sources=json.loads((ROOT/SOURCE/'verified-sources.json').read_text())
        cls.oldcms=json.loads(cls.old['assets/data/creator-cms.json'])
        cls.cms=json.loads(cls.files['assets/data/creator-cms.json'])

    def test_approved_baseline_and_adopted_content_are_byte_identical(self):
        info,files=read_release(ROOT,BASE)
        self.assertEqual(info['artifactDigest'],DIGEST)
        self.assertEqual(files,self.old)
        # Verify the historical growth release; successor adoption is tested separately.
        _,current=read_release(ROOT,'71ea73944d72fadef5d186a5346a65f1a1609511')
        self.assertEqual({p:b for p,b in current.items()if p!=MANIFEST},
                         {p:b for p,b in self.files.items()if p!=MANIFEST})
        self.assertTrue(json.loads(current[MANIFEST])['growthPreview']['publicationApproved'])
        self.assertTrue(set(self.old)<=set(self.files))
        self.assertFalse(self.report['deploymentPerformed'])

    def test_all_artists_and_old_work_identities_and_lyrics_are_preserved(self):
        self.assertEqual(self.cms['artists'],self.oldcms['artists'])
        before={r['slug']:r for r in self.oldcms['releases']};after={r['slug']:r for r in self.cms['releases']}
        self.assertEqual(len(after),109);self.assertEqual(set(after)-set(before),NEW_SLUGS)
        for slug,old in before.items():
            current=copy.deepcopy(after[slug]);old=copy.deepcopy(old)
            permitted={'relatedShorts','shortsUrl'}
            if slug=='anata-dake-ni-okuru-happy-birthday':
                permitted|={'scheduledStreamingRelease','coverImage','coverAlt','formalJacketImage','imageRole','artworkStatus','coverSource'}
            for key in permitted:old.pop(key,None);current.pop(key,None)
            self.assertEqual(current,old,slug)
        for name,b in self.old.items():
            if name.startswith('lyrics/') and name.endswith('.html'):
                a=HTML();a.feed(b.decode());c=HTML();c.feed(self.files[name].decode())
                self.assertEqual([t for t in a.text if t.strip()],[t for t in c.text if t.strip()],name)

    def test_cinematic_worlds_audio_service_worker_and_media_are_unchanged(self):
        for n,b in self.old.items():
            if n.startswith(('assets/cinema/','assets/baba-nova/','assets/v6-media/','images/')) or n in {
                'assets/cinematic-universe-v6.js','assets/cinematic-universe-v6.css','assets/v6-protected-audio.js','v6-audio-worker.js',
                'assets/music-production.js','assets/music-production.css','assets/main.js'}:
                self.assertEqual(b,self.files[n],n)
        for route in json.loads(self.old[MANIFEST])['v6Routes']:
            pattern=r'<script type="application/json" id="v6-config">(.*?)</script>'
            self.assertEqual(re.search(pattern,self.old[route].decode(),re.S)[1],re.search(pattern,self.files[route].decode(),re.S)[1])
        self.assertFalse(any(n.endswith(('.mp3','.wav','.m4a','.aac','.ogg','.flac','.m3u8','.ts')) for n in self.files))

    def test_upcoming_is_never_promoted_by_calendar_or_player_alone(self):
        pending=self.cms['upcoming'][-1]
        self.assertEqual(pending['slug'],'last-ignition');self.assertEqual(pending['status'],'upcoming')
        self.assertNotIn('last-ignition',{r['slug']for r in self.cms['releases']})
        self.assertNotIn('releases/last-ignition/index.html',self.files)
        self.assertEqual(pending['scheduledAt'],'2026-11-01T20:00:00+09:00')
        self.assertEqual(json.loads(self.files['assets/data/upcoming-releases.json'])['releases'],self.cms['upcoming'])
        self.assertIn('data-release-slug="last-ignition"',self.files['schedule/index.html'].decode())
        changed=copy.deepcopy(self.sources)
        v=next(v for v in changed['videos']if v['kind']=='upcoming');v.update(playability='OK',duration=300,publishedAt='2026-11-02T20:00:00+09:00')
        self.assertEqual(canonical(changed,self.oldcms)['upcoming'][-1]['status'],'upcoming')
        changed=copy.deepcopy(self.sources);next(v for v in changed['videos']if v['kind']=='audio')['playability']='LOGIN_REQUIRED'
        with self.assertRaisesRegex(ValueError,'not verified publicly playable'):canonical(changed,self.oldcms)

    def test_streaming_date_is_separate_from_video_date_and_has_evidence(self):
        r=next(r for r in self.cms['releases']if r['slug']=='anata-dake-ni-okuru-happy-birthday')
        self.assertEqual(r['releaseDate'],'2026-10-25')
        self.assertEqual(r['scheduledStreamingRelease']['releaseDate'],'2026-10-31')
        self.assertEqual(r['scheduledStreamingRelease']['status'],'published')
        self.assertTrue(r['formalJacketImage'].startswith('images/v6-growth/'))
        text=self.files['releases/anata-dake-ni-okuru-happy-birthday/index.html'].decode()
        self.assertIn('data-streaming-state="published"',text)
        self.assertNotIn('data-streaming-state="upcoming"',text)
        s=next(r for r in self.cms['releases']if r['slug']=='onaji-josei-e')
        self.assertEqual(s['releaseDate'],'2026-10-27');self.assertFalse(s['youtubeUrl']);self.assertFalse(s['lyricsAvailable'])

    def test_only_two_unreachable_deezer_buttons_are_suppressed(self):
        policy=json.loads((ROOT/SOURCE/'store-link-policy.json').read_text())
        self.assertEqual({(s['linkcoreCode'],s['service']) for s in policy['suppressed']},
            {('vvasqg5z','deezer'),('aU8rN04N','deezer')})
        html=''.join(b.decode() for n,b in self.files.items() if n.endswith('.html'))
        for code in ['vvasqg5z','aU8rN04N']:
            stream=next(s for s in self.sources['streaming'] if s['code']==code)
            self.assertIn('href="'+stream['url']+'"',html)
            for store in stream['stores']:
                if store['id']=='deezer':self.assertNotIn('href="'+store['url']+'"',html)
                else:self.assertIn('href="'+store['url']+'"',html)
        # An older work's Deezer button is outside this narrowly scoped suppression.
        old=next(s for s in self.sources['streaming'] if s['code']=='66hxyRr8')
        self.assertIn('href="'+next(s['url'] for s in old['stores'] if s['id']=='deezer')+'"',html)

    def test_hero_artwork_is_identical_and_only_matching_images_are_preloaded(self):
        for name in json.loads(self.old[MANIFEST])['v6Routes']:
            old=self.old[name].decode();new=self.files[name].decode()
            hero=r'<section\b[^>]*class="hero\b[^\"]*"[^>]*>\s*(<picture\b.*?</picture>)'
            self.assertEqual(re.search(hero,old,re.S)[1],re.search(hero,new,re.S)[1],name)
            parser=HTML();parser.feed(new)
            self.assertEqual(new.count('rel="preload" as="image"'),2,name)
            self.assertEqual(new.count('src="/assets/v6-background-resilience.js"'),1,name)
            self.assertLess(new.index('src="/assets/v6-background-resilience.js"'),new.index('src="/assets/cinematic-universe-v6.js"'))
            for srcset in re.findall(r'<link rel="preload"[^>]*imagesrcset="([^"]+)"',new):
                self.assertIn('srcset="'+srcset+'"',re.search(hero,new,re.S)[1],name)
            self.assertIn('(min-width:641px) and (orientation:landscape), (min-width:1025px)',new)
        self.assertNotIn('v6-background-resilience.js',self.files['music-production/index.html'].decode())

    def test_exactly_six_shorts_and_four_news_are_added(self):
        old={s['videoId']for s in self.oldcms['youtubeSnapshot']['shortVideos']}
        added=[s for s in self.cms['youtubeSnapshot']['shortVideos']if s['videoId']not in old]
        self.assertEqual(len(added),6);self.assertEqual(len(self.cms['news'])-len(self.oldcms['news']),4)
        product=next(s for s in added if s['videoId']=='6bMysrub3LU')
        self.assertEqual(product['relatedProduct'],'michiru-line-stickers');self.assertNotIn('relatedRelease',product)

    def test_sticker_purchase_requires_published_and_verified_url(self):
        s=self.sources['stickers'];self.assertEqual([(x['count'],x['price'])for x in s[:2]],[(8,190),(16,190)])
        text=self.files['line-stickers/index.html'].decode()
        self.assertEqual(text.count('data-growth-action="sticker"'),2)
        self.assertIn('COMING SOON',text);self.assertEqual(len(s[0]['previews']),8);self.assertEqual(len(s[1]['previews']),16)
        for status,url in [('in-review',s[0]['url']),('published',None),('retired',s[0]['url'])]:
            product={**s[0],'status':status,'url':url}
            output=stickers_section([product],self.sources,self.old,full=True)
            self.assertNotIn('data-growth-action="sticker"',output)
        incomplete={**s[2],'status':'published','url':s[0]['url']}
        self.assertNotIn('data-growth-action="sticker"',stickers_section([incomplete],self.sources,self.old))

    def test_all_html_internal_files_anchors_images_and_jsonld(self):
        parsed={}
        for name,b in self.files.items():
            if name.endswith('.html'):
                p=HTML();p.feed(b.decode());parsed[name]=p
                for im in p.images:
                    self.assertIn('alt',im,name)
                    self.assertFalse(im.get('src','').startswith(SITE+'/images/v6-growth/'),'New render assets must resolve locally in preview: '+name)
        errors=[]
        for name,p in parsed.items():
            for ref in p.refs:
                u=urlsplit(urljoin(SITE+'/'+name,ref))
                if u.netloc!='www.suzukaofficial.com' or u.scheme!='https':continue
                dest=unquote(u.path.lstrip('/'))
                if not dest or dest.endswith('/'):dest+='index.html'
                elif not Path(dest).suffix:dest+='/index.html'
                if dest not in self.files:errors.append((name,dest))
                elif u.fragment and dest in parsed and unquote(u.fragment) not in parsed[dest].anchors:
                    errors.append((name,dest+'#'+u.fragment))
        self.assertEqual(errors,[])

    def test_new_pages_metadata_and_sitemap_preserve_all_old_urls(self):
        ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        def urls(b):return [n.findtext('s:loc',namespaces=ns)for n in ET.fromstring(b)]
        before=urls(self.old['sitemap.xml']);after=urls(self.files['sitemap.xml'])
        self.assertEqual(len(after),381);self.assertTrue(set(before)<=set(after));self.assertEqual(len(after),len(set(after)))
        for name in self.report['addedFiles']:
            if not name.endswith('.html'):continue
            text=self.files[name].decode();canonical=SITE+'/'+name.removesuffix('index.html')
            self.assertIn('rel="canonical" href="'+canonical+'"',text)
            for field in ['og:image','og:title','og:description','twitter:card','description']:self.assertIn(field,text)
            self.assertNotIn('noindex',text)
        for name in ['sitemap.xml','image-sitemap.xml','video-sitemap.xml']:
            u=urls(self.files[name]);self.assertEqual(len(u),len(set(u)),name)

    def test_consultation_mailto_is_preserved_and_preview_is_analytics_gated(self):
        pattern=r'href="(mailto:[^"]+)"'
        self.assertEqual(re.findall(pattern,self.old['music-production/index.html'].decode()),re.findall(pattern,self.files['music-production/index.html'].decode()))
        for n,b in self.files.items():
            if n.endswith('.html') and 'SUZUKA:GA4:START' in b.decode():
                self.assertIn('location.origin !== "'+SITE+'"',b.decode(),n)
        self.assertIn('Facebookでシェア',self.files['assets/social.js'].decode())
        self.assertIn('navigator.share',self.files['assets/social.js'].decode())

    def test_manifest_and_build_are_deterministic(self):
        _,again,_=build();self.assertEqual(again,self.files)
        from build_music_production_release import sha
        m=json.loads(self.files[MANIFEST]);self.assertEqual(set(m['files']),set(self.files)-{MANIFEST})
        self.assertTrue(all(sha(self.files[n])==h for n,h in m['files'].items()))


if __name__=='__main__':unittest.main(verbosity=2)

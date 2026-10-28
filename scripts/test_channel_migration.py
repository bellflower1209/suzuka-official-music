import copy
import unittest
import json
from pathlib import Path
from audit_release_state import has_historical_migration_source
from video_migration import transform_html,video_id,NOTICE

class MigrationDisplay(unittest.TestCase):
    def setUp(self):
        self.pending={'previousVideoId':'12345678901','previousUrl':'https://www.youtube.com/watch?v=12345678901','releaseSlug':'sample','status':'in-progress','officialChannelUrl':'https://www.youtube.com/channel/UCofficial'}
        self.moved={**self.pending,'status':'migrated','replacement':{'id':'abcdefghijk','url':'https://www.youtube.com/watch?v=abcdefghijk','title':'Confirmed song','publishedAt':'2026-10-01T20:00:00+09:00','duration':200,'thumbnail':'https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg'}}
    def test_private_play_link_and_embed_become_notice(self):
        source='<a href="https://youtu.be/12345678901">WATCH MV</a><iframe src="https://www.youtube-nocookie.com/embed/12345678901"></iframe>'
        out=transform_html(source,[self.pending]);self.assertIn(NOTICE,out);self.assertNotIn('iframe',out);self.assertNotIn('youtu.be/12345678901',out)
    def test_only_exact_identity_is_replaced(self):
        source='<a href="https://www.youtube.com/watch?v=12345678901">Video</a><a href="https://www.youtube.com/watch?v=98765432100">Other</a>'
        out=transform_html(source,[self.moved]);self.assertIn(self.moved['replacement']['url'],out);self.assertIn('v=98765432100',out)
    def test_private_video_schema_removed_but_work_retained(self):
        source='<script type="application/ld+json">{"@graph":[{"@type":"MusicRecording","name":"Song","subjectOf":{"@id":"#video"}},{"@type":"VideoObject","@id":"#video","contentUrl":"https://www.youtube.com/watch?v=12345678901"}]}</script>'
        out=transform_html(source,[self.pending]);self.assertIn('MusicRecording',out);self.assertNotIn('VideoObject',out);self.assertNotIn('subjectOf',out)
    def test_verified_replacement_has_its_own_publication_date(self):
        source='<script type="application/ld+json">{"@type":"VideoObject","contentUrl":"https://www.youtube.com/watch?v=12345678901","uploadDate":"2026-01-01"}</script>'
        out=transform_html(source,[self.moved]);self.assertIn('2026-10-01T20:00:00+09:00',out);self.assertNotIn('2026-01-01',out)
    def test_transform_is_idempotent(self):
        source='<a href="https://www.youtube.com/watch?v=12345678901">Watch</a>'
        for row in [self.pending,self.moved]:
            first=transform_html(source,[row]);self.assertEqual(first,transform_html(first,[row]))
    def test_non_video_channel_and_thumbnails_are_not_play_links(self):
        self.assertEqual(video_id('https://www.youtube.com/@artist'),'');self.assertEqual(video_id('https://i.ytimg.com/vi/12345678901/hqdefault.jpg'),'')

class HistoricalSource(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]
        cms=json.loads((root/'assets/data/creator-cms.json').read_text())
        self.item=next(r for r in cms['releases'] if r['slug']=='mia')
        self.artist=next(a for a in cms['artists'] if a['slug']=='enomoto-mia')
        proof=json.loads((root/'docs/channel-migration-20261026.json').read_text())
        self.record=next(r for r in proof['records'] if r['releaseSlug']=='mia')
    def test_evidenced_historical_work_is_still_published(self):
        self.assertTrue(has_historical_migration_source(self.item,self.record,self.artist))
    def test_blank_video_without_migration_is_not_a_source(self):
        self.assertFalse(has_historical_migration_source({'youtubeUrl':'','status':'published'},None,self.artist))
    def test_wrong_official_channel_is_rejected(self):
        artist={**self.artist,'officialYoutubeChannelId':'UCunverified'}
        self.assertFalse(has_historical_migration_source(self.item,self.record,artist))
    def test_original_video_history_cannot_be_removed(self):
        item={**self.item,'videoHistory':[]}
        self.assertFalse(has_historical_migration_source(item,self.record,self.artist))
    def test_upcoming_work_cannot_use_historical_exception(self):
        self.assertFalse(has_historical_migration_source({**self.item,'status':'upcoming'},self.record,self.artist))
    def test_private_history_cannot_claim_public_playback(self):
        item=copy.deepcopy(self.item);item['videoHistory'][0]['currentAvailability']='public'
        self.assertFalse(has_historical_migration_source(item,self.record,self.artist))
if __name__=='__main__':unittest.main()

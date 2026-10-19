#!/usr/bin/env python3
"""Regression gates: private-only audio scope; historical silent rollback stays valid."""
import copy,json,re,unittest
from pathlib import Path
from verify_public_release import read_release,verify_private_audio
ROOT=Path(__file__).resolve().parents[1]
class Gate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.info,cls.files=read_release(ROOT,allow_pending=True)
  cls.routes=json.loads(cls.files['suzuka-v6-candidate-manifest.json'])['v6Routes']
 def check_bad(self,info=None,files=None):
  with self.assertRaises(ValueError):verify_private_audio(info or self.info,files or self.files,self.routes)
 def approved(self):
  i=copy.deepcopy(self.info);i['privateAudioApproval']['status']='approved';return i
 def mutate(self,fn):
  files=dict(self.files);p=self.routes[0];text=files[p].decode();m=re.search(r'(<script type="application/json" id="v6-config">)(.*?)(</script>)',text,re.S);c=json.loads(m[2]);fn(c);files[p]=(text[:m.start(2)]+json.dumps(c)+text[m.end(2):]).encode();return files
 def test_pending_cannot_publish(self):
  i=self.approved();i['privateAudioApproval']['status']='pending-final-gate';self.check_bad(i)
 def test_approved_private_endpoint(self):
  verify_private_audio(self.approved(),self.files,self.routes)
 def test_old_public_archive_scope_rejected(self):
  i=self.approved();i['privateAudioApproval']['scope']='website-playback-and-public-git-archive';self.check_bad(i)
 def test_public_git_audio_permission_rejected(self):
  i=self.approved();i['privateAudioApproval']['publicGitAudioAllowed']=True;self.check_bad(i)
 def test_direct_mp3_rejected(self):
  self.check_bad(self.approved(),self.mutate(lambda c:c['worlds'][0]['music'].update(source='https://example.invalid/song.mp3')))
 def test_unapproved_track_hash_rejected(self):
  self.check_bad(self.approved(),self.mutate(lambda c:c['worlds'][0]['music'].update(sha256='0'*64)))
 def test_other_host_rejected(self):
  self.check_bad(self.approved(),self.mutate(lambda c:c['audioDelivery'].update(endpoint='https://example.invalid/v1/')))
 def test_local_host_rejected(self):
  self.check_bad(self.approved(),self.mutate(lambda c:c['audioDelivery'].update(endpoint='http://127.0.0.1:8871/v1/')))
 def test_missing_track_rejected(self):
  i=self.approved();i['privateAudioApproval']['tracks'].pop();self.check_bad(i)
 def test_missing_user_record_rejected(self):
  i=self.approved();i['privateAudioApproval']['source']='inferred';self.check_bad(i)
 def test_preview_mode_rejected(self):
  self.check_bad(self.approved(),self.mutate(lambda c:c.update(publicationMode='preview')))
if __name__=='__main__':unittest.main()

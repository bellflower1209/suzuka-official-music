#!/usr/bin/env python3
"""Prepare approved environment derivatives; never opens artist artwork.

CI checks stored dimensions/hashes instead of re-encoding across codec builds.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true');args=p.parse_args()
 source=args.root/'site-content/baba-nova';path=source/'backgrounds.json';data=json.loads(path.read_text())
 assert data['approval']=={'source':'explicit-user-message','date':'2026-10-28','scope':'new-night-background-no-people-no-text'}
 if args.check:
  for item in data['masters']+data['files']:
   file=source/item['path'];assert file.is_file() and not file.is_symlink();assert sha(file.read_bytes())==item['sha256'];assert Image.open(file).size==(item['width'],item['height'])
  print('PASS 2 approved masters and8 immutable responsive variants');return
 masters=[];files=[];out=source/'backgrounds';out.mkdir(exist_ok=True)
 for name,widths in [('landscape',[768,1280,1600]),('mobile',[768])]:
  master=source/f'background-{name}.png';assert master.is_file() and not master.is_symlink();image=Image.open(master).convert('RGB')
  masters.append({'path':master.name,'width':image.width,'height':image.height,'sha256':sha(master.read_bytes())})
  for width in widths:
   assert width<=image.width,'Do not upscale the generated master'
   im=image.resize((width,round(width*image.height/image.width)),Image.Resampling.LANCZOS)
   for fmt,q in [('webp',84),('avif',55)]:
    file=out/f'{name}-{width}.{fmt}';assert not file.is_symlink();im.save(file,quality=q,**({'method':6} if fmt=='webp' else {'speed':6}));raw=file.read_bytes()
    assert len(raw)<300000,'Review excessive background payload'
    files.append({'path':str(file.relative_to(source)),'publicPath':'assets/baba-nova/'+file.name,'width':im.width,'height':im.height,'bytes':len(raw),'sha256':sha(raw)})
 data.update(masters=masters,files=files);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('Prepared 8 approved responsive environment variants')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Encode authorized environment plates and proportional official thumbnails.

Pillow is only needed when preparing assets, not by the normal static build.
No image synthesis, retouching, portrait crop or original replacement happens here.
"""
from pathlib import Path
import argparse, hashlib, json, shutil
from PIL import Image, ImageOps

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def encode(image, path, fmt):
    kwargs = {'quality': 81, 'method': 6} if fmt == 'WEBP' else {'quality': 68, 'speed': 6}
    image.save(path, fmt, **kwargs)
    return {'path': path.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path), 'width': image.width, 'height': image.height}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args();root = args.root.resolve();output = root/'assets/cinema'
    output.mkdir(parents=True, exist_ok=True);args.archive.mkdir(parents=True, exist_ok=True)
    records = []
    for item in json.loads(args.sources.read_text()):
        mobile_source = item.get('mobileSource')
        source = Path(item['source']);raw = args.archive/(item['id']+'.png')
        if not raw.exists():shutil.copy2(source, raw)
        if digest(raw) != digest(source):raise ValueError('Archived original mismatch')
        image = ImageOps.exif_transpose(Image.open(source));variants = []
        item = {k:v for k,v in item.items() if k not in ['source','mobileSource']}
        item.update(sourceFile=source.name, sourceSha256=digest(source), sourceWidth=image.width, sourceHeight=image.height)
        if item['kind'] == 'environment':
            image = image.convert('RGB')
            for width in [768,1280,1600]:
                if width > image.width:raise ValueError('Do not upscale environment originals')
                resized = image.resize((width,round(image.height*width/image.width)), Image.Resampling.LANCZOS)
                for suffix,fmt in [('webp','WEBP'),('avif','AVIF')]:
                    record=encode(resized,output/f"{item['id']}-{width}.{suffix}",fmt);record['path']=str(Path(record['path']).relative_to(root));variants.append(record)
            # Art direction for tall screens: crop only the empty environment,
            # keeping the central architecture. Official portraits are never cropped.
            if mobile_source:
                mobile_path=Path(mobile_source);mobile_raw=args.archive/(item['id']+'-mobile.png')
                if not mobile_raw.exists():shutil.copy2(mobile_path,mobile_raw)
                if digest(mobile_raw)!=digest(mobile_path):raise ValueError('Archived mobile original mismatch')
                mobile_original=ImageOps.exif_transpose(Image.open(mobile_path)).convert('RGB')
                item.update(mobileSourceFile=mobile_path.name,mobileSourceSha256=digest(mobile_path),mobileSourceWidth=mobile_original.width,mobileSourceHeight=mobile_original.height)
                mobile=ImageOps.fit(mobile_original,(round(image.height*2/3),image.height),Image.Resampling.LANCZOS,centering=(.5,.5))
            else:
                mobile = ImageOps.fit(image,(round(image.height*2/3),image.height),Image.Resampling.LANCZOS,centering=(.5,.5))
            for suffix,fmt in [('webp','WEBP'),('avif','AVIF')]:
                record=encode(mobile,output/f"{item['id']}-mobile.{suffix}",fmt);record['path']=str(Path(record['path']).relative_to(root));variants.append(record)
        else:
            if item['kind']=='transparent-frame' and ('A' not in image.getbands() or image.getextrema()[-1][0]!=0):raise ValueError('Portal frame must contain genuine transparency')
            for width in [480,960]:
                resized=image.resize((width,round(image.height*width/image.width)),Image.Resampling.LANCZOS)
                record=encode(resized,output/f"{item['id']}-{width}.webp",'WEBP');record['path']=str(Path(record['path']).relative_to(root));variants.append(record)
        item['variants']=variants;records.append(item)
    official=[]
    (output/'official').mkdir(exist_ok=True)
    cms=json.loads((root/'assets/data/creator-cms.json').read_text())
    for artist in cms['artists']:
        if not artist.get('image'):continue
        source=root/artist['image'];image=ImageOps.exif_transpose(Image.open(source)).convert('RGB');variants=[]
        for requested in [480,960]:
            width=min(requested,image.width);resized=image.resize((width,round(width*image.height/image.width)),Image.Resampling.LANCZOS)
            record=encode(resized,output/'official'/f"{artist['slug']}-{requested}.webp",'WEBP');record['path']=str(Path(record['path']).relative_to(root));variants.append(record)
        official.append({'id':artist['slug'],'source':artist['image'],'sourceSha256':digest(source),'usage':'Proportional encoding of canonical official image; entire composition preserved; not generated','variants':variants})
    manifest={'version':3,'serviceTerms':'https://openai.com/policies/terms-of-use/','rightsNote':'Generated decorative environments are used within this user-authorized redesign. No third-party stock image license or exclusivity is asserted. Official identity assets retain their existing provenance.','assets':records,'officialThumbnails':official}
    (root/'assets/data/celestial-cinema-assets.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'environmentPlates':sum(i['kind']=='environment' for i in records),'physicalDoorTextures':sum(i['kind']=='door-leaves' for i in records),'transparentFrames':sum(i['kind']=='transparent-frame' for i in records),'officialThumbnails':len(official),'encodedFiles':sum(len(i['variants']) for i in records+official),'totalBytes':sum(v['bytes'] for i in records+official for v in i['variants'])}))

if __name__=='__main__':main()

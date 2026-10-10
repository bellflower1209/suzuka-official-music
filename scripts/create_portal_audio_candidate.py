#!/usr/bin/env python3
"""Deterministic, original DSP sound study. NOT the approved SUZUKA Ver.2."""
import array, hashlib, json, math, random, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RATE=48000
DURATION=3.1
rng=random.Random(4102026)
channels=[[],[]]; low=[0.,0.]; phase=0.
for i in range(round(RATE*DURATION)):
    t=i/RATE
    # Starts at opening (.9s on the visual timeline). Gentle attack; bass and
    # stone friction recede before the leaves settle. Air bloom follows entry.
    attack=min(1.,t/.10)**2
    body=attack*math.exp(-t/1.0)*max(0.,min(1.,(1.7-t)/.5))
    phase+=2*math.pi*(43+35*math.exp(-t*4))/RATE
    bass=(math.sin(phase)+.28*math.sin(phase*1.99))*.48*body
    air=max(0.,min(1.,(t-1.65)/.25))*max(0.,min(1.,(3.1-t)/.55))*.14
    for c in range(2):
        noise=rng.uniform(-1,1);low[c]+=.028*(noise-low[c])
        friction=(low[c]*1.8+math.sin(t*2*math.pi*(137+c*3))*.055)*body
        shimmer=math.sin(t*2*math.pi*(311+c*7))*math.sin(t*2*math.pi*.7)*.035*air
        channels[c].append(bass+friction*.20+low[c]*air+shimmer)
peak=max(abs(x) for ch in channels for x in ch);scale=.70/max(peak,1e-9)
pcm=array.array('h',(round(channels[c][i]*scale*32767) for i in range(len(channels[0])) for c in range(2)))
p=ROOT/'assets/audio/door-heavy-candidate-v4.wav';p.parent.mkdir(exist_ok=True)
with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm.tobytes())
manifest={'status':'new-candidate-not-adopted','name':'Portal V4 DSP sound study','path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sampleRate':RATE,'channels':2,'durationSeconds':DURATION,'peakDbFS':round(20*math.log10(.70),2),'provenance':'Original deterministic procedural synthesis; no sampled music or official Ver.2 audio.','rights':'Original project sound candidate, locally synthesized for this review. No third-party samples. Formal adoption pending.','timelineOffsetMs':900,'generator':'scripts/create_portal_audio_candidate.py'}
(ROOT/'assets/data/portal-audio-candidate.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))

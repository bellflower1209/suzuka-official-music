#!/usr/bin/env node
/* V5 acceptance: actual candidate decoding; formal Ver.2 remains untested/missing. */
const {chromium,webkit,devices}=require(process.env.CG_PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base=(process.argv[2]||'http://127.0.0.1:8825/').replace(/\/?$/,'/');
const out=process.env.CG_QA_OUTPUT||'/private/tmp/celestial-portal-v5';fs.mkdirSync(out,{recursive:true});
const artists=JSON.parse(fs.readFileSync(root+'/assets/data/creator-cms.json')).artists;
const results=[];let browser;
async function test(name,fn){try{const details=await fn();results.push({name,status:'PASS',details});console.log('PASS',name)}catch(e){results.push({name,status:'FAIL',error:e.message});console.error('FAIL',name,e.message)}}
async function home(p){await p.goto(base,{waitUntil:'load'});}
async function context(options={}){return browser.newContext(options)}
(async()=>{
 for(const engine of ['chrome','webkit']){
  browser=await(engine==='chrome'?chromium:webkit).launch({headless:true,...(engine==='chrome'?{executablePath:process.env.CG_CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}:{})});
  const c=await context(engine==='webkit'?devices['iPhone 13']:{viewport:{width:1440,height:1000}});const p=await c.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
  for(const a of artists.filter(a=>!process.env.CG_ARTIST_FILTER||process.env.CG_ARTIST_FILTER.split(',').includes(a.slug)))await test(engine+' full portal '+a.slug,async()=>{
   await home(p);await p.locator('[data-cg-world="'+a.slug+'"]').click();
   await p.waitForFunction(()=>document.querySelector('dialog[open]')?.dataset.phase==='approach');
   const samples=await p.evaluate(()=>Promise.all([200,700,1700,2650,3500,4400].map(ms=>new Promise(resolve=>setTimeout(()=>{
    const d=document.querySelector('dialog[open]');if(!d){resolve({ms,missing:true});return;}
    resolve({ms,phase:d.dataset.phase,realm:d.classList.contains('cg-infernal'),scene:d.querySelector('.cg-door-beyond img').currentSrc,left:getComputedStyle(d.querySelector('.cg-door-left')).transform,right:getComputedStyle(d.querySelector('.cg-door-right')).transform,origins:[getComputedStyle(d.querySelector('.cg-door-left')).transformOrigin,getComputedStyle(d.querySelector('.cg-door-right')).transformOrigin],portal:getComputedStyle(d.querySelector('.cg-door-portal')).transform,world:getComputedStyle(d.querySelector('.cg-door-beyond')).transform,wash:getComputedStyle(d.querySelector('.cg-door-wash')).backgroundImage,washOpacity:getComputedStyle(d.querySelector('.cg-door-wash')).opacity});
   },ms)))));
   assert(samples.every(s=>!s.missing));assert.deepEqual(samples.map(s=>s.phase),['approach','glow','opening','world','entry','mist']);
   assert(samples[2].left.includes('matrix3d'));assert.notEqual(samples[2].left,samples[0].left);assert(samples[2].origins[0].startsWith('0px'));assert(!samples[2].origins[1].startsWith('0px'));
   assert.notEqual(samples[4].portal,samples[3].portal);assert.notEqual(samples[4].world,samples[3].world);assert(samples[5].washOpacity>.25);assert(samples.every(s=>s.realm===(a.slug==='nox')));
   if(a.slug==='nox')assert(/rgba?\(16, 7, 14[,)]/.test(samples[5].wash));
   await p.waitForURL(base+'artists/'+a.slug+'/');await p.waitForFunction(()=>!document.querySelector('.cg-arrival'));
   const source=await p.locator('.explorer-hero .cg-scene img').evaluate(i=>i.currentSrc);assert.equal(source,samples[0].scene);
   assert.equal(await p.locator('body').getAttribute('data-cg-realm'),a.slug==='nox'?'infernal':'celestial');
   assert.equal(errors.length,0);return{samples,destinationSource:source,physicalDevice:false};
  });
  await test(engine+' failed navigation restores focus and scrolling',async()=>{
   await home(p);await p.route('**/artists/asteria/',r=>r.fulfill({status:503,contentType:'text/html',body:'Unavailable'}));await p.locator('[data-cg-world="asteria"]').click();await p.locator('.cg-door-skip').click();await p.locator('.cg-nav-error').waitFor();assert.equal(p.url(),base);assert.equal(await p.locator('dialog[open]').count(),0);assert.equal(await p.evaluate(()=>document.body.style.overflow),'');await p.locator('.cg-nav-error button').click();assert.equal(await p.locator(':focus').getAttribute('data-cg-world'),'asteria');await p.unroute('**/artists/asteria/');
  });
  await test(engine+' data saver bypasses camera and sound',async()=>{
   await p.addInitScript(()=>{Object.defineProperty(navigator,'connection',{value:{saveData:true},configurable:true});localStorage.setItem('suzuka.cg.sound','on')});await home(p);const audio=[];const listener=r=>{if(r.url().includes('/audio/'))audio.push(r.url())};p.on('request',listener);await p.locator('[data-cg-world="nox"]').click();await p.waitForURL(base+'artists/nox/');assert.equal(audio.length,0);p.off('request',listener);
  });
  await c.close();
  await test(engine+' real candidate: opt-in, scheduled onset, volume, cancellation',async()=>{
   const c=await context();const p=await c.newPage();await p.addInitScript(()=>{
    window._audio=[];const Context=window.AudioContext||window.webkitAudioContext;
    const start=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(when,...args){window._audio.push({type:'start',now:this.context.currentTime,when,duration:this.buffer.duration,channels:this.buffer.numberOfChannels});return start.call(this,when,...args)};
    window._filters=[];const filter=Context.prototype.createBiquadFilter;Context.prototype.createBiquadFilter=function(){const node=filter.call(this);window._filters.push(node);return node};
    const original=Context.prototype.createGain;Context.prototype.createGain=function(){const gain=original.call(this);if(!window._testGain)window._testGain=gain;return gain};
   });
   await home(p);assert.equal(await p.evaluate(()=>window._audio.length),0);await p.locator('.cg-settings summary').click();await p.locator('[data-cg-sound]').click();assert((await p.locator('[data-cg-sound]').textContent()).includes('候補音声 ON'));
   await p.locator('[data-cg-volume]').evaluate(e=>{e.value='0.15';e.dispatchEvent(new Event('input',{bubbles:true}))});
   await p.locator('[data-cg-world="asteria"]').click();await p.waitForFunction(()=>window._audio.some(e=>e.type==='start'));
   const audio=await p.evaluate(()=>({events:window._audio,volume:window._testGain.gain.value,description:document.querySelector('#cg-door-description').textContent}));assert.equal(audio.events.length,1);assert(Math.abs(audio.events[0].when-audio.events[0].now-.95)<.08);assert.equal(audio.events[0].channels,2);assert(Math.abs(audio.events[0].duration-3.1)<.001);assert(Math.abs(audio.volume-.15)<.001);assert(audio.description.includes('正式Ver.2ではありません'));
   await p.locator('[data-cg-dialog-volume]').evaluate(e=>{e.value='0.12';e.dispatchEvent(new Event('input',{bubbles:true}))});await p.waitForTimeout(200);assert(Math.abs(await p.evaluate(()=>window._testGain.gain.value)-.12)<.002);
   await p.locator('[data-cg-dialog-sound]').click();assert.equal(await p.locator('[data-cg-dialog-sound]').getAttribute('aria-pressed'),'false');
   await p.keyboard.press('Escape');await p.waitForTimeout(4700);assert.equal(p.url(),base);await p.locator('.cg-settings summary').click();assert.equal(await p.locator('[data-cg-sound]').getAttribute('aria-pressed'),'false');
   await p.locator('[data-cg-world="nox"]').click();await p.waitForTimeout(1000);assert.equal(await p.evaluate(()=>window._audio.length),1);await p.keyboard.press('Escape');if(!await p.locator('.cg-settings').evaluate(e=>e.open))await p.locator('.cg-settings summary').click();await p.locator('[data-cg-sound]').click();await p.locator('[data-cg-world="nox"]').click();await p.waitForFunction(()=>window._audio.length===2);const noxFilter=await p.evaluate(()=>window._filters.map(f=>({type:f.type,hz:f.frequency.value,q:f.Q.value})));assert.deepEqual(noxFilter,[{type:'lowpass',hz:720,q:Math.fround(.45)}]);await p.keyboard.press('Escape');await c.close();return{actualCandidateDecoded:true,formalVer2Decoded:false,noxFilter,...audio};
  });
  await browser.close();
 }
 fs.writeFileSync(out+'/portal-results.json',JSON.stringify({checks:results,failures:results.filter(r=>r.status==='FAIL').length,physicalDeviceValidated:false},null,2));if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
})().catch(e=>{console.error(e);browser?.close();process.exitCode=1});

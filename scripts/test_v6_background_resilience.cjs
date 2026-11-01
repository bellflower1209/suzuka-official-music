// Failure, timeout and SPA regression tests for the generated, browser-native recovery.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.argv[2];
if (!root) throw new Error('Pass the generated candidate root');
const code = fs.readFileSync(path.join(root, 'assets/v6-background-resilience.js'), 'utf8');

function fixture({loaded = false, visible = true, avif = true, selectedWebp = false, eligible = true, src = '/assets/cinema/hero-1600.webp'} = {}) {
  const listeners = new Map();
  const img = {dataset:{},complete:loaded,naturalWidth:loaded ? 1600 : 0,isConnected:true,changes:0,
    currentSrc:avif && !selectedWebp ? '/assets/cinema/hero-mobile.avif' : src,
    matches:()=>eligible,closest:()=>eligible ? {} : null,
    getBoundingClientRect:()=>({width:390,height:844,top:visible ? 0 : 3000,bottom:visible ? 844 : 3844}),
    getAttribute:name=>name==='src' ? src : null,
    addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name),
    load:()=>{img.complete=true;img.naturalWidth=1600;listeners.get('load')?.();},
    fail:()=>{img.complete=true;img.naturalWidth=0;listeners.get('error')?.();}};
  const source = type => {
    let media='',srcset='/assets/cinema/hero-mobile.'+(type==='image/avif'?'avif':'webp');
    return {get media(){return media;},set media(value){media=value;img.complete=false;img.changes++;},
      get srcset(){return srcset;},set srcset(value){srcset=value;img.complete=false;img.changes++;}};
  };
  const avifSource=source('image/avif'),webpSource=source('image/webp');
  img.parentElement={querySelectorAll:selector=>selector.includes('avif') ? (avif ? [avifSource] : []) : [webpSource]};
  Object.defineProperty(img,'src',{get:()=>src,set:value=>{src=value;img.complete=false;img.changes++;}});
  return {img,avifSource,webpSource,listeners};
}
function environment(images) {
  let time=0,id=0,mutation,registrations=0;
  const timers=new Map(),events=new Map(),docEvents=new Map();
  const document={baseURI:'https://preview.invalid/',hidden:false,documentElement:{},querySelectorAll:()=>images,
    addEventListener:(name,fn)=>{registrations++;docEvents.set(name,fn);}};
  const window={addEventListener:(name,fn)=>{registrations++;events.set(name,fn);}};
  const context=vm.createContext({document,window,navigator:{onLine:true},location:{origin:'https://preview.invalid'},
    URL,Map,innerHeight:844,MutationObserver:class {constructor(fn){mutation=fn;}observe(){}},
    setTimeout:(fn,ms)=>{timers.set(++id,{at:time+ms,fn});return id;},clearTimeout:id=>timers.delete(id)});
  const run=()=>vm.runInContext(code,context);
  run();
  return {timers,events,docEvents,document,context,run,get registrations(){return registrations;},scan:()=>mutation(),
    advance:ms=>{time+=ms;let safety=0;for(const [id,t] of timers){if(t.at<=time){timers.delete(id);t.fn();}if(++safety>100)throw Error('Unbounded recovery');}}};
}

// Successful first paint does not trigger alternate downloads or retries.
{
  const {img}=fixture({loaded:true}),env=environment([img]);env.advance(30000);
  assert.equal(img.changes,0);assert.equal(env.timers.size,0);assert.equal(img.fetchPriority,'high');
  const registrations=env.registrations;
  env.run();assert.equal(env.registrations,registrations,'duplicate installation must not duplicate handlers');
}
// A stalled AVIF request switches to the existing responsive WebP after 6.5 seconds.
{
  const f=fixture(),env=environment([f.img]);env.advance(6499);assert.equal(f.img.changes,0);
  env.advance(1);assert.equal(f.avifSource.media,'not all');assert.equal(f.img.dataset.v6BackgroundState,'webp');
  assert(!f.webpSource.srcset.includes('retry'));f.img.load();env.advance(30000);
  assert.equal(f.img.dataset.v6BackgroundState,'ready');assert.equal(env.timers.size,0);
}
// Failures exhaust two recovery stages and never reload the page or loop.
{
  const f=fixture(),env=environment([f.img]);f.img.fail();f.img.fail();
  assert(f.webpSource.srcset.includes('v6-background-retry=1'));
  const count=f.img.changes;f.img.fail();f.img.fail();env.advance(60000);
  assert.equal(f.img.changes,count);assert.equal(f.img.dataset.v6BackgroundState,'unavailable');assert.equal(env.timers.size,0);
}
// A WebP-only browser gets one retry, without inventing another format or source.
{
  const f=fixture({selectedWebp:true}),env=environment([f.img]);f.img.fail();
  assert(f.img.src.includes('v6-background-retry=1'));const changes=f.img.changes;
  f.img.fail();env.advance(60000);assert.equal(f.img.changes,changes);
}
// Hidden/offline tabs do not spend retries; reconnection resumes bounded recovery.
{
  const f=fixture(),env=environment([f.img]);env.context.navigator.onLine=false;
  env.advance(6500);assert.equal(f.img.changes,0);assert.equal(f.img.dataset.v6BackgroundState,'offline');
  env.context.navigator.onLine=true;env.events.get('online')();env.advance(6500);assert.equal(f.avifSource.media,'not all');
  env.document.hidden=true;env.docEvents.get('visibilitychange')();assert.equal(env.timers.size,0);
  env.document.hidden=false;env.docEvents.get('visibilitychange')();assert.equal(env.timers.size,1);
}
// Body replacement cleans up old timers/listeners and watches the incoming background.
{
  const a=fixture(),b=fixture(),images=[a.img],env=environment(images);a.img.isConnected=false;images[0]=b.img;env.scan();
  assert.equal(a.listeners.size,0);assert.equal(env.timers.size,1);env.advance(6500);
  assert.equal(a.img.changes,0);assert.equal(b.avifSource.media,'not all');
}
// No eager recovery for offscreen pictures, unrelated artwork, or external/unapproved paths.
{
  const imgs=[fixture({visible:false}).img,fixture({eligible:false}).img,fixture({src:'https://other.invalid/image.webp'}).img,
    fixture({src:'/assets/v6-music/private.webp'}).img];
  const env=environment(imgs);env.advance(60000);assert(imgs.every(img=>img.changes===0));assert.equal(env.timers.size,0);
}
console.log('PASS: 7 background recovery scenarios (success, timeout, failures, WebP-only, offline, SPA cleanup, scope).');

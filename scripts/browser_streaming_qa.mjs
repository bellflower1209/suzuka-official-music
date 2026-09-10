import fs from 'node:fs';
import assert from 'node:assert/strict';
const base=(process.argv[2]||'http://127.0.0.1:8765/').replace(/\/?$/,'/');
const target=(await(await fetch('http://127.0.0.1:9223/json')).json()).find(t=>t.type==='page');
const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
let id=0;const pending=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}
 if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);
 if(m.method==='Runtime.consoleAPICalled'&&m.params.type==='error')errors.push(m.params);
 if(m.method==='Network.responseReceived'&&m.params.response.status>=400)errors.push(m.params.response.url);
};
function send(method,params={}){const n=++id;ws.send(JSON.stringify({id:n,method,params}));return new Promise((resolve,reject)=>pending.set(n,{resolve,reject}));}
const evaluate=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;
await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.setCacheDisabled',{cacheDisabled:true});
await send('Emulation.setTimezoneOverride',{timezoneId:'America/Los_Angeles'});
const routes=['','releases/hanakotoba/','news/hanakotoba-streaming-release/','artists/enomoto-mia/','search/?q=花言葉','releases/','features/suzuka-with-care/','releases/yume-to-kaigo-to-watashitachi/','releases/sedai-wo-koete-mama-e/'];
const results=[];fs.mkdirSync('/private/tmp/suzuka-streaming-qa',{recursive:true});
for(const width of [390,768,1280])for(const route of routes){
 await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});
 await send('Page.navigate',{url:new URL(route,base).href});
 for(let i=0;i<80;i++){if(await evaluate(`document.readyState==='complete'&&!!document.querySelector('.suzuka-music-player')`))break;await new Promise(r=>setTimeout(r,150));}
 await evaluate(`(async()=>{for(const img of document.images){img.loading='eager';}await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));})()`);
 const result=await evaluate(`(()=>{const p=document.querySelector('.suzuka-music-player');const b=document.querySelector('.streaming-release');b?.scrollIntoView({block:'center',behavior:'instant'});const a=b?.querySelector('.streaming-primary');a?.scrollIntoView({block:'center',behavior:'instant'});const x=a?.getBoundingClientRect(),y=p?.getBoundingClientRect();return {width:innerWidth,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,images:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src),player:!!p,autoplay:document.querySelectorAll('[autoplay],iframe[src*="autoplay=1"]').length,overlap:!!x&&!!y&&x.left<y.right&&x.right>y.left&&x.top<y.bottom&&x.bottom>y.top,status:b?.querySelector('[data-streaming-date]')?.textContent,cta:a?.href,search:document.querySelector('[data-search-count]')?.textContent,searchStreaming:document.querySelector('[data-search-results]')?.textContent.includes('配信サービスで聴く')}})()`);
 assert.equal(result.overflow,0,JSON.stringify({route,width,result}));assert.deepEqual(result.images,[],route);assert.equal(result.autoplay,0,route);assert.equal(result.overlap,false,JSON.stringify({route,width,result}));assert.equal(result.player,true,route);
 if(route.includes('?q=')){assert.equal(result.search,'1');assert.equal(result.searchStreaming,true);}
 results.push({route,width,...result});
 if(['','releases/hanakotoba/','news/hanakotoba-streaming-release/'].includes(route)&&width===390){const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync('/private/tmp/suzuka-streaming-qa/'+(route.replaceAll('/','-')||'home')+'390.png',Buffer.from(shot.data,'base64'));}
}
// Run the actual page script at the Tokyo midnight boundary while the browser is in Los Angeles.
for(const [instant,expected] of [['2026-09-10T14:59:59Z','明日リリース'],['2026-09-10T15:00:00Z','NOW STREAMING'],['2026-09-11T15:00:00Z','NOW STREAMING']]){
 const {identifier}=await send('Page.addScriptToEvaluateOnNewDocument',{source:`{const RealDate=Date;window.Date=class extends RealDate{constructor(...args){super(...(args.length?args:[${JSON.stringify(instant)}]));}static now(){return new RealDate(${JSON.stringify(instant)}).getTime();}};}`});
 await send('Page.navigate',{url:base});
 for(let i=0;i<80;i++){if(await evaluate(`document.querySelector('[data-streaming-date]')?.textContent===${JSON.stringify(expected)}`))break;await new Promise(r=>setTimeout(r,100));}
 assert.equal(await evaluate(`document.querySelector('[data-streaming-date]').textContent`),expected,instant);
 await send('Page.removeScriptToEvaluateOnNewDocument',{identifier});
}
await send('Emulation.setTimezoneOverride',{timezoneId:'Asia/Tokyo'});
assert.deepEqual(errors,[]);ws.close();
fs.writeFileSync('/private/tmp/suzuka-streaming-qa/results.json',JSON.stringify({base,results,dateBoundary:'passed',errors},null,2));
console.log('Streaming browser QA passed: 27 views, Tokyo midnight boundary in Los Angeles, one search result, no overflow/image/JS errors/autoplay/player overlap.');

import fs from 'node:fs';
import assert from 'node:assert/strict';

const base=(process.argv[2]||'http://127.0.0.1:8766/').replace(/\/?$/,'/');
const targets=await(await fetch('http://127.0.0.1:9223/json')).json();
const target=targets.find(item=>item.type==='page');
assert.ok(target,'Chrome page target');
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve=>ws.onopen=resolve);
let id=0;const pending=new Map(),errors=[];
ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(message.error):task.resolve(message.result);}if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);if(message.method==='Runtime.consoleAPICalled'&&message.params.type==='error')errors.push(message.params);if(message.method==='Network.responseReceived'&&message.params.response.status>=400)errors.push({status:message.params.response.status,url:message.params.response.url});};
const send=(method,params={})=>{const requestId=++id;ws.send(JSON.stringify({id:requestId,method,params}));return new Promise((resolve,reject)=>pending.set(requestId,{resolve,reject}));};
const evaluate=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;
await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Network.setCacheDisabled',{cacheDisabled:true});
const routes=['','artists/enomoto-mia/','news/enomoto-mia-september-21-double-release/','releases/hello-hello-halloween/','schedule/','search/?q=Hello%20Hello%20Halloween','search/?q=百万告','search/?q=JOYSOUND','search/?q=カラオケ'];
const results=[];fs.mkdirSync('/private/tmp/suzuka-mia-schedule-qa',{recursive:true});
for(const width of [390,768,1280])for(const route of routes){
  await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});
  await send('Page.navigate',{url:new URL(route,base).href});
  for(let tick=0;tick<80;tick++){if(await evaluate("document.readyState==='complete'"))break;await new Promise(resolve=>setTimeout(resolve,100));}
  await evaluate("Promise.race([Promise.all([...document.images].map(image=>image.decode().catch(()=>{}))),new Promise(resolve=>setTimeout(resolve,800))])");
  if(route.startsWith('search/?q='))await new Promise(resolve=>setTimeout(resolve,300));
  const result=await evaluate(`(()=>{const player=document.querySelector('.suzuka-music-player');const panel=document.querySelector('.mia-release-schedule');const playerRect=player?.getBoundingClientRect();const panelRect=panel?.getBoundingClientRect();const hit=(a,b)=>!!a&&!!b&&a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;return {overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,brokenImages:[...document.images].filter(image=>!image.complete||image.naturalWidth===0).map(image=>image.src),autoplay:document.querySelectorAll('[autoplay],iframe[src*="autoplay=1"]').length,player:!!player,playerOverlap:hit(playerRect,panelRect),scheduleItems:panel?.querySelectorAll('.mia-schedule-item').length||0,searchText:document.querySelector('[data-v31-search-results]')?.textContent||'',musicRecording:document.body.textContent.includes('MusicRecording')}})()`);
  assert.equal(result.overflow,0,JSON.stringify({route,width,result}));
  assert.equal(result.autoplay,0,route);assert.equal(result.player,true,route);assert.equal(result.playerOverlap,false,route);
  if(route===''||route==='artists/enomoto-mia/')assert.equal(result.scheduleItems,4,route);
  if(route.startsWith('search/?q='))assert.ok(result.searchText.trim()&&!result.searchText.includes('該当する公式コンテンツはありません'),route);
  results.push({route,width,...result});
  if(width===390&&['','artists/enomoto-mia/','news/enomoto-mia-september-21-double-release/'].includes(route)){
    if(result.scheduleItems){await evaluate("(()=>{const element=document.querySelector('.mia-release-schedule');window.scrollTo({top:element.offsetTop-80,behavior:'instant'});})()");await new Promise(resolve=>setTimeout(resolve,300));}
    const screenshot=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(`/private/tmp/suzuka-mia-schedule-qa/${route.replaceAll('/','-')||'home'}-${width}.png`,Buffer.from(screenshot.data,'base64'));
  }
}
const statuses=async instant=>{
  const {identifier}=await send('Page.addScriptToEvaluateOnNewDocument',{source:`{const RealDate=Date;window.Date=class extends RealDate{constructor(...args){super(...(args.length?args:[${JSON.stringify(instant)}]));}static now(){return new RealDate(${JSON.stringify(instant)}).getTime();}};}`});
  await send('Page.navigate',{url:base});await new Promise(resolve=>setTimeout(resolve,400));
  const value=await evaluate("[...document.querySelectorAll('[data-activity-status]')].map(node=>node.textContent)");
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier});return value;
};
assert.deepEqual(await statuses('2026-09-12T00:00:00+09:00'),['NOW STREAMING','KARAOKE / JOYSOUND · COMING 09.18','NEW RELEASE · COMING 09.21','NEW RELEASE · COMING 09.21']);
assert.deepEqual(await statuses('2026-09-21T00:00:00+09:00'),['NOW STREAMING','KARAOKE / JOYSOUND','NOW STREAMING','NOW STREAMING']);
assert.deepEqual(errors,[]);ws.close();
fs.writeFileSync('/private/tmp/suzuka-mia-schedule-qa/results.json',JSON.stringify({base,views:results.length,results,errors,dateBoundary:'passed'},null,2));
console.log(`MIA schedule browser QA passed: ${results.length} views, 390/768/1280, date boundary, no overflow/image/JS/autoplay/player overlap errors.`);

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
const routes=['artists/koga-kamishiro/','releases/mahou-ga-toketemo/','releases/hyakumankoku/','search/?q=神代煌牙','search/?q=魔法が解けても','search/?q=榎本魅愛','search/?q=Streaming%20Release','search/?q=Over%20Drive','search/?q=September%20Blue','','artists/enomoto-mia/','news/enomoto-mia-september-21-double-release/','releases/hello-hello-halloween/','schedule/','search/?q=Hello%20Hello%20Halloween','search/?q=百万告','search/?q=JOYSOUND','search/?q=カラオケ'];
const results=[];fs.mkdirSync('/private/tmp/suzuka-postpublication-qa',{recursive:true});
for(const width of [390,768,1280])for(const route of routes){
  await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});
  await send('Page.navigate',{url:new URL(route,base).href});
  const expectedUrl = new URL(route,base).href;
  for(let tick=0;tick<200;tick++) {
    if(await evaluate(`location.pathname===${JSON.stringify(new URL(expectedUrl).pathname)}&&new URL(location.href).searchParams.get('q')===${JSON.stringify(new URL(expectedUrl).searchParams.get('q'))}&&document.readyState==='complete'`)) break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  // Both search renderers fetch asynchronously; await their results before images.
  if(route.startsWith('search/?q=')) {
    for(let tick=0;tick<200;tick++) {
      if(await evaluate("!!document.querySelector('[data-v31-search-results]')?.textContent.trim() && document.querySelector('[name=artist]')?.options.length>1")) break;
      await new Promise(resolve=>setTimeout(resolve,100));
    }
  }
  let stableImages=0, previousImages='';
  for(let tick=0;tick<200 && stableImages<3;tick++) {
    const state=await evaluate("(()=>{document.querySelectorAll('img[loading=lazy]').forEach(image=>image.loading='eager');return {sources:[...document.images].map(image=>image.src).join('|'),loaded:[...document.images].every(image=>image.complete)};})()");
    stableImages=state.loaded&&state.sources===previousImages?stableImages+1:0;
    previousImages=state.sources;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const result=await evaluate(`(()=>{const player=document.querySelector('.suzuka-music-player');const panel=document.querySelector('.mia-release-schedule');const playerRect=player?.getBoundingClientRect();const panelRect=panel?.getBoundingClientRect();const hit=(a,b)=>!!a&&!!b&&a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;return {overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,brokenImages:[...document.images].filter(image=>!image.complete||image.naturalWidth===0).map(image=>image.src),autoplay:document.querySelectorAll('[autoplay],iframe[src*="autoplay=1"]').length,player:!!player,playerOverlap:hit(playerRect,panelRect),scheduleItems:panel?.querySelectorAll('.mia-schedule-item').length||0,searchText:document.querySelector('[data-v31-search-results]')?.textContent||'',musicRecording:document.body.textContent.includes('MusicRecording')}})()`);
  assert.equal(result.overflow,0,JSON.stringify({route,width,result}));
  assert.deepEqual(result.brokenImages,[],route);
  assert.equal(result.autoplay,0,route);assert.equal(result.player,true,route);assert.equal(result.playerOverlap,false,route);
  if(route===''||route==='artists/enomoto-mia/')assert.equal(result.scheduleItems,6,route);
  if(route.startsWith('search/?q=')) {
    const query=new URL(route,base).searchParams.get('q');
    const expected={'神代煌牙':'artists/koga-kamishiro/','魔法が解けても':'releases/mahou-ga-toketemo/','榎本魅愛':'artists/enomoto-mia/','百万告':'releases/hyakumankoku/','Streaming Release':'releases/hyakumankoku/','Over Drive':'releases/over-drive/','September Blue':'releases/september-blue/','Hello Hello Halloween':'releases/hello-hello-halloween/','JOYSOUND':'releases/hanakotoba/','カラオケ':'releases/hanakotoba/'}[query];
    assert.ok(await evaluate(`[...document.querySelectorAll('[data-v31-search-results] a')].some(a=>new URL(a.href).pathname===${JSON.stringify('/'+expected)})`),JSON.stringify({route,width,searchText:result.searchText}));
  }
  await evaluate("window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})");
  await new Promise(resolve=>setTimeout(resolve,150));
  const bottom=await evaluate(`(()=>{const player=document.querySelector('.suzuka-music-player')?.getBoundingClientRect();const links=[...document.querySelectorAll('footer a,.site-footer a')].filter(n=>n.getBoundingClientRect().height);const last=links.at(-1)?.getBoundingClientRect();return {playerTop:player?.top,lastBottom:last?.bottom,overlap:!!player&&!!last&&last.bottom>player.top&&last.top<player.bottom};})()`);
  assert.equal(bottom.overlap,false,JSON.stringify({route,width,bottom}));
  await evaluate("window.scrollTo({top:0,behavior:'instant'})");
  results.push({route,width,...result,bottom});
  if(width===390&&['','artists/enomoto-mia/','artists/koga-kamishiro/','schedule/','releases/mahou-ga-toketemo/','releases/hyakumankoku/'].includes(route)){
    if(result.scheduleItems){await evaluate("(()=>{const element=document.querySelector('.mia-release-schedule');window.scrollTo({top:element.offsetTop-80,behavior:'instant'});})()");await new Promise(resolve=>setTimeout(resolve,300));}
    const screenshot=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(`/private/tmp/suzuka-postpublication-qa/${route.replaceAll('/','-')||'home'}-${width}.png`,Buffer.from(screenshot.data,'base64'));
  }
}
const statuses=async instant=>{
  const {identifier}=await send('Page.addScriptToEvaluateOnNewDocument',{source:`{const RealDate=Date;window.Date=class extends RealDate{constructor(...args){super(...(args.length?args:[${JSON.stringify(instant)}]));}static now(){return new RealDate(${JSON.stringify(instant)}).getTime();}};}`});
  await send('Page.navigate',{url:base});await new Promise(resolve=>setTimeout(resolve,400));
  const value=await evaluate("[...document.querySelectorAll('[data-activity-status]')].map(node=>node.textContent)");
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier});return value;
};
assert.deepEqual(await statuses('2026-09-12T00:00:00+09:00'),['NOW STREAMING','KARAOKE / JOYSOUND · COMING 09.18','STREAMING RELEASE · COMING 09.21','NEW RELEASE · COMING 09.21','NEW RELEASE · COMING 09.22','NEW RELEASE · COMING 09.22']);
assert.deepEqual(await statuses('2026-09-21T00:00:00+09:00'),['NOW STREAMING','KARAOKE / JOYSOUND','STREAMING RELEASE · 配信状況はLinkCoreへ','NOW STREAMING','NEW RELEASE · COMING 09.22','NEW RELEASE · COMING 09.22']);
for(const timezoneId of ['Asia/Tokyo','America/Los_Angeles','UTC']) {
  await send('Emulation.setTimezoneOverride',{timezoneId});
  for(const instant of ['2026-09-14T00:00:00+09:00','2026-09-21T00:00:00+09:00']) {
    const {identifier}=await send('Page.addScriptToEvaluateOnNewDocument',{source:`{const RealDate=Date;window.Date=class extends RealDate{constructor(...args){super(...(args.length?args:[${JSON.stringify(instant)}]));}static now(){return new RealDate(${JSON.stringify(instant)}).getTime();}};}`});
    await send('Page.navigate',{url:new URL('schedule/',base).href});
    await new Promise(resolve=>setTimeout(resolve,800));
    const group=instant.startsWith('2026-09-14')?'next-week':'this-week';
    const slugs=await evaluate(`[...document.querySelectorAll('#${group} [data-release-slug]')].map(n=>n.dataset.releaseSlug)`);
    assert.ok(slugs.includes('over-drive')&&slugs.includes('september-blue'),JSON.stringify({timezoneId,instant,slugs}));
    const helloGroup=instant.startsWith('2026-09-14')?'next-week':'today';
    assert.ok(await evaluate(`!!document.querySelector('#${helloGroup} [data-release-slug="hello-hello-halloween"]')`));
    await send('Page.removeScriptToEvaluateOnNewDocument',{identifier});
  }
}
assert.deepEqual(errors,[]);ws.close();
fs.writeFileSync('/private/tmp/suzuka-postpublication-qa/results.json',JSON.stringify({base,views:results.length,results,errors,dateBoundary:'passed'},null,2));
console.log(`Postpublication browser QA passed: ${results.length} views, 390/768/1280, date boundary, no overflow/image/JS/autoplay/player overlap errors.`);

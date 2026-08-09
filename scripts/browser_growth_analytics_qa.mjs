#!/usr/bin/env node
/* Exercise Discovery & Growth links and inspect real GA4 collect responses. */

const cdpPort = process.env.CDP_PORT || "9223";
const base = (process.argv[2] || "https://www.suzukaofficial.com/").replace(/\/?$/, "/");
const measurementId = "G-LS3PCRB60D";
const scenarios = [
  {name:"Header channel",route:"",selector:'header a[data-source-section="header_channel"]',event:"youtube_click",source:"header_channel"},
  {name:"Footer channel",route:"",selector:'footer a[data-source-section="footer_channel"]',event:"youtube_click",source:"footer_channel"},
  {name:"Home subscribe",route:"",selector:'a[data-source-section="home_subscribe"]',event:"youtube_subscribe_click",source:"home_subscribe"},
  {name:"Lyrics subscribe",route:"lyrics/hanakotoba/",selector:'[data-source-section="lyrics_subscribe"] a',event:"youtube_subscribe_click",source:"lyrics_subscribe",work:true},
  {name:"Release subscribe",route:"releases/hanakotoba/",selector:'[data-source-section="release_subscribe"] a',event:"youtube_subscribe_click",source:"release_subscribe",work:true},
  {name:"Playlist subscribe",route:"playlists/love/",selector:'[data-source-section="playlist_subscribe"] a',event:"youtube_subscribe_click",source:"playlist_subscribe"},
  {name:"Official MV",route:"releases/hanakotoba/",selector:'a[href*="youtube.com/watch"]',event:"official_mv_click"},
  {name:"Lyrics internal",route:"releases/hanakotoba/",selector:'a[href*="/lyrics/hanakotoba/"]',event:"lyrics_click"},
  {name:"Release internal",route:"lyrics/hanakotoba/",selector:'a[href*="/releases/hanakotoba/"]',event:"release_click"},
  {name:"Photobook internal",route:"",selector:'[data-photobook] a[href*="/photobooks/"]',event:"photobook_click"},
  {name:"Photobook note",route:"photobooks/enomoto-mia-wasurenaide-watashi-no-koto/",selector:'[data-photobook] a[data-note-link]',event:"note_click"},
];
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json`)).json();
const target = targets.find(item => item.type === "page");
if (!target) throw new Error("No Chrome page target found");
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
let id=0, requests=[];
const pending=new Map();
socket.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.id&&pending.has(message.id)){const p=pending.get(message.id);pending.delete(message.id);message.error?p.reject(new Error(message.error.message)):p.resolve(message.result);}
  if(message.method==="Network.requestWillBeSent"&&/google-analytics\.com\/g\/collect/.test(message.params.request.url)){
    const query=new URL(message.params.request.url).searchParams;
    const rows=(message.params.request.postData||"").split(/\r?\n/).filter(Boolean);
    for(const row of rows.length?rows:[""]){
      const body=new URLSearchParams(row);
      const value=key=>body.get(key)||query.get(key)||"";
      requests.push({requestId:message.params.requestId,measurementId:value("tid"),eventName:value("en"),source:value("ep.source_section"),destination:value("ep.destination_url"),current:value("ep.current_page"),contentType:value("ep.content_type"),artist:value("ep.artist"),slug:value("ep.slug")});
    }
  }
  if(message.method==="Network.responseReceived"){
    requests.filter(item=>item.requestId===message.params.requestId).forEach(item=>{item.httpStatus=message.params.response.status;});
  }
};
function send(method,params={}){const requestId=++id;socket.send(JSON.stringify({id:requestId,method,params}));return new Promise((resolve,reject)=>pending.set(requestId,{resolve,reject}));}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function evaluate(expression){const result=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.text||"Runtime evaluation failed");return result.result.value;}
async function waitFor(expression){for(let attempt=0;attempt<80;attempt+=1){if(await evaluate(`Boolean(${expression})`))return;await wait(250);}throw new Error(`Timed out: ${expression}`);}
await send("Runtime.enable");await send("Network.enable");await send("Network.setCacheDisabled",{cacheDisabled:true});await send("Page.enable");
const results=[];
for(const scenario of scenarios){
  requests=[];const page=new URL(scenario.route,base).href;await send("Page.navigate",{url:page});
  await waitFor(`document.readyState==="complete"&&typeof window.gtag==="function"`);await waitFor(`document.querySelector(${JSON.stringify(scenario.selector)})`);
  for(let attempt=0;attempt<80&&!requests.some(item=>item.eventName==="page_view");attempt+=1)await wait(250);
  requests=[];
  await evaluate(`(()=>{const a=document.querySelector(${JSON.stringify(scenario.selector)});a.addEventListener("click",event=>event.preventDefault(),{once:true});a.click();return a.href})()`);
  let observation;
  for(let attempt=0;attempt<80;attempt+=1){observation=requests.find(item=>item.eventName===scenario.event&&item.measurementId===measurementId);if(observation?.httpStatus)break;await wait(250);}
  const ok=observation?.httpStatus===204&&(!scenario.source||observation.source===scenario.source)&&observation?.destination&&observation?.current&&(!scenario.work||(observation.artist&&observation.slug));
  results.push({name:scenario.name,event:scenario.event,ok:Boolean(ok),observation});
}
socket.close();
const failures=results.filter(item=>!item.ok);
console.log(JSON.stringify({status:failures.length?"failed":"passed",measurementId,results},null,2));
if(failures.length)process.exit(1);

#!/usr/bin/env node
/* Confirm that production sends a GA4 page_view request for the configured ID. */

const cdpPort = process.env.CDP_PORT || "9223";
const targetUrl = process.argv[2] || "https://bellflower1209.github.io/suzuka-official-music/";
const measurementId = "G-LS3PCRB60D";
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json`)).json();
const target = targets.find(item => item.type === "page");
if (!target) throw new Error("No Chrome page target found");
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let id = 0;
const pending = new Map();
const requests = new Map();
const observations = [];
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const {resolve, reject} = pending.get(message.id); pending.delete(message.id);
    message.error ? reject(new Error(message.error.message)) : resolve(message.result);
  }
  if (message.method === "Network.requestWillBeSent") {
    const url = message.params.request.url;
    if (/google-analytics\.com\/g\/collect/.test(url)) {
      requests.set(message.params.requestId, url);
    }
  }
  if (message.method === "Network.responseReceived" && requests.has(message.params.requestId)) {
    const url = new URL(requests.get(message.params.requestId));
    observations.push({
      status: message.params.response.status,
      measurementId: url.searchParams.get("tid"),
      eventName: url.searchParams.get("en"),
      pageLocation: url.searchParams.get("dl"),
    });
  }
};
function send(method, params={}) {
  const requestId=++id; socket.send(JSON.stringify({id:requestId,method,params}));
  return new Promise((resolve,reject)=>pending.set(requestId,{resolve,reject}));
}
await send("Runtime.enable");
await send("Network.enable");
await send("Network.setCacheDisabled", {cacheDisabled:true});
await send("Page.enable");
await send("Page.navigate", {url:targetUrl});
for (let attempt=0;attempt<40&&!observations.some(item=>item.eventName==="page_view");attempt+=1) {
  await new Promise(resolve=>setTimeout(resolve,250));
}
socket.close();
const pageView=observations.find(item=>item.eventName==="page_view"&&item.measurementId===measurementId);
if (!pageView || pageView.status < 200 || pageView.status >= 300) {
  console.error(JSON.stringify({status:"failed",observations},null,2));
  process.exit(1);
}
console.log(JSON.stringify({status:"passed",pageView},null,2));

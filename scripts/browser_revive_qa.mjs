#!/usr/bin/env node
/* Responsive browser QA for the verified RE:VIVE lineup update. */

const cdpPort = process.env.CDP_PORT || "9223";
const base = (process.argv[2] || "http://127.0.0.1:8765/").replace(/\/?$/, "/");
const routes = ["artists/", "artists/revive/", "artists/hoshimiya-hanon/", "artists/hoshino-miu/", "artists/asteria/", "wiki/artists/"];
const sizes = [{width:390,height:844},{width:768,height:1024},{width:1280,height:900}];
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json`)).json();
const target = targets.find(item => item.type === "page");
if (!target) throw new Error("No Chrome page target found");
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let id = 0;
const pending = new Map();
const runtimeProblems = [];
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const job = pending.get(message.id); pending.delete(message.id);
    message.error ? job.reject(new Error(message.error.message)) : job.resolve(message.result);
  }
  if (message.method === "Runtime.exceptionThrown") runtimeProblems.push(message.params.exceptionDetails.text);
  if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") runtimeProblems.push("console.error");
  if (message.method === "Network.responseReceived" && message.params.response.status >= 400 && !message.params.response.url.endsWith("/favicon.ico")) {
    runtimeProblems.push(`HTTP ${message.params.response.status}: ${message.params.response.url}`);
  }
};
function send(method, params={}) {
  const requestId = ++id;
  socket.send(JSON.stringify({id: requestId, method, params}));
  return new Promise((resolve, reject) => pending.set(requestId, {resolve, reject}));
}
async function waitReady(url) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const result = await send("Runtime.evaluate", {expression: `location.href===${JSON.stringify(url)}&&document.readyState==="complete"`, returnByValue:true});
    if (result.result.value) return;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Page did not become ready: ${url}`);
}
await send("Runtime.enable"); await send("Network.enable"); await send("Page.enable");
const failures = [];
for (const size of sizes) {
  for (const route of routes) {
    const before = runtimeProblems.length;
    await send("Emulation.setDeviceMetricsOverride", {width:size.width,height:size.height,deviceScaleFactor:1,mobile:size.width===390});
    const url = new URL(route, base).href;
    await send("Page.navigate", {url});
    await waitReady(url);
    await new Promise(resolve => setTimeout(resolve, 300));
    const result = await send("Runtime.evaluate", {expression:`(() => {
      const player=document.querySelector('.suzuka-music-player');
      const images=[...document.images];
      const badImages=images.filter(image=>image.complete&&image.naturalWidth===0).map(image=>image.src);
      const memberImages=[...document.querySelectorAll('.v31-member-card img')];
      const memberNames=[...document.querySelectorAll('.v31-member-card h3')].map(node=>node.textContent.trim());
      return {
        overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
        h1:document.querySelectorAll('h1').length,
        badImages,
        memberImages:memberImages.length,
        memberNames,
        playerFixed:player?getComputedStyle(player).position==='fixed':false,
        trackCount:player?.querySelector('.suzuka-player-track-select')?.options.length||0,
        autoplay:[...document.querySelectorAll('audio,video')].some(media=>media.autoplay)||[...document.querySelectorAll('iframe')].some(frame=>frame.src.includes('autoplay=1')),
      };
    })()`, returnByValue:true});
    const value = result.result.value;
    const reviveMismatch = route === "artists/revive/" && (value.memberImages !== 5 || JSON.stringify(value.memberNames) !== JSON.stringify(["白石 陽向","天城 結衣","月城 蒼依","橘 紗良","星宮 羽音"]));
    if (value.overflow || value.h1 !== 1 || value.badImages.length || !value.playerFixed || value.trackCount !== 14 || value.autoplay || reviveMismatch || runtimeProblems.length > before) {
      failures.push({route,width:size.width,...value,errors:runtimeProblems.slice(before)});
    }
  }
}
socket.close();
console.log(JSON.stringify({status:failures.length?"failed":"passed",pages:routes.length,viewports:sizes.map(size=>size.width),checks:routes.length*sizes.length,failures},null,2));
if (failures.length) process.exit(1);

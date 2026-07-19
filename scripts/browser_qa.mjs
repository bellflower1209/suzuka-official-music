#!/usr/bin/env node
/* Browser-level responsive, console, network and fixed-player smoke test. */

import fs from "node:fs";

const cdpPort = process.env.CDP_PORT || "9223";
const base = (process.argv[2] || "http://127.0.0.1:8765/").replace(/\/?$/, "/");
const releaseCatalog = JSON.parse(fs.readFileSync(new URL("../assets/data/enomoto-mia-releases.json", import.meta.url), "utf8"));
const expectedTrackCount = releaseCatalog.releases.filter(item => item.status === "published").length;
const pages = [
  "", "artists/", "artists/enomoto-mia/", "artists/eclypse/", "artists/koga-kamishiro/",
  "releases/", "news/", "news/eclypse-joins-suzuka/", "news/shadow-code-announcement/",
  "releases/mia/", "releases/hyakumankoku/", "releases/muteki-jikan-ato-3byou/",
  "releases/toriatsukai-chui/", "releases/tokenai-mahou-wo-ai-to-yobu/",
  "releases/kimi-to-nara-last-boss-made/", "releases/ai-demo-wakaranai/",
  "releases/kimi-wa-hanabi/", "releases/sukitte-baretemo-ii/", "releases/mermaid-merman/",
  "releases/mirai-no-watashi-ga-miteru/", "releases/our-kingdom/",
  "releases/suki-ga-kyou-mo-fueteiku/", "releases/moshimo-ashita-hajimemashite-ni-natte-mo/", "about/",
  "releases/shadow-code/", "releases/my-queen-my-oath/",
  "news/hyakumankoku-release/", "news/toriatsukai-chui-release/",
  "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/",
  "social/",
];
const sizes = [{width:1280,height:900},{width:768,height:1024},{width:390,height:844}];
const screenshotDir = process.env.QA_SCREENSHOT_DIR;
if (screenshotDir) fs.mkdirSync(screenshotDir, {recursive:true});
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json`)).json();
const target = targets.find(item => item.type === "page");
if (!target) throw new Error("No Chrome page target found");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let id = 0;
const pending = new Map();
const problems = [];
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const {resolve, reject} = pending.get(message.id); pending.delete(message.id);
    message.error ? reject(new Error(message.error.message)) : resolve(message.result);
  }
  if (message.method === "Runtime.exceptionThrown") problems.push(`exception: ${message.params.exceptionDetails.text}`);
  if (message.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(message.params.type)) problems.push(`console.${message.params.type}: ${message.params.args.map(v => v.value || v.description || "").join(" ")}`);
  if (message.method === "Network.loadingFailed" && !message.params.canceled) problems.push(`network failed: ${message.params.errorText} ${message.params.requestId}`);
  if (message.method === "Network.responseReceived" && message.params.response.status >= 400) problems.push(`HTTP ${message.params.response.status}: ${message.params.response.url}`);
};
function send(method, params={}) {
  const requestId = ++id;
  socket.send(JSON.stringify({id: requestId, method, params}));
  return new Promise((resolve, reject) => pending.set(requestId, {resolve, reject}));
}
await send("Runtime.enable"); await send("Network.enable"); await send("Page.enable");
const results = [];
for (const size of sizes) {
  for (const route of pages) {
    if (size.width !== 390 && !["", "artists/enomoto-mia/", "releases/", "news/", "social/", "releases/mia/", "releases/shadow-code/", "releases/my-queen-my-oath/", "news/hyakumankoku-release/", "news/toriatsukai-chui-release/", "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/"].includes(route)) continue;
    const before = problems.length;
    await send("Emulation.setDeviceMetricsOverride", {width:size.width,height:size.height,deviceScaleFactor:1,mobile:size.width===390});
    await send("Page.navigate", {url:new URL(route, base).href});
    await new Promise(resolve => setTimeout(resolve, 700));
    const evaluated = await send("Runtime.evaluate", {expression:`(() => { const p=document.querySelector('.suzuka-music-player'); const s=p?getComputedStyle(p):null; const select=p?.querySelector('.suzuka-player-track-select'); const socialHubLinks=[...document.querySelectorAll('a')].filter(a=>a.href.endsWith('/social/')).length; const needsContext=(${JSON.stringify(route)}.startsWith('releases/')&&${JSON.stringify(route)}!=='releases/')||(${JSON.stringify(route)}.startsWith('news/')&&${JSON.stringify(route)}!=='news/'); return {title:document.title, overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1, scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, player:!!p, playerPosition:s&&s.position, trackCount:select?.options.length||0, iframeCount:p?.querySelectorAll('iframe').length||0, pageLink:!!p?.querySelector('.suzuka-player-page')?.href, h1:document.querySelectorAll('h1').length, socialHubLinks, socialContext:!!document.querySelector('.social-context-section'), needsContext}; })()`, returnByValue:true});
    const value = evaluated.result.value;
    if (screenshotDir && ["releases/", "social/", "releases/shadow-code/", "releases/my-queen-my-oath/", "news/", "news/hyakumankoku-release/", "news/toriatsukai-chui-release/", "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/"].includes(route) && [1280, 390].includes(size.width)) {
      const shot = await send("Page.captureScreenshot", {format:"png", captureBeyondViewport:false});
      const name = route === "releases/" ? "releases" : route === "news/" ? "news" : route.split("/").filter(Boolean).at(-1);
      fs.writeFileSync(`${screenshotDir}/${name}-${size.width}.png`, Buffer.from(shot.data, "base64"));
    }
    if (value.overflow || !value.player || value.playerPosition !== "fixed" || value.trackCount !== expectedTrackCount || value.iframeCount !== 0 || !value.pageLink || value.h1 !== 1 || value.socialHubLinks < 1 || (value.needsContext && !value.socialContext) || problems.length > before) {
      results.push({route:route||"/", width:size.width, ...value, errors:problems.slice(before)});
    }
  }
}

await send("Emulation.setDeviceMetricsOverride", {width:390,height:844,deviceScaleFactor:1,mobile:true});
await send("Page.navigate", {url:new URL("releases/", base).href});
await new Promise(resolve => setTimeout(resolve, 700));
const selection = await send("Runtime.evaluate", {expression:`(() => { const select=document.querySelector('.suzuka-player-track-select'); select.value='1'; select.dispatchEvent(new Event('change',{bubbles:true})); return document.querySelector('.suzuka-player-details strong').textContent; })()`, returnByValue:true});
await send("Page.navigate", {url:new URL("news/", base).href});
await new Promise(resolve => setTimeout(resolve, 700));
const persisted = await send("Runtime.evaluate", {expression:`(() => { const player=document.querySelector('.suzuka-music-player'); player.classList.add('is-expanded'); const title=player.querySelector('.suzuka-player-details strong').textContent; return {title, selected:player.querySelector('.suzuka-player-track-select').value, overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1, autoplayIframe:player.querySelectorAll('iframe').length}; })()`, returnByValue:true});
if (persisted.result.value.title !== selection.result.value || persisted.result.value.selected !== "1" || persisted.result.value.overflow || persisted.result.value.autoplayIframe !== 0) {
  results.push({route:"news/", width:390, persistenceTest:persisted.result.value, expectedTitle:selection.result.value});
}

await send("Page.navigate", {url:new URL("releases/mia/", base).href});
await new Promise(resolve => setTimeout(resolve, 800));
const shareFallback = await send("Runtime.evaluate", {expression:`(async()=>{ const copy=[...document.querySelectorAll('.social-share-button')].find(button=>button.textContent.includes('URLをコピー')); copy?.click(); await new Promise(resolve=>setTimeout(resolve,150)); const copyStatus=document.querySelector('.social-copy-status')?.textContent||''; const share=[...document.querySelectorAll('.social-share-button')].find(button=>button.textContent.trim()==='共有'); share?.click(); await new Promise(resolve=>setTimeout(resolve,150)); return {copyStatus, shareStatus:document.querySelector('.social-copy-status')?.textContent||'', buttons:document.querySelectorAll('.social-share-button').length};})()`, awaitPromise:true, returnByValue:true});
if (shareFallback.result.value.buttons < 4 || !shareFallback.result.value.copyStatus || !shareFallback.result.value.shareStatus) {
  results.push({route:"releases/mia/", width:390, shareFallback:shareFallback.result.value});
}
socket.close();
if (results.length) {
  console.error(JSON.stringify(results, null, 2));
  process.exit(1);
}
console.log(`Browser QA passed: ${pages.length} pages at 390px and key templates at 768px/1280px; no overflow, console/network errors, or player regressions.`);

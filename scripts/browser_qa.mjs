#!/usr/bin/env node
/* Browser-level responsive, console, network and fixed-player smoke test. */

import fs from "node:fs";

const cdpPort = process.env.CDP_PORT || "9223";
const base = (process.argv[2] || "http://127.0.0.1:8765/").replace(/\/?$/, "/");
const pages = [
  "", "artists/", "artists/enomoto-mia/", "artists/eclypse/", "artists/koga-kamishiro/",
  "releases/", "news/", "news/eclypse-joins-suzuka/", "news/shadow-code-announcement/",
  "releases/mia/", "releases/hyakumankoku/", "releases/muteki-jikan-ato-3byou/",
  "releases/toriatsukai-chui/", "releases/tokenai-mahou-wo-ai-to-yobu/",
  "releases/kimi-to-nara-last-boss-made/", "releases/ai-demo-wakaranai/",
  "releases/kimi-wa-hanabi/", "releases/sukitte-baretemo-ii/", "releases/mermaid-merman/",
  "releases/mirai-no-watashi-ga-miteru/", "releases/our-kingdom/",
  "releases/suki-ga-kyou-mo-fueteiku/", "releases/moshimo-ashita-hajimemashite-ni-natte-mo/", "about/",
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
    if (size.width !== 390 && !["", "artists/enomoto-mia/", "releases/", "news/", "releases/mia/"].includes(route)) continue;
    const before = problems.length;
    await send("Emulation.setDeviceMetricsOverride", {width:size.width,height:size.height,deviceScaleFactor:1,mobile:size.width===390});
    await send("Page.navigate", {url:new URL(route, base).href});
    await new Promise(resolve => setTimeout(resolve, 700));
    const evaluated = await send("Runtime.evaluate", {expression:`(() => { const p=document.querySelector('.suzuka-music-player'); const s=p?getComputedStyle(p):null; return {title:document.title, overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1, scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, player:!!p, playerPosition:s&&s.position, h1:document.querySelectorAll('h1').length}; })()`, returnByValue:true});
    const value = evaluated.result.value;
    if (screenshotDir && route === "releases/" && [1280, 390].includes(size.width)) {
      const shot = await send("Page.captureScreenshot", {format:"png", captureBeyondViewport:false});
      fs.writeFileSync(`${screenshotDir}/releases-${size.width}.png`, Buffer.from(shot.data, "base64"));
    }
    if (value.overflow || !value.player || value.playerPosition !== "fixed" || value.h1 !== 1 || problems.length > before) {
      results.push({route:route||"/", width:size.width, ...value, errors:problems.slice(before)});
    }
  }
}
socket.close();
if (results.length) {
  console.error(JSON.stringify(results, null, 2));
  process.exit(1);
}
console.log(`Browser QA passed: ${pages.length} pages at 390px and key templates at 768px/1280px; no overflow, console/network errors, or player regressions.`);

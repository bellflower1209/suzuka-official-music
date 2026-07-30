#!/usr/bin/env node
/* Browser-level responsive, console, network and fixed-player smoke test. */

import fs from "node:fs";

const cdpPort = process.env.CDP_PORT || "9223";
const base = (process.argv[2] || "http://127.0.0.1:8765/").replace(/\/?$/, "/");
const releaseCatalog = JSON.parse(fs.readFileSync(new URL("../assets/data/enomoto-mia-releases.json", import.meta.url), "utf8"));
const explorerCatalog = JSON.parse(fs.readFileSync(new URL("../assets/data/releases-catalog.json", import.meta.url), "utf8"));
const expectedTrackCount = releaseCatalog.releases.filter(item => item.status === "published" && item.playerEnabled !== false).length;
const explorerPages = [
  "rankings/", "features/", "features/love-songs/", "features/cheer-songs/", "features/tearjerkers/",
  "features/summer-songs/", "features/dark/", "features/k-pop/", "features/enka/", "features/visual-kei/",
  "features/ai-idols/", "features/ai-bands/", "gallery/",
  ...explorerCatalog.releases.map(item => `gallery/${item.slug}/`),
  "universe/", "wiki/", "wiki/artists/", "wiki/works/", "wiki/terms/", "wiki/genres/",
  "wiki/timeline/", "wiki/ai-artists/",
  "playlists/", "playlists/love/", "playlists/summer/", "playlists/winter/", "playlists/cheer/",
  "playlists/tearjerkers/", "playlists/ai-idols/", "playlists/k-pop/", "playlists/visual-kei/",
  "playlists/enka/", "playlists/popular/", "playlists/latest/", "playlists/music-videos/",
  "community/", "admin/", "admin/dashboard/",
  "en/", "en/artists/", "en/releases/", "en/search/", "en/genres/", "en/discography/", "en/universe/", "en/news/",
];
const pages = [
  "", "artists/", "artists/enomoto-mia/", "artists/eclypse/", "artists/koga-kamishiro/",
  "artists/rangili/", "artists/asagiri-shinobu/", "artists/revive/",
  "artists/nox/",
  "search/", "genres/", "genres/j-pop/", "genres/enka/", "genres/k-pop-inspired/", "genres/visual-kei/", "discography/",
  "releases/", "news/", "news/eclypse-joins-suzuka/", "news/shadow-code-announcement/",
  "releases/mia/", "releases/hyakumankoku/", "releases/muteki-jikan-ato-3byou/",
  "releases/toriatsukai-chui/", "releases/tokenai-mahou-wo-ai-to-yobu/",
  "releases/kimi-to-nara-last-boss-made/", "releases/ai-demo-wakaranai/",
  "releases/kimi-wa-hanabi/", "releases/sukitte-baretemo-ii/", "releases/mermaid-merman/",
  "releases/mirai-no-watashi-ga-miteru/", "releases/our-kingdom/",
  "releases/suki-ga-kyou-mo-fueteiku/", "releases/moshimo-ashita-hajimemashite-ni-natte-mo/", "about/",
  "releases/shadow-code/", "releases/my-queen-my-oath/",
  "releases/red-moon-rising/",
  "releases/smile-and-say-goodbye/", "releases/boukyaku-no-ikimono/",
  "releases/namaste-galaxy/", "releases/wasurenai-kokoro/",
  "news/hyakumankoku-release/", "news/toriatsukai-chui-release/",
  "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/",
  "news/red-moon-rising-release/",
  "news/my-queen-my-oath-release/", "news/upcoming-artists/",
  "news/namaste-galaxy-release/", "news/wasurenai-kokoro-release/",
  "news/smile-and-say-goodbye-release/", "news/echoes-of-you-release/",
  "news/heal-you-again-release/", "releases/echoes-of-you/", "releases/heal-you-again/",
  "news/ashita-wa-kitto-release/", "news/chimpanzee-no-rakuen-release/",
  "releases/ashita-wa-kitto/", "releases/chimpanzee-no-rakuen/",
  "news/koisuru-maharaja-release/", "releases/koisuru-maharaja/",
  "social/", ...explorerPages,
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
  if (message.method === "Network.responseReceived" && message.params.response.status >= 400 && !message.params.response.url.endsWith("/favicon.ico")) problems.push(`HTTP ${message.params.response.status}: ${message.params.response.url}`);
};
function send(method, params={}) {
  const requestId = ++id;
  socket.send(JSON.stringify({id: requestId, method, params}));
  return new Promise((resolve, reject) => pending.set(requestId, {resolve, reject}));
}
async function waitForPageReady(expectedUrl) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const ready = await send("Runtime.evaluate", {
      expression: `location.href === ${JSON.stringify(expectedUrl)} && document.readyState === 'complete' && !!document.querySelector('.suzuka-music-player')`,
      returnByValue: true,
    });
    if (ready.result.value) {
      await send("Runtime.evaluate", {expression: "window.scrollTo(0, 0)"});
      await new Promise(resolve => setTimeout(resolve, 500));
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Page did not become ready: ${expectedUrl}`);
}
await send("Runtime.enable"); await send("Network.enable"); await send("Network.clearBrowserCache"); await send("Page.enable");
const results = [];
for (const size of sizes) {
  for (const route of pages) {
    if (size.width !== 390 && !["", "artists/enomoto-mia/", "artists/eclypse/", "artists/koga-kamishiro/", "artists/revive/", "artists/nox/", "releases/", "news/", "social/", "rankings/", "features/", "features/love-songs/", "gallery/", "gallery/chimpanzee-no-rakuen/", "universe/", "wiki/", "wiki/artists/", "playlists/", "playlists/love/", "community/", "admin/", "admin/dashboard/", "en/", "en/search/", "releases/mia/", "releases/shadow-code/", "releases/red-moon-rising/", "releases/my-queen-my-oath/", "releases/smile-and-say-goodbye/", "releases/boukyaku-no-ikimono/", "releases/echoes-of-you/", "releases/heal-you-again/", "news/hyakumankoku-release/", "news/toriatsukai-chui-release/", "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/", "news/red-moon-rising-release/", "news/my-queen-my-oath-release/", "news/echoes-of-you-release/", "news/heal-you-again-release/"].includes(route)) continue;
    const before = problems.length;
    await send("Emulation.setDeviceMetricsOverride", {width:size.width,height:size.height,deviceScaleFactor:1,mobile:size.width===390});
    const targetUrl = new URL(route, base).href;
    await send("Page.navigate", {url:targetUrl});
    await waitForPageReady(targetUrl);
    const evaluated = await send("Runtime.evaluate", {expression:`(() => { const p=document.querySelector('.suzuka-music-player'); const s=p?getComputedStyle(p):null; const select=p?.querySelector('.suzuka-player-track-select'); const socialHubLinks=[...document.querySelectorAll('a')].filter(a=>a.href.endsWith('/social/')).length; const creatorStandalone=${JSON.stringify(route)}.startsWith('en/'); const needsContext=(${JSON.stringify(route)}.startsWith('releases/')&&${JSON.stringify(route)}!=='releases/')||(${JSON.stringify(route)}.startsWith('news/')&&${JSON.stringify(route)}!=='news/'&&${JSON.stringify(route)}!=='news/upcoming-artists/'); return {title:document.title, overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1, scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, player:!!p, playerPosition:s&&s.position, trackCount:select?.options.length||0, iframeCount:p?.querySelectorAll('iframe').length||0, pageLink:!!p?.querySelector('.suzuka-player-page')?.href, h1:document.querySelectorAll('h1').length, socialHubLinks, creatorStandalone, socialContext:!!document.querySelector('.social-context-section'), needsContext}; })()`, returnByValue:true});
    const value = evaluated.result.value;
    if (screenshotDir && ["", "about/", "artists/", "artists/enomoto-mia/", "artists/nox/", "releases/", "social/", "rankings/", "features/", "gallery/", "gallery/chimpanzee-no-rakuen/", "universe/", "wiki/", "releases/namaste-galaxy/", "releases/shadow-code/", "releases/red-moon-rising/", "releases/my-queen-my-oath/", "releases/smile-and-say-goodbye/", "releases/boukyaku-no-ikimono/", "releases/echoes-of-you/", "releases/heal-you-again/", "news/", "news/namaste-galaxy-release/", "news/hyakumankoku-release/", "news/toriatsukai-chui-release/", "news/moshimo-ashita-hajimemashite-ni-natte-mo-release/", "news/red-moon-rising-release/", "news/my-queen-my-oath-release/", "news/echoes-of-you-release/", "news/heal-you-again-release/"].includes(route) && [1280, 390].includes(size.width)) {
      const shot = await send("Page.captureScreenshot", {format:"png", captureBeyondViewport:false});
      const name = route === "" ? "home" : route === "releases/" ? "releases" : route === "news/" ? "news" : route.split("/").filter(Boolean).at(-1);
      fs.writeFileSync(`${screenshotDir}/${name}-${size.width}.png`, Buffer.from(shot.data, "base64"));
    }
    if (value.overflow || !value.player || value.playerPosition !== "fixed" || value.trackCount !== expectedTrackCount || value.iframeCount !== 0 || !value.pageLink || value.h1 !== 1 || (!value.creatorStandalone && value.socialHubLinks < 1) || (value.needsContext && !value.socialContext) || problems.length > before) {
      results.push({route:route||"/", width:size.width, ...value, errors:problems.slice(before)});
    }
  }
}

await send("Emulation.setDeviceMetricsOverride", {width:390,height:844,deviceScaleFactor:1,mobile:true});
const releasesUrl = new URL("releases/", base).href;
await send("Page.navigate", {url:releasesUrl});
await waitForPageReady(releasesUrl);
const selection = await send("Runtime.evaluate", {expression:`(() => { const select=document.querySelector('.suzuka-player-track-select'); select.value='1'; select.dispatchEvent(new Event('change',{bubbles:true})); return document.querySelector('.suzuka-player-details strong').textContent; })()`, returnByValue:true});
const newsUrl = new URL("news/", base).href;
await send("Page.navigate", {url:newsUrl});
await waitForPageReady(newsUrl);
const persisted = await send("Runtime.evaluate", {expression:`(() => { const player=document.querySelector('.suzuka-music-player'); player.classList.add('is-expanded'); const title=player.querySelector('.suzuka-player-details strong').textContent; return {title, selected:player.querySelector('.suzuka-player-track-select').value, overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1, autoplayIframe:player.querySelectorAll('iframe').length}; })()`, returnByValue:true});
if (persisted.result.value.title !== selection.result.value || persisted.result.value.selected !== "1" || persisted.result.value.overflow || persisted.result.value.autoplayIframe !== 0) {
  results.push({route:"news/", width:390, persistenceTest:persisted.result.value, expectedTitle:selection.result.value});
}

const miaUrl = new URL("releases/mia/", base).href;
await send("Page.navigate", {url:miaUrl});
await waitForPageReady(miaUrl);
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

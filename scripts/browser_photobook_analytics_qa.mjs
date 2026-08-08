#!/usr/bin/env node
/* Exercise production photobook links and inspect the real GA4 collect requests. */

const cdpPort = process.env.CDP_PORT || "9223";
const measurementId = "G-LS3PCRB60D";
const scenarios = [
  {name: "Top → Photobook", page: "https://www.suzukaofficial.com/", selector: '[data-photobook] a[href*="/photobooks/"]', event: "photobook_click"},
  {name: "Photobook detail → note", page: "https://www.suzukaofficial.com/photobooks/enomoto-mia-wasurenaide-watashi-no-koto/", selector: "[data-photobook] a[data-note-link]", event: "note_click"},
  {name: "Artist → Photobook", page: "https://www.suzukaofficial.com/artists/enomoto-mia/", selector: '[data-photobook] a[href*="/photobooks/"]', event: "photobook_click"},
  {name: "Gallery → Photobook", page: "https://www.suzukaofficial.com/gallery/hanakotoba/", selector: '.v31-photobook-crosslink a[href*="/photobooks/"]', event: "photobook_click"},
  {name: "News → Photobook", page: "https://www.suzukaofficial.com/news/hanakotoba-release/", selector: '.v31-photobook-crosslink a[href*="/photobooks/"]', event: "photobook_click"},
];
const requiredParameters = ["photobook_title", "artist", "source_section", "destination_url", "current_page"];
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json`)).json();
const target = targets.find(item => item.type === "page");
if (!target) throw new Error("No Chrome page target found");
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let id = 0;
const pending = new Map();
let requests = [];
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const promise = pending.get(message.id); pending.delete(message.id);
    message.error ? promise.reject(new Error(message.error.message)) : promise.resolve(message.result);
  }
  if (message.method === "Network.requestWillBeSent") {
    const request = message.params.request;
    if (/google-analytics\.com\/g\/collect/.test(request.url)) {
      const query = new URL(request.url).searchParams;
      const body = new URLSearchParams(request.postData || "");
      const value = key => query.get(key) || body.get(key) || "";
      requests.push({
        requestId: message.params.requestId,
        measurementId: value("tid"), eventName: value("en"),
        parameters: Object.fromEntries(requiredParameters.map(key => [key, value(`ep.${key}`)])),
        requestUrl: request.url,
      });
    }
  }
  if (message.method === "Network.responseReceived") {
    const match = requests.find(item => item.requestId === message.params.requestId);
    if (match) match.httpStatus = message.params.response.status;
  }
};
function send(method, params = {}) {
  const requestId = ++id;
  socket.send(JSON.stringify({id: requestId, method, params}));
  return new Promise((resolve, reject) => pending.set(requestId, {resolve, reject}));
}
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "Runtime evaluation failed");
  return result.result.value;
}
async function waitFor(expression, attempts = 60) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (await evaluate(`Boolean(${expression})`)) return;
    await wait(250);
  }
  throw new Error(`Timed out waiting for ${expression}`);
}

await send("Runtime.enable");
await send("Network.enable");
await send("Network.setCacheDisabled", {cacheDisabled: true});
await send("Page.enable");
const results = [];
for (const scenario of scenarios) {
  requests = [];
  await send("Page.navigate", {url: scenario.page});
  await waitFor(`document.readyState === "complete" && typeof window.gtag === "function"`);
  await waitFor(`document.querySelector(${JSON.stringify(scenario.selector)})`);
  for (let attempt = 0; attempt < 80 && !requests.some(item => item.eventName === "page_view"); attempt += 1) {
    await wait(250);
  }
  if (!requests.some(item => item.eventName === "page_view")) {
    throw new Error(`GA4 page_view was not ready before ${scenario.name}`);
  }
  await wait(500);
  requests = [];
  const clicked = await evaluate(`(() => {
    const anchor = document.querySelector(${JSON.stringify(scenario.selector)});
    const destination = new URL(anchor.href, location.href).href;
    anchor.addEventListener("click", event => event.preventDefault(), {once: true});
    anchor.click();
    return {destination, text: anchor.textContent.trim()};
  })()`);
  let observation;
  for (let attempt = 0; attempt < 80; attempt += 1) {
    observation = requests.find(item => item.eventName === scenario.event && item.measurementId === measurementId);
    if (observation?.httpStatus) break;
    await wait(250);
  }
  const missing = !observation ? requiredParameters : requiredParameters.filter(key => !observation.parameters[key]);
  const cleanUrls = observation && [observation.parameters.destination_url, observation.parameters.current_page]
    .every(value => value && !/[?#]/.test(value));
  results.push({scenario: scenario.name, clicked, observation, missingParameters: missing, cleanUrls});
}
socket.close();
const failures = results.filter(result =>
  !result.observation || result.observation.httpStatus < 200 || result.observation.httpStatus >= 300 ||
  result.missingParameters.length || !result.cleanUrls
);
console.log(JSON.stringify({status: failures.length ? "failed" : "passed", measurementId, results}, null, 2));
if (failures.length) process.exit(1);

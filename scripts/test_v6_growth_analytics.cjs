// Exercise the generated production listener, including legacy coexistence.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const input = process.argv[2];
if (!input) throw new Error('Pass the generated preview root');
const events = [], listeners = {};
const location = {origin:'https://www.suzukaofficial.com',pathname:'/music-production/',href:'https://www.suzukaofficial.com/music-production/'};
const document = {body:{},querySelectorAll:()=>[],querySelector:()=>null,
  addEventListener:(name,fn)=>{(listeners[name] ||= []).push(fn);}};
const window = {location,gtag:(...args)=>events.push(args)};
const source = fs.readFileSync(path.join(input,'assets/analytics.js'),'utf8');
const context = vm.createContext({document,window,location,URL,console});
vm.runInContext(source,context); vm.runInContext(source,context);
assert.equal(listeners.click.length,1,'loading the script twice must not double count');
const click = (action, extra={}) => {
  const anchor={dataset:{growthAction:action,releaseSlug:'test-song',artistSlug:'enomoto-mia',service:'linkcore',productId:'enomoto-mia-line-stickers',...extra},
    href:'mailto:private@example.invalid?body=DO_NOT_SEND_THIS',
    closest:()=>({dataset:{sourceSection:'growth_music'}})};
  const start=events.length;listeners.click[0]({target:{closest:()=>anchor}});
  assert.equal(events.length-start,1,'one growth interaction must produce exactly one event');
  const output=events.at(-1);assert(!JSON.stringify(output).includes('private@example'));assert(!JSON.stringify(output).includes('DO_NOT_SEND_THIS'));
  return output;
};
assert.equal(click('streaming')[1],'streaming_click');
assert.equal(click('sticker')[1],'line_sticker_click');
assert.equal(click('production-contact')[2].interaction,'consultation');
assert.equal(click('production-visit')[2].interaction,'visit');
assert.equal(click('streaming',{releaseSlug:'bad/value?token=secret'})[2].release_slug,'');
assert(events.every(x=>x[1]!=='outbound_click'),'growth events must bypass legacy outbound counting');
window.gtag=undefined;
listeners.click[0]({target:{closest:()=>({dataset:{growthAction:'streaming'},closest:()=>null})}});
console.log('PASS: listener deduplication, 3 event categories, visit/contact separation, privacy allowlist, blocked GA4 fallback.');

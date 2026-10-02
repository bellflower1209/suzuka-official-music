import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const code=fs.readFileSync(new URL('../assets/streaming-release.js',import.meta.url),'utf8');
for(const [instant, expected] of [
 ['2026-09-09T14:59:59Z','COMING SOON'],
 ['2026-09-09T15:00:00Z','明日リリース'],
 ['2026-09-10T14:59:59Z','明日リリース'],
 ['2026-09-10T15:00:00Z','NOW STREAMING'],
 ['2026-09-11T15:00:00Z','NOW STREAMING'],
 ['2027-09-09T15:00:00Z','NOW STREAMING']]) {
 let now=instant, tick;
 const node={dataset:{streamingDate:'2026-09-11'},textContent:''};
 class Clock extends Date { constructor(...args){super(...(args.length?args:[now]));} }
 vm.runInNewContext(code,{Date:Clock,Intl,document:{querySelectorAll:()=>[node],addEventListener:()=>{}},setInterval:f=>{tick=f;}});
 assert.equal(node.textContent,expected,instant);
 now='2026-09-10T15:00:00Z';tick();assert.equal(node.textContent,'NOW STREAMING','open-tab rollover');
}
console.log('Tokyo date test passed: 6 boundary/future cases and open-tab rollover.');
for(const status of ['upcoming','draft']) {
 const node={dataset:{streamingDate:'2026-10-03',streamingState:status},textContent:''};
 class Clock extends Date {constructor(...args){super(...(args.length?args:['2026-10-03T01:00:00Z']));}}
 vm.runInNewContext(code,{Date:Clock,Intl,document:{querySelectorAll:()=>[node],addEventListener:()=>{}},setInterval:()=>{}});
 assert.equal(node.textContent,'配信状況確認中','Elapsed date does not verify '+status);
}
console.log('Unverified streaming states remain pending after their scheduled date.');

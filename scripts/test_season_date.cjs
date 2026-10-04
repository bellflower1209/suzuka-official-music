const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync(require('node:path').join(__dirname,'../assets/season-2026.js'),'utf8');
for(const [time,expected] of [['2026-09-30T14:59:59Z',false],['2026-09-30T15:00:00Z',true],['2026-10-31T14:59:59Z',true],['2026-10-31T15:00:00Z',false],['2027-10-03T00:00:00Z',false]]){
 let result;
 class ClockDate extends Date {constructor(){super(time)}}
 vm.runInNewContext(code,{Date:ClockDate,Intl,document:{querySelector:()=>null,documentElement:{style:{setProperty(){}},classList:{toggle:(key,value)=>result=value}}}});
 assert.equal(result,expected,time);
}
console.log('Season JST boundary tests passed: 5 cases.');

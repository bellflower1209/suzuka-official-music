const {chromium}=require(process.env.PLAYWRIGHT_PATH || 'playwright');
const fs=require('fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const output=process.env.QA_OUTPUT || path.join(root,'../ハロウィン更新監査_20261004');
fs.mkdirSync(output,{recursive:true});
const base=(process.argv[2] || 'http://127.0.0.1:8766/').replace(/\/?$/, '/');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const cms=JSON.parse(fs.readFileSync(root+'/assets/data/creator-cms.json'));
 const routes=['','artists/','news/','releases/renkinku/','gallery/hanakotoba/','search/',...cms.artists.map(x=>'artists/'+x.slug+'/')];
 const all=[];
 for(const width of [1280,768,390]){
  const context=await browser.newContext({viewport:{width,height:1000}});
  await context.route(/googletagmanager|google-analytics/,r=>r.fulfill({status:200,body:''}));
  const page=await context.newPage();
  for(const route of routes){
   const errors=[],http=[];const err=e=>errors.push(String(e));const resp=r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()})};
   const failed=r=>errors.push(r.url()+': '+r.failure()?.errorText);
   const consoleError=m=>{if(m.type()==='error')errors.push(m.text())};
   page.on('pageerror',err);page.on('response',resp);page.on('requestfailed',failed);page.on('console',consoleError);
   const response=await page.goto(base+route,{waitUntil:'load'});
   await page.locator('img').evaluateAll(imgs=>imgs.forEach(i=>i.loading='eager'));
   await page.waitForFunction(()=>[...document.querySelectorAll('link[rel=stylesheet]')].every(l=>l.sheet),{timeout:20000});
   await page.waitForTimeout(1000);
   await page.evaluate(()=>Promise.all([...document.images].map(i=>Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,20000))]))));
   const state=await page.evaluate(()=>({overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),broken:[...document.images].filter(i=>i.getAttribute('src')&&(!i.complete||!i.naturalWidth)).map(i=>i.src),audio:document.querySelectorAll('audio,iframe,.suzuka-music-player').length,season:document.documentElement.classList.contains('halloween-2026'),bannerTop:document.querySelector('.season-banner').getBoundingClientRect().top,headerBottom:document.querySelector('.site-header').getBoundingClientRect().bottom,pending:[...document.images].filter(i=>i.src.includes('official-image-pending')).length,michiru:[...document.images].filter(i=>i.src.includes('michiru-official-channel-note')).map(i=>i.naturalWidth),links:[...document.querySelectorAll('a[href]')].filter(a=>/youtube|linkco.re|music.apple.com/.test(a.href)).length}));
   const result={width,route,status:response.status(),...state,errors,http};all.push(result);console.log(JSON.stringify(result));
   if(['','artists/','artists/michiru/','artists/tetsuhige/'].includes(route))await page.screenshot({path:output+'/'+(route.replaceAll('/','-')||'home')+'-'+width+'.png',fullPage:route==='artists/tetsuhige/'});
   page.off('pageerror',err);page.off('response',resp);page.off('requestfailed',failed);page.off('console',consoleError);
  }
  await context.close();
 }
 fs.writeFileSync(output+'/browser.json',JSON.stringify(all,null,2));
 await browser.close();
 if(all.some(x=>x.status!==200||x.overflow||x.broken.length||x.audio||x.errors.length||x.http.length||!x.season||x.bannerTop<x.headerBottom-1))process.exitCode=1;
})();

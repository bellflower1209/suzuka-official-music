#!/usr/bin/env node
'use strict';
// Local static review only. No build, write, publication, or external binding.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const review = path.resolve(root, '../CELESTIAL_PORTAL_V5_QA');
const port = Number(process.argv[2] || 8825);
if (!Number.isInteger(port) || port < 1024 || port > 65535) {
  console.error('Choose a port between 1024 and 65535.');
  process.exit(1);
}
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8',
  '.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8',
  '.webmanifest':'application/manifest+json','.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.xml':'application/xml; charset=utf-8','.txt':'text/plain; charset=utf-8',
  '.md':'text/plain; charset=utf-8','.avif':'image/avif','.webp':'image/webp',
  '.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.svg':'image/svg+xml',
  '.mp4':'video/mp4','.webm':'video/webm','.ico':'image/x-icon','.wav':'audio/wav','.mp3':'audio/mpeg'};
const server = http.createServer(async (req,res) => {
  if (!['GET','HEAD'].includes(req.method)) {res.writeHead(405);res.end();return;}
  let requestPath;
  try {requestPath=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}
  catch {res.writeHead(400);res.end();return;}
  const isReview=requestPath.startsWith('/review/');
  const base=isReview?review:root;
  const relative=isReview?requestPath.slice(8):requestPath.slice(1);
  if (relative.split('/').some(p=>p.startsWith('.')) || relative.includes('\0')) {
    res.writeHead(403);res.end();return;
  }
  let file=path.resolve(base,relative);
  if (file!==base && !file.startsWith(base+path.sep)) {res.writeHead(403);res.end();return;}
  try {
    if ((await fs.promises.stat(file)).isDirectory()) file=path.join(file,'index.html');
    const type=mime[path.extname(file).toLowerCase()];
    const real=await fs.promises.realpath(file);
    if (!type || !real.startsWith(base+path.sep)) {res.writeHead(403);res.end();return;}
    const size=(await fs.promises.stat(real)).size;
    const headers={'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Accept-Ranges':'bytes'};
    let start=0,end=size-1,status=200;
    if (req.headers.range) {
      const match=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
      if (!match || (!match[1]&&!match[2])) {res.writeHead(416,{'Content-Range':`bytes */${size}`});res.end();return;}
      start=match[1]?Number(match[1]):Math.max(0,size-Number(match[2]));
      end=match[1]&&match[2]?Math.min(size-1,Number(match[2])):size-1;
      if (!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||start>=size||end<start) {res.writeHead(416,{'Content-Range':`bytes */${size}`});res.end();return;}
      status=206;headers['Content-Range']=`bytes ${start}-${end}/${size}`;
    }
    headers['Content-Length']=Math.max(0,end-start+1);
    res.writeHead(status,headers);
    if (req.method==='HEAD'||!size) {res.end();return;}
    const stream=fs.createReadStream(real,{start,end});
    stream.on('error',()=>res.destroy());res.on('close',()=>stream.destroy());stream.pipe(res);
  } catch {res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('Not found');}
});
server.on('error',error=>{console.error(error.message);process.exitCode=1;});
server.listen(port,'127.0.0.1',()=>{
  console.log(`Site: http://127.0.0.1:${port}/`);
  console.log(`Review: http://127.0.0.1:${port}/review/review.html`);
  console.log('Stop with Ctrl+C. Bound to this computer only.');
});

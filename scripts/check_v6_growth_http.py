"""Serve the candidate privately on an ephemeral loopback port and verify HTTP routes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


class Server(ThreadingHTTPServer):
    request_queue_size=64
    daemon_threads=True


def check(root):
    if not (root/'suzuka-v6-candidate-manifest.json').is_file():raise ValueError('Not a materialized candidate')
    server=Server(('127.0.0.1',0),partial(QuietHandler,directory=str(root)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_port)
    urls=[n.text for n in ET.parse(root/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    def get(url):
        local=base+url.removeprefix('https://www.suzukaofficial.com')
        try:
            with urllib.request.urlopen(local,timeout=15)as r:r.read();return r.status
        except urllib.error.HTTPError as error:return error.code
    try:
        with ThreadPoolExecutor(max_workers=4)as pool:statuses=list(pool.map(get,urls))
        missing={path:get('https://www.suzukaofficial.com'+path) for path in [
            '/does-not-exist-20261101/','/releases/last-ignition/','/scripts/build_v6_growth_preview.py','/v6/music/approved/private.mp3']}
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
    result={'status':'PASS' if all(s==200 for s in statuses) and all(s==404 for s in missing.values()) else 'FAIL',
        'publicUrls':len(urls),'http200':sum(s==200 for s in statuses),
        'failures':[{'url':url,'status':s}for url,s in zip(urls,statuses)if s!=200],
        'expected404':missing,'externalRequests':False}
    if result['status']!='PASS':raise ValueError(json.dumps(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--report',type=Path)
    args=p.parse_args();result=check(args.root.resolve())
    if args.report:args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

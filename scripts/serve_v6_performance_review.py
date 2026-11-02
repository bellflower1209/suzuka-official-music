"""Serve already-built review variants on loopback only, with identical gzip/cache headers.

Local HTTP/1.1 is a controlled comparison, not a replica of Pages HTTP/2 or PSI.
No source generation, Git operations, deployment, analytics injection or audio files.
"""
import argparse
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import threading
from urllib.parse import unquote, urlparse


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def serve(self, head=False):
        name = unquote(urlparse(self.path).path).lstrip('/')
        path = (self.server.root / name).resolve()
        if not path.is_relative_to(self.server.root):
            self.send_error(403)
            return
        if path.is_dir():
            path = path / 'index.html'
        status = 200
        if not path.is_file():
            path, status = self.server.root / '404.html', 404
        data = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        text = path.suffix in {'.html', '.css', '.js', '.json', '.xml', '.svg', '.txt'}
        compressed = text and 'gzip' in self.headers.get('Accept-Encoding', '')
        if compressed:
            data = gzip.compress(data, mtime=0)
        self.send_response(status)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if text else ''))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'max-age=600')
        self.send_header('Vary', 'Accept-Encoding')
        if compressed:
            self.send_header('Content-Encoding', 'gzip')
        self.end_headers()
        if not head:
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(head=True)

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    servers = []
    try:
        for port, variant in ((8880, 'baseline'), (8881, 'images'), (8882, 'combined')):
            directory = root / variant
            if not (directory / 'suzuka-v6-candidate-manifest.json').is_file():
                raise ValueError('Build the verified variants first: ' + variant)
            server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
            server.root = directory
            servers.append(server)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            print(f'http://127.0.0.1:{port}/ — {variant}', flush=True)
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()

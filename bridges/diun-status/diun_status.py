#!/usr/bin/env python3
"""diun-status — exposes Diun image update status as a JSON HTTP endpoint."""
import http.client
import json
import logging
import os
import socket
import struct
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

DIUN_CONTAINER = os.environ.get('DIUN_CONTAINER', 'diun')
DOCKER_SOCK    = '/var/run/docker.sock'
PORT           = int(os.environ.get('PORT', '8080'))


class _UnixHTTPConn(http.client.HTTPConnection):
    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(30)
        s.connect(DOCKER_SOCK)
        self.sock = s


def _docker(method, path, body=None):
    conn = _UnixHTTPConn('localhost')
    payload = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'} if payload else {}
    conn.request(method, path, body=payload, headers=headers)
    return conn.getresponse()


def _demux(data: bytes) -> str:
    """Strip Docker multiplexed-stream headers (8-byte frames), return stdout."""
    out, pos = [], 0
    while pos + 8 <= len(data):
        stream_type = data[pos]
        size = struct.unpack('>I', data[pos + 4:pos + 8])[0]
        pos += 8
        if stream_type == 1:  # stdout only
            out.append(data[pos:pos + size])
        pos += size
    return b''.join(out).decode('utf-8', errors='replace')


def get_diun_images():
    resp = _docker('POST', f'/containers/{DIUN_CONTAINER}/exec', {
        'AttachStdout': True, 'AttachStderr': False, 'Tty': False,
        'Cmd': ['diun', 'image', 'list'],
    })
    data = json.loads(resp.read())
    exec_id = data.get('Id')
    if not exec_id:
        raise RuntimeError(f'exec create failed: {data}')

    resp = _docker('POST', f'/exec/{exec_id}/start', {'Detach': False, 'Tty': False})
    output = _demux(resp.read())

    images = []
    for line in output.splitlines()[1:]:   # skip header row
        parts = line.split()
        if len(parts) < 4:
            continue
        name   = parts[0]
        status = parts[1].lower()
        digest = next((p for p in parts if p.startswith('sha256:')), '')
        images.append({
            'name':             name,
            'status':           status,
            'digest':           digest[7:19] if digest else '',  # 12-char short hash
            'update_available': status == 'update',
        })
    return images


def _html(images) -> bytes:
    from datetime import datetime, timezone
    rows = []
    for img in sorted(images, key=lambda i: (not i['update_available'], i['name'])):
        badge = (
            '<span style="color:#d73a49;font-weight:bold">⚠ update available</span>'
            if img['update_available'] else
            '<span style="color:#28a745">✓ up to date</span>'
        )
        rows.append(
            f'<tr><td>{img["name"]}</td><td>{img["status"]}</td>'
            f'<td>{badge}</td><td><code>{img["digest"]}</code></td></tr>'
        )
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    return f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Diun – Image Status</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #333; }}
  h1   {{ font-size: 1.4rem; margin-bottom: .25rem; }}
  p.ts {{ color: #888; font-size: .85rem; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #e1e4e8; }}
  th {{ background: #f6f8fa; font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; }}
  tr:hover {{ background: #f6f8fa; }}
  code {{ font-size: .85rem; color: #555; }}
</style>
</head>
<body>
<h1>🐳 Docker Image Status (Diun)</h1>
<p class="ts">Fetched {now}</p>
<table>
<thead><tr><th>Image</th><th>Status</th><th>Update</th><th>Running digest</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body></html>
'''.encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            images = get_diun_images()
            want_html = 'text/html' in self.headers.get('Accept', '')
            if want_html:
                body = _html(images)
                content_type = 'text/html; charset=utf-8'
            else:
                body = json.dumps(images, indent=2).encode()
                content_type = 'application/json'
            self.send_response(200)
        except Exception as e:
            log.exception('Failed to query diun')
            body = json.dumps({'error': str(e)}).encode()
            content_type = 'application/json'
            self.send_response(500)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)


if __name__ == '__main__':
    log.info('diun-status listening on :%d (container=%s)', PORT, DIUN_CONTAINER)
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()

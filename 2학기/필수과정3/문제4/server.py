from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from ipaddress import ip_address
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import os
from typing import Dict, Tuple, Optional


HOST = '0.0.0.0'
PORT = 8080
INDEX_FILE = 'index.html'
ENCODING = 'utf-8'
API_TIMEOUT = 3.0  # seconds


def classify_ip(ip: str) -> str:
    try:
        addr = ip_address(ip)
    except ValueError:
        return '알 수 없음'
    if addr.is_loopback:
        return '로컬호스트'
    if addr.is_private:
        return '사설망'
    return '공용망'


def geolocate_ip(ip: str) -> Optional[Dict[str, str]]:
    kind = classify_ip(ip)
    if kind != '공용망':
        return None
    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,org,as,timezone,query'
    req = Request(url, headers={'User-Agent': 'SpacePirateServer/1.0'})
    try:
        with urlopen(req, timeout=API_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
    except (HTTPError, URLError, TimeoutError):
        return None

    if data.get('status') != 'success':
        return None

    return {
        'ip': data.get('query', ip),
        'country': data.get('country', ''),
        'region': data.get('regionName', ''),
        'city': data.get('city', ''),
        'lat': str(data.get('lat', '')),
        'lon': str(data.get('lon', '')),
        'org': data.get('org', ''),
        'asn': data.get('as', ''),
        'tz': data.get('timezone', ''),
    }


class SpacePirateHandler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args: Tuple[object, ...]) -> None:
        return

    def do_HEAD(self) -> None:
        if self.path in ('/', '/index.html'):
            content = self._read_index()
            if content is None:
                self._send_headers(404, 0)
            else:
                self._send_headers(200, len(content))
        else:
            self._send_headers(404, 0)

    def do_GET(self) -> None:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]
        geo = geolocate_ip(client_ip)
        if geo:
            print(
                f'[접속 시간] {now} | [IP] {client_ip} (공용망) | '
                f"[위치] {geo.get('country','')}, {geo.get('region','')}, {geo.get('city','')} | "
                f"[좌표] {geo.get('lat','')},{geo.get('lon','')} | "
                f"[조직] {geo.get('org','')} | [ASN] {geo.get('asn','')} | [TZ] {geo.get('tz','')}"
            )
        else:
            print(f'[접속 시간] {now} | [IP] {client_ip} ({classify_ip(client_ip)})')

        # 3) 라우팅
        if self.path in ('/', '/index.html'):
            content = self._read_index()
            if content is None:
                self._send_headers(404, 0)
                self.wfile.write(b'')
                return
            self._send_headers(200, len(content))
            self.wfile.write(content)
        else:
            self._send_headers(404, 0)
            self.wfile.write(b'')

    def _send_headers(self, code: int, length: int) -> None:
        self.send_response(code)
        self.send_header('Content-Type', f'text/html; charset={ENCODING}')
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Connection', 'close')
        self.end_headers()

    def _read_index(self) -> Optional[bytes]:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, INDEX_FILE)
        try:
            with open(path, 'r', encoding=ENCODING) as f:
                html = f.read()
            return html.encode(ENCODING)
        except FileNotFoundError:
            print('index.html 파일을 찾을 수 없습니다.')
            return None


def run_server() -> None:
    server = HTTPServer((HOST, PORT), SpacePirateHandler)
    print(f'HTTP Server listening on http://localhost:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n서버가 종료되었습니다.')
    finally:
        server.server_close()


if __name__ == '__main__':
    run_server()

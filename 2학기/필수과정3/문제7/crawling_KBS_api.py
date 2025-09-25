import json
import re
import time
from html import unescape
from typing import List, Dict

import requests
from requests import Response

BASE = 'https://news.kbs.co.kr'
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Referer': BASE + '/',
    'Accept': 'application/json,text/html;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko,en;q=0.8',
    'Connection': 'close',
}
TIMEOUT = 10


def _get(url: str, params: Dict = None, json_expected: bool = False) -> Response:
    for _ in range(2):
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if r.ok:
            if json_expected:
                # KBS가 text/html로 JSON을 주는 경우가 있어 강제 파싱 대비
                _ = r.text  # touch for encoding
            return r
        time.sleep(0.4)
    r.raise_for_status()
    return r  # pragma: no cover


def _clean(s: str) -> str:
    s = unescape(s or '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def fetch_via_newest(limit: int = 20) -> List[str]:
    """GET /api/getNewestList"""
    url = BASE + '/api/getNewestList'
    params = {
        'pageNo': 1,
        'rowsPerPage': max(1, min(limit, 50)),
        'exceptPhotoYn': 'Y',  # 사진기사 제외
    }
    r = _get(url, params=params, json_expected=True)
    try:
        data = r.json()
    except json.JSONDecodeError:
        return []
    items = data.get('list') or data.get('data') or []
    out = []
    for it in items:
        t = it.get('title') or it.get('newsTitle') or ''
        t = _clean(t)
        if 5 <= len(t) <= 160:
            out.append(t)
    return out


def fetch_via_list(limit: int = 20) -> List[str]:
    """GET /api/getNewsList (종합뉴스 메뉴 코드: 0000000001)"""
    url = BASE + '/api/getNewsList'
    params = {
        'menuCode': '0000000001',
        'pageNo': 1,
        'rowsPerPage': max(1, min(limit, 50)),
        'exceptPhotoYn': 'Y',
        # 필요시 추가 파라미터 예:
        # 'sortCd': '1', 'broadCode': '0000', 'contentsCode': 'ALL'
    }
    r = _get(url, params=params, json_expected=True)
    try:
        data = r.json()
    except json.JSONDecodeError:
        return []
    items = data.get('list') or data.get('data') or []
    out = []
    for it in items:
        t = it.get('title') or it.get('newsTitle') or ''
        t = _clean(t)
        if 5 <= len(t) <= 160:
            out.append(t)
    return out


def fetch_from_home_backup(limit: int = 20) -> List[str]:
    """홈 HTML 백업 파싱: h1~h3 및 'headline' 힌트"""
    r = _get(BASE + '/', json_expected=False)
    html = r.text
    # JSON-LD headline
    out = []
    for m in re.finditer(r'<script[^>]+ld\+json[^>]*>(.*?)</script>', html, re.I | re.S):
        block = m.group(1)
        for mh in re.finditer(r'"headline"\s*:\s*"([^"]{5,160})"', block):
            out.append(_clean(mh.group(1)))
    # h1~h3 텍스트
    for tag in ('h1', 'h2', 'h3'):
        for mh in re.finditer(
            rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.I | re.S
        ):
            txt = _clean(re.sub(r'<[^>]+>', ' ', mh.group(1)))
            if 5 <= len(txt) <= 160:
                out.append(txt)
    # 필터 및 dedupe
    seen, dedup = set(), []
    for t in out:
        if re.search(r'(구독|광고|이벤트|로그인|회원가입|바로가기)', t):
            continue
        if t not in seen:
            seen.add(t)
            dedup.append(t)
        if len(dedup) >= limit:
            break
    return dedup


def fetch_kbs_headlines(limit: int = 20) -> List[str]:
    """1순위 최신 API → 2순위 리스트 API → 3순위 HTML"""
    headlines = fetch_via_newest(limit)
    if len(headlines) < 5:
        alt = fetch_via_list(limit)
        headlines = headlines + [t for t in alt if t not in headlines]
    if len(headlines) < 5:
        alt2 = fetch_from_home_backup(limit)
        headlines = headlines + [t for t in alt2 if t not in headlines]
    return headlines[:limit]


def fetch_weather_brief(limit: int = 5) -> List[str]:
    """보너스: KBS 노출 JSON 활용"""
    d = time.strftime('%Y%m%d%H%M%S')
    url = BASE + f'/expose/weatherAllRegion.json?d={d}'
    try:
        r = _get(url, json_expected=True)
        data = r.json()
    except Exception:
        return []
    brief = []
    # 서울, 부산, 대구 우선
    priority = {'108': '서울', '159': '부산', '143': '대구'}
    # stationId, weatherStatus, temperature
    for row in data:
        sid = row.get('stationId')
        name = priority.get(sid)
        if not name:
            continue
        text = f"{name} {row.get('weatherStatus','')} {row.get('temperature','')}℃"
        brief.append(_clean(text))
        if len(brief) >= limit:
            break
    if not brief:
        for row in data[:limit]:
            text = f"{row.get('stationName','')} {row.get('weatherStatus','')} {row.get('temperature','')}℃"
            brief.append(_clean(text))
    return brief[:limit]


def main() -> None:
    heads = fetch_kbs_headlines(limit=20)
    print('KBS 헤드라인:\n')
    print(heads)

    print('\n보너스: 날씨 요약:\n')
    print(fetch_weather_brief(limit=5))


if __name__ == '__main__':
    main()

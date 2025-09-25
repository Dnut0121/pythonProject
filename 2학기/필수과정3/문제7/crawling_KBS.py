import re, time
from html import unescape
from urllib.parse import urljoin
from typing import List, Set, Iterable
import requests
from bs4 import BeautifulSoup

BASE = 'https://news.kbs.co.kr'
NAVER_KBS = 'https://newsstand.naver.com/056'  # KBS 언론사 페이지(정적 HTML)
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Referer': 'https://news.naver.com/',
}

def get_html(url: str, timeout: int = 12) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    return r.text

def clean(s: str) -> str:
    s = unescape(s or '')
    return re.sub(r'\s+', ' ', s).strip()

def dedupe(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set(); out: List[str] = []
    for x in items:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def extract_article_urls_from_kbs_lists(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    urls: List[str] = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/news/' in href and ('/view.' in href or 'newsId=' in href):
            urls.append(urljoin(BASE, href))
    # 스크립트 내 URL 보강
    for m in re.finditer(r'(https?://[^"\']*?/news/[^"\']*?(?:view\.[a-z]+|newsId=\d+)[^"\']*)', html, re.I):
        urls.append(m.group(1))
    return dedupe(urls)

def extract_article_urls_from_naver(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    urls: List[str] = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'news.kbs.co.kr' in href and ('/news/' in href):
            urls.append(href)
    # 텍스트 덩어리에서도 회수
    for m in re.finditer(r'https?://news\.kbs\.co\.kr/[^"\']+', html):
        if '/news/' in m.group(0):
            urls.append(m.group(0))
    # 상세 링크만 남김
    urls = [u for u in urls if ('/view.' in u) or ('newsId=' in u)]
    return dedupe(urls)

def extract_title_from_article(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    # 1) og:title
    og = soup.find('meta', attrs={'property': 'og:title'})
    if og and og.get('content'):
        t = clean(og['content'])
        if 5 <= len(t) <= 160: return t
    # 2) 본문 h1/h2/타이틀류
    for sel in ('h1', 'h2', '[class*="title"]', '[class*="tit"]'):
        el = soup.select_one(sel)
        if el:
            t = clean(el.get_text(' ', strip=True))
            if 5 <= len(t) <= 160: return t
    # 3) <title>
    if soup.title and soup.title.string:
        t = clean(soup.title.string)
        if 5 <= len(t) <= 160: return t
    # 4) JSON-LD headline
    for sc in soup.find_all('script', attrs={'type': re.compile('ld\\+json', re.I)}):
        m = re.search(r'"headline"\s*:\s*"([^"]{5,160})"', sc.string or '', re.S)
        if m: return clean(m.group(1))
    return ''

def fetch_kbs_headlines(limit: int = 20) -> List[str]:
    urls: List[str] = []

    # A) KBS 리스트 페이지 시도
    for url in (
        f'{BASE}/news/list.do?mcd=0000000001',
        f'{BASE}/news/pc/list.html?mcd=0000000001',
        f'{BASE}/',
    ):
        try:
            html = get_html(url)
            urls += extract_article_urls_from_kbs_lists(html)
        except Exception:
            pass
        if len(urls) >= limit * 2:
            break

    # B) 비면 네이버 뉴스스탠드 KBS에서 URL 시드
    if len(dedupe(urls)) < 5:
        try:
            nhtml = get_html(NAVER_KBS)
            urls += extract_article_urls_from_naver(nhtml)
        except Exception:
            pass

    urls = dedupe(urls)[: max(limit * 3, 30)]

    # C) 각 기사 페이지에서 제목 추출
    titles: List[str] = []
    s = requests.Session(); s.headers.update(HEADERS)
    for u in urls:
        try:
            r = s.get(u, timeout=12); r.raise_for_status()
            r.encoding = r.apparent_encoding or r.encoding
            t = extract_title_from_article(r.text)
            if t:
                titles.append(t)
        except Exception:
            continue
        if len(titles) >= limit:
            break

    # D) 잡음 제거 및 중복 제거
    titles = [t for t in titles if not re.search(r'(구독|광고|이벤트|로그인|회원가입|바로가기)', t)]
    return dedupe(titles)[:limit]

def main():
    heads = fetch_kbs_headlines(20)
    print('KBS 헤드라인:\n')
    print(heads)
    if not heads:
        print('\n[DIAG] 비정상 환경 가능성: 프록시/방화벽(사내망), DNS, 403. 다른 네트워크에서 재시도 권장.')

if __name__ == '__main__':
    main()

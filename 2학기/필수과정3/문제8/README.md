# 네이버 로그인·메일 크롤러 README

## 개요

셀레니움으로 네이버 비로그인/로그인 콘텐츠 비교 후, 로그인 전용 콘텐츠로 “메일 제목”을 수집한다. 결과는 리스트 객체로 출력한다.

## 설치

```bash
pip install selenium webdriver-manager python-dotenv
```

## 환경변수

`.env`

```
NAVER_ID=네이버아이디
NAVER_PW=네이버비밀번호
```

## 실행

```bash
python crawling_KBS.py
```

옵션: 창 유지
Windows `set KEEP_OPEN=1` / macOS·Linux `export KEEP_OPEN=1`

---

## 함수별 상세 설명

### `setup_driver() -> webdriver.Chrome`

* 크롬 옵션 설정. 창 크기, 자동화 탐지 최소화, 페이지 로딩 전략(eager) 적용.
* 사용자 프로필 디렉터리(`./.selenium_profile`) 지정. 세션/2FA 재사용.
* `webdriver-manager`로 크롬드라이버 자동 설치·연결.
* `navigator.webdriver` 감춤 스크립트 주입.

### `apply_refresh_guards(driver) -> None`

* SPA 자동 새로고침, `beforeunload` 이벤트, 페이지 비가시성 이벤트를 무력화.
* keepalive 타이머로 탭 비활성화 시 렌더 정지 방지.

### `scrape_logged_out(driver, limit=10) -> List[str]`

* 비로그인 상태의 네이버 메인에서 뉴스·타이틀 텍스트를 다중 셀렉터로 수집.
* 중복 제거. 최대 `limit`개 반환.

### `login_naver(driver, uid: str, pw: str) -> None`

* 네이버 로그인 페이지로 이동. 기본이 간편로그인 탭이면 ID로그인으로 전환.
* 프레임 유무를 탐지해 ID·PW 입력 필드 탐색.
* 사람 타이핑처럼 느리게 입력해 입력 이벤트 유도.
* 로그인 버튼 클릭 실패 시 Enter 제출로 폴백.
* 로그인 성공 후 `mail.naver.com` 도달을 대기. 보안단계(2FA)면 수동 인증 후 진행.
* 메일 도메인 진입 뒤 `apply_refresh_guards` 적용.

### `click_by_text(driver, tag, contains_text_list, timeout=6) -> bool`

* XPath로 특정 텍스트를 포함하는 사이드바 항목을 찾아 클릭.
* “받은메일함”, “전체메일” 등 라벨 기반 네비게이션에 사용.

### `_find_scroll_container(driver) -> Any`

* 실제 스크롤이 발생하는 컨테이너를 JS로 탐색.
* 가상 리스트(무한 스크롤)에서 화면 로드 진전을 만들기 위한 스크롤 타깃을 반환.

### `_collect_subjects_js(driver) -> List[str]`

* 데스크톱 UI에서 제목 노드 후보를 JS로 일괄 수집.
* 대상: `div.mailList .subject a|span`, `[data-nodeid] .subject a|span`, `span.mail_title`, 그리드형 `role='row'` 내 subject.
* 텍스트 정제 후 중복 제거 리스트 반환.

### `go_mail_list_pc(driver) -> None`

* `/mail.naver.com`로 진입 후 사이드바에서 “받은메일함” 또는 “전체메일” 클릭.
* 단순 URL 진입이 아닌 실제 클릭으로 리스트 렌더를 강제.
* `apply_refresh_guards` 선적용.

### `wait_mail_ready(driver, max_wait=90) -> bool`

* 메일 리스트가 렌더될 때까지 다중 셀렉터로 존재 여부를 폴링.
* 로딩 중에는 윈도우 스크롤로 추가 렌더 유도.
* 준비되면 True, 타임아웃 시 False.

### `scrape_mail_subjects_pc(driver, max_items=40) -> List[str]`

* `go_mail_list_pc`로 사이드바 클릭 진입.
* `wait_mail_ready`로 리스트 렌더 완료 대기.
* `_find_scroll_container`로 스크롤 대상 결정.
* 루프: `_collect_subjects_js`로 제목 수집 → 증가 없으면 큰 스크롤, 증가 있으면 작은 스크롤로 계속 로드.
* 최대 `max_items`개 제목을 정제해 반환.

### `main() -> None`

* `.env` 로드. 자격 검증.
* `setup_driver` 실행.
* 1. 비로그인 콘텐츠 수집 후 즉시 출력.
* 2. 로그인 수행.
* 3. PC 메일 제목 수집.
* 4. 비로그인·로그인 결과를 하나의 객체로 최종 출력.
* `KEEP_OPEN` 미설정 시 종료 시 드라이버 정리.

---
# crawling_KBS.py
# 설치: pip install selenium webdriver-manager python-dotenv pyperclip

import os, sys, time
from typing import List
from dotenv import load_dotenv
import pyperclip

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------- Driver ----------
def setup_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--window-size=1500,2400")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("detach", True)
    opts.page_load_strategy = "eager"
    prof = os.path.abspath("./.selenium_profile")
    os.makedirs(prof, exist_ok=True)
    opts.add_argument(f"--user-data-dir={prof}")
    opts.add_argument("--profile-directory=selenium")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    })
    return driver


# ---------- Utils ----------
def apply_refresh_guards(driver):
    js = r"""
    try{
      window.__reloadBlocked=true;
      const _r=location.reload.bind(location);
      location.reload=function(){ if(!window.__reloadBlocked) _r(); };
      window.onbeforeunload=null;
      document.addEventListener('visibilitychange',e=>{e.stopImmediatePropagation();},true);
      Object.defineProperty(document,'visibilityState',{get:()=> 'visible'});
      Object.defineProperty(document,'hidden',{get:()=> false});
      if(!window.__keepalive) window.__keepalive=setInterval(()=>{},15000);
    }catch(e){}
    """
    try: driver.execute_script(js)
    except: pass


def click_by_text(driver, tag, contains_text_list, timeout=6) -> bool:
    end = time.time() + timeout
    xps = [f"//{tag}[contains(normalize-space(text()), '{t}') or contains(@aria-label,'{t}')]"
           for t in contains_text_list]
    while time.time() < end:
        for xp in xps:
            try:
                el = WebDriverWait(driver, 1.5).until(EC.presence_of_element_located((By.XPATH, xp)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.2)
                if el.is_displayed():
                    el.click()
                    return True
            except Exception:
                continue
    return False


def _find_scroll_container(driver):
    js = r"""
    const cands=[document.scrollingElement, document.documentElement, document.body, ...document.querySelectorAll('*')];
    let best=document.scrollingElement, H=0;
    for(const el of cands){
      try{
        const sh=el.scrollHeight||0, ch=el.clientHeight||0, oy=getComputedStyle(el).overflowY;
        if(sh>ch+20 && (oy==='auto'||oy==='scroll')){ if(sh>H){H=sh; best=el;} }
      }catch(e){}
    }
    return best;
    """
    try:
        return driver.execute_script(js)
    except:
        return None


def _collect_subjects_js(driver):
    js = r"""
    const out=[];
    document.querySelectorAll("div.mailList div.subject a, div.mailList div.subject span").forEach(e=>{
      const t=(e.innerText||e.textContent||"").trim(); if(t) out.push(t);
    });
    document.querySelectorAll("[data-nodeid] .subject a, [data-nodeid] .subject span, span.mail_title").forEach(e=>{
      const t=(e.innerText||e.textContent||"").trim(); if(t) out.push(t);
    });
    document.querySelectorAll("[role='row'] [class*='subject'] a, [role='row'] [class*='subject'] span").forEach(e=>{
      const t=(e.innerText||e.textContent||"").trim(); if(t) out.push(t);
    });
    return Array.from(new Set(out));
    """
    try:
        cur = driver.execute_script(js)
        return cur if isinstance(cur, list) else []
    except:
        return []


# ---------- Public (비로그인) ----------
def scrape_logged_out(driver, limit=10) -> List[str]:
    driver.get("https://www.naver.com/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    sels = ["a[href*='news'] span", "a.media_end_head_headline", "a[class*='title'], a[class*='link']"]
    out=[]
    for s in sels:
        for el in driver.find_elements(By.CSS_SELECTOR, s):
            t = el.text.strip()
            if t and t not in out:
                out.append(t)
            if len(out) >= limit:
                return out
    return out[:limit]


# ---------- Login ----------
def login_naver(driver, uid: str, pw: str):
    driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://mail.naver.com/")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    for s in ["#id_tab", "#id_login", "a#id_login", "button#id_login", "li[id*='id_login'] *"]:
        btn = driver.find_elements(By.CSS_SELECTOR, s)
        if btn:
            try: btn[0].click(); time.sleep(0.5)
            except: pass
            break
    frames=[None]+driver.find_elements(By.CSS_SELECTOR,"iframe,frame")
    id_el=pw_el=None
    for fr in frames:
        try:
            driver.switch_to.default_content()
            if fr: driver.switch_to.frame(fr)
            id_el = next((e for e in driver.find_elements(By.CSS_SELECTOR,"#id, input[name='id']") if e.is_displayed()), None)
            pw_el = next((e for e in driver.find_elements(By.CSS_SELECTOR,"#pw, input[name='pw'], input[type='password']") if e.is_displayed()), None)
            if id_el and pw_el: break
        except: pass
    driver.switch_to.default_content()
    if not id_el or not pw_el:
        print("[WARN] 로그인 폼 인식 실패. 창에서 수동 로그인 후 Enter."); input(); return
    for ch in uid: id_el.send_keys(ch); time.sleep(0.05)
    time.sleep(0.2)
    for ch in pw:  pw_el.send_keys(ch); time.sleep(0.05)
    time.sleep(0.2)
    try:
        btn = next((b for b in sum([driver.find_elements(By.CSS_SELECTOR,s) for s in
                       ["#log\\.login","button[type='submit']","input[type='submit']","button[id*='btn_login']"]],[])
                    if b.is_displayed()), None)
        (btn.click() if btn else pw_el.send_keys(Keys.ENTER))
    except: pw_el.send_keys(Keys.ENTER)
    WebDriverWait(driver, 60).until(EC.url_contains("mail.naver.com"))
    apply_refresh_guards(driver)


# ---------- Mail (PC) ----------
def go_mail_list_pc(driver):
    driver.get("https://mail.naver.com/")
    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    apply_refresh_guards(driver)
    if not click_by_text(driver, "a", ["받은메일함", "전체메일", "전체 메일"]):
        pass
    time.sleep(1.0)


def wait_mail_ready(driver, max_wait=90) -> bool:
    sels = [
        "div.mailList div.subject a", "div.mailList div.subject span",
        "[data-nodeid] .subject a", ".list_mail", ".list_area", "div[role='list']",
        "[role='row'] [class*='subject'] a, [role='row'] [class*='subject'] span"
    ]
    end=time.time()+max_wait
    while time.time()<end:
        for s in sels:
            if driver.find_elements(By.CSS_SELECTOR, s):
                return True
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(0.6)
    return False


def scrape_mail_subjects_pc(driver, max_items=40) -> List[str]:
    go_mail_list_pc(driver)
    if not wait_mail_ready(driver, 60):
        return []
    subjects: List[str] = []
    scroller = _find_scroll_container(driver)
    start = time.time()
    last = -1
    while time.time()-start < 120 and len(subjects) < max_items:
        for t in _collect_subjects_js(driver):
            if t and t not in subjects:
                subjects.append(t)
                if len(subjects) >= max_items: break
        if len(subjects) == last:
            if scroller:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 1400;", scroller)
            else:
                driver.execute_script("window.scrollBy(0, 1400);")
            time.sleep(0.8)
        else:
            last = len(subjects)
            if scroller:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 800;", scroller)
            else:
                driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.6)
    return subjects[:max_items]


# ---------- pyperclip ----------
def subjects_to_list_via_clipboard(subjects: List[str]) -> List[str]:
    prev = None
    try:
        prev = pyperclip.paste()
    except Exception:
        prev = None
    out = []
    try:
        for t in subjects:
            pyperclip.copy(t)
            copied = pyperclip.paste().strip()
            if copied:
                out.append(copied)
    finally:
        if prev is not None:
            try: pyperclip.copy(prev)
            except Exception: pass
    return out if out else subjects[:]  # 실패 시 원본 반환


# ---------- Main ----------
def main():
    load_dotenv()
    uid=os.getenv("NAVER_ID","").strip()
    pw=os.getenv("NAVER_PW","").strip()
    if not uid or not pw:
        print("[ERROR] .env에 NAVER_ID, NAVER_PW 필요"); sys.exit(1)

    driver=setup_driver()
    try:
        public_items = scrape_logged_out(driver, 8)
        print("=== 비로그인 콘텐츠 ===")
        print({"logged_out_sample_headlines": public_items})

        login_naver(driver, uid, pw)

        subjects = scrape_mail_subjects_pc(driver, 40)
        subjects_clip = subjects_to_list_via_clipboard(subjects)

        print("=== 최종 결과 ===")
        print({
            "logged_out_sample_headlines": public_items,
            "mail_subjects_after_login": subjects_clip
        })
    finally:
        if os.getenv("KEEP_OPEN","0")!="1":
            try: driver.quit()
            except: pass


if __name__=="__main__":
    main()

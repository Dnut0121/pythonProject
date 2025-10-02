import os, sys, time
from typing import List
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ================= Driver =================
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
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    })
    return driver


# ================= Common =================
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


# ================= Public (비로그인) =================
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


# ================= Login =================
def login_naver(driver, uid: str, pw: str):
    driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://mail.naver.com/")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    # ID 로그인 탭
    for s in ["#id_tab", "#id_login", "a#id_login", "button#id_login", "li[id*='id_login'] *"]:
        btn = driver.find_elements(By.CSS_SELECTOR, s)
        if btn:
            try: btn[0].click(); time.sleep(0.5)
            except: pass
            break
    # 입력창(프레임 대비)
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
    # 느린 타이핑
    for ch in uid: id_el.send_keys(ch); time.sleep(0.05)
    time.sleep(0.2)
    for ch in pw:  pw_el.send_keys(ch); time.sleep(0.05)
    time.sleep(0.2)
    # 제출
    try:
        btn = next((b for b in sum([driver.find_elements(By.CSS_SELECTOR,s) for s in
                       ["#log\\.login","button[type='submit']","input[type='submit']","button[id*='btn_login']"]],[])
                    if b.is_displayed()), None)
        (btn.click() if btn else pw_el.send_keys(Keys.ENTER))
    except: pw_el.send_keys(Keys.ENTER)
    # 도달
    WebDriverWait(driver, 60).until(EC.url_contains("mail.naver.com"))
    apply_refresh_guards(driver)


# ================= Mail(PC, 사이드바 강제) =================
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
    // 행 기반(테이블/그리드) 대비
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


def go_mail_list_pc(driver):
    driver.get("https://mail.naver.com/")
    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    apply_refresh_guards(driver)
    if not click_by_text(driver, "a", ["받은메일함", "받은메일함 999+", "받은메일함 99+"]):
        click_by_text(driver, "a", ["전체메일", "전체 메일"])
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
    go_mail_list_pc(driver)  # 사이드바 클릭 진입
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
                if len(subjects) >= max_items:
                    break
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


# ================= Main =================
def main():
    load_dotenv()
    uid=os.getenv("NAVER_ID","").strip()
    pw=os.getenv("NAVER_PW","").strip()
    if not uid or not pw:
        print("[ERROR] .env에 NAVER_ID, NAVER_PW 필요"); sys.exit(1)

    driver=setup_driver()
    try:
        # 1) 비로그인 콘텐츠 수집 및 즉시 출력
        public_items = scrape_logged_out(driver, 8)
        print("=== 비로그인 콘텐츠 ===")
        print({"logged_out_sample_headlines": public_items})

        # 2) 로그인
        login_naver(driver, uid, pw)

        # 3) PC 메일 제목 수집
        subjects = scrape_mail_subjects_pc(driver, 40)

        # 4) 최종 결과 출력
        print("=== 최종 결과 ===")
        print({
            "logged_out_sample_headlines": public_items,
            "mail_subjects_after_login": subjects
        })

    finally:
        if os.getenv("KEEP_OPEN","0")!="1":
            try: driver.quit()
            except: pass


if __name__=="__main__":
    main()

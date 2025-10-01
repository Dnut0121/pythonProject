# crawling_KBS.py
# 목적: 네이버 로그인 전/후 비교, 로그인 후 메일 제목 수집
# 준비: pip install selenium webdriver-manager python-dotenv
# .env: NAVER_ID=아이디, NAVER_PW=비밀번호
# 창 유지: Windows -> set KEEP_OPEN=1, mac/Linux -> export KEEP_OPEN=1

import os, sys, time
from typing import List
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ------------------------ 드라이버 ------------------------

def setup_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2400")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("detach", True)   # 스크립트 종료돼도 창 유지
    opts.page_load_strategy = "eager"
    # UA/언어 고정
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_argument("--lang=ko-KR,ko")

    # 고정 프로필로 세션 재사용
    profile_dir = os.path.abspath("./.selenium_profile")
    os.makedirs(profile_dir, exist_ok=True)
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_argument("--profile-directory=selenium")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.implicitly_wait(0)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


# ------------------------ 유틸 ------------------------

def robust_click(driver, css_list, timeout=10) -> bool:
    last = None
    for sel in css_list:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});", el
            )
            WebDriverWait(driver, timeout).until(lambda d: el.is_displayed() and el.is_enabled())
            try:
                el.click(); return True
            except Exception as e1:
                last = e1
            try:
                ActionChains(driver).move_to_element(el).pause(0.2).click().perform(); return True
            except Exception as e2:
                last = e2
            try:
                driver.execute_script("arguments[0].click();", el); return True
            except Exception as e3:
                last = e3
        except Exception as e:
            last = e
    if last: print("[robust_click] 마지막 오류:", repr(last))
    return False


def slow_type(el, text, delay=0.12):
    el.clear()
    for ch in text:
        el.send_keys(ch); time.sleep(delay)


def wait_any(driver, selectors: List[str], timeout: int) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        for sel in selectors:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if any(e.is_displayed() for e in els):
                return True
        time.sleep(0.4)
    return False


# ------------------------ 콘텐츠 ------------------------

def scrape_logged_out_content(driver: webdriver.Chrome, limit: int = 10) -> List[str]:
    driver.get("https://www.naver.com/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    sels = [
        "a[href*='news'] span",
        "a.media_end_head_headline",
        "a[class*='link'], a[class*='title']"
    ]
    out = []
    for sel in sels:
        for el in driver.find_elements(By.CSS_SELECTOR, sel):
            t = el.text.strip()
            if t and t not in out:
                out.append(t)
            if len(out) >= limit:
                return out
    return out[:limit]


def is_logged_in_soft(driver: webdriver.Chrome) -> bool:
    try:
        cookies = {c['name'] for c in driver.get_cookies()}
        if {"NID_AUT", "NID_SES"} & cookies:
            return True
        url = driver.current_url.lower()
        if "mail.naver.com" in url or "m.mail.naver.com" in url:
            return True
        return False
    except Exception:
        return False


def force_go_inbox(driver: webdriver.Chrome) -> None:
    # 전체메일함 → 받은편지함 → 모바일 순으로 시도
    targets = [
        "https://mail.naver.com/v2/folders/0/all",  # 전체메일함(SPA)
        "https://mail.naver.com/v2/inbox",          # 받은편지함
        "https://m.mail.naver.com/list/0"           # 모바일
    ]
    for url in targets:
        driver.get(url)
        try:
            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            if "folders/0/all" in driver.current_url:
                return
        except Exception:
            continue


def wait_for_inbox_ready(driver: webdriver.Chrome, max_wait=120) -> bool:
    sels = [
        # 데스크톱
        "div.mailList div.subject a",
        "div.mailList div.subject span",
        "span.mail_title",
        "[data-nodeid] .subject a",
        ".list_mail", ".list_area", "div[role='list']",
        # 모바일
        "strong.subject", ".mail_subject", ".subject", "a.mail_title, span.mail_title"
    ]
    end = time.time() + max_wait
    while time.time() < end:
        if wait_any(driver, sels, 2):
            return True
        force_go_inbox(driver)
    return False


def scrape_mail_subjects(driver: webdriver.Chrome, max_items=30) -> List[str]:
    subjects: List[str] = []

    def collect_desktop_all():
        selectors = [
            "div.mailList div.subject a",
            "div.mailList div.subject span",
            "span.mail_title",
            "[data-nodeid] .subject a",
        ]
        for sel in selectors:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                t = el.text.strip()
                if t and t not in subjects:
                    subjects.append(t)
                if len(subjects) >= max_items:
                    return

    def collect_mobile():
        for sel in ["strong.subject", ".mail_subject", ".subject", "a.mail_title", "span.mail_title"]:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                t = el.text.strip()
                if t and t not in subjects:
                    subjects.append(t)
                if len(subjects) >= max_items:
                    return

    # 1) 전체메일함 고정 수집
    driver.get("https://mail.naver.com/v2/folders/0/all")
    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    start = time.time()
    while time.time() - start < 90 and len(subjects) < max_items:
        collect_desktop_all()
        if len(subjects) >= max_items:
            break
        driver.execute_script("window.scrollBy(0, 1400);")
        time.sleep(0.9)

    # 2) 부족 시 받은편지함/모바일 백업
    if len(subjects) < max_items:
        for url in ["https://mail.naver.com/v2/inbox", "https://m.mail.naver.com/list/0"]:
            driver.get(url)
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except Exception:
                continue
            for _ in range(10):
                collect_desktop_all(); collect_mobile()
                if len(subjects) >= max_items:
                    break
                driver.execute_script("window.scrollBy(0, 1400);"); time.sleep(0.8)

    return subjects[:max_items]


# ------------------------ 로그인 ------------------------

def login_naver(driver: webdriver.Chrome, user_id: str, user_pw: str) -> None:
    driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://mail.naver.com/v2/folders/0/all")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # ID 로그인 탭 전환
    for sel in ["#id_tab", "#id_login", "a#id_login", "button#id_login", "li[id*='id_login'] *"]:
        btn = driver.find_elements(By.CSS_SELECTOR, sel)
        if btn:
            try: btn[0].click(); time.sleep(0.6)
            except: pass
            break

    # 입력창 탐색(프레임 대비)
    frames = [None] + driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    id_el = pw_el = None
    for fr in frames:
        try:
            driver.switch_to.default_content()
            if fr: driver.switch_to.frame(fr)
            cand_id = driver.find_elements(By.CSS_SELECTOR, "#id, input[name='id']")
            cand_pw = driver.find_elements(By.CSS_SELECTOR, "#pw, input[name='pw'], input[type='password']")
            id_el = next((e for e in cand_id if e.is_displayed()), None)
            pw_el = next((e for e in cand_pw if e.is_displayed()), None)
            if id_el and pw_el: break
        except: pass
    driver.switch_to.default_content()

    if not id_el or not pw_el:
        print("[WARN] 로그인 입력창 탐색 실패. 창에서 직접 로그인 후 Enter.")
        try: input()
        except: pass
    else:
        slow_type(id_el, user_id, 0.12); time.sleep(0.3)
        slow_type(pw_el, user_pw, 0.12); time.sleep(0.3)

        # 로그인 제출
        btns = [
            "#log\\.login", "#log\\:login",
            "button[type='submit']", "input[type='submit']",
            "button[id*='btn_login']", "a[id*='btn_login']"
        ]
        if not robust_click(driver, btns, timeout=8):
            try: pw_el.send_keys(Keys.ENTER)
            except: pass

    # 경고창/새창 처리
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except: pass
    try:
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
    except: pass

    # 도달 확인 후 보안 인증이면 수동
    try:
        WebDriverWait(driver, 60).until(
            EC.any_of(
                EC.url_contains("mail.naver.com"),
                EC.url_contains("account.naver.com"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='mail.naver.com'], a[href*='inbox']"))
            )
        )
    except: pass

    if "account.naver.com" in driver.current_url.lower():
        try: input("2단계 인증/캡챠 완료 후 Enter: ")
        except: pass

    # 전체메일함으로 확정 이동
    force_go_inbox(driver)


# ------------------------ 메인 ------------------------

def main():
    load_dotenv()
    uid = os.getenv("NAVER_ID", "").strip()
    pw = os.getenv("NAVER_PW", "").strip()
    if not uid or not pw:
        print("[ERROR] .env에 NAVER_ID, NAVER_PW 필요")
        sys.exit(1)

    driver = setup_driver(headless=False)

    try:
        print("[STEP] 비로그인 콘텐츠 수집")
        logged_out = scrape_logged_out_content(driver, 10)

        print("[STEP] 로그인 시도")
        login_naver(driver, uid, pw)

        # 판정 실패해도 진행
        logged_in_flag = is_logged_in_soft(driver)
        print("[INFO] soft login check:", logged_in_flag, "URL:", driver.current_url)

        # 받은편지함 준비 대기
        ready = wait_for_inbox_ready(driver, max_wait=120)
        print("[INFO] inbox ready:", ready, "URL:", driver.current_url)

        print("[STEP] 메일 제목 수집")
        subjects = scrape_mail_subjects(driver, max_items=30)

        result = {
            "logged_out_sample_headlines": logged_out,
            "mail_subjects_after_login": subjects
        }
        print("=== 결과 리스트 객체 ===")
        print(result)

        # 디버그 보조
        print("COOKIES(top10):", [c['name'] for c in driver.get_cookies()][:10])
        print("WINDOWS:", driver.window_handles)
        print("FINAL URL:", driver.current_url)
        print("VISIBLE NODES:",
              len(driver.find_elements(By.CSS_SELECTOR,
                  "div.mailList div.subject a, div.mailList div.subject span, "
                  "strong.subject, .mail_subject, .subject, a.mail_title, span.mail_title")))

    except Exception as e:
        print("[EXCEPTION]", repr(e))
        print("창을 유지합니다. 화면에서 상태 확인 후 Enter.")
        try: input()
        except: pass
    finally:
        if os.getenv("KEEP_OPEN", "0") != "1":
            try: driver.quit()
            except: pass
        else:
            print("KEEP_OPEN=1. 창은 수동 종료.")


if __name__ == "__main__":
    main()

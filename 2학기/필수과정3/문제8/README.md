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

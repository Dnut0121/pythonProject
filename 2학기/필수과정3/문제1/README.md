# 문제1 SOS

.env에 Gmail 계정과 **앱 비밀번호**를 저장하고, 별도 창에서 수신자·제목·본문·첨부파일을 입력해 메일을 발송한다.

---

## 기능 요약

* Gmail SMTP로 메일 발송(STARTTLS 587 / SSL 465)
* 수신자 다중 입력(쉼표 구분)
* 본문 멀티라인 입력
* 첨부파일 추가/제거
* 실시간 로그 표시
* .env에서 자격증명 로드

---

## 필수 조건


* Gmail **2단계 인증 활성화** 및 **앱 비밀번호 16자리** 발급
* 인터넷 연결

---

## 설치

```bash
pip install python-dotenv
```


---

## .env 설정

프로젝트 루트에 `.env` 파일 생성:

```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx   # 앱 비밀번호 16자리
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SSL=false
```

> 일반 계정 비밀번호는 불가. 앱 비밀번호만 허용.

---

## 실행

```bash
python sendmail.py
```

---

## 사용 방법

1. 창 상단 **From**: .env의 GMAIL_USER가 표시됨(수정 불가).
2. **To**: 수신자 이메일 입력. 여러 명은 `,`로 구분.
3. **Subject**: 제목 입력.
4. **Body**: 본문 입력.
5. **Attachments**:

   * `추가`: 파일 선택
   * `제거`: 선택 항목 삭제
   * `모두삭제`: 첨부 초기화
6. **SSL(465)** 체크 시 포트가 자동으로 465로 전환. 해제 시 587.
7. **Send** 클릭 → 하단 **Log**에 진행 상황 표시.

---

## GUI 구성

* 상단: 발송자, 수신자, 제목
* 중앙: 내용 텍스트 영역
* 첨부파일: 리스트 + 추가/제거 버튼
* SMTP 옵션: SSL 체크, Port 표시
* 하단: Send 버튼, Log 뷰어

![img.png](img.png)
---

## 예외 및 해결

| 증상                       | 원인                                      | 해결                                     |
| ------------------------ | --------------------------------------- | -------------------------------------- |
| `[ERR] 인증 실패. 앱 비밀번호 확인` | 일반 비밀번호 사용, 앱 비번 오입력, 2단계 미설정, 조직 정책 차단 | 2단계 인증 활성화 → 앱 비밀번호 재발급(16자) → .env 갱신 |
| 수신자 거부                   | 주소 오타, 정책 차단                            | 이메일 주소 재확인, 다른 수신자 테스트                 |
| 연결 실패                    | 방화벽/망 정책, 포트 차단                         | SSL 체크 후 465 사용, 사내망 정책 확인             |
| 메일이 안 보임                 | 스팸/필터                                   | 스팸함·필터 규칙 확인                           |

---

## 보안 주의

* `.env`에는 민감정보가 있으므로 VCS에 커밋 금지(`.gitignore`).
* 공용 PC에서 사용 금지. 필요시 앱 비밀번호 회수/재발급.
* From 주소는 GMAIL_USER와 동일해야 정상 발송.

---

## 파일 구조

```
.
├─ sendmail.py   # GUI 클라이언트 본체
├─ .env              # Gmail 계정/앱 비밀번호(로컬 전용)

```

---

## 코드 핵심(동작 흐름)

* `.env` 로드 → `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `SMTP_*` 값 확보
* Tkinter로 입력 수집(To/Subject/Body/Attachments)
* `EmailMessage` 구성 + MIME 타입 추정 후 첨부
* SMTP 전송

  * STARTTLS: `SMTP_PORT=587`, `SMTP_SSL=false`
  * SSL: `SMTP_PORT=465`, `SMTP_SSL=true`
* 예외 처리: 인증 실패, 수신자 거부, 기타 오류 로그 및 알림



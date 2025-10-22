
---
# 문제2 감동의 메세지
## 1) CSV 형식

* 파일명: `mail_target_list.csv`
* 인코딩: `UTF-8` 또는 `UTF-8-SIG`
* 헤더 포함: **이름,이메일**

예시:

```csv
이름,이메일
test,test@naver.com
test2,test@gmail.com
```

> 주의: 쉼표로 구분. 공백·빈 줄 제거.

---

## 2) 폴더 구성

```
project/
├─ sendmail.py        # 단일 파일 서버
├─ .env                   # SMTP 자격증명
├─ mail_target_list.csv   # 수신자 목록 (옵션: 브라우저에서 CSV 선택으로 업로드 가능)

```

---

## 3) .env 설정

Gmail(STARTTLS 587) 예시:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SSL=false
SMTP_USER=you@gmail.com
SMTP_PASSWORD=앱비밀번호16자리
FROM_ADDR=you@gmail.com
BIND=127.0.0.1
SERVE_PORT=8000
```

네이버(SSL 465) 예시:

```env
SMTP_HOST=smtp.naver.com
SMTP_PORT=465
SMTP_SSL=true
SMTP_USER=yourid@naver.com
SMTP_PASSWORD=네이버비밀번호
FROM_ADDR=yourid@naver.com
```

> Gmail은 **앱 비밀번호** 필수. 네이버는 POP3/SMTP 사용 허용 필요.

---

## 4) 실행

```bash
python sendmail.py
# 브라우저에서 http://127.0.0.1:8000 접속
```

---

## 5) 사용 절차

1. **받는사람** 입력 또는 우측 상단의 **CSV 선택** 버튼으로 `mail_target_list.csv` 업로드
   → CSV의 모든 이메일이 자동으로 채워짐.
2. **제목** 입력.
3. **본문** 입력(HTML, 에디터 제공).
4. **첨부** 선택(여러 개 가능).
5. **보내기** 클릭 → 서버가 SMTP로 발송.

---

## 6) 문제 해결

* “인증 실패”

  * Gmail: 앱 비밀번호 16자리인지 확인.
  * 네이버: `FROM_ADDR==SMTP_USER`인지, SMTP 허용 여부 확인.
* CSV가 안 읽힘

  * 헤더가 `이름,이메일`인지 확인.
  * 인코딩을 `UTF-8-SIG`로 저장.
* 587 차단

  * `.env`에서 `SMTP_SSL=true`, `SMTP_PORT=465`로 전환.

---


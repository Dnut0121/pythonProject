# 문제4 조금 더 나은 웹서버

브라우저로 접속하면 `index.html`을 전송하고, 서버 콘솔에는 **접속 시간 / 클라이언트 IP / 대략적 위치 정보를 출력합니다.

---

## 구성

```
project/
├─ server.py
└─ index.html
```

---

## 실행 방법

```bash
python server.py
```

브라우저에서 접속:

```
http://localhost:8080/
```

---

## 동작 개요

* **접속 포트**: `8080` (`HOST = '0.0.0.0'`)
* **라우팅**

  * `GET /` 또는 `GET /index.html` → `index.html` 반환
* **서버 로그(매 요청)**
  접속 시간 · 클라이언트 IP · IP 유형(로컬호스트/사설/공용) · 공용 IP일 경우 **국가/지역/도시/좌표/기관/ASN/시간대**

로그 예시:

```
[접속 시간] 2025-09-18 01:23:45 | [IP] 203.0.113.24 (공용망) | [위치] United States, California, Los Angeles | [좌표] 34.05,-118.24 | [조직] Example ISP | [ASN] AS12345 | [TZ] America/Los_Angeles
```

---

## 웹페이지
<img width="756" height="911" alt="image" src="https://github.com/user-attachments/assets/95f75329-a7bb-4161-8b58-51873d02d94d" />

## 외부 API(지오로케이션)

* API: **ip-api.com** (무료/키 불필요)
* 호출 예:

  ```
  http://ip-api.com/json/<IP>?fields=status,country,regionName,city,lat,lon,org,as,timezone,query
  ```
* 성공 시(`status=success`)만 값 사용
* **사설/로컬호스트 IP는 호출 안 함**
* 실패·타임아웃 시 위치 정보 없이 **기본 IP 유형만** 로그

---



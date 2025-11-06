# 문제1 또 새로운 프로젝트

간단한 공유 TO-DO API와 웹 클라이언트. FastAPI + uvicorn 사용.

## 요구 사항

* Python 3.9+
* pip

## 설치

```bash
pip install fastapi uvicorn
```

## 프로젝트 구조

```
project/
├─ todo.py          # FastAPI 앱 (API)
├─ index.html       # 웹 클라이언트
└─ README.md
```

## 실행

개발 서버:

```bash
python -m uvicorn todo:app --reload
# 기본: http://127.0.0.1:8000
```

외부 접속 허용:

```bash
python -m uvicorn todo:app --host 0.0.0.0 --port 8000
```

## API 개요

* `POST /todo/add`

  * 본문: `Dict` 자유 스키마. 예: `{"title":"buy milk","assignee":"minji","priority":"P2"}`
  * 빈 객체 `{}`이면 400과 경고 반환.
  * 응답:

    ```json
    {"status":"ok","added":{...},"count":1}
    ```
* `GET /todo/list`

  * 응답:

    ```json
    {"status":"ok","todo_list":[{...}], "count":1}
    ```

## curl 확인

추가:

```bash
curl -s -X POST "http://127.0.0.1:8000/todo/add" \
  -H "Content-Type: application/json" \
  -d '{"title":"회의 준비","assignee":"minji","priority":"P2","status":"todo"}' | jq
```

목록:

```bash
curl -s "http://127.0.0.1:8000/todo/list" | jq
```

빈 Dict 검증:

```bash
curl -i -s -X POST "http://127.0.0.1:8000/todo/add" \
  -H "Content-Type: application/json" -d '{}' 
# HTTP/1.1 400
# {"detail":{"warning":"입력 Dict가 비었습니다."}}
```

## 웹 클라이언트 (`index.html`)

단일 파일. 브라우저 UI 제공. `BASE`를 API 주소에 맞게 수정.

정적 서빙:

```bash
python -m http.server 5500
# http://127.0.0.1:5500/index.html
```

## 데이터 스키마 참고

자유 Dict. 권장 키:

```json
{
  "title": "문서 초안 작성",
  "assignee": "minji",
  "due": "2025-11-07",
  "priority": "P1|P2|P3",
  "status": "todo|doing|done",
  "notes": "세부 내용"
}
```

## 실행화면

![메인화면.png](image/%EB%A9%94%EC%9D%B8%ED%99%94%EB%A9%B4.png)

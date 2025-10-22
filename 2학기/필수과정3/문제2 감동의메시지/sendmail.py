import os, sys, ssl, smtplib, mimetypes, html, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.message import EmailMessage
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# SMTP 설정(.env)
HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
PORT = int(os.getenv("SMTP_PORT", "587"))          # 465=SSL, 587=STARTTLS
USE_SSL = os.getenv("SMTP_SSL", "false").lower() in ("1","true","yes","y")
USER = os.getenv("SMTP_USER", "").strip()          # Gmail: you@gmail.com / Naver: id@naver.com
PASS = os.getenv("SMTP_PASSWORD", "").strip()      # Gmail: 앱 비밀번호 16자리 / Naver: 계정 비번(POP/SMTP 허용)
FROM = os.getenv("FROM_ADDR", USER).strip()
BIND = os.getenv("BIND", "127.0.0.1")
SERVE_PORT = int(os.getenv("SERVE_PORT", "7171"))

HTML_FORM = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>메일 보내기</title>
<style>
:root{--bg:#0b0e12;--panel:#121821;--muted:#96a0b5;--text:#e7ecf3;--border:#202835;--accent:#4ea3ff;}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#0b0f17,#0b0e12);
font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Malgun Gothic,sans-serif;color:var(--text)}
.wrap{max-width:920px;margin:32px auto;padding:0 16px}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden}
.row{display:grid;grid-template-columns:100px 1fr;border-bottom:1px solid var(--border)}
.row:last-child{border-bottom:0}
.label{padding:12px;color:var(--muted);background:rgba(255,255,255,.03)}
.field{padding:10px}
input[type=text]{width:100%;background:transparent;border:0;color:var(--text);padding:10px;outline:none}
#editor{min-height:260px;max-height:60vh;overflow:auto;padding:12px;border:1px solid var(--border);border-radius:10px;background:rgba(255,255,255,.02)}
.attach{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.badges{display:flex;gap:6px;flex-wrap:wrap}
.badge{border:1px solid var(--border);border-radius:16px;padding:6px 10px;color:var(--muted);font-size:12px}
input[type=file]{display:none}
.btn{appearance:none;border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--text);
padding:10px 14px;border-radius:10px;cursor:pointer}
.btn.primary{background:linear-gradient(135deg,var(--accent),#7f6bff);border:0;color:#fff}
.toolbar{display:flex;gap:6px;margin:8px 0}
.tool{border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--text);
padding:6px 10px;border-radius:8px;cursor:pointer;font-size:13px}
.hint{color:var(--muted);font-size:12px;margin-top:8px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h2 style="margin:0">메일 보내기</h2>
    <div style="display:flex;gap:8px">
      <button class="btn" type="button" id="btn-load-csv">CSV에서 받는사람 불러오기</button>
      <label class="btn"><input type="file" id="csv" accept=".csv">CSV 선택</label>
      <button class="btn primary" type="button" id="btn-send">보내기</button>
    </div>
  </div>

  <form class="panel" id="form" method="post" action="/send" enctype="multipart/form-data">
    <div class="row">
      <div class="label">받는사람</div>
      <div class="field">
        <input type="text" name="to" id="to" placeholder="쉼표로 여러 명 ex) a@x.com, b@y.com" required>
        <div class="hint">CSV 형식: <code>이름,이메일</code> 헤더 포함</div>
      </div>
    </div>

    <div class="row">
      <div class="label">제목</div>
      <div class="field"><input type="text" name="subject" id="subject" placeholder="제목을 입력하세요" required></div>
    </div>

    <div class="row">
      <div class="label">본문</div>
      <div class="field">
        <div class="toolbar">
          <button class="tool" data-cmd="bold" type="button"><b>B</b></button>
          <button class="tool" data-cmd="italic" type="button"><i>I</i></button>
          <button class="tool" data-cmd="underline" type="button"><u>U</u></button>
          <button class="tool" data-cmd="insertUnorderedList" type="button">• 목록</button>
          <button class="tool" id="btn-link" type="button">링크</button>
          <button class="tool" id="btn-clear" type="button">서식지움</button>
        </div>
        <div id="editor" contenteditable="true">
          <h3>{{name}}님 안녕하세요.</h3>
          <p>HTML 본문 작성 영역입니다.</p>
        </div>
        <textarea name="html" id="html" style="display:none"></textarea>
      </div>
    </div>

    <div class="row">
      <div class="label">첨부</div>
      <div class="field attach">
        <div class="badges" id="files-list"></div>
        <label class="btn"><input type="file" name="files" id="files" multiple>파일 선택</label>
      </div>
    </div>
  </form>

  <div class="hint">SMTP 인증 정보는 서버(.env)에만 저장됩니다.</div>
</div>

<script>
// 서식 버튼
document.querySelectorAll('.tool[data-cmd]').forEach(btn=>{
  btn.addEventListener('click',()=>{ document.execCommand(btn.dataset.cmd,false,null); document.getElementById('editor').focus(); });
});
document.getElementById('btn-link').addEventListener('click', ()=>{
  const url = prompt('링크 URL 입력'); if(url) document.execCommand('createLink', false, url);
});
document.getElementById('btn-clear').addEventListener('click', ()=>{ document.execCommand('removeFormat', false, null); });

// 첨부 미리표시
const filesInput = document.getElementById('files');
const filesList  = document.getElementById('files-list');
filesInput.addEventListener('change', ()=>{
  filesList.innerHTML = '';
  [...filesInput.files].forEach(f=>{
    const b = document.createElement('span');
    b.className = 'badge';
    b.textContent = f.name + ' • ' + Math.round(f.size/1024) + 'KB';
    filesList.appendChild(b);
  });
});

// CSV 로더: FileReader로 로컬 CSV(이름,이메일) 읽어 '받는사람' 채움
document.getElementById('btn-load-csv').addEventListener('click', ()=>{
  document.getElementById('csv').click();
});
document.getElementById('csv').addEventListener('change', ()=>{
  const file = document.getElementById('csv').files[0];
  if(!file) return;
  const fr = new FileReader();
  fr.onload = () => {
    const lines = fr.result.split(/\\r?\\n/);
    const emails = [];
    for (let i=0;i<lines.length;i++){
      const line = lines[i].trim();
      if(!line) continue;
      if (i===0 && /이름\\s*,\\s*이메일/.test(line)) continue; // 헤더 스킵
      const parts = line.split(',');
      if (parts.length>=2){
        const email = (parts[1]||'').trim();
        if (email && /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) emails.push(email);
      }
    }
    const to = document.getElementById('to');
    const exist = to.value.split(',').map(s=>s.trim()).filter(Boolean);
    const merged = Array.from(new Set(exist.concat(emails)));
    to.value = merged.join(', ');
    alert('CSV에서 ' + emails.length + '개 이메일을 불러왔습니다.');
  };
  fr.readAsText(file, 'utf-8');
});

// 보내기: contenteditable → textarea 동기화 후 제출
document.getElementById('btn-send').addEventListener('click', async ()=>{
  document.getElementById('html').value = document.getElementById('editor').innerHTML;
  const form = document.getElementById('form');
  const fd = new FormData(form);
  const res = await fetch('/send', { method:'POST', body: fd });
  const txt = await res.text();
  if(res.ok) alert('발송 완료'); else alert('오류\\n'+txt);
});
</script>
</body></html>
"""

HTML_OK  = """<!doctype html><meta charset="utf-8"><title>OK</title>
<h2>발송 완료</h2><p>수신자 수: {n}</p><p><a href="/">돌아가기</a></p>"""
HTML_ERR = """<!doctype html><meta charset="utf-8"><title>ERROR</title>
<h2>오류</h2><pre style="white-space:pre-wrap">{msg}</pre><p><a href="/">돌아가기</a></p>"""

# ---------------- SMTP ----------------
def send_smtp(msg: EmailMessage):
    if USE_SSL:
        with smtplib.SMTP_SSL(HOST, PORT, context=ssl.create_default_context(), timeout=30) as s:
            s.login(USER, PASS); s.send_message(msg)
    else:
        with smtplib.SMTP(HOST, PORT, timeout=30) as s:
            s.ehlo(); s.starttls(context=ssl.create_default_context()); s.ehlo()
            s.login(USER, PASS); s.send_message(msg)

def html_to_text_fallback(html_body: str) -> str:
    # 간단 변환: 줄바꿈 보존 후 태그 제거
    t = html_body.replace("<br>", "\n").replace("<br/>","\n").replace("<br />","\n") \
                 .replace("</p>","\n").replace("</li>","\n").replace("</div>","\n")
    return re.sub(r"<[^>]+>", "", t)

def build_message(from_addr: str, to_list: list[str], subject: str, html_body: str, attachments: list[tuple[str, bytes]]) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    txt = html_to_text_fallback(html_body) or "HTML 미지원 클라이언트를 위한 대체 본문입니다."
    msg.set_content(txt)
    msg.add_alternative(html_body, subtype="html")
    for filename, data in attachments:
        ctype, enc = mimetypes.guess_type(filename)
        if ctype is None or enc is not None: ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    return msg

# ---------------- HTTP 핸들러 ----------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_FORM.encode("utf-8"))

    def do_POST(self):
        if self.path != "/send":
            self.send_response(404); self.end_headers(); return
        if not (USER and PASS and FROM):
            return self._error("SMTP 자격 증명이 없습니다(.env: SMTP_USER, SMTP_PASSWORD, FROM_ADDR).")
        ctype = self.headers.get("Content-Type","")
        if "multipart/form-data" not in ctype:
            return self._error("Content-Type이 multipart/form-data가 아닙니다.")
        try:
            fields = self._parse_multipart(ctype, int(self.headers.get("Content-Length","0")))
            # 텍스트 필드
            to_raw   = "".join(v for kind,_,v in fields.get("to",[("text",None,"")]) if kind=="text")
            subject  = "".join(v for kind,_,v in fields.get("subject",[("text",None,"")]) if kind=="text").strip()
            html_body= "".join(v for kind,_,v in fields.get("html",[("text",None,"")]) if kind=="text")
            # 파일 필드
            files_up = [(fn, data) for kind, fn, data in fields.get("files", []) if kind=="file" and fn]

            # 수신자 파싱
            to_list = [t.strip() for t in to_raw.split(",") if t and "@" in t]
            if not to_list: return self._error("수신자(to)가 비어 있습니다.")
            if not subject: return self._error("제목(subject)이 비어 있습니다.")
            if not html_body: return self._error("HTML 본문이 비어 있습니다.")

            msg = build_message(FROM, to_list, subject, html_body, files_up)
            send_smtp(msg)
            self._ok(len(to_list))
        except smtplib.SMTPAuthenticationError:
            self._error("인증 실패: 앱 비밀번호 또는 계정 정책을 확인하세요.")
        except Exception as e:
            self._error(f"{type(e).__name__}: {e}")

    # 간단 multipart parser
    def _parse_multipart(self, content_type: str, content_length: int):
        m = re.search(r'boundary=([^;]+)', content_type)
        if not m: return {}
        boundary = m.group(1)
        if boundary.startswith('"') and boundary.endswith('"'): boundary = boundary[1:-1]
        boundary = boundary.encode()
        body = self.rfile.read(content_length)
        parts = body.split(b'--' + boundary)
        fields = {}
        for part in parts:
            if not part or part in (b'--\r\n', b'--'): continue
            if part.startswith(b'\r\n'): part = part[2:]
            header_blob, _, content = part.partition(b'\r\n\r\n')
            if not content: continue
            headers = header_blob.decode(errors="ignore").split("\r\n")
            disp = ""; ctype = ""
            for h in headers:
                hl = h.lower()
                if hl.startswith("content-disposition:"): disp = h
                elif hl.startswith("content-type:"): ctype = h
            name_m = re.search(r'name="([^"]+)"', disp)
            fn_m   = re.search(r'filename="([^"]*)"', disp)
            name = name_m.group(1) if name_m else None
            filename = fn_m.group(1) if fn_m else None
            if content.endswith(b"\r\n"): content = content[:-2]
            if filename:
                fields.setdefault(name, []).append(("file", filename, content))
            else:
                val = content.decode(errors="ignore")
                fields.setdefault(name, []).append(("text", None, val))
        return fields

    def _ok(self, n:int):
        body = HTML_OK.format(n=n).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def _error(self, msg:str):
        body = HTML_ERR.format(msg=html.escape(msg)).encode("utf-8")
        self.send_response(400); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

def main():
    if not USER or not PASS:
        print("[WARN] SMTP_USER/SMTP_PASSWORD 미설정. .env로 설정하세요.", file=sys.stderr)
    srv = HTTPServer((BIND, SERVE_PORT), Handler)
    print(f"[INFO] http://{BIND}:{SERVE_PORT} | SMTP={HOST}:{PORT} SSL={USE_SSL}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] stopped.")

if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    main()

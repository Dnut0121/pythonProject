import os, ssl, smtplib, mimetypes, threading, sys
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ------------------------------
# 보조 유틸 함수
# ------------------------------

def env_bool(key: str, default: bool = False) -> bool:
    """문자열 환경변수를 불리언으로 변환"""
    v = os.getenv(key, str(default)).strip().lower()
    return v in ("1", "true", "yes", "y")

def attach_files_to_msg(msg: EmailMessage, paths: list[str], log_cb) -> None:
    """첨부파일 경로 리스트를 EmailMessage 객체에 추가"""
    for p in paths:
        pth = Path(p)
        if not pth.exists():
            log_cb(f"[WARN] 첨부 없음: {pth}")
            continue
        # 파일 MIME 타입 추정
        ctype, enc = mimetypes.guess_type(pth.name)
        if ctype is None or enc is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        # 바이너리로 읽어 첨부
        with open(pth, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=pth.name
            )
        log_cb(f"[INFO] 첨부 추가: {pth.name}")

def build_message(sender: str, to_list: list[str], subject: str, body: str,
                  attachments: list[str], log_cb) -> EmailMessage:
    """메일 헤더/본문을 세팅하고 첨부를 추가해 EmailMessage 구성"""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.set_content(body)  # 일반 텍스트 본문
    attach_files_to_msg(msg, attachments, log_cb)
    return msg

def send_gmail(msg: EmailMessage, host: str, port: int, use_ssl: bool,
               sender: str, app_pw: str, log_cb) -> None:
    """SMTP 서버로 메시지 전송. SSL 또는 STARTTLS 모드 지원"""
    if use_ssl:
        # 465 포트, SSL 즉시
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as s:
            s.login(sender, app_pw)
            s.send_message(msg)
    else:
        # 587 포트, STARTTLS 업그레이드
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.ehlo()
            s.login(sender, app_pw)
            s.send_message(msg)

# ------------------------------
# GUI 클래스
# ------------------------------

class MailGUI(tk.Tk):
    """Tkinter 기반 Gmail 발송 클라이언트"""
    def __init__(self) -> None:
        super().__init__()
        self.title("메일 발송")
        self.geometry("720x600")
        self.attachments: list[str] = []

        # .env 로드 및 SMTP 기본값 설정
        load_dotenv()  # 현재 경로의 .env 읽기
        self.sender = os.getenv("GMAIL_USER", "").strip()             # 발신 Gmail 주소
        self.app_pw = os.getenv("GMAIL_APP_PASSWORD", "").strip()     # 앱 비밀번호(16자리)
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()  # SMTP 호스트
        self.port = tk.StringVar(value=os.getenv("SMTP_PORT", "587")) # 포트
        self.use_ssl = tk.BooleanVar(value=env_bool("SMTP_SSL", False))  # SSL 사용 여부

        # 레이아웃 프레임
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # 발송자
        ttk.Label(frm, text="발송자").grid(row=0, column=0, sticky="w")
        self.e_from = ttk.Entry(frm)
        self.e_from.insert(0, self.sender)
        self.e_from.config(state="readonly")
        self.e_from.grid(row=0, column=1, columnspan=3, sticky="we", padx=6, pady=2)

        # 수신자 (쉼표 구분)
        ttk.Label(frm, text="수신자 (쉼표 구분)").grid(row=1, column=0, sticky="w")
        self.e_to = ttk.Entry(frm)
        self.e_to.grid(row=1, column=1, columnspan=3, sticky="we", padx=6, pady=2)

        # 제목
        ttk.Label(frm, text="제목").grid(row=2, column=0, sticky="w")
        self.e_subject = ttk.Entry(frm)
        self.e_subject.grid(row=2, column=1, columnspan=3, sticky="we", padx=6, pady=2)

        # 내용
        ttk.Label(frm, text="내용").grid(row=3, column=0, sticky="nw")
        self.t_body = tk.Text(frm, height=12)
        self.t_body.grid(row=3, column=1, columnspan=3, sticky="we", padx=6, pady=2)

        # 첨부 리스트 + 버튼
        ttk.Label(frm, text="첨부파일").grid(row=4, column=0, sticky="nw")
        self.lst_attach = tk.Listbox(frm, height=6)
        self.lst_attach.grid(row=4, column=1, sticky="we", padx=6, pady=2)
        btns = ttk.Frame(frm)
        btns.grid(row=4, column=2, sticky="n")
        ttk.Button(btns, text="추가", command=self.add_attach).pack(fill="x", pady=2)
        ttk.Button(btns, text="제거", command=self.remove_attach).pack(fill="x", pady=2)
        ttk.Button(btns, text="모두삭제", command=self.clear_attach).pack(fill="x", pady=2)

        # SMTP 옵션(SSL/포트 표시)
        opt = ttk.Frame(frm)
        opt.grid(row=5, column=1, columnspan=3, sticky="we", pady=4)
        ttk.Checkbutton(opt, text="SSL(465)", variable=self.use_ssl, command=self.on_ssl_toggle).pack(side="left")
        ttk.Label(opt, text="Port").pack(side="left", padx=(10,4))
        self.e_port = ttk.Entry(opt, width=6, textvariable=self.port)
        self.e_port.pack(side="left")
        ttk.Label(opt, text=f"Host={self.host}").pack(side="left", padx=10)

        # 발송 버튼
        self.btn_send = ttk.Button(frm, text="Send", command=self.on_send)
        self.btn_send.grid(row=6, column=3, sticky="e", pady=4)

        # 로그 출력 영역
        ttk.Label(frm, text="Log").grid(row=7, column=0, sticky="nw")
        self.t_log = tk.Text(frm, height=10, state="disabled")
        self.t_log.grid(row=7, column=1, columnspan=3, sticky="nsew", padx=6, pady=2)

        # 그리드 가중치 설정(리사이즈 대응)
        for i in range(4):
            frm.columnconfigure(i, weight=1)
        frm.rowconfigure(7, weight=1)

        # 사전 점검(자격 증명 유무 등)
        self._precheck()

    # ------------------------------
    # GUI 헬퍼
    # ------------------------------

    def log(self, s: str) -> None:
        """하단 로그 텍스트 위젯에 한 줄 추가"""
        self.t_log.config(state="normal")
        self.t_log.insert(tk.END, s + "\n")
        self.t_log.see(tk.END)
        self.t_log.config(state="disabled")
        self.update_idletasks()

    def _precheck(self) -> None:
        """.env 필수값 확인 및 진단 정보 출력"""
        if not self.sender or not self.app_pw:
            messagebox.showerror("오류", ".env에 GMAIL_USER, GMAIL_APP_PASSWORD가 필요합니다.")
        self.log(f"[DIAG] USER={self.sender} | APP_PW_LEN={len(self.app_pw)} | SSL={self.use_ssl.get()} | PORT={self.port.get()}")

    def on_ssl_toggle(self) -> None:
        """SSL 체크박스 상태에 따라 포트를 465/587로 자동 전환"""
        if self.use_ssl.get() and self.port.get() == "587":
            self.port.set("465")
        if not self.use_ssl.get() and self.port.get() == "465":
            self.port.set("587")

    def add_attach(self) -> None:
        """파일 선택 대화상자로 첨부 추가"""
        files = filedialog.askopenfilenames(title="첨부 파일 선택")
        for f in files:
            if f not in self.attachments:
                self.attachments.append(f)
                self.lst_attach.insert(tk.END, f)

    def remove_attach(self) -> None:
        """선택된 첨부를 리스트에서 제거"""
        sel = list(self.lst_attach.curselection())
        sel.reverse()
        for idx in sel:
            val = self.lst_attach.get(idx)
            self.lst_attach.delete(idx)
            try:
                self.attachments.remove(val)
            except ValueError:
                pass

    def clear_attach(self) -> None:
        """첨부 전체 초기화"""
        self.lst_attach.delete(0, tk.END)
        self.attachments.clear()

    # ------------------------------
    # 발송 처리
    # ------------------------------

    def on_send(self) -> None:
        """입력값 검증 후 별도 스레드에서 SMTP 발송"""
        to_line = self.e_to.get().strip()
        subject = self.e_subject.get().strip()
        body = self.t_body.get("1.0", tk.END).strip()

        # 필수 입력 검증
        if not to_line:
            messagebox.showerror("오류", "수신자 이메일이 필요합니다.")
            return
        if not subject:
            messagebox.showerror("오류", "제목이 필요합니다.")
            return
        if not body:
            messagebox.showerror("오류", "본문이 필요합니다.")
            return

        # 수신자 파싱(쉼표 구분)
        to_list = [t.strip() for t in to_line.split(",") if t.strip()]

        # 포트 숫자 변환
        try:
            port = int(self.port.get())
        except ValueError:
            messagebox.showerror("오류", "포트가 올바르지 않습니다.")
            return

        # 메일 객체 구성
        msg = build_message(self.sender, to_list, subject, body, self.attachments, self.log)
        host = self.host
        use_ssl = self.use_ssl.get()

        # GUI 프리징 방지용 스레드에서 전송
        def task():
            self.btn_send.config(state="disabled")
            try:
                self.log("[INFO] 발송 시작")
                send_gmail(msg, host, port, use_ssl, self.sender, self.app_pw, self.log)
                self.log("[OK] 발송 완료")
                messagebox.showinfo("완료", "메일 발송이 완료되었습니다.")
            except smtplib.SMTPAuthenticationError:
                self.log("[ERR] 인증 실패. 앱 비밀번호 확인 필요")
                messagebox.showerror("오류", "인증 실패. 앱 비밀번호를 확인하세요.")
            except smtplib.SMTPRecipientsRefused as e:
                self.log(f"[ERR] 수신자 거부: {e.recipients}")
                messagebox.showerror("오류", f"수신자 거부: {e.recipients}")
            except Exception as e:
                self.log(f"[ERR] 오류: {e}")
                messagebox.showerror("오류", str(e))
            finally:
                self.btn_send.config(state="normal")

        threading.Thread(target=task, daemon=True).start()

# ------------------------------
# 엔트리 포인트
# ------------------------------

if __name__ == "__main__":
    # Windows 콘솔 한글 깨짐 완화(실패해도 무시)
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

    app = MailGUI()
    app.mainloop()

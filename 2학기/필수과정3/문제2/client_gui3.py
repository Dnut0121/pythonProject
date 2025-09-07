import sys, socket, threading, queue, tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.scrolledtext import ScrolledText

ENC = 'utf-8'

def pick_font() -> str:
    if sys.platform.startswith('win'): return 'Malgun Gothic'
    if sys.platform == 'darwin': return 'Apple SD Gothic Neo'
    return 'Noto Sans KR'

class ClientApp:
    def __init__(self, host='127.0.0.1', port=5000) -> None:
        self.host, self.port = host, port
        self.nick, self.sock, self.r, self.w = '', None, None, None
        self.q: 'queue.Queue[str]' = queue.Queue()
        self.root = tk.Tk(); self.root.title('Chat'); self.root.geometry('420x640'); self.root.configure(bg='#F2F2F2')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.font = (pick_font(), 11)

        top = tk.Frame(self.root, bg='#F2F2F2'); top.pack(fill='x', padx=8, pady=(8,4))
        self.title = tk.Label(top, text='연결 안 됨', bg='#F2F2F2', font=(self.font[0], 12, 'bold')); self.title.pack(side='left')

        self.chat = ScrolledText(self.root, state='disabled', wrap='word', font=self.font, bg='#F2F2F2')
        self.chat.pack(fill='both', expand=True, padx=8, pady=4)
        self.chat.tag_config('sys', justify='center', foreground='#666', background='#E5E5E5', spacing1=4, lmargin1=80, rmargin=80)
        self.chat.tag_config('me',  justify='right',  background='#FEE500', spacing1=4, lmargin1=40, rmargin=10)
        self.chat.tag_config('ot',  justify='left',   background='#FFFFFF', spacing1=4, lmargin1=10,  rmargin=40)

        bottom = tk.Frame(self.root, bg='#F2F2F2'); bottom.pack(fill='x', padx=8, pady=(4,8))
        self.entry = tk.Entry(bottom, font=self.font); self.entry.pack(side='left', fill='x', expand=True)
        tk.Button(bottom, text='전송', command=self.send_current, bg='#222', fg='white', padx=12, pady=6).pack(side='left', padx=(6,0))
        self.entry.bind('<Return>', lambda e: (self.send_current(), 'break'))
        self.root.after(100, lambda: self.entry.focus_force())

        self.connect()
        self.root.after(50, self.poll)

    def connect(self) -> None:
        self.nick = simpledialog.askstring('닉네임', '닉네임을 입력하세요:', parent=self.root) or 'user'
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self.sock.connect((self.host, self.port))
            self.r = self.sock.makefile('r', encoding=ENC, newline='\n'); self.w = self.sock.makefile('w', encoding=ENC, newline='\n')
            self.title.config(text=f'{self.nick} @ {self.host}:{self.port}')
            threading.Thread(target=self.recv_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror('연결 실패', str(e)); self.put('서버 연결 실패', 'sys')

    def recv_loop(self) -> None:
        try:
            for line in self.r:
                t = line.rstrip('\n')
                if '닉네임을 입력하세요' in t:
                    self.send_line(self.nick); continue
                self.q.put(t)
        except Exception:
            pass
        finally:
            self.q.put('** 연결이 종료되었습니다 **')

    def send_line(self, text: str) -> None:
        try: self.w.write(text + '\n'); self.w.flush()
        except Exception: self.put('전송 실패 (연결 끊김)', 'sys')

    def poll(self) -> None:
        try:
            while True: self.route(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def route(self, t: str) -> None:
        if t.startswith('** 연결이 종료되었습니다'):
            self.put('연결이 종료되었습니다.', 'sys')
            return

        if t.endswith('입장하셨습니다.') or t.endswith('퇴장하셨습니다.'):
            self.put(t, 'sys')
            return

        if t.startswith('(귓속말) '):
            try:
                rest = t[6:].strip()  # "(귓속말)" 제거
                name, body = rest.split('> ', 1)
                if name == self.nick:
                    self.put(f'(귓) {body}', 'me')
                else:
                    self.put(f'{name}(귓)> {body}', 'ot')
            except ValueError:
                self.put(t, 'sys')
            return

        if t.startswith('(귓속말 전송됨) '):
            self.put(t, 'sys')
            return

        if '> ' in t:
            name, body = t.split('> ', 1)
            if name == self.nick:
                self.put(body, 'me')
            else:
                self.put(f'{name}> {body}', 'ot')
            return

        if '닉네임을 입력하세요' in t:
            return

        self.put(t, 'sys')

    def put(self, text: str, tag: str) -> None:
        self.chat['state'] = 'normal'
        self.chat.insert('end', text + '\n', tag)
        self.chat['state'] = 'disabled'
        self.chat.see('end')

    def send_current(self) -> None:
        text = self.entry.get().strip()
        if not text: return
        if text == '/종료': self.send_line(text); self.close(); return
        self.send_line(text); self.entry.delete(0, 'end')

    def close(self) -> None:
        try:
            if self.w: self.w.write('/종료\n'); self.w.flush()
        except Exception: pass
        try:
            if self.r: self.r.close()
            if self.w: self.w.close()
            if self.sock: self.sock.close()
        finally:
            self.root.destroy()

def main() -> None:
    host = '127.0.0.1'; port = 5000
    if len(sys.argv) >= 2: host = sys.argv[1]
    if len(sys.argv) >= 3: port = int(sys.argv[2])
    ClientApp(host, port).root.mainloop()

if __name__ == '__main__':
    main()

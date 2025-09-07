import socket, threading
from typing import Dict, Tuple, TextIO

ENC = 'utf-8'

class ChatServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000) -> None:
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((host, port)); self.s.listen()
        self.lock = threading.Lock()
        self.clients: Dict[str, Tuple[socket.socket, TextIO, TextIO]] = {}

    def start(self) -> None:
        print('listening...')
        try:
            while True:
                c, a = self.s.accept()
                threading.Thread(target=self.handle, args=(c,), daemon=True).start()
        finally:
            self.s.close()

    def handle(self, conn: socket.socket) -> None:
        with conn:
            r = conn.makefile('r', encoding=ENC, newline='\n')
            w = conn.makefile('w', encoding=ENC, newline='\n')
            self.send(w, '닉네임을 입력하세요: ')
            name = (r.readline() or '').strip() or 'user'
            with self.lock:
                n = name; i = 1
                while n in self.clients: i += 1; n = f'{name}{i}'
                name = n; self.clients[name] = (conn, r, w)
            self.broadcast(f'{name}님이 입장하셨습니다.')
            try:
                for line in r:
                    msg = line.rstrip('\n')
                    if msg == '/종료': self.send(w, '연결을 종료합니다.'); break
                    if self.whisper(name, msg): continue
                    self.broadcast(f'{name}> {msg}')
            finally:
                with self.lock:
                    ent = self.clients.pop(name, None)
                if ent:
                    _, rf, wf = ent
                    try: rf.close(); wf.close()
                    except Exception: pass
                self.broadcast(f'{name}님이 퇴장하셨습니다.')

    def whisper(self, sender: str, msg: str) -> bool:
        if not msg: return False
        if msg.startswith('@'):
            parts = msg.split(' ', 1)
            if len(parts) < 2: self.send_to(sender, '사용법: @닉 메시지'); return True
            target, body = parts[0][1:], parts[1]
            return self._deliver_whisper(sender, target, body)
        if msg.startswith('/w '):
            parts = msg.split(' ', 2)
            if len(parts) < 3: self.send_to(sender, '사용법: /w 닉 메시지'); return True
            _, target, body = parts
            return self._deliver_whisper(sender, target, body)
        return False

    def _deliver_whisper(self, sender: str, target: str, body: str) -> bool:
        if not target or not body: self.send_to(sender, '귓속말 형식 오류'); return True
        if target == sender: self.send_to(sender, '본인에게는 보낼 수 없습니다.'); return True
        with self.lock: ent = self.clients.get(target)
        if not ent: self.send_to(sender, f'[{target}] 없음'); return True
        self.send(ent[2], f'(귓속말) {sender}> {body}')
        self.send_to(sender, f'(귓속말 전송됨) {sender} -> {target}: {body}')
        return True

    def broadcast(self, text: str) -> None:
        with self.lock: targets = [w for _, _, w in self.clients.values()]
        for w in targets: self.send(w, text)

    def send_to(self, name: str, text: str) -> None:
        with self.lock: ent = self.clients.get(name)
        if ent: self.send(ent[2], text)

    @staticmethod
    def send(w: TextIO, text: str) -> None:
        try: w.write(text + '\n'); w.flush()
        except Exception: pass

if __name__ == '__main__':
    ChatServer().start()

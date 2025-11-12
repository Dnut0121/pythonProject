import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import requests

# ----- 설정 -----
BASE = "http://127.0.0.1:8000"
URL_ADD  = f"{BASE}/todo/add"
URL_LIST = f"{BASE}/todo/list"
URL_ONE  = lambda _id: f"{BASE}/todo/{_id}"

TIMEOUT = 8  # 초

# ----- HTTP 래퍼 -----
def request(method, url, json_body=None):
    try:
        kwargs = {"timeout": TIMEOUT}
        if json_body is not None:
            kwargs["json"] = json_body
        r = requests.request(method, url, **kwargs)
        # FastAPI 에러 포맷 처리
        if not r.ok:
            try:
                data = r.json()
                msg = data.get("detail", data)
                if isinstance(msg, dict) and "warning" in msg:
                    raise RuntimeError(str(msg["warning"]))
                raise RuntimeError(str(msg))
            except ValueError:
                raise RuntimeError(f"HTTP {r.status_code}")
        # 성공 응답
        try:
            return r.json()
        except ValueError:
            return r.text
    except requests.exceptions.Timeout:
        raise RuntimeError("요청 시간 초과")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("서버에 연결할 수 없음")
    except Exception as e:
        raise RuntimeError(str(e))

# ----- 비동기 유틸 -----
def run_async(fn):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        t.start()
    return wrapper

# ----- 상세/수정 창 -----
class DetailWindow(tk.Toplevel):
    def __init__(self, master, item_id, on_changed):
        super().__init__(master)
        self.title(f"항목 상세 #{item_id}")
        self.geometry("520x420")
        self.resizable(False, False)

        self.item_id = item_id
        self.on_changed = on_changed

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # 폼
        self.vars = {
            "title": tk.StringVar(),
            "assignee": tk.StringVar(),
            "due": tk.StringVar(),
            "priority": tk.StringVar(),
            "status": tk.StringVar(),
        }

        row = 0
        ttk.Label(frm, text="제목").grid(row=row, column=0, sticky="w");
        ttk.Entry(frm, textvariable=self.vars["title"], width=48).grid(row=row, column=1, sticky="we"); row+=1

        ttk.Label(frm, text="담당자").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["assignee"]).grid(row=row, column=1, sticky="we"); row+=1

        ttk.Label(frm, text="기한(YYYY-MM-DD)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["due"]).grid(row=row, column=1, sticky="we"); row+=1

        ttk.Label(frm, text="우선순위(P1/P2/P3)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["priority"]).grid(row=row, column=1, sticky="we"); row+=1

        ttk.Label(frm, text="상태(todo/doing/done)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["status"]).grid(row=row, column=1, sticky="we"); row+=1

        ttk.Label(frm, text="메모").grid(row=row, column=0, sticky="nw")
        self.txt_notes = tk.Text(frm, height=8, width=48)
        self.txt_notes.grid(row=row, column=1, sticky="we"); row+=1

        frm.grid_columnconfigure(1, weight=1)

        # 버튼 영역
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=2, sticky="e", pady=(10,0))
        self.msg = ttk.Label(frm, foreground="#888")
        self.msg.grid(row=row+1, column=0, columnspan=2, sticky="w", pady=(6,0))

        ttk.Button(btns, text="저장", command=self.save).pack(side="right", padx=4)
        ttk.Button(btns, text="삭제", command=self.delete).pack(side="right", padx=4)
        ttk.Button(btns, text="닫기", command=self.destroy).pack(side="right", padx=4)

        self.load()

    @run_async
    def load(self):
        try:
            data = request("GET", URL_ONE(self.item_id))
            item = data.get("item", {})
            self.vars["title"].set(item.get("title","") or "")
            self.vars["assignee"].set(item.get("assignee","") or "")
            self.vars["due"].set(item.get("due","") or "")
            self.vars["priority"].set(item.get("priority","") or "")
            self.vars["status"].set(item.get("status","") or "")
            self.txt_notes.delete("1.0", "end")
            self.txt_notes.insert("1.0", item.get("notes","") or "")
            self.msg.config(text="불러오기 완료")
        except Exception as e:
            self.msg.config(text=f"오류: {e}")

    @run_async
    def save(self):
        try:
            patch = {}
            # 비어 있으면 전달하지 않음(부분 수정)
            for k, var in self.vars.items():
                v = var.get().strip()
                if v != "":
                    patch[k] = v
            notes = self.txt_notes.get("1.0", "end").strip()
            patch["notes"] = notes  # 빈 문자열도 허용. 변경 없음을 원하면 주석 처리.

            if not patch:
                self.msg.config(text="변경할 필드가 없습니다.")
                return
            request("PUT", URL_ONE(self.item_id), json_body=patch)
            self.msg.config(text="저장됨")
            if self.on_changed: self.on_changed()
        except Exception as e:
            self.msg.config(text=f"오류: {e}")

    @run_async
    def delete(self):
        try:
            request("DELETE", URL_ONE(self.item_id))
            self.msg.config(text="삭제됨")
            if self.on_changed: self.on_changed()
            self.after(200, self.destroy)
        except Exception as e:
            self.msg.config(text=f"오류: {e}")

# ----- 메인 앱 -----
class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("팀 TO-DO 클라이언트")
        self.geometry("900x560")
        self.resizable(True, True)

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        # 좌측: 추가 폼
        left = ttk.LabelFrame(root, text="할 일 추가", padding=10)
        left.pack(side="left", fill="y")

        self.inp = {
            "title": tk.StringVar(),
            "assignee": tk.StringVar(),
            "due": tk.StringVar(),
            "priority": tk.StringVar(value="P2"),
            "status": tk.StringVar(value="todo"),
        }

        ttk.Label(left, text="제목 *").pack(anchor="w")
        ttk.Entry(left, textvariable=self.inp["title"], width=30).pack(anchor="w", pady=(0,6))

        ttk.Label(left, text="담당자").pack(anchor="w")
        ttk.Entry(left, textvariable=self.inp["assignee"]).pack(anchor="w", pady=(0,6))

        ttk.Label(left, text="기한(YYYY-MM-DD)").pack(anchor="w")
        ttk.Entry(left, textvariable=self.inp["due"]).pack(anchor="w", pady=(0,6))

        ttk.Label(left, text="우선순위(P1/P2/P3)").pack(anchor="w")
        ttk.Combobox(left, textvariable=self.inp["priority"], values=["P1","P2","P3"], width=6, state="readonly").pack(anchor="w", pady=(0,6))

        ttk.Label(left, text="상태(todo/doing/done)").pack(anchor="w")
        ttk.Combobox(left, textvariable=self.inp["status"], values=["todo","doing","done"], width=8, state="readonly").pack(anchor="w", pady=(0,6))

        ttk.Label(left, text="메모").pack(anchor="w")
        self.notes = tk.Text(left, height=8, width=30)
        self.notes.pack(anchor="w")

        lf_btns = ttk.Frame(left)
        lf_btns.pack(anchor="e", pady=(8,0))
        ttk.Button(lf_btns, text="초기화", command=self.reset_form).pack(side="left", padx=4)
        ttk.Button(lf_btns, text="추가", command=self.add).pack(side="left")

        self.left_msg = ttk.Label(left, foreground="#888")
        self.left_msg.pack(anchor="w", pady=(6,0))

        # 우측: 목록 + 도구
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, padx=(12,0))

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="검색:").pack(side="left")
        self.q = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.q, width=30).pack(side="left", padx=(4,8))
        ttk.Button(toolbar, text="새로고침", command=self.refresh).pack(side="left")
        self.count_lbl = ttk.Label(toolbar, text="총 0건")
        self.count_lbl.pack(side="right")

        # Treeview
        cols = ("id", "title", "assignee", "status", "priority", "due")
        self.tv = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for c, w in zip(cols, (60, 280, 120, 90, 70, 100)):
            self.tv.heading(c, text=c.upper())
            self.tv.column(c, width=w, anchor="w")
        self.tv.pack(fill="both", expand=True, pady=(6,0))

        # 하단 액션
        actions = ttk.Frame(right)
        actions.pack(fill="x", pady=(10,0))
        ttk.Button(actions, text="보기", command=self.view_selected).pack(side="left", padx=4)
        ttk.Button(actions, text="수정", command=self.edit_selected).pack(side="left", padx=4)
        ttk.Button(actions, text="삭제", command=self.delete_selected).pack(side="left", padx=4)

        self.status = ttk.Label(self, anchor="w", relief="sunken")
        self.status.pack(fill="x")

        # 초기 로드
        self.refresh()

    def reset_form(self):
        self.inp["title"].set("")
        self.inp["assignee"].set("")
        self.inp["due"].set("")
        self.inp["priority"].set("P2")
        self.inp["status"].set("todo")
        self.notes.delete("1.0", "end")
        self.left_msg.config(text="")

    @run_async
    def add(self):
        self.left_msg.config(text="추가 중...")
        payload = {}
        t = self.inp["title"].get().strip()
        if t:
            payload["title"] = t
        a = self.inp["assignee"].get().strip()
        if a:
            payload["assignee"] = a
        d = self.inp["due"].get().strip()
        if d:
            payload["due"] = d
        p = self.inp["priority"].get().strip()
        if p:
            payload["priority"] = p
        s = self.inp["status"].get().strip()
        if s:
            payload["status"] = s
        n = self.notes.get("1.0", "end").strip()
        if n:
            payload["notes"] = n

        try:
            request("POST", URL_ADD, json_body=payload)
            self.left_msg.config(text="추가됨")
            self.reset_form()
            self.refresh()
        except Exception as e:
            self.left_msg.config(text=f"추가 실패: {e}")

    def _selected_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("안내", "항목을 선택하세요.")
            return None
        item = self.tv.item(sel[0])
        return item["values"][0]

    def view_selected(self):
        _id = self._selected_id()
        if _id is None:
            return
        DetailWindow(self, _id, on_changed=self.refresh)

    def edit_selected(self):
        self.view_selected()

    @run_async
    def delete_selected(self):
        _id = self._selected_id()
        if _id is None:
            return
        try:
            request("DELETE", URL_ONE(_id))
            self.status.config(text=f"삭제됨: #{_id}")
            self.refresh()
        except Exception as e:
            self.status.config(text=f"삭제 실패: {e}")

    @run_async
    def refresh(self):
        self.status.config(text="로드 중...")
        try:
            data = request("GET", URL_LIST)
            items = data.get("todo_list", [])
            q = self.q.get().strip().lower()
            # 테이블 갱신
            for i in self.tv.get_children():
                self.tv.delete(i)
            for it in items:
                if q and not (
                    (it.get("title","") or "").lower().find(q) >= 0 or
                    (it.get("assignee","") or "").lower().find(q) >= 0
                ):
                    continue
                self.tv.insert("", "end", values=(
                    it.get("id", ""),
                    it.get("title", ""),
                    it.get("assignee", ""),
                    it.get("status", ""),
                    it.get("priority", ""),
                    it.get("due", ""),
                ))
            self.count_lbl.config(text=f"총 {len(items)}건")
            self.status.config(text="준비됨")
        except Exception as e:
            self.status.config(text=f"로드 실패: {e}")

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()

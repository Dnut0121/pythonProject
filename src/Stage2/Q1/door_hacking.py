import zipfile
import zlib
import time
import torch
import sys
from multiprocessing import Process, Queue, Event, cpu_count
from tqdm import tqdm

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
LENGTH = 6

def base36_encode(idx: int, chars: str, length: int) -> str:
    base = len(chars)
    s = []
    for _ in range(length):
        idx, rem = divmod(idx, base)
        s.append(chars[rem])
    return ''.join(reversed(s))

def producer(batch_size: int, queue: Queue, stop_evt: Event):
    total = len(CHARS) ** LENGTH
    idx = 0
    pbar = tqdm(total=total, desc="Passwords Generated", unit="pwd")
    try:
        while idx < total and not stop_evt.is_set():
            end = min(total, idx + batch_size)
            indices = torch.arange(idx, end, device='cuda', dtype=torch.long)
            passwords = [base36_encode(int(i), CHARS, LENGTH)
                         for i in indices.cpu().tolist()]
            queue.put(passwords)
            pbar.update(len(passwords))
            idx = end
    finally:
        pbar.close()
        for _ in range(cpu_count()):
            queue.put(None)

def worker(zip_path: str, queue: Queue, stop_evt: Event, result_q: Queue):
    zf = zipfile.ZipFile(zip_path)
    to_test = zf.namelist()[0]
    while not stop_evt.is_set():
        batch = queue.get()
        if batch is None:
            break
        for pwd in batch:
            try:
                _ = zf.read(to_test, pwd=pwd.encode())
            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                continue
            else:
                stop_evt.set()
                result_q.put((pwd, time.time()))
                return

def unlock_zip_parallel(zip_path: str, batch_size: int = 100_000):
    start_time = time.time()
    q = Queue(maxsize=cpu_count() * 2)
    stop_evt = Event()
    result_q = Queue()

    prod = Process(target=producer, args=(batch_size, q, stop_evt))
    prod.start()

    workers = []
    for _ in range(cpu_count()):
        p = Process(target=worker, args=(zip_path, q, stop_evt, result_q))
        p.start()
        workers.append(p)

    try:
        pwd, found_time = result_q.get()
        elapsed = found_time - start_time
        print(f"\n[✔] Success! Password: '{pwd}'")
        print(f"    Elapsed: {elapsed:.2f}s (batch_size={batch_size})")

        with open('password.txt', 'w') as f:
            f.write(pwd)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Stopping all processes...")
        stop_evt.set()
    finally:
        prod.join()
        for p in workers:
            p.join()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        zip_path = sys.argv[1]
    else:
        zip_path = "emergency_storage_key.zip"
        print(f"[i] No argument given. Using default: {zip_path}")
    unlock_zip_parallel(zip_path)

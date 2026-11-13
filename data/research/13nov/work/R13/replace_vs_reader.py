import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Does a reader holding the target open (as the gateway's static server does) refuse os.replace on Windows?
Writer: tmp + os.replace every 10 ms. Reader: open/read/close in a loop, holding the file HOLD_S each time."""
import os, threading, time, ctypes
from ctypes import wintypes
D = r"D:\ApexOptions\data\research\13nov\work\R13\scratch_replace"; os.makedirs(D, exist_ok=True)
P = os.path.join(D, "f.json"); body = "x" * 35000
open(P, "w").write(body)
def reader_py(stop, hold):
    while not stop.is_set():
        try:
            with open(P, "rb") as f:
                f.read(); time.sleep(hold)
        except OSError: pass
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.restype = wintypes.HANDLE
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
def reader_share_delete(stop, hold):
    import msvcrt
    while not stop.is_set():
        h = k32.CreateFileW(P, 0x80000000, 0x1 | 0x2 | 0x4, None, 3, 0x80, None)   # GENERIC_READ, share R|W|DELETE, OPEN_EXISTING
        if h in (None, wintypes.HANDLE(-1).value):
            continue
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY)
        with os.fdopen(fd, "rb") as f:
            f.read(); time.sleep(hold)
def run(reader, hold, n=150):
    stop = threading.Event(); th = threading.Thread(target=reader, args=(stop, hold), daemon=True); th.start()
    refused = 0
    for i in range(n):
        tmp = P + ".tmp"
        with open(tmp, "w") as f: f.write(body)
        try: os.replace(tmp, P)
        except PermissionError: refused += 1
        time.sleep(0.01)
    stop.set(); th.join(1)
    return refused, n
for hold in (0.0, 0.002):
    print(f"reader holds {hold*1000:.0f} ms: python open() reader -> refused {run(reader_py, hold)}; "
          f"share-delete reader -> refused {run(reader_share_delete, hold)}")
def no_reader(stop, hold):
    stop.wait()
print("no reader at all -> refused", run(no_reader, 0.0))
# in-place double slot: writer rewrites slot k (no rename), reader picks the complete newest slot
def slots_test(n=150):
    S = [os.path.join(D, f"slot{k}.json") for k in (0, 1)]
    for s in S: open(s, "w").write("0\n" + body)
    stop = threading.Event(); bad = [0, 0]
    def rd():
        while not stop.is_set():
            best = None
            for s in S:
                try:
                    with open(s, "rb") as f: txt = f.read()
                except OSError: bad[1] += 1; continue
                head, _, rest = txt.partition(b"\n")
                if head.isdigit() and len(rest) == len(body):
                    best = max(best or 0, int(head))
                else: bad[0] += 1
    th = threading.Thread(target=rd, daemon=True); th.start(); errs = 0
    for i in range(1, n + 1):
        try:
            with open(S[i % 2], "w") as f: f.write(f"{i}\n" + body)
        except OSError: errs += 1
        time.sleep(0.01)
    stop.set(); th.join(1)
    return dict(write_errors=errs, torn_reads_skipped=bad[0], open_errors=bad[1])
print("double slot, no rename:", slots_test())

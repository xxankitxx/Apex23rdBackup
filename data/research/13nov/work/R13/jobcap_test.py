import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Test: put THIS process in a Windows job object with a hard CPU-rate cap, then spin and measure CPU used."""
import ctypes, time
from ctypes import wintypes
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
class CPU_RATE(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]
k32.CreateJobObjectW.restype = wintypes.HANDLE
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
def cap(pct):
    job = k32.CreateJobObjectW(None, None)
    info = CPU_RATE(0x1 | 0x4, int(pct * 100))           # ENABLE | HARD_CAP; CpuRate in 1/100 of a percent of the WHOLE machine
    ok1 = k32.SetInformationJobObject(job, 15, ctypes.byref(info), ctypes.sizeof(info))   # JobObjectCpuRateControlInformation
    ok2 = k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
    return bool(ok1), bool(ok2), ctypes.get_last_error(), job
def spin(s):
    c0, w0 = time.process_time(), time.time(); x = 0
    while time.time() - w0 < s: x += 1
    return round((time.process_time() - c0) / (time.time() - w0) * 100, 1)
print("uncapped, one thread: CPU % of one core:", spin(2.0))
print("cap 2 % of machine:", cap(2.0)[:3])
print("capped: CPU % of one core:", spin(3.0), "(16 logical cores: 2 % of machine = 32 % of one core)")

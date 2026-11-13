"""Import this FIRST in any research script run while the live session is up (13 Nov):
idle CPU priority (the live engine and feed run above normal and always win) and one math thread."""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_k] = "1"
try:
    import ctypes
    _k32 = ctypes.windll.kernel32
    _k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    _k32.SetPriorityClass(_k32.GetCurrentProcess(), 0x00004000)      # BELOW_NORMAL: yields to the engine (above
    # normal) and to every normal-priority program; idle class starved under the 13 Nov machine load (87 % CPU)
except Exception:
    pass

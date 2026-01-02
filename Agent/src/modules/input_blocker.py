import ctypes
import time
import sys

user32 = ctypes.WinDLL("user32", use_last_error=True)

# -------- BlockInput --------
BlockInput = user32.BlockInput
BlockInput.argtypes = [ctypes.c_bool]
BlockInput.restype = ctypes.c_bool

# -------- ClipCursor --------
ClipCursor = user32.ClipCursor
ClipCursor.argtypes = [ctypes.c_void_p]
ClipCursor.restype = ctypes.c_bool

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

def block_input_for(seconds: int):
    rect = RECT(0, 0, 1, 1)

    if not BlockInput(True):
        print("[-] BlockInput failed (run as admin)")
        sys.exit(1)

    try:
        print(f"[+] Input blocked for {seconds} seconds")

        end_time = time.time() + seconds
        while time.time() < end_time:
            # Re-apply mouse confinement every second
            ClipCursor(ctypes.byref(rect))
            time.sleep(1)

    finally:
        # ALWAYS restore input
        ClipCursor(None)
        BlockInput(False)
        print("[+] Input fully restored")

if __name__ == "__main__":
    block_input_for(30)



### block input evry second is needed to add same like clipsursor

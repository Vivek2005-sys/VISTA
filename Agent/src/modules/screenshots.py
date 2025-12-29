
import threading
import time
from datetime import datetime
from mss import mss
from PIL import Image
from io import BytesIO
import os
from uuid import uuid4

# Global
_capture_thread = None
_running = False
_last_thumbnail = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "ss")

# SCREENSHOT_DIR = "screenshots"
INTERVAL = 1.0  # seconds
SESSION_ID = uuid4().hex[:6].upper()


def _capture_loop():
    global _last_thumbnail, _running

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with mss() as sct:
        monitor = sct.monitors[0]  # SAFE: all screens

        while _running:
            t_start = time.monotonic()

            try:
                frame = sct.grab(monitor)
                img = Image.frombytes("RGB", frame.size, frame.rgb)

                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename = f"{timestamp}_{SESSION_ID}.jpg"
                path = os.path.join(SCREENSHOT_DIR, filename)

                img.save(path, "JPEG", quality=80, subsampling=2)

                #thumbnail
                thumb = img.resize((500, 350))
                buf = BytesIO()
                thumb.save(buf, "JPEG", quality=50)
                _last_thumbnail = buf.getvalue()

            except Exception as e:
                print(f"Screenshot error: {e}")

           
            elapsed = time.monotonic() - t_start
            time.sleep(max(0, INTERVAL - elapsed))


def start():
    global _capture_thread, _running

    if _running:
        return False

    _running = True
    _capture_thread = threading.Thread(
        target=_capture_loop,
        name="ScreenshotThread",
        daemon=True,
    )
    _capture_thread.start()
    print("Screenshot module started")
    return True


def stop():
    global _running, _capture_thread

    if not _running:
        return False

    _running = False
    if _capture_thread:
        _capture_thread.join(timeout=3)
    print("Screenshot module stopped")
    return True


def get_thumbnail():
    return _last_thumbnail or b""


if __name__ == "__main__":
    start()
    print("Running... Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop()


# ┌─────────────────┐
# │   SCRIPT START  │  (if __name__ == "__main__")
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ start()         │  ← Set _running=True
# │ - Check not     │  (if already? Return False)
# │   running       │
# │ - Spawn thread  │  (_capture_loop, daemon=True)
# │   (daemon)      │  Prints "Screenshot module started"
# └─────────┬───────┘
#           │ Success (returns True)
#           ▼
# ┌─────────────────┐
# │ Print "Running..│  Ctrl+C to stop"
# │ . Ctrl+C prompt │
# └─────────┬───────┘
#           │
#           ▼  [Infinite Idle Loop]
# ┌─────────────────┐  (while True: time.sleep(1) — low CPU wait)
# │ Wait Forever    │
# │ (sleep 1s)      │
# └─────────┬───────┘
#           │
#           ▼  [Ctrl+C / KeyboardInterrupt]
# ┌─────────────────┐
# │ stop()          │  ← Set _running=False (loop exits)
# │ - Check running │  (if not? Return False)
# │ - Join thread   │  (wait 3s max—graceful end)
# │   (3s timeout)  │  Prints "Screenshot module stopped"
# └─────────┬───────┘
#           │ Success (returns True)
#           ▼
# ┌─────────────────┐
# │   SCRIPT END    │  (Clean exit; daemon thread auto-dies)
# └─────────────────┘
#           ↑
#           │ [Background: _capture_loop Thread Runs Parallel]
#           │
# ┌─────────────────┐  (While _running: Every exact INTERVAL=1s)
# │ _capture_loop   │
# │ - Make "ss" dir │  (os.makedirs once)
# │ - mss instance  │
# │ - Grab monitor[0]│  (auto full/all screens)
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Start Timer     │  t_start = time.monotonic() (precise, no drift)
# │ (monotonic)     │
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Grab Frame      │  sct.grab(monitor) → raw RGB pixels
# │ (mss.grab)      │
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Convert to PIL  │  Image.frombytes("RGB", size, rgb)
# │ Image           │
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Save Full-Res   │  timestamp = YYYY-MM-DD_HHMMSS
# │ JPG             │  filename = timestamp + SESSION_ID + .jpg
# │ (quality=80)    │  path = "ss/filename.jpg"
# │ subsampling=2   │  img.save(path, JPEG, 80) (~200KB)
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Make Thumbnail  │  thumb = img.resize((500, 350))
# │ (500x350)       │  buf = BytesIO()
# │ Compress        │  thumb.save(buf, JPEG, quality=50) (~20KB)
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Update Global   │  _last_thumbnail = buf.getvalue() (bytes ready)
# │ _last_thumbnail │
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ Handle Error?   │  try/except: Print e, continue (no crash)
# │ (try/except)    │
# └─────────┬───────┘
#           │
#           ▼
# ┌─────────────────┐
# │ End Timer &     │  elapsed = monotonic() - t_start
# │ Sleep Remainder │  sleep(max(0, INTERVAL - elapsed)) — exact 1s
# └───────────────┐
#                │ Loop back to Grab (while _running)
#                ▼
# [stop() sets _running=False → Loop exits naturally]
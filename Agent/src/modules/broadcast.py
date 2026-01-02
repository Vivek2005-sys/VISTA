import os
import tkinter as tk
from PIL import Image, ImageTk

# =========================
# CONFIG
# =========================
IMAGE_DIR = r"C:\coding\FP Project\images"
CHANGE_INTERVAL_MS = 1000  # 1 second

# =========================
# LOAD IMAGE PATHS
# =========================
image_files = [
    os.path.join(IMAGE_DIR, f)
    for f in sorted(os.listdir(IMAGE_DIR))
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
]

if not image_files:
    raise RuntimeError("No images found in folder")

# =========================
# TK WINDOW SETUP
# =========================
root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg="black")
root.bind("<Escape>", lambda e: root.destroy())  # emergency exit

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

label = tk.Label(root, bg="black")
label.pack(fill="both", expand=True)

# =========================
# IMAGE CACHE
# =========================
cached_images = []

for path in image_files:
    img = Image.open(path).convert("RGB")
    img = img.resize((screen_w, screen_h), Image.LANCZOS)
    cached_images.append(ImageTk.PhotoImage(img))

# =========================
# IMAGE ROTATION
# =========================
index = 0

def show_next_image():
    global index
    label.config(image=cached_images[index])
    index = (index + 1) % len(cached_images)
    root.after(CHANGE_INTERVAL_MS, show_next_image)

# =========================
# START
# =========================
show_next_image()
root.mainloop()

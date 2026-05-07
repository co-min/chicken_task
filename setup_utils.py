import os
import tkinter as tk
from datetime import datetime
from psychopy import visual, monitors, gui, core
import ctypes

from config import (
    WIDTH, HEIGHT, BG_COLOR, FULLSCREEN, FORCE_WINDOWED_MODE,
    AUTO_DETECT_WINDOW_SIZE, MONITOR_NAME, MONITOR_WIDTH_CM, MONITOR_DISTANCE_CM,
)


def get_subject_id() -> str:
    while True:
        subject_id = input("피험자 ID 입력 (예: P001): ").strip()
        if subject_id:
            return subject_id
        print("ID를 입력해주세요.")



def create_save_dir(subject_id: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data')
    save_dir = os.path.join(base, f"{subject_id}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def create_window() -> visual.Window:
    fallback = [WIDTH, HEIGHT]
    screen_size = _detect_screen_size(fallback) if AUTO_DETECT_WINDOW_SIZE else fallback
    win_size = [min(WIDTH, screen_size[0]), min(HEIGHT, screen_size[1])]

    monitor = monitors.Monitor(
        MONITOR_NAME,
        width=MONITOR_WIDTH_CM,
        distance=MONITOR_DISTANCE_CM,
    )
    monitor.setSizePix(screen_size)

    win = visual.Window(
        size=win_size,
        color=[c / 255 for c in BG_COLOR],
        colorSpace='rgb',
        fullscr=FULLSCREEN and not FORCE_WINDOWED_MODE,
        screen=1,
        monitor=monitor,
        units='pix',
        allowGUI=True,
    )
    win.mouseVisible = True
    return win


def _detect_screen_size(fallback_size):
    try:
        root = tk.Tk()
        root.withdraw()
        logical_w = root.winfo_screenwidth()
        logical_h = root.winfo_screenheight()
        root.destroy()

        # tkinter returns logical pixels even when SetProcessDpiAwareness(1) is active,
        # because Tcl/Tk has its own DPI layer. Query GDI for the true DPI and scale up
        # to physical pixels, which is what PsychoPy (and Win32) expect.
        try:
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            scale = dpi / 96.0
        except Exception:
            scale = 1.0

        return [int(logical_w * scale), int(logical_h * scale)]
    except Exception:
        return list(fallback_size)

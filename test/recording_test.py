from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ctypes
from ctypes import wintypes
import win32process
import win32gui
import psutil
import time
import signal
import subprocess
import os
profile_path = r"firefox_profiles\psxoje5e.default-release-2"
ff_profile = FirefoxProfile(profile_path)

firefox_options = Options()
firefox_options.add_argument("--start-maximized")

# firefox_options.add_argument("--headless")  # remove if you want to see browser
firefox_options.profile = ff_profile

driver = webdriver.Firefox(options=firefox_options)   


pid=driver.service.process.pid
recording_process=None
#children = psutil.Process(pid).children(recursive=True)
#firefox_pid = children[0].pid
print(pid)

driver.get("https://discord.com/app")


def get_firefox_hwnd_from_driver(driver):
    """Find the main Firefox window handle from a Selenium Firefox driver."""
    time.sleep(2)  # give time for window to appear

    # Step 1: find all firefox.exe children spawned by geckodriver
    gecko_pid = driver.service.process.pid
    parent = psutil.Process(gecko_pid)
    hwnds = []

    for child in parent.children(recursive=True):
        if "firefox" in child.name().lower():
            pid = child.pid

            def callback(hwnd, _):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    title = win32gui.GetWindowText(hwnd)
                    if title.strip():  # only keep visible windows with titles
                        hwnds.append((hwnd, title))

            win32gui.EnumWindows(callback, None)
    
    # Step 2: try fallback with EnumChildWindows (hidden/nested)
    if not hwnds:
        def child_cb(hwnd, _):
            try:
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid in [c.pid for c in parent.children(recursive=True)]:
                    title = win32gui.GetWindowText(hwnd)
                    if title.strip():
                        hwnds.append((hwnd, title))
            except Exception:
                pass
        win32gui.EnumChildWindows(None, child_cb, None)
    
    return hwnds

def pick_main_firefox_window(hwnds):
    print(hwnds)
    for hwnd, title in hwnds:
        if "firefox" in title.lower() and "discord" in title.lower():
            return hwnd
    for hwnd, title in hwnds:
        if "firefox" in title.lower():
            return hwnd
    return None

def start_recording():
    global recording_process

    all_hwnds = get_firefox_hwnd_from_driver(driver)
    discord_hwnd = pick_main_firefox_window(all_hwnds)
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "gdigrab",
        "-framerate", "30",
        "-i", f"hwnd={discord_hwnd}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        'test.mp4'
    ]
    recording_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_recording(BOT_ID=0):
    global recording_process
    if recording_process is None:
        print(f"[{BOT_ID}] No recording in progress")
        return

    print(f"[{BOT_ID}] Stopping recording...")

    # Try graceful termination first
    try:
        recording_process.send_signal(signal.CTRL_BREAK_EVENT)  # safer than terminate on Windows
        recording_process.wait(timeout=5)
    except Exception:
        # Force kill if FFmpeg doesn’t respond
        print(f"[{BOT_ID}] Graceful stop failed, forcing terminate")
        recording_process.kill()
        recording_process.wait()

    # Convert MKV → MP4 safely without re-encoding
    mkv_file = recording_process.mkv_file
    mp4_file = recording_process.mp4_target
    print(f"[{BOT_ID}] Converting MKV → MP4: {mp4_file}")
    

    # Remove intermediate MKV
    os.remove(mkv_file)
    recording_process = None
    print(f"[{BOT_ID}] Recording complete")


start_recording()

time.sleep(10)

stop_recording()
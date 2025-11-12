import redis
import json
import os
import datetime
import subprocess
import time
import get_bot_id
import signal
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
import argparse
parser = argparse.ArgumentParser(description="Screen share recording bot")
parser.add_argument(
    "--profile-path",
    required=True,
    help="Full path to the Firefox profile for this bot (e.g. C:\\Users\\You\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\abc123.default-release)"
)
args = parser.parse_args()
# -------------------------------
# Firefox setup
# -------------------------------
profile_path = args.profile_path
ff_profile = FirefoxProfile(profile_path)
BOT_ID = get_bot_id.get_bot_id_from_firefox_profile(profile_path)

firefox_options = Options()
firefox_options.add_argument("--start-maximized")

# firefox_options.add_argument("--headless")  # remove if you want to see browser
firefox_options.profile = ff_profile

driver = webdriver.Firefox(options=firefox_options)   


pid=driver.service.process.pid

#children = psutil.Process(pid).children(recursive=True)
#firefox_pid = children[0].pid
print(pid)
wait = WebDriverWait(driver, 5)
driver.get("https://discord.com/app")



REDIS_HOST = "localhost"
REDIS_PORT = 6379
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

recording_process = None





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



def get_discord_user_id(driver):
    
    # This fetches your own user ID via localStorage trick
    script = "return window.localStorage.getItem('user_id_cache');"
    return driver.execute_script(script)
def start_recording(driver, BOT_ID,channel_member):
    global recording_process
    if recording_process is not None:
        print(f"[{BOT_ID}] Already recording")
        return

    # Find all Firefox windows
    all_hwnds = get_firefox_hwnd_from_driver(driver)
    discord_hwnd = pick_main_firefox_window(all_hwnds)
    if discord_hwnd is None:
        print(f"[{BOT_ID}] No suitable Firefox window found")
        return

    # Prepare filenames
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = os.path.join("recordings", BOT_ID)
    os.makedirs(folder_path, exist_ok=True)
    mkv_filename = os.path.join(folder_path, f"{channel_member}_{now_str}_stream.mkv")
    mp4_filename = os.path.join(folder_path, f"{channel_member}_{now_str}_stream.mp4")

    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "gdigrab",
        "-framerate", "30",
        "-i", f"hwnd={discord_hwnd}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        mp4_filename
    ]

    print(f"[{BOT_ID}] Starting recording: {mkv_filename}")

    # Start FFmpeg asynchronously
    recording_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    recording_process.mkv_file = mkv_filename
    recording_process.mp4_target = mp4_filename

def stop_recording(BOT_ID):
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
    subprocess.run(["ffmpeg", "-y", "-i", mkv_file, "-c", "copy", mp4_file])

    # Remove intermediate MKV
    os.remove(mkv_file)
    recording_process = None
    print(f"[{BOT_ID}] Recording complete")



# -------------------------------
# Discord actions
# -------------------------------
def click_server(server_name):
    server_elem = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//span[@class='hiddenVisually__27f77' and text()='{server_name}']")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", server_elem)
    driver.execute_script("arguments[0].click();", server_elem)

def click_channel(server, channel,member):
    full_name = f"{channel} / {server}"
    channel_elem = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{full_name}')]"))
    )
    channel_elem.click()
    print(f"[{BOT_ID}] Clicked channel element")
    time.sleep(2)

    stream_elem = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='Watch Stream']"))
    )
    stream_elem.click()
    print(f"[{BOT_ID}] Clicked Watch Stream")
    time.sleep(2)

    start_recording(BOT_ID=BOT_ID,driver=driver,channel_member=member)

# -------------------------------
# Command handler
# -------------------------------
def handle_command(cmd: str):
    print(f"[{BOT_ID}] Received command: {cmd}")

    try:
        data = json.loads(cmd)
        action = data.get("action")
    except Exception:
        action = cmd.strip().lower()
        data = {}

    if action == "click_channel":
        click_channel(data.get("server"), data.get("channel"),data.get("member"))
        
    elif action == "record_start":
        start_recording(BOT_ID=BOT_ID,driver=driver)
    elif action == "record_stop":
        stop_recording(BOT_ID)
    else:
        print(f"[{BOT_ID}] Unknown action: {action}")

    # ACK back to Redis
    r.rpush(f"acks:{BOT_ID}", json.dumps({
        "status": "ok",
        "action": action,
        "timestamp": datetime.datetime.now().isoformat()
    }))

# -------------------------------
# Main loop
# -------------------------------
import time
def main():
    
    
    print(f"[{BOT_ID}] Listening for commands...")

    hwnds=get_firefox_hwnd_from_driver(driver)
    print(pick_main_firefox_window(hwnds))

    while True:
        _, cmd = r.brpop(f"tasks:{BOT_ID}")  # blocks until command arrives
        handle_command(cmd)

if __name__ == "__main__":
    main()

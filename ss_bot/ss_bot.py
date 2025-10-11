import redis
import json
import os
import datetime
import subprocess
import time
import get_bot_id
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------------
# Firefox setup
# -------------------------------
profile_path = r"C:\Users\Jake\Documents\GitHub\SS_selfbot\firefox_profiles\psxoje5e.default-release-2"
ff_profile = FirefoxProfile(profile_path)

firefox_options = Options()
firefox_options.add_argument("--start-maximized")
# firefox_options.add_argument("--headless")  # remove if you want to see browser
firefox_options.profile = ff_profile

driver = webdriver.Firefox(options=firefox_options)
wait = WebDriverWait(driver, 5)
driver.get("https://discord.com/app")

# -------------------------------
# Redis setup (optional)
# -------------------------------
REDIS_HOST = "localhost"
REDIS_PORT = 6379
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

BOT_ID = get_bot_id.get_bot_id_from_firefox_profile(profile_path)
recording_process = None
print(BOT_ID)
# -------------------------------
# Recording functions
# -------------------------------
def get_discord_user_id(driver):
    # This fetches your own user ID via localStorage trick
    script = "return window.localStorage.getItem('user_id_cache');"
    return driver.execute_script(script)

def start_recording():
    global recording_process
    if recording_process is not None:
        print(f"{BOT_ID} already recording")
        return

    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = os.path.join("recordings", BOT_ID)
    os.makedirs(folder_path, exist_ok=True)
    filename = os.path.join(folder_path, f"{now_str}_stream.mp4")

    cmd = [
        "ffmpeg",
        "-y",                # overwrite output
        "-f", "gdigrab",     # capture Windows desktop
        "-framerate", "30",
        "-i", "desktop",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        filename
    ]

    print(f"[{BOT_ID}] Starting recording: {filename}")
    recording_process = subprocess.Popen(cmd)

def stop_recording():
    global recording_process
    if recording_process is None:
        print(f"[{BOT_ID}] No recording in progress")
        return

    print(f"[{BOT_ID}] Stopping recording...")
    recording_process.terminate()
    recording_process.wait()
    recording_process = None

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

def click_channel(server, channel):
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

    start_recording()

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
        click_channel(data.get("server"), data.get("channel"))
        print(get_discord_user_id(driver))
    elif action == "record_start":
        start_recording()
    elif action == "record_stop":
        stop_recording()
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
    print(BOT_ID)
    while True:
        _, cmd = r.brpop(f"tasks:{BOT_ID}")  # blocks until command arrives
        handle_command(cmd)

if __name__ == "__main__":
    main()

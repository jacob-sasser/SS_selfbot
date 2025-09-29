import redis
from time import sleep
import json
import os
import datetime
import subprocess

import atexit
import sys
import signal

import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile


profile_path = "/root/.mozilla/firefox/bn6jv641.test_bot"

ff_profile = FirefoxProfile(profile_path)
firefox_options = Options()
firefox_options.add_argument("--start-maximized")

#firefox_options.add_argument("--headless")  # remove if you want to see browser
firefox_options.profile=ff_profile
driver = webdriver.Firefox(options=firefox_options)

wait = WebDriverWait(driver, 10)
driver.get('https://discord.com/app')
# Connect to Redis (using Docker service name "redis")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

BOT_ID = os.getenv("BOT_ID","1")  # change to bot2, bot3, etc. per container
recording_process=None


def start_recording():
    global recording_process
    if recording_process is not None:
        print(f"{BOT_ID} already recording" )
        return
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = f"recordings/{BOT_ID}"
    os.makedirs(folder_path, exist_ok=True)
    filename = f"{folder_path}/{now_str}_stream.mp4"
    cmd = [
        "ffmpeg",
        "-y",                # overwrite output
        "-f", "x11grab",     # capture X11 screen
        "-s", "1080x1920",   # resolution (change if needed)
        "-i", ":0.0",        # display to grab (:0.0 = default)
        "-r", "15",          # fps
        "-codec:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        filename
    ]
    print(f"[{BOT_ID}] Starting recording: {filename}")
    recording_process = subprocess.Popen(cmd)


def stop_recording():
    """Stop ffmpeg screen recording."""
    global recording_process
    if recording_process is None:
        print(f"[{BOT_ID}] No recording in progress")
        return

    print(f"[{BOT_ID}] Stopping recording...")
    recording_process.terminate()
    recording_process.wait()
    recording_process = None

def upload_recording(recording):
    pass

def click_server(server_name):
    server_elem = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//span[@class='hiddenVisually__27f77' and text()='{server_name}']")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", server_elem)

    driver.execute_script("arguments[0].click();", server_elem)


def click_channel(server,channel):
    full_name=f"{channel} / {server}"
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
    print(f"{BOT_ID} Clicked Watched Stream")


def handle_command(cmd: str):
    """
    Handle commands sent from the head bot.
    Commands should be plain strings or JSON with fields.
    """
    print(f"[{BOT_ID}] Received command: {cmd}")

    try:
        data = json.loads(cmd)
        action = data.get("action")
    except Exception:
        action = cmd.strip().lower()
        data = {}

    if action == "click_channel":
        server = data.get("server")
        channel = data.get("channel")
        click_channel(server, channel)
        time.sleep(5)
        start_recording()
    elif action == "record_stop":
        stop_recording()
    elif action == "record_start":
        start_recording()
    else:
        print(f"[{BOT_ID}] Unknown action: {action}")

    # ✅ Send ACK back to master
    r.rpush(f"acks:{BOT_ID}", json.dumps({
        "status": "ok",
        "action": action,
        "timestamp": datetime.datetime.now().isoformat()
    }))

def main():
    print(f"[{BOT_ID}] Listening for commands...")
    while True:
        _, cmd = r.brpop(f"tasks:{BOT_ID}")  # queue name e.g. tasks:bot1
        handle_command(cmd)

if __name__ == "__main__":
    main()

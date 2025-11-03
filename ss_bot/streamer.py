import redis
import json
import os
import datetime
import subprocess
import time
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import ss_bot

BOT_ID=99
REDIS_PORT=6379
REDIS_HOST = "localhost"

driver=None

recording_process=None

def configure_ff(profile_path: str):
    ff_profile = FirefoxProfile(profile_path)

    firefox_options = Options()
    firefox_options.add_argument("--start-maximized")
    firefox_options.profile = ff_profile

    driver = webdriver.Firefox(options=firefox_options)
    wait = WebDriverWait(driver, 10)
    driver.get("https://discord.com/app")


def start_stream(token_path:str,title,)->str:
    creds=Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/youtube'])
    youtube = build('youtube', 'v3', credentials=creds)

    request=youtube.liveBroadcasts().insert(
        part="snippet,status",
        body={
            "snippet":{
                "title":title,
                "scheduledStartTime": time.time()
            },
            "status":{"privacyStatus":"Unlisted"}
            }
    )
    response=request.execute()
    return response

    

def start_streaming(stream_key:str):
    ff_window_title=driver.title
    if recording_process is None:
        cmd=['ffmpeg',
            '-y',
            'f','gdigrab',
            "-i", ff_window_title,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-an", "-f", "flv", f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
            
        ]
        recording_process = subprocess.Popen(cmd)
    else:
        print("already streaming")




def stop_streaming():
    global recording_process
    if recording_process is None:
        print(f"[{BOT_ID}] No recording in progress")
        return

    print(f"[{BOT_ID}] Stopping stream")
    recording_process.terminate()
    recording_process.wait()
    recording_process = None


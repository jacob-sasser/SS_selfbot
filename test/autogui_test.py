import xvfbwrapper
import os
import pyautogui
from time import sleep

Height=2880
Width=1920
#xvfb=xvfbwrapper.Xvfb(Height,Width,display=12)
voicebox_coordinates=(103,1583)
'''
xvfb.start()

try:
    os.system('discord')
finally:
    pass'''

print(pyautogui.locateOnScreen('test/voice_connected2.png'))

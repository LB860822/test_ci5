#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
from io import BytesIO
from PIL import Image, ImageChops
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time

def get_gap_test(picture0, picture1, picture2):
    position=picture0.getbbox()
    up=position[3]
    bottom=position[1]
    left=position[0]
    right=position[2]

    #diff_position=ImageChops.difference(picture1, picture2).getbbox()
    #diff_left=diff_position[0]
    #diff_right=diff_position[2]

    moved = {}
    for move in range(0,picture0.size[0]-right):
        thisabs=0
        for checkx in range(0,picture0.size[0]):
            for checky in range(bottom,up):
                for checkpixel in range(0,3):
                    if checkx >= move+left and checkx <= move+right:
                        thisabs+=abs(picture0.getpixel((checkx-move,checky))[checkpixel]-picture1.getpixel((checkx,checky))[checkpixel])
                    else :
                        thisabs+=abs(picture2.getpixel((checkx,checky))[checkpixel]-picture1.getpixel((checkx,checky))[checkpixel])
        moved[move]=thisabs

    minmove=0
    minmoved=None
    for move in moved.keys():
        if minmoved is None or minmoved >= moved[move]:
            minmoved=moved[move]
            minmove=move
    print(minmove)
    return minmove

def simpleSimulateDragX(driver, source, targetOffsetX):
    action_chains = ActionChains(driver)
    action_chains.click_and_hold(source)
    action_chains.pause(0.2)
    action_chains.move_by_offset(targetOffsetX, 0)
    action_chains.pause(0.6)
    action_chains.release()
    action_chains.perform()

headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'}

parser = argparse.ArgumentParser()
parser.description='please enter parameters ...'
parser.add_argument('-s', '--search', help='what you want to search', dest='search', type=str, default='lindy')
parser.add_argument('-o', '--output', help='output file', dest='out', type=str, default='hermes.txt')
args = parser.parse_args()

url='https://www.hermes.com/pl/en/search/?s='+args.search+'#||Category'

# Get the Firefox profile object
profile = webdriver.firefox.webdriver.FirefoxProfile()
# Disable images
#profile.set_preference('permissions.default.image', 2)
# Disable Flash
profile.set_preference(
    'dom.ipc.plugins.enabled.libflashplayer.so', 'false'
)
profile.native_events_enabled = True
options = webdriver.firefox.options.Options()
options.headless = True
firefox = webdriver.Firefox(firefox_profile=profile, options=options, timeout=60)
firefox.get(url)

geted = False
errors='unknown errors'
content=''

time.sleep(2)
while 'You have been blocked' in firefox.title:
    print(firefox.title)
    firefox.switch_to.frame(0)
    WebDriverWait(firefox, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='geetest_holder geetest_wind geetest_ready']").is_displayed())
    captcha = firefox.find_element_by_xpath('//div[@class="geetest_holder geetest_wind geetest_ready"]')
    ActionChains(firefox).move_to_element_with_offset(to_element=captcha, xoffset=0, yoffset=1).perform()
    ActionChains(firefox).move_to_element_with_offset(to_element=captcha, xoffset=0, yoffset=2).perform()
    time.sleep(2)
    #with open('source2.txt', 'w') as filehermes:
    #    filehermes.write(firefox.page_source)
    WebDriverWait(firefox, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='geetest_holder geetest_wind geetest_wait_compute']").is_displayed())
    compute = firefox.find_element_by_xpath('//div[@class="geetest_holder geetest_wind geetest_wait_compute"]')
    compute.click()
    time.sleep(3)
    WebDriverWait(firefox, 30).until(lambda the_driver: the_driver.find_element_by_xpath("//div[@class='geetest_slider_button']").is_displayed())
    img_info = firefox.execute_script('return document.getElementsByClassName("geetest_canvas_fullbg geetest_fade geetest_absolute")[0].toDataURL("image/png");')
    img_base64 = img_info.split(",")[1]
    img_bytes = base64.b64decode(img_base64)
    picture1 = Image.open(BytesIO(img_bytes))
    img_info = firefox.execute_script('return document.getElementsByClassName("geetest_canvas_bg geetest_absolute")[0].toDataURL("image/png");')
    img_base64 = img_info.split(",")[1]
    img_bytes = base64.b64decode(img_base64)
    picture2 = Image.open(BytesIO(img_bytes))
    img_info = firefox.execute_script('return document.getElementsByClassName("geetest_canvas_slice geetest_absolute")[0].toDataURL("image/png");')
    img_base64 = img_info.split(",")[1]
    img_bytes = base64.b64decode(img_base64)
    picture0 = Image.open(BytesIO(img_bytes))
    gap = get_gap_test(picture0, picture1, picture2)
    slider = firefox.find_element_by_xpath('//div[@class="geetest_slider_button"]')
    simpleSimulateDragX(firefox, slider, gap)
    firefox.switch_to_default_content()
    time.sleep(30)
    if 'You have been blocked' in firefox.title:
        firefox.refresh()

subtitles = firefox.find_elements_by_xpath('//div[@class="sub-title"]')
if len(subtitles) == 0:
    geted = True
else:
    errors=subtitles[0].text
    print(errors)
maintitles = firefox.find_elements_by_xpath('//div[@class="main-title"]')
if len(maintitles) > 0:
    content=maintitles[0].text
    print(content)
else:
    print('no main-title')
    geted = False
with open(args.out, 'w') as filehermes:
    filehermes.write(content+'\n'+url)

firefox.close()
firefox.quit()

if not geted:
    raise Exception(errors)

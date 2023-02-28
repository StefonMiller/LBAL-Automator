from PIL import Image
from pytesseract import pytesseract
import pyautogui
from pywinauto import Application
from pywinauto import findwindows
import win32gui
import time
import os
import cv2
import numpy as np

def mse(img1, img2):
   h, w = img1.shape
   diff = cv2.subtract(img1, img2)
   err = np.sum(diff**2)
   mse = err/(float(h*w))
   return mse

def compare_images(path1, path2):
    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    error = mse(img1, img2)
    print(error)
    return error < 2

def get_text_from_image(path):
    # Opening the image & storing it in an image object
    img = Image.open(path)

    # Providing the tesseract executable
    # location to pytesseract library
    pytesseract.tesseract_cmd = path_to_tesseract

    # Passing the image object to image_to_string() function
    # This function will extract the text from the image
    text = pytesseract.image_to_string(img)

    # Displaying the extracted text
    return text[:-1]


# Defining paths to tesseract.exe
# and the image we would be using
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Screen locations are for 1920x1080 w/ 200% UI/text scaling
wh = pyautogui.size()
curr_screen_width = wh.width
curr_screen_height = wh.height

print(f'Current screen width: {curr_screen_width}\nCurrent screen height: {curr_screen_height}')


# Can be used for both email and symbol/item addition
header_start_x = (119 / 1920) * curr_screen_width
header_start_y = (137 / 1080) * curr_screen_height
header_end_x = (1796 / 1920) * curr_screen_width
header_end_y = (223 / 1080) * curr_screen_height

spin_start_x = (0 / 1920) * curr_screen_width
spin_start_y = (924 / 1080) * curr_screen_height
spin_end_x = (1920 / 1920) * curr_screen_width
spin_end_y = (1080 / 1080) * curr_screen_height

coins_start_x = (113 / 1920) * curr_screen_width
coins_start_y = (43 / 1080) * curr_screen_height
coins_end_x = (260 / 1920) * curr_screen_width
coins_end_y = (129 / 1080) * curr_screen_height

item1_start_x = (151 / 1920) * curr_screen_width
item1_start_y = (336 / 1080) * curr_screen_height
item1_end_x = (669 / 1920) * curr_screen_width
item1_end_y = (410 / 1080) * curr_screen_height

item2_start_x = (700 / 1920) * curr_screen_width
item2_start_y = (336 / 1080) * curr_screen_height
item2_end_x = (1212 / 1920) * curr_screen_width
item2_end_y = (410 / 1080) * curr_screen_height

item3_start_x = (1248 / 1920) * curr_screen_width
item3_start_y = (336 / 1080) * curr_screen_height
item3_end_x = (1759 / 1920) * curr_screen_width
item3_end_y = (410 / 1080) * curr_screen_height

spin_button_x = (962 / 1920) * curr_screen_width
spin_button_y = (1015 / 1080) * curr_screen_height

skip_button_x = (965 / 1920) * curr_screen_width
spin_button_y = (284 / 1080) * curr_screen_height

retry_button_x = (955 / 1920) * curr_screen_width
retry_button_y = (909 / 1080) * curr_screen_height

email_button_x = (960 / 1920) * curr_screen_width
email_button_y = (968 / 1080) * curr_screen_height

pay_button_x = (950 / 1920) * curr_screen_width
pay_button_y = (985 / 1080) * curr_screen_height


hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')

win32gui.SetForegroundWindow(hwnd)
win32gui.ShowWindow(hwnd, 9)

time.sleep(.5)
# 
p = pyautogui.screenshot(region=(header_start_x, header_start_y, (header_end_x - header_start_x), (header_end_y - header_start_y)))
p.save(r'temp.png')

print(pyautogui.position())




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

# Can be used for both email and symbol/item addition
header_start_x = 119
header_start_y = 137
header_end_x = 1796
header_end_y = 223

spin_start_x = 0
spin_start_y = 924
spin_end_x = 1920
spin_end_y = 1080

coins_start_x = 113
coins_start_y = 43
coins_end_x = 260
coins_end_y = 129

item1_start_x = 151
item1_start_y = 336
item1_end_x = 669
item1_end_y = 410

item2_start_x = 700
item2_start_y = 336
item2_end_x = 1212
item2_end_y = 410

item3_start_x = 1248
item3_start_y = 336
item3_end_x = 1759
item3_end_y = 410

spin_button_x = 962
spin_button_y = 1015

skip_button_x = 965
spin_button_y = 284

retry_button_x = 955
retry_button_y = 909

email_button_x = 960
email_button_y = 968

pay_button_x = 950
pay_button_y = 985+


hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')

win32gui.SetForegroundWindow(hwnd)
win32gui.ShowWindow(hwnd, 9)

time.sleep(.5)

p = pyautogui.screenshot(region=(header_start_x, header_start_y, (header_end_x - header_start_x), (header_end_y - header_start_y)))
p.save(r'temp.png')

print(pyautogui.position())




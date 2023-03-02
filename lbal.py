from PIL import Image
# from pytesseract import pytesseract
import pyautogui
from pywinauto import Application
from pywinauto import findwindows
from pywinauto import mouse
import win32gui
import time
import os
import cv2
import math
import numpy as np

class Game:
  spins = [5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10]
  payments = [25, 50, 100, 150, 225, 300, 350, 425, 575, 625, 675, 777, 1000]
  priority_items = ['Flower', 'Bee', 'Rain', 'Coal', 'Seed', 'Farmer', 'Sun', 'Beehive', 'Honey']
  def __init__(self):
    self.payment_num = 0
    self.coins = 0
    self.symbols = ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower']


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

# Determine where we currently are
def current_screen(i):
    p = pyautogui.screenshot()
    p.save(rf'debug\temp{i}.png')
    spin = pyautogui.locateOnScreen(r'cur\spin.png')
    if spin:
        print('Found spin button')
        pyautogui.moveTo(int(spin.left + (spin.width/2)), int(spin.top + (spin.height / 2)))
        pyautogui.click()
        return
    skip = pyautogui.locateOnScreen(r'cur\skip.PNG')
    if skip:
        print('Found skip button')
        pyautogui.moveTo(int(skip.left + (skip.width/2)), int(skip.top + (skip.height / 2)))
        pyautogui.click()
        return
    check = pyautogui.locateOnScreen(r'cur\check.PNG')
    if check:
        print('Found check button')
        pyautogui.moveTo(int(check.left + (check.width/2)), int(check.top + (check.height / 2)))
        pyautogui.click()
        return
    start = pyautogui.locateOnScreen(r'cur\start.PNG')
    if check:
        print('Found start button')
        pyautogui.moveTo(int(start.left + (start.width/2)), int(start.top + (start.height / 2)))
        pyautogui.click()
        return
    retry = pyautogui.locateOnScreen(r'cur\retry.PNG')
    if retry:
        print('Found retry button')
        pyautogui.moveTo(int(retry.left + (retry.width/2)), int(retry.top + (retry.height / 2)))
        pyautogui.click()
        return

    print('No match found')
    

# Defining paths to tesseract.exe
# and the image we would be using
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Screen locations are for 1920x1080 w/ 200% UI/text scaling
wh = pyautogui.size()
curr_screen_width = wh.width
curr_screen_height = wh.height

print(f'Current screen width: {curr_screen_width}\nCurrent screen height: {curr_screen_height}')



# hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
# rect = win32gui.GetWindowRect(hwnd)
# window_x = rect[0] + 45
# window_y = rect[1] + 45
# win32gui.SetForegroundWindow(hwnd)
# win32gui.ShowWindow(hwnd, 9)
# time.sleep(.5)
# i = 0
# while(1):
#     pyautogui.moveTo(window_x, window_y)
#     current_screen(i)
#     time.sleep(1.5)
#     i = i +1
#     print('\n-------------------------------------------------------------------------------------------------------\n')
# win32gui.ShowWindow(hwnd, 6)


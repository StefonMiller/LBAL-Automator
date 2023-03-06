from PIL import Image
import pytesseract
# from pytesseract import pytesseract
import pyautogui
from pywinauto import Application
from pywinauto import findwindows
from pywinauto import mouse
import win32gui
import time
import os
import cv2
import json
import math
import numpy as np
from scipy import ndimage
import pylab as pl
from imutils.object_detection import non_max_suppression
from PIL import Image
import logging
import difflib

class Game:
    spins = [5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10]
    payments = [25, 50, 100, 150, 225, 300, 350, 425, 575, 625, 675, 777, 1000]
    priority_symbols = ['Flower', 'Bee', 'Rain', 'Coal', 'Seed', 'Farmer', 'Sun', 'Beehive', 'Honey', '(@oy-} |']

    def __init__(self):
        self.payment_num = 0
        self.coins = 0
        self.symbols = ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower']
        self.spins_remaining = self.spins[self.payment_num]
        self.gold_per_spin = 5
        self.all_symbols = json.load(open(r'symbols.json'))
        self.all_items = json.load(open(r'items.json'))

    def choose_symbol(self, symbols):
        logging.info('Options:')
        syms = self.all_symbols.keys()
        priority_options = {}
        for sym_name in symbols:
            sym = difflib.get_close_matches(sym_name, syms)[0]
            logging.info(f'\t{sym}: {self.all_symbols[sym]} gold')
            if sym in self.priority_symbols:
                logging.info(f'\t^Priority item, should take this')
                priority_options[sym] = sym_name
        # Grab most valuable priority option
        if len(priority_options.keys()) > 0:
            logging.info("We have priority options, should take one of these")
            cur_g = 0
            cur_sym = ''
            for option in priority_options.keys():
                if self.all_symbols[option] > cur_g:
                    cur_sym = option
                    cur_g = self.all_symbols[option]
            logging.info(f'SELECTION: {cur_sym}')
            self.symbols.append(cur_sym)
            self.gold_per_spin = self.gold_per_spin + self.all_symbols[cur_sym]
            return symbols.index(priority_options[cur_sym])
        else:
            logging.info('No priority symbol options. Checking if we are falling behind on rent')
            expected_gold = (self.coins + self.spins[self.payment_num] * self.gold_per_spin)
            if expected_gold >= self.payments[self.payment_num]:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payments[self.payment_num]}. Not adding symbol')
                return 0
            else:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payments[self.payment_num]}. Need to add one of these symbols')
                cur_g = 0
                cur_sym = ''
                res = {}
                for sym_name in symbols:
                    sym = difflib.get_close_matches(sym_name, syms)[0]
                    res[sym] = sym_name
                    if self.all_symbols[sym] > cur_g:
                        cur_g = self.all_symbols[sym]
                        cur_sym = sym
                logging.info(f'SELECTION: {cur_sym}')
                self.symbols.append(cur_sym)
                self.gold_per_spin = self.gold_per_spin + self.all_symbols[cur_sym]
                return symbols.index(res[cur_sym])            
    def choose_item(self, items):
        logging.info('Options:')
        itms = self.all_items.keys()
        cur_priority = 0
        cur_itm = ''
        item_names = {}
        for itm in items:
            match = difflib.get_close_matches(itm, itms)
            if len(match) > 0:
                match = match[0]
                item_names[match] = itm
                logging.info(f'\t{match}: {self.all_items[match]} priority')
                if self.all_items[match] > cur_priority:
                    cur_priority = self.all_items[match]
                    cur_itm = match
            else:
                name = itm.split(' ')
                name.reverse()
                name = ' '.join(name)
                match = difflib.get_close_matches(name, itms)
                if len(match) > 0:
                    match = match[0]
                    item_names[match] = itm
                    logging.info(f'\t{match}: {self.all_items[match]} priority')
                    if self.all_items[match] > cur_priority:
                        cur_priority = self.all_items[match]
                        cur_itm = match
                else:
                    item_names[''] = ''
        logging.info(f'Found best item based on priority. SELECTING {cur_itm}')
        if cur_itm == '':
            return 1
        else:
            return items.index(item_names[cur_itm])

    def spin(self):
        if self.spins_remaining < 1:
            # Subtract rent payment
            self.coins = self.coins - self.payments[self.payment_num]
            # Increment payment number
            self.payment_num = self.payment_num + 1
            self.spins_remaining = self.spins[self.payment_num] - 1
            # Add coins from spin
            self.coins = self.coins + self.gold_per_spin - 1

        else:
            self.spins_remaining = self.spins_remaining - 1
            self.coins = self.coins + self.gold_per_spin - 1

    def __str__(self):
        return f"Spins til payment: {self.spins_remaining}\nCurrent payment: {self.payments[self.payment_num]}\nGold/spin: {self.gold_per_spin}\nSymbols: {self.symbols}\nCoins: {self.coins}"

    

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
    logging.info(error)
    return error < 2

def crop_image_to_text(img_path, i, n):
    image = cv2.imread(img_path)

    # image height and width should be multiple of 32
    imgWidth=320
    imgHeight=320

    orig = image.copy()
    (H, W) = image.shape[:2]
    (newW, newH) = (imgWidth, imgHeight)

    rW = W / float(newW)
    rH = H / float(newH)
    image = cv2.resize(image, (newW, newH))

    (H, W) = image.shape[:2]

    net = cv2.dnn.readNet(r"frozen_east_text_detection.pb")

    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
                             (123.68, 116.78, 103.94), swapRB=True, crop=False)
    outputLayers = []
    outputLayers.append("feature_fusion/Conv_7/Sigmoid")
    outputLayers.append("feature_fusion/concat_3")
    net.setInput(blob)
    output = net.forward(outputLayers)
    scores = output[0]
    geometry = output[1]
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            # if our score does not have sufficient probability, ignore it
            if scoresData[x] < 0.5:
                continue

            # compute the offset factor as our resulting feature maps will
            # be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
    boxes = non_max_suppression(np.array(rects), probs=confidences)
    # loop over the bounding boxes
    ims = []
    for (startX, startY, endX, endY) in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # draw the bounding box on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
        im = Image.open(img_path)
        im2 = im.crop((startX - 5, startY - 5, endX + 5, endY + 5))
        im2.save(rf'tmp\iter_{i}_sym_{n}_cropped_{len(ims)}.png')
        ims.append(f'tmp\iter_{i}_sym_{n}_cropped_{len(ims)}.png')
    return ims 

def get_coins():
    coin = pyautogui.locateOnScreen(r'cur\coin.PNG')
    if coin:
        p = pyautogui.screenshot(region=((coin.left + coin.width), (coin.top), 80, coin.height - 10))
        p.save(r'tmp\coins.png')
        text = get_text_from_image(r'tmp\coins.png', 0, 0, True)
        return text

def get_text_from_image(path, i, n, param):
    ims = crop_image_to_text(path, i, n)
    text_segments = []
    for im in ims:
        # Opening the image & storing it in an image object
        img = Image.open(im)
        # Providing the tesseract executable
        # location to pytesseract library
        pytesseract.tesseract_cmd = path_to_tesseract

        # Passing the image object to image_to_string() function
        # This function will extract the text from the image
        if param:
            img = img.convert('L')
            text = pytesseract.image_to_string(img, config="--psm 13")
        else:
            text = pytesseract.image_to_string(img)
        if text[:-1] not in text_segments:
            text_segments.append(text[:-1])
    
    text_segments.reverse()
    logging.info(f'Text segments for iteration {i}: {text_segments}')
    return ' '.join(text_segments)

def skip(skip_button):
    pyautogui.moveTo(int(skip_button.left + (skip_button.width/2)), int(skip_button.top + (skip_button.height / 2)))
    pyautogui.click()

# Determine where we currently are
def current_screen(i, cur_game):
    logging.info(cur_game)
    p = pyautogui.screenshot()
    p.save(rf'tmp\iter_{i}_fullscreen.png')
    spin = pyautogui.locateOnScreen(r'cur\spin.png')
    if spin:
        logging.info('Found spin button')
        cur_game.spin()
        pyautogui.moveTo(int(spin.left + (spin.width/2)), int(spin.top + (spin.height / 2)))
        pyautogui.click()
        return
    skip = pyautogui.locateOnScreen(r'cur\skip.PNG')
    if skip:
        if cur_game.coins > 10:
            coins = get_coins()
            print(coins)
            cur_game.coins = int(coins)
        logging.info('Need to select symbol/item')
        sym = pyautogui.locateOnScreen(r'cur\symbol.png')
        if sym:
            symbols = pyautogui.locateAllOnScreen(r'cur\symbol.png')
            symbol_names = []
            symbol_arr = []
            for symbol in symbols:
                p = pyautogui.screenshot(region=((symbol.left), (symbol.top), symbol.width + 10, 150))
                p.save(rf'tmp\iter_{i}_sym_{len(symbol_names)}.png')
                symbol_arr.append(symbol)
                symbol_names.append(get_text_from_image(rf'tmp\iter_{i}_sym_{len(symbol_names)}.png', i, len(symbol_names), False))
            res = cur_game.choose_symbol(symbol_names)
            if res == 0:
                pyautogui.moveTo(int(skip.left + (skip.width/2)), int(skip.top + (skip.height / 2)))
                pyautogui.click()
            else:
                logging.info(f'Selecting symbol index {res}')
                sel_sym = symbol_arr[res]
                pyautogui.moveTo(int(sel_sym.left + (sel_sym.width/2)), int(sel_sym.top + (sel_sym.height/2)))
                pyautogui.click()
        else:
            items = pyautogui.locateAllOnScreen(r'cur\item.png')
            item_names = []
            item_arr = []
            for item in items:
                p = pyautogui.screenshot(region=((item.left), (item.top), item.width + 10, 150))
                p.save(rf'tmp\iter_{i}_itm_{len(item_names)}.png')
                item_arr.append(item)
                item_names.append(get_text_from_image(rf'tmp\iter_{i}_itm_{len(item_names)}.png', i, len(item_names), False))
            res = cur_game.choose_item(item_names)      
            if res == 0:
                pyautogui.moveTo(int(skip.left + (skip.width/2)), int(skip.top + (skip.height / 2)))
                pyautogui.click() 
            else:
                logging.info(f'Selecting item index {res}')
                sel_itm = item_arr[res]
                pyautogui.moveTo(int(sel_itm.left + (sel_itm.width/2)), int(sel_itm.top + (sel_itm.height/2)))
                pyautogui.click()
        return
    pay = pyautogui.locateOnScreen(r'cur\pay.PNG')
    if pay:
        logging.info('Found pay button')
        pyautogui.moveTo(int(pay.left + (pay.width/2)), int(pay.top + (pay.height / 2)))
        pyautogui.click()
        return
    check = pyautogui.locateOnScreen(r'cur\check.PNG')
    if check:
        logging.info('Found check button')
        pyautogui.moveTo(int(check.left + (check.width/2)), int(check.top + (check.height / 2)))
        pyautogui.click()
        return
    floor = pyautogui.locateOnScreen(r'cur\floor.PNG')
    if floor:
        logging.info('Found floor select button')
        pyautogui.moveTo(int(floor.left + (floor.width/2)), int(floor.top + (floor.height / 2)))
        pyautogui.click()
        return
    start = pyautogui.locateOnScreen(r'cur\start.PNG')
    if start:
        logging.info('Found start button')
        pyautogui.moveTo(int(start.left + (start.width/2)), int(start.top + (start.height / 2)))
        pyautogui.click()
        return
    retry = pyautogui.locateOnScreen(r'cur\retry.PNG')
    if retry:
        logging.info('Found retry button')
        pyautogui.moveTo(int(retry.left + (retry.width/2)), int(retry.top + (retry.height / 2)))
        pyautogui.click()
        cur_game = Game()
        return

    logging.info('No match found')
    

# Defining paths to tesseract.exe
# and the image we would be using
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Screen locations are for 1920x1080 w/ 200% UI/text scaling
wh = pyautogui.size()
curr_screen_width = wh.width
curr_screen_height = wh.height

logging.basicConfig(filename='log.txt',
                    filemode='w',
                    format='%(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.info(f'Current screen width: {curr_screen_width}\nCurrent screen height: {curr_screen_height}')

cur_game = Game()
hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
rect = win32gui.GetWindowRect(hwnd)
window_x = rect[0] + 45
window_y = rect[1] + 45
win32gui.SetForegroundWindow(hwnd)
win32gui.ShowWindow(hwnd, 9)
time.sleep(.5)
i = 0
while(1):
    logging.info(f'Iteration {i}')
    pyautogui.moveTo(window_x, window_y)
    current_screen(i, cur_game)
    time.sleep(1.5)
    i = i +1
    logging.info('\n-------------------------------------------------------------------------------------------------------\n')
win32gui.ShowWindow(hwnd, 6)


from PIL import Image
import pyautogui
import win32gui
import time
import os
import cv2
import json
import math
import numpy as np
import logging
import difflib
import re

class Game:
    spins = [5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10]
    payments = [27, 65, 100, 150, 225, 300, 350, 425, 575, 625, 675, 777, 1000]
    priority_symbols = ['Flower', 'Bee', 'Rain', 'Coal', 'Seed', 'Farmer', 'Sun', 'Beehive', 'Honey', 'Bronze Arrow', 'Silver Arrow', 'Golden Arrow', 'Buffing Capsule', 'Item Capsule', 'Lucky Capsule', 'Buffing Capsule', 'Reroll Capsule']
    synergizing_symbols = {'Flower': 1, 'Bee': 2, 'Rain': 2, 'Sun': 5}
    def __init__(self, pm, c, s, sr, gps, als, ai):
        self.payment_num = pm
        self.coins = c
        self.symbols = s
        self.spins_remaining = sr
        self.gold_per_spin = gps
        self.all_symbols = als
        self.all_items = ai

    def choose_symbol(self, symbols):
        logging.info('Options:')
        syms = self.all_symbols.keys()
        priority_options = {}
        for sym_name in symbols:
            sym = difflib.get_close_matches(sym_name, syms)
            if len(sym) > 0:
                sym = sym[0]
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
                if option != '':
                    if self.all_symbols[option] >= cur_g:
                        cur_sym = option
                        cur_g = self.all_symbols[option]
            logging.info(f'OPTIONS: {priority_options}')
            logging.info(f'SELECTION: {cur_sym}')
            if cur_sym != '':
                self.symbols.append(cur_sym)
            self.calculate_gold_per_spin()
            logging.info(f'SELECTION #: {symbols.index(priority_options[cur_sym])}')
            return symbols.index(priority_options[cur_sym])
        else:
            logging.info('No priority symbol options. Checking if we are falling behind on rent')
            logging.info(f'{self.coins} + ({self.spins_remaining} * {self.gold_per_spin}) - {self.spins_remaining}')
            expected_gold = (self.coins + ((self.spins_remaining * self.gold_per_spin) - (self.spins_remaining)))
            if expected_gold >= self.payments[self.payment_num]:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payments[self.payment_num]}. Not adding symbol')
                return -1
            else:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payments[self.payment_num]}. May need to add one of these symbols')
                cur_g = 0
                cur_sym = ''
                res = {}
                for sym_name in symbols:
                    sym = difflib.get_close_matches(sym_name, syms)
                    if len(sym) > 0:
                        sym = sym[0]
                        res[sym] = sym_name
                        if self.all_symbols[sym] >= cur_g:
                            cur_sym = sym
                            cur_g = self.all_symbols[sym]
                if cur_g < 2 and self.payment_num > 2:
                    logging.info(f'After payment 2, cant take any of these symbols bc theyre less than 2g in value')
                    return -1
                elif cur_g < 3 and self.payment_num > 4 and len(self.symbols) > 20:
                    logging.info(f'After payment 4, cant take any symbols less than 3 in value')
                    return -1
                logging.info(f'OPTIONS: {res}')
                logging.info(f'SELECTION: {cur_sym}')
                if cur_sym != '':
                    self.symbols.append(cur_sym)
                    self.calculate_gold_per_spin()
                    logging.info(f'SYMBOL #: {symbols.index(res[cur_sym])}')
                    return symbols.index(res[cur_sym]) 
                return -1
                       
    def choose_item(self, items):
        logging.info('Options:')
        itms = self.all_items.keys()
        cur_priority = 0
        cur_itm = ''
        item_names = {}
        for item_name in items:
            itm = difflib.get_close_matches(item_name, itms)
            if len(itm) > 0:
                itm = itm[0]
                item_names[itm] = item_name
                if self.all_items[itm] >= cur_priority:
                    cur_itm = itm
                    cur_priority = self.all_items[itm]
        logging.info(f'OPTIONS: {item_names}')
        logging.info(f'Found best item based on priority. SELECTING {cur_itm}')
        logging.info(f'ITEM #: {items.index(item_names[cur_itm])}')
        return items.index(item_names[cur_itm])

    def spin(self):
        self.spins_remaining = self.spins_remaining - 1
        self.coins = self.coins + self.gold_per_spin - 1

    def calculate_gold_per_spin(self):
        cur_symbols = {}
        for symb in self.symbols:
            if symb in cur_symbols:
                cur_symbols[symb] = cur_symbols[symb] + 1
            else:
                cur_symbols[symb] = 1
        # Number of spaces
        n = 20
        cur_g = 0
        distinct_symbols = set(cur_symbols.keys())
        for sym in distinct_symbols:
            if sym == 'Flower':
                tmp_symbols = list(i for i in self.synergizing_symbols.keys() if i in distinct_symbols)
                a = cur_symbols[sym]
                tmp_symbols.remove(sym)
                for syn_sym in tmp_symbols:
                    b = cur_symbols[syn_sym]
                    ev = self.synergizing_symbols[syn_sym]
                    matches = (110*a*b)/(n*(n-1))
                    cur_g = cur_g + (matches * ev)
            else:
                cur_g = cur_g + (self.all_symbols[sym] * cur_symbols[sym])
        logging.info(f'Current gold per spin: {cur_g}')
        self.gold_per_spin = cur_g


    def pay_rent(self):
        # Subtract rent payment
        self.coins = self.coins - self.payments[self.payment_num]
        if self.coins < 0:
            self.coins = 0
        # Increment payment number
        self.payment_num = self.payment_num + 1
        self.spins_remaining = self.spins[self.payment_num]

    def update(self, syms):
        logging.info(f'updating symbols to {syms}')
        self.symbols = []
        for sym in syms.keys():
            for i in range(0, syms[sym]):
                self.symbols.append(sym)
        logging.info(f'Symbols: {self.symbols}')
        self.calculate_gold_per_spin()

    # TODO: Fix removal algorithm, may be bc locatecenteronscreen isn't locating the symbol correctly
    def remove_symbols(self, syms):
        hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
        rect = win32gui.GetWindowRect(hwnd)
        window_x = rect[0] + 45
        window_y = rect[1] + 45
        lowest_g = 0  
        self.update(syms)
        while pyautogui.locateCenterOnScreen(r'cur\x.PNG') != None and lowest_g < 3:
            print(f'Current game symbols: {self.symbols}')
            lowest_sym = ''
            for cur_sym in self.symbols:
                print(f'Current symbol for gold value {lowest_g}: {cur_sym} with value {self.all_symbols[cur_sym]}')
                if self.all_symbols[cur_sym] <= lowest_g and cur_sym not in self.priority_symbols and cur_sym in self.symbols:
                    lsp = cur_sym.replace(' ', '_')
                    low_sym_path = rf'cur\Symbols_3x\{lsp}.png'
                    print(f'\t\tFound lowest current non-priority symbol {cur_sym}')
                    lsym = pyautogui.locateCenterOnScreen(low_sym_path)
                    if lsym:
                        pyautogui.moveTo(lsym.x, lsym.y)
                        time.sleep(0.25)
                        pyautogui.moveTo(window_x, window_y)
                        time.sleep(0.25)
                        self.symbols.remove(cur_sym)
                        lowest_sym = cur_sym
                        break
                    else:
                        print('Could not find symbol on screen!')
                        exit(0)
            if lowest_sym == '':
                lowest_g = lowest_g + 1
        exit(0)
        
    def __str__(self):
        return f"Spins til payment: {self.spins_remaining}\nCurrent payment: {self.payments[self.payment_num]}\nGold/spin: {self.gold_per_spin}\nSymbols: {self.symbols}\nCoins: {self.coins}"

def get_coins():
    coin = pyautogui.locateOnScreen(r'cur\coin.PNG')
    if coin:
        segments = 5
        segs = []
        cur_offset = coin.left + coin.width
        for i in range(0, segments):
            p = pyautogui.screenshot(region=(cur_offset, (coin.top + 7), 16, 24))
            img_path = rf'tmp\coins_seg{i}.png'
            p.save(img_path)
            closest_num = find_closest_num(img_path, r'cur\nums\coin_nums')
            # Attempt to recrop segment if template is not a black box and we don't get a valid #
            if not closest_num and p.getbbox():
                # If this image isn't blank and there is no #, try cropping 20px wide
                p = pyautogui.screenshot(region=(cur_offset, (coin.top + 7), 20, 24))
                p.save(img_path)
                closest_num_recropped = find_closest_num(img_path, r'cur\nums\coin_nums')
                if closest_num_recropped:
                    segs.append(closest_num_recropped)
                    cur_offset = cur_offset + 20
            elif closest_num and p.getbbox():
                segs.append(closest_num)
                cur_offset = cur_offset + 16
        coins = int(''.join(segs))
        return coins
    else:
        logging.info('No coin symbol found, returning')
        return None

def find_closest_num(img, path):
    template = cv2.imread(rf'{img}', 0)
    for name in os.listdir(rf'{path}'):
        img = cv2.imread(rf'{path}\{name}', 0)
        conf = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED).max()
        if conf > 0.97:
            return name.replace('.png', '').replace('.PNG', '')
    return None

def get_selections(options, path):
    best_images = []
    for option in options:
        template = cv2.imread(option, 0)
        max_conf = 0
        best_image = ''
        for name in os.listdir(path):
            img = cv2.imread(rf'{path}\{name}', 0)
            conf = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED).max()
            if conf > max_conf:
                max_conf = conf
                best_image = name.replace('.png', '').replace('.PNG', '').replace('_', ' ').replace('ESS', '')
        best_images.append(best_image)
    return best_images

def skip(skip_button):
    pyautogui.moveTo(int(skip_button.left + (skip_button.width/2)), int(skip_button.top + (skip_button.height / 2)))
    pyautogui.click()



def intersected(bottom_left1, top_right1, bottom_left2, top_right2):
    if top_right1[0] < bottom_left2[0] or bottom_left1[0] > top_right2[0]:
        return 0

    if top_right1[1] < bottom_left2[1] or bottom_left1[1] > top_right2[1]:
        return 0

    return 1

def get_symbols():
    items_label = pyautogui.locateOnScreen(r'cur\items_inv.PNG', confidence=0.95)
    payments_label = pyautogui.locateOnScreen(r'cur\payments_inv.PNG', confidence=0.95)
    removal_label = pyautogui.locateOnScreen(r'cur\removal_inv.PNG', confidence=0.95)
    if items_label and payments_label:
        logging.info('Found items and payments label')
        symbols_img = pyautogui.screenshot(region=((items_label.left), (payments_label.top + 50), items_label.width + 850, (items_label.top - (payments_label.top))))
        symbols_img.save(r'tmp\symbols.png')
    elif items_label and removal_label:
        logging.info('Found items and removal label')
        symbols_img = pyautogui.screenshot(region=((items_label.left), (removal_label.top + 50), items_label.width + 850, (items_label.top - (removal_label.top))))
        symbols_img.save(r'tmp\symbols.png')
    elif payments_label:
        logging.info('Found payments label only')
        symbols_img = pyautogui.screenshot(region=(payments_label.left, payments_label.top + 50, payments_label.width + 850, 200))
        symbols_img.save(r'tmp\symbols.png')
    elif removal_label:
        logging.info('Found removal label only')
        symbols_img = pyautogui.screenshot(region=(removal_label.left, removal_label.top + 50, removal_label.width + 750, 200))
        symbols_img.save(r'tmp\symbols.png')
    template = cv2.imread(r'tmp\symbols.png', 1)
    syms = {}
    for name in os.listdir(r'cur\Symbols_3x'):
        img = cv2.imread(rf'cur\Symbols_3x\{name}', 1)
        conf = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where( conf >= 0.97)
        for pt in zip(*loc[::-1]):
            intersection = 0
            matches = []
            for match in matches:
                if intersected(match, (match[0] + 18, match[1] + 18), pt, (pt[0] + 18, pt[1] + 18)):
                    intersection = 1
                    break
            if intersection == 0:
                p = Image.fromarray(template)
                img = p.crop(((pt[0] - 36), pt[1], (pt[0] - 20), (pt[1] + 36)))
                img.save(rf'tmp\tmp_{name}')
                inv_template = cv2.imread(rf'tmp\tmp_{name}', 0)
                for num in os.listdir(r'cur\nums\inv_nums'):
                    img = cv2.imread(rf'cur\nums\inv_nums\{num}', 0)
                    conf = cv2.matchTemplate(img, inv_template, cv2.TM_CCOEFF_NORMED).max()
                    if conf > 0.97:
                        count = int(num.replace('.png', '').replace('.PNG', ''))
                        matches.append(pt)
                        sym_name = name.replace('.png', '').replace('.PNG', '').replace('_', ' ')
                        if sym_name in syms:
                            syms[sym_name] = syms[sym_name] + int(count)
                        else:
                            syms[sym_name] = count
                        break
    return syms
   
def update_symbols(cur_game):
    inv = pyautogui.locateCenterOnScreen(r'cur\inventory.PNG')
    if inv:
        pyautogui.moveTo(inv.x, inv.y)
        pyautogui.click()
        time.sleep(0.5)
        syms = get_symbols()
        cur_game.update(syms)        
    x_button = pyautogui.locateCenterOnScreen(r'cur\x.PNG')
    if x_button:
        pyautogui.moveTo(x_button.x, x_button.y)
        pyautogui.click()

# Determine where we currently are
def current_screen(i, cur_game):
    logging.info(cur_game)
    p = pyautogui.screenshot()
    p.save(rf'tmp\fullscreen.png')
    win = pyautogui.locateOnScreen(r'cur\win.PNG')
    if win:
        logging.info("WON GAME!!!!!!!!")
        exit(0)
    remove = pyautogui.locateCenterOnScreen(r'cur\remove.png')
    # Only remove if we are over max # of symbols
    if remove and len(cur_game.symbols) > 20:
        logging.info(f'Attempting to remove bad symbol as we have {len(cur_game.symbols)}')
        pyautogui.moveTo(remove.x, remove.y)
        pyautogui.click()
        time.sleep(0.5)
        syms = get_symbols()
        cur_game.remove_symbols(syms)  
        return 1
        
    spin = pyautogui.locateOnScreen(r'cur\spin.png')
    if spin:
        logging.info('Found spin button')
        update_symbols(cur_game)
        time.sleep(0.5)
        coins = get_coins()
        if coins:
            cur_game.coins = coins
            logging.info(f'Updated games coin total to {coins}')
        else:
            logging.info('Error parsing coins, not updated')
        exit(0)
        cur_game.spin()
        pyautogui.moveTo(int(spin.left + (spin.width/2)), int(spin.top + (spin.height / 2)))
        pyautogui.click()
        return 1
    skip = pyautogui.locateOnScreen(r'cur\skip.PNG')
    if skip:
        logging.info('Need to select symbol/item')
        sym = pyautogui.locateOnScreen(r'cur\symbol.png')
        if sym:
            symbols = pyautogui.locateAllOnScreen(r'cur\symbol.png')
            symbol_arr = []
            symbol_locs = []
            for symbol in symbols:
                symbol_locs.append((int(symbol.left + (symbol.width/2)), int(symbol.top + ((symbol.height+50)/2))))
                p = pyautogui.screenshot(region=((symbol.left), (symbol.top), symbol.width + 10, 150))
                p.save(rf'tmp\option_{len(symbol_arr)}.png')
                symbol_arr.append(rf'tmp\option_{len(symbol_arr)}.png')
            symbol_names = get_selections(symbol_arr, r'cur\Symbols_8x')
            res = cur_game.choose_symbol(symbol_names)
            if res == -1:
                logging.info('Res is -1, dont want any symbols here. Going to see if we can reroll')
                reroll = pyautogui.locateOnScreen(r'cur\reroll.PNG')
                if reroll:
                    logging.info(f'Found reroll button, rerolling symbols')
                    # Reroll if the symbols are junk and we are able to
                    pyautogui.moveTo(int(reroll.left + (reroll.width/2)), int(reroll.top + (reroll.height/2)))
                    pyautogui.click()
                    return 1
                pyautogui.moveTo(int(skip.left + (skip.width/2)), int(skip.top + (skip.height / 2)))
                pyautogui.click()
            else:
                logging.info(f'Selecting symbol index {res}')
                sel_sym = symbol_locs[res]
                pyautogui.moveTo(sel_sym[0], sel_sym[1])
                pyautogui.click()
        else:
            items = pyautogui.locateAllOnScreen(r'cur\item.png')
            item_locs = []
            item_arr = []
            for item in items:
                item_locs.append(item)
                p = pyautogui.screenshot(region=((item.left), (item.top), item.width + 10, 150))
                p.save(rf'tmp\option_{len(item_arr)}.png')
                item_arr.append(rf'tmp\option_{len(item_arr)}.png')
            item_names = get_selections(item_arr, r'cur\Items_8x')
            res = cur_game.choose_item(item_names)
            if res == -1:
                pyautogui.moveTo(int(skip.left + (skip.width/2)), int(skip.top + (skip.height / 2)))
                pyautogui.click() 
            else:
                logging.info(f'Selecting item index {res}')
                sel_itm = item_locs[res]
                pyautogui.moveTo(int(sel_itm.left + (sel_itm.width/2)), int(sel_itm.top + (sel_itm.height/2)))
                pyautogui.click()
        return 1
    pay = pyautogui.locateOnScreen(r'cur\pay.PNG')
    if pay:
        logging.info('Found pay button')
        pyautogui.moveTo(int(pay.left + (pay.width/2)), int(pay.top + (pay.height / 2)))
        pyautogui.click()
        cur_game.pay_rent()
        return 1
    check = pyautogui.locateOnScreen(r'cur\check.PNG')
    if check:
        logging.info('Found check button')
        pyautogui.moveTo(int(check.left + (check.width/2)), int(check.top + (check.height / 2)))
        pyautogui.click()
        return 1
    floor = pyautogui.locateOnScreen(r'cur\floor.PNG')
    if floor:
        logging.info('Found floor select button')
        pyautogui.moveTo(int(floor.left + (floor.width/2)), int(floor.top + (floor.height / 2)))
        pyautogui.click()
        return 1
    start = pyautogui.locateOnScreen(r'cur\start.PNG')
    if start:
        logging.info('Found start button')
        pyautogui.moveTo(int(start.left + (start.width/2)), int(start.top + (start.height / 2)))
        pyautogui.click()
        return -1
    retry = pyautogui.locateOnScreen(r'cur\retry.PNG')
    if retry:
        logging.info('Found retry button')
        pyautogui.moveTo(int(retry.left + (retry.width/2)), int(retry.top + (retry.height / 2)))
        pyautogui.click()
        return -1
    
    logging.info('No match found')

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


cur_game = Game(0, 0, ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower'], 5, 5, json.load(open(r'symbols.json')), json.load(open(r'items.json')))
cur_game.symbols = ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower', 'Cat', 'Coin', 'Pearl', 'Cherry', 'Flower', 'Cat', 'Coin', 'Pearl', 'Cherry', 'Flower', 'Cat', 'Coin', 'Pearl', 'Cherry', 'Flower', 'Cat', 'Coin', 'Pearl', 'Cherry', 'Flower', 'Cat', 'Coin', 'Pearl', 'Cherry', 'Flower']
hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
rect = win32gui.GetWindowRect(hwnd)
window_x = rect[0] + 45
window_y = rect[1] + 45
win32gui.SetForegroundWindow(hwnd)
win32gui.ShowWindow(hwnd, 9)
time.sleep(2)
i = 0
while(1):
    logging.info(f'Iteration {i}')
    pyautogui.moveTo(window_x, window_y)
    result = current_screen(i, cur_game)
    if result == -1:
        cur_game = Game(0, 0, ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower'], 5, 5, json.load(open(r'symbols.json')), json.load(open(r'items.json')))
    time.sleep(1.5)
    i = i +1
    logging.info('\n-------------------------------------------------------------------------------------------------------\n')
for f in os.listdir(r'tmp'):
    os.remove(rf'tmp\{f}')
exit(0)
win32gui.ShowWindow(hwnd, 6)


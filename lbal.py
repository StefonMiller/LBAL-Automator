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
from datetime import datetime

# Class for default games (777 win achievement)
# Upon winning, will restart game as opposed to starting endless mode
class Game:
    # Symbols to pick for game strategy (Flower/bee/rain/sun)
    # Can be edited to conform to other stragegies
    synergizing_symbols = {'Flower': 1, 'Bee': 2, 'Rain': 2, 'Sun': 5}

    def __init__(self, pm, c, s, sr, gps, als, ai):
        self.payment_due = pm
        self.coins = c
        self.symbols = s
        self.spins_remaining = sr
        self.gold_per_spin = gps
        self.all_symbols = als
        self.all_items = ai
        self.priority_symbols = self.calculate_priority_symbols()

    # Dynamically calculate what additional symbols we should pick on init
    # List is computed based on the symbols json file & their associated priority
    def calculate_priority_symbols(self):
        priority_syms = []
        for sym in self.all_symbols:
            if self.all_symbols[sym]['priority'] >= 4:
                priority_syms.append(sym)
        return priority_syms

    # From the 3 options passed in, determine which one (if any) should be taken
    def choose_symbol(self, symbols):
        logging.info('Options:')
        syms = self.all_symbols.keys()
        priority_options = {}
        for sym_name in symbols:
            sym = difflib.get_close_matches(sym_name, syms)
            if len(sym) > 0:
                sym = sym[0]
                g = self.all_symbols[sym]['gold']
                logging.info(f'\t{sym}: {g} gold')
                if sym in self.priority_symbols:
                    logging.info(f'\t^Priority item, should take this')
                    priority_options[sym] = sym_name
        # Grab most valuable priority option
        if len(priority_options.keys()) > 0:
            logging.info("We have priority options, should take one of these")
            cur_g = 0
            cur_sym = ''
            cur_p = 0
            for option in priority_options.keys():
                if option != '':
                    if self.all_symbols[option]['priority'] >= cur_p:
                        cur_sym = option
                        cur_g = self.all_symbols[option]['gold']
                        cur_p = self.all_symbols[option]['priority']
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
            if expected_gold >= self.payment_due:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payment_due}. Not adding symbol')
                return -1
            else:
                logging.info(f'Will have {expected_gold} coins by this rent payment of {self.payment_due}. May need to add one of these symbols')
                cur_g = 0
                cur_sym = ''
                res = {}
                cur_p = 0
                for sym_name in symbols:
                    # Gets closest match from all symbols to the symbol we're picking. I initially used this when attempting OCR, so I think
                    # this can be removed but don't feel like testing/fixing if this somehow breaks the functionality
                    sym = difflib.get_close_matches(sym_name, syms)
                    if len(sym) > 0:
                        sym = sym[0]
                        res[sym] = sym_name
                        if self.all_symbols[sym]['priority'] >= cur_p:
                            cur_sym = sym
                            cur_g = self.all_symbols[sym]['gold']
                            cur_p = self.all_symbols[sym]['priority']
                # After payment 2, skip lower value symbols (if not rain, flower, bee, etc) since we need tos cale
                if cur_p < 2 and self.payment_due > 100:
                    logging.info(f'After payment 2, cant take any of these symbols bc theyre less than 2g in value')
                    return -1
                # Additional scaling for payment 7, by now we should be entirely focusing on synergies/run building
                elif cur_p < 3 and self.payment_due > 325 and len(self.symbols) > 20:
                    logging.info(f'After payment 7, cant take any symbols less than 3 in value')
                    return -1
                logging.info(f'OPTIONS: {res}')
                logging.info(f'SELECTION: {cur_sym}')
                if cur_sym != '':
                    self.symbols.append(cur_sym)
                    self.calculate_gold_per_spin()
                    logging.info(f'SYMBOL #: {symbols.index(res[cur_sym])}')
                    return symbols.index(res[cur_sym]) 
                return -1
    
    # From current selection of items, determine which one should be taken
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
        # Attempt to pick an item that synergizes with our strategy. If not, select one based on priority
        # assigned in the items.json file
        logging.info(f'Found best item based on priority. SELECTING {cur_itm}')
        if cur_itm != '':
            logging.info(f'ITEM #: {items.index(item_names[cur_itm])}')
            return items.index(item_names[cur_itm])
        else:
            return -1

    # Update gold/spin values
    def spin(self):
        self.spins_remaining = self.spins_remaining - 1
        self.coins = self.coins + self.gold_per_spin - 1

    # Used to estimate what gold we'll have by rent payment. Useful for deciding if we need to take a 
    # bad symbol to make rent
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
                    # Estimate how much gold we're going to get from symbols that synergize when adjacent,
                    # equation from https://www.reddit.com/r/askmath/comments/oqev8i/probability_of_adjacent_symbols_in_luck_be_a/
                    ev = self.synergizing_symbols[syn_sym]
                    matches = (110*a*b)/(n*(n-1))
                    cur_g = cur_g + (matches * ev)
            else:
                cur_g = cur_g + (self.all_symbols[sym]['gold'] * cur_symbols[sym])
        logging.info(f'Current gold per spin: {cur_g}')
        self.gold_per_spin = cur_g

    # Update list of current symbols pased on dict passed in
    # Dict is in item: count format, we parse this to a list of 
    # items. So item: 2 would conver to [item, item]
    def update(self, syms):
        logging.info(f'updating symbols to {syms}')
        self.symbols = []
        for sym in syms.keys():
            for i in range(0, syms[sym]):
                self.symbols.append(sym)
        logging.info(f'Symbols: {self.symbols}')
        self.calculate_gold_per_spin()

    # Remove symbols based on their associated gold values (Except for priority/synergizing symbols)
    def remove_symbols(self, syms):
        hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
        rect = win32gui.GetWindowRect(hwnd)
        window_x = rect[0] + 45
        window_y = rect[1] + 45
        self.update(syms)  
        while pyautogui.locateOnScreen(r'cur\x.PNG'):
            pyautogui.moveTo(window_x, window_y)
            time.sleep(0.25)
            lowest_g = 3
            lowest_sym = ''
            for sym in self.symbols:
                if (self.all_symbols[sym]['gold'] < lowest_g) and (sym not in self.priority_symbols):
                    lowest_g = self.all_symbols[sym]['gold']
                    lowest_sym = sym
            if lowest_sym != '':
                logging.info(f'Removing symbol {lowest_sym} with gold value {lowest_g}')
                sym_img = lowest_sym.replace(' ', '_') + '.png'
                sym_loc = pyautogui.locateCenterOnScreen(rf'cur\Symbols_3x\{sym_img}', confidence=0.9)
                if sym_loc:
                    pyautogui.moveTo(sym_loc.x, sym_loc.y)
                    time.sleep(0.25)
                    pyautogui.click()
                    time.sleep(0.25)
                    self.symbols.remove(lowest_sym)
                else:
                    logging.info('Could not find symbol to remove!')
                    return
            else:
                return
        
    def __str__(self):
        return f"Spins til payment: {self.spins_remaining}\nCurrent payment: {self.payment_due}\nGold/spin: {self.gold_per_spin}\nSymbols: {self.symbols}\nCoins: {self.coins}"

# Class for guillotine essence achievements. The Game class object is converted to a GuillotineGame
# upon winning the game. From there, it will continue in endless mode and try to add the
# guillotine essence item. The strategy used for 1B coins is 19 suns + 1 flower + Clear Skies
class GuillotineGame(Game):
    # Converts a game object to a GuillotineGame
    def __init__(self, game):
        self.payment_due = 0
        self.coins = game.coins
        self.symbols = game.symbols
        self.spins_remaining = game.spins_remaining
        self.gold_per_spin = game.gold_per_spin
        self.all_symbols = game.all_symbols
        self.all_items = game.all_items
        # Only need 1 flower for strategy, so don't take any more
        if 'Flower' in self.symbols:
            logging.info("Already have flower, only need suns now")
            self.flower_count = 1
        else:
            logging.info('Also need to find 1 flower')
            self.flower_count = 0
        self.sun_count = 0
        self.priority_symbols = ['Removal Capsule', 'Reroll Capsule', 'Lucky Capsule', 'Essence Capsule']
        self.priority_items = ['Guillotine', 'Cardboard Box', 'Sunglasses', 'Clear Sky', 'Recycling', 'Lucky Carrot', 'Dishwasher', 'Golden Carrot']

    # From the 3 options passed in, determine which one (if any) should be taken
    def choose_symbol(self, symbols):
        logging.info(symbols)
        for sym in symbols:
            if (sym == 'Flower' and self.flower_count < 1) or (sym == 'Sun' and self.sun_count < 19) or (sym in self.priority_symbols): 
                logging.info(f'Taking {sym}')
                return symbols.index(sym)
        logging.info('Not taking anything')
        return -1
    
    # From the 3 options passed in, determine which one (if any) should be taken
    def choose_item(self, items):
        logging.info(f'items: {items}')
        for priority_itm in self.priority_items:
            for item in items:
                if item == priority_itm:
                    logging.info(f'Taking {item}')
                    return items.index(item)
        logging.info('Not taking anything')
        return -1

    # Update spin/gold count
    def spin(self):
        self.spins_remaining = self.spins_remaining - 1
        self.coins = self.coins + self.gold_per_spin - 1

    # Don't need to do this after winning as rent payment is 0
    def calculate_gold_per_spin(self):
        pass
    
    # Update list of current symbols pased on dict passed in
    # Dict is in item: count format, we parse this to a list of 
    # items. So item: 2 would conver to [item, item]
    def update(self, syms):
        logging.info(f'updating symbols to {syms}')
        self.symbols = []
        if 'Flower' not in syms.keys():
            self.flower_count = 0
        for sym in syms.keys():
            # Only want 1 flower for 1b coins
            if sym == 'Flower':
                self.flower_count = syms[sym]
            elif sym == 'Sun':
                self.sun_count = syms[sym]
            for i in range(0, syms[sym]):
                self.symbols.append(sym)
        logging.info(f'Symbols: {self.symbols}')

    # Remove symbols based on their associated gold values (Except for priority/synergizing symbols)
    def remove_symbols(self, syms):
        hwnd = win32gui.FindWindow(None, 'Luck Be a Landlord')
        rect = win32gui.GetWindowRect(hwnd)
        window_x = rect[0] + 45
        window_y = rect[1] + 45
        self.update(syms)  
        while pyautogui.locateOnScreen(r'cur\x.PNG'):
            pyautogui.moveTo(window_x, window_y)
            time.sleep(0.25)
            rem_sym = ''
            for sym in self.symbols:
                if (sym != 'Sun' and sym != 'Flower' and sym not in self.priority_symbols) or (sym == 'Flower' and self.flower_count > 1) or (sym == 'Sun' and self.sun_count > 19):
                    rem_sym = sym
            if rem_sym != '':
                logging.info(f'Removing symbol {rem_sym}')
                sym_img = rem_sym.replace(' ', '_') + '.png'
                sym_loc = pyautogui.locateCenterOnScreen(rf'cur\Symbols_3x\{sym_img}', confidence=0.9)
                if sym_loc:
                    pyautogui.moveTo(sym_loc.x, sym_loc.y)
                    time.sleep(0.25)
                    pyautogui.click()
                    time.sleep(0.25)
                    self.symbols.remove(rem_sym)
                    self.flower_count = self.flower_count - 1
                else:
                    logging.info('Could not find symbol to remove!')
                    return
            else:
                return

    def __str__(self):
        return "This is a guillotine game"

# Get current amount of coins we have after each spin. Finds the coin image and parses each digit using
# image pattern matching. 
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

# Update how many coins and spins remaining we have for the current game
def update_coins_and_spins():
    due = pyautogui.locateOnScreen(r'cur\due.PNG')
    spins= pyautogui.locateOnScreen(r'cur\spins.PNG')
    payment_coin = pyautogui.locateOnScreen(r'cur\payment_coin.PNG')
    if due and spins and payment_coin:
        spins_template = pyautogui.screenshot(region=((due.left + due.width), due.top, (spins.left - (due.left + due.width)), due.height))
        spins_template.save(r'tmp\spins_template.png')
        coins_due_template = pyautogui.screenshot(region=((payment_coin.left + payment_coin.width + 3), due.top + 8, (due.left - (payment_coin.left + payment_coin.width + 3)), due.height-12))
        coins_due_template.save(r'tmp\coins_due_template.png')
        spins = find_closest_num(r'tmp\spins_template.png', r'cur\nums\spin_nums')
        if not spins:
            spins = 0
        segments = 5
        segs = []
        cur_offset = payment_coin.left + payment_coin.width + 3
        for i in range(0, segments):
            p = pyautogui.screenshot(region=(cur_offset, (payment_coin.top + 11), 16, 24))
            img_path = rf'tmp\coins_seg{i}.png'
            p.save(img_path)
            closest_num = find_closest_num(img_path, r'cur\nums\coin_nums')
            # Attempt to recrop segment if template is not a black box and we don't get a valid #
            if not closest_num and p.getbbox():
                # If this image isn't blank and there is no #, try cropping 20px wide
                p = pyautogui.screenshot(region=(cur_offset, (payment_coin.top + 11), 20, 24))
                p.save(img_path)
                closest_num_recropped = find_closest_num(img_path, r'cur\nums\coin_nums')
                if closest_num_recropped:
                    segs.append(closest_num_recropped)
                    cur_offset = cur_offset + 20
            elif closest_num and p.getbbox():
                segs.append(closest_num)
                cur_offset = cur_offset + 16
        coins = int(''.join(segs))
        logging.info(f'{coins} coins due in {spins} spins')
        cur_game.payment_due = int(coins)
        cur_game.spins_remaining = int(spins)
        
# Given an image, attempts to match the correct digit associated with it
def find_closest_num(img, path):
    template = cv2.imread(rf'{img}', 0)
    for name in os.listdir(rf'{path}'):
        img = cv2.imread(rf'{path}\{name}', 0)
        conf = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED).max()
        if conf > 0.97:
            return name.replace('.png', '').replace('.PNG', '')
    return None

# Get the current item/symbol selections we have to choose from
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
                best_image = name.replace('.png', '').replace('.PNG', '').replace('_ESS', '').replace('_', ' ')
        best_images.append(best_image)
    return best_images

# This probably shouldn't be a method, not sure why moved this to a function
def skip(skip_button):
    pyautogui.moveTo(int(skip_button.left + (skip_button.width/2)), int(skip_button.top + (skip_button.height / 2)))
    pyautogui.click()


# Check if 2 boxes are intersecting
def intersected(bottom_left1, top_right1, bottom_left2, top_right2):
    if top_right1[0] < bottom_left2[0] or bottom_left1[0] > top_right2[0]:
        return 0
    if top_right1[1] < bottom_left2[1] or bottom_left1[1] > top_right2[1]:
        return 0
    return 1

# Returns a list of all symbols that we have in our inventory. Used for removing/updating current symbols
def get_symbols():
    items_label = pyautogui.locateOnScreen(r'cur\items_inv.PNG', confidence=0.95)
    payments_label = pyautogui.locateOnScreen(r'cur\payments_inv.PNG', confidence=0.95)
    removal_label = pyautogui.locateOnScreen(r'cur\removal_inv.PNG', confidence=0.95)
    # Inventory layout can change depending on the game state. Need to crop the image differently depending on this
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
    # Use template matching to determien what symbols are in the invenotry. Pixel values needed to be tested and calculated manually
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

# Updates Game object w/ the current symbols we have in the inventory using pattern matching
def update_symbols(cur_game):
    inv = pyautogui.locateCenterOnScreen(r'cur\inventory.PNG')
    if inv:
        pyautogui.moveTo(inv.x, inv.y)
        pyautogui.click()
        time.sleep(0.25)
        syms = get_symbols()
        cur_game.update(syms)        
    x_button = pyautogui.locateCenterOnScreen(r'cur\x.PNG')
    if x_button:
        pyautogui.moveTo(x_button.x, x_button.y)
        pyautogui.click()

# Determine what screen we're currently looking at
def current_screen(cur_game):
    logging.info(cur_game)
    p = pyautogui.screenshot()
    p.save(rf'tmp\fullscreen.png')
    win = pyautogui.locateCenterOnScreen(r'cur\win.PNG')
    if win:
        endless_button = pyautogui.locateCenterOnScreen(r'cur\endless.PNG')
        while not endless_button:
            time.sleep(0.25)
            pyautogui.scroll(-100)
            endless_button = pyautogui.locateCenterOnScreen(r'cur\endless.PNG')
        time.sleep(0.25)
        pyautogui.moveTo(endless_button.x, endless_button.y)
        pyautogui.click()
        logging.info('Won game!')
        return -2
    remove = pyautogui.locateCenterOnScreen(r'cur\remove.png')
    # Only remove if we are over max # of symbols
    if remove and ((len(cur_game.symbols) > 20 and type(cur_game) is Game) or (type(cur_game) is GuillotineGame)):
        logging.info(f'Attempting to remove bad symbol as we have {len(cur_game.symbols)}')
        pyautogui.moveTo(remove.x, remove.y)
        pyautogui.click()
        time.sleep(0.25)
        syms = get_symbols()
        cur_game.remove_symbols(syms)
        x_button = pyautogui.locateCenterOnScreen(r'cur\x.PNG')
        if x_button:
            pyautogui.moveTo(x_button.x, x_button.y)
            pyautogui.click()
            time.sleep(0.25)
    spin = pyautogui.locateOnScreen(r'cur\spin.png')
    if spin:
        logging.info('Found spin button')
        update_symbols(cur_game)
        time.sleep(0.25)
        coins = get_coins()
        if coins:
            cur_game.coins = coins
            logging.info(f'Updated games coin total to {coins}')
        else:
            logging.info('Error parsing coins, not updated')
        time.sleep(0.25)
        cur_game.spin()
        pyautogui.moveTo(int(spin.left + (spin.width/2)), int(spin.top + (spin.height / 2)))
        pyautogui.click()
        time.sleep(0.25)
        return 1
    skip = pyautogui.locateOnScreen(r'cur\skip.PNG')
    if skip:
        logging.info('Found skip button, updating spins/coins due')
        update_coins_and_spins()
        time.sleep(0.25)
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
        cur_game.coins = cur_game.coins - cur_game.payment_due
        pyautogui.moveTo(int(pay.left + (pay.width/2)), int(pay.top + (pay.height / 2)))
        pyautogui.click()
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
    swear_jar = pyautogui.locateCenterOnScreen(r'cur\swear_jar.PNG')
    if swear_jar:
        logging.info('Found swear jar pay button')
        pyautogui.moveTo(swear_jar.x, swear_jar.y)
        pyautogui.click()
        return
    retry = pyautogui.locateOnScreen(r'cur\retry.PNG')
    if retry:
        logging.info('Found retry button')
        pyautogui.moveTo(int(retry.left + (retry.width/2)), int(retry.top + (retry.height / 2)))
        pyautogui.click()
        return -1
    pepper = pyautogui.locateCenterOnScreen(r'cur\pepper.PNG')
    if pepper:
        logging.info('Found pepper selection from pepper item')
        pyautogui.moveTo(pepper.x, pepper.y)
        pyautogui.click()
        return 1
    column_respin = pyautogui.locateCenterOnScreen(r'cur\column.PNG')
    if column_respin:
        logging.info('Found column respin text for oil can item')
        oil_can_x = pyautogui.locateCenterOnScreen(r'cur\oil_can_x.PNG')
        pyautogui.moveTo(oil_can_x.x, oil_can_x.y)
        pyautogui.click()
        return 1

    
    logging.info('No match found')
    # Try scrolling down as we might be stuck on a lategame debuff screen
    time.sleep(0.25)
    pyautogui.scroll(-100)


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

# Initialize game object w/ default values based on a new game
cur_game = Game(25, 0, ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower'], 5, 5, json.load(open(r'symbols.json')), json.load(open(r'items.json')))
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
    result = current_screen(cur_game)
    logging.info(f'Result of last iteration: {result}')
    # current_screen has a return value which indicated whether or not we should:
    # -1: Create a new game object (Game over/restart)
    # -2: Convert the current game to a Guillotine game object (Won the game and are now in endless mode)
    # A flag can be inserted here depending on whether or not you want to go for the Guillotine achievements, or you can comment
    # out the -2 return if statement
    if result == -1:
        logging.info('Making new game')
        cur_game = Game(25, 0, ['Cat', 'Coin', 'Pearl', 'Cherry', 'Flower'], 5, 5, json.load(open(r'symbols.json')), json.load(open(r'items.json')))
    elif result == -2:
        logging.info('Creating new guillotine game')
        cur_game = GuillotineGame(cur_game)
    time.sleep(0.25)
    i = i +1
    logging.info('\n-------------------------------------------------------------------------------------------------------\n')

        



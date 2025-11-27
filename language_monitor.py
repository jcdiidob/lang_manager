##############################################################
#                CROSS PLATFORM LANGUAGE MONITOR            #
#                  Detects REAL language from typing        #
#       Learns per-process and switches language by pattern #
##############################################################

import os
import time
import json
import sys
import platform
from difflib import SequenceMatcher

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

##############################################################
#                       DEBUG PRINTER                        #
##############################################################

def dprint(*msg):
    print("[DEBUG]", *msg)
    sys.stdout.flush()

##############################################################
#                       STATE STORAGE                        #
##############################################################

if IS_MAC:
    BASE_DIR = os.path.expanduser("~/Library/Application Support/LanguageMonitor")
elif IS_WIN:
    BASE_DIR = os.path.expanduser("~/AppData/Local/LanguageMonitor")
else:
    BASE_DIR = "."

os.makedirs(BASE_DIR, exist_ok=True)
STATE_FILE = os.path.join(BASE_DIR, "language_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, "r", encoding="utf-8"))
        except:
            return {}
    return {}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), indent=4, ensure_ascii=False)

##############################################################
#                     SIMILARITY CHECK                       #
##############################################################

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_similar_key(target, state, threshold=0.7):
    best = None
    best_score = 0.0
    for k in state:
        score = similarity(k, target)
        if score > best_score and score > threshold:
            best = k
            best_score = score
    return best

##############################################################
#              LANGUAGE DETECTION FROM TYPING                #
##############################################################

def detect_lang_from_char(ch):
    # Hebrew block
    if '\u0590' <= ch <= '\u05FF':
        return "HE"
    # English letters
    if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
        return "EN"
    return None  # not useful

current_lang = "EN"  # fallback


##############################################################
#                 WINDOWS IMPLEMENTATION                     #
##############################################################

if IS_WIN:
    import ctypes
    import psutil
    import keyboard

    def get_active_window_info():
        user32 = ctypes.windll.user32

        hwnd = user32.GetForegroundWindow()

        title_len = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(title_len + 1)
        user32.GetWindowTextW(hwnd, buffer, title_len + 1)
        title = buffer.value

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pid = pid.value

        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
        except:
            process_name = "UNKNOWN"

        return {"process_name": process_name, "window_title": title}

    def switch_language():
        keyboard.press('alt')
        time.sleep(0.02)
        keyboard.press_and_release('shift')
        time.sleep(0.02)
        keyboard.release('alt')

    def set_language(target):
        # Keep switching until layout stabilizes
        for _ in range(10):
            switch_language()
            time.sleep(0.05)
        return True


##############################################################
#                   MAC IMPLEMENTATION                       #
##############################################################

if IS_MAC:
    from Quartz import (
        CGEventTapCreate, kCGHeadInsertEventTap, kCGEventKeyDown,
        CGEventGetIntegerValueField, kCGKeyboardEventKeycode,
        CGEventCopyCharacters,
        CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        CGEventTapEnable, CFMachPortCreateRunLoopSource,
        CFRunLoopAddSource, CFRunLoopRun
    )

    FN_KEYCODES = {63, 64, 296}

    def get_active_window_info():
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        )
        for w in windows:
            if w.get("kCGWindowLayer") == 0:
                return {
                    "process_name": w.get("kCGWindowOwnerName", "UNKNOWN"),
                    "window_title": w.get("kCGWindowName", "")
                }
        return {"process_name": "UNKNOWN", "window_title": ""}

    def set_language(target):
        # Optional: implement real macOS switching if you want
        return True

    def key_event_callback(proxy, etype, event, refcon):
        global current_lang

        if etype == kCGEventKeyDown:

            # 1. detect FN press (intent to switch language)
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            if keycode in FN_KEYCODES:
                dprint("FN pressed → waiting for next char to detect lang")
                return event

            # 2. detect character typed
            chars = CGEventCopyCharacters(event)
            if chars:
                ch = chars[0]
                lang = detect_lang_from_char(ch)

                if lang and lang != current_lang:
                    dprint(f"Language changed from typing: {current_lang} → {lang}")
                    current_lang = lang

        return event

    def start_mac_typing_listener():
        mask = (1 << kCGEventKeyDown)
        tap = CGEventTapCreate(
            0, kCGHeadInsertEventTap, 0,
            mask, key_event_callback, None
        )
        src = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(
            __import__("Quartz").CFRunLoopGetCurrent(),
            src,
            __import__("Quartz").kCFRunLoopDefaultMode
        )
        CGEventTapEnable(tap, True)
        CFRunLoopRun()


##############################################################
#                      MAIN MONITOR LOOP                     #
##############################################################

def monitor():
    global current_lang

    state = load_state()
    prev_process = ""

    dprint("MONITOR STARTED")

    while True:
        info = get_active_window_info()
        proc = info["process_name"]
        title = info["window_title"]

        dprint("WINDOW:", proc, "| TITLE:", title, "| LANG:", current_lang)

        # find similar
        same = find_similar_key(proc, state)
        if same:
            proc = same

        # create new entry
        if proc not in state:
            state[proc] = {"EN": 0, "HE": 0}

        # update stats
        if current_lang in ("EN", "HE"):
            state[proc][current_lang] += 1

        # detect pattern → apply language automatically
        total = state[proc]["EN"] + state[proc]["HE"]
        if total > 10:
            ratio_en = state[proc]["EN"] / total
            ratio_he = state[proc]["HE"] / total

            if ratio_en > 0.7:
                dprint("AUTO SWITCH → EN", proc)
                set_language("EN")
            elif ratio_he > 0.7:
                dprint("AUTO SWITCH → HE", proc)
                set_language("HE")

        save_state(state)
        time.sleep(0.2)


##############################################################
#                            RUN                             #
##############################################################

if IS_MAC:
    import threading
    threading.Thread(target=start_mac_typing_listener, daemon=True).start()

monitor()

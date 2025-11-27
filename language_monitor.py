##############################################################
#               CROSS PLATFORM LANGUAGE MONITOR              #
#              macOS (FN Key + Quartz) + Windows            #
##############################################################

import os
import json
import sys
import time
import platform
import ctypes
import psutil
import subprocess
import keyboard
from difflib import SequenceMatcher

##############################################################
#                       OS Detection                         #
##############################################################

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

##############################################################
#                   Persistent State File                    #
##############################################################

if IS_MAC:
    BASE_DIR = os.path.expanduser("~/Library/Application Support/LanguageMonitor")
else:
    BASE_DIR = os.path.expanduser("./")

os.makedirs(BASE_DIR, exist_ok=True)
STATE_FILE = os.path.join(BASE_DIR, "language_state.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except:
        pass


##############################################################
#                      Similarity Logic                      #
##############################################################

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_similar_key(target, state, threshold=0.7):
    best_key = None
    best_score = 0.0
    for key in state.keys():
        score = similarity(target, key)
        if score > best_score and score >= threshold:
            best_key = key
            best_score = score
    return best_key


##############################################################
#                     WINDOWS IMPLEMENTATION                 #
##############################################################

if IS_WIN:

    def get_current_keyboard_language():
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
        klid = user32.GetKeyboardLayout(thread_id)
        lang_id = klid & 0xffff
        return {0x0409: "EN", 0x040D: "HE"}.get(lang_id, "UNKNOWN")

    def switch_language():
        keyboard.press('alt')
        time.sleep(0.02)
        keyboard.press_and_release('shift')
        time.sleep(0.02)
        keyboard.release('alt')

    def set_language(target):
        for _ in range(10):
            if get_current_keyboard_language() == target:
                return True
            switch_language()
            time.sleep(0.05)
        return False

    def get_active_window_info():
        user32 = ctypes.windll.user32

        hwnd = user32.GetForegroundWindow()

        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pid = pid.value

        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
        except:
            process_name = "UNKNOWN"

        return {
            "process_name": process_name,
            "window_title": title,
        }


##############################################################
#                   macOS IMPLEMENTATION                    #
##############################################################

if IS_MAC:
    from Quartz import (
        CGEventTapCreate,
        kCGHeadInsertEventTap,
        kCGEventKeyDown,
        CGEventTapEnable,
        CFMachPortCreateRunLoopSource,
        CFRunLoopAddSource,
        CFRunLoopRun,
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        CGEventGetIntegerValueField,
        kCGKeyboardEventKeycode
    )

    ###############################
    #   FN/Globe → Language Flip #
    ###############################

    current_lang = "EN"

    FN_KEYCODES = {63, 64, 296}   # FN / Globe key variants

    def event_callback(proxy, event_type, event, refcon):
        global current_lang
        if event_type == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            if keycode in FN_KEYCODES:
                current_lang = "HE" if current_lang == "EN" else "EN"
                print("Language switched manually →", current_lang)
        return event

    def start_mac_listener():
        mask = (1 << kCGEventKeyDown)
        tap = CGEventTapCreate(
            0,  # HID event tap
            kCGHeadInsertEventTap,
            0,
            mask,
            event_callback,
            None
        )
        source = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(
            __import__("Quartz").CFRunLoopGetCurrent(),
            source,
            __import__("Quartz").kCFRunLoopDefaultMode,
        )
        CGEventTapEnable(tap, True)
        print("macOS FN listener started...")
        CFRunLoopRun()

    ##########################################
    #   Get Active Window (Quartz Based)     #
    ##########################################

    def get_active_window_info():
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )
        for w in windows:
            if w.get("kCGWindowLayer") == 0:
                return {
                    "process_name": w.get("kCGWindowOwnerName", "UNKNOWN"),
                    "window_title": w.get("kCGWindowName", ""),
                }
        return {"process_name": "UNKNOWN", "window_title": ""}

    def get_current_keyboard_language():
        return current_lang

    def switch_language():
        pass

    def set_language(target):
        pass


##############################################################
#                      MAIN MONITOR LOOP                     #
##############################################################

def monitor_language_switching(interval=0.2, save_interval=60):
    state = load_state()
    last_save = time.time()
    prev = ""

    print("Monitoring started...\n")

    while True:
        info = get_active_window_info()
        current_process = info["process_name"]
        current_lang = get_current_keyboard_language()

        similar = find_similar_key(current_process, state)
        if similar:
            current_process = similar

        if current_process not in state:
            state[current_process] = {"EN": 0, "HE": 0, "last_lang": current_lang}

        if current_process != prev:
            prev = current_process

        if state[current_process]["last_lang"] != current_lang:
            state[current_process][current_lang] += 1
            state[current_process]["last_lang"] = current_lang

        if time.time() - last_save >= save_interval:
            save_state(state)
            last_save = time.time()

        time.sleep(interval)


##############################################################
#                           RUN                              #
##############################################################

if IS_MAC:
    import threading
    threading.Thread(target=start_mac_listener, daemon=True).start()

monitor_language_switching()

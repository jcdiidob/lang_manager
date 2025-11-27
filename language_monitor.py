##############################################################
#               CROSS PLATFORM LANGUAGE MONITOR              #
#                    Windows + macOS Compatible              #
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

STATE_FILE = "language_state.json"


##############################################################
#                     State Persistence                      #
##############################################################

def load_state():
    if not os.path.exists(STATE_FILE):
        print("State file not found. Starting fresh.\n")
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            print("Loaded existing state.\n")
            return json.load(f)
    except:
        print("State corrupted. Starting fresh.\n")
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        print("State saved.")
    except Exception as e:
        print("Save failed:", e)


##############################################################
#                      Similarity Logic                      #
##############################################################

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def find_similar_key(target_key: str, state: dict, threshold: float = 0.7):
    best_key = None
    best_score = 0.0

    for key in state.keys():
        score = similarity(target_key, key)
        if score > best_score and score >= threshold:
            best_score = score
            best_key = key

    return best_key


##############################################################
#                  WINDOWS IMPLEMENTATION                    #
##############################################################

if IS_WIN:

    def get_current_keyboard_language():
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        hwnd = user32.GetForegroundWindow()
        thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
        klid = user32.GetKeyboardLayout(thread_id)
        lang_id = klid & (2**16 - 1)

        return {
            0x0409: "EN",
            0x040D: "HE",
        }.get(lang_id, "UNKNOWN")

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
            "pid": pid
        }


##############################################################
#                   MAC IMPLEMENTATION                       #
##############################################################

if IS_MAC:
    from AppKit import NSWorkspace

    def get_active_window_info():
        try:
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            process_name = app.localizedName()
        except:
            process_name = "UNKNOWN"

        return {
            "process_name": process_name,
            "window_title": "",
            "pid": None
        }

    ##########################################################
    #  🔥 NEW MAC LANGUAGE DETECTOR — NO APPLESCRIPT NEEDED  #
    ##########################################################
    def get_current_keyboard_language():
        """
        Uses defaults read on HIToolbox plist — works inside py2app bundle.
        """
        try:
            out = subprocess.check_output([
                "defaults",
                "read",
                "~/Library/Preferences/com.apple.HIToolbox.plist",
                "AppleSelectedInputSources"
            ], stderr=subprocess.STDOUT)

            txt = out.decode("utf-8", errors="ignore")

            if "Hebrew" in txt:
                return "HE"

            # English layouts
            if "U.S." in txt or "ABC" in txt or "British" in txt:
                return "EN"

            return "EN"
        except:
            return "EN"

    def switch_language():
        # Cmd+Space
        subprocess.run([
            "osascript",
            "-e",
            'tell application "System Events" to key code 49 using {command down}'
        ])

    def set_language(target):
        # Can't reliably use AppleScript for this in unsigned apps → skip
        return True


##############################################################
#                      MAIN MONITOR LOOP                     #
##############################################################

def monitor_language_switching(interval=0.2, save_interval=120):
    state = load_state()
    last_save = time.time()
    prv_process = ""

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

        if current_process != prv_process:
            prv_process = current_process
            counts = state[current_process]["EN"] + state[current_process]["HE"]

            if counts > 3:
                if state[current_process]["EN"] / counts > 0.7:
                    set_language("EN")
                    state[current_process]["last_lang"] = "EN"

                elif state[current_process]["HE"] / counts > 0.7:
                    set_language("HE")
                    state[current_process]["last_lang"] = "HE"

            continue

        if state[current_process]["last_lang"] != current_lang:
            if current_lang in ("EN", "HE"):
                state[current_process][current_lang] += 1
            state[current_process]["last_lang"] = current_lang

        if time.time() - last_save >= save_interval:
            save_state(state)
            last_save = time.time()

        time.sleep(interval)


##############################################################
#                           RUN                              #
##############################################################

monitor_language_switching()

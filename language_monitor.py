# ##############################################################
# #            CROSS PLATFORM INTELLIGENT LANGUAGE MONITOR     #
# #        Detect real language from typing (mac/win)          #
# #       Learn per-window patterns + auto-switch language      #
# ##############################################################
#
# import os
# import sys
# import time
# import json
# import platform
# from difflib import SequenceMatcher
#
# IS_WIN = platform.system() == "Windows"
# IS_MAC = platform.system() == "Darwin"
#
# ##############################################################
# #                        DEBUG PRINT                         #
# ##############################################################
# def dprint(*msg):
#     print("[DEBUG]", *msg)
#     sys.stdout.flush()
#
#
# ##############################################################
# #                     STATE MANAGEMENT                       #
# ##############################################################
#
# if IS_MAC:
#     BASE_DIR = os.path.expanduser("~/Library/Application Support/LanguageMonitor")
# elif IS_WIN:
#     BASE_DIR = os.path.expanduser("~/AppData/Local/LanguageMonitor")
# else:
#     BASE_DIR = "."
#
# os.makedirs(BASE_DIR, exist_ok=True)
# STATE_FILE = os.path.join(BASE_DIR, "language_state.json")
#
#
# def load_state():
#     try:
#         if os.path.exists(STATE_FILE):
#             return json.load(open(STATE_FILE, "r", encoding="utf-8"))
#     except:
#         pass
#     return {}
#
#
# def save_state(state):
#     try:
#         json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
#     except:
#         pass
#
#
# ##############################################################
# #                       SIMILARITY                           #
# ##############################################################
# def similarity(a, b):
#     return SequenceMatcher(None, a, b).ratio()
#
#
# def find_similar_key(target, state, threshold=0.7):
#     best = None
#     best_score = 0.0
#     for k in state:
#         score = similarity(k, target)
#         if score > best_score and score >= threshold:
#             best = k
#             best_score = score
#     return best
#
#
# ##############################################################
# #                 LANGUAGE DETECTION FROM TYPING             #
# ##############################################################
#
# def detect_lang_from_char(ch):
#     # Hebrew unicode block
#     if '\u0590' <= ch <= '\u05FF':
#         return "HE"
#     # English letters
#     if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
#         return "EN"
#     return None
#
#
# current_lang = "EN"  # initial guess
#
#
# ##############################################################
# #                 WINDOWS IMPLEMENTATION                     #
# ##############################################################
#
# if IS_WIN:
#     import ctypes
#     import psutil
#     import keyboard
#
#     def get_active_window_info():
#         user32 = ctypes.windll.user32
#         hwnd = user32.GetForegroundWindow()
#
#         # window title
#         length = user32.GetWindowTextLengthW(hwnd)
#         buffer = ctypes.create_unicode_buffer(length + 1)
#         user32.GetWindowTextW(hwnd, buffer, length + 1)
#         title = buffer.value
#
#         pid = ctypes.c_ulong()
#         user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
#         pid = pid.value
#
#         try:
#             name = psutil.Process(pid).name()
#         except:
#             name = "UNKNOWN"
#
#         return {"process_name": name, "window_title": title}
#
#     def switch_language():
#         keyboard.press('alt')
#         time.sleep(0.03)
#         keyboard.press_and_release('shift')
#         time.sleep(0.03)
#         keyboard.release('alt')
#
#     def set_language(lang):
#         for _ in range(8):
#             switch_language()
#             time.sleep(0.05)
#         return True
#
#
# ##############################################################
# #                        MAC IMPLEMENTATION                  #
# ##############################################################
#
# if IS_MAC:
#
#     from Quartz import (
#         CGEventTapCreate, CGEventGetIntegerValueField,
#         CGEventKeyboardGetUnicodeString,
#         kCGHeadInsertEventTap, kCGEventKeyDown,
#         kCGKeyboardEventKeycode,
#         CGEventTapEnable,
#         CFMachPortCreateRunLoopSource,
#         CFRunLoopAddSource, CFRunLoopRun,
#         CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
#         kCGNullWindowID
#     )
#
#     FN_KEYCODES = {63, 64, 296}  # Globe/Fn variants
#
#     def extract_char_from_event(event):
#         """
#         Replacement for CGEventCopyCharacters (not available in py2app).
#         Uses CGEventKeyboardGetUnicodeString → ALWAYS works.
#         """
#         buffer = bytearray(8)
#         length = CGEventKeyboardGetUnicodeString(event, 4, buffer, None)
#         if length > 0:
#             try:
#                 return buffer[:2].decode("utf-16le")
#             except:
#                 return None
#         return None
#
#     def key_event_callback(proxy, etype, event, refcon):
#         global current_lang
#
#         if etype == kCGEventKeyDown:
#             keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
#
#             # FN press
#             if keycode in FN_KEYCODES:
#                 dprint("FN/Globe pressed — waiting for next typed character…")
#                 return event
#
#             # Typed character
#             ch = extract_char_from_event(event)
#             if ch:
#                 lang = detect_lang_from_char(ch)
#                 if lang and lang != current_lang:
#                     dprint(f"Language change detected from typing: {current_lang} → {lang}")
#                     current_lang = lang
#
#         return event
#
#     def start_mac_key_listener():
#         mask = (1 << kCGEventKeyDown)
#         tap = CGEventTapCreate(
#             0,  # HID tap
#             kCGHeadInsertEventTap,
#             0,
#             mask,
#             key_event_callback,
#             None,
#         )
#         src = CFMachPortCreateRunLoopSource(None, tap, 0)
#         CFRunLoopAddSource(
#             __import__("Quartz").CFRunLoopGetCurrent(),
#             src,
#             __import__("Quartz").kCFRunLoopDefaultMode
#         )
#         CGEventTapEnable(tap, True)
#         CFRunLoopRun()
#
#     def get_active_window_info():
#         windows = CGWindowListCopyWindowInfo(
#             kCGWindowListOptionOnScreenOnly,
#             kCGNullWindowID
#         )
#         for w in windows:
#             if w.get("kCGWindowLayer") == 0:
#                 return {
#                     "process_name": w.get("kCGWindowOwnerName", "UNKNOWN"),
#                     "window_title": w.get("kCGWindowName", "")
#                 }
#         return {"process_name": "UNKNOWN", "window_title": ""}
#
#     def set_language(lang):
#         # optionally: implement real switching
#         return True
#
#
# ##############################################################
# #                     MAIN MONITOR LOOP                      #
# ##############################################################
#
# def monitor_loop():
#     global current_lang
#
#     state = load_state()
#     dprint("Monitoring started…")
#
#     prev_process = None
#
#     while True:
#         info = get_active_window_info()
#         pname = info["process_name"]
#         wtitle = info["window_title"]
#
#         dprint("WINDOW:", pname, "| TITLE:", wtitle, "| LANG:", current_lang)
#
#         # similar grouping
#         existing = find_similar_key(pname, state)
#         if existing:
#             pname = existing
#
#         # initialize new process
#         if pname not in state:
#             state[pname] = {"EN": 0, "HE": 0}
#
#         # update counters
#         if current_lang in ("EN", "HE"):
#             state[pname][current_lang] += 1
#
#         # auto-switch logic
#         total = state[pname]["EN"] + state[pname]["HE"]
#         if total > 12:
#             ratio_en = state[pname]["EN"] / total
#             ratio_he = state[pname]["HE"] / total
#
#             if ratio_en > 0.7:
#                 dprint("Auto-switch → EN for", pname)
#                 set_language("EN")
#
#             elif ratio_he > 0.7:
#                 dprint("Auto-switch → HE for", pname)
#                 set_language("HE")
#
#         save_state(state)
#         time.sleep(0.15)
#
#
# ##############################################################
# #                            RUN                             #
# ##############################################################
#
# if IS_MAC:
#     import threading
#     threading.Thread(target=start_mac_key_listener, daemon=True).start()
#
# monitor_loop()
# מפעילים מאזין

import sys
import threading
import time

from Quartz import (
    CGEventTapCreate, kCGEventKeyDown, kCGHeadInsertEventTap,
    CGEventKeyboardGetUnicodeString, CGEventTapEnable,
    CFMachPortCreateRunLoopSource, CFRunLoopAddSource, CFRunLoopRun
)

current_lang = None   # נקבע בפועל מהקלדה


def detect_lang_from_char(ch):
    """Returns 'HE' or 'EN' based on typed character."""
    # Hebrew Unicode block
    if '\u0590' <= ch <= '\u05FF':
        return "HE"
    # English letters
    if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
        return "EN"
    return None


def extract_char_from_event(event):
    """Reliable, py2app-compatible extraction of typed character."""
    buffer = bytearray(8)
    length = CGEventKeyboardGetUnicodeString(event, 4, buffer, None)

    if length > 0:
        try:
            return buffer[:2].decode("utf-16le")
        except:
            return None
    return None


def key_callback(proxy, etype, event, refcon):
    global current_lang

    if etype == kCGEventKeyDown:
        ch = extract_char_from_event(event)
        if ch:
            lang = detect_lang_from_char(ch)
            if lang:
                current_lang = lang
                print("[DEBUG] Current macOS lang →", current_lang)

    return event


def start_language_detector():
    """Starts macOS keyboard language listener."""
    tap = CGEventTapCreate(
        0,
        kCGHeadInsertEventTap,
        0,
        1 << kCGEventKeyDown,
        key_callback,
        None
    )

    src = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(
        __import__("Quartz").CFRunLoopGetCurrent(),
        src,
        __import__("Quartz").kCFRunLoopDefaultMode
    )
    CGEventTapEnable(tap, True)
    CFRunLoopRun()


def get_current_macos_language():
    """Returns the last detected macOS keyboard language."""
    return current_lang

threading.Thread(target=start_language_detector, daemon=True).start()

# עכשיו בכל רגע:
while True:
    print("Current language =", get_current_macos_language())
    time.sleep(1)

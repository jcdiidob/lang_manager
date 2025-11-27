##############################################################
#                  MACOS LANGUAGE + FN DETECTOR             #
##############################################################

import os
import time
import subprocess
import platform
from difflib import SequenceMatcher

IS_MAC = platform.system() == "Darwin"

##############################################################
#               persistent state location (mac)              #
##############################################################
BASE_DIR = os.path.expanduser("~/Library/Application Support/LanguageMonitor")
os.makedirs(BASE_DIR, exist_ok=True)
STATE_FILE = os.path.join(BASE_DIR, "language_state.json")

##############################################################
#                        Debug print                         #
##############################################################
import sys
def dprint(*msg):
    print("[DEBUG]", *msg)
    sys.stdout.flush()

##############################################################
#                MAC: Read language from system             #
##############################################################
def read_system_language():
    """
    Reads the CURRENT keyboard layout from HIToolbox plist.
    Works even inside py2app.
    """
    try:
        out = subprocess.check_output([
            "defaults", "read",
            "~/Library/Preferences/com.apple.HIToolbox.plist",
            "AppleSelectedInputSources"
        ], stderr=subprocess.STDOUT)

        txt = out.decode("utf-8", errors="ignore")

        if "Hebrew" in txt:
            return "HE"
        if "U.S." in txt or "ABC" in txt:
            return "EN"
        return "EN"
    except:
        return "EN"


##############################################################
#                MAC: FN/Globe Key Listener                 #
##############################################################
if IS_MAC:
    from Quartz import (
        CGEventTapCreate, kCGHeadInsertEventTap,
        kCGEventKeyDown, CGEventGetIntegerValueField,
        kCGKeyboardEventKeycode, CGEventTapEnable,
        CFMachPortCreateRunLoopSource, CFRunLoopAddSource,
        CFRunLoopRun
    )
    FN_KEYCODES = {63, 64, 296}  # globe/fn variants

    current_lang = read_system_language()

    def key_event_callback(proxy, event_type, event, refcon):
        global current_lang

        if event_type == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)

            if keycode in FN_KEYCODES:
                dprint("FN/Globe PRESSED! => user intends to switch language")

                # read NEW lang from system (after OS processed FN)
                time.sleep(0.05)
                new_lang = read_system_language()

                dprint("System language AFTER FN:", new_lang)

                current_lang = new_lang

        return event

    def start_fn_listener():
        dprint("Starting FN listener…")

        mask = (1 << kCGEventKeyDown)
        tap = CGEventTapCreate(
            0,  # HID tap
            kCGHeadInsertEventTap,
            0, mask,
            key_event_callback,
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


##############################################################
#                         Window Detection                   #
##############################################################
if IS_MAC:
    from Quartz import (
        CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )

    def get_active_window_info():
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )
        for w in windows:
            if w.get("kCGWindowLayer") == 0:
                return {
                    "process_name": w.get("kCGWindowOwnerName", "UNKNOWN"),
                    "window_title": w.get("kCGWindowName", "")
                }
        return {"process_name": "UNKNOWN", "window_title": ""}


##############################################################
#                         Monitor Loop                       #
##############################################################
def monitor():
    global current_lang
    import json

    dprint("Monitor started.")
    state = {}
    prev_lang = current_lang

    while True:
        # check if system language changed not via FN
        real_lang = read_system_language()
        if real_lang != current_lang:
            dprint("Language changed WITHOUT FN:", current_lang, "→", real_lang)
            current_lang = real_lang

        # detect window
        info = get_active_window_info()
        dprint("Window:", info["process_name"])

        time.sleep(0.15)


##############################################################
#                            RUN                             #
##############################################################
if IS_MAC:
    import threading
    threading.Thread(target=start_fn_listener, daemon=True).start()

monitor()

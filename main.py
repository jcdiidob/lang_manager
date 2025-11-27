import ctypes
from multiprocessing.process import current_process

import psutil
import keyboard
import time
import json
import os


STATE_FILE = "language_state.json"

def load_state():
    """
    קורא state מהדיסק אם קיים,
    אם לא — מחזיר state ריק.
    """
    if not os.path.exists(STATE_FILE):
        print("State file not found → starting with empty state.\n")
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            print("Loaded existing state from disk.\n")
            return state
    except:
        print("State file corrupted → starting fresh.\n")
        return {}


def save_state(state):
    """
    שומר state לדיסק בפורמט JSON.
    """
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        print("State saved to disk.")
    except Exception as e:
        print("Failed to save state:", e)


# --- Detect current language ---
def get_current_keyboard_language():
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    klid = user32.GetKeyboardLayout(thread_id)
    lang_id = klid & (2**16 - 1)

    language_map = {
        0x0409: "EN",  # English (US)
        0x040D: "HE",  # Hebrew
    }
    return language_map.get(lang_id, "UNKNOWN")



def switch_language():
    keyboard.press('alt')
    time.sleep(0.02)
    keyboard.press_and_release('shift')
    time.sleep(0.02)
    keyboard.release('alt')


# --- Ensure language is exactly target_lang ---
def set_language(target_lang):
    """
    target_lang: "EN" או "HE"
    """
    max_attempts = 10

    for _ in range(max_attempts):
        current = get_current_keyboard_language()

        if current == target_lang:
            return True

        switch_language()
        time.sleep(0.05)

    print("Failed to set language.")
    return False



def get_active_window_info():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # מזהה חלון פעיל
    hwnd = user32.GetForegroundWindow()

    # גודל המחרוזת של שם החלון
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    window_title = buffer.value

    # מזהה את התהליך
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid = pid.value

    try:
        proc = psutil.Process(pid)
        process_name = proc.name()        # לדוגמה: "chrome.exe"
        process_path = proc.exe()         # נתיב מלא
    except psutil.AccessDenied:
        process_name = "UNKNOWN"
        process_path = "UNKNOWN"

    return {
        "window_title": window_title,
        "process_name": process_name,
        "process_path": process_path,
        "pid": pid
    }

from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def find_similar_key(target_key: str, state: dict, threshold: float = 0.7):
    """
    target_key - המחרוזת שאנחנו רוצים למצוא לה מפתח דומה
    state - מילון המפתחות הקיימים
    threshold - ציון דמיון מינימלי כדי להיחשב 'דומה'

    מחזיר:
        את המפתח הדומה ביותר (אם יש מספיק דמיון)
        אחרת None
    """

    best_key = None
    best_score = 0.0

    for key in state.keys():
        score = similarity(target_key, key)

        if score > best_score and score >= threshold:
            best_score = score
            best_key = key

    return best_key


def monitor_language_switching(interval=0.2, save_interval=60):
    state = {}  # process -> {EN:count, HE:count, last_lang:str}
    last_save = time.time()

    print("Monitoring language usage per process...\n")
    prv_win = ''
    while True:
        data = get_active_window_info()
        current_process = data['process_name']
        window_title = data['window_title']
        # if similarity(current_process, 'chrome.exe') > 0.7:
        #     current_process = f"{window_title}"
        current_lang = get_current_keyboard_language()
        option_key = find_similar_key(current_process, state)
        if option_key:
            current_process = option_key
        # אם התהליך חדש - נייצר עבורו state
        if current_process not in state:
            state[current_process] = {"EN": 0, "HE": 0, "last_lang": current_lang}
        if current_process != prv_win:
            prv_win = current_process
            state[current_process]["last_lang"] = current_lang
            summy = state[current_process]['EN'] + state[current_process]['HE']
            if summy > 3:
                if state[current_process]['EN'] / summy > 0.7:
                    set_language('EN')
                    state[current_process]["last_lang"] = 'EN'


                elif state[current_process]['HE'] / summy > 0.7:
                    set_language('HE')
                    state[current_process]["last_lang"] = 'HE'
            continue
        # אם השפה השתנתה מאז הפעם האחרונה
        if state[current_process]["last_lang"] != current_lang:
            if current_lang in ("EN", "HE"):
                state[current_process][current_lang] += 1

            state[current_process]["last_lang"] = current_lang
        if time.time() - last_save >= save_interval:
            save_state(state)
            last_save = time.time()
        time.sleep(interval)


monitor_language_switching()
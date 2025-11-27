from setuptools import setup

APP = ['language_monitor.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,  # לא חובה — אם אין אז למחוק שורה זו
    'plist': {
        'CFBundleName': 'Language Monitor',
        'CFBundleDisplayName': 'Language Monitor',
        'CFBundleVersion': '1.0',
        'CFBundleIdentifier': 'com.yourname.languagemonitor',
        'LSUIElement': True,  # מריץ כ-Background App ללא אייקון דוק
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

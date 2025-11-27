from setuptools import setup

APP = ['language_monitor.py']

OPTIONS = {
    'argv_emulation': True,
    'packages': ['psutil', 'keyboard'],
    'includes': ['AppKit', 'Foundation'],
    'plist': {
        'CFBundleName': 'Language Monitor',
        'CFBundleDisplayName': 'Language Monitor',
        'CFBundleVersion': '1.0',
        'CFBundleIdentifier': 'com.jcdidob.languagemonitor',
        'LSUIElement': True,
    }
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

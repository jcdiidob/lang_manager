from setuptools import setup

APP = ['language_monitor.py']

OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'psutil',
        'keyboard'
    ],
    'includes': [
        'AppKit',
        'Foundation',
        'Quartz',
        'subprocess',
        'ctypes',
        'json',
        'plistlib',
    ],
    'frameworks': [
        '/System/Library/Frameworks/AppKit.framework',
        '/System/Library/Frameworks/Foundation.framework',
        '/System/Library/Frameworks/Quartz.framework'
    ],
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

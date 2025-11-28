# from setuptools import setup
#
# APP = ['language_monitor.py']
#
# OPTIONS = {
#     'argv_emulation': True,
#     'packages': [
#         'psutil',
#         'keyboard'
#     ],
#     'includes': [
#         'AppKit',
#         'Foundation',
#         'Quartz',
#         'subprocess',
#         'ctypes',
#         'json',
#         'plistlib'
#     ],
#     'plist': {
#         'CFBundleName': 'Language Monitor',
#         'CFBundleDisplayName': 'Language Monitor',
#         'CFBundleVersion': '1.0',
#         'CFBundleIdentifier': 'com.jcdidob.languagemonitor',
#         'LSUIElement': True,
#     }
# }
#
# setup(
#     app=APP,
#     options={'py2app': OPTIONS},
#     setup_requires=['py2app'],
# )
from setuptools import setup

APP = ['language_monitor.py']

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'psutil',
    ],
    'includes': [
        'Quartz',
        'objc',
        'Foundation',
        'AppKit',
    ],
    'frameworks': [
        '/System/Library/Frameworks/Quartz.framework',
        '/System/Library/Frameworks/ApplicationServices.framework',
        '/System/Library/Frameworks/CoreGraphics.framework',
    ],
    'plist': {
        'CFBundleName': 'Language Monitor',
        'CFBundleDisplayName': 'Language Monitor',
        'CFBundleVersion': '1.0',
        'CFBundleIdentifier': 'com.jcdidob.languagemonitor',
        'LSUIElement': True,  # app hides from dock
    }
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

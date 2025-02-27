import os
from pathlib import Path
from shutil import copy, copytree
import  sysconfig

# https://blog.csdn.net/qq_25262697/article/details/129302819
# https://www.cnblogs.com/happylee666/articles/16158458.html
args = [
    'nuitka',
    '--standalone',
    # '--windows-disable-console',
    '--follow-import-to=app' ,
    '--plugin-enable=pyside6' ,
    '--include-qt-plugins=sensible,styles' ,
    '--msvc=latest',
    '--show-memory' ,
    '--show-progress' ,
    '--windows-icon-from-ico=app/resource/images/logo.ico',
    '--include-module=app',
    '--nofollow-import-to=pywin',
    '--follow-import-to=win32com,win32gui,win32print,qfluentwidgets,app',
    '--output-dir=dist/main',
    'main.py',
]

os.system(' '.join(args))

# copy site-packages to dist folder
dist_folder = Path("dist/main/main.dist")
paths = sysconfig.get_paths()
site_packages = Path(paths['purelib'])

copied_libs = []

for src in copied_libs:
    src = site_packages / src
    dist = dist_folder / src.name

    print(f"Coping site-packages `{src}` to `{dist}`")

    try:
        if src.is_file():
            copy(src, dist)
        else:
            copytree(src, dist)
    except:
        pass


# copy standard library
copied_files = ["ctypes", "hashlib.py", "hmac.py", "random.py", "secrets.py", "uuid.py"]
for file in copied_files:
    src = site_packages.parent / file
    dist = dist_folder / src.name

    print(f"Coping stand library `{src}` to `{dist}`")

    try:
        if src.is_file():
            copy(src, dist)
        else:
            copytree(src, dist)
    except:
        pass
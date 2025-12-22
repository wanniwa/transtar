import os
from pathlib import Path
from shutil import copy, copytree
import sysconfig
# 1. activate virtual environment
#    $ conda activate YOUR_ENV_NAME
#
# 2. run deploy script
#    $ python package.py

args = [
    'nuitka',
    '--standalone',
    '--assume-yes-for-downloads',
    '--mingw64',
    '--windows-icon-from-ico=app/resource/images/icon.ico',
    '--enable-plugins=pyside6',
    '--show-memory',
    '--windows-product-version=3.0.0',
    '--windows-disable-console',
    '--show-progress',
    '--windows-file-description="Stardew Valley Mod Translation Tool"',
    '--windows-file-version=3.0.0',
    '--output-dir=F:/Python/transtar/build',
    
    # 只编译项目代码，不编译任何第三方依赖
    '--follow-imports',  # 跟踪导入但不编译
    '--nofollow-import-to=*',  # 不编译任何第三方包
    '--follow-import-to=app',  # 只编译项目的 app 目录
    '--follow-import-to=main',  # 编译主文件
    
    # 编译优化
    '--jobs=4',
    '--lto=no',
    '--clang',
    
    'F:/Python/transtar/main.py'
]

dist_folder = Path("F:/Python/transtar/build")

copied_site_packages = [
    # 手动复制被排除的包（如果运行时需要）
    # 'boto3',
    # 'botocore',
    # 'numpy',
]

copied_standard_packages = [
    "ctypes"
]

# run nuitka
# https://blog.csdn.net/qq_25262697/article/details/129302819
# https://www.cnblogs.com/happylee666/articles/16158458.html
os.system(" ".join(args))

# copy site-packages to dist folder
site_packages = Path(sysconfig.get_path("purelib"))

for src in copied_site_packages:
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
for file in copied_standard_packages:
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
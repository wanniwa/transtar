# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['sklearn', 'PySide6-Fluent-Widgets~=1.10.4', 'pyside6~=6.10.1', 'hjson~=3.1.0', 'translatepy~=2.3', 'rich~=14.2.0', 'deepl~=1.27.0', 'packaging>=25.0', 'appdirs', '', 'google-genai', 'openai', 'boto3', 'cohere', 'anthropic', 'tiktoken']
tmp_ret = collect_all('sklearn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['jaxlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Transtar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/resource/images/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Transtar',
)
app = BUNDLE(
    coll,
    name='Transtar.app',
    icon='./app/resource/images/icon.icns',
    bundle_identifier=None,
)

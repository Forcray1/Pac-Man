# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pac-man.py'],
    pathex=['mazegenerator-00001-py3-none-any'],
    binaries=[],
    datas=[('assets', 'assets'), ('animation', 'animation'), ('config', 'config'), ('scores', 'scores')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pac-man',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pac-man',
)
app = BUNDLE(
    coll,
    name='pac-man.app',
    icon=None,
    bundle_identifier=None,
)

# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

ROOT = os.path.abspath('.')

a = Analysis(
    ['squishfile/cli.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('squishfile/frontend/dist', 'squishfile/frontend/dist'),
        ('squishfile/models', 'squishfile/models'),
    ],
    hiddenimports=[
        'squishfile',
        'squishfile.main',
        'squishfile.cli',
        'squishfile.detector',
        'squishfile.routes.upload',
        'squishfile.routes.compress',
        'squishfile.compressor.engine',
        'squishfile.compressor.image',
        'squishfile.compressor.pdf',
        'squishfile.compressor.video',
        'squishfile.compressor.audio',
        'squishfile.compressor.ffmpeg_utils',
        'squishfile.compressor.predictor',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sklearn',
        'sklearn.tree',
        'sklearn.ensemble',
        'PIL',
        'fitz',
        'magic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SquishFile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

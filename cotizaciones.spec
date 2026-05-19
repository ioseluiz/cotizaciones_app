# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'PyQt6.sip',
        'keyring.backends',
        'keyring.backends.SecretService',
        'keyring.backends.macOS',
        'keyring.backends.Windows',
        'keyring.backends.fail',
        'jaraco.classes',
        'jaraco.context',
        'jaraco.functools',
        'openpyxl',
        'PIL',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pdfkit',
        'weasyprint',
        'tkinter',
        'unittest',
        'email',
        'http',
        'xml',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Windows: single .exe file
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='CotizacionesApp',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        # icon='installer/windows/app.ico',  # Agrega un .ico cuando tengas el ícono
    )

# macOS: .app bundle
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='CotizacionesApp',
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
        # icon='installer/mac/app.icns',  # Agrega un .icns cuando tengas el ícono
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='CotizacionesApp',
    )

    app = BUNDLE(
        coll,
        name='CotizacionesApp.app',
        # icon='installer/mac/app.icns',
        bundle_identifier='com.joseluismunoz.cotizacionesapp',
        info_plist={
            'CFBundleShortVersionString': os.environ.get('APP_VERSION', '1.0.0'),
            'CFBundleVersion': os.environ.get('APP_VERSION', '1.0.0'),
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '12.0',
        },
    )

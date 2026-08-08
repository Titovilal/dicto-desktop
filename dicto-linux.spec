# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import copy_metadata

# CI empaqueta el .tar.gz portable esperando dist/dicto/dicto (minúscula); en
# local el bundle se llama Dicto. build-deb.sh acepta las dos grafías.
BUNDLE_NAME = os.environ.get('DICTO_BUNDLE_NAME', 'Dicto')

# El PortAudio que PyInstaller recoge del wheel de sounddevice viene compilado
# sin backend de PulseAudio, y el libasound.so.2 que arrastra viaja sin sus
# módulos de alsa-lib. Con ellos dentro del bundle desaparecen los PCM
# `pulse`, `pipewire` y `default`, así que sólo quedan los `hw:` en acceso
# exclusivo: PipeWire ya tiene el micro cogido y grabar falla.
#
# Los dejamos fuera para enlazar contra los del sistema, que el .deb ya exige
# en Depends (libportaudio2, libasound2, libpulse0).
_SYSTEM_AUDIO_LIBS = ('libportaudio.so', 'libasound.so', 'libjack.so')


def _keep(entry):
    name = entry[0].split('/')[-1]
    return not name.startswith(_SYSTEM_AUDIO_LIBS)


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('src/ui/assets', 'src/ui/assets')] + copy_metadata('dicto'),
    hiddenimports=[
        'dbus_next',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = TOC([e for e in a.binaries if _keep(e)])

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=BUNDLE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='assets/icons/icon.png',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=BUNDLE_NAME,
)

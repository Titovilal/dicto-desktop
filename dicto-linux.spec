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

# El runtime de C++/GCC también sale fuera, y es CONSECUENCIA de lo anterior.
#
# Al excluir las de audio, la app carga el `libportaudio.so.2` DEL SISTEMA, que
# a su vez arrastra el `libjack.so.0` del sistema. En una distro moderna ese
# libjack exige símbolos nuevos (`GLIBCXX_3.4.32`), pero el bundle iba primero
# en la búsqueda del enlazador, así que ganaba el `libstdc++.so.6` copiado del
# runner de build (ubuntu-22.04 → tope `GLIBCXX_3.4.30`). Resultado en v2.8.5:
#
#   OSError: cannot load library 'libportaudio.so.2': .../_internal/
#   libstdc++.so.6: version `GLIBCXX_3.4.32' not found
#   (required by /usr/lib/x86_64-linux-gnu/libjack.so.0)
#
# Es decir: una lib VIEJA del bundle eclipsando una lib NUEVA del sistema. No
# basta con que el bundle sea autocontenido; en cuanto una dependencia se
# resuelve contra el sistema, el runtime de C++ tiene que ser el del sistema
# también, porque libstdc++ solo es compatible hacia ATRÁS.
#
# Sacarlas es seguro en las DOS direcciones, medido sobre el bundle:
#   - lo que el bundle NECESITA: GLIBCXX_3.4.29 (libQt6Core/Gui/Widgets,
#     libpyside6, libshiboken6) y GCC_4.8.0.
#   - lo que la distro más VIEJA que soportamos APORTA (Ubuntu 22.04, el suelo
#     declarado en Depends): GLIBCXX_3.4.30 y GCC_12.0.0.
# 3.4.29 <= 3.4.30, así que Qt arranca con la libstdc++ de una 22.04 real; y en
# una distro nueva se usa la suya, que es superset. Si algún día PySide6 pide
# más de lo que da la distro del suelo, hay que revertir esto o subir el suelo:
# el smoke test `scripts/check-bundle-abi.py` falla y lo dice.
_SYSTEM_CXX_RUNTIME = ('libstdc++.so', 'libgcc_s.so')

_SYSTEM_LIBS = _SYSTEM_AUDIO_LIBS + _SYSTEM_CXX_RUNTIME


def _keep(entry):
    name = entry[0].split('/')[-1]
    return not name.startswith(_SYSTEM_LIBS)


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

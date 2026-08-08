#!/usr/bin/env python3
"""Comprueba que el bundle de PyInstaller no eclipse librerias del sistema.

Uso:
    python3 scripts/check-bundle-abi.py dist/dicto

Este check existe por el bug de v2.8.5, que el smoke test de arranque NO cazo.

## Que paso

`dicto-linux.spec` excluye del bundle libportaudio/libasound/libjack para que
la app use las del sistema (arreglo del micro: las del wheel vienen sin backend
de PulseAudio). Efecto secundario: la app carga el `libportaudio.so.2` del
SISTEMA, que enlaza con el `libjack.so.0` del sistema. En una distro moderna
ese libjack exige `GLIBCXX_3.4.32`, pero el bundle iba primero en la busqueda
del enlazador y ganaba el `libstdc++.so.6` copiado del runner (ubuntu-22.04 →
tope `GLIBCXX_3.4.30`):

    OSError: cannot load library 'libportaudio.so.2': .../_internal/
    libstdc++.so.6: version `GLIBCXX_3.4.32' not found
    (required by /usr/lib/x86_64-linux-gnu/libjack.so.0)

O sea: una lib VIEJA del bundle eclipsando una lib NUEVA del sistema.

## Por que el smoke test de arranque no lo vio

Porque corre en el MISMO runner donde se compila (ubuntu-22.04). Alli el
libjack del sistema es igual de viejo que el libstdc++ del bundle, asi que
coincide y arranca. El fallo solo aparece en distros MAS NUEVAS que la de
build, que es justo donde estan los usuarios. Un smoke test que solo prueba la
distro de build no puede, por construccion, detectar esta clase de bug.

## Que comprueba este script

Para cada libreria que el bundle EXCLUYE a proposito (y que por tanto se
resolvera contra el sistema), mira que versiones simbolicas necesita la copia
del sistema, y las compara con lo que APORTAN las copias del bundle. Si el
sistema pide una version que el bundle no tiene, el bundle esta eclipsando y
la app reventara en cuanto la distro sea mas nueva que la de build.

Es determinista: solo lee tablas ELF con `objdump`, no arranca la app, no
necesita servidor de audio ni display, y no depende de que el runner sea de
una version u otra. En un runner 22.04 el libjack del sistema pide 3.4.30 y el
bundle (si vuelve a llevar libstdc++) da 3.4.30 → pasaria. Por eso el check NO
se conforma con el estado del runner: si el bundle trae un runtime de C++ que
puede eclipsar al del sistema, falla directamente, sea cual sea la distro.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

# Librerias que el spec deja fuera a proposito para usar las del sistema.
# Mantener en sync con `_SYSTEM_AUDIO_LIBS` en dicto-linux.spec.
EXCLUDED_SYSTEM_LIBS = ("libportaudio.so.2", "libasound.so.2", "libjack.so.0")

# Runtimes que NO pueden viajar en el bundle mientras haya libs del sistema en
# juego: el enlazador busca primero en el bundle, asi que una copia vieja de
# estas eclipsa a la del sistema y rompe cualquier lib del sistema mas nueva.
# Mantener en sync con `_SYSTEM_CXX_RUNTIME` en dicto-linux.spec.
SHADOWING_RUNTIMES = ("libstdc++.so", "libgcc_s.so")

VERSION_TAG = re.compile(r"\b(GLIBCXX|GLIBC|GCC|CXXABI)_(\d+(?:\.\d+)*)\b")

# Familias de simbolos que el bundle puede eclipsar de verdad, o sea las que
# vienen de una .so que PyInstaller SI copia.
#
# `GLIBC_*` queda FUERA a proposito: la libc, libm, libpthread y el propio
# ld-linux nunca viajan en el bundle (comprobado: `find dist/dicto -name
# 'libc.so*'` no devuelve nada), asi que siempre se resuelven contra el sistema
# y son, por construccion, imposibles de eclipsar. El unico fichero del bundle
# que declara aportar `GLIBC_*` es `libmvec.so.1`, la lib de matematica
# vectorial de la propia glibc, cuyos tags solo reflejan la glibc del host y no
# satisfacen ningun simbolo de libc. Compararla contra lo que pide el sistema
# daba 4 falsos positivos ("libasound necesita GLIBC_2.43, el bundle aporta
# 2.35") que no corresponden a ningun fallo real: ese es el mismo espejismo de
# `libmvec` que ya documenta .ctx/docs/release.md en el suelo de glibc. El
# suelo de glibc es politica de release (`GLIBC_FLOOR` en build-deb.sh), no
# algo que este check pueda ni deba inferir.
SHADOWABLE_FAMILIES = ("GLIBCXX", "CXXABI", "GCC")


def _version_key(raw: str) -> tuple[int, ...]:
    return tuple(int(part) for part in raw.split("."))


def _symbol_versions(path: Path, *, provided: bool) -> set[tuple[str, str]]:
    """Versiones simbolicas de la tabla dinamica de `path`.

    `objdump -T` mezcla dos cosas en la misma tabla y confundirlas invierte el
    sentido del check:

      - lineas con `*UND*` → simbolos que la lib NECESITA de otra.
      - el resto          → simbolos que la lib DEFINE, o sea que APORTA.

    Un `libQt6Core.so.6` que necesita `GLIBCXX_3.4.29` no aporta ese GLIBCXX:
    se lo pide a libstdc++. Contarlo como aportado hacia creer que el bundle
    cubria 3.4.29 cuando en realidad, sin libstdc++ dentro, no aporta ninguno.
    """
    try:
        out = subprocess.run(
            ["objdump", "-T", str(path)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    except OSError:
        return set()

    found: set[tuple[str, str]] = set()
    for line in out.splitlines():
        if ("*UND*" in line) == provided:
            continue
        match = VERSION_TAG.search(line)
        if match:
            found.add((match.group(1), match.group(2)))
    return found


def _resolve_system_lib(soname: str) -> Path | None:
    for base in (
        "/usr/lib/x86_64-linux-gnu",
        "/lib/x86_64-linux-gnu",
        "/usr/lib64",
        "/usr/lib",
    ):
        candidate = Path(base) / soname
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(f"uso: {sys.argv[0]} <dir-del-bundle>", file=sys.stderr)
        return 2

    bundle = Path(sys.argv[1])
    internal = bundle / "_internal"
    lib_dir = internal if internal.is_dir() else bundle
    if not lib_dir.is_dir():
        print(f"ERROR: no existe el bundle {bundle}", file=sys.stderr)
        return 2

    if not shutil.which("objdump"):
        print("ERROR: hace falta objdump (paquete binutils).", file=sys.stderr)
        return 2

    failures: list[str] = []

    # ── 1. Ningun runtime de C++/GCC dentro del bundle ────────────────────────
    # Esta es la asercion principal y es INDEPENDIENTE de la distro del runner:
    # basta con que la lib exista en el bundle para que pueda eclipsar. Asi el
    # check vale igual en un runner 22.04 (donde el fallo NO se reproduce) que
    # en uno nuevo.
    for pattern in SHADOWING_RUNTIMES:
        for found in sorted(lib_dir.rglob(f"{pattern}*")):
            failures.append(
                f"{found.relative_to(bundle)} viaja en el bundle. El enlazador "
                f"lo antepone al del sistema, asi que cualquier lib del sistema "
                f"(libjack, libportaudio...) compilada contra un runtime mas "
                f"nuevo fallara con 'version not found'. Es el bug de v2.8.5."
            )

    # ── 2. Lo que pide el sistema cabe en lo que aporta el bundle ─────────────
    # Defensa en profundidad y diagnostico: si alguna lib del bundle sigue
    # aportando una version simbolica por debajo de lo que exige la copia del
    # sistema que vamos a cargar, decimos exactamente cual y cuanto falta.
    provided: dict[str, tuple[int, ...]] = {}
    for so in lib_dir.rglob("*.so*"):
        if not so.is_file():
            continue
        for family, version in _symbol_versions(so, provided=True):
            key = _version_key(version)
            if key > provided.get(family, ()):
                provided[family] = key

    for soname in EXCLUDED_SYSTEM_LIBS:
        system_lib = _resolve_system_lib(soname)
        if system_lib is None:
            # No instalada en esta maquina: no podemos comprobar nada, y no es
            # un fallo del bundle. El .deb la exige en Depends.
            print(f"  aviso: {soname} no esta en este sistema; no se comprueba")
            continue
        # Lo que la copia del SISTEMA necesita de otras libs: eso es lo que el
        # bundle no debe eclipsar con una version mas vieja.
        for family, version in sorted(_symbol_versions(system_lib, provided=False)):
            if family not in SHADOWABLE_FAMILIES:
                continue
            needed = _version_key(version)
            have = provided.get(family)
            if have is not None and needed > have:
                have_str = ".".join(str(n) for n in have)
                failures.append(
                    f"{soname} (del sistema) necesita {family}_{version}, pero "
                    f"el bundle solo aporta {family}_{have_str} y se carga "
                    f"antes. La app rompera en cualquier distro mas nueva que "
                    f"la de build."
                )

    if failures:
        print("FALLO: el bundle eclipsa librerias del sistema\n")
        for line in failures:
            print(f"  - {line}")
        print(
            "\nArregla excluyendolas en dicto-linux.spec (ver "
            "_SYSTEM_CXX_RUNTIME) o dejando de excluir la lib del sistema."
        )
        return 1

    print("OK: el bundle no eclipsa ninguna libreria del sistema")
    print(f"     runtimes ausentes del bundle: {', '.join(SHADOWING_RUNTIMES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

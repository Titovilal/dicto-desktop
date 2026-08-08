#!/usr/bin/env python3
"""Sincroniza la version de installer.iss con la de pyproject.toml.

pyproject.toml es la unica fuente de verdad de la version. installer.iss la
tenia clavada a mano y se quedo en 2.5.1 mientras el proyecto iba por 2.8.4:
el CI la parcheaba al vuelo con PowerShell, asi que el desfase solo se notaba
en builds locales, que generaban un `Dicto-2.5.1-setup.exe`. Ese nombre lo da
por bueno el updater, que instalaria una "actualizacion" con numero mas bajo
que la que ya corre.

Se ejecuta desde `make installer` antes de invocar ISCC. Es idempotente, asi
que se puede correr las veces que haga falta.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INSTALLER = ROOT / "installer.iss"

# Solo la clave `version` de la tabla [project], no la de una dependencia.
_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
_DEFINE_RE = re.compile(r'^(#define\s+MyAppVersion\s+")([^"]*)(")', re.MULTILINE)


def main() -> int:
    match = _VERSION_RE.search(PYPROJECT.read_text(encoding="utf-8"))
    if not match:
        print(f"ERROR: no encuentro `version = \"...\"` en {PYPROJECT}", file=sys.stderr)
        return 1
    version = match.group(1)

    source = INSTALLER.read_text(encoding="utf-8")
    patched, count = _DEFINE_RE.subn(rf"\g<1>{version}\g<3>", source)
    if count != 1:
        print(
            f"ERROR: esperaba 1 `#define MyAppVersion` en {INSTALLER}, encontre {count}",
            file=sys.stderr,
        )
        return 1

    if patched != source:
        INSTALLER.write_text(patched, encoding="utf-8")
        print(f">> installer.iss actualizado a {version}")
    else:
        print(f">> installer.iss ya estaba en {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

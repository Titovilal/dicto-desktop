#!/usr/bin/env bash
# Instala las librerías de sistema que PySide6/Qt y el audio necesitan dentro
# del devcontainer (Debian). Idempotente: apt no reinstala lo ya presente.
#
# Backend gráfico: Wayland (el host corre Wayland y VS Code reenvía su socket).
# QT_QPA_PLATFORM=wayland se fija en devcontainer.json -> containerEnv.
#
# Nota: el hotkey global (pynput) NO funciona en contenedor sobre Wayland; la
# app arranca igualmente y la GUI es usable para desarrollo. El hotkey se prueba
# en Windows/X11.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  libgl1 libegl1 libglib2.0-0 libdbus-1-3 \
  libxkbcommon0 libxkbcommon-x11-0 \
  libfontconfig1 libfreetype6 \
  libx11-xcb1 libxcb1 libxcb-cursor0 libxcb-glx0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-render0 libxcb-shape0 \
  libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
  libxext6 libxrender1 libxi6 \
  libwayland-cursor0 libwayland-egl1 libwayland-client0 \
  qtwayland5 libgles2 libegl-mesa0 \
  libasound2 libpulse0 libportaudio2

echo "GUI system libs installed (Qt + Wayland + audio)."

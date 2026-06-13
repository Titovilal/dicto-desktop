"""Enumerate and select audio input devices (effects: PortAudio).

Isolated from capture so the UI can list and pick a microphone without owning a
stream. Ported from the old ``recorder.py`` device helpers, trimmed to just
discovery: the streaming lives in ``capture.py`` and ``loopback.py``.

``sounddevice`` is imported lazily inside each function so importing this module
(and unit-testing the pure layers) never requires PortAudio to be installed.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InputDevice:
    """A selectable microphone, as shown in the audio settings panel."""

    id: int
    name: str
    channels: int
    is_default: bool = False
    default_samplerate: int = 16000


def list_input_devices() -> list[InputDevice]:
    """Return available input devices, deduplicated to the default host API.

    On Windows PortAudio exposes each physical device once per host API
    (MME, DirectSound, WASAPI, WDM-KS), producing many duplicate entries. We
    filter to the system's default host API so each device appears once.
    """
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001
        logger.warning("sounddevice unavailable; no input devices", exc_info=True)
        return []

    devices: list[InputDevice] = []
    try:
        raw = sd.query_devices()
        try:
            default_in = sd.default.device[0]
        except Exception:  # noqa: BLE001
            default_in = None
        try:
            default_hostapi = sd.default.hostapi
        except Exception:  # noqa: BLE001
            default_hostapi = None
        if default_hostapi is None and default_in is not None and default_in >= 0:
            default_hostapi = raw[default_in].get("hostapi")

        for i, dev in enumerate(raw):
            if dev.get("max_input_channels", 0) <= 0:
                continue
            if default_hostapi is not None and dev.get("hostapi") != default_hostapi:
                continue
            devices.append(
                InputDevice(
                    id=i,
                    name=dev["name"],
                    channels=int(dev["max_input_channels"]),
                    is_default=(i == default_in),
                    default_samplerate=int(dev.get("default_samplerate", 16000)),
                )
            )
    except Exception:  # noqa: BLE001
        logger.warning("failed to list audio devices", exc_info=True)
    return devices


def default_input_device() -> InputDevice | None:
    """The device PortAudio considers the default input, if any."""
    for dev in list_input_devices():
        if dev.is_default:
            return dev
    return None


def has_input_device() -> bool:
    """True when at least one usable input device exists."""
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001
        return False
    try:
        return sd.default.device[0] is not None and sd.default.device[0] >= 0
    except Exception:  # noqa: BLE001
        return bool(list_input_devices())


def negotiate_samplerate(input_device: int | None, channels: int, target_rate: int) -> int:
    """Return a sample rate the device accepts, preferring ``target_rate``.

    Some devices only expose 44.1/48 kHz. When ``target_rate`` (typically
    16 kHz) is rejected, fall back to the device's native rate; the caller
    resamples captured audio down to ``target_rate`` before saving.
    """
    try:
        import sounddevice as sd
    except Exception:  # noqa: BLE001
        return target_rate
    try:
        sd.check_input_settings(
            device=input_device, channels=channels, dtype="int16", samplerate=target_rate
        )
        return target_rate
    except Exception:  # noqa: BLE001
        try:
            target = input_device
            if target is None:
                target = sd.default.device[0]
            if target is None or target < 0:
                native = 48000
            else:
                native = int(sd.query_devices(target).get("default_samplerate", 48000))
        except Exception:  # noqa: BLE001
            native = 48000
        logger.info(
            "device rejects %d Hz; capturing at %d Hz and resampling", target_rate, native
        )
        return native


def find_wasapi_loopback() -> tuple[int, int, int] | None:
    """Default WASAPI output device usable as a loopback input.

    Returns ``(device_index, channels, native_samplerate)`` or ``None``.
    Windows only.
    """
    if sys.platform != "win32":
        return None
    try:
        import sounddevice as sd

        hostapis = sd.query_hostapis()
        wasapi_idx = next(
            (i for i, h in enumerate(hostapis) if "WASAPI" in h.get("name", "")), None
        )
        if wasapi_idx is None:
            return None
        out_idx = hostapis[wasapi_idx].get("default_output_device", -1)
        if out_idx is None or out_idx < 0:
            return None
        dev = sd.query_devices(out_idx)
        channels = max(1, int(dev.get("max_output_channels", 2)))
        rate = int(dev.get("default_samplerate", 48000))
        logger.info("WASAPI loopback device: [%d] %s (%dch @ %dHz)", out_idx, dev["name"], channels, rate)
        return out_idx, channels, rate
    except Exception:  # noqa: BLE001
        logger.warning("failed to find WASAPI loopback device", exc_info=True)
        return None

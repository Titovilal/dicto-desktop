"""
Main controller that orchestrates all application components.
"""

from __future__ import annotations

import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from src.config.settings import Settings
from src.i18n import t
from src.services.hotkey import HotkeyListener, create_hotkey_listener
from src.services.keyboard_actions import KeyboardService
from src.services.recorder import AudioRecorder
from src.services.transcriber import Transcriber, TranscriptionError, APIKeyError
from src.services.clipboard import ClipboardManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class _Delivery:
    """Everything one transcription needs to undo its own clipboard hijack.

    Grouping these per transcription is what makes overlapping dictations safe:
    the restore timer closes over *its* delivery, so a second transcription
    starting mid-flight can neither reset the first one's paste-failure flag nor
    make the first one's timer act on the second one's text.
    """

    previous: str
    copied_text: str
    generation: int
    paste_failed: bool = field(default=False)


class Controller(QObject):
    state_changed = Signal(AppState)
    recording_started = Signal()
    recording_stopped = Signal(float)
    transcription_completed = Signal(str)
    transform_completed = Signal(str, str)  # (format_id, transformed_text)
    transform_failed = Signal(str, str)  # (format_id, error_message)
    error_occurred = Signal(str)
    # Partial successes: the transcription landed, but something downstream
    # (typically the auto-paste) could not be delivered. Kept separate from
    # error_occurred so the UI can show it as advice instead of a failure.
    warning_occurred = Signal(str)
    audio_level_changed = Signal(float)

    cancel_completed = Signal()
    presets_loaded = Signal(list)  # list of preset dicts

    # Internal signals to bounce results back to the main thread
    _transcription_done = Signal(str)
    _transcription_failed = Signal(str)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.current_state = AppState.IDLE

        self.hotkey_listener: HotkeyListener | None = None
        self.recorder: AudioRecorder | None = None
        self.transcriber: Transcriber | None = None
        self.keyboard = KeyboardService()

        self._cancelled: bool = False
        # State for the transcription currently being delivered. Each one gets a
        # fresh _Delivery, so nothing leaks between overlapping dictations.
        self._delivery: _Delivery | None = None
        self._delivery_generation: int = 0
        # The single pending restore timer. Kept as a handle so a new
        # transcription can cancel the previous one instead of letting stale
        # timers pile up and revert text they know nothing about.
        self._restore_timer: QTimer | None = None
        # The delivery that timer owes a restore to, so a superseding
        # transcription can inherit the clipboard snapshot it never put back.
        self._pending_restore: _Delivery | None = None

        # Single persistent thread pool – no QThread lifecycle issues
        self._pool = ThreadPoolExecutor(max_workers=1)

        # Connect internal signals (thread-safe delivery to main thread)
        self._transcription_done.connect(self._on_transcribe_finished)
        self._transcription_failed.connect(self._on_transcribe_error)

        self._init_services()
        if self.recorder:
            self.recorder.set_audio_level_callback(self._on_audio_level)

    def _init_services(self):
        try:
            self.recorder = AudioRecorder(
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                max_duration=self.settings.audio_max_duration,
                input_device=self.settings.audio_input_device,
                include_system_audio=self.settings.audio_include_system_audio,
            )

            api_key = self.settings.transcription_api_key
            if not api_key:
                logger.warning(
                    "No API key found. Set DICTO_API_KEY or add to config.yaml"
                )
            else:
                self.transcriber = Transcriber(
                    api_key=api_key,
                    language=self.settings.transcription_language,
                    model=self.settings.transcription_model,
                    transformation_model=self.settings.transformation_model,
                )

            # Global hotkeys require a supported keyboard backend (X11 on Linux,
            # native on Windows/macOS). On headless/Wayland dev containers pynput
            # cannot acquire a display, so degrade gracefully: keep the GUI usable
            # for development and leave the listeners disabled.
            try:
                toggle = self.settings.recording_mode == "toggle"
                self.hotkey_listener = create_hotkey_listener(
                    modifiers=self.settings.hotkey_modifiers,
                    key=self.settings.hotkey_key,
                    # In toggle mode the single press routes to _on_hotkey_toggle,
                    # which decides start vs stop from the controller's state.
                    on_press=self._on_hotkey_toggle if toggle else self._on_hotkey_press,
                    on_release=self._on_hotkey_release,
                    on_toggle=self._on_hotkey_toggle,
                    mode=self._record_listener_mode(),
                    shortcut_id="dicto-record",
                    description="Dicto: Record voice",
                )
            except Exception as e:
                self.hotkey_listener = None
                logger.warning(
                    f"Global hotkeys unavailable on this platform: {e}. "
                    "The GUI will run without hotkey support."
                )
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            traceback.print_exc()
            raise

    # ── Lifecycle ────────────────────────────────────────────

    def start(self):
        if self.hotkey_listener:
            self.hotkey_listener.start()
        self._set_state(AppState.IDLE)
        self.fetch_presets()
        logger.info("Controller started successfully")

    def fetch_presets(self):
        """Fetch favorite presets from the API in the background."""
        if not self.transcriber:
            return

        def _do_fetch():
            try:
                assert self.transcriber is not None
                presets = self.transcriber.get_favorite_presets()
                self.presets_loaded.emit(presets)
            except Exception as e:
                logger.warning(f"Failed to fetch presets: {e}")

        self._pool.submit(_do_fetch)

    def stop(self):
        logger.info("Stopping controller...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop_recording()
        self._pool.shutdown(wait=True, cancel_futures=True)
        if self.recorder:
            self.recorder.close()
        if self.transcriber:
            self.transcriber.close()
        logger.info("Controller stopped")

    # ── State ────────────────────────────────────────────────

    def _set_state(self, new_state: AppState):
        if self.current_state != new_state:
            logger.debug(f"State: {self.current_state.value} -> {new_state.value}")
            self.current_state = new_state
            self.state_changed.emit(new_state)

    # ── Hotkey callbacks ─────────────────────────────────────

    def _record_listener_mode(self) -> str:
        """Translate the configured recording_mode into a listener mode.

        "hold" → press-and-hold ("hold"); "toggle" → single press per tap
        ("press"), where each tap is routed to _on_hotkey_toggle, which decides
        start vs stop from the controller's own state. The Wayland portal backend
        is always toggle-only regardless of this value.
        """
        return "press" if self.settings.recording_mode == "toggle" else "hold"

    def _on_hotkey_press(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    def _on_hotkey_release(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()

    def _on_hotkey_toggle(self):
        """Single entry point for toggle-style hotkeys (Wayland portal).

        The Wayland GlobalShortcuts portal fires one neutral activation per tap
        (Deactivated is unreliable across compositors), so the listener can't
        track press/release itself. We decide start vs stop here, from the
        controller's own state — the single source of truth — which avoids the
        listener and controller drifting out of sync.
        """
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()
        elif self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
        # PROCESSING: ignore taps while a transcription is in flight.

    # ── Recording ────────────────────────────────────────────

    def _start_recording(self):
        if not self.recorder:
            self._handle_error("Audio recorder not initialized")
            return
        try:
            self._cancelled = False
            # Start first, announce after: flipping the UI to RECORDING before
            # knowing the recorder accepted leaves a phantom "recording" frame
            # on screen whenever the start fails.
            if not self.recorder.start_recording():
                self._handle_error(
                    self.recorder.get_last_error()
                    or "Could not start recording — the audio device is busy. "
                    "Try again in a moment."
                )
                return
            self._set_state(AppState.RECORDING)
            self.recording_started.emit()
        except Exception as e:
            self._handle_error(f"Error starting recording: {e}")

    def _stop_recording_and_process(self):
        if not self.recorder:
            self._handle_error("Audio recorder not initialized")
            return
        try:
            audio_file_path = self.recorder.stop_recording()
            duration = self.recorder.get_recording_duration()
            self.recording_stopped.emit(duration)

            if not audio_file_path:
                rec_error = self.recorder.get_last_error()
                self._handle_error(rec_error or "No audio recorded")
                return

            self._set_state(AppState.PROCESSING)
            self._transcribe_audio(audio_file_path)
        except Exception as e:
            self._handle_error(f"Error stopping recording: {e}")

    # ── Transcription ────────────────────────────────────────

    def _transcribe_audio(self, audio_file_path: str):
        if not self.transcriber:
            self._handle_error(
                "Transcriber not initialized. Set API key in environment or config.yaml"
            )
            return

        logger.info(f"Transcribing audio: {audio_file_path}")

        def _do_transcribe():
            try:
                assert self.transcriber is not None
                text = self.transcriber.transcribe(audio_file_path)
                if text:
                    self._transcription_done.emit(text)
                else:
                    self._transcription_failed.emit("Transcription returned empty text")
            except (APIKeyError, TranscriptionError) as e:
                self._transcription_failed.emit(str(e))
            except Exception as e:
                traceback.print_exc()
                self._transcription_failed.emit(f"Unexpected error: {e}")

        self._pool.submit(_do_transcribe)

    @Slot(str)
    def _on_transcribe_finished(self, text: str):
        if self._cancelled:
            self._cancelled = False
            if self.recorder:
                self.recorder.cleanup_temp_file()
            return
        if self.recorder:
            self.recorder.cleanup_temp_file()
        # A new transcription supersedes the previous one: drop any restore it
        # still had pending, or it would revert the text we are about to place.
        superseded = self._cancel_pending_restore()
        # Snapshot the clipboard before we overwrite it, so we can put it back
        # once the auto-paste has consumed our text.
        previous_clipboard = self._read_clipboard_for_restore()
        if superseded is not None and previous_clipboard == superseded.copied_text:
            # Dictating again before the previous restore fired: what we just
            # read is the *previous transcription*, not the user's data. Carry
            # the older snapshot forward, or the real clipboard is lost for good
            # and we would "restore" our own text over it.
            previous_clipboard = superseded.previous
        self._delivery_generation += 1
        delivery = _Delivery(
            previous=previous_clipboard,
            copied_text=text,
            generation=self._delivery_generation,
        )
        self._delivery = delivery
        if ClipboardManager.copy(text):
            self._set_state(AppState.SUCCESS)
            self.transcription_completed.emit(text)
            logger.info(f"Transcription successful: {text}")
            auto_paste = self.settings.auto_paste
            self._perform_auto_actions(delivery, auto_paste, self.settings.auto_enter)
            self._schedule_clipboard_restore(delivery, auto_paste)
        else:
            self._handle_error("Failed to copy to clipboard")

    @Slot(str)
    def _on_transcribe_error(self, error_message: str):
        if self.recorder:
            self.recorder.cleanup_temp_file()
        self._handle_error(error_message)

    # ── Auto-paste / auto-enter ──────────────────────────────

    def _perform_auto_actions(
        self, delivery: _Delivery, auto_paste: bool, auto_enter: bool
    ):
        if auto_paste:
            QTimer.singleShot(100, lambda: self._do_auto_paste(delivery, auto_enter))

    def _do_auto_paste(self, delivery: _Delivery, auto_enter: bool):
        """Press Ctrl+V for `delivery`, recording on it whether that worked.

        Both failure shapes — a False return (Wayland with no ydotool/xdotool)
        and a raised exception (pynput failing on X11/Windows) — are partial
        successes: the text is on the clipboard, so we warn the user and mark
        the delivery so its restore leaves the transcription alone. Marking only
        the False branch used to lose the transcription outright on X11.
        """
        try:
            pasted = self.keyboard.paste()
        except Exception as e:
            logger.error(f"Error performing auto-paste: {e}")
            pasted = False
        if not pasted:
            delivery.paste_failed = True
            self._warn_auto_paste_unavailable()
            return
        if auto_enter:
            QTimer.singleShot(50, self._do_auto_enter)

    def _warn_auto_paste_unavailable(self):
        """Tell the user the text is on the clipboard and how to enable pasting."""
        message = t("auto_paste_failed")
        logger.warning(message)
        self.warning_occurred.emit(message)

    def _do_auto_enter(self):
        try:
            self.keyboard.enter()
        except Exception as e:
            logger.error(f"Error performing auto-enter: {e}")

    # ── Clipboard restore ────────────────────────────────────

    # How long to wait, after the transcription lands on the clipboard, before
    # putting the user's previous content back.
    #
    # The auto-paste chain is: +100ms QTimer -> keyboard.paste() (Ctrl+V, which
    # on Wayland goes out through a ydotool subprocess) -> the focused app reads
    # the clipboard, which on Linux means a round-trip to whichever process owns
    # the selection (xclip/wl-copy, spawned by pyperclip). Every step is
    # asynchronous and out of our control, so restoring too early makes the app
    # paste the *old* content — the exact bug this feature must not introduce.
    # 1.2s leaves ~1.1s of slack after the paste is triggered, which is far more
    # than a local clipboard round-trip needs while still being short enough
    # that a user reaching for Ctrl+V themselves gets their own data back.
    # Being late is harmless; being early breaks the paste, so we err late.
    CLIPBOARD_RESTORE_DELAY_MS = 1200

    def _read_clipboard_for_restore(self) -> str:
        """Read the current clipboard so it can be restored later.

        Returns an empty string when the feature is disabled, so no restore is
        scheduled and we never pay the clipboard read cost.

        Unlike the restore, this read stays on the GUI thread: its result is
        needed *before* we overwrite the clipboard on the very next line, so
        offloading it would only add a blocking wait for the same work.
        """
        if not self.settings.restore_clipboard:
            return ""
        return ClipboardManager.paste()

    def _cancel_pending_restore(self) -> _Delivery | None:
        """Drop the restore still owed by the previous transcription, if any.

        Returns the delivery whose restore was cancelled, so the caller can
        inherit the clipboard snapshot it never got to put back.
        """
        if self._restore_timer is None:
            return None
        self._restore_timer.stop()
        self._restore_timer = None
        cancelled, self._pending_restore = self._pending_restore, None
        return cancelled

    def _schedule_clipboard_restore(self, delivery: _Delivery, auto_paste: bool):
        """Queue restoring the previous clipboard once the paste consumed ours.

        Only makes sense when auto-paste ran: without it, the transcription on
        the clipboard *is* the deliverable — the user's next action is pasting
        it by hand — so taking it away would break the app's main purpose.

        The timer is kept on `self._restore_timer` so the next transcription can
        cancel it, and `delivery.generation` is re-checked when it fires: the
        handle alone is not enough, because a timer can already be in the event
        queue by the time we try to stop it.
        """
        if (
            not auto_paste
            or not self.settings.restore_clipboard
            or not delivery.previous
        ):
            return
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._restore_clipboard(delivery))
        self._restore_timer = timer
        self._pending_restore = delivery
        timer.start(self.CLIPBOARD_RESTORE_DELAY_MS)

    def _run_clipboard_io(self, fn):
        """Run blocking clipboard work off the GUI thread.

        On Linux pyperclip shells out to xclip/wl-copy, and a restore is a read
        plus a write — up to two subprocesses. A hung selection owner (a classic
        X11 failure) would otherwise freeze the whole UI, so this goes to the
        worker pool. Nothing downstream touches Qt widgets, so no marshalling
        back to the main thread is needed.
        """
        try:
            self._pool.submit(fn)
        except RuntimeError:
            # Pool already shut down (app quitting): the restore no longer
            # matters, and running it inline could block the exit path.
            logger.debug("Skipping clipboard restore: worker pool is shut down")

    def _restore_clipboard(self, delivery: _Delivery):
        self._restore_timer = None
        self._pending_restore = None
        # A newer transcription owns the clipboard now; this timer is stale and
        # restoring would revert text the user just dictated.
        if delivery.generation != self._delivery_generation:
            logger.info(
                "Skipping clipboard restore: a newer transcription superseded it"
            )
            return
        # When the auto-paste never landed, the transcription on the clipboard is
        # all the user has left (we told them to press Ctrl+V), so keep it.
        # Read from the delivery, not from self: the flag belongs to *this*
        # transcription, and self would already have been reset by a newer one.
        if delivery.paste_failed:
            logger.info("Skipping clipboard restore: auto-paste did not run")
            return

        previous, copied_text = delivery.previous, delivery.copied_text

        def _do_restore():
            try:
                ClipboardManager.restore(previous, copied_text)
            except Exception as e:
                logger.error(f"Error restoring clipboard: {e}")

        self._run_clipboard_io(_do_restore)

    # ── Audio level callback ────────────────────────────────

    def _on_audio_level(self, level: float):
        """Called from audio thread; emit signal for thread-safe delivery."""
        self.audio_level_changed.emit(level)

    # ── Error handling ───────────────────────────────────────

    def _handle_error(self, error_message: str):
        logger.error(error_message)
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(error_message)

    # ── Public slots ─────────────────────────────────────────

    @Slot()
    def cancel(self):
        """Cancel the current operation and return to idle."""
        if self.current_state == AppState.RECORDING:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop_recording()
                self.recorder.cleanup_temp_file()
            self._set_state(AppState.IDLE)
            self.cancel_completed.emit()
        elif self.current_state == AppState.PROCESSING:
            self._cancelled = True
            self._set_state(AppState.IDLE)
            self.cancel_completed.emit()

    @Slot()
    def return_to_idle(self):
        self._set_state(AppState.IDLE)

    @Slot(object)
    def update_input_device(self, device_id):
        if self.recorder:
            self.recorder.set_input_device(device_id)

    @Slot(bool)
    def update_include_system_audio(self, enabled: bool):
        if self.recorder:
            self.recorder.set_include_system_audio(enabled)

    @Slot()
    def start_recording_manual(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    @Slot()
    def stop_recording_manual(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
        elif self.current_state == AppState.PROCESSING:
            self.cancel()

    # ── Hotkey updates ──────────────────────────────────────────

    def _update_hotkey_listener(
        self,
        listener_attr: str,
        modifiers: list[str],
        key: str,
        on_press,
        on_release,
        on_toggle=None,
        mode: str = "hold",
        suppress_key: bool = False,
        shortcut_id: str = "dicto-shortcut",
        description: str = "Dicto shortcut",
    ):
        """Generic hotkey listener update: stop old -> create new -> start."""
        old_listener = getattr(self, listener_attr)
        if old_listener:
            old_listener.stop()
        new_listener = create_hotkey_listener(
            modifiers=modifiers,
            key=key,
            on_press=on_press,
            on_release=on_release,
            on_toggle=on_toggle,
            mode=mode,
            suppress_key=suppress_key,
            shortcut_id=shortcut_id,
            description=description,
        )
        setattr(self, listener_attr, new_listener)
        new_listener.start()
        logger.info(f"Hotkey updated ({listener_attr}): {'+'.join(modifiers)}+{key}")

    def update_recording_hotkey(self, modifiers: list[str], key: str):
        toggle = self.settings.recording_mode == "toggle"
        self._update_hotkey_listener(
            "hotkey_listener",
            modifiers,
            key,
            self._on_hotkey_toggle if toggle else self._on_hotkey_press,
            self._on_hotkey_release,
            on_toggle=self._on_hotkey_toggle,
            mode=self._record_listener_mode(),
            shortcut_id="dicto-record",
            description="Dicto: Record voice",
        )

    @Slot(str)
    def update_recording_mode(self, mode: str):
        """Rebuild the record hotkey listener after the hold/toggle mode changes."""
        self.update_recording_hotkey(
            self.settings.hotkey_modifiers, self.settings.hotkey_key
        )

    # ── Transform ─────────────────────────────────────────────

    @Slot(str, str, str)
    def request_transform(self, format_id: str, text: str, instructions: str):
        """Request a text transformation in the background thread pool."""
        if not self.transcriber:
            self.transform_failed.emit(format_id, "Transcriber not initialized")
            return

        def _do_transform():
            try:
                assert self.transcriber is not None
                result = self.transcriber.transform(text, instructions)
                self.transform_completed.emit(format_id, result)
            except Exception as e:
                self.transform_failed.emit(format_id, str(e))

        self._pool.submit(_do_transform)

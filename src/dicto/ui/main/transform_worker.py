"""Run a transform call off the Qt thread.

Transform requests hit the network (blocking), so the detail view and chat view
must not call them on the GUI thread. ``run_transform`` wraps any callable that
returns text into a ``QRunnable`` pushed onto the global thread pool; the result
(or error) comes back as a Qt signal on the GUI thread.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class _Signals(QObject):
    finished = Signal(str)  # result text
    failed = Signal(str)  # error message


class _Task(QRunnable):
    def __init__(self, work: Callable[[], str]) -> None:
        super().__init__()
        self._work = work
        self.signals = _Signals()

    def run(self) -> None:  # executes on a pool thread
        try:
            result = self._work()
        except Exception as exc:  # noqa: BLE001 — surfaced to the UI
            self.signals.failed.emit(str(exc))
        else:
            self.signals.finished.emit(result)


# Hold the signal objects alive until their queued slot has fired; without this
# the QObject can be collected before the GUI thread delivers the result.
_pending: set[_Signals] = set()


def run_transform(
    work: Callable[[], str],
    on_done: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    """Run ``work`` on the thread pool; deliver result/error on the GUI thread."""
    task = _Task(work)
    sig = task.signals
    _pending.add(sig)

    def _cleanup() -> None:
        _pending.discard(sig)

    sig.finished.connect(on_done)
    sig.failed.connect(on_error)
    sig.finished.connect(_cleanup)
    sig.failed.connect(_cleanup)
    QThreadPool.globalInstance().start(task)

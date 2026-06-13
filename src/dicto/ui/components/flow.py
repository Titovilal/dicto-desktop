"""FlowLayout — wraps child widgets onto new rows when width runs out.

The classic Qt flow-layout recipe, trimmed. Used for the library's tag chips
so they wrap like the design instead of squeezing on one row.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy


class FlowLayout(QLayout):
    def __init__(self, parent=None, h_spacing: int = 6, v_spacing: int = 6) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h = h_spacing
        self._v = v_spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item: QLayoutItem) -> None:  # noqa: N802 — Qt override
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:  # noqa: N802 — Qt override
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # noqa: N802 — Qt override
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self) -> Qt.Orientation:  # noqa: N802 — Qt override
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802 — Qt override
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802 — Qt override
        return self._do_layout(QRect(0, 0, width, 0), apply_geometry=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802 — Qt override
        super().setGeometry(rect)
        self._do_layout(rect, apply_geometry=True)

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt override
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802 — Qt override
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )

    def _do_layout(self, rect: QRect, apply_geometry: bool) -> int:
        x, y = rect.x(), rect.y()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() + 1 and line_height > 0:
                x = rect.x()
                y += line_height + self._v
                line_height = 0
            if apply_geometry:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._h
            line_height = max(line_height, hint.height())
        return y + line_height - rect.y()


# Keep Qt happy about size policies of chip rows inside vertical layouts.
def make_wrapping(widget) -> None:
    widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

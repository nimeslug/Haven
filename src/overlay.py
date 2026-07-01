"""
overlay.py
----------
"""
from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import (
    QPixmap, QMouseEvent, QContextMenuEvent, QPainter, QColor, QTransform, QFont
)
from PySide6.QtWidgets import QWidget, QLabel, QMenu, QGraphicsOpacityEffect


TRANSPARENT_COLOR = QColor(1, 2, 3)  # neredeyse siyah - hiçbir görselde olmaz


def _make_window_transparent_windows(hwnd: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    LWA_COLORKEY = 0x00000001
    user32 = ctypes.windll.user32
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
    # COLORREF Windows'ta 0x00BBGGRR formatında.
    # RGB(1,2,3) → BGR(3,2,1) → 0x00030201
    user32.SetLayeredWindowAttributes(hwnd, 0x00030201, 0, LWA_COLORKEY)


CLICK_DRAG_THRESHOLD = 5


class BubbleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._label = QLabel(self)
        font = QFont()
        font.setPointSize(28)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "background: rgba(255, 255, 255, 220); "
            "border-radius: 22px; "
            "padding: 6px 10px;"
        )
        self._label.adjustSize()

        self._opacity_effect = QGraphicsOpacityEffect(self._label)
        self._label.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(500)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_anim.finished.connect(self.hide)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

    def show_emoji(self, emoji: str, near_widget: QWidget, duration_ms: int) -> None:
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(1.0)
        self._label.setText(emoji)
        self._label.adjustSize()

        pad = 8
        w = self._label.width() + pad * 2
        h = self._label.height() + pad * 2
        self.resize(w, h)
        self._label.move(pad, pad)

        pet_geo = near_widget.frameGeometry()
        facing_left = getattr(near_widget, "_facing_left", False)
        if facing_left:
            x = pet_geo.left() - w // 2
        else:
            x = pet_geo.right() - w // 2
        y = pet_geo.top() - h + 10
        self.move(x, y)

        self.show()
        self._hide_timer.start(max(duration_ms - 500, 100))

    def _start_fade_out(self) -> None:
        self._fade_anim.start()


class OverlayWindow(QWidget):
    clicked = Signal()
    activity_detected = Signal()
    walk_blocked = Signal()

    def __init__(self, size: int):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.resize(size, size)
        self.setMouseTracking(True)

        self._size = size
        self._pixmap: Optional[QPixmap] = None
        self._facing_left: bool = False
        self._y_offset: int = 0

        self._press_pos: Optional[QPoint] = None
        self._press_window_pos: Optional[QPoint] = None
        self._is_dragging: bool = False
        # Fare hareketinden aktivite algılama için (spamı önlemek için throttle)
        self._last_mouse_pos: Optional[QPoint] = None

        self._menu_builder = None
        self._native_transparency_applied = False

        self._bubble = BubbleWindow()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._native_transparency_applied:
            hwnd = int(self.winId())
            _make_window_transparent_windows(hwnd)
            self._native_transparency_applied = True

    def set_menu_builder(self, builder) -> None:
        self._menu_builder = builder

    def set_pixmap(self, pixmap: QPixmap, facing_left: bool = False) -> None:
        self._pixmap = pixmap
        self._facing_left = facing_left
        self.update()

    def set_y_offset(self, offset: int) -> None:
        if offset != self._y_offset:
            self._y_offset = offset
            self.update()

    def move_by(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        cur_x, cur_y = self.x(), self.y()
        target_x = cur_x + dx
        target_y = cur_y + dy

        blocked = False
        if screen is not None:
            geo = screen.availableGeometry()
            clamped_x = max(geo.left(), min(target_x, geo.right() - self.width()))
            clamped_y = max(geo.top(), min(target_y, geo.bottom() - self.height()))
            if clamped_x != target_x or clamped_y != target_y:
                blocked = True
            target_x, target_y = clamped_x, clamped_y

        self.move(target_x, target_y)
        if blocked:
            self.walk_blocked.emit()

    def show_bubble(self, emoji: str, duration_ms: int = 2500) -> None:
        self._bubble.show_emoji(emoji, self, duration_ms)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), TRANSPARENT_COLOR)

        if self._pixmap is None:
            return

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        pix = self._pixmap
        if self._facing_left:
            pix = pix.transformed(QTransform().scale(-1, 1))

        x = (self.width() - pix.width()) // 2
        y = (self.height() - pix.height()) // 2 + self._y_offset
        painter.drawPixmap(x, y, pix)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._press_window_pos = self.frameGeometry().topLeft()
            self._is_dragging = False
            self.activity_detected.emit()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        global_pos = event.globalPosition().toPoint()

        # Sürükleme yoksa: gerçek fare hareketi mi kontrol et
        # (widget hareket edip cursor'un altına girdiğinde global pos değişmez → aktivite değil)
        if self._press_pos is None:
            if self._last_mouse_pos is None or self._last_mouse_pos != global_pos:
                self._last_mouse_pos = global_pos
                self.activity_detected.emit()
            return

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        delta = global_pos - self._press_pos
        if not self._is_dragging:
            if abs(delta.x()) > CLICK_DRAG_THRESHOLD or abs(delta.y()) > CLICK_DRAG_THRESHOLD:
                self._is_dragging = True
        if self._is_dragging:
            new_pos = self._press_window_pos + delta
            self.move(new_pos)
        event.accept()

    # enterEvent artık activity tetiklemiyor — widget cursor'ün altına
    # girdiğinde de tetikleniyordu, uyku bug'ının parçasıydı.

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging:
                self.clicked.emit()
            self._press_pos = None
            self._press_window_pos = None
            self._is_dragging = False
            event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self._menu_builder is None:
            return
        menu: QMenu = self._menu_builder()
        menu.exec(event.globalPos())
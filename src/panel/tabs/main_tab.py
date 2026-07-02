"""
main_tab.py
-----------
🐾 Ana sekme — hızlı komut butonları, pet durumu, konum bilgisi.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PySide6.QtGui import QFont


class MainTab(QWidget):
    """Ana kontrol sekmesi.

    Referanslar:
        haven_app: HavenApp — animator, window, current_pet erişimi için
    """

    def __init__(self, haven_app, parent=None):
        super().__init__(parent)
        self.haven_app = haven_app

        self._build_ui()

        # Durum bilgisini periyodik güncelle
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(500)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ---- Başlık ----
        title = QLabel(f"{self.haven_app.current_pet.emoji}  {self.haven_app.current_pet.name}")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        subtitle = QLabel(f"{self.haven_app.current_pet.species} · Quick controls")
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # ---- Durum kutusu ----
        status_box = QFrame()
        status_box.setStyleSheet("""
            QFrame {
                background: #f7f7f9;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        status_layout = QVBoxLayout(status_box)
        status_layout.setSpacing(6)

        self._status_label = QLabel("Durum: —")
        self._status_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        status_layout.addWidget(self._status_label)

        self._position_label = QLabel("Konum: —")
        self._position_label.setStyleSheet("font-size: 12px; color: #666;")
        status_layout.addWidget(self._position_label)

        layout.addWidget(status_box)

        # ---- Hızlı komut butonları ----
        commands_label = QLabel("Hızlı komutlar")
        commands_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #555; margin-top: 8px;")
        layout.addWidget(commands_label)

        grid = QGridLayout()
        grid.setSpacing(10)

        # (Buton metni, animator davranış adı veya özel eylem)
        buttons = [
            ("🚶 Yürü",       "walk"),
            ("🐰 Zıpla",      "happy_jump"),
            ("👀 Etrafa bak", "look_around"),
            ("😴 Esne",       "yawn"),
            ("💤 Uyu/Uyan",   "toggle_sleep"),
            ("👋 Selamla",    "bubble_wave"),
        ]

        for i, (text, action) in enumerate(buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(48)
            btn.setStyleSheet(self._button_style())
            btn.clicked.connect(lambda _checked=False, a=action: self._on_command(a))
            grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(grid)
        layout.addStretch()

    def _button_style(self) -> str:
        return """
            QPushButton {
                background: #fff;
                border: 1.5px solid #e0e0e0;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #f2f2f5;
                border-color: #c9c9d0;
            }
            QPushButton:pressed {
                background: #e8e8ed;
            }
        """

    # ---------------- olaylar ----------------

    def _on_command(self, action: str) -> None:
        """Buton tıklandı → ilgili komutu çalıştır."""
        animator = self.haven_app.animator
        window = self.haven_app.window

        if action == "walk":
            # Manuel yürüme başlat (rastgele yön ve mesafe)
            if not animator._is_walking and not animator._is_sleeping:
                animator._start_walking()

        elif action == "happy_jump":
            animator.trigger_behavior("happy_jump")

        elif action == "toggle_sleep":
            animator.toggle_sleep()

        elif action == "bubble_wave":
            window.show_bubble("👋", duration_ms=2000)

        elif action in animator.pet.behaviors:
            # look_around, yawn gibi davranış adları
            animator.trigger_behavior(action)

    def _refresh_status(self) -> None:
        """Durum ve konum bilgilerini güncelle."""
        animator = self.haven_app.animator
        window = self.haven_app.window

        if animator.is_sleeping():
            status = "💤 Uyuyor"
        elif animator._is_walking:
            direction = "sola" if animator._walk_direction == -1 else "sağa"
            status = f"🚶 Yürüyor ({direction})"
        elif animator._current_behavior is not None:
            status = f"🎭 {animator._current_behavior.name}"
        elif animator._is_click_jumping:
            status = "❤️ Mutlu"
        else:
            status = "😊 Boşta"

        self._status_label.setText(f"Durum: {status}")
        self._position_label.setText(f"Konum: X {window.x()}, Y {window.y()}")
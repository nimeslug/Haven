"""
main_tab.py
-----------
🐾 Ana sekme — hızlı komut butonları, pet durumu, konum, açlık göstergesi.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QProgressBar
)
from PySide6.QtGui import QFont


class MainTab(QWidget):
    def __init__(self, haven_app, parent=None):
        super().__init__(parent)
        self.haven_app = haven_app

        self._build_ui()

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
            }
        """)
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(6)

        self._status_label = QLabel("Durum: —")
        self._status_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        status_layout.addWidget(self._status_label)

        self._position_label = QLabel("Konum: —")
        self._position_label.setStyleSheet("font-size: 12px; color: #666;")
        status_layout.addWidget(self._position_label)

        layout.addWidget(status_box)

        # ---- Açlık göstergesi ----
        hunger_box = QFrame()
        hunger_box.setStyleSheet("""
            QFrame {
                background: #fff8ee;
                border: 1px solid #f0e0c0;
                border-radius: 10px;
            }
        """)
        hunger_layout = QVBoxLayout(hunger_box)
        hunger_layout.setContentsMargins(14, 12, 14, 12)
        hunger_layout.setSpacing(10)

        hunger_header = QHBoxLayout()
        hunger_title = QLabel("🥕 Beslenme")
        hunger_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #555;")
        hunger_header.addWidget(hunger_title)
        hunger_header.addStretch()
        self._hunger_percent_label = QLabel("—%")
        self._hunger_percent_label.setStyleSheet("font-size: 13px; color: #666;")
        hunger_header.addWidget(self._hunger_percent_label)
        hunger_layout.addLayout(hunger_header)

        self._hunger_bar = QProgressBar()
        self._hunger_bar.setMinimum(0)
        self._hunger_bar.setMaximum(100)
        self._hunger_bar.setValue(80)
        self._hunger_bar.setTextVisible(False)
        self._hunger_bar.setFixedHeight(14)
        self._hunger_bar.setStyleSheet(self._hunger_bar_style("#8BC34A"))
        hunger_layout.addWidget(self._hunger_bar)

        self._hunger_mood_label = QLabel("Ruh hali: —")
        self._hunger_mood_label.setStyleSheet("font-size: 12px; color: #666;")
        hunger_layout.addWidget(self._hunger_mood_label)

        feed_row = QHBoxLayout()
        feed_row.setSpacing(10)
        self._feed_btn = QPushButton("🥕  Havuç ver")
        self._feed_btn.setMinimumHeight(40)
        self._feed_btn.setMinimumWidth(140)
        self._feed_btn.setStyleSheet(self._button_style())
        self._feed_btn.clicked.connect(self._on_feed_clicked)
        feed_row.addWidget(self._feed_btn)

        self._feed_status_label = QLabel("")
        self._feed_status_label.setStyleSheet("font-size: 11px; color: #999;")
        feed_row.addWidget(self._feed_status_label)
        feed_row.addStretch()
        hunger_layout.addLayout(feed_row)

        layout.addWidget(hunger_box)

        # ---- Hızlı komut butonları ----
        commands_label = QLabel("Hızlı komutlar")
        commands_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #555; margin-top: 8px;")
        layout.addWidget(commands_label)

        grid = QGridLayout()
        grid.setSpacing(10)

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
            btn.setMinimumHeight(44)
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
            QPushButton:disabled {
                background: #f5f5f5;
                color: #aaa;
                border-color: #eee;
            }
        """

    def _hunger_bar_style(self, color: str) -> str:
        return f"""
            QProgressBar {{
                background: #f0e6d2;
                border-radius: 7px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 7px;
            }}
        """

    # ---------------- olaylar ----------------

    def _on_command(self, action: str) -> None:
        animator = self.haven_app.animator
        window = self.haven_app.window

        if action == "walk":
            if not animator._is_walking and not animator._is_sleeping:
                animator._start_walking()
        elif action == "happy_jump":
            animator.trigger_behavior("happy_jump")
        elif action == "toggle_sleep":
            animator.toggle_sleep()
        elif action == "bubble_wave":
            window.show_bubble("👋", duration_ms=2000)
        elif action in animator.pet.behaviors:
            animator.trigger_behavior(action)

    def _on_feed_clicked(self) -> None:
        animator = self.haven_app.animator
        if animator.feed():
            self._feed_status_label.setText("Verildi! ❤️")
        else:
            self._feed_status_label.setText("Henüz aç değil, biraz bekle")

    def _refresh_status(self) -> None:
        animator = self.haven_app.animator
        window = self.haven_app.window

        # Durum
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

        # Açlık
        hunger = animator.get_hunger()
        self._hunger_bar.setValue(int(hunger))
        self._hunger_percent_label.setText(f"{int(hunger)}%")

        mood = animator.get_hunger_mood()
        mood_labels = {
            "tok":     ("😊 Tok",     "#8BC34A"),   # yeşil
            "normal":  ("🙂 Normal",  "#FFC107"),   # sarı
            "aç":      ("😐 Aç",       "#FF9800"),   # turuncu
            "çok_aç": ("😟 Çok aç",   "#F44336"),   # kırmızı
        }
        label_text, bar_color = mood_labels.get(mood, ("—", "#8BC34A"))
        self._hunger_mood_label.setText(f"Ruh hali: {label_text}")
        self._hunger_bar.setStyleSheet(self._hunger_bar_style(bar_color))

        # Yem butonu — cooldown durumu
        can_feed = animator.can_feed()
        self._feed_btn.setEnabled(can_feed)
        if not can_feed:
            elapsed = time.time() - animator.get_last_fed_wall_ts()
            remaining = int((animator.HUNGER_FEED_COOLDOWN_MS / 1000) - elapsed)
            if remaining > 0:
                self._feed_status_label.setText(f"Sonraki yem: {remaining}s")
        elif self._feed_status_label.text().startswith("Sonraki yem"):
            self._feed_status_label.setText("")
"""
settings_tab.py
---------------
⚙️ Ayarlar sekmesi — davranış, etkileşim, görsel ayarlar (slider + toggle).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSlider, QCheckBox, QScrollArea
)
from PySide6.QtGui import QFont


class SettingsTab(QWidget):
    def __init__(self, haven_app, parent=None):
        super().__init__(parent)
        self.haven_app = haven_app

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(self._scroll)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._scroll.setWidget(self._content)

        self._build_ui()

    # ---------------- yardımcılar ----------------

    def _make_section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #555; margin-top: 6px;")
        return lbl

    def _make_slider_row(
        self, label: str, minimum: int, maximum: int, current: int,
        value_formatter, on_change
    ) -> QWidget:
        """Etiket + slider + değer göstergesi olan bir satır oluştur."""
        row = QFrame()
        row.setStyleSheet("QFrame { background: #f7f7f9; border-radius: 8px; }")
        rl = QVBoxLayout(row)
        rl.setContentsMargins(12, 10, 12, 10)
        rl.setSpacing(6)

        header = QHBoxLayout()
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet("font-size: 13px; color: #333;")
        header.addWidget(title_lbl)
        header.addStretch()
        value_lbl = QLabel(value_formatter(current))
        value_lbl.setStyleSheet("font-size: 12px; color: #666; font-weight: 600;")
        header.addWidget(value_lbl)
        rl.addLayout(header)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(current)
        slider.setFixedHeight(24)
        rl.addWidget(slider)

        def _on_slider(v):
            value_lbl.setText(value_formatter(v))
            on_change(v)

        slider.valueChanged.connect(_on_slider)
        return row

    def _make_toggle_row(self, label: str, current: bool, on_change) -> QWidget:
        row = QFrame()
        row.setStyleSheet("QFrame { background: #f7f7f9; border-radius: 8px; }")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 8, 12, 8)

        title_lbl = QLabel(label)
        title_lbl.setStyleSheet("font-size: 13px; color: #333;")
        rl.addWidget(title_lbl)
        rl.addStretch()

        chk = QCheckBox()
        chk.setChecked(current)
        chk.stateChanged.connect(lambda state: on_change(state == Qt.CheckState.Checked.value))
        rl.addWidget(chk)
        return row

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Başlık
        title = QLabel("⚙️  Ayarlar")
        tf = QFont()
        tf.setPointSize(20)
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        subtitle = QLabel("Kişisel tercihlerin — istediğin gibi ayarla")
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        prefs = self.haven_app.user_settings.settings.preferences
        pet = self.haven_app.current_pet

        # ---------------- Davranış ----------------
        layout.addWidget(self._make_section_title("🎭 Davranış"))

        # Yürüme sıklığı
        walk_prob = prefs.walk_probability if prefs.walk_probability is not None else pet.walk.walk_probability
        layout.addWidget(self._make_slider_row(
            "Yürüme sıklığı",
            minimum=0, maximum=100, current=int(walk_prob * 100),
            value_formatter=lambda v: f"%{v}",
            on_change=lambda v: self._set_pref("walk_probability", v / 100.0),
        ))

        # Uyku süresi
        sleep_sec = (prefs.sleep_idle_timeout_ms or pet.sleep.idle_timeout_ms) // 1000
        layout.addWidget(self._make_slider_row(
            "Uykuya girme süresi",
            minimum=15, maximum=300, current=int(sleep_sec),
            value_formatter=lambda v: f"{v} sn" if v < 60 else f"{v // 60} dk {v % 60} sn",
            on_change=lambda v: self._set_pref("sleep_idle_timeout_ms", v * 1000),
        ))

        # Baloncuk sıklığı
        bubble_min_sec = (prefs.bubble_min_interval_ms or pet.bubbles.min_interval_ms) // 1000
        layout.addWidget(self._make_slider_row(
            "Baloncuk sıklığı (min bekleme)",
            minimum=5, maximum=180, current=int(bubble_min_sec),
            value_formatter=lambda v: f"{v} sn",
            on_change=lambda v: self._set_bubble_intervals(v),
        ))

        # Açlık düşme hızı
        hunger_rate = prefs.hunger_decay_per_min if prefs.hunger_decay_per_min is not None else 1.0
        layout.addWidget(self._make_slider_row(
            "Açlık düşme hızı",
            minimum=1, maximum=30, current=int(hunger_rate * 10),
            value_formatter=lambda v: f"{v / 10:.1f} puan/dk",
            on_change=lambda v: self._set_pref("hunger_decay_per_min", v / 10.0),
        ))

        # ---------------- Etkileşim ----------------
        layout.addWidget(self._make_section_title("🎮 Etkileşim"))

        cursor_on = prefs.cursor_tracking_enabled if prefs.cursor_tracking_enabled is not None else True
        layout.addWidget(self._make_toggle_row(
            "Fareyi takip et (yön değiştirme)",
            current=cursor_on,
            on_change=lambda v: self._set_pref("cursor_tracking_enabled", v),
        ))

        flee_on = prefs.flee_enabled if prefs.flee_enabled is not None else pet.flee.enabled
        layout.addWidget(self._make_toggle_row(
            "Fareden kaçma",
            current=flee_on,
            on_change=lambda v: self._set_pref("flee_enabled", v),
        ))

        # ---------------- Görsel ----------------
        layout.addWidget(self._make_section_title("🎨 Görsel"))

        size = prefs.display_size if prefs.display_size is not None else pet.display_size
        layout.addWidget(self._make_slider_row(
            "Pet boyutu",
            minimum=100, maximum=350, current=int(size),
            value_formatter=lambda v: f"{v} px",
            on_change=lambda v: self._set_pref("display_size", v),
        ))

        # ---------------- Reset ----------------
        layout.addSpacing(8)
        reset_btn = QPushButton("🔄  Varsayılana dön")
        reset_btn.setMinimumHeight(40)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #fff;
                border: 1.5px solid #e0a0a0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
                color: #c04040;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: #fff0f0;
            }
        """)
        reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    # ---------------- olaylar ----------------

    def _set_pref(self, attr_name: str, value) -> None:
        """UserPreferences üzerindeki bir alanı set et + uygula + kaydet."""
        prefs = self.haven_app.user_settings.settings.preferences
        setattr(prefs, attr_name, value)
        self.haven_app.apply_and_save_preferences()

    def _set_bubble_intervals(self, min_sec: int) -> None:
        """Baloncuk min interval ayarlanınca max'ı otomatik 3x olarak set et."""
        prefs = self.haven_app.user_settings.settings.preferences
        prefs.bubble_min_interval_ms = min_sec * 1000
        prefs.bubble_max_interval_ms = min_sec * 3 * 1000
        self.haven_app.apply_and_save_preferences()

    def _on_reset(self) -> None:
        """Tüm kullanıcı tercihlerini sıfırla ve UI'yi yeniden inşa et."""
        # 1) HavenApp'in reset metodunu çağır (pet'i default'a döndürür)
        self.haven_app.reset_preferences_to_defaults()

        # 2) İçerik alanını yeniden yarat
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._scroll.setWidget(self._content)
        self._build_ui()
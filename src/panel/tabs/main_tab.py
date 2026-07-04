"""
main_tab.py
-----------
🐾 Ana sekme — durum, açlık, envanter, hızlı komutlar.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QProgressBar, QScrollArea, QInputDialog
)
from PySide6.QtGui import QFont

from inventory import FOODS, seconds_until_next_daily, can_claim_daily_reward


class MainTab(QWidget):
    def __init__(self, haven_app, parent=None):
        super().__init__(parent)
        self.haven_app = haven_app

        # Ana layout — scroll area barındırır
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer_layout.addWidget(scroll)

        # İçerik konteynerı (bunun içine _build_ui inşa edecek)
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        scroll.setWidget(self._content)

        self._build_ui()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(500)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # ---- Başlık (isim + düzenle butonu) ----
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        display_name = self.haven_app.get_display_name()
        self._title_label = QLabel(f"{self.haven_app.current_pet.emoji}  {display_name}")
        tf = QFont()
        tf.setPointSize(20)
        tf.setBold(True)
        self._title_label.setFont(tf)
        title_row.addWidget(self._title_label)

        self._edit_name_btn = QPushButton("✏️")
        self._edit_name_btn.setToolTip("İsmi düzenle")
        self._edit_name_btn.setFixedSize(32, 32)
        self._edit_name_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #eaeaef;
            }
        """)
        self._edit_name_btn.clicked.connect(self._on_edit_name)
        title_row.addWidget(self._edit_name_btn)

        title_row.addStretch()
        layout.addLayout(title_row)

        subtitle = QLabel(f"{self.haven_app.current_pet.species} · Quick controls")
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # ---- Durum kutusu ----
        status_box = QFrame()
        status_box.setStyleSheet("QFrame { background: #f7f7f9; border-radius: 10px; }")
        sl = QVBoxLayout(status_box)
        sl.setContentsMargins(14, 12, 14, 12)
        sl.setSpacing(6)

        self._status_label = QLabel("Durum: —")
        self._status_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        sl.addWidget(self._status_label)

        self._position_label = QLabel("Konum: —")
        self._position_label.setStyleSheet("font-size: 12px; color: #666;")
        sl.addWidget(self._position_label)

        layout.addWidget(status_box)

        # ---- Açlık göstergesi ----
        hunger_box = QFrame()
        hunger_box.setStyleSheet(
            "QFrame { background: #fff8ee; border: 1px solid #f0e0c0; border-radius: 10px; }"
        )
        hl = QVBoxLayout(hunger_box)
        hl.setContentsMargins(14, 14, 14, 14)
        hl.setSpacing(10)

        # Başlık satırı
        hh = QHBoxLayout()
        ht = QLabel("🥕 Beslenme")
        ht.setStyleSheet("font-size: 13px; font-weight: 700; color: #555;")
        hh.addWidget(ht)
        hh.addStretch()
        self._hunger_percent_label = QLabel("—%")
        self._hunger_percent_label.setStyleSheet("font-size: 13px; color: #666;")
        hh.addWidget(self._hunger_percent_label)
        hl.addLayout(hh)

        # Progress bar
        self._hunger_bar = QProgressBar()
        self._hunger_bar.setMinimum(0)
        self._hunger_bar.setMaximum(100)
        self._hunger_bar.setValue(80)
        self._hunger_bar.setTextVisible(False)
        self._hunger_bar.setFixedHeight(14)
        self._hunger_bar.setStyleSheet(self._hunger_bar_style("#8BC34A"))
        hl.addWidget(self._hunger_bar)

        # Mood label
        self._hunger_mood_label = QLabel("Ruh hali: —")
        self._hunger_mood_label.setStyleSheet("font-size: 12px; color: #666;")
        hl.addWidget(self._hunger_mood_label)

        # Yem butonları
        feed_row = QHBoxLayout()
        feed_row.setSpacing(8)
        self._feed_buttons = {}
        for food_key, food in FOODS.items():
            btn = QPushButton(f"{food.emoji}  {food.display_name} ver")
            btn.setMinimumHeight(36)
            btn.setStyleSheet(self._button_style())
            btn.clicked.connect(lambda _c=False, k=food_key: self._on_feed_clicked(k))
            feed_row.addWidget(btn)
            self._feed_buttons[food_key] = btn
        hl.addLayout(feed_row)

        # Yem durum yazısı
        self._feed_status_label = QLabel("")
        self._feed_status_label.setStyleSheet("font-size: 11px; color: #999;")
        self._feed_status_label.setMinimumHeight(16)
        hl.addWidget(self._feed_status_label)

        layout.addWidget(hunger_box)

        # ---- Envanter ----
        inv_box = QFrame()
        inv_box.setStyleSheet(
            "QFrame { background: #f0f9f0; border: 1px solid #d4e8d4; border-radius: 10px; }"
        )
        il = QVBoxLayout(inv_box)
        il.setContentsMargins(14, 14, 14, 14)
        il.setSpacing(10)

        # Başlık
        it = QLabel("🎒 Envanter")
        it.setStyleSheet("font-size: 13px; font-weight: 700; color: #555;")
        il.addWidget(it)

        # Yem sayıları
        counts_row = QHBoxLayout()
        counts_row.setSpacing(20)
        self._count_labels = {}
        for food_key, food in FOODS.items():
            lbl = QLabel(f"{food.emoji}  0")
            lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #333;")
            counts_row.addWidget(lbl)
            self._count_labels[food_key] = lbl
        counts_row.addStretch()
        il.addLayout(counts_row)

        # Günlük ödül satırı
        daily_row = QHBoxLayout()
        daily_row.setSpacing(10)
        self._daily_btn = QPushButton("🎁 Günlük havuç sepeti")
        self._daily_btn.setMinimumHeight(38)
        self._daily_btn.setMinimumWidth(200)
        self._daily_btn.setStyleSheet(self._button_style())
        self._daily_btn.clicked.connect(self._on_daily_clicked)
        daily_row.addWidget(self._daily_btn)

        self._daily_status_label = QLabel("")
        self._daily_status_label.setStyleSheet("font-size: 11px; color: #999;")
        daily_row.addWidget(self._daily_status_label, 1)
        il.addLayout(daily_row)

        layout.addWidget(inv_box)

        # ---- Hızlı komutlar ----
        commands_label = QLabel("Hızlı komutlar")
        commands_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #555;")
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
            btn.setMinimumHeight(42)
            btn.setStyleSheet(self._button_style())
            btn.clicked.connect(lambda _c=False, a=action: self._on_command(a))
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
                padding: 6px 14px;
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

    def _on_feed_clicked(self, food_key: str) -> None:
        animator = self.haven_app.animator
        inventory = self.haven_app.inventory
        if inventory is None:
            return
        # Envanterde var mı?
        if inventory.get(food_key) <= 0:
            self._feed_status_label.setText(f"{FOODS[food_key].display_name} yok! Günlük ödül al 🎁")
            return
        if not animator.can_feed():
            self._feed_status_label.setText("Henüz aç değil, biraz bekle")
            return
        # Envanterden düş + yemi ver
        inventory.consume(food_key)
        animator.feed(food_key)
        self.haven_app.on_pet_fed(food_key)
        self._feed_status_label.setText(f"{FOODS[food_key].emoji} verildi!")

    def _on_daily_clicked(self) -> None:
        added = self.haven_app.claim_daily_reward_if_possible()
        if not added:
            self._daily_status_label.setText("Yarın tekrar gel!")
            return
        parts = []
        for food_key, amount in added:
            parts.append(f"{FOODS[food_key].emoji}×{amount}")
        self._daily_status_label.setText("Aldın: " + ", ".join(parts))

    def _on_edit_name(self) -> None:
        """İsim düzenleme diyaloğu göster."""
        from PySide6.QtWidgets import QInputDialog

        current = self.haven_app.get_display_name()
        default_name = self.haven_app.current_pet.name
        new_name, ok = QInputDialog.getText(
            self,
            "İsmi düzenle",
            f"Yeni isim (boş bırakırsan varsayılana döner: {default_name})",
            text=current,
        )
        if not ok:
            return

        self.haven_app.set_display_name(new_name)

        # Başlığı hemen güncelle
        display = self.haven_app.get_display_name()
        emoji = self.haven_app.current_pet.emoji
        self._title_label.setText(f"{emoji}  {display}")

    def _refresh_status(self) -> None:
        animator = self.haven_app.animator
        window = self.haven_app.window
        inventory = self.haven_app.inventory

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
            "tok":     ("😊 Tok",     "#8BC34A"),
            "normal":  ("🙂 Normal",  "#FFC107"),
            "aç":      ("😐 Aç",       "#FF9800"),
            "çok_aç": ("😟 Çok aç",   "#F44336"),
        }
        label_text, bar_color = mood_labels.get(mood, ("—", "#8BC34A"))
        self._hunger_mood_label.setText(f"Ruh hali: {label_text}")
        self._hunger_bar.setStyleSheet(self._hunger_bar_style(bar_color))

        # Yem butonları (cooldown + envanter var mı)
        can_feed_now = animator.can_feed()
        for food_key, btn in self._feed_buttons.items():
            has_stock = inventory is not None and inventory.get(food_key) > 0
            btn.setEnabled(can_feed_now and has_stock)

        # Cooldown süre göstergesi
        if not can_feed_now:
            elapsed = time.time() - animator.get_last_fed_wall_ts()
            remaining = int((animator.HUNGER_FEED_COOLDOWN_MS / 1000) - elapsed)
            if remaining > 0:
                # Cooldown yazısı — mevcut "verildi" yazısını 2 sn sonra geçersiz kılar
                current_text = self._feed_status_label.text()
                if current_text.startswith(("🥕", "🍓", "🍎", "🌸")) and elapsed < 2:
                    pass  # ilk 2 sn "verildi!" görünsün
                else:
                    self._feed_status_label.setText(f"⏳ Sonraki yem: {remaining}s")
        else:
            # Cooldown bitti, geriye kalan sayaç metnini temizle
            if self._feed_status_label.text().startswith("⏳"):
                self._feed_status_label.setText("")

        # Envanter sayıları
        if inventory is not None:
            for food_key, lbl in self._count_labels.items():
                food = FOODS[food_key]
                lbl.setText(f"{food.emoji} {inventory.get(food_key)}")

        # Günlük ödül durumu
        state = self.haven_app.user_settings.settings.get_or_create_pet_state(
            self.haven_app.current_pet.folder_name
        )
        if can_claim_daily_reward(state.last_daily_reward_ts):
            self._daily_btn.setEnabled(True)
            if not self._daily_status_label.text().startswith(("Aldın", "Yarın")):
                self._daily_status_label.setText("Hazır! 🎁")
        else:
            self._daily_btn.setEnabled(False)
            remaining = seconds_until_next_daily(state.last_daily_reward_ts)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            self._daily_status_label.setText(f"Sonraki: {hours}s {minutes}dk")
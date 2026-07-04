"""
inventory_tab.py
----------------
🎒 Envanter sekmesi — tüm yemler, açıklamalar, stok, ver butonları.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtGui import QFont

from inventory import FOODS, can_claim_daily_reward, seconds_until_next_daily


class InventoryTab(QWidget):
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

        # Bunlar _build_ui içinde doldurulacak
        self._count_labels = {}
        self._feed_buttons = {}
        self._daily_btn = None
        self._daily_status_label = None
        self._feed_status_label = None
        self._streak_label = None
        self._streak_max_label = None

        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(500)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Başlık
        title = QLabel("🎒  Envanter")
        tf = QFont()
        tf.setPointSize(20)
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        subtitle = QLabel("Yem depon ve besleme kontrolü")
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # ---- Günlük ödül ----
        daily_box = QFrame()

        # ---- İpuçları ----
        tips_box = QFrame()
        tips_box.setStyleSheet(
            "QFrame { background: #eef5ff; border: 1px solid #c8d8ee; border-radius: 10px; }"
        )
        tl = QVBoxLayout(tips_box)
        tl.setContentsMargins(14, 10, 14, 10)
        tl.setSpacing(4)

        tips_title = QLabel("💡 Yem kazanmanın yolları")
        tips_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #4a6ea0;")
        tl.addWidget(tips_title)

        tips_text = QLabel(
            "🎁 <b>Günlük sepet:</b> Her gün al, seri oluştur → bonus ödüller  ·  "
            "❤️ <b>Mutlu et:</b> Pamuk'a tıkla, %20 şans havuç düşer  ·  "
            "🚶 <b>Yürüme sonu:</b> %20 şans havuç bulur  ·  "
            "👀 <b>Etrafa bakış:</b> %30 şans havuç, %5 şans papatya 🌸"
        )
        tips_text.setStyleSheet("font-size: 11px; color: #556788; line-height: 150%;")
        tips_text.setWordWrap(True)
        tips_text.setTextFormat(Qt.TextFormat.RichText)
        tl.addWidget(tips_text)

        layout.addWidget(tips_box)

        # ---- Streak göstergesi ----
        streak_box = QFrame()
        streak_box.setStyleSheet(
            "QFrame { background: #ffece0; border: 1px solid #ffcaa0; border-radius: 10px; }"
        )
        sl = QHBoxLayout(streak_box)
        sl.setContentsMargins(14, 12, 14, 12)
        sl.setSpacing(12)

        streak_title = QLabel("🔥 Günlük seri")
        streak_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #b0623a;")
        sl.addWidget(streak_title)
        sl.addStretch()

        self._streak_label = QLabel("0 gün")
        self._streak_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #d0703a;")
        sl.addWidget(self._streak_label)

        self._streak_max_label = QLabel("(En yüksek: 0)")
        self._streak_max_label.setStyleSheet("font-size: 11px; color: #a07050;")
        sl.addWidget(self._streak_max_label)

        layout.addWidget(streak_box)

        # Bonus eşiklerini göster
        bonus_hint = QLabel(
            "🎯 Bonus eşikleri: 3g → +2🥕  ·  7g → +1🍎  ·  14g → +2🍓  ·  30g → +1🌸"
        )
        bonus_hint.setStyleSheet("font-size: 10px; color: #999; margin-bottom: 4px;")
        bonus_hint.setWordWrap(True)
        layout.addWidget(bonus_hint)

        # ---- Günlük ödül ----
        daily_box = QFrame()
        daily_box.setStyleSheet(
            "QFrame { background: #fff8ee; border: 1px solid #f0d090; border-radius: 10px; }"
        )
        dl = QHBoxLayout(daily_box)
        dl.setContentsMargins(14, 12, 14, 12)
        dl.setSpacing(12)

        daily_title = QLabel("🎁 Günlük yem sepeti")
        daily_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #555;")
        dl.addWidget(daily_title)
        dl.addStretch()

        self._daily_status_label = QLabel("")
        self._daily_status_label.setStyleSheet("font-size: 12px; color: #666;")
        dl.addWidget(self._daily_status_label)

        self._daily_btn = QPushButton("Al 🎁")
        self._daily_btn.setMinimumHeight(36)
        self._daily_btn.setMinimumWidth(100)
        self._daily_btn.setStyleSheet(self._button_style())
        self._daily_btn.clicked.connect(self._on_daily_clicked)
        dl.addWidget(self._daily_btn)

        layout.addWidget(daily_box)

        # ---- Feed status ----
        self._feed_status_label = QLabel("")
        self._feed_status_label.setStyleSheet("font-size: 12px; color: #888;")
        self._feed_status_label.setMinimumHeight(18)
        layout.addWidget(self._feed_status_label)

        # ---- Yem kartları ----
        yems_title = QLabel("Yemler")
        yems_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #555; margin-top: 4px;")
        layout.addWidget(yems_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        row, col = 0, 0
        for food_key, food in FOODS.items():
            card = self._make_food_card(food_key, food)
            grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        layout.addLayout(grid)

        layout.addStretch()

    def _make_food_card(self, food_key: str, food) -> QWidget:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1.5px solid #e5e5e5;
                border-radius: 12px;
            }
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(8)

        head = QHBoxLayout()
        emoji_lbl = QLabel(food.emoji)
        emoji_font = QFont()
        emoji_font.setPointSize(28)
        emoji_lbl.setFont(emoji_font)
        head.addWidget(emoji_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_lbl = QLabel(food.display_name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #333;")
        name_col.addWidget(name_lbl)
        rarity_lbl = QLabel(food.rarity_label)
        rarity_lbl.setStyleSheet("font-size: 10px; color: #999;")
        name_col.addWidget(rarity_lbl)
        head.addLayout(name_col)

        head.addStretch()

        count_lbl = QLabel("×0")
        count_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #444;")
        head.addWidget(count_lbl)
        self._count_labels[food_key] = count_lbl

        cl.addLayout(head)

        desc_lbl = QLabel(food.description)
        desc_lbl.setStyleSheet("font-size: 11px; color: #666;")
        desc_lbl.setWordWrap(True)
        cl.addWidget(desc_lbl)

        boost_lbl = QLabel(f"🍽️ Açlık: +{int(food.hunger_boost)}")
        boost_lbl.setStyleSheet("font-size: 11px; color: #5a8a5a; font-weight: 600;")
        cl.addWidget(boost_lbl)

        feed_btn = QPushButton(f"{food.emoji} Ver")
        feed_btn.setMinimumHeight(34)
        feed_btn.setStyleSheet(self._button_style())
        feed_btn.clicked.connect(lambda _c=False, k=food_key: self._on_feed_clicked(k))
        cl.addWidget(feed_btn)
        self._feed_buttons[food_key] = feed_btn

        return card

    def _button_style(self) -> str:
        return """
            QPushButton {
                background: #fff;
                border: 1.5px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background: #f2f2f5;
                border-color: #b0b0b0;
            }
            QPushButton:disabled {
                background: #f5f5f5;
                color: #aaa;
                border-color: #eee;
            }
        """

    # ---------------- olaylar ----------------

    def _on_feed_clicked(self, food_key: str) -> None:
        animator = self.haven_app.animator
        inventory = self.haven_app.inventory
        if inventory is None:
            return
        if inventory.get(food_key) <= 0:
            self._feed_status_label.setText(f"{FOODS[food_key].display_name} yok!")
            return
        if not animator.can_feed():
            elapsed = time.time() - animator.get_last_fed_wall_ts()
            remaining = int((animator.HUNGER_FEED_COOLDOWN_MS / 1000) - elapsed)
            self._feed_status_label.setText(f"⏳ Cooldown: {remaining}s")
            return
        inventory.consume(food_key)
        animator.feed(food_key)
        self._feed_status_label.setText(
            f"{FOODS[food_key].emoji} {FOODS[food_key].display_name} verildi!"
        )

    def _on_daily_clicked(self) -> None:
        added = self.haven_app.claim_daily_reward_if_possible()
        if not added:
            self._daily_status_label.setText("Yarın tekrar gel!")
            return
        parts = [f"{FOODS[k].emoji}×{a}" for k, a in added]
        self._daily_status_label.setText("Aldın: " + ", ".join(parts))

    def _refresh(self) -> None:
        animator = self.haven_app.animator
        inventory = self.haven_app.inventory
        if inventory is None:
            return
        
        # Streak göstergesi güncelle
        state = self.haven_app.user_settings.settings.get_or_create_pet_state(
            self.haven_app.current_pet.folder_name
        )
        self._streak_label.setText(f"{state.streak_count} gün")
        self._streak_max_label.setText(f"(En yüksek: {state.max_streak_count})")

        state = self.haven_app.user_settings.settings.get_or_create_pet_state(
            self.haven_app.current_pet.folder_name
        )

        # Streak göstergesi
        self._streak_label.setText(f"{state.streak_count} gün")
        self._streak_max_label.setText(f"(En yüksek: {state.max_streak_count})")

        # Envanter sayıları
        for food_key, lbl in self._count_labels.items():
            lbl.setText(f"×{inventory.get(food_key)}")

        # Yem butonları — cooldown + stok
        can_feed_now = animator.can_feed()
        for food_key, btn in self._feed_buttons.items():
            has_stock = inventory.get(food_key) > 0
            btn.setEnabled(can_feed_now and has_stock)
            if not has_stock:
                btn.setText(f"{FOODS[food_key].emoji} Yok")
            else:
                btn.setText(f"{FOODS[food_key].emoji} Ver")

        # Günlük ödül durumu
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
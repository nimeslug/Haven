"""
main_window.py
--------------
Haven kontrol paneli — solda ikonlu tab bar, sağda içerik.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtGui import QFont, QIcon

from panel.tabs.main_tab import MainTab
from panel.tabs.placeholder_tab import PlaceholderTab


# (Sekme etiketi, tab id — hangi sekme sınıfını kullanacağız)
TABS = [
    ("🐾  Ana",           "main"),
    ("⚙️  Ayarlar",       "settings"),
    ("🎨  Görünüm",       "appearance"),
    ("💬  Sohbet",        "chat"),
    ("⏰  Hatırlatıcılar", "reminders"),
    ("ℹ️  Hakkında",      "about"),
]


class PanelWindow(QMainWindow):
    """Kontrol paneli ana penceresi."""

    def __init__(self, haven_app):
        super().__init__()
        self.haven_app = haven_app

        self.setWindowTitle("Haven — Kontrol Paneli")
        self.resize(820, 680)
        self.setMinimumSize(720, 600)

        # Pencere ikonu
        icon_path = haven_app.current_pet_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Sol: tab bar ----
        self._tab_list = QListWidget()
        self._tab_list.setFixedWidth(180)
        self._tab_list.setStyleSheet("""
            QListWidget {
                background: #f5f5f8;
                border: none;
                padding: 12px 8px;
                outline: 0;
            }
            QListWidget::item {
                padding: 12px 14px;
                margin: 2px 0;
                border-radius: 8px;
                color: #333;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background: #eaeaef;
            }
            QListWidget::item:selected {
                background: #d8d8e6;
                color: #222;
                font-weight: 600;
            }
        """)
        for label, _tab_id in TABS:
            QListWidgetItem(label, self._tab_list)
        self._tab_list.currentRowChanged.connect(self._on_tab_changed)
        root.addWidget(self._tab_list)

        # ---- Sağ: içerik alanı ----
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #ffffff;")
        for label, tab_id in TABS:
            widget = self._build_tab(tab_id, label)
            self._stack.addWidget(widget)
        root.addWidget(self._stack, 1)

        # İlk sekme seçili
        self._tab_list.setCurrentRow(0)

    def _build_tab(self, tab_id: str, label: str) -> QWidget:
        """Tab id'sine göre uygun widget'ı oluştur."""
        if tab_id == "main":
            return MainTab(self.haven_app)
        # Diğerleri şimdilik placeholder
        return PlaceholderTab(label)

    def _on_tab_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
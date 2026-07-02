"""
placeholder_tab.py
------------------
Henüz doldurulmamış sekmeler için placeholder.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont


class PlaceholderTab(QWidget):
    """Boş sekme — 'yakında geliyor' mesajı gösterir."""

    def __init__(self, tab_name: str, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("🚧")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel(f"{tab_name} — yakında")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #888; margin-top: 12px;")
        layout.addWidget(title)

        desc = QLabel("Bu sekme sonraki güncellemelerde eklenecek.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #aaa; margin-top: 4px;")
        layout.addWidget(desc)
"""
about_tab.py
------------
ℹ️ Hakkında sekmesi — nasıl oynanır, özellikler, sürüm, GitHub.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton
)
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl


APP_VERSION = "0.7.0"
GITHUB_URL = "https://github.com/YOUR_USERNAME/haven"  # kendi kullanıcı adınla değiştir


class AboutTab(QWidget):
    def __init__(self, haven_app, parent=None):
        super().__init__(parent)
        self.haven_app = haven_app

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll.setWidget(content)

        self._build_ui(content)

    def _build_ui(self, content: QWidget) -> None:
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # ---- Başlık ----
        title = QLabel("ℹ️  Haven")
        tf = QFont()
        tf.setPointSize(22)
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        subtitle = QLabel(f"Sürüm {APP_VERSION} · Pixel-art masaüstü peti")
        subtitle.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(subtitle)

        # GitHub butonu
        gh_row = QHBoxLayout()
        gh_btn = QPushButton("🐙  GitHub'da görüntüle")
        gh_btn.setMinimumHeight(36)
        gh_btn.setStyleSheet(self._button_style())
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        gh_row.addWidget(gh_btn)
        gh_row.addStretch()
        layout.addLayout(gh_row)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # ---- Nasıl Oynanır ----
        layout.addWidget(self._section_title("🎮 Nasıl Oynanır"))

        gameplay = self._info_box(
            "Pamuk masaüstünde yaşar. Ona iyi bak — beslersen mutlu olur, "
            "yalnız bırakırsan uyur ve acıkır. Etkileşim kurdukça yem kazanırsın."
        )
        layout.addWidget(gameplay)

        # ---- Beslenme ----
        layout.addWidget(self._section_title("🥕 Beslenme"))

        feeding = self._info_box(
            "Pamuk'un açlığı zamanla düşer (dakikada 1 puan). "
            "Beslenme durumuna göre ruh hali değişir:\n\n"
            "• 😊 <b>Tok</b> (70-100): mutlu, oynak\n"
            "• 🙂 <b>Normal</b> (40-70): sakin\n"
            "• 😐 <b>Aç</b> (20-40): sık 🥕 baloncukları çıkarır\n"
            "• 😟 <b>Çok aç</b> (0-20): 🥺 baloncuklarıyla yalvarır\n\n"
            "<b>Yem türleri:</b>\n"
            "• 🥕 Havuç: +8 açlık (yaygın)\n"
            "• 🍓 Çilek: +12 açlık (yaygın)\n"
            "• 🍎 Elma: +15 açlık (az bulunur)\n"
            "• 🌸 Papatya: +5 açlık (nadir, özel)"
        )
        layout.addWidget(feeding)

        # ---- Yem Kazanma ----
        layout.addWidget(self._section_title("🎁 Yem Kazanma Yolları"))

        earning = self._info_box(
            "<b>1. Günlük yem sepeti:</b> Envanter sekmesinden her 24 saatte bir al. "
            "Garanti 6🥕 + 2🍓, ayrıca %60 şansla 🍎, %25 şansla 🌸.\n\n"
            "<b>2. Günlük seri (streak):</b> Art arda gün girişi bonuslar getirir:\n"
            "  • 3 gün → +2🥕\n"
            "  • 7 gün → +1🍎\n"
            "  • 14 gün → +2🍓\n"
            "  • 30 gün → +1🌸\n\n"
            "48 saatten fazla ara verirsen seri sıfırlanır!\n\n"
            "<b>3. Etkileşim ödülleri:</b>\n"
            "  • Pamuk'a tıklayıp mutlu ettiğinde → %20 şansla 🥕\n"
            "  • Yürüme bitince → %20 şansla 🥕 (toprakta bulur)\n"
            "  • 'Etrafa bak' davranışı sonrası → %30 şansla 🥕"
        )
        layout.addWidget(earning)

        # ---- Kontroller ----
        layout.addWidget(self._section_title("🖱️ Kontroller"))

        controls = self._info_box(
            "<b>Pamuk üzerinde:</b>\n"
            "• Sol tık → Mutlu et (zıplar, kalp çıkar)\n"
            "• Sol tık + sürükle → Yerini değiştir\n"
            "• Sağ tık → Menü (uyu/uyan, panel aç, çıkış)\n\n"
            "<b>Sistem tepsisi (görev çubuğu):</b>\n"
            "• Sol tık → Göster/gizle\n"
            "• Sağ tık → Tüm kontroller\n\n"
            "<b>Fare takibi:</b>\n"
            "Fare Pamuk'un yakınına gelirse ona döner ve bakar. "
            "Çok yaklaşırsan ürkütür ve kaçar!"
        )
        layout.addWidget(controls)

        # ---- Ayarlar ----
        layout.addWidget(self._section_title("⚙️ Kişiselleştirme"))

        settings = self._info_box(
            "<b>Ayarlar sekmesi:</b> Davranışları slider'la ayarla — yürüme sıklığı, "
            "uyku süresi, baloncuk sıklığı, açlık hızı, pet boyutu.\n\n"
            "<b>İsim düzenleme:</b> Ana sekmede ✏️ ikonuna tıklayarak Pamuk'a istediğin ismi ver.\n\n"
            "<b>Kaydetme:</b> Tüm veriler `user_settings.json` içinde saklanır. "
            "Uygulama kapansa bile açlık, envanter ve seri korunur."
        )
        layout.addWidget(settings)

        # ---- Teşekkür ----
        thanks = QLabel(
            "<i>Geri bildirim ve katkılar için GitHub'a gel.</i>"
        )
        thanks.setStyleSheet("color: #999; font-size: 11px; margin-top: 16px;")
        thanks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thanks.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(thanks)

        layout.addStretch()

    # ---------------- yardımcılar ----------------

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #444; margin-top: 12px;"
        )
        return lbl

    def _info_box(self, text: str) -> QFrame:
        box = QFrame()
        box.setStyleSheet(
            "QFrame { background: #f7f7f9; border-radius: 10px; }"
        )
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 12, 14, 12)

        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; color: #444; line-height: 160%;")
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        bl.addWidget(lbl)

        return box

    def _button_style(self) -> str:
        return """
            QPushButton {
                background: #fff;
                border: 1.5px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: #f2f2f5;
                border-color: #b0b0b0;
            }
        """
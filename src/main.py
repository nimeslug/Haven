"""
main.py
-------
Haven - masaüstü pet uygulaması.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QCursor

from pet_loader import list_available_pets, load_pet, Pet
from animator import Animator
from overlay import OverlayWindow


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


class HavenApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        # ÖNEMLİ: Pencere gizlendiğinde uygulama kapanmasın (tray'de kalsın)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.available_pet_dirs = list_available_pets(ASSETS_DIR)
        if not self.available_pet_dirs:
            print(f"HATA: {ASSETS_DIR} altında pet bulunamadı.")
            sys.exit(1)

        self.current_pet: Pet = load_pet(self.available_pet_dirs[0])

        self.window = OverlayWindow(size=self.current_pet.display_size)
        self.window.set_menu_builder(self._build_menu)

        self.animator = Animator(self.current_pet)
        self.animator.frame_changed.connect(self.window.set_pixmap)
        self.animator.offset_changed.connect(self.window.set_y_offset)
        self.animator.position_delta.connect(self.window.move_by)
        self.animator.bubble_requested.connect(self._on_bubble_requested)

        self.window.clicked.connect(self._on_pet_clicked)
        self.window.activity_detected.connect(self.animator.notify_activity)
        self.window.walk_blocked.connect(self.animator.on_walk_blocked)

        self._place_window_bottom_right()

        # Fare takip zamanlayıcısı
        self._cursor_timer = QTimer()
        self._cursor_timer.timeout.connect(self._check_cursor_direction)
        self._cursor_timer.start(400)

        # System tray
        self._setup_tray()

    # ---------------- system tray ----------------

    def _setup_tray(self) -> None:
        """Görev çubuğunda tray ikonu oluştur."""
        # Tray ikonu için pet'in idle görselini kullan
        icon_path = ASSETS_DIR / self.current_pet.folder_name / "idle_open.png"
        icon = QIcon(str(icon_path))

        self.tray = QSystemTrayIcon(icon, parent=self.qt_app)
        self.tray.setToolTip(f"Haven - {self.current_pet.name}")
        self.tray.setContextMenu(self._build_tray_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _build_tray_menu(self) -> QMenu:
        """Tray sağ tık menüsünü oluştur."""
        menu = QMenu()

        # Göster/Gizle
        toggle_action = QAction("👁️  Göster / Gizle", menu)
        toggle_action.triggered.connect(self._toggle_visibility)
        menu.addAction(toggle_action)

        menu.addSeparator()

        # Uyut / Uyandır
        if self.animator.is_sleeping():
            sleep_action = QAction("🌞  Uyandır", menu)
        else:
            sleep_action = QAction("💤  Uyut", menu)
        sleep_action.triggered.connect(self._toggle_sleep_and_refresh_tray)
        menu.addAction(sleep_action)

        menu.addSeparator()

        # Pet değiştir
        pet_submenu = menu.addMenu("🐾  Pet değiştir")
        for pet_dir in self.available_pet_dirs:
            try:
                preview = load_pet(pet_dir)
                label = f"{preview.emoji}  {preview.name} ({preview.species})"
            except Exception:
                label = pet_dir.name

            action = QAction(label, menu)
            action.setCheckable(True)
            if pet_dir.name == self.current_pet.folder_name:
                action.setChecked(True)
            action.triggered.connect(lambda _checked=False, p=pet_dir: self._switch_pet(p))
            pet_submenu.addAction(action)

        menu.addSeparator()

        # Çıkış
        quit_action = QAction("❌  Çıkış", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        return menu

    def _refresh_tray_menu(self) -> None:
        """Menüyü yeniden inşa et (uyku durumu değişince)."""
        self.tray.setContextMenu(self._build_tray_menu())

    def _on_tray_activated(self, reason) -> None:
        """Tray ikonuna sol tıklandığında göster/gizle."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        """Pet penceresini göster veya gizle."""
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()

    def _toggle_sleep_and_refresh_tray(self) -> None:
        self.animator.toggle_sleep()
        self._refresh_tray_menu()

    def _quit(self) -> None:
        """Uygulamayı tamamen kapat."""
        self.tray.hide()
        self.qt_app.quit()

    # ---------------- konumlandırma ----------------

    def _place_window_bottom_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 40
        x = geo.right() - self.window.width() - margin
        y = geo.bottom() - self.window.height() - margin
        self.window.move(x, y)

    # ---------------- olaylar ----------------

    def _on_pet_clicked(self) -> None:
        self.animator.trigger_behavior("happy_jump")

    def _on_bubble_requested(self, emoji: str) -> None:
        self.window.show_bubble(emoji, duration_ms=self.current_pet.bubbles.duration_ms)

    def _check_cursor_direction(self) -> None:
        # Pencere gizliyse fare takibi yapma
        if not self.window.isVisible():
            return
        cursor_pos = QCursor.pos()
        pet_center_x = self.window.x() + self.window.width() // 2
        pet_center_y = self.window.y() + self.window.height() // 2
        self.animator.face_toward_cursor(
            cursor_pos.x(), cursor_pos.y(),
            pet_center_x, pet_center_y
        )

    # ---------------- pet sağ tık menüsü (tavşan üzerinde) ----------------

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        if self.animator.is_sleeping():
            sleep_action = QAction("🌞 Uyandır", menu)
        else:
            sleep_action = QAction("💤 Uyut", menu)
        sleep_action.triggered.connect(self._toggle_sleep_and_refresh_tray)
        menu.addAction(sleep_action)

        menu.addSeparator()

        pet_submenu = menu.addMenu("Pet değiştir")
        for pet_dir in self.available_pet_dirs:
            try:
                preview = load_pet(pet_dir)
                label = f"{preview.emoji}  {preview.name} ({preview.species})"
            except Exception:
                label = pet_dir.name

            action = QAction(label, menu)
            action.setCheckable(True)
            if pet_dir.name == self.current_pet.folder_name:
                action.setChecked(True)
            action.triggered.connect(lambda _checked=False, p=pet_dir: self._switch_pet(p))
            pet_submenu.addAction(action)

        menu.addSeparator()

        quit_action = QAction("Çıkış", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        return menu

    def _switch_pet(self, pet_dir: Path) -> None:
        if pet_dir.name == self.current_pet.folder_name:
            return
        new_pet = load_pet(pet_dir)
        self.current_pet = new_pet
        self.window.resize(new_pet.display_size, new_pet.display_size)
        self.animator.switch_pet(new_pet)
        # Tray ikonunu da yeni pet ile güncelle
        icon_path = ASSETS_DIR / new_pet.folder_name / "idle_open.png"
        self.tray.setIcon(QIcon(str(icon_path)))
        self.tray.setToolTip(f"Haven - {new_pet.name}")
        self._refresh_tray_menu()

    def run(self) -> int:
        self.window.show()
        self.animator.start()
        return self.qt_app.exec()


def main() -> int:
    app = HavenApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
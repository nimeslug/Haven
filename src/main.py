"""
main.py
-------
Haven - masaüstü pet uygulaması.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QCursor

from pet_loader import list_available_pets, load_pet, Pet
from animator import Animator
from overlay import OverlayWindow
from panel.main_window import PanelWindow


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


class HavenApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
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

        self._cursor_timer = QTimer()
        self._cursor_timer.timeout.connect(self._check_cursor_direction)
        self._cursor_timer.start(400)

        # Panel (henüz açılmadı)
        self._panel: Optional[PanelWindow] = None

        self._setup_tray()

    # ---------------- yardımcı ----------------

    def current_pet_icon_path(self) -> Optional[Path]:
        """Panel penceresinin ikonu için kullanılacak."""
        path = ASSETS_DIR / self.current_pet.folder_name / "idle_open.png"
        return path if path.exists() else None

    # ---------------- system tray ----------------

    def _setup_tray(self) -> None:
        icon_path = self.current_pet_icon_path()
        icon = QIcon(str(icon_path)) if icon_path else QIcon()

        self.tray = QSystemTrayIcon(icon, parent=self.qt_app)
        self.tray.setToolTip(f"Haven - {self.current_pet.name}")
        self.tray.setContextMenu(self._build_tray_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _build_tray_menu(self) -> QMenu:
        menu = QMenu()

        panel_action = QAction("⚙️  Kontrol Paneli", menu)
        panel_action.triggered.connect(self._open_panel)
        menu.addAction(panel_action)

        menu.addSeparator()

        toggle_action = QAction("👁️  Göster / Gizle", menu)
        toggle_action.triggered.connect(self._toggle_visibility)
        menu.addAction(toggle_action)

        menu.addSeparator()

        if self.animator.is_sleeping():
            sleep_action = QAction("🌞  Uyandır", menu)
        else:
            sleep_action = QAction("💤  Uyut", menu)
        sleep_action.triggered.connect(self._toggle_sleep_and_refresh_tray)
        menu.addAction(sleep_action)

        menu.addSeparator()

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

        quit_action = QAction("❌  Çıkış", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        return menu

    def _refresh_tray_menu(self) -> None:
        self.tray.setContextMenu(self._build_tray_menu())

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()

    def _toggle_sleep_and_refresh_tray(self) -> None:
        self.animator.toggle_sleep()
        self._refresh_tray_menu()

    def _quit(self) -> None:
        if self._panel is not None:
            self._panel.close()
        self.tray.hide()
        self.qt_app.quit()

    # ---------------- panel ----------------

    def _open_panel(self) -> None:
        """Kontrol panelini aç (yoksa oluştur, varsa öne getir)."""
        if self._panel is None:
            self._panel = PanelWindow(self)
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()

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
        if not self.window.isVisible():
            return
        cursor_pos = QCursor.pos()
        pet_center_x = self.window.x() + self.window.width() // 2
        pet_center_y = self.window.y() + self.window.height() // 2
        self.animator.face_toward_cursor(
            cursor_pos.x(), cursor_pos.y(),
            pet_center_x, pet_center_y
        )

    # ---------------- pet üzerinde sağ tık menüsü ----------------

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        panel_action = QAction("⚙️ Kontrol Paneli", menu)
        panel_action.triggered.connect(self._open_panel)
        menu.addAction(panel_action)

        menu.addSeparator()

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
        icon_path = self.current_pet_icon_path()
        if icon_path:
            self.tray.setIcon(QIcon(str(icon_path)))
        self.tray.setToolTip(f"Haven - {new_pet.name}")
        self._refresh_tray_menu()
        # Panel açıksa kapat, yeni pet ile yeniden oluşturulacak
        if self._panel is not None:
            self._panel.close()
            self._panel = None

    def run(self) -> int:
        self.window.show()
        self.animator.start()
        return self.qt_app.exec()


def main() -> int:
    app = HavenApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
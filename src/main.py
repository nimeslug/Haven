"""
main.py
-------
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtGui import QAction, QGuiApplication

from pet_loader import list_available_pets, load_pet, Pet
from animator import Animator
from overlay import OverlayWindow


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


class HavenApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(True)

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
        self.window.walk_blocked.connect(self.animator.on_walk_blocked)  # YENİ

        self._place_window_bottom_right()

    def _place_window_bottom_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 40
        x = geo.right() - self.window.width() - margin
        y = geo.bottom() - self.window.height() - margin
        self.window.move(x, y)

    def _on_pet_clicked(self) -> None:
        self.animator.trigger_behavior("happy_jump")

    def _on_bubble_requested(self, emoji: str) -> None:
        self.window.show_bubble(emoji, duration_ms=self.current_pet.bubbles.duration_ms)

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        # YENİ: uyut/uyandır
        if self.animator.is_sleeping():
            sleep_action = QAction("🌞 Uyandır", menu)
        else:
            sleep_action = QAction("💤 Uyut", menu)
        sleep_action.triggered.connect(self.animator.toggle_sleep)
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
        quit_action.triggered.connect(self.qt_app.quit)
        menu.addAction(quit_action)

        return menu

    def _switch_pet(self, pet_dir: Path) -> None:
        if pet_dir.name == self.current_pet.folder_name:
            return
        new_pet = load_pet(pet_dir)
        self.current_pet = new_pet
        self.window.resize(new_pet.display_size, new_pet.display_size)
        self.animator.switch_pet(new_pet)

    def run(self) -> int:
        self.window.show()
        self.animator.start()
        return self.qt_app.exec()


def main() -> int:
    app = HavenApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
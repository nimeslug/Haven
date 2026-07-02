"""
main.py
-------
Haven - masaüstü pet uygulaması.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QCursor

from pet_loader import list_available_pets, load_pet, Pet
from animator import Animator
from overlay import OverlayWindow
from panel.main_window import PanelWindow
from user_settings import UserSettingsStore
from inventory import (
    Inventory, can_claim_daily_reward, claim_daily_reward, try_happy_jump_reward
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
USER_SETTINGS_PATH = PROJECT_ROOT / "user_settings.json"


class HavenApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.available_pet_dirs = list_available_pets(ASSETS_DIR)
        if not self.available_pet_dirs:
            print(f"HATA: {ASSETS_DIR} altında pet bulunamadı.")
            sys.exit(1)

        self.current_pet: Pet = load_pet(self.available_pet_dirs[0])
        self.user_settings = UserSettingsStore(USER_SETTINGS_PATH)
        # Kullanıcı tercihlerini pet'e uygula (varsa)
        self._apply_preferences_to_pet()

        self.window = OverlayWindow(size=self.current_pet.display_size)
        self.window.set_menu_builder(self._build_menu)

        self.animator = Animator(self.current_pet)
        # Envanter — _restore_pet_state içinde set edilecek
        self.inventory: Optional[Inventory] = None
        # Açlık ve envanter durumunu geri yükle
        self._restore_pet_state()

        # Sinyaller: animator → pencere
        self.animator.frame_changed.connect(self.window.set_pixmap)
        self.animator.offset_changed.connect(self.window.set_y_offset)
        self.animator.position_delta.connect(self.window.move_by)
        self.animator.bubble_requested.connect(self._on_bubble_requested)
        self.animator.happy_jump_triggered.connect(self._on_happy_jump)

        # Sinyaller: pencere → animator
        self.window.clicked.connect(self._on_pet_clicked)
        self.window.activity_detected.connect(self.animator.notify_activity)
        self.window.walk_blocked.connect(self.animator.on_walk_blocked)

        self._place_window_bottom_right()

        # Fare takibi
        self._cursor_timer = QTimer()
        self._cursor_timer.timeout.connect(self._check_cursor_direction)
        self._cursor_timer.start(400)

        # Kalıcı kayıt — her 30 sn'de bir açlığı diske yaz
        self._save_timer = QTimer()
        self._save_timer.timeout.connect(self._persist_pet_state)
        self._save_timer.start(30000)

        # Panel referansı
        self._panel: Optional[PanelWindow] = None

        self._setup_tray()

    # ---------------- yardımcı ----------------

    def current_pet_icon_path(self) -> Optional[Path]:
        path = ASSETS_DIR / self.current_pet.folder_name / "idle_open.png"
        return path if path.exists() else None
    
    def get_display_name(self) -> str:
        """Pet'in gösterim ismini döndürür (kullanıcı verdiyse onu, yoksa default)."""
        state = self.user_settings.settings.get_or_create_pet_state(
            self.current_pet.folder_name
        )
        if state.custom_name.strip():
            return state.custom_name.strip()
        return self.current_pet.name
    
    def _apply_preferences_to_pet(self) -> None:
        """user_settings'teki override'ları çalışma zamanında pet'e uygula.
        Böylece animator hep 'effective' değerleri okur, kod değişmez."""
        prefs = self.user_settings.settings.preferences
        pet = self.current_pet

        if prefs.display_size is not None:
            pet.display_size = prefs.display_size
        if prefs.walk_probability is not None:
            pet.walk.walk_probability = prefs.walk_probability
        if prefs.sleep_idle_timeout_ms is not None:
            pet.sleep.idle_timeout_ms = prefs.sleep_idle_timeout_ms
        if prefs.bubble_min_interval_ms is not None:
            pet.bubbles.min_interval_ms = prefs.bubble_min_interval_ms
        if prefs.bubble_max_interval_ms is not None:
            pet.bubbles.max_interval_ms = prefs.bubble_max_interval_ms
        if prefs.flee_enabled is not None:
            pet.flee.enabled = prefs.flee_enabled

    def apply_and_save_preferences(self) -> None:
        """Panel'den ayar değişince çağrılır: pet'e uygula + diske yaz."""
        prefs = self.user_settings.settings.preferences

        # Açlık hızı — animator sabiti
        if prefs.hunger_decay_per_min is not None:
            self.animator.HUNGER_DECAY_PER_MIN = prefs.hunger_decay_per_min

        # Boyut değişikliği → pet'i yeni boyutla yeniden yükle
        old_size = self.current_pet.display_size
        new_size = prefs.display_size if prefs.display_size is not None else old_size

        if new_size != old_size:
            # Pet'i yeni boyutla yeniden yükle (sprite'lar yeniden ölçeklenir)
            pet_dir = ASSETS_DIR / self.current_pet.folder_name
            self._persist_pet_state()  # önce mevcut açlık/envanteri kaydet
            self.current_pet = load_pet(pet_dir, size_override=new_size)
            self._apply_preferences_to_pet()
            self.window.resize(new_size, new_size)
            self.animator.switch_pet(self.current_pet)
            self._restore_pet_state()
        else:
            # Sadece diğer ayarları uygula
            self._apply_preferences_to_pet()

        self.user_settings.save()

    def reset_preferences_to_defaults(self) -> None:
        """Tüm kullanıcı tercihlerini sıfırla ve pet'i pet.json'dan yeniden yükle."""
        from user_settings import UserPreferences

        # 1) Preferences'i tamamen sıfırla
        self.user_settings.settings.preferences = UserPreferences()

        # 2) Açlık düşme hızını default'a döndür (Animator sabiti)
        self.animator.HUNGER_DECAY_PER_MIN = 1.0

        # 3) Pet'i pet.json'dan yeniden yükle (tüm değerler default'a döner)
        pet_dir = ASSETS_DIR / self.current_pet.folder_name
        old_size = self.current_pet.display_size

        # Önce mevcut durumu kaydet
        self._persist_pet_state()

        self.current_pet = load_pet(pet_dir)
        new_size = self.current_pet.display_size

        # Boyut değiştiyse pencereyi resize et
        if new_size != old_size:
            self.window.resize(new_size, new_size)

        # Animator'ı yeni pet ile besle
        self.animator.switch_pet(self.current_pet)
        self._restore_pet_state()

        # Diske yaz
        self.user_settings.save()

    def set_display_name(self, new_name: str) -> None:
        """Kullanıcı özel isim atadı — kaydet."""
        state = self.user_settings.settings.get_or_create_pet_state(
            self.current_pet.folder_name
        )
        new_name = new_name.strip()
        # Boş veya default ile aynıysa custom_name'i temizle
        if not new_name or new_name == self.current_pet.name:
            state.custom_name = ""
        else:
            state.custom_name = new_name
        self.user_settings.save()
        # Bağlı olan her yeri güncelle
        display = self.get_display_name()
        self.tray.setToolTip(f"Haven - {display}")
        if self._panel is not None:
            self._panel.setWindowTitle(f"Haven — {display}")

    # ---------------- system tray ----------------

    def _setup_tray(self) -> None:
        icon_path = self.current_pet_icon_path()
        icon = QIcon(str(icon_path)) if icon_path else QIcon()

        self.tray = QSystemTrayIcon(icon, parent=self.qt_app)
        self.tray.setToolTip(f"Haven - {self.get_display_name()}")
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

    # ---------------- state persist ----------------

    def _restore_pet_state(self) -> None:
        """Mevcut pet için açlık, envanter ve son yem zamanını user_settings'ten yükle,
        offline süreye göre açlığı düşür."""
        state = self.user_settings.settings.get_or_create_pet_state(
            self.current_pet.folder_name
        )
        self.animator.set_hunger(state.hunger)
        self.animator.set_last_fed_wall_ts(state.last_fed_ts)

        # Offline geçen süreyi uygula
        if state.last_saved_ts > 0:
            elapsed = time.time() - state.last_saved_ts
            if elapsed > 0:
                self.animator.apply_offline_hunger_decay(elapsed)

        # Envanter'i kur — PetState.inventory sözlüğünü doğrudan referansla
        self.inventory = Inventory(state.inventory)

    def _persist_pet_state(self) -> None:
        """Şu anki pet durumunu user_settings'e yaz."""
        state = self.user_settings.settings.get_or_create_pet_state(
            self.current_pet.folder_name
        )
        state.hunger = self.animator.get_hunger()
        state.last_fed_ts = self.animator.get_last_fed_wall_ts()
        state.last_saved_ts = time.time()
        # inventory sözlüğü zaten state.inventory referansı — ayrıca yazmaya gerek yok
        self.user_settings.save()

    # ---------------- envanter ödülleri ----------------

    def _on_happy_jump(self) -> None:
        """Pamuk mutlu olduğunda envantere havuç düşme şansı."""
        if self.inventory is None:
            return
        if try_happy_jump_reward(self.inventory):
            self.window.show_bubble("🥕", duration_ms=1800)

    def claim_daily_reward_if_possible(self) -> List[Tuple[str, int]]:
        """Günlük ödülü envantere ekle. Eklenen öğelerin listesini döner."""
        if self.inventory is None:
            return []
        state = self.user_settings.settings.get_or_create_pet_state(
            self.current_pet.folder_name
        )
        if not can_claim_daily_reward(state.last_daily_reward_ts):
            return []
        added = claim_daily_reward(self.inventory)
        state.last_daily_reward_ts = time.time()
        self.user_settings.save()
        return added

    # ---------------- panel ----------------

    def _open_panel(self) -> None:
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
        prefs = self.user_settings.settings.preferences
        if prefs.cursor_tracking_enabled is False:
            return
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
        # Önce mevcut pet'in durumunu kaydet
        self._persist_pet_state()
        new_pet = load_pet(pet_dir)
        self.current_pet = new_pet
        self.window.resize(new_pet.display_size, new_pet.display_size)
        self.animator.switch_pet(new_pet)
        # Yeni pet'in durumunu geri yükle (envanter dahil)
        self._restore_pet_state()
        icon_path = self.current_pet_icon_path()
        if icon_path:
            self.tray.setIcon(QIcon(str(icon_path)))
        self.tray.setToolTip(f"Haven - {self.get_display_name()}")
        self._refresh_tray_menu()
        # Panel açıksa kapat, yeni pet ile yeniden oluşturulacak
        if self._panel is not None:
            self._panel.close()
            self._panel = None

    def _quit(self) -> None:
        self._persist_pet_state()
        if self._panel is not None:
            self._panel.close()
        self.tray.hide()
        self.qt_app.quit()

    def run(self) -> int:
        self.window.show()
        self.animator.start()
        return self.qt_app.exec()


def main() -> int:
    app = HavenApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
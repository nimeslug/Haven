"""
animator.py
-----------
Pet motoru: nefes alma, davranışlar, ayrık zıplamalarla yürüme, uyku, baloncuklar,
fare takibi, fareden kaçma, açlık ve beslenme.
"""
from __future__ import annotations

import math
import random
import time
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, QElapsedTimer
from PySide6.QtGui import QPixmap

from pet_loader import Pet, Behavior


class Animator(QObject):
    frame_changed = Signal(QPixmap, bool)
    offset_changed = Signal(int)
    position_delta = Signal(int, int)
    bubble_requested = Signal(str)
    happy_jump_triggered = Signal()  # tıklamayla mutlu zıplama olduğunda

    FLOAT_TICK_MS = 33
    CLICK_JUMP_DURATION_MS = 500
    CLICK_JUMP_HEIGHT_PX = 50

    # Açlık
    HUNGER_DECAY_PER_MIN: float = 1.0     # dakikada kaç puan düşer
    HUNGER_FEED_AMOUNT: float = 30.0      # (kullanılmıyor; hunger_boost FOODS'tan gelir)
    HUNGER_FEED_COOLDOWN_MS: int = 30000  # yem verildikten sonra bekleme
    HUNGER_MAX: float = 100.0
    HUNGER_MIN: float = 0.0

    def __init__(self, pet: Pet, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.pet = pet

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_elapsed = QElapsedTimer()
        self._last_tick_ms: int = 0

        self._frame_timer = QTimer(self)
        self._frame_timer.setSingleShot(True)
        self._frame_timer.timeout.connect(self._next_frame)

        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._show_random_bubble)

        self._current_behavior: Optional[Behavior] = None
        self._current_frame_index: int = 0

        # Yürüme (hop-based)
        self._is_walking: bool = False
        self._walk_remaining_distance: float = 0.0
        self._walk_direction: int = 1
        self._hop_phase: str = "idle"
        self._hop_elapsed_ms: int = 0
        self._hop_distance: float = 0.0
        self._hop_x_accumulated: int = 0

        # Yön
        self._facing_left: bool = False

        # Tıklama zıplaması
        self._is_click_jumping: bool = False
        self._click_jump_elapsed_ms: int = 0

        # Uyku
        self._is_sleeping: bool = False
        self._last_activity_ms: int = 0
        self._sleep_bubble_last_ms: int = 0

        # Kaçma (flee)
        self._last_flee_ms: int = -100000  # başta cooldown'dan geçsin

        # Açlık — dışarıdan set edilir (user_settings.py yükler)
        self._hunger: float = 80.0
        self._last_fed_wall_ts: float = 0.0
        self._hunger_tick_accum_ms: int = 0

    # ---------------- yaşam döngüsü ----------------

    def start(self) -> None:
        self._emit_current_frame(self.pet.idle_pixmap)
        self._tick_elapsed.start()
        self._last_tick_ms = 0
        self._last_activity_ms = 0
        self._tick_timer.start(self.FLOAT_TICK_MS)
        self._schedule_next_idle_event()
        self._schedule_next_bubble()

    def stop(self) -> None:
        self._tick_timer.stop()
        self._frame_timer.stop()
        self._idle_timer.stop()
        self._bubble_timer.stop()

    def switch_pet(self, new_pet: Pet) -> None:
        self.stop()
        self.pet = new_pet
        self._is_walking = False
        self._hop_phase = "idle"
        self._is_click_jumping = False
        self._is_sleeping = False
        self._facing_left = False
        self._current_behavior = None
        self.offset_changed.emit(0)
        self.start()

    # ---------------- dış API ----------------

    def trigger_behavior(self, name: str) -> None:
        self._wake_up_if_sleeping()

        if name == "happy_jump":
            self._is_click_jumping = True
            self._click_jump_elapsed_ms = 0
            self.bubble_requested.emit("❤️")
            self.happy_jump_triggered.emit()
            return

        if name not in self.pet.behaviors:
            return
        # Yürümeyi iptal et
        self._is_walking = False
        self._hop_phase = "idle"
        self._frame_timer.stop()
        self._current_behavior = self.pet.behaviors[name]
        self._current_frame_index = 0
        self._show_current_frame()

    def notify_activity(self) -> None:
        """SADECE kullanıcı etkileşimi burada çağrılmalı."""
        self._wake_up_if_sleeping()
        self._last_activity_ms = self._tick_elapsed.elapsed()

    def toggle_sleep(self) -> None:
        if self._is_sleeping:
            self._wake_up_if_sleeping()
        else:
            self._enter_sleep()

    def on_walk_blocked(self) -> None:
        if not self._is_walking:
            return
        self._is_walking = False
        self._hop_phase = "idle"
        self._walk_remaining_distance = 0.0
        self.offset_changed.emit(0)
        self._emit_current_frame(self.pet.idle_pixmap)
        self._schedule_next_idle_event()

    def is_sleeping(self) -> bool:
        return self._is_sleeping

    # ---------------- uyku ----------------

    def _check_sleep_transition(self, now_ms: int) -> None:
        if not self.pet.sleep.enabled or self._is_sleeping:
            return
        if self._is_walking or self._current_behavior is not None or self._is_click_jumping:
            return
        if now_ms - self._last_activity_ms >= self.pet.sleep.idle_timeout_ms:
            self._enter_sleep()

    def _enter_sleep(self) -> None:
        self._is_sleeping = True
        self._is_walking = False
        self._hop_phase = "idle"
        self._is_click_jumping = False
        self._idle_timer.stop()
        self._frame_timer.stop()
        self._current_behavior = None
        self._facing_left = False
        self._emit_current_frame(self.pet.sleep_pixmap)
        self.bubble_requested.emit("💤")
        self._sleep_bubble_last_ms = self._tick_elapsed.elapsed()

    def _wake_up_if_sleeping(self) -> None:
        if not self._is_sleeping:
            return
        self._is_sleeping = False
        self._last_activity_ms = self._tick_elapsed.elapsed()
        self._emit_current_frame(self.pet.idle_pixmap)
        self._schedule_next_idle_event()

    # ---------------- ana tick ----------------

    def _tick(self) -> None:
        now = self._tick_elapsed.elapsed()
        dt_ms = now - self._last_tick_ms
        self._last_tick_ms = now

        # Açlık — her dakikada bir HUNGER_DECAY_PER_MIN puan
        self._hunger_tick_accum_ms += dt_ms
        if self._hunger_tick_accum_ms >= 60000:
            self._hunger_tick_accum_ms -= 60000
            self._hunger = max(self.HUNGER_MIN, self._hunger - self.HUNGER_DECAY_PER_MIN)

        self._check_sleep_transition(now)

        if self._is_sleeping:
            sc = self.pet.sleep
            if sc.float_amplitude_px > 0:
                phase = (now / sc.float_period_ms) * 2 * math.pi
                offset = int(round(math.sin(phase) * sc.float_amplitude_px))
                self.offset_changed.emit(offset)
            if now - self._sleep_bubble_last_ms > 8000:
                self.bubble_requested.emit("💤")
                self._sleep_bubble_last_ms = now
            return

        total_offset = 0

        if (not self._is_walking and not self._is_click_jumping
                and self.pet.float_amplitude_px > 0):
            phase = (now / self.pet.float_period_ms) * 2 * math.pi
            offset = int(round(math.sin(phase) * self.pet.float_amplitude_px))
            total_offset += offset

        if self._is_walking:
            total_offset += self._advance_hop(dt_ms)

        if self._is_click_jumping:
            self._click_jump_elapsed_ms += dt_ms
            if self._click_jump_elapsed_ms >= self.CLICK_JUMP_DURATION_MS:
                self._is_click_jumping = False
            else:
                t = self._click_jump_elapsed_ms / self.CLICK_JUMP_DURATION_MS
                jump = 4 * t * (1 - t)
                total_offset += -int(round(jump * self.CLICK_JUMP_HEIGHT_PX))

        self.offset_changed.emit(total_offset)

    # ---------------- yürüme (hop) ----------------

    def _advance_hop(self, dt_ms: int) -> int:
        wc = self.pet.walk

        if self._hop_phase == "resting":
            self._hop_elapsed_ms += dt_ms
            if self._hop_elapsed_ms >= wc.hop_pause_ms:
                self._start_next_hop_if_needed()
            return 0

        if self._hop_phase != "airborne":
            return 0

        self._hop_elapsed_ms += dt_ms

        if self._hop_elapsed_ms >= wc.hop_duration_ms:
            leftover = int(round(self._hop_distance)) - self._hop_x_accumulated
            if leftover > 0:
                self.position_delta.emit(leftover * self._walk_direction, 0)
                self._hop_x_accumulated += leftover
            self._hop_phase = "resting"
            self._hop_elapsed_ms = 0
            self._emit_current_frame(self.pet.idle_pixmap)
            return 0

        t = self._hop_elapsed_ms / wc.hop_duration_ms

        target_x = int(round(self._hop_distance * t))
        dx = target_x - self._hop_x_accumulated
        if dx > 0:
            self.position_delta.emit(dx * self._walk_direction, 0)
            self._hop_x_accumulated = target_x

        y_offset = -int(round(4 * t * (1 - t) * wc.hop_height_px))

        frames = wc.frames
        if t < 0.15 or t > 0.85:
            pix = self.pet.idle_pixmap
        elif t < 0.55:
            pix = frames[0] if frames else self.pet.idle_pixmap
        else:
            pix = frames[1] if len(frames) > 1 else (frames[0] if frames else self.pet.idle_pixmap)
        self._emit_current_frame(pix)

        return y_offset

    def _start_walking(self) -> None:
        wc = self.pet.walk
        distance = random.randint(wc.min_distance_px, wc.max_distance_px)
        direction = random.choice([-1, 1])
        self._facing_left = (direction == -1)
        self._walk_remaining_distance = float(distance)
        self._walk_direction = direction
        self._is_walking = True
        self._start_next_hop_if_needed()

    def _start_next_hop_if_needed(self) -> None:
        wc = self.pet.walk
        if self._walk_remaining_distance <= 0.5:
            self._is_walking = False
            self._hop_phase = "idle"
            self._emit_current_frame(self.pet.idle_pixmap)
            self._schedule_next_idle_event()
            return

        self._hop_distance = min(float(wc.hop_distance_px), self._walk_remaining_distance)
        self._walk_remaining_distance -= self._hop_distance
        self._hop_elapsed_ms = 0
        self._hop_x_accumulated = 0
        self._hop_phase = "airborne"

    # ---------------- idle event ----------------

    def _schedule_next_idle_event(self) -> None:
        if self._is_walking or self._current_behavior is not None or self._is_sleeping:
            return
        ic = self.pet.idle_event
        wait_ms = random.randint(ic.min_interval_ms, ic.max_interval_ms)
        self._idle_timer.start(wait_ms)

    def _on_idle_timeout(self) -> None:
        if self._is_sleeping:
            return
        wc = self.pet.walk
        if wc.enabled and wc.frames and random.random() < wc.walk_probability:
            self._start_walking()
        else:
            self._start_random_behavior()

    # ---------------- baloncuk ----------------

    def _schedule_next_bubble(self) -> None:
        bc = self.pet.bubbles
        if not bc.random_emojis:
            return
        wait_ms = random.randint(bc.min_interval_ms, bc.max_interval_ms)
        self._bubble_timer.start(wait_ms)

    def _show_random_bubble(self) -> None:
        bc = self.pet.bubbles
        if not self._is_sleeping and bc.random_emojis:
            emoji = random.choice(bc.random_emojis)
            self.bubble_requested.emit(emoji)
        self._schedule_next_bubble()

    # ---------------- davranışlar ----------------

    def _start_random_behavior(self) -> None:
        candidates = [b for b in self.pet.behaviors.values() if b.weight > 0]
        if not candidates:
            self._schedule_next_idle_event()
            return
        weights = [b.weight for b in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]

        self._current_behavior = chosen
        self._current_frame_index = 0
        self._show_current_frame()

    def _show_current_frame(self) -> None:
        b = self._current_behavior
        if b is None:
            return
        if self._current_frame_index >= len(b.frames):
            self._current_behavior = None
            self._emit_current_frame(self.pet.idle_pixmap)
            self._schedule_next_idle_event()
            return
        self._emit_current_frame(b.frames[self._current_frame_index])
        self._frame_timer.start(b.frame_duration_ms)

    def _next_frame(self) -> None:
        self._current_frame_index += 1
        self._show_current_frame()

    def _emit_current_frame(self, pixmap: QPixmap) -> None:
        self.frame_changed.emit(pixmap, self._facing_left)

    # ---------------- fare takibi ----------------

    def face_toward_cursor(self, cursor_global_x: int, cursor_global_y: int,
                           pet_center_x: int, pet_center_y: int) -> None:
        """Fareye göre yön çevir + dikey bakma + yakınsa kaç."""
        if self._is_sleeping or self._current_behavior is not None:
            return

        dx = cursor_global_x - pet_center_x
        dy = cursor_global_y - pet_center_y
        distance = math.hypot(dx, dy)

        fc = self.pet.flee
        now = self._tick_elapsed.elapsed()

        # 1) Kaçma tetikleyicisi
        if (fc.enabled and not self._is_walking
                and distance < fc.trigger_distance_px
                and now - self._last_flee_ms > fc.cooldown_ms):
            self._start_flee(dx)
            self._last_flee_ms = now
            return

        # 2) Yürüyorsa hiçbir şey değiştirme
        if self._is_walking:
            return

        # 3) Dikey bakma
        VERTICAL_LOOK_HORIZONTAL_TOLERANCE = 80
        VERTICAL_LOOK_MIN_DY = 60

        if abs(dx) < VERTICAL_LOOK_HORIZONTAL_TOLERANCE:
            if dy < -VERTICAL_LOOK_MIN_DY and self.pet.look_up_pixmap is not None:
                self._emit_current_frame(self.pet.look_up_pixmap)
                return
            elif dy > VERTICAL_LOOK_MIN_DY and self.pet.look_down_pixmap is not None:
                self._emit_current_frame(self.pet.look_down_pixmap)
                return
            self._emit_current_frame(self.pet.idle_pixmap)
            return

        # 4) Yatay yön çevirme
        new_facing_left = (dx < 0)
        if new_facing_left != self._facing_left:
            self._facing_left = new_facing_left
        self._emit_current_frame(self.pet.idle_pixmap)

    def _start_flee(self, cursor_dx: float) -> None:
        """Fareden ters yöne bir hop kaç."""
        fc = self.pet.flee
        direction = -1 if cursor_dx > 0 else 1
        self._facing_left = (direction == -1)
        self._walk_remaining_distance = float(fc.flee_distance_px)
        self._walk_direction = direction
        self._is_walking = True
        self._start_next_hop_if_needed()

    # ---------------- açlık ----------------

    def get_hunger(self) -> float:
        return self._hunger

    def set_hunger(self, value: float) -> None:
        self._hunger = max(self.HUNGER_MIN, min(self.HUNGER_MAX, value))

    def get_last_fed_wall_ts(self) -> float:
        return self._last_fed_wall_ts

    def set_last_fed_wall_ts(self, ts: float) -> None:
        self._last_fed_wall_ts = ts

    def can_feed(self) -> bool:
        """Yem verilebilir mi (cooldown geçti mi)?"""
        elapsed_since_feed = (time.time() - self._last_fed_wall_ts) * 1000
        return elapsed_since_feed >= self.HUNGER_FEED_COOLDOWN_MS

    def feed(self, food_key: str = "carrot") -> bool:
        """Belirli tür yem ver. Başarılıysa True."""
        from inventory import FOODS  # döngüsel import olmasın diye burada
        if not self.can_feed():
            return False
        food = FOODS.get(food_key)
        if food is None:
            return False
        self._hunger = min(self.HUNGER_MAX, self._hunger + food.hunger_boost)
        self._last_fed_wall_ts = time.time()
        self._wake_up_if_sleeping()
        self.bubble_requested.emit(food.bubble_emoji)
        self._is_click_jumping = True
        self._click_jump_elapsed_ms = 0
        return True

    def get_hunger_mood(self) -> str:
        """Açlık seviyesine göre ruh hali etiketi."""
        h = self._hunger
        if h >= 70:
            return "tok"
        if h >= 40:
            return "normal"
        if h >= 20:
            return "aç"
        return "çok_aç"

    def apply_offline_hunger_decay(self, elapsed_seconds: float) -> None:
        """Uygulama kapalıyken geçen süreye göre açlık düşür."""
        if elapsed_seconds <= 0:
            return
        decay = (elapsed_seconds / 60.0) * self.HUNGER_DECAY_PER_MIN
        self._hunger = max(self.HUNGER_MIN, self._hunger - decay)
"""
user_settings.py
----------------
Kullanıcı kalıcı ayarları: pet durumu (açlık, envanter) + kullanıcı tercihleri.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, Optional
from typing import Dict, Optional, List


@dataclass
class PetState:
    """Bir pet'in kalıcı durumu."""
    hunger: float = 80.0
    last_saved_ts: float = 0.0
    last_fed_ts: float = 0.0
    inventory: Dict[str, int] = field(default_factory=lambda: {
        "carrot": 5, "strawberry": 3, "apple": 2, "daisy": 1
    })
    last_daily_reward_ts: float = 0.0
    streak_count: int = 0                     # kaç gündür üst üste giriyor
    max_streak_count: int = 0   
    daily_quests: List[dict] = field(default_factory=list)  # o günkü aktif görevler
    quests_generated_date: str = ""                          # görevlerin üretildiği gün (YYYY-MM-DD)              # en yüksek streak (istatistik için)
    custom_name: str = ""


@dataclass
class UserPreferences:
    """Kullanıcının ayarladığı tercihler. None = default'ı kullan.

    Her alan Optional — kullanıcı slider'a dokunmadıysa None kalır,
    böylece pet.json'daki değer geçerli olur.
    """
    # Boyut
    display_size: Optional[int] = None                # px
    # Yürüme
    walk_probability: Optional[float] = None          # 0.0 - 1.0
    # Uyku
    sleep_idle_timeout_ms: Optional[int] = None       # ms
    # Baloncuk
    bubble_min_interval_ms: Optional[int] = None      # ms
    bubble_max_interval_ms: Optional[int] = None      # ms
    # Açlık
    hunger_decay_per_min: Optional[float] = None      # puan/dk
    # Etkileşim (bool toggle)
    cursor_tracking_enabled: Optional[bool] = None
    flee_enabled: Optional[bool] = None


@dataclass
class UserSettings:
    pet_states: Dict[str, PetState] = field(default_factory=dict)
    preferences: UserPreferences = field(default_factory=UserPreferences)

    def get_or_create_pet_state(self, folder_name: str) -> PetState:
        if folder_name not in self.pet_states:
            self.pet_states[folder_name] = PetState(
                hunger=80.0,
                last_saved_ts=time.time(),
                last_fed_ts=0.0,
                inventory={"carrot": 8, "strawberry": 4, "apple": 2, "daisy": 3},
                last_daily_reward_ts=0.0,
            )
        return self.pet_states[folder_name]


class UserSettingsStore:
    def __init__(self, path: Path):
        self.path = path
        self.settings = self._load()

    def _load(self) -> UserSettings:
        if not self.path.exists():
            return UserSettings()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Pet states
            pet_states_data = data.get("pet_states", {})
            pet_states = {}
            for name, state in pet_states_data.items():
                state.setdefault("inventory", {"carrot": 3, "apple": 0})
                state.setdefault("last_daily_reward_ts", 0.0)
                state.setdefault("custom_name", "")
                state.setdefault("streak_count", 0)
                state.setdefault("max_streak_count", 0)
                state.setdefault("daily_quests", [])
                state.setdefault("quests_generated_date", "")
                pet_states[name] = PetState(**state)

            # Preferences
            prefs_data = data.get("preferences", {})
            preferences = UserPreferences(**prefs_data)

            return UserSettings(pet_states=pet_states, preferences=preferences)
        except Exception as e:
            print(f"UYARI: user_settings.json okunamadı: {e}")
            return UserSettings()

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "pet_states": {
                    name: asdict(state)
                    for name, state in self.settings.pet_states.items()
                },
                "preferences": asdict(self.settings.preferences),
            }
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"UYARI: user_settings.json yazılamadı: {e}")
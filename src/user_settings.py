"""
user_settings.py
----------------
Kullanıcı kalıcı ayarları: pet durumu (açlık) + envanter + günlük ödül.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict


@dataclass
class PetState:
    """Bir pet'in kalıcı durumu."""
    hunger: float = 80.0
    last_saved_ts: float = 0.0
    last_fed_ts: float = 0.0
    # Envanter: yem türü → adet
    inventory: Dict[str, int] = field(default_factory=lambda: {"carrot": 3, "apple": 0})
    # Günlük ödül son alınış zamanı (UNIX timestamp)
    last_daily_reward_ts: float = 0.0


@dataclass
class UserSettings:
    pet_states: Dict[str, PetState] = field(default_factory=dict)

    def get_or_create_pet_state(self, folder_name: str) -> PetState:
        if folder_name not in self.pet_states:
            self.pet_states[folder_name] = PetState(
                hunger=80.0,
                last_saved_ts=time.time(),
                last_fed_ts=0.0,
                inventory={"carrot": 3, "apple": 0},
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
            pet_states_data = data.get("pet_states", {})
            pet_states = {}
            for name, state in pet_states_data.items():
                # Eksik alanlar için varsayılan
                state.setdefault("inventory", {"carrot": 3, "apple": 0})
                state.setdefault("last_daily_reward_ts", 0.0)
                pet_states[name] = PetState(**state)
            return UserSettings(pet_states=pet_states)
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
                }
            }
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"UYARI: user_settings.json yazılamadı: {e}")
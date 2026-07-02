"""
inventory.py
------------
Yem envanteri ve beslenme kuralları.
Merkezi bir yerden yem türleri, etkileri, ödülleri yönetilir.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple


# Bir gün = 24 saat (saniye cinsinden)
DAY_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class FoodItem:
    """Bir yem türünün tanımı."""
    key: str                # "carrot", "apple"
    emoji: str              # 🥕, 🍎
    display_name: str       # "Havuç", "Elma"
    hunger_boost: float     # açlığa etkisi
    bubble_emoji: str       # yendiğinde çıkan baloncuk


# Merkezi yem kataloğu
FOODS: Dict[str, FoodItem] = {
    "carrot": FoodItem(
        key="carrot",
        emoji="🥕",
        display_name="Havuç",
        hunger_boost=8.0,
        bubble_emoji="🥕",
    ),
    "apple": FoodItem(
        key="apple",
        emoji="🍎",
        display_name="Elma",
        hunger_boost=15.0,
        bubble_emoji="🍎",
    ),
}


# Günlük ödül miktarları
DAILY_REWARD_CARROTS = 3
DAILY_REWARD_APPLE_CHANCE = 0.3      # %30
HAPPY_JUMP_CARROT_CHANCE = 0.15      # %15


class Inventory:
    """Bir pet'in envanterini yönetir.

    Değerler PetState.inventory sözlüğüne yansır — burada direkt referansla çalışıyoruz,
    böylece save/load sırasında ek dönüşüm gerekmez.
    """

    def __init__(self, inventory_dict: Dict[str, int]):
        # Eksik anahtarları sıfırla doldur
        for key in FOODS:
            inventory_dict.setdefault(key, 0)
        self._data = inventory_dict

    def get(self, food_key: str) -> int:
        return self._data.get(food_key, 0)

    def add(self, food_key: str, amount: int = 1) -> None:
        if food_key not in FOODS:
            return
        self._data[food_key] = self.get(food_key) + amount

    def consume(self, food_key: str) -> bool:
        """Bir tane yem tüket. Yeterli varsa True döner."""
        if self.get(food_key) <= 0:
            return False
        self._data[food_key] -= 1
        return True

    def total_items(self) -> int:
        return sum(self._data.values())


def can_claim_daily_reward(last_claim_ts: float) -> bool:
    """Günlük ödül alınabilir mi? (Son ödülden bu yana 24 saat geçti mi?)"""
    return (time.time() - last_claim_ts) >= DAY_SECONDS


def seconds_until_next_daily(last_claim_ts: float) -> int:
    """Sonraki günlük ödüle kaç saniye kaldı? (0 = hazır)"""
    remaining = DAY_SECONDS - (time.time() - last_claim_ts)
    return max(0, int(remaining))


def claim_daily_reward(inventory: Inventory) -> List[Tuple[str, int]]:
    """Günlük ödülü envanter'e ekle. Eklenen öğelerin listesini döner.
    Örn: [("carrot", 3), ("apple", 1)]
    """
    added = []
    inventory.add("carrot", DAILY_REWARD_CARROTS)
    added.append(("carrot", DAILY_REWARD_CARROTS))
    if random.random() < DAILY_REWARD_APPLE_CHANCE:
        inventory.add("apple", 1)
        added.append(("apple", 1))
    return added


def try_happy_jump_reward(inventory: Inventory) -> bool:
    """Mutlu zıplamayla havuç kazanma şansı. Kazanılırsa True."""
    if random.random() < HAPPY_JUMP_CARROT_CHANCE:
        inventory.add("carrot", 1)
        return True
    return False
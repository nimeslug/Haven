"""
inventory.py
------------
Yem envanteri ve beslenme kuralları.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple


DAY_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class FoodItem:
    key: str
    emoji: str
    display_name: str
    hunger_boost: float
    bubble_emoji: str
    description: str
    rarity_label: str


# Yem kataloğu
FOODS: Dict[str, FoodItem] = {
    "carrot": FoodItem(
        key="carrot",
        emoji="🥕",
        display_name="Havuç",
        hunger_boost=8.0,
        bubble_emoji="🥕",
        description="Pamuk'un baş yemeği. Bol miktarda bulunur, hafif atıştırmalık.",
        rarity_label="Yaygın",
    ),
    "strawberry": FoodItem(
        key="strawberry",
        emoji="🍓",
        display_name="Çilek",
        hunger_boost=12.0,
        bubble_emoji="🍓",
        description="Tatlı meyveler moral yükseltir. Yedikten sonra mutlu olur.",
        rarity_label="Yaygın",
    ),
    "apple": FoodItem(
        key="apple",
        emoji="🍎",
        display_name="Elma",
        hunger_boost=15.0,
        bubble_emoji="🍎",
        description="Besleyici ve doyurucu. Uzun süre tok tutar.",
        rarity_label="Az bulunur",
    ),
    "daisy": FoodItem(
        key="daisy",
        emoji="🌸",
        display_name="Papatya",
        hunger_boost=5.0,
        bubble_emoji="🌸",
        description="Fazla besleyici değil ama çok özel. Süper mutluluk verir.",
        rarity_label="Nadir",
    ),
}


# Günlük ödül dağılımı — bereketli sürüm
DAILY_REWARD_CARROTS = 6
DAILY_REWARD_STRAWBERRIES = 2
DAILY_REWARD_APPLE_CHANCE = 0.6
DAILY_REWARD_DAISY_CHANCE = 0.25
HAPPY_JUMP_CARROT_CHANCE = 0.2


class Inventory:
    """Bir pet'in envanterini yönetir."""

    def __init__(self, inventory_dict: Dict[str, int]):
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
        if self.get(food_key) <= 0:
            return False
        self._data[food_key] -= 1
        return True

    def total_items(self) -> int:
        return sum(self._data.values())


def can_claim_daily_reward(last_claim_ts: float) -> bool:
    return (time.time() - last_claim_ts) >= DAY_SECONDS


def seconds_until_next_daily(last_claim_ts: float) -> int:
    remaining = DAY_SECONDS - (time.time() - last_claim_ts)
    return max(0, int(remaining))


def claim_daily_reward(inventory: Inventory) -> List[Tuple[str, int]]:
    """Günlük ödülü envanter'e ekle."""
    added = []

    # Havuç (garanti)
    inventory.add("carrot", DAILY_REWARD_CARROTS)
    added.append(("carrot", DAILY_REWARD_CARROTS))

    # Çilek (garanti)
    inventory.add("strawberry", DAILY_REWARD_STRAWBERRIES)
    added.append(("strawberry", DAILY_REWARD_STRAWBERRIES))

    # Elma (%60 şans)
    if random.random() < DAILY_REWARD_APPLE_CHANCE:
        inventory.add("apple", 1)
        added.append(("apple", 1))

    # Papatya (%25 şans, o da tuttuysa %20 ihtimalle 2 tane)
    if random.random() < DAILY_REWARD_DAISY_CHANCE:
        amount = 2 if random.random() < 0.2 else 1
        inventory.add("daisy", amount)
        added.append(("daisy", amount))

    return added


def try_happy_jump_reward(inventory: Inventory) -> bool:
    if random.random() < HAPPY_JUMP_CARROT_CHANCE:
        inventory.add("carrot", 1)
        return True
    return False

# Streak bonus eşikleri (art arda gün sayısı → ekstra ödüller)
STREAK_BONUSES = [
    (3,  "carrot", 2),      # 3 gün → +2 havuç
    (7,  "apple", 1),       # 7 gün → +1 elma
    (14, "strawberry", 2),  # 14 gün → +2 çilek
    (30, "daisy", 1),       # 30 gün → +1 papatya
]


def calculate_streak_bonus(streak_count: int) -> List[Tuple[str, int]]:
    """Streak seviyesine göre ekstra ödülleri hesapla.
    Sadece o gün için geçerli eşikleri döner.
    Örneğin streak 7 ise → 3 ve 7 eşiklerinin bonusları gelir."""
    bonuses = []
    for threshold, food_key, amount in STREAK_BONUSES:
        if streak_count >= threshold:
            bonuses.append((food_key, amount))
    return bonuses


def update_streak(last_claim_ts: float, current_streak: int) -> int:
    """Yeni streak sayısını hesapla.

    - Aynı gün ise (24 saatten az) → değişmez (zaten alınmıştı)
    - 24-48 saat arası → streak +1 (art arda)
    - 48 saat üstü → streak sıfırlanır, yeniden 1'den başlar
    """
    elapsed = time.time() - last_claim_ts
    if elapsed < DAY_SECONDS:
        # Aynı gün — bu durum can_claim_daily_reward tarafından zaten engelleniyor
        return current_streak
    if elapsed < DAY_SECONDS * 2:
        # Art arda gün
        return current_streak + 1
    # Ara verdi
    return 1
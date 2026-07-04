"""
quests.py
---------
Günlük görev sistemi — görev üretme, takip, tamamlama.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from datetime import date
from typing import List, Dict, Optional


@dataclass
class QuestTemplate:
    """Bir görev şablonu — havuzdan seçilir, günlük görev üretmek için kullanılır."""
    key: str                    # "feed_3_times"
    title: str                  # "3 kere yem ver"
    target: int                 # 3 (hedef sayı)
    reward_food: str            # "carrot", "apple", vs.
    reward_amount: int          # 2 (kaç tane ödül)
    event_type: str             # "feed", "click", "look_around", "walk_end", "sleep_toggle", "different_food", "daily_claim"
    icon: str                   # emoji


# Görev havuzu — buradan rastgele 3 tanesi seçilir
QUEST_POOL: List[QuestTemplate] = [
    QuestTemplate(
        key="feed_3_times",
        title="Pamuk'a 3 kere yem ver",
        target=3,
        reward_food="carrot",
        reward_amount=3,
        event_type="feed",
        icon="🍽️",
    ),
    QuestTemplate(
        key="feed_5_times",
        title="Pamuk'a 5 kere yem ver",
        target=5,
        reward_food="carrot",
        reward_amount=5,
        event_type="feed",
        icon="🥄",
    ),
    QuestTemplate(
        key="pet_5_times",
        title="Pamuk'u 5 kere okşa (tıkla)",
        target=5,
        reward_food="carrot",
        reward_amount=2,
        event_type="click",
        icon="❤️",
    ),
    QuestTemplate(
        key="pet_10_times",
        title="Pamuk'u 10 kere okşa",
        target=10,
        reward_food="strawberry",
        reward_amount=2,
        event_type="click",
        icon="💗",
    ),
    QuestTemplate(
        key="look_around_3",
        title="Pamuk'a 3 kere 'etrafa bak' komutunu ver",
        target=3,
        reward_food="strawberry",
        reward_amount=1,
        event_type="look_around",
        icon="👀",
    ),
    QuestTemplate(
        key="walk_5",
        title="5 kere yürümesini bekle",
        target=5,
        reward_food="carrot",
        reward_amount=3,
        event_type="walk_end",
        icon="🚶",
    ),
    QuestTemplate(
        key="sleep_toggle_2",
        title="Pamuk'u 2 kere uyut ve uyandır",
        target=2,
        reward_food="strawberry",
        reward_amount=1,
        event_type="sleep_toggle",
        icon="💤",
    ),
    QuestTemplate(
        key="different_foods_3",
        title="3 farklı yem türü ver",
        target=3,
        reward_food="apple",
        reward_amount=1,
        event_type="different_food",
        icon="🌈",
    ),
    QuestTemplate(
        key="daily_claim",
        title="Günlük yem sepetini al",
        target=1,
        reward_food="strawberry",
        reward_amount=2,
        event_type="daily_claim",
        icon="🎁",
    ),
    QuestTemplate(
        key="yawn_2",
        title="Pamuk 2 kere esnesin",
        target=2,
        reward_food="daisy",
        reward_amount=1,
        event_type="behavior_yawn",
        icon="😴",
    ),
]


def get_template_by_key(key: str) -> Optional[QuestTemplate]:
    """Anahtardan şablonu bul."""
    for t in QUEST_POOL:
        if t.key == key:
            return t
    return None


def today_str() -> str:
    """Bugünün tarihi YYYY-MM-DD formatında."""
    return date.today().isoformat()


def should_regenerate_quests(last_generated_date: str) -> bool:
    """Görevleri yeniden üretmeli miyiz? (Yeni gün geldiyse)"""
    return last_generated_date != today_str()


def generate_daily_quests(count: int = 3) -> List[dict]:
    """Havuzdan rastgele N tane görev seç, ilerlemeleri sıfırla."""
    templates = random.sample(QUEST_POOL, min(count, len(QUEST_POOL)))
    quests = []
    for t in templates:
        quests.append({
            "key": t.key,
            "progress": 0,
            "completed": False,
            "claimed": False,           # ödül alındı mı
            "different_foods_seen": [], # sadece "different_food" tipi için
        })
    return quests


def record_event(quests: List[dict], event_type: str, food_key: Optional[str] = None) -> List[dict]:
    """Bir olay gerçekleştiğinde ilgili görevlerin ilerlemesini artır.
    Tamamlanan görevlerin listesini döner (henüz claim edilmemişler)."""
    newly_completed = []

    for q in quests:
        if q["completed"]:
            continue
        template = get_template_by_key(q["key"])
        if template is None:
            continue

        # Özel durum: farklı yem türleri sayacı
        if template.event_type == "different_food" and event_type == "feed":
            if food_key and food_key not in q["different_foods_seen"]:
                q["different_foods_seen"].append(food_key)
                q["progress"] = len(q["different_foods_seen"])
        elif template.event_type == event_type:
            q["progress"] = min(q["progress"] + 1, template.target)

        # Tamamlandı mı?
        if not q["completed"] and q["progress"] >= template.target:
            q["completed"] = True
            newly_completed.append(q)

    return newly_completed


def get_all_completed_unclaimed(quests: List[dict]) -> List[dict]:
    """Tamamlanmış ama henüz ödülü alınmamış görevleri döner."""
    return [q for q in quests if q["completed"] and not q["claimed"]]
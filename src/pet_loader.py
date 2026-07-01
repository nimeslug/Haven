"""
pet_loader.py
-------------
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from typing import Dict, List, Optional


@dataclass
class Behavior:
    name: str
    frames: List[QPixmap]
    frame_duration_ms: int
    weight: int
    min_interval_ms: int
    max_interval_ms: int


@dataclass
class WalkConfig:
    enabled: bool = False
    walk_probability: float = 0.3
    min_distance_px: int = 60
    max_distance_px: int = 200
    hop_distance_px: int = 50
    hop_duration_ms: int = 500
    hop_height_px: int = 35
    hop_pause_ms: int = 280
    frames: List[QPixmap] = field(default_factory=list)


@dataclass
class SleepConfig:
    enabled: bool = False
    idle_timeout_ms: int = 15000
    float_amplitude_px: int = 2
    float_period_ms: int = 4500

@dataclass
class FleeConfig:
    enabled: bool = False
    trigger_distance_px: int = 120
    flee_distance_px: int = 100
    cooldown_ms: int = 3000

@dataclass
class BubbleConfig:
    random_emojis: List[str] = field(default_factory=list)
    min_interval_ms: int = 30000
    max_interval_ms: int = 90000
    duration_ms: int = 2500


@dataclass
class IdleEventConfig:
    min_interval_ms: int = 3000
    max_interval_ms: int = 9000


@dataclass
class Pet:
    folder_name: str
    name: str
    species: str
    emoji: str
    display_size: int
    idle_pixmap: QPixmap
    sleep_pixmap: QPixmap
    behaviors: Dict[str, Behavior]
    float_amplitude_px: int
    float_period_ms: int
    walk: WalkConfig = field(default_factory=WalkConfig)
    sleep: SleepConfig = field(default_factory=SleepConfig)
    bubbles: BubbleConfig = field(default_factory=BubbleConfig)
    idle_event: IdleEventConfig = field(default_factory=IdleEventConfig)
    flee: FleeConfig = field(default_factory=FleeConfig)
    look_up_pixmap: Optional[QPixmap] = None
    look_down_pixmap: Optional[QPixmap] = None


def _load_pixmap(path: Path, size: int) -> QPixmap:
    pm = QPixmap(str(path))
    if pm.isNull():
        raise FileNotFoundError(f"Görsel yüklenemedi: {path}")
    return pm.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def load_pet(pet_dir: Path) -> Pet:
    config_path = pet_dir / "pet.json"
    if not config_path.exists():
        raise FileNotFoundError(f"pet.json bulunamadı: {pet_dir}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    size = int(config.get("display_size", 180))
    frame_cache: Dict[str, QPixmap] = {}

    def get_frame(filename: str) -> QPixmap:
        if filename not in frame_cache:
            frame_cache[filename] = _load_pixmap(pet_dir / filename, size)
        return frame_cache[filename]

    behaviors: Dict[str, Behavior] = {}
    for bname, bdata in config.get("behaviors", {}).items():
        frames = [get_frame(fn) for fn in bdata["frames"]]
        behaviors[bname] = Behavior(
            name=bname,
            frames=frames,
            frame_duration_ms=int(bdata["frame_duration_ms"]),
            weight=int(bdata.get("weight", 1)),
            min_interval_ms=int(bdata.get("min_interval_ms", 5000)),
            max_interval_ms=int(bdata.get("max_interval_ms", 15000)),
        )

    idle_pixmap = get_frame(config["idle_frame"])
    sleep_pixmap = get_frame(config.get("sleep_frame", config["idle_frame"]))
    float_cfg = config.get("float", {})
    walk_cfg = config.get("walk", {})
    sleep_cfg = config.get("sleep", {})
    bubbles_cfg = config.get("bubbles", {})
    idle_cfg = config.get("idle_event", {})

    walk_frames = [get_frame(fn) for fn in walk_cfg.get("frames", [])]

    return Pet(
        folder_name=pet_dir.name,
        name=config.get("name", pet_dir.name),
        species=config.get("species", ""),
        emoji=config.get("emoji", "🐾"),
        display_size=size,
        idle_pixmap=idle_pixmap,
        sleep_pixmap=sleep_pixmap,
        look_up_pixmap=get_frame(config["look_up_frame"]) if "look_up_frame" in config else None,
        look_down_pixmap=get_frame(config["look_down_frame"]) if "look_down_frame" in config else None,
        behaviors=behaviors,
        float_amplitude_px=int(float_cfg.get("amplitude_px", 0)),
        float_period_ms=int(float_cfg.get("period_ms", 2000)),
        walk=WalkConfig(
            enabled=bool(walk_cfg.get("enabled", False)),
            walk_probability=float(walk_cfg.get("walk_probability", 0.3)),
            min_distance_px=int(walk_cfg.get("min_distance_px", 60)),
            max_distance_px=int(walk_cfg.get("max_distance_px", 200)),
            hop_distance_px=int(walk_cfg.get("hop_distance_px", 50)),
            hop_duration_ms=int(walk_cfg.get("hop_duration_ms", 500)),
            hop_height_px=int(walk_cfg.get("hop_height_px", 35)),
            hop_pause_ms=int(walk_cfg.get("hop_pause_ms", 280)),
            frames=walk_frames,
        ),
        sleep=SleepConfig(
            enabled=bool(sleep_cfg.get("enabled", False)),
            idle_timeout_ms=int(sleep_cfg.get("idle_timeout_ms", 15000)),
            float_amplitude_px=int(sleep_cfg.get("float_amplitude_px", 2)),
            float_period_ms=int(sleep_cfg.get("float_period_ms", 4500)),
        ),
        flee=FleeConfig(
            enabled=bool(config.get("flee", {}).get("enabled", False)),
            trigger_distance_px=int(config.get("flee", {}).get("trigger_distance_px", 120)),
            flee_distance_px=int(config.get("flee", {}).get("flee_distance_px", 100)),
            cooldown_ms=int(config.get("flee", {}).get("cooldown_ms", 3000)),
        ),
        bubbles=BubbleConfig(
            random_emojis=list(bubbles_cfg.get("random_emojis", [])),
            min_interval_ms=int(bubbles_cfg.get("min_interval_ms", 30000)),
            max_interval_ms=int(bubbles_cfg.get("max_interval_ms", 90000)),
            duration_ms=int(bubbles_cfg.get("duration_ms", 2500)),
        ),
        idle_event=IdleEventConfig(
            min_interval_ms=int(idle_cfg.get("min_interval_ms", 3000)),
            max_interval_ms=int(idle_cfg.get("max_interval_ms", 9000)),
        ),
    )


def list_available_pets(assets_dir: Path) -> List[Path]:
    if not assets_dir.exists():
        return []
    return sorted([
        p for p in assets_dir.iterdir()
        if p.is_dir() and (p / "pet.json").exists()
    ])
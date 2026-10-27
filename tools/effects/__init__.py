from __future__ import annotations

from typing import Type
from .base import VisualEffect
from .waveform import WaveformEffect

EFFECT_REGISTRY: dict[str, Type[VisualEffect]] = {
    "waveform": WaveformEffect,
}


def register(name: str, cls: Type[VisualEffect]) -> None:
    """Register a new visual effect class."""
    EFFECT_REGISTRY[name] = cls


__all__ = ["VisualEffect", "WaveformEffect", "EFFECT_REGISTRY", "register"]

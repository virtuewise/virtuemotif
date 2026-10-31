from __future__ import annotations

from .base import VisualEffect
from .waveform import WaveformEffect

EFFECT_REGISTRY: dict[str, type[VisualEffect]] = {
    "waveform": WaveformEffect,
}


def register(name: str, cls: type[VisualEffect]) -> None:
    """Register a new visual effect class."""
    EFFECT_REGISTRY[name] = cls


__all__ = ["EFFECT_REGISTRY", "VisualEffect", "WaveformEffect", "register"]

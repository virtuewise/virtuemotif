from __future__ import annotations

from typing import Any, Dict
from PIL import Image

class VisualEffect:
    """Base class for all visual‑lyric effects.

    Sub‑classes must implement :meth:`apply` which receives a chunk of audio data
    and a list of previously rendered frames, and returns a ``PIL.Image`` for the
    current frame.
    """

    def __init__(self, params: Dict[str, Any] | None = None) -> None:
        self.params = params or {}

    def apply(self, audio_chunk: Any, prev_frames: list[Image.Image]) -> Image.Image:
        """Render a frame.

        Args:
            audio_chunk: Arbitrary representation of the audio for the current
                time slice (e.g., a NumPy array of samples).
            prev_frames: List of previously rendered ``PIL.Image`` objects –
                useful for effects that need temporal context.
        Returns:
            A fully rendered ``PIL.Image``.
        """
        raise NotImplementedError

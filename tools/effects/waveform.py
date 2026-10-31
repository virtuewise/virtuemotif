from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .base import VisualEffect


class WaveformEffect(VisualEffect):
    """Render a simple waveform synced to RMS of the audio chunk.

    Expected params (all optional):
        - ``resolution``: "WxH" string or tuple of ints (default from defaults).
        - ``colour``: hex colour for the line (default ``#ff8c00``).
        - ``amplitude``: multiplier for vertical scaling (default 0.8).
    """

    def apply(self, audio_chunk, prev_frames):
        # Resolve resolution
        res = self.params.get("resolution", "1920x1080")
        if isinstance(res, str):
            width, height = map(int, res.split("x"))
        else:
            width, height = res
        colour = self.params.get("colour", "#ff8c00")
        amp = self.params.get("amplitude", 0.8)

        # Compute RMS of the chunk (fallback to 0 if empty)
        rms = float(np.sqrt(np.mean(np.square(audio_chunk)))) if hasattr(audio_chunk, "size") and audio_chunk.size else 0.0
        # Map RMS (0‑1) to vertical position
        y_center = height // 2
        y_offset = int((rms - 0.5) * height * amp)
        y = y_center - y_offset

        img = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(img)
        draw.line([(0, y), (width, y)], fill=colour, width=3)
        return img

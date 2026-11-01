"""Audio intelligence: beat grid, energy contour, and structural cue extraction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


def _frame_signal(samples: np.ndarray, window_size: int, hop_size: int) -> np.ndarray:
    if samples.size < 1:
        raise ValueError("audio contains no samples")
    if window_size < 32 or hop_size < 1:
        raise ValueError("window_size must be >= 32 and hop_size must be positive")
    frame_count = max(1, 1 + int(np.ceil(max(0, samples.size - window_size) / hop_size)))
    padded_size = (frame_count - 1) * hop_size + window_size
    padded = np.pad(samples, (0, max(0, padded_size - samples.size)))
    return np.lib.stride_tricks.sliding_window_view(padded, window_size)[::hop_size][:frame_count]


def _estimate_tempo(onset: np.ndarray, frame_rate: float) -> tuple[float | None, float, int | None]:
    if onset.size < int(frame_rate * 4):
        return None, 0.0, None
    envelope = onset.astype(np.float64) - float(np.mean(onset))
    scale = float(np.linalg.norm(envelope))
    if scale < 1e-9:
        return None, 0.0, None
    n_fft = 1 << (2 * envelope.size - 1).bit_length()
    spectrum = np.fft.rfft(envelope, n=n_fft)
    autocorr = np.fft.irfft(spectrum * np.conjugate(spectrum), n=n_fft)[: envelope.size]
    if autocorr[0] <= 1e-12:
        return None, 0.0, None
    autocorr /= autocorr[0]
    min_lag = max(1, int(frame_rate * 60 / 180))
    max_lag = min(envelope.size - 1, int(np.ceil(frame_rate * 60 / 60)))
    if max_lag < min_lag:
        return None, 0.0, None
    lag = min_lag + int(np.argmax(autocorr[min_lag : max_lag + 1]))
    # Resolve common half-time bias: when the shorter (double-tempo) period is
    # almost as strongly supported, prefer it. This is intentionally a modest
    # heuristic; ambiguous real music can still need a human tempo correction.
    half_lag = lag // 2
    if half_lag >= min_lag and autocorr[half_lag] >= autocorr[lag] * 0.75:
        lag = half_lag
    confidence = float(np.clip(autocorr[lag], 0.0, 1.0))
    if confidence < 0.02:
        return None, round(confidence, 3), None
    return round(60.0 * frame_rate / lag, 2), round(confidence, 3), lag


def analyze_samples(
    samples: np.ndarray,
    sample_rate: int,
    *,
    window_size: int = 2048,
    hop_size: int = 512,
) -> dict[str, Any]:
    """Analyze mono floating-point PCM and return versioned, timestamped cues."""
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")
    audio = np.asarray(samples, dtype=np.float32)
    if audio.ndim != 1:
        raise ValueError("samples must be mono (one-dimensional)")
    if audio.size == 0:
        raise ValueError("audio contains no samples")
    if not np.isfinite(audio).all():
        raise ValueError("audio contains NaN or infinite samples")

    duration = audio.size / sample_rate
    frames = _frame_signal(audio, window_size, hop_size)
    window = np.hanning(window_size).astype(np.float32)
    weighted = frames * window[None, :]
    rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    magnitude = np.abs(np.fft.rfft(weighted, axis=1)).astype(np.float32)
    positive_flux = np.maximum(np.diff(magnitude, axis=0, prepend=magnitude[:1]), 0).sum(axis=1)
    frame_rate = sample_rate / hop_size
    times = np.arange(frames.shape[0], dtype=np.float64) / frame_rate

    onset_scale = float(np.percentile(positive_flux, 95))
    onset = positive_flux / max(onset_scale, 1e-9)
    bpm, tempo_confidence, beat_lag = _estimate_tempo(onset, frame_rate)

    beat_times: list[float] = []
    if beat_lag is not None:
        # Choose the phase with strongest onset support; use a four-beat bar as
        # a rendering convention, not as a claim that the song's meter is known.
        period = beat_lag
        scores = np.array([
            float(onset[phase::period].sum()) for phase in range(period)
        ])
        phase = int(np.argmax(scores))
        beat_frames = np.arange(phase, len(onset), period)
        beat_times = [round(float(frame / frame_rate), 3) for frame in beat_frames if frame / frame_rate < duration]

    energy_max = float(np.max(rms))
    energy_norm = rms / max(energy_max, 1e-9)
    seconds = np.arange(int(np.ceil(duration)), dtype=np.int32)
    energy_curve = []
    for second in seconds:
        mask = (times >= second) & (times < second + 1)
        if np.any(mask):
            energy_curve.append({"time": int(second), "rms": round(float(np.mean(energy_norm[mask])), 4)})

    events: list[dict[str, Any]] = []
    for index in range(1, len(onset) - 1):
        if onset[index] >= onset[index - 1] and onset[index] > onset[index + 1] and onset[index] >= 0.8:
            events.append({"time": round(float(times[index]), 3), "type": "onset", "strength": round(float(onset[index]), 3)})
    for index in range(1, len(energy_curve)):
        delta = energy_curve[index]["rms"] - energy_curve[index - 1]["rms"]
        if delta >= 0.18:
            events.append({"time": energy_curve[index]["time"], "type": "energy-rise", "strength": round(delta, 3)})
        elif delta <= -0.18:
            events.append({"time": energy_curve[index]["time"], "type": "energy-drop", "strength": round(abs(delta), 3)})

    downbeats = [time for index, time in enumerate(beat_times) if index % 4 == 0]
    return {
        "schema_version": 1,
        "duration": round(duration, 3),
        "sample_rate": sample_rate,
        "analysis": {
            "method": "numpy-rms-spectral-flux-autocorrelation",
            "frame_rate": round(frame_rate, 3),
            "meter_assumption": "4/4 grid for visual cueing; not meter detection",
        },
        "tempo": {"bpm": bpm, "confidence": tempo_confidence},
        "beats": beat_times,
        "downbeats": downbeats,
        "energy_curve": energy_curve,
        "events": sorted(events, key=lambda event: event["time"]),
        "review_required": True,
    }


def analyze_file(path: str | Path) -> dict[str, Any]:
    """Read an audio file with SoundFile and analyze it as mono PCM."""
    try:
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError("Audio file decoding requires SoundFile: pip install soundfile") from exc
    audio, sample_rate = sf.read(str(path), dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1, dtype=np.float32)
    return analyze_samples(audio, int(sample_rate))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract beat, energy, and transition cues from audio.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path (default: timing/<stem>.audio-intelligence.json)")
    args = parser.parse_args()
    if not args.audio.is_file():
        parser.error(f"audio file not found: {args.audio}")
    output = args.output or Path("timing") / f"{args.audio.stem}.audio-intelligence.json"
    try:
        result = analyze_file(args.audio)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"audio-intelligence: {exc}\n")
    print(f"Analyzed {result['duration']:.2f}s: BPM={result['tempo']['bpm']} cues={len(result['events'])} -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

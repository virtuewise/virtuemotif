"""Multilingual auto-lyrics engine with streaming ASR output and language hints."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

# Conservative lexical hints; ambiguous short lines remain "und".
_LANGUAGE_MARKERS: dict[str, set[str]] = {
    "en": {"the", "and", "you", "your", "with", "love", "heart", "we", "are", "is", "my"},
    "sn": {"ndiri", "uri", "iwe", "isu", "rudo", "wangu", "wako", "moyo", "zvino", "kwete", "hongu", "ndinoda"},
    "nd": {"mina", "wena", "thina", "lami", "lakho", "uthando", "ngiyabonga", "yebo", "cha", "khona", "ngikhona"},
    "zu": {"mina", "wena", "thina", "yami", "yakho", "uthando", "ngiyabonga", "yebo", "cha", "kakhulu"},
    "xh": {"mna", "yam", "uthando", "enkosi", "ewe", "hayi", "ndiyakuthanda"},
    "af": {"die", "en", "ek", "jy", "liefde", "hart", "vir", "met", "ons", "nie"},
    "sw": {"mimi", "wewe", "upendo", "ndiyo", "hapana", "asante", "sana", "yangu"},
}
_WORD_RE = re.compile(r"[\w’']+", re.UNICODE)
_SCRIPT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ru", re.compile(r"[\u0400-\u04ff]")), ("ar", re.compile(r"[\u0600-\u06ff]")),
    ("hi", re.compile(r"[\u0900-\u097f]")), ("zh", re.compile(r"[\u4e00-\u9fff]")),
    ("ja", re.compile(r"[\u3040-\u30ff]")), ("ko", re.compile(r"[\uac00-\ud7af]")),
    ("th", re.compile(r"[\u0e00-\u0e7f]")), ("el", re.compile(r"[\u0370-\u03ff]")),
    ("he", re.compile(r"[\u0590-\u05ff]")),
)


def detect_text_language(text: str) -> dict[str, Any]:
    """Guess a language conservatively from a text span; not a full language model."""
    words = [w.casefold().replace("’", "'") for w in _WORD_RE.findall(text)]
    if not words:
        return {"language": "und", "confidence": 0.0, "method": "text-heuristic"}
    letters = sum(char.isalpha() for char in text)
    if letters:
        for code, pattern in _SCRIPT_PATTERNS:
            matches = len(pattern.findall(text))
            if matches / letters >= 0.35:
                return {"language": code, "confidence": round(min(0.99, 0.65 + matches / letters / 3), 3), "method": "script"}
    scores = {code: sum(word in markers for word in words) for code, markers in _LANGUAGE_MARKERS.items()}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    code, score = ranked[0]
    second = ranked[1][1]
    if score == 0:
        return {"language": "und", "confidence": 0.0, "method": "text-heuristic"}
    if score == second:
        return {"language": "und", "confidence": 0.25, "method": "ambiguous-lexical"}
    return {"language": code, "confidence": round(min(0.94, 0.45 + 0.12 * score + 0.08 * (score - second)), 3), "method": "lexical-hint"}


def _normalise_segment(segment: Any, asr_language: str, asr_confidence: float) -> dict[str, Any]:
    text = str(getattr(segment, "text", "")).strip()
    hint = detect_text_language(text)
    language = hint["language"] if hint["language"] != "und" else (asr_language or "und")
    return {
        "start": round(float(segment.start), 3), "end": round(float(segment.end), 3),
        "text": text, "language": language,
        "language_confidence": hint["confidence"] if hint["language"] != "und" else round(asr_confidence, 3),
        "language_method": hint["method"] if hint["language"] != "und" else "asr-segment-fallback",
        "asr_language": asr_language or "und",
        "words": [
            {"text": str(getattr(word, "word", "")).strip(), "start": round(float(word.start), 3),
             "end": round(float(word.end), 3), "probability": round(float(getattr(word, "probability", 0.0) or 0.0), 3)}
            for word in (getattr(segment, "words", None) or [])
        ],
    }


def transcribe_audio(audio_path: str | Path, model_name: str = "small", language: str | None = None,
                    device: str = "auto", compute_type: str = "default") -> Iterable[dict[str, Any]]:
    """Yield timestamped segments using optional multilingual faster-whisper."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("ASR backend unavailable. Install with: python -m pip install 'faster-whisper>=1.1'") from exc
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, info = model.transcribe(str(audio_path), language=language, word_timestamps=True,
        vad_filter=True, condition_on_previous_text=False, beam_size=5)
    asr_language = str(getattr(info, "language", "") or "und")
    asr_confidence = float(getattr(info, "language_probability", 0.0) or 0.0)
    for segment in segments:
        yield _normalise_segment(segment, asr_language, asr_confidence)



def transcribe_live(model_name: str = "small", language: str | None = None,
                    device: str = "auto", compute_type: str = "default",
                    sample_rate: int = 16000, chunk_seconds: float = 5.0) -> Iterable[dict[str, Any]]:
    """Yield low-latency lyric segments from the default microphone.

    Requires optional sounddevice and faster-whisper packages. Language is
    detected independently for each audio window when not explicitly supplied.
    """
    try:
        import sounddevice as sd
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Live capture needs optional packages: python -m pip install "
            "'faster-whisper>=1.1' sounddevice"
        ) from exc
    if sample_rate < 8000:
        raise ValueError("sample_rate must be at least 8000 Hz")
    if chunk_seconds < 1.0 or chunk_seconds > 30.0:
        raise ValueError("chunk_seconds must be between 1 and 30 seconds")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    chunk_index = 0
    print("Listening; press Ctrl+C to stop.", file=sys.stderr, flush=True)
    while True:
        samples = sd.rec(int(chunk_seconds * sample_rate), samplerate=sample_rate,
                         channels=1, dtype="float32", blocking=True).reshape(-1)
        segments, info = model.transcribe(
            samples, language=language, word_timestamps=True, vad_filter=True,
            condition_on_previous_text=False, beam_size=5,
        )
        asr_language = str(getattr(info, "language", "") or "und")
        asr_confidence = float(getattr(info, "language_probability", 0.0) or 0.0)
        offset = chunk_index * chunk_seconds
        for segment in segments:
            row = _normalise_segment(segment, asr_language, asr_confidence)
            row["start"] = round(row["start"] + offset, 3)
            row["end"] = round(row["end"] + offset, 3)
            for word in row["words"]:
                word["start"] = round(word["start"] + offset, 3)
                word["end"] = round(word["end"] + offset, 3)
            row["capture_mode"] = "microphone"
            yield row
        chunk_index += 1


def build_lyrics_document(song_id: str, segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a versioned lyric document that requires human review."""
    return {"schema_version": 1, "id": song_id, "source": "multilingual-auto-lyrics",
        "language_mode": "auto", "segments": segments, "review_required": True,
        "notes": "Machine lyrics may mishear singing, code-switching, names, and under-resourced languages. Review before publication."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate timestamped multilingual lyrics from audio.")
    parser.add_argument("audio", type=Path, nargs="?")
    parser.add_argument("--song-id", default=None)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default=None, help="Omit to enable backend language detection")
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--compute-type", default="default")
    parser.add_argument("--output", type=Path, default=None, help="Save complete JSON; otherwise stream JSONL events to stdout")
    parser.add_argument("--live", action="store_true", help="Transcribe from the default microphone in rolling audio windows")
    parser.add_argument("--chunk-seconds", type=float, default=5.0, help="Microphone window size (1-30 seconds)")
    args = parser.parse_args()
    song_id = args.song_id or args.audio.stem
    try:
        segments: list[dict[str, Any]] = []
        for segment in transcribe_audio(args.audio, args.model, args.language, args.device, args.compute_type):
            segments.append(segment)
            if args.output is None:
                print(json.dumps({"event": "lyric_segment", **segment}, ensure_ascii=False), flush=True)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(build_lyrics_document(song_id, segments), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {len(segments)} lyric segments to {args.output}", file=sys.stderr)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"lyrics-engine: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

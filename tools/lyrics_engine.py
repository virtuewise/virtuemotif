"""Multilingual auto-lyrics engine with streaming ASR output and language hints."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tools.language_timeline import build_language_timeline, segment_requires_review

# Conservative lexical hints; ambiguous short lines remain "und".
_LANGUAGE_MARKERS: dict[str, set[str]] = {
    "en": {"the", "and", "you", "your", "with", "love", "heart", "we", "are", "is", "my", "this", "that", "have", "never", "tonight", "forever", "because", "when", "all", "for", "to"},
    "sn": {"ndiri", "uri", "iwe", "isu", "rudo", "wangu", "wako", "moyo", "zvino", "kwete", "hongu", "ndinoda", "ndinokuda", "ndichauya", "musha", "hupenyu", "mangwanani", "manheru", "tiri", "nguva", "chokwadi", "kana", "ndiye", "ndichiri", "pamwe"},
    # Only distinctive forms are used for Nguni classification. Shared words such
    # as mina, wena, thina, uthando, yebo and cha are intentionally omitted.
    "nd": {"lami", "lakho", "ngikhona", "ngiyabonga", "ngiyahamba", "ngiyazi", "ngiyabona", "ngikhumbula", "ngizokubona", "ngiyakuthanda", "ngikhuluma", "ngifuna", "ngiyakhala", "ngiphila", "ngizobuya", "khona"},
    "zu": {"yami", "yakho", "kakhulu", "ngiyabonga", "ngiyakuthanda", "ngihamba", "ngiyazi", "ngiyabona", "ngifuna", "ngikhumbula", "ngizokubona", "ngiyaphila", "ngiyacula", "ngizobuya", "ngiyakhala"},
    "xh": {"mna", "yam", "enkosi", "ewe", "hayi", "ndiyakuthanda", "ndiyahamba", "ndiyazi", "ndiyabona", "ndifuna", "ndiyaphila", "ndikhumbula", "ndiza", "ndithetha"},
    "af": {"die", "en", "ek", "jy", "liefde", "hart", "vir", "met", "ons", "nie", "baie", "vandag", "saam", "altyd"},
    "sw": {"mimi", "wewe", "upendo", "ndiyo", "hapana", "asante", "sana", "yangu", "ninakupenda", "habari", "rafiki", "maisha", "kesho", "karibu"},
    # High-signal lexical hints for common Latin-script languages. These remain
    # heuristics: shared function words alone are deliberately not enough.
    "es": {"hola", "gracias", "quiero", "corazon", "corazón", "vida", "noche", "siempre", "estoy", "eres", "quieres", "bailar", "suenos", "sueños"},
    "fr": {"bonjour", "merci", "amour", "coeur", "cœur", "avec", "toujours", "nuit", "je", "suis", "aime", "monde"},
    "pt": {"obrigado", "obrigada", "saudade", "coracao", "coração", "voce", "você", "quero", "minha", "meu", "noite", "estou", "amanha", "amanhã"},
    "de": {"ich", "nicht", "heute", "nacht", "immer", "mein", "dein", "liebe", "herz", "möchte", "danke", "bitte", "leben"},
    "it": {"ciao", "grazie", "amore", "cuore", "sempre", "notte", "voglio", "sono", "perche", "perché", "bacio", "stelle", "vita"},
}
_WORD_RE = re.compile(r"[\w’']+", re.UNICODE)
_SCRIPT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ru", re.compile(r"[\u0400-\u04ff]")), ("ar", re.compile(r"[\u0600-\u06ff]")),
    ("hi", re.compile(r"[\u0900-\u097f]")), ("zh", re.compile(r"[\u4e00-\u9fff]")),
    ("ja", re.compile(r"[\u3040-\u30ff]")), ("ko", re.compile(r"[\uac00-\ud7af]")),
    ("th", re.compile(r"[\u0e00-\u0e7f]")), ("el", re.compile(r"[\u0370-\u03ff]")),
    ("he", re.compile(r"[\u0590-\u05ff]")),
)


def detect_code_switch_candidates(text: str) -> list[dict[str, Any]]:
    """Return conservative word-index spans for distinctive lexical code-switch evidence.

    These are review candidates, not word-level language predictions or timestamps.
    Only runs with at least two distinctive markers are reported, and shared words
    cannot independently establish an isiNdebele/isiZulu boundary.
    """
    if not isinstance(text, str):
        return []
    tokens = list(_WORD_RE.finditer(text))
    if len(tokens) < 4:
        return []
    owners_by_word: list[set[str]] = []
    for token in tokens:
        word = token.group(0).casefold().replace("’", "'")
        owners_by_word.append({
            code for code, markers in _LANGUAGE_MARKERS.items() if word in markers
        })

    # Assign only words with exclusive marker ownership; ambiguous shared markers
    # are deliberately left unlabeled rather than used to manufacture boundaries.
    labels = [
        next(iter(owners)) if len(owners) == 1 else None
        for owners in owners_by_word
    ]
    runs: list[dict[str, Any]] = []
    for index, label in enumerate(labels):
        if label is None:
            continue
        if runs and runs[-1]["language"] == label:
            runs[-1]["end_word"] = index + 1
            runs[-1]["marker_count"] += 1
        else:
            runs.append({
                "language": label,
                "start_word": index,
                "end_word": index + 1,
                "marker_count": 1,
            })

    candidates: list[dict[str, Any]] = []
    for left, right in itertools.pairwise(runs):
        if left["language"] == right["language"]:
            continue
        if left["marker_count"] < 2 or right["marker_count"] < 2:
            continue
        candidates.append({
            "after_word": left["end_word"] - 1,
            "before_word": right["start_word"],
            "from": left["language"],
            "to": right["language"],
            "candidate": True,
            "review_required": True,
            "timing_available": False,
            "method": "exclusive-lexical-markers",
        })
    return candidates


def detect_text_language(text: str) -> dict[str, Any]:
    """Guess a language conservatively from a text span; not a full language model."""
    if not isinstance(text, str):
        return {"language": "und", "confidence": 0.0, "method": "invalid-text-input"}
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
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    code, score = ranked[0]
    _, second = ranked[1]
    if score == 0:
        return {"language": "und", "confidence": 0.0, "method": "text-heuristic"}
    # A score tie is ambiguous unless at least two tied languages each have
    # exclusive marker evidence. Shared isiNdebele/isiZulu tokens alone cannot
    # prove code-switching, but balanced English/Shona markers can support it.
    if score == second:
        tied_languages = {language for language, value in scores.items() if value == score}
        exclusive_languages = {
            next(iter(owners))
            for word in words
            if len(owners := {
                language for language, markers in _LANGUAGE_MARKERS.items() if word in markers
            }) == 1
        }
        if len(words) >= 4 and len(tied_languages & exclusive_languages) >= 2:
            return {"language": "mul", "confidence": 0.4, "method": "code-switched-lexical"}
        return {"language": "und", "confidence": 0.25, "method": "ambiguous-lexical"}
    # A text span with substantial evidence for two languages is code-switched.
    if second >= 1 and score >= 1 and len(words) >= 5 and score <= second * 2:
        return {"language": "mul", "confidence": 0.45, "method": "code-switched-lexical"}
    return {"language": code, "confidence": round(min(0.94, 0.45 + 0.12 * score + 0.08 * (score - second)), 3), "method": "lexical-hint"}


def _normalise_segment(segment: Any, asr_language: str, asr_confidence: float) -> dict[str, Any]:
    """Normalize ASR evidence and reject malformed segment timing before serialization."""
    try:
        start = float(segment.start)
        end = float(segment.end)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("ASR segment must contain numeric start and end timestamps") from exc
    if not (math.isfinite(start) and math.isfinite(end)) or start < 0 or end < start:
        raise ValueError("ASR segment has invalid timestamp interval")

    text = str(getattr(segment, "text", "")).strip()
    hint = detect_text_language(text)
    asr_code = str(asr_language or "und")
    lexical_code = str(hint["language"])
    language = lexical_code if lexical_code != "und" else asr_code
    disagreement = lexical_code not in {"und", asr_code} and asr_code != "und"
    review_reasons = ["asr_lexical_disagreement"] if disagreement else []

    try:
        confidence = float(asr_confidence)
    except (TypeError, ValueError):
        confidence = float("nan")
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        confidence = 0.0
        review_reasons.append("invalid_asr_confidence")
    elif confidence < 0.55:
        review_reasons.append("low_asr_confidence")

    words: list[dict[str, Any]] = []
    invalid_word_timing_count = 0
    previous_word_start = start
    for word in getattr(segment, "words", None) or []:
        try:
            word_start = float(word.start)
            word_end = float(word.end)
        except (AttributeError, TypeError, ValueError):
            invalid_word_timing_count += 1
            continue
        if (
            not math.isfinite(word_start)
            or not math.isfinite(word_end)
            or word_start < start
            or word_start < previous_word_start
            or word_end < word_start
            or word_end > end + 0.05
        ):
            invalid_word_timing_count += 1
            continue
        previous_word_start = word_start
        try:
            probability = float(getattr(word, "probability", 0.0) or 0.0)
        except (TypeError, ValueError):
            probability = 0.0
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            probability = 0.0
        words.append({
            "text": str(getattr(word, "word", "")).strip(),
            "start": round(word_start, 3),
            "end": round(word_end, 3),
            "probability": round(probability, 3),
        })
    if invalid_word_timing_count:
        review_reasons.append("invalid_word_timing")

    return {
        "start": round(start, 3), "end": round(end, 3),
        "text": text, "language": language,
        "language_confidence": hint["confidence"] if lexical_code != "und" else round(confidence, 3),
        "language_method": hint["method"] if lexical_code != "und" else "asr-segment-fallback",
        "asr_language": asr_code,
        "language_evidence": {
            "asr_language": asr_code,
            "asr_confidence": round(confidence, 3),
            "lexical_language": lexical_code,
            "lexical_confidence": hint["confidence"],
            "lexical_method": hint["method"],
            "disagreement": disagreement,
        },
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "words": words,
        "code_switch_candidates": detect_code_switch_candidates(text),
        "invalid_word_timing_count": invalid_word_timing_count,
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
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate < 8000:
        raise ValueError("sample_rate must be an integer of at least 8000 Hz")
    if not math.isfinite(chunk_seconds) or chunk_seconds < 1.0 or chunk_seconds > 30.0:
        raise ValueError("chunk_seconds must be between 1 and 30 seconds")
    try:
        import sounddevice as sd
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Live capture needs optional packages: python -m pip install "
            "'faster-whisper>=1.1' sounddevice"
        ) from exc
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


def build_lyrics_document(
    song_id: str,
    segments: list[dict[str, Any]],
    language_mode: str = "auto",
) -> dict[str, Any]:
    """Create a versioned lyric document with language provenance and review warnings.

    A timestamped timeline is included when all segments carry start/end values.
    Incomplete legacy segment records remain supported and get no fabricated timeline.
    """
    language_counts: dict[str, int] = {}
    for segment in segments:
        language = str(segment.get("language") or "und")
        language_counts[language] = language_counts.get(language, 0) + 1
    has_timestamps = all("start" in segment and "end" in segment for segment in segments)
    timeline = build_language_timeline(segments) if has_timestamps else None
    return {
        "schema_version": 1,
        "id": song_id,
        "source": "multilingual-auto-lyrics",
        "language_mode": language_mode,
        "language_summary": dict(sorted(language_counts.items())),
        "segments": segments,
        "language_timeline": timeline,
        "review_required": True,
        "notes": "Machine lyrics may mishear singing, code-switching, names, and under-resourced languages. Review before publication.",
    }


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
    if args.live and args.audio is not None:
        parser.error("do not provide an audio path with --live")
    if not args.live and args.audio is None:
        parser.error("provide an audio path or use --live")
    if args.live and args.output is not None:
        parser.error("--output is only supported for audio-file transcription")
    song_id = args.song_id or (args.audio.stem if args.audio is not None else "live-capture")
    try:
        segments: list[dict[str, Any]] = []
        stream = (
            transcribe_live(args.model, args.language, args.device, args.compute_type,
                            chunk_seconds=args.chunk_seconds)
            if args.live else transcribe_audio(args.audio, args.model, args.language,
                                               args.device, args.compute_type)
        )
        previous_segment: dict[str, Any] | None = None
        for segment in stream:
            segments.append(segment)
            print(json.dumps({"event": "lyric_segment", **segment}, ensure_ascii=False), flush=True)
            language = str(segment.get("language") or "und")
            previous_language = str(previous_segment.get("language") or "und") if previous_segment else None
            if previous_segment is not None and language != previous_language:
                print(json.dumps({
                    "event": "language_transition_candidate",
                    "at": segment["start"],
                    "from": previous_language,
                    "to": language,
                    "candidate": True,
                    "review_required": (
                        segment_requires_review(previous_segment)
                        or segment_requires_review(segment)
                    ),
                }, ensure_ascii=False), flush=True)
            previous_segment = segment
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(build_lyrics_document(song_id, segments, args.language or "auto"), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Wrote {len(segments)} lyric segments to {args.output}", file=sys.stderr)
    except KeyboardInterrupt:
        print("Stopped live transcription.", file=sys.stderr)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"lyrics-engine: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

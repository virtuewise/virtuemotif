"""Convert multilingual ASR JSON into the Song schema consumed by Remotion."""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_LANGUAGE_NAMES = {"en": "English", "sn": "Shona", "nd": "isiNdebele", "zu": "isiZulu", "xh": "isiXhosa", "af": "Afrikaans", "sw": "Swahili"}
SUPPORTED_TYPOGRAPHY_PRESETS = ("display", "editorial", "neon", "whisper")


def _number(value: Any, field: str, index: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"segment {index}: {field} must be a finite number")
    return float(value)


def _segments(document: dict[str, Any], typography_preset: str) -> list[dict[str, Any]]:
    raw_segments = document.get("segments")
    if not isinstance(raw_segments, list):
        raise TypeError("input document must contain a segments array")
    result = []
    for index, raw in enumerate(raw_segments):
        if not isinstance(raw, dict):
            raise TypeError(f"segment {index}: expected an object")
        text = raw.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"segment {index}: text must be non-empty")
        start = _number(raw.get("start"), "start", index)
        end = _number(raw.get("end"), "end", index)
        if start < 0 or end <= start:
            raise ValueError(f"segment {index}: expected 0 <= start < end")
        language = raw.get("language", raw.get("asr_language", "und"))
        if not isinstance(language, str) or not language.strip():
            language = "und"
        confidence = min(1.0, max(0.0, _number(raw.get("language_confidence", 0), "language_confidence", index)))
        line: dict[str, Any] = {
            "text": text.strip(), "from": round(start, 3), "to": round(end, 3),
            "language": language, "languageConfidence": round(confidence, 3), "style": typography_preset,
        }
        words = raw.get("words") or []
        if not isinstance(words, list):
            raise TypeError(f"segment {index}: words must be an array")
        converted_words = []
        previous_word_start = start
        for word_index, word in enumerate(words):
            if not isinstance(word, dict) or not isinstance(word.get("text"), str) or not word["text"].strip():
                raise ValueError(f"segment {index}, word {word_index}: invalid word record")
            word_start = _number(word.get("start"), "word.start", index)
            word_end = _number(word.get("end"), "word.end", index)
            if word_start < start or word_end > end or word_end <= word_start:
                raise ValueError(f"segment {index}, word {word_index}: timing outside segment")
            if word_start < previous_word_start:
                raise ValueError(
                    f"segment {index}, word {word_index}: word starts must be non-decreasing"
                )
            previous_word_start = word_start
            converted_words.append({"w": word["text"].strip(), "from": round(word_start, 3), "to": round(word_end, 3)})
        if converted_words:
            # Preserve validated source order; sorting malformed timing would hide ASR defects.
            line["words"] = converted_words
        result.append(line)
    return sorted(result, key=lambda line: (line["from"], line["to"]))


def _clusters(lines: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for line in lines:
        if not groups or line["from"] - groups[-1][-1]["to"] > 4.5 or len(groups[-1]) >= 6:
            groups.append([line])
        else:
            groups[-1].append(line)
    return groups


def convert_lyrics_document(
    document: dict[str, Any], *, audio: str, title: str | None = None,
    subtitle: str | None = None, artist: str | None = None,
    song_id: str | None = None, duration: float | None = None,
    typography_preset: str = "display",
) -> dict[str, Any]:
    """Convert a schema-v1 ASR document to the Remotion Song data contract."""
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("input document must be a schema_version 1 object")
    if not isinstance(audio, str) or not audio.strip():
        raise ValueError("audio must be a non-empty path relative to film/public")
    if typography_preset not in SUPPORTED_TYPOGRAPHY_PRESETS:
        raise ValueError(f"unsupported typography preset: {typography_preset}")

    lines = _segments(document, typography_preset)
    last_end = max((line["to"] for line in lines), default=0.0)
    if duration is None and document.get("duration") is not None:
        duration = _number(document["duration"], "duration", -1)
    if duration is None:
        duration = last_end
    if not math.isfinite(duration) or duration < last_end or duration < 0:
        raise ValueError("duration must be finite and at least the final lyric end time")

    identifier = song_id or str(document.get("id") or "auto-lyrics")
    if not identifier.strip():
        raise ValueError("song id must not be empty")
    groups = _clusters(lines)
    sections: list[dict[str, Any]] = []
    if not groups:
        sections.append({"id": "instrumental", "label": "Instrumental", "look": "wide", "start": 0, "end": round(duration, 3), "lines": []})
    else:
        if groups[0][0]["from"] > 3.5:
            sections.append({"id": "intro", "label": "Intro — Instrumental", "look": "wide", "start": 0, "end": groups[0][0]["from"], "lines": []})
        frequency = Counter(line["text"].casefold().strip() for line in lines)
        verse_no = chorus_no = 1
        for index, group in enumerate(groups):
            start = group[0]["from"]
            final_line_end = group[-1]["to"]
            next_start = groups[index + 1][0]["from"] if index + 1 < len(groups) else duration
            repeated = sum(frequency[line["text"].casefold().strip()] > 1 for line in group)
            chorus = repeated >= math.ceil(len(group) * 0.45)
            if chorus:
                section_id, label, look = f"chorus{chorus_no}", f"Chorus {chorus_no}", "giant"
                chorus_no += 1
            else:
                section_id, label = f"verse{verse_no}", f"Verse {verse_no}"
                look = "walkers" if verse_no % 2 else "dusk"
                verse_no += 1

            end = min(duration, next_start if next_start - final_line_end <= 3.0 else final_line_end + 1.2)
            end = max(end, final_line_end)
            sections.append({
                "id": section_id, "label": label, "look": look,
                "start": round(start, 3), "end": round(end, 3),
                "lines": [{
                    "text": line["text"], "translation": "", "style": line["style"],
                    "from": line["from"], "to": line["to"],
                    **({"words": line["words"]} if line.get("words") else {}),
                    "language": line["language"], "languageConfidence": line["languageConfidence"],
                } for line in group],
            })
            if next_start - final_line_end > 3.0 and next_start > end:
                sections.append({
                    "id": f"interlude{index + 1}", "label": "Instrumental interlude", "look": "night",
                    "start": round(end, 3), "end": round(next_start, 3), "lines": [],
                })
        if sections[-1]["end"] < duration - 3.0:
            sections.append({
                "id": "outro_inst", "label": "Outro — Instrumental", "look": "night",
                "start": sections[-1]["end"], "end": round(duration, 3), "lines": [],
            })
        elif sections[-1]["end"] < duration:
            sections[-1]["end"] = round(duration, 3)

    known = [line for line in lines if line["language"] != "und"]
    language_counts = Counter(line["language"] for line in known)
    detected_language = language_counts.most_common(1)[0][0] if language_counts else "und"
    confidence = sum(line["languageConfidence"] for line in known) / len(known) if known else 0.0
    return {
        "id": identifier,
        "title": title or str(document.get("title") or identifier.replace("_", " ").title()),
        "subtitle": subtitle or str(document.get("subtitle") or "Auto-generated lyrics — review required"),
        "artist": artist or str(document.get("artist") or "virtuemotif"),
        "audio": audio.strip().lstrip("/"),
        "duration": round(duration, 3),
        "palette": "dusk",
        "detectedLanguage": _LANGUAGE_NAMES.get(detected_language, detected_language if detected_language != "und" else "Unknown / undetected"),
        "detectedLanguageCode": detected_language,
        "languageConfidence": round(confidence, 3),
        "reviewRequired": bool(document.get("review_required", True)),
        "sections": sections,
    }


def build_remotion_props(song: dict[str, Any]) -> dict[str, Any]:
    """Wrap Song data in the component-props shape expected by the AutoLyrics composition."""
    return {"song": song}


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert multilingual ASR output into Remotion Song JSON.")
    parser.add_argument("input", type=Path, help="Versioned JSON produced by tools.lyrics_engine")
    parser.add_argument("--audio", required=True, help="Path relative to film/public, e.g. audio/song.m4a")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--props-output", type=Path, help="Optional Remotion props JSON for the generic AutoLyrics composition")
    parser.add_argument("--song-id")
    parser.add_argument("--title")
    parser.add_argument("--subtitle")
    parser.add_argument("--artist")
    parser.add_argument("--duration", type=float, help="Full audio duration in seconds")
    parser.add_argument(
        "--typography-preset",
        choices=SUPPORTED_TYPOGRAPHY_PRESETS,
        default="display",
        help="Lyric visual preset: display, editorial, neon, or whisper",
    )
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        song = convert_lyrics_document(
            document, audio=args.audio, title=args.title, subtitle=args.subtitle,
            artist=args.artist, song_id=args.song_id, duration=args.duration,
            typography_preset=args.typography_preset,
        )
        if args.props_output is not None and args.props_output.resolve() == args.output.resolve():
            raise ValueError("--props-output must differ from --output")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(song, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.props_output is not None:
            args.props_output.parent.mkdir(parents=True, exist_ok=True)
            props = build_remotion_props(song)
            args.props_output.write_text(json.dumps(props, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"export-lyrics-song: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote Remotion Song JSON to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

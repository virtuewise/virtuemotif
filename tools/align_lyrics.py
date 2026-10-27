"""Forced-align the known lyrics to the song with Meta's MMS_FA CTC aligner.

Why this stack:
  * MMS_FA (torchaudio.pipelines.MMS_FA) is Meta's massively-multilingual CTC
    alignment model. It works on *phonemes*, so Shona / Ndebele / English all
    align with the same model (no per-language wav2vec2 head to hunt down).
  * We align the *known* lyric text (no ASR), so there are no transcription
    errors; the only job is Viterbi-decoding the text onto the audio frames.
  * A ``*`` ("star") token is inserted between lines so instrumental gaps,
    breaths and ad-libs are absorbed instead of being smeared onto words.
  * Alignment is done per song section inside a padded window, which keeps the
    44 s instrumental intro (and every later gap) out of the lyric path.

Outputs:
  timing/<id>.aligned.json   rich word-level timings (source of truth)
  timing/<id>.json           line overrides consumed by tools/build_timeline.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys
import wave

import numpy as np
import torch
import torchaudio

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")
SR = 16000
FRAME = 0.02  # MMS_FA emits one frame per 20 ms
PAD = 5.0  # seconds of context on each side of a section
EDGE_WARN = 0.75  # warn when a word lands this close to the window edge

BUNDLE = torchaudio.pipelines.MMS_FA
VOCAB = BUNDLE.get_dict()
STAR = VOCAB["*"]
BLANK = 0

STRIP = re.compile(r"[^a-z']+")


def norm_word(word: str) -> str:
    w = (
        word.lower()
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u02bc", "'")
        .replace("`", "'")
    )
    return STRIP.sub("", w)


def word_ids(words: list[str]) -> list[list[int]]:
    out = []
    for w in words:
        clean = norm_word(w)
        ids = [VOCAB[c] for c in clean if c in VOCAB]
        if ids:
            out.append(ids)
    return out


def ensure_wav(src: pathlib.Path, dst: pathlib.Path) -> pathlib.Path:
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )
    return dst


def read_wav(path: pathlib.Path) -> torch.Tensor:
    with wave.open(str(path), "rb") as f:
        assert f.getnchannels() == 1 and f.getframerate() == SR
        raw = f.readframes(f.getnframes())
    return torch.from_numpy(np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0)


def emissions(model, chunk: torch.Tensor) -> torch.Tensor:
    with torch.inference_mode():
        em, _ = model(chunk.unsqueeze(0))
    return em[0]


def long_emissions(model, wav: torch.Tensor, chunk: float = 30.0, overlap: float = 6.0) -> torch.Tensor:
    """Emission stream for a whole song, computed in overlapping windows.

    Each window keeps only its middle ``chunk - overlap`` seconds, so the kept
    pieces tile the song exactly and frame k still means t = k * 0.02 s.
    """
    dur = wav.numel() / SR
    crop = int(round((overlap / 2) / FRAME))
    step = chunk - overlap
    pieces = []
    a = 0.0
    while True:
        b = min(dur, a + chunk)
        em = emissions(model, wav[int(round(a * SR)) : int(round(b * SR))])
        lo = 0 if a <= 1e-6 else crop
        hi = em.shape[0] if b >= dur - 1e-6 else em.shape[0] - crop
        pieces.append(em[lo:hi])
        if b >= dur - 1e-6:
            break
        a += step
    em = torch.cat(pieces, 0)
    expect = int(round(dur / FRAME))
    print(f"[align] emissions {em.shape[0]} frames (expected ~{expect})", flush=True)
    return em


def align_whole(model, wav: torch.Tensor, song: dict, star_lines: bool = True) -> dict:
    em = long_emissions(model, wav)
    groups: list[dict] = [{"kind": "star", "ids": [STAR]} for _ in range(3)]
    for si, section in enumerate(song["sections"]):
        if not section.get("lines") or section.get("align") is False:
            continue
        for li, line in enumerate(section["lines"]):
            if star_lines:
                groups.append({"kind": "star", "ids": [STAR]})
            for wi, w in enumerate(line["text"].split(" ")):
                ids = word_ids([w])
                if ids:
                    groups.append(
                        {"kind": "word", "section": si, "line": li, "word": wi, "text": w, "ids": ids[0]}
                    )
    groups += [{"kind": "star", "ids": [STAR]} for _ in range(3)]

    print(f"[align] aligning {sum(g['kind']=='word' for g in groups)} words over {em.shape[0]} frames…", flush=True)
    spans = BUNDLE.get_aligner()(em, [g["ids"] for g in groups])

    for g, sp in zip(groups, spans):
        g["from"] = sp[0].start * FRAME
        g["to"] = sp[-1].end * FRAME
        g["score"] = float(np.mean([s.score for s in sp]))

    out = []
    for si, section in enumerate(song["sections"]):
        if not section.get("lines"):
            continue
        lines = []
        for li, line in enumerate(section["lines"]):
            ws = [g for g in groups if g["kind"] == "word" and g["section"] == si and g["line"] == li]
            if not ws:
                continue
            lines.append(
                {
                    "text": line["text"],
                    "translation": line.get("translation", ""),
                    "style": line.get("style", "display"),
                    "words": [
                        {
                            "i": g["word"],
                            "w": g["text"],
                            "from": round(g["from"], 3),
                            "to": round(g["to"], 3),
                            "score": round(g["score"], 3),
                        }
                        for g in ws
                    ],
                }
            )
        out.append({"id": section["id"], "window": [0.0, round(wav.numel() / SR, 3)], "lines": lines})
    return {"sections": out}


def derive_sections(aligned: list[dict], song: dict) -> list[dict]:
    """Re-time the film structure off the actual vocal onsets."""

    firsts = {}
    lasts = {}
    for sec in aligned:
        if not sec["lines"]:
            continue
        firsts[sec["id"]] = sec["lines"][0]["words"][0]["from"]
        lasts[sec["id"]] = sec["lines"][-1]["words"][-1]["to"]

    ordered = [s for s in song["sections"]]
    bounds = {}
    for i, s in enumerate(ordered):
        sid = s["id"]
        nxt = ordered[i + 1] if i + 1 < len(ordered) else None
        nxt_first = firsts.get(nxt["id"]) if nxt else None
        if sid in firsts:
            start = firsts[sid] - 1.4
            if i:
                start = max(start, bounds[ordered[i - 1]["id"]][1] + 0.1)
            end = (nxt_first - 1.4) if nxt_first else min(float(song["duration"]), lasts[sid] + 4.5)
            end = max(end, start + 1.0)
        else:
            # instrumental / intertitle section: honour the sheet, but stop
            # before the next sung section begins
            start = float(s["start"])
            end = float(s["end"])
            if nxt_first:
                end = min(end, nxt_first - 1.4)
        bounds[sid] = (round(start, 2), round(max(end, start + 0.5), 2))
    return [{"id": k, "start": v[0], "end": v[1]} for k, v in bounds.items()]


def align_section(model, wav: torch.Tensor, section: dict, pad: float = PAD) -> dict:
    dur = wav.numel() / SR
    if section.get("align_window"):
        win_a, win_b = (float(x) for x in section["align_window"])
    else:
        win_a = max(0.0, float(section["start"]) - pad)
        win_b = min(dur, float(section["end"]) + pad)
    win_a = max(0.0, win_a)
    win_b = min(dur, win_b)
    chunk = wav[int(round(win_a * SR)) : int(round(win_b * SR))]
    em = long_emissions(model, chunk)

    groups: list[dict] = []  # one entry per star / word, in lyric order
    for _ in range(3):
        groups.append({"kind": "star", "ids": [STAR]})
    for li, line in enumerate(section.get("lines", [])):
        if li > 0:
            groups.append({"kind": "star", "ids": [STAR]})
        for wi, w in enumerate(line["text"].split(" ")):
            ids = word_ids([w])
            if not ids:
                continue
            groups.append({"kind": "word", "line": li, "word": wi, "text": w, "ids": ids[0]})
    for _ in range(3):
        groups.append({"kind": "star", "ids": [STAR]})

    spans = BUNDLE.get_aligner()(em, [g["ids"] for g in groups])
    n_frames = em.shape[0]

    def secs(frame: int) -> float:
        return win_a + frame * FRAME

    for g, sp in zip(groups, spans):
        g["from"] = secs(sp[0].start)
        g["to"] = secs(sp[-1].end)
        g["score"] = float(np.mean([s.score for s in sp]))
        g["frames"] = sp[-1].end - sp[0].start

    lines = []
    for li, line in enumerate(section.get("lines", [])):
        ws = [g for g in groups if g["kind"] == "word" and g["line"] == li]
        if not ws:
            continue
        lines.append(
            {
                "text": line["text"],
                "translation": line.get("translation", ""),
                "style": line.get("style", "display"),
                "words": [
                    {
                        "i": g["word"],
                        "w": g["text"],
                        "from": round(g["from"], 3),
                        "to": round(g["to"], 3),
                        "score": round(g["score"], 3),
                    }
                    for g in ws
                ],
            }
        )

    first = lines[0]["words"][0]["from"] if lines else None
    last = lines[-1]["words"][-1]["to"] if lines else None
    edge = False
    if first is not None and (first - win_a) < EDGE_WARN:
        edge = True
    if last is not None and (win_b - last) < EDGE_WARN:
        edge = True

    return {
        "id": section["id"],
        "window": [round(win_a, 3), round(win_b, 3)],
        "frames": int(n_frames),
        "edge": edge,
        "lines": lines,
    }


def line_overrides(aligned: dict, sections: list[dict]) -> dict:
    """Display windows: start just before the vocal, hold until the next line.

    Works across section boundaries so a held last word cannot overlap the
    next sung line for long.
    """
    out: dict[str, dict] = {}
    by_id = {s["id"]: s for s in sections}
    flat: list[tuple[str, int, dict]] = []
    for sec in aligned:
        for i, ln in enumerate(sec["lines"]):
            flat.append((sec["id"], i, ln))

    for k, (sid, i, ln) in enumerate(flat):
        w0 = ln["words"][0]["from"]
        w1 = ln["words"][-1]["to"]
        f = w0 - 0.12
        b = by_id.get(sid)
        if k + 1 < len(flat):
            t = min(w1 + 1.6, flat[k + 1][2]["words"][0]["from"] - 0.08)
        elif b:
            t = min(w1 + 1.6, float(b["end"]) - 0.03)
        else:
            t = w1 + 1.6
        if b:
            f = max(float(b["start"]), f)
            t = min(t, float(b["end"]) - 0.02)
        t = max(t, f + 0.6)
        out.setdefault(sid, {})[str(i)] = {"from": round(f, 2), "to": round(t, 2)}

    # never let two lines overlap on screen
    prev_to = None
    for sid, i, _ln in flat:
        rec = out[sid][str(i)]
        if prev_to is not None and rec["from"] < prev_to + 0.02:
            rec["from"] = round(prev_to + 0.02, 2)
        if rec["to"] < rec["from"] + 0.6:
            rec["to"] = round(rec["from"] + 0.6, 2)
        prev_to = rec["to"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("song", nargs="?", default="horizon")
    ap.add_argument("--mode", choices=["whole", "sections"], default="whole")
    ap.add_argument("--stars", choices=["lines", "edges"], default="lines")
    ap.add_argument("--tag", default="", help="suffix for comparison runs")
    ap.add_argument("--wav", default="", help="align against this wav instead of the mix")
    ap.add_argument("--pad", type=float, default=PAD)
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--only", default="", help="comma separated section ids to (re)align in sections mode")
    ap.add_argument("--reuse", action="store_true", help="recompute overrides from an existing aligned.json")
    args = ap.parse_args()

    song_path = ROOT / "lyrics" / f"{args.song}.json"
    song = json.loads(song_path.read_text(encoding="utf-8"))
    audio = ROOT / "film" / "public" / song["audio"]
    if not audio.exists():
        audio = ROOT / song["audio"]

    print(f"[align] {song['id']} {audio.name} mode={args.mode}", flush=True)
    if args.wav:
        wav_path = pathlib.Path(args.wav)
        if not wav_path.is_absolute():
            wav_path = ROOT / wav_path
    else:
        wav_path = ensure_wav(audio, ROOT / "timing" / "wav" / f"{song['id']}.wav")
    wav = read_wav(wav_path)
    print(f"[align] source {wav_path.name} {wav.numel()/SR:.2f}s @ {SR}Hz", flush=True)
    if abs(wav.numel() / SR - float(song["duration"])) > 1.0:
        print(f"[align] WARNING sheet duration {song['duration']} != audio {wav.numel()/SR:.2f}", flush=True)

    suffix = f".{args.tag}" if args.tag else ""
    aligned_path = ROOT / "timing" / f"{song['id']}{suffix}.aligned.json"

    if args.reuse:
        if not aligned_path.exists():
            print(f"[align] no {aligned_path.name} to reuse", flush=True)
            return 2
        aligned = {"sections": json.loads(aligned_path.read_text(encoding="utf-8"))["sections"]}
        print(f"[align] reusing {aligned_path.name} (no model pass)", flush=True)
    else:
        print("[align] loading MMS_FA (315M params, cached)…", flush=True)
        model = BUNDLE.get_model(with_star=True).eval()
        if args.mode == "whole":
            aligned = align_whole(model, wav, song, star_lines=args.stars == "lines")
        else:
            only = {x.strip() for x in args.only.split(",") if x.strip()}
            prev = {}
            if only and aligned_path.exists():
                prev = {
                    s["id"]: s
                    for s in json.loads(aligned_path.read_text(encoding="utf-8"))["sections"]
                }
                print(f"[align] --only {sorted(only)} (keeping {len(prev)} cached sections)", flush=True)
            out_sections = []
            for s in song["sections"]:
                if not s.get("lines") or s.get("align") is False:
                    continue
                if only and s["id"] not in only and s["id"] in prev:
                    out_sections.append(prev[s["id"]])
                    continue
                res = align_section(model, wav, s, pad=args.pad)
                tries = 0
                while res["edge"] and args.retry and tries < 3:
                    tries += 1
                    res = align_section(model, wav, s, pad=args.pad + 3.0 * tries)
                out_sections.append(res)
            aligned = {"sections": out_sections}

    bounds = derive_sections(aligned["sections"], song)
    bmap = {b["id"]: b for b in bounds}
    for sec in aligned["sections"]:
        b = bmap.get(sec["id"])
        if b:
            sec["start"], sec["end"] = b["start"], b["end"]

    out = {
        "id": song["id"],
        "audio": song["audio"],
        "method": "mms_fa_ctc_forced_alignment",
        "model": "torchaudio.pipelines.MMS_FA (ctc_alignment_mling_uroman)",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "frame": FRAME,
        "sections": aligned["sections"],
    }
    aligned_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    ov = line_overrides(aligned["sections"], song["sections"])
    for s in song["sections"]:
        if s.get("align") is False:
            for i, ln in enumerate(s.get("lines", [])):
                if "from" in ln:
                    ov.setdefault(s["id"], {})[str(i)] = {
                        "from": float(ln["from"]),
                        "to": float(ln.get("to", float(ln["from"]) + 3.0)),
                    }
    ov_path = ROOT / "timing" / f"{song['id']}{suffix}.json"
    ov_path.write_text(json.dumps(ov, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"[align] wrote {aligned_path.name} and {ov_path.name}", flush=True)
    print("[align] structure / line starts:", flush=True)
    for b in bounds:
        print(f"  {b['id']:8s} {b['start']:7.2f} .. {b['end']:7.2f}", flush=True)
    for sec in aligned["sections"]:
        for ln in sec["lines"]:
            w = ln["words"]
            print(
                f"    {sec['id']:8s} {w[0]['from']:7.2f} +{w[-1]['to']-w[0]['from']:5.2f}s  "
                f"score {np.mean([x['score'] for x in w]):.2f}  {ln['text'][:52]}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

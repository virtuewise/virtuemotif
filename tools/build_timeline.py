"""Turn the lyric sheets into a render-ready timeline (lyrics + looks + timings).

Timing priority:
  1. timing/<id>.aligned.json  (MMS_FA forced alignment, word-level)
  2. timing/<id>.json          (line overrides / tap-sync export)
  3. even distribution         (proportional fallback across each section)
"""
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")
LYR = ROOT / "lyrics"
OUT = ROOT / "film" / "src" / "data"
TIM = ROOT / "timing"
OUT.mkdir(parents=True, exist_ok=True)


def load_json(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def build(song):
    sid = song["id"]
    overrides = load_json(TIM / f"{sid}.json", {})
    aligned = load_json(TIM / f"{sid}.aligned.json", None)
    word_map = {}
    if aligned:
        for sec in aligned.get("sections", []):
            for i, ln in enumerate(sec.get("lines", [])):
                word_map[(sec["id"], i)] = ln.get("words", [])

    sections = []
    for s in song["sections"]:
        start, end = float(s["start"]), float(s["end"])
        lines = s.get("lines", [])
        n = len(lines)
        slot = (end - start) / n if n else 0
        out_lines = []
        for i, ln in enumerate(lines):
            f = start + i * slot + 0.25
            t = min(f + slot - 0.45, end - 0.2)
            ov = overrides.get(s["id"], {}).get(str(i))
            if ov:
                f = float(ov["from"])
                t = float(ov["to"]) if ov.get("to") else min(f + (slot - 0.45), end - 0.2)
            words = word_map.get((s["id"], i))
            display = ln["text"].split(" ")
            if words:
                by_i = {w.get("i"): w for w in words}
                if len(by_i) != len(words) or any(k is None for k in by_i):
                    by_i = {k: w for k, w in enumerate(words)}
                filled = []
                for j, tok in enumerate(display):
                    src = by_i.get(j)
                    if src is None:
                        # punctuation-only token ("—", "…"): ride along with a neighbour
                        src = by_i.get(j - 1) or by_i.get(j + 1)
                    if src is None:
                        filled = []
                        break
                    filled.append({"w": tok, "from": round(src["from"], 2), "to": round(src["to"], 2)})
                words = filled or None
            item = {
                "text": ln["text"],
                "translation": ln.get("translation", ""),
                "style": ln.get("style", "display"),
                "from": round(f, 2),
                "to": round(t, 2),
            }
            if words:
                item["words"] = [
                    {"w": w["w"], "from": round(w["from"], 2), "to": round(w["to"], 2)} for w in words
                ]
            out_lines.append(item)
        sections.append(
            {
                "id": s["id"],
                "label": s.get("label", ""),
                "look": s.get("look", "wide"),
                "start": round(start, 2),
                "end": round(end, 2),
                "lines": out_lines,
            }
        )

    data = {
        "id": sid,
        "title": song["title"],
        "subtitle": song.get("subtitle", ""),
        "artist": song.get("artist", "virtuemotif"),
        "audio": song["audio"],
        "duration": song["duration"],
        "palette": song.get("palette", "dusk"),
        "sections": sections,
    }
    (OUT / f"{sid}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    total = sum(len(s["lines"]) for s in sections)
    print(f"{sid}: {len(sections)} sections, {total} lines -> {OUT / (sid + '.json')}")


if __name__ == "__main__":
    for p in sorted(LYR.glob("*.json")):
        if p.name.endswith(".written.json"):
            continue
        build(json.loads(p.read_text(encoding="utf-8")))

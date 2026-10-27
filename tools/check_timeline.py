"""Sanity-check a render timeline: monotonic words, sane windows, no overlap."""

import json
import pathlib
import sys

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")


def check(path: pathlib.Path) -> int:
    d = json.loads(path.read_text(encoding="utf-8"))
    bad = 0
    prev_to = -1.0
    print(f"\n== {d['id']}  {d['duration']}s  {len(d['sections'])} sections")
    for s in d["sections"]:
        if s["end"] <= s["start"]:
            print(f" !! section {s['id']} bad bounds {s['start']}..{s['end']}")
            bad += 1
        if s["start"] < prev_to - 0.01:
            print(f" !! section {s['id']} starts {s['start']} before prev end {prev_to}")
            bad += 1
        prev_to = s["end"]
        prev_line_to = None
        for i, ln in enumerate(s["lines"]):
            if ln["to"] <= ln["from"]:
                print(f" !! {s['id']}[{i}] to<=from {ln['from']}..{ln['to']}")
                bad += 1
            if ln["from"] < s["start"] - 0.01:
                print(f" !! {s['id']}[{i}] starts {-s['start'] + ln['from']:.2f}s before its section")
                bad += 1
            if ln["to"] > s["end"] + 0.01:
                print(f" !! {s['id']}[{i}] ends {ln['to'] - s['end']:.2f}s after its section")
                bad += 1
            if prev_line_to is not None and ln["from"] < prev_line_to - 0.01:
                print(f" !! {s['id']}[{i}] overlaps previous line by {prev_line_to - ln['from']:.2f}s")
                bad += 1
            prev_line_to = ln["to"]
            ws = ln.get("words") or []
            last = None
            for w in ws:
                if w["to"] <= w["from"]:
                    print(f" !! {s['id']}[{i}] word {w['w']!r} bad span {w['from']}..{w['to']}")
                    bad += 1
                if last is not None and w["from"] < last - 0.001:
                    print(f" !! {s['id']}[{i}] word {w['w']!r} starts before previous ends")
                    bad += 1
                if w["from"] < s["start"] - 0.05 or w["from"] > s["end"] + 0.05:
                    print(f" !! {s['id']}[{i}] word {w['w']!r} onset outside section")
                    bad += 1
                elif w["to"] > s["end"] + 0.05:
                    print(
                        f"  .. {s['id']}[{i}] word {w['w']!r} held {w['to'] - s['end']:.2f}s past section end"
                    )
                last = w["to"]
            ntok = len(ln["text"].split(" "))
            if ws and len(ws) != ntok:
                print(f" !! {s['id']}[{i}] {len(ws)} word times for {ntok} tokens")
                bad += 1
        if s["lines"]:
            print(
                f"  {s['id']:<9} {s['start']:7.2f}-{s['end']:7.2f}  {len(s['lines'])} lines  "
                + " | ".join(f"{ln['from']:.1f}" for ln in s["lines"])
            )
        else:
            print(f"  {s['id']:<9} {s['start']:7.2f}-{s['end']:7.2f}  (instrumental)")
    print("  OK" if not bad else f"  {bad} problem(s)")
    return bad


if __name__ == "__main__":
    names = sys.argv[1:] or ["horizon", "rise"]
    total = 0
    for n in names:
        p = ROOT / "film" / "src" / "data" / f"{n}.json"
        if p.exists():
            total += check(p)
        else:
            print(f"missing {p}")
    sys.exit(1 if total else 0)

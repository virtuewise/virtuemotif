"""Generate YouTube description, tags and chapter text from the timeline data."""
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")
DATA = ROOT / "film" / "src" / "data"
OUT = ROOT / "out" / "youtube"
OUT.mkdir(parents=True, exist_ok=True)

TAGS = {
    "horizon": "zimbabwe music, shona, ndebele, mbira, afrofuturism, lyrical film, lyric video, "
    "african folk, cinematic, sunset, tarisiro, virtuemotif, ambient folk, world music",
    "rise": "zimbabwe anthem, vuka zimbabwe, simudzai mureza, shona, ndebele, african choir, "
    "lyrical film, lyric video, unity, afrofuturism, virtuemotif, world music, uplifting",
}


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def build(d):
    sid = d["id"]
    lines_out = []
    for s in d["sections"]:
        if not s["lines"]:
            continue
        lines_out.append("")
        lines_out.append(f"[{s['label']}]")
        for ln in s["lines"]:
            lines_out.append(ln["text"])
            if ln.get("translation"):
                lines_out.append(f"  ({ln['translation']})")

    chapters = ["0:00 Intro"]
    for s in d["sections"]:
        if not s["lines"]:
            continue
        chapters.append(f"{mmss(s['start'])} {s['label']}")

    desc = f"""{(d['title'] + ' / ' + d['subtitle']).strip()}
{d['artist']}

A lyrical film in cut-paper and dusk light — painted horizons, silhouetted figures, and the lyric carried in moving type.

Sung in Shona, Ndebele and English.
Written, performed and produced by {d['artist']}.

LYRICS
{chr(10).join(lines_out)}

CHAPTERS
{chr(10).join(chapters)}

CREDITS
Song — {d['title']}{(' / ' + d['subtitle']) if d['subtitle'] else ''} · {d['artist']}
Film — 2D paper-cut animation, kinetic typography and sound-synced edit

#{' #'.join([t.strip() for t in TAGS.get(sid, '').split(',')[:6] if t.strip()])}
"""
    (OUT / f"{sid}-description.txt").write_text(desc, encoding="utf-8")
    (OUT / f"{sid}-tags.txt").write_text(TAGS.get(sid, ""), encoding="utf-8")
    print(f"{sid}: {len(chapters)} chapters, description {len(desc)} chars")


if __name__ == "__main__":
    for p in sorted(DATA.glob("*.json")):
        build(json.loads(p.read_text(encoding="utf-8")))

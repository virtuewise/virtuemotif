import json
import sys


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "timing/horizon.aligned.json"
    want = set(sys.argv[2:])
    d = json.load(open(path, encoding="utf-8"))
    for sec in d["sections"]:
        if want and sec["id"] not in want:
            continue
        print("##", sec["id"], sec.get("start"), sec.get("end"))
        for ln in sec["lines"]:
            print("  ", ln["text"][:64])
            for w in ln["words"]:
                print(
                    f"     {w['from']:7.2f} {w['to']:7.2f}  {w['w']}  ({w['score']})"
                )


if __name__ == "__main__":
    main()

from PIL import Image


def main() -> None:
    bad = []
    for i in list(range(0, 30)) + list(range(140, 160)) + list(range(1640, 1650)):
        try:
            im = Image.open(f"out/frames_proof_horizon/element-{i}.png")
            im.load()
            if im.size != (1920, 1080):
                bad.append((i, im.size))
        except Exception as e:
            bad.append((i, str(e)[:40]))
    print("bad:", bad[:10], "count", len(bad))


if __name__ == "__main__":
    main()

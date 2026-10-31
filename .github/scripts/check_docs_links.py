#!/usr/bin/env python3
"""Check that generated HTML documentation has no broken local file links."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class LocalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "build/site").resolve()
    if not root.is_dir():
        print(f"Documentation directory does not exist: {root}", file=sys.stderr)
        return 2

    required = [root / "index.html", root / "tools.html", root / "search.js"]
    missing_required = [path.relative_to(root) for path in required if not path.is_file()]
    if missing_required:
        for path in missing_required:
            print(f"Missing required documentation asset: {path}", file=sys.stderr)
        return 1

    broken: list[str] = []
    for page in sorted(root.rglob("*.html")):
        parser = LocalLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.links:
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or raw.startswith(("#", "data:")):
                continue
            target_path = unquote(parsed.path)
            if not target_path:
                target = page
            elif target_path.endswith("/"):
                target = page.parent / target_path / "index.html"
            else:
                target = page.parent / target_path
            target = target.resolve()
            if root not in target.parents and target != root:
                broken.append(f"{page.relative_to(root)} -> {raw} (outside docs root)")
            elif not target.is_file():
                broken.append(f"{page.relative_to(root)} -> {raw}")

    if broken:
        print("Broken local documentation links:", file=sys.stderr)
        for item in broken:
            print(f"  {item}", file=sys.stderr)
        return 1

    print(f"Checked {len(list(root.rglob('*.html')))} HTML pages; all local file links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

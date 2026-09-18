"""Strips the language pie and the star/fork counters from the 3D contribution SVGs.

github-profile-3d-contrib has no setting for this, so the workflow runs this after it.
Usage:  python3 scripts/trim_3d.py profile/contrib-3d-dark.svg profile/contrib-3d-light.svg
"""

import re
import sys
from pathlib import Path

PIE_GROUP = re.compile(r'<g transform="translate\(40, 520\)">')
# star and fork icons are the only groups drawn at scale(2); each is followed by its count
COUNTER_GROUP = re.compile(r'<g transform="translate\([\d.]+, [\d.]+\), scale\(2\)">')
TRAILING_TEXT = re.compile(r'\s*<text[^>]*>.*?</text>', re.S)


def group_end(svg, start):
    """Index just past the </g> that closes the <g> opening at `start`."""
    depth, pos = 0, start
    for tag in re.finditer(r"<g\b[^>]*?(/?)>|</g>", svg[start:]):
        if tag.group(0) == "</g>":
            depth -= 1
        elif not tag.group(1):
            depth += 1
        if depth == 0:
            return start + tag.end()
    raise ValueError(f"unbalanced <g> starting at {start}")


def remove_group(svg, match, with_trailing_text=False):
    end = group_end(svg, match.start())
    if with_trailing_text:
        text = TRAILING_TEXT.match(svg, end)
        if not text:
            raise ValueError("expected a counter <text> after the icon group")
        end = text.end()
    return svg[: match.start()] + svg[end:]


def trim(svg):
    pie = PIE_GROUP.search(svg)
    if not pie:
        raise ValueError("language pie group not found; the upstream SVG layout may have changed")
    svg = remove_group(svg, pie)
    counters = 0
    while (icon := COUNTER_GROUP.search(svg)):
        svg = remove_group(svg, icon, with_trailing_text=True)
        counters += 1
    if counters != 2:
        raise ValueError(f"expected star and fork counters, found {counters}")
    return svg


def main(paths):
    for path in map(Path, paths):
        path.write_text(trim(path.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"trimmed {path}")


if __name__ == "__main__":
    main(sys.argv[1:])

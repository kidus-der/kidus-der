"""Builds the static SVGs in assets/ (header + research chart) in light and dark.

Run from the repo root:  python3 scripts/make_assets.py
Edit PAPERS_BY_YEAR / PAPERS_BY_TOPIC when a new paper lands.
"""

from pathlib import Path

PAPERS_BY_YEAR = {"2025": 3, "2026": 8}
PAPERS_BY_TOPIC = {
    "benchmarks": 5,
    "datasets": 4,
    "deepfakes": 3,
    "documents": 3,
    "behavioral": 3,
    "llm eval": 3,
    "audio": 1,
}

THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#8B949E", "accent": "#E8B06A", "track": "#21262D"},
    "light": {"fg": "#1F2328", "muted": "#59636E", "accent": "#A8641A", "track": "#EAEEF2"},
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
ETHIOPIC = "'Kefa', 'Nyala', 'Ebrima', 'Noto Sans Ethiopic', 'Abyssinica SIL', " + SANS
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def cell_grid(x0, y0, cols, rows, size, gap, color, seed):
    """A faded contribution-style grid, deterministic so rebuilds don't churn."""
    cells = []
    state = seed
    for c in range(cols):
        for r in range(rows):
            state = (state * 1103515245 + 12345) % (2**31)
            level = state % 5
            fade = (c + 1) / cols
            opacity = round((0.08 + level * 0.18) * fade, 2)
            x = x0 + c * (size + gap)
            y = y0 + r * (size + gap)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2.5" '
                f'fill="{color}" opacity="{opacity}"/>'
            )
    return "\n  ".join(cells)


def header_svg(t):
    grid = cell_grid(520, 38, 22, 7, 13, 4, t["accent"], seed=41)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="200" viewBox="0 0 900 200" role="img" aria-label="Selam, I'm Kidus Dereje">
  <style>
    .hi {{ font: 600 30px {ETHIOPIC}; fill: {t["accent"]}; }}
    .name {{ font: 700 42px {SANS}; fill: {t["fg"]}; letter-spacing: -0.5px; }}
    .sub {{ font: 400 15px {MONO}; fill: {t["muted"]}; }}
  </style>
  {grid}
  <text class="hi" x="24" y="72">ሰላም,</text>
  <text class="name" x="24" y="122">I'm Kidus Dereje</text>
  <text class="sub" x="26" y="156">ml engineer / deepfake + document forensics</text>
</svg>
"""


def year_cells(x0, y0, count, t):
    return "".join(
        f'<rect x="{x0 + i * 17}" y="{y0}" width="13" height="13" rx="2.5" fill="{t["accent"]}"/>'
        for i in range(count)
    )


def research_svg(t):
    total = sum(PAPERS_BY_YEAR.values())
    left = [
        f'<text class="big" x="24" y="92">{total}</text>',
        f'<text class="label" x="26" y="120">papers since {min(PAPERS_BY_YEAR)}</text>',
    ]
    for i, (year, count) in enumerate(PAPERS_BY_YEAR.items()):
        y = 158 + i * 28
        left.append(f'<text class="tick" x="26" y="{y + 11}">{year}</text>')
        left.append(year_cells(72, y, count, t))
        left.append(f'<text class="tick" x="{72 + count * 17 + 6}" y="{y + 11}">{count}</text>')

    bar_x, bar_w, top = 470, 360, 44
    peak = max(PAPERS_BY_TOPIC.values())
    right = [f'<text class="label" x="{bar_x - 110}" y="{top - 14}">by topic</text>']
    for i, (topic, count) in enumerate(PAPERS_BY_TOPIC.items()):
        y = top + i * 28
        w = max(10, round(bar_w * count / peak))
        right += [
            f'<text class="tick" x="{bar_x - 110}" y="{y + 12}">{topic}</text>',
            f'<rect x="{bar_x}" y="{y + 1}" width="{bar_w}" height="14" rx="7" fill="{t["track"]}"/>',
            f'<rect x="{bar_x}" y="{y + 1}" '
            f'width="{w}" height="14" rx="7" fill="{t["accent"]}" opacity="{1 - i * 0.08:.2f}"/>',
            f'<text class="tick" x="{bar_x + bar_w + 12}" y="{y + 12}">{count}</text>',
        ]

    body = "\n  ".join(left + right)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-label="{total} papers: {', '.join(f'{k} {v}' for k, v in PAPERS_BY_TOPIC.items())}">
  <style>
    .big {{ font: 700 64px {SANS}; fill: {t["fg"]}; letter-spacing: -2px; }}
    .label {{ font: 500 14px {MONO}; fill: {t["muted"]}; }}
    .tick {{ font: 400 13px {MONO}; fill: {t["muted"]}; }}
  </style>
  <line x1="300" y1="24" x2="300" y2="216" stroke="{t["track"]}" stroke-width="1.5"/>
  {body}
</svg>
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for mode, theme in THEMES.items():
        (OUT_DIR / f"header-{mode}.svg").write_text(header_svg(theme), encoding="utf-8")
        (OUT_DIR / f"research-{mode}.svg").write_text(research_svg(theme), encoding="utf-8")
    print(f"wrote {len(THEMES) * 2} files to {OUT_DIR}")


if __name__ == "__main__":
    main()

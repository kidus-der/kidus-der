"""Builds the static SVGs in assets/ (header, research graph, stack) in light and dark.

Run from the repo root:  python3 scripts/make_assets.py
Add new papers to PAPERS and new tools to STACK, then rerun.
"""

import math
import re
import urllib.request
from xml.sax.saxutils import escape
from pathlib import Path

# (short name, topics) straight from the tags on kidusder.com/about
PAPERS = [
    ("ChatGPT Images 2.5 in the Wild", ["datasets", "deepfakes", "benchmarks"]),
    ("Advertised vs Measured: Images 2.5", ["documents", "benchmarks"]),
    ("Anatomy of a Scam Call", ["audio", "behavioral", "datasets"]),
    ("CallScreenBench", ["llm eval", "benchmarks", "behavioral"]),
    ("GPT-Image-2 in the Wild", ["datasets"]),
    ("When the Forger Is the Judge", ["documents", "benchmarks"]),
    ("Synthetic Eye Movement Dataset", ["datasets", "behavioral"]),
    ("Open Source Detector Benchmark", ["benchmarks"]),
    ("Can LLMs Detect Document Manipulation?", ["documents", "llm eval"]),
    ("Can LLMs Work as Deepfake Detectors?", ["deepfakes", "llm eval"]),
    ("Do Deepfake Detectors Work in Reality?", ["deepfakes"]),
]
# ordered around the ring so related topics sit next to each other (shortest total edge length)
TOPICS = ["deepfakes", "benchmarks", "documents", "llm eval", "behavioral", "audio", "datasets"]
TOPIC_LABELS = {
    "deepfakes": "deepfake detection",
    "benchmarks": "detector benchmarks",
    "documents": "document forgery",
    "llm eval": "LLM evaluation",
    "behavioral": "behavioral signals",
    "audio": "scam call audio",
    "datasets": "in-the-wild datasets",
}
PULL_MULTI, PULL_SINGLE, JITTER = 0.78, 0.62, 13

# (group label, [(simple-icons slug, label)])
STACK = [
    ("ml", [
        ("pytorch", "PyTorch"), ("tensorflow", "TensorFlow"), ("scikitlearn", "scikit-learn"),
        ("huggingface", "Hugging Face"), ("numpy", "NumPy"), ("pandas", "pandas"),
        ("onnx", "ONNX"), ("weightsandbiases", "W&B"),
    ]),
    ("agents", [
        ("claude", "Claude"), ("openai", "OpenAI"), ("modelcontextprotocol", "MCP"),
        ("langchain", "LangChain"), ("langgraph", "LangGraph"), ("crewai", "CrewAI"),
        ("pydantic", "Pydantic AI"), ("vllm", "vLLM"), ("ollama", "Ollama"),
        ("livekit", "LiveKit"), ("elevenlabs", "ElevenLabs"), ("deepgram", "Deepgram"),
    ]),
]
ICON_CDN = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"

THEMES = {
    "dark": {"fg": "#E6EDF3", "muted": "#8B949E", "accent": "#E8B06A",
             "track": "#21262D", "edge": "#3D444D", "chip": "#161B22"},
    "light": {"fg": "#1F2328", "muted": "#59636E", "accent": "#A8641A",
              "track": "#EAEEF2", "edge": "#D0D7DE", "chip": "#F6F8FA"},
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
MONO_CHAR_WIDTH = 7.8  # approx advance of a 13px monospace glyph

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def lcg(seed):
    """Tiny deterministic RNG so rebuilds don't churn the SVGs."""
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % (2**31)
        yield state


def cell_grid(x0, y0, cols, rows, size, gap, color, seed):
    rng = lcg(seed)
    cells = []
    for c in range(cols):
        for r in range(rows):
            level = next(rng) % 5
            opacity = round((0.08 + level * 0.18) * (c + 1) / cols, 2)
            cells.append(
                f'<rect x="{x0 + c * (size + gap)}" y="{y0 + r * (size + gap)}" width="{size}" '
                f'height="{size}" rx="2.5" fill="{color}" opacity="{opacity}"/>'
            )
    return "\n  ".join(cells)


def header_svg(t):
    grid = cell_grid(520, 38, 22, 7, 13, 4, t["accent"], seed=41)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="200" viewBox="0 0 900 200" role="img" aria-label="hey, I'm Kidus. Founding Engineer / Builder">
  <style>
    .name {{ font: 700 44px {SANS}; fill: {t["fg"]}; letter-spacing: -0.8px; }}
    .dot {{ fill: {t["accent"]}; }}
    .sub {{ font: 400 16px {MONO}; fill: {t["muted"]}; }}
  </style>
  {grid}
  <text class="name" x="22" y="104">hey, I'm Kidus<tspan class="dot">.</tspan></text>
  <text class="sub" x="25" y="142">Founding Engineer / Builder</text>
</svg>
"""


# ---------- research graph ----------

def topic_positions(cx, cy, rx, ry):
    step = 2 * math.pi / len(TOPICS)
    return {
        name: (cx + rx * math.cos(-math.pi / 2 + i * step), cy + ry * math.sin(-math.pi / 2 + i * step))
        for i, name in enumerate(TOPICS)
    }


def paper_positions(topics, cx, cy):
    positions = []
    for i, (_, tags) in enumerate(PAPERS):
        mx = sum(topics[tag][0] for tag in tags) / len(tags)
        my = sum(topics[tag][1] for tag in tags) / len(tags)
        pull = PULL_MULTI if len(tags) > 1 else PULL_SINGLE
        angle = i * 2.4
        positions.append((
            cx + pull * (mx - cx) + JITTER * math.cos(angle),
            cy + pull * (my - cy) + JITTER * math.sin(angle),
        ))
    return positions


def topic_label(name, x, y, cx, radius):
    if abs(x - cx) < 20:
        anchor, lx = "middle", x
        ly = y - radius - 10 if y < 170 else y + radius + 18
    elif x > cx:
        anchor, lx, ly = "start", x + radius + 10, y + 4
    else:
        anchor, lx, ly = "end", x - radius - 10, y + 4
    return f'<text class="topic" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{TOPIC_LABELS[name]}</text>'


def research_svg(t):
    cx, cy = 450, 172
    topics = topic_positions(cx, cy, rx=290, ry=118)
    papers = paper_positions(topics, cx, cy)
    counts = {name: sum(name in tags for _, tags in PAPERS) for name in TOPICS}

    edges, pulses, nodes, labels = [], [], [], []
    edge_index = 0
    for i, ((title, tags), (px, py)) in enumerate(zip(PAPERS, papers)):
        for tag in tags:
            tx, ty = topics[tag]
            path = f"M{px:.1f},{py:.1f} L{tx:.1f},{ty:.1f}"
            edges.append(f'<path d="{path}" class="edge"/>')
            begin = f"{(edge_index * 0.53) % 4:.2f}s"
            pulses.append(
                f'<circle r="2.6" class="pulse" opacity="0">'
                f'<animateMotion dur="2.6s" begin="{begin}" repeatCount="indefinite" path="{path}"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.15;0.8;1" '
                f'dur="2.6s" begin="{begin}" repeatCount="indefinite"/></circle>'
            )
            edge_index += 1
        nodes.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" class="paper"><title>{title}</title></circle>')

    for i, name in enumerate(TOPICS):
        x, y = topics[name]
        radius = 7 + 2.2 * counts[name]
        begin = f"{i * 0.45:.2f}s"
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" class="ring" opacity="0">'
            f'<animate attributeName="r" values="{radius:.1f};{radius + 14:.1f}" dur="3s" begin="{begin}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.55;0" dur="3s" begin="{begin}" repeatCount="indefinite"/></circle>'
        )
        nodes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" class="topic-node"/>')
        labels.append(topic_label(name, x, y, cx, radius))

    body = "\n  ".join(edges + pulses + nodes + labels)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="350" viewBox="0 0 900 350" role="img" aria-label="Research topics: {', '.join(TOPIC_LABELS[n] for n in TOPICS)}">
  <style>
    .edge {{ stroke: {t["edge"]}; stroke-width: 1.2; fill: none; }}
    .pulse {{ fill: {t["accent"]}; }}
    .paper {{ fill: {t["fg"]}; }}
    .topic-node {{ fill: {t["accent"]}; }}
    .ring {{ fill: none; stroke: {t["accent"]}; stroke-width: 1.5; }}
    .topic {{ font: 500 13px {MONO}; fill: {t["fg"]}; }}
    .legend {{ font: 400 12px {MONO}; fill: {t["muted"]}; }}
  </style>
  {body}
  <circle cx="22" cy="336" r="4" class="paper"/>
  <text class="legend" x="32" y="340">paper</text>
</svg>
"""


# ---------- stack ----------

def fetch_icon_path(slug):
    with urllib.request.urlopen(ICON_CDN.format(slug), timeout=20) as resp:
        svg = resp.read().decode("utf-8")
    match = re.search(r'<path d="([^"]+)"', svg)
    if not match:
        raise ValueError(f"no path found in simple-icons/{slug}")
    return match.group(1)


def stack_svg(t, icons):
    width, chip_h, gap, left = 900, 34, 8, 0
    rows, y = [], 4
    for group, tools in STACK:
        rows.append(f'<text class="group" x="2" y="{y + 12}">{group}</text>')
        y += 24
        x = left
        for slug, label in tools:
            chip_w = 42 + len(label) * MONO_CHAR_WIDTH
            if x + chip_w > width:
                x, y = left, y + chip_h + gap
            rows.append(
                f'<g transform="translate({x:.1f},{y})">'
                f'<rect width="{chip_w:.1f}" height="{chip_h}" rx="9" class="chip"/>'
                f'<g transform="translate(11,9) scale(0.667)"><path d="{icons[slug]}" class="icon"/></g>'
                f'<text class="label" x="34" y="22">{escape(label)}</text></g>'
            )
            x += chip_w + gap
        y += chip_h + gap + 14
    height = y - 2
    body = "\n  ".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Stack: {', '.join(escape(label) for _, tools in STACK for _, label in tools)}">
  <style>
    .chip {{ fill: {t["chip"]}; stroke: {t["track"]}; stroke-width: 1; }}
    .icon {{ fill: {t["accent"]}; }}
    .label {{ font: 400 13px {MONO}; fill: {t["fg"]}; }}
    .group {{ font: 500 13px {MONO}; fill: {t["muted"]}; }}
  </style>
  {body}
</svg>
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    icons = {slug: fetch_icon_path(slug) for _, tools in STACK for slug, _ in tools}
    builders = {"header": header_svg, "research": research_svg, "stack": lambda t: stack_svg(t, icons)}
    for mode, theme in THEMES.items():
        for name, build in builders.items():
            (OUT_DIR / f"{name}-{mode}.svg").write_text(build(theme), encoding="utf-8")
    print(f"wrote {len(THEMES) * len(builders)} files to {OUT_DIR}")


if __name__ == "__main__":
    main()

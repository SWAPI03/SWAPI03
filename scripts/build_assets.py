"""Generates the SVG assets used by README.md.

Run from the repo root:  python scripts/build_assets.py
Edit PROJECTS below to change the project cards.
"""
from html import escape
from pathlib import Path
import math
import textwrap

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', 'Fira Code', Consolas, Menlo, 'DejaVu Sans Mono', monospace"

INK = "#f1f5f9"
MUTED = "#94a3b8"
DIM = "#64748b"
EDGE = "#1e293b"

SKY = "#38bdf8"
VIOLET = "#a78bfa"
EMERALD = "#34d399"
AMBER = "#fbbf24"

NO_MOTION = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def mono_width(text, size):
    # Generous estimate so text always fits inside its pill
    return len(text) * size * 0.62


def pill(x, y, text, size, color, text_color, h):
    w = mono_width(text, size) + 22
    return w, (
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
        f'fill="{color}" fill-opacity="0.1" stroke="{color}" stroke-opacity="0.45"/>'
        f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + size * 0.36:.1f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="{size}" fill="{text_color}">{escape(text)}</text>'
    )


# ---------------------------------------------------------------- header

def header():
    W, H = 1200, 340
    layers_x = [770, 880, 990, 1100]
    counts = [3, 5, 5, 2]
    colors = [SKY, VIOLET, VIOLET, EMERALD]
    cy, gap = 178, 48
    nodes = [[(x, cy + (i - (n - 1) / 2) * gap) for i in range(n)] for x, n in zip(layers_x, counts)]

    period = 3.6
    edges, pulses = [], []
    for k in range(len(nodes) - 1):
        for a_i, (x1, y1) in enumerate(nodes[k]):
            for b_i, (x2, y2) in enumerate(nodes[k + 1]):
                d = f"M{x1},{y1} L{x2},{y2}"
                edges.append(f'<path d="{d}"/>')
                # light up roughly half the edges, staggered by layer
                if (a_i + b_i + k) % 2 == 0:
                    delay = k * 1.05 + ((a_i * 3 + b_i * 5) % 7) * 0.05
                    color = colors[k + 1]
                    pulses.append(
                        f'<path d="{d}" pathLength="100" stroke="{color}" '
                        f'style="animation-delay:{delay:.2f}s"/>'
                    )

    node_svg = []
    for k, layer in enumerate(nodes):
        for x, y in layer:
            delay = k * 1.05 + 0.25
            node_svg.append(
                f'<circle class="glow" cx="{x}" cy="{y}" r="15" fill="{colors[k]}" '
                f'style="animation-delay:{delay:.2f}s"/>'
                f'<circle cx="{x}" cy="{y}" r="7" fill="#0b1222" stroke="{colors[k]}" stroke-width="2.2"/>'
            )

    pills, x = [], 64
    for text, color in [("explainable-ai", SKY), ("computer-vision", VIOLET),
                        ("llm-apps", EMERALD), ("open-source", AMBER)]:
        w, svg = pill(x, 264, text, 14, color, "#e2e8f0", 32)
        pills.append(svg)
        x += w + 10

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Swapnil Yadav, ML Engineer, Data Scientist, AI Builder">
<title>Swapnil Yadav</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#060a16"/><stop offset="0.55" stop-color="#0c1428"/><stop offset="1" stop-color="#1a1440"/>
  </linearGradient>
  <linearGradient id="role" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{SKY}"/><stop offset="0.5" stop-color="{VIOLET}"/><stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1.5" cy="1.5" r="1.2" fill="#334155"/>
  </pattern>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0.2" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="0.9"/>
  </linearGradient>
  <mask id="dotmask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>
</defs>
<style>
  .edges path {{ stroke: #475569; stroke-opacity: .6; stroke-width: 1.1; fill: none; }}
  .pulses path {{ fill: none; stroke-width: 2.4; stroke-linecap: round; stroke-dasharray: 9 300;
                 stroke-dashoffset: 10; opacity: 0; animation: travel {period}s linear infinite; }}
  @keyframes travel {{ 0% {{ stroke-dashoffset: 10; opacity: 0; }} 2% {{ opacity: 1; }}
                       27% {{ stroke-dashoffset: -100; opacity: 1; }} 28%, 100% {{ stroke-dashoffset: -100; opacity: 0; }} }}
  .glow {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: fire {period}s ease-out infinite; }}
  @keyframes fire {{ 0% {{ opacity: 0; transform: scale(.4); }} 6% {{ opacity: .55; transform: scale(1); }}
                     22%, 100% {{ opacity: 0; transform: scale(1.5); }} }}
  .blob {{ animation: drift 14s ease-in-out infinite alternate; }}
  .blob2 {{ animation-duration: 18s; animation-direction: alternate-reverse; }}
  @keyframes drift {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(-90px, 40px); }} }}
  .cursor {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ fill-opacity: 0; }} }}
  .live {{ animation: live 2s ease-in-out infinite; }}
  @keyframes live {{ 50% {{ fill-opacity: .25; }} }}
  .rise {{ animation: rise .9s ease-out both; }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
  {NO_MOTION}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle class="blob" cx="980" cy="70" r="150" fill="{VIOLET}" opacity=".28" filter="url(#blur)"/>
  <circle class="blob blob2" cx="1120" cy="300" r="130" fill="{SKY}" opacity=".22" filter="url(#blur)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dotmask)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{EDGE}"/>

<g class="edges">{"".join(edges)}</g>
<g class="pulses">{"".join(pulses)}</g>
<g>{"".join(node_svg)}</g>

<g font-family="{MONO}" font-size="13">
  <circle class="live" cx="887" cy="40" r="5" fill="{EMERALD}"/>
  <text x="900" y="44.5" fill="{MUTED}">open to SWE / ML internships</text>
</g>

<g class="rise">
  <text x="64" y="74" font-family="{MONO}" font-size="19" fill="{EMERALD}">~$ whoami<tspan class="cursor" fill="{EMERALD}"> &#9612;</tspan></text>
  <text x="62" y="150" font-family="{SANS}" font-size="66" font-weight="700" fill="{INK}" letter-spacing="-1">Swapnil Yadav</text>
  <text x="64" y="198" font-family="{SANS}" font-size="27" font-weight="600" fill="url(#role)">ML Engineer · Data Scientist · AI Builder</text>
  <text x="64" y="238" font-family="{MONO}" font-size="16" fill="{MUTED}">B.Tech CSE (AI &amp; DS) @ IIIT Manipur · Lucknow, India</text>
  {"".join(pills)}
</g>
<text x="1136" y="318" text-anchor="end" font-family="{MONO}" font-size="12" fill="#475569">// model.train()</text>
</svg>
'''
    (ASSETS / "header.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- project cards

PROJECTS = [
    {
        "slug": "cve-copilot",
        "kicker": "LLM ENGINEERING",
        "title": "CVE Copilot",
        "status": "in progress",
        "accent": VIOLET,
        "desc": "LLM assistant that turns CVE advisories into JSON briefs and severity calls, scored against NVD ratings.",
        "metrics": [("100%", "WITHIN 1 LEVEL"), ("₹0.07", "COST PER CVE"), ("16", "FROZEN EVAL SET")],
        "chips": ["OpenAI API", "JSON mode", "streaming", "evals"],
    },
    {
        "slug": "chest-xray",
        "kicker": "COMPUTER VISION · MEDICAL AI",
        "title": "Chest X-Ray Pneumonia Detection",
        "accent": SKY,
        "desc": "DenseNet121 fine-tuned to flag pneumonia, with Grad-CAM heatmaps that show where the model is looking.",
        "metrics": [("95.5%", "ACCURACY"), ("0.97", "AUC-ROC"), ("96.2%", "RECALL")],
        "chips": ["PyTorch", "DenseNet121", "Grad-CAM"],
    },
    {
        "slug": "reliability-automl",
        "kicker": "AUTOML · DATA QUALITY",
        "title": "Reliability-Aware AutoML",
        "accent": EMERALD,
        "desc": "Scores data quality on 5 dimensions, spreads row trust through a similarity graph, trains on weighted rows.",
        "metrics": [("5", "QUALITY CHECKS"), ("60K+", "ROWS TESTED"), ("4", "DATASETS")],
        "chips": ["XGBoost", "NetworkX", "SHAP", "Streamlit"],
    },
    {
        "slug": "telco-churn",
        "kicker": "CLASSICAL ML · END TO END",
        "title": "Telco Churn Prediction",
        "accent": AMBER,
        "desc": "Churn model on 7,043 telecom customers, from EDA to a tuned pipeline served in a live Streamlit app.",
        "metrics": [("0.84", "ROC-AUC"), ("0.78", "RECALL (WAS 0.51)"), ("7K", "CUSTOMERS")],
        "chips": ["scikit-learn", "Pandas", "Streamlit"],
    },
]


def card(p, idx):
    W, H = 480, 270
    a = p["accent"]
    lines = textwrap.wrap(p["desc"], 56)
    assert len(lines) <= 2, f'{p["slug"]}: description needs to fit on 2 lines'
    desc = "".join(
        f'<text x="28" y="{108 + i * 22}" font-family="{SANS}" font-size="15" fill="{MUTED}">{escape(t)}</text>'
        for i, t in enumerate(lines)
    )

    metrics = []
    for i, (value, label) in enumerate(p["metrics"]):
        x = 28 + i * 148
        if i:
            metrics.append(f'<line x1="{x - 16}" y1="170" x2="{x - 16}" y2="214" stroke="{EDGE}"/>')
        metrics.append(
            f'<text x="{x}" y="196" font-family="{SANS}" font-size="27" font-weight="700" '
            f'fill="{a if i == 0 else INK}">{escape(value)}</text>'
            f'<text x="{x}" y="216" font-family="{MONO}" font-size="10.5" letter-spacing=".6" fill="{DIM}">{escape(label)}</text>'
        )

    chips, x = [], 28
    for c in p["chips"]:
        w, svg = pill(x, 232, c, 11.5, a, "#cbd5e1", 24)
        chips.append(svg)
        x += w + 8

    if p.get("status"):
        corner = (f'<text x="452" y="42" text-anchor="end" font-family="{MONO}" font-size="12" fill="{a}">'
                  f'<tspan class="live">●</tspan> {escape(p["status"])}</text>')
    else:
        corner = f'<text x="452" y="44" text-anchor="end" font-family="{SANS}" font-size="18" fill="{DIM}">↗</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(p["title"])}">
<title>{escape(p["title"])}</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1426"/><stop offset="1" stop-color="#0a0f1c"/></linearGradient>
  <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></linearGradient>
  <radialGradient id="glow" cx="1" cy="0" r="1"><stop offset="0" stop-color="{a}" stop-opacity=".22"/><stop offset=".6" stop-color="{a}" stop-opacity="0"/></radialGradient>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<style>
  .live {{ animation: live 1.8s ease-in-out infinite; }}
  @keyframes live {{ 50% {{ fill-opacity: .2; }} }}
  {NO_MOTION}
</style>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect width="{W}" height="3" fill="url(#bar)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>
<text x="28" y="42" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{a}">{idx:02d} · {escape(p["kicker"])}</text>
{corner}
<text x="28" y="78" font-family="{SANS}" font-size="23" font-weight="700" fill="{INK}">{escape(p["title"])}</text>
{desc}
<line x1="28" y1="156" x2="452" y2="156" stroke="{EDGE}"/>
{"".join(metrics)}
{"".join(chips)}
</svg>
'''
    (ASSETS / "projects" / f'{p["slug"]}.svg').write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- kaggle medal

def medal():
    W, H = 1000, 170
    BRONZE, BRONZE_LIGHT = "#cd7f32", "#f2b880"
    mx, my = 96, 98

    star = []
    for i in range(10):
        r = 17 if i % 2 == 0 else 7.5
        ang = math.radians(-90 + i * 36)
        star.append(f"{mx + r * math.cos(ang):.1f},{my + r * math.sin(ang):.1f}")

    stats = []
    for i, (value, label) in enumerate([("287th", "PLACE"), ("3,947", "TEAMS"), ("Top 8%", "FINISH")]):
        x = 700 + i * 96
        stats.append(
            f'<text x="{x}" y="96" font-family="{SANS}" font-size="26" font-weight="700" '
            f'fill="{BRONZE_LIGHT if i == 0 else INK}">{value}</text>'
            f'<text x="{x}" y="118" font-family="{MONO}" font-size="10.5" letter-spacing=".6" fill="{DIM}">{label}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Kaggle competition bronze medal: Biohub Cell Tracking During Development, 287th of 3,947 teams">
<title>Kaggle Bronze Medal</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#140f0c"/><stop offset=".45" stop-color="#0d1426"/><stop offset="1" stop-color="#0a0f1c"/></linearGradient>
  <radialGradient id="glow" cx="0.08" cy="0.5" r="0.5"><stop offset="0" stop-color="{BRONZE}" stop-opacity=".28"/><stop offset="1" stop-color="{BRONZE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="metal" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#ffd9ad"/><stop offset=".45" stop-color="{BRONZE}"/><stop offset="1" stop-color="#7a3f14"/></radialGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <clipPath id="disc"><circle cx="{mx}" cy="{my}" r="44"/></clipPath>
</defs>
<style>
  .shine {{ animation: sweep 4s ease-in-out infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-120px) skewX(-20deg); }} 45%, 100% {{ transform: translateX(120px) skewX(-20deg); }} }}
  {NO_MOTION}
</style>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <polygon points="64,-2 90,-2 108,58 82,58" fill="#1e3a5f"/>
  <polygon points="128,-2 102,-2 84,58 110,58" fill="#3b2f6b"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>

<circle cx="{mx}" cy="{my}" r="44" fill="url(#metal)" stroke="{BRONZE_LIGHT}" stroke-width="1.5"/>
<circle cx="{mx}" cy="{my}" r="34" fill="none" stroke="#7a3f14" stroke-opacity=".7" stroke-width="2"/>
<polygon points="{" ".join(star)}" fill="#fff1e0" fill-opacity=".9"/>
<g clip-path="url(#disc)"><rect class="shine" x="{mx - 20}" y="{my - 50}" width="40" height="100" fill="url(#shine)"/></g>

<text x="172" y="62" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{BRONZE_LIGHT}">KAGGLE · COMPETITION BRONZE MEDAL · 2026</text>
<text x="172" y="96" font-family="{SANS}" font-size="22" font-weight="700" fill="{INK}">Biohub: Cell Tracking During Development</text>
<text x="172" y="122" font-family="{SANS}" font-size="15" fill="{MUTED}">Research competition with a $60,000 prize pool</text>
<line x1="672" y1="58" x2="672" y2="124" stroke="{EDGE}"/>
{"".join(stats)}
</svg>
'''
    (ASSETS / "kaggle-bronze.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- footer

def wave(width, base, amp, length):
    d = f"M0,{base}"
    x, up = 0, True
    while x < width:
        d += f" Q{x + length / 4},{base - amp if up else base + amp} {x + length / 2},{base}"
        x += length / 2
        up = not up
    return d + f" L{width},160 L0,160 Z"


def footer():
    W, H = 1200, 160
    layers = [(90, 14, 600, ".25", "16s"), (104, 12, 400, ".4", "11s"), (118, 10, 300, ".85", "8s")]
    waves = "".join(
        f'<path class="w{i}" d="{wave(W + length, base, amp, length)}" fill="url(#g)" fill-opacity="{op}"/>'
        for i, (base, amp, length, op, dur) in enumerate(layers)
    )
    motion = "".join(
        f".w{i} {{ animation: flow{i} {dur} linear infinite; }} "
        f"@keyframes flow{i} {{ to {{ transform: translateX(-{length}px); }} }}\n  "
        for i, (base, amp, length, op, dur) in enumerate(layers)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Footer">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{SKY}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
</defs>
<style>
  {motion}{NO_MOTION}
</style>
<text x="{W / 2}" y="46" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{DIM}">// thanks for stopping by</text>
{waves}
</svg>
'''
    (ASSETS / "footer.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    (ASSETS / "projects").mkdir(parents=True, exist_ok=True)
    header()
    for i, p in enumerate(PROJECTS, 1):
        card(p, i)
    medal()
    footer()
    print("assets written to", ASSETS)

"""Generates the SVG assets used by README.md (ink / manga theme).

Run from the repo root:  python scripts/build_assets.py

Fonts (OFL / Apache, from github.com/google/fonts) are downloaded on the first
run and cached in scripts/.fonts. Each SVG embeds a subset of only the glyphs
it uses, so text renders the same everywhere.
"""
import base64
import io
import math
import random
import urllib.request
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_DIR = Path(__file__).resolve().parent / ".fonts"
FONT_SRC = "https://raw.githubusercontent.com/google/fonts/main/"

PAPER = "#f2ede3"
INK = "#121212"
SOFT = "#2e2b27"
GREY = "#6f695f"
RED = "#d6301f"
BRONZE = "#b5712f"

FONT_FILES = {
    "display": "ofl/anton/Anton-Regular.ttf",
    "mono": "ofl/spacemono/SpaceMono-Bold.ttf",
    "body": "ofl/ibmplexsanscondensed/IBMPlexSansCondensed-Medium.ttf",
    "hand": "apache/permanentmarker/PermanentMarker-Regular.ttf",
}
FALLBACK = {
    "display": "Impact, 'Arial Narrow', sans-serif",
    "mono": "Consolas, Menlo, monospace",
    "body": "'Arial Narrow', 'Segoe UI', sans-serif",
    "hand": "'Comic Sans MS', cursive",
}

FILTERS = """
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .11 0"/></filter>
<filter id="rough" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3.5" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="brush" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".06" numOctaves="3" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="8" xChannelSelector="R" yChannelSelector="G"/></filter>
"""


class Font:
    def __init__(self, key):
        self.path = FONT_DIR / Path(FONT_FILES[key]).name
        if not self.path.exists():
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(FONT_SRC + FONT_FILES[key], self.path)
        tt = TTFont(self.path)
        self.cmap = tt.getBestCmap()
        self.hmtx = tt["hmtx"]
        self.upm = tt["head"].unitsPerEm
        self.cap = tt["OS/2"].sCapHeight / self.upm

    def width(self, text, size, ls=0):
        missing = [c for c in text if ord(c) not in self.cmap]
        assert not missing, f"{self.path.name} has no glyph for {missing}"
        adv = sum(self.hmtx[self.cmap[ord(c)]][0] for c in text)
        return adv / self.upm * size + ls * len(text)


FONTS = {k: Font(k) for k in FONT_FILES}


def tw(key, text, size, ls=0):
    return FONTS[key].width(text, size, ls)


def cap(key, size):
    return FONTS[key].cap * size


def wrap(text, key, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and tw(key, trial, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def font_face(key, chars):
    opts = subset.Options()
    opts.flavor = "woff"
    opts.hinting = False
    opts.layout_features = ["kern"]
    font = TTFont(FONTS[key].path)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'SY-{key}';src:url(data:font/woff;base64,{data}) format('woff');}}"


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


class Svg:
    """Collects markup and the glyphs used per font, then embeds font subsets."""

    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.css, self.body = [], [], []
        self.used = {}

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, x, y, s, key, size, fill=INK, anchor="start", ls=0, attrs=""):
        self.used.setdefault(key, set()).update(s)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        return (f'<text x="{x:.1f}" y="{y:.1f}" class="{key[0]}" font-size="{size}" '
                f'fill="{fill}"{a}{l}{attrs}>{escape(s)}</text>')

    def tag(self, x, top, s, size=13, fg=PAPER, bg=INK, anchor="start", ls=1.5):
        """Solid label box. Returns (markup, width)."""
        w = tw("mono", s, size, ls) + 20
        h = size + 14
        if anchor == "middle":
            x -= w / 2
        box = f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h}" fill="{bg}"/>'
        return box + self.text(x + 10, top + h / 2 + cap("mono", size) / 2, s, "mono", size, fg, ls=ls), w

    def chips(self, x, top, items, size=12):
        out = []
        for item in items:
            w = tw("mono", item, size, 1) + 18
            out.append(f'<rect x="{x:.1f}" y="{top}" width="{w:.1f}" height="26" fill="{PAPER}" '
                       f'stroke="{INK}" stroke-width="2"/>')
            out.append(self.text(x + 9, top + 13 + cap("mono", size) / 2, item, "mono", size, INK, ls=1))
            x += w + 8
        return "".join(out)

    def sfx(self, x, y, s, size, rot=0, anchor="start", shadow=RED, off=6):
        """Manga sound-effect style number: ink fill, paper outline, red offset print."""
        stroke = f' stroke="{PAPER}" stroke-width="{size / 9:.1f}" stroke-linejoin="round" paint-order="stroke"'
        return (f'<g transform="rotate({rot} {x:.1f} {y:.1f})">'
                + self.text(x + off, y + off, s, "display", size, shadow, anchor, attrs=stroke)
                + self.text(x, y, s, "display", size, INK, anchor, attrs=stroke)
                + "</g>")

    def paragraph(self, x, y, s, size, maxw, lead, fill=SOFT, key="body"):
        lines = wrap(s, key, size, maxw)
        return "".join(self.text(x, y + i * lead, line, key, size, fill) for i, line in enumerate(lines)), len(lines)

    def render(self):
        faces = "".join(font_face(k, chars) for k, chars in sorted(self.used.items()))
        classes = "".join(f".{k[0]}{{font-family:'SY-{k}',{FALLBACK[k]};}}" for k in sorted(self.used))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">\n'
                f"<title>{escape(self.label)}</title>\n<defs>{FILTERS}{''.join(self.defs)}</defs>\n"
                f"<style>{faces}{classes}{''.join(self.css)}</style>\n" + "\n".join(self.body) + "\n</svg>\n")

    def save(self, name):
        path = ASSETS / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8")


# ---------------------------------------------------------------- drawing helpers

def focus_lines(cx, cy, r_in, r_out, n, rng, color=INK):
    """Manga concentration lines radiating from (cx, cy)."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.025, 0.025)
        w = rng.uniform(0.003, 0.013)
        r0 = r_in * rng.uniform(1.0, 1.7)
        p = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
             (cx + r_out * math.cos(a - w), cy + r_out * math.sin(a - w)),
             (cx + r_out * math.cos(a + w), cy + r_out * math.sin(a + w))]
        out.append(f'<polygon points="{pts(p)}"/>')
    return f'<g fill="{color}">{"".join(out)}</g>'


def speed_lines(x0, x1, y0, y1, n, rng, color=INK):
    """Horizontal motion streaks that taper to the left."""
    out = []
    for _ in range(n):
        y = rng.uniform(y0, y1)
        start = x1 - rng.uniform(0.35, 1.0) * (x1 - x0)
        t = rng.uniform(1, 5)
        out.append(f'<polygon points="{pts([(start, y), (x1, y - t / 2), (x1, y + t / 2)])}"/>')
    return f'<g fill="{color}">{"".join(out)}</g>'


def burst(cx, cy, r1, r2, n, rng, rx=1.0):
    p = []
    for i in range(2 * n):
        a = math.pi * i / n
        r = (r2 if i % 2 == 0 else r1) * rng.uniform(0.9, 1.08)
        p.append((cx + r * math.cos(a) * rx, cy + r * math.sin(a)))
    return p


def halftone(cx, cy, R, step, max_r, color, falloff=0.9):
    """Screentone: dots shrink with distance from the centre."""
    dots = []
    row = 0
    y = cy - R
    while y <= cy + R:
        x = cx - R + (step / 2 if row % 2 else 0)
        while x <= cx + R:
            d = math.hypot(x - cx, y - cy) / R
            if d < 1:
                r = max_r * (1 - d) ** falloff
                if r > 0.45:
                    dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}"/>')
            x += step
        y += step * 0.866
        row += 1
    return f'<g fill="{color}">{"".join(dots)}</g>'


def stamp(svg, cx, cy, s, rot, size=24, color=RED):
    w = tw("display", s, size, 2) + 34
    h = cap("display", size) + 26
    svg.css.append(".slam{transform-box:fill-box;transform-origin:center;animation:slam .45s cubic-bezier(.2,1.6,.4,1) .7s backwards}"
                   "@keyframes slam{from{transform:scale(1.8);opacity:0}}")
    return (f'<g transform="translate({cx} {cy}) rotate({rot})"><g class="slam" filter="url(#rough)" opacity=".9">'
            f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{color}" stroke-width="3.5"/>'
            f'<rect x="{-w / 2 + 5:.1f}" y="{-h / 2 + 5:.1f}" width="{w - 10:.1f}" height="{h - 10:.1f}" fill="none" stroke="{color}" stroke-width="1.5"/>'
            + svg.text(0, cap("display", size) / 2, s, "display", size, color, "middle", ls=2)
            + "</g></g>")


def hand_arrow(x0, y0, x1, y1, bend, color=RED, width=3):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + bend
    a = math.atan2(y1 - my, x1 - mx)
    h1 = (x1 - 14 * math.cos(a - 0.5), y1 - 14 * math.sin(a - 0.5))
    h2 = (x1 - 14 * math.cos(a + 0.5), y1 - 14 * math.sin(a + 0.5))
    return (f'<g fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" filter="url(#rough)">'
            f'<path d="M{x0},{y0} Q{mx},{my} {x1},{y1}"/>'
            f'<path d="M{h1[0]:.1f},{h1[1]:.1f} L{x1},{y1} L{h2[0]:.1f},{h2[1]:.1f}"/></g>')


def paper(svg, w, h, outline=True):
    svg.add(f'<rect width="{w}" height="{h}" fill="{PAPER}"/>')
    if outline:
        svg.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="#cfc6b4"/>')


def grain(svg, w, h):
    svg.add(f'<rect width="{w}" height="{h}" filter="url(#grain)" pointer-events="none"/>')


# ---------------------------------------------------------------- header

def header():
    W, H = 1200, 470
    s = Svg(W, H, "Swapnil Yadav: ML Engineer, Data Scientist, AI Builder")
    rng = random.Random(3)
    paper(s, W, H, outline=False)
    s.defs.append('<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
                  '<stop offset="1" stop-color="#5a4a2a" stop-opacity=".22"/></radialGradient>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')

    # book-cover frame
    s.add(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" fill="none" stroke="{INK}" stroke-width="3"/>',
          f'<rect x="22" y="22" width="{W - 44}" height="{H - 44}" fill="none" stroke="{INK}" stroke-width="1"/>')
    s.add(s.text(48, 60, "SWAPI03  /  VOL. 2026", "mono", 13, INK, ls=3),
          s.text(W - 48, 60, "LUCKNOW  /  IIIT MANIPUR", "mono", 13, INK, "end", ls=3),
          f'<line x1="48" y1="76" x2="{W - 48}" y2="76" stroke="{INK}" stroke-width="1.5"/>')

    # stacked name: solid ink over screentone-filled outline
    size = 138
    c = cap("display", size)
    y1 = 76 + 26 + c
    y2 = y1 + c + 20
    s.defs.append(f'<pattern id="tone" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                  f'<circle cx="3.5" cy="3.5" r="1.9" fill="{INK}"/></pattern>')
    s.add(s.text(44, y1, "SWAPNIL", "display", size, INK, ls=2),
          s.text(44, y2, "YADAV", "display", size, "url(#tone)", ls=2,
                 attrs=f' stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"'))
    s.add(s.text(48, y2 + 40, "ML ENGINEER  /  DATA SCIENTIST  /  AI BUILDER", "mono", 16, INK, ls=2.5))

    # ensō, drawn in on load
    cx, cy, R = 930, 232, 132
    a0 = math.radians(-58)
    path = []
    for i in range(121):
        a = a0 + math.radians(328) * i / 120
        r = R + 5 * math.sin(2 * a + 0.7) + 2.5 * math.sin(5 * a)
        path.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in path)
    head = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in path[:34])
    tail = path[70:]
    s.css.append(".draw{stroke-dasharray:1000;stroke-dashoffset:0;animation:draw 2.4s cubic-bezier(.55,.1,.3,1) .3s backwards}"
                 "@keyframes draw{from{stroke-dashoffset:1000}}"
                 ".dry{animation:dry .8s ease-out 2.2s backwards}@keyframes dry{from{opacity:0}}")
    s.add(f'<g fill="none" stroke="{INK}" stroke-linecap="round" filter="url(#brush)">'
          f'<path class="draw" pathLength="1000" d="{d}" stroke-width="24"/>'
          f'<path class="draw" pathLength="1000" d="{head}" stroke-width="36" style="animation-duration:.7s"/>'
          + "".join(
              f'<path class="dry" d="M' + " L".join(f"{cx + (math.hypot(x - cx, y - cy) + off) * (x - cx) / math.hypot(x - cx, y - cy):.1f},"
                                                     f"{cy + (math.hypot(x - cx, y - cy) + off) * (y - cy) / math.hypot(x - cx, y - cy):.1f}"
                                                     for x, y in tail)
              + f'" stroke-width="{sw}" stroke-dasharray="{dash}" opacity=".75"/>'
              for off, sw, dash in [(-9, 3, "40 9 70 16 22 8"), (10, 2.5, "26 12 50 8 90 20"), (15, 2, "60 22 30 14")])
          + "</g>")
    ex, ey = path[-1]
    s.add(f'<g fill="{INK}" filter="url(#rough)" class="dry">'
          + "".join(f'<circle cx="{ex + rng.uniform(4, 30):.1f}" cy="{ey + rng.uniform(-18, 8):.1f}" r="{rng.uniform(1.5, 4.5):.1f}"/>'
                    for _ in range(4)) + "</g>")

    # hanko seal
    s.add(f'<g transform="translate(1046 330) rotate(5)"><g class="slam" filter="url(#rough)">'
          f'<rect x="-36" y="-36" width="72" height="72" rx="4" fill="{RED}"/>'
          f'<rect x="-29" y="-29" width="58" height="58" fill="none" stroke="{PAPER}" stroke-width="2"/>'
          + s.text(0, cap("display", 34) / 2, "SY", "display", 34, PAPER, "middle", ls=1) + "</g></g>")
    s.css.append(".slam{transform-box:fill-box;transform-origin:center;animation:slam .45s cubic-bezier(.2,1.6,.4,1) 2.4s backwards}"
                 "@keyframes slam{from{transform:scale(1.8);opacity:0}}")

    # scrolling ticker on a black band
    seq = "B.TECH CSE (AI & DS)  •  KAGGLE BRONZE MEDALIST  •  MERGED PRS IN CREWAI + COMPOSIO  •  EX-ML INTERN @ FLYRANK  •  OPEN TO SWE / ML INTERNSHIPS  •  "
    sw = tw("mono", seq, 14, 2)
    reps = math.ceil((W + sw) / sw) + 1
    band_y = H - 64
    s.defs.append(f'<clipPath id="tick"><rect x="22" y="{band_y}" width="{W - 44}" height="42"/></clipPath>')
    s.css.append(f".tick{{animation:tick 26s linear infinite}}@keyframes tick{{to{{transform:translateX(-{sw:.1f}px)}}}}")
    s.add(f'<rect x="22" y="{band_y}" width="{W - 44}" height="42" fill="{INK}"/>',
          f'<g clip-path="url(#tick)"><g class="tick">'
          + s.text(40, band_y + 21 + cap("mono", 14) / 2, seq * reps, "mono", 14, PAPER, ls=2) + "</g></g>")

    s.css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    grain(s, W, H)
    s.save("header.svg")


# ---------------------------------------------------------------- featured projects: one manga page

def featured():
    W, H, M, G = 1000, 1180, 20, 9
    s = Svg(W, H, "Featured projects: CVE Copilot, Chest X-Ray Pneumonia Detection, Reliability-Aware AutoML, Telco Churn Prediction")
    rng = random.Random(11)
    paper(s, W, H)

    g1 = lambda x: 392 - 0.03 * x          # gutter under panel A
    g3 = lambda x: 792 + 0.028 * x         # gutter above panel D
    g2 = lambda y: 584 - 0.1 * (y - 380)   # slanted gutter between B and C

    def meet(line, dy, dx):
        x = 560
        for _ in range(30):
            x = g2(line(x) + dy) + dx
        return x, line(x) + dy

    panels = {
        "A": [(M, M), (W - M, M), (W - M, g1(W - M) - G), (M, g1(M) - G)],
        "B": [(M, g1(M) + G), meet(g1, G, -G), meet(g3, -G, -G), (M, g3(M) - G)],
        "C": [meet(g1, G, G), (W - M, g1(W - M) + G), (W - M, g3(W - M) - G), meet(g3, -G, G)],
        "D": [(M, g3(M) + G), (W - M, g3(W - M) + G), (W - M, H - M), (M, H - M)],
    }
    for k, p in panels.items():
        s.defs.append(f'<clipPath id="p{k}"><polygon points="{pts(p)}"/></clipPath>')

    def fade(id_, x0, x1):
        s.defs.append(f'<linearGradient id="{id_}g" x1="{x0}" x2="{x1}" y1="0" y2="0" gradientUnits="userSpaceOnUse">'
                      f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
                      f'<mask id="{id_}"><rect width="{W}" height="{H}" fill="url(#{id_}g)"/></mask>')

    def border(k):
        s.add(f'<polygon points="{pts(panels[k])}" fill="none" stroke="{INK}" stroke-width="5" '
              f'stroke-linejoin="round" filter="url(#rough)"/>')

    # A: CVE Copilot
    fade("fA", 500, 640)
    bx, by = 770, 186
    s.add(f'<g clip-path="url(#pA)"><g mask="url(#fA)">{focus_lines(bx, by, 120, 760, 130, rng)}</g>'
          f'<polygon points="{pts(burst(bx, by, 92, 126, 22, rng, rx=1.38))}" fill="{PAPER}" stroke="{INK}" '
          f'stroke-width="4" stroke-linejoin="round" filter="url(#rough)"/></g>')
    s.add(s.sfx(bx, by + cap("display", 112) / 2 - 6, "100%", 112, rot=-6, anchor="middle"))
    t, _ = s.tag(bx, 262, "WITHIN 1 SEVERITY LEVEL", 12, anchor="middle")
    s.add(t, stamp(s, 872, 62, "IN PROGRESS", 8))
    t, _ = s.tag(50, 50, "CH.01  /  LLM ENGINEERING")
    s.add(t, s.text(46, 50 + 27 + 18 + cap("display", 84), "CVE COPILOT", "display", 84, INK, ls=1))
    p, n = s.paragraph(50, 196, "LLM assistant that turns raw CVE advisories into JSON briefs and severity calls, "
                                "scored against real NVD ratings on a frozen 16-CVE eval set.", 19, 430, 25)
    s.add(p, s.chips(50, 196 + (n - 1) * 25 + 22, ["OPENAI API", "JSON MODE", "STREAMING", "EVALS"]))
    s.add(s.text(500, 336, "only 0.07 INR per CVE", "hand", 21, RED, attrs=' transform="rotate(-4 500 336)"'))
    border("A")

    # B: Chest X-Ray (an X-ray film with a Grad-CAM hot spot)
    fx, fy, fw, fh = 346, 440, 186, 292
    s.defs.append(f'<radialGradient id="lung" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="#3a3a3a"/>'
                  f'<stop offset="1" stop-color="#0b0b0b"/></radialGradient>')
    ribs = []
    mid = fx + fw / 2
    for i in range(7):
        y = fy + 70 + i * 29
        spread = 56 + i * 4
        for sgn in (-1, 1):
            ribs.append(f'<path d="M{mid + sgn * 8},{y} C{mid + sgn * spread * .55},{y - 20} {mid + sgn * spread},{y - 4} '
                        f'{mid + sgn * (spread - 6)},{y + 26}"/>')
    vert = "".join(f'<rect x="{mid - 7}" y="{fy + 34 + i * 17}" width="14" height="13" rx="3"/>' for i in range(14))
    s.add(f'<g clip-path="url(#pB)"><g transform="rotate(2.5 {fx + fw / 2} {fy + fh / 2})">'
          f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="url(#lung)" stroke="{INK}" stroke-width="4"/>'
          f'<g fill="none" stroke="{PAPER}" stroke-width="4.5" stroke-linecap="round" opacity=".85">{"".join(ribs)}'
          f'<path d="M{mid - 6},{fy + 52} Q{mid - 50},{fy + 38} {fx + 18},{fy + 50}"/>'
          f'<path d="M{mid + 6},{fy + 52} Q{mid + 50},{fy + 38} {fx + fw - 18},{fy + 50}"/></g>'
          f'<g fill="{PAPER}" opacity=".8">{vert}</g>'
          + halftone(fx + 52, fy + 206, 50, 7, 3.4, RED) + halftone(fx + 52, fy + 208, 22, 6, 2.2, "#ffb347")
          + f'<path d="M{fx + 40},{fy + 168} L{fx + 26},{fy + 140} L{fx + 14},{fy + 140}" fill="none" stroke="{PAPER}" stroke-width="1.5"/>'
          + s.text(fx + 12, fy + 133, "GRAD-CAM", "mono", 10, PAPER, ls=1)
          + s.text(fx + 12, fy + 30, "R", "display", 24, PAPER)
          + s.text(fx + 12, fy + fh - 12, "AUC 0.97", "mono", 11, PAPER, ls=1)
          + s.text(fx + fw - 12, fy + fh - 12, "RECALL 96.2%", "mono", 11, PAPER, "end", ls=1)
          + "</g></g>")
    t, _ = s.tag(48, 432, "CH.02  /  VISION")
    tsize = 60
    while tw("display", "CHEST X-RAY", tsize, 1) > fx - 46 - 18:
        tsize -= 1
    ty = 432 + 27 + 14 + cap("display", tsize)
    s.add(t, s.text(46, ty, "CHEST X-RAY", "display", tsize, INK, ls=1))
    s.add(s.text(48, ty + 26, "PNEUMONIA DETECTION", "mono", 13, GREY, ls=2))
    p, n = s.paragraph(48, ty + 56, "DenseNet121 fine-tuned to flag pneumonia, with Grad-CAM showing where it looks.",
                       17, fx - 48 - 22, 22)
    chips_top = ty + 56 + (n - 1) * 22 + 16
    s.add(p, s.chips(48, chips_top, ["PYTORCH", "DENSENET121"]))
    s.add(s.sfx(50, chips_top + 26 + 10 + cap("display", 70), "95.5%", 70, rot=-4))
    t, _ = s.tag(52, chips_top + 26 + 10 + cap("display", 70) + 10, "ACCURACY", 11)
    s.add(t)
    border("B")

    # C: Reliability-Aware AutoML (a trust graph)
    gx0, gx1, gy0, gy1 = 800, 956, 712, 790
    nodes = []
    while len(nodes) < 11:
        x, y = rng.uniform(gx0, gx1), rng.uniform(gy0, gy1)
        if all(math.hypot(x - a, y - b) > 30 for a, b, _ in nodes):
            nodes.append((x, y, rng.uniform(0.2, 1)))
    edges = set()
    for i, (x, y, _) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.hypot(nodes[j][0] - x, nodes[j][1] - y))[1:3]
        edges.update(tuple(sorted((i, j))) for j in near)
    graph = [halftone((gx0 + gx1) / 2, (gy0 + gy1) / 2, 110, 9, 2.6, "#b7ad9a")]
    for i, j in edges:
        weak = min(nodes[i][2], nodes[j][2]) < 0.35
        graph.append(f'<line x1="{nodes[i][0]:.1f}" y1="{nodes[i][1]:.1f}" x2="{nodes[j][0]:.1f}" y2="{nodes[j][1]:.1f}" '
                     f'stroke="{INK}" stroke-width="{1.5 if weak else 2.5}"{" stroke-dasharray=\"4 4\"" if weak else ""}/>')
    for x, y, t_ in nodes:
        r = 4 + 9 * t_
        if t_ > 0.6:
            graph.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{INK}"/>')
        elif t_ > 0.35:
            graph.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="2.5"/>')
        else:
            graph.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2:.1f}" fill="{PAPER}" stroke="{RED}" stroke-width="2.5" stroke-dasharray="3 3"/>')
    s.add(f'<g clip-path="url(#pC)">{"".join(graph)}</g>')
    s.add(s.text(gx1 + 4, gy0 - 14, "low trust = less weight", "hand", 15, RED, "end", attrs=f' transform="rotate(-3 {gx1} {gy0})"'))
    t, _ = s.tag(612, 420, "CH.03  /  AUTOML")
    y = 420 + 27 + 12 + cap("display", 44)
    s.add(t, s.text(610, y, "RELIABILITY-AWARE", "display", 44, INK, ls=1),
          s.text(610, y + cap("display", 44) + 12, "AUTOML", "display", 44, INK, ls=1))
    p, n = s.paragraph(612, y + cap("display", 44) + 46, "Scores data quality on 5 dimensions, spreads row trust through "
                                                         "a similarity graph, then trains on trust-weighted rows.", 16, 345, 21)
    s.add(p, s.chips(612, y + cap("display", 44) + 46 + (n - 1) * 21 + 16, ["XGBOOST", "NETWORKX", "SHAP"]))
    s.add(s.sfx(614, 760, "60K+", 70, rot=-5))
    t, _ = s.tag(616, 768, "ROWS / 4 DATASETS", 11)
    s.add(t)
    border("C")

    # D: Telco churn (recall powers up from 0.51 to 0.78)
    fade("fD", 470, 620)
    top = g3(M) + G
    s.add(f'<g clip-path="url(#pD)"><g mask="url(#fD)">{speed_lines(470, W - M, top + 40, H - 40, 70, rng)}</g>'
          f'<ellipse cx="790" cy="1000" rx="215" ry="105" fill="{PAPER}" filter="url(#brush)" opacity=".92"/></g>')
    big = 138
    x78 = W - M - 30 - tw("display", "0.78", big, 1)
    ax1, ax0 = x78 - 16, x78 - 106
    x51 = ax0 - 14
    w51 = tw("display", "0.51", 62, 1)
    s.add(s.text(x51, 1004, "0.51", "display", 62, GREY, "end", ls=1),
          f'<path d="M{x51 - w51 - 6},{994} L{x51 + 6},{980}" stroke="{RED}" stroke-width="7" stroke-linecap="round" filter="url(#rough)"/>',
          f'<g fill="{INK}" filter="url(#brush)"><polygon points="{pts([(ax0, 980), (ax1 - 34, 974), (ax1 - 34, 962), (ax1, 984), (ax1 - 34, 1006), (ax1 - 34, 994), (ax0, 990)])}"/></g>',
          s.sfx(x78, 1040, "0.78", big, rot=-4))
    t, _ = s.tag(x78 + 18, 1058, "CHURN RECALL", 12)
    s.add(t, s.text(x51 - w51, 1124, "53% more churners caught", "hand", 21, RED, attrs=f' transform="rotate(-3 {x51 - w51} 1124)"'))
    t, _ = s.tag(52, top + 34, "CH.04  /  CLASSICAL ML")
    s.add(t, s.text(48, top + 34 + 27 + 18 + cap("display", 84), "TELCO CHURN", "display", 84, INK, ls=1))
    yy = top + 34 + 27 + 18 + cap("display", 84) + 38
    p, n = s.paragraph(52, yy, "End-to-end churn model on 7,043 telecom customers, from EDA to a tuned pipeline "
                               "served in a live Streamlit app.", 19, 400, 25)
    s.add(p, s.chips(52, yy + (n - 1) * 25 + 22, ["SCIKIT-LEARN", "PANDAS", "STREAMLIT"]))
    s.add(s.text(52, yy + (n - 1) * 25 + 22 + 56, "ROC-AUC 0.84  /  7,043 CUSTOMERS", "mono", 13, GREY, ls=1.5))
    border("D")

    grain(s, W, H)
    s.save("featured.svg")


# ---------------------------------------------------------------- kaggle medal panel

def medal():
    W, H = 1000, 270
    s = Svg(W, H, "Kaggle competition bronze medal: Biohub Cell Tracking During Development, 287th of 3,947 teams, top 8%")
    rng = random.Random(5)
    paper(s, W, H)
    mx, my = 140, 148
    s.defs.append(f'<clipPath id="k"><rect x="10" y="10" width="{W - 20}" height="{H - 20}"/></clipPath>'
                  f'<clipPath id="disc"><circle cx="{mx}" cy="{my}" r="64"/></clipPath>'
                  f'<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                  f'<rect width="7" height="7" fill="{PAPER}"/><rect width="3" height="7" fill="{INK}"/></pattern>'
                  f'<linearGradient id="kfg" x1="200" x2="262" y1="0" y2="0" gradientUnits="userSpaceOnUse">'
                  f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="kf"><rect width="{W}" height="{H}" fill="url(#kfg)"/></mask>')
    s.add(f'<g clip-path="url(#k)"><g mask="url(#kf)">{focus_lines(mx, my, 92, 560, 96, rng)}</g>'
          f'<polygon points="{pts([(96, 0), (128, 0), (150, 96), (118, 96)])}" fill="url(#hatch)" stroke="{INK}" stroke-width="3"/>'
          f'<polygon points="{pts([(184, 0), (152, 0), (130, 96), (162, 96)])}" fill="{RED}" stroke="{INK}" stroke-width="3"/></g>')
    s.add(f'<circle cx="{mx}" cy="{my}" r="64" fill="{BRONZE}"/>',
          f'<g clip-path="url(#disc)">{halftone(mx + 40, my + 42, 80, 7, 3.6, "#6e3c12")}</g>',
          f'<circle cx="{mx}" cy="{my}" r="64" fill="none" stroke="{INK}" stroke-width="5" filter="url(#rough)"/>',
          f'<circle cx="{mx}" cy="{my}" r="49" fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="5 5"/>')
    star = []
    for i in range(10):
        r = 28 if i % 2 == 0 else 12
        a = math.radians(-90 + 36 * i)
        star.append((mx + r * math.cos(a), my + r * math.sin(a)))
    s.add(f'<polygon points="{pts(star)}" fill="{PAPER}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>',
          f'<path d="M{mx - 44},{my - 22} A50,50 0 0 1 {mx - 18},{my - 47}" fill="none" stroke="{PAPER}" stroke-width="5" stroke-linecap="round"/>')

    t, _ = s.tag(270, 40, "KAGGLE  /  COMPETITION BRONZE MEDAL")
    c = cap("display", 48)
    s.add(t, s.text(268, 40 + 27 + 16 + c, "BIOHUB: CELL TRACKING", "display", 48, INK, ls=1),
          s.text(268, 40 + 27 + 16 + 2 * c + 12, "DURING DEVELOPMENT", "display", 48, INK, ls=1),
          s.text(270, 236, "RESEARCH COMPETITION  /  $60,000 PRIZE POOL  /  SEP 2026", "mono", 12, GREY, ls=1.5))
    bx, by = 850, 122
    s.add(f'<polygon points="{pts(burst(bx, by, 70, 100, 20, rng, rx=1.3))}" fill="{PAPER}" stroke="{INK}" '
          f'stroke-width="4" stroke-linejoin="round" filter="url(#rough)"/>',
          s.sfx(bx, by + cap("display", 76) / 2 - 4, "TOP 8%", 76, rot=-6, anchor="middle", shadow=BRONZE))
    t, _ = s.tag(bx, 206, "287TH OF 3,947 TEAMS", 12, anchor="middle")
    s.add(t, f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="none" stroke="{INK}" stroke-width="5" filter="url(#rough)"/>')
    grain(s, W, H)
    s.save("kaggle-bronze.svg")


# ---------------------------------------------------------------- section titles (red tape)

TITLES = [
    ("01", "ABOUT ME", "about"),
    ("02", "FEATURED WORK", "work"),
    ("03", "ACHIEVEMENTS", "achievements"),
    ("04", "OPEN SOURCE", "open-source"),
    ("05", "EXPERIENCE", "experience"),
    ("06", "TOOLKIT", "toolkit"),
    ("07", "STATS", "stats"),
]


def title(num, label, slug):
    W, H = 1000, 76
    s = Svg(W, H, label.title())
    rng = random.Random(num)
    size = 36
    w = 20 + tw("mono", num, 16, 1) + 18 + tw("display", label, size, 2) + 26
    x0, y0, y1 = 12, 14, 62

    def torn(x, sign):
        out, steps = [], 7
        for i in range(steps + 1):
            yy = y0 + (y1 - y0) * i / steps
            out.append((x + sign * (rng.uniform(0, 7) if i % 2 else rng.uniform(-2, 2)), yy))
        return out

    tape = [(x0, y0)] + [(x0 + w, y0)] + torn(x0 + w, 1)[1:-1] + [(x0 + w, y1), (x0, y1)] + torn(x0, -1)[::-1][1:-1]
    s.add(f'<g transform="rotate(-1.2 {x0} {y1})">'
          f'<polygon points="{pts([(x + 5, y + 5) for x, y in tape])}" fill="{INK}" opacity=".18"/>'
          f'<polygon points="{pts(tape)}" fill="{RED}" filter="url(#rough)"/>'
          + s.text(x0 + 20, (y0 + y1) / 2 + cap("mono", 16) / 2, num, "mono", 16, PAPER, ls=1)
          + f'<line x1="{x0 + 20 + tw("mono", num, 16, 1) + 8}" y1="{y0 + 13}" x2="{x0 + 20 + tw("mono", num, 16, 1) + 8}" y2="{y1 - 13}" stroke="{PAPER}" stroke-width="2"/>'
          + s.text(x0 + 20 + tw("mono", num, 16, 1) + 18, (y0 + y1) / 2 + cap("display", size) / 2, label, "display", size, PAPER, ls=2)
          + "</g>")
    s.save(f"titles/{num}-{slug}.svg")


# ---------------------------------------------------------------- footer

def footer():
    W, H = 1200, 170
    s = Svg(W, H, "To be continued")
    label = "TO BE CONTINUED"
    size = 40
    w = tw("display", label, size, 3)
    x1 = W - 60 - 46
    x0 = x1 - w - 56
    top, bot = 50, 120
    mid = (top + bot) / 2
    arrow = [(x0, top), (x1, top), (x1 + 46, mid), (x1, bot), (x0, bot), (x0 + 22, mid)]
    s.css.append(".bob{animation:bob 1.6s ease-in-out infinite}@keyframes bob{50%{transform:translateX(10px)}}"
                 "@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add(f'<g class="bob"><polygon points="{pts([(x + 8, y + 8) for x, y in arrow])}" fill="{RED}"/>'
          f'<polygon points="{pts(arrow)}" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round" filter="url(#rough)"/>'
          + s.text((x0 + 22 + x1) / 2 + 4, mid + cap("display", size) / 2, label, "display", size, INK, "middle", ls=3)
          + "</g>")
    s.add(s.text(48, 104, "thanks for reading!", "hand", 34, RED, attrs=' transform="rotate(-3 48 104)"'))
    s.save("footer.svg")


if __name__ == "__main__":
    header()
    featured()
    medal()
    for t in TITLES:
        title(*t)
    footer()
    print("assets written to", ASSETS)

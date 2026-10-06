"""Text -> SVG path outlines, so GitHub renders the exact typography (no web fonts in <img> SVGs)."""
import math
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.basePen import BasePen

import os

# folder containing @fontsource/instrument-serif and @fontsource-variable/jetbrains-mono
NM = os.environ.get("FONT_NODE_MODULES", "../sivakumar_portfolio_v3/node_modules").rstrip("/") + "/"
IS = NM + "@fontsource/instrument-serif/files/instrument-serif-"
JB = NM + "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-"


def ntos(v):
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


class _Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]


def _chevron(right, x, y, size, adv):
    # custom angle bracket (⟨ ⟩) drawn as a thin filled chevron
    t = 0.055 * size
    top, mid, bot = y - 0.78 * size, y - 0.27 * size, y + 0.24 * size
    a, b = x + 0.12 * size, x + 0.40 * size
    if not right:
        a, b = b, a
        t = -t
    pts = [(a, top), (b, mid), (a, bot), (a + t, bot), (b + t, mid), (a + t, top)]
    return "M" + " L".join(f"{ntos(px)} {ntos(py)}" for px, py in pts) + "Z"


def _arrow(x, y, size, adv):
    t = 0.045 * size
    m = y - 0.3 * size
    x0, x1 = x + 0.08 * size, x + adv - 0.08 * size
    h = 0.17 * size
    return (f"M{ntos(x0)} {ntos(m - t)}H{ntos(x1 - h * 0.9)}V{ntos(m - h)}L{ntos(x1)} {ntos(m)}"
            f"L{ntos(x1 - h * 0.9)} {ntos(m + h)}V{ntos(m + t)}H{ntos(x0)}Z")


def _integral(x, y, size, adv):
    # ∫ as a filled stroke: top hook arc -> slanted stem -> bottom hook arc, thick in the middle
    pts = []
    for i in range(10):  # top hook, from its tip back to the stem
        a = math.radians(-35 + 215 * i / 9)
        pts.append((0.56 + 0.10 * math.cos(a), 0.74 + 0.10 * math.sin(a)))
    for i in range(1, 12):
        t = i / 12
        pts.append((0.46 + (0.30 - 0.46) * t, 0.74 + (-0.06 - 0.74) * t))
    for i in range(10):  # bottom hook
        a = math.radians(0 - 215 * i / 9)
        pts.append((0.20 + 0.10 * math.cos(a), -0.06 + 0.10 * math.sin(a)))
    n = len(pts)
    left, right = [], []
    for i, (px, py) in enumerate(pts):
        ax, ay = pts[max(0, i - 1)]
        bx, by = pts[min(n - 1, i + 1)]
        tx, ty = bx - ax, by - ay
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln, tx / ln
        w = 0.012 + 0.036 * math.sin(math.pi * i / (n - 1)) ** 1.5
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    poly = left + right[::-1]
    return "M" + " L".join(f"{ntos(x + px * size)} {ntos(y - py * size)}" for px, py in poly) + "Z"


CUSTOM = {
    "∫": (0.72, _integral),
    "⟩": (0.52, lambda x, y, s, a: _chevron(True, x, y, s, a)),
    "⟨": (0.52, lambda x, y, s, a: _chevron(False, x, y, s, a)),
    "→": (0.9, _arrow),
}


class Face:
    def __init__(self, paths, tracking=0.0):
        self.fonts = [_Font(p) for p in paths]
        self.tracking = tracking

    def _find(self, ch):
        for f in self.fonts:
            if ord(ch) in f.cmap:
                return f, f.cmap[ord(ch)]
        return None, None

    def glyph(self, ch, size, x, y):
        """returns (path d, advance)"""
        if ch in CUSTOM:
            w, fn = CUSTOM[ch]
            adv = w * size
            return fn(x, y, size, adv), adv + self.tracking * size
        f, name = self._find(ch)
        if f is None:
            raise KeyError(f"glyph missing: {ch!r} U+{ord(ch):04X}")
        k = size / f.upm
        adv = f.hmtx[name][0] * k
        pen = SVGPathPen(f.gs, ntos=ntos)
        f.gs[name].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
        return pen.getCommands(), adv + self.tracking * size

    def width(self, s, size):
        w = 0.0
        for ch in s:
            w += self.glyph(ch, size, 0, 0)[1]
        return w - (self.tracking * size if s else 0)

    def glyphs(self, s, size, x, y, anchor="start"):
        """list of dicts {ch,d,x,adv}"""
        w = self.width(s, size)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        out = []
        for ch in s:
            d, adv = self.glyph(ch, size, x, y)
            out.append(dict(ch=ch, d=d, x=x, adv=adv))
            x += adv
        return out

    def d(self, s, size, x, y, anchor="start"):
        return "".join(g["d"] for g in self.glyphs(s, size, x, y, anchor))

    def path(self, s, size, x, y, anchor="start", attrs=""):
        """Text as <use> refs to glyphs defined once per SVG (see REG/defs())."""
        w = self.width(s, size)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        U = 1000.0
        k = size / U
        out, cx, extra = "", 0.0, ""
        for ch in s:
            if ch in CUSTOM:
                wv, fn = CUSTOM[ch]
                out += f'<path d="{fn(cx, 0, U, wv * U)}"/>'
                cx += wv * U + self.tracking * U
                continue
            f, name = self._find(ch)
            if f is None:
                raise KeyError(f"glyph missing: {ch!r}")
            key = (id(f), name)
            if key not in REG:
                pen = SVGPathPen(f.gs, ntos=lambda v: str(round(v)))
                sc = U / f.upm
                f.gs[name].draw(TransformPen(pen, (sc, 0, 0, -sc, 0, 0)))
                REG[key] = (f"g{len(REG)}", pen.getCommands())
            gid, d = REG[key]
            if d:
                out += f'<use href="#{gid}"' + (f' x="{round(cx)}"' if round(cx) else "") + "/>"
            cx += f.hmtx[name][0] * U / f.upm + self.tracking * U
        return f'<g {attrs}><g transform="translate({ntos(x)} {ntos(y)}) scale({k:.4g})">{out}</g></g>'


REG = {}


def take_defs():
    s = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in REG.values() if d)
    REG.clear()
    return f"<defs>{s}</defs>" if s else ""


SERIF = Face([IS + "latin-400-normal.woff", IS + "latin-ext-400-normal.woff",
              JB + "greek-wght-normal.woff2", JB + "latin-wght-normal.woff2"])
ITALIC = Face([IS + "latin-400-italic.woff", IS + "latin-ext-400-italic.woff",
               JB + "greek-wght-italic.woff2", JB + "latin-wght-italic.woff2"])
MONO = Face([JB + "latin-wght-normal.woff2", JB + "greek-wght-normal.woff2", JB + "latin-ext-wght-normal.woff2"])
EYEBROW = Face([JB + "latin-wght-normal.woff2", JB + "greek-wght-normal.woff2"], tracking=0.08)


class _Flatten(BasePen):
    def __init__(self, gs, steps=24):
        super().__init__(gs)
        self.contours, self.cur, self.steps = [], None, steps

    def _moveTo(self, p):
        self.contours.append([p])

    def _lineTo(self, p):
        self.contours[-1].append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.contours[-1].append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                                      mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.contours[-1].append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                                      mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        pass


def outline_points(face, ch):
    """Polyline contours of a glyph in font units (y up)."""
    f, name = face._find(ch)
    pen = _Flatten(f.gs)
    f.gs[name].draw(pen)
    return pen.contours, f.upm

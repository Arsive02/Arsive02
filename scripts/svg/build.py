"""Generate the animated 'Math Editorial' SVGs for the GitHub profile README.

pip install fonttools brotli
FONT_NODE_MODULES=<path to node_modules with @fontsource fonts> python build.py ../../assets
Every SVG is emitted in a -dark and -light variant (README picks via <picture>).
Animations are CSS keyframes + SMIL only: GitHub serves SVGs as <img>, so no JS / web fonts.
"""
import cmath
import math
import os
import random
import sys

from fonts import SERIF, ITALIC, MONO, EYEBROW, outline_points, ntos, take_defs

PAL = {
    "dark": dict(bg="#0e0d0b", bg2="#161512", fg="#ede8de", muted="#9b958a", acc="#2dd4bf",
                 line="#ede8de", lineop=0.12, gridop=0.045),
    "light": dict(bg="#f2eee6", bg2="#e9e4d9", fg="#16140f", muted="#6b665c", acc="#0f766e",
                  line="#16140f", lineop=0.14, gridop=0.06),
}

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def svg(w, h, body, style="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>'
            f'<style>{style}{REDUCED}</style>{take_defs()}{body}</svg>')


def card(w, h, p, grid=True):
    s = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="{p["bg"]}" '
         f'stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>')
    if grid:
        s += (f'<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
              f'<path d="M40 0H0V40" fill="none" stroke="{p["line"]}" stroke-opacity="{p["gridop"]}"/></pattern>'
              f'<clipPath id="cardclip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17"/></clipPath></defs>'
              f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="url(#grid)"/>')
    return s


def f2(v):
    return ntos(v)


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


# ---------------------------------------------------------------- hero
def hero(p):
    W, H = 1200, 420
    rnd = random.Random(7)
    CYC = 9  # seconds; fast settle (~1.6s), long hold, dissolve, retrain
    SETTLE = 0.18
    b = card(W, H, p)
    b += EYEBROW.path("SENIOR APPLIED AI ENGINEER · RICOH", 13, 56, 66, attrs=f'fill="{p["acc"]}"')
    b += EYEBROW.path("BOULDER, CO · 40.01°N 105.27°W", 13, W - 56, 66, "end", attrs=f'fill="{p["muted"]}"')

    # name: per-glyph SGD-style settle from scattered positions
    first, last = "Sivakumar ", "Ramakrishnan"
    size = 112
    wf, wl = SERIF.width(first, size), ITALIC.width(last, size)
    if wf + wl > 1040:
        size *= 1040 / (wf + wl)
        wf, wl = SERIF.width(first, size), ITALIC.width(last, size)
    x0 = (W - wf - wl) / 2
    base = 228
    gl = [(g, p["fg"]) for g in SERIF.glyphs(first, size, x0, base)]
    gl += [(g, p["acc"]) for g in ITALIC.glyphs(last, size, x0 + wf, base)]
    letters, dots = "", ""
    for i, (g, col) in enumerate(gl):
        if g["ch"] == " ":
            continue
        dx, dy = rnd.uniform(-260, 260), rnd.uniform(-150, 150)
        delay = 0.02 * i
        letters += (f'<g class="L" style="--dx:{f2(dx)}px;--dy:{f2(dy)}px;animation-delay:{f2(delay)}s">'
                    f'<path fill="{col}" d="{g["d"]}"/></g>')
        for _ in range(2):
            tx = g["x"] + rnd.uniform(0.1, 0.9) * g["adv"]
            ty = base - rnd.uniform(0.05, 0.7) * size
            sx, sy = tx + rnd.uniform(-420, 420), ty + rnd.uniform(-170, 170)
            sx, sy = min(max(sx, 20), W - 20), min(max(sy, 90), H - 30)
            dots += (f'<circle class="P" cx="{f2(sx)}" cy="{f2(sy)}" r="{f2(rnd.uniform(1, 2.1))}" fill="{p["acc"]}" '
                     f'style="--tx:{f2(tx - sx)}px;--ty:{f2(ty - sy)}px;animation-delay:{f2(delay + rnd.uniform(0, .15))}s"/>')
    b += f'<g clip-path="url(#cardclip)">{dots}</g>{letters}'

    # readout with ticking epoch / loss
    ry = 292
    pre = "epoch "
    xw = MONO.width("epoch 000/200 · loss 0.0000 · optim SGD · β 0.9 · momentum", 14)
    rx = (W - xw) / 2
    b += MONO.path(pre, 14, rx, ry, attrs=f'fill="{p["muted"]}"')
    xn = rx + MONO.width(pre, 14)
    mid = "/200 · loss "
    xl = xn + MONO.width("000" + mid, 14)
    b += MONO.path(mid, 14, xn + MONO.width("000", 14), ry, attrs=f'fill="{p["muted"]}"')
    b += MONO.path(" · optim SGD · β 0.9 · momentum", 14, xl + MONO.width("0.0000", 14), ry, attrs=f'fill="{p["muted"]}"')
    N = 10
    settle = SETTLE
    for f in range(N + 1):
        ep = f * 20
        loss = 2.3026 * math.exp(-0.42 * f) + 0.0123
        t0 = settle * f / N
        t1 = settle * (f + 1) / N
        if f == 0:
            vals, kt = "1;0;1", f"0;{settle / N:.3f};0.880"
        elif f == N:
            vals, kt = "0;1;0", f"0;{settle:.3f};0.880"
        else:
            vals, kt = "0;1;0", f"0;{t0:.3f};{t1:.3f}"
        anim = f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="{CYC}s" calcMode="discrete" repeatCount="indefinite"/>'
        b += (f'<g opacity="{1 if f == 0 else 0}">{anim}'
              f'{MONO.path(f"{ep:03d}", 14, xn, ry, attrs=chr(32) + "fill=" + chr(34) + p["acc"] + chr(34))}'
              f'{MONO.path(f"{loss:.4f}", 14, xl, ry, attrs="fill=" + chr(34) + p["fg"] + chr(34))}</g>')

    b += ITALIC.path("Decoding chaos into elegant equations.", 34, W / 2, 356, "middle", attrs=f'fill="{p["muted"]}"')

    # mini loss curve (bottom-right) drawn in sync with the settle
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((1030 + 120 * t, 392 - 4 - 36 * math.exp(-4.2 * t) - 3 * math.sin(9 * t) * math.exp(-3 * t)))
    dpath = "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in pts)
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(40))
    b += (f'<path d="M1030 352V392H1150" fill="none" stroke="{p["line"]}" stroke-opacity=".25"/>'
          f'<path class="loss" d="{dpath}" fill="none" stroke="{p["acc"]}" stroke-width="1.6" '
          f'stroke-dasharray="{f2(L)}" style="--L:{f2(L)}"/>')
    b += MONO.path("loss", 11, 1030, 346, attrs=f'fill="{p["muted"]}"')
    # sine favicon motif bottom-left with travelling dot
    sp = "M56 372 " + " ".join(f"L{f2(56 + i * 2)} {f2(372 - 10 * math.sin(i * 2 / 120 * 2 * math.pi))}" for i in range(61))
    b += (f'<path id="sine" d="{sp}" fill="none" stroke="{p["acc"]}" stroke-width="1.6" opacity=".8"/>'
          f'<circle r="3.6" fill="{p["acc"]}"><animateMotion dur="4s" repeatCount="indefinite" calcMode="linear">'
          f'<mpath href="#sine"/></animateMotion></circle>')

    # translate + opacity only (no fill-box rotate/scale): far cheaper to repaint in an <img> SVG
    st = f"""
.L{{animation:settle {CYC}s cubic-bezier(.16,.84,.24,1) infinite both}}
@keyframes settle{{
0%{{transform:translate(var(--dx),var(--dy));opacity:0}}
3%{{opacity:.4}}
13%{{transform:translate(calc(var(--dx)*-.03),calc(var(--dy)*-.03));opacity:1}}
18%{{transform:none;opacity:1}}
88%{{transform:none;opacity:1;animation-timing-function:cubic-bezier(.6,0,.9,.4)}}
100%{{transform:translate(var(--dx),var(--dy));opacity:0}}}}
.P{{animation:fly {CYC}s cubic-bezier(.16,.84,.24,1) infinite both}}
@keyframes fly{{
0%{{transform:none;opacity:0}}
3%{{opacity:.9}}
13%{{transform:translate(var(--tx),var(--ty));opacity:.9}}
18%{{transform:translate(var(--tx),var(--ty));opacity:0}}
90%{{transform:translate(var(--tx),var(--ty));opacity:0;animation-timing-function:cubic-bezier(.6,0,.9,.4)}}
93%{{opacity:.7}}
100%{{transform:none;opacity:0}}}}
.loss{{animation:draw {CYC}s linear infinite both}}
@keyframes draw{{0%{{stroke-dashoffset:var(--L)}}18%,88%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:var(--L)}}}}
"""
    return svg(W, H, b, st, "Sivakumar Ramakrishnan — Senior Applied AI Engineer at Ricoh")


# ---------------------------------------------------------------- ket (superposition line)
def ket(p):
    W, H = 1200, 128
    size = 40
    parts = [("|me⟩ = ", None), ("α|AI engineer⟩", 0), (" + ", None), ("β|musician⟩", 1), (" + ", None),
             ("γ|chess player⟩", 2)]
    total = sum(ITALIC.width(s, size) for s, _ in parts)
    x = (W - total) / 2
    y = 62
    b = ""
    for s, k in parts:
        b += ITALIC.path(s, size, x, y, attrs=f'fill="{p["muted"]}"' if k is None else f'class="t t{k}"')
        x += ITALIC.width(s, size)
    caps = ["measure → |AI engineer⟩  ·  p = |α|²  ·  weekdays",
            "measure → |musician⟩  ·  p = |β|²  ·  venu, 8 holes, bamboo",
            "measure → |chess player⟩  ·  p = |γ|²  ·  1200 → 1400"]
    for k, c in enumerate(caps):
        b += MONO.path(c, 13, W / 2, 106, "middle", attrs=f'class="c c{k}" fill="{p["acc"]}"')
    b += MONO.path("superposition  ·  |α|² + |β|² + |γ|² = 1", 13, W / 2, 106, "middle", attrs=f'class="sp" fill="{p["muted"]}"')
    C = 12
    st = f".t{{fill:{p['fg']};animation:{C}s ease-in-out infinite both}}.c,.sp{{opacity:0;animation:{C}s ease-in-out infinite both}}"
    for k in range(3):
        a0 = k * 100 / 3
        on0, on1 = a0 + 8, a0 + 33.3 - 2
        # caption k visible while term k is the measured state
        st += (f"@keyframes C{k}{{0%,{f2(on0 - 2)}%,{f2(on1 - 1)}%,100%{{opacity:0}}{f2(on0 + 1)}%,{f2(on1 - 4)}%{{opacity:1}}}}"
               f".c{k}{{animation-name:C{k}}}")
    # term k: teal while measured, dimmed while another term is measured
    for k in range(3):
        stops = []
        for j in range(3):
            a0 = j * 100 / 3
            on0, on1 = a0 + 8, a0 + 33.3 - 2
            if j == k:
                stops.append((on0 - 4, p["fg"], 1)); stops.append((on0, p["acc"], 1))
                stops.append((on1 - 3, p["acc"], 1)); stops.append((on1, p["fg"], 1))
            else:
                stops.append((on0 - 4, p["fg"], 1)); stops.append((on0, p["fg"], .16))
                stops.append((on1 - 3, p["fg"], .16)); stops.append((on1, p["fg"], 1))
        kf = f"0%{{fill:{p['fg']};opacity:1}}" + "".join(f"{f2(t)}%{{fill:{c};opacity:{o}}}" for t, c, o in stops) + f"100%{{fill:{p['fg']};opacity:1}}"
        st += f"@keyframes K{k}{{{kf}}}.t{k}{{animation-name:K{k}}}"
    sp_stops = []
    for j in range(3):
        a0 = j * 100 / 3
        sp_stops += [(a0 + 0.5, 1), (a0 + 5, 1), (a0 + 7, 0), (a0 + 30.3, 0), (a0 + 32.5, 1)]
    st += "@keyframes S{0%{opacity:1}" + "".join(f"{f2(t)}%{{opacity:{o}}}" for t, o in sp_stops) + "100%{opacity:1}}.sp{animation-name:S}"
    return svg(W, H, b, st, "|me⟩ = α|AI engineer⟩ + β|musician⟩ + γ|chess player⟩")


# ---------------------------------------------------------------- fourier epicycles
def fourier(p):
    W, H = 460, 520
    contours, upm = outline_points(ITALIC, "S")
    pts = max(contours, key=len)
    # normalise into a 300px box centred at (230, 230), svg y-down
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    s = 300 / max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    pts = [complex(232 + (x - cx) * s, 236 - (y - cy) * s) for x, y in pts]
    pts.append(pts[0])
    # resample by arc length
    seg = [abs(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    Ltot = sum(seg)
    N = 512
    res, acc, j = [], 0.0, 0
    for i in range(N):
        target = Ltot * i / N
        while acc + seg[j] < target:
            acc += seg[j]
            j += 1
        t = (target - acc) / seg[j] if seg[j] else 0
        res.append(pts[j] + (pts[j + 1] - pts[j]) * t)
    coeffs = []
    for k in range(-N // 2, N // 2):
        c = sum(res[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N)) / N
        coeffs.append((k, c))
    c0 = [c for k, c in coeffs if k == 0][0]
    terms = sorted([(k, c) for k, c in coeffs if k != 0], key=lambda kc: -abs(kc[1]))[:48]
    T = 14.0
    # reconstruction for the traced path
    M = 600
    recon = []
    for i in range(M + 1):
        t = i / M
        z = c0 + sum(c * cmath.exp(2j * math.pi * k * t) for k, c in terms)
        recon.append(z)
    rd = "M" + " L".join(f"{f2(z.real)} {f2(z.imag)}" for z in recon)
    RL = sum(abs(recon[i + 1] - recon[i]) for i in range(M))

    b = card(W, H, p)
    b += f'<path d="{rd}" fill="none" stroke="{p["fg"]}" stroke-opacity=".08" stroke-width="10" stroke-linejoin="round"/>'
    # nested rotating arms
    chain = ""
    closers = ""
    prev_k, prev_phase = 0, 0.0
    for idx, (k, c) in enumerate(terms):
        r = abs(c)
        ph = math.degrees(cmath.phase(c))
        rel_k = k - prev_k
        rel_ph = ph - prev_phase
        dur = T / abs(rel_k) if rel_k else 0
        style = (f'animation-duration:{dur:.4f}s;animation-direction:{"normal" if rel_k > 0 else "reverse"}'
                 if rel_k else "animation:none")
        op = max(0.12, 0.5 - idx * 0.015)
        chain += (f'<g transform="rotate({f2(rel_ph)})"><g class="sp" style="{style}">'
                  f'<circle r="{f2(r)}" fill="none" stroke="{p["muted"]}" stroke-opacity="{op:.2f}" stroke-width=".8"/>'
                  f'<line x2="{f2(r)}" stroke="{p["acc"]}" stroke-opacity="{min(.9, op + .3):.2f}" stroke-width="1.1"/>'
                  f'<g transform="translate({f2(r)} 0)">')
        closers += "</g></g></g>"
        prev_k, prev_phase = k, ph
    chain += f'<circle r="4" fill="{p["acc"]}"/>'
    b += f'<path class="tr" d="{rd}" fill="none" stroke="{p["acc"]}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{f2(RL)} {f2(RL)}"/>'
    b += f'<g transform="translate({f2(c0.real)} {f2(c0.imag)})">{chain}{closers}</g>'
    b += f'<line x1="32" y1="436" x2="{W - 32}" y2="436" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'
    eq = "z(t) = Σ c e"
    b += ITALIC.path("z(t) = Σ", 26, 32, 476, attrs=f'fill="{p["fg"]}"')
    x = 32 + ITALIC.width("z(t) = Σ", 26)
    b += ITALIC.path("k", 15, x + 1, 484, attrs=f'fill="{p["muted"]}"')
    x += 14
    b += ITALIC.path(" c", 26, x, 476, attrs=f'fill="{p["fg"]}"')
    x += ITALIC.width(" c", 26)
    b += ITALIC.path("k", 15, x + 1, 484, attrs=f'fill="{p["muted"]}"')
    x += 12
    b += ITALIC.path(" e", 26, x, 476, attrs=f'fill="{p["fg"]}"')
    x += ITALIC.width(" e", 26)
    b += ITALIC.path("2πikt", 15, x + 1, 462, attrs=f'fill="{p["acc"]}"')
    b += EYEBROW.path(f"FIG. 1 · THE AUTHOR'S INITIAL", 10, W - 32, 466, "end", attrs=f'fill="{p["muted"]}"')
    b += EYEBROW.path(f"IN {len(terms)} HARMONICS", 10, W - 32, 482, "end", attrs=f'fill="{p["acc"]}"')
    st = (f".sp{{animation:spin linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}"
          f".tr{{animation:tr {2 * T}s linear infinite}}@keyframes tr{{0%{{stroke-dashoffset:{f2(RL)}}}50%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:{f2(-RL)}}}}}")
    return svg(W, H, b, st, "Fourier epicycles drawing the letter S")


# ---------------------------------------------------------------- bloch sphere experience
ROLES = [  # chronological
    ("2019", "Student Research Lead", "TEAM LMES · AUTONOMOUS GROUND VEHICLE", (118, 205)),
    ("2022", "Data Scientist, R&D", "ZOHO · RAG AT 10K+ QUERIES / DAY", (82, 262)),
    ("2024", "Research Assistant", "CU BOULDER · EDGE DL · DEPTH MAPPING", (58, 335)),
    ("2025", "Applied AI Engineer, Intern", "RICOH · AWS AGENT FOUNDATION", (38, 40)),
    ("2026", "Senior Applied AI Engineer", "RICOH · CLAUDE MULTI-AGENT PLATFORM", (16, 110)),
]


def bloch(p):
    W, H = 1200, 470
    cx, cy, R = 250, 248, 165
    az, el = math.radians(-32), math.radians(16)

    def proj(v):
        x, y, z = v
        X = x * math.cos(az) - y * math.sin(az)
        Y = x * math.sin(az) + y * math.cos(az)
        sy = z * math.cos(el) - Y * math.sin(el)
        depth = Y * math.cos(el) + z * math.sin(el)
        return cx + R * X, cy - R * sy, depth

    def sph(th, ph):
        th, ph = math.radians(th), math.radians(ph)
        return (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))

    def ring(fn, n=120):
        front, back = [], []
        P = [proj(fn(2 * math.pi * i / n)) for i in range(n + 1)]
        d_front = d_back = ""
        for i in range(n):
            a, bq = P[i], P[i + 1]
            seg = f"M{f2(a[0])} {f2(a[1])}L{f2(bq[0])} {f2(bq[1])}"
            if (a[2] + bq[2]) / 2 >= 0:
                d_front += seg
            else:
                d_back += seg
        return d_front, d_back

    b = card(W, H, p)
    stroke = f'fill="none" stroke="{p["fg"]}"'
    b += f'<circle cx="{cx}" cy="{cy}" r="{R}" {stroke} stroke-opacity=".35" stroke-width="1.2"/>'
    for fn in (lambda u: (math.cos(u), math.sin(u), 0), lambda u: (math.cos(u), 0, math.sin(u)),
               lambda u: (0, math.cos(u), math.sin(u))):
        fr, bk = ring(fn)
        b += f'<path d="{fr}" {stroke} stroke-opacity=".28"/><path d="{bk}" {stroke} stroke-opacity=".14" stroke-dasharray="3 5"/>'
    for v in [(0, 0, 1.18), (0, 0, -1.18), (1.25, 0, 0), (0, 1.25, 0)]:
        q = proj(v)
        b += f'<line x1="{cx}" y1="{cy}" x2="{f2(q[0])}" y2="{f2(q[1])}" {stroke} stroke-opacity=".22" stroke-dasharray="2 4"/>'
    top, bot = proj((0, 0, 1)), proj((0, 0, -1))
    b += ITALIC.path("|0⟩", 26, top[0] + 12, top[1] - 10, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path("|1⟩", 26, bot[0] + 12, bot[1] + 26, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path("x", 18, proj((1.32, 0, 0))[0], proj((1.32, 0, 0))[1] + 6, "middle", attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path("y", 18, proj((0, 1.32, 0))[0], proj((0, 1.32, 0))[1] + 6, "middle", attrs=f'fill="{p["muted"]}"')

    # role points
    vecs = [sph(*r[3]) for r in ROLES]
    for i, v in enumerate(vecs):
        q = proj(v)
        b += f'<circle cx="{f2(q[0])}" cy="{f2(q[1])}" r="3.2" fill="{p["fg"]}" fill-opacity="{.75 if q[2] >= 0 else .35}"/>'
        b += MONO.path(str(i + 1), 11, q[0] + 7, q[1] - 6, attrs=f'fill="{p["muted"]}"')

    # timeline: move 1.3s (slerp), hold 2.1s; finally swing home
    move, hold = 1.3, 2.1
    seq = vecs + [vecs[0]]
    frames = []  # (time, vec)
    t = 0.0
    dt = 0.1
    frames.append((0.0, seq[0]))
    for i in range(len(seq) - 1):
        a, c = seq[i], seq[i + 1]
        hold_i = hold * (1.8 if i == len(vecs) - 1 else 1)
        t += hold_i
        frames.append((t, a))
        om = math.acos(max(-1, min(1, sum(x * y for x, y in zip(a, c)))))
        n = int(move / dt)
        for s in range(1, n + 1):
            u = ease(s / n)
            if om < 1e-6:
                v = c
            else:
                k1, k2 = math.sin((1 - u) * om) / math.sin(om), math.sin(u * om) / math.sin(om)
                v = tuple(k1 * x + k2 * y for x, y in zip(a, c))
            frames.append((t + move * s / n, v))
        t += move
    TOT = t
    kt = ";".join(f"{fr[0] / TOT:.4f}" for fr in frames)
    P = [proj(v) for _, v in frames]
    Q = [proj((v[0], v[1], 0)) for _, v in frames]
    xs = ";".join(f2(q[0]) for q in P)
    ys = ";".join(f2(q[1]) for q in P)
    qx = ";".join(f2(q[0]) for q in Q)
    qy = ";".join(f2(q[1]) for q in Q)

    def an(attr, vals):
        return f'<animate attributeName="{attr}" values="{vals}" keyTimes="{kt}" dur="{TOT:.2f}s" repeatCount="indefinite"/>'

    b += (f'<line x1="{f2(P[0][0])}" y1="{f2(P[0][1])}" x2="{f2(Q[0][0])}" y2="{f2(Q[0][1])}" stroke="{p["acc"]}" stroke-opacity=".5" stroke-dasharray="2 3">'
          f'{an("x1", xs)}{an("y1", ys)}{an("x2", qx)}{an("y2", qy)}</line>')
    b += (f'<line x1="{cx}" y1="{cy}" x2="{f2(Q[0][0])}" y2="{f2(Q[0][1])}" stroke="{p["acc"]}" stroke-opacity=".35">'
          f'{an("x2", qx)}{an("y2", qy)}</line>')
    b += (f'<line x1="{cx}" y1="{cy}" x2="{f2(P[0][0])}" y2="{f2(P[0][1])}" stroke="{p["acc"]}" stroke-width="2.6" stroke-linecap="round">'
          f'{an("x2", xs)}{an("y2", ys)}</line>')
    b += (f'<circle cx="{f2(P[0][0])}" cy="{f2(P[0][1])}" r="14" fill="{p["acc"]}" fill-opacity=".18">{an("cx", xs)}{an("cy", ys)}</circle>'
          f'<circle cx="{f2(P[0][0])}" cy="{f2(P[0][1])}" r="6" fill="{p["acc"]}">{an("cx", xs)}{an("cy", ys)}</circle>'
          f'<circle cx="{cx}" cy="{cy}" r="3" fill="{p["fg"]}"/>')

    # equation
    ex, ey = 500, 72
    b += ITALIC.path("|ψ⟩ = a|0⟩ + e", 30, ex, ey, attrs=f'fill="{p["fg"]}"')
    x = ex + ITALIC.width("|ψ⟩ = a|0⟩ + e", 30)
    b += ITALIC.path("iφ", 17, x + 1, ey - 13, attrs=f'fill="{p["acc"]}"')
    b += ITALIC.path(" b|1⟩", 30, x + ITALIC.width("iφ", 17) + 2, ey, attrs=f'fill="{p["fg"]}"')
    b += EYEBROW.path("EACH ROLE IS A POINT ON THE SPHERE", 11, W - 48, ey - 6, "end", attrs=f'fill="{p["muted"]}"')
    b += f'<line x1="{ex}" y1="{ey + 22}" x2="{W - 48}" y2="{ey + 22}" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'

    # role rows (newest first), highlight synced with the arrow
    hold_starts = []
    t = 0.0
    for i in range(len(vecs)):
        hold_i = hold * (1.8 if i == len(vecs) - 1 else 1)
        hold_starts.append((t, t + hold_i))
        t += hold_i + move
    y0 = 138
    rowh = 66
    for row, i in enumerate(reversed(range(len(ROLES)))):
        yr, title, org, _ = ROLES[i]
        y = y0 + row * rowh
        a, c = hold_starts[i]
        a0, c0 = max(0, a - 0.25) / TOT, min(TOT, c + 0.25) / TOT
        if i == 0:
            vals, kts = "1;1;.32;.32;1", f"0;{c0:.4f};{min(.999, c0 + .02):.4f};{max(0, (TOT - .3) / TOT):.4f};1"
        else:
            vals, kts = ".32;.32;1;1;.32;.32", f"0;{a0:.4f};{min(1, a0 + .02):.4f};{c0:.4f};{min(1, c0 + .02):.4f};1"
        anim = f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{TOT:.2f}s" repeatCount="indefinite"/>'
        b += (f'<g opacity="{1 if i == 0 else .32}">{anim}'
              f'<rect x="{ex}" y="{y - 30}" width="3" height="40" rx="1.5" fill="{p["acc"]}"/>'
              f'{MONO.path(yr, 14, ex + 18, y - 12, attrs=chr(32) + "fill=" + chr(34) + p["acc"] + chr(34))}'
              f'{SERIF.path(title, 30, ex + 76, y - 4, attrs="fill=" + chr(34) + p["fg"] + chr(34))}'
              f'{EYEBROW.path(org, 10.5, ex + 76, y + 14, attrs="fill=" + chr(34) + p["muted"] + chr(34))}</g>')
        b += MONO.path(str(i + 1), 11, W - 48, y - 8, "end", attrs=f'fill="{p["muted"]}"')
    return svg(W, H, b, "", "Experience timeline on a Bloch sphere")


# ---------------------------------------------------------------- attention matrix skills
TOK = ["Claude", "agents", "RAG", "vLLM", "PyTorch", "Ray", "AWS", "SQL", "vision", "qubits"]
AFF = {("Claude", "agents"): 2.7, ("agents", "RAG"): 2.2, ("RAG", "vLLM"): 2.5, ("vLLM", "PyTorch"): 2.0,
       ("PyTorch", "vision"): 2.4, ("Ray", "AWS"): 1.9, ("Ray", "vLLM"): 1.7, ("AWS", "SQL"): 2.1,
       ("agents", "AWS"): 1.8, ("qubits", "PyTorch"): 1.2, ("Claude", "RAG"): 1.6, ("SQL", "agents"): 1.4,
       ("vision", "qubits"): 0.9, ("Ray", "PyTorch"): 1.5, ("Claude", "SQL"): 1.1}


def attention(p):
    W, H = 1200, 590
    n = len(TOK)
    rnd = random.Random(3)
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                S[i][j] = 3.0
            else:
                S[i][j] = AFF.get((TOK[i], TOK[j]), AFF.get((TOK[j], TOK[i]), 0.0)) + rnd.uniform(-.25, .25)
    taus = [4.0, 2.0, 1.0, 0.5, 0.25, 0.12, 0.08]

    def soft(row, tau):
        m = max(row)
        e = [math.exp((v - m) / tau) for v in row]
        s = sum(e)
        return [v / s for v in e]

    A = {tau: [soft(S[i], tau) for i in range(n)] for tau in taus}
    # timeline: hold at each tau, yoyo
    seq = taus + taus[-2:0:-1]
    seg = 1.0
    holdf = 0.55
    TOT = seg * len(seq)
    kts, idxs = [], []
    for k, tau in enumerate(seq):
        kts += [k * seg / TOT, (k * seg + seg * holdf) / TOT]
        idxs += [tau, tau]
    kts.append(1.0)
    idxs.append(seq[0])
    kt = ";".join(f"{v:.4f}" for v in kts)

    cell, gx, gy = 36, 150, 150
    b = card(W, H, p)
    # column labels (rotated)
    for j, t in enumerate(TOK):
        x = gx + j * cell + cell / 2 + 4
        b += f'<g transform="translate({f2(x)} {gy - 10}) rotate(-50)">{MONO.path(t, 12, 0, 0, attrs="fill=" + chr(34) + p["muted"] + chr(34))}</g>'
    for i, t in enumerate(TOK):
        b += MONO.path(t, 12, gx - 12, gy + i * cell + cell / 2 + 4, "end", attrs=f'fill="{p["muted"]}"')
    for i in range(n):
        for j in range(n):
            vals = ";".join(f"{min(1, A[tau][i][j] ** .7 * 1.15):.3f}" for tau in idxs)
            b += (f'<rect x="{gx + j * cell + 1.5}" y="{gy + i * cell + 1.5}" width="{cell - 3}" height="{cell - 3}" rx="4" '
                  f'fill="{p["acc"]}" fill-opacity="{min(1, A[taus[0]][i][j] ** .7 * 1.15):.3f}">'
                  f'<animate attributeName="fill-opacity" values="{vals}" keyTimes="{kt}" dur="{TOT}s" repeatCount="indefinite"/></rect>')
    b += f'<rect x="{gx}" y="{gy}" width="{n * cell}" height="{n * cell}" rx="6" fill="none" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'
    # sweeping query row
    rows = ";".join(str(gy + (k % n) * cell) for k in range(n + 1))
    b += (f'<rect x="{gx - 3}" y="{gy}" width="{n * cell + 6}" height="{cell}" rx="6" fill="none" stroke="{p["fg"]}" stroke-opacity=".55" stroke-width="1.2">'
          f'<animate attributeName="y" values="{rows}" dur="{n * 1.4}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # tau readout (discrete frames)
    tx, ty = gx, gy + n * cell + 50
    b += ITALIC.path("τ = ", 30, tx, ty, attrs=f'fill="{p["muted"]}"')
    vx = tx + ITALIC.width("τ = ", 30)
    for tau in taus:
        on = [k for k, tt in enumerate(seq) if tt == tau]
        vals, kk = [], []
        for k in range(len(seq)):
            vals.append("1" if k in on else "0")
            kk.append(f"{k * seg / TOT:.4f}")
        b += (f'<g opacity="{1 if tau == seq[0] else 0}"><animate attributeName="opacity" values="{";".join(vals)}" keyTimes="{";".join(kk)}" '
              f'dur="{TOT}s" calcMode="discrete" repeatCount="indefinite"/>{MONO.path(f"{tau:.2f}", 28, vx, ty, attrs="fill=" + chr(34) + p["acc"] + chr(34))}</g>')
    b += EYEBROW.path("ANNEALING  4 → 0.08", 11, gx + n * cell, ty - 6, "end", attrs=f'fill="{p["muted"]}"')

    # equation (right)
    ex, ey = 610, 150
    b += ITALIC.path("α", 40, ex, ey + 14, attrs=f'fill="{p["fg"]}"')
    b += ITALIC.path("ij", 20, ex + 25, ey + 22, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path("=", 36, ex + 56, ey + 12, attrs=f'fill="{p["fg"]}"')
    fx = ex + 92
    num = "exp(s  / τ)"
    b += ITALIC.path("exp(s", 30, fx + 40, ey - 6, attrs=f'fill="{p["fg"]}"')
    w1 = ITALIC.width("exp(s", 30)
    b += ITALIC.path("ij", 16, fx + 40 + w1, ey, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path(" / τ)", 30, fx + 40 + w1 + 12, ey - 6, attrs=f'fill="{p["fg"]}"')
    b += f'<line x1="{fx}" y1="{ey + 6}" x2="{fx + 250}" y2="{ey + 6}" stroke="{p["fg"]}" stroke-width="1.4"/>'
    b += ITALIC.path("Σ", 30, fx, ey + 40, attrs=f'fill="{p["fg"]}"')
    wk = ITALIC.width("Σ", 30)
    b += ITALIC.path("k", 16, fx + wk, ey + 47, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path(" exp(s", 30, fx + wk + 10, ey + 40, attrs=f'fill="{p["fg"]}"')
    w2 = ITALIC.width(" exp(s", 30)
    b += ITALIC.path("ik", 16, fx + wk + 10 + w2, ey + 46, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path(" / τ)", 30, fx + wk + 10 + w2 + 14, ey + 40, attrs=f'fill="{p["fg"]}"')

    groups = [
        ("AI & ML", ["Deep Learning · NLP · Computer Vision · Multimodal", "RAG · Agentic AI · Multi-agent · LLM eval · RLHF"]),
        ("QUANTUM", ["Qubits · Quantum algorithms"]),
        ("LANGUAGES", ["Python · SQL · Java · JavaScript · R"]),
        ("TOOLS", ["PyTorch · TensorFlow · vLLM · Hugging Face · Ray", "AWS · FastAPI · PostgreSQL · Docker · Claude Code"]),
    ]
    y = ey + 112
    b += f'<line x1="{ex}" y1="{y - 30}" x2="{W - 56}" y2="{y - 30}" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'
    for g, lines in groups:
        b += EYEBROW.path(g, 11, ex, y, attrs=f'fill="{p["acc"]}"')
        for ln in lines:
            b += MONO.path(ln, 14, ex + 118, y, attrs=f'fill="{p["fg"]}"')
            y += 24
        y += 12
    return svg(W, H, b, "", "Skills as a self-attention matrix with annealed temperature")


# ---------------------------------------------------------------- marquee
ROW1 = ["Claude", "Claude Code", "Multi-agent", "Tool calling", "RAG", "vLLM", "LLM eval", "RLHF · DPO", "PyTorch",
        "TensorFlow", "JAX", "Hugging Face", "Transformers", "Mamba SSM", "CLIP", "Whisper", "PaliGemma"]
ROW2 = ["Python", "SQL", "Java", "JavaScript", "React", "R", "AWS Lambda", "DynamoDB", "S3", "Aurora", "Ray", "PySpark",
        "FastAPI", "PostgreSQL", "Docker", "Git", "Qubits", "Streamlit"]


def marquee(p):
    W, H = 1200, 100
    b = (f'<defs><linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
         f'</linearGradient><mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs><g mask="url(#m)">')
    st = ""
    for r, (items, y, cls) in enumerate([(ROW1, 8, "a"), (ROW2, 56, "b")]):
        chips, x = "", 0.0
        for it in items:
            w = MONO.width(it, 14) + 32
            chips += (f'<rect x="{f2(x)}" y="{y}" width="{f2(w)}" height="34" rx="17" fill="{p["bg2"]}" fill-opacity=".55" '
                      f'stroke="{p["line"]}" stroke-opacity="{p["lineop"] + .06}"/>'
                      f'<circle cx="{f2(x + 16)}" cy="{y + 17}" r="2.5" fill="{p["acc"]}"/>')
            chips += MONO.path(it, 14, x + 26, y + 22, attrs=f'fill="{p["fg"]}"')
            x += w + 12
        Wc = x
        b += f'<g class="{cls}"><g>{chips}</g><g transform="translate({f2(Wc)} 0)">{chips}</g></g>'
        dur = Wc / 38
        st += (f".{cls}{{animation:{cls} {dur:.1f}s linear infinite}}"
               f"@keyframes {cls}{{from{{transform:translateX({0 if r == 0 else f2(-Wc)}px)}}to{{transform:translateX({f2(-Wc) if r == 0 else 0}px)}}}}")
    b += "</g>"
    return svg(W, H, b, st, "Tech stack marquee")


# ---------------------------------------------------------------- divider
def divider(p):
    W, H = 1200, 30
    lam = 150
    pts = " ".join(f"L{f2(i * 3)} {f2(15 - 5 * math.sin(2 * math.pi * i * 3 / lam))}" for i in range(int((W + lam) / 3) + 2))
    b = (f'<defs><linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>'
         f'<g mask="url(#m)"><path class="w" d="M0 15 {pts}" fill="none" stroke="{p["acc"]}" stroke-width="1.4" stroke-opacity=".75"/>'
         f'<line x1="0" y1="15" x2="{W}" y2="15" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/></g>'
         f'<circle cx="{W / 2}" cy="15" r="3.5" fill="{p["acc"]}"><animate attributeName="cy" values="15;10;15;20;15" dur="3s" repeatCount="indefinite"/></circle>')
    st = f".w{{animation:w 3s linear infinite}}@keyframes w{{to{{transform:translateX(-{lam}px)}}}}"
    return svg(W, H, b, st, "")


# ---------------------------------------------------------------- headings
HEADINGS = {
    "01": ("01 / ABOUT", [("I like the math ", 0), ("underneath", 1), (" the model.", 0)]),
    "02": ("02 / SELECTED WORK", [("Everything connects back to ", 0), ("math", 1), (".", 0)]),
    "03": ("03 / EXPERIENCE", [("A walk on the ", 0), ("Bloch", 1), (" sphere.", 0)]),
    "04": ("04 / SKILLS", [("What attends to ", 0), ("what", 1), ("?", 0)]),
    "05": ("05 / HONOURS", [("Relaxed into ", 0), ("place", 1), (".", 0)]),
    "06": ("06 / ACTIVITY", [("Commits, ", 0), ("integrated", 1), (" over time.", 0)]),
}


def heading(p, key):
    W, H = 1200, 132
    brow, parts = HEADINGS[key]
    num, label = brow.split(" / ")
    b = EYEBROW.path(num, 13, 4, 30, attrs=f'fill="{p["acc"]}"')
    xw = 4 + EYEBROW.width(num + " ", 13)
    b += EYEBROW.path("/ " + label, 13, xw, 30, attrs=f'fill="{p["muted"]}"')
    lx = xw + EYEBROW.width("/ " + label, 13) + 18
    b += f'<line class="hl" x1="{f2(lx)}" y1="25" x2="{W}" y2="25" stroke="{p["line"]}" stroke-opacity="{p["lineop"] + .06}"/>'
    x, size, y = 4, 62, 104
    words = ""
    for i, (s, it) in enumerate(parts):
        face = ITALIC if it else SERIF
        words += face.path(s, size, x, y, attrs=f'class="h" style="animation-delay:{.15 + i * .18:.2f}s" fill="{p["acc"] if it else p["fg"]}"')
        x += face.width(s, size)
    b += words
    st = (".h{opacity:0;animation:rise 1.1s cubic-bezier(.16,.84,.24,1) forwards}"
          "@keyframes rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}"
          ".hl{transform-box:fill-box;transform-origin:left;animation:grow 1.6s cubic-bezier(.16,.84,.24,1) both}"
          "@keyframes grow{from{transform:scaleX(0)}}"
          "@media (prefers-reduced-motion: reduce){.h{opacity:1}}")
    title = "".join(s for s, _ in parts)
    return svg(W, H, b, st, f"{brow.title()} — {title}")


# ---------------------------------------------------------------- contact / möbius footer
def contact(p):
    W, H = 1200, 420
    cx, cy, sc = 900, 200, 150
    FR, T = 30, 24.0

    def mob(u, v):
        r = 1 + v / 2 * math.cos(u / 2)
        return r * math.cos(u), r * math.sin(u), v / 2 * math.sin(u / 2)

    def frame(a):
        tilt = math.radians(-22)

        def pr(q):
            x, y, z = q
            x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
            return cx + sc * x, cy - sc * z * 1.0 + 0 * y

        rul = ""
        for i in range(40):
            u = 2 * math.pi * i / 40
            a1, a2 = pr(mob(u, -1)), pr(mob(u, 1))
            rul += f"M{a1[0]:.0f} {a1[1]:.0f}L{a2[0]:.0f} {a2[1]:.0f}"
        edge = ""
        for i in range(121):
            u = 4 * math.pi * i / 120
            q = pr(mob(u, 1))
            edge += f"{'M' if i == 0 else 'L'}{q[0]:.0f} {q[1]:.0f}"
        mid = ""
        for i in range(81):
            u = 2 * math.pi * i / 80
            q = pr(mob(u, 0))
            mid += f"{'M' if i == 0 else 'L'}{q[0]:.0f} {q[1]:.0f}"
        return rul, edge, mid

    fs = [frame(2 * math.pi * k / FR) for k in range(FR + 1)]
    b = card(W, H, p)

    def anim(idx):
        return f'<animate attributeName="d" values="{";".join(f[idx] for f in fs)}" dur="{T}s" repeatCount="indefinite"/>'

    b += f'<path d="{fs[0][0]}" fill="none" stroke="{p["fg"]}" stroke-opacity=".22" stroke-width="1">{anim(0)}</path>'
    b += f'<path d="{fs[0][2]}" fill="none" stroke="{p["fg"]}" stroke-opacity=".18" stroke-dasharray="2 4">{anim(2)}</path>'
    b += f'<path d="{fs[0][1]}" fill="none" stroke="{p["acc"]}" stroke-width="2" stroke-linejoin="round">{anim(1)}</path>'

    b += EYEBROW.path("07", 13, 64, 84, attrs=f'fill="{p["acc"]}"')
    b += EYEBROW.path("/ CONTACT", 13, 64 + EYEBROW.width("07 ", 13), 84, attrs=f'fill="{p["muted"]}"')
    b += SERIF.path("Let's build something", 60, 64, 168, attrs=f'fill="{p["fg"]}"')
    b += ITALIC.path("non-trivial.", 60, 64, 236, attrs=f'fill="{p["acc"]}"')
    b += ITALIC.path("One-sided surface, two-sided conversation.", 24, 64, 290, attrs=f'fill="{p["muted"]}"')
    b += f'<line x1="64" y1="322" x2="560" y2="322" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'
    b += MONO.path("sivakumar2ramakrishnan@gmail.com", 14, 64, 354, attrs=f'fill="{p["fg"]}"')
    b += EYEBROW.path("BOULDER, COLORADO · OPEN TO INTERESTING PROBLEMS", 10.5, 64, 380, attrs=f'fill="{p["muted"]}"')
    b += MONO.path("r(u,v) = ((1 + v/2·cos u/2)·cos u, (1 + v/2·cos u/2)·sin u, v/2·sin u/2)", 11, cx, 392, "middle",
                   attrs=f'fill="{p["muted"]}"')
    return svg(W, H, b, "", "Let's build something non-trivial — contact")


def main(out):
    os.makedirs(out, exist_ok=True)
    jobs = {"hero": hero, "ket": ket, "fourier": fourier, "bloch": bloch, "attention": attention,
            "marquee": marquee, "divider": divider, "contact": contact}
    for theme, p in PAL.items():
        for name, fn in jobs.items():
            open(os.path.join(out, f"{name}-{theme}.svg"), "w", encoding="utf-8").write(fn(p))
        for k in HEADINGS:
            open(os.path.join(out, f"h{k}-{theme}.svg"), "w", encoding="utf-8").write(heading(p, k))
    for fn in sorted(os.listdir(out)):
        print(f"{os.path.getsize(os.path.join(out, fn)) / 1024:7.1f} KB  {fn}")


if __name__ == "__main__":
    main(sys.argv[1])

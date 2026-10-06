"""All-time contribution activity as a Riemann sum: monthly bars c(t), the running integral ∫c dt, and a Fourier low-pass ĉ(t).

python activity.py <github_user> <out_dir>
Uses GraphQL when GITHUB_TOKEN is set (CI), otherwise the public contributions page.
Writes activity-dark.svg and activity-light.svg (same palette/typography as ../svg).
"""
import cmath
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "svg"))
from fonts import SERIF, ITALIC, MONO, EYEBROW  # noqa: E402
from build import PAL, svg, card, f2  # noqa: E402

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){createdAt
contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def _gql(tok, user, frm, to):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {
                                     "login": user, "from": f"{frm}T00:00:00Z", "to": f"{to}T23:59:59Z"}}).encode(),
                                 headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    return u["createdAt"], [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]


def _scrape(user, frm, to):
    html = urllib.request.urlopen(f"https://github.com/users/{user}/contributions?from={frm}&to={to}").read().decode()
    ids = {cid: d for d, cid in re.findall(r'data-date="([\d-]+)" id="([^"]+)"', html)}
    out = []
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        if cid in ids:
            m = re.match(r"([\d,]+) contribution", text)
            out.append((ids[cid], int(m.group(1).replace(",", "")) if m else 0))
    return out


def fetch(user):
    """Daily contributions from account creation to today."""
    tok = os.environ.get("GITHUB_TOKEN")
    today = dt.date.today()
    if tok:
        created = _gql(tok, user, today, today)[0]
    else:
        created = json.load(urllib.request.urlopen(f"https://api.github.com/users/{user}"))["created_at"]
    start = dt.date.fromisoformat(created[:10])
    days = {}
    for y in range(start.year, today.year + 1):
        frm, to = dt.date(y, 1, 1), min(dt.date(y, 12, 31), today)
        rows = _gql(tok, user, frm, to)[1] if tok else _scrape(user, frm, to)
        for d, c in rows:
            d = dt.date.fromisoformat(d)
            if start <= d <= today:
                days[d] = c
    return sorted(days.items())


def stats(days):
    counts = [c for _, c in days]
    longest = cur = 0
    for c in counts:
        cur = cur + 1 if c else 0
        longest = max(longest, cur)
    current = 0
    for c in reversed(counts):
        if c == 0:
            if current == 0 and days[-1][0] == dt.date.today():
                continue  # today not over yet
            break
        current += 1
    return longest, current


def activity(p, days):
    W, H = 1200, 480
    CYC = 12.0
    D0, D1 = 0.03, 0.42  # draw window (fraction of cycle)
    buckets = {}
    for d, c in days:
        buckets.setdefault((d.year, d.month), []).append((d, c))
    weeks = list(buckets.values())  # one bar per month
    wk = [sum(c for _, c in w) for w in weeks]
    n = len(wk)
    total = sum(wk)
    peak = max(max(wk), 1)
    mean = total / n
    longest, current = stats(days)

    x0, x1, yb, yt = 84, 1140, 392, 136
    bw = (x1 - x0) / n
    hb = yb - yt - 40  # bars use the lower part; integral uses full height

    b = card(W, H, p)
    b += EYEBROW.path(f"c(t) · CONTRIBUTIONS PER MONTH · SINCE {days[0][0].year}", 12, 56, 62, attrs=f'fill="{p["muted"]}"')
    b += EYEBROW.path("RIEMANN SUM → INTEGRAL", 12, 56, 84, attrs=f'fill="{p["acc"]}"')

    # headline integral, right aligned
    val = f"{total:,}"
    sz = 40
    rhs = f" c(τ) dτ = "
    wv = MONO.width(val, 36)
    wr = ITALIC.width(rhs, sz)
    wi = ITALIC.width("∫", sz * 1.5)
    xr = W - 56 - wv
    xs = xr - wr
    xi = xs - wi - 10
    b += ITALIC.path("∫", sz * 1.5, xi, 88, attrs=f'fill="{p["fg"]}"')
    b += ITALIC.path("t", 18, xi + wi - 2, 42, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path("0", 18, xi - 4, 108, attrs=f'fill="{p["muted"]}"')
    b += ITALIC.path(rhs, sz, xs, 82, attrs=f'fill="{p["fg"]}"')
    b += MONO.path(val, 36, xr, 82, attrs=f'fill="{p["acc"]}"')

    # axes + gridlines
    for k in range(5):
        y = yb - (yb - yt) * k / 4
        b += f'<line x1="{x0}" y1="{f2(y)}" x2="{x1}" y2="{f2(y)}" stroke="{p["line"]}" stroke-opacity="{p["lineop"] * (1 if k == 0 else .5)}"/>'
    b += MONO.path(str(peak), 11, x0 - 10, yb - hb + 4, "end", attrs=f'fill="{p["muted"]}"')
    b += MONO.path("0", 11, x0 - 10, yb + 4, "end", attrs=f'fill="{p["muted"]}"')
    b += MONO.path(f"{total:,}", 11, x1 + 8, yt + 4, attrs=f'fill="{p["acc"]}"')

    # month labels
    last = None
    for i, w in enumerate(weeks):
        y = w[0][0].year
        if y != last:
            b += f'<line x1="{f2(x0 + i * bw)}" y1="{yb}" x2="{f2(x0 + i * bw)}" y2="{yb + 6}" stroke="{p["muted"]}"/>'
            b += MONO.path(str(y), 11, x0 + i * bw + 4, yb + 22, attrs=f'fill="{p["muted"]}"')
        last = y

    # Riemann bars (SMIL height/y so no per-frame transform-box work)
    bars = ""
    for i, c in enumerate(wk):
        h = max(c / peak * hb, 0 if c == 0 else 2)
        x = x0 + i * bw + 2
        a = D0 + (D1 - D0) * i / n
        e = min(a + 0.05, D1 + 0.04)
        kt = f"0;{a:.4f};{e:.4f};0.9;0.96;1"
        bars += (f'<rect x="{f2(x)}" y="{yb}" width="{f2(bw - 4)}" height="0" rx="2" fill="{p["acc"]}" fill-opacity=".26">'
                 f'<animate attributeName="height" values="0;0;{f2(h)};{f2(h)};0;0" keyTimes="{kt}" dur="{CYC}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{yb};{yb};{f2(yb - h)};{f2(yb - h)};{yb};{yb}" keyTimes="{kt}" dur="{CYC}s" repeatCount="indefinite"/></rect>')
    b += bars

    # Fourier low-pass of the monthly signal
    sig = wk
    N = n
    K = max(4, n // 6)
    coef = [(k, sum(sig[t] * cmath.exp(-2j * math.pi * k * t / N) for t in range(N)) / N) for k in range(K + 1)]
    pts = []
    for s_ in range(301):
        t = s_ / 300 * (N - 1)
        v = coef[0][1].real + sum(2 * (c * cmath.exp(2j * math.pi * k * t / N)).real for k, c in coef[1:])
        pts.append((x0 + (t + 0.5) / N * (x1 - x0), yb - min(max(v, 0.0) / peak, 1.15) * hb))
    sd = "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in pts)
    b += f'<path class="lp" d="{sd}" fill="none" stroke="{p["fg"]}" stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="5 5"/>'
    lx, ly = pts[int(len(pts) * 0.62)]
    b += MONO.path(f"ĉ(t) · {K} harmonics", 13, lx + 8, ly - 12, attrs=f'class="lp" fill="{p["muted"]}"')

    # running integral F(t)
    cum, acc = [(x0, yb)], 0
    for i, c in enumerate(wk):
        acc += c
        cum.append((x0 + (i + 1) * bw, yb - (acc / max(total, 1)) * (yb - yt)))
    fd = "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in cum)
    L = sum(math.dist(cum[i], cum[i + 1]) for i in range(len(cum) - 1))
    b += (f'<path id="F" class="F" d="{fd}" fill="none" stroke="{p["acc"]}" stroke-width="2.6" stroke-linejoin="round" '
          f'stroke-linecap="round" stroke-dasharray="{f2(L)}" stroke-dashoffset="{f2(L)}"/>')
    b += ITALIC.path("F(t) = ∫ c", 22, x0 + 14, yt + 6, attrs=f'class="Fl" fill="{p["acc"]}"')
    sweep = f'keyTimes="0;{D0};{D1};1" dur="{CYC}s" repeatCount="indefinite"'
    b += (f'<line y1="{yt - 10}" y2="{yb}" stroke="{p["fg"]}" stroke-opacity=".35" stroke-dasharray="2 4" class="sw">'
          f'<animate attributeName="x1" values="{x0};{x0};{x1};{x1}" {sweep}/>'
          f'<animate attributeName="x2" values="{x0};{x0};{x1};{x1}" {sweep}/></line>')
    b += (f'<g class="tip"><circle r="12" fill="{p["acc"]}" fill-opacity=".18"/><circle r="5" fill="{p["acc"]}"/>'
          f'<animateMotion keyPoints="0;0;1;1" keyTimes="0;{D0};{D1};1" calcMode="linear" dur="{CYC}s" repeatCount="indefinite">'
          f'<mpath href="#F"/></animateMotion></g>')

    # stats row
    srow = (f"Σ = {total:,}   ·   max c = {peak} / mo   ·   μ = {mean:.1f} / mo   ·   "
            f"longest streak {longest} d   ·   current {current} d")
    b += f'<line x1="56" y1="424" x2="{W - 56}" y2="424" stroke="{p["line"]}" stroke-opacity="{p["lineop"]}"/>'
    b += MONO.path(srow, 13, 56, 452, attrs=f'fill="{p["fg"]}"')
    b += EYEBROW.path(f"UPDATED {days[-1][0].isoformat()}", 10, W - 56, 452, "end", attrs=f'fill="{p["muted"]}"')

    p0, p1 = D0 * 100, D1 * 100
    st = (f".F{{animation:F {CYC}s linear infinite}}"
          f"@keyframes F{{0%,{p0}%{{stroke-dashoffset:{f2(L)};opacity:1}}{p1}%,90%{{stroke-dashoffset:0;opacity:1}}"
          f"96%{{stroke-dashoffset:0;opacity:0}}100%{{stroke-dashoffset:{f2(L)};opacity:0}}}}"
          f".tip,.sw,.Fl{{animation:tip {CYC}s linear infinite}}"
          f"@keyframes tip{{0%,{p0 - 1}%{{opacity:0}}{p0 + 1}%,90%{{opacity:1}}96%,100%{{opacity:0}}}}"
          f".lp{{animation:lp {CYC}s ease infinite}}"
          f"@keyframes lp{{0%,{p1 + 2}%{{opacity:0}}{p1 + 10}%,88%{{opacity:1}}95%,100%{{opacity:0}}}}"
          "@media (prefers-reduced-motion: reduce){.F{stroke-dashoffset:0}.lp,.tip,.Fl{opacity:1}}")
    return svg(W, H, b, st, f"{total:,} contributions since account creation, drawn as a Riemann sum and its integral")


def main(user, out):
    days = fetch(user)
    os.makedirs(out, exist_ok=True)
    for theme, p in PAL.items():
        with open(os.path.join(out, f"activity-{theme}.svg"), "w", encoding="utf-8") as fh:
            fh.write(activity(p, days))
    print(f"{len(days)} days, {sum(c for _, c in days)} contributions -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

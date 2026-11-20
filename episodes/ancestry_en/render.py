"""Scenes + frame renderer for "What if every human is related?" (1080x1920, 30 fps).

usage:
  python -m episodes.ancestry_en.render stills 3.0 12.5 ...   # PNG stills to build/ancestry_en/stills
  python -m episodes.ancestry_en.render video                  # full silent render (4 workers)
"""
import math
import os
import random
import subprocess
import sys

import cairo
import numpy as np

from cinecode.core import (back_out, circle, clamp, ease_io, ease_out, hexc, kf, lerp, prog, rgrad, rrect, smooth,
                           src, vgrad)
from episodes.ancestry_en import people as P
from episodes.ancestry_en import ui
from episodes.ancestry_en.geo import AfricaMap, FlatMap, Globe
from episodes.ancestry_en.script import CAPTION, LINES
from episodes.ancestry_en.ui import CORAL, CYAN, PINK, BLUE, WHITE, YELLOW

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "ancestry_en")
W, H, FPS = 1080, 1920, 30

TIMING = ui.load_timing(BUILD)
DUR = TIMING["duration"]
TL = TIMING["lines"]


def S(l):
    return TL[l]["start"]


def E(l):
    return TL[l]["end"]


CAPS = ui.Captions(TL, CAPTION, [l for l, _, _ in LINES])


def word_t(line_id, word):
    """Time the first caption word containing `word` appears in a line."""
    for t0, t1, words, end in CAPS.chunks:
        if not (S(line_id) - 0.2 <= t0 <= E(line_id)):
            continue
        for w, _, tw in words:
            if word.lower() in w.lower():
                return tw
    raise KeyError((line_id, word))


# ------------------------------------------------------------------ shared assets (lazy, per process)
_A = {}


def asset(name):
    if name not in _A:
        _A[name] = {"globe": Globe, "africa": AfricaMap, "flat": FlatMap}[name]()
    return _A[name]


RNG = random.Random(11)
STARS = [(RNG.uniform(0, W), RNG.uniform(0, H), RNG.choice([1.0, 1.3, 1.8, 2.4]), RNG.uniform(0, 6.28)) for _ in range(260)]
SPARKS = [(RNG.uniform(0, W), RNG.uniform(380, H), RNG.uniform(0, 6.28)) for _ in range(9)]


def fmt(n):
    return f"{int(round(n)):,}"


# ------------------------------------------------------------------ backgrounds
def bg_space(cx, t):
    cx.set_source(rgrad(cx, W / 2, H * 0.47, 50, H * 0.75, [(0, hexc("#14254F")), (0.6, hexc("#0A1532")), (1, hexc("#050A1C"))]))
    cx.paint()
    for x, y, r, ph in STARS:
        a = 0.35 + 0.35 * math.sin(t * 1.3 + ph)
        cx.rectangle(x, y, r, r)
        src(cx, (1, 1, 1, a))
        cx.fill()
    for x, y, ph in SPARKS:
        a = 0.3 + 0.3 * math.sin(t * 0.9 + ph)
        src(cx, (1, 1, 1, a))
        cx.set_line_width(1.6)
        cx.move_to(x - 7, y)
        cx.line_to(x + 7, y)
        cx.move_to(x, y - 7)
        cx.line_to(x, y + 7)
        cx.stroke()
    _header_band(cx, (0.02, 0.04, 0.10, 0.55))


def _header_band(cx, c):
    cx.set_source(vgrad(cx, 0, 0, 0, 430, [(0, c), (0.82, c), (1, (*c[:3], 0))]))
    cx.rectangle(0, 0, W, 430)
    cx.fill()


def bg_navy(cx, t):
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, hexc("#0D1838")), (0.45, hexc("#172B58")), (1, hexc("#1E3566"))]))
    cx.paint()
    _header_band(cx, (0.03, 0.06, 0.15, 0.85))
    for x, y, r, ph in STARS[::3]:
        cx.rectangle(x, y, r * 0.8, r * 0.8)
        src(cx, (1, 1, 1, 0.12 + 0.1 * math.sin(t + ph)))
        cx.fill()


def bg_purple(cx, t):
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, hexc("#170F1E")), (0.5, hexc("#21162C")), (1, hexc("#2E2140"))]))
    cx.paint()
    _header_band(cx, (0.06, 0.03, 0.08, 0.8))
    # soft horizontal bands like the reference
    cx.rectangle(0, 1440, W, 480)
    src(cx, (1, 1, 1, 0.025))
    cx.fill()


# ================================================================== SCENE 1: Earth hook
def scene_earth(cx, t):
    bg_space(cx, t)
    g = asset("globe")
    X, Y, R = W / 2, 900, 345
    lon0 = 25 + t * 3.0
    lat0 = 18
    pop = fmt_pop_frac(t)
    g.draw(cx, X, Y, R, lon0, lat0, lights=0.12 + 0.88 * pop, t=t)
    # "what if we're all related?" -> golden connections across the globe
    k = prog(t, S("hook2") + 0.2, S("hook2") + 1.6)
    if k > 0:
        rnd = random.Random(3)
        for i in range(70):
            a = (rnd.uniform(-10, 110), rnd.uniform(-30, 60))
            b = (rnd.uniform(-10, 110), rnd.uniform(-30, 60))
            d = rnd.uniform(0, 0.6)
            if g.screen(*a, X, Y, R, lon0, lat0)[2] < 0.2 or g.screen(*b, X, Y, R, lon0, lat0)[2] < 0.2:
                continue
            f = ease_out(prog(k, d, d + 0.4))
            g.arc(cx, a, b, X, Y, R, lon0, lat0, frac=f, alpha=0.55, lw=1.8)
    # Just Needy steps in
    a = prog(t, S("intro") - 0.15, S("intro") + 0.45)
    if a > 0:
        h = 560 * back_out(a)
        P.draw_jn_full(cx, W / 2, 1420 + (1 - a) * 160, max(1, h), t=t, alpha=min(1, a * 2) * jn_full_alpha_earth(t))


def fmt_pop_frac(t):
    return ease_io(prog(t, 0.45, S("hook1") + (E("hook1") - S("hook1")) * 0.75))


def pop_value(t):
    return fmt(8_200_000_000 * fmt_pop_frac(t))


def jn_full_alpha_earth(t):
    return 1.0


# ================================================================== SCENE 2: the fan tree
def RG(g):
    return 1150 - 950 * 0.86 ** (g - 1)


BADGE_R = {1: 56, 2: 46, 3: 38, 4: 25, 5: 15}


def node_pos(g, i):
    th = math.pi * (1 - (i + 0.5) / 2 ** g)
    r = RG(g)
    return r * math.cos(th), -r * math.sin(th)


POS = {g: np.array([node_pos(g, i) for i in range(2 ** g)]) for g in range(1, 11)}
LINE_BROWN = hexc("#B9814F")
DOT_M = hexc("#4F8DFF")
DOT_F = hexc("#FF6FA8")
PALETTES = {
    "main": (DOT_M, DOT_F, hexc("#69D2FF")),
    "green": (hexc("#3FD08A"), hexc("#B6F06A"), hexc("#6CE3C0")),
    "orange": (hexc("#FFA94D"), hexc("#FF7B5C"), hexc("#FFD36B")),
    "violet": (hexc("#A88BFF"), hexc("#E58BFF"), hexc("#8FB0FF")),
    "teal": (hexc("#38C9D6"), hexc("#7CE0B8"), hexc("#5EB4FF")),
}


def spec_for(seed, g, i):
    return P.Spec(seed * 100000 + 2 ** g + i, female=(i % 2 == 1))


def draw_fan(cx, ox, oy, z, gf, seed=0, palette="main", alpha=1.0, root="jn", avatars=5, root_r=None,
             highlights=(), hl_amt=0.0, max_dot_g=10, label=True, t=0.0):
    """Fan-shaped family tree. gf = generations revealed (float, up to 30)."""
    if alpha <= 0.003:
        return
    cm, cf, c3 = PALETTES[palette]
    cx.push_group()
    cx.save()
    cx.translate(ox, oy)
    # glow behind the fan
    if gf > 3:
        rr = RG(min(30, gf)) * z
        cx.set_source(rgrad(cx, 0, 0, rr * 0.2, rr * 1.15, [(0, (*c3[:3], 0.10)), (1, (*c3[:3], 0))]))
        cx.arc(0, 0, rr * 1.15, math.pi, 2 * math.pi)
        cx.fill()
    # outer generations: dotted rings + radial texture
    if gf > 10:
        top = min(30.0, gf)
        r10 = RG(10) * z
        nsp = 256
        cx.set_line_width(max(0.6, 1.4 * z))
        for k in range(nsp):
            th = math.pi * (1 - (k + 0.5) / nsp)
            c = (cm, cf, c3)[k % 3]
            src(cx, (*c[:3], 0.22))
            r1 = RG(top) * z
            cx.move_to(r10 * math.cos(th), -r10 * math.sin(th))
            cx.line_to(r1 * math.cos(th), -r1 * math.sin(th))
            cx.stroke()
        for g in range(11, int(top) + 1):
            p = clamp(top - g + 1)
            c = (cm, cf, c3)[g % 3]
            cx.set_dash([max(1.0, 3 * z), max(1.5, 5 * z)])
            src(cx, (*c[:3], 0.5 * p))
            cx.arc(0, 0, RG(g) * z, math.pi, 2 * math.pi)
            cx.stroke()
        cx.set_dash([])
    # links + nodes, outermost first
    gmax = min(max_dot_g, int(math.ceil(gf)))
    for g in range(gmax, 0, -1):
        p = clamp(gf - (g - 1))
        if p <= 0:
            continue
        pts = POS[g] * z
        par = POS[g - 1] * z if g > 1 else np.zeros((1, 2))
        portrait = g <= avatars and BADGE_R.get(g, 0) * z >= 4.5
        lw = (5.0 if g <= 3 else 3.0 if g <= 5 else 1.6 if g <= 7 else 1.0) * max(z, 0.45)
        cx.set_line_width(lw)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        grow = ease_out(clamp(p * 1.6))
        for i in range(len(pts)):
            a = par[i // 2] if g > 1 else (0.0, 0.0)
            b = pts[i]
            ex, ey = a[0] + (b[0] - a[0]) * grow, a[1] + (b[1] - a[1]) * grow
            if portrait or g <= 5:
                src(cx, LINE_BROWN, 0.95)
            else:
                c = cf if i % 2 else cm
                src(cx, (*c[:3], 0.55))
            cx.move_to(*a)
            cx.line_to(ex, ey)
            cx.stroke()
        if portrait:
            r = BADGE_R[g] * z
            for i in range(len(pts)):
                pa = clamp(p * 1.8 - 0.4 - 0.25 * i / len(pts))
                if pa <= 0:
                    continue
                sc = back_out(pa)
                P.draw_badge(cx, pts[i][0], pts[i][1], r * sc, "person", spec_for(seed, g, i), alpha=min(1, pa * 2))
        else:
            r = max(1.0, {6: 7.5, 7: 5.5, 8: 3.8, 9: 2.6, 10: 1.8}.get(g, 9.0 if g <= 5 else 1.5) * max(z, 0.5) * (1.0 if g > 5 else z * 2))
            a = clamp(p * 1.5)
            for col, sel in ((cm, 0), (cf, 1)):
                for i in range(sel, len(pts), 2):
                    circle(cx, pts[i][0], pts[i][1], r)
                src(cx, col, a)
                cx.fill()
    # repeated-ancestor highlights
    if hl_amt > 0:
        for g, i in highlights:
            x, y = POS[g][i] * z
            cx.set_source(rgrad(cx, x, y, 0, 26, [(0, (1, 0.85, 0.3, 0.9 * hl_amt)), (1, (1, 0.85, 0.3, 0))]))
            circle(cx, x, y, 26)
            cx.fill()
            circle(cx, x, y, 7)
            src(cx, YELLOW, hl_amt)
            cx.fill()
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    # root
    rr = root_r if root_r is not None else max(56 * z, 36)
    if root == "jn":
        P.draw_badge(cx, ox, oy, rr, "jn", glow=P.GOLD, glow_a=0.8, alpha=alpha)
        if label:
            ui.pill(cx, "JUST NEEDY", ox, oy + rr + 26 * max(0.6, rr / 56), 22 * max(0.6, rr / 56), YELLOW, alpha=alpha)
    else:
        P.draw_badge(cx, ox, oy, rr, "person", P.Spec(seed * 7 + 3), alpha=alpha, ring=PALETTES[palette][0])


def tree_cam(t):
    """(root screen y, zoom) for the main fan."""
    keys = [
        (S("par") - 0.6, (1185.0, 1.0)),
        (S("dbl"), (1185.0, 1.0)),
        (S("dbl") + 0.8, (1210.0, 0.86)),
        (S("g30") + 0.2, (1220.0, 0.80)),
        (E("g30") - 0.3, (1250.0, 0.44)),
        (S("pop") + 0.2, (1290.0, 0.44)),
        (E("pop"), (1290.0, 0.44)),
        (S("same") + 0.4, (1270.0, 0.44)),
        (E("same"), (1270.0, 0.44)),
        (S("mix") + 0.9, (1250.0, 0.31)),
        (S("mrca"), (1250.0, 0.31)),
        (S("mrca") + 1.4, (1270.0, 0.24)),
    ]
    oy, z = kf(t, keys, ease_io)
    gf = gens_revealed(t)
    if gf > 3:  # keep the growing fan inside the frame width
        gm = min(30.0, gf + 0.6)
        z = min(z, 505 / (RG(gm) + BADGE_R.get(int(gm), 8)))
    return oy, z


def gens_revealed(t):
    g = 0.0
    g += smooth(prog(t, S("par") + 0.05, S("par") + 0.7))
    g += smooth(prog(t, S("gp") + 0.0, S("gp") + 0.6))
    g += smooth(prog(t, S("ggp") + 0.1, S("ggp") + 0.8))
    g += smooth(prog(t, S("dbl") + 0.4, S("dbl") + 1.3))
    g += 26 * prog(t, S("g30") + 0.1, E("g30") - 0.3) ** 1.6
    return g


def g30_counter(t):
    g = max(4, int(gens_revealed(t)))
    return fmt(2 ** min(30, g)) + " slots"


HL = [(6, 5), (7, 37), (8, 120), (6, 40), (7, 90), (9, 300), (8, 200), (9, 450), (6, 22), (7, 66)]


def scene_tree(cx, t):
    bg_navy(cx, t)
    oy, z = tree_cam(t)
    gf = gens_revealed(t)
    # other people's trees slide in and overlap (Scene C/D)
    side = smooth(prog(t, S("mix") + 0.1, S("mix") + 1.3))
    more = smooth(prog(t, S("mrca") + 0.2, S("mrca") + 1.6))
    others = []
    if side > 0:
        dx = 300 + (1 - side) * 500
        others += [(-dx, "green", 21, side), (dx, "orange", 22, side)]
    if more > 0:
        dx2 = 600 + (1 - more) * 500
        others += [(-dx2, "violet", 23, more), (dx2, "teal", 24, more)]
    for dx, pal, sd, a in others:
        draw_fan(cx, W / 2 + dx * (z / 0.31), oy + 10, z, 30, seed=sd, palette=pal, alpha=0.9 * a, root="person",
                 avatars=3, max_dot_g=8, root_r=max(30, 56 * z))
    hl = smooth(prog(t, S("same") + 0.5, S("same") + 1.2)) * (1 - smooth(prog(t, S("mix"), S("mix") + 0.6)))
    draw_fan(cx, W / 2, oy, z, gf, seed=1, palette="main", root="jn", highlights=HL, hl_amt=hl, t=t)
    # x2 tags while doubling is explained
    k2 = pulse_in(t, S("dbl") + 0.1, S("g30") + 0.4)
    if k2 > 0:
        for g in range(1, 5):
            x, y = POS[g][0] * z
            ui.pill(cx, "×2", W / 2 + x - 8, oy + y + 54 * z + 6, 22, YELLOW, alpha=k2 * clamp(gf - g + 1), scale=1.0)
    # repeated ancestor: one person linked to many slots
    if hl > 0:
        ax, ay = W / 2, 560
        P.draw_badge(cx, ax, ay, 50 * back_out(clamp(hl * 1.3)), "person", P.Spec(4242, female=True), glow=YELLOW,
                     glow_a=0.8, alpha=hl, ring=P.GOLD)
        cx.set_line_width(2.4)
        for k, (g, i) in enumerate(HL):
            x, y = POS[g][i] * z
            f = ease_out(clamp(hl * 1.6 - k * 0.05))
            src(cx, YELLOW, 0.75 * hl)
            cx.move_to(ax, ay + 50)
            cx.line_to(ax + (W / 2 + x - ax) * f, ay + 50 + (oy + y - ay - 50) * f)
            cx.stroke()
    # everyone's common ancestor (Scene D)
    if more > 0:
        ax, ay = W / 2, 560
        tops = [W / 2 + d * (z / 0.31) for d in (-1200, -900, -600, -300, 0, 300, 600, 900, 1200)]
        cx.set_line_width(3.0)
        for k, x in enumerate(tops):
            f = ease_out(clamp(more * 1.4 - abs(k - 4) * 0.08))
            ty = oy - RG(30) * z
            src(cx, hexc("#E6B94A"), 0.85)
            cx.move_to(ax, ay)
            cx.line_to(ax + (x - ax) * f, ay + (ty - ay) * f)
            cx.stroke()
        sa = smooth(prog(t, word_t("mrca", "ancestor") - 0.1, word_t("mrca", "ancestor") + 0.4))
        if sa > 0:
            rr = 30 + 6 * math.sin(t * 3)
            cx.set_source(rgrad(cx, ax, ay, 0, 140, [(0, (1, 0.9, 0.5, 0.75 * sa)), (0.35, (1, 0.8, 0.3, 0.25 * sa)), (1, (1, 0.8, 0.3, 0))]))
            circle(cx, ax, ay, 140)
            cx.fill()
            circle(cx, ax, ay, rr)
            src(cx, hexc("#FFE08A"), sa)
            cx.fill_preserve()
            src(cx, hexc("#B8862B"), sa)
            cx.set_line_width(4)
            cx.stroke()
            # small star
            cx.save()
            cx.translate(ax, ay)
            cx.rotate(t * 0.6)
            for j in range(10):
                rr2 = 18 if j % 2 == 0 else 7
                a = j * math.pi / 5
                (cx.line_to if j else cx.move_to)(rr2 * math.cos(a), rr2 * math.sin(a))
            cx.close_path()
            src(cx, hexc("#FFFFFF"), sa)
            cx.fill()
            cx.restore()
    # 1200s population panel (Scene B)
    pa = smooth(prog(t, S("pop") - 0.1, S("pop") + 0.35)) * (1 - smooth(prog(t, S("same") - 0.1, S("same") + 0.25)))
    if pa > 0:
        draw_pop_panel(cx, t, pa)


def pulse_in(t, a, b, fade=0.3):
    return smooth(prog(t, a, a + fade)) * (1 - smooth(prog(t, b - fade, b)))


def draw_pop_panel(cx, t, a):
    x, y, w, h = 70, 470 - (1 - a) * 40, 940, 280
    cx.push_group()
    rrect(cx, x, y, w, h, 26)
    src(cx, hexc("#0C1430"), 0.94)
    cx.fill_preserve()
    src(cx, hexc("#3B4C80"))
    cx.set_line_width(2.5)
    cx.stroke()
    ui.draw_text(cx, "ANCESTOR SLOTS NEEDED", x + 34, y + 62, 26, WHITE, align="left", alpha=0.9)
    bw = w - 68
    rrect(cx, x + 34, y + 80, bw, 52, 12)
    src(cx, hexc("#FF5A5F"))
    cx.fill()
    ui.draw_text(cx, "1,073,741,824", x + 34 + bw - 18, y + 118, 30, WHITE, align="right")
    ui.draw_text(cx, "PEOPLE ALIVE IN THE 1200s", x + 34, y + 186, 26, WHITE, align="left", alpha=0.9)
    gk = ease_out(prog(t, S("pop") + 0.5, word_t("pop", "400")))
    gw = max(24, bw * 400 / 1074 * gk)
    rrect(cx, x + 34, y + 204, gw, 52, 12)
    src(cx, hexc("#2ECC71"))
    cx.fill()
    ui.draw_text(cx, "~400 million", x + 34 + gw + 18, y + 242, 30, WHITE, align="left", alpha=clamp(gk * 1.5))
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)


# ================================================================== SCENE 3: Africa / genetic lines
ANC_Y = 700
MOD_Y = 1330
ANC_X = [100 + k * 176 for k in range(6)]
MOD_X = [72 + k * 133.7 for k in range(8)]
MOD_F = [True, False, True, False, False, True, False, True]
MOD_SPECS = [P.Spec(500 + k, female=MOD_F[k]) for k in range(8)]
ANC_SPECS = [P.Spec(600 + k, female=(k in (0, 2, 3)), ancient=True) for k in range(6)]
ANC_SPECS_B = [P.Spec(700 + k, female=(k in (1, 5)), ancient=True) for k in range(6)]
EVE, ADAM = 2, 3


def _bez(p0, p1, n=24):
    """Vertical S-curve from p0 (top) to p1."""
    (x0, y0), (x1, y1) = p0, p1
    ym = (y0 + y1) / 2
    ts = np.linspace(0, 1, n)
    c1, c2 = (x0, ym), (x1, ym)
    xs = (1 - ts) ** 3 * x0 + 3 * (1 - ts) ** 2 * ts * c1[0] + 3 * (1 - ts) * ts ** 2 * c2[0] + ts ** 3 * x1
    ys = (1 - ts) ** 3 * y0 + 3 * (1 - ts) ** 2 * ts * c1[1] + 3 * (1 - ts) * ts ** 2 * c2[1] + ts ** 3 * y1
    return list(zip(xs, ys))


def lineage_paths(root_x, targets):
    """Binary-ish branching from an ancestor (top) to target x's (bottom). Returns list of (polyline, depth0)."""
    y0, y1, y2, y3 = ANC_Y + 50, 905, 1110, MOD_Y - 56
    paths = []
    tg = sorted(targets)
    half = len(tg) // 2 or 1
    groups = [tg[:half], tg[half:]] if len(tg) > 1 else [tg]
    for grp in groups:
        if not grp:
            continue
        mx = sum(grp) / len(grp)
        paths.append((_bez((root_x, y0), (mx, y1)), 0))
        h2 = len(grp) // 2 or 1
        subs = [grp[:h2], grp[h2:]] if len(grp) > 1 else [grp]
        for sg in subs:
            if not sg:
                continue
            sx = sum(sg) / len(sg)
            paths.append((_bez((mx, y1), (sx, y2)), 1))
            for x in sg:
                paths.append((_bez((sx, y2), (x, y3)), 2))
    return paths


EVE_PATHS = lineage_paths(ANC_X[EVE], MOD_X)
ADAM_PATHS = lineage_paths(ANC_X[ADAM], [MOD_X[k] for k in range(8) if not MOD_F[k]])


def draw_paths(cx, paths, color, k, alpha=1.0, glow=True, travel=None):
    """k in [0,3]: growth through depth levels."""
    if alpha <= 0.003 or k <= 0:
        return
    for lw, a in (((22, 0.12), (12, 0.25), (6.5, 1.0)) if glow else ((6.5, 1.0),)):
        cx.set_line_width(lw)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(cx, color, a * alpha)
        for pl, d in paths:
            f = clamp(k - d)
            if f <= 0:
                continue
            n = max(2, int(len(pl) * ease_out(f)))
            cx.move_to(*pl[0])
            for p in pl[1:n]:
                cx.line_to(*p)
            cx.stroke()
    if travel is not None:
        for pl, d in paths:
            u = travel * 3 - d
            if 0 <= u <= 1:
                i = int(u * (len(pl) - 1))
                x, y = pl[i]
                cx.set_source(rgrad(cx, x, y, 0, 26, [(0, (1, 1, 1, 0.95 * alpha)), (1, (1, 1, 1, 0))]))
                circle(cx, x, y, 26)
                cx.fill()


def _web():
    """Genealogical web: everyone connects to everyone through many intermediate ancestors."""
    rnd = random.Random(5)
    layers = [[(x, ANC_Y) for x in ANC_X],
              [(80 + k * 102, 860 + rnd.uniform(-20, 20)) for k in range(10)],
              [(60 + k * 88, 1010 + rnd.uniform(-20, 20)) for k in range(12)],
              [(70 + k * 94, 1160 + rnd.uniform(-20, 20)) for k in range(11)],
              [(x, MOD_Y) for x in MOD_X]]
    edges = []
    for li in range(1, len(layers)):
        up = layers[li - 1]
        for j, (x, y) in enumerate(layers[li]):
            near = sorted(range(len(up)), key=lambda q: abs(up[q][0] - x) + rnd.uniform(0, 260))
            for q in near[:2]:
                edges.append((li, up[q], (x, y)))
    dna = set(rnd.sample(range(len(edges)), 12))
    return layers, edges, dna


WEB = _web()


def scene_africa(cx, t):
    bg_purple(cx, t)
    am = asset("africa")
    am.draw(cx, 60, 390, 720, alpha=0.95)
    ui.draw_text(cx, "AFRICA", 900, 560, 30, hexc("#C79A86"), alpha=0.9)
    # rewind icon flash
    ra = pulse_in(t, S("rewind") - 0.1, S("rewind") + 1.3, 0.25)
    if ra > 0:
        cx.save()
        cx.translate(W / 2, 980)
        for dx in (-34, 22):
            cx.move_to(dx + 30, -40)
            cx.line_to(dx - 26, 0)
            cx.line_to(dx + 30, 40)
            cx.close_path()
        src(cx, WHITE, 0.9 * ra)
        cx.fill()
        cx.restore()
    t_gen2 = word_t("gen", "DNA")
    # genealogical web (Scene E)
    wa = pulse_in(t, S("gen") - 0.2, S("mt") + 0.2, 0.35)
    if wa > 0:
        layers, edges, dna = WEB
        dim = 1 - 0.75 * smooth(prog(t, t_gen2 - 0.1, t_gen2 + 0.5))
        grow = ease_out(prog(t, S("gen") - 0.1, S("gen") + 1.2))
        cx.set_line_width(2.2)
        for n, (li, a, b) in enumerate(edges):
            f = clamp(grow * 4 - (li - 1))
            if f <= 0:
                continue
            src(cx, (0.85, 0.85, 0.95, 0.42 * wa * dim))
            cx.move_to(*a)
            cx.line_to(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            cx.stroke()
        for li in (1, 2, 3):
            for x, y in layers[li]:
                circle(cx, x, y, 6)
                src(cx, (0.9, 0.85, 1.0, 0.6 * wa * dim * grow))
                cx.fill()
        ka = smooth(prog(t, t_gen2, t_gen2 + 0.6)) * wa
        if ka > 0:
            cx.set_line_width(6)
            for n, (li, a, b) in enumerate(edges):
                if n in dna:
                    cx.set_source(rgrad(cx, b[0], b[1], 0, 1, [(0, CYAN), (1, CYAN)]))
                    src(cx, CYAN, ka)
                    cx.move_to(*a)
                    cx.line_to(*b)
                    cx.stroke()
    # mitochondrial lineage
    mt_k = 3 * ease_io(prog(t, S("mt") + 0.6, word_t("mt", "woman") + 0.3))
    mt_a = 1 - smooth(prog(t, S("adam") - 0.1, S("adam") + 0.4))
    mt_back = smooth(prog(t, S("trace") - 0.3, S("trace") + 0.3))
    pink_a = max(mt_a if mt_k > 0 else 0, mt_back)
    trav = None
    if t >= S("unbroken"):
        trav = ((t - S("unbroken")) / 1.3) % 1.0
    draw_paths(cx, EVE_PATHS, PINK, 3 if mt_back > 0 else mt_k, alpha=pink_a, travel=trav)
    # Y-chromosome lineage
    y_k = 3 * ease_io(prog(t, S("adam") + 0.5, word_t("adam", "one man") if False else word_t("adam", "man:") + 0.3))
    y_a = 1 - smooth(prog(t, S("trace") - 0.4, S("trace") + 0.1))
    if t >= S("adam"):
        draw_paths(cx, ADAM_PATHS, BLUE, y_k, alpha=y_a)
    # broken lineages of everyone else
    br = smooth(prog(t, word_t("trace", "weren't") - 0.2, word_t("trace", "weren't") + 0.6))
    if br > 0:
        rnd = random.Random(9)
        cx.set_dash([10, 9])
        for k, x in enumerate(ANC_X):
            if k == EVE:
                continue
            for j in range(2):
                ln = rnd.uniform(90, 330)
                dx = rnd.uniform(-60, 60) + (j - 0.5) * 50
                y0 = ANC_Y + 50
                f = ease_out(clamp(br * 1.4 - k * 0.06))
                ex, ey = x + dx * f, y0 + ln * f
                cx.set_line_width(3.5)
                src(cx, (0.7, 0.68, 0.78, 0.8 * br))
                cx.move_to(x, y0)
                cx.curve_to(x, y0 + ln * 0.5 * f, ex, ey - ln * 0.4 * f, ex, ey)
                cx.stroke()
                cx.set_dash([])
                circle(cx, ex, ey, 7)
                src(cx, CORAL, br * clamp(f * 2 - 1))
                cx.fill()
                cx.set_dash([10, 9])
        cx.set_dash([])
    # ancient row (swaps to a different era for Y-Adam)
    swap = smooth(prog(t, S("adam") - 0.2, S("adam") + 0.4)) * (1 - smooth(prog(t, S("trace") - 0.4, S("trace") + 0.1)))
    eve_hi = smooth(prog(t, word_t("mt", "woman") - 0.2, word_t("mt", "woman") + 0.3)) * (1 - swap)
    adam_hi = smooth(prog(t, word_t("adam", "man:") - 0.2, word_t("adam", "man:") + 0.3)) * swap
    for specs, a in ((ANC_SPECS, 1 - swap), (ANC_SPECS_B, swap)):
        if a <= 0.003:
            continue
        for k, x in enumerate(ANC_X):
            r = 44
            glow = None
            hi = 0
            if specs is ANC_SPECS and k == EVE:
                hi = eve_hi
                glow = PINK
            if specs is ANC_SPECS_B and k == ADAM:
                hi = adam_hi
                glow = BLUE
            P.draw_badge(cx, x, ANC_Y, r * (1 + 0.38 * hi), "person", specs[k], alpha=a, glow=glow if hi > 0 else None,
                         glow_a=hi, ring=(PINK if glow is PINK and hi > 0.5 else BLUE if glow is BLUE and hi > 0.5 else None))
    ea = smooth(prog(t, word_t("eve", "Mitochondrial") - 0.2, word_t("eve", "Mitochondrial") + 0.2)) * (1 - swap)
    ui.pill(cx, "Mitochondrial Eve", ANC_X[EVE], ANC_Y - 92, 25, PINK, fg=WHITE, alpha=ea)
    aa = smooth(prog(t, word_t("adam", "Y-chromosomal") - 0.2, word_t("adam", "Y-chromosomal") + 0.2)) * swap
    ui.pill(cx, "Y-chromosomal Adam", ANC_X[ADAM], ANC_Y - 92, 25, BLUE, fg=WHITE, alpha=aa)
    # modern row
    for k, x in enumerate(MOD_X):
        P.draw_badge(cx, x, MOD_Y, 54, "person", MOD_SPECS[k])
    # "not a couple" card (Scene F)
    ca = pulse_in(t, S("couple") - 0.1, S("trace") - 0.05, 0.3)
    if ca > 0:
        draw_couple_card(cx, t, ca)


def draw_couple_card(cx, t, a):
    cx.push_group()
    src(cx, (0.05, 0.03, 0.08, 0.82))
    cx.rectangle(0, 420, W, 1020)
    cx.fill()
    pop = back_out(clamp(a * 1.2))
    for x, spec, col, name in ((300, ANC_SPECS[EVE], PINK, "Mitochondrial Eve"), (780, ANC_SPECS_B[ADAM], BLUE, "Y-chromosomal Adam")):
        P.draw_badge(cx, x, 760, 120 * pop, "person", spec, glow=col, glow_a=0.6, ring=col)
        ui.pill(cx, name, x, 925, 26, col, fg=WHITE)
    # crossed-out "couple" symbol between them
    k = smooth(prog(t, S("couple") + 0.15, S("couple") + 0.6))
    cx.save()
    cx.translate(W / 2, 760)
    circle(cx, 0, 0, 44)
    src(cx, CORAL, k)
    cx.set_line_width(7)
    cx.stroke()
    cx.move_to(-31, 31)
    cx.line_to(31, -31)
    cx.stroke()
    cx.move_to(0, 16)
    cx.curve_to(-26, -2, -18, -24, 0, -12)
    cx.curve_to(18, -24, 26, -2, 0, 16)
    src(cx, WHITE, 0.9 * k)
    cx.fill()
    cx.move_to(-31, 31)
    cx.line_to(31, -31)
    src(cx, CORAL, k)
    cx.set_line_width(7)
    cx.stroke()
    cx.restore()
    # timeline with two different points in time
    k2 = smooth(prog(t, word_t("couple", "same") - 0.5, word_t("couple", "same") + 0.2))
    y = 1110
    cx.set_line_width(5)
    src(cx, (1, 1, 1, 0.55 * k2))
    cx.move_to(120, y)
    cx.line_to(960, y)
    cx.stroke()
    cx.move_to(960, y)
    cx.line_to(940, y - 12)
    cx.line_to(940, y + 12)
    cx.close_path()
    cx.fill()
    ui.draw_text(cx, "TIME", 960, y + 48, 22, WHITE, align="right", spacing=3, alpha=0.6 * k2)
    for x, col in ((330, PINK), (690, BLUE)):
        circle(cx, x, y, 15)
        src(cx, col, k2)
        cx.fill()
    ui.draw_text(cx, "different eras", W / 2, y - 34, 26, WHITE, alpha=0.85 * k2)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)


# ================================================================== SCENE 4: out of Africa
ROUTES = [
    # (waypoints lon/lat, start, end)
    ("south", [(37, 2), (43, 12.5), (52, 17), (60, 24), (70, 22), (78, 15), (90, 22), (100, 14), (104, 2), (115, -5),
               (125, -9), (133, -14), (135, -24)]),
    ("west", [(52, 17), (45, 28), (38, 33), (33, 38), (26, 41), (18, 45), (10, 48), (2, 47)]),
    ("east", [(60, 24), (62, 34), (68, 40), (82, 44), (98, 45), (112, 38), (122, 45), (138, 52), (160, 62),
              (190, 65), (210, 62), (228, 55), (238, 47), (250, 36), (258, 22), (278, 10), (285, 0), (283, -12),
              (290, -30), (290, -45)]),
]


def route_times():
    o0, r0, r1 = S("out") + 0.3, S("route"), E("route")
    return {"south": (o0, word_t("route", "Australia") + 0.15),
            "west": (S("out") + 1.4, word_t("route", "Europe") + 0.2),
            "east": (word_t("route", "Asia") - 0.1, r1 + 0.1)}


LABELS = [("AFRICA", 22, 4, "out", None), ("ASIA", 90, 50, "route", "Asia"), ("EUROPE", 32, 51, "route", "Europe"),
          ("AUSTRALIA", 134, -30, "route", "Australia"), ("THE AMERICAS", 262, 42, "route", "Americas")]


MAP_T, MAP_B = 440, 1270


def mig_years(t):
    k = prog(t, S("out") + 0.2, E("route"))
    return "~" + fmt(round((65000 - 50000 * ease_io(k)) / 1000) * 1000) + " years ago"


def scene_map(cx, t):
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, hexc("#0C1636")), (1, hexc("#13224A"))]))
    cx.paint()
    fm = asset("flat")
    keys = [
        (S("out") - 0.4, (45.0, 12.0, 0.66)),
        (S("out") + 0.6, (45.0, 12.0, 0.66)),
        (E("out") + 0.2, (75.0, 22.0, 0.50)),
        (word_t("route", "Australia"), (100.0, 10.0, 0.47)),
        (E("route") + 0.4, (238.0, 15.0, 0.43)),
        (E("route") + 3.0, (242.0, 15.0, 0.43)),
    ]
    lon, lat, zoom = kf(t, keys, ease_io)
    half = (MAP_B - MAP_T) / 2 / (FlatMap.PPD * zoom)
    lat = min(FlatMap.LAT0 - half, max(FlatMap.LAT1 + half, lat))
    mx, my = fm.pt(lon, lat)
    cy = (MAP_T + MAP_B) / 2
    cx.save()
    cx.rectangle(0, MAP_T, W, MAP_B - MAP_T)
    cx.clip()
    fm.draw(cx, mx, my, zoom, W, 2 * cy)
    cx.restore()
    for y in (MAP_T, MAP_B):
        cx.rectangle(0, y - 1.5, W, 3)
        src(cx, (1, 1, 1, 0.08))
        cx.fill()

    def scr(lo, la):
        x, y = fm.pt(lo, la)
        return W / 2 + (x - mx) * zoom, cy + (y - my) * zoom

    cx.save()
    cx.rectangle(0, MAP_T, W, MAP_B - MAP_T)
    cx.clip()
    # origin glow in East Africa
    ox, oy = scr(37, 2)
    pr = 30 + 6 * math.sin(t * 4)
    cx.set_source(rgrad(cx, ox, oy, 0, 70, [(0, (1, 0.45, 0.65, 0.85)), (1, (1, 0.45, 0.65, 0))]))
    circle(cx, ox, oy, 70)
    cx.fill()
    circle(cx, ox, oy, 11)
    src(cx, PINK)
    cx.fill()
    rt = route_times()
    for name, pts in ROUTES:
        t0, t1 = rt[name]
        k = prog(t, t0, t1)
        if k <= 0:
            continue
        sp = [scr(*p) for p in pts]
        seg = np.array([math.dist(a, b) for a, b in zip(sp, sp[1:])])
        total = seg.sum()
        upto = total * ease_io(k)
        for lw, a in ((16, 0.15), (9, 0.3), (5, 1.0)):
            cx.set_line_width(lw)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.set_line_join(cairo.LINE_JOIN_ROUND)
            src(cx, hexc("#FFD36B"), a)
            cx.move_to(*sp[0])
            acc = 0
            for (a_, b_), d in zip(zip(sp, sp[1:]), seg):
                if acc + d <= upto:
                    cx.line_to(*b_)
                else:
                    f = (upto - acc) / d if d else 0
                    cx.line_to(a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f)
                    break
                acc += d
            cx.stroke()
        acc = 0
        for i, (p, d) in enumerate(zip(sp[1:], seg)):
            acc += d
            if acc <= upto and i % 3 == 2:
                circle(cx, p[0], p[1], 7)
                src(cx, hexc("#FFF4C8"))
                cx.fill()
    for name, lo, la, lid, word in LABELS:
        ta = S(lid) + 0.1 if word is None else word_t(lid, word)
        a = smooth(prog(t, ta - 0.1, ta + 0.3))
        if a > 0:
            x, y = scr(lo, la)
            ui.draw_text(cx, name, x, y, 30, WHITE, spacing=3, alpha=a, shadow=1.0)
    cx.restore()


# ================================================================== SCENE 5: final reveal
PINS = [("JAPAN", 139.7, 35.7, "Japan", P.Spec(901, female=True)),
        ("BRAZIL", -47.9, -15.8, "Brazil", P.Spec(902, female=False)),
        ("TURKEY", 32.8, 39.9, "Turkey", P.Spec(903, female=True))]
JN_HOME = (-96.0, 39.0)


def final_view(t):
    """Globe centre lon/lat, screen y, radius."""
    wj, wb, wt = word_t("rel", "Japan"), word_t("rel", "Brazil"), word_t("rel", "Turkey")
    wd = word_t("rel", "distant")
    keys = [
        (S("think") - 0.5, (-80.0, 30.0)),
        (S("rel") + 0.2, (-90.0, 32.0)),
        (wj - 0.1, (130.0, 32.0)),
        (wb - 0.15, (-50.0, -5.0)),
        (wt - 0.15, (30.0, 35.0)),
        (wd, (-10.0, 30.0)),
        (E("rel") + 0.3, (-40.0, 30.0)),
        (DUR, (-25.0, 26.0)),
    ]
    lon, lat = kf(t, keys, ease_io)
    y, R = kf(t, [(S("end") - 0.2, (900.0, 345.0)), (S("end") + 1.2, (790.0, 300.0))], ease_io)
    return lon, lat, y, R


def scene_final(cx, t):
    bg_space(cx, t)
    g = asset("globe")
    lon0, lat0, Y, R = final_view(t)
    X = W / 2
    g.draw(cx, X, Y, R, lon0, lat0, lights=1.0, t=t)
    # relatives everywhere: arcs from Just Needy's home to the world
    ka = prog(t, word_t("rel", "distant") - 0.3, word_t("rel", "distant") + 1.6)
    if ka > 0:
        rnd = random.Random(8)
        L = g.lights
        for i in range(90):
            j = rnd.randrange(len(L))
            b = (math.degrees(L[j][0]), math.degrees(L[j][1]))
            d = rnd.uniform(0, 0.5)
            g.arc(cx, JN_HOME, b, X, Y, R, lon0, lat0, frac=ease_out(prog(ka, d, d + 0.5)), alpha=0.5, lw=1.7)
    # pins
    for name, lo, la, word, spec in PINS:
        ta = word_t("rel", word)
        a = smooth(prog(t, ta - 0.2, ta + 0.25)) * (1 - smooth(prog(t, S("end") - 0.2, S("end") + 0.5)))
        draw_pin(cx, g, X, Y, R, lon0, lat0, lo, la, a, "person", spec, name, 40)
    draw_pin(cx, g, X, Y, R, lon0, lat0, *JN_HOME, 1.0, "jn", None, "JUST NEEDY", 50)
    # Just Needy stands in front of the Earth for the closing line
    ja = smooth(prog(t, S("end") + 0.1, S("end") + 1.0))
    if ja > 0:
        h = 540 * (0.85 + 0.15 * back_out(ja))
        P.draw_jn_full(cx, W / 2, 1405, h, t=t, alpha=ja)


def draw_pin(cx, g, X, Y, R, lon0, lat0, lo, la, a, kind, spec, label, r):
    if a <= 0.003:
        return
    sx, sy, z = g.screen(lo, la, X, Y, R, lon0, lat0)
    vis = clamp((z - 0.05) / 0.25)
    a *= vis
    if a <= 0.003:
        return
    stem = 78
    cx.set_line_width(3)
    src(cx, WHITE, 0.9 * a)
    cx.move_to(sx, sy)
    cx.line_to(sx, sy - stem)
    cx.stroke()
    circle(cx, sx, sy, 6)
    src(cx, hexc("#FF4D6D"), a)
    cx.fill()
    P.draw_badge(cx, sx, sy - stem - r, r * back_out(clamp(a)), kind, spec, alpha=a,
                 glow=P.GOLD if kind == "jn" else None, glow_a=0.6)
    ui.pill(cx, label, sx, sy - stem - 2 * r - 24, 20, YELLOW, alpha=a)


# ================================================================== timeline
def scene_spans():
    return [
        (scene_earth, 0.0, E("intro") + 0.25),
        (scene_tree, E("intro") - 0.25, S("rewind") + 0.25),
        (scene_africa, S("rewind") - 0.25, S("out") + 0.2),
        (scene_map, S("out") - 0.3, S("think") + 0.15),
        (scene_final, S("think") - 0.35, DUR + 1),
    ]


def header_entries():
    t_dna = word_t("gen", "DNA")
    t_few = word_t("mrca", "few")
    return [
        (0.0, "WORLD POPULATION", pop_value, "", YELLOW),
        (S("hook2") - 0.05, "BUT WHAT IF...", "we're all related?", "", YELLOW),
        (S("intro") - 0.05, "FAMILY TREE", "Just Needy", "our main character", WHITE),
        (S("par") - 0.05, "ANCESTORS", "2 parents", "generation 1", WHITE),
        (S("gp") - 0.05, "ANCESTORS", "4 grandparents", "generation 2", WHITE),
        (S("ggp") - 0.05, "ANCESTORS", "8 great-grandparents", "generation 3", WHITE),
        (S("dbl") - 0.05, "EVERY GENERATION", "×2", "", YELLOW),
        (S("g30") - 0.05, "30 GENERATIONS BACK (~800 YEARS)", g30_counter, "positions in a simple doubling model", WHITE),
        (S("pop") - 0.05, "BUT IN THE 1200s", "~400 million people", "the entire world population", CORAL),
        (S("same") - 0.05, "THE ANSWER", "the same ancestors", "fill many slots in one tree", YELLOW),
        (S("mix") - 0.05, "THE RESULT", "family trees overlap", "", YELLOW),
        (S("mrca") - 0.05, "EVERYONE'S COMMON ANCESTOR", "?", "", WHITE),
        (t_few - 0.1, "EVERYONE'S COMMON ANCESTOR", "a few thousand years ago", "according to one model", YELLOW),
        (S("rewind") - 0.05, "BACK IN TIME", rewind_years, "", WHITE),
        (S("gen") - 0.05, "TWO KINDS OF ANCESTRY", "family tree", "everyone you descend from", WHITE),
        (t_dna - 0.1, "TWO KINDS OF ANCESTRY", "genetic ancestry", "DNA comes from only some ancestors", CYAN),
        (S("mt") - 0.05, "MOTHER'S LINE · mtDNA", "one woman", "~150,000–200,000 years ago", PINK),
        (S("eve") - 0.05, "MOTHER'S LINE · mtDNA", "Mitochondrial Eve", "~150,000–200,000 years ago", PINK),
        (S("adam") - 0.05, "FATHER'S LINE · Y CHROMOSOME", "Y-chromosomal Adam", "traced through fathers and sons", BLUE),
        (S("couple") - 0.05, "IMPORTANT", "not a couple", "probably lived at different times", CORAL),
        (S("trace") - 0.05, "GENETIC LINEAGES", "common ancestors", "traced through DNA", YELLOW),
        (word_t("trace", "weren't") - 0.15, "BUT REMEMBER", "not the only people", "many others lived at the same time", CORAL),
        (S("unbroken") - 0.05, "WHY THEM?", "unbroken lines", "all the way to today", YELLOW),
        (S("out") - 0.25, "OUT OF AFRICA", mig_years, "approximate dates", WHITE),
        (S("think") - 0.25, "JUST THINK...", "everyone, everywhere", "", WHITE),
        (S("rel") - 0.05, "WORLD POPULATION", "8.2 billion relatives", "", YELLOW),
    ]


def rewind_years(t):
    k = ease_io(prog(t, S("rewind") + 0.1, E("rewind") + 0.2))
    v = 3000 * (200000 / 3000) ** k
    return fmt(round(v / 1000) * 1000) + " years ago"


HEADERS = None


def caption_y(t):
    if t < S("rewind"):
        return 1500
    if t < S("out") - 0.2:
        return 1560
    if t < S("think") - 0.2:
        return 1420
    return kf(t, [(S("end") - 0.2, 1500.0), (S("end") + 0.6, 1560.0)])


def render_frame(t):
    global HEADERS
    if HEADERS is None:
        HEADERS = header_entries()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    spans = [s for s in scene_spans() if s[1] <= t < s[2]]
    for i, (fn, a, b) in enumerate(spans):
        alpha = 1.0
        if i > 0:
            alpha = smooth(prog(t, a, a + 0.5))
        if alpha >= 0.999 or i == 0:
            fn(cx, t)
        else:
            cx.push_group()
            fn(cx, t)
            cx.pop_group_to_source()
            cx.paint_with_alpha(alpha)
    # morph: Just Needy shrinks into the root portrait of his family tree
    mk = prog(t, E("intro") - 0.25, S("par") + 0.15)
    if 0 < mk < 1:
        k = ease_io(mk)
        h = lerp(560, 150, k)
        y = lerp(1420, 1185 + 75, k)
        P.draw_jn_full(cx, W / 2, y, h, t=t, alpha=1 - smooth(prog(mk, 0.55, 1.0)))
    ui.header(cx, t, HEADERS)
    CAPS.draw(cx, t, caption_y(t))
    # final fade out
    fo = smooth(prog(t, DUR - 0.7, DUR))
    if fo > 0:
        src(cx, (0, 0, 0, fo))
        cx.paint()
    return surf


# ------------------------------------------------------------------ CLI
def stills(times):
    out = os.path.join(BUILD, "stills")
    os.makedirs(out, exist_ok=True)
    for tt in times:
        p = os.path.join(out, f"t{float(tt):06.2f}.png")
        render_frame(float(tt)).write_to_png(p)
        print(p)


def _worker(args):
    wi, f0, f1, path = args
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
                             "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        surf = render_frame(f / FPS)
        proc.stdin.write(bytes(surf.get_data()))
        if wi == 0 and (f - f0) % 60 == 0:
            print(f"  worker0 {f - f0}/{f1 - f0}", flush=True)
    proc.stdin.close()
    proc.wait()
    return path


def video(workers=4):
    from multiprocessing import Pool
    n = int(math.ceil(DUR * FPS))
    seg = os.path.join(BUILD, "segments")
    os.makedirs(seg, exist_ok=True)
    k = 8
    bounds = [(i * n // k, (i + 1) * n // k) for i in range(k)]
    jobs = [(i, a, b, os.path.join(seg, f"seg_{i:02d}.mp4")) for i, (a, b) in enumerate(bounds)]
    with Pool(workers) as pool:
        paths = pool.map(_worker, jobs)
    lst = os.path.join(seg, "list.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    out = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print(out, n, "frames")


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills(sys.argv[2:])
    elif sys.argv[1] == "video":
        video()

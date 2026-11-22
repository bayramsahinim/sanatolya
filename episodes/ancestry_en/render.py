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
EARTH_X, EARTH_Y, EARTH_R = W / 2, 790, 330


def jn_opening(t):
    """Just Needy's position/size/expression in the opening: he steps in, looks up at the Earth,
    turns to us on 'relative?', then walks to centre for the family tree."""
    enter = ease_out(prog(t, S("hook_a") + 0.9, S("hook_a") + 1.7))
    to_c = ease_io(prog(t, S("intro") - 0.1, S("intro") + 0.7))
    x = lerp(300, W / 2, to_c)
    y = 1395 + (1 - enter) * 520
    h = 470
    t_rel = word_t("hook_b", "relative")
    turn = smooth(prog(t, t_rel - 0.25, t_rel + 0.1))
    look = lerpv2((0.65, -0.9), (0.0, 0.0), turn)
    brows = turn * (1 - to_c) * 0.9
    mouth = "o" if 0.3 < turn and to_c < 0.2 and t < t_rel + 0.7 else "smile"
    tilt = lerp(-0.12, 0.0, turn)
    return x, y, h, P.Expr(look, brows, mouth), tilt, enter


def lerpv2(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


# ------------------------------------------------------------------ opening: deep star field + slow camera
def _deep_stars():
    """Three parallax layers of naturally distributed stars (far = many, tiny, dim; near = few, larger,
    blue-white). Positions span a margin around the frame so the slow camera drift never reveals an edge."""
    rnd = np.random.default_rng(2024)
    M = 160
    layers = []
    for n, rmin, rmax, amin, amax, depth in ((1000, 0.75, 1.25, 0.22, 0.60, 0.25),
                                             (340, 1.05, 1.8, 0.42, 0.85, 0.55),
                                             (75, 1.5, 2.5, 0.65, 1.0, 1.0)):
        # loose clustering (a faint band) + uniform field, so it never looks like a regular grid
        u = rnd.random(n)
        x = rnd.uniform(-M, W + M, n)
        y = np.where(u < 0.3, H * 0.42 + (x - W / 2) * -0.55 + rnd.normal(0, 210, n), rnd.uniform(-M, H + M, n))
        r = rmin + (rmax - rmin) * rnd.random(n) ** 2.2          # mostly small, a few bright
        a = amin + (amax - amin) * rnd.random(n) ** 1.6
        tint = rnd.random(n)                                        # 0 = white, 1 = blue-white
        ph = rnd.uniform(0, 6.28, n)
        sp = rnd.uniform(0.6, 1.8, n)
        layers.append((x, y, r, a, tint, ph, sp, depth))
    return layers


DEEP = _deep_stars()


def opening_zoom(t):
    """Slow cinematic push toward the Earth: a gentle drift from frame one, a clearer push 1-3 s."""
    return 1.0 + 0.02 * prog(t, 0.0, 1.0) + 0.075 * ease_io(prog(t, 1.0, 3.3)) + 0.025 * prog(t, 3.3, 6.2)


def bg_space_deep(cx, t, zoom):
    cx.set_source(rgrad(cx, W / 2, H * 0.47, 50, H * 0.75, [(0, hexc("#14254F")), (0.6, hexc("#0A1532")), (1, hexc("#050A1C"))]))
    cx.paint()
    # very faint, wide milky band for depth (no colourful nebulae)
    cx.save()
    cx.translate(W / 2, H * 0.42)
    cx.rotate(-0.5)
    cx.scale(1.0, 0.22)
    cx.set_source(rgrad(cx, 0, 0, 0, W * 1.1, [(0, (0.55, 0.65, 0.95, 0.06)), (0.6, (0.45, 0.55, 0.9, 0.025)), (1, (0.4, 0.5, 0.9, 0))]))
    circle(cx, 0, 0, W * 1.1)
    cx.fill()
    cx.restore()
    CX0, CY0 = EARTH_X, EARTH_Y
    for x, y, r, a, tint, ph, sp, depth in DEEP:
        z = 1 + (zoom - 1) * depth                       # parallax: near stars spread faster
        X = CX0 + (x - CX0) * z - t * 5.0 * depth        # slow lateral drift, faster for near layers
        Y = CY0 + (y - CY0) * z + t * 1.6 * depth
        tw = 1 + 0.16 * np.sin(t * sp + ph)              # very subtle twinkle
        A = np.clip(a * tw, 0, 1)
        vis = (X > -4) & (X < W + 4) & (Y > -4) & (Y < H + 4)
        R_ = r * z
        if depth < 1.0:
            # batch by tint bucket for speed
            for lo, hi, col in ((0, 0.6, (1.0, 1.0, 1.0)), (0.6, 1.01, (0.78, 0.87, 1.0))):
                sel = vis & (tint >= lo) & (tint < hi)
                for xx, yy, rr, aa in zip(X[sel], Y[sel], R_[sel], A[sel]):
                    cx.arc(xx, yy, rr, 0, 6.2832)
                    src(cx, (*col, aa))
                    cx.fill()
        else:
            for xx, yy, rr, aa, tt in zip(X[vis], Y[vis], R_[vis], A[vis], tint[vis]):
                col = (0.72, 0.84, 1.0) if tt > 0.45 else (1.0, 1.0, 1.0)
                cx.set_source(rgrad(cx, xx, yy, 0, rr * 4.0, [(0, (*col, aa * 0.35)), (1, (*col, 0))]))
                circle(cx, xx, yy, rr * 4.0)
                cx.fill()
                circle(cx, xx, yy, rr)
                src(cx, (*col, aa))
                cx.fill()
    # the channel's soft four-point sparkles, kept few and quiet
    for x, y, ph in SPARKS[:6]:
        a = 0.18 + 0.16 * math.sin(t * 0.9 + ph)
        X = CX0 + (x - CX0) * zoom - t * 5.0
        Y = CY0 + (y - CY0) * zoom + t * 1.6
        src(cx, (0.85, 0.92, 1, a))
        cx.set_line_width(1.4)
        cx.move_to(X - 6, Y)
        cx.line_to(X + 6, Y)
        cx.move_to(X, Y - 6)
        cx.line_to(X, Y + 6)
        cx.stroke()
    _header_band(cx, (0.02, 0.04, 0.10, 0.55))


# populous regions used for the "shared ancestry" links (lon, lat)
HUBS = [(78, 23), (113, 30), (10, 48), (8, 9), (31, 29), (110, -6), (36, 0), (45, 33), (37, 55), (28, -26),
        (-5, 40), (100, 15), (67, 30), (-15, 14), (20, 0), (140, 36), (127, 37), (55, 25), (25, 60), (90, 45)]


def _hub_links():
    """Pairs of distant hubs (>= 35 deg apart), in a fixed order."""
    rnd = random.Random(5)
    out = []
    for _ in range(400):
        a, b = rnd.sample(HUBS, 2)
        la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
        d = math.degrees(math.acos(max(-1, min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(lo1 - lo2)))))
        if d >= 35 and (a, b) not in out and (b, a) not in out:
            j = (rnd.uniform(-3, 3), rnd.uniform(-3, 3))
            out.append(((a[0] + j[0], a[1] + j[1]), (b[0] - j[1], b[1] + j[0]), rnd.uniform(0, 0.7)))
        if len(out) == 18:
            break
    return out


EARTH_LINKS = _hub_links()
T_LINKS = 3.0


def scene_earth(cx, t):
    zoom = opening_zoom(t)
    bg_space_deep(cx, t, zoom)
    g = asset("globe")
    X, Y, R = EARTH_X, EARTH_Y, EARTH_R * zoom
    lon0 = 25 + t * 3.0
    lat0 = 18
    pop = fmt_pop_frac(t)
    g.draw(cx, X, Y, R, lon0, lat0, lights=0.03 + 0.97 * pop, t=t)
    # 3-5 s: thin glowing links between distant regions -> shared ancestors
    for a, b, d in EARTH_LINKS:
        f = ease_out(prog(t, T_LINKS + d, T_LINKS + d + 0.6))
        if f <= 0:
            continue
        if g.screen(*a, X, Y, R, lon0, lat0)[2] < 0.15 or g.screen(*b, X, Y, R, lon0, lat0)[2] < 0.15:
            continue
        # bright while drawing, then settles to a quiet glow
        al = 1.0 - 0.55 * smooth(prog(t, T_LINKS + d + 0.6, T_LINKS + d + 1.6))
        g.arc(cx, a, b, X, Y, R, lon0, lat0, frac=f, alpha=0.16 * al, lw=6.0)
        g.arc(cx, a, b, X, Y, R, lon0, lat0, frac=f, alpha=0.75 * al, lw=1.5)
        for p, show in ((a, 1.0), (b, 1.0 if f > 0.98 else 0.0)):
            sx, sy, _ = g.screen(*p, X, Y, R, lon0, lat0)
            ga = 0.8 * al * show
            if ga > 0:
                cx.set_source(rgrad(cx, sx, sy, 0, 11, [(0, (1.0, 0.9, 0.5, ga)), (1, (1.0, 0.85, 0.3, 0))]))
                circle(cx, sx, sy, 11)
                cx.fill()
    # Just Needy looks up at the Earth, then at us
    x, y, h, e, tilt, enter = jn_opening(t)
    if enter > 0 and t < E("intro") - 0.25:
        P.draw_jn_full(cx, x, y, h, t=t, expr=e, head_tilt=tilt)
        # a small "?" as he wonders
        t_rel = word_t("hook_b", "relative")
        qa = pulse_in(t, t_rel - 0.05, S("intro") + 0.1, 0.2)
        if qa > 0:
            sc = back_out(clamp((t - t_rel + 0.05) / 0.3))
            ui.draw_text(cx, "?", x + 95, y - h * 1.02, 84 * sc, YELLOW, alpha=qa, shadow=1.0)


def fmt_pop_frac(t):
    """People-lights (and the population counter) fill in during 'every person on Earth'."""
    return ease_io(prog(t, 0.9, 3.0))


def pop_value(t):
    # the counter starts rolling with the first word, ahead of the lights
    return fmt(8_200_000_000 * ease_io(prog(t, 0.2, 2.9)))


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
             highlights=(), hl_amt=0.0, max_dot_g=10, label=True, t=0.0, root_expr=None, line_c=None):
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
                src(cx, line_c or LINE_BROWN, 0.95)
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
        P.draw_badge(cx, ox, oy, rr, "jn", glow=P.GOLD, glow_a=0.8, alpha=alpha, expr=root_expr)
        if label:
            ui.pill(cx, "JUST NEEDY", ox, oy + rr + 30, 28, YELLOW, alpha=alpha)
    else:
        P.draw_badge(cx, ox, oy, rr, "person", P.Spec(seed * 7 + 3), alpha=alpha, ring=PALETTES[palette][0])


ROOT_Y = 1185.0
NEIGHBOUR_DX = 330.0      # screen spacing between neighbouring trees at the reference zoom 0.31


def tree_cam(t):
    """(root screen y, zoom) for the main fan."""
    keys = [
        (S("par") - 0.6, (ROOT_Y, 1.0)),
        (S("dbl"), (ROOT_Y, 1.0)),
        (S("dbl") + 0.8, (1210.0, 0.86)),
        (S("g30") + 0.2, (1220.0, 0.80)),
        (E("g30") - 0.3, (1250.0, 0.44)),
        (S("pop") + 0.2, (1330.0, 0.44)),
        (E("pop"), (1330.0, 0.44)),
        (S("same") + 0.4, (1260.0, 0.44)),
        (E("same") - 0.3, (1260.0, 0.44)),
        (S("mix") + 1.2, (1290.0, 0.37)),
        (S("mrca") + 0.3, (1290.0, 0.37)),
        (S("mrca") + 2.0, (1300.0, 0.29)),
        (E("mrca"), (1300.0, 0.28)),
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


def _cross_links():
    """Pairs of nodes in neighbouring trees that sit close together where the fans overlap: the
    'shared ancestor' links drawn when the trees merge. World units (zoom 1, root at 0,0)."""
    rnd = random.Random(17)
    D = NEIGHBOUR_DX / 0.31
    links = []
    for side in (-1, 1):
        for g in (7, 8, 9):
            n = 2 ** g
            idx = range(0, int(n * 0.32)) if side < 0 else range(int(n * 0.68), n)
            cands = rnd.sample(list(idx), 5)
            for i in cands:
                ax, ay = POS[g][i]
                best = None
                for g2 in (7, 8, 9):
                    n2 = 2 ** g2
                    idx2 = range(int(n2 * 0.68), n2) if side < 0 else range(0, int(n2 * 0.32))
                    for j in idx2:
                        bx, by = POS[g2][j]
                        bx += side * D
                        d = math.hypot(bx - ax, by - ay)
                        if best is None or d < best[0]:
                            best = (d, (bx, by))
                links.append(((ax, ay), best[1], side, rnd.uniform(0, 0.6)))
    # links between the outer neighbours and their neighbours (second wave)
    outer = []
    for (a, b, side, d) in links:
        outer.append(((a[0] + side * D, a[1]), (b[0] + side * D, b[1]), side, d + 0.2))
    return links, outer


LINKS, LINKS_OUTER = _cross_links()


def jn_root_expr(t):
    t_ov = word_t("mix", "overlap")
    surprise = pulse_in(t, t_ov - 0.15, S("mrca") + 0.8, 0.2)
    look_up = smooth(prog(t, S("par") - 0.2, S("par") + 0.3)) * (1 - smooth(prog(t, E("g30") - 0.4, E("g30"))))
    look_star = smooth(prog(t, word_t("mrca", "ancestor") - 0.3, word_t("mrca", "ancestor")))
    look_hl = pulse_in(t, S("same") + 0.4, E("same"), 0.25)
    ly = -max(look_up, look_star, look_hl) * 0.9
    if surprise > 0.5:
        return P.Expr((0, -0.3), 1.0, "o")
    if look_star > 0.5:
        return P.Expr((0, -1), 0.5, "smile")
    return P.Expr((0, ly), 0.0, "smile")


def scene_tree(cx, t):
    bg_navy(cx, t)
    oy, z = tree_cam(t)
    gf = gens_revealed(t)
    # rewind: the whole network collapses back into the past
    rw = ease_io(prog(t, S("rewind") - 0.1, S("rewind") + 0.9))
    if rw > 0:
        z *= 1 - 0.85 * rw
    net_a = 1 - smooth(prog(t, S("rewind") + 0.4, S("rewind") + 1.0))
    # neighbouring trees GROW from their own roots and run into ours (Scene C), more join for Scene D
    grow1 = prog(t, E("same") - 0.35, word_t("mix", "overlap") + 0.1)
    grow2 = prog(t, S("mrca") + 0.2, S("mrca") + 1.9)
    fans = []
    k = z / 0.31
    if grow1 > 0:
        fans += [(-1, "green", 21, grow1), (1, "orange", 22, grow1)]
    if grow2 > 0:
        fans += [(-2, "violet", 23, grow2), (2, "teal", 24, grow2)]
    for m, pal, sd, gp in fans:
        gfo = 1 + 13 * ease_out(gp) if gp < 1 else 30
        draw_fan(cx, W / 2 + m * NEIGHBOUR_DX * k, oy + 8, z, gfo, seed=sd, palette=pal,
                 alpha=0.92 * smooth(clamp(gp * 4)) * net_a, root="person", avatars=3, max_dot_g=8,
                 root_r=max(30, 56 * z))
    hl = smooth(prog(t, S("same") + 0.5, S("same") + 1.2)) * (1 - smooth(prog(t, E("same") - 0.2, S("mix") + 0.3)))
    draw_fan(cx, W / 2, oy, z, gf, seed=1, palette="main", root="jn", highlights=HL, hl_amt=hl, t=t,
             root_expr=jn_root_expr(t), alpha=net_a)
    # shared ancestors: links appear where the separate trees cross
    t_ov = word_t("mix", "overlap")
    lk = prog(t, t_ov - 0.4, t_ov + 1.0)
    lk2 = prog(t, S("mrca") + 1.0, S("mrca") + 2.4)
    for links, kk in ((LINKS, lk), (LINKS_OUTER, lk2)):
        if kk <= 0:
            continue
        for (a, b, side, d) in links:
            f = ease_out(clamp((kk - d) / 0.4))
            if f <= 0:
                continue
            ax, ay = W / 2 + a[0] * z, oy + a[1] * z
            bx, by = W / 2 + b[0] * z, oy + b[1] * z
            ex, ey = ax + (bx - ax) * f, ay + (by - ay) * f
            src(cx, YELLOW, 0.95 * net_a)
            cx.set_line_width(3.4)
            cx.move_to(ax, ay)
            cx.line_to(ex, ey)
            cx.stroke()
            for (px, py), on in (((ax, ay), True), ((bx, by), f >= 1)):
                if on:
                    cx.set_source(rgrad(cx, px, py, 0, 16, [(0, (1, 0.85, 0.3, 0.8 * net_a)), (1, (1, 0.85, 0.3, 0))]))
                    circle(cx, px, py, 16)
                    cx.fill()
                    circle(cx, px, py, 5)
                    src(cx, YELLOW, net_a)
                    cx.fill()
    # Just Needy's "!" when the trees connect
    ex_a = pulse_in(t, t_ov - 0.1, S("mrca") + 0.6, 0.2)
    if ex_a > 0:
        rr = max(56 * z, 36)
        sc = back_out(clamp((t - t_ov + 0.1) / 0.3))
        ui.draw_text(cx, "!", W / 2 + rr + 18, oy - rr - 6, 70 * sc, YELLOW, alpha=ex_a * net_a, shadow=1.0)
    # x2 tags while doubling is explained
    k2 = pulse_in(t, S("dbl") + 0.1, S("g30") + 0.4)
    if k2 > 0:
        for g in range(1, 5):
            x, y = POS[g][0] * z
            ui.pill(cx, "×2", W / 2 + x - 8, oy + y + 54 * z + 10, 30, YELLOW, alpha=k2 * clamp(gf - g + 1))
    # repeated ancestor: one person linked to many slots
    if hl > 0:
        ax, ay = W / 2, 560
        P.draw_badge(cx, ax, ay, 56 * back_out(clamp(hl * 1.3)), "person", P.Spec(4242, female=True), glow=YELLOW,
                     glow_a=0.8, alpha=hl, ring=P.GOLD)
        cx.set_line_width(2.6)
        for kq, (g, i) in enumerate(HL):
            x, y = POS[g][i] * z
            f = ease_out(clamp(hl * 1.6 - kq * 0.05))
            src(cx, YELLOW, 0.75 * hl)
            cx.move_to(ax, ay + 56)
            cx.line_to(ax + (W / 2 + x - ax) * f, ay + 56 + (oy + y - ay - 56) * f)
            cx.stroke()
    # everyone's common ancestor (Scene D)
    more = smooth(prog(t, word_t("mrca", "share") - 0.2, word_t("mrca", "ancestor") + 0.4))
    if more > 0:
        ax, ay = W / 2, 560
        cx.set_line_width(3.0)
        for m in range(-4, 5):
            x = W / 2 + m * NEIGHBOUR_DX * k
            f = ease_out(clamp(more * 1.4 - abs(m) * 0.08))
            ty = oy - RG(30) * z
            src(cx, hexc("#E6B94A"), 0.85 * net_a)
            cx.move_to(ax, ay)
            cx.line_to(ax + (x - ax) * f, ay + (ty - ay) * f)
            cx.stroke()
        sa = smooth(prog(t, word_t("mrca", "ancestor") - 0.1, word_t("mrca", "ancestor") + 0.4)) * net_a
        if sa > 0:
            draw_star_medallion(cx, ax, ay, t, sa)
    # rewind icon
    ra = pulse_in(t, S("rewind") - 0.05, E("rewind") + 0.2, 0.2)
    if ra > 0:
        draw_rewind_icon(cx, W / 2, 900, ra)
    # 1200s population panel (Scene B)
    pa = smooth(prog(t, S("pop") - 0.1, S("pop") + 0.35)) * (1 - smooth(prog(t, S("same") - 0.1, S("same") + 0.25)))
    if pa > 0:
        draw_pop_panel(cx, t, pa)


def draw_star_medallion(cx, ax, ay, t, sa):
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


def draw_rewind_icon(cx, x, y, a):
    cx.save()
    cx.translate(x, y)
    circle(cx, 0, 0, 92)
    src(cx, (0.03, 0.05, 0.12, 0.55 * a))
    cx.fill()
    for dx in (-30, 26):
        cx.move_to(dx + 30, -40)
        cx.line_to(dx - 26, 0)
        cx.line_to(dx + 30, 40)
        cx.close_path()
    src(cx, WHITE, 0.95 * a)
    cx.fill()
    cx.restore()


def pulse_in(t, a, b, fade=0.3):
    return smooth(prog(t, a, a + fade)) * (1 - smooth(prog(t, b - fade, b)))


def draw_pop_panel(cx, t, a):
    x, y, w, h = 60, 445 - (1 - a) * 40, 960, 340
    cx.push_group()
    rrect(cx, x, y, w, h, 28)
    src(cx, hexc("#0B1330"), 0.95)
    cx.fill_preserve()
    src(cx, hexc("#3B4C80"))
    cx.set_line_width(3)
    cx.stroke()
    ui.draw_text(cx, "ANCESTOR SLOTS NEEDED", x + 36, y + 66, 32, WHITE, align="left")
    bw = w - 72
    rrect(cx, x + 36, y + 88, bw, 66, 14)
    src(cx, hexc("#FF5A5F"))
    cx.fill()
    ui.draw_text(cx, "1,073,741,824", x + 36 + bw - 22, y + 136, 42, WHITE, align="right")
    ui.draw_text(cx, "PEOPLE ALIVE IN THE 1200s", x + 36, y + 222, 32, WHITE, align="left")
    gk = ease_out(prog(t, S("pop") + 0.5, word_t("pop", "400")))
    gw = max(24, bw * 400 / 1074 * gk)
    rrect(cx, x + 36, y + 244, gw, 66, 14)
    src(cx, hexc("#2ECC71"))
    cx.fill()
    ui.draw_text(cx, "~400 million", x + 36 + gw + 22, y + 292, 42, WHITE, align="left", alpha=clamp(gk * 1.5))
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)


# ================================================================== SCENE 2b: family tree vs DNA
DNA_LEAVES = sorted(random.Random(31).sample(range(64), 9))


def scene_dna(cx, t):
    """Genealogical vs genetic ancestry, on Just Needy's own tree."""
    bg_navy(cx, t)
    t_dna = word_t("gen", "DNA")
    z = kf(t, [(S("gen") - 0.4, 0.62), (t_dna, 0.74), (E("gen") + 0.4, 0.77)], ease_io)
    oy = kf(t, [(S("gen") - 0.4, 1290.0), (E("gen") + 0.4, 1310.0)], ease_io)
    gf = 6 * ease_out(prog(t, S("gen") - 0.3, S("gen") + 1.4))
    dim = smooth(prog(t, t_dna - 0.1, t_dna + 0.6))
    e = P.Expr((0, -0.9), 0.0, "smile") if dim < 0.5 else P.Expr((0.0, -0.6), 0.6, "smile")
    draw_fan(cx, W / 2, oy, z, gf, seed=1, palette="main", root="jn", t=t, root_expr=e,
             alpha=1 - 0.72 * dim, max_dot_g=6, avatars=4)
    # DNA: only a few branches actually pass pieces down
    if dim > 0:
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        grow = 6 * ease_out(prog(t, t_dna, t_dna + 1.4))
        for leaf in DNA_LEAVES:
            pts = [(0.0, 0.0)] + [tuple(POS[g][leaf >> (6 - g)]) for g in range(1, 7)]
            for gi in range(6):
                f = clamp(grow - gi)
                if f <= 0:
                    break
                (x0, y0), (x1, y1) = pts[gi], pts[gi + 1]
                for lw, al in ((16, 0.15), (6, 1.0)):
                    cx.set_line_width(lw)
                    src(cx, CYAN, al * dim)
                    cx.move_to(W / 2 + x0 * z, oy + y0 * z)
                    cx.line_to(W / 2 + (x0 + (x1 - x0) * f) * z, oy + (y0 + (y1 - y0) * f) * z)
                    cx.stroke()
            if grow >= 6:
                x, y = POS[6][leaf]
                circle(cx, W / 2 + x * z, oy + y * z, 11)
                src(cx, CYAN, dim)
                cx.fill()
        P.draw_badge(cx, W / 2, oy, max(56 * z, 36), "jn", glow=CYAN, glow_a=0.7 * dim, expr=e)
    # legend chips
    la = smooth(prog(t, S("gen") + 0.2, S("gen") + 0.6))
    ui.pill(cx, "FAMILY TREE = everyone", W / 2, 520, 32, hexc("#DDE6FF"), alpha=la * (1 - 0.6 * dim))
    ui.pill(cx, "DNA = only some", W / 2, 600, 32, CYAN, alpha=dim)


# ================================================================== SCENE 3: Africa / genetic lines
ANC_Y = 690
MOD_Y = 1250
ANC_X = [120 + k * 168 for k in range(6)]
MOD_X = [110 + k * 122.9 for k in range(8)]
MOD_F = [True, False, True, False, False, True, False, True]
JN_I = 3  # Just Needy is one of today's people
MOD_SPECS = [P.Spec(500 + k, female=MOD_F[k]) for k in range(8)]
ANC_SPECS = [P.Spec(600 + k, female=(k in (0, 2, 3)), ancient=True) for k in range(6)]
ANC_SPECS_B = [P.Spec(700 + k, female=(k in (1, 5)), ancient=True) for k in range(6)]
EVE, ADAM = 2, 3


def _crowd():
    """Other people alive at the same time, placed beyond the first framing (revealed by the pull-back)."""
    rnd = random.Random(12)
    out = []
    for row, y in enumerate((585, ANC_Y, 800)):
        x = -430.0 + rnd.uniform(0, 60)
        while x < 1510:
            inside = 40 < x < 1040
            if not (row == 1 and inside) and not (inside and row != 1 and abs(x - ANC_X[EVE]) < 260):
                out.append((x, y + rnd.uniform(-18, 18), P.Spec(800 + len(out), ancient=True), rnd.uniform(30, 38),
                            rnd.uniform(70, 230), rnd.uniform(-50, 50)))
            x += rnd.uniform(118, 170)
    return out


CROWD = _crowd()


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
    """Branching from an ancestor (top) to target x's (bottom). Returns list of (polyline, depth)."""
    y0, y1, y2, y3 = ANC_Y + 50, 880, 1060, MOD_Y - 54
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


def chain_to(paths, x):
    """The single polyline from the ancestor down to the descendant at x."""
    out = []
    target = None
    for d in (2, 1, 0):
        for pl, dd in paths:
            if dd != d:
                continue
            end = pl[-1]
            if (d == 2 and abs(end[0] - x) < 1) or (d < 2 and target and abs(end[0] - target[0]) < 1 and abs(end[1] - target[1]) < 1):
                out = pl + out[1:] if out else pl
                target = pl[0]
                break
    return out


EVE_PATHS = lineage_paths(ANC_X[EVE], MOD_X)
ADAM_PATHS = lineage_paths(ANC_X[ADAM], [MOD_X[k] for k in range(8) if not MOD_F[k]])
EVE_TO_JN = chain_to(EVE_PATHS, MOD_X[JN_I])


def draw_paths(cx, paths, color, k, alpha=1.0, glow=True, up=False):
    """k in [0,3]: growth through depth levels; up=True grows from the descendants back to the ancestor."""
    if alpha <= 0.003 or k <= 0:
        return
    for lw, a in (((22, 0.12), (12, 0.25), (6.5, 1.0)) if glow else ((6.5, 1.0),)):
        cx.set_line_width(lw)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(cx, color, a * alpha)
        for pl, d in paths:
            dd = (2 - d) if up else d
            f = clamp(k - dd)
            if f <= 0:
                continue
            pts = pl[::-1] if up else pl
            n = max(2, int(len(pts) * ease_out(f)))
            cx.move_to(*pts[0])
            for p in pts[1:n]:
                cx.line_to(*p)
            cx.stroke()


def travel_light(cx, pl, u, color, alpha=1.0):
    if not pl or u <= 0 or u >= 1:
        return
    i = int(u * (len(pl) - 1))
    x, y = pl[i]
    cx.set_source(rgrad(cx, x, y, 0, 40, [(0, (1, 1, 1, 0.95 * alpha)), (0.4, (*color[:3], 0.6 * alpha)), (1, (*color[:3], 0))]))
    circle(cx, x, y, 40)
    cx.fill()


CLIP_TOP = 400
CLIP_BOT = 1395


def stage_clip(cx):
    cx.rectangle(0, CLIP_TOP, W, CLIP_BOT - CLIP_TOP)
    cx.clip()


def stage_edges(cx, col):
    """Soft fade at the top/bottom of a camera stage so nothing collides with header or captions."""
    for y0, y1, a0, a1 in ((CLIP_TOP, CLIP_TOP + 40, 1, 0), (CLIP_BOT - 110, CLIP_BOT, 0, 1)):
        cx.set_source(vgrad(cx, 0, y0, 0, y1, [(0, (*col[:3], a0)), (1, (*col[:3], a1))]))
        cx.rectangle(0, y0, W, y1 - y0)
        cx.fill()


def bg_africa(cx, t, cam):
    bg_purple(cx, t)
    cx.save()
    stage_clip(cx)
    apply_cam(cx, cam)
    asset("africa").draw(cx, 60, 380, 720, alpha=0.95)
    ui.draw_text(cx, "AFRICA", 905, 560, 38, hexc("#D2A48E"), spacing=3, alpha=0.9)
    cx.restore()


def apply_cam(cx, cam):
    x, y, zm = cam
    cx.translate(W / 2, 900)
    cx.scale(zm, zm)
    cx.translate(-x, -y)


def af_cam(t):
    ex, ey = ANC_X[EVE], ANC_Y
    jx, jy = MOD_X[JN_I], MOD_Y
    t_w = word_t("mt", "woman")
    t_only = word_t("trace", "only")
    keys = [
        (S("mt") - 0.4, (540.0, 1130.0, 1.4)),
        (S("mt") + 1.2, (540.0, 1080.0, 1.25)),
        (t_w + 0.2, (540.0, 900.0, 1.0)),
        (S("eve") - 0.1, (520.0, 880.0, 1.05)),
        (E("eve") + 0.3, (ex, ey + 80, 1.55)),
        (E("eve") + 0.31, (ex, ey + 40, 1.7)),           # (cut to Adam / card in between)
        (S("trace") + 0.4, (ex, ey + 40, 1.6)),
        (t_only + 0.3, (560.0, 820.0, 0.7)),
        (E("trace") - 0.2, (560.0, 830.0, 0.68)),
        (S("unbroken") + 0.25, (ex, ey + 120, 1.25)),
        (E("unbroken") - 0.1, (jx, jy - 120, 1.3)),
        (E("unbroken") + 1.0, (jx, jy - 120, 1.3)),
    ]
    return kf(t, keys, ease_io)


def draw_modern_row(cx, t, jn_expr=None, jn_glow=None, jn_glow_a=0.0, men_only=False):
    for k, x in enumerate(MOD_X):
        if k == JN_I:
            P.draw_badge(cx, x, MOD_Y, 56, "jn", glow=jn_glow, glow_a=jn_glow_a, expr=jn_expr)
            ui.pill(cx, "JUST NEEDY", x, MOD_Y + 86, 24, YELLOW)
        else:
            dim = 0.35 if (men_only and MOD_F[k]) else 1.0
            P.draw_badge(cx, x, MOD_Y, 50, "person", MOD_SPECS[k], alpha=dim)


def scene_africa(cx, t):
    cam = af_cam(t)
    bg_africa(cx, t, cam)
    cx.save()
    stage_clip(cx)
    apply_cam(cx, cam)
    t_w = word_t("mt", "woman")
    # mother's line: grows from today's people back up to one woman
    mt_k = 3 * ease_io(prog(t, S("mt") + 0.3, t_w + 0.2))
    if t >= S("trace") - 0.5:
        mt_k = 3
    draw_paths(cx, EVE_PATHS, PINK, mt_k, up=True)
    # everyone else alive at the time: lines that ended (Scene F, "not the only people")
    t_br = word_t("trace", "weren't")
    br = smooth(prog(t, t_br - 0.1, t_br + 1.2))
    crowd_a = smooth(prog(t, S("trace") + 0.4, word_t("trace", "only")))
    if crowd_a > 0:
        for (x, y, spec, r, ln, dx) in CROWD:
            draw_broken_line(cx, x, y + r, ln, dx, br)
            P.draw_badge(cx, x, y, r, "person", spec, alpha=crowd_a * 0.95)
    if br > 0:
        rnd = random.Random(9)
        for k, x in enumerate(ANC_X):
            if k == EVE:
                continue
            for j in range(2):
                draw_broken_line(cx, x, ANC_Y + 46, rnd.uniform(90, 300), rnd.uniform(-60, 60) + (j - 0.5) * 50, br)
    # unbroken: a light travels down Eve's line to Just Needy
    u = prog(t, S("unbroken") + 0.2, E("unbroken") - 0.15)
    travel_light(cx, EVE_TO_JN, ease_io(u), PINK)
    arrived = smooth(prog(t, E("unbroken") - 0.3, E("unbroken")))
    # ancient row
    eve_hi = smooth(prog(t, t_w - 0.2, t_w + 0.3))
    for k, x in enumerate(ANC_X):
        hi = eve_hi if k == EVE else 0
        P.draw_badge(cx, x, ANC_Y, 46 * (1 + 0.4 * hi), "person", ANC_SPECS[k], glow=PINK if hi > 0 else None,
                     glow_a=hi, ring=PINK if (k == EVE and hi > 0.5) else None)
    ea = smooth(prog(t, word_t("eve", "Mitochondrial") - 0.25, word_t("eve", "Mitochondrial") + 0.15))
    if t > S("trace") - 0.5:
        ea = 1.0
    ui.pill(cx, "Mitochondrial Eve", ANC_X[EVE], ANC_Y - 102, 32, PINK, fg=WHITE, alpha=ea)
    # today
    e = P.Expr((0, -0.8), 0.0, "smile")
    if arrived > 0.5:
        e = P.Expr((0, -0.3), 0.8, "grin")
    draw_modern_row(cx, t, jn_expr=e, jn_glow=PINK, jn_glow_a=arrived)
    cx.restore()
    stage_edges(cx, hexc("#251A33"))


def draw_broken_line(cx, x, y0, ln, dx, br):
    if br <= 0:
        return
    f = ease_out(br)
    ex, ey = x + dx * f, y0 + ln * f
    cx.set_dash([10, 9])
    cx.set_line_width(3.5)
    src(cx, (0.72, 0.7, 0.8, 0.8 * br))
    cx.move_to(x, y0)
    cx.curve_to(x, y0 + ln * 0.5 * f, ex, ey - ln * 0.4 * f, ex, ey)
    cx.stroke()
    cx.set_dash([])
    circle(cx, ex, ey, 8)
    src(cx, CORAL, br * clamp(f * 2 - 1))
    cx.fill()


def adam_cam(t):
    t_m = word_t("adam", "man:")
    return kf(t, [(S("adam") - 0.3, (540.0, 1130.0, 1.4)), (S("adam") + 1.0, (560.0, 1080.0, 1.25)),
                  (t_m + 0.2, (560.0, 900.0, 1.0)), (E("adam"), (ANC_X[ADAM] - 40, 860.0, 1.12)),
                  (E("adam") + 1, (ANC_X[ADAM] - 40, 860.0, 1.12))], ease_io)


def scene_adam(cx, t):
    """Father-to-son line: a different era, different people; only the men's line."""
    cam = adam_cam(t)
    bg_africa(cx, t, cam)
    cx.save()
    stage_clip(cx)
    apply_cam(cx, cam)
    t_m = word_t("adam", "man:")
    k = 3 * ease_io(prog(t, S("adam") + 0.3, t_m + 0.2))
    draw_paths(cx, ADAM_PATHS, BLUE, k, up=True)
    hi = smooth(prog(t, t_m - 0.2, t_m + 0.3))
    for i, x in enumerate(ANC_X):
        h = hi if i == ADAM else 0
        P.draw_badge(cx, x, ANC_Y, 46 * (1 + 0.4 * h), "person", ANC_SPECS_B[i], glow=BLUE if h > 0 else None,
                     glow_a=h, ring=BLUE if (i == ADAM and h > 0.5) else None)
    aa = smooth(prog(t, word_t("adam", "Y-chromosomal") - 0.25, word_t("adam", "Y-chromosomal") + 0.15))
    ui.pill(cx, "Y-chromosomal Adam", ANC_X[ADAM], ANC_Y - 102, 32, BLUE, fg=WHITE, alpha=aa)
    draw_modern_row(cx, t, jn_expr=P.Expr((0, -0.8), 0.0, "smile"), jn_glow=BLUE, jn_glow_a=hi, men_only=True)
    cx.restore()
    stage_edges(cx, hexc("#251A33"))


def scene_couple(cx, t):
    """Eve and Adam: not a couple, probably not even alive at the same time."""
    bg_purple(cx, t)
    s0 = S("couple")
    kin = ease_out(prog(t, s0 - 0.3, s0 + 0.35))
    xs = ((lerp(-200, 290, kin), ANC_SPECS[EVE], PINK, "Mitochondrial Eve"),
          (lerp(1280, 790, kin), ANC_SPECS_B[ADAM], BLUE, "Y-chromosomal Adam"))
    for x, spec, col, name in xs:
        P.draw_badge(cx, x, 700, 150, "person", spec, glow=col, glow_a=0.6, ring=col)
        ui.pill(cx, name.split(" ")[0], x, 905, 34, col, fg=WHITE)
        ui.pill(cx, name.split(" ")[1], x, 960, 34, col, fg=WHITE)
    # crossed-out heart
    k = smooth(prog(t, s0 + 0.15, s0 + 0.5))
    cx.save()
    cx.translate(W / 2, 700)
    sc = 0.6 + 0.4 * back_out(k)
    cx.scale(sc, sc)
    circle(cx, 0, 0, 56)
    src(cx, (0.05, 0.03, 0.08, 0.9 * k))
    cx.fill()
    cx.move_to(0, 22)
    cx.curve_to(-36, -2, -25, -34, 0, -16)
    cx.curve_to(25, -34, 36, -2, 0, 22)
    src(cx, WHITE, 0.95 * k)
    cx.fill()
    circle(cx, 0, 0, 56)
    src(cx, CORAL, k)
    cx.set_line_width(9)
    cx.stroke()
    cx.move_to(-40, 40)
    cx.line_to(40, -40)
    cx.stroke()
    cx.restore()
    # two different points on a timeline, sliding apart
    k2 = smooth(prog(t, word_t("couple", "probably") - 0.1, word_t("couple", "probably") + 0.4))
    sep = ease_io(prog(t, word_t("couple", "probably"), word_t("couple", "same") + 0.2))
    y = 1150
    cx.set_line_width(6)
    src(cx, (1, 1, 1, 0.6 * k2))
    cx.move_to(110, y)
    cx.line_to(970, y)
    cx.stroke()
    cx.move_to(975, y)
    cx.line_to(948, y - 16)
    cx.line_to(948, y + 16)
    cx.close_path()
    cx.fill()
    ui.draw_text(cx, "TIME", 970, y + 58, 30, WHITE, align="right", spacing=4, alpha=0.75 * k2)
    for x0, x1, col in ((520, 290, PINK), (560, 790, BLUE)):
        x = lerp(x0, x1, sep)
        circle(cx, x, y, 20)
        src(cx, col, k2)
        cx.fill()
        cx.set_line_width(4)
        src(cx, col, 0.6 * k2)
        cx.move_to(x, y - 24)
        cx.line_to(x, 1000)
        cx.stroke()
    ui.draw_text(cx, "different times", W / 2, y + 120, 40, WHITE, alpha=k2 * sep, shadow=1.0)


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
            ui.draw_text(cx, name, x, y, 38, WHITE, spacing=3, alpha=a, shadow=1.0)
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
    ui.pill(cx, label, sx, sy - stem - 2 * r - 28, 28, YELLOW, alpha=a)


# ================================================================== SCENE 6: closing shot
def _finale_arcs():
    g = asset("globe")
    rnd = random.Random(21)
    L = g.lights
    arcs = []
    for i in range(110):
        a = L[rnd.randrange(len(L))]
        b = L[rnd.randrange(len(L))]
        a = (math.degrees(a[0]), math.degrees(a[1]))
        b = (math.degrees(b[0]), math.degrees(b[1]))
        arcs.append((a, b))
    # illuminate region by region: sweep west -> east by the arc's start longitude
    arcs.sort(key=lambda ab: ((ab[0][0] + 200) % 360))
    return arcs


_FARCS = None


def finale_cam(t):
    s0 = S("end")
    return kf(t, [(s0 - 0.3, (540.0, 930.0, 2.2)), (s0 + 0.5, (540.0, 920.0, 2.05)),
                  (s0 + 3.2, (540.0, 900.0, 1.0)), (DUR, (540.0, 900.0, 0.97))], ease_io)


def scene_finale(cx, t):
    global _FARCS
    if _FARCS is None:
        _FARCS = _finale_arcs()
    bg_space(cx, t)
    g = asset("globe")
    s0 = S("end")
    cam = finale_cam(t)
    cx.save()
    cx.rectangle(0, CLIP_TOP, W, 1430 - CLIP_TOP)
    cx.clip()
    cx.translate(W / 2, 900)
    cx.scale(cam[2], cam[2])
    cx.translate(-cam[0], -cam[1])
    X, Y, R = W / 2, 680, 300
    lon0 = kf(t, [(s0 - 0.3, -5.0), (DUR, 22.0)], ease_io)
    lat0 = 20
    g.draw(cx, X, Y, R, lon0, lat0, lights=1.0, t=t)
    # the family network: connections light up region by region as the camera pulls back
    kk = prog(t, s0 - 0.2, word_t("end", "connected") + 0.4)
    n = len(_FARCS)
    for i, (a, b) in enumerate(_FARCS):
        d = i / n * 0.75
        f = ease_out(clamp((kk - d) / 0.25))
        if f <= 0:
            continue
        g.arc(cx, a, b, X, Y, R, lon0, lat0, frac=f, alpha=0.42, lw=2.0 / max(1.0, cam[2] * 0.7))
    # Just Needy, part of the picture: looks up at the network, a moment of surprise, then a smile
    t_c = word_t("end", "connected")
    t_th = word_t("end", "think.")
    if t < t_c - 0.3:
        e, tilt = P.Expr((0.15, -1.0), 0.2, "smile"), -0.06
    elif t < t_th - 0.1:
        e, tilt = P.Expr((0.0, -0.7), 1.0, "o"), -0.03
    else:
        e, tilt = P.Expr((0.0, 0.0), 0.3, "smile"), 0.0
    P.draw_jn_full(cx, W / 2, 1385, 500, t=t, expr=e, head_tilt=tilt)
    cx.restore()
    for y0, y1, a0, a1 in ((CLIP_TOP, CLIP_TOP + 50, 1, 0), (1380, 1430, 0, 1)):
        cx.set_source(vgrad(cx, 0, y0, 0, y1, [(0, (0.04, 0.07, 0.16, a0)), (1, (0.04, 0.07, 0.16, a1))]))
        cx.rectangle(0, y0, W, y1 - y0)
        cx.fill()


# ================================================================== timeline
def scene_spans():
    """(scene, start, end, transition-in)"""
    return [
        (scene_earth, 0.0, E("intro") + 0.25, "fade"),
        (scene_tree, E("intro") - 0.25, S("gen") + 0.2, "fade"),
        (scene_dna, S("gen") - 0.2, S("mt") + 0.2, "fade"),
        (scene_africa, S("mt") - 0.2, S("adam") + 0.3, "fade"),
        (scene_adam, S("adam") - 0.3, S("couple") + 0.2, "slide"),
        (scene_couple, S("couple") - 0.2, S("trace") + 0.2, "fade"),
        (scene_africa, S("trace") - 0.2, S("out") + 0.2, "fade"),
        (scene_map, S("out") - 0.3, S("think") + 0.15, "fade"),
        (scene_final, S("think") - 0.35, S("end") + 0.25, "fade"),
        (scene_finale, S("end") - 0.25, DUR + 1, "fade"),
    ]


def header_entries():
    t_dna = word_t("gen", "DNA")
    t_few = word_t("mrca", "few")
    return [
        (0.0, "WORLD POPULATION", pop_value, "", YELLOW),
        (word_t("hook_b", "your") - 0.1, "WHAT IF...", "we're all related?", "", YELLOW),
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
    """Captions sit above the Shorts UI overlay (bottom ~22%) and below the diagrams."""
    if t < S("par") - 0.3:
        return 1500
    if t < S("mt") - 0.2:
        return 1470
    if t < S("out") - 0.2:
        return 1455
    if t < S("think") - 0.2:
        return 1400
    return 1490


def render_frame(t):
    global HEADERS
    if HEADERS is None:
        HEADERS = header_entries()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    spans = [sp for sp in scene_spans() if sp[1] <= t < sp[2]]
    if len(spans) == 2 and spans[1][3] == "slide":
        k = ease_io(prog(t, spans[1][1], spans[0][2]))
        for (fn, a, b, kind), off in ((spans[0], -W * k), (spans[1], W * (1 - k))):
            cx.save()
            cx.translate(off, 0)
            fn(cx, t)
            cx.restore()
    else:
        for i, (fn, a, b, kind) in enumerate(spans):
            alpha = 1.0 if i == 0 else smooth(prog(t, a, a + 0.45))
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
        x0, y0, h0, e, _, _ = jn_opening(E("intro") - 0.25)
        h = lerp(h0, 150, k)
        y = lerp(y0, ROOT_Y + 75, k)
        P.draw_jn_full(cx, lerp(x0, W / 2, k), y, h, t=t, alpha=1 - smooth(prog(mk, 0.55, 1.0)),
                       expr=P.Expr((0, -0.8 * k), 0, "smile"))
    ui.header(cx, t, HEADERS)
    CAPS.draw(cx, t, caption_y(t), size=64)
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

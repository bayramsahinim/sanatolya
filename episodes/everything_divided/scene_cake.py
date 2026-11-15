"""Scene 1 - the Earth cake (hook)."""
import math
import random

import cairo

from cinecode.core import back_out, ease_in, ease_io, ease_out, kf, prog, smooth
from episodes.everything_divided.art_cake import Cake, knife
from episodes.everything_divided.common import (H, W, WHITE, YELLOW, L0, L1, header, word_t)

CAKE = Cake(X=540, Y=870, R=380, k=0.42, Hc=255)
WEDGE = (1.02, 1.22)            # your slice (front-right)
BASE = 0.37                      # angle of the first cut


def _chop_times():
    tA = word_t("hook1", "divided")
    tB = word_t("hook1", "billion")
    return [tA + (tB - tA) * k / 6.0 for k in range(6)], tA, tB


CHOPS, T_A, T_B = _chop_times()
T_PEOPLE_END = L1("hook1")
T_Q = L0("hook2")
T_SPLIT = L0("hook3")
T_OUT = L0("land1")             # scene hands over to the sky


def n_diam(t):
    k = sum(1 for c in CHOPS if t >= c + 0.16)
    if k == 0:
        return 0
    n = 2 ** (k - 1)
    if t > CHOPS[-1] + 0.3:     # flurry: the fan keeps densifying
        u = prog(t, CHOPS[-1] + 0.3, T_PEOPLE_END)
        n = int(32 * 2 ** (3 * u))
    return n


def slices(t):
    k = sum(1 for c in CHOPS if t >= c + 0.16)
    if k == 0:
        return 1
    if t <= CHOPS[-1] + 0.3:
        return 2 ** k
    u = smooth(prog(t, CHOPS[-1] + 0.3, T_PEOPLE_END - 0.05))
    return int(round(64 * (8e9 / 64) ** u))


def cut_angles(t):
    n = n_diam(t)
    out = []
    for i in range(n):
        a = BASE + i * math.pi / n
        out += [a, a + math.pi]
    return out


_BG = {}


def background(cx, t, tint=0.0):
    if "bg" not in _BG:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        g = cairo.RadialGradient(W / 2, H * 0.45, 50, W / 2, H * 0.5, H * 0.75)
        g.add_color_stop_rgb(0, 0.17, 0.2, 0.5)
        g.add_color_stop_rgb(0.55, 0.1, 0.11, 0.33)
        g.add_color_stop_rgb(1, 0.03, 0.04, 0.14)
        c.set_source(g)
        c.paint()
        rnd = random.Random(11)
        stars = []
        for _ in range(260):
            x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.choice([1.0, 1.2, 1.6, 2.2])
            a = rnd.uniform(0.15, 0.6)
            c.arc(x, y, r, 0, 2 * math.pi)
            c.set_source_rgba(0.85, 0.9, 1, a)
            c.fill()
            if rnd.random() < 0.12:
                stars.append((x, y, rnd.uniform(0, 6.28), rnd.uniform(2.5, 4.5)))
        _BG["bg"] = s
        _BG["tw"] = stars
    cx.set_source_surface(_BG["bg"], 0, 0)
    cx.paint()
    for x, y, ph, sz in _BG["tw"]:
        a = 0.5 + 0.5 * math.sin(t * 2.2 + ph)
        g = cairo.RadialGradient(x, y, 0, x, y, sz * 3)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.75 * a)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        cx.set_source(g)
        cx.arc(x, y, sz * 3, 0, 2 * math.pi)
        cx.fill()


def knife_state(t):
    """(tip_x, tip_y, angle, alpha, ghosts)."""
    rest = (CAKE.X - 175, CAKE.Y - 245)
    hit = (CAKE.X - 190, CAKE.Y + 20)
    ang = -0.3
    x, y = rest
    # gentle hover (present from the very first frame)
    y += math.sin(t * 3.0) * 8
    x += math.sin(t * 1.7) * 5
    ghosts = 0
    for c in CHOPS:
        if c - 0.14 <= t <= c + 0.3:
            if t < c:
                u = ease_in(prog(t, c - 0.14, c))
            else:
                u = 1 - ease_out(prog(t, c + 0.04, c + 0.3))
            x = x + (hit[0] - x) * u
            y = y + (hit[1] - y) * u
            ang = ang + 0.12 * u
    if CHOPS[-1] + 0.3 < t < T_PEOPLE_END + 0.1:
        # rapid flurry of strokes
        ph = (t - CHOPS[-1] - 0.3) * 7.5
        u = 0.5 - 0.5 * math.cos(ph * 2 * math.pi)
        x = rest[0] + (hit[0] - rest[0]) * u * 0.85 + math.sin(ph * 3.1) * 40
        y = rest[1] + (hit[1] - rest[1]) * u * 0.85
        ang = -0.3 + 0.2 * math.sin(ph * 2.3)
        ghosts = 2
    # leave
    lv = ease_in(prog(t, T_PEOPLE_END + 0.05, T_Q + 0.25))
    x += lv * 520
    y -= lv * 380
    return x, y, ang, 1.0, ghosts


def shake_amt(t):
    s = 0.0
    for c in CHOPS:
        s += math.exp(-max(0, t - c) * 18) * (1 if t >= c else 0)
    return s


def draw(cx, t):
    background(cx, t)
    # camera
    z = kf(t, [(0, 1.0), (T_Q, 1.06), (T_SPLIT + 0.25, 1.1), (T_OUT + 0.15, 2.6)], ease_io)
    wo = CAKE.wedge_offset(*WEDGE, 1.0)
    fx = kf(t, [(0, CAKE.X), (T_SPLIT + 0.25, CAKE.X), (T_OUT + 0.15, CAKE.X + wo[0] + 80)], ease_io)
    fy = kf(t, [(0, 930.0), (T_SPLIT + 0.25, 950.0), (T_OUT + 0.15, CAKE.Y + wo[1] + 40)], ease_io)
    sh = shake_amt(t) * 5
    cx.save()
    cx.translate(W / 2, 930 + sh)
    cx.scale(z, z)
    cx.translate(-fx, -fy)
    pull = back_out(prog(t, T_Q + 0.05, T_Q + 0.6), 1.2)
    flag = back_out(prog(t, T_Q + 0.45, T_Q + 0.9))
    angs = cut_angles(t)
    if pull > 0:
        angs = angs + [WEDGE[0], WEDGE[1]]
    n = n_diam(t)
    ca = 1.0 if n <= 16 else max(0.35, 16 / n * 1.6)
    CAKE.draw(cx, cut_angles=angs, cut_alpha=ca, wedge=WEDGE if pull > 0 else None, pull=pull, flag=flag)
    # knife (with motion ghosts during the flurry)
    kx, ky, ka, kal, gh = knife_state(t)
    if kx < W + 300:
        for g in range(gh, 0, -1):
            kx2, ky2, ka2, _, _ = knife_state(t - g * 0.018)
            cx.push_group()
            knife(cx, kx2, ky2, ka2, s=1.12)
            cx.pop_group_to_source()
            cx.paint_with_alpha(0.22 / g)
        knife(cx, kx, ky, ka, s=1.12)
    cx.restore()
    # header
    def count(tt):
        n_ = slices(tt)
        return f"{n_:,} SLICE" + ("S" if n_ != 1 else "")
    header(cx, t, [
        {"t0": -1, "t1": CHOPS[0] - 0.05, "kick": "THE EARTH CAKE", "main": "8 BILLION PEOPLE", "color": WHITE,
         "sub": "one equal share each"},
        {"t0": CHOPS[0] - 0.05, "t1": T_Q - 0.1, "kick": "THE EARTH CAKE", "main": count, "color": YELLOW,
         "sub": "one slice for every person on Earth"},
        {"t0": T_Q - 0.1, "t1": T_OUT - 0.25, "kick": "YOUR SLICE", "main": "WHAT DO YOU GET?", "color": WHITE,
         "sub": "1 of 8,000,000,000"},
    ])

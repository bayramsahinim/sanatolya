"""Just Needy: Zombie Apocalypse, Day 2 "The Cellar". Timeline, shots, sound, SRT, render.

usage:
  python -m episodes.zombie_day_2.film plan                 # print the timeline
  python -m episodes.zombie_day_2.film stills t1 t2 ...     # PNG stills to build/day2
  python -m episodes.zombie_day_2.film sheet                # contact sheet of the whole film
  python -m episodes.zombie_day_2.film audio                # soundtrack + SRT
  python -m episodes.zombie_day_2.film video [--draft]      # render + mux
"""
import functools
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys

import cairo
import numpy as np

from cinecode import audio as A
from cinecode.core import clamp, ellipse, fs, hexc, kf, line, noise1, prog, rrect, shade, smooth, src
from episodes.zombie_day_2 import draw as D
from episodes.zombie_day_2 import sets as S
from episodes.zombie_day_2 import voice as V
from episodes.zombie_day_2.script import LINES, SPEAKER, TEXT, TITLE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "day2")
OUTDIR = os.path.join(ROOT, "output")
W, H, FPS = D.W, D.H, D.FPS
SR = A.SR

# ============================================================ timeline
PLAN = [
    ("shot", "couch"), ("wait", 0.7), ("line", "n01", 0.0), ("line", "n02", 0.35), ("line", "n03", 0.3),
    ("wait", 0.5),
    ("shot", "knock"), ("wait", 1.0), ("line", "n04", 0.0), ("wait", 1.1),
    ("shot", "window"), ("wait", 0.55), ("line", "n05", 0.0), ("line", "n06", 0.35), ("line", "n07", 0.45),
    ("line", "n08", 0.3), ("wait", 0.9),
    ("shot", "pack"), ("wait", 0.15), ("line", "n09", 0.0), ("wait", 0.35),
    ("shot", "items"), ("wait", 0.1), ("line", "n10", 0.0), ("wait", 0.25),
    ("shot", "thumb"), ("wait", 0.1), ("line", "n11", 0.0), ("wait", 0.6),
    ("shot", "yard"), ("wait", 0.3), ("line", "n12", 0.0), ("wait", 0.35),
    ("shot", "door"), ("wait", 0.1), ("line", "n13", 0.0), ("wait", 0.3),
    ("shot", "tip"), ("wait", 0.1), ("line", "n14", 0.0), ("wait", 0.4),
    ("shot", "hatch"), ("wait", 0.1), ("line", "n15", 0.0), ("wait", 1.2),
    ("shot", "hatchopen"), ("wait", 0.15), ("line", "n16", 0.0), ("wait", 1.15),
    ("line", "n17", 0.0), ("wait", 0.6),
    ("shot", "close"), ("wait", 1.0), ("line", "n18", 0.0), ("line", "n19", 0.5), ("line", "s01", 0.7),
    ("line", "s02", 1.5), ("wait", 1.0),
    ("shot", "end"), ("wait", 2.6),
]


@functools.lru_cache(maxsize=None)
def timeline():
    dur = V.durations()
    t = 0.0
    T = {}
    shots = []
    for ev in PLAN:
        if ev[0] == "shot":
            shots.append([ev[1], t])
        elif ev[0] == "wait":
            t += ev[1]
        else:
            t += ev[2]
            T[ev[1]] = (t, t + dur[ev[1]])
            t = T[ev[1]][1]
    # mid-line cut: the hatch opens in the first third of n16, then we are in the cellar
    n16 = T["n16"]
    for sh in shots:
        if sh[0] == "close":
            close_i = shots.index(sh)
    shots.insert(close_i, ["descend", n16[0] + 0.36 * (n16[1] - n16[0])])
    total = t
    return T, [tuple(s) for s in shots], total


def shot_at(t):
    T, shots, total = timeline()
    cur = shots[0]
    for sh in shots:
        if t >= sh[1]:
            cur = sh
    i = shots.index(cur)
    end = shots[i + 1][1] if i + 1 < len(shots) else total
    return cur[0], cur[1], end


def blink(t, seed=0):
    p = (t + seed * 1.37) % 3.4
    return 1.0 if p < 0.11 else 0.0


def talkmask(t, T, lids):
    return 0.0


# ============================================================ shots
def zsil_walkers(t, t0):
    """Zombie silhouettes passing behind the window (yard, morning)."""
    def fg(cx, gy):
        for i, (z, x0, v, s, d) in enumerate(((D.CAST[1], 250, 70, 0.55, 1), (D.CAST[3], 1000, 55, 0.6, -1),
                                               (D.CAST[0], -200, 60, 0.5, 1), (D.CAST[5], 1300, 75, 0.52, -1))):
            tt = t - t0 - i * 1.4
            x = x0 + d * v * tt
            D.zombie(cx, z, x, gy, s, t + i, face_dir=d, sil=(0.16, 0.14, 0.13, 0.92))
    return fg


def shot_couch(cx, t, st, en, T):
    lt = t - st
    z = 1.0 + 0.05 * smooth(prog(t, st, en))
    cx.save()
    cx.translate(W / 2, H * 0.55)
    cx.scale(z, z)
    cx.translate(-W / 2, -H * 0.55)
    S.living_room(cx, t, draw_fg=zsil_walkers(t, st - 2.0))
    S.couch_back(cx, 540, 1040, 1020, 300)
    look = (0, -0.5) if T["n01"][0] < t < T["n01"][1] + 0.6 else (0.0, 0.2)
    expr = "worried"
    if t >= T["n02"][0] - 0.1:
        expr = "tired"
    if t >= T["n03"][0]:
        expr = "flat"
        look = (0, 0)
    # glance back at the window when a silhouette passes
    turn = 0.0
    D.hero(cx, 540, 1720, 1.22, expr=expr, t=t, crouch=0.95, look=look, blink=blink(t),
           arm_l=(0.25, 0.75), arm_r=(-0.25, -0.75), shiver=0.6 if expr != "flat" else 0.2, turn=turn,
           tilt=0.05 * math.sin(t * 0.8))
    cx.restore()
    S.vignette(cx, 0.5)
    # DAY 2 identifier
    a = smooth(prog(lt, 0.25, 0.65)) * (1 - smooth(prog(lt, 2.6, 3.1)))
    if a > 0:
        y = 170 - 20 * (1 - smooth(prog(lt, 0.25, 0.7)))
        D.label(cx, "DAY 2", W / 2, y, 64, fill=D.WHITE, outline=D.INK, ow=8, alpha=a, spacing=14)
        w = 120 * smooth(prog(lt, 0.4, 0.9))
        for side in (-1, 1):
            line(cx, [(W / 2 + side * 150, y), (W / 2 + side * (150 + w), y)], (*D.YEL[:3], a), 5)


def shot_knock(cx, t, st, en, T):
    lt = t - st
    push = smooth(prog(t, T["n04"][1] - 0.2, en))
    z = 1.0 + 0.9 * push
    cx.save()
    cx.translate(610, 640)
    cx.scale(z, z)
    cx.translate(-610, -640)
    knock_t = [0.2, 0.42, 0.64]

    def fg(cx2, gy):
        # mailman silhouette at the glass, knocking
        k = max([math.exp(-max(0, lt - kt) * 10) if lt >= kt else 0 for kt in knock_t])
        D.zombie(cx2, D.MAILMAN, 640, gy + 120, 0.95, t, face_dir=-1, walking=False,
                 arms=((-0.4, -0.2), (-2.2 + 0.5 * k, -2.6 + 0.5 * k)), sil=(0.15, 0.13, 0.12, 0.95))
    S.living_room(cx, t, draw_fg=fg)
    S.couch_back(cx, 540, 1040, 1020, 300)
    # hero: startled jump, then tiptoes left, staring at the window
    jump = math.sin(math.pi * clamp((lt - 0.22) / 0.4)) if lt < 0.62 else 0
    x = 540 - 260 * smooth(prog(t, T["n04"][0] + 0.3, en))
    walking = T["n04"][0] + 0.3 < t < en
    D.hero(cx, x, 1720 - 140 * jump, 1.22, expr="shock" if lt < 1.2 else "scared", t=t,
           crouch=0.95 * (1 - smooth(prog(lt, 0.2, 0.5))) + 0.25, look=(0.3, -1), blink=blink(t, 2),
           walk=(t * 5.0) if walking else None, arm_l=(1.5, 2.2) if lt < 1.0 else None,
           arm_r=(-1.5, -2.2) if lt < 1.0 else None, tilt=-0.08)
    cx.restore()
    S.vignette(cx, 0.5)


def mailman_package(lt_lift):
    def hold(cx, hands):
        hx, hy = hands[1]
        lift = smooth(lt_lift)
        D.package(cx, hx - 30, hy - 40 - 30 * lift, 260, 190, -0.12 + 0.1 * lift)
    return hold


def shot_window(cx, t, st, en, T):
    lt = t - st
    rise = D.pop_scale(t, st, 0.45)
    n06 = T["n06"]
    left_at = n06[0] + 0.62 * (n06[1] - n06[0])
    lost = (t - left_at) if t >= left_at else None
    lift = prog(t, T["n07"][0] + 0.2, T["n07"][0] + 0.7)
    tap = 0.0
    for k in range(3):
        tk = T["n07"][0] + 0.9 + k * 0.28
        if t >= tk:
            tap = max(tap, math.exp(-(t - tk) * 12))

    def fg(cx2, gy):
        y_off = 700 * (1 - rise)
        lifted = smooth(lift) - 0.04 * tap

        D.zombie(cx2, D.MAILMAN, 500, gy + 620 + y_off, 2.2, t, face_dir=1, walking=False,
                 arms=((-0.2, 1.3 + 0.3 * lifted), (-0.9 - 0.2 * lifted, -1.6 - 0.4 * lifted)),
                 look=(1, 0.3), lost_left=lost,
                 jaw=0.5 + 0.5 * math.sin(t * 6) ** 2 if t < T["n05"][1] else None)
        # the package, pushed up against the glass for "still holding my package"
        sc = 1.0 + 0.25 * lifted
        D.package(cx2, 560, 1040 + y_off - 70 * lifted, 300 * sc, 210 * sc, -0.08 + 0.1 * lifted)

    S.window(cx, 90, 280, 900, 980, t, draw_fg=fg, curtains=False)
    S.striped_wall(cx, 0, 1330, W, H)
    cx.rectangle(0, 0, W, 230)
    S.striped_wall(cx, 0, 0, W, 230)
    cx.rectangle(0, 0, 60, H)
    src(cx, S.WALL)
    cx.fill()
    cx.rectangle(1020, 0, 60, H)
    cx.fill()
    S.window(cx, 90, 280, 900, 980, t, draw_fg=fg, curtains=False)  # redraw frame on top of walls
    # hero, foreground right, staring at the mailman
    if t < T["n05"][0] + 0.5:
        expr = "shock"
    elif t < T["n07"][0]:
        expr = "scared"
    else:
        expr = "confused"
    rec = smooth(prog(lt, 0.0, 0.5))
    D.hero(cx, 860 + 300 * (1 - rec), 2350, 1.75, expr=expr, t=t, turn=-0.7, look=(-1, -0.3),
           blink=blink(t, 4), tilt=0.12 if expr == "confused" else -0.05,
           arm_l=(0.3, 0.2), arm_r=(0.1, 0.0))
    S.vignette(cx, 0.45)
    # five stars
    n08 = T["n08"]
    for k in range(5):
        tk = n08[0] + 0.12 + k * 0.13
        sc = D.pop_scale(t, tk, 0.3)
        if sc > 0:
            star(cx, 180 + k * 180, 160, 64 * sc)


def star(cx, x, y, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    cx.close_path()
    fs(cx, D.YEL, D.YEL_D, max(3, r * 0.12))


def shot_pack(cx, t, st, en, T):
    lt = t - st
    n09 = T["n09"]
    grab = smooth(prog(t, n09[0] - 0.1, n09[0] + 0.35))
    slam = prog(t, n09[0] + 0.6, n09[0] + 0.8)
    S.kitchen(cx, t, table=False)
    D.hero(cx, 540, 1560, 1.2, expr="confident" if lt > 0.5 else "shock", t=t, blink=blink(t, 6),
           arm_l=(1.2 - 0.6 * slam, 2.0 - 0.6 * slam), arm_r=(-1.2 + 0.6 * slam, -2.0 + 0.6 * slam),
           look=(0, 0.6))
    S.kitchen_table(cx, 540, 1430, 860)
    bx = 1300 - 760 * grab
    by = 1040 + 300 * smooth(slam)
    opn = smooth(prog(t, n09[0] + 0.9, n09[1] + 0.2))
    D.backpack(cx, bx, by, 1.15, open_=opn, rot=0.4 * (1 - grab))
    S.vignette(cx, 0.45)


ITEMS = ("cookie", "cookie", "charger", "sock")


def draw_item(cx, name, x, y, s, rot=0.0):
    if name == "cookie":
        D.cookie(cx, x, y, 70 * s, rot)
    elif name == "cookies":
        D.cookie(cx, x - 80 * s, y + 10 * s, 70 * s, rot)
        D.cookie(cx, x + 80 * s, y - 10 * s, 70 * s, rot + 1)
    elif name == "charger":
        D.charger(cx, x - 40 * s, y - 40 * s, s * 1.1, rot)
    else:
        D.sock(cx, x - 20 * s, y, s * 1.05, rot)


def kit_panel(cx, t, filled, y=120, alpha=1.0):
    """SURVIVAL KIT inventory: filled = list of (item, time filled)."""
    if alpha <= 0:
        return
    cx.push_group()
    rrect(cx, 90, y, 900, 330, 34)
    fs(cx, (0.09, 0.08, 0.07, 0.82), D.YEL, 5)
    D.label(cx, "SURVIVAL KIT", W / 2, y + 70, 58, fill=D.YEL, outline=D.INK, ow=7, shadow=False)
    for k in range(4):
        x = 150 + k * 205
        rrect(cx, x, y + 135, 165, 165, 22)
        fs(cx, (1, 1, 1, 0.08), (1, 1, 1, 0.45), 3)
    for k, (name, tf) in enumerate(filled):
        if t < tf:
            continue
        sc = D.pop_scale(t, tf, 0.3)
        draw_item(cx, name, 150 + k * 205 + 82, y + 217, 0.62 * sc)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def kit_times(T):
    n10 = T["n10"]
    b = V.inner_beats("n10", 3, (0.0, 0.36, 0.70))
    return [n10[0] + b[0] + 0.05, n10[0] + b[0] + 0.3, n10[0] + b[1] + 0.05, n10[0] + b[2] + 0.1]


def shot_items(cx, t, st, en, T):
    kt = kit_times(T)
    S.tabletop_close(cx, t)
    # current close-up: cookies, charger, sock, each a quick cut with a pop
    beats = [(kt[0], "cookies"), (kt[2], "charger"), (kt[3], "sock")]
    cur = beats[0]
    for b in beats:
        if t >= b[0] - 0.05:
            cur = b
    sc = D.pop_scale(t, cur[0] - 0.05, 0.28)
    wob = 0.06 * math.sin((t - cur[0]) * 9) * math.exp(-(t - cur[0]) * 3)
    draw_item(cx, cur[1], W / 2, 1180, 2.6 * max(sc, 0.01), wob)
    kit_panel(cx, t, list(zip(ITEMS, kt)), y=150)
    S.vignette(cx, 0.4)


def shot_thumb(cx, t, st, en, T):
    lt = t - st
    S.kitchen(cx, t, table=False)
    up = smooth(prog(lt, 0.15, 0.45))
    D.hero(cx, 540, 1640, 1.3, expr="confident", t=t, blink=blink(t, 1),
           arm_r=(0.2 + 1.75 * up, 0.1 + 2.95 * up), hand_r="thumb" if up > 0.6 else "dot",
           arm_l=(0.2, 0.15), tilt=0.06)
    S.kitchen_table(cx, 540, 1470, 900)
    for (name, x, rot) in (("cookie", 250, 0.2), ("cookie", 360, 1.0), ("charger", 560, 0.1), ("sock", 790, -0.4)):
        draw_item(cx, name, x, 1420, 0.55, rot)
    # sparkle on the thumb
    sp = D.pop_scale(t, st + 0.5, 0.3) * (1 - smooth(prog(lt, 1.1, 1.5)))
    if sp > 0:
        star(cx, 420, 830, 40 * sp)
    kit_panel(cx, t, list(zip(ITEMS, [0, 0, 0, 0])), y=150, alpha=1 - smooth(prog(t, en - 0.4, en)))
    S.vignette(cx, 0.4)


YARD = [  # (zombie, x0, ground y, scale, dir, speed px/s)
    (D.CAST[5], 900, 1290, 0.42, -1, 22),
    (D.CAST[0], 120, 1350, 0.5, 1, 30),
    (D.CAST[1], 820, 1440, 0.6, -1, 26),
    (D.CAST[2], 60, 1570, 0.72, 1, 44),
    (D.CAST[3], 1000, 1700, 0.85, -1, 36),
    (D.CAST[4], 160, 1880, 1.02, 1, 28),
]


def shot_yard(cx, t, st, en, T):
    lt = t - st
    z = 1.0 + 0.06 * smooth(prog(t, st, en))

    def fg(cx2):
        for i, (zz, x0, gy, s, d, v) in enumerate(YARD):
            x = x0 + d * v * lt * (1 + 0.25 * math.sin(lt * 0.9 + i))
            D.zombie(cx2, zz, x, gy, s, t + i * 0.7, face_dir=d, phase=lt * zz.speed * 3.2 + i * 1.9)
    cx.save()
    cx.translate(W / 2, H * 0.6)
    cx.scale(z, z)
    cx.translate(-W / 2, -H * 0.6)
    S.farm_exterior(cx, t, draw_fg=fg)
    cx.restore()
    S.vignette(cx, 0.45)


DOOR_BANGS = (0.05, 0.5, 0.78, 1.32, 1.55, 2.05)


def door_bang(t, st):
    b = 0.0
    for k in DOOR_BANGS:
        tk = st + k
        if t >= tk:
            b = max(b, math.exp(-(t - tk) * 9))
    return b


def shot_door(cx, t, st, en, T):
    lt = t - st
    b = door_bang(t, st)
    cx.save()
    sh = (noise1(t * 40, 2) * 14 * b, noise1(t * 40, 7) * 10 * b)
    cx.translate(*sh)

    def hands(cx2):
        for k, (x, y, rot) in enumerate(((-90, -800, 0.3), (60, -850, -0.2), (-10, -760, 0.05))):
            press = 6 * b
            cx2.save()
            cx2.translate(x, y - press * (k + 1))
            cx2.rotate(rot)
            ellipse(cx2, 0, 0, 38, 46)
            src(cx2, (0.18, 0.2, 0.15, 0.9))
            cx2.fill()
            for f in range(4):
                line(cx2, [(-24 + f * 16, -20), (-30 + f * 20, -80 - 6 * (f % 2))], (0.18, 0.2, 0.15, 0.9), 13)
            cx2.restore()
    S.front_door(cx, t, bang=b, cracks=0.6 + 0.4 * b, draw_hands=hands)
    x = 760 + 170 * smooth(prog(lt, 0.2, 1.6))
    D.hero(cx, x, 1840, 1.15, expr="scared", t=t, look=(-1, -0.2), turn=-0.5, blink=blink(t, 3),
           walk=lt * 6 if 0.2 < lt < 1.6 else None, arm_l=(-1.0, -2.6), arm_r=(1.0, 2.6), shiver=0.6)
    cx.restore()
    S.vignette(cx, 0.5)


def shot_tip(cx, t, st, en, T):
    lt = t - st
    n14 = T["n14"]
    d14 = n14[1] - n14[0]
    S.front_door(cx, t, bang=door_bang(t, st - 2.6) * 0.5, cracks=0.8)
    src(cx, (0.05, 0.04, 0.03, 0.6 * smooth(prog(lt, 0, 0.3))))
    cx.paint()
    up = D.pop_scale(t, st, 0.4)
    cx.save()
    cx.translate(W / 2, 1000 + 900 * (1 - min(1, up)))
    cx.rotate(-0.03)
    rrect(cx, -430, -560, 860, 1120, 16)
    fs(cx, hexc("#f4efe3"), D.INK, 5)
    for x in (-160, 160):  # tape
        cx.save()
        cx.translate(x, -560)
        cx.rotate(0.2 if x < 0 else -0.2)
        cx.rectangle(-60, -22, 120, 44)
        src(cx, (0.95, 0.9, 0.7, 0.8))
        cx.fill()
        cx.restore()
    pen = (0.15, 0.15, 0.17, 1)

    def draw_part(pts, a, b, col=pen, lw=9):
        f = smooth(prog(t, n14[0] + a * d14, n14[0] + b * d14))
        if f <= 0:
            return
        L = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
        left = L * f
        out = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            dd = math.dist(p, q)
            if left >= dd:
                out.append(q)
                left -= dd
            else:
                r = left / dd if dd else 0
                out.append((p[0] + (q[0] - p[0]) * r, p[1] + (q[1] - p[1]) * r))
                break
        line(cx, out, col, lw)

    # house plan
    draw_part([(-300, -150), (-300, 380), (300, 380), (300, -150), (0, -400), (-300, -150), (300, -150)], 0.0, 0.2)
    # exit 1 (front): door + red X
    draw_part([(-90, 380), (-90, 220), (40, 220), (40, 380)], 0.12, 0.22)
    draw_part([(-120, 190), (70, 410)], 0.22, 0.27, hexc("#d23b2f"), 16)
    draw_part([(70, 190), (-120, 410)], 0.27, 0.32, hexc("#d23b2f"), 16)
    # exit 2 (back, side): green arrow out + check
    draw_part([(300, 60), (300, 200)], 0.3, 0.36, hexc("#f4efe3"), 16)
    draw_part([(120, 130), (420, 130)], 0.36, 0.48, hexc("#2e9a4a"), 14)
    draw_part([(380, 95), (420, 130), (380, 165)], 0.46, 0.5, hexc("#2e9a4a"), 14)
    draw_part([(330, -60), (360, -25), (420, -110)], 0.5, 0.56, hexc("#2e9a4a"), 14)
    # second sentence: a little figure enters, the escape path is traced back out
    draw_part([(-200, 40), (-200, -40)], 0.6, 0.64, pen, 7)
    ellipse(cx, -200, -70, 26 * smooth(prog(t, n14[0] + 0.58 * d14, n14[0] + 0.62 * d14)), 26 * smooth(
        prog(t, n14[0] + 0.58 * d14, n14[0] + 0.62 * d14)))
    fs(cx, None, pen, 6)
    f = smooth(prog(t, n14[0] + 0.66 * d14, n14[0] + 0.95 * d14))
    if f > 0:
        cx.set_dash([18, 14])
        draw_part([(-200, 60), (-200, 130), (120, 130)], 0.66, 0.95, hexc("#e0a32a"), 8)
        cx.set_dash([])
    cx.restore()
    S.vignette(cx, 0.4)


def shot_hatch(cx, t, st, en, T):
    lt = t - st
    n15 = T["n15"]
    z = 1.0 + 0.05 * smooth(prog(t, st, en))
    cx.save()
    cx.translate(W / 2, H * 0.7)
    cx.scale(z, z)
    cx.translate(-W / 2, -H * 0.7)
    S.kitchen(cx, t, table=False, hatch=lambda c: S.hatch_floor(c, 400, 1450, 360, 170))
    look_cam = n15[1] + 0.35 < t < n15[1] + 0.85
    D.hero(cx, 820, 1830, 1.15, expr="worried" if not look_cam else "flat", t=t, blink=blink(t, 5),
           turn=0.0 if look_cam else -0.55, look=(0, 0) if look_cam else (-1, 0.8), arm_l=(0.7, 1.9),
           arm_r=(-0.2, -0.2), shiver=0.4)
    cx.restore()
    S.vignette(cx, 0.5)
    bt = n15[1] - 0.05
    sc = D.pop_scale(t, bt, 0.32)
    if sc > 0:
        D.label(cx, "BAD IDEA", W / 2 - 60, 1080 + noise1(t * 20, 4) * 4, 118, rot=-0.05, scale=sc)


def shot_hatchopen(cx, t, st, en, T):
    n16 = T["n16"]
    o = smooth(prog(t, st + 0.1, en - 0.05))
    cx.save()
    cx.translate(W / 2, H * 0.68)
    cx.scale(1.55, 1.55)
    cx.translate(-400, -1520)
    S.kitchen(cx, t, table=False, hatch=lambda c: S.hatch_floor(c, 400, 1450, 360, 170, open_=o))
    cx.restore()
    # the hero's hand pulling the ring, from the right
    hand_y = 1300 - 420 * o
    D.sleeve(cx, [(1180, 1150), (900, hand_y + 40), (760, hand_y)], 70)
    D.hand_dot(cx, 760, hand_y, 30)
    S.vignette(cx, 0.6)


def cellar_cam(cx, fx, fy, zoom):
    cx.translate(W / 2, H / 2)
    cx.scale(zoom, zoom)
    x = clamp(fx, W / 2 / zoom, S.CELLAR_W - W / 2 / zoom)
    y = clamp(fy, H / 2 / zoom, H - H / 2 / zoom)
    cx.translate(-x, -y)


def descend_state(t, T):
    n16 = T["n16"]
    st = n16[0] + 0.36 * (n16[1] - n16[0])
    f = smooth(prog(t, st, n16[1] - 0.15))
    close_t = n16[1] - 0.05
    hatch = 1.0 - smooth(prog(t, close_t, close_t + 0.25))
    flash_t = close_t + 0.75
    flash = 1.0 if t >= flash_t else 0.0
    return f, hatch, flash, close_t, flash_t


def shot_descend(cx, t, st, en, T):
    f, hatch, flash, close_t, flash_t = descend_state(t, T)
    if f < 1:
        gx, gy = S.stair_point(f)
        walking = True
    else:
        gx, gy = S.stair_point(1.0)
        gx += 160 * smooth(prog(t, T["n16"][1], T["n17"][0]))
        gy = 1600
        walking = T["n16"][1] < t < T["n17"][0]
    # beam sweep: from right side shelves, settle on the shelves
    ang = -0.15 + 0.5 * math.sin(clamp(t - flash_t, 0, 2.0) * 1.6) * math.exp(-(t - flash_t) * 0.7) \
        if t > flash_t else 0.2
    cx.save()
    zoom = 1.15
    cellar_cam(cx, gx + 120, gy - 360, zoom)
    S.cellar(cx, t, hatch_open=hatch)
    expr = "worried"
    if t > T["n17"][0]:
        expr = "relieved"
    out = D.hero(cx, gx, gy, 0.95, expr=expr, t=t, blink=blink(t, 2), walk=t * 4.6 if walking else None,
                 arm_r=(-1.2 - ang * 0.6, -1.5 - ang), arm_l=(0.3, 0.2), look=(0.6, 0.2))
    hx, hy = out["arm_r"]
    D.flashlight(cx, hx, hy, -math.pi / 2 + 1.5 + ang * 0.9, 0.9, on=flash > 0)
    beam_ang = ang * 0.9 + 0.07
    lights = []
    if hatch > 0.01:
        lights.append(("cone", 285, 140, 1.25, 0.32, 1500, hatch))
        lights.append(("glow", 285, 170, 380, 0.6 * hatch))
        lights.append(("glow", gx, gy - 260, 430, 0.55 * hatch))
    if flash:
        lights.append(("cone", hx + 30, hy, beam_ang, 0.26, 1500, 1.0))
        lights.append(("glow", hx, hy, 330, 0.75))
    S.darkness(cx, 0.95, lights)
    cx.restore()
    S.vignette(cx, 0.55)


def shot_close(cx, t, st, en, T):
    lt = t - st
    s02 = T["s02"]
    flick = 1.0
    if t > s02[0] + 0.3:
        # flashlight flickers, harder towards the end
        k = noise1(t * 22, 13)
        rate = prog(t, s02[0] + 0.3, en)
        if k < -0.4 + 0.9 * rate:
            flick = 0.1 + 0.2 * max(0, noise1(t * 50, 3))
    cx.save()
    cellar_cam(cx, 1050, 1250, 1.9)
    S.cellar(cx, t)
    turn = -0.85 * smooth(prog(t, T["n19"][0] - 0.2, T["n19"][0] + 0.9))
    if t < st + 0.6:
        expr = "relieved"
    elif t < T["n18"][1] - 0.2:
        expr = "worried"
    else:
        expr = "terror"
    out = D.hero(cx, 980, 1720, 0.95, expr=expr, t=t, blink=blink(t, 7) if expr != "terror" else 0,
                 turn=turn, look=(-1 if turn < -0.3 else 0.5, 0), arm_r=(-1.35, -1.6), arm_l=(0.3, 0.2),
                 shiver=0.8 if expr == "terror" else 0.0)
    hx, hy = out["arm_r"]
    D.flashlight(cx, hx, hy, -math.pi / 2 + 1.5, 0.9, on=flick > 0.5)
    lights = [("cone", hx + 30, hy, 0.07, 0.26, 1500, flick), ("glow", hx - 40, hy - 120, 380, 0.8 * flick)]
    S.darkness(cx, 0.965, lights)
    cx.restore()
    S.vignette(cx, 0.6)


def shot_end(cx, t, st, en, T):
    src(cx, (0, 0, 0, 1))
    cx.paint()
    a = smooth(prog(t, st + 0.6, st + 1.0))
    D.label(cx, "PART 3", W / 2, H / 2, 64, fill=D.YEL, outline=None, alpha=a, spacing=6, shadow=False)


SHOTS = {"couch": shot_couch, "knock": shot_knock, "window": shot_window, "pack": shot_pack, "items": shot_items,
         "thumb": shot_thumb, "yard": shot_yard, "door": shot_door, "tip": shot_tip, "hatch": shot_hatch,
         "hatchopen": shot_hatchopen, "descend": shot_descend, "close": shot_close, "end": shot_end}


def render_frame(t):
    T, _, _ = timeline()
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(sf)
    src(cx, (0, 0, 0, 1))
    cx.paint()
    name, st, en = shot_at(t)
    SHOTS[name](cx, t, st, en, T)
    # tiny dip at cuts
    return sf


# ============================================================ sound
def knock():
    out = np.zeros(int(0.25 * SR))
    tt = A.t_arr(0.25)
    out += np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 70) * 0.5
    out += np.sin(2 * np.pi * 2700 * tt) * np.exp(-tt * 90) * 0.3
    out += A.bp(A.noise(0.25, 71), 600, 3000) * np.exp(-tt * 60) * 0.5
    out += np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 40) * 0.4
    return A.norm(out, 0.8)


def groan(seed, d=1.6, f0=95):
    tt = A.t_arr(d)
    r = np.random.default_rng(seed)
    vib = 1 + 0.04 * np.sin(2 * np.pi * (4 + r.random() * 2) * tt) + 0.02 * np.sin(2 * np.pi * 0.7 * tt)
    f = f0 * (1 + 0.15 * r.random()) * vib * (1 - 0.15 * tt / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = (ph / (2 * np.pi)) % 1 * 2 - 1
    x = A.bp(saw, 250, 900) * 0.8 + A.bp(A.noise(d, seed), 300, 1500) * 0.35
    env = np.minimum(1, tt / 0.25) * np.minimum(1, (d - tt) / 0.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 1.3 * tt))
    return A.norm(x * env, 0.7)


def breath(d=1.4, seed=3, inhale=True):
    tt = A.t_arr(d)
    x = A.bp(A.noise(d, seed), 400, 2600)
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** (1.5 if inhale else 0.8)
    return A.norm(x * env, 0.5)


def zipper(d=0.6):
    out = np.zeros(int(d * SR))
    t = 0.0
    k = 0
    while t < d - 0.01:
        c = A.hp(A.noise(0.006, 80 + k), 2500) * np.exp(-A.t_arr(0.006) * 600)
        A.add(out, c * 0.7, t)
        t += 0.012 + 0.006 * math.sin(k)
        k += 1
    return A.norm(out, 0.6)


def stair_creak(seed):
    c = A.sfx_creak()
    s = A.sfx_step(seed, heavy=True)
    out = np.zeros(max(len(c), len(s)))
    out[:len(s)] += s
    out[:len(c)] += c * 0.25
    return out


def bang():
    return A.norm(A.sfx_thud(55, 0.45) + A.sfx_crash_wood()[: int(0.45 * SR)] * 0.25, 0.95)


def plop():
    return A.norm(A.sfx_thud(140, 0.2) + A.lp(A.noise(0.2, 9), 900) * np.exp(-A.t_arr(0.2) * 25) * 0.6, 0.6)


def boom(d=2.5):
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * 42 * tt) * np.exp(-tt * 1.6) + A.lp(A.noise(d, 5), 200) * np.exp(-tt * 2.5) * 0.6
    return A.norm(x, 0.9)


def flicker_buzz(d=1.0):
    tt = A.t_arr(d)
    x = np.sign(np.sin(2 * np.pi * 120 * tt)) * 0.15 * (np.random.default_rng(4).random(len(tt)) > 0.6)
    return A.lp(x, 2500) * 0.5


def sfx_events():
    T, shots, total = timeline()
    st = {n: s for n, s in shots}
    ev = []
    ev += [(0.0, groan(1, 2.2, 85), 0.18), (2.6, groan(2, 1.8, 105), 0.14), (4.8, groan(5, 2.0, 92), 0.15)]
    for k in (0.2, 0.42, 0.64):
        ev.append((st["knock"] + k, knock(), 0.75))
    ev.append((st["knock"] + 0.25, A.get_sfx("boing"), 0.25))
    ev.append((st["window"] + 0.05, A.sfx_whoosh(0.35, 200, 1200), 0.35))
    ev.append((st["window"] + 0.15, groan(7, 1.6, 78), 0.45))
    n06 = T["n06"]
    ev.append((n06[0] + 0.62 * (n06[1] - n06[0]) + 0.35, plop(), 0.55))
    for k in range(3):
        ev.append((T["n07"][0] + 0.9 + k * 0.28, knock() * 0.6, 0.45))
    for k in range(5):
        ev.append((T["n08"][0] + 0.12 + k * 0.13, A.glock(79 + [0, 2, 4, 7, 9][k], 0.6), 0.5))
    n09 = T["n09"]
    ev.append((n09[0] - 0.1, A.sfx_whoosh(0.35), 0.4))
    ev.append((n09[0] + 0.7, A.sfx_thud(110, 0.3), 0.6))
    ev.append((n09[0] + 0.9, zipper(0.7), 0.5))
    for k, tk in enumerate(kit_times(T)):
        ev.append((tk - 0.05, A.sfx_pop(), 0.45))
        ev.append((tk, A.sfx_thud(170, 0.15), 0.35))
    ev.append((kit_times(T)[3] + 0.1, A.get_sfx("wah"), 0.22))
    ev.append((st["thumb"] + 0.5, A.sfx_ding(), 0.4))
    ev.append((st["thumb"] + 0.5, A.sfx_sparkle(), 0.3))
    for i in range(6):
        ev.append((st["yard"] + 0.2 + i * 0.55, groan(20 + i, 1.5 + 0.3 * (i % 3), 80 + 9 * i), 0.3))
        ev.append((st["yard"] + 0.4 + i * 0.47, A.sfx_step(i, heavy=True), 0.2))
    for k in DOOR_BANGS:
        ev.append((st["door"] + k, bang(), 0.75))
    ev.append((st["door"] + 0.3, groan(40, 2.0, 88), 0.35))
    for k in DOOR_BANGS[:3]:
        ev.append((st["tip"] - 2.6 + k + 2.6 + 0.6, bang() * 0.4, 0.3))
    ev.append((st["tip"], A.sfx_whoosh(0.3, 400, 2000), 0.3))
    ev.append((T["n15"][1] - 0.05, A.sfx_dun(), 0.45))
    ev.append((T["n15"][1] + 0.7, A.sfx_gulp(), 0.5))
    ev.append((st["hatchopen"] + 0.1, A.sfx_creak(), 0.6))
    f0 = st["descend"]
    _, _, _, close_t, flash_t = descend_state(f0, T)
    n = 7
    for k in range(n):
        ev.append((f0 + 0.1 + k * (close_t - f0 - 0.2) / n, stair_creak(k), 0.45))
    ev.append((close_t, A.sfx_thud(60, 0.5), 0.8))
    ev.append((close_t + 0.05, A.sfx_creak(), 0.25))
    ev.append((flash_t, A.sfx_flashlight(), 0.7))
    ev.append((T["n17"][0] - 0.35, breath(0.9, 11, inhale=False), 0.25))
    cl = st["close"]
    for k in range(4):
        ev.append((cl + 0.1 + k * 1.5, breath(1.3, 30 + k, inhale=k % 2 == 0), 0.35))
    for k in range(10):
        ev.append((T["n19"][0] + k * 0.75, A.sfx_heartbeat(), 0.35))
    ev.append((T["s02"][0] + 0.3, flicker_buzz(1.4), 0.35))
    ev.append((st["end"], boom(2.5), 0.7))
    return ev


def music_bed(total):
    """Light comic tension -> darker suspense -> near silence."""
    T, shots, _ = timeline()
    st = {n: s for n, s in shots}
    buf = np.zeros(int((total + 3) * SR))
    # A: comic pizzicato, D minor, 104 bpm, until the yard
    bpm = 104
    beat = 60 / bpm
    a_end = st["yard"]
    seq = [62, None, 65, 62, 69, None, 68, None, 62, None, 65, 62, 70, 69, 65, None]
    bassline = [38, 38, 41, 36]
    t = 0.0
    i = 0
    while t < a_end:
        n = seq[i % len(seq)]
        if n:
            A.add(buf, A.pluck(n, 0.35, 0.35, seed=i) * 0.22, t)
        if i % 4 == 0:
            A.add(buf, A.bass(bassline[(i // 8) % 4], beat * 1.6) * 0.35, t)
        if i % 2 == 1:
            A.add(buf, A.woodblock(i % 4 == 1) * 0.12, t)
        t += beat / 2
        i += 1
    # B: tension pulse, from the yard to the cellar hatch
    b0, b1 = st["yard"], st["hatchopen"]
    beat = 60 / 120
    t = b0
    k = 0
    while t < b1:
        m = 38 if (k // 8) % 2 == 0 else 39
        A.add(buf, A.bass(m, beat * 0.45) * 0.4, t)
        if k % 4 == 0:
            A.add(buf, A.kick() * 0.25, t)
        t += beat / 2
        k += 1
    A.add(buf, A.pad(50, b1 - b0 + 0.5, 0.2) * 0.35, b0)
    A.add(buf, A.pad(51, b1 - b0 + 0.5, 0.15) * 0.25, b0 + (b1 - b0) / 2)
    # C: dark drone in the cellar
    c0 = st["hatchopen"]
    c1 = st["end"]
    A.add(buf, A.pad(38, c1 - c0 + 0.4, 0.08) * 0.55, c0)
    A.add(buf, A.pad(45, c1 - c0 + 0.4, 0.06) * 0.25, c0 + 1.0)
    A.add(buf, A.pad(46, c1 - st["close"], 0.05) * 0.2, st["close"])
    # smooth envelopes between sections
    tt = np.arange(len(buf)) / SR
    env = np.ones_like(tt)
    env *= np.clip((tt - 0.0) / 0.6, 0, 1)
    fade_a = np.clip((a_end - tt) / 0.5, 0, 1) * (tt < a_end + 0.01)
    env_b = (tt >= b0) * 1.0
    env = np.where(tt < a_end, env * fade_a, env)
    env *= np.where(tt >= c1, np.clip(1 - (tt - c1) / 0.05, 0, 1), 1)
    whisper = np.clip((tt - (T["s01"][0] - 0.8)) / 0.8, 0, 1)
    env *= 1 - 0.5 * whisper
    return (buf * env)[: int((total + 1) * SR)]


def voice_track(total):
    T, _, _ = timeline()
    clips = V.clips()
    buf = np.zeros(int((total + 1) * SR))
    for lid, (s, e) in T.items():
        if lid in clips:
            c = clips[lid]
            c = c / (np.sqrt(np.mean(c ** 2)) + 1e-9) * 0.09
            if SPEAKER[lid] == "stranger":
                c = c * 1.05
            A.add(buf, c, s)
    return buf


def mix_audio():
    os.makedirs(BUILD, exist_ok=True)
    T, shots, total = timeline()
    n = int((total + 1) * SR)
    vox = voice_track(total)
    mus = music_bed(total)[:n]
    sfx = np.zeros(n)
    for t, x, g in sfx_events():
        A.add(sfx, np.asarray(x, dtype=np.float64) * g, t)
    env = A.envelope_follow(np.abs(vox), 0.02, 0.35) if np.any(vox) else np.zeros(n)
    duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 2.5, 0, 1)
    mix = vox + mus * 0.55 * duck + sfx * (0.75 + 0.25 * duck)
    mix = np.tanh(mix * 1.1) / 1.1
    raw = os.path.join(BUILD, "mix_raw.wav")
    import soundfile as sf
    sf.write(raw, np.stack([mix, mix], axis=1).astype(np.float32), SR)
    out = os.path.join(BUILD, "mix.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    write_srt(os.path.join(OUTDIR, TITLE + ".en.srt"))
    print("audio ->", out, f"{total:.2f}s")
    return out


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    T, _, _ = timeline()
    cues = []
    for lid, _, text, _ in LINES:
        s, e = T[lid]
        if lid == "n14":
            a, b = "Quick survival tip: always plan a second exit.", \
                "And never enter a space without knowing how you'll escape."
            mid = s + (e - s) * len(a) / (len(a) + len(b))
            cues += [(s, mid, a), (mid, e, b)]
        else:
            cues.append((s, e, text.replace("...", "…")))
    with open(path, "w") as f:
        for i, (s, e, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(s)} --> {fmt(e + 0.15)}\n{txt}\n\n")


# ============================================================ render
def _worker(args):
    i, f0, f1, path, draft = args
    w, h = (W // 2, H // 2) if draft else (W, H)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r",
           str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if draft else "slow", "-crf",
           "26" if draft else "18", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in range(f0, f1):
        sf = render_frame(fr / FPS)
        if draft:
            small = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            c = cairo.Context(small)
            c.scale(0.5, 0.5)
            c.set_source_surface(sf)
            c.paint()
            sf = small
        p.stdin.write(bytes(sf.get_data()))
    p.stdin.close()
    p.wait()
    return i


def render_video(draft=False, workers=4):
    os.makedirs(BUILD, exist_ok=True)
    _, _, total = timeline()
    nf = int(math.ceil(total * FPS))
    chunk = 90
    jobs = [(i, f, min(nf, f + chunk), os.path.join(BUILD, f"part_{i:03d}.mp4"), draft)
            for i, f in enumerate(range(0, nf, chunk))]
    with mp.Pool(workers) as pool:
        for i in pool.imap_unordered(_worker, jobs):
            print(f"  chunk {i + 1}/{len(jobs)}", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for j in jobs:
            f.write(f"file '{j[3]}'\n")
    silent = os.path.join(BUILD, "silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    mix = mix_audio()
    out = os.path.join(OUTDIR, TITLE + ("_draft" if draft else "") + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("video ->", out)
    return out


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "plan"
    T, shots, total = timeline()
    if cmd == "plan":
        for n, s in shots:
            print(f"{s:6.2f}  [{n}]")
        for lid, (s, e) in T.items():
            print(f"   {s:6.2f}-{e:6.2f} {lid} {TEXT[lid]}")
        print(f"total {total:.2f}s  (voice clips: {len(V.clips())})")
    elif cmd == "stills":
        os.makedirs(BUILD, exist_ok=True)
        for x in a[1:]:
            render_frame(float(x)).write_to_png(os.path.join(BUILD, f"still_{float(x):06.2f}.png"))
    elif cmd == "sheet":
        os.makedirs(BUILD, exist_ok=True)
        n = int(a[1]) if len(a) > 1 else 24
        cols = 8
        rows = (n + cols - 1) // cols
        tw, th = 270, 480
        sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, cols * tw, rows * th)
        c = cairo.Context(sheet)
        for i in range(n):
            t = (i + 0.5) * total / n
            sf = render_frame(t)
            c.save()
            c.translate((i % cols) * tw, (i // cols) * th)
            c.scale(tw / W, th / H)
            c.set_source_surface(sf)
            c.paint()
            c.restore()
            c.move_to((i % cols) * tw + 8, (i // cols) * th + 22)
            c.set_source_rgb(1, 0, 0)
            c.set_font_size(18)
            c.show_text(f"{t:.1f}")
        sheet.write_to_png(os.path.join(BUILD, "sheet.png"))
    elif cmd == "audio":
        mix_audio()
    elif cmd == "video":
        render_video(draft="--draft" in a)


if __name__ == "__main__":
    main()

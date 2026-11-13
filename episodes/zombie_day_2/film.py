"""Just Needy: Zombie Apocalypse, Day 2 "The Cellar". Timeline, shots, sound, SRT, render.

usage:
  python -m episodes.zombie_day_2.film plan                 # print the timeline
  python -m episodes.zombie_day_2.film stills t1 t2 ...     # PNG stills to build/day2
  python -m episodes.zombie_day_2.film sheet [n]            # contact sheet of the whole film
  python -m episodes.zombie_day_2.film strip t0 t1 [fps]    # motion strip of a time range
  python -m episodes.zombie_day_2.film audio                # soundtrack + SRT
  python -m episodes.zombie_day_2.film video [--draft]      # render + mux
"""
import functools
import json
import math
import multiprocessing as mp
import os
import random
import subprocess
import sys

import cairo
import numpy as np

from cinecode import audio as A
from cinecode.core import clamp, ellipse, fs, hexc, line, noise1, prog, rrect, smooth, src
from episodes.zombie_day_2 import draw as D
from episodes.zombie_day_2 import sets as S
from episodes.zombie_day_2 import voice as V
from episodes.zombie_day_2.script import LINES, SPEAKER, TEXT, TITLE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "day2")
OUTDIR = os.path.join(ROOT, "output")
OUT_NAME = TITLE + "_FINAL"
W, H, FPS = D.W, D.H, D.FPS
SR = A.SR
TARGET = 60.0

# ============================================================ timeline
# ("shot", name) starts a shot; ("line", id, gap_before); ("wait", seconds, scalable)
PLAN = [
    ("shot", "couch"), ("wait", 0.25, False), ("line", "n01", 0.0), ("line", "n02", 0.3), ("line", "n03", 0.3),
    ("wait", 0.35, True),
    ("shot", "mailwide"), ("wait", 0.15, False), ("line", "n04", 0.0), ("wait", 1.1, True),
    ("shot", "window"), ("wait", 0.1, False), ("line", "n05", 0.0), ("line", "n06", 0.3), ("line", "n07", 0.4),
    ("line", "n08", 0.3), ("wait", 0.8, True),
    ("shot", "pack"), ("wait", 0.1, False), ("line", "n09", 0.0), ("line", "n10", 0.45), ("line", "n11", 0.7),
    ("wait", 0.45, True),
    ("shot", "yard"), ("wait", 0.15, False), ("line", "n12", 0.0), ("wait", 0.5, True),
    ("shot", "door"), ("wait", 0.1, False), ("line", "n13", 0.0), ("wait", 0.45, True),
    ("shot", "search"), ("wait", 0.1, False), ("line", "n14", 0.0), ("wait", 0.25, True),
    ("shot", "hatch"), ("wait", 0.05, False), ("line", "n15", 0.0), ("wait", 1.05, True),
    ("shot", "hatchopen"), ("wait", 0.1, False), ("line", "n16", 0.0), ("wait", 1.2, False),
    ("line", "n17", 0.0), ("wait", 0.3, True),
    ("shot", "explore"), ("wait", 0.4, False), ("line", "n18", 0.0), ("wait", 0.85, False),
    ("line", "n19", 0.0), ("line", "s01", 0.35), ("line", "s02", 0.9), ("wait", 0.45, False),
    ("shot", "end"), ("wait", 1.5, False),
]
GAP_SCALABLE_LINES = True


@functools.lru_cache(maxsize=None)
def timeline():
    dur = V.durations()
    speech = sum(dur[e[1]] for e in PLAN if e[0] == "line")
    fixed = sum(e[1] for e in PLAN if e[0] == "wait" and not e[2])
    scal = sum(e[1] for e in PLAN if e[0] == "wait" and e[2]) + sum(e[2] for e in PLAN if e[0] == "line")
    k = clamp((TARGET - speech - fixed) / scal, 0.55, 1.6) if scal else 1.0
    t = 0.0
    T = {}
    shots = []
    for ev in PLAN:
        if ev[0] == "shot":
            shots.append([ev[1], t])
        elif ev[0] == "wait":
            t += ev[1] * (k if ev[2] else 1.0)
        else:
            t += ev[2] * k
            T[ev[1]] = (t, t + dur[ev[1]])
            t = T[ev[1]][1]
    n16 = T["n16"]
    i = [s[0] for s in shots].index("explore")
    shots.insert(i, ["descend", n16[0] + 0.32 * (n16[1] - n16[0])])
    return T, [tuple(s) for s in shots], t, k


def shot_at(t):
    T, shots, total, _ = timeline()
    cur = shots[0]
    for sh in shots:
        if t >= sh[1]:
            cur = sh
    i = shots.index(cur)
    end = shots[i + 1][1] if i + 1 < len(shots) else total
    return cur[0], cur[1], end


def st_of(name):
    return dict(timeline()[1])[name]


def blink(t, seed=0):
    p = (t + seed * 1.37) % 3.1
    return 1.0 if p < 0.1 else 0.0


def ik(sh, target, l1, l2, bend=1):
    """Two-bone IK in the rig's angle convention (0 = down, + = towards screen right)."""
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = clamp(math.hypot(dx, dy), 1.0, l1 + l2 - 0.5)
    base = math.atan2(dx, dy)
    a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    a1 = base + bend * a
    ex, ey = sh[0] + math.sin(a1) * l1, sh[1] + math.cos(a1) * l1
    return a1, math.atan2(target[0] - ex, target[1] - ey)


def shoulders(x, gy, s, crouch=0.0):
    hip = gy - 150 * s * (1 - 0.42 * crouch)
    y = hip - 179 * s
    return (x - 74 * s, y), (x + 74 * s, y)


def arm_to(x, gy, s, side, target, crouch=0.0, bend=None):
    sl, sr = shoulders(x, gy, s, crouch)
    sh = sl if side < 0 else sr
    return ik(sh, target, 82 * s, 78 * s, bend if bend is not None else (-side))


def beam_arm(x, gy, s, ang, reach=0.92, crouch=0.0):
    """Right arm pointing a flashlight along screen angle ang; returns (arm angles, hand)."""
    _, sr = shoulders(x, gy, s, crouch)
    L = 160 * s * reach
    hand = (sr[0] + math.cos(ang) * L, sr[1] + math.sin(ang) * L)
    return ik(sr, hand, 82 * s, 78 * s, -1), hand


def pend(t, keys):
    """Piecewise smooth keyframes [(t, v)]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            x = smooth(prog(t, a, b))
            if isinstance(va, tuple):
                return tuple(p + (q - p) * x for p, q in zip(va, vb))
            return va + (vb - va) * x
    return keys[-1][1]


# ============================================================ shots
SIL = (0.16, 0.14, 0.13, 0.93)
WALKERS = ((D.CAST[1], 0.0, 75, 0.55, 1), (D.CAST[3], 3.4, 60, 0.6, -1), (D.CAST[0], 5.6, 70, 0.5, 1),
           (D.CAST[5], 8.0, 80, 0.52, -1))


def window_walkers(t, t0):
    def fg(cx, gy):
        lt = t - t0
        for i, (z, start, v, s, d) in enumerate(WALKERS):
            if lt < start - 0.5:
                continue
            x = (330 if d > 0 else 900) + d * v * (lt - start)
            D.zombie(cx, z, x, gy, s, t + i, face_dir=d, sil=SIL)
    return fg


def shot_couch(cx, t, st, en, T):
    lt = t - st
    # the first silhouette crosses the window right away; the hero's eyes follow it
    sil_x = 330 + 75 * lt
    follow = clamp((sil_x - 610) / 300, -1, 1)
    close_up = 0.95 <= lt < 2.35
    cx.save()
    if close_up:
        cx.translate(W / 2, H * 0.45)
        cx.scale(2.6, 2.6)
        cx.translate(-540, -1200)
    S.living_room(cx, t, draw_fg=window_walkers(t, st))
    S.couch_back(cx, 540, 1040, 1020, 300)
    n02, n03 = T["n02"], T["n03"]
    rock = math.sin(t * 2.4) * 0.05
    crouch = 0.95
    head_dy = 0.0
    if t < n02[0]:
        expr, look, turn = "terror", (follow, -0.7), -0.25 + 0.25 * follow
        arms = dict(arm_l=(0.35, 1.2), arm_r=(-0.35, -1.2))
    elif t < n03[0]:
        # nodding off after a night awake: head droops, then snaps back up
        expr, look, turn = "tired", (0, 0.3), 0.0
        d = n02[1] - n02[0]
        nod = math.sin(math.pi * clamp((t - n02[0] - 0.2 * d) / (0.55 * d))) if t < n02[0] + 0.75 * d else 0
        head_dy = 26 * nod
        snap = n02[0] + 0.75 * d
        if snap <= t < snap + 0.45:
            expr = "shock"
        arms = dict(arm_l=(0.25, 0.75), arm_r=(-0.25, -0.75))
    else:
        # deadpan to camera with a little palms-up shrug
        expr, look, turn = "flat", (0, 0), 0.0
        sh_ = math.sin(math.pi * clamp((t - n03[0] - 0.15) / 0.9))
        arms = dict(arm_l=(-0.4 - 0.9 * sh_, -0.6 - 1.7 * sh_), arm_r=(0.4 + 0.9 * sh_, 0.6 + 1.7 * sh_))
    D.hero(cx, 540, 1720, 1.22, expr=expr, t=t, crouch=crouch, look=look, blink=blink(t), turn=turn,
           shiver=0.7 if expr == "terror" else 0.15, tilt=rock, head_dy=head_dy, **arms)
    if close_up:  # the zombie's shadow slides across his face
        sx = 380 + (lt - 0.95) * 260
        cx.save()
        cx.rectangle(0, 0, W, H)
        cx.clip()
        g = cairo.LinearGradient(sx - 120, 0, sx + 120, 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(0.5, 0, 0, 0, 0.45)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        cx.set_source(g)
        cx.rectangle(sx - 120, 900, 240, 700)
        cx.fill()
        cx.restore()
    cx.restore()
    S.vignette(cx, 0.5)
    a = smooth(prog(lt, 0.1, 0.4)) * (1 - smooth(prog(lt, 2.7, 3.1)))
    if a > 0:
        D.label(cx, "DAY 2", W / 2, 150, 54, fill=D.WHITE, outline=D.INK, ow=7, alpha=a, spacing=12)
        w = 90 * smooth(prog(lt, 0.25, 0.7))
        for side in (-1, 1):
            line(cx, [(W / 2 + side * 125, 150), (W / 2 + side * (125 + w), 150)], (*D.YEL[:3], a), 5)


def mail_beats(T):
    """Mailman in the wide shot: walks in, raises the package, knocks with it on 'knocked'."""
    st = st_of("mailwide")
    n04 = T["n04"]
    d = n04[1] - n04[0]
    arrive = n04[0] + 0.25 * d
    knocks = [n04[0] + 0.55 * d + k * 0.24 for k in range(3)]
    return st, arrive, knocks


def mailman_wide(t, T):
    st, arrive, knocks = mail_beats(T)

    def fg(cx, gy):
        walking = t < arrive
        x = 640 + 330 * (1 - smooth(prog(t, st - 0.6, arrive))) if walking else 640
        raise_ = smooth(prog(t, arrive, knocks[0] - 0.05))
        kb = 0.0
        for kt in knocks:
            if t >= kt - 0.08:
                kb = max(kb, math.exp(-max(0, t - kt) * 14) * (1 if t >= kt else (t - kt + 0.08) / 0.08))
        la = (0.15 + 0.75 * raise_, 0.2 + 2.0 * raise_)
        ra = (-0.15 - 0.75 * raise_, -0.2 - 2.0 * raise_)
        hx, hy, R, hands = D.zombie(cx, D.MAILMAN, x, 1040, 1.12, t, face_dir=-1, walking=walking,
                                     phase=t * 3.4, arms=(la, ra), look=(-0.4, 0.3))
        mx = (hands[0][0] + hands[1][0]) / 2
        my = (hands[0][1] + hands[1][1]) / 2
        sc = 1 + 0.09 * kb
        D.package(cx, mx, my + 18 - 12 * kb, 176 * sc, 126 * sc, -0.06 + 0.04 * math.sin(t * 2))
        if kb > 0.05:  # glass ripple on each knock
            for r in (40, 70):
                cx.arc(mx, my, r * (1.6 - kb), 0, 2 * math.pi)
                src(cx, (1, 1, 1, 0.45 * kb))
                cx.set_line_width(3)
                cx.stroke()
    return fg


def shot_mailwide(cx, t, st, en, T):
    _, arrive, knocks = mail_beats(T)
    S.living_room(cx, t, draw_fg=mailman_wide(t, T))
    S.couch_back(cx, 540, 1040, 1020, 300)
    k0 = knocks[0]
    # hero: hiding, startled by the knocks, then creeps out towards the window
    jump = math.sin(math.pi * clamp((t - k0) / 0.45)) if k0 <= t < k0 + 0.45 else 0
    creep0 = knocks[-1] + 0.35
    x = 540 - 240 * smooth(prog(t, creep0, en))
    walking = creep0 < t < en - 0.1
    crouch = 0.95 if t < k0 else 0.95 - 0.55 * smooth(prog(t, k0, k0 + 0.4))
    if t < k0:
        expr, look = "tired", (0.2, 0.4)
    elif t < creep0:
        expr, look = "shock", (0.3, -1)
    else:
        expr, look = "scared", (-0.4, -1)
    arms = dict(arm_l=(-1.4, -2.4), arm_r=(1.4, 2.4)) if k0 <= t < creep0 else \
        dict(arm_l=(0.9, 1.9), arm_r=(0.2, -0.3)) if walking else dict(arm_l=(0.25, 0.75), arm_r=(-0.25, -0.75))
    D.hero(cx, x, 1720 - 150 * jump, 1.22, expr=expr, t=t, crouch=crouch, look=look, blink=blink(t, 2),
           walk=(t * 4.2) if walking else None, tilt=-0.08 if walking else 0.0, shiver=0.3, **arms)
    S.vignette(cx, 0.5)


def shot_window(cx, t, st, en, T):
    lt = t - st
    n05, n06, n07, n08 = T["n05"], T["n06"], T["n07"], T["n08"]
    left_at = n06[0] + 0.62 * (n06[1] - n06[0])
    lost = (t - left_at) if t >= left_at else None
    lift = smooth(prog(t, n07[0] + 0.15, n07[0] + 0.6))
    tap = 0.0
    taps = [n07[0] + 0.75 + k * 0.26 for k in range(3)]
    for tk in taps:
        if t >= tk:
            tap = max(tap, math.exp(-(t - tk) * 12))
    nod = math.sin((t - n08[0]) * 9) * 0.12 if n08[0] < t < n08[1] + 0.4 else 0.0

    def fg(cx2, gy):
        lifted = lift - 0.05 * tap
        # creepy-absurd: grin + slow head tilt towards the hero, a jerky nod on the five stars
        D.zombie(cx2, D.MAILMAN, 500 + 10 * math.sin(t * 0.9), gy + 620, 2.2, t, face_dir=1, walking=False,
                 arms=((-0.2 + 0.05 * math.sin(t * 2), 1.3 + 0.3 * lifted),
                       (-0.9 - 0.2 * lifted, -1.6 - 0.4 * lifted)),
                 look=(1, 0.3), lost_left=lost, head_add=0.18 * smooth(prog(t, n05[0], n05[1])) + nod,
                 jaw=0.55 + 0.45 * math.sin(t * 5) ** 2 if t < n06[0] else None)
        sc = 1.0 + 0.25 * lifted
        D.package(cx2, 560, 1040 - 70 * lifted, 300 * sc, 210 * sc, -0.08 + 0.1 * lifted)
    S.striped_wall(cx, 0, 0, W, H)
    S.window(cx, 90, 280, 900, 980, t, draw_fg=fg, curtains=False)
    # hero: fear, a double take, then disbelief
    rec = smooth(prog(lt, 0.0, 0.45))
    dbl = n06[0] + 0.7 * (n06[1] - n06[0])
    if t < n05[1]:
        expr, turn, look, tilt = "terror", -0.7, (-1, -0.3), -0.05
        arms = dict(arm_l=(0.3, 0.2), arm_r=(0.1, 0.0))
    elif t < dbl:
        expr, turn, look, tilt = "scared", -0.7, (-1, -0.3), -0.05
        arms = dict(arm_l=(0.3, 0.2), arm_r=(0.1, 0.0))
    elif t < dbl + 0.55:  # double take to camera
        expr, turn, look, tilt = "shock", 0.0, (0, 0), 0.0
        arms = dict(arm_l=(0.3, 0.2), arm_r=(0.1, 0.0))
    elif t < n08[0]:
        expr, turn, look, tilt = "confused", -0.6, (-1, -0.2), 0.14 + 0.04 * math.sin(t * 3)
        arms = dict(arm_l=(0.6, 2.4), arm_r=(0.1, 0.0))  # scratches his head
    else:
        expr, turn, look, tilt = "flat", 0.0, (0, 0), 0.04
        arms = dict(arm_l=(0.3, 0.2), arm_r=(0.1, 0.0))
    D.hero(cx, 860 + 300 * (1 - rec), 2350, 1.75, expr=expr, t=t, turn=turn, look=look,
           blink=blink(t, 4), tilt=tilt, shiver=0.5 if expr in ("terror", "scared") else 0.0, **arms)
    S.vignette(cx, 0.45)
    for k in range(5):
        tk = n08[0] + 0.1 + k * 0.12
        sc = D.pop_scale(t, tk, 0.3)
        if sc > 0:
            star(cx, 180 + k * 180, 160, 60 * sc)


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


# ---------------------------------------------------------------- backpack
HX, HGY, HS = 560, 1560, 1.2       # hero behind the table
TABLE_Y = 1405                    # table top
BAG = (300, 1300)                 # backpack on the table (left)
BAG_MOUTH = (300, 1220)
SPOTS = {"cookie1": (520, TABLE_Y - 18), "cookie2": (600, TABLE_Y - 14), "charger": (720, TABLE_Y - 30),
         "sock": (880, TABLE_Y - 60)}


def pack_beats(T):
    n09, n10, n11 = T["n09"], T["n10"], T["n11"]
    b = V.inner_beats("n10", 3, (0.0, 0.36, 0.70))
    # each item: (name(s), reach start, pull out, release)
    beats = []
    for k, (names, r) in enumerate(((("cookie1", "cookie2"), b[0]), (("charger",), b[1]), (("sock",), b[2]))):
        t0 = n10[0] + r
        beats.append((names, t0 - 0.35, t0 - 0.05, t0 + 0.25))
    return n09, n10, n11, beats


def item_state(t, name, release, land_dt=0.38):
    """None before release (still in hand), else (x, y, rot) flying / landed."""
    if t < release:
        return None
    x1, y1 = SPOTS[name]
    x0, y0 = 400, 1130
    f = clamp((t - release) / land_dt)
    x = x0 + (x1 - x0) * f
    y = y0 + (y1 - y0) * f - 160 * math.sin(math.pi * f)
    rot = (1 - f) * 2.5 if name != "sock" else (1 - f) * 0.8
    if f >= 1:
        bt = t - release - land_dt
        y -= 22 * abs(math.sin(bt * 14)) * math.exp(-bt * 9) * (0.3 if name == "sock" else 1)
    return x, y, rot


def draw_named(cx, name, x, y, s, rot=0.0):
    if name.startswith("cookie"):
        D.cookie(cx, x, y, 44 * s, rot)
    elif name == "charger":
        D.charger(cx, x - 25 * s, y - 25 * s, 0.6 * s, rot)
    else:
        D.sock(cx, x, y, 0.55 * s, rot)


def shot_pack(cx, t, st, en, T):
    n09, n10, n11, beats = pack_beats(T)
    S.kitchen(cx, t, table=False)
    grab = smooth(prog(t, n09[0] - 0.1, n09[0] + 0.3))
    slam = prog(t, n09[0] + 0.45, n09[0] + 0.6)
    zip_ = smooth(prog(t, n09[0] + 0.7, n09[1] + 0.25))
    # backpack: flies in from the right into his hands, slams down on the table
    if slam < 1:
        bx = 1350 - 900 * grab + (BAG[0] - 450) * smooth(slam)
        by = 1000 + (BAG[1] - 1000) * smooth(slam)
        brot = 0.5 * (1 - grab)
    else:
        bx, by, brot = BAG[0], BAG[1] + 8 * math.exp(-(t - n09[0] - 0.6) * 10) * math.sin((t - n09[0]) * 40), 0
    # left hand: zipper, then into the bag for each item; right hand idle / thumbs up later
    l_target = None
    held = None
    if t < n09[0] + 0.6:
        l_target = (bx - 60, by - 120)
        r_target = (bx + 60, by - 120)
    else:
        r_target = None
        l_target = (BAG[0] - 70 + 160 * zip_, BAG[1] - 60) if t < n10[0] - 0.4 else None
        for names, reach, pull, rel in beats:
            if reach <= t < rel + 0.15:
                if t < pull:
                    l_target = (BAG_MOUTH[0] + 10, BAG_MOUTH[1] + 30 * smooth(prog(t, reach, pull)))
                elif t < rel:
                    f = smooth(prog(t, pull, rel))
                    l_target = (BAG_MOUTH[0] + 100 * f, BAG_MOUTH[1] - 120 * f)
                    held = (names, l_target)
                else:
                    l_target = (400, 1100)
    look = (-0.8, 0.8) if t < n11[0] else (0, 0)
    expr = "confident" if t < n10[0] else "neutral"
    arms = {}
    if l_target:
        arms["arm_l"] = arm_to(HX, HGY, HS, -1, l_target)
    else:
        arms["arm_l"] = (0.2, 0.15)
    if r_target:
        arms["arm_r"] = arm_to(HX, HGY, HS, 1, r_target)
    # n11: pause, look at the pile, blink, look at us, thumbs up with misplaced confidence
    thumb_t = n11[0] + 0.35 * (n11[1] - n11[0])
    tilt = 0.0
    hand_r = "dot"
    if t >= n11[0] - 0.5:
        look = (0.4, 1.0) if t < thumb_t - 0.25 else (0, 0)
        expr = "flat" if t < thumb_t - 0.25 else "confident"
        up = smooth(prog(t, thumb_t - 0.2, thumb_t + 0.15))
        arms["arm_r"] = (0.2 + 1.75 * up, 0.1 + 2.95 * up)
        hand_r = "thumb" if up > 0.6 else "dot"
        tilt = 0.08 * up + 0.03 * math.sin(t * 6) * up
    D.hero(cx, HX, HGY, HS, expr=expr, t=t, blink=blink(t, 6), look=look, tilt=tilt, hand_r=hand_r, **arms)
    S.kitchen_table(cx, 540, 1430, 900)
    D.backpack(cx, bx, by, 0.95, open_=zip_, rot=brot)
    # items: in hand, flying, landed
    for names, reach, pull, rel in beats:
        for j, name in enumerate(names):
            stt = item_state(t, name, rel + 0.12 * j)
            if stt is None:
                if held and held[0] == names:
                    hx, hy = held[1]
                    if name == "sock":  # dangles limply from his fingers
                        draw_named(cx, name, hx + 10, hy + 70, 1.0, 0.15 * math.sin(t * 7))
                    else:
                        draw_named(cx, name, hx + 30 * j, hy - 10 * j, 1.0, 0.3 * j)
                continue
            draw_named(cx, name, stt[0], stt[1], 1.0, stt[2])
    if t >= n11[0] - 0.5:
        sp = D.pop_scale(t, thumb_t + 0.1, 0.3) * (1 - smooth(prog(t, thumb_t + 0.8, thumb_t + 1.1)))
        if sp > 0:
            star(cx, 815, 850, 38 * sp)
    # inventory fills as each thing lands
    filled = [("cookie", beats[0][3] + 0.38), ("cookie", beats[0][3] + 0.5), ("charger", beats[1][3] + 0.38),
              ("sock", beats[2][3] + 0.38)]
    a = smooth(prog(t, n10[0] - 0.3, n10[0])) * (1 - smooth(prog(t, en - 0.3, en)))
    kit_panel(cx, t, filled, y=130, alpha=a)
    S.vignette(cx, 0.4)


def kit_panel(cx, t, filled, y=120, alpha=1.0):
    if alpha <= 0:
        return
    cx.push_group()
    rrect(cx, 150, y, 780, 270, 30)
    fs(cx, (0.09, 0.08, 0.07, 0.8), D.YEL, 4)
    D.label(cx, "SURVIVAL KIT", W / 2, y + 60, 50, fill=D.WHITE, outline=D.INK, ow=6, shadow=False)
    for k in range(4):
        x = 200 + k * 175
        rrect(cx, x, y + 110, 140, 140, 20)
        fs(cx, (1, 1, 1, 0.08), (1, 0.83, 0.23, 0.5), 3)
    for k, (name, tf) in enumerate(filled):
        if t < tf:
            continue
        sc = D.pop_scale(t, tf, 0.3)
        cxp, cyp = 200 + k * 175 + 70, y + 180
        if name == "cookie":
            D.cookie(cx, cxp, cyp, 40 * sc)
        elif name == "charger":
            D.charger(cx, cxp - 20 * sc, cyp - 25 * sc, 0.45 * sc)
        else:
            D.sock(cx, cxp - 10 * sc, cyp, 0.42 * sc)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


# ---------------------------------------------------------------- escape
YARD = [  # (zombie, x0, ground y, scale, dir, speed px/s)
    (D.CAST[5], 900, 1290, 0.42, -1, 22),
    (D.CAST[0], 120, 1350, 0.5, 1, 30),
    (D.CAST[1], 820, 1440, 0.6, -1, 26),
    (D.CAST[2], 60, 1570, 0.72, 1, 44),
    (D.CAST[3], 1000, 1700, 0.85, -1, 36),
    (D.CAST[4], 160, 1880, 1.02, 1, 28),
]


def yard_clank(T):
    n12 = T["n12"]
    return n12[0] + 0.55 * (n12[1] - n12[0])


def shot_yard(cx, t, st, en, T):
    lt = t - st
    clank = yard_clank(T)

    def fg(cx2):
        for i, (zz, x0, gy, s, d, v) in enumerate(YARD):
            # walk; on the clank from the house every head snaps towards it, they freeze, then press on faster
            react = clamp((t - clank - 0.04 * i) / 0.08) * (1 - smooth(prog(t, clank + 0.7, clank + 1.0)))
            prog_t = lt if t < clank else (clank - st) + max(0, t - clank - 0.6) * 1.5
            x = x0 + d * v * prog_t * (1 + 0.25 * math.sin(prog_t * 0.9 + i))
            hx_house = 540 - x
            head = react * clamp(hx_house / 400, -1, 1) * 0.5
            D.zombie(cx2, zz, x, gy, s, t + i * 0.7, face_dir=d if react < 0.5 else (1 if hx_house > 0 else -1),
                     walking=react < 0.5, phase=prog_t * zz.speed * 3.2 + i * 1.9, head_add=head,
                     look=(clamp(hx_house / 300, -1, 1), -0.5 * react))
    S.farm_exterior(cx, t, draw_fg=fg)
    S.vignette(cx, 0.45)


DOOR_BANGS = (0.0, 0.42, 0.7, 1.22, 1.5, 1.95, 2.3)


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
    cx.translate(noise1(t * 40, 2) * 12 * b, noise1(t * 40, 7) * 8 * b)

    def hands(cx2):
        for k, (x, y, rot) in enumerate(((-90, -800, 0.3), (60, -850, -0.2), (-10, -760, 0.05))):
            press = 6 * b + 4 * math.sin(t * 3 + k)
            cx2.save()
            cx2.translate(x + 5 * math.sin(t * 2 + k), y - press * (k + 1))
            cx2.rotate(rot + 0.05 * math.sin(t * 4 + k))
            ellipse(cx2, 0, 0, 38, 46)
            src(cx2, (0.18, 0.2, 0.15, 0.9))
            cx2.fill()
            for f in range(4):
                line(cx2, [(-24 + f * 16, -20), (-30 + f * 20, -80 - 6 * (f % 2))], (0.18, 0.2, 0.15, 0.9), 13)
            cx2.restore()
    S.front_door(cx, t, bang=b, cracks=0.6 + 0.4 * b, draw_hands=hands)
    # backs away, looks left and right for another way out, then bolts off screen right
    back = smooth(prog(lt, 0.1, 1.0))
    run = smooth(prog(t, en - 0.55, en))
    x = 700 + 160 * back + 500 * run
    look_lr = math.sin((lt - 1.0) * 6) if 1.0 < lt < en - st - 0.55 else -0.6
    D.hero(cx, x, 1840, 1.15, expr="scared", t=t, look=(look_lr, -0.1), turn=0.6 * look_lr if lt > 1 else -0.5,
           blink=blink(t, 3), walk=lt * (6 if run == 0 else 11) if (lt < 1.0 or run > 0) else None,
           arm_l=(-1.0, -2.6) if run == 0 else None, arm_r=(1.0, 2.6) if run == 0 else None, shiver=0.6,
           lean=0.12 * run)
    cx.restore()
    S.vignette(cx, 0.5)


HATCH = (380, 1500, 340, 160)


def kitchen_hatch(open_=0.0):
    return lambda c: S.hatch_floor(c, HATCH[0], HATCH[1], HATCH[2], HATCH[3], open_=open_)


def shot_search(cx, t, st, en, T):
    """Hero searches the kitchen for a second exit while the tip is spoken; finds the hatch."""
    lt = t - st
    n14 = T["n14"]
    d14 = n14[1] - n14[0]
    S.kitchen(cx, t, table=False, hatch=kitchen_hatch())
    # fridge door swings open (nothing useful), closes
    fo = math.sin(math.pi * clamp((t - (n14[0] + 0.32 * d14)) / (0.28 * d14)))
    if fo > 0:
        cx.save()
        cx.translate(1040, 0)
        cx.scale(1 - 1.25 * fo, 1)
        rrect(cx, -280, 600, 280, 640, 14)
        fs(cx, hexc("#f4f2ec"), D.INK, 4)
        cx.restore()
        cx.rectangle(762 + 280 * (1 - fo), 602, 276 * fo, 636)
        src(cx, (1, 0.97, 0.85, 0.85 * fo))
        cx.fill()
    keys_x = [(st, -150), (st + 0.55, 520), (n14[0] + 0.3 * d14, 700), (n14[0] + 0.62 * d14, 700),
              (n14[0] + 0.78 * d14, 760)]
    x = pend(t, keys_x)
    moving = abs(pend(t + 0.05, keys_x) - x) > 1.0
    # head turns: left at the cabinets, right at the fridge, then down at the hatch
    if t < n14[0] + 0.3 * d14:
        turn, look = -0.6 * math.sin(lt * 3), (-math.sin(lt * 3), -0.2)
        expr = "worried"
    elif t < n14[0] + 0.62 * d14:
        turn, look = 0.6, (1, 0)
        expr = "worried" if fo < 0.5 else "flat"
    elif t < n14[0] + 0.86 * d14:
        turn, look = -0.3, (-1, 0.2)
        expr = "worried"
    else:
        turn, look = -0.55, (-1, 1)
        expr = "shock"
    arms = dict(arm_r=arm_to(x, 1800, 1.15, 1, (870, 840))) if fo > 0.03 else {}
    D.hero(cx, x, 1800, 1.15, expr=expr, t=t, blink=blink(t, 8), turn=turn, look=look,
           walk=t * 9 if moving else None, lean=0.1 if moving and t < st + 0.55 else 0.0, **arms)
    S.vignette(cx, 0.45)
    # brief tip badge: first exit blocked, second exit yes
    a = smooth(prog(t, n14[0] + 0.05, n14[0] + 0.25)) * (1 - smooth(prog(t, n14[0] + 0.5 * d14,
                                                                             n14[0] + 0.5 * d14 + 0.25)))
    if a > 0:
        tip_badge(cx, t, a, n14[0])


def tip_badge(cx, t, a, t0):
    cx.push_group()
    rrect(cx, 240, 120, 600, 250, 34)
    fs(cx, (0.09, 0.08, 0.07, 0.82), D.YEL, 4)

    def door(x, y):
        rrect(cx, x - 45, y - 75, 90, 150, 8)
        fs(cx, None, D.WHITE, 7)
        ellipse(cx, x + 22, y + 5, 7, 7)
        src(cx, D.WHITE)
        cx.fill()
    door(380, 245)
    door(700, 245)
    f = smooth(prog(t, t0 + 0.35, t0 + 0.6))
    if f > 0:  # X over the first door
        line(cx, [(330, 185), (330 + 100 * f, 185 + 120 * f)], D.WHITE, 12)
        line(cx, [(430, 185), (430 - 100 * f, 185 + 120 * f)], D.WHITE, 12)
    g = smooth(prog(t, t0 + 0.6, t0 + 0.95))
    if g > 0:
        line(cx, [(470, 245), (470 + 140 * g, 245)], D.YEL, 12)
        if g > 0.95:
            line(cx, [(585, 220), (612, 245), (585, 270)], D.YEL, 12)
            line(cx, [(675, 330), (695, 350), (740, 300)], D.YEL, 12)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)


def shot_hatch(cx, t, st, en, T):
    lt = t - st
    n15 = T["n15"]
    d = n15[1] - n15[0]
    S.kitchen(cx, t, table=False, hatch=kitchen_hatch())
    x = pend(t, [(st, 760), (st + 0.6, 560)])
    walking = lt < 0.6
    crouch = smooth(prog(lt, 0.5, 0.85)) * 0.75
    ring = (HATCH[0], HATCH[1] + HATCH[3] * 0.82)
    # reaches for the ring, flinches back, reaches again, flinches... then BAD IDEA, gulp, grab
    reach_keys = [(st + 0.8, 0.0), (st + 1.15, 0.85), (st + 1.35, 0.1), (n15[1] - 0.6, 0.1), (n15[1] - 0.35, 0.7),
                  (n15[1] - 0.15, 0.05), (en - 0.45, 0.05), (en - 0.1, 1.0)]
    r = pend(t, reach_keys)
    sl, _ = shoulders(x, 1830, 1.15, crouch)
    tgt = (sl[0] + (ring[0] - sl[0]) * r, sl[1] + 60 + (ring[1] - sl[1] - 60) * r)
    look_cam = n15[1] + 0.15 < t < n15[1] + 0.65
    expr = "flat" if look_cam else ("scared" if r > 0.5 else "worried")
    D.hero(cx, x, 1830, 1.15, expr=expr, t=t, blink=blink(t, 5), crouch=crouch, walk=t * 5 if walking else None,
           turn=0.0 if look_cam else -0.55, look=(0, 0) if look_cam else (-1, 0.8),
           arm_l=arm_to(x, 1830, 1.15, -1, tgt, crouch), arm_r=(-0.3, -0.9) if not look_cam else (-0.6, -2.0),
           shiver=0.35)
    S.vignette(cx, 0.5)
    sc = D.pop_scale(t, n15[1] - 0.05, 0.32)
    if sc > 0:
        a = 1 - smooth(prog(t, en - 0.3, en))
        D.label(cx, "BAD IDEA", W / 2, 1020 + noise1(t * 20, 4) * 3, 104, fill=D.YEL, outline=D.INK, ow=12,
                rot=-0.04, scale=sc, alpha=a)


def shot_hatchopen(cx, t, st, en, T):
    o = smooth(prog(t, st + 0.1, en - 0.05))
    cx.save()
    cx.translate(W / 2, H * 0.68)
    cx.scale(1.55, 1.55)
    cx.translate(-HATCH[0], -HATCH[1] - 70)
    S.kitchen(cx, t, table=False, hatch=kitchen_hatch(o))
    # stale dust rising out of the hole
    r = random.Random(5)
    for k in range(26):
        ph = (t * 0.6 + r.random()) % 1.0
        px = HATCH[0] + r.uniform(-150, 150) + 20 * math.sin(t * 2 + k)
        py = HATCH[1] + HATCH[3] * 0.6 - ph * 300
        ellipse(cx, px, py, 3, 3)
        src(cx, (0.9, 0.85, 0.7, 0.5 * o * math.sin(math.pi * ph)))
        cx.fill()
    cx.restore()
    hand_y = 1300 - 420 * o
    D.sleeve(cx, [(1180, 1150), (900, hand_y + 40), (760, hand_y)], 70)
    D.hand_dot(cx, 760, hand_y, 30)
    S.vignette(cx, 0.6)


# ---------------------------------------------------------------- cellar
def cellar_cam(cx, fx, fy, zoom):
    cx.translate(W / 2, H / 2)
    cx.scale(zoom, zoom)
    x = clamp(fx, W / 2 / zoom, S.CELLAR_W - W / 2 / zoom)
    y = clamp(fy, H / 2 / zoom, H - H / 2 / zoom)
    cx.translate(-x, -y)


def descend_beats(T):
    n16 = T["n16"]
    st = n16[0] + 0.32 * (n16[1] - n16[0])
    close_t = n16[1] - 0.05
    nsteps = S.N_STEPS
    step_times = [st + 0.05 + k * (close_t - st - 0.15) / nsteps for k in range(nsteps)]
    flash_t = close_t + 0.6
    return st, step_times, close_t, flash_t


def descend_pos(t, T):
    st, steps, close_t, flash_t = descend_beats(T)
    k = sum(1 for s in steps if t >= s)
    if k == 0:
        return S.stair_point(0.0), None, 0
    k = min(k, len(steps))
    hop = clamp((t - steps[k - 1]) / 0.22)
    p0 = S.stair_point((k - 1) / S.N_STEPS)
    p1 = S.stair_point(min(1.0, k / S.N_STEPS))
    x = p0[0] + (p1[0] - p0[0]) * smooth(hop)
    y = p0[1] + (p1[1] - p0[1]) * smooth(hop) - 18 * math.sin(math.pi * hop)
    return (x, y), (k - 1 + hop) * math.pi, k


def beam_light(hand, ang, k):
    return [("cone", hand[0], hand[1], ang, 0.2, 1500, k), ("glow", hand[0], hand[1], 300, 0.7 * k)]


def dust(cx, t, hand, ang, k, n=70, seed=2):
    """Specks drifting in the flashlight beam."""
    if k <= 0.05:
        return
    r = random.Random(seed)
    for i in range(n):
        d = r.uniform(120, 1100)
        off = r.uniform(-0.17, 0.17)
        drift = 30 * math.sin(t * r.uniform(0.3, 0.8) + i)
        a = ang + off
        x = hand[0] + math.cos(a) * d + drift
        y = hand[1] + math.sin(a) * d + 25 * math.sin(t * 0.5 + i * 1.3) + (t * 12 * r.uniform(0.5, 1.5)) % 60
        rr = r.uniform(1.5, 4)
        ellipse(cx, x, y, rr, rr)
        src(cx, (1, 0.96, 0.85, 0.55 * k * (1 - d / 1200)))
        cx.fill()


def shot_descend(cx, t, st, en, T):
    _, steps, close_t, flash_t = descend_beats(T)
    n17 = T["n17"]
    (gx, gy), walk, k = descend_pos(t, T)
    if t >= steps[-1] + 0.25:
        gx2 = gx + 150 * smooth(prog(t, steps[-1] + 0.25, n17[0]))
        walk = (t * 4.0) if t < n17[0] else None
        gx = gx2
    hatch = 1.0 - smooth(prog(t, close_t, close_t + 0.22))
    flash = 1.0 if t >= flash_t else 0.0
    # wrist sweep after the click: across the shelves, down to the floor, settles
    ang = pend(t, [(flash_t, 0.05), (flash_t + 0.5, -0.35), (flash_t + 1.0, 0.35), (n17[0] + 0.2, 0.15),
                   (n17[1], 0.45)])
    close = t >= n17[0] - 0.1
    cx.save()
    if close:
        cellar_cam(cx, gx + 100, gy - 400, 2.0)
    else:
        cellar_cam(cx, gx + 120, gy - 360, 1.15)
    S.cellar(cx, t, hatch_open=hatch)
    arm, hand = beam_arm(gx, gy, 0.95, ang)
    relieved = t > n17[0] + 0.1
    D.hero(cx, gx, gy, 0.95, expr="relieved" if relieved else ("worried" if flash else "scared"), t=t,
           blink=blink(t, 2), walk=walk, arm_r=arm, arm_l=(0.3, 0.2),
           look=(math.cos(ang), math.sin(ang) * 0.6) if flash else (0.3, 0.6), turn=0.25 * math.cos(ang) if flash else 0,
           crouch=0.12 * smooth(prog(t, n17[0], n17[0] + 0.5)) if relieved else 0.0)
    D.flashlight(cx, hand[0], hand[1], ang, 0.9, on=flash > 0)
    lights = []
    if hatch > 0.01:
        lights += [("cone", 285, 140, 1.25, 0.32, 1500, hatch), ("glow", 285, 170, 380, 0.6 * hatch),
                   ("glow", gx, gy - 260, 430, 0.55 * hatch)]
    if flash:
        lights += beam_light(hand, ang, 1.0)
    S.darkness(cx, 0.95, lights)
    dust(cx, t, hand, ang, flash)
    cx.restore()
    S.vignette(cx, 0.55)


def explore_beats(T):
    n18, n19, s01, s02 = T["n18"], T["n19"], T["s01"], T["s02"]
    box_t = n18[1] + 0.12
    whip = box_t + 0.22
    flick0 = s01[0] + 0.3
    shadow_t = s02[0] + 0.15
    stepback = s02[0] + 0.55
    return box_t, whip, flick0, shadow_t, stepback


def flicker(t, t0, en):
    if t < t0:
        return 1.0
    rate = prog(t, t0, en)
    k = noise1(t * 24, 13)
    if k < -0.55 + 0.85 * rate:
        return 0.08 + 0.15 * max(0, noise1(t * 60, 3))
    return 1.0


def unnatural_shadow(cx, x, y, h, t, alpha):
    """A huge, wrong shadow thrown on the wall: too tall, neck bent, arms far too long. Never its source."""
    if alpha <= 0:
        return
    cx.push_group()
    sway = math.sin(t * 1.3) * 0.06
    lean = 0.08 + sway
    cx.save()
    cx.translate(x, y)
    cx.rotate(lean)
    body = [(-70, 0), (-90, -h * 0.45), (-60, -h * 0.72), (60, -h * 0.72), (90, -h * 0.45), (70, 0)]
    cx.move_to(*body[0])
    for p in body[1:]:
        cx.line_to(*p)
    cx.close_path()
    src(cx, (0, 0, 0, 1))
    cx.fill()
    # neck bent sideways, head too small
    neck = (0, -h * 0.72)
    hx, hy = neck[0] + h * 0.12, neck[1] - h * 0.08 + 10 * math.sin(t * 2.1)
    line(cx, [neck, (hx - 20, hy + 40), (hx, hy)], (0, 0, 0, 1), 40)
    ellipse(cx, hx + 10, hy - 30, 62, 74, 0.6)
    src(cx, (0, 0, 0, 1))
    cx.fill()
    # arms: long, jointed wrong, slowly reaching
    for side, ph in ((-1, 0.0), (1, 1.4)):
        sx, sy = side * 70, -h * 0.66
        a1 = side * (0.5 + 0.25 * math.sin(t * 0.9 + ph))
        ex, ey = sx + math.sin(a1) * h * 0.38, sy + math.cos(a1) * h * 0.38
        a2 = a1 - side * (1.6 + 0.4 * math.sin(t * 1.2 + ph))
        hx2, hy2 = ex + math.sin(a2) * h * 0.4, ey + math.cos(a2) * h * 0.4
        line(cx, [(sx, sy), (ex, ey), (hx2, hy2)], (0, 0, 0, 1), 30)
        for f in range(4):
            fa = a2 + (f - 1.5) * 0.25
            line(cx, [(hx2, hy2), (hx2 + math.sin(fa) * 110, hy2 + math.cos(fa) * 110)], (0, 0, 0, 1), 9)
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def shot_explore(cx, t, st, en, T):
    n18, n19, s01, s02 = T["n18"], T["n19"], T["s01"], T["s02"]
    box_t, whip, flick0, shadow_t, stepback = explore_beats(T)
    # creeping right along the shelves, beam searching; freezes when he hears the breathing
    x = pend(t, [(st, 1000), (n18[0] + 0.5, 1180), (stepback, 1180), (stepback + 0.35, 1100)])
    walking = (st < t < n18[0] + 0.5) or (stepback < t < stepback + 0.35)
    gy = 1600
    if t < whip:
        ang = 0.05 + 0.3 * math.sin((t - st) * 1.9) * (1 - smooth(prog(t, n18[0] + 0.4, n18[0] + 0.8))) - 0.1
        turn = 0.35
    elif t < whip + 0.14:  # whip round to the crash behind him
        f = smooth(prog(t, whip, whip + 0.14))
        ang = -0.05 + (math.pi - 0.8 - (-0.05)) * f
        turn = 0.35 - 1.15 * f
    elif t < shadow_t - 0.5:
        ang = math.pi - 0.8 + 0.05 * noise1(t * 9, 3) + 0.25 * smooth(prog(t, whip + 0.6, n19[0]))
        turn = -0.8
    else:  # slowly back towards the wall where the breathing came from
        f = smooth(prog(t, shadow_t - 0.5, shadow_t + 0.2))
        a0 = math.pi - 0.55
        ang = a0 + (-0.5 - a0) * f
        turn = -0.8 + 1.05 * f
    ang += 0.03 * noise1(t * 14, 21) * (1 if t > whip else 0)  # trembling wrist
    k = flicker(t, flick0, en)
    if shadow_t <= t < shadow_t + 0.4:
        k = 1.0  # one clear flash shows the shadow
    if t < n18[0] + 0.3:
        expr = "worried"
    elif t < whip:
        expr = "scared"
    else:
        expr = "terror"
    close = n19[0] - 0.05 <= t < s02[0]
    cx.save()
    if close:
        cellar_cam(cx, x - 20, gy - 470, 2.5)
    else:
        pan = smooth(prog(t, box_t + 0.05, box_t + 0.35)) * (1 - smooth(prog(t, shadow_t - 0.5, shadow_t)))
        wide = smooth(prog(t, shadow_t - 0.5, shadow_t))
        cellar_cam(cx, x + 60 - 260 * pan + 140 * wide, gy - 520 - 60 * wide, 1.25 - 0.22 * wide)
    S.cellar(cx, t, box_fall=(t - box_t) if t >= box_t - 0.5 else None)
    sh_a = (1.0 if t >= shadow_t else 0.0)
    unnatural_shadow(cx, 1520 + 50 * math.sin(t * 0.7) + 40 * prog(t, shadow_t, en), 1600, 1180, t, 0.95 * sh_a)
    arm, hand = beam_arm(x, gy, 0.95, ang)
    eyes = 0.0 if t < s01[0] else smooth(prog(t, s01[0], s01[0] + 0.3))
    D.hero(cx, x, gy, 0.95, expr=expr, t=t, blink=0 if expr == "terror" else blink(t, 7), walk=t * 3.2 if walking
           else None, arm_r=arm, arm_l=(0.3, 0.2) if expr != "terror" else (0.9, 2.3), turn=turn,
           look=(math.cos(ang), math.sin(ang) * 0.6), shiver=0.9 if expr == "terror" else 0.15,
           head_dy=-6 * eyes)
    D.flashlight(cx, hand[0], hand[1], ang, 0.9, on=k > 0.5)
    lights = beam_light(hand, ang, k)
    if t >= shadow_t - 0.3:  # the beam lands on the wall: a wide pool of light there
        wx, wy = hand[0] + math.cos(ang) * 520, hand[1] + math.sin(ang) * 520
        lights.append(("glow", wx, wy, 700, 1.0 * k))
    S.darkness(cx, 0.965, lights)
    dust(cx, t, hand, ang, k, seed=4)
    cx.restore()
    S.vignette(cx, 0.6)


def shot_end(cx, t, st, en, T):
    src(cx, (0, 0, 0, 1))
    cx.paint()
    a = smooth(prog(t, st + 0.35, st + 0.6))
    D.label(cx, "PART 3", W / 2, H / 2, 60, fill=D.YEL, outline=None, alpha=a, spacing=6, shadow=False)


SHOTS = {"couch": shot_couch, "mailwide": shot_mailwide, "window": shot_window, "pack": shot_pack,
         "yard": shot_yard, "door": shot_door, "search": shot_search, "hatch": shot_hatch,
         "hatchopen": shot_hatchopen, "descend": shot_descend, "explore": shot_explore, "end": shot_end}


def render_frame(t):
    T = timeline()[0]
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(sf)
    src(cx, (0, 0, 0, 1))
    cx.paint()
    name, st, en = shot_at(t)
    SHOTS[name](cx, t, st, en, T)
    return sf


# ============================================================ sound
def knock(glass=True):
    d = 0.25
    tt = A.t_arr(d)
    out = np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 70) * (0.5 if glass else 0.1)
    out += np.sin(2 * np.pi * 2700 * tt) * np.exp(-tt * 90) * (0.3 if glass else 0.05)
    out += A.bp(A.noise(d, 71), 600, 3000) * np.exp(-tt * 60) * 0.5
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
    x = A.bp(A.noise(d, seed), 300, 2200)
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


def plink(f=1400, d=0.18, seed=1):
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 30) * 0.5 + A.sfx_thud(220, d)[: len(tt)] * 0.5
    x += A.bp(A.noise(d, seed), 1500, 6000) * np.exp(-tt * 80) * 0.3
    return A.norm(x, 0.6)


def clatter():
    out = np.zeros(int(0.5 * SR))
    for k, dt in enumerate((0.0, 0.07, 0.15, 0.2)):
        A.add(out, plink(900 + 300 * k, 0.15, k) * (1 - 0.2 * k), dt)
    return A.norm(out, 0.6)


def flop():
    d = 0.25
    tt = A.t_arr(d)
    return A.norm(A.lp(A.noise(d, 33), 700) * np.exp(-tt * 25), 0.4)


def stair_creak(seed):
    c = A.sfx_creak()
    s = A.sfx_step(seed, heavy=True)
    out = np.zeros(max(len(c), len(s)))
    out[:len(s)] += s
    out[:len(c)] += c * (0.18 if seed % 3 else 0.35)
    return out


def bang():
    return A.norm(A.sfx_thud(55, 0.45) + A.sfx_crash_wood()[: int(0.45 * SR)] * 0.25, 0.95)


def plop():
    return A.norm(A.sfx_thud(140, 0.2) + A.lp(A.noise(0.2, 9), 900) * np.exp(-A.t_arr(0.2) * 25) * 0.6, 0.6)


def box_crash():
    d = 0.9
    tt = A.t_arr(d)
    x = A.sfx_thud(75, 0.5)
    out = np.zeros(int(d * SR))
    A.add(out, A.sfx_crash_wood()[: int(0.6 * SR)] * 0.6, 0)
    A.add(out, x, 0)
    out += A.lp(A.noise(d, 12), 1200) * np.exp(-tt * 6) * 0.25
    return A.norm(out, 0.9)


def boom(d=2.5):
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * 42 * tt * (1 - 0.15 * tt / d)) * np.exp(-tt * 1.6)
    x += A.lp(A.noise(d, 5), 220) * np.exp(-tt * 2.5) * 0.7
    x[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    return A.norm(x, 0.95)


def flicker_buzz(t0, t1, ref):
    """Electrical buzz that follows the picture's flicker."""
    n = int((t1 - t0) * SR)
    tt = np.arange(n) / SR
    gate = np.array([1.0 if flicker(t0 + i / 200, t0, t1) < 0.5 else 0.0 for i in range(int((t1 - t0) * 200) + 1)])
    g = np.repeat(gate, SR // 200)[:n]
    if len(g) < n:
        g = np.pad(g, (0, n - len(g)))
    hum = np.sign(np.sin(2 * np.pi * 120 * tt)) * 0.2
    return A.lp(hum * g, 3000) + A.hp(A.noise(t1 - t0, 44)[:n], 3000) * g * 0.1


def whisper_air(d=3.0):
    tt = A.t_arr(d)
    x = A.bp(A.noise(d, 61), 2000, 7000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * tt))
    return x * np.minimum(1, tt / 0.8) * np.minimum(1, (d - tt) / 0.8) * 0.3


def hero_steps(t0, t1, rate, ev, gain=0.25, seed=0):
    """A footstep each half walk cycle (walk phase = t * rate)."""
    k0 = math.ceil(t0 * rate / math.pi)
    k1 = math.floor(t1 * rate / math.pi)
    for k in range(k0, k1 + 1):
        ev.append((k * math.pi / rate, A.sfx_step(seed + k), gain))


def sfx_events():
    T, shots, total, _ = timeline()
    st = dict(shots)
    ev = []
    # opening: groans outside, the silhouette shuffling past
    ev += [(0.0, groan(1, 2.2, 85), 0.22), (2.4, groan(2, 1.8, 105), 0.15), (4.6, groan(5, 2.0, 92), 0.15)]
    ev.append((0.95, A.sfx_heartbeat(), 0.35))
    ev.append((1.6, A.sfx_heartbeat(), 0.3))
    n02 = T["n02"]
    ev.append((n02[0] + 0.75 * (n02[1] - n02[0]), A.sfx_boing(), 0.18))
    # mailman knocks with the package
    s0, arrive, knocks = mail_beats(T)
    for i in range(4):
        ev.append((s0 - 0.4 + i * 0.45, A.sfx_step(40 + i, heavy=True), 0.12))
    ev.append((s0 + 0.2, groan(7, 1.4, 80), 0.3))
    for kt in knocks:
        ev.append((kt, knock(), 0.7))
    ev.append((knocks[0] + 0.05, A.sfx_gasp(0.6), 0.25))
    hero_steps(knocks[-1] + 0.35, st["window"], 4.2, ev, 0.12, 5)
    ev.append((st["window"], A.sfx_whoosh(0.35, 200, 1200), 0.3))
    ev.append((st["window"] + 0.1, groan(8, 1.6, 78), 0.4))
    n06, n07, n08 = T["n06"], T["n07"], T["n08"]
    ev.append((n06[0] + 0.62 * (n06[1] - n06[0]) + 0.3, plop(), 0.55))
    for k in range(3):
        ev.append((n07[0] + 0.75 + k * 0.26, knock() * 0.7, 0.45))
    for k in range(5):
        ev.append((n08[0] + 0.1 + k * 0.12, A.glock(79 + [0, 2, 4, 7, 9][k], 0.6), 0.45))
    # backpack
    n09, n10, n11, beats = pack_beats(T)
    ev.append((n09[0] - 0.1, A.sfx_whoosh(0.35), 0.4))
    ev.append((n09[0] + 0.6, A.sfx_thud(110, 0.3), 0.6))
    ev.append((n09[0] + 0.7, zipper(0.75), 0.5))
    for names, reach, pull, rel in beats:
        ev.append((pull - 0.05, A.sfx_swish(), 0.2))
        for j, name in enumerate(names):
            land = rel + 0.12 * j + 0.38
            if name.startswith("cookie"):
                ev.append((land, plink(1500 + 300 * j, 0.18, j), 0.45))
            elif name == "charger":
                ev.append((land, clatter(), 0.5))
            else:
                ev.append((land, flop(), 0.55))
                ev.append((land + 0.15, A.sfx_wah(), 0.2))
    thumb_t = n11[0] + 0.35 * (n11[1] - n11[0])
    ev.append((thumb_t + 0.1, A.sfx_ding(), 0.4))
    ev.append((thumb_t + 0.1, A.sfx_sparkle(), 0.3))
    # yard
    clank = yard_clank(T)
    for i in range(6):
        ev.append((st["yard"] + 0.15 + i * 0.5, groan(20 + i, 1.4 + 0.3 * (i % 3), 80 + 9 * i), 0.26))
    for i in range(10):
        ev.append((st["yard"] + 0.2 + i * 0.31 + 0.05 * math.sin(i), A.sfx_step(i, heavy=True), 0.12))
    ev.append((clank, A.sfx_clank(), 0.5))
    ev.append((clank + 0.12, groan(30, 1.2, 110), 0.4))
    # door
    for k in DOOR_BANGS:
        ev.append((st["door"] + k, bang(), 0.7))
    ev.append((st["door"] + 0.3, groan(40, 2.0, 88), 0.3))
    hero_steps(st["door"] + 0.1, st["door"] + 1.0, 6, ev, 0.14, 9)
    hero_steps(st["search"] - 0.55, st["search"], 11, ev, 0.18, 12)
    # search
    n14 = T["n14"]
    d14 = n14[1] - n14[0]
    hero_steps(st["search"], st["search"] + 0.55, 9, ev, 0.16, 20)
    ev.append((n14[0] + 0.05, A.sfx_pop(), 0.3))
    ev.append((n14[0] + 0.32 * d14, A.sfx_click(), 0.4))
    ev.append((n14[0] + 0.32 * d14 + 0.28 * d14 - 0.1, A.sfx_thud(160, 0.2), 0.35))
    ev.append((n14[0] + 0.86 * d14, A.sfx_dun(), 0.3))
    for k in (0.4, 1.4):
        ev.append((st["search"] + k + 1.8, bang() * 0.4, 0.25))
    # hatch
    n15 = T["n15"]
    hero_steps(st["hatch"], st["hatch"] + 0.6, 5, ev, 0.14, 30)
    ev.append((n15[1] - 0.05, A.sfx_dun(), 0.45))
    ev.append((n15[1] + 0.55, A.sfx_gulp(), 0.5))
    ev.append((st["hatchopen"] + 0.1, A.sfx_creak(), 0.6))
    # descend
    _, steps, close_t, flash_t = descend_beats(T)
    for i, s in enumerate(steps):
        ev.append((s + 0.2, stair_creak(i), 0.42))
    ev.append((close_t, A.sfx_thud(60, 0.5), 0.8))
    ev.append((close_t + 0.05, A.sfx_creak(), 0.2))
    ev.append((flash_t, A.sfx_flashlight(), 0.7))
    hero_steps(steps[-1] + 0.25, T["n17"][0], 4.0, ev, 0.12, 50)
    ev.append((T["n17"][0] - 0.3, breath(0.9, 11, inhale=False), 0.3))
    # ending
    box_t, whip, flick0, shadow_t, stepback = explore_beats(T)
    s1, s2 = T["s01"], T["s02"]
    hero_steps(st["explore"], T["n18"][0] + 0.5, 3.2, ev, 0.1, 60)
    for k in range(3):
        ev.append((T["n18"][0] - 0.3 + k * 1.1, breath(1.0, 30 + k, inhale=k % 2 == 0), 0.45))
    ev.append((box_t + 0.38, box_crash(), 0.8))
    ev.append((whip, A.sfx_whoosh(0.25, 600, 2500), 0.3))
    for k in range(9):
        ev.append((whip + 0.3 + k * 0.52, A.sfx_heartbeat(), 0.38))
    ev.append((s1[0] - 0.4, whisper_air(s2[1] - s1[0] + 0.8), 0.6))
    ev.append((flick0, flicker_buzz(flick0, st["end"], None), 0.35))
    ev.append((shadow_t, A.sfx_dun(), 0.35))
    ev.append((stepback, A.sfx_step(77), 0.25))
    ev.append((stepback + 0.05, A.sfx_creak(), 0.15))
    ev.append((st["end"], boom(2.0), 0.85))
    return ev


def music_bed(total):
    """Dark comedy -> tension -> suspense; silence on the cut to black (the impact plays alone)."""
    T, shots, _, _ = timeline()
    st = dict(shots)
    n = int((total + 1) * SR)
    buf = np.zeros(n + 3 * SR)
    a_end = st["yard"]
    beat = 60 / 104
    seq = [62, None, 65, 62, 69, None, 68, None, 62, None, 65, 62, 70, 69, 65, None]
    bassline = [38, 38, 41, 36]
    t, i = 0.0, 0
    while t < a_end:
        nt = seq[i % len(seq)]
        if nt:
            A.add(buf, A.pluck(nt, 0.35, 0.35, seed=i) * 0.22, t)
        if i % 4 == 0:
            A.add(buf, A.bass(bassline[(i // 8) % 4], beat * 1.6) * 0.35, t)
        if i % 2 == 1:
            A.add(buf, A.woodblock(i % 4 == 1) * 0.1, t)
        t += beat / 2
        i += 1
    b0, b1 = st["yard"], st["hatchopen"]
    beat = 60 / 124
    t, k = b0, 0
    while t < b1:
        m = 38 if (k // 8) % 2 == 0 else 39
        A.add(buf, A.bass(m, beat * 0.45) * 0.42, t)
        if k % 4 == 0:
            A.add(buf, A.kick() * 0.25, t)
        if k % 2 == 1:
            A.add(buf, A.shaker() * 0.5, t)
        t += beat / 2
        k += 1
    A.add(buf, A.pad(50, b1 - b0 + 0.5, 0.2) * 0.35, b0)
    A.add(buf, A.pad(51, (b1 - b0) / 2 + 0.5, 0.15) * 0.25, b0 + (b1 - b0) / 2)
    c0, c1 = st["hatchopen"], st["end"]
    A.add(buf, A.pad(38, c1 - c0 + 0.3, 0.08) * 0.55, c0)
    A.add(buf, A.pad(45, c1 - c0 + 0.3, 0.06) * 0.25, c0 + 1.0)
    e0 = st["explore"]
    A.add(buf, A.pad(46, c1 - e0 + 0.3, 0.05) * 0.3, e0)
    # rising high cluster in the last seconds
    tt = A.t_arr(c1 - e0)
    rise = np.sin(2 * np.pi * (880 + 120 * tt / (c1 - e0)) * tt) * 0.04 * (tt / (c1 - e0)) ** 2
    A.add(buf, rise, e0)
    tt = np.arange(len(buf)) / SR
    env = np.clip(tt / 0.3, 0, 1)
    env = np.where(tt < a_end, env * np.clip((a_end - tt) / 0.4, 0, 1), env)
    env *= np.where(tt >= c1, 0.0, 1.0)
    return (buf * env)[:n]


def voice_track(total):
    T = timeline()[0]
    clips = V.clips()
    buf = np.zeros(int((total + 1) * SR))
    for lid, (s, e) in T.items():
        if lid in clips:
            c = clips[lid]
            c = c / (np.sqrt(np.mean(c ** 2)) + 1e-9) * 0.09
            if lid in ("n18", "n19", "s01", "s02"):
                c = c * 0.85
            A.add(buf, c, s)
    return buf


def mix_audio():
    import soundfile as sf
    os.makedirs(BUILD, exist_ok=True)
    T, shots, total, _ = timeline()
    n = int((total + 1) * SR)
    vox = voice_track(total)
    mus = music_bed(total)[:n]
    sfx = np.zeros(n)
    for t, x, g in sfx_events():
        A.add(sfx, np.asarray(x, dtype=np.float64) * g, t)
    if np.any(vox):
        env = A.envelope_follow(np.abs(vox), 0.02, 0.35)
        env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
    else:  # no takes yet: duck where lines are planned
        env = np.zeros(n)
        for s, e in T.values():
            env[int(s * SR):int(e * SR)] = 1.0
        env = A.envelope_follow(env, 0.03, 0.3)
    mix = vox + mus * 0.55 * (1 - 0.6 * env) + sfx * (0.8 - 0.35 * env)
    mix = np.tanh(mix * 1.1) / 1.1
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, np.stack([mix, mix], axis=1).astype(np.float32), SR)
    out = os.path.join(BUILD, "mix.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    if V.clips():
        write_srt(os.path.join(OUTDIR, OUT_NAME + ".srt"))
    print("audio ->", out, f"{total:.2f}s")
    return out


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    T = timeline()[0]
    cues = []
    for lid, _, text, _ in LINES:
        s, e = T[lid]
        if lid == "n14":
            beats = V.inner_beats("n14", 2, (0.0, 0.45))
            mid = s + beats[1]
            cues += [(s, mid - 0.05, "Quick survival tip: always plan a second exit."),
                     (mid, e, "And never enter a space without knowing how you'll escape.")]
        else:
            cues.append((s, e, text.replace("...", "…")))
    with open(path, "w") as f:
        for i, (s, e, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{txt}\n\n")
    print("srt ->", path)


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
    total = timeline()[2]
    nf = int(round(total * FPS))
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
    out = os.path.join(OUTDIR, OUT_NAME + ("_draft" if draft else "") + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("video ->", out)
    return out


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "plan"
    T, shots, total, k = timeline()
    if cmd == "plan":
        for n, s in shots:
            print(f"{s:6.2f}  [{n}]")
        for lid, (s, e) in T.items():
            print(f"   {s:6.2f}-{e:6.2f} {lid} {TEXT[lid]}")
        print(f"total {total:.2f}s  gap scale {k:.2f}  (voice clips: {len(V.clips())})")
    elif cmd == "stills":
        os.makedirs(BUILD, exist_ok=True)
        for x in a[1:]:
            render_frame(float(x)).write_to_png(os.path.join(BUILD, f"still_{float(x):06.2f}.png"))
    elif cmd in ("sheet", "strip"):
        os.makedirs(BUILD, exist_ok=True)
        if cmd == "sheet":
            n = int(a[1]) if len(a) > 1 else 24
            times = [(i + 0.5) * total / n for i in range(n)]
            cols = 8
        else:
            t0, t1 = float(a[1]), float(a[2])
            fps = float(a[3]) if len(a) > 3 else 4
            times = [t0 + i / fps for i in range(int((t1 - t0) * fps) + 1)]
            cols = min(8, len(times))
        rows = (len(times) + cols - 1) // cols
        tw, th = 270, 480
        sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, cols * tw, rows * th)
        c = cairo.Context(sheet)
        for i, t in enumerate(times):
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
            c.show_text(f"{t:.2f}")
        sheet.write_to_png(os.path.join(BUILD, cmd + ".png"))
    elif cmd == "audio":
        mix_audio()
    elif cmd == "video":
        render_video(draft="--draft" in a)


if __name__ == "__main__":
    main()

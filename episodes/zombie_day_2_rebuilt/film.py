"""Just Needy: Zombie Apocalypse, Day 2 "Don't Open the Door" (rebuilt). Timeline, shots, sound, SRT, render.

usage:
  python -m episodes.zombie_day_2_rebuilt.film plan
  python -m episodes.zombie_day_2_rebuilt.film stills t1 t2 ...
  python -m episodes.zombie_day_2_rebuilt.film sheet [n]
  python -m episodes.zombie_day_2_rebuilt.film strip t0 t1 [fps]
  python -m episodes.zombie_day_2_rebuilt.film audio
  python -m episodes.zombie_day_2_rebuilt.film video [--draft]
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
from episodes.zombie_day_2_rebuilt import draw as D
from episodes.zombie_day_2_rebuilt import sets as S
from episodes.zombie_day_2_rebuilt import voice as V
from episodes.zombie_day_2_rebuilt.script import NARRATION, TEXT, TITLE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "day2_rebuilt")
OUTDIR = os.path.join(ROOT, "output")
W, H, FPS = D.W, D.H, D.FPS
SR = A.SR
TARGET = 60.0

EXT_TINT = (0.70, 0.77, 0.88)
INT_TINT = (0.60, 0.65, 0.76)

# ============================================================ timeline
PLAN = [
    ("shot", "ext_knock"), ("wait", 1.05, False), ("line", "l01", 0.0),
    ("shot", "eyes"), ("line", "l02", 0.35),
    ("shot", "approach"), ("line", "l03", 0.3),
    ("shot", "peek"), ("line", "l04", 0.45), ("line", "l05", 0.35),
    ("shot", "lock"), ("line", "l06", 0.3), ("wait", 0.6, True),
    ("shot", "science"), ("line", "l07", 0.2), ("line", "l08", 0.35), ("line", "l09", 0.35), ("line", "l10", 0.45),
    ("line", "l11", 0.25), ("wait", 0.5, True),
    ("shot", "decide"), ("line", "l12", 0.1),
    ("shot", "talk"), ("line", "l13", 0.4),
    ("shot", "radio"), ("line", "l14", 0.4),
    ("shot", "dial"), ("line", "l15", 0.25), ("wait", 0.6, True),
    ("shot", "ots"), ("line", "l16", 0.25),
    ("shot", "barn"), ("line", "l17", 0.3),
    ("shot", "faces"), ("line", "l18", 0.15),
    ("shot", "heroeyes"), ("line", "l19", 0.25),
    ("shot", "corn"), ("line", "l20", 0.25), ("wait", 0.5, True),
    ("shot", "yard"), ("line", "l21", 0.2), ("line", "l22", 0.6),
    ("shot", "herofear"), ("line", "l23", 0.5), ("wait", 0.55, False),
    ("shot", "thing"), ("line", "l24", 0.0), ("wait", 0.65, False),
    ("shot", "end"), ("wait", 1.3, False),
]
# shots that start with a line begin slightly before the voice (cut lands on the breath before the line)
LEAD = 0.12


@functools.lru_cache(maxsize=None)
def timeline():
    dur = V.durations()
    speech = sum(dur[e[1]] for e in PLAN if e[0] == "line")
    fixed = sum(e[1] for e in PLAN if e[0] == "wait" and not e[2])
    scal = sum(e[1] for e in PLAN if e[0] == "wait" and e[2]) + sum(e[2] for e in PLAN if e[0] == "line")
    k = clamp((TARGET - speech - fixed) / scal, 0.4, 2.0)
    t = 0.0
    T = {}
    shots = []
    pending = None
    for ev in PLAN:
        if ev[0] == "shot":
            pending = ev[1]
            if not shots:
                shots.append([ev[1], 0.0])
                pending = None
        elif ev[0] == "wait":
            if pending:
                shots.append([pending, t])
                pending = None
            t += ev[1] * (k if ev[2] else 1.0)
        else:
            t += ev[2] * k
            if pending:
                shots.append([pending, max(shots[-1][1] + 0.3, t - LEAD)])
                pending = None
            T[ev[1]] = (t, t + dur[ev[1]])
            t = T[ev[1]][1]
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


def blink(t, seed=0, period=3.7):
    p = (t + seed * 1.37) % period
    return 1.0 if p < 0.1 else 0.0


def pend(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            x = smooth(prog(t, a, b))
            if isinstance(va, tuple):
                return tuple(p + (q - p) * x for p, q in zip(va, vb))
            return va + (vb - va) * x
    return keys[-1][1]


def ik(sh, target, l1, l2, bend=1):
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = clamp(math.hypot(dx, dy), 1.0, l1 + l2 - 0.5)
    base = math.atan2(dx, dy)
    a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    a1 = base + bend * a
    ex, ey = sh[0] + math.sin(a1) * l1, sh[1] + math.cos(a1) * l1
    return a1, math.atan2(target[0] - ex, target[1] - ey)


def arm_to(x, gy, s, side, target, crouch=0.0):
    hip = gy - 150 * s * (1 - 0.42 * crouch)
    sh = (x + side * 74 * s, hip - 179 * s)
    return ik(sh, target, 82 * s, 78 * s, -side)


def cam_apply(cx, x, y, z):
    cx.translate(W / 2, H / 2)
    cx.scale(z, z)
    cx.translate(-x, -y)


def post(cx, t, tint, fog_k=0.0, vig=0.6):
    S.grade(cx, tint)
    if fog_k:
        S.fog(cx, t, H * 0.55, H * 0.95, k=0.08 * fog_k, seed=21, speed=12)
    S.vignette(cx, vig)
    S.grain(cx, t, 0.07)


def accent(cx, text, t, t0, t1, y, size=46, col=None, spacing=8):
    a = smooth(prog(t, t0, t0 + 0.35)) * (1 - smooth(prog(t, t1 - 0.35, t1)))
    if a <= 0:
        return
    col = col or S.MUTED_WHITE
    dy = 10 * (1 - smooth(prog(t, t0, t0 + 0.5)))
    D.label(cx, text, W / 2, y + dy, size, fill=col, outline=None, alpha=a, spacing=spacing, shadow=False)


# ============================================================ characters
NEIGHBOR = dict(cloth=hexc("#6a4a3e"), hood=False, hat="cap", hat_col=hexc("#4b4a3c"), dirt=True)
WOMAN = dict(cloth=hexc("#4a5a52"), hood=False, hat="beanie", hat_col=hexc("#5a3c36"), dirt=True)
CHILD = dict(cloth=hexc("#7d3735"), hood=False, dirt=True)
ELDER = dict(cloth=hexc("#4f5560"), hood=False, hat="cap", hat_col=hexc("#2e3136"), dirt=True)


def neighbor_at_door(t, T, knocks):
    """Figure on the porch (exterior world coords), knocking heavily."""
    def fig(cx):
        k = 0.0
        for kt in knocks:
            if t >= kt - 0.12:
                k = max(k, math.exp(-max(0, t - kt) * 10) * (1 if t >= kt else (t - kt + 0.12) / 0.12))
        D.hero(cx, 545, 1212, 0.42, expr="tired", t=t, turn=-0.9, look=(-1, 0), blink=blink(t, 3),
               arm_l=(-2.3 + 0.5 * k, -2.0 + 0.6 * k), tilt=0.05 * math.sin(t * 1.3), **NEIGHBOR)
    return fig


# ============================================================ shots
def knock_times():
    st = st_of("ext_knock")
    return [st + 0.08, st + 0.42, st + 0.76]


def shot_ext_knock(cx, t, st, en, T):
    lt = t - st
    cam = (pend(t, [(st, 700), (en, 580)]), pend(t, [(st, 1060), (en, 1110)]), pend(t, [(st, 1.15), (en, 1.55)]))
    S.exterior(cx, t, cam, door_figure=neighbor_at_door(t, T, knock_times()))
    post(cx, t, EXT_TINT, vig=0.65)
    accent(cx, "DAY 2", t, st + 0.1, st + 2.6, 170, 44, spacing=12)
    a = smooth(prog(lt, 0.3, 0.8)) * (1 - smooth(prog(lt, 2.2, 2.6)))
    if a > 0:
        w = 70 * smooth(prog(lt, 0.3, 0.9))
        for side in (-1, 1):
            line(cx, [(W / 2 + side * 100, 170), (W / 2 + side * (100 + w), 170)], (*S.AMBER[:3], a * 0.9), 3)


def hero_close(cx, t, x, y, R, **kw):
    """The hero's head in close-up; (x, y) = head centre on screen, R = head radius."""
    s = R / 142
    gy = y + (0.66 * 142 + 205 + 150) * s - (kw.pop("head_dy", 0) or 0) * s
    return D.hero(cx, x, gy, s, t=t, **kw)


def shot_eyes(cx, t, st, en, T):
    lt = t - st
    S.hallway(cx, t, moon=0.6)
    src(cx, (0, 0, 0, 0.35))
    cx.paint()
    look_x = -smooth(prog(lt, 0.35, 1.3))
    hero_close(cx, t, 560 + 20 * math.sin(lt * 0.5), 980, 470, expr="worried", look=(look_x, -0.1),
               blink=1.0 if 1.6 < lt < 1.7 else 0.0, turn=-0.18 * smooth(prog(lt, 0.9, 1.8)), arm_l=(0.1, 0.1),
               arm_r=(-0.1, -0.1))
    # cold light from the left
    g = cairo.LinearGradient(0, 0, W, 0)
    g.add_color_stop_rgba(0, 0.6, 0.7, 0.85, 0.12)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    cx.set_source(g)
    cx.paint()
    post(cx, t, INT_TINT, vig=0.7)


def neighbor_in_sidelight(t, T, scale=0.55, gesture=0.0):
    def draw(cx, rect):
        x0, y0, w, h = rect
        S.fog(cx, t, y0 + h * 0.4, y0 + h, k=0.25, seed=13, x0=x0 - 200, x1=x0 + w + 200)
        D.hero(cx, x0 + w * 0.5, y0 + h * 1.05, scale, expr="worried", t=t, turn=-0.3, look=(-0.6, 0),
               blink=blink(t, 5), **NEIGHBOR)
    return draw


def shot_approach(cx, t, st, en, T):
    lt = t - st
    S.hallway(cx, t, outside_draw=neighbor_in_sidelight(t, T))
    x = pend(t, [(st, 1010), (en, 860)])
    D.hero(cx, x, 1720, 1.05, expr="worried", t=t, walk=t * 2.6, look=(-1, -0.2), turn=-0.35,
           blink=blink(t, 2), arm_l=(0.55 + 0.05 * math.sin(t * 2.6), 1.5), arm_r=(0.2, 0.9), lean=-0.04)
    post(cx, t, INT_TINT, fog_k=0.0, vig=0.65)


def knock_times_2(T):
    s, e = T["l03"]
    return [s + 0.62 * (e - s), s + 0.62 * (e - s) + 0.38]


def peek_scene(cx, t, push, neigh_kw, ots=True):
    """Through the tall sidelight: the neighbor on the porch. Over-the-shoulder hero in the foreground."""
    cx.save()
    cam_apply(cx, 540, 960, 1.0 + push)
    S.panel_wall(cx, -200, -200, W + 200, H + 200)
    wx, wy, ww, wh = 230, 170, 620, 1560
    cx.save()
    cx.rectangle(wx, wy, ww, wh)
    cx.clip()
    g = cairo.LinearGradient(0, wy, 0, wy + wh)
    g.add_color_stop_rgba(0, *hexc("#56636e"))
    g.add_color_stop_rgba(0.6, *hexc("#3a444b"))
    g.add_color_stop_rgba(1, *hexc("#262c30"))
    cx.set_source(g)
    cx.paint()
    S.treeline(cx, wy + 760, 260, hexc("#26302f"), 7, x0=wx - 100, x1=wx + ww + 100, t=t)
    cx.rectangle(wx, wy + 1050, ww, 600)
    src(cx, hexc("#3a3631"))
    cx.fill()
    line(cx, [(wx + 70, wy), (wx + 70, wy + 1100)], hexc("#2e2a26"), 26)       # porch post
    S.fog(cx, t, wy + 500, wy + 1100, k=0.22, seed=17, x0=wx - 200, x1=wx + ww + 200, speed=16)
    kw = dict(NEIGHBOR)
    kw.update(neigh_kw)
    D.hero(cx, 560, 2120, 1.55, **kw)
    # rain-streaked glass + reflection
    r = random.Random(4)
    for k in range(18):
        x = wx + r.uniform(0, ww)
        y = wy + (r.uniform(0, wh) + t * r.uniform(30, 80)) % wh
        line(cx, [(x, y), (x + 2, y + r.uniform(30, 90))], (0.8, 0.85, 0.9, 0.12), 3)
    cx.move_to(wx + ww * 0.1, wy + wh)
    cx.line_to(wx + ww * 0.55, wy)
    cx.line_to(wx + ww * 0.7, wy)
    cx.line_to(wx + ww * 0.25, wy + wh)
    src(cx, (1, 1, 1, 0.05))
    cx.fill()
    cx.restore()
    cx.rectangle(wx, wy, ww, wh)
    fs(cx, None, hexc("#48443e"), 30)
    for k in (1, 2):
        line(cx, [(wx, wy + k * wh / 3), (wx + ww, wy + k * wh / 3)], hexc("#48443e"), 16)
    cx.restore()
    if ots:
        D.hero_back(cx, 130 - 40 * push, 1640, 1.35, t=t)


def shot_peek(cx, t, st, en, T):
    lt = t - st
    push = 0.12 * smooth(prog(t, st, en))
    l04, l05 = T["l04"], T["l05"]
    glance = 0.0
    if l04[1] < t < l05[0] + 0.3:
        glance = smooth(prog(t, l04[1], l04[1] + 0.3)) * (1 - smooth(prog(t, l05[0], l05[0] + 0.3)))
    kw = dict(expr="tired" if t < l05[0] else "worried", t=t, turn=0.7 * glance - 0.1, look=(0.9 * glance, 0.1),
              blink=blink(t, 5, 2.9), head_dy=3 * math.sin(t * 2.2),
              arm_l=(-0.1, -0.15) if lt > 0.9 else (-2.0, -2.9 + 0.15 * math.sin(t * 8)),
              arm_r=(0.15, 0.1))
    peek_scene(cx, t, push, kw)
    post(cx, t, INT_TINT, vig=0.6)


def shot_lock(cx, t, st, en, T):
    lt = t - st
    l06 = T["l06"]
    z = 1.0 + 0.1 * smooth(prog(t, st, en))
    cx.save()
    cam_apply(cx, 560, 960, z)
    # door surface in close-up
    cx.rectangle(-200, -200, W + 400, H + 400)
    src(cx, hexc("#2f2722"))
    cx.fill()
    r = random.Random(11)
    for k in range(40):
        y = r.uniform(-200, H + 200)
        cx.move_to(-200, y)
        cx.curve_to(300, y + r.uniform(-20, 20), 700, y + r.uniform(-20, 20), W + 200, y + r.uniform(-30, 30))
        src(cx, (0.12, 0.09, 0.08, 0.35))
        cx.set_line_width(r.uniform(2, 5))
        cx.stroke()
    line(cx, [(-200, 300), (W + 200, 300)], hexc("#211b18"), 14)
    # deadbolt plate + thumb turn + chain
    rrect(cx, 430, 760, 220, 400, 24)
    fs(cx, hexc("#5e5038"), S.INK, 5)
    ellipse(cx, 540, 900, 70, 70)
    fs(cx, hexc("#4b402c"), S.INK, 5)
    turn_a = 0.0
    cx.save()
    cx.translate(540, 900)
    cx.rotate(turn_a)
    rrect(cx, -22, -62, 44, 124, 14)
    fs(cx, hexc("#7a6a48"), S.INK, 5)
    cx.restore()
    ellipse(cx, 540, 1060, 34, 34)
    fs(cx, hexc("#2a231b"), S.INK, 4)
    chain = [(380 + k * 34, 520 + 60 * math.sin(k * 0.45) + 4 * math.sin(t * 2)) for k in range(9)]
    for p in chain:
        ellipse(cx, p[0], p[1], 16, 10, 0.4)
        fs(cx, None, hexc("#8a8a86"), 7)
    # the hand: approaches, stops just short, trembles, draws back
    hx, hy = pend(t, [(st, (1200, 1500)), (l06[0] + 0.15, (660, 990)), (l06[1] - 0.15, (630, 960)),
                      (en - 0.1, (820, 1150))])
    if l06[0] < t < en - 0.4:
        hx += noise1(t * 30, 2) * 5
        hy += noise1(t * 30, 6) * 5
    D.sleeve(cx, [(1250, 1700), (hx + 160, hy + 230), (hx + 30, hy + 40)], 150)
    ellipse(cx, hx, hy, 70, 62)
    src(cx, D.INK)
    cx.fill()
    cx.restore()
    # cold sliver of light from the sidelight
    g = cairo.LinearGradient(0, 0, W, 0)
    g.add_color_stop_rgba(0, 0.6, 0.7, 0.85, 0.18)
    g.add_color_stop_rgba(0.5, 0.6, 0.7, 0.85, 0.0)
    cx.set_source(g)
    cx.paint()
    post(cx, t, INT_TINT, vig=0.7)


# ---------------------------------------------------------------- science
def silhouette(cx, x, gy, s, col, hunch=0.0, walk=None):
    """Plain stick-figure silhouette for the motion graphic."""
    cx.save()
    leg = 120 * s
    hip = gy - leg
    for side in (-1, 1):
        a = 0 if walk is None else math.sin(walk + (0 if side < 0 else math.pi)) * 0.3
        line(cx, [(x, hip), (x + math.sin(a) * leg + side * 8 * s, gy)], col, 12 * s)
    top = hip - 150 * s
    line(cx, [(x, hip), (x + 30 * s * hunch, top)], col, 16 * s)
    for side in (-1, 1):
        line(cx, [(x + 30 * s * hunch, top + 15 * s), (x + side * 45 * s + 30 * s * hunch, top + 110 * s)], col,
             11 * s)
    ellipse(cx, x + 45 * s * hunch, top - 55 * s + 20 * s * hunch, 48 * s, 48 * s)
    src(cx, col)
    cx.fill()
    cx.restore()


def shot_science(cx, t, st, en, T):
    l07, l08, l09, l10, l11 = (T[k] for k in ("l07", "l08", "l09", "l10", "l11"))
    # background: charcoal, faint grid, slow drift
    src(cx, S.CHAR)
    cx.paint()
    off = (t * 6) % 80
    for k in range(-1, 15):
        line(cx, [(k * 80 + off, 0), (k * 80 + off, H)], (0.3, 0.36, 0.4, 0.08), 1.5)
    for k in range(25):
        line(cx, [(0, k * 80), (W, k * 80)], (0.3, 0.36, 0.4, 0.08), 1.5)
    g = cairo.RadialGradient(W / 2, H * 0.48, 50, W / 2, H * 0.48, 900)
    g.add_color_stop_rgba(0, 0.16, 0.22, 0.3, 0.6)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cx.set_source(g)
    cx.paint()
    fade_all = 1 - smooth(prog(t, en - 0.35, en))
    cx.push_group()
    ty = 1180
    x_e, x_s = 150, 930
    grow = smooth(prog(t, st + 0.1, l07[1]))
    cold = (0.44, 0.5, 0.55, 1)
    line(cx, [(x_e, ty), (x_e + (x_s + 40 - x_e) * grow, ty)], cold, 5)
    if grow > 0.98:
        line(cx, [(x_s + 20, ty - 16), (x_s + 40, ty), (x_s + 20, ty + 16)], cold, 5)
    # nodes + labels
    nodes = ((x_e, "EXPOSURE", l07[0] + 0.3), ((x_e + x_s) / 2, "INCUBATION", l08[0] + 0.2), (x_s, "SYMPTOMS",
                                                                                             l08[0] + 0.9))
    for x, lab, t0 in nodes:
        a = smooth(prog(t, t0, t0 + 0.35))
        if a <= 0:
            continue
        ellipse(cx, x, ty, 14 * a, 14 * a)
        fs(cx, S.CHAR, S.MUTED_WHITE, 4)
        D.label(cx, lab, x, ty + 70, 30, fill=(*S.MUTED_WHITE[:3], 0.85), outline=None, alpha=a, spacing=3,
                shadow=False)
    # incubation band
    band = smooth(prog(t, l08[0] + 0.3, l08[0] + 1.0))
    if band > 0:
        cx.rectangle(x_e + 14, ty - 22, (x_s - x_e - 28) * band, 44)
        src(cx, (*S.AMBER[:3], 0.22))
        cx.fill()
        line(cx, [(x_e + 14, ty - 22), (x_e + 14 + (x_s - x_e - 28) * band, ty - 22)], (*S.AMBER[:3], 0.7), 2)
        line(cx, [(x_e + 14, ty + 22), (x_e + 14 + (x_s - x_e - 28) * band, ty + 22)], (*S.AMBER[:3], 0.7), 2)
    # the person moving along the timeline: exposure particle, looks fine, then symptoms
    px = pend(t, [(l07[0] + 0.3, x_e), (l08[0] + 0.5, x_e + 40), (l09[1], (x_e + x_s) / 2 + 200),
                  (l10[0], (x_e + x_s) / 2 + 220)])
    walking = l08[0] + 0.5 < t < l09[1]
    sym = smooth(prog(t, l08[1] - 0.6, l08[1])) * (1 - smooth(prog(t, l09[0], l09[0] + 0.3)))
    a_p = smooth(prog(t, l07[0] + 0.2, l07[0] + 0.6))
    if a_p > 0:
        col = (0.78, 0.8, 0.8, a_p)
        if sym > 0:  # preview of the symptomatic stage at the end of the line
            silhouette(cx, x_s, ty - 60, 1.1, (*S.RUST[:3], 0.9 * sym), hunch=0.6)
        silhouette(cx, px, ty - 60, 1.1, col, walk=t * 5 if walking else None)
        # exposure particles
        if l07[0] + 0.3 < t < l08[0] + 0.3:
            for k in range(6):
                ph = (t * 1.2 + k / 6) % 1
                ex = x_e - 120 + 120 * ph
                ey = ty - 300 + 40 * math.sin(k * 2 + t * 3)
                ellipse(cx, ex, ey, 7, 7)
                src(cx, (0.85, 0.85, 0.82, 0.6 * (1 - ph)))
                cx.fill()
    # presymptomatic spread: dotted arcs from the (healthy-looking) person to another
    sp = smooth(prog(t, l09[0] + 0.2, l09[1] - 0.2))
    fade_sp = 1 - smooth(prog(t, l10[0], l10[0] + 0.5))
    if sp > 0 and fade_sp > 0:
        bx = W - 150
        silhouette(cx, bx, ty - 60, 1.1, (0.78, 0.8, 0.8, fade_sp))
        for k in range(3):
            ph = (t * 0.9 + k / 3) % 1
            for j in range(10):
                f = j / 10
                if f > ph:
                    break
                x = px + 50 + (bx - px - 100) * f
                y = ty - 300 - 160 * math.sin(math.pi * f) + k * 30
                ellipse(cx, x, y, 6, 6)
                src(cx, (*S.AMBER[:3], 0.8 * sp * fade_sp * (1 - (ph - f))))
                cx.fill()
        ring = 0.5 + 0.5 * math.sin(t * 5)
        ellipse(cx, bx, ty - 360, 80 + 8 * ring, 80 + 8 * ring)
        fs(cx, None, (*S.AMBER[:3], 0.5 * sp * fade_sp), 3)
        ellipse(cx, px + 30, ty - 360, 80, 80)
        fs(cx, None, (*S.AMBER[:3], 0.35 * sp * fade_sp), 3)
    # "But this outbreak?" — the model breaks down: routes become question marks
    q = smooth(prog(t, l10[0] + 0.1, l10[0] + 0.6))
    if q > 0:
        for k, (dx, dy) in enumerate(((-260, -520), (0, -600), (260, -520))):
            a = q * (0.55 + 0.45 * math.sin(t * 2 + k))
            cx.set_dash([10, 12])
            line(cx, [(px + 30, ty - 360), (px + 30 + dx * 0.8, ty - 360 + dy * 0.55)], (0.75, 0.78, 0.8, 0.5 * a), 4)
            cx.set_dash([])
            D.label(cx, "?", px + 30 + dx * 0.9, ty - 360 + dy * 0.65, 72, fill=(*S.MUTED_WHITE[:3], a), outline=None,
                    shadow=False)
    cx.pop_group_to_source()
    cx.paint_with_alpha(fade_all)
    accent(cx, "INCUBATION PERIOD", t, l08[0] + 0.35, l09[0] + 0.1, 520, 52, col=S.AMBER, spacing=5)
    accent(cx, "TRANSMISSION UNKNOWN", t, l11[0] - 0.05, en, 330, 52, col=S.MUTED_WHITE, spacing=5)
    if t > l11[0]:  # quiet rust pulse
        a = 0.12 * (0.5 + 0.5 * math.sin((t - l11[0]) * 4)) * fade_all
        g = cairo.RadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 1000)
        g.add_color_stop_rgba(0, *S.RUST[:3], a)
        g.add_color_stop_rgba(1, *S.RUST[:3], 0)
        cx.set_source(g)
        cx.paint()
    S.vignette(cx, 0.55)
    S.grain(cx, t, 0.06)


# ---------------------------------------------------------------- decision, radio
def shot_decide(cx, t, st, en, T):
    lt = t - st
    S.hallway(cx, t, outside_draw=neighbor_in_sidelight(t, T))
    # hand comes off the bolt, a step back, palm flat on the door
    x = pend(t, [(st, 700), (st + 0.8, 780)])
    walking = lt < 0.8
    reach = pend(t, [(st, 1.0), (st + 0.5, 0.0), (en - 0.7, 0.0), (en - 0.25, 0.8)])
    tgt = (540 + 60 * (1 - reach), 900 + 120 * (1 - reach))
    D.hero(cx, x, 1720, 1.05, expr="worried", t=t, walk=t * 2.4 if walking else None, turn=-0.45, look=(-1, 0),
           blink=blink(t, 4), arm_l=arm_to(x, 1720, 1.05, -1, tgt), arm_r=(0.15, 0.5))
    post(cx, t, INT_TINT, vig=0.65)


def shot_talk(cx, t, st, en, T):
    lt = t - st
    l13 = T["l13"]
    # neighbor talks and points towards the barn; our hero stays behind the glass, palm raised: keep back
    point = smooth(prog(t, l13[0] + 0.3, l13[0] + 0.8))
    kw = dict(expr="worried", t=t, turn=0.25 * point - 0.1, look=(0.6 * point - 0.2, 0), blink=blink(t, 6),
              head_dy=3 * math.sin(t * 2.2), talk=abs(math.sin(t * 11)) * 0.6 if lt < en - st - 0.3 else 0,
              arm_r=(0.2 + 1.5 * point, 0.3 + 1.6 * point), arm_l=(-0.15, -0.1))
    peek_scene(cx, t, 0.06, kw, ots=False)
    # hero's raised palm against the inside of the frame, foreground
    D.sleeve(cx, [(-60, 1950), (80, 1650), (120, 1450)], 120)
    ellipse(cx, 125, 1420, 58, 66)
    src(cx, D.INK)
    cx.fill()
    post(cx, t, INT_TINT, vig=0.6)


def kitchen_window_view(t, cam):
    def draw(cx, rect):
        x0, y0, w, h = rect
        cx.save()
        cx.translate(x0, y0)
        cx.scale(w / W, w / W)
        cx.translate(0, -(H - h * W / w) / 2)
        S.exterior(cx, t, cam)
        cx.restore()
    return draw


def shot_radio(cx, t, st, en, T):
    lt = t - st
    S.kitchen_dark(cx, t, window_draw=kitchen_window_view(t, (1500, 1050, 0.9)), led=0.6)
    lift = smooth(prog(lt, 0.5, 1.2))
    rx, ry = 700 - 90 * lift, 1390 - 230 * lift
    D.hero(cx, 520, 1600, 1.15, expr="worried", t=t, blink=blink(t, 3), look=(0.6, 0.6), turn=0.2,
           arm_r=arm_to(520, 1600, 1.15, 1, (rx - 60, ry - 20)), arm_l=arm_to(520, 1600, 1.15, -1, (rx - 170, ry)))
    S.table_top(cx)
    S.radio(cx, rx, ry, 0.5, dial=0.2, t=t, led=1.0, static=0.4)
    post(cx, t, INT_TINT, vig=0.65)


def shot_dial(cx, t, st, en, T):
    lt = t - st
    S.kitchen_dark(cx, t, led=1.0)
    src(cx, (0, 0, 0, 0.45))
    cx.paint()
    dial = 0.2 + 0.55 * smooth(prog(lt, 0.1, en - st - 0.2)) + 0.02 * math.sin(t * 9)
    S.radio(cx, 520, 1050, 1.9, dial=dial, t=t, led=0.8 + 0.2 * math.sin(t * 6), static=1.0)
    # fingers on the knob: the hand turns with the dial
    kx, ky = 520 + 100 * 1.9, 1050 + 40 * 1.9
    a = dial * 5.5
    D.sleeve(cx, [(1250, 1700), (kx + 260, ky + 260), (kx + 70, ky + 60)], 150)
    for k in (-1, 1):
        ellipse(cx, kx + math.cos(a + k * 1.2) * 70, ky + math.sin(a + k * 1.2) * 70, 34, 30)
        src(cx, D.INK)
        cx.fill()
    post(cx, t, INT_TINT, vig=0.65)


# ---------------------------------------------------------------- something is wrong
SURVIVORS = [(1490, 1255, 0.5, WOMAN, 0.0), (1545, 1262, 0.34, CHILD, 0.6), (1610, 1250, 0.52, ELDER, 1.3)]


def survivors(t, react=1.0):
    def fig(cx):
        for (x, gy, s, kw, seed) in SURVIVORS:
            D.hero(cx, x, gy, s, expr="scared", t=t + seed, turn=0.75, look=(1, -0.1), blink=blink(t, seed * 3),
                   tilt=0.03 * math.sin(t * 1.4 + seed), arm_l=(0.5, 1.4) if kw is CHILD else (0.25, 0.6),
                   arm_r=(-0.1, 0.4), shiver=0.3, **kw)
    return fig


def shot_ots(cx, t, st, en, T):
    lt = t - st
    push = 0.1 * smooth(prog(t, st, en))
    cam = (pend(t, [(st, 1350), (en, 1600)]), 1050, 0.95)
    cx.save()
    cam_apply(cx, 540, 900, 1 + push)
    S.kitchen_dark(cx, t, window_draw=kitchen_window_view(t, cam), led=0.4)
    cx.restore()
    D.hero_back(cx, 260, 1500, 1.5, t=t, turn=math.sin(t) * 0.5)
    post(cx, t, INT_TINT, vig=0.6)


def shot_barn(cx, t, st, en, T):
    cam = (pend(t, [(st, 1560), (en, 1640)]), 1090, pend(t, [(st, 1.75), (en, 1.9)]))
    S.exterior(cx, t, cam, actors_mid=survivors(t))
    post(cx, t, EXT_TINT, vig=0.62)


def shot_faces(cx, t, st, en, T):
    lt = t - st
    # dark barn boards behind them
    src(cx, hexc("#2c1c1b"))
    cx.paint()
    for k in range(14):
        line(cx, [(k * 80 + 20, 0), (k * 80 + 20, H)], hexc("#1f1413"), 6)
    S.fog(cx, t, 400, 1700, k=0.18, seed=31)
    hero_close(cx, t, 330, 960, 230, expr="scared", turn=0.8, look=(1, -0.05), blink=blink(t, 2, 2.6),
               head_dy=4 * math.sin(t * 3), shiver=0.5, **WOMAN)
    hero_close(cx, t, 760, 1260, 170, expr="terror", turn=0.75, look=(1, 0), blink=0, shiver=0.6,
               head_dy=3 * math.sin(t * 3.4), **CHILD)
    post(cx, t, EXT_TINT, vig=0.7)


def shot_heroeyes(cx, t, st, en, T):
    lt = t - st
    S.kitchen_dark(cx, t, led=0.3)
    src(cx, (0, 0, 0, 0.3))
    cx.paint()
    lx = smooth(prog(lt, 0.15, 0.9))
    hero_close(cx, t, 520, 960, 440, expr="worried", look=(lx, -0.05), turn=0.2 * lx, blink=0,
               arm_l=(0.1, 0.1), arm_r=(-0.1, -0.1))
    g = cairo.LinearGradient(0, 0, W, 0)   # pale window light from the right
    g.add_color_stop_rgba(0, 0, 0, 0, 0.35)
    g.add_color_stop_rgba(1, 0.65, 0.75, 0.9, 0.16)
    cx.set_source(g)
    cx.paint()
    post(cx, t, INT_TINT, vig=0.7)


def corn_disturb(t, t0, t1, x0=2250, x1=2700):
    if t < t0:
        return None
    f = prog(t, t0, t1)
    return (x0 + (x1 - x0) * f, 1.0 * math.sin(math.pi * min(1, f * 1.2)) + 0.3)


def shot_corn(cx, t, st, en, T):
    cam = (pend(t, [(st, 2420), (en, 2470)]), pend(t, [(st, 1000), (en, 1030)]), pend(t, [(st, 1.35), (en, 1.6)]))
    S.exterior(cx, t, cam, corn_disturb=corn_disturb(t, st + 0.2, en + 1.0))
    post(cx, t, EXT_TINT, vig=0.7)


YARD_INF = [  # (zombie, x, ground y, scale, wander dir)
    (D.INFECTED[0], 1430, 1330, 0.55, 1),
    (D.INFECTED[1], 1600, 1420, 0.6, -1),
    (D.INFECTED[2], 1760, 1360, 0.52, 1),
    (D.INFECTED[3], 1880, 1470, 0.66, -1),
    (D.INFECTED[4], 1330, 1500, 0.7, 1),
]


def yard_actors(t, T):
    l21, l22 = T["l21"], T["l22"]
    stop = l21[0] + 0.25
    backs = [l22[0] + 0.2 + k * 0.45 for k in range(len(YARD_INF))]
    backs = [backs[i] for i in (2, 0, 3, 1, 4)]

    def fig(cx):
        for i, (z, x0, gy, s, d) in enumerate(YARD_INF):
            if t < stop:  # aimless shamble
                x = x0 + d * 22 * (t - st_of("yard")) * z.speed
                D.zombie(cx, z, x, gy, s, t + i, face_dir=d, phase=t * z.speed * 3.0 + i * 1.7,
                         look=(d * 0.3, 0.4))
                continue
            x_stop = x0 + d * 22 * (stop - st_of("yard")) * z.speed
            react = smooth(prog(t, stop + i * 0.06, stop + i * 0.06 + 0.12))   # head snaps to the corn
            bt = backs[i]
            back = max(0.0, t - bt)
            x = x_stop - 55 * back * (1 + 0.3 * (i % 2))
            guard = smooth(prog(t, bt - 0.2, bt + 0.4))
            arms = ((-0.15, -0.05), (0.2 + 1.0 * guard, 0.3 + 1.9 * guard))
            D.zombie(cx, z, x, gy, s, t + i, face_dir=1, walking=back > 0, phase=-(back * 2.6) + i,
                     head_add=0.45 * react - z.tilt0 * 0.6 * react, look=(1, -0.2), jaw=0.15 if back > 0 else None,
                     arms=arms if t > stop + 0.3 else None)
    return fig


def shot_yard(cx, t, st, en, T):
    l21 = T["l21"]
    cam = (pend(t, [(st, 1700), (l21[1], 1730), (en, 1690)]), 1200, pend(t, [(st, 1.5), (en, 1.62)]))
    S.exterior(cx, t, cam, actors_mid=yard_actors(t, T), corn_disturb=corn_disturb(t, T["l21"][0], en + 3,
                                                                                    2500, 2650))
    post(cx, t, EXT_TINT, vig=0.62)


def shot_herofear(cx, t, st, en, T):
    lt = t - st
    l23 = T["l23"]
    S.kitchen_dark(cx, t, led=0.3)
    src(cx, (0, 0, 0, 0.3))
    cx.paint()
    if t < l23[0] + 0.35:
        expr = "worried"
    elif t < l23[1]:
        expr = "scared"
    else:
        expr = "terror"
    hero_close(cx, t, 540, 980, 400 + 30 * smooth(prog(t, st, en)), expr=expr, look=(0.8, -0.05), turn=0.25,
               blink=0, shiver=0.3 if expr == "terror" else 0.0, arm_l=(0.1, 0.1), arm_r=(-0.1, -0.1))
    g = cairo.LinearGradient(0, 0, W, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.4)
    g.add_color_stop_rgba(1, 0.65, 0.75, 0.9, 0.16)
    cx.set_source(g)
    cx.paint()
    post(cx, t, INT_TINT, vig=0.72)


def thing(t, t0, t1):
    """Something big moving behind the corn. Never fully seen."""
    def draw(cx):
        f = prog(t, t0, t1)
        x = 2330 + 330 * smooth(f)
        gy = 1180
        h = 560
        sway = math.sin(t * 2.2) * 0.04
        cx.save()
        cx.translate(x, gy)
        cx.rotate(sway)
        cx.move_to(-90, 0)
        cx.curve_to(-120, -h * 0.5, -60, -h * 0.85, 20, -h)
        cx.curve_to(90, -h * 0.97, 130, -h * 0.7, 110, -h * 0.45)
        cx.curve_to(100, -h * 0.25, 120, -h * 0.1, 90, 0)
        cx.close_path()
        src(cx, (0.03, 0.04, 0.05, 0.92))
        cx.fill()
        # a long arm hanging forward
        line(cx, [(70, -h * 0.75), (170, -h * 0.45), (200, -h * 0.12)], (0.03, 0.04, 0.05, 0.9), 26)
        cx.restore()
    return draw


def shot_thing(cx, t, st, en, T):
    l24 = T["l24"]
    cam = (pend(t, [(st, 2420), (en, 2470)]), 1000, pend(t, [(st, 1.3), (en, 1.4)]))
    S.exterior(cx, t, cam, actors_corn=thing(t, l24[0] - 0.1, l24[1] + 0.5),
               corn_disturb=(2330 + 330 * smooth(prog(t, l24[0] - 0.1, l24[1] + 0.5)), 1.1))
    post(cx, t, EXT_TINT, vig=0.75)


def shot_end(cx, t, st, en, T):
    src(cx, (0, 0, 0, 1))
    cx.paint()
    a = smooth(prog(t, st + 0.3, st + 0.55))
    D.label(cx, "PART 3", W / 2, H / 2, 50, fill=S.MUTED_WHITE, outline=None, alpha=a, spacing=10, shadow=False)
    w = 60 * smooth(prog(t, st + 0.35, st + 0.8))
    line(cx, [(W / 2 - w, H / 2 + 55), (W / 2 + w, H / 2 + 55)], (*S.AMBER[:3], a), 3)


SHOTS = {k[5:]: v for k, v in globals().items() if k.startswith("shot_") and callable(v)}


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
def door_knock():
    d = 0.5
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * 85 * tt) * np.exp(-tt * 18) + np.sin(2 * np.pi * 160 * tt) * np.exp(-tt * 30) * 0.6
    x += A.lp(A.noise(d, 3), 900) * np.exp(-tt * 40) * 0.8
    return A.norm(x, 0.9)


def wind(d, seed=1):
    tt = A.t_arr(d)
    x = A.bp(A.noise(d, seed), 150, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt + 1))
    x += A.bp(A.noise(d, seed + 1), 1500, 4000) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * tt))
    return x


def rustle(d, seed=2):
    tt = A.t_arr(d)
    x = A.hp(A.noise(d, seed), 2500) * (np.abs(np.sin(2 * np.pi * 3.1 * tt)) ** 3)
    return A.norm(x * np.sin(np.pi * tt / d), 0.5)


def creak(seed=0):
    return A.sfx_creak() * 0.7


def step_soft(seed):
    return A.sfx_step(seed) * 0.6


def static(d, seed=5, voices=True):
    tt = A.t_arr(d)
    x = A.bp(A.noise(d, seed), 300, 5000) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * tt))
    # tuning whistles
    f = 900 + 600 * np.sin(2 * np.pi * 0.35 * tt)
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.08
    if voices:  # fragmented distant voices: band-limited babble, chopped
        b = A.bp(A.sfx_crowd_murmur(d)[: len(tt)], 400, 2500)
        gate = (np.sin(2 * np.pi * 0.9 * tt + 1) > 0.55).astype(float)
        gate = A.lp(gate, 30)
        x[: len(b)] += b * gate[: len(b)] * 1.4
    return A.norm(x, 0.6)


def distant_breath(d=1.6, seed=3):
    tt = A.t_arr(d)
    x = A.bp(A.noise(d, seed), 200, 1200) * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    g = np.sin(2 * np.pi * 70 * tt) * 0.15 * np.sin(np.pi * np.clip(tt / d, 0, 1))
    return A.norm(A.lp(x + g, 1500), 0.5)


def rumble(d, seed=9):
    tt = A.t_arr(d)
    x = A.lp(A.noise(d, seed), 90) * 3 + np.sin(2 * np.pi * 38 * tt) * 0.3
    return A.norm(x * np.minimum(1, tt / 1.5) * np.minimum(1, (d - tt) / 0.6), 0.8)


def impact(d=2.6):
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * 40 * tt * (1 - 0.1 * tt / d)) * np.exp(-tt * 1.4)
    x += A.lp(A.noise(d, 5), 240) * np.exp(-tt * 2.2) * 0.8
    x[: int(0.008 * SR)] *= np.linspace(0, 1, int(0.008 * SR))
    return A.norm(x, 0.95)


def tick():
    d = 0.05
    tt = A.t_arr(d)
    return np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 120) * 0.3


def sfx_events():
    T, shots, total, _ = timeline()
    st = dict(shots)
    ev = []
    for kt in knock_times():
        ev.append((kt, door_knock(), 0.9))
    for kt in knock_times_2(T):
        ev.append((kt, door_knock() * 0.8, 0.6))
    ev.append((st["eyes"] + 0.2, creak(), 0.3))
    for k in range(5):
        ev.append((st["approach"] + 0.25 + k * 0.6, step_soft(k), 0.4))
    ev.append((st["approach"] + 0.8, creak(), 0.25))
    ev.append((st["peek"] + 0.3, A.sfx_step(20, heavy=True) * 0.3, 0.2))
    ev.append((st["lock"] + 0.3, A.sfx_heartbeat(), 0.3))
    ev.append((st["lock"] + 1.2, A.sfx_heartbeat(), 0.3))
    # science: soft ticks on the nodes
    l07, l08 = T["l07"], T["l08"]
    for t0 in (l07[0] + 0.3, l08[0] + 0.2, l08[0] + 0.9):
        ev.append((t0, tick(), 0.6))
    ev.append((st["decide"] + 0.3, step_soft(30), 0.35))
    ev.append((st["decide"] + 0.4, creak(), 0.2))
    ev.append((st["radio"] + 0.5, A.sfx_thud(200, 0.15), 0.25))
    ev.append((st["radio"] + 1.0, A.sfx_click(), 0.4))
    ev.append((st["radio"] + 1.05, static(st["ots"] - st["radio"] - 1.0), 0.5))
    for k in range(4):
        ev.append((st["barn"] + 0.2 + k * 0.9, distant_breath(1.4, 40 + k), 0.12))
    ev.append((st["corn"], rustle(st["yard"] - st["corn"] + 1.0, 7), 0.2))
    ev.append((st["corn"] - 0.5, rumble(total - st["corn"] + 0.5), 0.16))
    ev.append((st["yard"] + 0.4, rustle(3.0, 8), 0.22))
    for k in range(5):
        ev.append((T["l22"][0] + 0.2 + k * 0.45, step_soft(50 + k) * 0.8, 0.3))
        ev.append((st["yard"] + k * 0.7, distant_breath(1.2, 60 + k), 0.18))
    for k in range(6):
        ev.append((st["herofear"] - 0.2 + k * 0.62, A.sfx_heartbeat(), 0.12))
    ev.append((st["thing"] + 0.2, rustle(2.2, 11), 0.15))
    ev.append((st["end"], impact(), 0.95))
    return ev


def music_bed(total):
    T, shots, _, _ = timeline()
    st = dict(shots)
    n = int((total + 1) * SR)
    buf = np.zeros(n + 3 * SR)
    end = st["end"]
    # low drone throughout, a second voice enters with the science, tension cluster from the corn on
    A.add(buf, A.pad(33, end, 0.06) * 0.6, 0)
    A.add(buf, A.pad(40, end - st["ext_knock"] - 2.0, 0.05) * 0.25, 2.0)
    A.add(buf, A.pad(45, st["decide"] - st["science"] + 1.0, 0.12) * 0.25, st["science"])
    A.add(buf, A.pad(48, st["decide"] - st["science"] + 1.0, 0.1) * 0.15, st["science"] + 1.5)
    # sparse low pulse while the radio searches
    t = st["radio"]
    while t < st["corn"]:
        A.add(buf, A.bass(33, 0.5) * 0.35, t)
        t += 1.0
    A.add(buf, A.pad(46, end - st["corn"], 0.05) * 0.25, st["corn"])
    A.add(buf, A.pad(39, end - st["yard"], 0.04) * 0.25, st["yard"])
    tt = A.t_arr(end - st["yard"])
    A.add(buf, np.sin(2 * np.pi * (660 + 40 * tt / tt[-1]) * tt) * 0.02 * (tt / tt[-1]) ** 2, st["yard"])
    tt = np.arange(len(buf)) / SR
    env = np.clip(tt / 0.5, 0, 1) * np.where(tt >= end, 0.0, 1.0)
    return (buf * env)[:n]


def ambience(total):
    T, shots, _, _ = timeline()
    n = int((total + 1) * SR)
    w = wind(total + 1)[:n]
    tt = np.arange(n) / SR
    # wind louder outside, muffled inside, gone in the science section and after the cut
    lvl = np.full(n, 0.35)
    for name, s, e in [(nm, s, e) for (nm, s), (_, e) in zip(shots, shots[1:] + [("x", total)])]:
        a, b = int(s * SR), int(e * SR)
        if name in ("ext_knock", "barn", "corn", "yard", "thing", "faces"):
            lvl[a:b] = 0.55
        elif name == "science":
            lvl[a:b] = 0.12
        elif name == "end":
            lvl[a:b] = 0.0
    lvl = A.lp(lvl, 3)
    return w * lvl * 0.35


def voice_track(total):
    T = timeline()[0]
    clips = V.clips()
    buf = np.zeros(int((total + 1) * SR))
    for lid, (s, e) in T.items():
        if lid in clips:
            c = clips[lid]
            c = c / (np.sqrt(np.mean(c ** 2)) + 1e-9) * 0.09
            if lid == "l24":
                c *= 1.08
            A.add(buf, c, s)
    return buf


MUS_GAIN = 0.2


def mix_audio():
    import soundfile as sf
    os.makedirs(BUILD, exist_ok=True)
    T, shots, total, _ = timeline()
    n = int((total + 1) * SR)
    vox = voice_track(total)
    mus = music_bed(total)[:n]
    amb = ambience(total)[:n]
    sfx = np.zeros(n)
    for t, x, g in sfx_events():
        A.add(sfx, np.asarray(x, dtype=np.float64) * g, t)
    if np.any(vox):
        env = A.envelope_follow(np.abs(vox), 0.02, 0.35)
        env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
    else:
        env = np.zeros(n)
        for s, e in T.values():
            env[int(s * SR):int(e * SR)] = 1.0
        env = A.envelope_follow(env, 0.03, 0.3)
    late = np.clip((np.arange(n) / SR - (T["l23"][0] - 0.5)) / 0.5, 0, 1)
    env = np.clip(env * (1 + 0.5 * late), 0, 1)
    mix = vox + (mus * MUS_GAIN + amb) * (1 - 0.7 * env) + sfx * (0.72 - 0.5 * env)
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
        write_srt(os.path.join(OUTDIR, TITLE + ".srt"))
    print("audio ->", out, f"{total:.2f}s")
    return out


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    T = timeline()[0]
    with open(path, "w") as f:
        for i, (lid, text) in enumerate(NARRATION, 1):
            s, e = T[lid]
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{text.replace('...', '…')}\n\n")
    print("srt ->", path)


# ============================================================ render
def _worker(args):
    i, f0, f1, path, draft = args
    w, h = (W // 2, H // 2) if draft else (W, H)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r",
           str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if draft else "slow", "-crf",
           "26" if draft else "17", "-pix_fmt", "yuv420p", path]
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
    chunk = 60
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
            c.set_source_rgb(1, 0.2, 0.2)
            c.set_font_size(18)
            c.show_text(f"{t:.2f} {shot_at(t)[0]}")
        sheet.write_to_png(os.path.join(BUILD, cmd + ".png"))
    elif cmd == "audio":
        mix_audio()
    elif cmd == "video":
        render_video(draft="--draft" in a)


if __name__ == "__main__":
    main()

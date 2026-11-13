"""Day 2 "Don't Open the Door" — FINAL revision: new hook, compressed science, rebuilt 12-second ending.
Reuses the rebuilt episode's sets, characters, sound generators and shots where they still fit.

usage:
  python -m episodes.zombie_day_2_rebuilt.film_final plan | stills t.. | sheet [n] | strip t0 t1 [fps] | audio | video
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
from episodes.zombie_day_2_rebuilt import film as F
from episodes.zombie_day_2_rebuilt import sets as S
from episodes.zombie_day_2_rebuilt import voice as V
from episodes.zombie_day_2_rebuilt.script import NARRATION, TEXT, TITLE

ROOT = F.ROOT
BUILD = os.path.join(ROOT, "build", "day2_final")
OUTDIR = F.OUTDIR
W, H, FPS, SR = F.W, F.H, F.FPS, F.SR
TARGET = 60.0

# brighter, still cold: readable on a phone
F.EXT_TINT = (0.80, 0.86, 0.97)
F.INT_TINT = (0.74, 0.78, 0.89)
EXT, INT = F.EXT_TINT, F.INT_TINT
pend, cam_apply, accent, hero_close, blink, arm_to = F.pend, F.cam_apply, F.accent, F.hero_close, F.blink, F.arm_to

PLAN = [
    ("shot", "hook"), ("wait", 0.75, False), ("line", "a01", 0.0), ("wait", 0.2, True),
    ("shot", "exinf"), ("line", "a02", 0.1),
    ("shot", "approach"), ("line", "a03", 0.3),
    ("shot", "peek"), ("line", "a04", 0.25), ("wait", 0.15, True),
    ("shot", "science"), ("line", "a05", 0.2), ("line", "a06", 0.35), ("wait", 0.3, True),
    ("shot", "doubt"), ("line", "a07", 0.15), ("line", "a08", 0.3),
    ("shot", "decide"), ("line", "a09", 0.25),
    ("shot", "talk"), ("line", "a10", 0.3),
    ("shot", "radio"), ("line", "a11", 0.3),
    ("shot", "dial"), ("line", "a12", 0.2), ("wait", 0.3, True),
    ("shot", "ots"), ("line", "a13", 0.2),
    ("shot", "barn"), ("line", "a14", 0.25),
    ("shot", "faces"), ("line", "a15", 0.15),
    ("shot", "heroeyes"), ("line", "a16", 0.2),
    ("shot", "corn"), ("line", "a17", 0.2), ("wait", 0.25, True),
    ("shot", "stop"), ("wait", 0.3, False), ("line", "a18", 0.0), ("wait", 1.45, False),
    ("shot", "lowcorn"), ("wait", 2.3, False),
    ("shot", "retreat"), ("wait", 0.1, False), ("line", "a19", 0.0), ("wait", 0.35, False),
    ("shot", "watch"), ("line", "a20", 0.1), ("line", "a21", 0.6), ("wait", 0.2, False),
    ("shot", "thing"), ("wait", 1.25, False),
    ("shot", "end"), ("wait", 1.0, False),
]
LEAD = 0.12


@functools.lru_cache(maxsize=None)
def timeline():
    dur = V.durations()
    speech = sum(dur[e[1]] for e in PLAN if e[0] == "line")
    fixed = sum(e[1] for e in PLAN if e[0] == "wait" and not e[2])
    scal = sum(e[1] for e in PLAN if e[0] == "wait" and e[2]) + sum(e[2] for e in PLAN if e[0] == "line")
    k = clamp((TARGET - speech - fixed) / scal, 0.4, 2.5)
    t, T, shots, pending = 0.0, {}, [], None
    for ev in PLAN:
        if ev[0] == "shot":
            if not shots:
                shots.append([ev[1], 0.0])
            else:
                pending = ev[1]
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
    return cur[0], cur[1], (shots[i + 1][1] if i + 1 < len(shots) else total)


def st_of(name):
    return dict(timeline()[1])[name]


def rim(cx, x, y, r, k=0.22, col=(0.62, 0.72, 0.86)):
    """Soft cold back-light behind a character so it separates from the dark."""
    g = cairo.RadialGradient(x, y, r * 0.2, x, y, r)
    g.add_color_stop_rgba(0, *col, k)
    g.add_color_stop_rgba(1, *col, 0)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.fill()


# ============================================================ hook
def hook_knocks():
    return [0.05, 0.3, 0.55]


def knock_k(t, times, decay=9):
    k = 0.0
    for kt in times:
        if t >= kt:
            k = max(k, math.exp(-(t - kt) * decay))
    return k


def frosted(cx, x0, y0, w, h, t, sil=1.0, sx=None):
    """Frosted glass panel with a blurred human silhouette pressed behind it."""
    cx.save()
    cx.rectangle(x0, y0, w, h)
    cx.clip()
    g = cairo.LinearGradient(0, y0, 0, y0 + h)
    g.add_color_stop_rgba(0, 0.42, 0.5, 0.58, 1)
    g.add_color_stop_rgba(1, 0.28, 0.33, 0.38, 1)
    cx.set_source(g)
    cx.paint()
    if sil > 0:
        sx = x0 + w * 0.55 + 14 * math.sin(t * 0.9) if sx is None else sx
        sy = y0 + h * 0.3 + 6 * math.sin(t * 1.7)
        for k, (grow, a) in enumerate(((1.5, 0.12), (1.25, 0.18), (1.08, 0.3), (1.0, 0.45))):
            ellipse(cx, sx, sy, 95 * grow, 105 * grow)
            src(cx, (0.05, 0.06, 0.07, a * sil))
            cx.fill()
            cx.move_to(sx - 230 * grow, y0 + h)
            cx.curve_to(sx - 230 * grow, sy + 220, sx - 140 * grow, sy + 120, sx, sy + 120)
            cx.curve_to(sx + 140 * grow, sy + 120, sx + 230 * grow, sy + 220, sx + 230 * grow, y0 + h)
            cx.close_path()
            cx.fill()
    r = random.Random(3)
    for k in range(900):  # frost speckle
        ellipse(cx, x0 + r.uniform(0, w), y0 + r.uniform(0, h), r.uniform(1, 3), r.uniform(1, 3))
        src(cx, (0.85, 0.9, 0.95, r.uniform(0.04, 0.12)))
        cx.fill()
    cx.restore()
    cx.rectangle(x0, y0, w, h)
    fs(cx, None, hexc("#48443e"), 22)


def door_surface(cx, x0, x1):
    cx.rectangle(x0, -300, x1 - x0, H + 600)
    src(cx, hexc("#3a2f29"))
    cx.fill()
    r = random.Random(11)
    for k in range(46):
        y = r.uniform(-300, H + 300)
        cx.move_to(x0, y)
        cx.curve_to(x0 + 300, y + r.uniform(-20, 20), x1 - 300, y + r.uniform(-20, 20), x1, y + r.uniform(-30, 30))
        src(cx, (0.14, 0.1, 0.08, 0.35))
        cx.set_line_width(r.uniform(2, 5))
        cx.stroke()


def lock_scene(cx, t, hand, sil_t, tremble=0.0, glow=0.18):
    """Deadbolt in close-up, frosted strip on the right with the shape outside."""
    door_surface(cx, -300, 860)
    frosted(cx, 870, -100, 420, H + 200, sil_t, sil=1.0, sx=1010)
    rrect(cx, 360, 760, 220, 400, 24)
    fs(cx, hexc("#6b5b3e"), D.INK, 5)
    ellipse(cx, 470, 900, 70, 70)
    fs(cx, hexc("#55482f"), D.INK, 5)
    rrect(cx, 448, 838, 44, 124, 14)
    fs(cx, hexc("#8a7a52"), D.INK, 5)
    ellipse(cx, 470, 1060, 34, 34)
    fs(cx, hexc("#2a231b"), D.INK, 4)
    for k in range(9):
        p = (300 + k * 34, 520 + 60 * math.sin(k * 0.45) + 4 * math.sin(t * 2))
        ellipse(cx, p[0], p[1], 16, 10, 0.4)
        fs(cx, None, hexc("#9a9a96"), 7)
    if hand:
        hx, hy = hand
        hx += noise1(t * 30, 2) * 6 * tremble
        hy += noise1(t * 30, 6) * 6 * tremble
        D.sleeve(cx, [(1000, 2000), (hx + 170, hy + 260), (hx + 30, hy + 40)], 150)
        ellipse(cx, hx, hy, 70, 62)
        src(cx, D.INK)
        cx.fill()
    g = cairo.LinearGradient(1300, 0, 300, 0)
    g.add_color_stop_rgba(0, 0.6, 0.7, 0.85, glow)
    g.add_color_stop_rgba(1, 0.6, 0.7, 0.85, 0.0)
    cx.set_source(g)
    cx.paint()


def shot_hook(cx, t, st, en, T):
    lt = t - st
    k = knock_k(lt, hook_knocks())
    if lt < 0.85:   # A: the door takes three violent hits; a shape behind the frosted glass
        cx.save()
        cx.translate(noise1(t * 45, 1) * 16 * k, noise1(t * 45, 4) * 10 * k)
        S.panel_wall(cx, -100, -100, W + 100, H + 100)
        cx.save()
        cx.translate(noise1(t * 60, 9) * 10 * k, 0)
        door_surface(cx, -100, 600)
        for py in (380, 1080):
            rrect(cx, 60, py, 420, 560, 8)
            fs(cx, None, hexc("#251d19"), 8)
        ellipse(cx, 540, 1020, 26, 26)
        fs(cx, hexc("#7a6a48"), D.INK, 4)
        cx.restore()
        frosted(cx, 640, 220, 360, 1300, t)
        r = random.Random(int(lt * 20))   # dust shaken loose
        for j in range(int(40 * k)):
            ellipse(cx, r.uniform(0, 620), r.uniform(0, 600) + lt * 300, 3, 3)
            src(cx, (0.8, 0.78, 0.7, 0.5 * k))
            cx.fill()
        cx.restore()
        F.post(cx, t, INT, vig=0.62)
    elif lt < 1.85:  # B: his hand reaches for the lock
        hand = pend(t, [(st + 0.85, (1150, 1600)), (st + 1.85, (600, 1010))])
        cx.save()
        cam_apply(cx, 600, 960, 1.0 + 0.05 * prog(lt, 0.85, 1.85))
        lock_scene(cx, t, hand, t, tremble=0.6)
        cx.restore()
        F.post(cx, t, INT, vig=0.62)
    else:            # C: tight on his face. Uncertain.
        S.hallway(cx, t, moon=0.6)
        src(cx, (0, 0, 0, 0.3))
        cx.paint()
        rim(cx, 380, 900, 700, 0.25)
        f = smooth(prog(lt, 1.95, 2.6))
        hero_close(cx, t, 560, 1010, 560 + 30 * prog(lt, 1.85, en - st), expr="worried",
                   look=(-0.9 + 0.6 * smooth(prog(lt, 2.9, 3.4)), -0.1 + 0.25 * f), turn=-0.22,
                   blink=1.0 if 2.75 < lt < 2.85 else 0.0, arm_l=(0.1, 0.1), arm_r=(-0.1, -0.1))
        F.post(cx, t, INT, vig=0.7)
    a = smooth(prog(lt, 0.3, 0.6)) * (1 - smooth(prog(lt, 3.0, 3.4)))
    if a > 0:
        D.label(cx, "DAY 2", 90, 120, 34, fill=S.MUTED_WHITE, outline=None, alpha=a, spacing=8, shadow=False)
        line(cx, [(52, 150), (52 + 76 * smooth(prog(lt, 0.4, 0.9)), 150)], (*S.AMBER[:3], a), 3)


# ============================================================ infected at the fence
def shot_exinf(cx, t, st, en, T):
    lt = t - st
    cam = (pend(t, [(st, 1100), (en, 1160)]), 1180, pend(t, [(st, 1.45), (en, 1.55)]))

    def fig(c):
        rim(c, 1150, 1180, 520, 0.18)
        for i, (z, x0, gy, s, d) in enumerate(((D.INFECTED[0], 960, 1320, 0.62, 1), (D.INFECTED[1], 1330, 1360, 0.6, -1),
                                               (D.INFECTED[3], 1150, 1420, 0.66, 1))):
            D.zombie(c, z, x0 + d * 24 * lt * z.speed, gy, s, t + i * 2, face_dir=d,
                     phase=t * z.speed * 2.6 + i * 2)
    S.exterior(cx, t, cam, actors_mid=fig)
    F.post(cx, t, EXT, vig=0.6)


# ============================================================ door, neighbor
def shot_peek(cx, t, st, en, T):
    lt = t - st
    push = 0.1 * smooth(prog(t, st, en))
    shift = math.sin(t * 1.3)            # shifting his weight from foot to foot
    glance = smooth(prog(lt, 0.9, 1.2)) * (1 - smooth(prog(lt, 1.6, 1.9)))
    kw = dict(expr="tired", t=t, turn=0.75 * glance - 0.1, look=(0.9 * glance, 0.1), blink=F.blink(t, 5, 2.9),
              head_dy=3 * math.sin(t * 2.2), lean=0.05 * shift, head_dx=10 * shift,
              arm_l=(-2.0, -2.9 + 0.15 * math.sin(t * 8)) if lt < 0.7 else (-0.15, -0.2), arm_r=(0.15, 0.1))
    F.peek_scene(cx, t, push, kw)
    F.post(cx, t, INT, vig=0.58)


def mini_figure(cx, x, gy, s, col, hunch=0.0, walk=None):
    F.silhouette(cx, x, gy, s, col, hunch=hunch, walk=walk)


def shot_science(cx, t, st, en, T):
    """The neighbor stays visible behind a restrained motion graphic: exposure -> incubation -> symptoms."""
    a05, a06 = T["a05"], T["a06"]
    lt = t - st
    kw = dict(expr="tired", t=t, turn=-0.1, look=(-0.2, 0.1), blink=F.blink(t, 5, 2.9), head_dy=3 * math.sin(t * 2.2),
              lean=0.05 * math.sin(t * 1.3), head_dx=10 * math.sin(t * 1.3), arm_l=(-0.15, -0.2), arm_r=(0.15, 0.1))
    F.peek_scene(cx, t, 0.12 + 0.04 * prog(t, st, en), kw, ots=False)
    fade = smooth(prog(lt, 0.0, 0.4)) * (1 - smooth(prog(t, en - 0.4, en)))
    src(cx, (0.03, 0.04, 0.06, 0.62 * fade))
    cx.paint()
    F.post(cx, t, INT, vig=0.55)
    cx.push_group()
    ty, x_e, x_s = 1500, 170, 910
    grow = smooth(prog(t, a05[0] - 0.1, a05[0] + 0.7))
    cold = (0.62, 0.68, 0.74, 1)
    line(cx, [(x_e, ty), (x_e + (x_s + 40 - x_e) * grow, ty)], cold, 4)
    labels = ((x_e, "EXPOSURE", a05[0]), ((x_e + x_s) / 2, "INCUBATION", a05[0] + 0.5),
              (x_s, "SYMPTOMS", a05[0] + 1.0))
    for x, lab, t0 in labels:
        a = smooth(prog(t, t0, t0 + 0.3))
        if a > 0:
            ellipse(cx, x, ty, 11 * a, 11 * a)
            fs(cx, S.CHAR, S.MUTED_WHITE, 3)
            D.label(cx, lab, x, ty + 52, 24, fill=(*S.MUTED_WHITE[:3], 0.85), outline=None, alpha=a, spacing=2,
                    shadow=False)
    band = smooth(prog(t, a05[0] + 0.6, a05[0] + 1.4))
    if band > 0:
        cx.rectangle(x_e + 12, ty - 16, (x_s - x_e - 24) * band, 32)
        src(cx, (*S.AMBER[:3], 0.25))
        cx.fill()
    # one person walks the timeline: outwardly healthy through incubation, symptoms only at the end
    px = pend(t, [(a05[0] + 0.2, x_e + 20), (a05[1], (x_e + x_s) / 2 + 120), (a06[1], (x_e + x_s) / 2 + 230)])
    sym = smooth(prog(t, a05[1] - 0.8, a05[1] - 0.2)) * (1 - smooth(prog(t, a06[0], a06[0] + 0.3)))
    if sym > 0:
        mini_figure(cx, x_s, ty - 40, 0.75, (*S.RUST[:3], 0.85 * sym), hunch=0.6)
    mini_figure(cx, px, ty - 40, 0.75, (0.85, 0.87, 0.88, smooth(prog(t, a05[0], a05[0] + 0.3))),
                walk=t * 5 if t < a06[1] else None)
    # some diseases: spread before symptoms (dots to a second person, small label)
    sp = smooth(prog(t, a06[0] + 0.25, a06[0] + 1.2))
    if sp > 0:
        bx = x_s + 30
        mini_figure(cx, bx, ty - 40, 0.75, (0.85, 0.87, 0.88, 0.8 * sp))
        for k in range(2):
            ph = (t * 1.1 + k / 2) % 1
            for j in range(9):
                f = j / 9
                if f > ph:
                    break
                ellipse(cx, px + 30 + (bx - px - 60) * f, ty - 250 - 90 * math.sin(math.pi * f) + k * 20, 5, 5)
                src(cx, (*S.AMBER[:3], 0.85 * sp * (1 - (ph - f))))
                cx.fill()
        D.label(cx, "IN SOME DISEASES", (px + bx) / 2, ty - 400, 24, fill=(*S.MUTED_WHITE[:3], 0.8), outline=None,
                alpha=sp, spacing=2, shadow=False)
    cx.pop_group_to_source()
    cx.paint_with_alpha(fade)
    accent(cx, "INCUBATION", t, a05[0] + 0.55, a06[0] + 0.2, 1060, 40, col=S.AMBER, spacing=6)
    S.grain(cx, t, 0.05)


def shot_doubt(cx, t, st, en, T):
    lt = t - st
    a07, a08 = T["a07"], T["a08"]
    S.hallway(cx, t, moon=0.6)
    src(cx, (0, 0, 0, 0.3))
    cx.paint()
    rim(cx, 360, 980, 700, 0.25)
    # looks at the door... down... back. Thinking.
    lx = pend(t, [(st, -0.9), (a07[1], -0.9), (a08[0] + 0.2, -0.2), (a08[1], -0.6)])
    ly = pend(t, [(st, -0.1), (a08[0], 0.5), (a08[1], 0.1)])
    hero_close(cx, t, 600, 1040, 480, expr="worried", look=(lx, ly), turn=-0.2 + 0.1 * lx,
               blink=1.0 if a08[0] + 0.05 < t < a08[0] + 0.15 else 0.0, tilt=-0.04 * smooth(prog(t, a08[0], a08[1])),
               arm_l=(0.1, 0.1), arm_r=(-0.1, -0.1))
    F.post(cx, t, INT, vig=0.68)
    accent(cx, "TRANSMISSION UNKNOWN", t, a08[0] - 0.05, en + 0.2, 300, 40, col=S.MUTED_WHITE, spacing=5)


def shot_decide(cx, t, st, en, T):
    """The hand hovers... closes into a fist, and pulls away from the lock."""
    hand = pend(t, [(st, (600, 1010)), (st + 0.45, (620, 1000)), (en - 0.5, (860, 1250)), (en, (980, 1420))])
    cx.save()
    cam_apply(cx, 640, 980, 1.05)
    lock_scene(cx, t, hand, t, tremble=0.8 * (1 - prog(t, st + 0.4, en)))
    cx.restore()
    F.post(cx, t, INT, vig=0.62)


def shot_talk(cx, t, st, en, T):
    T2 = dict(T)
    T2["l13"] = T["a10"]
    F.shot_talk(cx, t, st, en, T2)


# ============================================================ the ending
YARD = [  # zombie, x, ground y, scale, wander dir, head turn order
    (D.INFECTED[0], 1440, 1330, 0.6, 1, 0),
    (D.INFECTED[1], 1620, 1420, 0.62, -1, 2),
    (D.INFECTED[2], 1760, 1350, 0.56, 1, 1),
    (D.INFECTED[3], 1890, 1470, 0.66, -1, 3),
    (D.INFECTED[4], 1330, 1500, 0.7, 1, 4),
]


def ending_beats(T):
    stop = T["a18"][0] - 0.05
    turns = [stop + 0.45 + 0.42 * k for k in range(5)]
    a19 = T["a19"]
    first_back = a19[0] + 0.05
    turn_away = a19[0] + 0.7
    group = a19[0] + 1.25
    return stop, turns, first_back, turn_away, group


def yard_fig(t, T, small=False):
    stop, turns, first_back, turn_away, group = ending_beats(T)
    s0 = st_of("stop")

    def fig(cx):
        rim(cx, 1650, 1250, 650, 0.16)
        for i, (z, x0, gy, s, d, order) in enumerate(YARD):
            if t < stop:  # aimless, uneven shamble
                x = x0 + d * 22 * (t - s0) * z.speed
                D.zombie(cx, z, x, gy, s, t + i, face_dir=d, phase=t * z.speed * 3.0 + i * 1.7, look=(d * 0.3, 0.4))
                continue
            xs = x0 + d * 22 * (stop - s0) * z.speed
            tt = turns[order]
            turn = smooth(prog(t, tt, tt + 0.75))          # heads rotate slowly towards the corn, one by one
            target = 0.55 - z.tilt0 * 0.7
            if i == 0:
                start = first_back
            elif i == 1:
                start = turn_away
            else:
                start = group + 0.25 * (i - 2)
            mv = max(0.0, t - start)
            if i == 1 and mv > 0:  # turns its back on the field and lurches away, sudden acceleration
                x = xs - 70 * mv - 80 * mv * mv
                D.zombie(cx, z, x, gy, s, t + i, face_dir=-1, walking=True, phase=mv * 7 + i,
                         head_add=-0.25 * (1 - smooth(prog(mv, 0, 0.3))), look=(-1, 0))
                continue
            x = xs - 60 * mv * (1 + 0.25 * (i % 2))
            guard = smooth(prog(mv, 0.0, 0.35))
            arms = ((-0.15, -0.05), (0.2 + 1.0 * guard, 0.3 + 1.9 * guard)) if mv > 0 else None
            D.zombie(cx, z, x, gy, s, t + i, face_dir=1, walking=mv > 0, phase=-(mv * 2.8) + i,
                     head_add=target * turn, look=(turn, -0.2 * turn), still=mv == 0, arms=arms,
                     jaw=0.1 if t >= stop else None, blink=0.0)
    return fig


def yard_cam(t, st, en, zoom0=1.55):
    return (pend(t, [(st, 1690), (en, 1660)]), 1205, pend(t, [(st, zoom0), (en, zoom0 + 0.08)]))


def shot_stop(cx, t, st, en, T):
    S.exterior(cx, t, yard_cam(t, st, en), actors_mid=yard_fig(t, T), fog_k=1.2)
    F.post(cx, t, EXT, vig=0.6)


def presence(t, t0, t1, x0=2700, x1=2450, alpha=0.75, h=520):
    """Something heavy between the rows. Only mass and shadow, never a shape you can name."""
    def draw(cx):
        f = smooth(prog(t, t0, t1))
        x = x0 + (x1 - x0) * f
        cx.save()
        cx.translate(x, 1215)
        g = cairo.RadialGradient(0, -h * 0.5, 20, 0, -h * 0.5, h * 0.75)
        g.add_color_stop_rgba(0, 0.02, 0.03, 0.03, alpha)
        g.add_color_stop_rgba(0.7, 0.02, 0.03, 0.03, alpha * 0.8)
        g.add_color_stop_rgba(1, 0.02, 0.03, 0.03, 0)
        cx.set_source(g)
        cx.scale(0.7, 1.0)
        cx.arc(0, -h * 0.5, h * 0.75, 0, 2 * math.pi)
        cx.fill()
        cx.restore()
    return draw


def shot_lowcorn(cx, t, st, en, T):
    """Low angle into the rows. The wind leans everything right; something pushes the stalks left."""
    S.WIND_BIAS = 0.07 + 0.02 * math.sin(t * 0.8)
    f = prog(t, st, en + 0.6)
    dx = 2780 - 380 * f
    cam = (pend(t, [(st, 2560), (en, 2520)]), 1330, pend(t, [(st, 2.0), (en, 2.2)]))
    S.exterior(cx, t, cam, actors_corn=presence(t, st, en + 0.6, 2780, 2400, alpha=0.93, h=900),
               corn_disturb=(dx, 1.0, True),
               fog_k=1.3)
    S.WIND_BIAS = 0.0
    # its shadow passing through the stalks: a heavy dark mass, no shape you can name
    wx = 2780 - 380 * smooth(prog(t, st, en + 0.6))
    sx = W / 2 + (wx - cam[0]) * cam[2]
    for k, (rx, ry, a) in enumerate(((330, 640, 0.35), (240, 520, 0.4), (170, 420, 0.35))):
        g = cairo.RadialGradient(sx, 980, 10, sx, 980, ry)
        g.add_color_stop_rgba(0, 0.0, 0.01, 0.01, a)
        g.add_color_stop_rgba(1, 0.0, 0.01, 0.01, 0)
        cx.save()
        cx.translate(sx, 980)
        cx.scale(rx / ry, 1)
        cx.translate(-sx, -980)
        cx.set_source(g)
        cx.arc(sx, 980, ry, 0, 2 * math.pi)
        cx.fill()
        cx.restore()
    F.post(cx, t, EXT, vig=0.7)


def shot_retreat(cx, t, st, en, T):
    S.exterior(cx, t, yard_cam(t, st, en, 1.5), actors_mid=yard_fig(t, T), fog_k=1.2,
               corn_disturb=(2500 - 60 * prog(t, st, en), 0.7, True))
    F.post(cx, t, EXT, vig=0.6)


def shot_watch(cx, t, st, en, T):
    a20, a21 = T["a20"], T["a21"]
    cut = a20[1] + 0.3
    if t < cut:   # over his shoulder: through the window, the infected backing off the yard
        cam = (1640, 1180, 1.05)

        def view(c, rect):
            x0, y0, w, h = rect
            c.save()
            c.translate(x0, y0)
            c.scale(w / W, w / W)
            c.translate(0, -(H - h * W / w) / 2)
            S.exterior(c, t, cam, actors_mid=yard_fig(t, T))
            c.restore()
        cx.save()
        cam_apply(cx, 540, 860, 1.12)
        S.kitchen_dark(cx, t, window_draw=view, led=0.3)
        cx.restore()
        D.hero_back(cx, 250, 1520, 1.5, t=t, turn=0.3)
        F.post(cx, t, INT, vig=0.6)
    else:         # his face: confusion turning into real fear
        S.kitchen_dark(cx, t, led=0.25)
        src(cx, (0, 0, 0, 0.3))
        cx.paint()
        rim(cx, 760, 900, 700, 0.28)
        f = smooth(prog(t, cut, a21[1]))
        expr = "worried" if f < 0.45 else "scared"
        hero_close(cx, t, 540, 1000, 470 + 30 * f, expr=expr, look=(0.85, -0.05), turn=0.25, blink=0,
                   shiver=0.25 * f, arm_l=(0.1, 0.1), arm_r=(-0.1, -0.1))
        g = cairo.LinearGradient(0, 0, W, 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.35)
        g.add_color_stop_rgba(1, 0.65, 0.75, 0.9, 0.18)
        cx.set_source(g)
        cx.paint()
        F.post(cx, t, INT, vig=0.7)


def shot_thing(cx, t, st, en, T):
    cam = (pend(t, [(st, 2440), (en, 2470)]), 1060, pend(t, [(st, 1.35), (en, 1.42)]))
    S.WIND_BIAS = 0.06
    S.exterior(cx, t, cam, actors_corn=F.thing(t, st - 0.4, en + 0.4),
               corn_disturb=(2330 + 330 * smooth(prog(t, st - 0.4, en + 0.4)), 1.1, True), fog_k=1.2)
    S.WIND_BIAS = 0.0
    F.post(cx, t, EXT, vig=0.72)


def shot_end(cx, t, st, en, T):
    src(cx, (0, 0, 0, 1))
    cx.paint()
    a = smooth(prog(t, st + 0.2, st + 0.45))
    D.label(cx, "PART 3", W / 2, H / 2, 48, fill=S.MUTED_WHITE, outline=None, alpha=a, spacing=10, shadow=False)
    w = 56 * smooth(prog(t, st + 0.25, st + 0.6))
    line(cx, [(W / 2 - w, H / 2 + 52), (W / 2 + w, H / 2 + 52)], (*S.AMBER[:3], a), 3)


def reuse(name):
    def f(cx, t, st, en, T):
        getattr(F, "shot_" + name)(cx, t, st, en, T)
    return f


SHOTS = {"hook": shot_hook, "exinf": shot_exinf, "approach": reuse("approach"), "peek": shot_peek,
         "science": shot_science, "doubt": shot_doubt, "decide": shot_decide, "talk": shot_talk,
         "radio": reuse("radio"), "dial": reuse("dial"), "ots": reuse("ots"), "barn": reuse("barn"),
         "faces": reuse("faces"), "heroeyes": reuse("heroeyes"), "corn": reuse("corn"), "stop": shot_stop,
         "lowcorn": shot_lowcorn, "retreat": shot_retreat, "watch": shot_watch, "thing": shot_thing,
         "end": shot_end}


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
def sfx_events():
    T, shots, total, _ = timeline()
    st = dict(shots)
    ev = []
    for kt in hook_knocks():
        ev.append((kt, F.door_knock(), 1.0))
        ev.append((kt + 0.02, A.sfx_crash_wood()[: int(0.25 * SR)] * 0.25, 0.5))
    ev.append((0.9, F.creak(), 0.25))
    ev.append((1.9, F.distant_breath(1.6, 7), 0.25))         # quiet breathing behind the glass
    for k in range(3):
        ev.append((st["exinf"] + 0.3 + k * 0.7, F.distant_breath(1.3, 20 + k), 0.2))
    for k in range(4):
        ev.append((st["approach"] + 0.25 + k * 0.62, F.step_soft(k), 0.4))
    ev.append((st["approach"] + 0.9, F.creak(), 0.3))
    a03 = T["a03"]
    for kt in (a03[0] + 0.62 * (a03[1] - a03[0]), a03[0] + 0.62 * (a03[1] - a03[0]) + 0.36):
        ev.append((kt, F.door_knock() * 0.8, 0.6))
    a05 = T["a05"]
    for t0 in (a05[0], a05[0] + 0.5, a05[0] + 1.0):
        ev.append((t0, F.tick(), 0.5))
    ev.append((st["doubt"] + 0.2, A.sfx_heartbeat(), 0.22))
    ev.append((st["doubt"] + 1.1, A.sfx_heartbeat(), 0.22))
    ev.append((st["decide"] + 0.3, F.creak(), 0.2))
    ev.append((st["decide"] + 0.9, F.step_soft(30), 0.35))
    ev.append((st["radio"] + 0.5, A.sfx_thud(200, 0.15), 0.25))
    ev.append((st["radio"] + 1.0, A.sfx_click(), 0.4))
    ev.append((st["radio"] + 1.05, F.static(st["ots"] - st["radio"] - 1.0), 0.45))
    for k in range(4):
        ev.append((st["barn"] + 0.2 + k * 0.9, F.distant_breath(1.4, 40 + k), 0.12))
    ev.append((st["corn"], F.rustle(st["stop"] - st["corn"] + 0.5, 7), 0.2))
    # ending: everything drops away except a low rumble; then the corn
    stop, turns, first_back, turn_away, group = ending_beats(T)
    ev.append((stop - 0.3, F.rumble(total - stop + 0.3, 9), 0.3))
    ev.append((stop - 0.2, F.rumble(st["retreat"] - stop + 0.4, 10), 0.22))
    for k in range(3):
        ev.append((turns[k] + 0.1, F.creak() * 0.5, 0.08))
    ev.append((st["lowcorn"], F.rustle(st["retreat"] - st["lowcorn"] + 0.3, 12), 0.5))
    ev.append((st["lowcorn"] + 0.6, A.sfx_thud(45, 0.6), 0.35))           # heavy footfalls in the rows
    ev.append((st["lowcorn"] + 1.6, A.sfx_thud(42, 0.6), 0.3))
    ev.append((first_back, F.step_soft(70), 0.35))
    ev.append((turn_away, F.step_soft(71), 0.35))
    for k in range(5):
        ev.append((group + k * 0.32, F.step_soft(72 + k), 0.28))
    for k in range(5):
        ev.append((st["watch"] + 0.2 + k * 0.7, A.sfx_heartbeat(), 0.12))
    ev.append((st["thing"], F.rustle(1.6, 11), 0.3))
    ev.append((st["end"], F.impact(), 0.95))
    return ev


def music_bed(total):
    T, shots, _, _ = timeline()
    st = dict(shots)
    n = int((total + 1) * SR)
    buf = np.zeros(n + 3 * SR)
    end = st["end"]
    A.add(buf, A.pad(33, end, 0.06) * 0.6, 0)
    A.add(buf, A.pad(40, end - 3.0, 0.05) * 0.25, 3.0)
    A.add(buf, A.pad(45, st["decide"] - st["science"] + 0.5, 0.12) * 0.22, st["science"])
    t = st["radio"]
    while t < st["corn"]:
        A.add(buf, A.bass(33, 0.5) * 0.35, t)
        t += 1.0
    A.add(buf, A.pad(46, end - st["corn"], 0.05) * 0.25, st["corn"])
    tt = A.t_arr(end - st["stop"])
    A.add(buf, np.sin(2 * np.pi * (620 + 50 * tt / tt[-1]) * tt) * 0.02 * (tt / tt[-1]) ** 2, st["stop"])
    tt = np.arange(len(buf)) / SR
    env = np.clip(tt / 0.5, 0, 1) * np.where(tt >= end, 0.0, 1.0)
    # a breath of near-silence when they freeze
    s0 = st["stop"] + 0.3
    env *= 1 - 0.65 * np.clip((tt - s0) / 0.3, 0, 1) * np.clip((st["lowcorn"] - tt) / 0.3, 0, 1)
    return (buf * env)[:n]


OUTSIDE = ("exinf", "barn", "corn", "stop", "lowcorn", "retreat", "thing", "faces")


def ambience(total):
    T, shots, _, _ = timeline()
    n = int((total + 1) * SR)
    w = F.wind(total + 1)[:n]
    lvl = np.full(n, 0.35)
    for (nm, s), (_, e) in zip(shots, shots[1:] + [("x", total)]):
        a, b = int(s * SR), int(e * SR)
        lvl[a:b] = 0.55 if nm in OUTSIDE else (0.15 if nm == "science" else (0.0 if nm == "end" else 0.35))
    return w * A.lp(lvl, 3) * 0.35


def voice_track(total):
    T = timeline()[0]
    clips = V.clips()
    buf = np.zeros(int((total + 1) * SR))
    for lid, (s, e) in T.items():
        if lid in clips:
            c = clips[lid]
            c = c / (np.sqrt(np.mean(c ** 2)) + 1e-9) * 0.09
            if lid in ("a01", "a21"):
                c = c * 1.06
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
    env = A.envelope_follow(np.abs(vox), 0.02, 0.35)
    env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
    late = np.clip((np.arange(n) / SR - (T["a20"][0] - 0.5)) / 0.5, 0, 1)
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
    write_srt(os.path.join(OUTDIR, TITLE + ".srt"))
    print("audio ->", out, f"{total:.2f}s")
    return out


def write_srt(path):
    T = timeline()[0]
    with open(path, "w") as f:
        for i, (lid, text) in enumerate(NARRATION, 1):
            s, e = T[lid]
            f.write(f"{i}\n{F.fmt(s)} --> {F.fmt(e)}\n{text.replace('...', '…')}\n\n")
    print("srt ->", path)


# ============================================================ render
def _worker(args):
    i, f0, f1, path = args
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r",
           str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in range(f0, f1):
        p.stdin.write(bytes(render_frame(fr / FPS).get_data()))
    p.stdin.close()
    p.wait()
    return i


def render_video(workers=4):
    os.makedirs(BUILD, exist_ok=True)
    total = timeline()[2]
    nf = int(round(total * FPS))
    jobs = [(i, f, min(nf, f + 60), os.path.join(BUILD, f"part_{i:03d}.mp4")) for i, f in enumerate(range(0, nf, 60))]
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
    out = os.path.join(OUTDIR, TITLE + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("video ->", out)


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "plan"
    T, shots, total, k = timeline()
    os.makedirs(BUILD, exist_ok=True)
    if cmd == "plan":
        for n, s in shots:
            print(f"{s:6.2f}  [{n}]")
        for lid, (s, e) in T.items():
            print(f"   {s:6.2f}-{e:6.2f} {lid} {TEXT[lid]}")
        print(f"total {total:.2f}s  gap scale {k:.2f}  (voice clips: {len(V.clips())})")
    elif cmd == "stills":
        for x in a[1:]:
            render_frame(float(x)).write_to_png(os.path.join(BUILD, f"still_{float(x):06.2f}.png"))
    elif cmd in ("sheet", "strip"):
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
            c.save()
            c.translate((i % cols) * tw, (i // cols) * th)
            c.scale(tw / W, th / H)
            c.set_source_surface(render_frame(t))
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
        render_video()


if __name__ == "__main__":
    main()

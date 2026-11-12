"""Shared helpers for Episode 1 shots (vertical 1080x1920)."""
import math
import random

import cairo

from cinecode import captions
from cinecode.characters import HERO, Pose, breathe, hero_pose, run, walk  # noqa: F401
from cinecode.core import (FPS, H, OUTLINE, W, Cam, cam_kf, circle, clamp, ease_in, ease_io, ease_out,  # noqa
                           ellipse, fs, hexc, kf, lerp, line, mix, poly, prog, pulse, rrect, shake, smooth, src,
                           text, win, back_out, shade)
from cinecode.timeline import Shot  # noqa: F401
from episodes.zombie_series import farm as F  # noqa: F401
from episodes.zombie_series.cast import (MAILMAN, NEIGHBOR, ZOMBIE_B, ZOMBIE_C, crawl, rooster,  # noqa: F401
                                         shamble, zombie_pose)

# Series caption accent colour (soft yellow #FFD43B); primary text stays white.
captions.YELLOW = (1.0, 0xD4 / 255, 0x3B / 255, 1.0)

ACCENT_Y = 330          # accents sit in the upper-middle, clear of the Shorts UI
ACCENT_SIZE = 118


def fig(cx, sh, cam, f, pose, who=None):
    J = f.draw(cx, pose)
    if who and cam is not None:
        sh.track(who, J, cam)
    return J


def world(cx, cam):
    cx.save()
    cam.apply(cx)


def end(cx):
    cx.restore()


def pick(t, keys):
    v = keys[0][1]
    for k, val in keys:
        if t >= k:
            v = val
    return v


def vignette(cx, a=0.38, inner=0.42):
    g = cairo.RadialGradient(W / 2, H / 2, H * inner * 0.6, W / 2, H / 2, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    cx.set_source(g)
    cx.paint()


def tint(cx, c, a):
    if a <= 0:
        return
    cx.rectangle(0, 0, W, H)
    src(cx, (c[0], c[1], c[2], a))
    cx.fill()


def black(cx, a=1.0):
    tint(cx, (0, 0, 0), a)


def cold_grade(cx, a):
    """Desaturate + cool tint for tense moments."""
    if a <= 0:
        return
    cx.save()
    cx.set_operator(cairo.OPERATOR_HSL_SATURATION)
    cx.rectangle(0, 0, W, H)
    cx.set_source_rgba(0.5, 0.5, 0.5, 0.45 * a)
    cx.fill()
    cx.restore()
    tint(cx, (0.12, 0.2, 0.32), 0.18 * a)


def warm_grade(cx, a):
    tint(cx, (1.0, 0.75, 0.4), 0.07 * a)


def shadow(cx, x, y, w, a=0.25):
    ellipse(cx, x, y, w, w * 0.16)
    src(cx, (0, 0, 0, a))
    cx.fill()


def cut_at(P, lid, offset):
    """End the current shot `offset` seconds into line `lid` (the line keeps playing over the next shot)."""
    P.t = P.m[lid][0] + offset
    return P.t


def sit(p, lean=0.0):
    """Seated legs (side view) - hips at chair height."""
    return p.but(hip_a=84, hip_b=80, knee_a=92, knee_b=88, bob=p.bob + 46, lean=p.lean + lean)


def speed_lines(cx, t, x0, x1, y0, y1, n=10, a=0.45, seed=2, dirx=-1):
    r = random.Random(seed)
    for k in range(n):
        y = y0 + r.random() * (y1 - y0)
        ln = 120 + r.random() * 220
        x = x0 + ((r.random() * (x1 - x0) + dirx * t * 2400) % (x1 - x0))
        line(cx, [(x, y), (x - dirx * ln, y)], (1, 1, 1, a), 5)


def letters(cx, t, x, y, n=5, seed=4):
    """Mail fluttering out of a bag."""
    r = random.Random(seed)
    for k in range(n):
        t0 = k * 0.18
        if t < t0:
            continue
        u = t - t0
        px = x - u * (180 + r.random() * 120) + math.sin(u * 6 + k) * 30
        py = y - 160 * u + 260 * u * u
        rot = u * (4 + k) * (1 if k % 2 else -1)
        cx.save()
        cx.translate(px, py)
        cx.rotate(rot)
        rrect(cx, -30, -20, 60, 40, 3)
        fs(cx, hexc("#F3EEE2"), OUTLINE, 3.5)
        line(cx, [(-30, -20), (0, 4), (30, -20)], OUTLINE, 3)
        cx.restore()


def glint(cx, x, y, r, a):
    if a <= 0:
        return
    cx.save()
    cx.translate(x, y)
    for ang in (0, math.pi / 2):
        cx.save()
        cx.rotate(ang)
        poly(cx, [(-r, 0), (0, -r * 0.18), (r, 0), (0, r * 0.18)])
        src(cx, (1, 0.98, 0.85, a))
        cx.fill()
        cx.restore()
    cx.restore()

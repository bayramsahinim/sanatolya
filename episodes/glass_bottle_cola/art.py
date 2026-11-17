"""Drawing kit for the glass-bottle cola Short (1080x1920 portrait).

Bottles, can, molecules, material cross-sections, tongue, calendar, mascot.
All vector (Cairo), Just Needy look: clean dark outlines, flat colour with soft
dimensional shading.
"""
import functools
import math
import random

import cairo

from cinecode.core import (OUTLINE, circle, clamp, ellipse, fs, hexc, line, rrect, smooth_poly, src)

W, H = 1080, 1920
SHELF_Y = 1340

COLA_TOP = hexc("#7a2f17")
COLA_MID = hexc("#5a1f0e")
COLA_DEEP = hexc("#2c0d05")
RED = hexc("#d62b2b")
RED_D = hexc("#9c1a1a")
O_COL = hexc("#ef7a70")
C_COL = hexc("#2a2a2e")
AROMA = [hexc("#7cc76a"), hexc("#f2c14e"), hexc("#ee9250")]


# ===================================================================== surfaces
def _surf(w=W, h=H):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)


@functools.lru_cache(maxsize=None)
def wall_surface(tint="warm"):
    s = _surf()
    cx = cairo.Context(s)
    top, bot = (hexc("#efe0c2"), hexc("#e2c79b")) if tint == "warm" else (hexc("#f3dcd4"), hexc("#e9c6bd"))
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bot)
    cx.set_source(g)
    cx.paint()
    # soft spotlight (arched, like a lamp behind the shelf)
    g = cairo.RadialGradient(W / 2, 760, 60, W / 2, 760, 900)
    g.add_color_stop_rgba(0, 1, 0.97, 0.9, 0.75)
    g.add_color_stop_rgba(0.55, 1, 0.96, 0.88, 0.25)
    g.add_color_stop_rgba(1, 1, 0.96, 0.88, 0)
    cx.set_source(g)
    cx.paint()
    # faint ruled paper lines
    for y in range(140, H, 66):
        line(cx, [(0, y), (W, y)], (0.45, 0.33, 0.2, 0.05), 2)
    # vignette
    g = cairo.RadialGradient(W / 2, H * 0.45, 500, W / 2, H * 0.45, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.25, 0.12, 0.02, 0.35)
    cx.set_source(g)
    cx.paint()
    return s


@functools.lru_cache(maxsize=None)
def shelf_surface():
    s = _surf()
    cx = cairo.Context(s)
    # top surface
    g = cairo.LinearGradient(0, SHELF_Y - 4, 0, SHELF_Y + 34)
    g.add_color_stop_rgba(0, *hexc("#c08657"))
    g.add_color_stop_rgba(1, *hexc("#a06a40"))
    cx.rectangle(0, SHELF_Y, W, 34)
    cx.set_source(g)
    cx.fill()
    # front face
    g = cairo.LinearGradient(0, SHELF_Y + 34, 0, H)
    g.add_color_stop_rgba(0, *hexc("#8a5634"))
    g.add_color_stop_rgba(1, *hexc("#4e2c17"))
    cx.rectangle(0, SHELF_Y + 34, W, H)
    cx.set_source(g)
    cx.fill()
    rnd = random.Random(4)
    for k in range(9):
        y = SHELF_Y + 70 + k * 58 + rnd.uniform(-8, 8)
        line(cx, [(0, y), (W, y + rnd.uniform(-6, 6))], (0.18, 0.08, 0.02, 0.22), 2.5)
    line(cx, [(0, SHELF_Y), (W, SHELF_Y)], OUTLINE, 5)
    line(cx, [(0, SHELF_Y + 34), (W, SHELF_Y + 34)], (0.18, 0.09, 0.04, 0.9), 3)
    line(cx, [(0, SHELF_Y + 4), (W, SHELF_Y + 4)], (1, 0.85, 0.65, 0.35), 3)
    # shadow from lamp onto the wall just above shelf
    return s


def paint_surface(cx, s, alpha=1.0):
    cx.set_source_surface(s, 0, 0)
    cx.paint_with_alpha(alpha)


def contact_shadow(cx, x, w, alpha=0.35):
    cx.save()
    g = cairo.RadialGradient(x, SHELF_Y + 6, 4, x, SHELF_Y + 6, w)
    g.add_color_stop_rgba(0, 0.12, 0.05, 0.0, alpha)
    g.add_color_stop_rgba(1, 0.12, 0.05, 0.0, 0)
    cx.translate(0, SHELF_Y + 6)
    cx.scale(1, 0.18)
    cx.translate(0, -(SHELF_Y + 6))
    cx.set_source(g)
    cx.arc(x, SHELF_Y + 6, w, 0, 2 * math.pi)
    cx.fill()
    cx.restore()


def warm_glow(cx, x, y, r, alpha=0.35):
    g = cairo.RadialGradient(x, y, 10, x, y, r)
    g.add_color_stop_rgba(0, 0.98, 0.62, 0.3, alpha)
    g.add_color_stop_rgba(1, 0.98, 0.62, 0.3, 0)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.fill()


# ===================================================================== molecules
def co2(cx, x, y, ang=0.0, s=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    dx, dy = math.cos(ang) * 21 * s, math.sin(ang) * 21 * s
    cx.push_group()
    line(cx, [(x - dx, y - dy), (x + dx, y + dy)], OUTLINE, 6 * s)
    for (px, py), r, c in (((x - dx, y - dy), 11.5, O_COL), ((x + dx, y + dy), 11.5, O_COL), ((x, y), 12.5, C_COL)):
        circle(cx, px, py, r * s)
        fs(cx, c, OUTLINE, 3.2 * s)
        circle(cx, px - r * s * 0.35, py - r * s * 0.35, r * s * 0.3)
        fill_a(cx, (1, 1, 1, 0.45 if c is not C_COL else 0.25))
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def fill_a(cx, c):
    src(cx, c)
    cx.fill()


def aroma(cx, x, y, kind=0, ang=0.0, s=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    col = AROMA[kind % 3]
    cx.push_group()
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    # tail chain
    pts = [(0, 0), (22, 10), (40, 2)]
    line(cx, pts, OUTLINE, 3)
    for px, py in pts[1:]:
        circle(cx, px, py, 5)
        fs(cx, col, OUTLINE, 2.4)
    hexp = [(13 * math.cos(a), 13 * math.sin(a)) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]
    cx.move_to(*hexp[0])
    for p in hexp[1:]:
        cx.line_to(*p)
    cx.close_path()
    fs(cx, col, OUTLINE, 3.2)
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def bubble(cx, x, y, r, alpha=0.6):
    circle(cx, x, y, r)
    src(cx, (1, 0.85, 0.75, 0.10 * alpha))
    cx.fill_preserve()
    src(cx, (1, 0.88, 0.78, 0.55 * alpha))
    cx.set_line_width(max(1.2, r * 0.28))
    cx.stroke()


def sparkle(cx, x, y, r, alpha=1.0, col=None):
    if alpha <= 0.01 or r <= 0.5:
        return
    col = col or hexc("#f2b04a")
    cx.move_to(x, y - r)
    for k in range(4):
        a1 = -math.pi / 2 + k * math.pi / 2
        a2 = a1 + math.pi / 4
        a3 = a1 + math.pi / 2
        cx.curve_to(x + math.cos(a2) * r * 0.18, y + math.sin(a2) * r * 0.18,
                    x + math.cos(a2) * r * 0.18, y + math.sin(a2) * r * 0.18,
                    x + math.cos(a3) * r, y + math.sin(a3) * r)
    cx.close_path()
    src(cx, (*col[:3], alpha))
    cx.fill_preserve()
    src(cx, (0.45, 0.22, 0.05, 0.8 * alpha))
    cx.set_line_width(max(1.5, r * 0.07))
    cx.stroke()


# ===================================================================== bottles
GLASS = [(76, 0), (88, 12), (91, 52), (77, 140), (93, 222), (100, 302), (97, 372), (81, 432), (57, 482),
         (39, 522), (32, 560), (33, 584), (37, 592), (37, 606)]
GLASS_LEVEL = 548
PET = [(62, 0), (80, 5), (89, 28), (91, 70), (91, 196), (85, 210), (91, 224), (91, 410), (82, 462),
       (60, 515), (41, 556), (32, 580), (32, 600)]
PET_LEVEL = 505


def _outline(prof, inset=0.0):
    pts = [(max(3, hw - inset), y + (inset * 0.6 if y == 0 else 0)) for hw, y in prof]
    right = pts
    left = [(-hw, y) for hw, y in reversed(pts)]
    top = (0, pts[-1][1] + 0.5)
    bot = (0, pts[0][1] - 0.5)
    return right + [top] + left + [bot]


def _path(cx, prof, x, base, s, inset=0.0, sx=1.0):
    pts = [(x + px * s * sx, base - py * s) for px, py in _outline(prof, inset)]
    smooth_poly(cx, pts, close=True, k=0.55)


def _hw_at(prof, y):
    for (h0, y0), (h1, y1) in zip(prof, prof[1:]):
        if y0 <= y <= y1:
            return h0 + (h1 - h0) * (y - y0) / max(1e-6, y1 - y0)
    return prof[-1][0]


def _bubble_field(seed, n):
    rnd = random.Random(seed)
    return [(rnd.uniform(-0.85, 0.85), rnd.random(), rnd.uniform(40, 120), rnd.uniform(2.5, 6.5),
             rnd.uniform(0, 6.28)) for _ in range(n)]


BF_GLASS = _bubble_field(11, 70)
BF_PET = _bubble_field(12, 70)


def _liquid(cx, prof, x, base, s, level, t, density=1.0, field=BF_GLASS, sx=1.0, fizz=0.0):
    cx.save()
    _path(cx, prof, x, base, s, inset=9, sx=sx)
    cx.clip()
    top = base - level * s
    hw = 100 * s * sx
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    g.add_color_stop_rgba(0, *COLA_DEEP)
    g.add_color_stop_rgba(0.3, *COLA_MID)
    g.add_color_stop_rgba(0.55, *COLA_TOP)
    g.add_color_stop_rgba(1, *COLA_DEEP)
    cx.rectangle(x - hw - 20, top, 2 * hw + 40, base - top + 10)
    cx.set_source(g)
    cx.fill()
    g = cairo.LinearGradient(0, top, 0, base)
    g.add_color_stop_rgba(0, 0.75, 0.32, 0.12, 0.25)
    g.add_color_stop_rgba(0.25, 0.75, 0.32, 0.12, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.25)
    cx.rectangle(x - hw - 20, top, 2 * hw + 40, base - top + 10)
    cx.set_source(g)
    cx.fill()
    # meniscus
    line(cx, [(x - hw, top), (x + hw, top)], (0.95, 0.55, 0.35, 0.55), 3 * s)
    # bubbles
    nb = int(len(field) * clamp(density, 0, 1.5))
    for i, (u, ph, sp, r, wph) in enumerate(field[:min(nb, len(field))]):
        yy = ((ph * level + t * sp * (1 + fizz * 2.5)) % (level - 10))
        hwl = _hw_at(prof, yy) - 14
        bx = x + (u * hwl + math.sin(t * 2 + wph) * 3) * s * sx
        by = base - (yy + 6) * s
        bubble(cx, bx, by, r * s * 0.8)
    if fizz > 0 and nb > len(field):
        for u, ph, sp, r, wph in field[: nb - len(field)]:
            yy = ((ph * level + t * sp * 3.5 + 37) % (level - 10))
            hwl = _hw_at(prof, yy) - 14
            bubble(cx, x + u * hwl * s * sx * 0.9, base - (yy + 6) * s, r * s * 0.6)
    cx.restore()


def glass_bottle(cx, x, base, s, t, cap=1.0, cap_off=(0, 0, 0), density=1.0, fizz=0.0, sx=1.0,
                 shine=0.0, liquid=True):
    """cap: alpha of crown cap; cap_off: (dx, dy, rot) in px/rad."""
    prof = GLASS
    # glass body (behind liquid)
    _path(cx, prof, x, base, s, sx=sx)
    src(cx, (0.86, 0.94, 0.9, 0.35))
    cx.fill()
    if liquid:
        _liquid(cx, prof, x, base, s, GLASS_LEVEL, t, density, BF_GLASS, sx, fizz)
    # label band
    cx.save()
    _path(cx, prof, x, base, s, inset=0, sx=sx)
    cx.clip()
    y0, y1 = base - 352 * s, base - 268 * s
    hw = 104 * s * sx
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    g.add_color_stop_rgba(0, *RED_D)
    g.add_color_stop_rgba(0.3, *hexc("#e23a36"))
    g.add_color_stop_rgba(0.42, *hexc("#f05a52"))
    g.add_color_stop_rgba(0.6, *RED)
    g.add_color_stop_rgba(1, *hexc("#7e1212"))
    cx.rectangle(x - hw, y0, 2 * hw, y1 - y0)
    cx.set_source(g)
    cx.fill()
    line(cx, [(x - hw, y0), (x + hw, y0)], (0.35, 0.05, 0.05, 0.8), 3 * s)
    line(cx, [(x - hw, y1), (x + hw, y1)], (0.35, 0.05, 0.05, 0.8), 3 * s)
    # glass flutes + highlights
    for k in (-0.55, -0.2, 0.2, 0.55):
        line(cx, [(x + k * 80 * s * sx, base - 40 * s), (x + k * 88 * s * sx, base - 250 * s)],
             (1, 1, 1, 0.13), 3 * s)
        line(cx, [(x + k * 85 * s * sx, base - 365 * s), (x + k * 70 * s * sx, base - 440 * s)],
             (1, 1, 1, 0.13), 3 * s)
    hl = [(x + (-_hw_at(prof, yy) + 22) * s * sx, base - yy * s) for yy in range(20, 560, 20)]
    line(cx, hl, (1, 1, 1, 0.42), 9 * s)
    hl2 = [(x + (_hw_at(prof, yy) - 17) * s * sx, base - yy * s) for yy in range(60, 420, 20)]
    line(cx, hl2, (1, 1, 1, 0.18), 5 * s)
    if shine > 0:
        sxp = x - 160 * s + shine * 320 * s
        g = cairo.LinearGradient(sxp - 60 * s, 0, sxp + 60 * s, 0)
        g.add_color_stop_rgba(0, 1, 1, 1, 0)
        g.add_color_stop_rgba(0.5, 1, 1, 1, 0.35)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        cx.set_source(g)
        cx.paint()
    cx.restore()
    # outline + rim
    _path(cx, prof, x, base, s, sx=sx)
    fs(cx, None, OUTLINE, 5.5 * s)
    _path(cx, prof, x, base, s, inset=8, sx=sx)
    src(cx, (0.2, 0.08, 0.04, 0.25))
    cx.set_line_width(2 * s)
    cx.stroke()
    lip = base - 592 * s
    rrect(cx, x - 40 * s * sx, lip - 15 * s, 80 * s * sx, 18 * s, 8 * s)
    fs(cx, (0.9, 0.95, 0.92, 0.45), OUTLINE, 4.5 * s)
    if cap > 0.01:
        crown_cap(cx, x + cap_off[0], base - 606 * s + cap_off[1], s, cap_off[2], cap)


def crown_cap(cx, x, ybot, s, rot=0.0, alpha=1.0):
    cx.push_group()
    cx.save()
    cx.translate(x, ybot - 14 * s)
    cx.rotate(rot)
    w, h = 47 * s, 15 * s
    cx.move_to(-w + 4 * s, -h)
    cx.curve_to(-w + 4 * s, -h - 9 * s, w - 4 * s, -h - 9 * s, w - 4 * s, -h)
    n = 11
    cx.line_to(w, h - 3 * s)
    for k in range(n, -1, -1):
        px = -w + 2 * w * k / n
        cx.line_to(px, h + (5 * s if k % 2 else 0))
    cx.line_to(-w, h - 3 * s)
    cx.close_path()
    g = cairo.LinearGradient(-w, 0, w, 0)
    g.add_color_stop_rgba(0, *RED_D)
    g.add_color_stop_rgba(0.35, *hexc("#f05048"))
    g.add_color_stop_rgba(1, *hexc("#8e1616"))
    cx.set_source(g)
    cx.fill_preserve()
    fs(cx, None, OUTLINE, 4.5 * s)
    for k in range(1, n):
        px = -w + 2 * w * k / n
        line(cx, [(px, -h + 4 * s), (px, h)], (0.4, 0.05, 0.05, 0.5), 2 * s)
    line(cx, [(-w * 0.6, -h - 2 * s), (w * 0.2, -h - 4 * s)], (1, 1, 1, 0.5), 3 * s)
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def pet_bottle(cx, x, base, s, t, density=1.0, sx=1.0, wall_glow=0.0, label_stamp=0.0):
    prof = PET
    _path(cx, prof, x, base, s, sx=sx)
    src(cx, (0.9, 0.96, 1.0, 0.28))
    cx.fill()
    _liquid(cx, prof, x, base, s, PET_LEVEL, t, density, BF_PET, sx)
    cx.save()
    _path(cx, prof, x, base, s, sx=sx)
    cx.clip()
    hw = 95 * s * sx
    y0, y1 = base - 196 * s, base - 106 * s
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    g.add_color_stop_rgba(0, *RED_D)
    g.add_color_stop_rgba(0.35, *hexc("#ea4840"))
    g.add_color_stop_rgba(0.6, *RED)
    g.add_color_stop_rgba(1, *hexc("#7e1212"))
    cx.rectangle(x - hw, y0, 2 * hw, y1 - y0)
    cx.set_source(g)
    cx.fill()
    for yy in (y0, y1):
        line(cx, [(x - hw, yy), (x + hw, yy)], (0.35, 0.05, 0.05, 0.8), 3 * s)
    # grooves + petaloid base
    for gy in (210, 300, 390):
        line(cx, [(x - 88 * s * sx, base - gy * s), (x + 88 * s * sx, base - gy * s)], (1, 1, 1, 0.22), 3 * s)
    for k in (-0.45, 0, 0.45):
        line(cx, [(x + k * 85 * s * sx, base - 2 * s), (x + k * 70 * s * sx, base - 34 * s)], (0.1, 0.05, 0.03, 0.35), 3 * s)
    # glossy highlights (plastic = broad soft sheen)
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    g.add_color_stop_rgba(0.08, 1, 1, 1, 0)
    g.add_color_stop_rgba(0.2, 1, 1, 1, 0.38)
    g.add_color_stop_rgba(0.3, 1, 1, 1, 0.05)
    g.add_color_stop_rgba(0.8, 1, 1, 1, 0.0)
    g.add_color_stop_rgba(0.88, 1, 1, 1, 0.2)
    g.add_color_stop_rgba(0.95, 1, 1, 1, 0)
    cx.set_source(g)
    cx.paint()
    if wall_glow > 0:
        _path(cx, prof, x, base, s, sx=sx)
        src(cx, (1, 0.5, 0.45, 0.5 * wall_glow))
        cx.set_line_width(26 * s)
        cx.stroke()
    cx.restore()
    _path(cx, prof, x, base, s, sx=sx)
    fs(cx, None, OUTLINE, 4.5 * s)
    # neck ring + cap
    ring = base - 586 * s
    rrect(cx, x - 43 * s * sx, ring - 6 * s, 86 * s * sx, 12 * s, 5 * s)
    fs(cx, (0.92, 0.96, 1, 0.8), OUTLINE, 3.5 * s)
    cy0 = base - 650 * s
    rrect(cx, x - 36 * s * sx, cy0, 72 * s * sx, 56 * s, 8 * s)
    g = cairo.LinearGradient(x - 36 * s, 0, x + 36 * s, 0)
    g.add_color_stop_rgba(0, *RED_D)
    g.add_color_stop_rgba(0.35, *hexc("#f05048"))
    g.add_color_stop_rgba(1, *hexc("#8e1616"))
    cx.set_source(g)
    cx.fill_preserve()
    fs(cx, None, OUTLINE, 4.5 * s)
    for k in range(-3, 4):
        line(cx, [(x + k * 9 * s * sx, cy0 + 12 * s), (x + k * 9 * s * sx, cy0 + 50 * s)], (0.4, 0.05, 0.05, 0.45), 2 * s)
    if label_stamp > 0:
        stamp(cx, x, base - 151 * s, "FLAT", label_stamp, s)


def stamp(cx, x, y, txt, k, s=1.0):
    """k: 0..1 slam-in progress."""
    sc = 1 + 0.9 * (1 - min(1, k * 1.0)) ** 2
    a = clamp(k * 3)
    cx.save()
    cx.translate(x, y)
    cx.rotate(-0.16)
    cx.scale(sc * s, sc * s)
    cx.push_group()
    rrect(cx, -100, -38, 200, 76, 10)
    src(cx, (0.97, 0.93, 0.88, 0.85))
    cx.fill_preserve()
    src(cx, hexc("#b81c1c"))
    cx.set_line_width(7)
    cx.stroke()
    rrect(cx, -90, -28, 180, 56, 6)
    src(cx, hexc("#b81c1c"))
    cx.set_line_width(3)
    cx.stroke()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(50)
    e = cx.text_extents(txt)
    cx.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
    src(cx, hexc("#b81c1c"))
    cx.show_text(txt)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


# ===================================================================== can
CAN_W, CAN_H = 100, 340


def _can_path(cx, x, base, s):
    pts = [(84, 0), (97, 16), (100, 42), (100, 300), (90, 326), (84, 336)]
    full = [(x + px * s, base - py * s) for px, py in pts] + \
           [(x - px * s, base - py * s) for px, py in reversed(pts)]
    smooth_poly(cx, full, close=True, k=0.35)


def aluminum_can(cx, x, base, s, t, xray=0.0, mols=None):
    """xray 0..1 fades the red sleeve to reveal cola inside; mols: list of (x,y,ang) in local px."""
    # body
    cx.save()
    _can_path(cx, x, base, s)
    cx.clip()
    hw = 100 * s
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    for off, c in ((0, "#666b72"), (0.18, "#c9ced5"), (0.32, "#f4f6f8"), (0.5, "#b4b9c0"), (0.8, "#8c9198"),
                   (1, "#53575d")):
        g.add_color_stop_rgba(off, *hexc(c))
    cx.set_source(g)
    cx.paint()
    # cola visible in xray
    if xray > 0:
        y_top = base - 312 * s
        g2 = cairo.LinearGradient(x - hw, 0, x + hw, 0)
        g2.add_color_stop_rgba(0, *COLA_DEEP)
        g2.add_color_stop_rgba(0.5, *COLA_TOP)
        g2.add_color_stop_rgba(1, *COLA_DEEP)
        cx.rectangle(x - hw + 8 * s, y_top, 2 * hw - 16 * s, base - y_top - 10 * s)
        cx.set_source(g2)
        cx.fill()
        for u, ph, sp, r, wph in BF_PET[:40]:
            yy = (ph * 290 + t * sp) % 290
            bubble(cx, x + u * 86 * s, base - (yy + 14) * s, r * s * 0.75)
        if mols:
            for mx, my, ma in mols:
                co2(cx, x + mx * s, base - my * s, ma, s * 0.85)
    # red sleeve
    g = cairo.LinearGradient(x - hw, 0, x + hw, 0)
    for off, c in ((0, "#6e1010"), (0.16, "#b82222"), (0.3, "#ee4b46"), (0.4, "#d93030"), (0.82, "#a01c1c"),
                   (1, "#5e0e0e")):
        g.add_color_stop_rgba(off, *hexc(c))
    cx.rectangle(x - hw, base - 300 * s, 2 * hw, 258 * s)
    cx.set_source(g)
    cx.paint_with_alpha(1 - 0.72 * xray)
    cx.rectangle(x - hw, base - 300 * s, 2 * hw, 258 * s)
    src(cx, (0.2, 0.02, 0.02, 0.0))
    cx.new_path()
    line(cx, [(x - hw, base - 300 * s), (x + hw, base - 300 * s)], (0.25, 0.05, 0.05, 0.7), 3 * s)
    line(cx, [(x - hw, base - 42 * s), (x + hw, base - 42 * s)], (0.25, 0.05, 0.05, 0.7), 3 * s)
    line(cx, [(x - 52 * s, base - 296 * s), (x - 52 * s, base - 46 * s)], (1, 1, 1, 0.45), 9 * s)
    line(cx, [(x + 70 * s, base - 296 * s), (x + 70 * s, base - 46 * s)], (1, 1, 1, 0.15), 5 * s)
    cx.restore()
    _can_path(cx, x, base, s)
    fs(cx, None, OUTLINE, 5 * s)
    # lid
    ly = base - 336 * s
    ellipse(cx, x, ly, 84 * s, 15 * s)
    g = cairo.LinearGradient(x - 84 * s, 0, x + 84 * s, 0)
    g.add_color_stop_rgba(0, *hexc("#8d9299"))
    g.add_color_stop_rgba(0.4, *hexc("#eef1f4"))
    g.add_color_stop_rgba(1, *hexc("#7d8188"))
    cx.set_source(g)
    cx.fill_preserve()
    fs(cx, None, OUTLINE, 4.5 * s)
    ellipse(cx, x, ly + 1 * s, 70 * s, 11 * s)
    src(cx, (0.3, 0.32, 0.36, 0.6))
    cx.set_line_width(2.5 * s)
    cx.stroke()
    rrect(cx, x - 12 * s, ly - 8 * s, 46 * s, 14 * s, 7 * s)
    fs(cx, hexc("#c3c8ce"), OUTLINE, 3 * s)
    ellipse(cx, x + 24 * s, ly - 1 * s, 6 * s, 3 * s)
    fs(cx, hexc("#5a5e64"), None, 0)


# ===================================================================== cross-sections
def _chain(rnd, y0, y1, w):
    pts = []
    y = rnd.uniform(y0, y1)
    amp = rnd.uniform(20, 70)
    fr = rnd.uniform(0.004, 0.012)
    ph = rnd.uniform(0, 6.28)
    x = -60
    while x < w + 60:
        pts.append((x, clamp(y + amp * math.sin(x * fr + ph) + rnd.uniform(-10, 10), y0 - 30, y1 + 30)))
        x += rnd.uniform(28, 46)
    return pts


@functools.lru_cache(maxsize=None)
def polymer_layers(y0=640, y1=960):
    """(back, front) surfaces of tangled polymer chains (plastic wall cross-section)."""
    rnd = random.Random(7)
    out = []
    for layer in range(2):
        s = _surf()
        cx = cairo.Context(s)
        for k in range(30 if layer == 0 else 8):
            pts = _chain(rnd, y0, y1, W)
            for lw, c in ((15, (0.32, 0.36, 0.44, 1)), (10, (0.97, 0.98, 1.0, 1)), (3, (0.78, 0.82, 0.9, 1))):
                smooth_poly(cx, pts, close=False)
                src(cx, c)
                cx.set_line_width(lw)
                cx.set_line_cap(cairo.LINE_CAP_ROUND)
                cx.stroke()
        out.append(s)
    return tuple(out)


@functools.lru_cache(maxsize=None)
def glass_lattice(y0=0, y1=760):
    s = _surf()
    cx = cairo.Context(s)
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *hexc("#cfe8e3"))
    g.add_color_stop_rgba(1, *hexc("#a9d2cb"))
    cx.rectangle(0, y0, W, y1 - y0)
    cx.set_source(g)
    cx.fill()
    r = 17
    dy = r * 1.732
    row = 0
    y = y0 + r
    while y < y1 - r * 0.6:
        off = r if row % 2 else 0
        x = -r + off
        while x < W + r:
            circle(cx, x, y, r - 2)
            fs(cx, (0.86, 0.95, 0.93, 1), (0.33, 0.52, 0.5, 1), 2.6)
            circle(cx, x - 5, y - 5, 4)
            fill_a(cx, (1, 1, 1, 0.6))
            x += 2 * r
        y += dy
        row += 1
    line(cx, [(0, y1), (W, y1)], OUTLINE, 5)
    return s


@functools.lru_cache(maxsize=None)
def metal_layers(metal_y1=700, liner_y1=762):
    s = _surf()
    cx = cairo.Context(s)
    g = cairo.LinearGradient(0, 0, 0, metal_y1)
    for off, c in ((0, "#9aa0a8"), (0.45, "#dfe3e8"), (0.6, "#f5f7f9"), (0.85, "#b8bec6"), (1, "#7d838b")):
        g.add_color_stop_rgba(off, *hexc(c))
    cx.rectangle(0, 0, W, metal_y1)
    cx.set_source(g)
    cx.fill()
    rnd = random.Random(3)
    for _ in range(140):
        y = rnd.uniform(10, metal_y1 - 10)
        x = rnd.uniform(-200, W)
        line(cx, [(x, y), (x + rnd.uniform(120, 420), y)], (1, 1, 1, rnd.uniform(0.08, 0.25)), rnd.uniform(1, 3))
    for _ in range(60):
        y = rnd.uniform(10, metal_y1 - 10)
        x = rnd.uniform(-200, W)
        line(cx, [(x, y), (x + rnd.uniform(120, 420), y)], (0.2, 0.22, 0.26, rnd.uniform(0.05, 0.15)), 1.5)
    # liner
    cx.rectangle(0, metal_y1, W, liner_y1 - metal_y1)
    src(cx, hexc("#f1e6c8"))
    cx.fill()
    for _ in range(50):
        x = rnd.uniform(0, W)
        y = rnd.uniform(metal_y1 + 8, liner_y1 - 8)
        line(cx, [(x, y), (x + rnd.uniform(20, 60), y + rnd.uniform(-3, 3))], (0.75, 0.65, 0.45, 0.35), 2)
    line(cx, [(0, metal_y1), (W, metal_y1)], OUTLINE, 5)
    line(cx, [(0, liner_y1), (W, liner_y1)], OUTLINE, 4)
    return s


def cola_field(cx, y0, t, seed=1, n=60, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *hexc("#8a3a1a"))
    g.add_color_stop_rgba(0.35, *hexc("#5e200c"))
    g.add_color_stop_rgba(1, *hexc("#2a0c04"))
    cx.rectangle(0, y0, W, y1 - y0)
    cx.set_source(g)
    cx.fill()
    rnd = random.Random(seed)
    span = y1 - y0
    for _ in range(n):
        x = rnd.uniform(0, W)
        ph = rnd.random()
        sp = rnd.uniform(30, 90)
        r = rnd.uniform(4, 11)
        y = y1 - ((ph * span + t * sp) % span)
        bubble(cx, x + math.sin(t * 1.5 + ph * 9) * 6, y, r)


def label_pill(cx, x, y, txt, k, size=46, fg=None, bg=(1, 1, 1, 0.95)):
    if k <= 0.01:
        return
    fg = fg or hexc("#b81c1c")
    cx.save()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(size)
    e = cx.text_extents(txt)
    w, h = e.x_advance + size * 1.3, size * 1.6
    sc = 0.85 + 0.15 * min(1, k)
    cx.translate(x, y + (1 - min(1, k)) * 12)
    cx.scale(sc, sc)
    cx.push_group()
    rrect(cx, -w / 2 + 3, -h / 2 + 6, w, h, h / 2)
    src(cx, (0, 0, 0, 0.18))
    cx.fill()
    rrect(cx, -w / 2, -h / 2, w, h, h / 2)
    fs(cx, bg, OUTLINE, 4.5)
    cx.move_to(-e.x_advance / 2, size * 0.36)
    src(cx, fg)
    cx.show_text(txt)
    cx.pop_group_to_source()
    cx.paint_with_alpha(clamp(k))
    cx.restore()


# ===================================================================== tongue
@functools.lru_cache(maxsize=None)
def tongue_surface(top=760):
    s = _surf()
    cx = cairo.Context(s)

    def edge(x):
        return top + 26 * math.sin(x * 0.006 + 0.4) + 10 * math.sin(x * 0.019)

    cx.move_to(0, H)
    for x in range(0, W + 21, 20):
        cx.line_to(x, edge(x))
    cx.line_to(W, H)
    cx.close_path()
    g = cairo.LinearGradient(0, top - 30, 0, H)
    g.add_color_stop_rgba(0, *hexc("#e8838a"))
    g.add_color_stop_rgba(0.3, *hexc("#d4646f"))
    g.add_color_stop_rgba(1, *hexc("#a8404e"))
    cx.set_source(g)
    cx.fill()
    rnd = random.Random(9)
    for _ in range(170):
        x = rnd.uniform(-20, W + 20)
        y = rnd.uniform(top + 40, H + 20)
        if y < edge(x) + 30:
            continue
        r = rnd.uniform(14, 30) * (0.7 + 0.5 * (y - top) / (H - top))
        ellipse(cx, x, y, r, r * 0.66)
        fs(cx, (0.93, 0.56, 0.6, 1), (0.55, 0.2, 0.26, 0.9), 2.6)
        ellipse(cx, x - r * 0.3, y - r * 0.25, r * 0.3, r * 0.18)
        fill_a(cx, (1, 0.85, 0.86, 0.6))
    # median groove
    line(cx, [(W * 0.5, top + 30), (W * 0.52, H)], (0.5, 0.15, 0.22, 0.5), 7)
    cx.move_to(0, edge(0))
    for x in range(0, W + 21, 20):
        cx.line_to(x, edge(x))
    src(cx, OUTLINE)
    cx.set_line_width(5)
    cx.stroke()
    return s


def tongue_edge(x, top=760):
    return top + 26 * math.sin(x * 0.006 + 0.4) + 10 * math.sin(x * 0.019)


# ===================================================================== calendar + tag
def calendar(cx, x, y, num, flip=0.0, prev=None, s=1.0):
    w, h = 230 * s, 250 * s

    def card(n, ang=0.0, dy=0.0, alpha=1.0):
        cx.save()
        cx.translate(x, y + dy)
        cx.rotate(ang)
        cx.push_group()
        rrect(cx, -w / 2 + 6, -h / 2 + 10, w, h, 18 * s)
        src(cx, (0, 0, 0, 0.15))
        cx.fill()
        rrect(cx, -w / 2, -h / 2, w, h, 18 * s)
        fs(cx, hexc("#fbf7ef"), OUTLINE, 5 * s)
        cx.save()
        rrect(cx, -w / 2, -h / 2, w, h, 18 * s)
        cx.clip()
        cx.rectangle(-w / 2, -h / 2, w, 62 * s)
        src(cx, hexc("#cf2b2b"))
        cx.fill()
        cx.restore()
        line(cx, [(-w / 2, -h / 2 + 62 * s), (w / 2, -h / 2 + 62 * s)], OUTLINE, 4 * s)
        cx.select_font_face("Montserrat ExtraBold")
        cx.set_font_size(36 * s)
        e = cx.text_extents("WEEK")
        cx.move_to(-e.width / 2 - e.x_bearing, -h / 2 + 46 * s)
        src(cx, (1, 1, 1, 1))
        cx.show_text("WEEK")
        cx.set_font_size(118 * s)
        e = cx.text_extents(str(n))
        cx.move_to(-e.width / 2 - e.x_bearing, 74 * s)
        src(cx, OUTLINE)
        cx.show_text(str(n))
        for rx in (-w / 4, w / 4):
            rrect(cx, rx - 7 * s, -h / 2 - 16 * s, 14 * s, 34 * s, 7 * s)
            fs(cx, hexc("#9aa0a8"), OUTLINE, 3 * s)
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
        cx.restore()

    card(num)
    if prev is not None and flip < 1:
        card(prev, ang=-0.5 * flip, dy=flip * 140 * s, alpha=1 - flip)


def gas_tag(cx, x, y, pct, s=1.0, rot=0.18):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(34 * s)
    txt = f"GAS {pct}%"
    e = cx.text_extents(txt)
    w, h = e.x_advance + 36 * s, 58 * s
    cx.move_to(-w / 2 - 14 * s, 0)
    cx.line_to(-w / 2, -h / 2)
    cx.line_to(w / 2, -h / 2)
    cx.line_to(w / 2, h / 2)
    cx.line_to(-w / 2, h / 2)
    cx.close_path()
    fs(cx, hexc("#fbf7ef"), OUTLINE, 4 * s)
    circle(cx, -w / 2 + 2 * s, 0, 5 * s)
    fs(cx, hexc("#e2c79b"), OUTLINE, 2.5 * s)
    col = OUTLINE if pct > 90 else hexc("#b81c1c")
    cx.move_to(-w / 2 + 16 * s, e.height / 2)
    src(cx, col)
    cx.show_text(txt)
    cx.restore()


# ===================================================================== mascot
BLUE = hexc("#0a63f2")
BLUE_D = hexc("#0846b8")


def mascot_peek(cx, x, y, r, look=(-1, 0), mood="worried", blink=0.0):
    """Just Needy mascot: white round head, black oval eyes, thin brows, small mouth,
    royal-blue hoodie collar. (x, y) = head centre."""
    lw = r * 0.06
    # hood collar (behind head, below)
    cx.move_to(x - r * 1.05, y + r * 1.45)
    cx.curve_to(x - r * 1.1, y + r * 0.85, x - r * 0.6, y + r * 0.72, x, y + r * 0.78)
    cx.curve_to(x + r * 0.6, y + r * 0.72, x + r * 1.1, y + r * 0.85, x + r * 1.05, y + r * 1.45)
    cx.close_path()
    fs(cx, BLUE, OUTLINE, lw)
    # neck
    rrect(cx, x - r * 0.2, y + r * 0.7, r * 0.4, r * 0.4, r * 0.05)
    fs(cx, (0.97, 0.97, 1, 1), OUTLINE, lw * 0.8)
    # head
    cx.save()
    circle(cx, x, y, r)
    cx.clip()
    src(cx, hexc("#dcd8ef"))       # lavender crescent shading on the left, as on the model sheet
    cx.paint()
    circle(cx, x + r * 0.2, y - r * 0.04, r * 0.97)
    fill_a(cx, hexc("#fbfbfe"))
    cx.restore()
    circle(cx, x, y, r)
    fs(cx, None, OUTLINE, lw)
    lx, ly = look
    ex = [x - r * 0.3 + lx * r * 0.08, x + r * 0.3 + lx * r * 0.08]
    ey = y - r * 0.08 + ly * r * 0.06
    for e in ex:
        ellipse(cx, e, ey, r * 0.095, r * 0.17 * (1 - 0.9 * blink))
        fs(cx, OUTLINE, None, 0)
    if mood == "worried":
        line(cx, [(ex[0] - r * 0.17, ey - r * 0.25), (ex[0] + r * 0.12, ey - r * 0.36)], OUTLINE, lw * 0.75)
        line(cx, [(ex[1] - r * 0.12, ey - r * 0.36), (ex[1] + r * 0.17, ey - r * 0.25)], OUTLINE, lw * 0.75)
        cx.move_to(x - r * 0.2 + lx * r * 0.05, y + r * 0.42)
        cx.curve_to(x - r * 0.08, y + r * 0.32, x + r * 0.08, y + r * 0.32, x + r * 0.2 + lx * r * 0.05, y + r * 0.42)
    else:
        line(cx, [(ex[0] - r * 0.16, ey - r * 0.3), (ex[0] + r * 0.14, ey - r * 0.36)], OUTLINE, lw * 0.75)
        line(cx, [(ex[1] - r * 0.14, ey - r * 0.36), (ex[1] + r * 0.16, ey - r * 0.3)], OUTLINE, lw * 0.75)
        cx.move_to(x - r * 0.25, y + r * 0.3)
        cx.curve_to(x - r * 0.1, y + r * 0.45, x + r * 0.1, y + r * 0.45, x + r * 0.25, y + r * 0.32)
    src(cx, OUTLINE)
    cx.set_line_width(lw * 0.75)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()

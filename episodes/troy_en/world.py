"""Sets (layered 2.5D backgrounds) and props for the Troy episode.

World space = frame space at zoom 1 (1080 x 1920). Each set is a list of gfx.Layer, back to front:
far layers move less (parallax < 1) and are blurred more (depth of field).
"""
import math
import random

import cairo
import cv2
import numpy as np

from cinecode.core import (OUTLINE, circle, curve, ellipse, fs, hexc, lerp, line, mix, poly, rrect, shade,
                           smooth_poly, src)
from episodes.troy_en import gfx
from episodes.troy_en.gfx import H, LH, LW, PADX, PADY, W, Layer

INK = OUTLINE
X0, X1 = -PADX, W + PADX     # drawable world extents
Y0, Y1 = -PADY, H + PADY

_TEX = {}


def noise_tex(scale=60, seed=1, octaves=4, size=512):
    """Tileable grey value-noise pattern (OPERATOR_OVERLAY friendly)."""
    seed = abs(int(seed)) % 6
    key = (scale, seed, octaves, size)
    if key not in _TEX:
        rng = np.random.default_rng(seed)
        img = np.zeros((size, size), np.float32)
        amp, tot = 1.0, 0.0
        s = scale
        for _ in range(octaves):
            n = max(2, size // max(1, int(s)))
            g = rng.random((n, n)).astype(np.float32)
            g = np.tile(g, (2, 2))
            up = cv2.resize(g, (size * 2, size * 2), interpolation=cv2.INTER_CUBIC)[:size, :size]
            img += up * amp
            tot += amp
            amp *= 0.5
            s /= 2
        img = img / tot
        img = (img - img.min()) / (img.max() - img.min() + 1e-6)
        a = np.zeros((size, size, 4), np.uint8)
        v = (img * 255).astype(np.uint8)
        a[:, :, 0] = a[:, :, 1] = a[:, :, 2] = v
        a[:, :, 3] = 255
        s_ = gfx.from_np(a)
        pat = cairo.SurfacePattern(s_)
        pat.set_extend(cairo.EXTEND_REPEAT)
        _TEX[key] = pat
    return _TEX[key]


def texture(cx, alpha=0.25, scale=60, seed=1, op=cairo.OPERATOR_OVERLAY):
    """Overlay noise inside the current clip."""
    cx.save()
    cx.set_operator(op)
    cx.set_source(noise_tex(scale, seed))
    cx.paint_with_alpha(alpha)
    cx.restore()


def vgrad_fill(cx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(c if len(c) == 4 else (*c, 1)))
    cx.set_source(g)


def rect_all(cx):
    cx.rectangle(X0, Y0, LW, LH)


# ================================================================ common painters
def sky(cx, top, horizon, y_h, sun=None, sun_c=(1, 0.95, 0.8)):
    rect_all(cx)
    vgrad_fill(cx, 0, Y0, 0, y_h, [(0, top), (1, horizon)])
    cx.fill()
    if sun:
        gfx.glow(cx, sun[0], sun[1], sun[2], sun_c, 0.9, cairo.OPERATOR_OVER)


def clouds(cx, n, y0, y1, seed, color=(1, 1, 1), alpha=0.9, shade_c=(0.85, 0.88, 0.95)):
    r = random.Random(seed)
    for _ in range(n):
        x = r.uniform(X0, X1)
        y = r.uniform(y0, y1)
        w = r.uniform(140, 300)
        for k in range(6):
            bx = x + (k - 2.5) * w * 0.28 + r.uniform(-15, 15)
            by = y - math.sin(k / 5 * math.pi) * w * 0.18
            rr = w * r.uniform(0.18, 0.28)
            ellipse(cx, bx, by + rr * 0.15, rr, rr * 0.8)
            src(cx, (*shade_c, alpha))
            cx.fill()
            ellipse(cx, bx - rr * 0.1, by, rr * 0.95, rr * 0.75)
            src(cx, (*color, alpha))
            cx.fill()


def stone_blocks(cx, x, y, w, h, base, seed=1, bw=90, bh=46, mortar=None):
    """Fill a rect with staggered lit stone blocks (clip-friendly)."""
    r = random.Random(seed)
    cx.save()
    cx.rectangle(x, y, w, h)
    cx.clip()
    src(cx, mortar or shade(base, -0.35))
    cx.rectangle(x, y, w, h)
    cx.fill()
    row = 0
    yy = y
    while yy < y + h:
        off = (bw / 2) * (row % 2)
        xx = x - off
        while xx < x + w:
            bwr = bw * r.uniform(0.75, 1.25)
            c = shade(base, r.uniform(-0.12, 0.10))
            rrect(cx, xx + 3, yy + 3, bwr - 6, bh - 6, 6)
            src(cx, c)
            cx.fill()
            # top-light bevel
            rrect(cx, xx + 5, yy + 4, bwr - 10, 8, 4)
            src(cx, shade(c, 0.25), 0.6)
            cx.fill()
            rrect(cx, xx + 5, yy + bh - 14, bwr - 10, 8, 4)
            src(cx, shade(c, -0.2), 0.5)
            cx.fill()
            xx += bwr
        yy += bh
        row += 1
    texture(cx, 0.22, 40, seed + 5)
    cx.restore()


def ground(cx, y, top, bottom, seed=2, tex=0.2):
    cx.save()
    cx.rectangle(X0, y, LW, Y1 - y)
    vgrad_fill(cx, 0, y, 0, Y1, [(0, top), (1, bottom)])
    cx.fill_preserve()
    cx.clip()
    texture(cx, tex, 50, seed)
    cx.restore()


def banner(cx, x, y, w, h, color, sym=True):
    cx.move_to(x, y)
    cx.line_to(x + w, y)
    cx.line_to(x + w, y + h)
    cx.line_to(x + w / 2, y + h - w * 0.4)
    cx.line_to(x, y + h)
    cx.close_path()
    fs(cx, color, INK, 4)
    if sym:
        circle(cx, x + w / 2, y + h * 0.38, w * 0.22)
        fs(cx, hexc("#F2C14E"), INK, 3)
    line(cx, [(x - 8, y), (x + w + 8, y)], hexc("#5B3A1E"), 8)


def tower(cx, x, y, w, h, base, seed):
    stone_blocks(cx, x, y, w, h, base, seed, bw=70, bh=40)
    for i in range(int(w // 46) + 1):
        rrect(cx, x - 6 + i * 46, y - 34, 30, 40, 4)
        src(cx, shade(base, 0.05))
        cx.fill()
    cx.rectangle(x, y, w, h)
    fs(cx, None, shade(base, -0.5), 4)
    # tower shading on right side
    cx.rectangle(x + w * 0.65, y, w * 0.35, h)
    src(cx, (0, 0, 0, 0.12))
    cx.fill()


# ================================================================ SET: beach (day)
BEACH_HORIZON = 900
SAND_Y = 1040


def beach_far(cx):
    sky(cx, hexc("#5FB3E8"), hexc("#FCE7C8"), BEACH_HORIZON, sun=(880, 180, 380))
    clouds(cx, 9, 80, 560, 3)
    # distant hill with Troy
    cx.move_to(X0, 900)
    cx.curve_to(-100, 720, 220, 640, 430, 650)
    cx.curve_to(600, 660, 700, 760, 760, 900)
    cx.close_path()
    src(cx, hexc("#A9B98A"))
    cx.fill()
    base = hexc("#E6D2AE")
    stone_blocks(cx, -120, 560, 760, 120, base, 7, bw=40, bh=22)
    for tx in (-80, 120, 330, 520):
        tower(cx, tx, 480, 80, 180, base, tx)
        banner(cx, tx + 22, 470, 34, 70, hexc("#C0392B"))
    # haze
    cx.rectangle(X0, 400, LW, 520)
    vgrad_fill(cx, 0, 400, 0, 920, [(0, (1, 0.95, 0.85, 0.0)), (1, (1, 0.93, 0.82, 0.55))])
    cx.fill()


def sea_band(cx, y_top, y_bot, x_shore_top, x_shore_bot, night=False, glints=True, seed=4):
    cx.save()
    cx.move_to(x_shore_top, y_top)
    cx.line_to(X1, y_top)
    cx.line_to(X1, y_bot)
    cx.line_to(x_shore_bot, y_bot)
    cx.close_path()
    if night:
        vgrad_fill(cx, 0, y_top, 0, y_bot, [(0, hexc("#1B3358")), (1, hexc("#0E1E38"))])
    else:
        vgrad_fill(cx, 0, y_top, 0, y_bot, [(0, hexc("#5CC6D6")), (0.5, hexc("#2C9BC0")), (1, hexc("#1D7FA6"))])
    cx.fill_preserve()
    cx.clip()
    r = random.Random(seed)
    for _ in range(140):
        x = r.uniform(X0, X1)
        y = y_top + (y_bot - y_top) * r.random() ** 1.6
        w = 10 + (y - y_top) / (y_bot - y_top + 1) * 60
        line(cx, [(x, y), (x + w, y)], (1, 1, 1, 0.35 if not night else 0.18), 2 + (y - y_top) / 200)
    texture(cx, 0.18, 70, seed)
    cx.restore()
    # foam line along the shore
    pts = [(x_shore_top + (x_shore_bot - x_shore_top) * k / 12 + math.sin(k * 1.7) * 14,
            y_top + (y_bot - y_top) * k / 12) for k in range(13)]
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    src(cx, (1, 1, 1, 0.8 if not night else 0.35))
    cx.set_line_width(12)
    cx.stroke()


def beach_mid(cx):
    sea_band(cx, BEACH_HORIZON, SAND_Y + 140, 640, 1180)


def campfire(cx, x, y, s=1.0):
    ellipse(cx, x, y, 70 * s, 20 * s)
    src(cx, hexc("#2B2522"), 0.85)
    cx.fill()
    for a in (-0.4, 0.3, 1.2):
        cx.save()
        cx.translate(x, y - 6 * s)
        cx.rotate(a)
        rrect(cx, -50 * s, -7 * s, 100 * s, 14 * s, 6 * s)
        fs(cx, hexc("#3B2A20"), INK, 3)
        cx.restore()
    for k in range(3):
        circle(cx, x - 20 * s + k * 20 * s, y - 14 * s, 5 * s)
        src(cx, hexc("#FF8A3D"), 0.5)
        cx.fill()


def stuck_spear(cx, x, y, ang, L=230):
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    line(cx, [(0, 0), (0, -L)], INK, 12)
    line(cx, [(0, 0), (0, -L)], hexc("#8A5A33"), 6)
    poly(cx, [(-12, -L), (12, -L), (0, -L - 46)])
    fs(cx, hexc("#B7BEC6"), INK, 4)
    cx.restore()


def beach_ground(cx):
    ground(cx, SAND_Y, hexc("#F1D49B"), hexc("#D9A963"), seed=11, tex=0.18)
    # wet sand near the sea
    cx.move_to(700, SAND_Y)
    cx.line_to(X1, SAND_Y)
    cx.line_to(X1, Y1)
    cx.line_to(1300, Y1)
    cx.close_path()
    src(cx, hexc("#C99A5C"), 0.45)
    cx.fill()
    r = random.Random(8)
    # ripples
    for _ in range(60):
        x = r.uniform(X0, X1)
        y = r.uniform(SAND_Y + 30, Y1)
        w = 30 + (y - SAND_Y) * 0.12
        curve(cx, (x, y), (x + w * 0.3, y - 6), (x + w * 0.7, y - 6), (x + w, y), (0.55, 0.38, 0.2, 0.25), 3)
    # footprints heading to the sea
    for k in range(14):
        x = 300 + k * 52
        y = 1500 - k * 26 + (k % 2) * 18
        ellipse(cx, x, y, 12, 6, -0.3)
        src(cx, (0.5, 0.35, 0.18, 0.35))
        cx.fill()
    campfire(cx, -150, 1220, 0.9)
    campfire(cx, 980, 1180, 0.7)
    stuck_spear(cx, 60, 1150, -0.25)
    stuck_spear(cx, 1050, 1110, 0.35, 180)
    # tent poles + torn cloth
    for x in (-260, 1200):
        line(cx, [(x, 1130), (x + 30, 900)], INK, 12)
        line(cx, [(x, 1130), (x + 30, 900)], hexc("#7A4E2D"), 6)
        cx.move_to(x + 30, 905)
        cx.curve_to(x + 90, 930, x + 70, 990, x + 120, 1010)
        cx.line_to(x + 22, 990)
        cx.close_path()
        fs(cx, hexc("#E8DCC4"), INK, 3.5)


def beach_near(cx):
    r = random.Random(21)
    # blurred foreground: grass tufts + broken amphora + shield
    for x in (-300, -140, 1150, 1330):
        for k in range(9):
            a = -math.pi / 2 + (k - 4) * 0.16
            L = r.uniform(180, 320)
            curve(cx, (x, Y1 - 30), (x + math.cos(a) * L * 0.3, Y1 - 30 + math.sin(a) * L * 0.5),
                  (x + math.cos(a) * L * 0.7, Y1 - 30 + math.sin(a) * L * 0.85),
                  (x + math.cos(a) * L, Y1 - 30 + math.sin(a) * L), hexc("#7F9A4D"), 14)
    ellipse(cx, 1180, 2180, 160, 90)
    fs(cx, hexc("#B5653A"), INK, 6)
    circle(cx, -200, 2150, 150)
    fs(cx, hexc("#C9A13B"), INK, 7)
    circle(cx, -200, 2150, 60)
    fs(cx, hexc("#2E6FB8"), INK, 6)


def SET_BEACH():
    return [Layer(beach_far, 0.25, 2.5), Layer(beach_mid, 0.55, 1.0), Layer(beach_ground, 1.0, 0.0),
            Layer(beach_near, 1.45, 9.0)]


# ================================================================ SET: open sea (day / night)
SEA_H = 980


def sea_far(night):
    def f(cx):
        if night:
            sky(cx, hexc("#0B1530"), hexc("#2B3E6B"), SEA_H, sun=(800, 260, 300), sun_c=(0.7, 0.8, 1.0))
            r = random.Random(5)
            for _ in range(160):
                circle(cx, r.uniform(X0, X1), r.uniform(Y0, SEA_H - 120), r.uniform(1, 3.2))
                src(cx, (1, 1, 1, r.uniform(0.3, 0.9)))
                cx.fill()
            circle(cx, 800, 260, 70)
            fs(cx, hexc("#F4F1DE"), None, 0)
            circle(cx, 778, 245, 14)
            src(cx, (0.8, 0.8, 0.75, 0.5))
            cx.fill()
        else:
            sky(cx, hexc("#4FA8E0"), hexc("#FDEBD0"), SEA_H, sun=(250, 260, 420))
            clouds(cx, 8, 60, 600, 9)
        # island (Tenedos)
        cx.move_to(560, SEA_H + 4)
        cx.curve_to(620, 870, 760, 820, 860, 840)
        cx.curve_to(960, 860, 1060, 900, 1140, SEA_H + 4)
        cx.close_path()
        src(cx, hexc("#26385C") if night else hexc("#7E9B78"))
        cx.fill()
        cx.rectangle(X0, SEA_H - 220, LW, 226)
        vgrad_fill(cx, 0, SEA_H - 220, 0, SEA_H + 6,
                   [(0, (1, 1, 1, 0)), (1, (0.6, 0.7, 0.9, 0.35) if night else (1, 0.95, 0.88, 0.5))])
        cx.fill()
    return f


def sea_water(night):
    def f(cx):
        sea_band(cx, SEA_H, Y1, X0, X0, night=night, seed=12)
        if not night:
            gfx.glow(cx, 250, SEA_H + 60, 300, (1, 0.95, 0.8), 0.35, cairo.OPERATOR_ADD)
        else:
            # moon path
            r = random.Random(3)
            for _ in range(50):
                y = r.uniform(SEA_H + 10, SEA_H + 700)
                w = 20 + (y - SEA_H) * 0.2
                x = 800 + r.uniform(-1, 1) * (30 + (y - SEA_H) * 0.25)
                line(cx, [(x - w / 2, y), (x + w / 2, y)], (1, 1, 0.9, 0.5), 3)
    return f


def SET_SEA(night=False):
    return [Layer(sea_far(night), 0.25, 2.0), Layer(sea_water(night), 0.8, 0.0)]


def ship(cx, x, y, s=1.0, f=1, sail="#F3EBD9", stripe="#2E6FB8", t=0.0, night=False, rowers=True):
    """Greek galley, bow pointing in direction f."""
    cx.save()
    cx.translate(x, y + math.sin(t * 2.0 + x * 0.01) * 6 * s)
    cx.rotate(math.sin(t * 1.6 + x) * 0.03)
    cx.scale(s * f, s)
    dk = 0.55 if night else 1.0
    # hull
    cx.move_to(-230, -40)
    cx.curve_to(-200, 30, 180, 30, 230, -40)
    cx.curve_to(260, -70, 280, -110, 300, -120)
    cx.line_to(250, -60)
    cx.line_to(-230, -60)
    cx.curve_to(-260, -90, -250, -130, -230, -150)
    cx.curve_to(-280, -110, -270, -60, -230, -40)
    cx.close_path()
    fs(cx, shade(hexc("#7A4A26"), -(1 - dk)), INK, 6)
    line(cx, [(-220, -50), (230, -50)], shade(hexc(stripe), -(1 - dk)), 9)
    # eye on the bow
    circle(cx, 205, -30, 12)
    fs(cx, (1, 1, 1, dk), INK, 3)
    circle(cx, 208, -30, 5)
    fs(cx, INK, None, 0)
    if rowers:
        for k in range(7):
            ox = -180 + k * 55
            ph = t * 4 + k * 0.2
            line(cx, [(ox, -20), (ox - 30 + math.sin(ph) * 22, 70)], shade(hexc("#C9A066"), -(1 - dk)), 6)
    # mast + sail
    line(cx, [(0, -60), (0, -380)], INK, 12)
    line(cx, [(0, -60), (0, -380)], shade(hexc("#8A5A33"), -(1 - dk)), 6)
    billow = 30 + math.sin(t * 2.2) * 6
    cx.move_to(-150, -360)
    cx.line_to(150, -360)
    cx.curve_to(150 + billow, -260, 150 + billow, -190, 140, -130)
    cx.line_to(-140, -130)
    cx.curve_to(-150 + billow, -190, -150 + billow, -260, -150, -360)
    cx.close_path()
    fs(cx, shade(hexc(sail), -(1 - dk) * 0.8), INK, 5)
    for k in (-80, 0, 80):
        line(cx, [(k, -360), (k + billow * 0.4, -135)], shade(hexc(stripe), -(1 - dk)), 10)
    line(cx, [(-160, -362), (160, -362)], INK, 10)
    cx.restore()


# ================================================================ SET: reeds
def reeds_far(cx):
    sky(cx, hexc("#7CC0E8"), hexc("#FBE6C6"), 820, sun=(900, 150, 320))
    clouds(cx, 6, 60, 420, 17)
    sea_band(cx, 820, 900, X0, X0, seed=31)
    cx.rectangle(X0, 890, LW, 30)
    src(cx, hexc("#C8B27A"))
    cx.fill()


def reed_clump(cx, x, y, seed, h=420, col="#8FA24F", head="#7A5230", lw=9):
    r = random.Random(seed)
    for k in range(14):
        a = -math.pi / 2 + r.uniform(-0.28, 0.28)
        L = h * r.uniform(0.6, 1.1)
        bx = x + r.uniform(-50, 50)
        ex, ey = bx + math.cos(a) * L, y + math.sin(a) * L
        curve(cx, (bx, y), (bx + (ex - bx) * 0.2, y - L * 0.4), (ex - (ex - bx) * 0.1, ey + L * 0.2), (ex, ey),
              shade(hexc(col), r.uniform(-0.2, 0.15)), lw)
        if r.random() < 0.5:
            ellipse(cx, ex, ey + 18, lw * 0.9, 26, a + math.pi / 2)
            fs(cx, hexc(head), INK, 2.5)


def reeds_mid(cx):
    ground(cx, 920, hexc("#B9A46A"), hexc("#8D7A45"), seed=13, tex=0.14)
    # water pools
    for (x, y, w) in ((200, 1050, 260), (820, 1000, 200), (520, 1300, 340)):
        ellipse(cx, x, y, w, w * 0.18)
        fs(cx, hexc("#6FB4C8"), None, 0)
        ellipse(cx, x - w * 0.2, y - w * 0.05, w * 0.4, w * 0.04)
        src(cx, (1, 1, 1, 0.45))
        cx.fill()
    for i, x in enumerate(range(-300, 1400, 130)):
        reed_clump(cx, x, 960 + (i % 3) * 18, i, 360)
    gfx.glow(cx, 900, 150, 900, (1, 0.9, 0.7), 0.15, cairo.OPERATOR_ADD)


def reeds_near(cx):
    for i, x in enumerate((-280, -120, 1180, 1340)):
        reed_clump(cx, x, Y1, 50 + i, 1300, col="#6E8A3A", lw=26)


def SET_REEDS():
    return [Layer(reeds_far, 0.3, 2.5), Layer(reeds_mid, 1.0, 0.0), Layer(reeds_near, 1.5, 10.0)]


# ================================================================ SET: walls / gate (exterior)
WALL_TOP = 560
WALL_BOT = 1160
GATE_X, GATE_W, GATE_H = 540, 360, 470   # centre x, width, height (bottom at WALL_BOT)


def walls_far(night):
    def f(cx):
        if night:
            sky(cx, hexc("#0C1633"), hexc("#34466E"), WALL_BOT, sun=(260, 200, 260), sun_c=(0.7, 0.8, 1))
            r = random.Random(9)
            for _ in range(120):
                circle(cx, r.uniform(X0, X1), r.uniform(Y0, 500), r.uniform(1, 3))
                src(cx, (1, 1, 1, r.uniform(0.3, 0.9)))
                cx.fill()
            circle(cx, 260, 200, 58)
            fs(cx, hexc("#F4F1DE"), None, 0)
        else:
            sky(cx, hexc("#56AEE6"), hexc("#FFE9C9"), WALL_BOT, sun=(180, 160, 360))
            clouds(cx, 8, 40, 420, 23)
    return f


def wall_body(cx, breach=0.0, night=False):
    base = hexc("#E3CBA0") if not night else hexc("#6C7391")
    stone_blocks(cx, X0, WALL_TOP, LW, WALL_BOT - WALL_TOP, base, 3, bw=120, bh=60)
    # crenellations
    for i in range(int(LW // 80) + 1):
        x = X0 + i * 80
        rrect(cx, x, WALL_TOP - 50, 50, 56, 5)
        src(cx, shade(base, 0.08))
        cx.fill()
    # sloped base shadow
    cx.rectangle(X0, WALL_BOT - 70, LW, 70)
    vgrad_fill(cx, 0, WALL_BOT - 70, 0, WALL_BOT, [(0, (0, 0, 0, 0)), (1, (0, 0, 0, 0.28))])
    cx.fill()
    # towers either side of the gate
    for tx in (GATE_X - GATE_W / 2 - 250, GATE_X + GATE_W / 2 + 60):
        tower(cx, tx, WALL_TOP - 200, 190, WALL_BOT - WALL_TOP + 200, shade(base, 0.04), int(tx))
        banner(cx, tx + 60, WALL_TOP - 160, 70, 170, hexc("#C0392B") if not night else hexc("#6B2230"))
    # gate arch (dark opening)
    gx0 = GATE_X - GATE_W / 2
    gy0 = WALL_BOT - GATE_H
    cx.move_to(gx0, WALL_BOT)
    cx.line_to(gx0, gy0 + GATE_W / 2)
    cx.arc(GATE_X, gy0 + GATE_W / 2, GATE_W / 2, math.pi, 2 * math.pi)
    cx.line_to(gx0 + GATE_W, WALL_BOT)
    cx.close_path()
    fs(cx, hexc("#2A1C14") if not night else hexc("#0E0B14"), INK, 6)
    # lintel stones
    for k in range(9):
        a = math.pi + k * math.pi / 8
        cx.save()
        cx.translate(GATE_X + math.cos(a) * (GATE_W / 2 + 22), gy0 + GATE_W / 2 + math.sin(a) * (GATE_W / 2 + 22))
        cx.rotate(a + math.pi / 2)
        rrect(cx, -24, -22, 48, 44, 5)
        fs(cx, shade(base, -0.06), INK, 3)
        cx.restore()
    if breach > 0:
        # torn-down section to the right of the gate (rubble + bright opening)
        cx.save()
        cx.move_to(GATE_X - GATE_W / 2 - 20, WALL_BOT)
        pts = [(GATE_X - GATE_W / 2 - 20, WALL_BOT), (GATE_X - GATE_W / 2 - 40, 760), (GATE_X - 120, 640),
               (GATE_X + 20, 600), (GATE_X + 160, 650), (GATE_X + GATE_W / 2 + 60, 760),
               (GATE_X + GATE_W / 2 + 40, WALL_BOT)]
        smooth_poly(cx, pts, close=True, k=0.25)
        vgrad_fill(cx, 0, 600, 0, WALL_BOT, [(0, hexc("#8CCBF0") if not night else hexc("#2B3A66")),
                                             (1, hexc("#FFE7C4") if not night else hexc("#1A2340"))])
        cx.fill_preserve()
        cx.save()
        cx.clip_preserve()
        # the city seen through the hole: rooftops + a temple
        hc = hexc("#E9B98A") if not night else hexc("#3A4266")
        for k, (hx, hw, hh) in enumerate(((240, 120, 160), (360, 150, 220), (520, 200, 300), (700, 140, 190),
                                          (820, 130, 150))):
            cx.rectangle(hx, WALL_BOT - hh, hw, hh)
            src(cx, shade(hc, -0.05 * k))
            cx.fill()
            poly(cx, [(hx - 10, WALL_BOT - hh), (hx + hw / 2, WALL_BOT - hh - 50), (hx + hw + 10, WALL_BOT - hh)])
            src(cx, hexc("#B5523B") if not night else hexc("#3B2433"))
            cx.fill()
        cx.restore()
        src(cx, INK)
        cx.set_line_width(6)
        cx.stroke()
        cx.restore()
        r = random.Random(12)
        for k in range(16):
            a = k / 15
            x = lerp(GATE_X - GATE_W / 2 - 40, GATE_X + GATE_W / 2 + 60, a)
            y = 600 + 160 * (2 * a - 1) ** 2 + r.uniform(-10, 10)
            stone(cx, x, y, r.uniform(50, 80), r.uniform(-0.4, 0.4), shade(base, r.uniform(-0.12, 0.05)))


def walls_mid(breach, night):
    def f(cx):
        wall_body(cx, breach, night)
    return f


def walls_ground(breach, night):
    def f(cx):
        if night:
            ground(cx, WALL_BOT, hexc("#3E4766"), hexc("#232A42"), seed=19)
        else:
            ground(cx, WALL_BOT, hexc("#D9B77F"), hexc("#B98B53"), seed=19)
        # road
        cx.move_to(GATE_X - GATE_W / 2, WALL_BOT)
        cx.line_to(GATE_X + GATE_W / 2, WALL_BOT)
        cx.line_to(GATE_X + 700, Y1)
        cx.line_to(GATE_X - 700, Y1)
        cx.close_path()
        src(cx, (0.55, 0.38, 0.22, 0.25) if not night else (0, 0, 0, 0.2))
        cx.fill()
        if breach:
            r = random.Random(4)
            base = hexc("#E3CBA0") if not night else hexc("#6C7391")
            for _ in range(36):
                x = GATE_X + r.uniform(-420, 420)
                y = WALL_BOT + r.uniform(-30, 200)
                w = r.uniform(40, 110)
                cx.save()
                cx.translate(x, y)
                cx.rotate(r.uniform(-0.5, 0.5))
                rrect(cx, -w / 2, -w * 0.3, w, w * 0.6, 8)
                fs(cx, shade(base, r.uniform(-0.15, 0.05)), INK, 4)
                cx.restore()
    return f


def SET_WALLS(breach=0.0, night=False):
    return [Layer(walls_far(night), 0.3, 2.5), Layer(walls_mid(breach, night), 0.85, 0.6),
            Layer(walls_ground(breach, night), 1.0, 0.0)]


# ================================================================ SET: city plaza (day festival / night)
PLAZA_Y = 1120


def plaza_far(night):
    def f(cx):
        if night:
            sky(cx, hexc("#0A1330"), hexc("#2A3A66"), PLAZA_Y, sun=(860, 180, 240), sun_c=(0.7, 0.8, 1))
            r = random.Random(2)
            for _ in range(140):
                circle(cx, r.uniform(X0, X1), r.uniform(Y0, 600), r.uniform(1, 3))
                src(cx, (1, 1, 1, r.uniform(0.3, 0.9)))
                cx.fill()
            circle(cx, 860, 180, 64)
            fs(cx, hexc("#F4F1DE"), None, 0)
        else:
            sky(cx, hexc("#62B6EA"), hexc("#FFE7C4"), PLAZA_Y, sun=(150, 140, 380))
            clouds(cx, 6, 40, 360, 41)
        base = hexc("#EBD9B8") if not night else hexc("#5B6488")
        # temple
        tx, ty = 540, 520
        poly(cx, [(tx - 360, ty), (tx, ty - 170), (tx + 360, ty)])
        fs(cx, shade(base, 0.05), INK, 5)
        rrect(cx, tx - 380, ty, 760, 40, 4)
        fs(cx, base, INK, 4)
        for k in range(7):
            x = tx - 320 + k * 107
            rrect(cx, x - 22, ty + 40, 44, 400, 6)
            vgrad_fill(cx, x - 22, 0, x + 22, 0, [(0, shade(base, 0.1)), (0.6, base), (1, shade(base, -0.2))])
            cx.fill_preserve()
            src(cx, INK)
            cx.set_line_width(4)
            cx.stroke()
        cx.rectangle(tx - 300, ty + 40, 600, 400)
        src(cx, (0, 0, 0, 0.25))
        cx.fill()
        # houses left and right
        for hx, hy, hw, hh, c in ((-300, 720, 300, 420, "#E7B98A"), (-60, 800, 220, 340, "#F0D3A8"),
                                  (900, 760, 280, 380, "#E2A77A"), (1150, 690, 300, 450, "#EFCB9C")):
            col = hexc(c) if not night else shade(hexc(c), -0.6)
            rrect(cx, hx, hy, hw, hh, 6)
            fs(cx, col, INK, 5)
            poly(cx, [(hx - 20, hy), (hx + hw / 2, hy - 70), (hx + hw + 20, hy)])
            fs(cx, hexc("#B5523B") if not night else hexc("#3B2433"), INK, 5)
            for wy in range(int(hy + 60), int(hy + hh - 80), 120):
                rrect(cx, hx + 40, wy, 50, 70, 25)
                fs(cx, hexc("#3B2A20") if not night else hexc("#FFC86B"), INK, 3)
                rrect(cx, hx + hw - 90, wy, 50, 70, 25)
                fs(cx, hexc("#3B2A20") if not night else hexc("#FFC86B"), INK, 3)
        cx.rectangle(X0, 300, LW, PLAZA_Y - 300)
        vgrad_fill(cx, 0, 300, 0, PLAZA_Y, [(0, (1, 1, 1, 0)), (1, (1, 0.92, 0.8, 0.35) if not night
                                                                  else (0.3, 0.4, 0.7, 0.3))])
        cx.fill()
    return f


def plaza_ground(night):
    def f(cx):
        top, bot = (hexc("#E9D3A6"), hexc("#C89F69")) if not night else (hexc("#4A5378"), hexc("#262C48"))
        ground(cx, PLAZA_Y, top, bot, seed=29, tex=0.25)
        # perspective paving lines
        vx = 540
        for k in range(-12, 13):
            line(cx, [(vx + k * 40, PLAZA_Y), (vx + k * 260, Y1)], (0, 0, 0, 0.12), 3)
        y = PLAZA_Y
        step = 20
        while y < Y1:
            line(cx, [(X0, y), (X1, y)], (0, 0, 0, 0.12), 3)
            step *= 1.25
            y += step
        if not night:
            # garland + banners across the top
            for k in range(4):
                x0 = X0 + k * 480
                curve(cx, (x0, 380), (x0 + 160, 520), (x0 + 320, 520), (x0 + 480, 380), hexc("#3E7D3A"), 12)
                r = random.Random(k)
                for j in range(9):
                    tt = j / 8
                    bx = (1 - tt) ** 3 * x0 + 3 * (1 - tt) ** 2 * tt * (x0 + 160) + 3 * (1 - tt) * tt ** 2 * (
                        x0 + 320) + tt ** 3 * (x0 + 480)
                    by = (1 - tt) ** 3 * 380 + 3 * (1 - tt) ** 2 * tt * 520 + 3 * (1 - tt) * tt ** 2 * 520 + tt ** 3 * 380
                    circle(cx, bx, by + 6, 13)
                    fs(cx, hexc(r.choice(["#E94F64", "#F7B32B", "#F25F5C", "#FFFFFF"])), INK, 3)
    return f


def SET_PLAZA(night=False):
    return [Layer(plaza_far(night), 0.35, 2.0), Layer(plaza_ground(night), 1.0, 0.0)]


def torch(cx, x, y, t, s=1.0, seed=0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    line(cx, [(0, 0), (0, -140)], INK, 14)
    line(cx, [(0, 0), (0, -140)], hexc("#7A4E2D"), 8)
    rrect(cx, -20, -170, 40, 34, 8)
    fs(cx, hexc("#5B3A1E"), INK, 4)
    fl = 1 + 0.12 * math.sin(t * 17 + seed) + 0.08 * math.sin(t * 29 + seed * 2)
    cx.move_to(-20, -170)
    cx.curve_to(-26, -210 * fl, 0, -230 * fl, 6, -262 * fl)
    cx.curve_to(18, -220 * fl, 28, -200, 20, -170)
    cx.close_path()
    fs(cx, hexc("#FFB238"), hexc("#D9480F"), 4)
    cx.move_to(-8, -172)
    cx.curve_to(-10, -195 * fl, 0, -205 * fl, 4, -222 * fl)
    cx.curve_to(10, -200 * fl, 12, -186, 8, -172)
    cx.close_path()
    src(cx, hexc("#FFF3B0"))
    cx.fill()
    cx.restore()


def torch_glow(cx, x, y, t, s=1.0, seed=0, r=360):
    fl = 1 + 0.08 * math.sin(t * 13 + seed)
    gfx.glow(cx, x, y - 200 * s, r * s * fl, (1.0, 0.62, 0.25), 0.55)


# ================================================================ SET: inside the horse
def belly_bg(night):
    def f(cx):
        dark = hexc("#3B2414") if not night else hexc("#22170F")
        rect_all(cx)
        src(cx, dark)
        cx.fill()
        r = random.Random(6)
        # planks (horizontal), curving like a hull
        y = Y0
        while y < Y1:
            h = r.uniform(80, 120)
            c = shade(hexc("#8A5A33"), r.uniform(-0.15, 0.1) - (0.25 if night else 0))
            cx.move_to(X0, y)
            cx.curve_to(W * 0.3, y - 30, W * 0.7, y - 30, X1, y)
            cx.line_to(X1, y + h - 6)
            cx.curve_to(W * 0.7, y + h - 36, W * 0.3, y + h - 36, X0, y + h - 6)
            cx.close_path()
            src(cx, c)
            cx.fill_preserve()
            src(cx, shade(c, -0.45))
            cx.set_line_width(5)
            cx.stroke()
            for k in range(int(LW // 160)):
                circle(cx, X0 + 80 + k * 160 + r.uniform(-20, 20), y + h / 2 - 15, 6)
                src(cx, shade(c, -0.5))
                cx.fill()
            y += h
        cx.save()
        rect_all(cx)
        cx.clip()
        texture(cx, 0.14, 30, 8)
        cx.restore()
        # ribs
        for x in (-250, 180, 900, 1330):
            cx.move_to(x - 40, Y0)
            cx.curve_to(x - 90, H * 0.4, x - 90, H * 0.6, x - 40, Y1)
            cx.line_to(x + 40, Y1)
            cx.curve_to(x - 10, H * 0.6, x - 10, H * 0.4, x + 40, Y0)
            cx.close_path()
            fs(cx, shade(hexc("#6B4428"), -0.3 if night else 0), INK, 6)
        # floor
        cx.rectangle(X0, 1420, LW, Y1 - 1420)
        src(cx, shade(hexc("#5A3A20"), -0.2 if night else 0))
        cx.fill()
        line(cx, [(X0, 1420), (X1, 1420)], INK, 6)
        # deep shadow at edges
        g = cairo.RadialGradient(W / 2, H * 0.5, 200, W / 2, H * 0.5, 1300)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
        cx.set_source(g)
        rect_all(cx)
        cx.fill()
    return f


def SET_BELLY(night=False):
    return [Layer(belly_bg(night), 1.0, 0.0)]


SETS = {
    "beach": SET_BEACH, "sea": lambda: SET_SEA(False), "sea_night": lambda: SET_SEA(True),
    "reeds": SET_REEDS, "walls": lambda: SET_WALLS(0, False), "walls_breach": lambda: SET_WALLS(1, False),
    "walls_night": lambda: SET_WALLS(1, True), "plaza": lambda: SET_PLAZA(False),
    "plaza_night": lambda: SET_PLAZA(True), "belly": lambda: SET_BELLY(False),
    "belly_night": lambda: SET_BELLY(True),
}
_CACHE = {}


def get_set(name):
    if name not in _CACHE:
        _CACHE[name] = SETS[name]()
    return _CACHE[name]


# ================================================================ PROP: the horse
WOOD = hexc("#C68A4E")
WOOD_DK = hexc("#8C5A2E")
WOOD_LT = hexc("#E2B27A")


def _plank_fill(cx, base, seed, step=26, vertical=False, ang=0.0):
    """Fill current path with wood + plank lines + nails; keeps path clip inside."""
    cx.save()
    cx.clip_preserve()
    src(cx, base)
    cx.fill_preserve()
    x0, y0, x1, y1 = cx.fill_extents()
    r = random.Random(seed)
    cx.new_path()
    cx.translate((x0 + x1) / 2, (y0 + y1) / 2)
    cx.rotate(ang)
    ext = max(x1 - x0, y1 - y0)
    k = -ext
    while k < ext:
        c = shade(base, r.uniform(-0.1, 0.08))
        if vertical:
            cx.rectangle(k, -ext, step, 2 * ext)
        else:
            cx.rectangle(-ext, k, 2 * ext, step)
        src(cx, c)
        cx.fill()
        if vertical:
            line(cx, [(k, -ext), (k, ext)], shade(base, -0.4), 2.2)
        else:
            line(cx, [(-ext, k), (ext, k)], shade(base, -0.4), 2.2)
        k += step
    cx.restore()


def _shade_body(cx, top=0.35, bottom=0.35, extents=None):
    x0, y0, x1, y1 = extents
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, 1, 0.95, 0.85, top)
    g.add_color_stop_rgba(0.45, 1, 1, 1, 0)
    g.add_color_stop_rgba(1, 0.2, 0.1, 0.05, bottom)
    cx.save()
    cx.clip_preserve()
    cx.set_source(g)
    cx.fill()
    cx.restore()


def horse(cx, x, y, s=1.0, f=-1, t=0.0, hatch=0.0, bow=0.0, spear=0.0, wobble=0.0, roll=0.0, night=False,
          tag=None):
    """Giant wooden horse on a wheeled platform. (x, y) = ground point under the silhouette centre.
    Muzzle tip sits at x + f*525*s, bow at local (300,-760), belly hatch at local x=5 (world x + f*-140*s).
    f=-1 faces left. hatch 0..1 opens the belly hatch. bow 0..1 shows a gift bow. spear 0..1 spear stuck in flank.
    Size at s=1: about 900 px tall, 780 px long."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f, s)           # local space faces right; f=-1 mirrors it to face left
    cx.rotate(wobble)
    cx.translate(-145, 0)        # centre the silhouette (tail..muzzle) on x
    dk = -0.35 if night else 0.0
    wood, wdk, wlt = shade(WOOD, dk), shade(WOOD_DK, dk), shade(WOOD_LT, dk)
    # platform + wheels
    rrect(cx, -380, -110, 760, 70, 10)
    cx.new_path()
    rrect(cx, -380, -110, 760, 70, 10)
    _plank_fill(cx, wdk, 3, 30, vertical=True)
    rrect(cx, -380, -110, 760, 70, 10)
    fs(cx, None, INK, 7)
    for wx in (-270, 270):
        cx.save()
        cx.translate(wx, -45)
        cx.rotate(roll / 60)
        circle(cx, 0, 0, 56)
        fs(cx, wdk, INK, 7)
        circle(cx, 0, 0, 40)
        fs(cx, None, shade(wdk, -0.3), 5)
        for k in range(6):
            a = k * math.pi / 3
            line(cx, [(0, 0), (math.cos(a) * 40, math.sin(a) * 40)], shade(wdk, -0.3), 7)
        circle(cx, 0, 0, 12)
        fs(cx, hexc("#9AA3AD"), INK, 4)
        cx.restore()
    # legs (4 blocky posts, far pair darker)
    for lx, far in ((-240, True), (190, True), (-180, False), (250, False)):
        c = shade(wood, -0.18) if far else wood
        cx.move_to(lx - 38, -500)
        cx.line_to(lx + 38, -500)
        cx.line_to(lx + 32, -112)
        cx.line_to(lx - 32, -112)
        cx.close_path()
        _plank_fill(cx, c, lx, 24, vertical=True)
        cx.move_to(lx - 38, -500)
        cx.line_to(lx + 38, -500)
        cx.line_to(lx + 32, -112)
        cx.line_to(lx - 32, -112)
        cx.close_path()
        fs(cx, None, INK, 6)
        rrect(cx, lx - 40, -150, 80, 40, 6)
        fs(cx, shade(c, -0.3), INK, 5)
    # tail
    for k in range(5):
        curve(cx, (-330, -640), (-420, -600 + k * 10), (-430, -460 + k * 20), (-390 - k * 8, -380 + k * 10),
              INK, 18)
        curve(cx, (-330, -640), (-420, -600 + k * 10), (-430, -460 + k * 20), (-390 - k * 8, -380 + k * 10),
              shade(wdk, -0.1 + k * 0.04), 11)
    # body barrel
    def body_path():
        cx.move_to(-330, -700)
        cx.curve_to(-380, -640, -370, -520, -300, -470)
        cx.curve_to(-120, -430, 140, -430, 300, -470)
        cx.curve_to(380, -520, 390, -650, 330, -720)
        cx.curve_to(150, -770, -150, -770, -330, -700)
        cx.close_path()
    body_path()
    _plank_fill(cx, wood, 11, 30, ang=-0.02)
    body_path()
    _shade_body(cx, 0.35, 0.45, (-380, -770, 390, -430))
    body_path()
    fs(cx, None, INK, 8)
    # nails along plank seams
    r = random.Random(4)
    for k in range(26):
        nx, ny = r.uniform(-300, 300), r.uniform(-730, -480)
        circle(cx, nx, ny, 3.5)
        src(cx, shade(wdk, -0.4))
        cx.fill()
    # belly hatch
    hx0, hy0, hw, hh = -70, -500, 150, 46
    if hatch > 0:
        rrect(cx, hx0, hy0 - 6, hw, hh, 4)
        fs(cx, hexc("#120B07"), INK, 5)
        cx.save()
        cx.translate(hx0, hy0 + hh - 6)
        cx.scale(1, -math.cos(min(1, hatch) * math.pi * 0.55))
        rrect(cx, 0, 0, hw, hh, 4)
        fs(cx, wdk, INK, 5)
        cx.restore()
    else:
        rrect(cx, hx0, hy0 - 6, hw, hh, 4)
        fs(cx, None, shade(wdk, -0.35), 4)
        circle(cx, hx0 + hw - 18, hy0 + hh / 2 - 6, 6)
        fs(cx, hexc("#9AA3AD"), INK, 2.5)
    # neck
    def neck_path():
        cx.move_to(200, -720)
        cx.curve_to(240, -860, 300, -980, 360, -1060)
        cx.line_to(470, -1010)
        cx.curve_to(440, -900, 400, -760, 380, -620)
        cx.close_path()
    neck_path()
    _plank_fill(cx, wood, 13, 28, ang=-0.55)
    neck_path()
    _shade_body(cx, 0.3, 0.3, (200, -1060, 470, -620))
    neck_path()
    fs(cx, None, INK, 8)
    # head
    def head_path():
        cx.move_to(330, -1050)
        cx.curve_to(360, -1120, 440, -1150, 500, -1120)
        cx.line_to(640, -990)
        cx.curve_to(670, -960, 660, -920, 620, -910)
        cx.line_to(520, -920)
        cx.curve_to(470, -930, 430, -960, 400, -990)
        cx.close_path()
    head_path()
    _plank_fill(cx, wood, 17, 26, ang=0.6)
    head_path()
    _shade_body(cx, 0.35, 0.3, (330, -1150, 670, -910))
    head_path()
    fs(cx, None, INK, 8)
    # ears
    for ex in (390, 430):
        poly(cx, [(ex - 20, -1120), (ex + 4, -1200), (ex + 26, -1112)])
        fs(cx, wlt, INK, 6)
    # mane (chunky plank tufts)
    for k in range(8):
        mx = 300 + k * 22
        my = -1080 + k * 52
        poly(cx, [(mx, my), (mx - 70, my - 10), (mx - 20, my + 40)])
        fs(cx, wdk, INK, 5)
    # eye (painted, big and slightly dopey) + nostril + mouth line
    circle(cx, 480, -1070, 26)
    fs(cx, (1, 1, 1, 1) if not night else (0.75, 0.75, 0.8, 1), INK, 5)
    circle(cx, 488, -1066, 12)
    fs(cx, INK, None, 0)
    circle(cx, 484, -1071, 4)
    fs(cx, (1, 1, 1, 1), None, 0)
    ellipse(cx, 625, -945, 10, 7)
    fs(cx, INK, None, 0)
    curve(cx, (560, -925), (590, -915), (620, -915), (640, -925), INK, 5)
    # bridle (red)
    for a_, b_ in (((425, -1125), (455, -985)), ((560, -1035), (585, -935)), ((455, -1000), (575, -985))):
        line(cx, [a_, b_], INK, 15)
        line(cx, [a_, b_], hexc("#C0392B"), 9)
    if bow > 0:
        cx.save()
        cx.translate(300, -760)
        cx.scale(bow, bow)
        for sgn in (-1, 1):
            cx.move_to(0, 0)
            cx.curve_to(sgn * 60, -90, sgn * 150, -40, sgn * 120, 20)
            cx.curve_to(sgn * 90, 50, sgn * 30, 20, 0, 0)
            cx.close_path()
            fs(cx, hexc("#E63946"), INK, 6)
            cx.move_to(sgn * 6, 10)
            cx.line_to(sgn * 50, 130)
            cx.line_to(sgn * 80, 110)
            cx.line_to(sgn * 20, 6)
            cx.close_path()
            fs(cx, hexc("#C1121F"), INK, 5)
        circle(cx, 0, 0, 26)
        fs(cx, hexc("#E63946"), INK, 6)
        cx.restore()
    if tag:
        # gift tag hanging from the bow (text drawn upright)
        cx.save()
        cx.translate(300, -700)
        cx.scale(f, 1)            # un-flip so the text reads correctly
        sw = math.sin(t * 2.4) * 0.06
        cx.rotate(sw)
        line(cx, [(0, 0), (0, 90)], hexc("#7A4E2D"), 4)
        cx.translate(0, 90)
        cx.move_to(-90, 0)
        cx.line_to(90, 0)
        cx.line_to(90, 110)
        cx.line_to(-90, 110)
        cx.close_path()
        fs(cx, hexc("#FFF4D6"), INK, 5)
        circle(cx, 0, 18, 7)
        fs(cx, hexc("#7A4E2D"), INK, 2)
        from cinecode.core import text
        text(cx, tag[0], 0, 62, 34, INK)
        text(cx, tag[1], 0, 98, 30, hexc("#C0392B"))
        cx.restore()
    if spear > 0:
        cx.save()
        cx.translate(-60, -600)
        cx.rotate(-0.3 + math.sin(t * 40) * 0.06 * max(0, 1 - spear) * 0)
        line(cx, [(0, 0), (-330, -170)], INK, 15)
        line(cx, [(0, 0), (-330, -170)], hexc("#8A5A33"), 8)
        cx.restore()
    cx.restore()


def horse_rim(cx, x, y, s, f=-1, color=(1, 0.85, 0.55), alpha=0.25):
    """Warm rim light glow behind the horse silhouette."""
    gfx.glow(cx, x, y - 600 * s, 700 * s, color, alpha, cairo.OPERATOR_ADD)


# ================================================================ PROP: misc
def serpent(cx, pts, t, w=70, col="#3F8F4E", belly="#D9E7A5", seed=0):
    """Thick serpent following a list of points (head = last point)."""
    cx.save()
    smooth_poly(cx, pts, close=False)
    src(cx, INK)
    cx.set_line_width(w + 12)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    smooth_poly(cx, pts, close=False)
    src(cx, hexc(col))
    cx.set_line_width(w)
    cx.stroke()
    smooth_poly(cx, pts, close=False)
    src(cx, hexc(belly))
    cx.set_dash([w * 0.35, w * 0.5], 0)
    cx.set_line_width(w * 0.35)
    cx.stroke()
    cx.set_dash([])
    # head
    hx, hy = pts[-1]
    px, py = pts[-2]
    a = math.atan2(hy - py, hx - px)
    cx.translate(hx, hy)
    cx.rotate(a)
    ellipse(cx, w * 0.3, 0, w * 0.95, w * 0.62)
    fs(cx, hexc(col), INK, 6)
    for sgn in (-1, 1):
        circle(cx, w * 0.45, sgn * w * 0.32, w * 0.2)
        fs(cx, hexc("#FFE066"), INK, 4)
        ellipse(cx, w * 0.48, sgn * w * 0.32, w * 0.05, w * 0.15)
        fs(cx, INK, None, 0)
    fl = (math.sin(t * 14 + seed) > 0)
    if fl:
        line(cx, [(w * 1.2, 0), (w * 1.7, 0), (w * 1.9, -w * 0.15)], hexc("#E63946"), 6)
        line(cx, [(w * 1.7, 0), (w * 1.9, w * 0.15)], hexc("#E63946"), 6)
    cx.restore()


def petal(cx, x, y, a, c, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(a)
    ellipse(cx, 0, 0, 14 * s, 8 * s)
    fs(cx, c, INK, 2.5)
    cx.restore()


def stone(cx, x, y, w, a, c, seed=0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(a)
    rrect(cx, -w / 2, -w * 0.32, w, w * 0.64, w * 0.12)
    fs(cx, c, INK, 4)
    rrect(cx, -w / 2 + 5, -w * 0.32 + 4, w - 10, 8, 4)
    src(cx, shade(c, 0.25), 0.6)
    cx.fill()
    cx.restore()


def dust(cx, x, y, t, t0, n=10, size=120, seed=0, color=(0.92, 0.84, 0.7)):
    """Expanding dust puffs, starting at t0."""
    if t < t0:
        return
    u = t - t0
    r = random.Random(seed)
    for _ in range(n):
        a = r.uniform(math.pi, 2 * math.pi)
        sp = r.uniform(80, 260)
        px = x + math.cos(a) * sp * min(u, 1.6) * 1.2
        py = y + math.sin(a) * sp * min(u, 1.6) * 0.6
        rr = size * r.uniform(0.5, 1.0) * (0.4 + min(u, 1.5))
        al = max(0, 0.75 - u * 0.4)
        circle(cx, px, py, rr)
        src(cx, (*color, al))
        cx.fill()


def rope(cx, a, b, sag=40, lw=9):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag
    curve(cx, a, (mx, my), (mx, my), b, INK, lw + 6)
    curve(cx, a, (mx, my), (mx, my), b, hexc("#C9A66B"), lw)


def pickaxe(cx, x, y, ang, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    line(cx, [(0, 0), (0, -120)], INK, 14)
    line(cx, [(0, 0), (0, -120)], hexc("#8A5A33"), 8)
    cx.move_to(-60, -110)
    cx.curve_to(-20, -140, 20, -140, 60, -110)
    cx.curve_to(20, -128, -20, -128, -60, -110)
    cx.close_path()
    fs(cx, hexc("#9AA3AD"), INK, 5)
    cx.restore()


def storm_cloud(cx, x, y, t, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    for (bx, by, rr) in ((-50, 0, 40), (0, -20, 50), (50, 0, 40), (0, 14, 44)):
        circle(cx, bx, by, rr)
    fs(cx, hexc("#5C6370"), INK, 5)
    r = random.Random(int(t * 12))
    for k in range(6):
        dx = -60 + k * 24
        dy = 50 + ((t * 300 + k * 37) % 120)
        line(cx, [(dx, dy), (dx - 4, dy + 18)], hexc("#7FB7E8"), 4)
    if int(t * 3) % 4 == 0:
        poly(cx, [(10, 40), (-10, 90), (8, 88), (-6, 130), (26, 76), (8, 78)])
        fs(cx, hexc("#FFE066"), INK, 3)
    cx.restore()

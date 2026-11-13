"""Environments for the Okene short.

Heavy, static detail (textured steel, rust, rivets, pipes) is rendered once into high-res
"plates" and re-used every frame through the camera; animated pieces are drawn live.
World units == screen pixels at zoom 1 (screen is 1080x1920).
"""
import math
import random

import cairo
import numpy as np

from cinecode.core import (OUTLINE, H, W, circle, ellipse, fs, hexc, line, mix, poly, rrect, shade,
                           smooth_poly, src, text)
from . import look

DENS = 1.5   # plate pixels per world unit

_plates = {}


class Plate:
    def __init__(self, x0, y0, w, h, surf):
        self.x0, self.y0, self.w, self.h, self.surf = x0, y0, w, h, surf

    def blit(self, cx, alpha=1.0):
        cx.save()
        cx.translate(self.x0, self.y0)
        cx.scale(1 / DENS, 1 / DENS)
        cx.set_source_surface(self.surf, 0, 0)
        cx.get_source().set_filter(cairo.FILTER_GOOD)
        cx.paint_with_alpha(alpha) if alpha < 1 else cx.paint()
        cx.restore()


def plate(name, x0, y0, w, h, fn, tex=None):
    """Render (once per process) a plate covering world rect; fn(cx) draws in world coords.
    tex(arr_h, arr_w) -> float multiplier map (H,W) or (H,W,3) applied after drawing."""
    if name in _plates:
        return _plates[name]
    pw, ph = int(w * DENS), int(h * DENS)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, pw, ph)
    cx = cairo.Context(s)
    cx.scale(DENS, DENS)
    cx.translate(-x0, -y0)
    fn(cx)
    if tex is not None:
        s.flush()
        a = np.ndarray((ph, pw, 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))
        m = tex(ph, pw)
        if m.ndim == 2:
            m = m[..., None]
        rgb = a[:, :, :3].astype(np.float32) * m[:, :, ::-1] if m.shape[2] == 3 else a[:, :, :3].astype(np.float32) * m
        a[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        s.mark_dirty()
    p = Plate(x0, y0, w, h, s)
    _plates[name] = p
    return p


def grime_tex(seed, base=0.82, var=0.36, streak=0.25, tint=(1.0, 0.93, 0.85)):
    def f(h, w):
        n = look.value_noise(w, h, 260, seed=seed, octaves=5)
        st = look.streaks(w, h, seed=seed + 1, length=300)
        fine = look.value_noise(w, h, 18, seed=seed + 2, octaves=2)
        m = base + var * (n - 0.5) - streak * st + 0.08 * (fine - 0.5)
        rust = np.clip((n - 0.62) * 3.0, 0, 1) * 0.6 + st * 0.5
        rgb = np.stack([m * (1 + 0.10 * rust * tint[0]), m * (1 - 0.06 * rust), m * (1 - 0.22 * rust)], 2)
        return np.clip(rgb, 0.25, 1.3)
    return f


# ======================================================================= corridor
VPX, VPY = 540, 800          # vanishing point


def _ring(z, x0=-200, y0=-200, x1=W + 200, y1=H + 200):
    """corridor cross-section rectangle at depth z (0 = front)."""
    k = 1 / (1 + z * 0.9)
    return (VPX + (x0 - VPX) * k, VPY + (y0 - VPY) * k, VPX + (x1 - VPX) * k, VPY + (y1 - VPY) * k)


def _quad(cx, pts, col):
    poly(cx, pts)
    src(cx, col)
    cx.fill()


def corridor_draw(cx, steel="#5F6E6C", deep=6.0):
    rng = random.Random(4)
    wall_l = hexc(steel)
    wall_r = shade(wall_l, -0.18)
    ceil = shade(wall_l, -0.32)        # the old floor (ship is upside down) - now overhead
    floor = shade(wall_l, -0.1)
    zs = [i * 0.5 for i in range(int(deep / 0.5) + 1)]
    for z0, z1 in zip(zs, zs[1:]):
        a, b = _ring(z0), _ring(z1)
        sh = -0.05 * z0
        _quad(cx, [(a[0], a[1]), (b[0], b[1]), (b[0], b[3]), (a[0], a[3])], shade(wall_l, sh))
        _quad(cx, [(a[2], a[1]), (b[2], b[1]), (b[2], b[3]), (a[2], a[3])], shade(wall_r, sh))
        _quad(cx, [(a[0], a[1]), (a[2], a[1]), (b[2], b[1]), (b[0], b[1])], shade(ceil, sh))
        _quad(cx, [(a[0], a[3]), (a[2], a[3]), (b[2], b[3]), (b[0], b[3])], shade(floor, sh))
        # frame ribs at each ring
        for (p, q) in (((b[0], b[1]), (b[0], b[3])), ((b[2], b[1]), (b[2], b[3])),
                       ((b[0], b[1]), (b[2], b[1])), ((b[0], b[3]), (b[2], b[3]))):
            line(cx, [p, q], shade(wall_l, -0.45 + 0.04 * z1), max(2, 14 / (1 + z1)))
    # end of corridor: black opening
    e = _ring(deep)
    cx.rectangle(e[0], e[1], e[2] - e[0], e[3] - e[1])
    src(cx, hexc("#030607"))
    cx.fill()
    # panel seams + rivets on side walls
    for z in [i * 0.25 for i in range(int(deep * 4))]:
        a = _ring(z)
        lw = max(1, 4 / (1 + z))
        line(cx, [(a[0], a[1]), (a[0], a[3])], shade(wall_l, -0.3), lw)
        line(cx, [(a[2], a[1]), (a[2], a[3])], shade(wall_r, -0.3), lw)
        for side in (0, 2):
            for v in np.linspace(0.08, 0.92, 9):
                yy = a[1] + (a[3] - a[1]) * v
                r = max(0.8, 5 / (1 + z))
                circle(cx, a[side] + (r * 2 if side == 0 else -r * 2), yy, r)
                src(cx, shade(wall_l, 0.15))
                cx.fill()
    # horizontal wainscot band
    for v, col in ((0.38, -0.25), (0.40, 0.12), (0.72, -0.2)):
        for side in (0, 2):
            pts = []
            for z in (0, deep):
                a = _ring(z)
                pts.append((a[side], a[1] + (a[3] - a[1]) * v))
            line(cx, pts, shade(wall_l, col), 6)
    # overhead grating (old deck floor, now the ceiling)
    for k in range(12):
        u = k / 11
        a, b = _ring(0), _ring(deep)
        line(cx, [(a[0] + (a[2] - a[0]) * u, a[1]), (b[0] + (b[2] - b[0]) * u, b[1])], shade(ceil, -0.35), 5)
    for z in [i * 0.18 for i in range(int(deep / 0.18))]:
        a = _ring(z)
        line(cx, [(a[0], a[1]), (a[2], a[1])], shade(ceil, -0.3), max(1, 6 / (1 + z)))
    # pipes along two edges
    for (side_x, side_y, off, col, rad) in ((0, 1, (60, 70), "#7B5B3A", 36), (0, 1, (140, 40), "#4F6A73", 24),
                                           (2, 3, (-70, -60), "#8A3B2C", 40), (2, 1, (-50, 120), "#6C7A7E", 22)):
        pts = []
        for z in np.linspace(0, deep, 30):
            a = _ring(z)
            k = 1 / (1 + z * 0.9)
            pts.append((a[side_x] + off[0] * k, a[side_y] + off[1] * k, rad * k))
        for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
            line(cx, [(x0, y0), (x1, y1)], OUTLINE, r0 * 2 + 4)
        for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
            line(cx, [(x0, y0), (x1, y1)], hexc(col), r0 * 2)
            line(cx, [(x0, y0 - r0 * 0.45), (x1, y1 - r1 * 0.45)], shade(hexc(col), 0.3), r0 * 0.5)
        for z in np.linspace(0.2, deep, 9):  # pipe clamps
            a = _ring(z)
            k = 1 / (1 + z * 0.9)
            x, y = a[side_x] + off[0] * k, a[side_y] + off[1] * k
            rrect(cx, x - rad * k * 1.3, y - 6 * k, rad * k * 2.6, 12 * k, 3 * k)
            fs(cx, hexc("#2e3134"), OUTLINE, 2 * k)
    # doorways on the left and right walls
    for (side, z0, z1) in ((0, 1.0, 1.7), (2, 2.4, 3.0), (0, 3.6, 4.1)):
        a, b = _ring(z0), _ring(z1)
        top = 0.12
        bot = 0.95   # upside down: door sill near the top, opening reaches down
        pts = [(a[side], a[1] + (a[3] - a[1]) * top), (b[side], b[1] + (b[3] - b[1]) * top),
               (b[side], b[1] + (b[3] - b[1]) * bot), (a[side], a[1] + (a[3] - a[1]) * bot)]
        poly(cx, pts)
        fs(cx, hexc("#06090a"), shade(wall_l, -0.5), 8 / (1 + z0))
    # dead light fixtures on the floor-turned-ceiling... ceiling-turned-floor
    for z in (0.6, 2.0, 3.4, 4.8):
        a = _ring(z)
        k = 1 / (1 + z * 0.9)
        x = VPX
        y = a[3] - 14 * k
        rrect(cx, x - 120 * k, y - 22 * k, 240 * k, 26 * k, 8 * k)
        fs(cx, hexc("#C9D2CF"), OUTLINE, 3 * k)
        rrect(cx, x - 110 * k, y - 17 * k, 220 * k, 14 * k, 6 * k)
        src(cx, hexc("#8D9A97"))
        cx.fill()
    # upside-down sign
    a = _ring(1.25)
    k = 1 / (1 + 1.25 * 0.9)
    cx.save()
    cx.translate(a[2] - 30 * k, a[1] + (a[3] - a[1]) * 0.55)
    cx.scale(k, k)
    cx.rotate(math.pi)
    rrect(cx, -10, -40, 210, 64, 6)
    fs(cx, hexc("#D9D2B8"), OUTLINE, 4)
    text(cx, "CREW MESS", 95, 3, 30, hexc("#2b3b45"))
    cx.restore()
    # debris clumps on the floor
    for i in range(14):
        z = rng.uniform(0.2, 5)
        a = _ring(z)
        k = 1 / (1 + z * 0.9)
        x = a[0] + (a[2] - a[0]) * rng.random()
        y = a[3] - rng.uniform(0, 30) * k
        ellipse(cx, x, y, rng.uniform(20, 60) * k, rng.uniform(6, 16) * k)
        src(cx, shade(floor, -0.4))
        cx.fill()


def corridor_plate():
    return plate("corridor", -250, -250, W + 500, H + 500, corridor_draw, tex=grime_tex(11))


def corridor_plate_dry():
    """same corridor before the capsize (right way up, warmer)."""
    def fn(cx):
        cx.save()
        cx.translate(W / 2, H / 2)
        cx.rotate(math.pi)
        cx.translate(-W / 2, -H / 2)
        corridor_draw(cx, steel="#7E8784")
        cx.restore()
    return plate("corridor_dry", -250, -250, W + 500, H + 500, fn, tex=grime_tex(12, var=0.25, streak=0.12))


# ======================================================================= air-pocket cabin (upside down)
CAB_X0, CAB_X1 = -300, W + 300
CAB_TOP, CAB_BOT = -700, H + 600
FLOOR_Y = 330      # the old floor, now overhead
CEIL_Y = 1900      # the old ceiling, now deep underwater


def cabin_draw(cx):
    rng = random.Random(8)
    # back wall
    g = cairo.LinearGradient(0, FLOOR_Y, 0, CEIL_Y)
    g.add_color_stop_rgb(0, *hexc("#6E7B78")[:3])
    g.add_color_stop_rgb(1, *hexc("#3E4C4D")[:3])
    cx.rectangle(CAB_X0, FLOOR_Y, CAB_X1 - CAB_X0, CEIL_Y - FLOOR_Y)
    cx.set_source(g)
    cx.fill()
    # wall panels
    for i, x in enumerate(range(CAB_X0, CAB_X1, 260)):
        rrect(cx, x + 10, FLOOR_Y + 40, 240, CEIL_Y - FLOOR_Y - 80, 10)
        fs(cx, shade(hexc("#66736F"), -0.04 * (i % 2)), shade(hexc("#3E4C4D"), -0.3), 5)
        for v in (0.1, 0.5, 0.9):
            for u in (0.06, 0.94):
                circle(cx, x + 10 + 240 * u, FLOOR_Y + 40 + (CEIL_Y - FLOOR_Y - 80) * v, 5)
                fs(cx, hexc("#9AA6A3"), OUTLINE, 2)
    # porthole (outside is black sea)
    px, py = 830, 820
    circle(cx, px, py, 92)
    fs(cx, hexc("#8E979A"), OUTLINE, 6)
    circle(cx, px, py, 72)
    fs(cx, hexc("#03080A"), OUTLINE, 5)
    for k in range(8):
        a = k / 8 * 6.283
        circle(cx, px + math.cos(a) * 82, py + math.sin(a) * 82, 5)
        fs(cx, hexc("#C0C7C9"), OUTLINE, 2)
    cx.move_to(px - 40, py - 40)
    cx.line_to(px - 10, py - 60)
    src(cx, (1, 1, 1, 0.25))
    cx.set_line_width(6)
    cx.stroke()
    # old floor overhead: linoleum + skirting
    cx.rectangle(CAB_X0, CAB_TOP, CAB_X1 - CAB_X0, FLOOR_Y - CAB_TOP)
    src(cx, hexc("#4A3F35"))
    cx.fill()
    for x in range(CAB_X0, CAB_X1, 70):
        line(cx, [(x, CAB_TOP), (x + 30, FLOOR_Y)], hexc("#3B3129"), 3)
    rrect(cx, CAB_X0, FLOOR_Y - 10, CAB_X1 - CAB_X0, 34, 4)
    fs(cx, hexc("#2F3436"), OUTLINE, 4)
    # bolted table hanging upside down from the old floor
    tx = 300
    rrect(cx, tx - 210, FLOOR_Y + 210, 420, 34, 8)
    fs(cx, hexc("#8C6A4A"), OUTLINE, 5)
    for lx in (tx - 180, tx + 180):
        rrect(cx, lx - 9, FLOOR_Y + 20, 18, 194, 5)
        fs(cx, hexc("#9AA2A5"), OUTLINE, 4)
    rrect(cx, tx - 210, FLOOR_Y + 244, 420, 10, 4)
    fs(cx, hexc("#6B4F36"), OUTLINE, 3)
    # bunk frame on the right, upside down
    rrect(cx, 700, FLOOR_Y + 30, 380, 40, 6)
    fs(cx, hexc("#7F8A8C"), OUTLINE, 4)
    rrect(cx, 700, FLOOR_Y + 70, 380, 70, 12)
    fs(cx, hexc("#3C5C7A"), OUTLINE, 4)
    for lx in (712, 1064):
        rrect(cx, lx - 6, FLOOR_Y, 12, 150, 4)
        fs(cx, hexc("#9AA2A5"), OUTLINE, 3)
    # cables & pipe along the wall
    line(cx, [(CAB_X0, FLOOR_Y + 120), (CAB_X1, FLOOR_Y + 120)], OUTLINE, 30)
    line(cx, [(CAB_X0, FLOOR_Y + 120), (CAB_X1, FLOOR_Y + 120)], hexc("#7B5B3A"), 24)
    line(cx, [(CAB_X0, FLOOR_Y + 112), (CAB_X1, FLOOR_Y + 112)], hexc("#A07A52"), 6)
    for x in range(CAB_X0 + 80, CAB_X1, 340):
        rrect(cx, x, FLOOR_Y + 100, 16, 40, 3)
        fs(cx, hexc("#2e3134"), OUTLINE, 2)
    # upside-down notice
    cx.save()
    cx.translate(470, 640)
    cx.rotate(math.pi)
    rrect(cx, -90, -60, 180, 110, 6)
    fs(cx, hexc("#E7E1CC"), OUTLINE, 4)
    text(cx, "LIFE", 0, -14, 30, hexc("#B23A2E"))
    text(cx, "JACKETS", 0, 22, 26, hexc("#2b3b45"))
    cx.restore()
    # old ceiling deep below: light fixture
    rrect(cx, 340, CEIL_Y - 60, 400, 50, 10)
    fs(cx, hexc("#C9D2CF"), OUTLINE, 5)
    cx.rectangle(CAB_X0, CEIL_Y, CAB_X1 - CAB_X0, CAB_BOT - CEIL_Y)
    src(cx, hexc("#2E3A3B"))
    cx.fill()


def cabin_plate():
    return plate("cabin", CAB_X0, CAB_TOP, CAB_X1 - CAB_X0, CAB_BOT - CAB_TOP, cabin_draw, tex=grime_tex(21, var=0.3))


# ======================================================================= seabed + capsized hull
HULL_CX, HULL_Y = 560, 900   # keel line (top of the upturned hull)


def hull_shape(cx, x, y, s=1.0):
    """Upturned tug hull (side view, bow to the left). Origin at keel middle."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-620, 300)          # gunwale bow
    cx.curve_to(-660, 160, -560, 20, -420, -10)
    cx.line_to(380, -20)            # keel
    cx.curve_to(470, -20, 560, 60, 600, 200)
    cx.line_to(620, 300)            # gunwale stern
    cx.close_path()
    cx.restore()


def hull_draw(cx, x=HULL_CX, y=HULL_Y, s=1.0, name=True, sunk=True):
    rng = random.Random(3)
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # inverted superstructure (wheelhouse hanging down, buried in silt)
    rrect(cx, -330, 300, 420, 230, 14)
    fs(cx, hexc("#C9C3B2"), OUTLINE, 7)
    for wx in range(-300, 60, 85):
        rrect(cx, wx, 440, 60, 50, 6)
        fs(cx, hexc("#0B1416"), OUTLINE, 4)
    rrect(cx, -220, 530, 220, 140, 10)
    fs(cx, hexc("#BDB6A4"), OUTLINE, 6)
    # mast pointing down into the seabed
    line(cx, [(-120, 660), (-110, 820)], OUTLINE, 18)
    line(cx, [(-120, 660), (-110, 820)], hexc("#B9B39F"), 10)
    # hull body
    hull_shape(cx, 0, 0)
    src(cx, hexc("#1E2224"))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(8)
    cx.stroke()
    # red antifouling (old underside, now on top)
    cx.save()
    hull_shape(cx, 0, 0)
    cx.clip()
    cx.rectangle(-800, -100, 1600, 230)
    src(cx, hexc("#8E2E24"))
    cx.fill()
    line(cx, [(-700, 130), (700, 130)], hexc("#D9D2C0"), 10)   # boot-top stripe
    # plating seams + weld lines
    for k in range(-640, 660, 92):
        line(cx, [(k, -40), (k + 10, 310)], (0, 0, 0, 0.35), 3)
    for yy in (40, 210, 260):
        line(cx, [(-700, yy), (700, yy)], (0, 0, 0, 0.3), 3)
    # tyre fenders along the gunwale (upside down)
    for k in range(-520, 560, 110):
        ellipse(cx, k, 285, 34, 22)
        fs(cx, hexc("#151515"), OUTLINE, 4)
    # marine growth blotches
    for i in range(60):
        ellipse(cx, rng.uniform(-620, 620), rng.uniform(-20, 300), rng.uniform(8, 40), rng.uniform(4, 16))
        src(cx, (0.35, 0.42, 0.3, rng.uniform(0.15, 0.4)))
        cx.fill()
    cx.restore()
    # upside-down name on the stern quarter
    if name:
        cx.save()
        cx.translate(380, 200)
        cx.rotate(math.pi)
        text(cx, "JASCON 4", 0, 0, 46, hexc("#E9E4D4"))
        cx.restore()
    # rudder + propeller sticking up at the stern
    poly(cx, [(430, -18), (520, -18), (540, -150), (450, -160)])
    fs(cx, hexc("#7F2A22"), OUTLINE, 6)
    cx.save()
    cx.translate(380, -70)
    for k in range(4):
        cx.save()
        cx.rotate(k * math.pi / 2 + 0.4)
        ellipse(cx, 0, -40, 22, 44)
        fs(cx, hexc("#B88A3A"), OUTLINE, 5)
        cx.restore()
    circle(cx, 0, 0, 18)
    fs(cx, hexc("#9C742F"), OUTLINE, 5)
    cx.restore()
    line(cx, [(380, -50), (380, -18)], OUTLINE, 22)
    cx.restore()


def seabed_draw(cx):
    rng = random.Random(6)
    # water backdrop gradient (very murky green-blue)
    g = cairo.LinearGradient(0, -900, 0, 2400)
    g.add_color_stop_rgb(0, 0.16, 0.42, 0.46)
    g.add_color_stop_rgb(0.45, 0.07, 0.2, 0.23)
    g.add_color_stop_rgb(1, 0.03, 0.08, 0.09)
    cx.rectangle(-900, -900, 2900, 3400)
    cx.set_source(g)
    cx.fill()
    # distant seabed ridges
    for k, (yb, col) in enumerate(((1350, "#203B3A"), (1450, "#2A4744"))):
        pts = [(-900, 2500)]
        for x in range(-900, 2100, 120):
            pts.append((x, yb + math.sin(x * 0.004 + k) * 60 + rng.uniform(-20, 20)))
        pts.append((2100, 2500))
        poly(cx, pts)
        src(cx, hexc(col))
        cx.fill()
    hull_draw(cx)
    # silt bank in front of the wreck + rocks
    pts = [(-900, 2500)]
    for x in range(-900, 2100, 80):
        pts.append((x, 1560 + math.sin(x * 0.006) * 50 + rng.uniform(-12, 12)))
    pts.append((2100, 2500))
    poly(cx, pts)
    src(cx, hexc("#5E6B55"))
    cx.fill()
    for i in range(40):
        x = rng.uniform(-800, 1900)
        y = rng.uniform(1560, 2300)
        r = rng.uniform(14, 60)
        ellipse(cx, x, y, r, r * 0.55)
        fs(cx, hexc("#4C5648"), OUTLINE, 3)
    # sea-grass tufts
    for i in range(30):
        x = rng.uniform(-800, 1900)
        y = rng.uniform(1570, 2000)
        for k in range(4):
            cx.move_to(x + k * 6, y)
            cx.curve_to(x + k * 6 - 10, y - 40, x + k * 6 + 14, y - 60, x + k * 6 + rng.uniform(-10, 10), y - 90)
        src(cx, hexc("#3E5B3A"))
        cx.set_line_width(5)
        cx.stroke()


def seabed_plate():
    return plate("seabed", -900, -900, 2900, 3400, seabed_draw, tex=grime_tex(31, var=0.28, streak=0.08))


# ======================================================================= storm sea (flashback)
def storm_sky_draw(cx):
    g = cairo.LinearGradient(0, -300, 0, 1300)
    g.add_color_stop_rgb(0, *hexc("#1B2733")[:3])
    g.add_color_stop_rgb(0.65, *hexc("#3D4E5A")[:3])
    g.add_color_stop_rgb(0.85, *hexc("#8A7A63")[:3])
    g.add_color_stop_rgb(1, *hexc("#B48C5A")[:3])
    cx.rectangle(-400, -400, W + 800, 1800)
    cx.set_source(g)
    cx.fill()
    rng = random.Random(12)
    for i in range(46):
        x = rng.uniform(-400, W + 400)
        y = rng.uniform(-300, 950)
        r = rng.uniform(80, 220)
        dark = 0.12 + 0.2 * (y + 300) / 1250
        ellipse(cx, x, y, r * 1.8, r * 0.7)
        src(cx, (dark * 0.8, dark * 0.9, dark, 0.55))
        cx.fill()
    # distant coastline (Nigeria) under the dawn glow
    pts = [(-400, 1300)]
    for x in range(-400, W + 420, 40):
        pts.append((x, 1120 - 18 * math.sin(x * 0.01) - (30 if 150 < x < 520 else 0) - rng.uniform(0, 8)))
    pts.append((W + 400, 1300))
    poly(cx, pts)
    src(cx, hexc("#2C3A35"))
    cx.fill()


def storm_sky_plate():
    def tex(h, w):
        n = look.value_noise(w, h, 300, seed=5, octaves=5)
        return np.clip(0.8 + 0.45 * (n - 0.5), 0.5, 1.3)
    return plate("storm_sky", -400, -400, W + 800, 1800, storm_sky_draw, tex=tex)


def wave_layer(cx, t, y, amp, k, speed, col, foam=True, seed=0, x0=-500, x1=W + 500, swell=None):
    pts = []
    for x in range(int(x0), int(x1) + 30, 30):
        yy = y + math.sin(x * k + t * speed + seed) * amp + math.sin(x * k * 2.7 - t * speed * 1.3 + seed) * amp * 0.35
        if swell:
            sx, sh, sw = swell
            yy -= sh * math.exp(-((x - sx) / sw) ** 2)
        pts.append((x, yy))
    poly(cx, pts + [(x1, 3000), (x0, 3000)])
    src(cx, hexc(col) if isinstance(col, str) else col)
    cx.fill()
    if foam:
        cx.move_to(*pts[0])
        for p in pts[1:]:
            cx.line_to(*p)
        cx.set_source_rgba(0.85, 0.9, 0.92, 0.55)
        cx.set_line_width(6)
        cx.stroke()
    return pts


def tug(cx, x, y, s=1.0, rot=0.0, lights=1.0, t=0.0):
    """Jascon-4 style ocean tug, side view (bow right). Origin at waterline middle."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    # hull
    cx.move_to(-330, -70)
    cx.line_to(300, -70)
    cx.curve_to(370, -70, 390, -40, 380, 0)
    cx.curve_to(360, 60, 300, 100, 200, 110)
    cx.line_to(-280, 110)
    cx.curve_to(-330, 100, -340, 40, -330, -70)
    cx.close_path()
    src(cx, hexc("#1F2326"))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(6)
    cx.stroke()
    cx.save()
    cx.move_to(-330, -70)
    cx.line_to(300, -70)
    cx.curve_to(370, -70, 390, -40, 380, 0)
    cx.curve_to(360, 60, 300, 100, 200, 110)
    cx.line_to(-280, 110)
    cx.curve_to(-330, 100, -340, 40, -330, -70)
    cx.clip()
    cx.rectangle(-400, 20, 800, 120)
    src(cx, hexc("#8E2E24"))
    cx.fill()
    line(cx, [(-400, 18), (400, 18)], hexc("#D9D2C0"), 8)
    cx.restore()
    text(cx, "JASCON 4", 190, -20, 34, hexc("#EDE8DA"))
    for k in range(-280, 300, 80):
        ellipse(cx, k, -66, 24, 16)
        fs(cx, hexc("#121212"), OUTLINE, 3)
    # bulwark + deck house + wheelhouse
    rrect(cx, -300, -110, 600, 44, 6)
    fs(cx, hexc("#D8D2C2"), OUTLINE, 5)
    rrect(cx, -120, -240, 300, 134, 8)
    fs(cx, hexc("#E6E1D3"), OUTLINE, 5)
    rrect(cx, -60, -330, 230, 96, 8)
    fs(cx, hexc("#F0ECE0"), OUTLINE, 5)
    for wx in range(-40, 160, 52):
        rrect(cx, wx, -310, 40, 36, 5)
        fs(cx, (1, 0.85, 0.5, 0.3 + 0.7 * lights), OUTLINE, 3)
    for wx in range(-90, 150, 70):
        circle(cx, wx, -175, 13)
        fs(cx, (1, 0.85, 0.5, 0.25 + 0.6 * lights), OUTLINE, 3)
    # mast + funnel + towing gear
    line(cx, [(60, -330), (60, -470)], OUTLINE, 12)
    line(cx, [(60, -330), (60, -470)], hexc("#D8D2C2"), 7)
    line(cx, [(20, -430), (100, -430)], OUTLINE, 8)
    circle(cx, 60, -478, 8)
    fs(cx, (1, 0.95, 0.7, lights), OUTLINE, 3)
    rrect(cx, -220, -230, 70, 120, 10)
    fs(cx, hexc("#C23A2C"), OUTLINE, 5)
    rrect(cx, -220, -230, 70, 24, 8)
    fs(cx, hexc("#222222"), OUTLINE, 4)
    rrect(cx, -310, -150, 60, 42, 10)
    fs(cx, hexc("#3a3f44"), OUTLINE, 4)
    cx.restore()


def rain(cx, t, alpha=0.4, n=160, seed=9, wind=0.28):
    rng = random.Random(seed)
    cx.set_line_width(2.4)
    for i in range(n):
        x0 = rng.uniform(-300, W + 300)
        sp = rng.uniform(1600, 2400)
        y = (rng.uniform(0, H + 400) + t * sp) % (H + 400) - 200
        x = x0 + (y + 200) * wind
        cx.move_to(x, y)
        cx.line_to(x + 34 * wind * 2, y + 70)
        cx.set_source_rgba(0.8, 0.85, 0.9, alpha * rng.uniform(0.4, 1))
        cx.stroke()

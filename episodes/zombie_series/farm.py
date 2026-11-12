"""The farm: the series' single location. Exterior + farmhouse interiors + props.

World conventions
  exterior: horizon at y=HZ, farmhouse front x 0..620 (porch faces camera), red barn x 1500..2050,
            well at x=1060, garden x 700..1000, foreground fence y=FENCE_Y.
  interior: kitchen world x 0..2400 (window+table left, sink centre-right, fridge, back door far right),
            floor line y=FLOOR.
Keep these fixed between episodes so the farm stays recognisable.
"""
import math
import random

import cairo

from cinecode.core import (H, OUTLINE, W, circle, clamp, ellipse, fs, hexc, lerp, line, mix, poly, rrect,
                           shade, smooth, src, vgrad)

HZ = 980          # exterior horizon
YARD = 1180       # where the house / yard sit
FENCE_Y = 1430    # foreground fence base
FLOOR = 1240      # interior floor line

C = {
    "sky_top": "#7F93A6", "sky_mid": "#B9B9B0", "sky_hz": "#E6C49B", "sun": "#F7E6C0",
    "far": "#6F7D6A", "far2": "#5F6E5C", "field_a": "#A9A26C", "field_b": "#8F965E", "grass": "#7C8B57",
    "grass_dk": "#66764A", "dirt": "#A98F6A", "barn": "#9B3F35", "barn_dk": "#7A2F28", "trim": "#E9E3D4",
    "roof": "#56595F", "house": "#E2DBCB", "house_sh": "#C4BBA6", "wood": "#8A6A4B", "wood_dk": "#6B4F37",
    "fence": "#866548", "stone": "#9A968C",
}


def col(k, a=1.0):
    return hexc(C[k], a)


def _lay(cx, cam, par, fn, *a, **kw):
    cx.save()
    cam.apply(cx, par)
    fn(cx, *a, **kw)
    cx.restore()


# =========================================================== EXTERIOR
def sky(cx, t, dark=0.0, sun_y=760, sun_x=1900):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *mix(col("sky_top"), hexc("#2B3340"), dark))
    g.add_color_stop_rgba(0.42, *mix(col("sky_mid"), hexc("#3C4350"), dark))
    g.add_color_stop_rgba(0.62, *mix(col("sky_hz"), hexc("#55505A"), dark))
    g.add_color_stop_rgba(1, *mix(col("sky_hz"), hexc("#55505A"), dark))
    cx.set_source(g)
    cx.paint()


def _sun(cx, x, y, a=1.0):
    g = cairo.RadialGradient(x, y, 10, x, y, 420)
    g.add_color_stop_rgba(0, 1, 0.95, 0.82, 0.55 * a)
    g.add_color_stop_rgba(1, 1, 0.92, 0.75, 0)
    cx.set_source(g)
    circle(cx, x, y, 420)
    cx.fill()
    circle(cx, x, y, 58)
    src(cx, col("sun"), 0.95 * a)
    cx.fill()


def _cloud_strip(cx, t, y, seed, a=0.45):
    r = random.Random(seed)
    for k in range(9):
        x = -1800 + k * 700 + r.random() * 200 + t * 6
        for j in range(4):
            ellipse(cx, x + j * 70, y + r.random() * 18, 110 + r.random() * 60, 22 + r.random() * 10)
        src(cx, hexc("#EDE6DA"), a)
        cx.fill()


def _treeline(cx, y, x0, x1, seed, c, h=70, bump=60):
    r = random.Random(seed)
    cx.move_to(x0, y + 40)
    x = x0
    while x < x1:
        w = 50 + r.random() * bump
        hh = h * (0.6 + r.random() * 0.8)
        cx.curve_to(x + w * 0.1, y - hh, x + w * 0.9, y - hh, x + w, y - hh * 0.3)
        x += w
    cx.line_to(x1, y + 40)
    cx.close_path()
    src(cx, c)
    cx.fill()


def tree(cx, x, y, s=1.0, c="#5A6B4A", seed=1):
    r = random.Random(seed)
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-18, 0)
    cx.line_to(-12, -150)
    cx.line_to(-40, -210)
    cx.line_to(-6, -170)
    cx.line_to(4, -240)
    cx.line_to(14, -160)
    cx.line_to(46, -200)
    cx.line_to(16, -140)
    cx.line_to(20, 0)
    cx.close_path()
    fs(cx, hexc("#5A4535"), OUTLINE, 5)
    for k in range(7):
        a = k / 7 * math.pi * 2
        circle(cx, math.cos(a) * 95 + r.random() * 20, -270 + math.sin(a) * 70, 70 + r.random() * 20)
    circle(cx, 0, -280, 105)
    fs(cx, hexc(c), OUTLINE, 5)
    for k in range(5):
        circle(cx, -40 + r.random() * 90, -320 + r.random() * 80, 30)
    src(cx, shade(hexc(c), 0.12), 0.7)
    cx.fill()
    cx.restore()


def barn(cx, x=1500, y=1100, w=560, light=1.0):
    h = 300
    rx0, rx1 = x - 20, x + w + 20
    # gambrel roof
    roof = [(rx0, y - h), (x + w * 0.12, y - h - 150), (x + w / 2, y - h - 230), (x + w * 0.88, y - h - 150),
            (rx1, y - h)]
    cx.rectangle(x, y - h, w, h)
    fs(cx, col("barn"), OUTLINE, 6)
    for k in range(1, 12):
        line(cx, [(x + k * w / 12, y - h + 6), (x + k * w / 12, y - 4)], col("barn_dk"), 3)
    poly(cx, roof)
    fs(cx, col("barn"), OUTLINE, 6)
    poly(cx, [(rx0 - 10, y - h + 6), (x + w * 0.12, y - h - 152), (x + w / 2, y - h - 238),
              (x + w * 0.88, y - h - 152), (rx1 + 10, y - h + 6), (rx1 + 10, y - h - 8), (x + w * 0.88, y - h - 168),
              (x + w / 2, y - h - 254), (x + w * 0.12, y - h - 168), (rx0 - 10, y - h - 8)])
    fs(cx, col("roof"), OUTLINE, 5)
    # hay loft
    lx, ly = x + w / 2, y - h - 90
    cx.rectangle(lx - 50, ly - 50, 100, 100)
    fs(cx, col("barn_dk"), OUTLINE, 5)
    for a, b in [((lx - 50, ly - 50), (lx + 50, ly + 50)), ((lx + 50, ly - 50), (lx - 50, ly + 50))]:
        line(cx, [a, b], col("trim"), 8)
    cx.rectangle(lx - 50, ly - 50, 100, 100)
    fs(cx, None, col("trim"), 9)
    # doors
    dw, dh = 230, 210
    dx = x + w / 2 - dw / 2
    cx.rectangle(dx, y - dh, dw, dh)
    fs(cx, col("barn_dk"), OUTLINE, 5)
    for k in range(2):
        x0 = dx + k * dw / 2
        line(cx, [(x0 + 6, y - dh + 6), (x0 + dw / 2 - 6, y - 6)], col("trim"), 8)
        line(cx, [(x0 + dw / 2 - 6, y - dh + 6), (x0 + 6, y - 6)], col("trim"), 8)
        cx.rectangle(x0, y - dh, dw / 2, dh)
        fs(cx, None, col("trim"), 9)
    cx.rectangle(x, y - h, w, h)
    fs(cx, None, col("trim"), 8)
    cx.rectangle(x, y - h, w, h)
    fs(cx, None, OUTLINE, 4)


def silo(cx, x=2100, y=1100, w=150, h=520):
    rrect(cx, x, y - h, w, h, 8)
    fs(cx, hexc("#A7A39A"), OUTLINE, 6)
    for k in range(1, 9):
        line(cx, [(x + 4, y - h + k * h / 9), (x + w - 4, y - h + k * h / 9)], hexc("#8C887F"), 3)
    cx.move_to(x - 4, y - h + 4)
    cx.curve_to(x, y - h - 100, x + w, y - h - 100, x + w + 4, y - h + 4)
    cx.close_path()
    fs(cx, col("roof"), OUTLINE, 6)


def farmhouse(cx, x=0, y=YARD, w=640, light=1.0, win_glow=0.0, curtains=0.0):
    h = 420
    # roof (gable)
    poly(cx, [(x - 50, y - h), (x + w / 2, y - h - 250), (x + w + 50, y - h)])
    fs(cx, col("roof"), OUTLINE, 6)
    # walls with clapboard
    cx.rectangle(x, y - h, w, h)
    fs(cx, col("house"), OUTLINE, 6)
    cx.save()
    cx.rectangle(x, y - h, w, h)
    cx.clip()
    for k in range(int(h / 22) + 1):
        line(cx, [(x, y - h + k * 22), (x + w, y - h + k * 22)], col("house_sh"), 2.5)
    cx.restore()
    # gable siding + attic window
    poly(cx, [(x + 10, y - h), (x + w / 2, y - h - 220), (x + w - 10, y - h)])
    fs(cx, col("house"), OUTLINE, 5)
    circle(cx, x + w / 2, y - h - 90, 40)
    fs(cx, hexc("#3A4250"), OUTLINE, 5)
    line(cx, [(x + w / 2 - 40, y - h - 90), (x + w / 2 + 40, y - h - 90)], col("trim"), 5)
    line(cx, [(x + w / 2, y - h - 130), (x + w / 2, y - h - 50)], col("trim"), 5)
    # windows
    for wx in (x + 70, x + w - 210):
        window_ext(cx, wx, y - 330, 140, 170, glow=win_glow, curtains=curtains)
    # door
    dx = x + w / 2 - 55
    cx.rectangle(dx, y - 240, 110, 240)
    fs(cx, hexc("#6E4D3A"), OUTLINE, 6)
    rrect(cx, dx + 18, y - 220, 74, 70, 6)
    fs(cx, hexc("#3A4250"), OUTLINE, 4)
    circle(cx, dx + 92, y - 120, 7)
    fs(cx, hexc("#D9B44A"), OUTLINE, 3)
    # porch roof + posts + steps
    poly(cx, [(x - 30, y - 270), (x + w + 30, y - 270), (x + w + 10, y - 300), (x - 10, y - 300)])
    fs(cx, col("roof"), OUTLINE, 5)
    for px in (x - 10, x + w * 0.33, x + w * 0.67, x + w + 2):
        cx.rectangle(px - 6, y - 270, 14, 250)
        fs(cx, col("trim"), OUTLINE, 4)
    cx.rectangle(x - 30, y - 24, w + 60, 24)
    fs(cx, col("wood"), OUTLINE, 5)
    for k in range(3):
        cx.rectangle(dx - 30 - k * 10, y + k * 18, 170 + k * 20, 18)
        fs(cx, col("wood"), OUTLINE, 4)
    # railing
    for side in (0, 1):
        x0 = x - 10 if side == 0 else dx + 150
        x1 = dx - 40 if side == 0 else x + w + 2
        line(cx, [(x0, y - 110), (x1, y - 110)], col("trim"), 8)
        for k in range(int((x1 - x0) / 28)):
            line(cx, [(x0 + 14 + k * 28, y - 106), (x0 + 14 + k * 28, y - 26)], col("trim"), 5)


def window_ext(cx, x, y, w, h, glow=0.0, curtains=0.0, dark="#38404D"):
    cx.rectangle(x - 14, y - 14, w + 28, h + 28)
    fs(cx, col("trim"), OUTLINE, 5)
    cx.rectangle(x, y, w, h)
    fs(cx, mix(hexc(dark), hexc("#F2C77A"), glow), OUTLINE, 4)
    if curtains > 0:
        for side in (0, 1):
            cw = w / 2 * clamp(curtains)
            cx.rectangle(x + (0 if side == 0 else w - cw), y, cw, h)
            fs(cx, hexc("#B65C4A"), OUTLINE, 3)
    line(cx, [(x + w / 2, y), (x + w / 2, y + h)], col("trim"), 7)
    line(cx, [(x, y + h / 2), (x + w, y + h / 2)], col("trim"), 7)
    # shutters
    for sx in (x - 46, x + w + 14):
        cx.rectangle(sx, y - 10, 32, h + 20)
        fs(cx, hexc("#4E6B5A"), OUTLINE, 4)
        for k in range(6):
            line(cx, [(sx + 6, y + 6 + k * h / 6), (sx + 26, y + 6 + k * h / 6)], hexc("#3D5747"), 3)


def well(cx, x=1060, y=1330, s=1.0, bucket=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # posts + roof
    for px in (-78, 70):
        cx.rectangle(px, -250, 14, 200)
        fs(cx, col("wood"), OUTLINE, 4)
    poly(cx, [(-120, -240), (0, -320), (120, -240), (110, -228), (0, -300), (-110, -228)])
    fs(cx, col("barn_dk"), OUTLINE, 5)
    poly(cx, [(-118, -238), (0, -318), (118, -238)])
    fs(cx, col("barn"), OUTLINE, 5)
    line(cx, [(-70, -200), (76, -200)], col("wood_dk"), 10)
    line(cx, [(0, -200), (0, -140 + 30 * bucket)], OUTLINE, 3)
    rrect(cx, -16, -140 + 30 * bucket, 32, 30, 4)
    fs(cx, hexc("#7C7F86"), OUTLINE, 3.5)
    # stone ring
    ellipse(cx, 0, -60, 100, 24)
    fs(cx, hexc("#2A2A30"), OUTLINE, 5)
    cx.move_to(-100, -60)
    cx.line_to(-100, 10)
    cx.curve_to(-100, 40, 100, 40, 100, 10)
    cx.line_to(100, -60)
    cx.curve_to(100, -36, -100, -36, -100, -60)
    cx.close_path()
    fs(cx, col("stone"), OUTLINE, 5)
    r = random.Random(5)
    for row in range(3):
        for k in range(6):
            xx = -88 + k * 34 + (17 if row % 2 else 0)
            if xx > 86:
                continue
            rrect(cx, xx, -40 + row * 22, 28, 16, 5)
            fs(cx, shade(col("stone"), -0.1 + r.random() * 0.15), OUTLINE, 2.5)
    cx.restore()


def garden(cx, x=690, y=1250, w=330, rows=3, t=0.0):
    r = random.Random(3)
    for k in range(rows):
        yy = y + k * 34
        ellipse(cx, x + w / 2, yy + 6, w / 2 + 10, 12)
        src(cx, hexc("#7A5E44"))
        cx.fill()
        for j in range(7):
            px = x + 14 + j * (w - 28) / 6
            sway = math.sin(t * 1.5 + j + k) * 2
            for a in (-0.7, 0, 0.7):
                ellipse(cx, px + math.sin(a) * 12 + sway, yy - 12, 9, 17, a)
            fs(cx, hexc(["#6E9A4A", "#5F8C42", "#7FA855"][j % 3]), OUTLINE, 3)
            if k == 1 and j % 2 == 0:
                circle(cx, px + 6, yy - 6, 7)
                fs(cx, hexc("#C8473A"), OUTLINE, 2.5)
    # stakes
    for j in range(4):
        line(cx, [(x + 30 + j * 90, y - 40), (x + 30 + j * 90, y + 70)], col("wood_dk"), 4)


def fence(cx, y, x0, x1, step=170, h=110, c=None, lw=5):
    c = c or col("fence")
    for k in range(int((x1 - x0) / step) + 1):
        px = x0 + k * step
        rrect(cx, px - 9, y - h - 10, 18, h + 10, 3)
        fs(cx, c, OUTLINE, lw)
    for yy in (y - h + 18, y - h * 0.45):
        rrect(cx, x0, yy - 7, x1 - x0, 14, 4)
        fs(cx, shade(c, 0.08), OUTLINE, lw - 1)


def mailbox(cx, x, y, flag=1.0):
    line(cx, [(x, y), (x, y - 120)], col("wood_dk"), 12)
    rrect(cx, x - 48, y - 168, 96, 52, 22)
    fs(cx, hexc("#5C6F86"), OUTLINE, 5)
    line(cx, [(x + 40, y - 150), (x + 40 + 30 * math.sin(flag), y - 150 - 34 * math.cos(flag))],
         hexc("#D63A2E"), 7)


def fields(cx, x0=-2500, x1=4500, vx=1100):
    # ground base
    cx.rectangle(x0, HZ, x1 - x0, 3000)
    src(cx, col("grass"))
    cx.fill()
    # crop field band with converging rows
    cx.save()
    cx.rectangle(x0, HZ, x1 - x0, YARD - 50 - HZ)
    cx.clip()
    cx.rectangle(x0, HZ, x1 - x0, 400)
    cx.set_source(vgrad(cx, 0, HZ, 0, YARD, [(0, col("field_b")), (1, col("field_a"))]))
    cx.fill()
    for k in range(-60, 60):
        line(cx, [(vx + k * 18, HZ), (vx + k * 120, YARD + 200)], hexc("#7E7E4E", 0.55), 3)
    cx.restore()
    # yard
    cx.rectangle(x0, YARD - 50, x1 - x0, 3000)
    cx.set_source(vgrad(cx, 0, YARD - 50, 0, 1900, [(0, col("grass")), (1, col("grass_dk"))]))
    cx.fill()
    r = random.Random(9)
    for k in range(160):
        gx = x0 + r.random() * (x1 - x0)
        gy = YARD - 30 + r.random() * 700
        line(cx, [(gx, gy), (gx - 4, gy - 12)], hexc("#5F6F44", 0.7), 3)
    # dirt path to the porch and to the barn
    cx.move_to(250, YARD + 10)
    cx.curve_to(260, 1350, 500, 1600, 520, 2400)
    cx.line_to(820, 2400)
    cx.curve_to(760, 1600, 420, 1350, 400, YARD + 10)
    cx.close_path()
    src(cx, col("dirt"))
    cx.fill()
    cx.move_to(420, 1300)
    cx.curve_to(900, 1240, 1400, 1130, 1700, 1100)
    cx.line_to(1830, 1100)
    cx.curve_to(1450, 1160, 950, 1300, 520, 1360)
    cx.close_path()
    src(cx, col("dirt"))
    cx.fill()


def farm_exterior(cx, cam, t, dark=0.0, fog=0.55, sun=True, before_fg=None, house=True, curtains=0.0,
                  win_glow=0.0, fence_fg=True, sun_pos=(1900, 760)):
    """Full farm wide shot. `before_fg(cx)` draws characters (world coords) before the foreground fence."""
    sky(cx, t, dark)
    _lay(cx, cam, 0.08, lambda c: _sun(c, *sun_pos, 0.0 if not sun else 1.0 - dark * 0.8))
    _lay(cx, cam, 0.12, lambda c: (_cloud_strip(c, t, 330, 1), _cloud_strip(c, t * 0.7, 520, 2, 0.3)))
    _lay(cx, cam, 0.3, lambda c: _treeline(c, HZ - 10, -3000, 5000, 4, col("far"), 60, 90))
    _lay(cx, cam, 0.55, lambda c: _treeline(c, HZ + 10, -3000, 5000, 6, col("far2"), 90, 70))

    def world(c):
        fields(c)
        # fog band
        c.rectangle(-3000, HZ - 160, 8000, 320)
        c.set_source(vgrad(c, 0, HZ - 160, 0, HZ + 160, [(0, (1, 1, 1, 0)), (0.5, (0.93, 0.9, 0.86, fog)),
                                                         (1, (1, 1, 1, 0))]))
        c.fill()
        fence(c, YARD - 60, -1800, 3800, 150, 70, lw=3.5)
        silo(c)
        barn(c)
        tree(c, -330, YARD + 20, 1.25, seed=2)
        tree(c, 2500, 1110, 1.0, "#55684A", seed=5)
        if house:
            farmhouse(c, curtains=curtains, win_glow=win_glow)
        garden(c, t=t)
        well(c)
        mailbox(c, 1480, 1460)
        if before_fg:
            before_fg(c)
        if fence_fg:
            fence(c, FENCE_Y + 140, -1800, 3800, 200, 150)
    _lay(cx, cam, 1.0, world)
    if dark > 0:
        cx.rectangle(0, 0, W, H)
        src(cx, (0.08, 0.1, 0.16, 0.45 * dark))
        cx.fill()


# =========================================================== INTERIOR
WALL = "#9EA98D"
WALL_DK = "#8A967A"


def _wallpaper(cx, x0, x1, y0, y1, c=WALL):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, hexc(c))
    cx.fill()
    for k in range(int((x1 - x0) / 60) + 1):
        x = x0 + k * 60
        cx.rectangle(x, y0, 14, y1 - y0)
    src(cx, hexc(WALL_DK), 0.35)
    cx.fill()
    for k in range(int((x1 - x0) / 60) + 1):
        for j in range(int((y1 - y0) / 120) + 1):
            circle(cx, x0 + k * 60 + 37, y0 + j * 120 + (60 if k % 2 else 0), 4)
    src(cx, hexc("#C9C8A8"), 0.35)
    cx.fill()


def _floor(cx, x0, x1, y0=FLOOR, y1=2400, vx=1200, c="#7B5B41"):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, hexc(c))
    cx.fill()
    for k in range(-40, 60):
        line(cx, [(vx + k * 40, y0), (vx + k * 140, y1)], hexc("#5E4430", 0.6), 3)
    for k, yy in enumerate([y0 + 60, y0 + 150, y0 + 270, y0 + 430, y0 + 640]):
        line(cx, [(x0, yy), (x1, yy)], hexc("#6A4D36", 0.5), 2)
    line(cx, [(x0, y0), (x1, y0)], OUTLINE, 5)


def _wainscot(cx, x0, x1, top=980, y1=FLOOR):
    cx.rectangle(x0, top, x1 - x0, y1 - top)
    fs(cx, hexc("#8C6A4C"), None, 0)
    for k in range(int((x1 - x0) / 120) + 1):
        rrect(cx, x0 + k * 120 + 14, top + 30, 92, y1 - top - 60, 6)
        fs(cx, None, hexc("#6E523A"), 4)
    line(cx, [(x0, top), (x1, top)], hexc("#5E4430"), 10)
    line(cx, [(x0, top), (x1, top)], OUTLINE, 3)


def interior_window(cx, x, y, w, h, view=None, curtains=0.0, light=1.0, t=0.0, open_=0.0, sill=True):
    """Window seen from inside. view(cx, x, y, w, h) draws the outside into the glass rect."""
    cx.rectangle(x - 22, y - 22, w + 44, h + 44)
    fs(cx, hexc("#E9E3D4"), OUTLINE, 5)
    cx.save()
    cx.rectangle(x, y, w, h)
    cx.clip()
    if view:
        view(cx, x, y, w, h)
    else:
        cx.rectangle(x, y, w, h)
        src(cx, hexc("#C9D2D8"))
        cx.fill()
    # glass sheen
    cx.move_to(x + w * 0.1, y + h)
    cx.line_to(x + w * 0.35, y)
    cx.line_to(x + w * 0.5, y)
    cx.line_to(x + w * 0.25, y + h)
    cx.close_path()
    src(cx, (1, 1, 1, 0.10))
    cx.fill()
    cx.restore()
    # sash (open_ lifts the lower sash)
    lift = h * 0.45 * open_
    line(cx, [(x, y + h / 2 - lift), (x + w, y + h / 2 - lift)], hexc("#E9E3D4"), 14)
    line(cx, [(x + w / 2, y), (x + w / 2, y + h)], hexc("#E9E3D4"), 10)
    cx.rectangle(x, y, w, h)
    fs(cx, None, OUTLINE, 4)
    if sill:
        rrect(cx, x - 40, y + h + 18, w + 80, 26, 6)
        fs(cx, hexc("#E9E3D4"), OUTLINE, 5)
    # curtains: 0 open .. 1 closed
    cur = clamp(curtains)
    rod_y = y - 50
    line(cx, [(x - 70, rod_y), (x + w + 70, rod_y)], hexc("#5E4430"), 9)
    for side in (-1, 1):
        cw = 70 + (w / 2 - 40) * cur
        x0 = x - 60 if side < 0 else x + w + 60 - cw
        cx.save()
        cx.translate(x0 if side < 0 else x0 + cw, rod_y)
        cx.scale(side * -1 if side > 0 else 1, 1)
        cx.move_to(0, 0)
        cx.line_to(cw, 0)
        sway = math.sin(t * 2 + side) * 6 * (1 - cur)
        cx.curve_to(cw + 10 + sway, h * 0.5, cw - 20 * (1 - cur) + sway, h * 0.8, cw - 30 * (1 - cur), h + 70)
        cx.line_to(0, h + 70)
        cx.close_path()
        fs(cx, hexc("#B65C4A"), OUTLINE, 5)
        for k in range(1, 4):
            line(cx, [(cw * k / 4, 8), (cw * k / 4 - 8 * (1 - cur), h + 60)], hexc("#8E4436"), 3)
        cx.restore()


def pendant_lamp(cx, x, y, on=1.0, t=0.0, swing=0.0):
    a = swing * math.sin(t * 3)
    cx.save()
    cx.translate(x, 0)
    cx.rotate(a)
    line(cx, [(0, 0), (0, y)], OUTLINE, 4)
    if on > 0:
        g = cairo.RadialGradient(0, y + 40, 10, 0, y + 40, 700)
        g.add_color_stop_rgba(0, 1, 0.86, 0.55, 0.45 * on)
        g.add_color_stop_rgba(1, 1, 0.86, 0.55, 0)
        cx.set_source(g)
        circle(cx, 0, y + 40, 700)
        cx.fill()
    circle(cx, 0, y + 46, 22)
    fs(cx, mix(hexc("#8D8A80"), hexc("#FFF2C4"), on), OUTLINE, 3)
    cx.move_to(-70, y + 50)
    cx.line_to(-24, y)
    cx.line_to(24, y)
    cx.line_to(70, y + 50)
    cx.close_path()
    fs(cx, hexc("#3E5A4A"), OUTLINE, 5)
    cx.restore()


def wall_clock(cx, x, y, t, r=48):
    circle(cx, x, y, r)
    fs(cx, hexc("#F3EEE2"), OUTLINE, 6)
    for k in range(12):
        a = k / 12 * math.tau
        line(cx, [(x + math.cos(a) * r * 0.78, y + math.sin(a) * r * 0.78),
                  (x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9)], OUTLINE, 3)
    ah = -math.pi / 2 + 6.5 / 12 * math.tau
    am = -math.pi / 2 + (t / 60 + 0.25) * math.tau
    asec = -math.pi / 2 + math.floor(t) / 60 * math.tau
    line(cx, [(x, y), (x + math.cos(ah) * r * 0.45, y + math.sin(ah) * r * 0.45)], OUTLINE, 6)
    line(cx, [(x, y), (x + math.cos(am) * r * 0.7, y + math.sin(am) * r * 0.7)], OUTLINE, 4)
    line(cx, [(x, y), (x + math.cos(asec) * r * 0.75, y + math.sin(asec) * r * 0.75)], hexc("#C0392B"), 2)


def counter_sink(cx, x=1150, w=620, top=1060, faucet_x=None):
    faucet_x = faucet_x or x + w * 0.45
    # upper cabinets
    for k in range(3):
        rrect(cx, x + k * w / 3 + 6, 300, w / 3 - 12, 330, 8)
        fs(cx, hexc("#D9CFB8"), OUTLINE, 5)
        rrect(cx, x + k * w / 3 + 26, 320, w / 3 - 52, 290, 6)
        fs(cx, None, hexc("#B7AC93"), 4)
        circle(cx, x + k * w / 3 + w / 6, 600, 6)
        fs(cx, hexc("#7E6A4A"), OUTLINE, 2.5)
    # backsplash tiles
    cx.rectangle(x, 640, w, top - 640)
    src(cx, hexc("#E7E2D3"))
    cx.fill()
    for k in range(int(w / 50) + 1):
        line(cx, [(x + k * 50, 640), (x + k * 50, top)], hexc("#C9C2AE"), 2)
    for k in range(int((top - 640) / 50) + 1):
        line(cx, [(x, 640 + k * 50), (x + w, 640 + k * 50)], hexc("#C9C2AE"), 2)
    # base cabinets + counter
    cx.rectangle(x, top, w, FLOOR - top)
    fs(cx, hexc("#C9BEA4"), OUTLINE, 5)
    for k in range(3):
        rrect(cx, x + k * w / 3 + 14, top + 50, w / 3 - 28, FLOOR - top - 70, 6)
        fs(cx, None, hexc("#A79C82"), 4)
    rrect(cx, x - 16, top - 26, w + 32, 34, 6)
    fs(cx, hexc("#E9E3D4"), OUTLINE, 5)
    # sink basin
    rrect(cx, faucet_x - 110, top - 18, 220, 22, 6)
    fs(cx, hexc("#B8BCC2"), OUTLINE, 4)
    return faucet_x


def faucet(cx, x, y, s=1.0, handle=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, -22, -30, 44, 30, 6)
    fs(cx, hexc("#C7CCD2"), OUTLINE, 4)
    cx.move_to(-10, -28)
    cx.line_to(-10, -110)
    cx.curve_to(-10, -150, 70, -150, 70, -110)
    cx.line_to(70, -84)
    cx.line_to(50, -84)
    cx.line_to(50, -108)
    cx.curve_to(50, -126, 10, -126, 10, -108)
    cx.line_to(10, -28)
    cx.close_path()
    fs(cx, hexc("#C7CCD2"), OUTLINE, 4)
    cx.save()
    cx.translate(0, -60)
    cx.rotate(-0.9 * handle)
    rrect(cx, -6, -60, 12, 60, 5)
    fs(cx, hexc("#D9DDE2"), OUTLINE, 3.5)
    circle(cx, 0, -62, 10)
    fs(cx, hexc("#E04848"), OUTLINE, 3)
    cx.restore()
    cx.restore()


def fridge(cx, x=1800, y=FLOOR, w=230, h=640, hum=0.0, t=0.0):
    rrect(cx, x, y - h, w, h, 30)
    fs(cx, hexc("#DCD6C4"), OUTLINE, 6)
    line(cx, [(x + 6, y - h * 0.62), (x + w - 6, y - h * 0.62)], OUTLINE, 4)
    rrect(cx, x + w - 34, y - h * 0.62 - 120, 14, 90, 6)
    fs(cx, hexc("#B9B3A2"), OUTLINE, 3)
    rrect(cx, x + w - 34, y - h * 0.62 + 30, 14, 110, 6)
    fs(cx, hexc("#B9B3A2"), OUTLINE, 3)
    # magnets + kid drawing
    rrect(cx, x + 40, y - h * 0.5, 80, 100, 4)
    fs(cx, hexc("#F5F1E6"), OUTLINE, 3)
    line(cx, [(x + 56, y - h * 0.5 + 70), (x + 80, y - h * 0.5 + 30), (x + 104, y - h * 0.5 + 70)], hexc("#C0392B"), 4)
    circle(cx, x + 80, y - h * 0.5 + 18, 6)
    fs(cx, hexc("#2F6FDB"), None, 0)


def back_door(cx, x=2080, y=FLOOR, w=270, h=700, open_=0.0, t=0.0, outside=None, light=1.0):
    """Door hinged on its right edge, opening INTO the kitchen (toward the camera / left)."""
    # frame
    cx.rectangle(x - 26, y - h - 26, w + 52, h + 26)
    fs(cx, hexc("#E9E3D4"), OUTLINE, 5)
    # doorway (outside)
    cx.save()
    cx.rectangle(x, y - h, w, h)
    cx.clip()
    if outside:
        outside(cx, x, y - h, w, h)
    cx.restore()
    cx.rectangle(x, y - h, w, h)
    fs(cx, None, OUTLINE, 5)
    if open_ > 0:
        # cold light spilling on the floor
        g = cairo.LinearGradient(x + w / 2, y, x - 600, y + 650)
        g.add_color_stop_rgba(0, 0.86, 0.92, 1.0, 0.55 * light * open_)
        g.add_color_stop_rgba(1, 0.86, 0.92, 1.0, 0)
        cx.set_source(g)
        cx.move_to(x, y)
        cx.line_to(x + w, y)
        cx.line_to(x + w - 200, y + 700)
        cx.line_to(x - 700 * open_, y + 700)
        cx.close_path()
        cx.fill()
    # the door leaf
    ang = open_ * 1.25
    vis = math.cos(ang)
    lw = w * vis
    skew = 60 * math.sin(ang)
    hx = x + w
    pts = [(hx, y - h), (hx - lw, y - h - skew * 0.4), (hx - lw, y + skew * 0.4), (hx, y)]
    poly(cx, pts)
    fs(cx, hexc("#7A563E"), OUTLINE, 6)
    # panels / window on the leaf (mapped)
    def P(u, v):
        top = (hx - lw * u, y - h - skew * 0.4 * u)
        bot = (hx - lw * u, y + skew * 0.4 * u)
        return (top[0], top[1] + (bot[1] - top[1]) * v)
    if lw > 20:
        poly(cx, [P(0.15, 0.08), P(0.85, 0.08), P(0.85, 0.42), P(0.15, 0.42)])
        fs(cx, hexc("#9FB2C2") if open_ == 0 else hexc("#C9D6E2"), OUTLINE, 4)
        line(cx, [P(0.5, 0.08), P(0.5, 0.42)], hexc("#7A563E"), 6)
        line(cx, [P(0.15, 0.25), P(0.85, 0.25)], hexc("#7A563E"), 6)
        poly(cx, [P(0.15, 0.52), P(0.85, 0.52), P(0.85, 0.92), P(0.15, 0.92)])
        fs(cx, None, hexc("#5E4430"), 4)
        kx, ky = P(0.9, 0.55)
        circle(cx, kx, ky, 9)
        fs(cx, hexc("#D9B44A"), OUTLINE, 3)
        # deadbolt
        bx, by = P(0.9, 0.47)
        rrect(cx, bx - 8, by - 8, 16, 16, 4)
        fs(cx, hexc("#D9B44A"), OUTLINE, 2.5)


def outside_cold(cx, x, y, w, h, t=0.0):
    """Pale cold morning seen through the open back door: fog, field edge, a fence."""
    cx.rectangle(x, y, w, h)
    cx.set_source(vgrad(cx, 0, y, 0, y + h, [(0, hexc("#C9D4DE")), (0.55, hexc("#E4E8EA")),
                                            (0.56, hexc("#9AA592")), (1, hexc("#7E8C70"))]))
    cx.fill()
    _treeline(cx, y + h * 0.55, x - 50, x + w + 50, 3, hexc("#A9B3AE"), 30, 40)
    fence(cx, y + h * 0.78, x - 80, x + w + 80, 110, 70, c=hexc("#8E8B80"), lw=3)
    # drifting fog
    for k in range(4):
        fx = x + ((t * 18 + k * 110) % (w + 200)) - 100
        ellipse(cx, fx, y + h * 0.6 + k * 30, 120, 26)
        src(cx, (1, 1, 1, 0.35))
        cx.fill()


def kitchen_table(cx, x=280, top=1440, w=560, food=1.0, t=0.0):
    # legs
    for lx in (x + 30, x + w - 50):
        rrect(cx, lx, top + 20, 22, 300, 4)
        fs(cx, hexc("#6E4F37"), OUTLINE, 4)
    rrect(cx, x - 20, top - 10, w + 40, 40, 8)
    fs(cx, hexc("#8E6A4A"), OUTLINE, 5)
    # checkered cloth
    cx.save()
    rrect(cx, x + 40, top - 14, w - 80, 26, 4)
    cx.clip()
    for k in range(20):
        cx.rectangle(x + 40 + k * 26, top - 14, 13, 26)
    src(cx, hexc("#C9574A"), 0.6)
    cx.fill()
    cx.restore()


def breakfast(cx, x, y, s=1.0, eaten=0.0, steam=1.0, t=0.0):
    """Plate of pancakes + eggs and a mug, sitting on a surface at y."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, -6, 110, 24)
    fs(cx, hexc("#F3F1EA"), OUTLINE, 4)
    n = max(0, 3 - int(eaten * 3))
    for k in range(n):
        ellipse(cx, -10, -18 - k * 14, 70, 16)
        fs(cx, hexc("#D9A456"), OUTLINE, 3.5)
    if n:
        rrect(cx, -22, -38 - (n - 1) * 14, 26, 12, 3)
        fs(cx, hexc("#F7E08A"), OUTLINE, 2.5)
        cx.move_to(-60, -20 - (n - 1) * 14)
        cx.curve_to(-40, -6 - (n - 1) * 14, 20, -6 - (n - 1) * 14, 40, -24 - (n - 1) * 14)
        src(cx, hexc("#8A4B1E"), 0.8)
        cx.set_line_width(6)
        cx.stroke()
    ellipse(cx, 70, -16, 26, 12)
    fs(cx, (1, 1, 1, 1), OUTLINE, 3)
    circle(cx, 70, -18, 9)
    fs(cx, hexc("#F2B33A"), OUTLINE, 2.5)
    # mug
    rrect(cx, 150, -84, 64, 80, 10)
    fs(cx, hexc("#2F6FDB"), OUTLINE, 4)
    cx.new_path()
    cx.arc(214, -46, 18, -math.pi / 2, math.pi / 2)
    src(cx, OUTLINE)
    cx.set_line_width(5)
    cx.stroke()
    if steam > 0:
        for k in range(3):
            ph = t * 1.4 + k * 0.6
            yy = -100 - (ph % 1.0) * 70
            a = math.sin(math.pi * (ph % 1.0)) * steam
            cx.move_to(166 + k * 16, yy)
            cx.curve_to(156 + k * 16, yy - 14, 176 + k * 16, yy - 24, 166 + k * 16, yy - 38)
            src(cx, (1, 1, 1, 0.7 * a))
            cx.set_line_width(4)
            cx.stroke()
    cx.restore()


def kitchen(cx, cam, t, power=1.0, curtains=1.0, door_open=0.0, window_view=None, dim=0.0, lamp_swing=0.0,
            table=True, food=1.0, faucet_handle=0.0, before_fg=None, door_light=1.0, window_open=0.0):
    """The farmhouse kitchen. power: lamp/fridge on. dim: extra darkness grade (0..1)."""
    cx.save()
    cam.apply(cx)
    _wallpaper(cx, -400, 2800, -200, FLOOR)
    cx.rectangle(-400, -200, 3200, 120 + 200)
    src(cx, hexc("#E4DDCB"))
    cx.fill()
    line(cx, [(-400, 120), (2800, 120)], hexc("#B9AE94"), 14)
    _wainscot(cx, -400, 1150)
    _floor(cx, -400, 2800)
    interior_window(cx, 330, 470, 440, 470, view=window_view, curtains=curtains, t=t, open_=window_open)
    wall_clock(cx, 960, 330, t)
    fx = counter_sink(cx)
    faucet(cx, fx, 1040, 1.0, faucet_handle)
    fridge(cx, hum=power, t=t)
    back_door(cx, open_=door_open, t=t, outside=lambda c, x, y, w, h: outside_cold(c, x, y, w, h, t),
              light=door_light)
    # shelf with jars
    rrect(cx, 60, 300, 220, 18, 4)
    fs(cx, hexc("#8E6A4A"), OUTLINE, 4)
    for k, c in enumerate(["#C8473A", "#E2A33A", "#6E9A4A"]):
        rrect(cx, 80 + k * 66, 236, 50, 64, 10)
        fs(cx, hexc(c), OUTLINE, 4)
        rrect(cx, 80 + k * 66, 228, 50, 16, 4)
        fs(cx, hexc("#D9CFB8"), OUTLINE, 3)
    pendant_lamp(cx, 700, 300, on=power, t=t, swing=lamp_swing)
    if table:
        kitchen_table(cx)
    if before_fg:
        before_fg(cx)
    cx.restore()
    grade_dark(cx, (1 - power) * 0.42 + dim)
    if door_open > 0:
        g = cairo.RadialGradient(*cam.to_screen(2215, 900), 20, *cam.to_screen(2215, 900), 900 * cam.zoom)
        g.add_color_stop_rgba(0, 0.85, 0.92, 1.0, 0.35 * door_open * door_light)
        g.add_color_stop_rgba(1, 0.85, 0.92, 1.0, 0)
        cx.set_source(g)
        cx.paint()


def grade_dark(cx, a, c=(0.06, 0.08, 0.14)):
    if a <= 0:
        return
    cx.rectangle(0, 0, W, H)
    src(cx, (c[0], c[1], c[2], min(0.92, a)))
    cx.fill()


def bedroom(cx, cam, t, light=0.6):
    cx.save()
    cam.apply(cx)
    _wallpaper(cx, -400, 1600, -200, FLOOR, c="#A9A2B4")
    _floor(cx, -400, 1600, vx=540, c="#80604A")
    interior_window(cx, 620, 360, 330, 420, view=lambda c, x, y, w, h: _dawn_view(c, x, y, w, h, t),
                    curtains=0.25, t=t)
    # bed
    rrect(cx, 40, 920, 50, 420, 10)
    fs(cx, hexc("#6E4F37"), OUTLINE, 5)
    rrect(cx, 40, 1180, 760, 120, 14)
    fs(cx, hexc("#6E4F37"), OUTLINE, 5)
    rrect(cx, 80, 1110, 700, 90, 20)
    fs(cx, hexc("#F1ECE0"), OUTLINE, 5)
    # nightstand + alarm clock
    rrect(cx, 830, 1080, 170, 220, 8)
    fs(cx, hexc("#8E6A4A"), OUTLINE, 5)
    rrect(cx, 870, 1010, 90, 70, 14)
    fs(cx, hexc("#C8473A"), OUTLINE, 4)
    rrect(cx, 884, 1024, 62, 34, 6)
    fs(cx, hexc("#1E1F26"), None, 0)
    from cinecode.core import text as _t
    _t(cx, "6:47", 915, 1050, 24, hexc("#7CF27A"))
    cx.restore()


def quilt(cx, cam, x0=110, y=1110, w=680, h=150, lift=0.0, seed=4):
    cx.save()
    cam.apply(cx)
    r = random.Random(seed)
    pal = ["#C9574A", "#E2B04A", "#5E8A9E", "#7FA06A", "#D98B6A", "#EFE6D0"]
    cx.save()
    rrect(cx, x0, y - lift, w, h, 24)
    cx.clip()
    for i in range(10):
        for j in range(3):
            cx.rectangle(x0 + i * 70, y - lift + j * 52, 70, 52)
            src(cx, hexc(r.choice(pal)))
            cx.fill()
    cx.restore()
    rrect(cx, x0, y - lift, w, h, 24)
    fs(cx, None, OUTLINE, 5)
    cx.restore()


def _dawn_view(cx, x, y, w, h, t):
    cx.rectangle(x, y, w, h)
    cx.set_source(vgrad(cx, 0, y, 0, y + h, [(0, col("sky_top")), (0.7, col("sky_hz")), (0.71, col("far2")),
                                            (1, col("grass"))]))
    cx.fill()
    barn(cx, x + w * 0.45, y + h * 0.84, 160)


def hallway(cx, cam, t, light=0.25, door_glow=0.0):
    """One-point-perspective dark hallway (vanishing at 540, 900)."""
    cx.save()
    cam.apply(cx)
    vx, vy = 540, 900
    ex0, ey0, ex1, ey1 = 400, 640, 680, 1080   # far end opening
    cx.rectangle(-600, -600, 2400, 3200)
    src(cx, hexc("#5E6656"))
    cx.fill()
    # walls (left/right trapezoids) with wallpaper tone
    poly(cx, [(-600, -600), (ex0, ey0), (ex0, ey1), (-600, 2600)])
    src(cx, hexc("#7C866E"))
    cx.fill()
    poly(cx, [(1680, -600), (ex1, ey0), (ex1, ey1), (1680, 2600)])
    src(cx, hexc("#727C64"))
    cx.fill()
    # ceiling + floor
    poly(cx, [(-600, -600), (1680, -600), (ex1, ey0), (ex0, ey0)])
    src(cx, hexc("#B8B19E"))
    cx.fill()
    poly(cx, [(-600, 2600), (1680, 2600), (ex1, ey1), (ex0, ey1)])
    src(cx, hexc("#6E523C"))
    cx.fill()
    for k in range(-8, 9):
        line(cx, [(vx + k * 34, ey1), (vx + k * 300, 2600)], hexc("#4E3A2A", 0.7), 3)
    for d in (0.15, 0.32, 0.52, 0.74):
        yy = ey1 + (2600 - ey1) * d * d
        line(cx, [(ex0 - (ex0 + 600) * d * d, yy), (ex1 + (1680 - ex1) * d * d, yy)], hexc("#4E3A2A", 0.4), 2)
    # far end: black void (the unknown)
    cx.rectangle(ex0, ey0, ex1 - ex0, ey1 - ey0)
    src(cx, hexc("#101217"))
    cx.fill()
    # door frames on both sides
    for side, d0, d1 in [(-1, 0.25, 0.42), (1, 0.48, 0.62)]:
        def P(dd, yy_top):
            if side < 0:
                x = ex0 - (ex0 + 600) * (1 - dd)
                return x
            return ex1 + (1680 - ex1) * (1 - dd)
        xa, xb = P(d0, 0), P(d1, 0)
        ya_t = ey0 - (ey0 + 600) * (1 - d0) * 0.55
        yb_t = ey0 - (ey0 + 600) * (1 - d1) * 0.55
        ya_b = ey1 + (2600 - ey1) * (1 - d0) * 0.62
        yb_b = ey1 + (2600 - ey1) * (1 - d1) * 0.62
        poly(cx, [(xa, ya_t), (xb, yb_t), (xb, yb_b), (xa, ya_b)])
        fs(cx, hexc("#2A2C2E"), hexc("#D9D2C0"), 10)
    # picture frame
    poly(cx, [(70, 640), (230, 690), (230, 860), (70, 840)])
    fs(cx, hexc("#4D5A6A"), hexc("#8E6A4A"), 10)
    # runner rug
    poly(cx, [(ex0 + 40, ey1 + 10), (ex1 - 40, ey1 + 10), (900, 2600), (180, 2600)])
    src(cx, hexc("#7A3B34", 0.85))
    cx.fill()
    cx.restore()
    grade_dark(cx, 1 - light)
    # pool of darkness toward the end
    g = cairo.RadialGradient(*cam.to_screen(vx, vy), 40, *cam.to_screen(vx, vy), 800 * cam.zoom)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.75)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cx.set_source(g)
    cx.paint()


def pantry(cx, cam, t, light=0.6, water=0):
    cx.save()
    cam.apply(cx)
    cx.rectangle(-400, -400, 2000, 2800)
    src(cx, hexc("#7E6A52"))
    cx.fill()
    r = random.Random(12)
    for k, y in enumerate((520, 860, 1200)):
        rrect(cx, 60, y, 960, 26, 4)
        fs(cx, hexc("#A4815E"), OUTLINE, 5)
        x = 90
        while x < 980:
            kind = r.choice(["can", "can", "jar", "sack", "can"])
            if kind == "can":
                hh, ww = 90, 62
                rrect(cx, x, y - hh, ww, hh, 6)
                fs(cx, hexc(r.choice(["#C8473A", "#E2A33A", "#5E8A9E", "#7FA06A"])), OUTLINE, 4)
                rrect(cx, x, y - hh * 0.65, ww, hh * 0.3, 2)
                fs(cx, hexc("#F1ECE0"), OUTLINE, 2.5)
            elif kind == "jar":
                hh, ww = 120, 76
                rrect(cx, x, y - hh, ww, hh, 14)
                fs(cx, hexc(r.choice(["#D9734A", "#9E2F3A", "#6E9A4A"]), 0.9), OUTLINE, 4)
                rrect(cx, x + 4, y - hh - 12, ww - 8, 20, 5)
                fs(cx, hexc("#D9B44A"), OUTLINE, 3)
            else:
                hh, ww = 150, 110
                cx.move_to(x, y)
                cx.curve_to(x - 8, y - hh * 0.6, x + 10, y - hh, x + ww / 2, y - hh)
                cx.curve_to(x + ww - 10, y - hh, x + ww + 8, y - hh * 0.6, x + ww, y)
                cx.close_path()
                fs(cx, hexc("#E6D9B8"), OUTLINE, 4)
            x += ww + 14
    cx.restore()
    grade_dark(cx, 1 - light)


def water_jug(cx, x, y, s=1.0, fill=1.0, label=True):
    """1-gallon drinking-water jug."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-60, 0)
    cx.line_to(-60, -150)
    cx.curve_to(-60, -190, -30, -200, -20, -210)
    cx.line_to(-20, -232)
    cx.line_to(20, -232)
    cx.line_to(20, -210)
    cx.curve_to(30, -200, 60, -190, 60, -150)
    cx.line_to(60, 0)
    cx.close_path()
    fs(cx, hexc("#DCEBF5", 0.9), OUTLINE, 5)
    cx.save()
    cx.rectangle(-58, -200 * fill, 116, 200 * fill)
    cx.clip()
    cx.move_to(-60, 0)
    cx.line_to(-60, -150)
    cx.curve_to(-60, -190, -30, -200, -20, -210)
    cx.line_to(20, -210)
    cx.curve_to(30, -200, 60, -190, 60, -150)
    cx.line_to(60, 0)
    cx.close_path()
    src(cx, hexc("#7FC4F0", 0.75))
    cx.fill()
    cx.restore()
    rrect(cx, -24, -250, 48, 24, 6)
    fs(cx, hexc("#2F6FDB"), OUTLINE, 4)
    # handle
    cx.new_path()
    cx.arc(40, -140, 22, -math.pi / 2, math.pi / 2)
    src(cx, OUTLINE)
    cx.set_line_width(5)
    cx.stroke()
    if label:
        rrect(cx, -44, -110, 88, 50, 6)
        fs(cx, hexc("#2F6FDB"), OUTLINE, 3)
        from cinecode.core import text as _t
        _t(cx, "WATER", 0, -77, 20, hexc("#FFFFFF"))
    cx.restore()


def pump_unit(cx, x, y, s=1.0, on=1.0, t=0.0, needle=1.0):
    """Electric well pump: pressure tank + controller box with power light + gauge."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # pipe from the floor
    rrect(cx, -260, -40, 40, 400, 8)
    fs(cx, hexc("#9AA1A8"), OUTLINE, 5)
    rrect(cx, -260, -60, 300, 40, 8)
    fs(cx, hexc("#9AA1A8"), OUTLINE, 5)
    # pressure tank
    rrect(cx, -40, -380, 260, 560, 110)
    fs(cx, hexc("#3E6FA8"), OUTLINE, 6)
    ellipse(cx, 40, -260, 30, 120, 0)
    src(cx, (1, 1, 1, 0.18))
    cx.fill()
    # controller box
    rrect(cx, -330, -360, 200, 240, 14)
    fs(cx, hexc("#BFC3C7"), OUTLINE, 6)
    from cinecode.core import text as _t
    _t(cx, "PUMP", -230, -320, 30, OUTLINE)
    # power light
    if on > 0:
        g = cairo.RadialGradient(-230, -250, 4, -230, -250, 80)
        g.add_color_stop_rgba(0, 0.4, 1, 0.45, 0.8 * on)
        g.add_color_stop_rgba(1, 0.4, 1, 0.45, 0)
        cx.set_source(g)
        circle(cx, -230, -250, 80)
        cx.fill()
    circle(cx, -230, -250, 22)
    fs(cx, mix(hexc("#3A3D40"), hexc("#55F06A"), on), OUTLINE, 4)
    # gauge
    circle(cx, -230, -170, 34)
    fs(cx, hexc("#F3EEE2"), OUTLINE, 4)
    a = math.pi * (0.85 + 1.0 * needle) + (0.04 * math.sin(t * 20) * on)
    line(cx, [(-230, -170), (-230 + 26 * math.cos(a), -170 + 26 * math.sin(a))], hexc("#C0392B"), 4)
    # vibration lines when running
    if on > 0.5:
        for k in range(3):
            ph = (t * 3 + k * 0.33) % 1
            line(cx, [(240 + ph * 30, -300 + k * 60), (260 + ph * 30, -290 + k * 60)], OUTLINE, 3)
    cx.restore()


def front_door_close(cx, t, bolt=0.0, chain=0.0, light=0.8):
    """Close-up of the front door's deadbolt + chain (bolt/chain 0..1 = locked)."""
    cx.rectangle(0, 0, W, H)
    src(cx, hexc("#7A563E"))
    cx.fill()
    for k in range(6):
        line(cx, [(k * 200 + 40, 0), (k * 200 + 40, H)], hexc("#6A4A34"), 6)
    rrect(cx, 120, 300, 840, 520, 20)
    fs(cx, None, hexc("#5E4430"), 10)
    rrect(cx, 120, 1100, 840, 700, 20)
    fs(cx, None, hexc("#5E4430"), 10)
    # frame edge on the right
    cx.rectangle(960, 0, 120, H)
    fs(cx, hexc("#E9E3D4"), OUTLINE, 6)
    # deadbolt
    rrect(cx, 650, 860, 200, 200, 30)
    fs(cx, hexc("#D9B44A"), OUTLINE, 6)
    cx.save()
    cx.translate(750, 960)
    cx.rotate(-math.pi / 2 * (1 - bolt))
    rrect(cx, -70, -20, 140, 40, 18)
    fs(cx, hexc("#C79E3A"), OUTLINE, 5)
    cx.restore()
    # bolt throw into frame
    rrect(cx, 860, 940, 60 + 80 * bolt, 40, 8)
    fs(cx, hexc("#B8BCC2"), OUTLINE, 4)
    # chain
    rrect(cx, 990, 500, 60, 120, 10)
    fs(cx, hexc("#B8BCC2"), OUTLINE, 4)
    ax, ay = 1020, 600
    bx, by = lerp(820, 1010, chain), lerp(760, 540, chain)
    sag = 120 * (1 - chain) + 30
    for k in range(9):
        u = k / 8
        px = ax + (bx - ax) * u
        py = ay + (by - ay) * u + math.sin(math.pi * u) * sag
        ellipse(cx, px, py, 14, 9, 0.6 if k % 2 else -0.6)
        fs(cx, None, hexc("#C7CCD2"), 6)
    rrect(cx, bx - 14, by - 14, 28, 28, 8)
    fs(cx, hexc("#C7CCD2"), OUTLINE, 4)
    grade_dark(cx, 1 - light)

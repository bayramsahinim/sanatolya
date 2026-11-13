"""Day 2 sets (vertical). Every set function draws in screen space 1080x1920 unless noted."""
import math
import random

import cairo

from cinecode.core import ellipse, fs, hexc, line, mix, noise1, rrect, shade, src
from episodes.zombie_day_2.draw import H, INK, W

WALL = hexc("#cbbf9f")
WALL_S = hexc("#c2b593")
FLOOR = hexc("#5c412f")
FLOOR_L = hexc("#6b4c37")


def striped_wall(cx, x0, y0, x1, y1, base=WALL, stripe=WALL_S, step=72):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, base)
    cx.fill()
    x = x0 - (x0 % step)
    while x < x1:
        cx.rectangle(x, y0, step / 2, y1 - y0)
        src(cx, stripe)
        cx.fill()
        x += step


def wood_floor(cx, x0, y0, x1, y1, base=FLOOR, seed=1):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, base)
    cx.fill()
    r = random.Random(seed)
    y = y0
    h = 26
    while y < y1:
        line(cx, [(x0, y), (x1, y)], shade(base, -0.25), 2.5)
        x = x0 + r.uniform(0, 300)
        while x < x1:
            line(cx, [(x, y), (x, y + h)], shade(base, -0.25), 2)
            x += r.uniform(250, 420)
        y += h
        h *= 1.12
    # baseboard
    cx.rectangle(x0, y0 - 26, x1 - x0, 26)
    fs(cx, hexc("#e9e2d0"), INK, 3)


def frame_pic(cx, x, y, w, h):
    rrect(cx, x, y, w, h, 4)
    fs(cx, hexc("#5b3b26"), INK, 3)
    cx.rectangle(x + 10, y + 10, w - 20, h - 20)
    fs(cx, hexc("#e8dfc9"), None)
    for k in (0.35, 0.65):
        line(cx, [(x + w * k, y + h * 0.3), (x + w * k, y + h * 0.72)], INK, 3)
        ellipse(cx, x + w * k, y + h * 0.3, 7, 7)
        src(cx, INK)
        cx.fill()


def floor_lamp(cx, x, y_floor, y_top, on=False):
    line(cx, [(x, y_top + 60), (x, y_floor - 10)], INK, 9)
    ellipse(cx, x, y_floor - 6, 46, 10)
    src(cx, INK)
    cx.fill()
    cx.move_to(x - 48, y_top)
    cx.line_to(x + 48, y_top)
    cx.line_to(x + 78, y_top + 100)
    cx.line_to(x - 78, y_top + 100)
    cx.close_path()
    fs(cx, hexc("#dcc58e"), INK, 4)


def rug(cx, x, y, rx, ry):
    ellipse(cx, x, y, rx, ry)
    src(cx, hexc("#7a3d2c"))
    cx.fill()
    ellipse(cx, x, y, rx * 0.78, ry * 0.72)
    src(cx, hexc("#a2624a"), 0.6)
    cx.set_line_width(4)
    cx.stroke()


# ------------------------------------------------------------ outside (farm, morning)
def outside(cx, x0, y0, w, h, t, ground_frac=0.78, draw_fg=None, dim=0.0):
    """Morning farm view inside a rectangle. draw_fg(cx, ground_y) draws figures in the yard."""
    cx.save()
    cx.rectangle(x0, y0, w, h)
    cx.clip()
    g = cairo.LinearGradient(0, y0, 0, y0 + h)
    g.add_color_stop_rgba(0, *hexc("#e9d3a5"))
    g.add_color_stop_rgba(0.55, *hexc("#f3e2bb"))
    g.add_color_stop_rgba(1, *hexc("#f0dcb0"))
    cx.set_source(g)
    cx.paint()
    sx, sy = x0 + w * 0.72, y0 + h * 0.5
    rg = cairo.RadialGradient(sx, sy, 10, sx, sy, w * 0.5)
    rg.add_color_stop_rgba(0, 1, 0.97, 0.85, 0.9)
    rg.add_color_stop_rgba(1, 1, 0.95, 0.8, 0)
    cx.set_source(rg)
    cx.paint()
    ellipse(cx, sx, sy, w * 0.05, w * 0.05)
    src(cx, hexc("#fff5d6"))
    cx.fill()
    for k, (cy, cs) in enumerate(((0.18, 1.0), (0.32, 0.7))):
        ccx = x0 + ((t * (9 + 5 * k) + k * 0.45 * w) % (w * 1.6)) - w * 0.3
        ellipse(cx, ccx, y0 + h * cy, w * 0.13 * cs, h * 0.025 * cs)
        src(cx, (1, 1, 1, 0.5))
        cx.fill()
    hy = y0 + h * 0.56
    cx.move_to(x0, hy + 30)
    for i in range(13):
        xx = x0 + w * i / 12
        cx.line_to(xx, hy - 30 * abs(math.sin(i * 1.7)) - 10)
    cx.line_to(x0 + w, y0 + h)
    cx.line_to(x0, y0 + h)
    cx.close_path()
    src(cx, hexc("#8d9576"))
    cx.fill()
    gy = y0 + h * 0.62
    cx.rectangle(x0, gy, w, h)
    src(cx, hexc("#b8a068"))
    cx.fill()
    cx.rectangle(x0, y0 + h * ground_frac, w, h)
    src(cx, hexc("#7f6a45"))
    cx.fill()
    # barn
    bx, bw = x0 + w * 0.62, w * 0.3
    by = gy + 6
    bh = bw * 0.62
    cx.move_to(bx, by)
    cx.line_to(bx, by - bh * 0.62)
    cx.line_to(bx + bw / 2, by - bh)
    cx.line_to(bx + bw, by - bh * 0.62)
    cx.line_to(bx + bw, by)
    cx.close_path()
    fs(cx, hexc("#a8392f"), INK, 3)
    cx.rectangle(bx + bw * 0.32, by - bh * 0.42, bw * 0.36, bh * 0.42)
    fs(cx, hexc("#8a2c24"), hexc("#f0e6d6"), 3)
    line(cx, [(bx + bw * 0.32, by - bh * 0.42), (bx + bw * 0.68, by)], hexc("#f0e6d6"), 3)
    line(cx, [(bx + bw * 0.68, by - bh * 0.42), (bx + bw * 0.32, by)], hexc("#f0e6d6"), 3)
    # fence
    fy = y0 + h * 0.66
    line(cx, [(x0, fy), (x0 + w, fy)], hexc("#4a3a2a"), 4)
    line(cx, [(x0, fy + 18), (x0 + w, fy + 18)], hexc("#4a3a2a"), 4)
    for k in range(int(w / 50) + 1):
        line(cx, [(x0 + k * 50, fy - 10), (x0 + k * 50, fy + 30)], hexc("#4a3a2a"), 5)
    if draw_fg:
        draw_fg(cx, y0 + h * ground_frac + 20)
    if dim:
        cx.paint_with_alpha(0)
        src(cx, (0.1, 0.08, 0.06, dim))
        cx.paint()
    cx.restore()


def window(cx, x0, y0, w, h, t, draw_fg=None, curtains=True, sill=True):
    outside(cx, x0, y0, w, h, t, draw_fg=draw_fg)
    # glass reflection
    cx.save()
    cx.rectangle(x0, y0, w, h)
    cx.clip()
    cx.move_to(x0 + w * 0.1, y0 + h)
    cx.line_to(x0 + w * 0.45, y0)
    cx.line_to(x0 + w * 0.62, y0)
    cx.line_to(x0 + w * 0.27, y0 + h)
    src(cx, (1, 1, 1, 0.10))
    cx.fill()
    cx.restore()
    # frame + muntins
    fw = max(14, w * 0.035)
    cx.rectangle(x0, y0, w, h)
    src(cx, hexc("#efe9db"))
    cx.set_line_width(fw * 2)
    cx.stroke()
    cx.rectangle(x0 - fw, y0 - fw, w + 2 * fw, h + 2 * fw)
    src(cx, INK)
    cx.set_line_width(3)
    cx.stroke()
    line(cx, [(x0 + w / 2, y0), (x0 + w / 2, y0 + h)], hexc("#efe9db"), fw * 0.7)
    line(cx, [(x0, y0 + h * 0.45), (x0 + w, y0 + h * 0.45)], hexc("#efe9db"), fw * 0.7)
    if sill:
        rrect(cx, x0 - fw * 2.2, y0 + h + fw * 0.6, w + fw * 4.4, fw * 1.4, 4)
        fs(cx, hexc("#efe9db"), INK, 3)
    if curtains:
        for side in (-1, 1):
            cxp = x0 - fw * 2 if side < 0 else x0 + w + fw * 2
            sway = w * 0.025 * math.sin(t * 1.1 + side) + w * 0.012 * math.sin(t * 2.3 + side * 2)
            cx.move_to(cxp, y0 - fw * 3)
            cx.line_to(cxp - side * w * 0.2, y0 - fw * 3)
            cx.curve_to(cxp - side * w * 0.12 + sway * 0.5, y0 + h * 0.4, cxp - side * w * 0.2 + sway,
                        y0 + h * 0.8, cxp - side * w * 0.14 + sway * 1.4, y0 + h + fw * 2)
            cx.line_to(cxp, y0 + h + fw * 2)
            cx.close_path()
            fs(cx, hexc("#d9b65a"), INK, 3)
        rrect(cx, x0 - fw * 4, y0 - fw * 3.6, w + fw * 8, fw * 0.9, 4)
        fs(cx, hexc("#6b4a30"), INK, 2)


def couch_back(cx, x, y, w, h):
    """Couch seen from behind; (x, y) top-centre of the backrest."""
    for side in (-1, 1):
        ax = x + side * (w / 2 - 40)
        rrect(cx, ax - 70, y + 40, 140, h - 40, 40)
        fs(cx, hexc("#5f7a4f"), INK, 4)
    rrect(cx, x - w / 2 + 60, y, w - 120, h, 46)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgba(0, *hexc("#7a9666"))
    g.add_color_stop_rgba(1, *hexc("#5b744c"))
    cx.set_source(g)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(4)
    cx.stroke()
    for k in (-1, 0, 1):
        line(cx, [(x + k * (w - 120) / 3 * 0.9, y + 30), (x + k * (w - 120) / 3 * 0.9, y + h - 30)],
             shade(hexc("#5b744c"), -0.2), 3)
    for side in (-1, 1):
        line(cx, [(x + side * (w / 2 - 110), y + h), (x + side * (w / 2 - 110), y + h + 22)], INK, 12)


def living_room(cx, t, draw_fg=None, light=1.0):
    striped_wall(cx, 0, 0, W, 1320)
    cx.rectangle(0, 0, W, 40)
    fs(cx, hexc("#e9e2d0"), INK, 3)
    frame_pic(cx, 70, 300, 120, 96)
    frame_pic(cx, 210, 270, 90, 74)
    window(cx, 330, 360, 560, 520, t, draw_fg=draw_fg)
    floor_lamp(cx, 980, 1320, 840)
    wood_floor(cx, 0, 1320, W, H)
    rug(cx, 540, 1640, 520, 150)
    # morning light falling through the window
    cx.move_to(330, 880)
    cx.line_to(890, 880)
    cx.line_to(1080, 1900)
    cx.line_to(160, 1900)
    cx.close_path()
    g = cairo.LinearGradient(0, 880, 0, 1900)
    g.add_color_stop_rgba(0, 1, 0.92, 0.7, 0.16 * light)
    g.add_color_stop_rgba(1, 1, 0.92, 0.7, 0.0)
    cx.set_source(g)
    cx.fill()


def kitchen(cx, t, table=True, hatch=None):
    striped_wall(cx, 0, 0, W, 1240, base=hexc("#d3c7a8"), stripe=hexc("#cbbf9e"), step=90)
    # upper cabinets
    for k in range(3):
        rrect(cx, 40 + k * 230, 170, 210, 260, 8)
        fs(cx, hexc("#b39b6c"), INK, 4)
        ellipse(cx, 40 + k * 230 + (190 if k % 2 == 0 else 20), 400, 8, 8)
        src(cx, INK)
        cx.fill()
    # fridge
    rrect(cx, 760, 260, 280, 980, 18)
    fs(cx, hexc("#ece9e1"), INK, 4)
    line(cx, [(760, 600), (1040, 600)], INK, 3)
    line(cx, [(790, 420), (790, 540)], INK, 9)
    line(cx, [(790, 660), (790, 820)], INK, 9)
    rrect(cx, 880, 330, 110, 90, 3)
    fs(cx, hexc("#f2df8c"), INK, 2)
    # counter
    rrect(cx, 0, 760, 740, 40, 4)
    fs(cx, hexc("#e1d8c2"), INK, 3)
    cx.rectangle(0, 800, 740, 440)
    fs(cx, hexc("#a88e60"), INK, 4)
    for k in range(3):
        rrect(cx, 30 + k * 240, 840, 210, 360, 6)
        fs(cx, None, shade(hexc("#a88e60"), -0.3), 3)
    wood_floor(cx, 0, 1240, W, H, base=hexc("#5f4532"), seed=4)
    if hatch is not None:
        hatch(cx)
    if table:
        kitchen_table(cx, 540, 1430, 860)


def kitchen_table(cx, x, y, w):
    rrect(cx, x - w / 2, y - 18, w, 36, 8)
    fs(cx, hexc("#8a5f3c"), INK, 4)
    for side in (-1, 1):
        line(cx, [(x + side * (w / 2 - 50), y + 18), (x + side * (w / 2 - 50), y + 400)], INK, 22)
        line(cx, [(x + side * (w / 2 - 50), y + 18), (x + side * (w / 2 - 50), y + 400)], hexc("#7a5234"), 14)


def tabletop_close(cx, t):
    """Overhead close view of the wooden table for item close-ups."""
    cx.rectangle(0, 0, W, H)
    src(cx, hexc("#8a5f3c"))
    cx.fill()
    r = random.Random(7)
    for k in range(9):
        y = k * 230 + 40
        line(cx, [(0, y), (W, y)], shade(hexc("#8a5f3c"), -0.3), 4)
        for j in range(6):
            xx = r.uniform(0, W)
            cx.move_to(xx, y + 40)
            cx.curve_to(xx + 60, y + 60, xx + 120, y + 30, xx + 200, y + 70)
            src(cx, shade(hexc("#8a5f3c"), -0.15))
            cx.set_line_width(3)
            cx.stroke()
    g = cairo.RadialGradient(W / 2, H * 0.55, 200, W / 2, H * 0.55, 1300)
    g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.12)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    cx.set_source(g)
    cx.paint()


def front_door(cx, t, bang=0.0, cracks=0.0, draw_hands=None):
    striped_wall(cx, 0, 0, W, 1320)
    wood_floor(cx, 0, 1320, W, H, seed=9)
    cx.save()
    dx = bang * 10
    cx.translate(540 + dx, 1320)
    cx.scale(1 + bang * 0.012, 1)
    # frame
    rrect(cx, -300, -1080, 600, 1080, 6)
    fs(cx, hexc("#e9e2d0"), INK, 4)
    rrect(cx, -250, -1040, 500, 1040, 4)
    g = cairo.LinearGradient(-250, 0, 250, 0)
    g.add_color_stop_rgba(0, *hexc("#6e4a2f"))
    g.add_color_stop_rgba(1, *hexc("#5a3b25"))
    cx.set_source(g)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(4)
    cx.stroke()
    # small window in the door, zombie hands press on it
    rrect(cx, -150, -960, 300, 220, 10)
    fs(cx, hexc("#e8d4a6"), INK, 4)
    if draw_hands:
        cx.save()
        rrect(cx, -150, -960, 300, 220, 10)
        cx.clip()
        draw_hands(cx)
        cx.restore()
    line(cx, [(0, -960), (0, -740)], hexc("#e9e2d0"), 10)
    for py in (-660, -330):
        rrect(cx, -190, py, 160, 260, 6)
        fs(cx, None, shade(hexc("#5a3b25"), -0.35), 4)
        rrect(cx, 30, py, 160, 260, 6)
        fs(cx, None, shade(hexc("#5a3b25"), -0.35), 4)
    ellipse(cx, 190, -520, 22, 22)
    fs(cx, hexc("#c9a24a"), INK, 3)
    # chain + bolt
    line(cx, [(160, -700), (200, -660), (240, -700)], hexc("#b8b8b8"), 6)
    # light leaking through cracks
    if cracks > 0:
        src(cx, (1, 0.9, 0.6, 0.5 * cracks))
        cx.rectangle(-252, -1040, 6, 1040)
        cx.fill()
        cx.rectangle(-250, -6, 500, 6)
        cx.fill()
    cx.restore()


def hatch_floor(cx, x, y, w, h, open_=0.0, glow=0.0):
    """Trapdoor in the floor, in mild perspective. open_ 0..1 swings the lid up (towards the back)."""
    # hole
    cx.move_to(x - w / 2, y)
    cx.line_to(x + w / 2, y)
    cx.line_to(x + w / 2 + 30, y + h)
    cx.line_to(x - w / 2 - 30, y + h)
    cx.close_path()
    src(cx, hexc("#0c0908"))
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(5)
    cx.stroke()
    if open_ > 0.02:
        # top step visible
        for k in range(3):
            yy = y + h * (0.3 + k * 0.25)
            line(cx, [(x - w / 2 + 10, yy), (x + w / 2 - 10, yy)], hexc("#3a2a1c"), 14)
    # lid
    lh = h * math.cos(open_ * math.pi * 0.55)
    top = y + h - lh if open_ < 0.5 else y + h - lh
    lid_y0 = y + h - h if open_ == 0 else None
    ang = open_ * math.pi * 0.6
    # lid hinged at the back edge (y); its front edge rises
    fy = y + h * math.cos(ang)
    lift = h * math.sin(ang) * 1.2
    cx.move_to(x - w / 2, y)
    cx.line_to(x + w / 2, y)
    cx.line_to(x + w / 2 + 30 * math.cos(ang), fy - lift)
    cx.line_to(x - w / 2 - 30 * math.cos(ang), fy - lift)
    cx.close_path()
    src(cx, hexc("#7a5636") if open_ < 0.5 else hexc("#6a4a2e"))
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(5)
    cx.stroke()
    for k in range(1, 4):
        f = k / 4
        line(cx, [(x - w / 2 + w * f, y), (x - w / 2 + w * f, fy - lift)], shade(hexc("#7a5636"), -0.3), 3)
    # iron ring handle near the front edge
    rx, ry = x, y + (fy - lift - y) * 0.82
    cx.arc(rx, ry, 26, 0, 2 * math.pi)
    src(cx, hexc("#3a3a3a"))
    cx.set_line_width(7)
    cx.stroke()


# ------------------------------------------------------------ cellar (world coords, 1900 wide)
CELLAR_W = 1900


def cellar(cx, t, hatch_open=0.0, box_fall=None):
    # stone walls
    cx.rectangle(0, 0, CELLAR_W, H)
    src(cx, hexc("#4a4036"))
    cx.fill()
    r = random.Random(3)
    for row in range(26):
        y = 160 + row * 64
        off = (row % 2) * 70
        x = -off
        while x < CELLAR_W:
            w = r.uniform(110, 170)
            rrect(cx, x + 4, y + 4, w - 8, 56, 14)
            src(cx, shade(hexc("#5a4f43"), r.uniform(-0.12, 0.08)))
            cx.fill()
            x += w
    # ceiling beams
    cx.rectangle(0, 0, CELLAR_W, 170)
    fs(cx, hexc("#3b2a1c"), INK, 4)
    for k in range(7):
        rrect(cx, 60 + k * 280, 120, 70, 90, 6)
        fs(cx, hexc("#4b3624"), INK, 3)
    # hatch opening in the ceiling (top-left)
    hx0, hx1 = 150, 420
    cx.rectangle(hx0, 100, hx1 - hx0, 70)
    src(cx, mix(hexc("#0c0908"), hexc("#f4dfae"), hatch_open))
    cx.fill()
    # dirt floor
    cx.rectangle(0, 1580, CELLAR_W, H - 1580)
    src(cx, hexc("#3a2e24"))
    cx.fill()
    line(cx, [(0, 1580), (CELLAR_W, 1580)], INK, 4)
    # stairs from hatch down to the right
    stair_steps(cx)
    # shelves with jars
    sx = 1000
    for k in range(4):
        y = 700 + k * 230
        rrect(cx, sx, y, 520, 22, 4)
        fs(cx, hexc("#6b4b30"), INK, 3)
        for j in range(5):
            jx = sx + 40 + j * 95
            col = [hexc("#c46a2f"), hexc("#8a9a3a"), hexc("#b33b3b"), hexc("#d9b04a")][(j + k) % 4]
            rrect(cx, jx, y - 110, 60, 110, 10)
            fs(cx, col, INK, 3)
            rrect(cx, jx + 6, y - 126, 48, 20, 4)
            fs(cx, hexc("#9a9a9a"), INK, 2)
    for x in (sx, sx + 520):
        line(cx, [(x, 620), (x, 1580)], hexc("#5a3e27"), 18)
    # boxes
    for i, (bx, by, bw, bh) in enumerate(((640, 1400, 220, 180), (700, 1250, 170, 150), (1560, 1380, 260, 200),
                                          (1600, 1220, 190, 160))):
        if i == 1 and box_fall is not None:
            falling_box(cx, box_fall)
            continue
        rrect(cx, bx, by, bw, bh, 6)
        fs(cx, hexc("#9c7a4c"), INK, 4)
        line(cx, [(bx + bw / 2, by), (bx + bw / 2, by + bh * 0.35)], hexc("#c9b48a"), 10)
    # barrel
    ellipse(cx, 1720, 1500, 90, 110)
    fs(cx, hexc("#7a5232"), INK, 4)
    for dy in (-60, 60):
        line(cx, [(1636, 1500 + dy), (1804, 1500 + dy)], hexc("#3a3a3a"), 8)
    # pitchfork and shovel leaning on the wall
    line(cx, [(1580, 1580), (1650, 760)], hexc("#7a5232"), 12)
    for d in (-24, 0, 24):
        line(cx, [(1652 + d, 770), (1658 + d, 660)], hexc("#8a8a8a"), 7)
    line(cx, [(1630, 772), (1680, 770)], hexc("#8a8a8a"), 7)
    line(cx, [(900, 1580), (940, 860)], hexc("#7a5232"), 12)
    cx.move_to(915, 1580)
    cx.line_to(880, 1470)
    cx.line_to(960, 1470)
    cx.close_path()
    fs(cx, hexc("#8a8a8a"), INK, 3)
    # cobwebs
    for (wx, wy, d) in ((0, 170, 1), (CELLAR_W, 170, -1)):
        for k in range(4):
            cx.arc(wx, wy, 60 + k * 45, 0 if d > 0 else math.pi / 2, math.pi / 2 if d > 0 else math.pi)
            src(cx, (0.85, 0.85, 0.85, 0.35))
            cx.set_line_width(2)
            cx.stroke()
        for a in (0.2, 0.7, 1.2):
            aa = a if d > 0 else math.pi - a
            line(cx, [(wx, wy), (wx + math.cos(aa) * 200, wy + math.sin(aa) * 200)], (0.85, 0.85, 0.85, 0.35), 2)
    # hanging bulb (off)
    sw = 0.06 * math.sin(t * 1.4)
    bx, by = 760 + math.sin(sw) * 170, 170 + math.cos(sw) * 170
    line(cx, [(760, 170), (bx, by)], INK, 3)
    ellipse(cx, bx, by + 20, 22, 28)
    fs(cx, hexc("#9a9a8a"), INK, 3)


STAIR_TOP = (180, 170)
STAIR_BOT = (820, 1580)
N_STEPS = 11


def stair_point(f):
    """Ground point on the stairs at fraction f (0 top, 1 bottom)."""
    k = min(N_STEPS - 1, int(f * N_STEPS))
    x0, y0 = STAIR_TOP
    x1, y1 = STAIR_BOT
    sx = x0 + (x1 - x0) * (k + 0.5) / N_STEPS
    sy = y0 + (y1 - y0) * (k + 1) / N_STEPS
    return sx, sy


def stair_steps(cx):
    x0, y0 = STAIR_TOP
    x1, y1 = STAIR_BOT
    for k in range(N_STEPS):
        sx = x0 + (x1 - x0) * k / N_STEPS
        sy = y0 + (y1 - y0) * (k + 1) / N_STEPS
        rrect(cx, sx - 30, sy - 8, (x1 - x0) / N_STEPS + 90, 26, 4)
        fs(cx, hexc("#6e4c2e"), INK, 3)
    line(cx, [(x0 - 40, y0 + 40), (x1 + 20, y1 + 10)], hexc("#4a321e"), 20)
    line(cx, [(x0 + 120, y0 - 20), (x1 + 110, y1 - 140)], hexc("#5a3e27"), 10)  # handrail


def darkness(cx, alpha, lights):
    """Overlay darkness, punching out lights. lights: list of ('cone', x, y, ang, half, length, k) or
    ('glow', x, y, r, k)."""
    cx.push_group()
    src(cx, (0.01, 0.01, 0.02, alpha))
    cx.paint()
    cx.set_operator(cairo.OPERATOR_DEST_OUT)
    for L in lights:
        if L[0] == "cone":
            _, x, y, ang, half, length, k = L
            g = cairo.RadialGradient(x, y, 10, x, y, length)
            g.add_color_stop_rgba(0, 0, 0, 0, 0.98 * k)
            g.add_color_stop_rgba(0.6, 0, 0, 0, 0.85 * k)
            g.add_color_stop_rgba(1, 0, 0, 0, 0.0)
            for soft, mult in ((1.35, 0.35), (1.0, 1.0)):
                cx.move_to(x, y)
                cx.arc(x, y, length, ang - half * soft, ang + half * soft)
                cx.close_path()
                cx.save()
                cx.clip()
                cx.set_source(g)
                cx.paint_with_alpha(mult)
                cx.restore()
        else:
            _, x, y, r, k = L
            g = cairo.RadialGradient(x, y, 0, x, y, r)
            g.add_color_stop_rgba(0, 0, 0, 0, k)
            g.add_color_stop_rgba(1, 0, 0, 0, 0)
            cx.set_source(g)
            cx.paint()
    cx.set_operator(cairo.OPERATOR_OVER)
    cx.pop_group_to_source()
    cx.paint()
    # warm tint inside the beams
    for L in lights:
        if L[0] == "cone":
            _, x, y, ang, half, length, k = L
            cx.move_to(x, y)
            cx.arc(x, y, length, ang - half, ang + half)
            cx.close_path()
            g = cairo.RadialGradient(x, y, 10, x, y, length)
            g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.22 * k)
            g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0)
            cx.set_source(g)
            cx.fill()


def farm_exterior(cx, t, draw_fg=None):
    g = cairo.LinearGradient(0, 0, 0, 1000)
    g.add_color_stop_rgba(0, *hexc("#d9c49a"))
    g.add_color_stop_rgba(1, *hexc("#f1dfb6"))
    cx.set_source(g)
    cx.paint()
    sx, sy = 820, 760
    rg = cairo.RadialGradient(sx, sy, 10, sx, sy, 600)
    rg.add_color_stop_rgba(0, 1, 0.97, 0.85, 0.8)
    rg.add_color_stop_rgba(1, 1, 0.95, 0.8, 0)
    cx.set_source(rg)
    cx.paint()
    ellipse(cx, sx, sy, 50, 50)
    src(cx, hexc("#fff3d0"))
    cx.fill()
    # clouds
    for (x, y, s) in ((200, 300, 1.0), (760, 420, 0.8), (480, 200, 0.6)):
        x += (t * 6) % 200 - 100
        ellipse(cx, x, y, 110 * s, 22 * s)
        src(cx, (1, 1, 1, 0.45))
        cx.fill()
    cx.move_to(0, 880)
    for i in range(14):
        cx.line_to(i * 90, 820 - 50 * abs(math.sin(i * 1.3)))
    cx.line_to(W, 1000)
    cx.line_to(0, 1000)
    cx.close_path()
    src(cx, hexc("#7f8c6a"))
    cx.fill()
    cx.rectangle(0, 900, W, H)
    src(cx, hexc("#b39a63"))
    cx.fill()
    cx.rectangle(0, 1080, W, H)
    src(cx, hexc("#6e8a4e"))
    cx.fill()
    # farmhouse
    hx, hy, hw, hh = 260, 1100, 520, 330
    cx.move_to(hx - 30, hy - hh)
    cx.line_to(hx + hw / 2, hy - hh - 170)
    cx.line_to(hx + hw + 30, hy - hh)
    cx.close_path()
    fs(cx, hexc("#55575c"), INK, 4)
    cx.rectangle(hx, hy - hh, hw, hh)
    fs(cx, hexc("#ece6d6"), INK, 4)
    for k in range(1, 12):
        line(cx, [(hx, hy - hh + k * hh / 12), (hx + hw, hy - hh + k * hh / 12)], hexc("#d6cfbd"), 2)
    rrect(cx, hx + hw * 0.62, hy - hh - 220, 40, 90, 3)
    fs(cx, hexc("#6b4a3a"), INK, 3)
    for wx in (hx + 50, hx + hw - 150):
        for wy in (hy - hh + 40,):
            cx.rectangle(wx, wy, 100, 110)
            fs(cx, hexc("#3e4a58"), INK, 4)
            line(cx, [(wx + 50, wy), (wx + 50, wy + 110)], hexc("#ece6d6"), 5)
    cx.rectangle(hx + hw / 2 - 50, hy - 170, 100, 170)
    fs(cx, hexc("#7a3b2c"), INK, 4)
    rrect(cx, hx - 40, hy - 10, hw + 80, 20, 3)
    fs(cx, hexc("#8b7a64"), INK, 3)
    # barn on the right
    bx = 840
    cx.move_to(bx, 1100)
    cx.line_to(bx, 900)
    cx.line_to(bx + 150, 800)
    cx.line_to(bx + 300, 900)
    cx.line_to(bx + 300, 1100)
    cx.close_path()
    fs(cx, hexc("#a8392f"), INK, 4)
    # fence
    for k in range(25):
        line(cx, [(k * 45, 1150), (k * 45, 1215)], hexc("#5a4632"), 7)
    line(cx, [(0, 1165), (W, 1165)], hexc("#5a4632"), 6)
    line(cx, [(0, 1195), (W, 1195)], hexc("#5a4632"), 6)
    # yard path
    cx.move_to(hx + hw / 2 - 60, 1100)
    cx.line_to(hx + hw / 2 + 60, 1100)
    cx.line_to(700, H)
    cx.line_to(200, H)
    cx.close_path()
    src(cx, hexc("#9c8156"))
    cx.fill()
    if draw_fg:
        draw_fg(cx)


def vignette(cx, k=0.45):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, k)
    cx.set_source(g)
    cx.paint()


def falling_box(cx, ft):
    """The top box of the left stack slides off and crashes to the floor (ft = seconds since it started)."""
    bx, by, bw, bh = 700, 1250, 170, 150
    if ft <= 0:
        x, y, rot = bx, by, 0.0
    else:
        g = 2600
        x = bx + 170 * min(ft, 0.42) / 0.42
        y = min(by + 0.5 * g * ft * ft, 1580 - bh)
        rot = min(1.0, ft / 0.42) * 1.35
        if y >= 1580 - bh:
            rot = math.pi / 2 + 0.06 * math.exp(-(ft - 0.42) * 8) * math.sin((ft - 0.42) * 40)
    cx.save()
    cx.translate(x + bw / 2, y + bh / 2)
    cx.rotate(rot)
    rrect(cx, -bw / 2, -bh / 2, bw, bh, 6)
    fs(cx, hexc("#9c7a4c"), INK, 4)
    line(cx, [(0, -bh / 2), (0, -bh / 2 + bh * 0.35)], hexc("#c9b48a"), 10)
    cx.restore()
    if ft > 0.4:  # dust puff
        k = ft - 0.4
        for j in range(8):
            a = math.pi + j * math.pi / 7
            r = 40 + 260 * (1 - math.exp(-k * 4))
            ellipse(cx, x + bw / 2 + math.cos(a) * r, 1560 + math.sin(a) * r * 0.25, 40 + 30 * k, 22 + 14 * k)
            src(cx, (0.7, 0.65, 0.55, max(0, 0.35 - k * 0.3)))
            cx.fill()

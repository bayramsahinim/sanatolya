"""Environments. Each set draws itself through the camera with parallax layers.
Ground line for characters is GROUND (world y)."""
import math
import random

import cairo

from . import props as P
from .characters import Figure, Pose, RomanStyle, breathe
from .core import (H, OUTLINE, W, Cam, circle, clamp, curve, ellipse, fs, hexc, line, mix, poly,
                   rrect, shade, smooth, src, text, vgrad)

GROUND = 880


def _layer(cx, cam, par, fn, *a, **kw):
    cx.save()
    cam.apply(cx, par)
    fn(cx, *a, **kw)
    cx.restore()


def sky(cx, top="#7EC8F2", bottom="#D9F1FF"):
    cx.rectangle(-20000, -20000, 40000, 40000)
    cx.set_source(vgrad(cx, 0, -400, 0, GROUND, [(0, hexc(top)), (1, hexc(bottom))]))
    cx.fill()


def _paint_bg(cx, top, bottom):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *hexc(top))
    g.add_color_stop_rgba(1, *hexc(bottom))
    cx.set_source(g)
    cx.paint()


# ===================================================================== room
def room(cx, cam, t, night=False, lamp=1.0):
    _paint_bg(cx, "#F3E3C7", "#F3E3C7")

    def back(cx):
        # wall
        cx.rectangle(-1200, -600, 4400, GROUND + 600)
        src(cx, hexc("#F1D9B5"))
        cx.fill()
        cx.rectangle(-1200, GROUND - 40, 4400, 40)
        src(cx, hexc("#E2C49A"))
        cx.fill()
        # window with modern skyline
        wx, wy, ww, wh = 1180, 170, 420, 340
        rrect(cx, wx - 14, wy - 14, ww + 28, wh + 28, 10)
        fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
        cx.save()
        cx.rectangle(wx, wy, ww, wh)
        cx.clip()
        cx.set_source(vgrad(cx, 0, wy, 0, wy + wh, [(0, hexc("#8ECDF2")), (1, hexc("#D8F0FF"))]))
        cx.paint()
        r = random.Random(4)
        for i in range(9):
            bx = wx + i * 50 - 10
            bh = 90 + r.random() * 150
            cx.rectangle(bx, wy + wh - bh, 46, bh)
            src(cx, hexc(r.choice(["#9DB4C8", "#8AA2B8", "#AFC3D4"])))
            cx.fill()
            for k in range(int(bh // 26)):
                cx.rectangle(bx + 8, wy + wh - bh + 10 + k * 26, 10, 12)
                cx.rectangle(bx + 26, wy + wh - bh + 10 + k * 26, 10, 12)
            src(cx, hexc("#DDEBF5"))
            cx.fill()
        cx.restore()
        line(cx, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], hexc("#FFFFFF"), 10)
        line(cx, [(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], hexc("#FFFFFF"), 10)
        rrect(cx, wx, wy, ww, wh, 2)
        fs(cx, None, OUTLINE, 4)
        # poster (blank-ish rocket poster)
        rrect(cx, 330, 190, 190, 250, 6)
        fs(cx, hexc("#2F4A7A"), OUTLINE, 5)
        cx.move_to(425, 250)
        cx.curve_to(460, 290, 460, 350, 445, 380)
        cx.line_to(405, 380)
        cx.curve_to(390, 350, 390, 290, 425, 250)
        fs(cx, hexc("#F2F2F2"), OUTLINE, 3)
        circle(cx, 425, 315, 12)
        fs(cx, hexc("#7EC8F2"), OUTLINE, 3)
        P.star(cx, 370, 230, 9, hexc("#FFC857"))
        P.star(cx, 480, 410, 7, hexc("#FFC857"))
        # shelf + plant
        rrect(cx, 600, 300, 260, 16, 4)
        fs(cx, hexc("#B07A45"), OUTLINE, 4)
        rrect(cx, 630, 250, 40, 50, 6)
        fs(cx, hexc("#D96A4A"), OUTLINE, 4)
        for a in (-0.6, 0, 0.6):
            ellipse(cx, 650 + a * 30, 230, 12, 28, a)
            fs(cx, hexc("#5DAA4A"), OUTLINE, 3)
        for k in range(4):
            rrect(cx, 720 + k * 26, 246 + (k % 2) * 6, 22, 54 - (k % 2) * 6, 3)
            fs(cx, hexc(["#E05A47", "#4A86EA", "#FFC857", "#5DAA4A"][k]), OUTLINE, 3)
        # desk + laptop
        rrect(cx, 1650, 640, 420, 26, 5)
        fs(cx, hexc("#B07A45"), OUTLINE, 5)
        for lx in (1680, 2040):
            line(cx, [(lx, 664), (lx, GROUND)], OUTLINE, 14)
            line(cx, [(lx, 664), (lx, GROUND)], hexc("#B07A45"), 8)
        poly(cx, [(1760, 640), (1740, 560), (1880, 560), (1900, 640)])
        fs(cx, hexc("#B9BEC6"), OUTLINE, 4)
        poly(cx, [(1752, 630), (1736, 572), (1872, 572)], close=True)
        cx.new_path()
        # bed on left
        rrect(cx, -700, 690, 760, 120, 18)
        fs(cx, hexc("#6F9FC9"), OUTLINE, 5)
        rrect(cx, -700, 640, 60, 240, 10)
        fs(cx, hexc("#B07A45"), OUTLINE, 5)
        rrect(cx, -620, 660, 170, 60, 26)
        fs(cx, hexc("#FFFFFF"), OUTLINE, 4)
        # rug
        ellipse(cx, 900, GROUND + 6, 420, 26)
        fs(cx, hexc("#D96A4A"), OUTLINE, 4)
        ellipse(cx, 900, GROUND + 6, 340, 16)
        fs(cx, None, hexc("#F2B183"), 4)

    _layer(cx, cam, 1.0, back)


# ===================================================================== roman street
def _insula_block(cx, x, w, h, r, base):
    top = GROUND - h
    cx.rectangle(x, top, w, h)
    src(cx, base)
    cx.fill()
    # plaster texture blobs
    for k in range(6):
        ellipse(cx, x + r.random() * w, top + r.random() * h * 0.8, 20 + r.random() * 30, 8 + r.random() * 10)
        src(cx, shade(base, -0.06))
        cx.fill()
    cx.rectangle(x, top, w, h)
    fs(cx, None, OUTLINE, 5)
    # roof tiles
    rrect(cx, x - 16, top - 26, w + 32, 30, 6)
    fs(cx, hexc("#C0583A"), OUTLINE, 5)
    for k in range(int((w + 32) // 22)):
        line(cx, [(x - 10 + k * 22, top - 22), (x - 10 + k * 22, top + 2)], hexc("#9C4128"), 3)
    # floors
    floors = max(1, int((h - 260) // 150))
    for fl in range(floors):
        fy = top + 50 + fl * 150
        nwin = max(1, int(w // 150))
        for k in range(nwin):
            wx = x + (k + 0.5) * w / nwin
            rrect(cx, wx - 26, fy, 52, 72, 4)
            fs(cx, hexc("#3B2A20"), OUTLINE, 4)
            if r.random() < 0.6:
                # shutters
                for sx in (-1, 1):
                    rrect(cx, wx + sx * 40 - 14, fy - 2, 28, 76, 3)
                    fs(cx, hexc(r.choice(["#5E8C6A", "#3F6E8C", "#8C5A3F"])), OUTLINE, 3.5)
            if r.random() < 0.35:
                # flower box
                rrect(cx, wx - 34, fy + 70, 68, 16, 3)
                fs(cx, hexc("#A0522D"), OUTLINE, 3)
                for j in range(4):
                    circle(cx, wx - 24 + j * 16, fy + 66, 8)
                    fs(cx, hexc(r.choice(["#E05A47", "#F4D03F", "#5DAA4A"])), OUTLINE, 2.5)
    # ground floor: shop arch (taberna)
    ax = x + w / 2
    cx.move_to(ax - 70, GROUND)
    cx.line_to(ax - 70, GROUND - 150)
    cx.arc(ax, GROUND - 150, 70, math.pi, 2 * math.pi)
    cx.line_to(ax + 70, GROUND)
    cx.close_path()
    fs(cx, hexc("#4A3326"), OUTLINE, 5)
    cx.move_to(ax - 70, GROUND - 150)
    cx.arc(ax, GROUND - 150, 70, math.pi, 2 * math.pi)
    fs(cx, None, hexc("#E8D5B0"), 10)


def rome_street(cx, cam, t, x0=-2000, x1=8000, seed=11, dusk=0.0):
    _paint_bg(cx, "#7EC8F2", "#CBEBFF")

    def far(cx):
        r = random.Random(seed + 1)
        x = x0 * 0.4 - 400
        while x < x1 * 0.4 + 2400:
            w = 160 + r.random() * 200
            h = 360 + r.random() * 260
            cx.rectangle(x, GROUND - h - 140, w, h + 140)
            src(cx, hexc(r.choice(["#E7CBA0", "#E3BE93", "#EBD5B3"])))
            cx.fill()
            rrect(cx, x - 10, GROUND - h - 160, w + 20, 24, 5)
            src(cx, hexc("#D88C6A"))
            cx.fill()
            x += w + 10
        # cypress
        for k in range(12):
            px = x0 * 0.4 + k * 420 + r.random() * 200
            ellipse(cx, px, GROUND - 640, 26, 110)
            src(cx, hexc("#4E7A4A"))
            cx.fill()

    _layer(cx, cam, 0.45, far)

    def main(cx):
        r = random.Random(seed)
        x = x0
        while x < x1:
            w = 300 + r.random() * 220
            h = 560 + r.random() * 260
            base = hexc(r.choice(["#F0C987", "#E9B27A", "#F2D4A2", "#E7A97C", "#F3DDB5", "#DDB384"]))
            _insula_block(cx, x, w, h, r, base)
            # laundry line between blocks
            if r.random() < 0.5:
                ly = GROUND - h + 180
                curve(cx, (x + w - 20, ly), (x + w + 60, ly + 40), (x + w + 140, ly + 40), (x + w + 220, ly), OUTLINE, 2.5)
                for j in range(3):
                    cxp = x + w + 30 + j * 62
                    rrect(cx, cxp, ly + 22 + (j % 2) * 4, 40, 50, 4)
                    fs(cx, hexc(r.choice(["#FFFFFF", "#E05A47", "#6F9FC9", "#F4D03F"])), OUTLINE, 3)
            x += w
        # cobbles
        cx.rectangle(x0, GROUND, x1 - x0, 600)
        src(cx, hexc("#C9B79C"))
        cx.fill()
        line(cx, [(x0, GROUND), (x1, GROUND)], OUTLINE, 5)
        for row in range(5):
            yy = GROUND + 18 + row * 34
            off = (row % 2) * 30
            for k in range(int((x1 - x0) / 60)):
                ellipse(cx, x0 + off + k * 60, yy, 24, 10)
                src(cx, hexc("#B8A68A"))
                cx.fill()

    _layer(cx, cam, 1.0, main)
    if dusk:
        cx.rectangle(0, 0, W, H)
        src(cx, (0.2, 0.1, 0.3, 0.25 * dusk))
        cx.fill()


# ===================================================================== market / forum
def _temple(cx, x, y, s=1.0, col="#F3E9D2"):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # steps
    for k in range(4):
        cx.rectangle(-360 + k * 10, -k * 20, 720 - k * 20, 20)
        fs(cx, hexc("#E6D8BA"), OUTLINE, 4)
    base = -80
    # columns
    for k in range(7):
        cxx = -300 + k * 100
        cx.rectangle(cxx - 22, base - 300, 44, 300)
        fs(cx, hexc(col), OUTLINE, 4)
        for f in (-10, 0, 10):
            line(cx, [(cxx + f, base - 290), (cxx + f, base - 10)], hexc("#D8CBB0"), 2.5)
        rrect(cx, cxx - 30, base - 312, 60, 16, 3)
        fs(cx, hexc(col), OUTLINE, 3.5)
    # entablature + pediment
    cx.rectangle(-340, base - 360, 680, 50)
    fs(cx, hexc(col), OUTLINE, 4)
    poly(cx, [(-360, base - 360), (0, base - 480), (360, base - 360)])
    fs(cx, hexc(col), OUTLINE, 4)
    poly(cx, [(-300, base - 372), (0, base - 462), (300, base - 372)])
    fs(cx, hexc("#E6D8BA"), OUTLINE, 3)
    cx.restore()


def _stall(cx, x, w, stripe1, stripe2, goods, r, sag=0.0, wet=0.0):
    top = GROUND - 330
    # posts
    for px in (x + 10, x + w - 10):
        line(cx, [(px, top), (px, GROUND)], OUTLINE, 14)
        line(cx, [(px, top), (px, GROUND)], hexc("#8A5A2E"), 8)
    # counter
    rrect(cx, x - 10, GROUND - 120, w + 20, 120, 6)
    fs(cx, hexc("#B07A45"), OUTLINE, 5)
    for k in range(1, 4):
        line(cx, [(x - 6, GROUND - 120 + k * 30), (x + w + 6, GROUND - 120 + k * 30)], hexc("#8A5A2E"), 3)
    # goods on counter
    n = max(1, int(w // 130))
    for k in range(n):
        gx = x + (k + 0.5) * w / n
        g = goods[k % len(goods)]
        if g == "bread":
            for j in range(3):
                P.round_loaf(cx, gx - 30 + j * 30, GROUND - 132 - (j % 2) * 10, 0.9)
        elif g == "amphora":
            P.amphora(cx, gx, GROUND - 120, 0.75, r.choice(["#C66B3D", "#B5573A"]))
        else:
            P.basket(cx, gx, GROUND - 150, 0.85, g, seed=k + int(x))
    # awning (striped, scalloped)
    aw_y = top - 10 + sag
    stripes = int(w // 40) + 1
    for k in range(stripes):
        sx = x - 30 + k * (w + 60) / stripes
        sw = (w + 60) / stripes
        cx.move_to(sx, top - 70)
        cx.line_to(sx + sw, top - 70)
        cx.line_to(sx + sw, aw_y + 30)
        cx.curve_to(sx + sw, aw_y + 52, sx, aw_y + 52, sx, aw_y + 30)
        cx.close_path()
        c = hexc(stripe1 if k % 2 == 0 else stripe2)
        if wet:
            c = shade(c, -0.25 * wet)
        fs(cx, c, None, 0)
    cx.move_to(x - 30, top - 70)
    cx.line_to(x + w + 30, top - 70)
    cx.line_to(x + w + 30, aw_y + 30)
    for k in range(stripes - 1, -1, -1):
        sx = x - 30 + k * (w + 60) / stripes
        sw = (w + 60) / stripes
        cx.curve_to(sx + sw, aw_y + 52, sx, aw_y + 52, sx, aw_y + 30)
    cx.close_path()
    fs(cx, None, OUTLINE, 5)


MARKET_STALLS = [
    # x, w, stripe1, stripe2, goods
    (-900, 380, "#D9534F", "#F7EBD3", ["apples", "oranges"]),
    (-380, 420, "#3E7CB1", "#F7EBD3", ["amphora", "grapes"]),
    (180, 460, "#E8A23B", "#F7EBD3", ["bread", "bread"]),
    (820, 380, "#5E9A6E", "#F7EBD3", ["lemons", "figs", "olives"]),
    (1380, 420, "#9C5BA8", "#F7EBD3", ["amphora", "apples"]),
    (1980, 420, "#D9534F", "#F7EBD3", ["oranges", "grapes"]),
    (2580, 380, "#3E7CB1", "#F7EBD3", ["bread", "figs"]),
    (3140, 420, "#E8A23B", "#F7EBD3", ["olives", "apples"]),
]


def market(cx, cam, t, weather="sun", stalls=True, wet=0.0, cloud_dark=0.0):
    if weather == "rain":
        _paint_bg(cx, "#5B6577", "#9AA4B4")
    elif weather == "storm":
        _paint_bg(cx, "#7E8A9C", "#C9D3DE")
    else:
        _paint_bg(cx, "#7EC8F2", "#D9F1FF")

    def clouds(cx):
        drift = t * 12
        for k, (x, y, s) in enumerate([(-600, 160, 1.2), (300, 110, 0.9), (1100, 190, 1.1), (1900, 120, 1.0),
                                       (2700, 170, 1.2), (3500, 120, 0.9)]):
            c = (1, 1, 1, 0.92) if weather == "sun" else mix(hexc("#B7BFCB"), hexc("#596273"), 0.6)
            P.cloud(cx, x + drift, y, s, c)

    _layer(cx, cam, 0.15, clouds)

    def far(cx):
        # hills
        cx.move_to(-3000, GROUND - 300)
        for k in range(30):
            cx.line_to(-3000 + k * 300, GROUND - 330 - 60 * math.sin(k * 1.3) - 40 * math.sin(k * 0.7))
        cx.line_to(6000, GROUND)
        cx.line_to(-3000, GROUND)
        cx.close_path()
        src(cx, mix(hexc("#9CC48A"), hexc("#5E6E66"), 0.5 if weather != "sun" else 0))
        cx.fill()
        _temple(cx, 760, GROUND - 120, 1.0,
                "#F3E9D2" if weather == "sun" else "#CDD2D6")
        for k, px in enumerate([-500, -200, 1500, 1800, 2400, 2900]):
            ellipse(cx, px, GROUND - 340, 28, 120)
            src(cx, hexc("#4E7A4A") if weather == "sun" else hexc("#3E5A48"))
            cx.fill()
        # back wall of the forum
        cx.rectangle(-3000, GROUND - 200, 9000, 200)
        src(cx, hexc("#E8D2A8") if weather == "sun" else hexc("#A9A497"))
        cx.fill()
        line(cx, [(-3000, GROUND - 200), (6000, GROUND - 200)], OUTLINE, 4)

    _layer(cx, cam, 0.55, far)

    def mid(cx):
        # paving
        cx.rectangle(-3000, GROUND, 9000, 800)
        src(cx, hexc("#D8C7A6") if weather == "sun" else hexc("#8E8F94"))
        cx.fill()
        line(cx, [(-3000, GROUND), (6000, GROUND)], OUTLINE, 5)
        for row in range(6):
            yy = GROUND + 26 + row * 40
            for k in range(160):
                xx = -3000 + k * 60 + (row % 2) * 30
                cx.rectangle(xx, yy, 56, 2.5)
        src(cx, hexc("#C2B08E") if weather == "sun" else hexc("#7C7D83"))
        cx.fill()
        if wet:
            for k in range(14):
                ellipse(cx, -1500 + k * 400 + (k % 3) * 70, GROUND + 60 + (k % 4) * 40, 90, 12)
                src(cx, (0.75, 0.85, 1, 0.35 * wet))
                cx.fill()
        if stalls:
            r = random.Random(3)
            for (x, w, s1, s2, goods) in MARKET_STALLS:
                _stall(cx, x, w, s1, s2, goods, r, wet=wet)

    _layer(cx, cam, 1.0, mid)


# ===================================================================== bakery interior
def bakery(cx, cam, t, fire=1.0):
    _paint_bg(cx, "#E7C59A", "#E7C59A")

    def back(cx):
        cx.rectangle(-1500, -600, 5000, GROUND + 600)
        src(cx, hexc("#E9C9A0"))
        cx.fill()
        # brick patches
        r = random.Random(9)
        for k in range(40):
            bx = -1200 + r.random() * 4000
            by = 60 + r.random() * 600
            for j in range(3):
                rrect(cx, bx + (j % 2) * 20, by + j * 20, 46, 16, 3)
                fs(cx, hexc("#D9A47A"), hexc("#B98560"), 2)
        # domed oven
        ox, oy = 300, GROUND
        cx.move_to(ox - 260, oy)
        cx.line_to(ox - 260, oy - 220)
        cx.curve_to(ox - 260, oy - 520, ox + 260, oy - 520, ox + 260, oy - 220)
        cx.line_to(ox + 260, oy)
        cx.close_path()
        fs(cx, hexc("#C0704A"), OUTLINE, 6)
        for row in range(6):
            for k in range(7):
                rrect(cx, ox - 230 + k * 66 + (row % 2) * 30, oy - 60 - row * 60, 54, 22, 4)
                fs(cx, None, hexc("#A25A38"), 3)
        # mouth with fire
        cx.move_to(ox - 110, oy - 120)
        cx.line_to(ox - 110, oy - 230)
        cx.arc(ox, oy - 230, 110, math.pi, 2 * math.pi)
        cx.line_to(ox + 110, oy - 120)
        cx.close_path()
        fs(cx, hexc("#2A1A14"), OUTLINE, 5)
        g = cairo.RadialGradient(ox, oy - 150, 10, ox, oy - 150, 160)
        g.add_color_stop_rgba(0, 1, 0.85, 0.4, 0.95 * fire)
        g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
        cx.set_source(g)
        circle(cx, ox, oy - 160, 160)
        cx.fill()
        for k in range(5):
            fx = ox - 60 + k * 30
            fh = 50 + 25 * math.sin(t * 9 + k * 1.7)
            cx.move_to(fx - 16, oy - 124)
            cx.curve_to(fx - 16, oy - 124 - fh * 0.6, fx, oy - 124 - fh, fx, oy - 124 - fh)
            cx.curve_to(fx, oy - 124 - fh, fx + 16, oy - 124 - fh * 0.6, fx + 16, oy - 124)
            cx.close_path()
            fs(cx, hexc("#FF9E3D", fire), None, 0)
        rrect(cx, ox - 140, oy - 130, 280, 18, 4)
        fs(cx, hexc("#9A9188"), OUTLINE, 4)
        # shelves with loaves
        for sy in (330, 470):
            rrect(cx, 760, sy, 520, 18, 4)
            fs(cx, hexc("#8A5A2E"), OUTLINE, 4)
            for k in range(6):
                P.round_loaf(cx, 805 + k * 86, sy - 18, 1.05)
        # window arch to street
        wx = 1600
        cx.move_to(wx - 120, 560)
        cx.line_to(wx - 120, 300)
        cx.arc(wx, 300, 120, math.pi, 2 * math.pi)
        cx.line_to(wx + 120, 560)
        cx.close_path()
        cx.set_source(vgrad(cx, 0, 180, 0, 560, [(0, hexc("#9FD6F5")), (1, hexc("#E9F6FF"))]))
        cx.fill_preserve()
        src(cx, OUTLINE)
        cx.set_line_width(6)
        cx.stroke()
        # hanging herbs + utensils
        for k in range(4):
            hx = 820 + k * 120
            line(cx, [(hx, 150), (hx, 210)], OUTLINE, 3)
            for j in range(5):
                ellipse(cx, hx + (j - 2) * 7, 220 + abs(j - 2) * 6, 6, 18, (j - 2) * 0.3)
                fs(cx, hexc("#6E9B5A"), OUTLINE, 2)
        # floor
        cx.rectangle(-1500, GROUND, 5000, 600)
        src(cx, hexc("#B98E66"))
        cx.fill()
        line(cx, [(-1500, GROUND), (3500, GROUND)], OUTLINE, 5)
        for k in range(40):
            line(cx, [(-1500 + k * 140, GROUND + 4), (-1500 + k * 140 - 60, GROUND + 300)], hexc("#A87D57"), 3)
        # flour sacks
        for k, (sx, ss) in enumerate([(-260, 1.0), (-160, 0.85)]):
            cx.save()
            cx.translate(sx, GROUND)
            cx.scale(ss, ss)
            cx.move_to(-60, 0)
            cx.curve_to(-80, -80, -50, -150, -30, -160)
            cx.line_to(30, -160)
            cx.curve_to(50, -150, 80, -80, 60, 0)
            cx.close_path()
            fs(cx, hexc("#EEE3CC"), OUTLINE, 5)
            text(cx, "FARINA", 0, -60, 20, hexc("#8A5A2E"))
            cx.restore()

    _layer(cx, cam, 1.0, back)


def counter(cx, x, w=700, top=GROUND - 150):
    rrect(cx, x - w / 2, top, w, GROUND - top + 10, 8)
    fs(cx, hexc("#B07A45"), OUTLINE, 6)
    rrect(cx, x - w / 2 - 16, top - 10, w + 32, 24, 6)
    fs(cx, hexc("#C99A62"), OUTLINE, 5)
    for k in range(1, 4):
        line(cx, [(x - w / 2 + 6, top + 14 + k * 36), (x + w / 2 - 6, top + 14 + k * 36)], hexc("#8A5A2E"), 3)


# ===================================================================== square / festival
def square(cx, cam, t, festival=True, stage_x=960, crowd_bg=True, sky_dark=0.0):
    _paint_bg(cx, "#79C1EE", "#E2F4FF")
    if sky_dark:
        cx.rectangle(0, 0, W, H)
        src(cx, (0.3, 0.33, 0.4, 0.5 * sky_dark))
        cx.fill()

    def far(cx):
        for (x, y, s) in [(-200, 140, 1.1), (900, 100, 0.8), (1800, 160, 1.0)]:
            P.cloud(cx, x + t * 8, y, s, (1, 1, 1, 0.92))

    _layer(cx, cam, 0.15, far)

    def back(cx):
        # colonnade
        cx.rectangle(-2000, GROUND - 520, 6000, 520)
        src(cx, hexc("#EADBBE"))
        cx.fill()
        cx.rectangle(-2000, GROUND - 560, 6000, 50)
        fs(cx, hexc("#F3E9D2"), OUTLINE, 5)
        for k in range(40):
            px = -1800 + k * 140
            cx.rectangle(px - 22, GROUND - 510, 44, 510)
            fs(cx, hexc("#F6EEDC"), OUTLINE, 4)
            rrect(cx, px - 30, GROUND - 520, 60, 16, 3)
            fs(cx, hexc("#F6EEDC"), OUTLINE, 3)
        # arcade shadows
        for k in range(39):
            px = -1800 + k * 140 + 70
            cx.rectangle(px - 46, GROUND - 480, 92, 480)
            src(cx, hexc("#CDB894"))
            cx.fill()
        if festival:
            # garlands
            for k in range(14):
                gx = -1200 + k * 300
                curve(cx, (gx, GROUND - 540), (gx + 80, GROUND - 450), (gx + 220, GROUND - 450),
                      (gx + 300, GROUND - 540), hexc("#4E8A4A"), 12)
                for j in range(5):
                    circle(cx, gx + 40 + j * 55, GROUND - 470 + abs(j - 2) * -8 + 8, 8)
                    fs(cx, hexc(["#E05A47", "#FFC857", "#F2F2F2"][j % 3]), OUTLINE, 2)
            # banners
            for k in range(-4, 6):
                bx = stage_x + k * 420 + 140
                cx.move_to(bx - 60, GROUND - 600)
                cx.line_to(bx + 60, GROUND - 600)
                cx.line_to(bx + 60, GROUND - 330)
                cx.line_to(bx, GROUND - 370 + math.sin(t * 2 + k) * 5)
                cx.line_to(bx - 60, GROUND - 330)
                cx.close_path()
                fs(cx, hexc("#B8322E"), OUTLINE, 5)
                text(cx, "SPQR", bx, GROUND - 480, 30, hexc("#FFC857"))
                circle(cx, bx, GROUND - 420, 16)
                fs(cx, None, hexc("#FFC857"), 4)
        # paving
        cx.rectangle(-2000, GROUND, 6000, 800)
        src(cx, hexc("#D8C7A6"))
        cx.fill()
        line(cx, [(-2000, GROUND), (4000, GROUND)], OUTLINE, 5)

    _layer(cx, cam, 1.0, back)


def stage(cx, x, top=GROUND - 150, w=760):
    """Wooden festival stage. top = stage floor y."""
    cx.rectangle(x - w / 2, top, w, GROUND - top)
    fs(cx, hexc("#A8703E"), OUTLINE, 6)
    for k in range(1, int(w // 90)):
        line(cx, [(x - w / 2 + k * 90, top + 6), (x - w / 2 + k * 90, GROUND - 4)], hexc("#8A5A2E"), 3)
    rrect(cx, x - w / 2 - 14, top - 14, w + 28, 22, 5)
    fs(cx, hexc("#C99A62"), OUTLINE, 5)
    # bunting
    for k in range(int(w // 60)):
        bx = x - w / 2 + 10 + k * 60
        poly(cx, [(bx, top + 10), (bx + 50, top + 10), (bx + 25, top + 46)])
        fs(cx, hexc(["#B8322E", "#FFC857", "#F7EBD3"][k % 3]), OUTLINE, 3)


def rain_rig(cx, x, top, bucket_tilt=0.0, bucket_drop=0.0, rope_pull=0.0, collapse=0.0, cloth=True,
             water=True, bucket_vis=True, t=0.0):
    """The fake-rain contraption: wooden gantry above a stage, hidden bucket, rope to the side.
    (x, top) = point above stage centre where the bucket hangs. Returns rope end."""
    beam_y = top
    lean = collapse * 0.5
    cx.save()
    # posts
    for sx in (-1, 1):
        px = x + sx * 300
        cx.save()
        cx.translate(px, GROUND - 150)
        cx.rotate(sx * lean * (1 if sx > 0 else 0.6))
        line(cx, [(0, 0), (0, beam_y - (GROUND - 150))], OUTLINE, 18)
        line(cx, [(0, 0), (0, beam_y - (GROUND - 150))], hexc("#9C6B3F"), 11)
        cx.restore()
    # beam
    cx.save()
    cx.translate(x, beam_y)
    cx.rotate(collapse * 0.35)
    cx.translate(0, collapse * 120)
    rrect(cx, -330, -16, 660, 30, 8)
    fs(cx, hexc("#9C6B3F"), OUTLINE, 6)
    # disguise cloth (sky-blue sheet with painted clouds)
    if cloth:
        cx.move_to(-280, 10)
        for k in range(15):
            cx.line_to(-280 + k * 40, 110 + (12 if k % 2 else 0) + math.sin(t * 2 + k) * 4)
        cx.line_to(280, 10)
        cx.close_path()
        fs(cx, hexc("#A9D8F5"), OUTLINE, 5)
        P.cloud(cx, -120, 60, 0.45, (1, 1, 1, 0.95))
        P.cloud(cx, 130, 50, 0.38, (1, 1, 1, 0.95))
    # pulley
    circle(cx, 0, 14, 16)
    fs(cx, hexc("#7E5128"), OUTLINE, 4)
    cx.restore()
    cx.restore()
    rope_end = (x + 420 - rope_pull * 40, GROUND - 280 + rope_pull * 60)
    return rope_end


# ===================================================================== desert
def desert(cx, cam, t, heat=1.0):
    _paint_bg(cx, "#F7C873", "#FCE9B8")

    def far(cx):
        g = cairo.RadialGradient(1500, 180, 10, 1500, 180, 260)
        g.add_color_stop_rgba(0, 1, 1, 0.9, 1)
        g.add_color_stop_rgba(0.35, 1, 0.95, 0.7, 0.9)
        g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
        cx.set_source(g)
        circle(cx, 1500, 180, 260)
        cx.fill()
        circle(cx, 1500, 180, 80)
        fs(cx, hexc("#FFF6D6"), OUTLINE, 5)
        # pyramids
        for (px, w, h) in [(620, 520, 380), (1060, 380, 280), (300, 300, 200)]:
            poly(cx, [(px - w / 2, GROUND - 120), (px, GROUND - 120 - h), (px + w / 2, GROUND - 120)])
            fs(cx, hexc("#E9B66A"), OUTLINE, 5)
            poly(cx, [(px, GROUND - 120 - h), (px + w / 2, GROUND - 120), (px + w * 0.12, GROUND - 120)])
            fs(cx, hexc("#D29A50"), None, 0)
            for k in range(1, 7):
                yy = GROUND - 120 - h * k / 7
                hw = w / 2 * (1 - k / 7)
                line(cx, [(px - hw, yy), (px + hw, yy)], hexc("#C88F48"), 2)
        # palm
        px = 1400
        curve(cx, (px, GROUND - 110), (px - 10, GROUND - 200), (px + 20, GROUND - 260), (px + 10, GROUND - 330),
              hexc("#8A5A2E"), 14)
        for a in range(6):
            ang = -math.pi * (0.1 + a * 0.16)
            curve(cx, (px + 10, GROUND - 330), (px + 10 + math.cos(ang) * 60, GROUND - 360 + math.sin(ang) * 40),
                  (px + 10 + math.cos(ang) * 110, GROUND - 330 + math.sin(ang) * 30),
                  (px + 10 + math.cos(ang) * 140, GROUND - 300), hexc("#5E9A4A"), 12)

    _layer(cx, cam, 0.5, far)

    def dunes(cx):
        cx.move_to(-2000, GROUND - 90)
        for k in range(40):
            cx.line_to(-2000 + k * 150, GROUND - 100 - 40 * math.sin(k * 0.9) - 20 * math.sin(k * 2.1))
        cx.line_to(4000, GROUND + 800)
        cx.line_to(-2000, GROUND + 800)
        cx.close_path()
        fs(cx, hexc("#F0C680"), None, 0)
        cx.rectangle(-2000, GROUND, 6000, 800)
        src(cx, hexc("#EDBB6E"))
        cx.fill()
        for k in range(18):
            curve(cx, (-1200 + k * 260, GROUND + 60 + (k % 3) * 50), (-1140 + k * 260, GROUND + 40 + (k % 3) * 50),
                  (-1080 + k * 260, GROUND + 40 + (k % 3) * 50), (-1020 + k * 260, GROUND + 60 + (k % 3) * 50),
                  hexc("#D9A25A"), 4)

    _layer(cx, cam, 1.0, dunes)
    if heat:
        # heat shimmer lines
        for k in range(6):
            y = 640 + k * 30
            cx.move_to(0, y)
            for x in range(0, W + 40, 40):
                cx.line_to(x, y + math.sin(x * 0.02 + t * 4 + k) * 4)
            src(cx, (1, 1, 1, 0.12 * heat))
            cx.set_line_width(3)
            cx.stroke()


# ===================================================================== crowd
_CROWD_CACHE = {}


def crowd_figs(seed, n):
    key = (seed, n)
    if key not in _CROWD_CACHE:
        _CROWD_CACHE[key] = [Figure(RomanStyle(seed=seed * 100 + i), seed=seed * 100 + i) for i in range(n)]
    return _CROWD_CACHE[key]


def crowd(cx, t, x0, x1, y, n, seed=1, s=0.85, mood="idle", mood_t=0.0, face=0.0, look=(0, 0),
          rows=1, row_dy=-40, view="front", skip=()):
    """mood: idle, gasp, cheer, laugh, murmur, confused, angry, wet. mood_t = seconds since mood start."""
    figs = crowd_figs(seed, n * rows)
    r = random.Random(seed)
    idx = 0
    for row in range(rows - 1, -1, -1):
        for i in range(n):
            fig = figs[idx]
            idx += 1
            if (row, i) in skip:
                continue
            jitter = r.random()
            x = x0 + (i + 0.5 + (0.5 if row % 2 else 0)) * (x1 - x0) / n + (jitter - 0.5) * 30
            yy = y + row * row_dy
            sc = s * (1 - row * 0.08) * (0.92 + 0.16 * r.random())
            ft = 1 if (r.random() < 0.5) else -1
            p = Pose(x=x, y=yy, s=sc, t=t + jitter * 3, view=view, f=ft, blink_seed=idx,
                     look=look, mouth="smile", arm_a=8, arm_b=8, elb_a=8, elb_b=8)
            if view == "front":
                p = p.but(arm_a=10, arm_b=10)
            p = breathe(p, t + jitter * 5)
            delay = jitter * 0.25
            m = mood if mood_t > delay else "idle"
            if m == "gasp":
                p = p.but(eyes="wide", mouth="o", brows="up", mouth_open=1.2, lean=-6,
                          arm_a=40 + 30 * jitter, arm_b=40, elb_a=100, elb_b=100)
            elif m == "cheer":
                ph = (t * 3 + jitter * 6)
                p = p.but(eyes="happy", mouth="grin", arm_a=150 + 20 * math.sin(ph), arm_b=150 - 20 * math.sin(ph),
                          elb_a=15, elb_b=15, bob=-abs(math.sin(ph)) * 18)
            elif m == "laugh":
                ph = (t * 7 + jitter * 6)
                p = p.but(eyes="happy", mouth="grin", lean=-8 + 6 * math.sin(ph), bob=-abs(math.sin(ph)) * 6,
                          arm_a=60, arm_b=60, elb_a=90, elb_b=90)
            elif m == "confused":
                p = p.but(eyes="open", mouth="flat", brows="skeptic", tilt=12 * (1 if jitter > 0.5 else -1),
                          look=(1 if jitter > 0.5 else -1, 0))
            elif m == "murmur":
                p = p.but(mouth="o" if math.sin(t * 8 + jitter * 9) > 0 else "flat", mouth_open=0.6,
                          look=(1 if jitter > 0.5 else -1, 0), brows="up")
            elif m == "angry":
                p = p.but(brows="angry", mouth="yell", mouth_open=0.7, arm_a=150, elb_a=-20)
            elif m == "stare":
                p = p.but(eyes="open", mouth="flat", brows="neutral")
            elif m == "wet":
                p = p.but(brows="angry", mouth="frown", arm_a=150, arm_b=150, elb_a=60, elb_b=60)
            fig.draw(cx, p)

"""Environments and props for the vertical short (scene space = 1080x1920)."""
import math
import random

import cairo

from episodes.japan_johatsu.art import (FONT, H, INK, JP_FONT, W, alpha, cached_layer, contact_shadow, ellipse,
                                        fill_ink, glow, hx, ink, light_cone, lin, mixc, paint_layer, poly, rad,
                                        rrect, shade, src, text)

WARM = hx("#ffcf8a")
COLD = hx("#7fa6ff")
NEON = hx("#ff4fa3")


# ---------------------------------------------------------------- city skyline (used through windows)
def skyline(cx, x, y, w, h, seed=1, dawn=0.0, lit=0.55):
    sky_top = mixc(hx("#0b1330"), hx("#3b4f8a"), dawn)
    sky_bot = mixc(hx("#1d2c5e"), hx("#f2a76b"), dawn)
    lin(cx, 0, y, 0, y + h, [(0, sky_top), (1, sky_bot)])
    cx.rectangle(x, y, w, h)
    cx.fill()
    rng = random.Random(seed)
    for layer, (col, hmin, hmax, a) in enumerate([
            (mixc(hx("#1a2550"), hx("#7c6a8e"), dawn), 0.25, 0.55, 1.0),
            (mixc(hx("#111a3b"), hx("#4c4466"), dawn), 0.15, 0.40, 1.0)]):
        xx = x - 10
        while xx < x + w:
            bw = rng.uniform(w * 0.06, w * 0.16)
            bh = rng.uniform(hmin, hmax) * h
            by = y + h - bh
            cx.rectangle(xx, by, bw, bh)
            src(cx, col)
            cx.fill()
            # lit windows
            for wy in range(int(by + 8), int(y + h - 6), 14):
                for wx in range(int(xx + 5), int(xx + bw - 6), 11):
                    if rng.random() < lit * (1 - dawn * 0.8):
                        cx.rectangle(wx, wy, 5, 7)
                        src(cx, alpha(hx("#ffd98a") if rng.random() < 0.8 else hx("#bfe3ff"),
                                      rng.uniform(0.45, 0.95)))
                        cx.fill()
            xx += bw + rng.uniform(0, 6)


# ---------------------------------------------------------------- apartment
def apartment_static(cx, night=True):
    # wall
    lin(cx, 0, 0, 0, 1180, [(0, hx("#6d5a43")), (0.5, hx("#a68c66")), (1, hx("#8c7454"))])
    cx.rectangle(0, 0, W, 1180)
    cx.fill()
    # wallpaper pattern
    for i in range(0, W, 36):
        cx.rectangle(i, 0, 2, 1180)
        src(cx, (1, 1, 1, 0.035))
        cx.fill()
    # ceiling line / molding
    cx.rectangle(0, 120, W, 16)
    src(cx, hx("#5b4632"))
    cx.fill()
    # window (right)
    wx, wy, ww, wh = 610, 300, 400, 470
    skyline(cx, wx, wy, ww, wh, seed=3)
    glow(cx, wx + ww * 0.75, wy + 80, 90, hx("#cfe0ff"), 0.35)
    # frame + mullions
    for (rx, ry, rw, rh) in [(wx - 16, wy - 16, ww + 32, 16), (wx - 16, wy + wh, ww + 32, 22),
                             (wx - 16, wy, 16, wh), (wx + ww, wy, 16, wh), (wx + ww / 2 - 5, wy, 10, wh)]:
        cx.rectangle(rx, ry, rw, rh)
        lin(cx, rx, ry, rx, ry + rh, [(0, hx("#5a432e")), (1, hx("#3e2d1f"))])
        cx.fill()
    cx.rectangle(wx, wy + wh * 0.5 - 4, ww, 8)
    src(cx, hx("#4a3726"))
    cx.fill()
    # curtain
    cx.move_to(wx - 30, wy - 30)
    for k in range(7):
        cx.line_to(wx - 30 + k * 13, wy + wh + 40 if k % 2 else wy + wh + 30)
    cx.line_to(wx + 70, wy - 30)
    cx.close_path()
    lin(cx, wx - 30, 0, wx + 70, 0, [(0, hx("#1f4b3c")), (0.5, hx("#2f6a54")), (1, hx("#1d4436"))])
    cx.fill()
    # shoji sliding door (left)
    sx, sy, sw, sh = 50, 380, 300, 800
    cx.rectangle(sx - 14, sy - 14, sw + 28, sh + 14)
    src(cx, hx("#4b3624"))
    cx.fill()
    lin(cx, sx, sy, sx + sw, sy, [(0, hx("#d9cfb4")), (1, hx("#c3b795"))])
    cx.rectangle(sx, sy, sw, sh)
    cx.fill()
    for k in range(1, 4):
        cx.rectangle(sx + sw * k / 4 - 3, sy, 6, sh)
        src(cx, hx("#6b4d33"))
        cx.fill()
    for k in range(1, 8):
        cx.rectangle(sx, sy + sh * k / 8 - 3, sw, 6)
        src(cx, hx("#6b4d33"))
        cx.fill()
    # calendar
    cx.rectangle(420, 400, 130, 170)
    src(cx, hx("#efe9dc"))
    cx.fill()
    cx.rectangle(420, 400, 130, 34)
    src(cx, hx("#b8443a"))
    cx.fill()
    for r_ in range(4):
        for c_ in range(5):
            cx.rectangle(432 + c_ * 23, 448 + r_ * 28, 14, 14)
            src(cx, hx("#9a9387"))
            cx.fill()
    # shelf
    cx.rectangle(610, 880, 400, 18)
    src(cx, hx("#4a3423"))
    cx.fill()
    contact_shadow(cx, 810, 905, 210, 12, 0.35)
    # floor (tatami) with perspective
    lin(cx, 0, 1180, 0, H, [(0, hx("#8f8a50")), (1, hx("#5d5a33"))])
    cx.rectangle(0, 1180, W, H - 1180)
    cx.fill()
    vp = (540, 620)
    for k in range(-6, 8):
        x0 = 540 + k * 230
        cx.move_to(vp[0] + (x0 - vp[0]) * 0.0 + (x0 - 540) * 0.33, 1180)
        cx.line_to(x0 + (x0 - 540) * 0.9, H)
        src(cx, (0.2, 0.18, 0.08, 0.35))
        cx.set_line_width(4)
        cx.stroke()
    for yy in (1330, 1560, 1860):
        cx.rectangle(0, yy, W, 5)
        src(cx, (0.2, 0.18, 0.08, 0.35))
        cx.fill()
    # skirting
    cx.rectangle(0, 1170, W, 18)
    src(cx, hx("#3e2c1d"))
    cx.fill()
    # cold window light on floor
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    lin(cx, 0, 1180, 0, 1700, [(0, alpha(COLD, 0.10)), (1, alpha(COLD, 0))])
    poly(cx, [(610, 1180), (1010, 1180), (1080, 1700), (520, 1700)])
    cx.fill()
    cx.restore()


def books(cx, x, y, n, seed=2, keep=1.0):
    rng = random.Random(seed)
    cols = [hx(c) for c in ("#8a3b34", "#2f5a7a", "#c49a3a", "#3b6b4a", "#6b4a7a", "#d9cfb4")]
    for i in range(n):
        if i / n >= keep:
            break
        bw = rng.uniform(16, 26)
        bh = rng.uniform(70, 100)
        cx.rectangle(x, y - bh, bw, bh)
        lin(cx, x, 0, x + bw, 0, [(0, shade(cols[i % 6], 0.1)), (1, shade(cols[i % 6], -0.25))])
        cx.fill()
        x += bw + 2


def photo_frame(cx, x, y, w=110, h=130, tilt=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(tilt)
    rrect(cx, -w / 2, -h, w, h, 6)
    src(cx, hx("#3a2a1c"))
    cx.fill()
    cx.rectangle(-w / 2 + 12, -h + 12, w - 24, h - 24)
    lin(cx, 0, -h, 0, 0, [(0, hx("#9cc3d9")), (1, hx("#d9e4c0"))])
    cx.fill()
    # tiny family (mom + boy) in the photo
    for dx, r, col in ((-14, 15, hx("#6e3a63")), (16, 12, hx("#283553"))):
        cx.arc(dx, -h * 0.58, r * 0.75, 0, 2 * math.pi)
        src(cx, hx("#f1c7a1"))
        cx.fill()
        ellipse(cx, dx, -h * 0.28, r * 0.75, r)
        src(cx, col)
        cx.fill()
    cx.arc(-14, -h * 0.66, 12, math.pi, 2 * math.pi)
    src(cx, hx("#bdb8bd"))
    cx.fill()
    cx.restore()


def low_table(cx, x=540, y=1420, w=620, items=()):
    # top
    contact_shadow(cx, x, y + 110, w * 0.6, 28, 0.55)
    poly(cx, [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + 30, y + 70), (x - w / 2 - 30, y + 70)])
    lin(cx, 0, y, 0, y + 70, [(0, hx("#7a4f2e")), (1, hx("#a26a3e"))])
    cx.fill_preserve()
    ink(cx, 5)
    cx.rectangle(x - w / 2 - 30, y + 70, w + 60, 26)
    src(cx, hx("#5a381f"))
    cx.fill_preserve()
    ink(cx, 5)
    for sx in (-1, 1):
        cx.rectangle(x + sx * (w / 2 - 10) - 16, y + 96, 32, 70)
        src(cx, hx("#4a2e19"))
        cx.fill_preserve()
        ink(cx, 4)
    # sheen
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    poly(cx, [(x - 60, y + 4), (x + 120, y + 4), (x + 90, y + 66), (x - 110, y + 66)])
    src(cx, (1, 0.85, 0.6, 0.07))
    cx.fill()
    cx.restore()


def cash_stack(cx, x, y, n=5, a=1.0):
    for k in range(n):
        cx.save()
        cx.translate(x + (k % 2) * 6 - 3, y - k * 6)
        cx.rotate(0.04 * ((k * 7) % 5 - 2))
        poly(cx, [(-70, -16), (70, -16), (80, 16), (-80, 16)])
        lin(cx, -70, 0, 80, 0, [(0, alpha(hx("#e9dcc0"), a)), (1, alpha(hx("#cdb98f"), a))])
        cx.fill_preserve()
        ink(cx, 2.5, alpha(INK, a))
        ellipse(cx, 40, 0, 14, 10)
        src(cx, alpha(hx("#b9a479"), a))
        cx.fill()
        cx.rectangle(-55, -6, 60, 4)
        src(cx, alpha(hx("#a08a5c"), a))
        cx.fill()
        cx.restore()


def tea_cup(cx, x, y, t=0.0, steam=1.0):
    contact_shadow(cx, x, y + 4, 34, 8, 0.4)
    poly(cx, [(x - 26, y - 56), (x + 26, y - 56), (x + 20, y), (x - 20, y)])
    lin(cx, x - 26, 0, x + 26, 0, [(0, hx("#d8d3c8")), (0.4, hx("#f4f1ea")), (1, hx("#a9a499"))])
    cx.fill_preserve()
    ink(cx, 3.5)
    ellipse(cx, x, y - 56, 26, 6)
    src(cx, hx("#7a8a4a"))
    cx.fill_preserve()
    ink(cx, 3)
    if steam > 0:
        for k in range(3):
            ph = (t * 0.35 + k / 3) % 1.0
            cx.new_path()
            yy = y - 70 - ph * 140
            xx = x + math.sin(ph * 6 + k) * 12
            ellipse(cx, xx, yy, 14 + ph * 26, 10 + ph * 18)
            src(cx, (1, 1, 1, steam * 0.16 * math.sin(ph * math.pi)))
            cx.fill()


def papers(cx, x, y, n=3, seed=4):
    rng = random.Random(seed)
    for k in range(n):
        cx.save()
        cx.translate(x + rng.uniform(-40, 40), y + rng.uniform(-10, 10))
        cx.rotate(rng.uniform(-0.3, 0.3))
        poly(cx, [(-50, -30), (50, -30), (56, 30), (-56, 30)])
        src(cx, hx("#f1ece0"))
        cx.fill_preserve()
        ink(cx, 2.5)
        for j in range(3):
            cx.rectangle(-36, -16 + j * 12, 60 - j * 10, 4)
            src(cx, hx("#b8b0a0"))
            cx.fill()
        cx.restore()


def pendant_lamp(cx, x, y, on=1.0):
    cx.move_to(x, 0)
    cx.line_to(x, y - 60)
    src(cx, INK)
    cx.set_line_width(4)
    cx.stroke()
    poly(cx, [(x - 30, y - 60), (x + 30, y - 60), (x + 90, y), (x - 90, y)])
    lin(cx, 0, y - 60, 0, y, [(0, hx("#e9d9b0")), (1, hx("#c9a96a"))])
    cx.fill_preserve()
    ink(cx, 4)
    ellipse(cx, x, y + 6, 22, 14)
    src(cx, mixc(hx("#6b5a3a"), hx("#fff3c4"), on))
    cx.fill()
    if on > 0:
        glow(cx, x, y + 10, 380, WARM, 0.33 * on)
        light_cone(cx, x, y, 180, 900, 1200, WARM, 0.10 * on)


def box(cx, x, y, w, h, taped=True, label=None, flap=0.0):
    """Cardboard box, 3/4 view; (x, y) bottom-centre."""
    d = w * 0.28
    contact_shadow(cx, x + d * 0.3, y + 4, w * 0.62, 12, 0.45)
    # front
    cx.rectangle(x - w / 2, y - h, w, h)
    lin(cx, x - w / 2, 0, x + w / 2, 0, [(0, hx("#c79a5d")), (1, hx("#b0844a"))])
    cx.fill_preserve()
    ink(cx, 4)
    # side
    poly(cx, [(x + w / 2, y - h), (x + w / 2 + d, y - h - d * 0.55), (x + w / 2 + d, y - d * 0.55), (x + w / 2, y)])
    src(cx, hx("#8f6a3a"))
    cx.fill_preserve()
    ink(cx, 4)
    # top
    poly(cx, [(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 + d, y - h - d * 0.55), (x - w / 2 + d, y - h - d * 0.55)])
    src(cx, hx("#d9ac6c"))
    cx.fill_preserve()
    ink(cx, 4)
    if taped:
        poly(cx, [(x - 9, y - h), (x + 9, y - h), (x + 9 + d, y - h - d * 0.55), (x - 9 + d, y - h - d * 0.55)])
        src(cx, hx("#e8d3a5"))
        cx.fill()
        cx.rectangle(x - 9, y - h, 18, h * 0.3)
        cx.fill()
    if label:
        rrect(cx, x - w * 0.36, y - h * 0.62, w * 0.72, h * 0.34, 4)
        src(cx, hx("#f6f1e4"))
        cx.fill_preserve()
        ink(cx, 2.5)
        text(cx, label, x, y - h * 0.38, h * 0.16, INK, font=FONT)


# ---------------------------------------------------------------- night street
def street_static(cx, dawn=0.0):
    lin(cx, 0, 0, 0, 900, [(0, hx("#070b1f")), (1, hx("#1a2350"))])
    cx.rectangle(0, 0, W, 1000)
    cx.fill()
    skyline(cx, 0, 520, W, 380, seed=11, lit=0.35)
    # moon
    glow(cx, 820, 230, 220, hx("#9fb8ff"), 0.25)
    cx.arc(820, 230, 46, 0, 2 * math.pi)
    src(cx, hx("#e8eeff"))
    cx.fill()
    # left building (apartment block) with doorway
    poly(cx, [(0, 300), (380, 420), (380, 1330), (0, 1440)])
    lin(cx, 0, 0, 380, 0, [(0, hx("#2b3150")), (1, hx("#394069"))])
    cx.fill()
    for row in range(6):
        for col in range(2):
            x0 = 60 + col * 150
            y0 = 420 + row * 140 + col * 30
            poly(cx, [(x0, y0), (x0 + 100, y0 + 22), (x0 + 100, y0 + 92), (x0, y0 + 74)])
            lit_ = (row * 3 + col) % 5 == 1
            src(cx, hx("#ffcf7a") if lit_ else hx("#1b2038"))
            cx.fill()
            if lit_:
                glow(cx, x0 + 50, y0 + 50, 110, WARM, 0.18)
    # entrance light
    glow(cx, 330, 1180, 160, WARM, 0.25)
    rrect(cx, 300, 1120, 60, 190, 4)
    src(cx, hx("#ffd99a"))
    cx.fill()
    # right houses
    poly(cx, [(1080, 520), (760, 640), (760, 1300), (1080, 1400)])
    lin(cx, 760, 0, 1080, 0, [(0, hx("#363c63")), (1, hx("#262b4a"))])
    cx.fill()
    poly(cx, [(1100, 470), (740, 620), (760, 660), (1100, 530)])
    src(cx, hx("#1b1f38"))
    cx.fill()
    # road
    poly(cx, [(380, 1330), (760, 1300), (1080, 1420), (1080, H), (0, H), (0, 1440)])
    lin(cx, 0, 1300, 0, H, [(0, hx("#1c2140")), (1, hx("#0d1026"))])
    cx.fill()
    # wet reflections
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    for (rx, col, a) in ((330, WARM, 0.12), (820, hx("#9fb8ff"), 0.08), (600, hx("#7fd6ff"), 0.05)):
        lin(cx, 0, 1350, 0, H, [(0, alpha(col, a)), (1, alpha(col, 0))])
        poly(cx, [(rx - 30, 1350), (rx + 30, 1350), (rx + 80, H), (rx - 80, H)])
        cx.fill()
    cx.restore()
    # utility poles + wires
    for px, top, bot, wdt in ((180, 200, 1500, 26), (900, 440, 1340, 16)):
        cx.rectangle(px - wdt / 2, top, wdt, bot - top)
        lin(cx, px - wdt / 2, 0, px + wdt / 2, 0, [(0, hx("#2c2a35")), (1, hx("#141219"))])
        cx.fill()
        cx.rectangle(px - wdt * 3, top + 40, wdt * 6, wdt * 0.5)
        src(cx, hx("#141219"))
        cx.fill()
    for k in range(4):
        cx.move_to(0, 240 + k * 22)
        cx.curve_to(400, 330 + k * 22, 700, 430 + k * 18, 1080, 470 + k * 16)
        src(cx, (0.05, 0.05, 0.08, 0.9))
        cx.set_line_width(3)
        cx.stroke()
    # street lamp
    cx.rectangle(890, 700, 12, 640)
    src(cx, hx("#16141c"))
    cx.fill()
    glow(cx, 870, 700, 260, hx("#bfe0ff"), 0.30)
    light_cone(cx, 870, 700, 40, 520, 680, hx("#bfe0ff"), 0.10)
    # curb lines
    cx.move_to(0, 1440)
    cx.line_to(380, 1330)
    cx.line_to(760, 1300)
    cx.line_to(1080, 1420)
    src(cx, (1, 1, 1, 0.12))
    cx.set_line_width(5)
    cx.stroke()


def van(cx, x, y, s=1.0, lights=0.0, t=0.0, dawn=0.0):
    """Dark unmarked box van, 3/4 front view facing left-ish. (x, y) = ground centre."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    contact_shadow(cx, 0, 0, 260, 34, 0.7)
    body = hx("#262a33")
    # cargo box side (right/back)
    poly(cx, [(-60, -380), (230, -330), (230, -40), (-60, -50)])
    lin(cx, -60, 0, 230, 0, [(0, shade(body, 0.12)), (1, shade(body, -0.25))])
    cx.fill_preserve()
    ink(cx, 6)
    # cab front
    poly(cx, [(-240, -250), (-60, -380), (-60, -50), (-240, -40)])
    lin(cx, -240, 0, -60, 0, [(0, shade(body, 0.05)), (1, shade(body, 0.22))])
    cx.fill_preserve()
    ink(cx, 6)
    # windshield
    poly(cx, [(-228, -240), (-72, -350), (-72, -230), (-228, -160)])
    lin(cx, -228, -350, -72, -160, [(0, hx("#4c5a7a")), (1, hx("#151a2a"))])
    cx.fill_preserve()
    ink(cx, 4)
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    poly(cx, [(-200, -250), (-170, -272), (-110, -200), (-140, -186)])
    src(cx, (0.6, 0.7, 1.0, 0.10 + dawn * 0.1))
    cx.fill()
    cx.restore()
    # grille + bumper
    poly(cx, [(-236, -120), (-64, -150), (-64, -90), (-236, -70)])
    src(cx, hx("#16181d"))
    cx.fill_preserve()
    ink(cx, 4)
    # headlights
    for hxp, hyp in ((-215, -112), (-95, -134)):
        ellipse(cx, hxp, hyp, 20, 12)
        src(cx, mixc(hx("#4a4f5a"), hx("#fff6d8"), lights))
        cx.fill_preserve()
        ink(cx, 3)
        if lights > 0:
            glow(cx, hxp, hyp, 130, hx("#fff1c8"), 0.55 * lights)
    if lights > 0:
        cx.save()
        cx.set_operator(cairo.OPERATOR_ADD)
        lin(cx, -150, -120, -700, 60, [(0, alpha(hx("#fff1c8"), 0.25 * lights)), (1, alpha(hx("#fff1c8"), 0))])
        poly(cx, [(-120, -150), (-240, -80), (-800, 120), (-600, -260)])
        cx.fill()
        cx.restore()
    # wheels
    for wx_, wy_, r in ((-170, -30, 44), (150, -30, 46)):
        cx.arc(wx_, wy_, r, 0, 2 * math.pi)
        src(cx, hx("#0d0d10"))
        cx.fill_preserve()
        ink(cx, 4)
        cx.arc(wx_, wy_, r * 0.45, 0, 2 * math.pi)
        src(cx, hx("#5a5d66"))
        cx.fill()
        a = t * 6
        for k in range(4):
            cx.move_to(wx_, wy_)
            cx.line_to(wx_ + math.cos(a + k * 1.57) * r * 0.42, wy_ + math.sin(a + k * 1.57) * r * 0.42)
        src(cx, hx("#2a2c31"))
        cx.set_line_width(4)
        cx.stroke()
    # side rim light
    cx.move_to(-60, -380)
    cx.line_to(230, -330)
    src(cx, (0.7, 0.8, 1.0, 0.35))
    cx.set_line_width(4)
    cx.stroke()
    cx.restore()


# ---------------------------------------------------------------- phone
def phone(cx, x, y, w, h, screen_fn, tilt=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(tilt)
    # shadow
    cx.save()
    cx.translate(18, 30)
    rrect(cx, -w / 2, -h / 2, w, h, w * 0.14)
    src(cx, (0, 0, 0, 0.45))
    cx.fill()
    cx.restore()
    rrect(cx, -w / 2 - 8, -h / 2 - 8, w + 16, h + 16, w * 0.15)
    lin(cx, -w / 2, 0, w / 2, 0, [(0, hx("#4a4d57")), (0.08, hx("#15161b")), (0.92, hx("#15161b")),
                                   (1, hx("#3a3d46"))])
    cx.fill()
    rrect(cx, -w / 2 + 6, -h / 2 + 6, w - 12, h - 12, w * 0.12)
    cx.save()
    cx.clip()
    cx.translate(-w / 2 + 6, -h / 2 + 6)
    screen_fn(cx, w - 12, h - 12)
    cx.restore()
    # dynamic island
    rrect(cx, -w * 0.15, -h / 2 + 22, w * 0.3, 30, 15)
    src(cx, hx("#050507"))
    cx.fill()
    # glass sheen
    cx.save()
    rrect(cx, -w / 2 + 6, -h / 2 + 6, w - 12, h - 12, w * 0.12)
    cx.clip()
    cx.set_operator(cairo.OPERATOR_ADD)
    poly(cx, [(-w / 2, -h / 2), (-w * 0.05, -h / 2), (-w * 0.55, h / 2), (-w / 2, h / 2)])
    src(cx, (1, 1, 1, 0.04))
    cx.fill()
    cx.restore()
    cx.restore()


def status_bar(cx, w, t, signal=True, time_s="23:58"):
    text(cx, time_s, 60, 70, 26, (1, 1, 1, 0.95), anchor="l")
    if signal:
        for k in range(4):
            cx.rectangle(w - 150 + k * 11, 66 - k * 6, 7, 6 + k * 6)
            src(cx, (1, 1, 1, 0.95))
            cx.fill()
    else:
        text(cx, "NO SIGNAL", w - 60, 70, 20, (1, 1, 1, 0.85), anchor="r")
    if signal:
        rrect(cx, w - 92, 52, 40, 20, 5)
        src(cx, (1, 1, 1, 0.9))
        cx.set_line_width(2)
        cx.stroke()
        cx.rectangle(w - 88, 56, 26, 12)
        cx.fill()


# ---------------------------------------------------------------- Japan map (lon, lat)
HOKKAIDO = [(141.9, 45.5), (142.6, 45.0), (143.6, 44.2), (144.8, 43.9), (145.6, 43.4), (145.2, 43.1),
            (144.0, 42.9), (143.3, 42.0), (142.0, 42.5), (141.0, 42.3), (140.4, 41.5), (139.9, 41.6),
            (140.2, 42.3), (139.8, 42.6), (140.4, 43.3), (141.4, 43.3), (141.6, 44.3), (141.7, 45.4)]
HONSHU = [(140.9, 41.5), (141.5, 41.4), (141.4, 40.6), (142.0, 39.6), (141.9, 38.9), (141.5, 38.3),
          (141.0, 38.0), (141.0, 37.0), (140.6, 36.3), (140.8, 35.7), (140.3, 35.1), (139.8, 35.0),
          (139.9, 35.6), (139.7, 35.4), (139.2, 35.2), (139.0, 34.7), (138.8, 34.6), (138.5, 35.0),
          (137.6, 34.6), (136.9, 34.6), (136.8, 34.3), (136.3, 34.2), (135.8, 33.5), (135.1, 33.9),
          (135.4, 34.6), (134.7, 34.8), (133.5, 34.5), (132.5, 34.3), (131.9, 33.9), (130.9, 34.0),
          (131.4, 34.4), (132.3, 35.3), (133.3, 35.5), (134.5, 35.6), (135.7, 35.5), (136.0, 35.9),
          (136.7, 36.7), (137.0, 37.0), (136.8, 37.4), (137.3, 37.5), (137.3, 36.8), (138.3, 37.1),
          (139.0, 37.9), (139.6, 38.5), (140.0, 39.6), (139.9, 40.6), (140.3, 41.2)]
SHIKOKU = [(132.4, 33.0), (132.9, 32.7), (133.3, 33.4), (134.2, 33.2), (134.7, 33.8), (134.6, 34.2),
           (133.6, 34.4), (132.9, 34.1), (132.0, 33.6)]
KYUSHU = [(130.9, 33.9), (131.6, 33.6), (131.9, 33.1), (131.4, 31.5), (130.7, 31.0), (130.2, 31.3),
          (130.3, 32.0), (130.0, 32.5), (129.6, 33.1), (129.8, 33.4), (130.4, 33.6)]
ISLANDS = [HOKKAIDO, HONSHU, SHIKOKU, KYUSHU]


def map_xy(lon, lat, cxm=540, cym=760, sc=58):
    return (cxm + (lon - 137.5) * sc * 0.83, cym - (lat - 38.0) * sc)


def japan_map(cx, cxm=540, cym=760, sc=58, fill=hx("#efe6cf"), line=INK, lw=4):
    for isl in ISLANDS:
        pts = [map_xy(lo, la, cxm, cym, sc) for lo, la in isl]
        cx.move_to(*pts[0])
        for p in pts[1:]:
            cx.line_to(*p)
        cx.close_path()
    src(cx, fill)
    cx.fill_preserve()
    src(cx, line)
    cx.set_line_width(lw)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()


def point_in_poly(x, y, pts):
    ins = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def map_dots(n=140, seed=5):
    rng = random.Random(seed)
    out = []
    weights = [0.12, 0.66, 0.08, 0.14]
    while len(out) < n:
        isl = rng.choices(range(4), weights)[0]
        pts = ISLANDS[isl]
        lo = rng.uniform(min(p[0] for p in pts), max(p[0] for p in pts))
        la = rng.uniform(min(p[1] for p in pts), max(p[1] for p in pts))
        if point_in_poly(lo, la, pts):
            out.append((lo, la, rng.random(), rng.random()))
    return out

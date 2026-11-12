"""Props. All functions draw in the current (world) coordinate space."""
import math
import random

import cairo

from .core import (OUTLINE, circle, clamp, curve, ellipse, fs, hexc, line, mix, poly, rgrad, rrect,
                   shade, smooth, smooth_poly, src, text, vgrad)


# ------------------------------------------------------------------ phone
def phone(cx, x, y, s=1.0, rot=0.0, screen="off", battery=3, glow=0.0, t=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -16, -28, 32, 56, 7)
    fs(cx, hexc("#1E1F26"), OUTLINE, 3)
    if screen == "off":
        rrect(cx, -12, -23, 24, 44, 3)
        fs(cx, hexc("#2C2E38"), None, 0)
    else:
        rrect(cx, -12, -23, 24, 44, 3)
        fs(cx, hexc("#9FD8FF") if screen != "red" else hexc("#FF9C9C"), None, 0)
        if screen == "battery":
            rrect(cx, -8, -4, 14, 8, 1.5)
            fs(cx, None, OUTLINE, 1.6)
            w = 12 * clamp(battery / 100)
            cx.rectangle(-7, -3, max(w, 1), 6)
            src(cx, hexc("#E04848") if battery < 10 else hexc("#3CB371"))
            cx.fill()
    if glow > 0:
        # flashlight LED at top
        circle(cx, 0, -24, 3)
        fs(cx, (1, 1, 0.9, glow), None, 0)
    cx.restore()


def flash_beam(cx, x, y, ang, length=900, spread=0.32, alpha=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    g = cairo.LinearGradient(0, 0, length, 0)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.75 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 0.85, 0.0)
    cx.move_to(0, 0)
    cx.line_to(length, -length * spread)
    cx.line_to(length, length * spread)
    cx.close_path()
    cx.set_source(g)
    cx.fill()
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 60)
    g.add_color_stop_rgba(0, 1, 1, 0.9, 0.9 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 0.9, 0)
    cx.set_source(g)
    circle(cx, 0, 0, 60)
    cx.fill()
    cx.restore()


# ------------------------------------------------------------------ watch
def watch(cx, x, y, s=1.0, rot=0.0, display="", lcd_glow=0.0, button=0.0, label=True, strap=True):
    """Cheap chunky digital watch. (x,y) = centre of face."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    if strap:
        rrect(cx, -34, -78, 68, 156, 12)
        fs(cx, hexc("#2A2A30"), OUTLINE, 4)
        for k in (-60, -46, 46, 60):
            line(cx, [(-26, k), (26, k)], hexc("#3D3D45"), 3)
    rrect(cx, -62, -50, 124, 100, 22)
    fs(cx, hexc("#B9BEC6"), OUTLINE, 5)
    rrect(cx, -54, -42, 108, 84, 16)
    fs(cx, hexc("#8F959E"), OUTLINE, 3)
    # lcd
    rrect(cx, -44, -26, 88, 44, 6)
    lcd = mix(hexc("#9DB89A"), hexc("#C8FFB4"), lcd_glow)
    fs(cx, lcd, OUTLINE, 3)
    if display:
        size = 30 if len(display) <= 5 else max(12, 150 / len(display))
        text(cx, display, 0, 8 + size * 0.0, size, hexc("#1F2A1E"))
    # red button
    by = 2 * button
    rrect(cx, 60, -12 + by * 0, 12 - 4 * button, 22, 4)
    fs(cx, hexc("#E23B3B"), OUTLINE, 3)
    if label:
        text(cx, "TIME TRAVEL DEVICE", 0, -31, 7.5, hexc("#2A2A30"))
    cx.restore()


def wrist_watch_small(cx, x, y, s=1.0, rot=0.0, blink=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -11, -9, 22, 18, 5)
    fs(cx, hexc("#B9BEC6"), OUTLINE, 3)
    rrect(cx, -7, -5, 14, 9, 2)
    fs(cx, mix(hexc("#9DB89A"), hexc("#D4FFB0"), blink), None, 0)
    circle(cx, 12, 0, 3)
    fs(cx, hexc("#E23B3B"), OUTLINE, 1.5)
    cx.restore()


# ------------------------------------------------------------------ box
def product_box(cx, x, y, s=1.0, open_=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # body
    rrect(cx, -110, -90, 220, 90, 6)
    fs(cx, hexc("#E9D7B6"), OUTLINE, 5)
    # flaps
    for side in (-1, 1):
        a = -side * (0.2 + 1.9 * open_)
        cx.save()
        cx.translate(side * 110, -90)
        cx.rotate(a)
        rrect(cx, -110 if side > 0 else 0, -10, 110, 12, 3)
        fs(cx, hexc("#DCC69E"), OUTLINE, 4)
        cx.restore()
    text(cx, "TIME MACHINE", 0, -52, 22, hexc("#C0392B"))
    text(cx, "ONLY $12!", 0, -24, 18, OUTLINE)
    # cheap star sticker
    star(cx, 82, -22, 18, hexc("#FFC857"))
    cx.restore()


def star(cx, x, y, r, c, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(cx, pts)
    fs(cx, c, OUTLINE, 3)


# ------------------------------------------------------------------ food
def bread(cx, x, y, s=1.0, rot=0.0, bite=False):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 34, 22)
    fs(cx, hexc("#D99A4E"), OUTLINE, 4)
    for k in (-14, 0, 14):
        line(cx, [(k - 6, -12), (k + 6, -2)], hexc("#B87634"), 4)
    if bite:
        circle(cx, 30, -6, 12)
        fs(cx, hexc("#F4D9A6"), OUTLINE, 3)
    cx.restore()


def round_loaf(cx, x, y, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # Roman panis quadratus: round loaf scored into 8 wedges
    ellipse(cx, 0, 0, 30, 20)
    fs(cx, hexc("#C98A45"), OUTLINE, 4)
    for k in range(4):
        a = k * math.pi / 4
        line(cx, [(-math.cos(a) * 22, -math.sin(a) * 13), (math.cos(a) * 22, math.sin(a) * 13)],
             hexc("#9E6A30"), 3)
    cx.restore()


def apple(cx, x, y, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(0, -14)
    cx.curve_to(10, -24, 26, -14, 22, 4)
    cx.curve_to(18, 20, 6, 24, 0, 18)
    cx.curve_to(-6, 24, -18, 20, -22, 4)
    cx.curve_to(-26, -14, -10, -24, 0, -14)
    cx.close_path()
    fs(cx, hexc("#D93A3A"), OUTLINE, 4)
    line(cx, [(0, -14), (3, -26)], hexc("#5B3A1E"), 4)
    ellipse(cx, 10, -26, 9, 4.5, -0.4)
    fs(cx, hexc("#5DAA4A"), OUTLINE, 2.5)
    ellipse(cx, -10, -4, 4, 7, 0.4)
    fs(cx, (1, 1, 1, 0.5), None, 0)
    cx.restore()


def flatbread(cx, x, y, s=1.0, bite=0.0, steam=0.0, t=0.0):
    """The 'pizza': dough, cheese, olives in a smiley face. No tomatoes."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 92, 30)
    fs(cx, hexc("#E3B46A"), OUTLINE, 5)
    ellipse(cx, 0, -2, 78, 23)
    fs(cx, hexc("#F6E7B0"), None, 0)
    # olive smiley
    for ox in (-26, 26):
        ellipse(cx, ox, -8, 9, 6)
        fs(cx, hexc("#2E3A2A"), OUTLINE, 2.5)
    for k in range(5):
        a = math.pi * (0.15 + k * 0.175)
        ellipse(cx, math.cos(a) * 40, 2 + math.sin(a) * 12, 7, 5)
        fs(cx, hexc("#2E3A2A"), OUTLINE, 2.5)
    if bite > 0:
        # bite out of the right edge
        cx.set_operator(cairo.OPERATOR_CLEAR)
        circle(cx, 92, -4, 22 * bite)
        cx.fill()
        cx.set_operator(cairo.OPERATOR_OVER)
    if steam > 0:
        for k in (-30, 0, 30):
            ph = t * 2 + k
            curve(cx, (k, -30), (k - 10, -50 + math.sin(ph) * 4), (k + 10, -70), (k, -90),
                  (1, 1, 1, 0.6 * steam), 5)
    cx.restore()


def plate(cx, x, y, s=1.0, dirty=0.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 40, 12)
    fs(cx, hexc("#C77B4E"), OUTLINE, 4)
    ellipse(cx, 0, -2, 26, 6)
    fs(cx, hexc("#D9925F"), None, 0)
    if dirty > 0:
        for k in range(4):
            ellipse(cx, -18 + k * 12, -1 + (k % 2) * 3, 5, 2.5)
            fs(cx, (0.45, 0.3, 0.18, dirty), None, 0)
    cx.restore()


def dish_stack(cx, x, y, n=8, s=1.0, wobble=0.0, t=0.0):
    for i in range(n):
        dx = math.sin(t * 7 + i) * wobble * i * 1.5
        plate(cx, x + dx, y - i * 11 * s, s, dirty=1.0)


def tray(cx, x, y, s=1.0, rot=0.0, shine=0.0, tilt=1.0):
    """Polished metal serving tray seen as an ellipse; tilt 1 = face-on."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s * max(0.15, tilt))
    circle(cx, 0, 0, 52)
    fs(cx, hexc("#D9C27A"), OUTLINE, 5)
    circle(cx, 0, 0, 40)
    g = cairo.LinearGradient(-40, -40, 40, 40)
    g.add_color_stop_rgba(0, 1, 0.97, 0.85, 1)
    g.add_color_stop_rgba(0.5, 0.88, 0.76, 0.42, 1)
    g.add_color_stop_rgba(1, 1, 0.95, 0.75, 1)
    cx.set_source(g)
    cx.fill()
    if shine > 0:
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 90)
        g.add_color_stop_rgba(0, 1, 1, 0.9, 0.9 * shine)
        g.add_color_stop_rgba(1, 1, 1, 0.9, 0)
        cx.set_source(g)
        circle(cx, 0, 0, 90)
        cx.fill()
    cx.restore()


def sun_ray(cx, x0, y0, x1, y1, alpha=1.0, w=40):
    cx.save()
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0)
    cx.translate(x0, y0)
    cx.rotate(ang)
    g = cairo.LinearGradient(0, 0, L, 0)
    g.add_color_stop_rgba(0, 1, 1, 0.8, 0.85 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 0.8, 0.5 * alpha)
    cx.set_source(g)
    cx.move_to(0, -w * 0.3)
    cx.line_to(L, -w)
    cx.line_to(L, w)
    cx.line_to(0, w * 0.3)
    cx.close_path()
    cx.fill()
    cx.restore()
    g = cairo.RadialGradient(x1, y1, 0, x1, y1, w * 2.5)
    g.add_color_stop_rgba(0, 1, 1, 0.9, alpha)
    g.add_color_stop_rgba(1, 1, 1, 0.9, 0)
    cx.set_source(g)
    circle(cx, x1, y1, w * 2.5)
    cx.fill()


def bucket(cx, x, y, s=1.0, rot=0.0, water=True, handle=True):
    """(x,y) = centre of bucket mouth."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    if handle:
        cx.arc(0, 0, 44, math.pi, 2 * math.pi)
        src(cx, OUTLINE)
        cx.set_line_width(4)
        cx.stroke()
    cx.move_to(-46, 0)
    cx.line_to(-36, 80)
    cx.curve_to(-20, 86, 20, 86, 36, 80)
    cx.line_to(46, 0)
    cx.close_path()
    fs(cx, hexc("#9C6B3F"), OUTLINE, 5)
    for yy in (18, 60):
        line(cx, [(-44 + yy * 0.12, yy), (44 - yy * 0.12, yy)], hexc("#5E5E66"), 6)
    for xx in (-20, 0, 20):
        line(cx, [(xx, 4), (xx * 0.85, 78)], shade(hexc("#9C6B3F"), -0.25), 2.5)
    ellipse(cx, 0, 0, 46, 11)
    fs(cx, hexc("#3E8BD0") if water else hexc("#4A3220"), OUTLINE, 4)
    cx.restore()


def water_splash(cx, x, y, t, s=1.0, alpha=1.0, seed=3):
    """Burst of drops. t: seconds since impact."""
    if t < 0 or t > 1.4:
        return
    r = random.Random(seed)
    for i in range(26):
        a = -math.pi * (0.1 + 0.8 * r.random())
        v = 380 + 420 * r.random()
        dx = math.cos(a) * v * t
        dy = math.sin(a) * v * t + 900 * t * t
        rad = (6 + 8 * r.random()) * (1 - t / 1.4)
        ellipse(cx, x + dx * s, y + dy * s, rad, rad * 1.3)
        fs(cx, (0.55, 0.8, 1.0, alpha * (1 - t / 1.4)), (0.15, 0.35, 0.6, alpha * (1 - t / 1.4)), 2)


def water_pour(cx, x, y0, y1, w, alpha=1.0, t=0.0):
    g = cairo.LinearGradient(x - w, 0, x + w, 0)
    g.add_color_stop_rgba(0, 0.45, 0.72, 0.95, 0.85 * alpha)
    g.add_color_stop_rgba(0.5, 0.75, 0.9, 1.0, 0.95 * alpha)
    g.add_color_stop_rgba(1, 0.45, 0.72, 0.95, 0.85 * alpha)
    cx.set_source(g)
    cx.move_to(x - w * 0.6, y0)
    for k in range(9):
        yy = y0 + (y1 - y0) * k / 8
        cx.line_to(x - w * (0.6 + 0.4 * k / 8) + math.sin(t * 20 + k) * 4, yy)
    for k in range(8, -1, -1):
        yy = y0 + (y1 - y0) * k / 8
        cx.line_to(x + w * (0.6 + 0.4 * k / 8) + math.sin(t * 22 + k * 1.3) * 4, yy)
    cx.close_path()
    cx.fill()


def drips(cx, x, y, w, t, n=8, alpha=1.0, seed=5):
    r = random.Random(seed)
    for i in range(n):
        px = x + (r.random() - 0.5) * w
        period = 0.6 + r.random() * 0.6
        ph = ((t + r.random() * period) % period) / period
        py = y + ph * 120
        ellipse(cx, px, py, 4, 6)
        fs(cx, (0.55, 0.8, 1.0, alpha * (1 - ph)), None, 0)


def rope(cx, pts, sag=0.0):
    cx.move_to(*pts[0])
    if len(pts) == 2 and sag:
        (x0, y0), (x1, y1) = pts
        cx.curve_to(x0 + (x1 - x0) * 0.33, y0 + sag, x0 + (x1 - x0) * 0.66, y1 + sag, x1, y1)
    else:
        for p in pts[1:]:
            cx.line_to(*p)
    src(cx, OUTLINE)
    cx.set_line_width(9)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    src(cx, hexc("#D8B57A"))
    cx.set_line_width(5)
    cx.stroke()


# ------------------------------------------------------------------ market goods
def basket(cx, x, y, s=1.0, fruit="apples", rot=0.0, seed=1):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    r = random.Random(seed)
    cols = {"apples": ["#D93A3A", "#E2533A", "#C92F2F"], "oranges": ["#F09A2B", "#F2A93B"],
            "grapes": ["#7B4B94", "#8E5BA8"], "lemons": ["#F4D03F", "#F7DC6F"],
            "figs": ["#6E3B5C", "#80456B"], "olives": ["#5B6B3A", "#2E3A2A"]}[fruit]
    for i in range(9):
        fx = -40 + (i % 5) * 20 + (6 if i >= 5 else 0)
        fy = -10 - (12 if i >= 5 else 0)
        circle(cx, fx, fy, 13 if fruit != "olives" and fruit != "grapes" else 9)
        fs(cx, hexc(r.choice(cols)), OUTLINE, 3)
    cx.move_to(-56, -8)
    cx.line_to(-46, 30)
    cx.line_to(46, 30)
    cx.line_to(56, -8)
    cx.close_path()
    fs(cx, hexc("#C8954E"), OUTLINE, 4)
    for k in range(1, 4):
        line(cx, [(-54 + k * 2, -8 + k * 9.5), (54 - k * 2, -8 + k * 9.5)], hexc("#A87634"), 2.5)
    cx.restore()


def amphora(cx, x, y, s=1.0, c="#C66B3D"):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-10, -120)
    cx.line_to(-12, -100)
    cx.curve_to(-46, -88, -40, -20, 0, 0)
    cx.curve_to(40, -20, 46, -88, 12, -100)
    cx.line_to(10, -120)
    cx.close_path()
    fs(cx, hexc(c), OUTLINE, 4)
    for sx in (-1, 1):
        curve(cx, (sx * 10, -114), (sx * 34, -116), (sx * 34, -96), (sx * 22, -88), OUTLINE, 4)
    line(cx, [(-30, -60), (30, -60)], shade(hexc(c), -0.25), 4)
    cx.restore()


def crate(cx, x, y, w=110, h=70):
    rrect(cx, x - w / 2, y - h, w, h, 4)
    fs(cx, hexc("#B07A45"), OUTLINE, 4)
    line(cx, [(x - w / 2 + 4, y - h / 2), (x + w / 2 - 4, y - h / 2)], hexc("#8A5A2E"), 3)
    line(cx, [(x - w / 2 + 6, y - 6), (x + w / 2 - 6, y - h + 6)], hexc("#8A5A2E"), 3)


def fruit_cart(cx, x, y, s=1.0, rot=0.0, wheel_rot=0.0, spill=0.0, seed=2):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.rotate(rot)
    rrect(cx, -120, -120, 240, 60, 8)
    fs(cx, hexc("#A8703E"), OUTLINE, 5)
    for k in (-60, 0, 60):
        line(cx, [(k, -116), (k, -64)], hexc("#7E5128"), 3)
    r = random.Random(seed)
    for i in range(int(14 * (1 - spill))):
        fx = -100 + (i % 7) * 33
        fy = -126 - (i // 7) * 20
        circle(cx, fx, fy, 15)
        fs(cx, hexc(r.choice(["#D93A3A", "#F09A2B", "#F4D03F", "#8CB369"])), OUTLINE, 3)
    line(cx, [(120, -90), (200, -70)], hexc("#7E5128"), 9)
    for wx in (-70, 70):
        cx.save()
        cx.translate(wx, -40)
        cx.rotate(wheel_rot)
        circle(cx, 0, 0, 38)
        fs(cx, hexc("#8A5A2E"), OUTLINE, 5)
        for k in range(4):
            a = k * math.pi / 4
            line(cx, [(-math.cos(a) * 34, -math.sin(a) * 34), (math.cos(a) * 34, math.sin(a) * 34)],
                 OUTLINE, 3.5)
        circle(cx, 0, 0, 8)
        fs(cx, hexc("#5E3A1E"), OUTLINE, 3)
        cx.restore()
    cx.restore()


def rolling_fruit(cx, x, y, r, c, rot=0.0):
    circle(cx, x, y, r)
    fs(cx, hexc(c), OUTLINE, 3)
    ellipse(cx, x - r * 0.3 * math.cos(rot), y - r * 0.4, r * 0.25, r * 0.15)
    fs(cx, (1, 1, 1, 0.5), None, 0)


def wash_tub(cx, x, y, s=1.0, splash=0.0, t=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-110, -80)
    cx.line_to(-96, 0)
    cx.line_to(96, 0)
    cx.line_to(110, -80)
    cx.close_path()
    fs(cx, hexc("#9A9188"), OUTLINE, 5)
    ellipse(cx, 0, -80, 110, 18)
    fs(cx, hexc("#7FB5E0"), OUTLINE, 4)
    for k in range(5):
        circle(cx, -60 + k * 30, -84 + math.sin(t * 3 + k) * 2, 9)
        fs(cx, (1, 1, 1, 0.85), (0.6, 0.75, 0.9, 1), 2)
    cx.restore()


def sign(cx, x, y, txt, w=420, h=90, rot=0.0, size=34, board="#E6C98F", ink="#5A2E1A"):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    rrect(cx, -w / 2, -h / 2, w, h, 10)
    fs(cx, hexc(board), OUTLINE, 5)
    rrect(cx, -w / 2 + 8, -h / 2 + 8, w - 16, h - 16, 6)
    fs(cx, None, shade(hexc(board), -0.25), 3)
    text(cx, txt, 0, size * 0.36, size, hexc(ink))
    cx.restore()


def table(cx, x, y, w=360, h=110, cloth="#C0563A"):
    rrect(cx, x - w / 2, y - h, w, 22, 5)
    fs(cx, hexc("#9C6B3F"), OUTLINE, 5)
    for lx in (x - w / 2 + 24, x + w / 2 - 24):
        line(cx, [(lx, y - h + 20), (lx, y)], OUTLINE, 12)
        line(cx, [(lx, y - h + 20), (lx, y)], hexc("#9C6B3F"), 6)
    cx.move_to(x - w / 2 + 10, y - h + 20)
    cx.line_to(x - w / 2 + 30, y - h + 70)
    cx.line_to(x + w / 2 - 30, y - h + 70)
    cx.line_to(x + w / 2 - 10, y - h + 20)
    cx.close_path()
    fs(cx, hexc(cloth), OUTLINE, 4)


# ------------------------------------------------------------------ pigeon
def pigeon(cx, x, y, s=1.0, f=1.0, t=0.0, flap=0.0, peck=0.0, coo=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f, s)
    bob = math.sin(t * 6) * 2 * (1 - flap)
    # tail
    poly(cx, [(-30, -16), (-58, -10), (-56, -2), (-28, -6)])
    fs(cx, hexc("#6F7782"), OUTLINE, 3)
    # body
    ellipse(cx, -4, -18, 32, 20)
    fs(cx, hexc("#9AA3AE"), OUTLINE, 3.5)
    # wing
    if flap > 0:
        a = math.sin(t * 40) * 0.9 * flap
        cx.save()
        cx.translate(-6, -26)
        cx.rotate(-0.6 - a)
        ellipse(cx, -20, 0, 30, 12)
        fs(cx, hexc("#7D8692"), OUTLINE, 3)
        cx.restore()
    else:
        ellipse(cx, -10, -18, 22, 12, 0.1)
        fs(cx, hexc("#7D8692"), OUTLINE, 3)
        line(cx, [(-22, -14), (-4, -12)], hexc("#5E6670"), 2.5)
    # neck + head
    hx, hy = 22 + peck * 8, -38 + bob + peck * 16
    ellipse(cx, 16, -30 + bob * 0.5, 12, 14)
    fs(cx, hexc("#6E9C8C"), None, 0)
    circle(cx, hx, hy, 13)
    fs(cx, hexc("#8A93A0"), OUTLINE, 3.5)
    circle(cx, hx + 4, hy - 3, 3.5)
    fs(cx, hexc("#E87D2B"), None, 0)
    circle(cx, hx + 4, hy - 3, 1.8)
    fs(cx, OUTLINE, None, 0)
    poly(cx, [(hx + 11, hy - 2), (hx + 22, hy + 2), (hx + 11, hy + 5)])
    fs(cx, hexc("#E3B04B"), OUTLINE, 2)
    # legs
    if flap < 0.5:
        for lx in (-8, 6):
            line(cx, [(lx, 0), (lx, 12)], hexc("#D9776A"), 3)
            line(cx, [(lx - 5, 12), (lx + 6, 12)], hexc("#D9776A"), 3)
    cx.restore()


# ------------------------------------------------------------------ sky stuff
def cloud(cx, x, y, s=1.0, c=(1, 1, 1, 1), outline=True):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.new_path()
    for (dx, dy, r) in [(-60, 0, 38), (-20, -24, 48), (30, -18, 42), (66, 2, 32), (0, 6, 44)]:
        cx.new_sub_path()
        cx.arc(dx, dy, r, 0, 2 * math.pi)
    src(cx, c)
    if outline:
        cx.fill_preserve()
        cx.set_line_width(0)
        cx.new_path()
    else:
        cx.fill()
    cx.restore()


def storm_cloud(cx, x, y, s=1.0, dark=1.0):
    cloud(cx, x, y, s, mix(hexc("#C9CED6"), hexc("#4F5663"), dark))
    cloud(cx, x + 30 * s, y + 18 * s, s * 0.8, mix(hexc("#B8BEC8"), hexc("#3D434F"), dark))


def raindrop(cx, x, y, s=1.0, alpha=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(0, -18)
    cx.curve_to(10, -2, 10, 8, 0, 8)
    cx.curve_to(-10, 8, -10, -2, 0, -18)
    cx.close_path()
    fs(cx, (0.55, 0.8, 1.0, alpha), (0.15, 0.3, 0.55, alpha), 3)
    cx.restore()


def rain(cx, t, x0, x1, y0, y1, density=1.0, alpha=1.0, wind=0.18, seed=7):
    r = random.Random(seed)
    n = int((x1 - x0) * (y1 - y0) / 9000 * density)
    src(cx, (0.82, 0.88, 1.0, 0.55 * alpha))
    cx.set_line_width(3)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    span = y1 - y0 + 200
    for i in range(n):
        px = x0 + r.random() * (x1 - x0)
        sp = 1500 + 500 * r.random()
        py = y0 - 100 + ((r.random() * span + t * sp) % span)
        px += (py - y0) * wind
        L = 34 + 18 * r.random()
        cx.move_to(px, py)
        cx.line_to(px - L * wind, py - L)
    cx.stroke()


def portal(cx, x, y, r, t, alpha=1.0):
    if r <= 1:
        return
    cx.save()
    g = cairo.RadialGradient(x, y, 0, x, y, r * 1.6)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.95 * alpha)
    g.add_color_stop_rgba(0.35, 0.55, 0.9, 1, 0.8 * alpha)
    g.add_color_stop_rgba(0.7, 0.45, 0.35, 1, 0.45 * alpha)
    g.add_color_stop_rgba(1, 0.4, 0.3, 1, 0)
    cx.set_source(g)
    circle(cx, x, y, r * 1.6)
    cx.fill()
    for k in range(7):
        rr = r * (0.25 + k * 0.12)
        a0 = t * (3 + k * 0.7) * (1 if k % 2 else -1) + k
        cx.new_path()
        cx.arc(x, y, rr, a0, a0 + math.pi * 1.2)
        src(cx, (1, 1, 1, 0.75 * alpha))
        cx.set_line_width(5)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    ellipse(cx, x, y, r, r)
    src(cx, (0.85, 0.95, 1, 0.55 * alpha))
    cx.set_line_width(8)
    cx.stroke()
    cx.restore()


def sparkles(cx, x, y, t, r=60, n=6, alpha=1.0, c=(1, 0.95, 0.6, 1), seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.random() * 2 * math.pi + t * 0.8
        d = r * (0.5 + 0.5 * rnd.random())
        tw = 0.5 + 0.5 * math.sin(t * 8 + i * 1.7)
        sx, sy = x + math.cos(a) * d, y + math.sin(a) * d
        sz = 8 + 6 * tw
        cx.move_to(sx, sy - sz)
        cx.line_to(sx + sz * 0.25, sy - sz * 0.25)
        cx.line_to(sx + sz, sy)
        cx.line_to(sx + sz * 0.25, sy + sz * 0.25)
        cx.line_to(sx, sy + sz)
        cx.line_to(sx - sz * 0.25, sy + sz * 0.25)
        cx.line_to(sx - sz, sy)
        cx.line_to(sx - sz * 0.25, sy - sz * 0.25)
        cx.close_path()
        src(cx, c, alpha * tw)
        cx.fill()


def speed_lines(cx, x0, y0, x1, y1, t, n=14, alpha=0.6, seed=3, dirx=-1):
    r = random.Random(seed)
    for i in range(n):
        y = y0 + r.random() * (y1 - y0)
        L = 120 + 200 * r.random()
        ph = (t * 3 + r.random()) % 1
        x = x0 + (x1 - x0) * ((ph if dirx > 0 else 1 - ph))
        line(cx, [(x, y), (x - dirx * L, y)], (1, 1, 1, alpha * math.sin(ph * math.pi)), 5)


def motion_puffs(cx, x, y, t, n=3, alpha=1.0, seed=2):
    r = random.Random(seed)
    for i in range(n):
        ph = ((t * 2.5 + i / n) % 1)
        px = x - ph * 60 - r.random() * 10
        py = y - 10 - r.random() * 20 - ph * 20
        circle(cx, px, py, 10 + ph * 18)
        fs(cx, (0.93, 0.88, 0.78, alpha * (1 - ph)), None, 0)


def impact_star(cx, x, y, r, alpha=1.0, c="#FFF4C2"):
    pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * 0.45
        a = i * math.pi / 8
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(cx, pts)
    fs(cx, hexc(c, alpha), (0.11, 0.11, 0.14, alpha), 4)


def anger_mark(cx, x, y, s=1.0, alpha=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    for a in range(4):
        cx.save()
        cx.rotate(a * math.pi / 2)
        curve(cx, (4, -16), (4, -6), (6, -4), (16, -4), (0.85, 0.15, 0.15, alpha), 5)
        cx.restore()
    cx.restore()


def exclaim(cx, x, y, s=1.0, alpha=1.0, mark="!"):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    if mark == "!":
        cx.move_to(-7, -46)
        cx.line_to(7, -46)
        cx.line_to(4, -8)
        cx.line_to(-4, -8)
        cx.close_path()
        fs(cx, (1, 0.85, 0.3, alpha), (0.11, 0.11, 0.14, alpha), 4)
        circle(cx, 0, 4, 6)
        fs(cx, (1, 0.85, 0.3, alpha), (0.11, 0.11, 0.14, alpha), 4)
    else:
        text(cx, mark, 0, 0, 60, (0.11, 0.11, 0.14, alpha))
    cx.restore()


def dizzy_stars(cx, x, y, t, r=50, alpha=1.0):
    for i in range(4):
        a = t * 5 + i * math.pi / 2
        star(cx, x + math.cos(a) * r, y + math.sin(a) * r * 0.35, 11, hexc("#FFC857", alpha))

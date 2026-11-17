"""Glowing line-art sets and UI pieces for the vertical short."""
import math

import cairo

from .look import (BLUE, GLOW_BLUE, GREY1, GREY2, GREY3, GREY4, H, INK, LINE, LINE_DIM, PANEL, PANEL2, W,
                   WHITE, ellipse, font, gcircle, gline, glow_blob, grect, hexc, rrect, src, text, text_w)


# ------------------------------------------------------------------ rooms
def room(f, back=(250, 520, 830, 1180), a=1.0, floor_lines=6, col=LINE_DIM, extend=900):
    """Box-room interior: back wall rect, edges to the corners, faint floor boards."""
    x0, y0, x1, y1 = back
    c = f.cx
    # wall tint
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(c, PANEL, 0.55 * a)
    c.fill()
    grect(f, x0, y0, x1 - x0, y1 - y0, 0, col, 2.4, a * 0.9, glow=0.35)
    vx, vy = (x0 + x1) / 2, (y0 + y1) / 2
    for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        dx, dy = px - vx, py - vy
        gline(f, [(px, py), (px + dx * extend / 100, py + dy * extend / 100)], col, 2.4, a * 0.9, glow=0.35)
    # floor boards converge to vanishing point
    for i in range(1, floor_lines):
        k = i / floor_lines
        bx = x0 + (x1 - x0) * k
        dx = bx - vx
        gline(f, [(bx, y1), (bx + dx * 9, y1 + (y1 - vy) * 9)], col, 1.4, a * 0.35, glow=0.0)


def window(f, x, y, w, h, a=1.0, light=0.0, col=LINE):
    grect(f, x, y, w, h, 6, col, 2.6, a, glow=0.5, fillc=hexc("#1e2330"), fill_a=0.9)
    if light > 0:
        glow_blob(f, x + w / 2, y + h / 2, max(w, h) * 0.9, hexc("#dfe8ff"), 0.35 * light * a)
        f.cx.rectangle(x + 4, y + 4, w - 8, h - 8)
        src(f.cx, hexc("#c9d6f0"), 0.18 * light * a)
        f.cx.fill()
    gline(f, [(x + w / 2, y), (x + w / 2, y + h)], col, 2.0, a * 0.8, glow=0.3)
    gline(f, [(x, y + h / 2), (x + w, y + h / 2)], col, 2.0, a * 0.8, glow=0.3)


def bed(f, x, y, w, a=1.0):
    """Bed seen from the side, top surface at y."""
    grect(f, x, y, w, 70, 18, LINE, 2.6, a, fillc=PANEL2)
    grect(f, x, y - 30, w * 0.95, 34, 16, LINE, 2.2, a, fillc=hexc("#2b2f39"))  # blanket
    grect(f, x - 30, y - 120, 30, 260, 8, LINE, 2.6, a, fillc=PANEL)                # headboard
    gline(f, [(x + 20, y + 70), (x + 20, y + 120)], LINE, 2.6, a)
    gline(f, [(x + w - 20, y + 70), (x + w - 20, y + 120)], LINE, 2.6, a)


def mirror(f, x, y, w, h, a=1.0, shine=1.0):
    """Bathroom mirror; returns inner rect for the reflection."""
    grect(f, x, y, w, h, 34, WHITE, 4.0, a, glow=0.9, fillc=hexc("#1a1f2a"), fill_a=0.95)
    grect(f, x + 16, y + 16, w - 32, h - 32, 24, LINE, 2.0, a * 0.7, glow=0.3)
    if shine:
        for k, (dx, ln) in enumerate(((0.14, 0.22), (0.22, 0.12))):
            gline(f, [(x + w * dx, y + h * (0.16 + k * 0.05)), (x + w * (dx + ln * 0.8), y + h * (0.06 + k * 0.05))],
                  WHITE, 3, a * 0.45 * shine, glow=0.4)
    return (x + 16, y + 16, w - 32, h - 32)


def sink(f, x, y, w, a=1.0):
    grect(f, x - w / 2, y, w, 46, 10, LINE, 2.6, a, fillc=PANEL2)
    gline(f, [(x, y), (x, y - 40), (x + 40, y - 40)], LINE, 3, a)


def door(f, x, y, w, h, openk=0.0, a=1.0, inside_light=0.0):
    """Front door frame at (x,y,w,h). openk 0..1 swings the leaf open (to the left)."""
    c = f.cx
    if inside_light > 0:
        c.rectangle(x, y, w, h)
        g = cairo.LinearGradient(0, y, 0, y + h)
        g.add_color_stop_rgba(0, 1, 0.97, 0.9, 0.10 * inside_light * a)
        g.add_color_stop_rgba(1, 1, 0.97, 0.9, 0.22 * inside_light * a)
        c.set_source(g)
        c.fill()
        glow_blob(f, x + w / 2, y + h * 0.45, w * 0.9, hexc("#fff3dc"), 0.22 * inside_light * a)
    grect(f, x - 18, y - 18, w + 36, h + 18, 4, LINE, 3.0, a, glow=0.5)
    # leaf in perspective
    lw = w * (1 - openk * 0.82)
    skew = openk * 60
    pts = [(x, y), (x + lw, y + skew * 0.4), (x + lw, y + h - skew * 0.4), (x, y + h)]
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.close_path()
    src(c, hexc("#20242d"), a)
    c.fill()
    gline(f, pts, LINE, 2.6, a, glow=0.5, close=True)
    if lw > 60:
        # panels + knob
        for (py, ph) in ((0.1, 0.35), (0.52, 0.38)):
            inset = 0.14
            q = [(x + lw * inset, y + h * py + skew * 0.4 * inset), (x + lw * (1 - inset), y + h * py + skew * 0.4 * (1 - inset)),
                 (x + lw * (1 - inset), y + h * (py + ph) - skew * 0.2), (x + lw * inset, y + h * (py + ph))]
            gline(f, q, LINE_DIM, 2.0, a, glow=0.2, close=True)
        gcircle(f, x + lw * 0.86, y + h * 0.52, 9, LINE, 2.4, a)
    # step
    grect(f, x - 50, y + h, w + 100, 26, 4, LINE_DIM, 2.0, a, glow=0.2, fillc=PANEL)


def wall_lamp(f, x, y, a=1.0, on=1.0):
    grect(f, x - 18, y, 36, 50, 8, LINE, 2.2, a)
    if on:
        glow_blob(f, x, y + 25, 160, hexc("#fff1d6"), 0.35 * on * a)


# ------------------------------------------------------------------ subway
def subway(f, t, a=1.0, sway=0.0):
    c = f.cx
    # car shell (perspective box)
    room(f, back=(300, 430, 780, 1010), a=a, floor_lines=5)
    # windows along the side walls (perspective strips)
    for side in (-1, 1):
        for i in range(3):
            k0 = 0.15 + i * 0.28
            k1 = k0 + 0.2
            def P(k, yy):
                bx = 300 if side < 0 else 780
                ox = 0 if side < 0 else W
                return (ox + (bx - ox) * (1 - (1 - k) ** 1.0) if False else bx + (ox - bx) * (1 - k), yy)
            x0 = P(k0, 0)[0]
            x1 = P(k1, 0)[0]
            yt0, yt1 = 430 + (1 - k0) * -280, 430 + (1 - k1) * -280
            yb0, yb1 = 720 + (1 - k0) * 40, 720 + (1 - k1) * 40
            q = [(x0, yt0 + 120), (x1, yt1 + 120), (x1, yb1 - 20), (x0, yb0 - 20)]
            c.move_to(*q[0])
            for p in q[1:]:
                c.line_to(*p)
            c.close_path()
            src(c, hexc("#1c2230"), a)
            c.fill()
            # passing tunnel lights
            ph = (t * 1.8 + i * 0.37 + (side + 1) * 0.2) % 1.0
            if ph < 0.25:
                src(c, hexc("#dfe8ff"), a * 0.25 * math.sin(ph / 0.25 * math.pi))
                c.move_to(*q[0])
                for p in q[1:]:
                    c.line_to(*p)
                c.close_path()
                c.fill()
            gline(f, q, LINE, 2.2, a, glow=0.4, close=True)
    # ceiling rails + straps
    for side in (-1, 1):
        gline(f, [(540 + side * 170, 430), (540 + side * 520, 60)], LINE_DIM, 3, a, glow=0.2)
    # route display
    grect(f, 420, 455, 240, 36, 6, LINE, 2, a, glow=0.4, fillc=hexc("#11141b"))
    text(f, "NEXT: CENTRAL", 540, 481, 18, hexc("#c9d6f0"), a * 0.9, glow=0.6)
    # poles
    for px in (360, 720):
        gline(f, [(px + sway * 4, 300), (px + sway * 4, 1500)], GREY2, 7, a, glow=0.3)


# ------------------------------------------------------------------ shops / office
def bakery(f, a=1.0):
    room(f, back=(170, 560, 910, 1120), a=a, floor_lines=6)
    # awning stripes on back wall + sign
    grect(f, 380, 470, 320, 60, 10, WHITE, 2.4, a, glow=0.5, fillc=hexc("#151820"))
    text(f, "BAKERY", 540, 513, 32, WHITE, a, glow=0.5)
    # shelves with bread
    for row, yy in enumerate((740, 830)):
        gline(f, [(220, yy), (860, yy)], LINE, 2.4, a)
        for i in range(6):
            bx = 260 + i * 105 + (row * 40)
            ellipse(f.cx, bx, yy - 22, 38, 20)
            src(f.cx, hexc("#9a9fab"), a)
            f.cx.fill_preserve()
            src(f.cx, INK, a)
            f.cx.set_line_width(3)
            f.cx.stroke()
            for k in (-1, 0, 1):
                gline(f, [(bx + k * 14 - 6, yy - 32), (bx + k * 14 + 6, yy - 14)], hexc("#6b707c"), 2.5, a, glow=0)


def counter(f, x, y, w, h=300, a=1.0):
    grect(f, x, y, w, h, 10, LINE, 3, a, glow=0.5, fillc=hexc("#1d2129"))
    gline(f, [(x, y + 26), (x + w, y + 26)], LINE_DIM, 2, a, glow=0.2)


def office(f, a=1.0):
    room(f, back=(200, 520, 880, 1100), a=a, floor_lines=6)
    for i in range(3):
        window(f, 250 + i * 215, 580, 150, 230, a * 0.45, light=0.15)


def desk(f, x, y, w, a=1.0, monitor=True, plant=False):
    grect(f, x, y, w, 30, 6, LINE, 3, a, glow=0.5, fillc=PANEL2)
    gline(f, [(x + 30, y + 30), (x + 30, y + 330)], LINE, 3, a)
    gline(f, [(x + w - 30, y + 30), (x + w - 30, y + 330)], LINE, 3, a)
    if monitor:
        mx = x + w * 0.62
        grect(f, mx - 120, y - 200, 240, 160, 10, LINE, 3, a, glow=0.6, fillc=hexc("#141820"))
        for i in range(5):
            gline(f, [(mx - 95, y - 175 + i * 24), (mx - 95 + (150 - (i * 37) % 80), y - 175 + i * 24)],
                  GREY2, 5, a * 0.8, glow=0.5)
        gline(f, [(mx, y - 40), (mx, y)], LINE, 4, a)
        gline(f, [(mx - 40, y - 2), (mx + 40, y - 2)], LINE, 4, a)
    if plant:
        px = x + 70
        grect(f, px - 26, y - 56, 52, 56, 8, LINE, 2.4, a, fillc=PANEL)
        for k in (-1, 0, 1):
            gline(f, [(px, y - 56), (px + k * 30, y - 130 + abs(k) * 20)], LINE, 2.4, a)


# ------------------------------------------------------------------ city
def city(f, t, a=1.0, nums=None, seed=7, rows=1.0, scroll=0.0):
    """Night skyline of buildings with lit windows. nums: draw tiny numbers in some windows."""
    import random
    rng = random.Random(seed)
    xs = 0
    while xs < W + 100:
        bw = rng.randint(150, 260)
        bh = rng.randint(700, 1500)
        x0 = xs - 40
        y0 = H - bh + scroll * (0.6 + rng.random() * 0.4)
        grect(f, x0, y0, bw, bh + 400, 4, LINE_DIM, 2.4, a, glow=0.3, fillc=hexc("#11141a"))
        cols = max(2, (bw - 30) // 46)
        for r in range(int(bh / 70)):
            for k in range(cols):
                wx = x0 + 20 + k * 46
                wy = y0 + 30 + r * 70
                if wy > H + 40:
                    continue
                on = rng.random() < 0.42
                flick = 0.75 + 0.25 * math.sin(t * 0.7 + rng.random() * 6)
                if on:
                    f.cx.rectangle(wx, wy, 28, 38)
                    src(f.cx, hexc("#e7ecf7"), a * 0.55 * flick)
                    f.cx.fill()
                    f.gx.rectangle(wx, wy, 28, 38)
                    src(f.gx, hexc("#e7ecf7"), a * 0.35 * flick)
                    f.gx.fill()
                    if nums and rng.random() < 0.35:
                        text(f, str(rng.choice(nums)), wx + 14, wy - 8, 18, WHITE, a * 0.85, glow=0.6)
                else:
                    f.cx.rectangle(wx, wy, 28, 38)
                    src(f.cx, hexc("#2a2f3a"), a)
                    f.cx.fill()
        xs += bw + rng.randint(10, 40)


# ------------------------------------------------------------------ cafe
def cafe(f, t, a=1.0):
    room(f, back=(160, 470, 920, 1080), a=a, floor_lines=6)
    # big rainy window
    c = f.cx
    wx, wy, ww, wh = 210, 520, 660, 420
    grect(f, wx, wy, ww, wh, 10, LINE, 2.6, a, glow=0.5, fillc=hexc("#141a26"))
    c.save()
    c.rectangle(wx, wy, ww, wh)
    c.clip()
    import random
    rng = random.Random(4)
    for i in range(70):
        rx = wx + rng.random() * ww
        sp = 500 + rng.random() * 300
        ry = wy + ((rng.random() * wh + t * sp) % (wh + 60)) - 30
        gline(f, [(rx, ry), (rx - 4, ry + 26)], hexc("#9fb0cc"), 1.6, a * 0.6, glow=0.3)
    for i in range(14):  # bokeh street lights
        bx = wx + rng.random() * ww
        by = wy + 80 + rng.random() * (wh - 120)
        glow_blob(f, bx, by, 26 + rng.random() * 30, hexc("#cfd9ee"), 0.25 * a)
    c.restore()
    gline(f, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], LINE, 2.4, a)
    # pendant lamp
    gline(f, [(540, 0), (540, 400)], LINE_DIM, 2, a)
    lamp = [(470, 470), (610, 470), (575, 400), (505, 400)]
    gline(f, lamp, WHITE, 3, a, glow=0.8, close=True)
    glow_blob(f, 540, 480, 420, hexc("#fff4de"), 0.22 * a)
    # light cone
    c.move_to(470, 470)
    c.line_to(610, 470)
    c.line_to(860, 1250)
    c.line_to(220, 1250)
    c.close_path()
    g = cairo.LinearGradient(0, 470, 0, 1250)
    g.add_color_stop_rgba(0, 1, 0.97, 0.9, 0.10 * a)
    g.add_color_stop_rgba(1, 1, 0.97, 0.9, 0.0)
    c.set_source(g)
    c.fill()


def cafe_table(f, x, y, a=1.0, steam_t=None):
    ellipse(f.cx, x, y, 260, 50)
    src(f.cx, hexc("#1f232c"), a)
    f.cx.fill()
    f.both(lambda c: (ellipse(c, x, y, 260, 50)))
    for c, w, al in ((f.cx, 3, a), (f.gx, 7, a * 0.5)):
        ellipse(c, x, y, 260, 50)
        src(c, LINE, al)
        c.set_line_width(w)
        c.stroke()
    gline(f, [(x, y + 50), (x, y + 330)], LINE, 4, a)
    for dx in (-90, 90):
        cup(f, x + dx, y - 6, a, steam_t)


def cup(f, x, y, a=1.0, steam_t=None):
    pts = [(x - 26, y - 50), (x + 26, y - 50), (x + 20, y), (x - 20, y)]
    f.cx.move_to(*pts[0])
    for p in pts[1:]:
        f.cx.line_to(*p)
    f.cx.close_path()
    src(f.cx, WHITE, a)
    f.cx.fill()
    gline(f, pts, INK, 3, a, glow=0, close=True)
    if steam_t is not None:
        for k in (-1, 1):
            ph = steam_t * 0.8 + k
            pts = [(x + k * 8 + math.sin(ph + i * 0.8) * 6, y - 60 - i * 14) for i in range(6)]
            gline(f, pts, WHITE, 2.2, a * 0.35, glow=0.6)


# ------------------------------------------------------------------ dad's kitchen bench
def kitchen(f, a=1.0):
    room(f, back=(190, 520, 890, 1100), a=a, floor_lines=6)
    window(f, 420, 580, 240, 260, a, light=0.6)
    # wall tiles
    for i in range(8):
        gline(f, [(190, 880 + i * 28), (890, 880 + i * 28)], LINE_DIM, 1, a * 0.3, glow=0)


def table_front(f, x, y, w, a=1.0, h=360):
    grect(f, x, y, w, 28, 6, LINE, 3, a, glow=0.5, fillc=PANEL2)
    f.cx.rectangle(x + 10, y + 28, w - 20, h)
    src(f.cx, hexc("#151820"), a * 0.92)
    f.cx.fill()
    gline(f, [(x + 30, y + 28), (x + 30, y + h)], LINE, 3, a)
    gline(f, [(x + w - 30, y + 28), (x + w - 30, y + h)], LINE, 3, a)


def tea_glass(f, x, y, a=1.0):
    pts = [(x - 16, y - 50), (x + 16, y - 50), (x + 12, y), (x - 12, y)]
    gline(f, pts, WHITE, 2.6, a, glow=0.5, close=True)
    ellipse(f.cx, x, y + 6, 30, 7)
    src(f.cx, LINE, a)
    f.cx.set_line_width(2.4)
    f.cx.stroke()


# ------------------------------------------------------------------ bubbles / icons
def bubble(f, x, y, w, h, a=1.0, tail=-1, glow=0.5):
    """Rounded speech bubble centred at (x,y). tail: -1 down-left, 1 down-right."""
    c = f.cx
    for cc, lw, al, fillit in ((f.cx, 3.2, a, True), (f.gx, 7, a * glow, False)):
        rrect(cc, x - w / 2, y - h / 2, w, h, h * 0.32)
        tx = x + tail * w * 0.18
        cc.move_to(tx - 18, y + h / 2 - 2)
        cc.line_to(tx + tail * 6, y + h / 2 + 30)
        cc.line_to(tx + 18, y + h / 2 - 2)
        if fillit:
            src(cc, hexc("#151820"), al)
            cc.fill_preserve()
        src(cc, WHITE, al)
        cc.set_line_width(lw)
        cc.stroke()
    _ = c


def icon(f, kind, x, y, s=40, a=1.0, col=WHITE):
    """Simple glowing line icons."""
    L = lambda pts, close=False: gline(f, pts, col, s * 0.09, a, glow=0.7, close=close)
    if kind == "cloud":
        for c, lw, al in ((f.cx, s * 0.09, a), (f.gx, s * 0.2, a * 0.7)):
            c.new_sub_path()
            c.arc(x - s * 0.35, y + s * 0.1, s * 0.3, math.pi * 0.5, math.pi * 1.5)
            c.arc(x, y - s * 0.1, s * 0.42, math.pi * 1.05, math.pi * 1.95)
            c.arc(x + s * 0.38, y + s * 0.1, s * 0.3, math.pi * 1.5, math.pi * 0.5)
            c.close_path()
            src(c, col, al)
            c.set_line_width(lw)
            c.stroke()
    elif kind == "ball":
        gcircle(f, x, y, s * 0.45, col, s * 0.09, a, glow=0.7)
        L([(x - s * 0.15, y - s * 0.1), (x + s * 0.15, y - s * 0.1), (x + s * 0.22, y + s * 0.15), (x, y + s * 0.3),
           (x - s * 0.22, y + s * 0.15)], close=True)
    elif kind == "tomato":
        gcircle(f, x, y + s * 0.05, s * 0.42, col, s * 0.09, a, glow=0.7)
        L([(x - s * 0.2, y - s * 0.4), (x, y - s * 0.3), (x + s * 0.2, y - s * 0.4)])
        L([(x, y - s * 0.3), (x, y - s * 0.55)])
    elif kind == "heart":
        pts = []
        for i in range(41):
            th = i / 40 * 2 * math.pi
            hx = 16 * math.sin(th) ** 3
            hy = -(13 * math.cos(th) - 5 * math.cos(2 * th) - 2 * math.cos(3 * th) - math.cos(4 * th))
            pts.append((x + hx * s / 34, y + hy * s / 34))
        L(pts, close=True)
    elif kind == "star":
        pts = []
        for i in range(10):
            r = s * (0.5 if i % 2 == 0 else 0.22)
            th = -math.pi / 2 + i * math.pi / 5
            pts.append((x + r * math.cos(th), y + r * math.sin(th)))
        L(pts, close=True)
    elif kind == "cake":
        L([(x - s * 0.4, y + s * 0.35), (x + s * 0.4, y + s * 0.35), (x + s * 0.4, y - s * 0.05), (x - s * 0.4, y - s * 0.05)], True)
        L([(x - s * 0.4, y + s * 0.12), (x + s * 0.4, y + s * 0.12)])
        L([(x, y - s * 0.05), (x, y - s * 0.3)])
        gcircle(f, x, y - s * 0.38, s * 0.05, col, s * 0.07, a, glow=0.9)
    elif kind == "ring":
        gcircle(f, x - s * 0.15, y + s * 0.05, s * 0.28, col, s * 0.08, a, glow=0.7)
        gcircle(f, x + s * 0.15, y + s * 0.05, s * 0.28, col, s * 0.08, a, glow=0.7)
    elif kind == "case":
        L([(x - s * 0.42, y - s * 0.2), (x + s * 0.42, y - s * 0.2), (x + s * 0.42, y + s * 0.35), (x - s * 0.42, y + s * 0.35)], True)
        L([(x - s * 0.15, y - s * 0.2), (x - s * 0.15, y - s * 0.38), (x + s * 0.15, y - s * 0.38), (x + s * 0.15, y - s * 0.2)])
    elif kind == "house":
        L([(x - s * 0.4, y - s * 0.02), (x, y - s * 0.42), (x + s * 0.4, y - s * 0.02)])
        L([(x - s * 0.3, y - s * 0.1), (x - s * 0.3, y + s * 0.38), (x + s * 0.3, y + s * 0.38), (x + s * 0.3, y - s * 0.1)])
    elif kind == "phone":
        L([(x - s * 0.24, y - s * 0.42), (x + s * 0.24, y - s * 0.42), (x + s * 0.24, y + s * 0.42), (x - s * 0.24, y + s * 0.42)], True)
    elif kind == "school":
        L([(x - s * 0.5, y - s * 0.1), (x, y - s * 0.35), (x + s * 0.5, y - s * 0.1), (x, y + s * 0.12)], True)
        L([(x + s * 0.35, y - s * 0.05), (x + s * 0.35, y + s * 0.3)])
    elif kind == "plane":
        L([(x - s * 0.5, y + s * 0.05), (x + s * 0.5, y - s * 0.1)])
        L([(x - s * 0.05, y - s * 0.02), (x - s * 0.25, y - s * 0.4)])
        L([(x - s * 0.05, y - s * 0.02), (x + s * 0.1, y + s * 0.35)])


# ------------------------------------------------------------------ phone UI
def phone(f, x, y, w=560, h=1080, a=1.0, glow=0.9, screen_col=hexc("#0f1218")):
    """Big phone frame centred at (x, y); returns screen rect."""
    c = f.cx
    rrect(c, x - w / 2, y - h / 2, w, h, 70)
    src(c, screen_col, a)
    c.fill()
    grect(f, x - w / 2, y - h / 2, w, h, 70, WHITE, 5, a, glow=glow)
    grect(f, x - w / 2 + 14, y - h / 2 + 14, w - 28, h - 28, 58, LINE_DIM, 2, a * 0.6, glow=0)
    rrect(c, x - 60, y - h / 2 + 30, 120, 30, 15)
    src(c, hexc("#05060a"), a)
    c.fill()
    return (x - w / 2 + 28, y - h / 2 + 80, w - 56, h - 120)


def avatar(f, x, y, r, a=1.0, col=WHITE):
    gcircle(f, x, y, r, col, r * 0.12, a, glow=0.4)
    gcircle(f, x, y - r * 0.2, r * 0.32, col, r * 0.1, a, glow=0.3)
    f.cx.arc(x, y + r * 0.62, r * 0.55, math.pi * 1.15, math.pi * 1.85)
    src(f.cx, col, a)
    f.cx.set_line_width(r * 0.1)
    f.cx.stroke()


def contact_row(f, x, y, w, name, num, a=1.0, hl=0.0, num_a=1.0, glow_num=0.6):
    if hl > 0:
        rrect(f.cx, x - 10, y - 38, w + 20, 76, 18)
        src(f.cx, WHITE, 0.10 * hl * a)
        f.cx.fill()
        grect(f, x - 10, y - 38, w + 20, 76, 18, WHITE, 2.4, a * hl, glow=0.6)
    avatar(f, x + 30, y, 22, a * 0.9, GREY1)
    text(f, name, x + 74, y + 11, 30, WHITE if hl else GREY1, a, "left", weight="bold")
    if num is not None:
        text(f, str(num), x + w - 6, y + 11, 32, WHITE, a * num_a, "right", family="Inter Display", glow=glow_num)
    gline(f, [(x + 74, y + 38), (x + w, y + 38)], hexc("#2a2e38"), 1.5, a, glow=0)


def msg_bubble(f, x, y, s, mine=True, a=1.0, size=30, glow=0.3):
    w = text_w(f.cx, s, size=size) + 56
    h = size + 40
    bx = x - w if mine else x
    rrect(f.cx, bx, y - h / 2, w, h, 26)
    src(f.cx, BLUE if mine else hexc("#e9eaee"), a)
    f.cx.fill()
    if glow:
        rrect(f.gx, bx, y - h / 2, w, h, 26)
        src(f.gx, BLUE if mine else WHITE, a * glow)
        f.gx.fill()
    text(f, s, bx + w / 2, y + size * 0.36, size, WHITE if mine else INK, a)
    return w

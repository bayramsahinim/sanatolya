"""Sets and props for the dry-peas prison episode (world coordinates, vertical 1080x1920 frame).

CELL      - inside the cell: teal stone back wall with THE CRACK, barred door (corridor behind it),
            small barred window, cot.
CORRIDOR  - outside the cell: warm brick corridor, torches; the cell front (bars) on the right with
            the crack visible through them.
OUTSIDE   - sunset field outside the burst prison wall.
"""
import math
import random

import cairo

from cinecode.core import (OUTLINE, H, W, circle, clamp, curve, ellipse, fs, hexc, line, mix, poly, rgrad,
                           rrect, shade, smooth, smooth_poly, src, text, vgrad)

GROUND = 1560
CRACK_X = 1240
CRACK_Y0, CRACK_Y1 = 800, 1430

PEA = hexc("#D8C24A")
PEA_DK = hexc("#A8912A")
PEA_WET = hexc("#E9DA5A")
STONE = hexc("#7FA7A2")
STONE_DK = hexc("#5D8580")
MORTAR = hexc("#46625F")
BRICK = hexc("#C4603E")
BRICK_DK = hexc("#9C4630")
WOOD = hexc("#8A5A34")
WOOD_DK = hexc("#6A4226")
METAL = hexc("#3A3D44")


# ============================================================ helpers
def blocks(cx, x0, y0, x1, y1, bw, bh, base, mortar, seed=1, var=0.06, r=6, lw=4.0, outline=None):
    """Staggered block wall (stone or brick)."""
    rnd = random.Random(seed)
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, mortar)
    cx.fill()
    row = 0
    y = y0
    while y < y1:
        off = (bw / 2) * (row % 2) - bw
        x = x0 + off
        while x < x1:
            k = rnd.uniform(-var, var)
            c = shade(base, k)
            rrect(cx, x + lw / 2, y + lw / 2, bw - lw, bh - lw, r)
            src(cx, c)
            cx.fill()
            # top-left highlight
            if rnd.random() < 0.55:
                rrect(cx, x + lw / 2 + 6, y + lw / 2 + 5, (bw - lw) * rnd.uniform(0.2, 0.5), 5, 2.5)
                src(cx, (1, 1, 1, 0.10))
                cx.fill()
            x += bw
        y += bh
        row += 1
    if outline:
        cx.rectangle(x0, y0, x1 - x0, y1 - y0)
        fs(cx, None, outline, 5)


def floor(cx, x0, x1, y0, y1, base, line_c, seed=3):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    cx.set_source(vgrad(cx, 0, y0, 0, y1, [(0, shade(base, -0.12)), (1, base)]))
    cx.fill()
    y = y0
    k = 0
    while y < y1:
        h = 40 + k * 22
        line(cx, [(x0, y), (x1, y)], line_c, 4)
        off = (k % 2) * 90
        xx = x0 + off
        while xx < x1:
            line(cx, [(xx, y), (xx + (xx - 1000) * 0.05, y + h)], line_c, 3.5)
            xx += 180 + k * 30
        y += h
        k += 1
    line(cx, [(x0, y0), (x1, y0)], OUTLINE, 6)


def glow(cx, x, y, r, c, a=1.0):
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x, y, 0, r, [(0, (*c[:3], 0.55 * a)), (0.45, (*c[:3], 0.18 * a)), (1, (*c[:3], 0))]))
    cx.fill()
    cx.restore()


def label_chip(cx, x, y, txt, size=34, alpha=1.0, fill_c=(1, 1, 1, 1), ink=OUTLINE):
    cx.save()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(size)
    e = cx.text_extents(txt)
    w, h = e.width + size * 1.0, size * 1.45
    cx.push_group()
    rrect(cx, x - w / 2, y - h / 2, w, h, h / 2)
    fs(cx, fill_c, OUTLINE, 4)
    text(cx, txt, x, y + size * 0.36, size, ink)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


# ============================================================ peas
def pea(cx, x, y, r, swell=0.0, wet=0.0, rot=0.0, lw=3.0):
    rr = r * (1 + 0.55 * swell)
    c = mix(PEA, PEA_WET, max(swell, wet))
    if swell < 0.5:
        # dry: slightly squarish, wrinkled
        cx.save()
        cx.translate(x, y)
        cx.rotate(rot)
        pts = []
        for k in range(10):
            a = k / 10 * 2 * math.pi
            d = rr * (1 - 0.1 * (1 - 2 * swell) * (0.5 + 0.5 * math.cos(3 * a + rot * 3)))
            pts.append((math.cos(a) * d, math.sin(a) * d))
        smooth_poly(cx, pts)
        fs(cx, c, OUTLINE, lw)
        if swell < 0.35:
            curve(cx, (-rr * 0.45, -rr * 0.1), (-rr * 0.1, rr * 0.25), (rr * 0.15, -rr * 0.2), (rr * 0.45, rr * 0.1),
                  (*PEA_DK[:3], 0.9), lw * 0.8)
        cx.restore()
    else:
        circle(cx, x, y, rr)
        fs(cx, c, OUTLINE, lw)
    ellipse(cx, x - rr * 0.35, y - rr * 0.38, rr * 0.28, rr * 0.18, -0.5)
    src(cx, (1, 1, 1, 0.55 + 0.3 * max(swell, wet)))
    cx.fill()


# ============================================================ the crack
class Crack:
    def __init__(self, x=CRACK_X, y0=CRACK_Y0, y1=CRACK_Y1, maxw=31, seed=7):
        rnd = random.Random(seed)
        self.x, self.y0, self.y1 = x, y0, y1
        n = 16
        self.left, self.right = [], []
        for i in range(n + 1):
            u = i / n
            y = y0 + (y1 - y0) * u
            w = maxw * (math.sin(math.pi * u) ** 1.1) + 2
            cxo = math.sin(u * 7.0) * 18 + rnd.uniform(-8, 8)
            self.left.append((x + cxo - w + rnd.uniform(-6, 4), y))
            self.right.append((x + cxo + w + rnd.uniform(-4, 6), y))
        # pea slots inside, bottom-up
        slots = []
        rr = 13
        y = y1 - 24
        row = 0
        while y > y0 + 20:
            u = (y - y0) / (y1 - y0)
            i = min(n - 1, int(u * n))
            fr = u * n - i
            lx = self.left[i][0] + (self.left[i + 1][0] - self.left[i][0]) * fr
            rx = self.right[i][0] + (self.right[i + 1][0] - self.right[i][0]) * fr
            span = rx - lx
            k = max(1, int(span / (rr * 1.75)))
            for j in range(k):
                px = lx + span * (j + 0.5) / k + rnd.uniform(-3, 3)
                slots.append((px, y + rnd.uniform(-3, 3), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.1)))
            y -= rr * 1.55
            row += 1
        self.slots = slots
        # overflow peas (stuck on the wall surface, around the crack) - used when bulge > 0
        self.over = []
        for k in range(70):
            u = rnd.uniform(0.05, 0.95)
            y = y0 + (y1 - y0) * u
            side = rnd.choice((-1, 1))
            dx = side * rnd.uniform(20, 70) * math.sin(math.pi * u) ** 0.5
            self.over.append((x + math.sin(u * 7.0) * 18 + dx, y, rnd.uniform(0, 6.28), rnd.random()))
        # sprouts
        self.sprouts = []
        for k in range(7):
            u = 0.12 + 0.76 * k / 6 + rnd.uniform(-0.03, 0.03)
            y = y0 + (y1 - y0) * u
            side = 1 if k % 2 else -1
            self.sprouts.append((x + math.sin(u * 7.0) * 18 + side * 20, y, side, rnd.uniform(0.7, 1.2)))
        # wall fractures (branching)
        self.fract = []
        for k in range(9):
            u = rnd.uniform(0.05, 0.95)
            sx = x + math.sin(u * 7.0) * 18
            sy = y0 + (y1 - y0) * u
            side = rnd.choice((-1, 1))
            pts = [(sx, sy)]
            a = math.pi / 2 - side * math.pi / 2 + rnd.uniform(-0.7, 0.7)
            for s in range(rnd.randint(4, 7)):
                a += rnd.uniform(-0.6, 0.6)
                L = rnd.uniform(40, 90)
                pts.append((pts[-1][0] + math.cos(a) * L, pts[-1][1] + math.sin(a) * L))
            self.fract.append(pts)

    def path(self, cx, grow=1.0):
        pts = self.left + self.right[::-1]
        if grow != 1.0:
            pts = [(self.x + (px - self.x) * grow, py) for px, py in pts]
        poly(cx, pts)

    def draw(self, cx, fill=0.0, swell=0.0, wet=0.0, bulge=0.0, sprout=0.0, fracture=0.0, t=0.0, gap=1.0,
             dark=(0.17, 0.22, 0.23, 1)):
        g = gap * (1 + 0.5 * bulge + 0.6 * swell)
        # dark gap
        self.path(cx, g)
        fs(cx, dark, OUTLINE, 5)
        # peas in the crack
        n = int(round(clamp(fill) * len(self.slots)))
        cx.save()
        self.path(cx, g * 1.15)
        cx.clip()
        for (px, py, rot, sc) in self.slots[:n]:
            pea(cx, self.x + (px - self.x) * g, py, 13 * sc, swell, wet, rot)
        cx.restore()
        if fill >= 1.0 and bulge > 0:
            m = int(len(self.over) * clamp(bulge))
            for (px, py, rot, rr) in self.over[:m]:
                pea(cx, self.x + (px - self.x) * (1 + 0.4 * swell), py, (12 + rr * 3), swell, wet, rot)
        # wet shine
        if wet > 0:
            self.path(cx, g)
            src(cx, (0.6, 0.85, 1.0, 0.25 * wet))
            cx.fill()
            for k in range(5):
                yy = self.y0 + (self.y1 - self.y0) * (0.2 + 0.15 * k) + ((t * 60 + k * 37) % 80)
                ellipse(cx, self.x + math.sin(k * 3) * 16, yy, 4, 7)
                src(cx, (0.7, 0.9, 1, 0.6 * wet))
                cx.fill()
        if sprout > 0:
            for (sx, sy, side, sc) in self.sprouts:
                L = 70 * sc * smooth(sprout)
                sway = math.sin(t * 2 + sy) * 4
                ex, ey = sx + side * L * 0.7 + sway, sy - L
                curve(cx, (sx, sy), (sx + side * L * 0.4, sy - L * 0.2), (ex - side * 10, ey + L * 0.3), (ex, ey),
                      OUTLINE, 9)
                curve(cx, (sx, sy), (sx + side * L * 0.4, sy - L * 0.2), (ex - side * 10, ey + L * 0.3), (ex, ey),
                      hexc("#6DBB45"), 5)
                lf = 22 * sc * smooth(sprout)
                for s2 in (-1, 1):
                    ellipse(cx, ex + s2 * lf * 0.6, ey - lf * 0.15, lf * 0.62, lf * 0.32, s2 * 0.5)
                    fs(cx, hexc("#7FD255"), OUTLINE, 3.5)
        if fracture > 0:
            for k, pts in enumerate(self.fract):
                f = clamp(fracture * 1.4 - k * 0.05)
                if f <= 0:
                    continue
                m = max(2, int(len(pts) * f))
                line(cx, pts[:m], OUTLINE, 6)
                line(cx, pts[:m], (0.95, 0.97, 1.0, 0.65), 2)


CRACK = Crack()


# ============================================================ props
def bowl(cx, x, y, s=1.0, fill=1.0, seed=2):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rnd = random.Random(seed)
    if fill > 0:
        n = int(14 * fill)
        for k in range(n):
            a = k / 14
            px = -42 + (k % 7) * 14 + rnd.uniform(-3, 3)
            py = -6 - (k // 7) * 11 - 6 * math.sin(math.pi * ((k % 7) / 6)) * fill
            pea(cx, px, py, 9, rot=rnd.uniform(0, 6), lw=2.4)
    cx.move_to(-58, -8)
    cx.curve_to(-54, 26, 54, 26, 58, -8)
    cx.close_path()
    fs(cx, hexc("#B8BEC6"), OUTLINE, 4)
    ellipse(cx, 0, -8, 58, 7)
    fs(cx, None, OUTLINE, 3.5)
    cx.move_to(-40, 4)
    cx.curve_to(-30, 14, -10, 16, 6, 16)
    src(cx, (1, 1, 1, 0.5))
    cx.set_line_width(4)
    cx.stroke()
    cx.restore()


def spoon(cx, x, y, ang, s=1.0, has_pea=False, swell=0.0):
    """x,y = grip point (hand). ang = radians of the spoon direction."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    rrect(cx, -14, -5, 66, 10, 5)
    fs(cx, hexc("#C9CED6"), OUTLINE, 3.5)
    ellipse(cx, 68, 0, 20, 13)
    fs(cx, hexc("#D9DEE5"), OUTLINE, 3.5)
    if has_pea:
        pea(cx, 68, -4, 10, swell, lw=2.6)
    cx.restore()


def cup(cx, x, y, s=1.0, tilt=0.0, water=1.0):
    """tin cup, x,y = handle grip; tilt radians (+ = pour toward +x)."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(tilt)
    cx.scale(s, s)
    rrect(cx, -6, -36, 56, 66, 8)
    fs(cx, hexc("#AEB5BF"), OUTLINE, 4)
    ellipse(cx, 22, -36, 28, 7)
    fs(cx, hexc("#7BB8E8") if water > 0.05 else hexc("#59606B"), OUTLINE, 3.5)
    cx.arc(-8, -4, 14, math.pi * 0.5, math.pi * 1.5)
    src(cx, OUTLINE)
    cx.set_line_width(6)
    cx.stroke()
    cx.restore()


def water_stream(cx, x0, y0, x1, y1, t, w=12, alpha=1.0):
    if alpha <= 0:
        return
    cx.save()
    mx, my = (x0 + x1) / 2 + 20, (y0 + y1) / 2 - 10
    cx.move_to(x0, y0)
    cx.curve_to(mx, my - 20, x1, y1 - 60, x1, y1)
    src(cx, (*OUTLINE[:3], alpha))
    cx.set_line_width(w + 6)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.move_to(x0, y0)
    cx.curve_to(mx, my - 20, x1, y1 - 60, x1, y1)
    src(cx, (0.45, 0.75, 1.0, alpha))
    cx.set_line_width(w)
    cx.stroke()
    for k in range(4):
        ph = (t * 3 + k * 0.25) % 1
        ellipse(cx, x1 + math.sin(k * 2.3) * 14 * ph, y1 + 10 + 30 * ph, 4, 6)
        src(cx, (0.55, 0.82, 1.0, alpha * (1 - ph)))
        cx.fill()
    cx.restore()


def sausage_fork(cx, x, y, ang, s=1.0, t=0.0, steam=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    line(cx, [(-10, 0), (60, 0)], OUTLINE, 9)
    line(cx, [(-10, 0), (60, 0)], hexc("#C9CED6"), 5)
    for k in (-6, 0, 6):
        line(cx, [(60, k * 0.6), (84, k)], OUTLINE, 4)
    # sausage across the tines
    cx.save()
    cx.translate(110, 0)
    rrect(cx, -48, -16, 130, 32, 16)
    fs(cx, hexc("#D2553A"), OUTLINE, 4)
    for k in range(4):
        curve(cx, (-30 + k * 28, -10), (-24 + k * 28, -2), (-24 + k * 28, 4), (-30 + k * 28, 10),
              hexc("#9E3626"), 3)
    rrect(cx, -36, -12, 90, 6, 3)
    src(cx, (1, 1, 1, 0.35))
    cx.fill()
    cx.restore()
    cx.restore()
    if steam > 0:
        bx = x + math.cos(ang) * 130 * s
        by = y + math.sin(ang) * 130 * s
        for k in range(3):
            ph = (t * 0.8 + k / 3) % 1
            yy = by - 30 * s - ph * 90 * s
            xx = bx + (k - 1) * 22 * s
            cx.move_to(xx, yy + 30 * s)
            for j in range(1, 7):
                cx.line_to(xx + math.sin(j * 1.3 + t * 5) * 7 * s, yy + 30 * s - j * 7 * s)
            src(cx, (1, 1, 1, steam * 0.75 * math.sin(math.pi * ph)))
            cx.set_line_width(5 * s)
            cx.stroke()


def bucket(cx, x, y, s=1.0, rot=0.0, water=True):
    """x,y = handle top."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    cx.arc(0, 40, 48, math.pi, 2 * math.pi)
    src(cx, OUTLINE)
    cx.set_line_width(5)
    cx.stroke()
    cx.move_to(-50, 40)
    cx.line_to(-40, 130)
    cx.line_to(40, 130)
    cx.line_to(50, 40)
    cx.close_path()
    fs(cx, hexc("#D63A2F"), OUTLINE, 4.5)
    for yy in (60, 110):
        line(cx, [(-48 + (yy - 40) * 0.11, yy), (48 - (yy - 40) * 0.11, yy)], hexc("#A82A22"), 5)
    ellipse(cx, 0, 40, 50, 10)
    fs(cx, hexc("#7BB8E8") if water else hexc("#5A1A15"), OUTLINE, 4)
    cx.restore()


def jug(cx, x, y, s=1.0, peas=0.0, swell=0.0, shake=0.0, crack=0.0, t=0.0):
    """glass water jug standing at x,y (bottom centre)."""
    cx.save()
    cx.translate(x + math.sin(t * 60) * shake * 4, y)
    cx.scale(s, s)

    def body():
        cx.move_to(-22, -150)
        cx.line_to(-20, -118)
        cx.curve_to(-62, -100, -64, -10, -50, 0)
        cx.line_to(50, 0)
        cx.curve_to(64, -10, 62, -100, 20, -118)
        cx.line_to(22, -150)
        cx.close_path()

    body()
    src(cx, (0.82, 0.93, 0.98, 0.55))
    cx.fill()
    cx.save()
    body()
    cx.clip()
    cx.rectangle(-70, -88, 140, 90)
    src(cx, (0.45, 0.72, 0.95, 0.55))
    cx.fill()
    rnd = random.Random(4)
    n = int(26 * peas)
    for k in range(n):
        px = rnd.uniform(-44, 44)
        py = -10 - rnd.uniform(0, 60) - 30 * swell * rnd.random()
        pea(cx, px, py, 9, swell, 1.0, rnd.uniform(0, 6), lw=2.2)
    cx.restore()
    body()
    fs(cx, None, OUTLINE, 4.5)
    line(cx, [(-40, -90), (-44, -30)], (1, 1, 1, 0.7), 5)
    # handle
    cx.move_to(48, -100)
    cx.curve_to(90, -100, 90, -40, 52, -36)
    src(cx, OUTLINE)
    cx.set_line_width(7)
    cx.stroke()
    if crack > 0:
        rnd = random.Random(9)
        for k in range(5):
            pts = [(rnd.uniform(-30, 30), rnd.uniform(-100, -20))]
            for j in range(int(1 + 3 * crack)):
                pts.append((pts[-1][0] + rnd.uniform(-18, 18), pts[-1][1] + rnd.uniform(-18, 18)))
            line(cx, pts, (1, 1, 1, 0.95), 2.5)
    cx.restore()


def jug_burst(cx, x, y, s, u, seed=5):
    """explosion of glass + swollen peas, u = 0..1 progress."""
    if u <= 0 or u >= 1:
        return
    rnd = random.Random(seed)
    cx.save()
    cx.translate(x, y - 70 * s)
    cx.scale(s, s)
    # flash
    r = 40 + 260 * u
    cx.arc(0, 0, r, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, 0, 0, 0, r, [(0, (1, 1, 0.85, 0.9 * (1 - u))), (1, (1, 0.8, 0.4, 0))]))
    cx.fill()
    for k in range(26):
        a = rnd.uniform(0, 2 * math.pi)
        v = rnd.uniform(200, 520)
        px = math.cos(a) * v * u
        py = math.sin(a) * v * u + 400 * u * u
        if k % 2:
            pea(cx, px, py, 12, 1.0, 1.0, a, lw=2.5)
        else:
            cx.save()
            cx.translate(px, py)
            cx.rotate(a + u * 8)
            poly(cx, [(-10, -6), (12, -2), (-2, 10)])
            fs(cx, (0.85, 0.95, 1.0, 0.85), OUTLINE, 2.5)
            cx.restore()
    for k in range(8):
        a = k / 8 * 2 * math.pi
        line(cx, [(math.cos(a) * r * 0.45, math.sin(a) * r * 0.45), (math.cos(a) * r * 0.8, math.sin(a) * r * 0.8)],
             (1, 0.95, 0.6, 1 - u), 8)
    cx.restore()


def table(cx, x, y, w=360, h=150, top="#9A6A3E"):
    """x = centre, y = floor."""
    rrect(cx, x - w / 2, y - h, w, 26, 6)
    fs(cx, hexc(top), OUTLINE, 5)
    for sx in (-1, 1):
        rrect(cx, x + sx * (w / 2 - 34) - 10, y - h + 24, 20, h - 24, 4)
        fs(cx, shade(hexc(top), -0.25), OUTLINE, 4)


def chair(cx, x, y, f=1):
    rrect(cx, x - 50, y - 110, 100, 18, 5)
    fs(cx, WOOD, OUTLINE, 4)
    for sx in (-1, 1):
        rrect(cx, x + sx * 38 - 7, y - 94, 14, 94, 3)
        fs(cx, WOOD_DK, OUTLINE, 3.5)
    rrect(cx, x - f * 50 - 7, y - 260, 14, 160, 4)
    fs(cx, WOOD_DK, OUTLINE, 3.5)
    rrect(cx, x - f * 50 - 9, y - 250, 18 + 0, 60, 4)
    fs(cx, WOOD, OUTLINE, 3.5)


def lantern(cx, x, y, s=1.0, t=0.0, lit=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    fl = 0.85 + 0.15 * math.sin(t * 13) * math.sin(t * 5.3)
    glow(cx, 0, -50, 380, (1.0, 0.65, 0.25), lit * fl)
    rrect(cx, -30, -100, 60, 90, 8)
    fs(cx, (1.0, 0.85, 0.45, 0.85 * lit), OUTLINE, 4)
    ellipse(cx, 0, -48, 9 * fl, 18 * fl)
    src(cx, (1, 0.65, 0.2, lit))
    cx.fill()
    rrect(cx, -36, -12, 72, 14, 4)
    fs(cx, METAL, OUTLINE, 3.5)
    poly(cx, [(-36, -100), (0, -128), (36, -100)])
    fs(cx, METAL, OUTLINE, 3.5)
    cx.arc(0, -132, 12, math.pi, 2 * math.pi)
    fs(cx, None, OUTLINE, 4)
    cx.restore()


def torch(cx, x, y, t, s=1.0):
    fl = math.sin(t * 11 + x) * 0.5 + math.sin(t * 7.3) * 0.5
    glow(cx, x, y - 70 * s, 420 * s, (1.0, 0.6, 0.25), 0.9 + 0.1 * fl)
    rrect(cx, x - 10 * s, y - 40 * s, 20 * s, 90 * s, 5)
    fs(cx, WOOD_DK, OUTLINE, 4)
    cx.move_to(x - 22 * s, y - 40 * s)
    cx.curve_to(x - 26 * s, y - 90 * s, x - 6 * s + fl * 6, y - 120 * s, x + fl * 8 * s, y - 150 * s)
    cx.curve_to(x + 10 * s, y - 110 * s, x + 28 * s, y - 90 * s, x + 22 * s, y - 40 * s)
    cx.close_path()
    fs(cx, hexc("#FFB238"), OUTLINE, 4)
    ellipse(cx, x, y - 66 * s, 9 * s, 20 * s)
    src(cx, hexc("#FFF0A8"))
    cx.fill()
    rrect(cx, x - 26 * s, y - 46 * s, 52 * s, 14 * s, 4)
    fs(cx, METAL, OUTLINE, 3.5)


def sign_board(cx, x, y, alpha=1.0):
    cx.save()
    cx.push_group()
    line(cx, [(x - 120, y - 240), (x - 90, y - 150)], OUTLINE, 4)
    line(cx, [(x + 120, y - 240), (x + 90, y - 150)], OUTLINE, 4)
    rrect(cx, x - 200, y - 160, 400, 250, 14)
    fs(cx, hexc("#F3E3C3"), OUTLINE, 6)
    rrect(cx, x - 184, y - 144, 368, 218, 10)
    fs(cx, None, hexc("#C0392B"), 4)
    text(cx, "SEE THE", x, y - 90, 48, hexc("#C0392B"))
    text(cx, "WALL", x, y - 30, 64, hexc("#C0392B"))
    text(cx, "SPROUT", x, y + 36, 58, hexc("#C0392B"))
    # arrow
    poly(cx, [(x + 150, y - 40), (x + 190, y - 10), (x + 150, y + 20)])
    fs(cx, hexc("#C0392B"), None, 0)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def coin(cx, x, y, r=16, rot=0.0):
    ellipse(cx, x, y, r * max(0.15, abs(math.cos(rot))), r)
    fs(cx, hexc("#F2C94C"), OUTLINE, 3)


def ticket(cx, x, y, rot=0.0, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -40, -22, 80, 44, 5)
    fs(cx, hexc("#F7E08A"), OUTLINE, 3.5)
    line(cx, [(14, -18), (14, 18)], OUTLINE, 2)
    text(cx, "1", -12, 12, 30, hexc("#C0392B"))
    cx.restore()


def cot(cx, x, y, w=460):
    for sx in (-1, 1):
        rrect(cx, x + sx * (w / 2 - 20) - 8, y - 120, 16, 120, 4)
        fs(cx, METAL, OUTLINE, 3.5)
    rrect(cx, x - w / 2, y - 120, w, 40, 10)
    fs(cx, hexc("#8E9AA6"), OUTLINE, 4.5)
    rrect(cx, x - w / 2 + 14, y - 150, w * 0.32, 40, 16)
    fs(cx, hexc("#F1F1EC"), OUTLINE, 4)
    rrect(cx, x - w / 2 + w * 0.36, y - 132, w * 0.6, 22, 8)
    fs(cx, hexc("#5E7FA3"), OUTLINE, 4)


def tears(cx, x, y, R, t, amt=1.0, side_list=(-1, 1)):
    """two cartoon tear streams from eyes at head centre x,y (radius R)."""
    if amt <= 0:
        return
    for s in side_list:
        ex, ey = x + s * R * 0.34, y + R * 0.05
        for k in range(3):
            ph = (t * 2.2 + k / 3) % 1
            px = ex + s * (20 + 90 * ph) * amt
            py = ey - 10 + 120 * ph * ph
            cx.move_to(px, py - 14)
            cx.curve_to(px + 9, py, px + 9, py + 8, px, py + 10)
            cx.curve_to(px - 9, py + 8, px - 9, py, px, py - 14)
            src(cx, (0.55, 0.82, 1, amt * (1 - ph * 0.6)))
            cx.fill_preserve()
            src(cx, (*OUTLINE[:3], amt))
            cx.set_line_width(2.5)
            cx.stroke()


def drool(cx, x, y, u, s=1.0):
    if u <= 0:
        return
    L = 70 * u * s
    cx.move_to(x - 5 * s, y)
    cx.curve_to(x - 6 * s, y + L * 0.6, x - 3 * s, y + L, x, y + L)
    cx.curve_to(x + 3 * s, y + L, x + 6 * s, y + L * 0.6, x + 5 * s, y)
    fs(cx, (0.75, 0.9, 1, 0.9), OUTLINE, 2.5)
    circle(cx, x, y + L + 6 * s, 7 * s * u)
    fs(cx, (0.75, 0.9, 1, 0.9), OUTLINE, 2.5)


def zzz(cx, x, y, t, alpha=1.0, s=1.0):
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1
        a = alpha * math.sin(math.pi * ph)
        text(cx, "Z", x + ph * 70 * s + k * 6, y - ph * 140 * s, (34 + 18 * ph) * s, (*hexc("#DDE7FF")[:3], a))


def bunny(cx, x, y, s=1.0, alpha=1.0, t=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.push_group()
    for sx in (-1, 1):
        ellipse(cx, sx * 14, -78, 11, 32, sx * 0.15)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3.5)
        ellipse(cx, sx * 14, -76, 5, 22, sx * 0.15)
        src(cx, hexc("#FFB3C7"))
        cx.fill()
    ellipse(cx, 0, -6, 34, 30)
    fs(cx, (1, 1, 1, 1), OUTLINE, 3.5)
    circle(cx, 0, -40, 26)
    fs(cx, (1, 1, 1, 1), OUTLINE, 3.5)
    for sx in (-1, 1):
        circle(cx, sx * 9, -43, 3.5)
        fs(cx, OUTLINE, None, 0)
    circle(cx, 0, -34, 3)
    fs(cx, hexc("#FF7AA0"), None, 0)
    # heart
    hx, hy = 40, -78 - 6 * math.sin(t * 4)
    cx.move_to(hx, hy + 12)
    cx.curve_to(hx - 22, hy - 2, hx - 10, hy - 20, hx, hy - 8)
    cx.curve_to(hx + 10, hy - 20, hx + 22, hy - 2, hx, hy + 12)
    fs(cx, hexc("#FF5C8A"), OUTLINE, 3)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def poof(cx, x, y, u, r=90, c="#FF6FA8"):
    if u <= 0 or u >= 1:
        return
    rnd = random.Random(3)
    for k in range(9):
        a = k / 9 * 2 * math.pi + 0.3
        d = r * (0.3 + 0.9 * u)
        circle(cx, x + math.cos(a) * d, y + math.sin(a) * d, r * 0.35 * (1 - u) + 6)
        fs(cx, (*hexc(c)[:3], 1 - u), (*OUTLINE[:3], 1 - u), 3)
    for k in range(6):
        a = rnd.uniform(0, 6.28)
        d = r * 1.4 * u
        sx, sy = x + math.cos(a) * d, y + math.sin(a) * d
        line(cx, [(sx - 10, sy), (sx + 10, sy)], (1, 1, 1, 1 - u), 4)
        line(cx, [(sx, sy - 10), (sx, sy + 10)], (1, 1, 1, 1 - u), 4)


def splash(cx, x, y, u, s=1.0, seed=2):
    if u <= 0 or u >= 1:
        return
    rnd = random.Random(seed)
    for k in range(22):
        a = rnd.uniform(-math.pi, 0)
        v = rnd.uniform(150, 420) * s
        px = x + math.cos(a) * v * u
        py = y + math.sin(a) * v * u + 600 * s * u * u
        r = rnd.uniform(6, 14) * s * (1 - 0.5 * u)
        ellipse(cx, px, py, r, r * 1.3)
        fs(cx, (0.55, 0.82, 1.0, 1 - u * 0.7), (*OUTLINE[:3], 1 - u), 2.5)


# ============================================================ sets
def corridor_backdrop(cx, x0, x1, y0, y1, t, torches=(), seed=11):
    blocks(cx, x0, y0, x1, y1, 120, 56, BRICK, BRICK_DK, seed=seed, var=0.08, r=5, lw=6)
    for tx, ty in torches:
        torch(cx, tx, ty, t)


def bars(cx, x0, x1, y0, y1, step=70, w=16, cross=(), frame=True):
    x = x0
    while x <= x1 + 1:
        rrect(cx, x - w / 2, y0, w, y1 - y0, w / 2)
        cx.set_source(vgrad(cx, x - w / 2, 0, x + w / 2, 0, [(0, METAL), (0.4, hexc("#6A707A")), (1, shade(METAL, -0.3))]))
        cx.fill_preserve()
        src(cx, OUTLINE)
        cx.set_line_width(3.5)
        cx.stroke()
        x += step
    for cy in cross:
        rrect(cx, x0 - w, cy - 10, x1 - x0 + 2 * w, 20, 6)
        fs(cx, METAL, OUTLINE, 3.5)
        x = x0
        while x <= x1 + 1:
            circle(cx, x, cy, 5)
            fs(cx, hexc("#7A808A"), None, 0)
            x += step
    if frame:
        rrect(cx, x0 - 34, y0 - 30, x1 - x0 + 68, 34, 6)
        fs(cx, METAL, OUTLINE, 4)


def cell(cx, t, P=None, behind_bars=None):
    """World-space cell interior. P: dict(fill, swell, wet, bulge, sprout, fracture, window, door)."""
    P = P or {}
    # back wall
    blocks(cx, -600, -800, 2700, GROUND, 170, 96, STONE, MORTAR, seed=5, var=0.07, r=10, lw=7)
    # soft wall shading (darker top, lit middle)
    cx.rectangle(-600, -800, 3300, GROUND + 800)
    cx.set_source(vgrad(cx, 0, -800, 0, GROUND, [(0, (0, 0.05, 0.08, 0.45)), (0.55, (0, 0, 0, 0)), (1, (0, 0.05, 0.08, 0.25))]))
    cx.fill()
    # barred door with corridor behind
    dx0, dx1, dy0 = 110, 640, 470
    cx.save()
    cx.rectangle(dx0, dy0, dx1 - dx0, GROUND - dy0)
    cx.clip()
    corridor_backdrop(cx, dx0 - 100, dx1 + 100, dy0 - 100, GROUND, t, torches=((380, 830),), seed=21)
    floor(cx, dx0, dx1, GROUND - 70, GROUND, hexc("#7A5A44"), hexc("#5E4433"))
    if behind_bars:
        behind_bars(cx)
    cx.restore()
    bars(cx, dx0 + 20, dx1 - 20, dy0, GROUND, step=75, cross=(820, 1230))
    rrect(cx, dx0 - 20, dy0 - 36, dx1 - dx0 + 40, 40, 8)
    fs(cx, STONE_DK, OUTLINE, 5)
    # window + light beam
    wx, wy = 1640, 330
    rrect(cx, wx - 110, wy - 80, 220, 160, 10)
    cx.set_source(vgrad(cx, 0, wy - 80, 0, wy + 80, [(0, hexc("#BFE6FF")), (1, hexc("#EAF7FF"))]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(6)
    cx.stroke()
    for k in range(-1, 2):
        line(cx, [(wx + k * 55, wy - 80), (wx + k * 55, wy + 80)], METAL, 12)
    wl = P.get("window", 1.0)
    if wl > 0:
        cx.save()
        cx.set_operator(cairo.OPERATOR_ADD)
        poly(cx, [(wx - 110, wy + 80), (wx + 110, wy + 80), (wx - 260, GROUND + 150), (wx - 700, GROUND + 150)])
        cx.set_source(vgrad(cx, 0, wy, 0, GROUND, [(0, (1, 0.95, 0.75, 0.22 * wl)), (1, (1, 0.95, 0.75, 0.0))]))
        cx.fill()
        cx.restore()
    # floor
    floor(cx, -600, 2700, GROUND, 2900, hexc("#5F7F7B"), hexc("#4B6865"))
    # cot
    cot(cx, 1900, GROUND + 40)
    # the crack
    CRACK.draw(cx, fill=P.get("fill", 0.0), swell=P.get("swell", 0.0), wet=P.get("wet", 0.0),
               bulge=P.get("bulge", 0.0), sprout=P.get("sprout", 0.0), fracture=P.get("fracture", 0.0), t=t)


def corridor(cx, t, P=None, in_cell=None, cell_x0=1180, crack_off=330, props=None, torches=((360, 760),)):
    """World-space corridor; the cell front (bars) starts at cell_x0, crack visible through it
    (crack centre at cell_x0 + crack_off). `props(cx)` draws corridor props before the bars' pillar."""
    P = P or {}
    corridor_backdrop(cx, -600, cell_x0 + 40, -800, GROUND, t, torches=torches)
    # ceiling beams
    for k in range(4):
        y = -40 + k * 0
    cx.rectangle(-600, -800, 3400, 340)
    src(cx, WOOD_DK)
    cx.fill()
    for k in range(-2, 12):
        rrect(cx, -600 + k * 330, -800, 70, 360, 6)
        fs(cx, WOOD, OUTLINE, 4)
    rrect(cx, -600, -470, 3400, 40, 6)
    fs(cx, WOOD, OUTLINE, 4)
    # cell interior seen through the bars
    cx.save()
    cx.rectangle(cell_x0, -440, 3000, GROUND + 600)
    cx.clip()
    cx.save()
    s = 0.78
    cx.translate(cell_x0 + crack_off - CRACK_X * s, (GROUND - 40) - GROUND * s)
    cx.scale(s, s)
    blocks(cx, 0, -600, 2400, GROUND, 170, 96, shade(STONE, -0.12), shade(MORTAR, -0.1), seed=6, var=0.07, r=10, lw=7)
    floor(cx, 0, 2400, GROUND, 2600, hexc("#55716E"), hexc("#435E5B"))
    CRACK.draw(cx, fill=P.get("fill", 0.0), swell=P.get("swell", 0.0), wet=P.get("wet", 0.0),
               bulge=P.get("bulge", 0.0), sprout=P.get("sprout", 0.0), fracture=P.get("fracture", 0.0), t=t)
    if in_cell:
        in_cell(cx)
    cx.restore()
    # recess shadow
    cx.rectangle(cell_x0, -440, 3000, GROUND + 600)
    cx.set_source(vgrad(cx, cell_x0, 0, cell_x0 + 300, 0, [(0, (0, 0, 0, 0.35)), (1, (0, 0, 0, 0))]))
    cx.fill()
    cx.restore()
    # floor
    floor(cx, -600, 3400, GROUND, 2900, hexc("#7A6A5E"), hexc("#5E5148"))
    if props:
        props(cx)
    # cell front bars + pillar
    bars(cx, cell_x0 + 60, cell_x0 + 1500, -430, GROUND + 30, step=86, cross=(300, 1150), frame=False)
    rrect(cx, cell_x0 - 30, -440, 70, GROUND + 470, 8)
    fs(cx, STONE_DK, OUTLINE, 5)


def outside(cx, t, burst=1.0, peas_level=1.0):
    """Sunset field; prison wall with a huge hole behind."""
    cx.rectangle(-600, -1200, 3400, 4000)
    cx.set_source(vgrad(cx, 0, -600, 0, 1300, [(0, hexc("#5B4B9A")), (0.45, hexc("#E7769A")), (0.8, hexc("#FFB46B")),
                                          (1, hexc("#FFD58A"))]))
    cx.fill()
    circle(cx, 760, 1080, 120)
    src(cx, hexc("#FFE7A0"))
    cx.fill()
    glow(cx, 760, 1080, 600, (1, 0.8, 0.5), 0.8)
    # hills
    for k, (c, yb, amp) in enumerate([("#7DA35A", 1180, 60), ("#5E8C45", 1290, 50)]):
        cx.move_to(-600, 2900)
        for x in range(-600, 2800, 60):
            cx.line_to(x, yb - amp * math.sin(x / 300 + k * 2) - 30 * math.sin(x / 130 + k))
        cx.line_to(2800, 2900)
        cx.close_path()
        fs(cx, hexc(c), OUTLINE, 5)
    # trees
    for x, y, s in [(120, 1170, 1.0), (980, 1150, 1.2), (1300, 1190, 0.9)]:
        rrect(cx, x - 12 * s, y - 120 * s, 24 * s, 140 * s, 6)
        fs(cx, WOOD_DK, OUTLINE, 4)
        for dx, dy, r in [(-40, -150, 70), (40, -160, 72), (0, -220, 80)]:
            circle(cx, x + dx * s, y + dy * s, r * s)
        fs(cx, hexc("#4E7D3A"), OUTLINE, 5)

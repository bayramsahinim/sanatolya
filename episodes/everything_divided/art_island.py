"""Floating-island world: sky, clouds, islets, the island with soccer fields, forest, birds,
chickens, gold, the magnifying glass and the ant close-up."""
import math
import random

import cairo

from cinecode.core import back_out, ease_out, hexc, prog, rrect, shade, smooth, src
from cinecode.characters import HERO, Pose
from episodes.everything_divided.common import H, W, outlined

TAU = 2 * math.pi
SPR = 3.0          # sprite supersampling (crisp under camera zoom)


def _surface(w, h):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))


def blit(cx, surf, x, y, scale=1.0, alpha=1.0, anchor=(0.5, 1.0), sup=SPR):
    """Draw a supersampled sprite; (x, y) is the anchor point in world coords."""
    w, h = surf.get_width() / sup, surf.get_height() / sup
    cx.save()
    cx.translate(x, y)
    cx.scale(scale / sup, scale / sup)
    cx.set_source_surface(surf, -anchor[0] * w * sup, -anchor[1] * h * sup)
    cx.get_source().set_filter(cairo.FILTER_GOOD)
    cx.paint_with_alpha(alpha)
    cx.restore()


# ====================================================================== sky
_CACHE = {}


def sky(cx, night=0.0):
    if "sky" not in _CACHE:
        s = _surface(W, H)
        c = cairo.Context(s)
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, 0.30, 0.6, 0.9)
        g.add_color_stop_rgb(0.45, 0.55, 0.8, 0.97)
        g.add_color_stop_rgb(1, 0.86, 0.95, 1.0)
        c.set_source(g)
        c.paint()
        g = cairo.RadialGradient(W * 0.18, H * 0.16, 10, W * 0.18, H * 0.16, 700)
        g.add_color_stop_rgba(0, 1, 0.98, 0.85, 0.65)
        g.add_color_stop_rgba(1, 1, 0.98, 0.85, 0)
        c.set_source(g)
        c.paint()
        _CACHE["sky"] = s
    cx.set_source_surface(_CACHE["sky"], 0, 0)
    cx.paint_with_alpha(1 - night)


def cloud_sprite(seed, w=360):
    key = ("cloud", seed, w)
    if key in _CACHE:
        return _CACHE[key]
    rnd = random.Random(seed)
    s = _surface(w * SPR, w * 0.6 * SPR)
    c = cairo.Context(s)
    c.scale(SPR, SPR)
    puffs = []
    n = rnd.randint(5, 8)
    for i in range(n):
        x = w * (0.15 + 0.7 * i / (n - 1)) + rnd.uniform(-12, 12)
        r = w * rnd.uniform(0.1, 0.17) * (1.25 - abs(i / (n - 1) - 0.5))
        y = w * 0.42 - r * 0.6 + rnd.uniform(-6, 6)
        puffs.append((x, y, r))
    base_y = w * 0.47
    # shadow underside
    for x, y, r in puffs:
        c.arc(x, y + 6, r, 0, TAU)
    c.rectangle(puffs[0][0], base_y - 30, puffs[-1][0] - puffs[0][0], 30)
    c.set_source_rgba(0.62, 0.72, 0.86, 1)
    c.fill()
    for x, y, r in puffs:
        g = cairo.RadialGradient(x - r * 0.3, y - r * 0.45, r * 0.1, x, y, r * 1.05)
        g.add_color_stop_rgb(0, 1, 1, 1)
        g.add_color_stop_rgb(0.75, 0.96, 0.98, 1)
        g.add_color_stop_rgb(1, 0.84, 0.9, 0.98)
        c.arc(x, y, r, 0, TAU)
        c.set_source(g)
        c.fill()
    _CACHE[key] = s
    return s


CLOUDS = [  # x, y, width, seed, speed, depth
    (130, 470, 300, 1, 9, 0.5), (900, 420, 340, 2, 7, 0.55), (560, 300, 260, 3, 6, 0.4),
    (-80, 760, 380, 4, 8, 0.7), (1010, 690, 300, 5, 10, 0.65), (300, 1600, 420, 6, 6, 0.8),
    (880, 1700, 380, 7, 7, 0.85),
]


def clouds(cx, t, alpha=1.0, front=False):
    for x, y, w, seed, sp, depth in CLOUDS:
        if front != (y > 1300):
            continue
        xx = (x + t * sp + 300) % (W + 600) - 300
        blit(cx, cloud_sprite(seed, w), xx, y, 1.0, alpha * (0.95 if not front else 0.9), anchor=(0.5, 0.5))


def islet_sprite(seed, w=110):
    key = ("islet", seed, w)
    if key in _CACHE:
        return _CACHE[key]
    rnd = random.Random(seed + 40)
    s = _surface(w * SPR, w * 0.9 * SPR)
    c = cairo.Context(s)
    c.scale(SPR, SPR)
    top = w * 0.28
    c.move_to(w * 0.05, top)
    pts = [(w * 0.05, top)]
    for i in range(1, 8):
        u = i / 8
        pts.append((w * (0.05 + 0.9 * u), top + w * 0.5 * math.sin(math.pi * u) ** 1.4 + rnd.uniform(-3, 3)))
    pts.append((w * 0.95, top))
    for p_ in pts[1:]:
        c.line_to(*p_)
    c.close_path()
    g = cairo.LinearGradient(0, top, 0, top + w * 0.5)
    g.add_color_stop_rgb(0, 0.55, 0.47, 0.5)
    g.add_color_stop_rgb(1, 0.38, 0.33, 0.4)
    c.set_source(g)
    c.fill()
    c.save()
    c.translate(w / 2, top)
    c.scale(1, 0.3)
    c.arc(0, 0, w * 0.46, 0, TAU)
    c.restore()
    c.set_source_rgb(0.42, 0.72, 0.42)
    c.fill()
    for k in range(rnd.randint(2, 4)):
        x = w * rnd.uniform(0.2, 0.8)
        r = w * rnd.uniform(0.06, 0.1)
        c.arc(x, top - r * 0.6, r, 0, TAU)
        c.set_source_rgb(0.33, 0.62, 0.38)
        c.fill()
    _CACHE[key] = s
    return s


ISLETS = [(110, 640, 90, 1), (960, 560, 110, 2), (70, 1080, 70, 3), (1010, 1010, 80, 4), (250, 380, 60, 5),
          (820, 300, 70, 6), (980, 1320, 60, 7), (90, 1380, 75, 8), (640, 520, 50, 9)]


def islets(cx, t, alpha=1.0):
    for x, y, w, seed in ISLETS:
        yy = y + math.sin(t * 0.8 + seed) * 6
        blit(cx, islet_sprite(seed, w), x, yy, 1.0, alpha * 0.85, anchor=(0.5, 0.3))


# ====================================================================== island
class Island:
    IX, IY = 540.0, 1000.0
    A, B, KY, N = 432.0, 292.0, 0.62, 3.2
    DEPTH = 360.0

    FIELDS = [(-250, -214, 330, 214, "full"), (-250, 0, 330, 214, "full"), (80, 0, 165, 214, "half")]
    HERO_UV = (-45.0, 150.0)

    def S(self, u, v):
        return self.IX + u, self.IY + v * self.KY

    def outline(self, k=1.0, n=160):
        pts = []
        for i in range(n):
            a = TAU * i / n
            c, s = math.cos(a), math.sin(a)
            wob = 1 + 0.025 * math.sin(a * 5 + 1) + 0.015 * math.sin(a * 11)
            u = self.A * k * wob * math.copysign(abs(c) ** (2 / self.N), c)
            v = self.B * k * wob * math.copysign(abs(s) ** (2 / self.N), s)
            pts.append((u, v))
        return pts

    def inside(self, u, v, k=1.0):
        return (abs(u) / (self.A * k)) ** self.N + (abs(v) / (self.B * k)) ** self.N < 1

    # ---------------------------------------------------------------- cached base
    def base_surface(self):
        if "island" in _CACHE:
            return _CACHE["island"]
        pad = 40
        x0, y0 = self.IX - self.A - pad, self.IY - self.B * self.KY - pad
        w, h = 2 * (self.A + pad), self.B * self.KY * 2 + self.DEPTH + 2 * pad + 60
        sup = 2.0
        s = _surface(w * sup, h * sup)
        c = cairo.Context(s)
        c.scale(sup, sup)
        c.translate(-x0, -y0)
        out = self.outline()
        scr = [self.S(u, v) for u, v in out]
        rnd = random.Random(5)
        # underside rock mass
        front = [p for p, (u, v) in zip(scr, out) if v >= 0]
        front.sort(key=lambda p: p[0])
        left, right = front[0], front[-1]
        tipx, tipy = self.IX + 30, self.IY + self.B * self.KY + self.DEPTH
        c.new_path()
        c.move_to(*left)
        for p in front:
            c.line_to(p[0], p[1] + 46)
        pts = []
        n = 14
        for i in range(n + 1):
            u = i / n
            x = right[0] + (tipx - right[0]) * u
            y = right[1] + 46 + (tipy - right[1] - 46) * math.sin(u * math.pi / 2) ** 1.3
            x += math.sin(u * 9) * 14 * (1 - u)
            pts.append((x, y))
        for i in range(n + 1):
            u = i / n
            x = tipx + (left[0] - tipx) * u
            y = tipy + (left[1] + 46 - tipy) * (1 - math.cos(u * math.pi / 2)) ** 0.8
            x += math.sin(u * 7 + 2) * 16 * u
            pts.append((x, y))
        for p in pts:
            c.line_to(p[0], p[1] + rnd.uniform(-5, 5))
        c.close_path()
        under = c.copy_path()
        g = cairo.LinearGradient(0, self.IY, 0, tipy)
        g.add_color_stop_rgb(0, 0.52, 0.36, 0.25)
        g.add_color_stop_rgb(0.5, 0.42, 0.31, 0.26)
        g.add_color_stop_rgb(1, 0.3, 0.25, 0.27)
        c.set_source(g)
        c.fill()
        # side shading
        c.append_path(under)
        g = cairo.LinearGradient(left[0], 0, right[0], 0)
        g.add_color_stop_rgba(0, 1, 0.95, 0.85, 0.18)
        g.add_color_stop_rgba(0.4, 1, 1, 1, 0.0)
        g.add_color_stop_rgba(1, 0.1, 0.05, 0.1, 0.35)
        c.set_source(g)
        c.fill()
        # strata + rocks
        c.save()
        c.append_path(under)
        c.clip()
        for k in range(7):
            yy = self.IY + self.B * self.KY + 70 + k * 42
            c.move_to(left[0] - 20, yy)
            for i in range(30):
                x = left[0] + (right[0] - left[0]) * i / 29
                c.line_to(x, yy + math.sin(i * 0.9 + k) * 6)
            c.set_source_rgba(0.2, 0.12, 0.1, 0.22)
            c.set_line_width(3)
            c.stroke()
        for _ in range(55):
            x = rnd.uniform(left[0], right[0])
            y = rnd.uniform(self.IY + self.B * self.KY + 50, tipy - 40)
            r = rnd.uniform(6, 18)
            c.save()
            c.translate(x, y)
            c.scale(1, 0.7)
            c.arc(0, 0, r, 0, TAU)
            c.restore()
            g = cairo.LinearGradient(x, y - r, x, y + r)
            g.add_color_stop_rgba(0, 0.7, 0.62, 0.6, 0.85)
            g.add_color_stop_rgba(1, 0.38, 0.32, 0.33, 0.85)
            c.set_source(g)
            c.fill()
        c.restore()
        # hanging roots
        for _ in range(18):
            x = rnd.uniform(left[0] + 40, right[0] - 40)
            y = self.IY + self.B * self.KY * 0.9 + 46 + rnd.uniform(0, 20)
            ln = rnd.uniform(40, 120)
            c.move_to(x, y)
            c.curve_to(x + rnd.uniform(-15, 15), y + ln * 0.4, x + rnd.uniform(-20, 20), y + ln * 0.7,
                       x + rnd.uniform(-10, 10), y + ln)
            c.set_source_rgba(0.35, 0.24, 0.16, 0.8)
            c.set_line_width(rnd.uniform(2, 4))
            c.stroke()
        # soil band under the turf
        c.new_path()
        c.move_to(*left)
        for p in front:
            c.line_to(*p)
        for p in reversed(front):
            c.line_to(p[0], p[1] + 46)
        c.close_path()
        g = cairo.LinearGradient(0, self.IY, 0, self.IY + self.B * self.KY + 46)
        g.add_color_stop_rgb(0, 0.45, 0.3, 0.2)
        g.add_color_stop_rgb(1, 0.36, 0.23, 0.16)
        c.set_source(g)
        c.fill()
        # turf lip
        c.new_path()
        c.move_to(*left)
        for p in front:
            c.line_to(*p)
        for p in reversed(front):
            c.line_to(p[0], p[1] + 16)
        c.close_path()
        c.set_source_rgb(0.28, 0.6, 0.25)
        c.fill()
        # grass top
        c.new_path()
        c.move_to(*scr[0])
        for p in scr[1:]:
            c.line_to(*p)
        c.close_path()
        top = c.copy_path()
        g = cairo.LinearGradient(0, self.IY - self.B * self.KY, 0, self.IY + self.B * self.KY)
        g.add_color_stop_rgb(0, 0.42, 0.74, 0.32)
        g.add_color_stop_rgb(1, 0.5, 0.82, 0.36)
        c.set_source(g)
        c.fill()
        c.append_path(top)
        c.set_source_rgba(0.2, 0.45, 0.18, 0.9)
        c.set_line_width(3)
        c.stroke()
        # grass tufts along the front rim
        for p in front[::3]:
            for j in range(3):
                x = p[0] + rnd.uniform(-6, 6)
                c.move_to(x, p[1] + 10)
                c.line_to(x + rnd.uniform(-5, 5), p[1] + 22 + rnd.uniform(0, 10))
                c.set_source_rgba(0.25, 0.55, 0.22, 0.9)
                c.set_line_width(2.5)
                c.stroke()
        self._origin = (x0, y0, sup)
        _CACHE["island"] = s
        _CACHE["island_o"] = (x0, y0, sup)
        return s

    def draw_base(self, cx, alpha=1.0):
        s = self.base_surface()
        x0, y0, sup = _CACHE["island_o"]
        cx.save()
        cx.translate(x0, y0)
        cx.scale(1 / sup, 1 / sup)
        cx.set_source_surface(s, 0, 0)
        cx.get_source().set_filter(cairo.FILTER_GOOD)
        cx.paint_with_alpha(alpha)
        cx.restore()

    # ---------------------------------------------------------------- fields
    def field(self, cx, u0, v0, Lu, Lv, kind, grow=1.0, alpha=1.0):
        """Soccer field in plane coords (caller has applied the plane transform)."""
        if grow <= 0 or alpha <= 0:
            return
        cx.save()
        cu, cv = u0 + Lu / 2, v0 + Lv / 2
        cx.translate(cu, cv)
        cx.scale(grow, grow)
        cx.translate(-cu, -cv)
        cx.push_group()
        n = 12 if kind == "full" else 6
        for i in range(n):
            cx.rectangle(u0 + Lu * i / n, v0, Lu / n + 0.5, Lv)
            cx.set_source_rgb(*((0.36, 0.72, 0.3) if i % 2 == 0 else (0.31, 0.65, 0.27)))
            cx.fill()
        m = Lu / (105 if kind == "full" else 52.5)  # px per metre
        lw = 2.6

        def stroke():
            cx.set_source_rgba(1, 1, 1, 0.92)
            cx.set_line_width(lw)
            cx.stroke()
        cx.rectangle(u0 + 3, v0 + 3, Lu - 6, Lv - 6)
        stroke()
        mid_v = v0 + Lv / 2
        ends = [u0, u0 + Lu] if kind == "full" else [u0]
        if kind == "full":
            cx.move_to(u0 + Lu / 2, v0 + 3)
            cx.line_to(u0 + Lu / 2, v0 + Lv - 3)
            stroke()
            cx.arc(u0 + Lu / 2, mid_v, 9.15 * m, 0, TAU)
            stroke()
            cx.arc(u0 + Lu / 2, mid_v, 2.5, 0, TAU)
            cx.set_source_rgba(1, 1, 1, 0.92)
            cx.fill()
        else:
            cx.arc(u0 + Lu - 3, mid_v, 9.15 * m, math.pi / 2, 3 * math.pi / 2)
            stroke()
        for e in ends:
            sgn = 1 if e == u0 else -1
            ee = e + 3 * sgn
            cx.rectangle(min(ee, ee + sgn * 16.5 * m), mid_v - 20.15 * m, 16.5 * m, 40.3 * m)
            stroke()
            cx.rectangle(min(ee, ee + sgn * 5.5 * m), mid_v - 9.15 * m, 5.5 * m, 18.3 * m)
            stroke()
            cx.arc(ee + sgn * 11 * m, mid_v, 2.2, 0, TAU)
            cx.set_source_rgba(1, 1, 1, 0.92)
            cx.fill()
            # goal
            cx.rectangle(min(ee, ee - sgn * 2.4 * m), mid_v - 3.66 * m, 2.4 * m, 7.32 * m)
            cx.set_source_rgba(1, 1, 1, 0.7)
            cx.fill()
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
        cx.restore()

    def draw_fields(self, cx, grows, alpha=1.0):
        cx.save()
        cx.translate(self.IX, self.IY)
        cx.scale(1, self.KY)
        for (u0, v0, Lu, Lv, kind), g in zip(self.FIELDS, grows):
            self.field(cx, u0, v0, Lu, Lv, kind, g, alpha)
        cx.restore()

    def field_badges(self, cx, pops, labels=("1", "2", "½")):
        for (u0, v0, Lu, Lv, kind), p, lab in zip(self.FIELDS, pops, labels):
            if p <= 0:
                continue
            x, y = self.S(u0 + Lu / 2, v0 + Lv / 2)
            y -= 8
            s = back_out(p)
            cx.save()
            cx.translate(x, y)
            cx.scale(s, s)
            cx.arc(0, 3, 30, 0, TAU)
            cx.set_source_rgba(0, 0, 0, 0.25)
            cx.fill()
            cx.arc(0, 0, 30, 0, TAU)
            cx.set_source_rgba(1.0, 200 / 255, 87 / 255, 1)
            cx.fill_preserve()
            cx.set_source_rgba(0.06, 0.06, 0.08, 1)
            cx.set_line_width(4)
            cx.stroke()
            outlined(cx, lab, 0, 13, 36, fill=(0.06, 0.06, 0.08, 1), ow=0, shadow=False)
            cx.restore()


ISLAND = Island()


# ====================================================================== trees
def tree_sprite(var):
    key = ("tree", var)
    if key in _CACHE:
        return _CACHE[key]
    rnd = random.Random(var * 31 + 7)
    w, h = 90, 120
    s = _surface(w * SPR, h * SPR)
    c = cairo.Context(s)
    c.scale(SPR, SPR)
    bx, by = w / 2, h - 6
    conifer = var % 4 == 3
    greens = [hexc("#3f9d3c"), hexc("#4caf45"), hexc("#2f8a3a"), hexc("#5bb84a"), hexc("#3a9447"), hexc("#68be4f")]
    base = greens[var % len(greens)]
    # trunk
    c.move_to(bx - 4.5, by)
    c.line_to(bx - 3, by - 34)
    c.line_to(bx + 3, by - 34)
    c.line_to(bx + 4.5, by)
    c.close_path()
    g = cairo.LinearGradient(bx - 5, 0, bx + 5, 0)
    g.add_color_stop_rgb(0, 0.5, 0.33, 0.2)
    g.add_color_stop_rgb(1, 0.33, 0.2, 0.12)
    c.set_source(g)
    c.fill()
    if conifer:
        dark = shade(hexc("#2e7d47"), -0.1)
        for k in range(4):
            yb = by - 14 - k * 17
            half = 30 - k * 6
            c.move_to(bx - half, yb)
            c.curve_to(bx - half * 0.5, yb - 4, bx - 6, yb - 30, bx, yb - 34)
            c.curve_to(bx + 6, yb - 30, bx + half * 0.5, yb - 4, bx + half, yb)
            c.close_path()
            g = cairo.LinearGradient(bx - half, yb - 30, bx + half, yb)
            g.add_color_stop_rgb(0, 0.36, 0.66, 0.42)
            g.add_color_stop_rgb(0.5, 0.2, 0.52, 0.32)
            g.add_color_stop_rgb(1, *dark[:3])
            c.set_source(g)
            c.fill()
    else:
        blobs = []
        for k in range(rnd.randint(5, 7)):
            ang = rnd.uniform(0, TAU)
            d = rnd.uniform(0, 15)
            blobs.append((bx + math.cos(ang) * d * 1.2, by - 58 + math.sin(ang) * d * 0.8, rnd.uniform(15, 21)))
        # dark under-layer
        for x, y, r in blobs:
            c.arc(x + 2, y + 4, r, 0, TAU)
            c.set_source_rgb(*shade(base, -0.35)[:3])
            c.fill()
        for x, y, r in sorted(blobs, key=lambda b: b[1]):
            g = cairo.RadialGradient(x - r * 0.4, y - r * 0.5, r * 0.1, x, y, r * 1.05)
            g.add_color_stop_rgb(0, *shade(base, 0.35)[:3])
            g.add_color_stop_rgb(0.6, *base[:3])
            g.add_color_stop_rgb(1, *shade(base, -0.25)[:3])
            c.arc(x, y, r, 0, TAU)
            c.set_source(g)
            c.fill()
        for _ in range(6):
            x, y = bx + rnd.uniform(-18, 14), by - 58 + rnd.uniform(-18, 6)
            c.arc(x, y, rnd.uniform(1.5, 3), 0, TAU)
            c.set_source_rgba(1, 1, 0.85, 0.45)
            c.fill()
        if var % 5 == 1:  # a few fruit/blossom dots
            for _ in range(5):
                x, y = bx + rnd.uniform(-20, 20), by - 58 + rnd.uniform(-16, 14)
                c.arc(x, y, 2.6, 0, TAU)
                c.set_source_rgb(0.95, 0.4, 0.35)
                c.fill()
    _CACHE[key] = s
    return s


def forest_layout(n=375, seed=21):
    if "forest" in _CACHE:
        return _CACHE["forest"]
    I = ISLAND
    rnd = random.Random(seed)
    pts = []
    tries = 0
    rmin = 25.0
    while len(pts) < n and tries < 60000:
        tries += 1
        u = rnd.uniform(-I.A, I.A)
        v = rnd.uniform(-I.B, I.B)
        if not I.inside(u, v, 0.9):
            continue
        hu, hv = I.HERO_UV
        if hu - 190 < u < hu + 175 and v > hv - 95:      # the glade in front of you
            continue
        if any((u - a) ** 2 + (v - b) ** 2 < rmin ** 2 for a, b, _, _, _ in pts):
            if tries > 30000:
                rmin = 21.0
            continue
        var = rnd.randrange(12)
        sc = rnd.uniform(0.8, 1.1)
        order = (u + I.A) / (2 * I.A) * 0.75 + rnd.random() * 0.25    # spreads left -> right
        pts.append((u, v, var, sc, order))
    ranks = sorted(range(len(pts)), key=lambda i: pts[i][4])
    out = [None] * len(pts)
    for r, i in enumerate(ranks):
        u, v, var, sc, _ = pts[i]
        out[i] = (u, v, var, sc, r / max(1, len(pts) - 1))
    _CACHE["forest"] = out
    return out


def draw_trees(cx, t, grown, items_front=None, night=0.0):
    """grown: fraction of the 375 trees grown. items_front: list of (v, draw_fn) to interleave by depth."""
    I = ISLAND
    trees = forest_layout()
    n_total = len(trees)
    shown = grown * n_total
    entries = []
    for u, v, var, sc, rank in trees:
        k = rank * (n_total - 1)
        g = (shown - k) / 6.0          # each tree takes a few 'slots' to grow
        if g <= 0:
            continue
        entries.append((v, ("tree", u, v, var, sc, min(1.0, g))))
    for v, fn in (items_front or []):
        entries.append((v, ("fn", fn)))
    entries.sort(key=lambda e: e[0])
    # ground shadows first
    for v, e in entries:
        if e[0] != "tree":
            continue
        _, u, v_, var, sc, g = e
        x, y = I.S(u, v_)
        cx.save()
        cx.translate(x + 3, y + 1)
        cx.scale(1, 0.35)
        cx.arc(0, 0, 20 * sc * g, 0, TAU)
        cx.restore()
        cx.set_source_rgba(0.1, 0.25, 0.08, 0.28)
        cx.fill()
    for v, e in entries:
        if e[0] == "fn":
            e[1](cx)
            continue
        _, u, v_, var, sc, g = e
        x, y = I.S(u, v_)
        gs = back_out(g, 2.2) if g < 1 else 1.0
        sway = math.sin(t * 1.4 + u * 0.05) * 0.03
        cx.save()
        cx.translate(x, y)
        cx.rotate(sway)
        blit(cx, tree_sprite(var), 0, 0, sc * 0.82 * gs, 1.0)
        cx.restore()


# ====================================================================== hero
def hero(cx, t, x, y, s=0.3, mood="smile", look=(0, 0), wave=0.0, arms=None):
    p = Pose(x=x, y=y, s=s, f=1, view="front", mouth=mood, look=look, t=t, blink_seed=3,
             arm_a=12, arm_b=-12, elb_a=8, elb_b=-8)
    p = p.but(bob=math.sin(t * 2.4) * 1.5, arm_a=12 + math.sin(t * 2.4 + 0.5) * 2)
    if wave > 0:
        p = p.but(arm_b=-150 * wave + 12 * (1 - wave), elb_b=-25 + 25 * math.sin(t * 12) * wave)
    if arms:
        p = p.but(**arms)
    # contact shadow
    cx.save()
    cx.translate(x, y)
    cx.scale(1, 0.3)
    cx.arc(0, 0, 70 * s * 1.3, 0, TAU)
    cx.restore()
    cx.set_source_rgba(0.08, 0.2, 0.06, 0.3)
    cx.fill()
    return HERO.draw(cx, p)


# ====================================================================== birds & chickens
BIRD_COLS = [("#2f7de1", "#f4f4f4"), ("#e2483d", "#ffd2b0"), ("#f2c230", "#3a3a3a"),
             ("#7a4fd6", "#e8dcff"), ("#2eae7a", "#f6e6a8"), ("#ef8a2c", "#ffe7c4")]


def bird(cx, x, y, s, t, k, facing=1, alpha=1.0):
    body, belly = hexc(BIRD_COLS[k % 6][0]), hexc(BIRD_COLS[k % 6][1])
    flap = math.sin(t * 13 + k * 1.7)
    cx.save()
    cx.translate(x, y)
    cx.scale(s * facing, s)
    if alpha < 1:
        cx.push_group()
    # far wing
    cx.move_to(-2, -4)
    cx.curve_to(-8, -20 * flap - 6, -24, -26 * flap - 4, -30, -22 * flap)
    cx.curve_to(-18, -6, -10, 0, -2, -4)
    src(cx, shade(body, -0.25))
    cx.fill()
    # body
    cx.save()
    cx.scale(1.0, 0.72)
    cx.arc(0, 0, 18, 0, TAU)
    cx.restore()
    g = cairo.LinearGradient(0, -14, 0, 14)
    g.add_color_stop_rgba(0, *body)
    g.add_color_stop_rgba(1, *shade(body, -0.2))
    cx.set_source(g)
    cx.fill()
    cx.save()
    cx.translate(4, 5)
    cx.scale(1.0, 0.5)
    cx.arc(0, 0, 12, 0, TAU)
    cx.restore()
    src(cx, belly)
    cx.fill()
    # tail
    cx.move_to(-14, -3)
    cx.line_to(-30, -9)
    cx.line_to(-28, 3)
    cx.close_path()
    src(cx, shade(body, -0.15))
    cx.fill()
    # head
    cx.arc(14, -9, 10, 0, TAU)
    src(cx, body)
    cx.fill()
    cx.arc(17, -11, 2.6, 0, TAU)
    cx.set_source_rgb(0.05, 0.05, 0.08)
    cx.fill()
    cx.arc(17.6, -11.8, 0.9, 0, TAU)
    cx.set_source_rgb(1, 1, 1)
    cx.fill()
    cx.move_to(22, -11)
    cx.line_to(31, -8)
    cx.line_to(22, -5)
    cx.close_path()
    cx.set_source_rgb(0.98, 0.7, 0.2)
    cx.fill()
    # near wing
    cx.move_to(0, -4)
    cx.curve_to(4, -22 * flap - 8, -12, -32 * flap - 6, -22, -28 * flap - 2)
    cx.curve_to(-12, -4, -6, 2, 0, -4)
    src(cx, shade(body, 0.15))
    cx.fill()
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


def chicken(cx, x, y, s, t, k, facing=1, alpha=1.0):
    peck = max(0.0, math.sin(t * 3.2 + k * 2.1)) ** 6
    bob = math.sin(t * 6 + k) * 0.6
    cx.save()
    cx.translate(x, y)
    cx.scale(s * facing, s)
    if alpha < 1:
        cx.push_group()
    cx.save()
    cx.scale(1, 0.3)
    cx.arc(0, 0, 24, 0, TAU)
    cx.restore()
    cx.set_source_rgba(0.1, 0.2, 0.05, 0.3)
    cx.fill()
    # legs
    for dx in (-5, 5):
        cx.move_to(dx, -14)
        cx.line_to(dx + 1, 0)
        cx.set_source_rgb(0.95, 0.65, 0.15)
        cx.set_line_width(3)
        cx.stroke()
    # tail feathers
    cx.move_to(-14, -26)
    cx.curve_to(-30, -48, -34, -30, -26, -20)
    cx.close_path()
    cx.set_source_rgb(0.86, 0.86, 0.84)
    cx.fill()
    # body
    cx.save()
    cx.translate(0, -26 + bob)
    cx.scale(1.0, 0.78)
    cx.arc(0, 0, 21, 0, TAU)
    cx.restore()
    g = cairo.RadialGradient(-6, -36, 4, 0, -26, 24)
    g.add_color_stop_rgb(0, 1, 1, 1)
    g.add_color_stop_rgb(1, 0.82, 0.82, 0.8)
    cx.set_source(g)
    cx.fill_preserve()
    cx.set_source_rgba(0.4, 0.4, 0.45, 0.6)
    cx.set_line_width(1.5)
    cx.stroke()
    cx.move_to(-10, -28)
    cx.curve_to(-2, -20, 6, -22, 10, -30)
    cx.set_source_rgba(0.7, 0.7, 0.7, 0.8)
    cx.set_line_width(2)
    cx.stroke()
    # neck/head (pecks down)
    hx, hy = 15 + 8 * peck, -44 + 30 * peck + bob
    cx.move_to(8, -34)
    cx.line_to(hx, hy)
    cx.set_source_rgb(0.97, 0.97, 0.95)
    cx.set_line_width(12)
    cx.stroke()
    cx.arc(hx, hy, 9, 0, TAU)
    cx.set_source_rgb(1, 1, 1)
    cx.fill()
    # comb + wattle
    for i in range(3):
        cx.arc(hx - 4 + i * 4, hy - 9, 3.6, 0, TAU)
    cx.set_source_rgb(0.9, 0.18, 0.2)
    cx.fill()
    cx.arc(hx + 6, hy + 7, 3.2, 0, TAU)
    cx.fill()
    cx.move_to(hx + 7, hy - 2)
    cx.line_to(hx + 15, hy + 1)
    cx.line_to(hx + 7, hy + 3)
    cx.close_path()
    cx.set_source_rgb(0.98, 0.72, 0.15)
    cx.fill()
    cx.arc(hx + 2, hy - 2, 1.8, 0, TAU)
    cx.set_source_rgb(0.05, 0.05, 0.08)
    cx.fill()
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


# ====================================================================== gold
GOLD_HI, GOLD, GOLD_LO = hexc("#fff1a8"), hexc("#f5c542"), hexc("#b07a12")


def gold_bar(cx, x, y, s=1.0, t=0.0, glint=0.0):
    """Small ingot resting on the ground at (x, y)."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.save()
    cx.scale(1, 0.3)
    cx.arc(0, 0, 40, 0, TAU)
    cx.restore()
    cx.set_source_rgba(0.1, 0.15, 0.05, 0.35)
    cx.fill()
    # front face (trapezoid)
    fl, fr, top_in, hgt, dep = -34, 34, 7, 20, 14
    cx.move_to(fl, 0)
    cx.line_to(fr, 0)
    cx.line_to(fr - top_in, -hgt)
    cx.line_to(fl + top_in, -hgt)
    cx.close_path()
    g = cairo.LinearGradient(0, -hgt, 0, 0)
    g.add_color_stop_rgba(0, *GOLD)
    g.add_color_stop_rgba(1, *GOLD_LO)
    cx.set_source(g)
    cx.fill()
    # right side face
    cx.move_to(fr, 0)
    cx.line_to(fr + dep * 0.7, -dep * 0.5)
    cx.line_to(fr + dep * 0.7 - top_in, -hgt - dep * 0.5)
    cx.line_to(fr - top_in, -hgt)
    cx.close_path()
    src(cx, shade(GOLD_LO, -0.15))
    cx.fill()
    # top face
    cx.move_to(fl + top_in, -hgt)
    cx.line_to(fr - top_in, -hgt)
    cx.line_to(fr - top_in + dep * 0.7, -hgt - dep * 0.5)
    cx.line_to(fl + top_in + dep * 0.7, -hgt - dep * 0.5)
    cx.close_path()
    g = cairo.LinearGradient(fl, -hgt, fr, -hgt - dep)
    g.add_color_stop_rgba(0, *GOLD_HI)
    g.add_color_stop_rgba(1, *GOLD)
    cx.set_source(g)
    cx.fill()
    # moving sheen across the front
    sx = -60 + 140 * ((t * 0.6) % 1.0)
    cx.save()
    cx.move_to(fl, 0)
    cx.line_to(fr, 0)
    cx.line_to(fr - top_in, -hgt)
    cx.line_to(fl + top_in, -hgt)
    cx.close_path()
    cx.clip()
    cx.move_to(sx, 0)
    cx.line_to(sx + 10, 0)
    cx.line_to(sx + 22, -hgt)
    cx.line_to(sx + 12, -hgt)
    cx.close_path()
    cx.set_source_rgba(1, 1, 0.9, 0.55)
    cx.fill()
    cx.restore()
    # stamp
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(10)
    e = cx.text_extents("27 g")
    cx.move_to(-e.x_advance / 2, -6)
    cx.set_source_rgba(0.55, 0.36, 0.05, 0.85)
    cx.show_text("27 g")
    cx.move_to(fl, 0)
    cx.line_to(fr, 0)
    cx.line_to(fr + dep * 0.7, -dep * 0.5)
    cx.line_to(fr + dep * 0.7 - top_in, -hgt - dep * 0.5)
    cx.line_to(fl + top_in + dep * 0.7, -hgt - dep * 0.5)
    cx.line_to(fl + top_in, -hgt)
    cx.close_path()
    cx.set_source_rgba(0.35, 0.22, 0.02, 0.8)
    cx.set_line_width(1.6)
    cx.stroke()
    if glint > 0:
        sparkle(cx, fr - 12, -hgt - 8, 14 * glint, t)
    cx.restore()


def sparkle(cx, x, y, r, t, alpha=1.0):
    k = 0.75 + 0.25 * math.sin(t * 9)
    cx.save()
    cx.translate(x, y)
    cx.rotate(t * 0.8)
    for a in range(4):
        cx.rotate(math.pi / 2)
        cx.move_to(0, 0)
        cx.line_to(r * 0.18, r * 0.18)
        cx.line_to(0, r * k)
        cx.line_to(-r * 0.18, r * 0.18)
        cx.close_path()
    cx.set_source_rgba(1, 1, 0.92, 0.95 * alpha)
    cx.fill()
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r * 0.8)
    g.add_color_stop_rgba(0, 1, 1, 0.8, 0.7 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 0.8, 0)
    cx.arc(0, 0, r * 0.8, 0, TAU)
    cx.set_source(g)
    cx.fill()
    cx.restore()


def gold_cube(cx, x, y, size, t, alpha=1.0):
    """Big gold cube, (x, y) = centre of the bottom-front edge."""
    a = size
    dx, dy = a * 0.55, a * 0.32
    cx.save()
    cx.translate(x, y)
    if alpha < 1:
        cx.push_group()
    # front
    cx.rectangle(-a / 2, -a, a, a)
    g = cairo.LinearGradient(0, -a, 0, 0)
    g.add_color_stop_rgba(0, *GOLD)
    g.add_color_stop_rgba(1, *GOLD_LO)
    cx.set_source(g)
    cx.fill()
    # right
    cx.move_to(a / 2, 0)
    cx.line_to(a / 2 + dx, -dy)
    cx.line_to(a / 2 + dx, -a - dy)
    cx.line_to(a / 2, -a)
    cx.close_path()
    g = cairo.LinearGradient(a / 2, 0, a / 2 + dx, 0)
    g.add_color_stop_rgba(0, *shade(GOLD_LO, -0.05))
    g.add_color_stop_rgba(1, *shade(GOLD_LO, -0.3))
    cx.set_source(g)
    cx.fill()
    # top
    cx.move_to(-a / 2, -a)
    cx.line_to(a / 2, -a)
    cx.line_to(a / 2 + dx, -a - dy)
    cx.line_to(-a / 2 + dx, -a - dy)
    cx.close_path()
    g = cairo.LinearGradient(-a / 2, -a, a / 2 + dx, -a - dy)
    g.add_color_stop_rgba(0, *GOLD_HI)
    g.add_color_stop_rgba(1, *GOLD)
    cx.set_source(g)
    cx.fill()
    # sheen sweep on the front
    sx = -a + 2.4 * a * ((t * 0.45) % 1.0)
    cx.save()
    cx.rectangle(-a / 2, -a, a, a)
    cx.clip()
    cx.move_to(sx, 0)
    cx.line_to(sx + a * 0.12, 0)
    cx.line_to(sx + a * 0.42, -a)
    cx.line_to(sx + a * 0.3, -a)
    cx.close_path()
    cx.set_source_rgba(1, 1, 0.9, 0.35)
    cx.fill()
    cx.restore()
    # edges
    cx.set_source_rgba(0.4, 0.25, 0.02, 0.9)
    cx.set_line_width(3)
    cx.rectangle(-a / 2, -a, a, a)
    cx.stroke()
    cx.move_to(a / 2, 0)
    cx.line_to(a / 2 + dx, -dy)
    cx.line_to(a / 2 + dx, -a - dy)
    cx.line_to(-a / 2 + dx, -a - dy)
    cx.line_to(-a / 2, -a)
    cx.stroke()
    cx.move_to(a / 2, -a)
    cx.line_to(a / 2 + dx, -a - dy)
    cx.set_source_rgba(1, 1, 0.85, 0.7)
    cx.stroke()
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


# ====================================================================== magnifier
def magnifier(cx, x, y, R, ang=0.7, alpha=1.0, content=None):
    """Lens centred at (x, y), radius R; handle toward `ang` (rad, from +x, y down).
    content(cx) draws what is seen through the lens (already clipped)."""
    cx.save()
    if alpha < 1:
        cx.push_group()
    hx, hy = math.cos(ang), math.sin(ang)
    # handle
    x0, y0 = x + hx * R * 1.08, y + hy * R * 1.08
    x1, y1 = x + hx * R * 2.25, y + hy * R * 2.25
    cx.move_to(x0, y0)
    cx.line_to(x1, y1)
    cx.set_source_rgba(0.1, 0.07, 0.06, 1)
    cx.set_line_width(R * 0.24)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.move_to(x0 + hx * R * 0.3, y0 + hy * R * 0.3)
    cx.line_to(x1, y1)
    cx.set_source_rgba(0.45, 0.25, 0.15, 1)
    cx.set_line_width(R * 0.17)
    cx.stroke()
    # lens content
    cx.save()
    cx.arc(x, y, R, 0, TAU)
    cx.clip()
    if content:
        content(cx)
    g = cairo.RadialGradient(x - R * 0.4, y - R * 0.45, R * 0.05, x, y, R)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.28)
    g.add_color_stop_rgba(0.5, 0.85, 0.95, 1, 0.06)
    g.add_color_stop_rgba(1, 0.4, 0.6, 0.8, 0.22)
    cx.set_source(g)
    cx.paint()
    cx.arc(x - R * 0.3, y - R * 0.35, R * 0.55, math.pi * 1.05, math.pi * 1.55)
    cx.set_source_rgba(1, 1, 1, 0.55)
    cx.set_line_width(R * 0.06)
    cx.stroke()
    cx.restore()
    # rim
    cx.arc(x, y, R, 0, TAU)
    g = cairo.LinearGradient(x - R, y - R, x + R, y + R)
    g.add_color_stop_rgb(0, 0.92, 0.92, 0.96)
    g.add_color_stop_rgb(0.5, 0.55, 0.57, 0.65)
    g.add_color_stop_rgb(1, 0.3, 0.32, 0.38)
    cx.set_source(g)
    cx.set_line_width(R * 0.11)
    cx.stroke()
    cx.arc(x, y, R * 1.055, 0, TAU)
    cx.set_source_rgba(0.1, 0.1, 0.14, 1)
    cx.set_line_width(3)
    cx.stroke()
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


# ====================================================================== ant close-up
def _ground_tile():
    if "ground" in _CACHE:
        return _CACHE["ground"]
    size = 1400
    s = _surface(size, size)
    c = cairo.Context(s)
    g = cairo.RadialGradient(size / 2, size / 2, 100, size / 2, size / 2, size * 0.7)
    g.add_color_stop_rgb(0, 0.62, 0.47, 0.32)
    g.add_color_stop_rgb(1, 0.46, 0.34, 0.23)
    c.set_source(g)
    c.paint()
    rnd = random.Random(99)
    for _ in range(5000):
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        r = rnd.uniform(1, 3.5)
        c.arc(x, y, r, 0, TAU)
        v = rnd.uniform(-0.12, 0.12)
        c.set_source_rgba(0.55 + v, 0.42 + v, 0.3 + v, 0.6)
        c.fill()
    for _ in range(140):  # pebbles
        x, y, r = rnd.uniform(0, size), rnd.uniform(0, size), rnd.uniform(6, 22)
        c.save()
        c.translate(x, y)
        c.rotate(rnd.uniform(0, 3))
        c.scale(1, rnd.uniform(0.6, 0.9))
        c.arc(2, 4, r, 0, TAU)
        c.set_source_rgba(0.25, 0.17, 0.1, 0.35)
        c.fill()
        c.arc(0, 0, r, 0, TAU)
        g = cairo.RadialGradient(-r * 0.4, -r * 0.4, 1, 0, 0, r)
        tone = rnd.uniform(0.55, 0.8)
        g.add_color_stop_rgb(0, tone + 0.15, tone + 0.12, tone + 0.08)
        g.add_color_stop_rgb(1, tone - 0.2, tone - 0.24, tone - 0.28)
        c.set_source(g)
        c.fill()
        c.restore()
    for _ in range(40):  # fallen leaves
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        c.save()
        c.translate(x, y)
        c.rotate(rnd.uniform(0, TAU))
        L = rnd.uniform(30, 55)
        c.move_to(-L / 2, 0)
        c.curve_to(-L / 4, -L / 3, L / 4, -L / 3, L / 2, 0)
        c.curve_to(L / 4, L / 3, -L / 4, L / 3, -L / 2, 0)
        tone = rnd.choice([(0.55, 0.62, 0.25), (0.75, 0.55, 0.2), (0.45, 0.55, 0.22)])
        c.set_source_rgba(*tone, 0.9)
        c.fill()
        c.move_to(-L / 2, 0)
        c.line_to(L / 2, 0)
        c.set_source_rgba(0.3, 0.25, 0.1, 0.6)
        c.set_line_width(1.5)
        c.stroke()
        c.restore()
    for _ in range(260):  # grass blades
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        if rnd.random() < 0.6:
            continue
        for k in range(rnd.randint(3, 6)):
            h = rnd.uniform(30, 70)
            c.move_to(x + k * 4, y)
            c.curve_to(x + k * 4, y - h * 0.5, x + k * 4 + rnd.uniform(-10, 10), y - h * 0.8,
                       x + k * 4 + rnd.uniform(-16, 16), y - h)
            c.set_source_rgba(0.35, 0.62, 0.25, 0.9)
            c.set_line_width(3)
            c.stroke()
    _CACHE["ground"] = s
    return s


def ant(cx, x, y, ang, s, t, ph):
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    gait = math.sin(t * 22 + ph)
    # legs (tripod gait)
    for side in (-1, 1):
        for j, (ax, spread) in enumerate(((-4, -0.9), (2, 0.0), (7, 0.8))):
            sw = gait * (1 if (j + (side > 0)) % 2 == 0 else -1) * 0.35
            a = side * (math.pi / 2) + spread * side * 0.6 + sw
            kx, ky = ax + math.cos(a - side * 0.5) * 9 * 0.8, math.sin(a - side * 0.5) * 9
            fx, fy = kx + math.cos(a + side * 0.3 * spread) * 10, ky + math.sin(a + side * 0.3 * spread) * 9
            cx.move_to(ax, 0)
            cx.line_to(kx, ky)
            cx.line_to(fx, fy)
            cx.set_source_rgba(0.08, 0.05, 0.04, 1)
            cx.set_line_width(1.6)
            cx.stroke()
    # body: abdomen, petiole, thorax, head
    for bx, rx, ry in ((-12, 8.5, 6.5), (0, 5.2, 3.6), (10.5, 5.2, 4.8)):
        cx.save()
        cx.translate(bx, 0)
        cx.scale(rx, ry)
        cx.arc(0, 0, 1, 0, TAU)
        cx.restore()
        cx.set_source_rgb(0.12, 0.06, 0.04)
        cx.fill()
        cx.save()
        cx.translate(bx - rx * 0.25, -ry * 0.35)
        cx.scale(rx * 0.45, ry * 0.3)
        cx.arc(0, 0, 1, 0, TAU)
        cx.restore()
        cx.set_source_rgba(1, 0.85, 0.75, 0.35)
        cx.fill()
    # antennae
    wig = math.sin(t * 9 + ph) * 0.25
    for side in (-1, 1):
        cx.move_to(14, side * 2)
        cx.line_to(19, side * 6 + wig * 4)
        cx.line_to(25, side * 4 + wig * 8)
        cx.set_source_rgb(0.1, 0.06, 0.04)
        cx.set_line_width(1.2)
        cx.stroke()
    cx.restore()


def ant_field(n=190, seed=4):
    key = ("ants", n, seed)
    if key in _CACHE:
        return _CACHE[key]
    rnd = random.Random(seed)
    ants = []
    for i in range(n):
        trail = i < n * 0.3
        if trail:  # a winding ant highway
            ants.append(("trail", rnd.uniform(0, 1), rnd.uniform(-17, 17), rnd.uniform(0.9, 1.15),
                         rnd.uniform(0, 6), 1 if rnd.random() < 0.6 else -1))
        else:
            ants.append(("wander", rnd.uniform(-900, 900), rnd.uniform(-900, 900), rnd.uniform(0.85, 1.15),
                         rnd.uniform(0, 6), rnd.uniform(0, TAU)))
    _CACHE[key] = ants
    return ants


def _trail_xy(u):
    x = -900 + 1800 * u
    y = 120 * math.sin(u * 5.5) - 60 + 160 * math.sin(u * 2.1 + 1)
    dx = 1520
    dy = 120 * 5.5 * math.cos(u * 5.5) + 160 * 2.1 * math.cos(u * 2.1 + 1)
    return x, y, math.atan2(dy, dx)


def ground_closeup(cx, t, cx0, cy0, scale=1.0, density=1.0):
    """Magnified ground with walking ants, centred at (cx0, cy0)."""
    tile = _ground_tile()
    cx.save()
    cx.translate(cx0, cy0)
    cx.scale(scale, scale)
    pat = cairo.SurfacePattern(tile)
    pat.set_extend(cairo.EXTEND_REFLECT)
    m = cairo.Matrix()
    m.translate(700, 700)
    pat.set_matrix(m)
    cx.set_source(pat)
    cx.paint()
    ants = ant_field()
    nshow = int(len(ants) * density)
    for i, a in enumerate(ants[:nshow]):
        if a[0] == "trail":
            _, u0, off, sc, ph, d = a
            u = (u0 + d * t * 0.045) % 1.0
            x, y, ang = _trail_xy(u)
            nx, ny = -math.sin(ang), math.cos(ang)
            x += nx * off * 2.2
            y += ny * off * 2.2
            if d < 0:
                ang += math.pi
            ant(cx, x, y, ang, 1.35 * sc, t, ph)
        else:
            _, x0, y0, sc, ph, a0 = a
            ang = a0 + math.sin(t * 0.7 + ph) * 0.9
            sp = 38 * sc
            x = x0 + math.cos(a0) * sp * t * 0.6 + math.sin(t * 0.7 + ph) * 25
            y = y0 + math.sin(a0) * sp * t * 0.6
            x = (x + 900) % 1800 - 900
            y = (y + 900) % 1800 - 900
            ant(cx, x, y, ang + math.cos(t * 0.7 + ph) * 0.4, 1.3 * sc, t, ph)
    cx.restore()


def you_tag(cx, x, y, alpha=1.0, s=1.0):
    """Small red 'YOU' tag floating above the mascot's head; (x, y) = tip of the pointer."""
    if alpha <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    w, h = 74, 38
    rrect(cx, -w / 2, -h - 12, w, h, 12)
    cx.move_to(-9, -13)
    cx.line_to(0, 0)
    cx.line_to(9, -13)
    cx.close_path()
    cx.set_source_rgba(0.93, 0.22, 0.32, alpha)
    cx.fill_preserve()
    cx.set_source_rgba(0.06, 0.06, 0.08, alpha)
    cx.set_line_width(3.5)
    cx.stroke()
    outlined(cx, "YOU", 0, -h / 2 - 12 + 9, 25, ow=0, shadow=False, alpha=alpha)
    cx.restore()

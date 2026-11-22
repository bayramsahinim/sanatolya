"""Shot list for the Troy episode. Every shot is anchored to narration word times (timing.json).

Each Shot draws, back to front:
  set layers (parallax <= 1) -> back() [world] -> chars() [world, sticker halo] -> front() [world]
  -> near layers (parallax > 1, blurred) -> post() [screen] -> grade
"""
import json
import math
import os
import random

import cairo

from cinecode.core import (OUTLINE, back_out, circle, clamp, curve, ease_in, ease_io, ease_out, ellipse, fs,
                           hexc, kf, lerp, line, poly, prog, rrect, shade, smooth, src, text)
from episodes.troy_en import cast as C
from episodes.troy_en import gfx
from episodes.troy_en import world as Wd
from episodes.troy_en.gfx import H, W

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMING = json.load(open(os.path.join(ROOT, "build", "troy_en", "timing.json")))
DUR = TIMING["duration"]
_BY_LINE = {}
for _s, _e, _w, _l in TIMING["words"]:
    _BY_LINE.setdefault(_l, []).append((_s, _e, _w))


def WS(line_id, k):
    return _BY_LINE[line_id][k][0]


def WE(line_id, k):
    return _BY_LINE[line_id][k][1]


INK = OUTLINE


# ================================================================ base
class Shot:
    set = None
    keys = [(0, (540, 960, 1.0))]
    shakes = []
    grade_kind = "day"
    drift = 0.0

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1
        self.J = {}

    def w(self, line_id, k):
        return WS(line_id, k) - self.t0

    def cam(self, t):
        return gfx.cam_kf(t, self.keys, shake_amp=self.drift, shake_t=self.shakes)

    def back(self, cx, t):
        pass

    def chars(self, cx, t):
        pass

    def front(self, cx, t):
        pass

    def post(self, cx, t):
        pass

    def tags(self, t):
        """[(name, text, alpha)] joke captions active at local time t"""
        return []

    sfx = []

    def layers(self, t):
        return Wd.get_set(self.set) if self.set else []

    def render(self, t):
        cam = self.cam(t)
        s = gfx.surface()
        cx = cairo.Context(s)
        L = self.layers(t)
        for l in L:
            if l.par <= 1:
                l.paint(cx, cam)
        cx.save()
        cam.apply(cx)
        self.back(cx, t)
        cx.restore()
        chs = gfx.surface()
        c2 = cairo.Context(chs)
        cam.apply(c2)
        self.chars(c2, t)
        gfx.halo_composite(cx, chs, radius=max(4, 6 * cam.zoom))
        cx.save()
        cam.apply(cx)
        self.front(cx, t)
        cx.restore()
        for l in L:
            if l.par > 1:
                l.paint(cx, cam)
        self.post(cx, t)
        grade(cx, self.grade_kind)
        return s


def grade(cx, kind):
    if kind == "day":
        gfx.grade(cx, (1, 0.93, 0.8, 0.35), (0.6, 0.45, 0.3, 0.25))
        gfx.vignette(cx, 0.38)
    elif kind == "night":
        gfx.grade(cx, (0.3, 0.4, 0.8, 0.45), (0.15, 0.2, 0.45, 0.5), op=cairo.OPERATOR_SOFT_LIGHT)
        gfx.vignette(cx, 0.6, (0.02, 0.03, 0.08))
    elif kind == "inside":
        gfx.grade(cx, (1, 0.75, 0.45, 0.3), (0.3, 0.15, 0.05, 0.4))
        gfx.vignette(cx, 0.65)
    elif kind == "inside_night":
        gfx.grade(cx, (0.4, 0.45, 0.8, 0.4), (0.1, 0.08, 0.2, 0.5))
        gfx.vignette(cx, 0.7, (0.02, 0.02, 0.05))


P = C.pose


def walk_x(t, a, b, x0, x1):
    return lerp(x0, x1, smooth(prog(t, a, b)))


# ================================================================ HOOK
class S01_HorseReveal(Shot):
    """Low angle on the wheels, tilt up to the giant horse; Greeks trudge off to the ships."""
    set = "beach"
    keys = [(0, (560, 1420, 1.55)), (2.6, (560, 900, 1.0))]
    sfx = [(0.0, "wind", 0.6), (0.1, "creak", 0.5), (1.4, "gull", 0.4)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 600, 1380, 0.8)
        gfx.contact_shadow(cx, 600, 1385, 420, 0.45)
        Wd.horse(cx, 600, 1380, 0.8, t=t)

    def chars(self, cx, t):
        for i, (x0, y, s) in enumerate(((760, 1250, 0.62), (880, 1230, 0.58), (1000, 1215, 0.55))):
            x = x0 + t * 70
            p = C.walk(P(x, y, t, s=s, f=1, seed=i, mouth="flat", eyes="half"), t + i * 0.3, 1.2)
            C.greek_soldier(i).draw(cx, p)


class S02_Bow(Shot):
    """Gift bow pops onto the horse's neck with a tag: TO: TROY."""
    set = "beach"
    keys = [(0, (520, 800, 1.6)), (1.5, (510, 830, 1.75))]
    sfx = [(0.12, "pop", 0.9), (0.2, "sparkle", 0.5)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 600, 1380, 0.8)
        b = back_out(prog(t, 0.08, 0.38))
        Wd.horse(cx, 600, 1380, 0.8, t=t, bow=b, tag=("TO:", "TROY") if t > 0.3 else None)

    def post(self, cx, t):
        if t > 0.1:
            k = max(0, 1 - (t - 0.1) / 0.6)
            gfx.glow(cx, 520, 880, 380, (1, 0.95, 0.7), 0.5 * k)


class S03_SailHome(Shot):
    set = "sea"
    keys = [(0, (540, 960, 1.05)), (1.4, (600, 960, 1.12))]
    sfx = [(0.0, "waves", 0.7), (0.2, "sail", 0.5)]

    def back(self, cx, t):
        for i, (x, y, s) in enumerate(((330, 1180, 0.62), (720, 1060, 0.4), (930, 1010, 0.26))):
            Wd.ship(cx, x + t * 90 * s, y, s, f=1, t=t + i)

    def chars(self, cx, t):
        # a cheerful Greek waving goodbye from the stern of the nearest ship
        x = 330 + t * 90 * 0.62 - 120
        y = 1180 - 0.62 * 60 + math.sin(t * 2.0 + 330 * 0.01) * 6 * 0.62
        wave = math.sin(t * 12) * 25
        C.greek_soldier(0).draw(cx, P(x, y, t, s=0.55, f=-1, mouth="grin", eyes="happy", arm_b=160 + wave, elb_b=20))


# ================================================================ BEACH
class S04_RushOut(Shot):
    set = "walls"
    keys = [(0, (540, 1000, 1.0)), (1.7, (540, 1060, 1.08))]
    sfx = [(0.0, "gate", 0.6), (0.15, "crowd_run", 0.8)]

    def chars(self, cx, t):
        r = random.Random(4)
        for i in range(7):
            delay = i * 0.14
            u = max(0, t - delay)
            x = 540 + r.uniform(-120, 120) + u * (220 if i % 2 else -200) * r.uniform(0.8, 1.2)
            y = 1170 + u * 260
            s = 0.55 + u * 0.32
            fig = C.trojan_soldier(i) if i % 3 == 0 else C.trojan_citizen(i)
            p = C.run(P(x, y, t, s=s, f=1 if i % 2 else -1, seed=i, mouth="grin", eyes="wide"), t + i * 0.13, 2.4)
            fig.draw(cx, p)


class S05_JustAHorse(Shot):
    set = "beach"
    keys = [(0, (560, 1180, 1.05)), (2.0, (560, 1100, 1.18))]
    sfx = [(0.05, "skid", 0.8)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 600, 1380, 0.8)
        gfx.contact_shadow(cx, 600, 1385, 420, 0.45)
        Wd.horse(cx, 600, 1380, 0.8, t=t)

    def chars(self, cx, t):
        no1, no2, up = self.w("beach", 6), self.w("beach", 8), self.w("beach", 10)
        for i, x in enumerate((260, 430, 640, 820)):
            skid = 1 - ease_out(prog(t, 0, 0.35))
            xx = x - skid * 160
            if t < no2:
                look = (-1, 0) if t > no1 else (0, 0)
                f = -1
            elif t < up:
                look, f = (1, 0), 1
            else:
                look, f = (0, -1), (1 if i < 2 else -1)
            fig = C.trojan_soldier(i) if i % 2 == 0 else C.trojan_citizen(i + 3)
            mouth = "o" if t > up else "flat"
            eyes = "wide" if t > up else "open"
            p = P(xx, 1600 + (i % 2) * 40, t, s=1.15, f=f, seed=i, look=look, mouth=mouth, eyes=eyes,
                  lean=-12 * skid, tilt=-10 if t > up else 0)
            fig.draw(cx, C.breathe(p, t))


class S06_Laocoon(Shot):
    """Laocoön marches in and hurls his spear."""
    set = "beach"
    keys = [(0, (400, 1250, 1.3)), (1.9, (470, 1220, 1.38))]

    @property
    def sfx(self):
        return [(0.0, "step", 0.5), (self.w("spear", 4) - 0.05, "whoosh", 1.0)]

    def chars(self, cx, t):
        throw = self.w("spear", 4)
        x = walk_x(t, 0, 0.9, 160, 380)
        p = P(x, 1520, t, s=1.35, f=1, seed=11, brows="angry", mouth="yell" if t > throw else "frown",
              eyes="angry", mouth_open=1.0)
        if t < 0.9:
            p = C.walk(p, t, 1.4)
        wind = smooth(prog(t, throw - 0.5, throw - 0.1))
        rel = ease_out(prog(t, throw - 0.1, throw + 0.12))
        p = p.but(arm_b=lerp(lerp(10, -150, wind), 100, rel), elb_b=lerp(30, 10, rel), lean=lerp(-8, 14, rel) * wind)
        J = C.LAOCOON.draw(cx, p)
        if t < throw:
            hx, hy = J["hand_b"]
            line(cx, [(hx - 60, hy + 40), (hx + 120, hy - 80)], INK, 14)
            line(cx, [(hx - 60, hy + 40), (hx + 120, hy - 80)], hexc("#8A5A33"), 8)
            poly(cx, [(hx + 112, hy - 92), (hx + 138, hy - 70), (hx + 150, hy - 104)])
            fs(cx, hexc("#B7BEC6"), INK, 4)

    def front(self, cx, t):
        throw = self.w("spear", 4)
        if t >= throw:
            u = t - throw
            x, y = 520 + u * 1800, 1260 - u * 600 + u * u * 300
            cx.save()
            cx.translate(x, y)
            cx.rotate(-0.32 + u * 0.3)
            line(cx, [(-160, 0), (40, 0)], INK, 14)
            line(cx, [(-160, 0), (40, 0)], hexc("#8A5A33"), 8)
            poly(cx, [(40, -14), (40, 14), (86, 0)])
            fs(cx, hexc("#B7BEC6"), INK, 4)
            cx.restore()
            for k in range(4):
                line(cx, [(x - 200 - k * 40, y + 10 + k * 8), (x - 260 - k * 60, y + 14 + k * 8)], (1, 1, 1, 0.6), 5)


class S07_SpearHits(Shot):
    set = "beach"
    keys = [(0, (700, 930, 1.9)), (1.2, (700, 920, 2.0))]
    shakes = [(0.3, 18, 0.35)]
    sfx = [(0.3, "thunk", 1.0), (0.32, "boing_wood", 0.6)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 600, 1380, 0.8)
        hit = 0.3
        Wd.horse(cx, 600, 1380, 0.8, t=t)
        u = prog(t, 0, hit)
        wob = math.sin((t - hit) * 40) * 0.08 * math.exp(-(t - hit) * 5) if t > hit else 0
        tipx, tipy = 700, 930
        cx.save()
        if t < hit:
            cx.translate(lerp(tipx - 700, tipx, u), lerp(tipy - 280, tipy, u))
        else:
            cx.translate(tipx, tipy)
        cx.rotate(0.38 + wob)
        line(cx, [(-420, 0), (0, 0)], INK, 15)
        line(cx, [(-420, 0), (0, 0)], hexc("#8A5A33"), 8)
        cx.restore()
        if t > hit:
            for k in range(8):
                a = k * math.pi / 4
                rr = 30 + (t - hit) * 260
                al = max(0, 1 - (t - hit) * 3)
                line(cx, [(tipx + math.cos(a) * rr, tipy + math.sin(a) * rr),
                          (tipx + math.cos(a) * (rr + 30), tipy + math.sin(a) * (rr + 30))], (1, 0.95, 0.7, al), 6)


class S08_Hollow(Shot):
    """Inside the horse: the spear tip pokes through right between two Greeks."""
    set = "belly"
    grade_kind = "inside"
    keys = [(0, (540, 1150, 1.25)), (2.0, (540, 1120, 1.4))]
    sfx = [(0.05, "dong", 1.0), (0.9, "gulp", 0.8)]

    def front(self, cx, t):
        # spear tip through the planks, right between Odysseus and Anticlus
        u = ease_out(prog(t, 0.05, 0.18))
        bx, by = 400, 930
        for k in range(7):
            a = k * 0.9
            line(cx, [(bx, by), (bx + math.cos(a) * 60, by + math.sin(a) * 60)], hexc("#2A190E"), 6)
        cx.save()
        cx.translate(bx, by)
        cx.rotate(0.25)
        L = 150 * u
        line(cx, [(-10, 0), (L - 50, 0)], INK, 18)
        line(cx, [(-10, 0), (L - 50, 0)], hexc("#8A5A33"), 10)
        poly(cx, [(L - 60, -28), (L - 60, 28), (L + 20, 0)])
        fs(cx, hexc("#C9D0D8"), INK, 5)
        cx.restore()

    def post(self, cx, t):
        gfx.rays(cx, 520, 0, math.pi / 2 + 0.05, 0.25, 1600, (1, 0.85, 0.55), 0.12, 5, t=t)

    def chars(self, cx, t):
        hol = self.w("spear", 13)
        scared = t > hol - 0.1
        figs = [C.greek_soldier(1), C.ODYSSEUS, C.ANTICLUS, C.greek_soldier(2)]
        for i, (fig, x) in enumerate(zip(figs, (120, 340, 640, 900))):
            f = 1 if x < 500 else -1
            p = P(x, 1480, t, s=1.4, f=f, seed=30 + i, eyes="wide" if scared else "open",
                  mouth="flat" if not scared else ("wavy" if i % 2 else "o"),
                  look=(0.8 * f, -0.5) if scared else (0, 0), sweat=prog(t, hol, hol + 0.4) if scared else 0,
                  brows="worried" if scared else "neutral", squash=1 - 0.04 * scared)
            fig.draw(cx, p)


class S09_Beware(Shot):
    set = "beach"
    keys = [(0, (540, 1100, 1.6)), (1.7, (560, 1060, 1.85))]
    drift = 3.0
    sfx = [(0.0, "sting", 0.8)]

    def chars(self, cx, t):
        for i, x in enumerate((830, 980)):
            shrug = smooth(prog(t, 0.6 + i * 0.1, 0.9 + i * 0.1)) * (1 - smooth(prog(t, 1.4, 1.7)))
            C.trojan_citizen(i + 1).draw(cx, P(x, 1380, t, s=0.9, f=-1, seed=i, mouth="flat", eyes="half",
                                               arm_a=lerp(10, 80, shrug), arm_b=lerp(-10, 80, shrug),
                                               elb_a=lerp(10, -90, shrug), elb_b=lerp(10, -90, shrug)))
        p = P(470, 1560, t, s=1.65, view="front", seed=11, brows="angry", eyes="angry", mouth="yell")
        p = C.talk(p, t, 11).but(arm_b=170 + math.sin(t * 10) * 6, elb_b=-10, arm_a=-20, elb_a=40)
        C.LAOCOON.draw(cx, p)


# ================================================================ SINON
class S10_Reeds(Shot):
    set = "reeds"
    keys = [(0, (560, 1160, 1.15)), (3.9, (560, 1100, 1.3))]
    sfx = [(0.0, "rustle", 0.9), (0.4, "drag", 0.7)]

    def chars(self, cx, t):
        name = self.w("sinon", 10)
        x = walk_x(t, 0, 1.8, 1020, 600)
        moving = t < 1.8
        for i, dx in enumerate((-190, 190)):
            g = C.trojan_soldier(i + 1)
            p = P(x + dx, 1420 + i * 20, t, s=1.1, f=-1, seed=50 + i, brows="angry", mouth="frown",
                  arm_b=60 if dx < 0 else 60, elb_b=10)
            if moving:
                p = C.walk(p, t + i * 0.2, 1.3, arms=False)
            g.draw(cx, p)
        look = t > name
        p = P(x, 1440, t, s=1.15, f=-1 if not look else 1, view="front" if look else "side", seed=52,
              eyes="closed" if not look else "open", mouth="wavy" if not look else "grin", brows="worried",
              arm_a=30, arm_b=30, elb_a=70, elb_b=70, lean=-8 if moving else 0, foot_a=0)
        C.SINON.draw(cx, p)


class S11_Sobbing(Shot):
    """Sinon sobs a fountain of tears while a Trojan behind him dabs his own eyes."""
    set = "reeds"
    keys = [(0, (540, 1100, 1.55)), (4.4, (540, 1050, 1.85))]
    sfx = [(0.0, "sob", 0.9), (1.4, "violin", 0.6)]

    def chars(self, cx, t):
        C.trojan_soldier(2).draw(cx, P(870, 1330, t, s=0.95, f=-1, seed=61, eyes="closed", mouth="wavy",
                                       brows="worried", arm_b=150, elb_b=60))
        C.trojan_citizen(4).draw(cx, P(210, 1330, t, s=0.95, f=1, seed=62, eyes="half", mouth="frown",
                                       brows="worried"))
        sob = math.sin(t * 9) * 0.5 + 0.5
        p = P(540, 1600, t, s=1.6, view="front", seed=52, eyes="squeeze", mouth="scream", mouth_open=0.6 + 0.4 * sob,
              brows="worried", arm_a=-30, arm_b=-30, elb_a=-80, elb_b=-80, bob=sob * 6)
        self.J = C.SINON.draw(cx, p)

    def front(self, cx, t):
        if not self.J:
            return
        hx, hy = self.J["head"]
        R = self.J["head_rad"]
        for side in (-1, 1):
            ex, ey = hx + side * R * 0.35, hy - R * 0.05
            for k in range(9):
                u = ((t * 1.6 + k / 9) % 1)
                x = ex + side * u * 260
                y = ey - 60 * math.sin(u * math.pi) + u * 220
                ellipse(cx, x, y, 11, 15)
                fs(cx, hexc("#7FD1F5"), INK, 3)

    def tags(self, t):
        a = self.w("lie", 3) - 0.2
        return [("Sinon:", "*TEARS: 100% FAKE*")] if t > a else []


class S12_TooBig(Shot):
    set = "walls"
    keys = [(0, (540, 900, 0.95)), (2.7, (540, 900, 1.0))]
    sfx = [(0.2, "measure", 0.7), (1.2, "measure", 0.7), (2.0, "ding", 0.6)]

    def back(self, cx, t):
        gfx.contact_shadow(cx, 560, 1420, 360, 0.4)
        Wd.horse(cx, 560, 1420, 0.72, t=t)

    def front(self, cx, t):
        # dimension bars: GATE vs HORSE
        g = ease_out(prog(t, 0.15, 0.6))
        hh = ease_out(prog(t, 1.0, 1.6))
        gx, gy0, gy1 = 280, Wd.WALL_BOT, Wd.WALL_BOT - Wd.GATE_H
        hx, hy0, hy1 = 930, 1420, 1420 - 1200 * 0.72
        for (x, y0, y1, k, lab, col) in ((gx, gy0, gy1, g, "GATE", "#FFFFFF"), (hx, hy0, hy1, hh, "HORSE", "#FFD60A")):
            if k <= 0:
                continue
            yt = lerp(y0, y1, k)
            line(cx, [(x, y0), (x, yt)], INK, 16)
            line(cx, [(x, y0), (x, yt)], hexc(col), 8)
            for yy in (y0, yt):
                line(cx, [(x - 30, yy), (x + 30, yy)], INK, 14)
                line(cx, [(x - 30, yy), (x + 30, yy)], hexc(col), 7)
            label(cx, lab, x, yt - 50, 46, hexc(col), alpha=k)
        if t > 2.0:
            s = back_out(prog(t, 2.0, 2.3))
            cx.save()
            cx.translate(560, 380)
            cx.scale(s, s)
            label(cx, "HORSE  >  GATE", 0, 0, 72, hexc("#FFD60A"))
            cx.restore()


def label(cx, s, x, y, size, col, alpha=1.0):
    cx.save()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(size)
    e = cx.text_extents(s)
    cx.move_to(x - e.width / 2 - e.x_bearing, y + size * 0.35)
    cx.text_path(s)
    src(cx, (0.08, 0.06, 0.05, alpha))
    cx.set_line_width(size * 0.22)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    src(cx, col, alpha)
    cx.fill()
    cx.restore()


# ================================================================ SERPENTS
class S13_Serpents(Shot):
    set = "sea"
    keys = [(0, (540, 1080, 1.0)), (3.0, (540, 1180, 1.2))]
    drift = 2.5
    sfx = [(0.0, "sting_low", 0.9), (0.3, "splash", 0.9), (0.9, "splash", 0.7), (1.4, "hiss", 0.8)]

    def back(self, cx, t):
        Wd.ship(cx, 960, 1000, 0.18, f=1, t=t, rowers=False)
        for k, (bx, ph) in enumerate(((320, 0.0), (760, 0.5))):
            rise = ease_out(prog(t, 0.2 + ph, 1.6 + ph))
            pts = []
            for i in range(9):
                u = i / 8
                y = 1700 - u * 760 * rise
                x = bx + math.sin(u * 5 + t * 3 + k) * 90 * (0.4 + u)
                pts.append((x, y))
            Wd.serpent(cx, pts, t, 80, seed=k)
            # splash ring at the waterline
            for j in range(8):
                a = j * math.pi / 4 + t
                ellipse(cx, bx + math.cos(a) * 90, 1640 + math.sin(a) * 18, 26, 12)
                src(cx, (1, 1, 1, 0.7 * rise))
                cx.fill()


class S14_Strangle(Shot):
    """Coils wrap around Laocoön mid-rant; he gets yanked out of frame."""
    set = "beach"
    keys = [(0, (520, 1250, 1.35)), (1.8, (520, 1230, 1.4))]
    sfx = [(0.0, "hiss", 0.8), (0.4, "squeeze", 0.9), (1.1, "yank", 1.0)]

    def chars(self, cx, t):
        yank = ease_in(prog(t, 1.1, 1.5))
        wrap = smooth(prog(t, 0.15, 0.7))
        x = 560 - yank * 900
        p = P(x, 1540, t, s=1.4, view="front", seed=11, eyes="spiral" if wrap > 0.6 else "wide",
              mouth="scream" if wrap > 0.3 else "yell", brows="worried", arm_a=lerp(-20, 150, wrap),
              arm_b=lerp(170, 150, wrap), elb_a=20, elb_b=20, squash=1 - 0.08 * wrap, lean=-20 * yank)
        self.J = C.LAOCOON.draw(cx, p)
        if wrap > 0:
            # coils around the robe
            for k in range(3):
                y = 1540 - 180 * 1.4 + k * 70 * 1.4 * 0.7
                wk = clamp(wrap * 3 - k)
                if wk <= 0:
                    continue
                ellipse(cx, x, y, 95 * wk, 26)
                fs(cx, hexc("#3F8F4E"), INK, 6)
            # the serpent body trailing off to the left
            pts = [(x - 60, 1540 - 250), (x - 260, 1400), (x - 500, 1500), (x - 800, 1380)]
            Wd.serpent(cx, pts[::-1][:1] + pts[::-1][1:], t, 60)


class S15_Sacred(Shot):
    set = "beach"
    keys = [(0, (560, 1150, 1.05)), (2.1, (560, 1080, 0.98))]
    sfx = [(0.0, "crickets", 0.8), (1.3, "choir", 0.8)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 600, 1380, 0.8, alpha=0.25 + 0.35 * smooth(prog(t, 1.3, 2.0)))
        gfx.contact_shadow(cx, 600, 1385, 420, 0.45)
        Wd.horse(cx, 600, 1380, 0.8, t=t)

    def chars(self, cx, t):
        sac = self.w("snakes", 19) - 0.25
        look = int(t * 2.2) % 2
        bow = smooth(prog(t, sac, sac + 0.5))
        for i, x in enumerate((200, 380, 700, 880)):
            fig = C.trojan_soldier(i) if i % 2 == 0 else C.trojan_citizen(i + 3)
            f = 1 if (i + look) % 2 == 0 else -1
            p = P(x, 1640 + (i % 2) * 30, t, s=1.05, f=f if bow < 0.1 else (1 if x < 540 else -1), seed=i,
                  eyes="half" if bow < 0.5 else "closed", mouth="flat", brows="flat",
                  lean=40 * bow, arm_a=lerp(10, 70, bow), arm_b=lerp(-10, 70, bow), head_dy=10 * bow)
            fig.draw(cx, p)

    def post(self, cx, t):
        k = smooth(prog(t, 1.3, 2.0))
        if k:
            gfx.rays(cx, 540, -100, math.pi / 2, 0.5, 1800, (1, 0.92, 0.6), 0.2 * k, 9, t=t)


# ================================================================ WALLS
class S16_Bonk(Shot):
    set = "walls"
    keys = [(0, (820, 980, 0.95)), (2.4, (800, 960, 1.0))]

    @property
    def shakes(self):
        return [(self.w("walls", 12) - 0.12, 26, 0.45)]

    @property
    def sfx(self):
        return [(0.0, "rope_pull", 0.7), (0.0, "wood_roll", 0.6), (self.w("walls", 12) - 0.12, "bonk_big", 1.0)]

    def hx(self, t):
        hit = self.w("walls", 12) - 0.12
        return lerp(1500, 1100, ease_io(prog(t, 0, hit))) + (math.sin((t - hit) * 30) * 10 * math.exp(-(t - hit) * 6)
                                                              if t > hit else 0)

    def back(self, cx, t):
        x = self.hx(t)
        gfx.contact_shadow(cx, x, 1420, 360, 0.4)
        hit = self.w("walls", 12) - 0.12
        Wd.horse(cx, x, 1420, 0.72, t=t, roll=(1500 - x), wobble=0.04 * math.exp(-(t - hit) * 4) if t > hit else 0)
        if t > hit:
            for k in range(3):
                a = (t - hit) * 6 + k * 2.1
                circle(cx, x - 330 + math.cos(a) * 70, 560 + math.sin(a) * 22, 16)
                fs(cx, hexc("#FFE066"), INK, 3)

    def chars(self, cx, t):
        x = self.hx(t)
        hit = self.w("walls", 12) - 0.12
        for i in range(3):
            px = x - 720 + i * 120
            fig = C.trojan_citizen(i + 6)
            p = P(px, 1520 + (i % 2) * 20, t, s=0.9, f=-1, seed=70 + i, mouth="grin" if t < hit else "o",
                  eyes="squeeze" if t < hit else "wide", lean=18 if t < hit else -8, arm_a=-60, arm_b=-50,
                  elb_a=-20, elb_b=-10)
            if t < hit:
                p = C.walk(p, t, 1.1, arms=False)
            J = fig.draw(cx, p)
            Wd.rope(cx, J["hand_b"], (x - 250, 950), 40, 6)


class S17_TearDown(Shot):
    set = "walls"
    keys = [(0, (540, 1020, 1.05)), (2.2, (540, 980, 0.95))]

    @property
    def hit(self):
        return self.w("walls", 18) - 0.9

    @property
    def shakes(self):
        return [(self.hit, 40, 0.9)]

    @property
    def sfx(self):
        return [(0.1, "pick", 0.7), (0.45, "pick", 0.7), (0.8, "pick", 0.7), (self.hit, "rubble", 1.0)]

    def layers(self, t):
        return Wd.get_set("walls_breach" if t > self.hit + 0.25 else "walls")

    def chars(self, cx, t):
        swing = (t * 2.6) % 1
        for i, (x, f) in enumerate(((330, 1), (520, -1), (760, -1), (900, -1))):
            hitting = t < self.hit + 0.3
            fig = C.trojan_soldier(i) if i % 2 else C.trojan_citizen(i + 8)
            ph = (swing + i * 0.25) % 1
            a = lerp(170, 60, ease_in(ph)) if hitting else 20
            p = P(x, 1250 + (i % 2) * 30, t, s=0.95, f=f, seed=80 + i, mouth="grin", eyes="happy" if hitting else "wide",
                  arm_b=a, arm_a=a - 10, elb_b=10, elb_a=10, lean=10 * ease_in(ph) if hitting else -10)
            J = fig.draw(cx, p)
            if hitting:
                hx, hy = J["hand_b"]
                Wd.pickaxe(cx, hx, hy, (math.radians(a) - math.pi) * f * -1 + (0.3 if f > 0 else -0.3), 0.9)

    def front(self, cx, t):
        if t > self.hit:
            r = random.Random(9)
            u = t - self.hit
            for k in range(18):
                x0 = 540 + r.uniform(-300, 300)
                y0 = 700 + r.uniform(-100, 300)
                vx = r.uniform(-300, 300)
                x = x0 + vx * u
                y = y0 + r.uniform(-200, 50) * u + 1800 * u * u
                if y < 1700:
                    Wd.stone(cx, x, y, r.uniform(40, 90), u * r.uniform(-4, 4), hexc("#E3CBA0"))
            Wd.dust(cx, 540, 1150, t, self.hit, 16, 160, 3)


# ================================================================ CASSANDRA
class S18_Cassandra(Shot):
    set = "plaza"
    keys = [(0, (480, 1150, 1.25)), (2.8, (420, 1150, 1.45))]
    drift = 2.0
    sfx = [(0.0, "festival", 0.6), (0.5, "scream", 0.8)]

    def back(self, cx, t):
        Wd.horse_rim(cx, 720, 1300, 0.62)
        gfx.contact_shadow(cx, 720, 1305, 320, 0.4)
        Wd.horse(cx, 720, 1300, 0.62, t=t, bow=1.0)

    def chars(self, cx, t):
        for i, x in enumerate((560, 960)):
            C.trojan_citizen(i + 12).draw(cx, C.walk(P(x + t * 40, 1420, t, s=0.75, f=1, seed=90 + i, mouth="grin",
                                                       eyes="happy"), t, 1.3))
        p = P(250, 1640, t, s=1.5, f=1, seed=3, eyes="wide", mouth="scream", brows="worried",
              arm_b=110 + math.sin(t * 14) * 8, elb_b=0, arm_a=150 + math.sin(t * 12) * 10, elb_a=30)
        C.CASSANDRA.draw(cx, C.talk(p, t, 12))


class S19_Cursed(Shot):
    set = "plaza"
    keys = [(0, (420, 1150, 1.2)), (3.6, (420, 1120, 1.28))]

    @property
    def sfx(self):
        return [(0.0, "festival", 0.6), (0.3, "crowd_cheer", 0.6), (self.w("cass", 12) - 0.25, "thunder_small", 0.8)]

    def back(self, cx, t):
        Wd.horse(cx, 920, 1300, 0.62, t=t, bow=1.0)

    def chars(self, cx, t):
        for i in range(6):
            x = -200 + ((t * 230 + i * 260) % 1500)
            fig = C.trojan_citizen(i + 20)
            p = C.walk(P(x, 1500 + (i % 3) * 50, t, s=0.85 + 0.05 * (i % 3), f=1, seed=100 + i, mouth="grin",
                         eyes="happy", arm_b=120, elb_b=20), t + i * 0.3, 1.4)
            fig.draw(cx, p)
        cur = self.w("cass", 12) - 0.25
        p = P(300, 1640, t, s=1.35, f=1, seed=3, eyes="half" if t > cur else "wide",
              mouth="flat" if t > cur else "yell", brows="flat" if t > cur else "worried",
              arm_b=110 if t < cur else -10, elb_b=0, arm_a=-10, sweat=0)
        if t < cur:
            p = C.talk(p, t, 12)
        self.J = C.CASSANDRA.draw(cx, p)

    def front(self, cx, t):
        r = random.Random(int(t * 4))
        for k in range(14):
            u = ((t * 0.5 + k * 0.071) % 1)
            x = 500 + k * 50 + math.sin(t * 2 + k) * 40
            y = 800 + u * 900
            Wd.petal(cx, x, y, t * 3 + k, hexc(["#E94F64", "#F7B32B", "#FFFFFF"][k % 3]))
        cur = self.w("cass", 12) - 0.25
        if t > cur and self.J:
            hx, hy = self.J["head_top"]
            Wd.storm_cloud(cx, hx, hy - 120, t, 1.1 * back_out(prog(t, cur, cur + 0.3)))

    def tags(self, t):
        return [("Cassandra:", "*RIGHT. AGAIN.*")] if t > self.w("cass", 12) else []


# ================================================================ NIGHT
class S20_Helen(Shot):
    set = "plaza_night"
    grade_kind = "night"
    keys = [(0, (560, 1150, 1.05)), (4.0, (520, 1180, 1.18))]
    sfx = [(0.0, "night_amb", 0.8), (1.9, "voice_honey", 0.8)]

    def back(self, cx, t):
        for i, (x, y) in enumerate(((120, 1250), (960, 1250))):
            Wd.torch(cx, x, y, t, 1.0, i)
        gfx.contact_shadow(cx, 600, 1355, 380, 0.5)
        Wd.horse(cx, 600, 1350, 0.75, t=t, night=True, bow=1.0)

    def chars(self, cx, t):
        x = walk_x(t, 0, 3.8, 180, 760)
        call = self.w("helen", 5) - 0.1
        calling = t > call
        p = P(x, 1660, t, s=1.5, f=1, seed=4, eyes="half", mouth="o" if calling else "smirk",
              arm_a=40, elb_a=80, arm_b=150 if calling else 60, elb_b=50 if calling else 60)
        p = C.walk(p, t, 0.9, arms=False)
        if calling:
            p = C.talk(p, t, 8)
        self.J = C.HELEN.draw(cx, p)
        hx, hy = self.J["hand_a"]
        Wd.torch(cx, hx, hy + 60, t, 0.55, 7)

    def post(self, cx, t):
        cam = self.cam(t)
        for i, (x, y) in enumerate(((120, 1250), (960, 1250))):
            sx, sy = cam.to_screen(x, y)
            Wd.torch_glow(cx, sx, sy, t, 1.0 * cam.zoom, i)
        if self.J:
            sx, sy = cam.to_screen(*self.J["hand_a"])
            gfx.glow(cx, sx, sy - 80, 300, (1.0, 0.62, 0.25), 0.5)
        call = self.w("helen", 5) - 0.1
        if t > call and self.J:
            hx, hy = cam.to_screen(*self.J["head_top"])
            bubble(cx, hx + 160, hy - 140, "Honeyyy? It's me!", back_out(prog(t, call, call + 0.3)))


def bubble(cx, x, y, s, k=1.0, size=48):
    if k <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(k, k)
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(size)
    e = cx.text_extents(s)
    w, h = e.width + 70, size + 50
    rrect(cx, -w / 2, -h / 2, w, h, h / 2)
    cx.move_to(-w * 0.2, h / 2 - 4)
    cx.line_to(-w * 0.32, h / 2 + 46)
    cx.line_to(-w * 0.05, h / 2 - 4)
    fs(cx, (1, 1, 1, 1), INK, 6)
    rrect(cx, -w / 2 + 3, -h / 2 + 3, w - 6, h - 6, h / 2)
    src(cx, (1, 1, 1, 1))
    cx.fill()
    cx.move_to(-e.width / 2 - e.x_bearing, size * 0.36)
    src(cx, hexc("#D6336C"))
    cx.show_text(s)
    cx.restore()


class S21_AboutToAnswer(Shot):
    set = "belly_night"
    grade_kind = "inside_night"
    keys = [(0, (560, 1150, 1.45)), (1.9, (600, 1130, 1.65))]
    sfx = [(0.0, "voice_honey_far", 0.6), (0.6, "inhale", 0.8)]

    def post(self, cx, t):
        gfx.rays(cx, 900, 300, math.pi * 0.62, 0.15, 1500, (1, 0.7, 0.35), 0.16, 3, t=t)

    def chars(self, cx, t):
        C.ODYSSEUS.draw(cx, P(300, 1440, t, s=1.2, f=1, seed=5, eyes="half", mouth="flat", brows="flat"))
        lean = smooth(prog(t, 0.3, 1.2))
        p = P(640, 1440, t, s=1.2, f=1, seed=6, eyes="wide", mouth="grin" if lean < 0.7 else "o", brows="up",
              lean=18 * lean, blush=1.0, arm_b=lerp(-10, 120, lean), elb_b=lerp(10, 40, lean))
        self.J = C.ANTICLUS.draw(cx, p)
        C.greek_soldier(2).draw(cx, P(920, 1440, t, s=1.2, f=-1, seed=7, eyes="wide", mouth="o", brows="worried",
                                      sweat=lean))

    def front(self, cx, t):
        if self.J:
            hx, hy = self.J["head"]
            for k in range(3):
                u = (t * 0.8 + k / 3) % 1
                heart(cx, hx + 90 + k * 30, hy - 80 - u * 160, 18 * (1 - u * 0.5), 1 - u)


def heart(cx, x, y, r, a=1.0):
    cx.save()
    cx.translate(x, y)
    cx.move_to(0, r * 0.9)
    cx.curve_to(-r * 1.6, -r * 0.2, -r * 0.6, -r * 1.3, 0, -r * 0.4)
    cx.curve_to(r * 0.6, -r * 1.3, r * 1.6, -r * 0.2, 0, r * 0.9)
    cx.close_path()
    src(cx, hexc("#FF5D8F"), a)
    cx.fill_preserve()
    src(cx, INK, a)
    cx.set_line_width(3)
    cx.stroke()
    cx.restore()


class S22_Clamp(Shot):
    set = "belly_night"
    grade_kind = "inside_night"
    keys = [(0, (560, 1080, 1.7)), (2.3, (560, 1060, 1.8))]

    @property
    def clamp(self):
        return self.w("hand", 8) - 0.05

    @property
    def shakes(self):
        return [(self.clamp, 12, 0.3)]

    @property
    def sfx(self):
        return [(self.clamp, "slap", 1.0), (self.clamp + 0.12, "mmmf", 0.9)]

    def post(self, cx, t):
        gfx.rays(cx, 900, 300, math.pi * 0.62, 0.15, 1500, (1, 0.7, 0.35), 0.16, 3, t=t)

    def chars(self, cx, t):
        c = self.clamp
        k = ease_out(prog(t, c - 0.15, c))
        pa = P(640, 1440, t, s=1.3, f=-1, seed=6, eyes="wide", mouth="o", brows="up" if k < 1 else "worried",
               lean=-10 * k)
        Ja = C.ANTICLUS.draw(cx, pa)
        po = P(380, 1440, t, s=1.3, f=1, seed=5, eyes="angry" if k > 0 else "half", mouth="flat",
               brows="angry", arm_b=lerp(-10, 95, k), elb_b=lerp(10, -10, k), lean=12 * k)
        C.ODYSSEUS.draw(cx, po)
        if k > 0:
            hx, hy = Ja["head"]
            R = Ja["head_rad"]
            mx, my = hx - R * 0.15, hy + R * 0.45
            sx = lerp(380 + 60, mx, k)
            sy = lerp(1100, my, k)
            line(cx, [(380 + 30, 1440 - 1.3 * 230), (sx, sy)], INK, 12 * 1.3 + 7)
            line(cx, [(380 + 30, 1440 - 1.3 * 230), (sx, sy)], C.ODYSSEUS.st.skin, 12 * 1.3)
            ellipse(cx, sx, sy, 46, 34)
            fs(cx, C.ODYSSEUS.st.skin, INK, 5)
            for j in range(3):
                line(cx, [(sx - 20 + j * 18, sy - 22), (sx - 14 + j * 18, sy + 22)], shade(C.ODYSSEUS.st.skin, -0.3), 3)

    def tags(self, t):
        return [("Anticlus:", "*THAT WAS CLOSE*")] if t > self.clamp + 0.3 else []


class S23_Hatch(Shot):
    set = "plaza_night"
    grade_kind = "night"
    keys = [(0, (500, 1080, 1.15)), (1.8, (480, 1040, 1.25))]

    @property
    def op(self):
        return self.w("night", 3) - 0.05

    @property
    def sfx(self):
        return [(self.op, "creak", 0.9), (self.op + 0.35, "rope_drop", 0.8)]

    def back(self, cx, t):
        Wd.torch(cx, 980, 1250, t, 1.0, 1)
        Wd.horse(cx, 560, 1400, 0.95, t=t, night=True, hatch=ease_out(prog(t, self.op, self.op + 0.4)))
        if t > self.op + 0.3:
            # rope ladder dropping from the hatch (hatch at local (-70..80, -500) mirrored)
            k = ease_out(prog(t, self.op + 0.3, self.op + 0.6))
            hx = 560 - 140 * 0.95
            top = 1400 - 500 * 0.95
            bot = lerp(top, 1440, k)
            for sx in (-30, 30):
                line(cx, [(hx + sx, top), (hx + sx, bot)], INK, 9)
                line(cx, [(hx + sx, top), (hx + sx, bot)], hexc("#C9A66B"), 5)
            y = top + 30
            while y < bot:
                line(cx, [(hx - 30, y), (hx + 30, y)], hexc("#C9A66B"), 6)
                y += 45

    def chars(self, cx, t):
        p = P(700, 1600, t, s=1.2, f=-1, seed=52, eyes="half", mouth="smirk", brows="skeptic",
              arm_b=lerp(20, 140, smooth(prog(t, self.op - 0.4, self.op))), elb_b=20)
        C.SINON.draw(cx, p)
        if t > self.op + 0.45:
            u = ease_out(prog(t, self.op + 0.45, self.op + 0.9))
            C.greek_soldier(1).draw(cx, P(427, 1400 - 500 * 0.95 + 120 - 150 * u, t, s=0.75, f=-1, seed=8,
                                          eyes="open", mouth="smirk", view="front"))

    def post(self, cx, t):
        cam = self.cam(t)
        sx, sy = cam.to_screen(980, 1250)
        Wd.torch_glow(cx, sx, sy, t, cam.zoom, 1)


class S24_Gates(Shot):
    set = "walls_night"
    grade_kind = "night"
    keys = [(0, (540, 1000, 1.15)), (1.2, (540, 980, 1.22))]
    sfx = [(0.0, "gate_heavy", 0.9)]

    def back(self, cx, t):
        k = ease_io(prog(t, 0.0, 0.9))
        gx0 = Wd.GATE_X - Wd.GATE_W / 2
        top = Wd.WALL_BOT - Wd.GATE_H + 40
        for side in (-1, 1):
            w = Wd.GATE_W / 2 * (1 - k * 0.85)
            x = gx0 if side < 0 else gx0 + Wd.GATE_W - w
            rrect(cx, x, top, w, Wd.GATE_H - 40, 6)
            fs(cx, hexc("#4A3020"), INK, 6)
            for j in range(4):
                line(cx, [(x + 8, top + 60 + j * 110), (x + w - 8, top + 60 + j * 110)], hexc("#2A1A10"), 8)

    def chars(self, cx, t):
        for i, x in enumerate((420, 620)):
            p = P(x, 1210, t, s=0.8, f=-1 if i else 1, seed=120 + i, eyes="half", mouth="smirk", brows="skeptic",
                  arm_b=160 if i == 0 else 20, elb_b=10)
            C.greek_soldier(i).draw(cx, C.walk(p, t, 0.8, arms=False) if t < 0.6 else p)

    def post(self, cx, t):
        cam = self.cam(t)
        sx, sy = cam.to_screen(420, 900)
        gfx.glow(cx, sx, sy, 260, (1, 0.6, 0.25), 0.45)


class S25_Fleet(Shot):
    set = "sea_night"
    grade_kind = "night"
    keys = [(0, (700, 980, 1.05)), (2.8, (640, 1040, 1.15))]
    sfx = [(0.0, "waves", 0.7), (0.4, "horn", 0.9), (1.2, "oars", 0.8)]

    def back(self, cx, t):
        ships = []
        goals = [(230, 1180, 0.42), (620, 1130, 0.36), (900, 1230, 0.44), (380, 1380, 0.55), (760, 1430, 0.6),
                 (120, 1560, 0.7), (980, 1600, 0.72)]
        for i, (gx, gy, gs) in enumerate(goals):
            u = ease_out(clamp((t - i * 0.22) / 2.4))
            x = lerp(900 + (i % 3) * 60, gx, u)
            y = lerp(990, gy, u)
            s = lerp(0.06, gs, u)
            ships.append((y, x, s, i))
        for y, x, s, i in sorted(ships):
            Wd.ship(cx, x, y, s, f=-1, t=t + i, night=True)

    def front(self, cx, t):
        k = smooth(prog(t, 0.6, 1.0))
        if k:
            label(cx, "TENEDOS", 860, 760, 40, hexc("#FFFFFF"), alpha=k)
            line(cx, [(860, 790), (860, 830)], (1, 1, 1, k), 5)


# ================================================================ FINALE: split screen
class SplitHalf(Shot):
    def __init__(self, t0, t1, kind):
        super().__init__(t0, t1)
        self.kind = kind
        self.set = "walls" if kind == "greeks" else "walls_breach"
        self.keys = [(0, (540, 1130, 1.3)), (6, (540, 1130, 1.38))]

    @property
    def shakes(self):
        if self.kind == "greeks":
            return [(k * 0.9 + 0.35, 10, 0.25) for k in range(8)]
        return [(0.3, 22, 0.6), (1.2, 18, 0.5)]

    def back(self, cx, t):
        if self.kind == "trojans":
            Wd.horse(cx, lerp(1300, 560, ease_io(prog(t, 1.4, 3.2))), 1420, 0.6, t=t, roll=t * 300)

    def chars(self, cx, t):
        if self.kind == "greeks":
            ph = (t % 0.9) / 0.9
            push = math.sin(min(ph, 0.4) / 0.4 * math.pi / 2) if ph < 0.4 else 1 - (ph - 0.4) / 0.6
            x = 420 + push * 120
            # battering ram (log)
            cx.save()
            rrect(cx, x - 300, 1060, 520, 70, 34)
            fs(cx, hexc("#8A5A33"), INK, 6)
            circle(cx, x + 220, 1095, 36)
            fs(cx, hexc("#C9A13B"), INK, 5)
            cx.restore()
            for i in range(3):
                C.greek_soldier(i).draw(cx, P(x - 220 + i * 150, 1260, t, s=0.85, f=1, seed=130 + i,
                                              eyes="squeeze" if push > 0.8 else "half", mouth="teeth",
                                              brows="angry", arm_b=-80, arm_a=-70, elb_a=-30, elb_b=-30,
                                              sweat=1.0, lean=16 * push))
        else:
            swing = (t * 2.4) % 1
            for i, (x, f) in enumerate(((240, 1), (420, 1), (700, -1), (880, -1))):
                ph = (swing + i * 0.25) % 1
                a = lerp(170, 60, ease_in(ph))
                fig = C.trojan_soldier(i) if i % 2 else C.trojan_citizen(i + 30)
                J = fig.draw(cx, P(x, 1280, t, s=0.85, f=f, seed=140 + i, mouth="grin", eyes="happy",
                                   arm_b=a, arm_a=a - 10, elb_b=10, elb_a=10))
                hx, hy = J["hand_b"]
                Wd.pickaxe(cx, hx, hy, (math.radians(a) - math.pi) * f * -1 + (0.3 if f > 0 else -0.3), 0.8)

    def front(self, cx, t):
        if self.kind == "trojans":
            Wd.dust(cx, 540, 1150, t, 0.2, 12, 120, 5)


class S26_Split(Shot):
    """Top: Greeks with a battering ram, 10 YEARS. Bottom (from 'The Trojans'): Trojans tearing it down."""

    def __init__(self, t0, t1):
        super().__init__(t0, t1)
        self.top = SplitHalf(t0, t1, "greeks")
        self.bottom = SplitHalf(t0, t1, "trojans")

    @property
    def b0(self):
        return self.w("end", 9) - 0.1

    @property
    def sfx(self):
        out = [(k * 0.9 + 0.35, "ram", 0.6) for k in range(3)]
        out += [(self.b0, "whoosh", 0.8), (self.b0 + 0.3, "rubble", 0.9), (self.b0 + 0.9, "pick", 0.6),
                (self.b0 + 1.3, "rubble", 0.6), (self.b0 + 1.5, "crowd_cheer", 0.6)]
        return out

    def render(self, t):
        s = gfx.surface()
        cx = cairo.Context(s)
        src(cx, hexc("#141018"))
        cx.paint()
        split = ease_out(prog(t, self.b0, self.b0 + 0.35))
        top_h = lerp(H, H / 2, split)
        a = self.top.render(t)
        cx.save()
        cx.rectangle(0, 0, W, top_h)
        cx.clip()
        cx.set_source_surface(a, 0, -(H - top_h) / 2 + 160 * split)
        cx.paint()
        cx.restore()
        label(cx, "10 YEARS", W / 2, 140, 92, hexc("#FFFFFF"),
              alpha=smooth(prog(t, 0.2, 0.5)))
        if split > 0:
            b = self.bottom.render(t - self.b0)
            cx.save()
            cx.rectangle(0, top_h, W, H - top_h)
            cx.clip()
            cx.set_source_surface(b, 0, top_h - 560 + (1 - split) * 200)
            cx.paint()
            cx.restore()
            line(cx, [(0, top_h), (W, top_h)], (1, 1, 1, 1), 12)
            line(cx, [(0, top_h), (W, top_h)], INK, 4)
            k = back_out(prog(t, self.b0 + 0.9, self.b0 + 1.25))
            if k > 0:
                cx.save()
                cx.translate(W / 2, top_h + 110)
                cx.scale(k, k)
                label(cx, "1 AFTERNOON", 0, 0, 92, hexc("#FFD60A"))
                cx.restore()
        return s


# ================================================================ timeline
def build():
    T = WS
    cuts = [
        (S01_HorseReveal, 0.0),
        (S02_Bow, T("hook", 10) - 0.05),
        (S03_SailHome, T("hook", 14) - 0.05),
        (S04_RushOut, T("beach", 0) - 0.05),
        (S05_JustAHorse, T("beach", 6) - 0.1),
        (S06_Laocoon, T("spear", 0) - 0.05),
        (S07_SpearHits, T("spear", 6) - 0.05),
        (S08_Hollow, T("spear", 10) - 0.05),
        (S09_Beware, T("beware", 0) - 0.12),
        (S10_Reeds, T("sinon", 0) - 0.05),
        (S11_Sobbing, T("lie", 0) - 0.05),
        (S12_TooBig, T("lie", 17) - 0.05),
        (S13_Serpents, T("snakes", 0) - 0.05),
        (S14_Strangle, T("snakes", 10) - 0.05),
        (S15_Sacred, T("snakes", 14) - 0.1),
        (S16_Bonk, T("walls", 0) - 0.05),
        (S17_TearDown, T("walls", 13) - 0.05),
        (S18_Cassandra, T("cass", 0) - 0.05),
        (S19_Cursed, T("cass", 6) - 0.1),
        (S20_Helen, T("helen", 0) - 0.05),
        (S21_AboutToAnswer, T("hand", 0) - 0.05),
        (S22_Clamp, T("hand", 7) - 0.05),
        (S23_Hatch, T("night", 0) - 0.05),
        (S24_Gates, T("night", 5) - 0.05),
        (S25_Fleet, T("night", 10) - 0.05),
        (S26_Split, T("end", 0) - 0.05),
    ]
    shots = []
    for i, (cls, t0) in enumerate(cuts):
        t1 = cuts[i + 1][1] if i + 1 < len(cuts) else DUR
        shots.append(cls(max(0.0, t0), t1))
    return shots


SHOTS = build()


def shot_at(T):
    for s in SHOTS:
        if s.t0 <= T < s.t1:
            return s
    return SHOTS[-1]

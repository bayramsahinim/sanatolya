"""Shots 8-18: why he survived (science), the wait, the discovery, the rescue."""
import math
import random

import cairo

from cinecode.core import (OUTLINE, Cam, H, W, circle, clamp, ease_in, ease_io, ease_out, ellipse, fs, hexc, kf,
                           line, prog, rrect, shake, smooth, src, text)
from cinecode.characters import Figure
from . import look, sets
from .cast import DIVER, DIVER2, DIVER_ST, HARRISON, DiverStyle, bare_hand, diver, glove_hand, harrison
from .common import (WL, cam_keys, debris, draw_rotated, helmet_lamp, o2, snow, splash, swim, underwater)
from .frame import Shot
from .shots_a import pulse_

HARRISON_HELMET = Figure(DiverStyle(shell="#E9EEF2"), seed=8)
HARRISON_HELMET.st.skin = hexc("#8A5A3B")


def cold_key(F, c, power=0.8):
    """stylised cold key light used for the explanation shots inside the pocket."""
    F.lights.point(*c.to_screen(300, 300), 1350 * c.zoom, (0.5, 0.66, 0.88), power * 1.5)
    F.lights.point(*c.to_screen(900, 560), 700 * c.zoom, (0.55, 0.62, 0.7), power * 0.5)


def pocket_scene(F, c, t, p, water=WL, wamp=6):
    sets.cabin_plate().blit(F.cx)
    J = HARRISON.draw(F.cx, p)
    look.water_body(F.cx, water, t, color=(0.05, 0.2, 0.22), alpha=0.74, x0=-600, x1=1700, amp=wamp, seed=1)
    return J


# --------------------------------------------------------------------- 8  cutaway: the trapped air
class S8(Shot):
    punch = 0.05

    def __init__(self, t0, t1, label_t):
        super().__init__(t0, t1)
        self.label_t = label_t - t0

    def render(self, F):
        t = F.t
        F.unlit = True
        F.fog_amt = 0
        F.grade = ((0.0, 0.01, 0.015), (1.0, 1.0, 1.02), 0.95)
        F.bloom = 0.4
        cx = F.cx
        cam = cam_keys(t, [(0, (540, 960, 0.95)), (0.8, (540, 960, 1.0)), (self.dur, (400, 990, 1.8))])
        c = self.apply_cam(F, cam)
        # deep-water backdrop
        g = cairo.LinearGradient(0, -400, 0, 2300)
        g.add_color_stop_rgb(0, 0.1, 0.32, 0.38)
        g.add_color_stop_rgb(1, 0.02, 0.07, 0.09)
        cx.rectangle(-800, -800, 2700, 3500)
        cx.set_source(g)
        cx.fill()
        look.god_rays(cx, t, alpha=0.05, color=(0.6, 0.9, 1.0))
        # seabed
        cx.rectangle(-800, 1480, 2700, 1200)
        src(cx, hexc("#3E4A3C"))
        cx.fill()
        hx, hy, s = 540, 860, 0.86
        # inverted superstructure below the hull
        cx.save()
        cx.translate(hx, hy)
        cx.scale(s, s)
        rrect(cx, -330, 300, 420, 230, 14)
        fs(cx, hexc("#C9C3B2"), OUTLINE, 7)
        rrect(cx, -220, 530, 220, 140, 10)
        fs(cx, hexc("#BDB6A4"), OUTLINE, 6)
        cx.restore()
        # cut-open hull: interior compartments
        cx.save()
        sets.hull_shape(cx, hx, hy, s)
        cx.clip()
        cx.rectangle(-800, -800, 2700, 3500)
        src(cx, hexc("#3a4245"))
        cx.fill()
        fill_k = smooth(prog(t, 0.0, 1.2))
        comps = []
        decks = [hy - 30 * s, hy + 110 * s, hy + 310 * s]
        bulk = [hx - 640 * s, hx - 330 * s, hx - 60 * s, hx + 210 * s, hx + 470 * s, hx + 640 * s]
        for di in range(2):
            for bi in range(5):
                comps.append((bulk[bi], decks[di], bulk[bi + 1], decks[di + 1]))
        pocket_i = 6           # lower deck (old upper deck), compartment 2: the air pocket
        for i, (x0, y0, x1, y1) in enumerate(comps):
            hgt = y1 - y0
            if i == pocket_i:
                lvl = y1 - hgt * 0.55 * fill_k  # water rises from the bottom only to 55%
            else:
                lvl = y1 - hgt * min(1, fill_k * 1.15)
            cx.rectangle(x0, lvl, x1 - x0, y1 - lvl)
            src(cx, (0.12, 0.45, 0.6, 0.92))
            cx.fill()
            look.water_surface_path(cx, lvl, t, x0, x1, amp=2.5, k=0.05, seed=i)
            src(cx, (0.7, 0.95, 1, 0.8 if fill_k < 1 or i == pocket_i else 0))
            cx.set_line_width(3)
            cx.stroke()
        # air pocket glow
        x0, y0, x1, y1 = comps[pocket_i]
        airb = y1 - (y1 - y0) * 0.55
        glow_k = smooth(prog(t, 0.6, 1.4))
        cx.rectangle(x0, y0, x1 - x0, airb - y0)
        src(cx, (0.85, 0.97, 1.0, 0.28 * glow_k))
        cx.fill()
        # tiny Harrison in the pocket
        from .cast import harrison as hp
        HARRISON.draw(cx, hp((x0 + x1) / 2, airb + 70 * s, t, s=0.24, f=-1, eyes="open"))
        cx.rectangle(x0, airb, x1 - x0, y1 - airb)
        src(cx, (0.12, 0.45, 0.6, 0.6))
        cx.fill()
        # deck + bulkhead steel
        for yv in decks:
            line(cx, [(bulk[0], yv), (bulk[-1], yv)], hexc("#20262a"), 12 * s)
        for xv in bulk:
            line(cx, [(xv, decks[0]), (xv, decks[-1])], hexc("#20262a"), 12 * s)
        cx.restore()
        sets.hull_shape(cx, hx, hy, s)
        src(cx, OUTLINE)
        cx.set_line_width(10)
        cx.stroke()
        cx.save()
        sets.hull_shape(cx, hx, hy, s)
        cx.clip()
        cx.rectangle(-800, hy - 120 * s, 2700, 90 * s)
        src(cx, hexc("#8E2E24"))
        cx.fill()
        cx.restore()
        # "AIR POCKET" call-out
        lk = smooth(prog(t, self.label_t, self.label_t + 0.3))
        if lk > 0:
            ax, ay = (x0 + x1) / 2, (y0 + airb) / 2
            tx, ty = ax - 95, ay - 210
            line(cx, [(ax + 30, ay - 10), (ax + 30 + (tx + 115 - ax - 30) * lk, ay - 10 + (ty + 14 - ay + 10) * lk)], (1, 1, 1, lk), 4)
            circle(cx, ax + 30, ay - 10, 8)
            src(cx, (1, 1, 1, lk))
            cx.fill()
            rrect(cx, tx - 10, ty - 50, 250, 64, 12)
            src(cx, (0.05, 0.1, 0.12, 0.75 * lk))
            cx.fill()
            text(cx, "AIR POCKET", tx + 115, ty - 6, 34, (1, 1, 1, lk))
        snow(F, t, cam, 0.35)


# --------------------------------------------------------------------- 9a  close-up: breathing
class S9a(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.1, (0.05, 0.08, 0.1))
        cam = cam_keys(t, [(0, (600, 520, 1.85)), (self.dur, (610, 500, 2.0))])
        c = self.apply_cam(F, cam)
        breath = 0.5 + 0.5 * math.sin(t * 2.8)
        p = harrison(640, WL + 225, t, s=1.15, f=-1, eyes="half", brows="worried", mouth="o",
                     mouth_open=0.4 + 0.6 * breath, look=(-0.2, -0.3), arm_a=140, elb_a=40, arm_b=120, elb_b=60)
        p = p.but(bob=-breath * 6)
        pocket_scene(F, c, t, p)
        cold_key(F, c, 0.9)
        snow(F, t, cam, 0.2)


# --------------------------------------------------------------------- 9b/9c  the air volume
class S9b(Shot):
    punch = 0.04
    dim = False

    def render(self, F):
        t = F.t
        underwater(F, 0.1, (0.05, 0.08, 0.1))
        if self.dim:
            cam = cam_keys(t, [(0, (620, 590, 1.45)), (self.dur, (640, 570, 1.65))])
        else:
            cam = cam_keys(t, [(0, (600, 600, 1.3)), (self.dur, (610, 590, 1.4))])
        c = self.apply_cam(F, cam)
        breath = 0.5 + 0.5 * math.sin(t * 2.6)
        p = harrison(640, WL + 225, t, s=1.15, f=-1, eyes="half" if self.dim else "open", brows="worried",
                     mouth="flat", look=(-0.3, -0.4), arm_a=140, elb_a=40, arm_b=120, elb_b=60)
        p = p.but(bob=-breath * 5)
        sets.cabin_plate().blit(F.cx)
        cx = F.cx
        # breathable air volume: shimmering pale fill between overhead and the water
        k = smooth(prog(t, 0, 0.5))
        if self.dim:
            k *= 1 - 0.75 * smooth(prog(t, 0.4, self.dur))
        g = cairo.LinearGradient(0, sets.FLOOR_Y, 0, WL)
        g.add_color_stop_rgba(0, 0.75, 0.95, 1.0, 0.0)
        g.add_color_stop_rgba(0.5, 0.75, 0.95, 1.0, 0.16 * k)
        g.add_color_stop_rgba(1, 0.75, 0.95, 1.0, 0.26 * k)
        cx.rectangle(-600, sets.FLOOR_Y + 20, 2300, WL - sets.FLOOR_Y - 20)
        cx.set_source(g)
        cx.fill()
        HARRISON.draw(cx, p)
        look.water_body(cx, WL, t, color=(0.05, 0.2, 0.22), alpha=0.74, x0=-600, x1=1700, amp=6, seed=1)
        # outline of the pocket
        cx.rectangle(-60, sets.FLOOR_Y + 30, 1200, WL - sets.FLOOR_Y - 40)
        cx.set_dash([18, 14], t * 40)
        cx.set_source_rgba(0.8, 0.97, 1, 0.75 * k)
        cx.set_line_width(5)
        cx.stroke()
        cx.set_dash([])
        cold_key(F, c, 0.85 * (1 - 0.35 * self.dim * smooth(prog(t, 0.3, self.dur))))
        look.glow(F.ax, *c.to_screen(560, 520), 600, (0.7, 0.9, 1.0), 0.12 * k)
        snow(F, t, cam, 0.2)


class S9c(S9b):
    dim = True
    punch = 0.06


# --------------------------------------------------------------------- 10/11  oxygen down, CO2 up
class SGas(Shot):
    punch = 0.05
    kind = "o2"

    def render(self, F):
        t = F.t
        underwater(F, 0.08, (0.05, 0.08, 0.1))
        cam = cam_keys(t, [(0, (560, 520, 1.55)), (self.dur, (580, 510, 1.68))])
        c = self.apply_cam(F, cam)
        cx = F.cx
        co2 = self.kind == "co2"
        breath = 0.5 + 0.5 * math.sin(t * 3.4 - 1.2)
        p = harrison(700, WL + 225, t, s=1.15, f=-1, eyes="half" if co2 else "open", brows="worried",
                     mouth="o", mouth_open=0.4 + 0.7 * breath, look=(-0.4, -0.2) if not co2 else (-0.2, 0.3),
                     arm_a=140, elb_a=40, arm_b=120, elb_b=60, tilt=(math.sin(t * 1.3) * 6 if co2 else 0))
        J = pocket_scene(F, c, t, p)
        mx, my = J["head"][0] - 26, J["head"][1] + 30
        rng = random.Random(5 if not co2 else 6)
        if not co2:
            # O2 molecules drift toward the mouth and vanish one by one
            for i in range(14):
                x0, y0 = rng.uniform(80, 1000), rng.uniform(380, 660)
                tv = 0.15 + i * 0.075
                k = ease_in(prog(t, tv - 0.35, tv))
                if t > tv:
                    continue
                x = x0 + (mx - x0) * k + math.sin(t * 2 + i) * 10 * (1 - k)
                y = y0 + (my - y0) * k + math.cos(t * 2.3 + i) * 10 * (1 - k)
                o2(cx, x, y, 24 * (1 - 0.6 * k), 1.0, "o2")
        else:
            # CO2 piles up in the pocket; haze thickens
            n = int(4 + 22 * smooth(prog(t, 0, self.dur)))
            for i in range(n):
                te = i * self.dur / 26
                age = t - te
                if age < 0:
                    continue
                tx_, ty_ = rng.uniform(60, 1020), rng.uniform(360, 660)
                k = ease_out(prog(age, 0, 0.8))
                x = mx + (tx_ - mx) * k + math.sin(t * 1.5 + i) * 8
                y = my + (ty_ - my) * k + math.cos(t * 1.7 + i) * 8
                o2(cx, x, y, 12 + 14 * k, min(1, age * 4), "co2")
            haze = smooth(prog(t, 0, self.dur))
            cx.rectangle(-600, sets.FLOOR_Y, 2300, WL - sets.FLOOR_Y)
            src(cx, (0.55, 0.42, 0.40, 0.18 * haze))
            cx.fill()
        cold_key(F, c, 0.95)
        snow(F, t, cam, 0.15)


class S10(SGas):
    kind = "o2"


class S11(SGas):
    kind = "co2"


# --------------------------------------------------------------------- 12  the water rises
class S12(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.1, (0.05, 0.08, 0.1))
        cam = cam_keys(t, [(0, (560, 620, 1.3)), (self.dur, (560, 600, 1.42))])
        c = self.apply_cam(F, cam)
        cx = F.cx
        rise = ease_io(prog(t, 0.2, self.dur))
        wl = WL + 40 - 150 * rise
        p = harrison(640, wl + 225 + 20 * rise, t, s=1.15, f=-1, eyes="wide", brows="worried", mouth="flat",
                     look=(0.0, -0.9), tilt=-18 * rise, arm_a=150, elb_a=30, arm_b=140, elb_b=40)
        sets.cabin_plate().blit(cx)
        # scratch marks on the wall where the water used to be
        for k, yy in enumerate((WL + 40, WL - 10, WL - 60, WL - 110)):
            line(cx, [(930, yy), (1010, yy)], (0.9, 0.95, 0.9, 0.55), 5)
        HARRISON.draw(cx, p)
        look.water_body(cx, wl, t, color=(0.05, 0.2, 0.22), alpha=0.76, x0=-600, x1=1700, amp=7, seed=1)
        # headroom bracket shrinking
        top, bot = sets.FLOOR_Y + 22, wl - 8
        bx = 270
        for (a, b) in (((bx, top), (bx, bot)),):
            line(cx, [a, b], (1, 1, 1, 0.9), 5)
        for yy in (top, bot):
            line(cx, [(bx - 22, yy), (bx + 22, yy)], (1, 1, 1, 0.9), 5)
        # arrow pushing up from the water
        ay = bot - 30
        cx.move_to(bx, ay - 36)
        cx.line_to(bx - 20, ay - 6)
        cx.line_to(bx + 20, ay - 6)
        cx.close_path()
        src(cx, (1, 1, 1, 0.9))
        cx.fill()
        cold_key(F, c, 0.9)
        snow(F, t, cam, 0.15)


# --------------------------------------------------------------------- 13  hours pass
class S13a(Shot):
    """Time-lapse wide: the light and the water breathe, he barely moves."""
    punch = 0.03

    def render(self, F):
        t = F.t
        underwater(F, 0.14, (0.03, 0.05, 0.06))
        cam = cam_keys(t, [(0, (560, 640, 1.35)), (self.dur, (540, 700, 1.0))])
        c = self.apply_cam(F, cam)
        p = harrison(700, WL + 225, t * 3, s=1.15, f=-1, eyes="half", brows="worried", mouth="flat",
                     look=(-0.2, 0.4), arm_a=140, elb_a=40, arm_b=120, elb_b=60)
        p = p.but(bob=math.sin(t * 5) * 4)
        pocket_scene(F, c, t * 3, p, wamp=4)
        debris(F.cx, t * 3, [("bottle", 250, WL - 6, 0.8, 1.45), ("cup", 980, WL - 4, 0.8, 0.2), ("plank", 420, WL + 6, 0.9, 0.05)])
        fl = 0.55 + 0.2 * math.sin(t * 7) + 0.15 * math.sin(t * 2.3)
        cold_key(F, c, fl)
        F.vig = 0.75


class S13b(Shot):
    """Cold and exhausted: shivering, teeth chattering."""
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.12, (0.03, 0.05, 0.06))
        cam = cam_keys(t, [(0, (640, 480, 1.9)), (self.dur, (650, 470, 2.05))])
        c = self.apply_cam(F, cam)
        shiver = math.sin(t * 38) * 3
        p = harrison(700 + shiver, WL + 225, t, s=1.15, f=-1, eyes="half", brows="worried", mouth="teeth",
                     look=(-0.1, 0.5), arm_a=150, elb_a=100, arm_b=140, elb_b=110, tilt=-6)
        pocket_scene(F, c, t, p, wamp=3)
        # breath vapour
        hx, hy = 700 - 60, WL + 225 - 340 * 1.15 + 40
        for i in range(3):
            age = (t * 0.9 + i / 3) % 1
            ellipse(F.ax, hx - 40 - age * 120, hy - age * 60, 30 + age * 60, 16 + age * 30)
            src(F.ax, (0.6, 0.7, 0.8, 0.12 * (1 - age)))
            F.ax.fill()
        cold_key(F, c, 0.6)
        F.vig = 0.75


# --------------------------------------------------------------------- 14a  darkness
class S14a(Shot):
    punch = 0.02

    def __init__(self, t0, t1, clank):
        super().__init__(t0, t1)
        self.clank = clank - t0

    def render(self, F):
        t = F.t
        underwater(F, 0.0, (0.005, 0.008, 0.01))
        cam = cam_keys(t, [(0, (660, 470, 2.2)), (self.dur, (660, 465, 2.35))])
        c = self.apply_cam(F, cam)
        up = smooth(prog(t, self.clank, self.clank + 0.3))
        p = harrison(700, WL + 225, t, s=1.15, f=-1, eyes="wide" if up > 0.5 else "half", brows="worried",
                     mouth="flat", look=(-0.2 - 0.6 * up, 0.4 - 0.9 * up), arm_a=150, elb_a=100, arm_b=140, elb_b=110,
                     blink=False)
        pocket_scene(F, c, t, p, wamp=2)
        F.lights.point(*c.to_screen(640, 600), 420 * c.zoom, (0.4, 0.5, 0.68), 0.9)
        F.vig = 0.85
        F.bloom = 0.2


# --------------------------------------------------------------------- 14b  rescue divers enter the wreck
class S14b(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.24, (0.06, 0.13, 0.14))
        cam = cam_keys(t, [(0, (640, 760, 1.15)), (self.dur, (520, 1040, 1.3))])
        c = self.apply_cam(F, cam)
        sets.seabed_plate().blit(F.cx)
        cx = F.cx
        # dark entry hatch in the hull side
        rrect(cx, 330, 1020, 150, 120, 14)
        fs(cx, hexc("#020405"), hexc("#3a3f42"), 10)
        for k, (x0, y0, x1, y1, ph, fig, delay) in enumerate(((760, 420, 470, 1000, 0.0, DIVER, 0.0),
                                                            (980, 300, 640, 900, 1.3, DIVER2, 0.5))):
            u = ease_io(prog(t, delay, self.dur + 0.3))
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            p = diver(x, y, t + ph, s=0.7, f=-1, eyes="open", brows="flat", extra={"hose_len": 360, "hose_dy": -320})
            J = draw_rotated(cx, fig, swim(p, t + ph, 1.0, 0.8), -1.15)
            lx, ly = c.to_screen(*J["head"])
            ang = math.pi * 0.72
            F.lights.spot(lx, ly, ang, spread=0.33, reach=900, power=1.8)
            look.beam(F.ax, lx, ly, ang, length=850 * c.zoom, spread=0.26, alpha=0.16)
            look.bubble_stream(cx, J["head"][0], J["head"][1] - 40, t + ph, t0=-3, rate=6, seed=30 + k, size=(2, 7))
        snow(F, t, cam, 0.5)
        F.lights.rect_grad(-200, 1300, (0.25, 0.45, 0.48), 0.45)
        look.god_rays(F.ax, t, alpha=0.06)


# --------------------------------------------------------------------- 15  searching for bodies
class S15(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.2, (0.015, 0.04, 0.045))
        cam = cam_keys(t, [(0, (560, 860, 1.05)), (self.dur, (540, 840, 1.2))])
        c = self.apply_cam(F, cam)
        sets.corridor_plate().blit(F.cx)
        debris(F.cx, t, [("cloth", 300, 640, 1.0, 0.4), ("boot", 820, 1150, 0.7, -0.4), ("can", 640, 520, 0.8, 0.9)])
        x = kf(t, [(0, 140), (self.dur, 320)])
        p = diver(x, 1500, t, s=1.35, f=1, eyes="open", brows="flat", mouth="flat", look=(0.6, -0.1))
        J = draw_rotated(F.cx, DIVER, swim(p, t, 0.9, 0.6), 0.55)
        look.bubble_stream(F.cx, J["head"][0] - 40, J["head"][1] - 60, t, t0=-3, rate=6, seed=40, size=(3, 9))
        snow(F, t, cam, 0.65)
        ang = -0.75 + 0.35 * math.sin(t * 1.5)
        helmet_lamp(F, c, J, p, ang, reach=1700, spread=0.3, power=2.3, beam_alpha=0.22)


# --------------------------------------------------------------------- 16  "Instead..." rising toward the pocket
class S16(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.18, (0.02, 0.05, 0.06))
        cam = cam_keys(t, [(0, (560, 1000, 1.05)), (self.dur, (560, 900, 1.15))])
        c = self.apply_cam(F, cam)
        sets.cabin_plate().blit(F.cx)
        look.water_body(F.cx, WL, t, color=(0.04, 0.16, 0.18), alpha=0.85, x0=-600, x1=1700, amp=6, seed=1)
        rise = ease_io(prog(t, 0, self.dur + 0.5))
        p = diver(470, 1560 - 220 * rise, t, s=1.15, f=1, eyes="open", brows="up", mouth="flat", look=(0.2, -0.9),
                  arm_a=165, elb_a=10, arm_b=60, elb_b=40, extra={"hose_len": 300, "hose_dy": 200})
        J = draw_rotated(F.cx, DIVER, p, -0.2)
        look.bubble_stream(F.cx, J["head"][0] - 50, J["head"][1] - 60, t, t0=-3, rate=7, seed=41, size=(3, 9))
        F.lights.point(*c.to_screen(*J["head"]), 420 * c.zoom, (0.8, 0.85, 0.8), 0.7)
        lx, ly = c.to_screen(*J["head"])
        ang = -1.45
        F.lights.spot(lx, ly, ang, spread=0.34, reach=1300, power=2.2)
        look.beam(F.ax, lx, ly, ang, length=1200, spread=0.26, alpha=0.2)
        look.caustics(F.ax, t, -100, 0, W + 100, c.to_screen(0, WL)[1] + 40, alpha=0.12)
        snow(F, t, cam, 0.5)


# --------------------------------------------------------------------- 17  they found a survivor
class S17(Shot):
    punch = 0.07

    def __init__(self, t0, t1, grab):
        super().__init__(t0, t1)
        self.grab = grab - t0

    def render(self, F):
        t = F.t
        g = self.grab
        underwater(F, 0.08, (0.03, 0.06, 0.07))
        F.flash = 0.18 * (1 - smooth(prog(t, 0, 0.2)))
        cam = cam_keys(t, [(0, (560, 620, 1.3)), (self.dur, (580, 590, 1.45))], ease_out)
        c = self.apply_cam(F, cam)
        cx = F.cx
        sets.cabin_plate().blit(cx)
        up = ease_out(prog(t, 0, 0.3))
        reach = smooth(prog(t, g - 0.25, g + 0.1))
        p = harrison(780, WL + 225, t, s=1.15, f=-1, eyes="wide", brows="up", mouth="smile" if t > g + 0.3 else "o",
                     look=(-0.7, 0.2), arm_a=140 - 60 * reach, elb_a=40 - 30 * reach, arm_b=120, elb_b=60, blink=False)
        Jh = HARRISON.draw(cx, p)
        pd = diver(340, WL + 400 - 100 * up, t, s=1.15, f=1, eyes="wide", brows="up", mouth="o", look=(0.8, -0.1),
                   arm_a=100 - 10 * reach, elb_a=15, arm_b=50, elb_b=30, extra={"hose": False}, blink=False)
        Jd = DIVER.draw(cx, pd)
        look.water_body(cx, WL, t, color=(0.05, 0.2, 0.22), alpha=0.72, x0=-600, x1=1700, amp=8 + 14 * (1 - up), seed=1)
        splash(cx, 360, WL, t, 0.0, s=1.1, alpha=0.85, seed=8)
        # hands meeting
        if t > g - 0.05:
            mx = (Jh["hand_a"][0] + Jd["hand_a"][0]) / 2
            look.glow(F.ax, *c.to_screen(mx, Jh["hand_a"][1]), 160, (1, 0.95, 0.8), 0.25 * pulse_(t, g, g + 1.2))
        ang = kf(t, [(0, -0.6), (0.3, -0.25), (self.dur, -0.22)], ease_out)
        helmet_lamp(F, c, Jd, pd, ang, reach=1300, spread=0.38, power=2.1, beam_alpha=0.16)
        snow(F, t, cam, 0.25)


# --------------------------------------------------------------------- 18a  rescue: helmet for Harrison
class S18a(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.08, (0.04, 0.07, 0.08))
        cam = cam_keys(t, [(0, (540, 600, 1.3)), (self.dur, (545, 590, 1.38))])
        c = self.apply_cam(F, cam)
        cx = F.cx
        sets.cabin_plate().blit(cx)
        p = harrison(700, WL + 225, t, s=1.15, f=-1, eyes="happy", brows="up", mouth="smile",
                     arm_a=100, elb_a=20, arm_b=120, elb_b=60)
        Jh = HARRISON.draw(cx, p)
        pd = diver(350, WL + 225, t, s=1.15, f=1, eyes="open", brows="flat", mouth="smile",
                   arm_a=95, elb_a=25, arm_b=70, elb_b=60, extra={"hose_len": 300, "hose_dy": 300})
        Jd = DIVER.draw(cx, pd)
        # spare dive helmet passed between them
        hk = smooth(prog(t, 0.1, 1.0))
        hx = Jd["hand_a"][0] + (Jh["hand_a"][0] - Jd["hand_a"][0]) * 0.5 * hk
        hy = Jd["hand_a"][1] - 40
        ellipse(cx, hx, hy, 66, 62)
        fs(cx, hexc("#E9EEF2"), OUTLINE, 6)
        circle(cx, hx + 8, hy + 4, 34)
        fs(cx, hexc("#10181b"), OUTLINE, 6)
        look.water_body(cx, WL, t, color=(0.05, 0.2, 0.22), alpha=0.72, x0=-600, x1=1700, amp=6, seed=1)
        helmet_lamp(F, c, Jd, pd, -0.1, reach=1200, spread=0.42, power=1.8, beam_alpha=0.12)
        F.lights.point(*c.to_screen(560, 520), 700, (1.0, 0.85, 0.65), 0.35)
        snow(F, t, cam, 0.25)


# --------------------------------------------------------------------- 18b  final image: up toward the light
class S18b(Shot):
    punch = 0.04

    def render(self, F):
        t = F.t
        underwater(F, 0.22, (0.08, 0.17, 0.19))
        F.black = smooth(prog(t, self.dur - 0.6, self.dur))
        cam = cam_keys(t, [(0, (540, 1060, 1.0)), (self.dur, (540, 900, 1.1))])
        c = self.apply_cam(F, cam)
        cx = F.cx
        g = cairo.LinearGradient(0, -400, 0, 2300)
        g.add_color_stop_rgb(0, 0.32, 0.6, 0.62)
        g.add_color_stop_rgb(0.5, 0.1, 0.27, 0.3)
        g.add_color_stop_rgb(1, 0.02, 0.07, 0.08)
        cx.rectangle(-800, -800, 2700, 3500)
        cx.set_source(g)
        cx.fill()
        # the diving bell waiting above, glowing
        bx, by = 540, 160
        rrect(cx, bx - 170, by - 220, 340, 300, 60)
        fs(cx, hexc("#D9B43A"), OUTLINE, 8)
        circle(cx, bx, by - 70, 58)
        fs(cx, hexc("#FFF2C8"), OUTLINE, 6)
        rrect(cx, bx - 190, by + 70, 380, 30, 10)
        fs(cx, hexc("#3a3f44"), OUTLINE, 5)
        line(cx, [(bx, by - 220), (bx, -800)], OUTLINE, 10)
        # guide line
        line(cx, [(470, by + 100), (470, 2400)], hexc("#E2D9B8"), 5)
        rise = 260 * ease_io(prog(t, 0, self.dur + 1.0))
        figs = ((DIVER, 330, 1330, 0.0, "#E8B620"), (HARRISON_HELMET, 560, 1240, 0.8, None), (DIVER2, 720, 1420, 1.6, None))
        for fig, x, y, ph, _ in figs:
            p = diver(x, y - rise, t + ph, s=1.1, f=1 if x < 540 else -1, eyes="happy" if fig is HARRISON_HELMET else "open",
                      brows="up" if fig is HARRISON_HELMET else "flat", mouth="smile",
                      arm_a=170, elb_a=10, arm_b=150, elb_b=20, extra={"hose": fig is not HARRISON_HELMET, "hose_len": 300, "hose_dy": 400})
            p = swim(p, t + ph, 0.7, 0.4).but(arm_a=170, elb_a=10)
            J = fig.draw(cx, p)
            look.bubble_stream(cx, J["head"][0], J["head"][1] - 70, t + ph, t0=-3, rate=6, seed=50 + int(ph * 10), size=(3, 9))
        snow(F, t, cam, 0.5)
        F.lights.rect_grad(-300, 1500, (0.55, 0.75, 0.75), 1.0)
        F.lights.point(*c.to_screen(bx, by), 700, (1.0, 0.92, 0.7), 1.2)
        look.god_rays(F.ax, t, x0=0, x1=1080, alpha=0.11, color=(0.8, 0.95, 1.0))
        look.glow(F.ax, *c.to_screen(bx, by - 70), 380, (1, 0.93, 0.7), 0.45)

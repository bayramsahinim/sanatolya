"""Shots 1-7: the hook, the reveal, the wreck, the flashback capsize, the air pocket."""
import math
import random

import cairo

from cinecode.core import (OUTLINE, Cam, H, W, circle, clamp, ease_in, ease_io, ease_out, ellipse, fs, hexc, kf,
                           line, prog, rrect, shake, smooth, src)
from . import look, sets
from .cast import (DIVER, DIVER2, DIVER_ST, HARRISON, HARRISON_ST, bare_hand, diver, glove_hand, harrison)
from .common import (UNDER_FOG, WL, cam_keys, debris, draw_rotated, helmet_lamp, snow, splash, swim, underwater)
from .frame import Shot


# --------------------------------------------------------------------- 1a  close-up: diver searching
class S1a(Shot):
    """Strong opening close-up: the diver's helmet in the black wreck, lamp scanning."""

    def render(self, F):
        t = F.t
        underwater(F, 0.16, (0.02, 0.05, 0.055))
        cam = cam_keys(t, [(0, (560, 820, 1.18)), (self.dur, (600, 800, 1.30))])
        c = self.apply_cam(F, cam)
        sets.corridor_plate().blit(F.cx)
        debris(F.cx, t, [("cloth", 980, 520, 0.9, 0.3), ("can", 860, 1180, 1.0, 1.0)])
        look_x = math.sin(t * 1.9) * 0.6 + 0.3
        p = diver(330, 1450, t, s=2.2, f=1, eyes="open", brows="flat", look=(look_x, 0.15), mouth="flat",
                  arm_a=60, elb_a=40, arm_b=40, elb_b=50, lean=10)
        p = p.but(bob=math.sin(t * 1.5) * 6)
        J = DIVER.draw(F.cx, p)
        look.bubble_stream(F.cx, J["head"][0] - 70, J["head"][1] - 120, t, t0=-3, rate=7, seed=4)
        snow(F, t, cam, 0.65)
        ang = -0.05 + math.sin(t * 1.9) * 0.22
        helmet_lamp(F, c, J, p, ang, reach=1500, spread=0.33, power=2.2, beam_alpha=0.26)


# --------------------------------------------------------------------- 1b  POV: the dark corridor
class S1b(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.2, (0.015, 0.04, 0.045))
        cam = cam_keys(t, [(0, (540, 860, 1.0)), (self.dur, (548, 840, 1.14))])
        c = self.apply_cam(F, cam)
        sets.corridor_plate().blit(F.cx)
        debris(F.cx, t, [("boot", 300, 1050, 0.8, 0.6), ("bottle", 760, 650, 0.9, -0.8),
                         ("cloth", 620, 1330, 1.2, 0.1), ("plank", 380, 560, 0.7, 0.9)])
        snow(F, t, cam, 0.7)
        # lamp from just behind the camera, bottom-left, sweeping toward the black doorway ahead
        sweep = kf(t, [(0, -1.05), (0.7, -1.35), (1.3, -1.15)], ease_io)
        ox, oy = 120, 1880
        F.lights.spot(ox, oy, sweep, spread=0.30, reach=2300, power=2.4)
        look.beam(F.ax, ox, oy, sweep, length=2100, spread=0.24, alpha=0.2)


# --------------------------------------------------------------------- 1c  insert: the hand grabs
class S1c(Shot):
    """Gloved hand probing a black hatchway -> a bare hand shoots out and grabs it."""
    punch = 0.04

    def __init__(self, t0, t1, grab):
        super().__init__(t0, t1)
        self.grab = grab - t0      # local time of the grab

    def render(self, F):
        t = F.t
        g = self.grab
        underwater(F, 0.12, (0.02, 0.045, 0.05))
        hit = t - g
        if hit >= 0:
            F.shake = shake(t, 22 * math.exp(-hit * 5), freq=24, seed=3)
            F.flash = 0.35 * math.exp(-hit * 14)
        cam = cam_keys(t, [(0, (540, 960, 1.0)), (g, (560, 960, 1.06)), (g + 0.12, (590, 960, 1.16)),
                           (self.dur, (600, 960, 1.2))], ease_out)
        c = self.apply_cam(F, cam)
        cx = F.cx
        # steel wall with a black open hatch on the right
        g1 = cairo.LinearGradient(0, 0, W, 0)
        g1.add_color_stop_rgb(0, *hexc("#56635F")[:3])
        g1.add_color_stop_rgb(1, *hexc("#3C4744")[:3])
        cx.rectangle(-300, -300, W + 600, H + 600)
        cx.set_source(g1)
        cx.fill()
        for yy in range(-300, H + 300, 210):
            line(cx, [(-300, yy), (W + 300, yy)], hexc("#2F3836"), 6)
            for xx in range(-260, 620, 90):
                circle(cx, xx, yy + 22, 7)
                fs(cx, hexc("#7C8A86"), OUTLINE, 2)
        rrect(cx, 620, 330, 560, 1240, 60)
        fs(cx, hexc("#020405"), hexc("#262E2C"), 34)
        rrect(cx, 620, 330, 560, 1240, 60)
        fs(cx, None, OUTLINE, 6)
        for yy in (420, 1480):
            rrect(cx, 590, yy - 40, 60, 80, 10)
            fs(cx, hexc("#6E7975"), OUTLINE, 5)
        # glove reaching in from the left
        reach = kf(t, [(0, 0), (g, 1)], ease_io)
        gx = -180 + 520 * reach
        gy = 1010 + math.sin(t * 2) * 10
        jerk = 0.0
        if hit >= 0:
            jerk = 70 * ease_out(prog(hit, 0, 0.12)) - 40 * smooth(prog(hit, 0.12, 0.6))
        # the bare hand shoots out of the dark
        if hit > -0.06:
            k = ease_out(prog(t, g - 0.06, g + 0.02))
            hx = 1300 + (gx + 235 - 1300) * k + jerk   # palm lands over the glove's fingers
            bare_hand(cx, hx, gy - 6, 1.1, math.pi + 0.05, grip=0.85 * smooth(prog(hit, 0.0, 0.1)), spread=0.0)
        glove_hand(cx, gx + jerk, gy, 1.05, 0.03, grip=0.15 + 0.5 * smooth(prog(hit, 0.05, 0.25)))
        if hit >= 0:   # fingers wrap over the glove (drawn on top)
            k = smooth(prog(hit, 0.0, 0.1))
            for i, fy in enumerate((-40, -10, 20)):
                rrect(cx, gx + jerk + 150, gy + fy - 14, 70 * k, 28, 14)
                fs(cx, hexc("#8E5E3E"), OUTLINE, 6)
        look.bubble_stream(cx, gx + jerk + 200, gy, t, t0=self.dur + 1, burst=(g, 30), seed=7)
        snow(F, t, cam, 0.5)
        # helmet lamp light from upper-left
        F.lights.spot(-80, 300, 0.62, spread=0.42, reach=2200, power=2.3)
        look.beam(F.ax, -80, 300, 0.62, length=1900, spread=0.3, alpha=0.16)


# --------------------------------------------------------------------- 1d  the diver's reaction
class S1d(Shot):
    punch = 0.06

    def render(self, F):
        t = F.t
        underwater(F, 0.15, (0.02, 0.05, 0.055))
        F.shake = shake(t, 10 * math.exp(-t * 3), freq=20, seed=8)
        cam = cam_keys(t, [(0, (520, 840, 1.25)), (self.dur, (500, 830, 1.36))])
        c = self.apply_cam(F, cam)
        sets.corridor_plate().blit(F.cx)
        back = 60 * ease_out(prog(t, 0, 0.25))
        p = diver(380 - back, 1450, t, s=2.0, f=1, eyes="wide", brows="up", mouth="o", mouth_open=1.3,
                  look=(0.7, 0.0), lean=-12, arm_a=95, elb_a=10, arm_b=25, elb_b=60, blink=False)
        J = DIVER.draw(F.cx, p)
        # the stranger's arm, out of the black on the right, still clamped to the diver's wrist
        hx, hy = J["hand_a"]
        line(F.cx, [(hx + 10, hy), (1300, hy + 60)], hexc("#8A5A3B"), 26)
        F.cx.move_to(hx + 10, hy - 13)
        F.cx.line_to(1300, hy + 47)
        F.cx.move_to(hx + 10, hy + 13)
        F.cx.line_to(1300, hy + 73)
        src(F.cx, OUTLINE)
        F.cx.set_line_width(5)
        F.cx.stroke()
        circle(F.cx, hx + 6, hy, 24)
        fs(F.cx, hexc("#8A5A3B"), OUTLINE, 5)
        look.bubble_stream(F.cx, J["head"][0] - 80, J["head"][1] - 120, t, t0=self.dur + 5, burst=(0.0, 40), seed=9)
        snow(F, t, cam, 0.6)
        ang = 0.15 + 0.25 * math.sin(t * 9) * math.exp(-t * 3)
        helmet_lamp(F, c, J, p, ang, reach=1500, spread=0.33, power=2.2, beam_alpha=0.24)


# --------------------------------------------------------------------- 2  reveal: Harrison alive in the pocket
class S2(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.1, (0.025, 0.05, 0.06))
        cam = cam_keys(t, [(0, (560, 760, 1.15)), (self.dur, (700, 600, 1.5))])
        c = self.apply_cam(F, cam)
        sets.cabin_plate().blit(F.cx)
        cx = F.cx
        # Harrison: head + shoulders above the water, clinging to the table
        p = harrison(820, WL + 225, t, s=1.15, f=-1, view="side", eyes="wide", brows="up", mouth="o",
                     mouth_open=0.9, look=(-0.6, 0.1), arm_a=140, elb_a=40, arm_b=120, elb_b=60, blink=False)
        p = p.but(bob=math.sin(t * 1.3) * 5)
        HARRISON.draw(cx, p)
        # diver's helmet just breaking the surface, bottom-left
        pd = diver(140, WL + 300, t, s=1.15, f=1, eyes="open", brows="up", mouth="o", look=(0.8, -0.1),
                   arm_a=80, elb_a=20, arm_b=60, elb_b=30, extra={"hose": False})
        Jd = DIVER.draw(cx, pd)
        look.water_body(cx, WL, t, color=(0.05, 0.2, 0.22), alpha=0.72, x0=-600, x1=1700, amp=7, seed=1)
        snow(F, t, cam, 0.35)
        ang = kf(t, [(0, 0.2), (0.6, -0.42), (self.dur, -0.38)], ease_out)
        helmet_lamp(F, c, Jd, pd, ang, reach=1300, spread=0.36, power=2.0, beam_alpha=0.18)


# --------------------------------------------------------------------- 3a/3b  the wreck on the seabed
def _seabed_lights(F, c, t, divers=True):
    F.lights.rect_grad(-200, 1300, (0.25, 0.45, 0.48), 0.6)
    look.god_rays(F.ax, t, alpha=0.07)


class S3a(Shot):
    """Descend through murky water onto the upturned hull."""
    punch = 0.03

    def render(self, F):
        t = F.t
        underwater(F, 0.28, (0.07, 0.15, 0.16))
        F.depth_fog = None
        cam = cam_keys(t, [(0, (560, 350, 0.82)), (self.dur, (590, 820, 0.95))])
        c = self.apply_cam(F, cam)
        sets.seabed_plate().blit(F.cx)
        # two support divers with lamps working near the hull
        for k, (x, y, ph) in enumerate(((1080, 760, 0.0), (90, 1180, 1.7))):
            p = diver(x, y, t + ph, s=0.55, f=-1 if k == 0 else 1, eyes="open", extra={"hose_len": 400, "hose_dy": -300})
            J = draw_rotated(F.cx, DIVER if k == 0 else DIVER2, swim(p, t + ph, 0.8, 0.6), (-1 if k == 0 else 1) * 1.1)
            lx, ly = c.to_screen(*J["head"])
            ang = (math.pi - 0.6) if k == 0 else 0.5
            F.lights.spot(lx, ly, ang, spread=0.32, reach=700, power=1.4)
            look.beam(F.ax, lx, ly, ang, length=600 * c.zoom, spread=0.25, alpha=0.14)
            look.bubble_stream(F.cx, J["head"][0], J["head"][1] - 40, t + ph, t0=-3, rate=5, seed=10 + k, size=(2, 6))
        snow(F, t, cam, 0.55)
        _seabed_lights(F, c, t)


class S3b(Shot):
    """Closer on the hull: air leaking out of a seam - something is still trapped inside."""
    punch = 0.05

    def render(self, F):
        t = F.t
        underwater(F, 0.2, (0.06, 0.13, 0.14))
        cam = cam_keys(t, [(0, (300, 1000, 1.6)), (self.dur, (360, 960, 1.8))])
        c = self.apply_cam(F, cam)
        sets.seabed_plate().blit(F.cx)
        for k, sx in enumerate((210, 330, 470)):
            look.bubble_stream(F.cx, sx, 960 + k * 30, t, t0=-4, rate=3 + k, seed=20 + k, size=(2, 7), rise=180, life=3)
        snow(F, t, cam, 0.5)
        _seabed_lights(F, c, t)
        sx, sy = c.to_screen(700, 820)
        F.lights.spot(sx + 200, sy - 600, 2.2, spread=0.4, reach=1500, power=1.4)
        look.beam(F.ax, sx + 200, sy - 600, 2.2, length=1300, spread=0.3, alpha=0.12)


# --------------------------------------------------------------------- 4  flashback: the tug in the storm
def _storm(F, t, cam, swell=None, sea_y=1180):
    c = cam
    sets.storm_sky_plate().blit(F.cx)
    sets.wave_layer(F.cx, t, sea_y - 40, 18, 0.006, 0.9, "#1F3A44", seed=1)
    sets.wave_layer(F.cx, t, sea_y + 10, 26, 0.008, 1.2, "#1A3039", seed=2)
    return c


class S4(Shot):
    punch = 0.06

    def render(self, F):
        t = F.t
        F.unlit = True
        F.fog = (0.28, 0.32, 0.35)
        F.fog_amt = 0.12
        F.grade = ((0.01, 0.01, 0.015), (1.0, 0.97, 0.94), 0.78)
        F.bloom = 0.35
        F.flash = 0.8 * (1 - smooth(prog(t, 0, 0.3)))
        F.shake = shake(t, 5, freq=3, seed=4)
        cam = cam_keys(t, [(0, (560, 1080, 1.05)), (self.dur, (600, 1060, 1.18))])
        c = self.apply_cam(F, cam)
        _storm(F, t, c)
        bob = math.sin(t * 1.6) * 30
        pitch = math.sin(t * 1.6 + 0.8) * 0.09
        sets.tug(F.cx, 560, 1220 + bob, 1.0, pitch, lights=1.0, t=t)
        sets.wave_layer(F.cx, t, 1300, 34, 0.007, 1.6, "#16303A", seed=3)
        sets.wave_layer(F.cx, t, 1460, 50, 0.005, 1.3, "#10242C", seed=4)
        sets.rain(F.cx, t, 0.45)
        # wheelhouse glow + mast light
        look.glow(F.ax, *c.to_screen(600, 1220 + bob - 300), 160, (1, 0.8, 0.5), 0.18)


class S5(Shot):
    """A huge swell rolls the tug over."""
    punch = 0.04

    def __init__(self, t0, t1, roll):
        super().__init__(t0, t1)
        self.roll = roll - t0

    def render(self, F):
        t = F.t
        r = self.roll
        F.unlit = True
        F.fog = (0.28, 0.32, 0.35)
        F.fog_amt = 0.12
        F.grade = ((0.01, 0.01, 0.015), (1.0, 0.97, 0.94), 0.78)
        F.bloom = 0.35
        k = ease_in(prog(t, r - 0.2, r + 0.9))
        F.shake = shake(t, 6 + 26 * pulse_(t, r, r + 1.2), freq=8, seed=5)
        cam = cam_keys(t, [(0, (560, 1060, 0.92)), (self.dur, (560, 1140, 1.02))])
        c = self.apply_cam(F, cam)
        _storm(F, t, c)
        swell_h = 380 * smooth(prog(t, r - 0.9, r + 0.3)) * (1 - 0.5 * smooth(prog(t, r + 0.6, self.dur)))
        rot = -math.pi * 0.97 * k + math.sin(t * 1.6) * 0.06 * (1 - k)
        y = 1220 + math.sin(t * 1.6) * 20 - swell_h * 0.7 + 260 * smooth(prog(t, r + 0.6, self.dur + 0.5))
        x = 560 + 140 * k
        sets.tug(F.cx, x, y, 1.0, rot, lights=1 - k)
        sets.wave_layer(F.cx, t, 1300, 34, 0.007, 1.6, "#16303A", seed=3, swell=(400 + 300 * k, swell_h, 420))
        splash(F.cx, x, 1200, t, r + 0.45, s=1.6, alpha=0.9, seed=4)
        sets.wave_layer(F.cx, t, 1470, 50, 0.005, 1.3, "#10242C", seed=4, swell=(300 + 300 * k, swell_h * 0.5, 500))
        sets.rain(F.cx, t, 0.5)


def pulse_(t, a, b):
    return smooth(prog(t, a, a + 0.15)) * (1 - smooth(prog(t, a + 0.15, b)))


# --------------------------------------------------------------------- 6  inside: the water rushes in
class S6(Shot):
    punch = 0.05

    def render(self, F):
        t = F.t
        flick = 0.65 + 0.35 * (math.sin(t * 37) > -0.3) * (0.7 + 0.3 * math.sin(t * 13))
        F.lights.ambient[:] = (0.05, 0.03, 0.03)
        F.fog = (0.05, 0.02, 0.02)
        F.fog_amt = 0.05
        F.grade = ((0.01, 0.005, 0.005), (1.04, 0.98, 0.95), 0.9)
        rot = kf(t, [(0, -0.12), (self.dur, 0.42)], ease_in)
        F.shake = shake(t, 8, freq=12, seed=6)
        cam = Cam(540, 900, 1.22, rot)
        c = self.apply_cam(F, cam)
        sets.corridor_plate_dry().blit(F.cx)
        cx = F.cx
        # Harrison scrambling through the tilting corridor
        p = harrison(560, 1330, t, s=1.45, f=-1, eyes="wide", brows="worried", mouth="scream", mouth_open=0.8,
                     lean=18, blink=False)
        from cinecode.characters import run as run_
        p = run_(p, t, speed=2.0, amp=0.8)
        p = p.but(eyes="wide", mouth="scream")
        HARRISON.draw(cx, p)
        # water: jet from a doorway + rising flood
        lvl = 1420 - 200 * smooth(prog(t, 0, self.dur))
        jet = smooth(prog(t, 0, 0.3))
        for k in range(10):
            yy = 900 + k * 14
            cx.move_to(1180, yy)
            cx.curve_to(900, yy - 40 + k * 4, 760, yy + 120, 640 - k * 10, lvl)
            cx.set_source_rgba(0.75, 0.88, 0.9, 0.22 * jet)
            cx.set_line_width(26 - k)
            cx.stroke()
        look.water_body(cx, lvl, t * 1.8, color=(0.08, 0.22, 0.24), alpha=0.82, x0=-600, x1=1700, amp=22, seed=3)
        splash(cx, 640, lvl, (t % 0.6), 0.0, s=0.9, alpha=0.8, seed=int(t / 0.6) + 2)
        # red emergency light
        F.lights.point(*c.to_screen(540, 300), 900, (1.0, 0.25, 0.18), 2.0 * flick)
        F.lights.point(*c.to_screen(560, 1250), 520, (0.9, 0.5, 0.35), 0.5 * flick)
        look.glow(F.ax, *c.to_screen(540, 300), 240, (1.0, 0.3, 0.2), 0.35 * flick)


# --------------------------------------------------------------------- 7a  swimming up in the dark
class S7a(Shot):
    punch = 0.04

    def render(self, F):
        t = F.t
        underwater(F, 0.25, (0.03, 0.08, 0.09))
        cam = cam_keys(t, [(0, (560, 1080, 1.0)), (self.dur, (580, 980, 1.1))])
        c = self.apply_cam(F, cam)
        sets.cabin_plate().blit(F.cx)
        look.water_body(F.cx, WL, t, color=(0.04, 0.16, 0.18), alpha=0.82, x0=-600, x1=1700, amp=6, seed=1)
        rise = 300 * ease_io(prog(t, 0, self.dur + 0.4))
        p = harrison(520, 1640 - rise, t, s=1.25, f=1, eyes="squeeze", brows="worried", mouth="flat",
                     blink=False)
        p = swim(p, t, 1.8, 1.0).but(arm_a=160 + 20 * math.sin(t * 11), arm_b=150 - 20 * math.sin(t * 11), elb_a=20, elb_b=20)
        J = draw_rotated(F.cx, HARRISON, p, -0.25)
        look.bubble_stream(F.cx, J["head"][0] + 20, J["head"][1] + 20, t, t0=-1, rate=9, seed=12, size=(3, 9))
        F.lights.point(*c.to_screen(*J["head"]), 600, (0.5, 0.7, 0.8), 0.8)
        # surface above glowing faintly
        look.caustics(F.ax, t, -100, 0, W + 100, 600, alpha=0.08)
        F.lights.rect_grad(-100, 1100, (0.3, 0.5, 0.55), 0.7)
        snow(F, t, cam, 0.5)


# --------------------------------------------------------------------- 7b  surfacing into the air pocket
class S7b(Shot):
    punch = 0.05

    def __init__(self, t0, t1, breach):
        super().__init__(t0, t1)
        self.breach = breach - t0

    def render(self, F):
        t = F.t
        b = self.breach
        underwater(F, 0.12, (0.06, 0.1, 0.13))
        cam = cam_keys(t, [(0, (560, 780, 1.18)), (self.dur, (590, 700, 1.32))])
        c = self.apply_cam(F, cam)
        sets.cabin_plate().blit(F.cx)
        up = ease_out(prog(t, b - 0.1, b + 0.35))
        gasp = smooth(prog(t, b, b + 0.2)) * (1 - 0.6 * smooth(prog(t, b + 0.8, b + 1.6)))
        p = harrison(560, WL + 225 + 200 * (1 - up), t, s=1.15, f=-1, view="side", eyes="wide" if up > 0.5 else "squeeze",
                     brows="worried", mouth="o", mouth_open=0.6 + 0.8 * gasp, look=(-0.3, -0.5), blink=False,
                     arm_a=150 - 20 * up, elb_a=40, arm_b=130, elb_b=70)
        p = p.but(bob=math.sin(t * 2.3) * 6 * up)
        HARRISON.draw(F.cx, p)
        look.water_body(F.cx, WL, t, color=(0.05, 0.2, 0.22), alpha=0.72, x0=-600, x1=1700, amp=7 + 10 * pulse_(t, b, b + 1.5), seed=1)
        splash(F.cx, 560, WL, t, b, s=1.1, alpha=0.85, seed=6)
        # stylised cold key light so we can read the scene (in reality: total darkness)
        F.lights.point(*c.to_screen(300, 300), 900, (0.45, 0.6, 0.8), 0.8)
        snow(F, t, cam, 0.25)

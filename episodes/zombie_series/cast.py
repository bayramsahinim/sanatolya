"""Series cast for Just Needy — Zombie Apocalypse.

The hero is the channel's Just Needy guy (cinecode.characters.HERO, unchanged).
Everyone else shares the same stick-figure rig so the series reads as one world.
"""
import math
import random

from cinecode.characters import HERO, Figure, Pose, Style, hero_pose  # noqa: F401
from cinecode.core import (OUTLINE, circle, clamp, ellipse, fs, hexc, lerp, line, rrect, shade, smooth,
                           src)

# ------------------------------------------------------------------ zombies
ZOMBIE_SKIN = hexc("#B9C7A2")


class ZombieStyle(Style):
    """Infected locals: grey-green skin, torn clothes, sunken eyes, stiff limbs."""
    skin = ZOMBIE_SKIN
    limb = hexc("#2A2C24")

    def __init__(self, shirt="#8E3B32", pants="#3E5C86", kind="tee", seed=0, overalls=False, cap=None,
                 hair=None):
        self.shirt = hexc(shirt)
        self.pants = hexc(pants)
        self.kind = kind
        self.seed = seed
        self.overalls = overalls
        self.cap = hexc(cap) if cap else None
        self.hair = hexc(hair) if hair else None

    def _ragged(self, cx, xl, xr, y, r, amp=10, n=7):
        """ragged hem path segment from right to left at height y."""
        for i in range(n + 1):
            x = xr - (xr - xl) * i / n
            cx.line_to(x, y + (amp if i % 2 else 0) + r.random() * 4)

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        r = random.Random(self.seed)
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 34
        # shirt with a torn hem
        cx.move_to(-hw + 2, -T + 10)
        cx.curve_to(-hw - 2, -T + 2, -hw + 8, -T - 2, -hw + 18, -T - 2)
        cx.line_to(hw - 18, -T - 2)
        cx.curve_to(hw - 8, -T - 2, hw + 2, -T + 2, hw - 2, -T + 10)
        cx.line_to(hw + 2, 4)
        self._ragged(cx, -hw - 2, hw + 2, 6, r)
        cx.close_path()
        fs(cx, self.shirt, OUTLINE, self.outline_w)
        if self.kind == "flannel":
            cx.save()
            cx.move_to(-hw + 2, -T + 10)
            cx.line_to(hw - 2, -T + 10)
            cx.line_to(hw + 2, 6)
            cx.line_to(-hw - 2, 6)
            cx.close_path()
            cx.clip()
            for k in range(-4, 5):
                cx.rectangle(k * 18 - 3, -T - 10, 7, T + 30)
                cx.rectangle(-60, -T + k * 18 + 60, 120, 7)
            src(cx, shade(self.shirt, -0.45), 0.55)
            cx.fill()
            cx.restore()
        if self.overalls:
            den = self.pants
            cx.move_to(-22, -T * 0.55)
            cx.line_to(22, -T * 0.55)
            cx.line_to(hw + 2, 8)
            cx.line_to(-hw - 2, 8)
            cx.close_path()
            fs(cx, den, OUTLINE, 4)
            line(cx, [(-18, -T * 0.55), (-24, -T + 4)], den, 9)
            line(cx, [(18, -T * 0.55), (24, -T + 4)], den, 9)
            circle(cx, -18, -T * 0.55 + 6, 4)
            circle(cx, 18, -T * 0.55 + 6, 4)
            fs(cx, hexc("#D9B44A"), OUTLINE, 2)
            rrect(cx, -12, -T * 0.42, 24, 18, 3)
            fs(cx, shade(den, -0.15), OUTLINE, 2.5)
        # stains / rips
        for k in range(3):
            ellipse(cx, -20 + r.random() * 40, -T * 0.25 - r.random() * T * 0.5, 6 + r.random() * 6,
                    4 + r.random() * 4)
            src(cx, hexc("#5A2A24"), 0.55)
            cx.fill()
        line(cx, [(hw - 10, -T * 0.6), (hw - 2, -T * 0.5), (hw - 12, -T * 0.42)], OUTLINE, 3)
        cx.restore()

    def draw_head_back(self, cx, fig, J, p):
        if self.hair is not None:
            hx, hy = J["head"]
            R = self.head_r
            cx.save()
            cx.translate(hx, hy)
            cx.rotate(J["head_r"])
            r = random.Random(self.seed + 5)
            for k in range(9):
                a = math.pi * (1.0 + k / 8)
                circle(cx, math.cos(a) * R * 0.95, math.sin(a) * R * 0.95, 11 + r.random() * 6)
            fs(cx, self.hair, OUTLINE, 4)
            cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        off = f * R * 0.22
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # sunken eye shadows (drawn over the face, multiply-ish)
        for side in (-1, 1):
            ellipse(cx, off + side * R * 0.34, -R * 0.06 + 14, 15, 7)
            src(cx, hexc("#55613F"), 0.45)
            cx.fill()
        # decay patch + stitches
        r = random.Random(self.seed)
        px, py = -f * R * 0.35 + (r.random() - 0.5) * 20, -R * 0.55
        ellipse(cx, px, py, 13, 9, 0.4)
        src(cx, hexc("#7E8F63"), 0.9)
        cx.fill()
        line(cx, [(px - 22, py + 22), (px + 4, py + 30)], OUTLINE, 3)
        for k in range(3):
            x = px - 18 + k * 9
            line(cx, [(x, py + 20), (x + 3, py + 32)], OUTLINE, 2.5)
        if self.cap is not None:
            cx.move_to(-R - 2, -R * 0.38)
            cx.curve_to(-R - 2, -R * 1.25, R + 2, -R * 1.25, R + 2, -R * 0.38)
            cx.close_path()
            fs(cx, self.cap, OUTLINE, self.outline_w)
            if p.view == "side":
                cx.move_to(f * R * 0.5, -R * 0.42)
                cx.line_to(f * (R + 34), -R * 0.36)
                cx.curve_to(f * (R + 34), -R * 0.24, f * R * 0.6, -R * 0.26, f * R * 0.4, -R * 0.3)
                cx.close_path()
                fs(cx, shade(self.cap, -0.2), OUTLINE, 4)
            else:
                ellipse(cx, 0, -R * 0.38, R * 0.85, 9)
                fs(cx, shade(self.cap, -0.2), OUTLINE, 4)
        # drool
        if p.extra.get("drool", 0) > 0:
            dx = off * 1.1 + 6
            d = p.extra["drool"]
            line(cx, [(dx, R * 0.6), (dx + 2, R * 0.6 + 26 * d)], hexc("#CFE3C0", 0.9), 4)
        cx.restore()


class MailmanStyle(Style):
    shirt = hexc("#9CB6CF")
    shorts = hexc("#2E3F5C")
    bag = hexc("#7A5232")

    def draw_back(self, cx, fig, J, p):
        # mailbag on the hip, behind the body
        hx, hy = J["hip"]
        f = p.f if p.view == "side" else 1
        cx.save()
        cx.translate(hx - f * 34, hy - 18 + math.sin(p.t * 14) * 4)
        cx.rotate(-0.1 * f)
        rrect(cx, -34, -26, 68, 54, 10)
        fs(cx, self.bag, OUTLINE, self.outline_w)
        rrect(cx, -34, -26, 68, 22, 8)
        fs(cx, shade(self.bag, -0.2), OUTLINE, 4)
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 34
        cx.move_to(-hw, 0)
        cx.line_to(-hw + 2, -T + 16)
        cx.curve_to(-hw + 2, -T + 2, -hw + 12, -T, -hw + 20, -T)
        cx.line_to(hw - 20, -T)
        cx.curve_to(hw - 12, -T, hw - 2, -T + 2, hw - 2, -T + 16)
        cx.line_to(hw, 0)
        cx.close_path()
        fs(cx, self.shirt, OUTLINE, self.outline_w)
        rrect(cx, -hw - 2, -10, 2 * hw + 4, 34, 6)
        fs(cx, self.shorts, OUTLINE, 4)
        # strap + patch
        line(cx, [(-hw + 8, -T + 4), (hw - 6, -6)], self.bag, 9)
        rrect(cx, 8, -T + 22, 18, 14, 3)
        fs(cx, hexc("#E04848"), OUTLINE, 2)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        if p.extra.get("cap_off", 0) > 0:
            cx.translate(-f * 30 * p.extra["cap_off"], -60 * p.extra["cap_off"])
            cx.rotate(-0.6 * p.extra["cap_off"] * (f or 1))
        cx.move_to(-R - 2, -R * 0.36)
        cx.curve_to(-R, -R * 1.2, R, -R * 1.2, R + 2, -R * 0.36)
        cx.close_path()
        fs(cx, self.shorts, OUTLINE, self.outline_w)
        if p.view == "side":
            cx.move_to(f * R * 0.4, -R * 0.4)
            cx.line_to(f * (R + 30), -R * 0.34)
            cx.curve_to(f * (R + 30), -R * 0.22, f * R * 0.6, -R * 0.24, f * R * 0.3, -R * 0.28)
            cx.close_path()
            fs(cx, shade(self.shorts, -0.3), OUTLINE, 4)
        circle(cx, 0, -R * 0.78, 7)
        fs(cx, hexc("#E9B949"), OUTLINE, 2)
        cx.restore()


NEIGHBOR = Figure(ZombieStyle("#A0463A", "#4C6A92", kind="flannel", seed=3, overalls=True, cap="#5E7A3A"), seed=21)
ZOMBIE_B = Figure(ZombieStyle("#C9C2AE", "#4A4A52", kind="tee", seed=7, hair="#3B2E26"), seed=22)
ZOMBIE_C = Figure(ZombieStyle("#C7A33B", "#5A5048", kind="tee", seed=11, hair="#8A6A3A"), seed=23)
MAILMAN = Figure(MailmanStyle(), seed=24)


def zombie_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=1.0, t=t, blink=False, eyes="wide", look=(0.2, 0.3), brows="none", mouth="teeth",
             tilt=-8, blink_seed=9)
    d.update(kw)
    return Pose(**d)


def shamble(p, t, speed=0.8, amp=1.0, seed=0):
    """Stiff, lurching zombie walk: one leg drags, arms raised forward, head lolls."""
    ph = t * speed * 2 * math.pi + seed
    s = math.sin(ph)
    c = math.cos(ph)
    lurch = max(0, s) ** 2
    return p.but(hip_a=-20 * s * amp, hip_b=10 * s * amp + 4, knee_a=6 + 30 * max(0, c) * amp, knee_b=4,
                 bob=-abs(c) * 6 * amp + 4 + 6 * lurch, lean=p.lean + 10 + 6 * lurch,
                 arm_a=78 + 8 * math.sin(ph * 0.5 + 1), arm_b=86 + 8 * math.sin(ph * 0.5),
                 elb_a=6 + 10 * lurch, elb_b=-4, tilt=p.tilt + 14 * math.sin(ph * 0.5 + seed) - 4)


def crawl(p, t, speed=3.0):
    """The neighbor's ridiculous all-fours gallop."""
    ph = t * speed * 2 * math.pi
    s = math.sin(ph)
    c = math.cos(ph)
    return p.but(lean=74 + 6 * s, bob=56 - abs(c) * 26, hip_a=46 + 30 * s, hip_b=46 - 30 * s,
                 knee_a=104 + 24 * max(0, c), knee_b=104 + 24 * max(0, -c),
                 arm_a=14 + 40 * c, arm_b=14 - 40 * c, elb_a=-14, elb_b=-14, tilt=-72 - 6 * s,
                 head_dy=10)


def run_scared(p, t, speed=2.6):
    from cinecode.characters import run
    return run(p, t, speed, 1.0, flail=True)


# ------------------------------------------------------------------ rooster
def rooster(cx, x, y, s=1.0, f=1.0, t=0.0, crow=0.0, puff=0.0, peck=0.0, blink=True, look=0.0):
    """The farm's rooster. crow 0..1 = head thrown back + beak open; puff = chest pride."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f, s)
    # legs
    for dx in (-14, 12):
        line(cx, [(dx, -60), (dx + 2, -6)], hexc("#E2A33A"), 7)
        line(cx, [(dx - 14, 0), (dx + 2, -6), (dx + 18, 0)], hexc("#E2A33A"), 6)
    # tail feathers
    sway = math.sin(t * 2.2) * 0.06
    cx.save()
    cx.translate(-48, -110)
    cx.rotate(sway - 0.1 * puff)
    for k, (col, ang, ln) in enumerate([("#2E4A3A", -1.9, 120), ("#1F3B33", -1.6, 140), ("#3D5E3E", -1.25, 125),
                                       ("#2A2A30", -0.95, 100), ("#7A2E22", -2.2, 90)]):
        cx.save()
        cx.rotate(ang + math.pi / 2)
        cx.move_to(0, 0)
        cx.curve_to(-30, -ln * 0.4, -26, -ln * 0.95, 8, -ln)
        cx.curve_to(18, -ln * 0.7, 14, -ln * 0.3, 10, 0)
        cx.close_path()
        fs(cx, hexc(col), OUTLINE, 4)
        cx.restore()
    cx.restore()
    # body
    py = 1 + 0.12 * puff
    ellipse(cx, 0, -92, 64 * py, 50 * py, -0.15)
    fs(cx, hexc("#C8643A"), OUTLINE, 5)
    # wing
    ellipse(cx, -6, -88, 36, 24, -0.3)
    fs(cx, hexc("#9C4A2A"), OUTLINE, 4)
    for k in range(3):
        line(cx, [(-30 + k * 14, -80), (-20 + k * 14, -70)], OUTLINE, 3)
    # neck + head: crow stretches the neck up and throws the head back, beak wide open
    nb = (34, -118)                                   # neck base on the body
    hx = 52 + 6 * crow + 14 * peck
    hy = -178 - 34 * crow + 70 * peck
    cx.move_to(nb[0] - 26, nb[1] + 18)
    cx.curve_to(nb[0] - 30, nb[1] - 20, hx - 30, hy + 30, hx - 18, hy + 4)
    cx.line_to(hx + 22, hy + 10)
    cx.curve_to(hx + 20, hy + 40, nb[0] + 34, nb[1] - 10, nb[0] + 30, nb[1] + 22)
    cx.close_path()
    fs(cx, hexc("#E08A3E"), OUTLINE, 5)
    for k in range(4):                                # hackle feathers
        y0 = hy + 30 + k * 16
        line(cx, [(hx - 22 + k * 2, y0), (hx - 4 + k * 3, y0 + 12)], hexc("#B8642A"), 3)
    cx.save()
    cx.translate(hx, hy)
    cx.rotate(-0.85 * crow + 0.5 * peck)
    # comb (behind the head)
    for k, (dx, r) in enumerate([(-16, 11), (-4, 13), (8, 12), (18, 9)]):
        circle(cx, dx, -26 - (3 if k in (1, 2) else 0), r)
    fs(cx, hexc("#D63A2E"), OUTLINE, 4)
    circle(cx, 0, 0, 26)
    fs(cx, hexc("#F4EFE6"), OUTLINE, 5)
    # beak (opens with crow)
    o = crow
    cx.save()
    cx.translate(22, 2)
    cx.move_to(0, -9)
    cx.line_to(32, -4 - 14 * o)
    cx.line_to(0, 1)
    cx.close_path()
    fs(cx, hexc("#F2B33A"), OUTLINE, 3.5)
    cx.move_to(0, 3)
    cx.line_to(28, 6 + 16 * o)
    cx.line_to(0, 11)
    cx.close_path()
    fs(cx, hexc("#E39A2A"), OUTLINE, 3.5)
    cx.restore()
    # wattle
    ellipse(cx, 14, 26, 8, 13)
    fs(cx, hexc("#D63A2E"), OUTLINE, 3.5)
    # eye: squeezed shut with effort while crowing
    bl = blink and ((t * 0.9) % 2.7) > 2.6
    if bl or crow > 0.6:
        line(cx, [(0, -8), (10, -4), (0, 0)], OUTLINE, 4)
    else:
        circle(cx, 6, -6, 7)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3)
        circle(cx, 7 + 2 * look, -6, 3.5)
        fs(cx, OUTLINE, None, 0)
    # proud brow
    line(cx, [(-4, -18 + 2 * crow), (14, -15)], OUTLINE, 4)
    cx.restore()
    cx.restore()

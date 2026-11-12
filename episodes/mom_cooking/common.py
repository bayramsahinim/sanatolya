"""Shared assets for the vertical Short: Mom, prehistoric animals, props and sets.

All shots are 1080x1920 (CINECODE_SIZE is set by episodes.mom_cooking.episode before cinecode
is imported). World coordinates equal screen coordinates when the camera is at rest.
"""
import math
import random

import cairo

from cinecode import props as P
from cinecode.characters import (HERO, Figure, Pose, Style, breathe, hero_pose, run, talk, walk)
from cinecode.core import (FPS, H, OUTLINE, W, Cam, cam_kf, circle, clamp, curve, ease_in, ease_io,
                           ease_out, back_out, ellipse, fs, hexc, kf, lerp, line, mix, noise1, poly,
                           prog, pulse, rrect, shade, shake, smooth, smooth_poly, src, vgrad, win)
from cinecode.timeline import Shot

FLOOR = 1480          # default ground line (screen y) for full-body shots
BLUE = hexc("#3478F6")
CHAR = hexc("#1F1F24")


# ====================================================================== helpers
def fig(cx, sh, cam, f, pose, who=None):
    J = f.draw(cx, pose)
    if who and cam is not None:
        sh.track(who, J, cam)
    return J


def world(cx, cam):
    cx.save()
    cam.apply(cx)


def end(cx):
    cx.restore()


def tint(cx, c, a):
    if a <= 0:
        return
    cx.save()
    cx.identity_matrix()
    cx.rectangle(0, 0, W, H)
    src(cx, (c[0], c[1], c[2], a))
    cx.fill()
    cx.restore()


def flash(cx, a, c=(1, 1, 1)):
    tint(cx, c, a)


def vignette(cx, a=0.35, c=(0, 0, 0)):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75)
    g.add_color_stop_rgba(0, *c, 0)
    g.add_color_stop_rgba(1, *c, a)
    cx.set_source(g)
    cx.paint()


def pick(t, keys):
    v = keys[0][1]
    for k, val in keys:
        if t >= k:
            v = val
    return v


def sit(p, seat_h=58, legs=1.0):
    """Side-view sitting: thighs forward, shins down. seat_h = hip height above feet (unscaled)."""
    return p.but(hip_a=86 * legs, knee_a=86 * legs, hip_b=80 * legs, knee_b=84 * legs,
                 bob=p.bob + 116 - seat_h)


def thumb(cx, x, y, s=1.0, down=True, rot=0.0):
    """A little thumb on a fist (thumbs-down / thumbs-up)."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s if down else -s)
    rrect(cx, -6, 2, 12, 26, 6)
    fs(cx, OUTLINE, None, 0)
    cx.restore()


def tongue(cx, x, y, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(-9, 0)
    cx.curve_to(-10, 18, 10, 18, 9, 0)
    cx.close_path()
    fs(cx, hexc("#F07A86"), OUTLINE, 3)
    line(cx, [(0, 3), (0, 10)], hexc("#C9505E"), 2)
    cx.restore()


def eye_sparkle(cx, J, p, a=1.0):
    """Star-shaped glints over both eyes (for 'treasure' reactions)."""
    if a <= 0:
        return
    hx, hy = J["head"]
    R = J["head_rad"]
    s = p.s
    f = p.f if p.view == "side" else 0.0
    off = f * R * 0.22
    for side in (-1, 1):
        x = hx + off + side * R * 0.34
        y = hy - R * 0.06
        P.star(cx, x, y, 13 * s * (0.85 + 0.15 * math.sin(p.t * 14 + side)), hexc("#FFC857", a))
        cx.new_path()


def soot(cx, J, a=1.0):
    if a <= 0:
        return
    hx, hy = J["head"]
    R = J["head_rad"]
    for (dx, dy, rx, ry, rot) in ((-0.55, 0.42, 0.2, 0.1, 0.3), (0.58, 0.38, 0.16, 0.08, -0.4),
                                  (0.1, -0.72, 0.22, 0.09, 0.1)):
        ellipse(cx, hx + dx * R, hy + dy * R, R * rx, R * ry, rot)
        src(cx, (0.25, 0.25, 0.28, 0.45 * a))
        cx.fill()


def sweat_fly(cx, x, y, t, a=1.0, s=1.0):
    """Drops flying off a panicking head."""
    for k in range(4):
        ph = (t * 3 + k / 4) % 1
        ang = -math.pi / 2 + (k - 1.5) * 0.7
        d = (30 + ph * 90) * s
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d + ph * ph * 60 * s
        cx.save()
        cx.translate(px, py)
        cx.scale(s, s)
        cx.move_to(0, -12)
        cx.curve_to(8, 0, 8, 7, 0, 7)
        cx.curve_to(-8, 7, -8, 0, 0, -12)
        src(cx, hexc("#8FD3FF"), a * (1 - ph))
        cx.fill_preserve()
        src(cx, OUTLINE, a * (1 - ph))
        cx.set_line_width(2.5)
        cx.stroke()
        cx.restore()


def puff(cx, x, y, r, a=1.0, c=(0.93, 0.9, 0.84), seed=1):
    if a <= 0 or r <= 0:
        return
    rr = random.Random(seed)
    for k in range(7):
        ang = k / 7 * 6.28 + rr.random()
        d = r * 0.55
        circle(cx, x + math.cos(ang) * d, y + math.sin(ang) * d * 0.7, r * (0.4 + 0.2 * rr.random()))
    circle(cx, x, y, r * 0.6)
    src(cx, (*c, a))
    cx.fill()


def smoke_wisps(cx, x, y, t, a=1.0, n=3, s=1.0, dark=0.0):
    c = mix((0.86, 0.86, 0.86, 1), (0.25, 0.25, 0.27, 1), dark)
    for k in range(n):
        ph = (t * 0.9 + k / n) % 1
        px = x + math.sin(t * 3 + k * 2) * 14 * s * ph
        py = y - ph * 160 * s
        circle(cx, px, py, (10 + 26 * ph) * s)
        src(cx, (c[0], c[1], c[2], a * 0.8 * (1 - ph)))
        cx.fill()


def steam(cx, x, y, t, a=1.0, s=1.0, n=3):
    for k in range(n):
        ph = (t * 0.6 + k / n) % 1
        xx = x + (k - (n - 1) / 2) * 26 * s
        cx.move_to(xx, y)
        for j in range(1, 6):
            yy = y - j * 14 * s
            cx.line_to(xx + math.sin(j * 1.3 + t * 5 + k) * 7 * s, yy)
        src(cx, (1, 1, 1, a * 0.8 * math.sin(ph * math.pi)))
        cx.set_line_width(5 * s)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()


def light_rays(cx, x, y, t, a=1.0, r=900, n=14, c=(1.0, 0.92, 0.6)):
    if a <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.rotate(t * 0.25)
    for k in range(n):
        a0 = k * 2 * math.pi / n
        cx.move_to(0, 0)
        cx.arc(0, 0, r, a0, a0 + math.pi / n * 0.9)
        cx.close_path()
    g = cairo.RadialGradient(0, 0, 20, 0, 0, r)
    g.add_color_stop_rgba(0, *c, 0.75 * a)
    g.add_color_stop_rgba(1, *c, 0)
    cx.set_source(g)
    cx.fill()
    cx.restore()


def speed_lines_v(cx, t, a=0.5, c=(1, 1, 1), n=18, seed=3, dirx=1, y0=0, y1=None):
    """Horizontal speed streaks across the whole frame."""
    y1 = H if y1 is None else y1
    r = random.Random(seed)
    for i in range(n):
        y = y0 + r.random() * (y1 - y0)
        L = 160 + 260 * r.random()
        ph = (t * (2.6 + r.random()) + r.random()) % 1
        x = -L + (W + 2 * L) * (ph if dirx > 0 else 1 - ph)
        line(cx, [(x, y), (x - dirx * L, y)], (*c, a * math.sin(ph * math.pi)), 4 + 3 * r.random())


def leg_wheel(cx, x, y, t, s=1.0, a=1.0):
    """Cartoon 'legs spinning into a wheel' blur."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    for k in range(5):
        a0 = -t * 40 + k * 1.25
        cx.new_path()
        cx.arc(0, 0, 52 - k * 3, a0, a0 + 0.9)
        src(cx, (0.11, 0.11, 0.14, a * (0.55 - k * 0.08)))
        cx.set_line_width(7)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.restore()


def dust_trail(cx, x, y, t, s=1.0, dirx=-1, a=1.0, n=6):
    for i in range(n):
        ph = (t * 3.2 + i / n) % 1
        px = x - dirx * ph * 220 * s
        py = y - 8 * s - ph * 50 * s
        circle(cx, px, py, (14 + ph * 34) * s)
        fs(cx, (0.86, 0.76, 0.6, a * 0.85 * (1 - ph)), None, 0)


# ====================================================================== Mom
class MomStyle(Style):
    """Mom: dark-brown bob, coral sweater, navy skirt. Same rig and line weight as the hero."""
    head_r = 48
    torso = 106
    thigh = 56
    shin = 56
    limb_w = 8.5
    lashes = True
    top = hexc("#E2725B")
    top_dk = hexc("#C25A45")
    skirt = hexc("#3E4C6E")
    hair = hexc("#4A2E22")
    shoe = hexc("#3E4C6E")

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        # skirt
        cx.move_to(-32, -14)
        cx.curve_to(-38, 20, -46, 50, -50, 74)
        cx.curve_to(-16, 80, 16, 80, 50, 74)
        cx.curve_to(46, 50, 38, 20, 32, -14)
        cx.close_path()
        fs(cx, self.skirt, OUTLINE, self.outline_w)
        # sweater
        cx.move_to(-33, 2)
        cx.curve_to(-35, -T * 0.4, -34, -T + 14, -26, -T + 4)
        cx.curve_to(-12, -T - 4, 12, -T - 4, 26, -T + 4)
        cx.curve_to(34, -T + 14, 35, -T * 0.4, 33, 2)
        cx.curve_to(12, 8, -12, 8, -33, 2)
        cx.close_path()
        fs(cx, self.top, OUTLINE, self.outline_w)
        # neckline + hem rib
        f = p.f if p.view == "side" else 0
        cx.move_to(-14 + f * 6, -T + 2)
        cx.curve_to(-8 + f * 6, -T + 16, 8 + f * 6, -T + 16, 14 + f * 6, -T + 2)
        fs(cx, None, self.top_dk, 3.5)
        line(cx, [(-30, -6), (30, -6)], self.top_dk, 4)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.75, sy + (ey - sy) * 0.75
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 24)
        line(cx, [(sx, sy), (mx, my)], self.top, 16)

    def draw_head_back(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        f = p.f if p.view == "side" else 0
        # bob: hair mass behind the face down to the jaw
        cx.move_to(-R - 10 - f * 8, R * 0.55)
        cx.curve_to(-R - 16 - f * 8, -R * 1.25, R + 16 - f * 8, -R * 1.25, R + 10 - f * 8, R * 0.55)
        cx.curve_to(R * 0.6, R * 0.75, -R * 0.6, R * 0.75, -R - 10 - f * 8, R * 0.55)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, self.outline_w)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # side-swept fringe
        cx.move_to(-R - 3, -R * 0.05)
        cx.curve_to(-R - 4, -R * 1.25, R + 4, -R * 1.25, R + 3, -R * 0.05)
        cx.curve_to(R * 0.7, -R * 0.42, R * 0.2 + f * 10, -R * 0.62, -R * 0.15 + f * 10, -R * 0.5)
        cx.curve_to(-R * 0.5, -R * 0.4, -R * 0.8, -R * 0.2, -R - 3, -R * 0.05)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, self.outline_w)
        cx.restore()


MOM = Figure(MomStyle(), seed=5)
MOM_SCALE = 1.0


def mom_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=MOM_SCALE, t=t, blink_seed=5, mouth="smile", brows="neutral")
    d.update(kw)
    return Pose(**d)


# ====================================================================== food & props
def casserole_plate(cx, x, y, s=1.0, t=0.0, steam_a=1.0):
    """Mom's (perfectly fine) broccoli casserole."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 92, 24)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    ellipse(cx, 0, -2, 64, 14)
    fs(cx, None, hexc("#E3E6EC"), 3)
    cx.move_to(-56, -2)
    cx.curve_to(-50, -38, 50, -38, 56, -2)
    cx.close_path()
    fs(cx, hexc("#C9B86A"), OUTLINE, 4)
    for k, (bx, by) in enumerate([(-30, -16), (-6, -24), (20, -18), (38, -8), (-42, -6), (6, -10)]):
        circle(cx, bx, by, 9)
        fs(cx, hexc("#6E9E4A"), OUTLINE, 3)
    cx.restore()
    if steam_a > 0:
        steam(cx, x, y - 40 * s, t, steam_a, s * 0.9)


def roast_chicken(cx, x, y, s=1.0, t=0.0, eaten=0.0, glow=0.0):
    """Golden roast chicken on a plate. eaten 0..1 shrinks it."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    if glow > 0:
        g = cairo.RadialGradient(0, -40, 10, 0, -40, 260)
        g.add_color_stop_rgba(0, 1, 0.9, 0.55, 0.65 * glow)
        g.add_color_stop_rgba(1, 1, 0.9, 0.55, 0)
        cx.set_source(g)
        circle(cx, 0, -40, 260)
        cx.fill()
    ellipse(cx, 0, 0, 150, 34)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    ellipse(cx, 0, -3, 112, 22)
    fs(cx, None, hexc("#E3E6EC"), 3)
    # greens
    for gx in (-96, 92):
        for k in range(3):
            ellipse(cx, gx + (k - 1) * 14, -10 - (k % 2) * 6, 14, 9, 0.4 * (k - 1))
            fs(cx, hexc("#5DAA4A"), OUTLINE, 2.5)
    k = 1 - 0.55 * eaten
    cx.save()
    cx.translate(0, -8)
    cx.scale(k, k)
    # legs
    for sx in (-1, 1):
        cx.save()
        cx.scale(sx, 1)
        ellipse(cx, 66, -30, 34, 22, -0.5)
        fs(cx, hexc("#D98B3A"), OUTLINE, 4)
        rrect(cx, 88, -66, 12, 26, 6)
        fs(cx, hexc("#FFF6E4"), OUTLINE, 3)
        circle(cx, 90, -68, 7)
        circle(cx, 99, -66, 7)
        fs(cx, hexc("#FFF6E4"), OUTLINE, 3)
        cx.restore()
    # body
    cx.move_to(-80, -8)
    cx.curve_to(-92, -92, 92, -92, 80, -8)
    cx.curve_to(40, 4, -40, 4, -80, -8)
    cx.close_path()
    fs(cx, hexc("#E39A45"), OUTLINE, 5)
    # shine
    ellipse(cx, -26, -54, 26, 10, -0.3)
    src(cx, (1, 0.93, 0.7, 0.7))
    cx.fill()
    curve(cx, (-40, -24), (-10, -34), (20, -34), (46, -22), hexc("#B9702C"), 3.5)
    cx.restore()
    cx.restore()


def drumstick(cx, x, y, s=1.0, rot=0.0, bite=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -6, 10, 12, 44, 6)
    fs(cx, hexc("#FFF6E4"), OUTLINE, 3.5)
    circle(cx, -6, 56, 8)
    circle(cx, 6, 56, 8)
    fs(cx, hexc("#FFF6E4"), OUTLINE, 3.5)
    ellipse(cx, 0, -14, 30, 36)
    fs(cx, hexc("#D98B3A"), OUTLINE, 4)
    if bite > 0:
        for k in range(3):
            circle(cx, -14 + k * 14, -48 + 4 * (k % 2), 11 * bite)
        src(cx, hexc("#F3E3C7"))
        cx.fill()
    ellipse(cx, -8, -24, 9, 14, -0.2)
    src(cx, (1, 0.93, 0.7, 0.6))
    cx.fill()
    cx.restore()


def potato(cx, x, y, s=1.0, burnt=0.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    c = mix(hexc("#C9995C"), hexc("#26211F"), burnt)
    cx.move_to(-26, 0)
    cx.curve_to(-28, -20, -6, -24, 6, -18)
    cx.curve_to(22, -22, 30, -6, 26, 6)
    cx.curve_to(22, 22, -20, 22, -26, 0)
    cx.close_path()
    fs(cx, c, OUTLINE, 4)
    for px, py in ((-12, -6), (8, 4), (14, -10)):
        circle(cx, px, py, 2.5)
        fs(cx, mix(hexc("#8A6436"), hexc("#111111"), burnt), None, 0)
    if burnt > 0.6:
        for k in range(3):
            line(cx, [(-16 + k * 12, -12 + k * 3), (-10 + k * 12, 8 - k * 2)], hexc("#4A4440", (burnt - 0.6) / 0.4), 2)
    cx.restore()


def club(cx, x, y, s=1.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    cx.move_to(-7, 30)
    cx.curve_to(-10, -40, -26, -90, -20, -120)
    cx.curve_to(-14, -150, 20, -150, 22, -118)
    cx.curve_to(26, -88, 8, -40, 7, 30)
    cx.close_path()
    fs(cx, hexc("#9B6A3F"), OUTLINE, 4)
    for k in range(3):
        circle(cx, -6 + k * 7, -110 + k * 18, 3)
        fs(cx, hexc("#6E4526"), None, 0)
    cx.restore()


def stick(cx, x0, y0, x1, y1, w=10):
    line(cx, [(x0, y0), (x1, y1)], OUTLINE, w + 6)
    line(cx, [(x0, y0), (x1, y1)], hexc("#9B6A3F"), w)


def campfire(cx, x, y, s=1.0, t=0.0, fire=1.0, smoke=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # stones
    for k in range(7):
        ang = math.pi * (k / 6)
        ellipse(cx, math.cos(ang) * 86, 8 - math.sin(ang) * 10 + 4, 22, 14)
        fs(cx, hexc("#A8A29A"), OUTLINE, 3.5)
    # logs
    for a in (-0.35, 0.35):
        cx.save()
        cx.rotate(a)
        rrect(cx, -60, -14, 120, 22, 10)
        fs(cx, hexc("#8B5A33"), OUTLINE, 4)
        cx.restore()
    if fire > 0:
        k = fire
        for layer, (c, sc) in enumerate([("#FF8A2A", 1.0), ("#FFC23D", 0.68), ("#FFF1A8", 0.38)]):
            fl = 1 + 0.08 * math.sin(t * 22 + layer)
            cx.save()
            cx.scale(sc * k, sc * k * fl)
            cx.move_to(-46, -4)
            cx.curve_to(-60, -60, -20, -80, -14, -130)
            cx.curve_to(0, -96, 8, -110, 14, -150)
            cx.curve_to(30, -110, 62, -70, 46, -4)
            cx.close_path()
            fs(cx, hexc(c), OUTLINE if layer == 0 else None, 4 if layer == 0 else 0)
            cx.restore()
    cx.restore()
    if smoke > 0:
        smoke_wisps(cx, x, y - 120 * s, t, smoke, 3, s)


def fork(cx, x, y, s=1.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -5, -10, 10, 70, 5)
    fs(cx, hexc("#C9CED6"), OUTLINE, 3)
    rrect(cx, -14, -16, 28, 8, 3)
    fs(cx, hexc("#C9CED6"), OUTLINE, 2.5)
    for k in range(4):
        rrect(cx, -13 + k * 7.4, -50, 4, 38, 2)
        fs(cx, hexc("#C9CED6"), OUTLINE, 2)
    cx.restore()


def knife(cx, x, y, s=1.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    cx.move_to(-5, 60)
    cx.line_to(-5, -56)
    cx.curve_to(12, -50, 14, -20, 6, -6)
    cx.line_to(6, 60)
    cx.close_path()
    fs(cx, hexc("#C9CED6"), OUTLINE, 3)
    cx.restore()


def fork_knife(cx, x, y, s=1.0, a=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # fork
    rrect(cx, -40, -10, 10, 70, 5)
    fs(cx, hexc("#C9CED6", a), OUTLINE, 3)
    for k in range(4):
        rrect(cx, -48 + k * 6.5, -46, 4, 40, 2)
        fs(cx, hexc("#C9CED6", a), OUTLINE, 2)
    rrect(cx, -48, -14, 26, 8, 3)
    fs(cx, hexc("#C9CED6", a), OUTLINE, 2.5)
    # knife
    cx.move_to(30, 60)
    cx.line_to(30, -46)
    cx.curve_to(46, -40, 48, -10, 40, 4)
    cx.line_to(40, 60)
    cx.close_path()
    fs(cx, hexc("#C9CED6", a), OUTLINE, 3)
    cx.restore()


def thought(cx, x, y, w, h, a, tail_to=None, draw_fn=None):
    if a <= 0:
        return
    cx.save()
    cx.push_group()
    for k in range(9):
        ang = k / 9 * 6.28
        ellipse(cx, x + math.cos(ang) * w * 0.36, y + math.sin(ang) * h * 0.32, w * 0.26, h * 0.3)
    ellipse(cx, x, y, w * 0.42, h * 0.38)
    fs(cx, (1, 1, 1, 1), OUTLINE, 5)
    for k in range(9):
        ang = k / 9 * 6.28
        ellipse(cx, x + math.cos(ang) * w * 0.36, y + math.sin(ang) * h * 0.32, w * 0.26 - 3, h * 0.3 - 3)
    ellipse(cx, x, y, w * 0.42, h * 0.38)
    src(cx, (1, 1, 1, 1))
    cx.fill()
    if tail_to:
        tx, ty = tail_to
        for k, r in enumerate((18, 12, 8)):
            px = x + (tx - x) * (0.55 + k * 0.16)
            py = y + h * 0.4 + (ty - y - h * 0.4) * (0.2 + k * 0.32)
            circle(cx, px, py, r)
            fs(cx, (1, 1, 1, 1), OUTLINE, 4)
    if draw_fn:
        draw_fn(cx)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def controller(cx, x, y, s=1.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    cx.move_to(-44, -14)
    cx.curve_to(-30, -22, 30, -22, 44, -14)
    cx.curve_to(60, -6, 62, 24, 46, 26)
    cx.curve_to(34, 28, 28, 12, 18, 10)
    cx.line_to(-18, 10)
    cx.curve_to(-28, 12, -34, 28, -46, 26)
    cx.curve_to(-62, 24, -60, -6, -44, -14)
    cx.close_path()
    fs(cx, hexc("#2B2D36"), OUTLINE, 4)
    for dx, c in ((24, "#E05A47"), (34, "#5DAA4A")):
        circle(cx, dx, -4 + (dx - 24) * 0.3, 5)
        fs(cx, hexc(c), None, 0)
    rrect(cx, -36, -8, 16, 5, 2)
    rrect(cx, -30.5, -13.5, 5, 16, 2)
    fs(cx, hexc("#9AA0AE"), None, 0)
    cx.restore()


# ====================================================================== mammoth
def mammoth(cx, x, y, s=1.0, f=-1, t=0.0, run_t=None, eye="calm", trunk_up=0.0, look=0.0,
            head_dip=0.0, chew=0.0, steam_a=0.0, dodo_rider=0.0):
    """Woolly mammoth standing on (x,y). f=-1 faces left. run_t animates a gallop."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f * -1, s)       # drawn facing left (-x) in local space
    fur = hexc("#9A6440")
    fur_dk = hexc("#7A4A2E")
    fur_lt = hexc("#B07A52")
    bob = 0.0
    legs = [0, 0, 0, 0]
    if run_t is not None:
        ph = run_t * 2 * math.pi * 2.6
        bob = -abs(math.sin(ph)) * 22
        legs = [math.sin(ph) * 22, math.sin(ph + 1.6) * 22, math.sin(ph + 3.1) * 22, math.sin(ph + 4.7) * 22]
    cx.translate(0, bob)
    # far legs (darker)
    for i, lx in enumerate((-120, 150)):
        cx.save()
        cx.translate(lx + 30, -150)
        cx.rotate(legs[i + 2] * 0.017)
        rrect(cx, -38, 0, 76, 150 - bob, 30)
        fs(cx, fur_dk, OUTLINE, 5)
        cx.restore()
    # tail
    curve(cx, (250, -260), (290, -240), (300, -200), (296, -170), OUTLINE, 6)
    ellipse(cx, 296, -164, 10, 16)
    fs(cx, fur_dk, OUTLINE, 3)
    # body
    cx.move_to(-150, -150)
    cx.curve_to(-200, -260, -170, -420, -40, -440)
    cx.curve_to(80, -456, 230, -400, 270, -300)
    cx.curve_to(300, -220, 280, -150, 240, -130)
    cx.curve_to(120, -110, -40, -110, -150, -150)
    cx.close_path()
    fs(cx, fur, OUTLINE, 6)
    # shaggy fringe
    cx.save()
    for k in range(13):
        fx = -140 + k * 30
        cx.move_to(fx - 14, -138)
        cx.line_to(fx, -104 + (k % 2) * 8)
        cx.line_to(fx + 14, -136)
    fs(cx, fur_dk, OUTLINE, 3.5)
    cx.restore()
    for k in range(8):
        a0 = -80 + k * 40
        curve(cx, (a0, -380 + (k % 3) * 30), (a0 + 12, -350), (a0 + 4, -320), (a0 + 18, -300 + (k % 2) * 20),
              fur_dk, 4)
    ellipse(cx, -10, -390, 70, 20, -0.12)
    src(cx, (*fur_lt[:3], 0.55))
    cx.fill()
    # near legs
    for i, lx in enumerate((-110, 170)):
        cx.save()
        cx.translate(lx, -150)
        cx.rotate(legs[i] * 0.017)
        rrect(cx, -42, -20, 84, 170 - bob, 32)
        fs(cx, fur, OUTLINE, 5)
        for k in range(3):
            ellipse(cx, -24 + k * 24, 146 - bob, 10, 6)
            fs(cx, hexc("#E9DCC4"), OUTLINE, 2.5)
        cx.restore()
    # head
    cx.save()
    cx.translate(-170, -330 + head_dip)
    cx.rotate(-0.1 * trunk_up + look * 0.05)
    # ear
    ellipse(cx, 70, 10, 46, 62, 0.3)
    fs(cx, fur_dk, OUTLINE, 5)
    # skull with dome
    cx.move_to(-90, 40)
    cx.curve_to(-120, -60, -60, -150, 10, -140)
    cx.curve_to(80, -130, 110, -40, 90, 50)
    cx.curve_to(40, 90, -60, 90, -90, 40)
    cx.close_path()
    fs(cx, fur, OUTLINE, 6)
    for k in range(4):
        curve(cx, (-40 + k * 26, -128), (-30 + k * 26, -150), (-20 + k * 26, -150), (-14 + k * 26, -132), fur_dk, 4)
    # trunk
    tu = trunk_up
    c0 = (-70, 40)
    c1 = lerpv((-110, 120), (-150, -10), tu)
    c2 = lerpv((-90, 230), (-230, -80), tu)
    c3 = lerpv((-60, 270), (-230, -170), tu)
    for w, c in ((52, OUTLINE), (40, fur)):
        cx.move_to(*c0)
        cx.curve_to(*c1, *c2, *c3)
        src(cx, c)
        cx.set_line_width(w)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    for k in range(5):
        tt = 0.2 + k * 0.15
        px = (1 - tt) ** 3 * c0[0] + 3 * (1 - tt) ** 2 * tt * c1[0] + 3 * (1 - tt) * tt ** 2 * c2[0] + tt ** 3 * c3[0]
        py = (1 - tt) ** 3 * c0[1] + 3 * (1 - tt) ** 2 * tt * c1[1] + 3 * (1 - tt) * tt ** 2 * c2[1] + tt ** 3 * c3[1]
        line(cx, [(px - 14, py - 4), (px + 14, py + 4)], fur_dk, 3)
    # mouth
    if chew > 0:
        ellipse(cx, -40, 64, 14, 6 + 6 * chew)
        fs(cx, hexc("#3A1F22"), OUTLINE, 3)
    # tusks
    for k, (dx, w) in enumerate(((-30, 1.0), (-6, 0.85))):
        cx.save()
        cx.translate(dx, 0)
        cx.scale(w, w)
        cx.move_to(-40, 50)
        cx.curve_to(-120, 120, -200, 80, -210, 0)
        cx.curve_to(-190, 50, -120, 80, -60, 30)
        cx.close_path()
        fs(cx, hexc("#F4EBD9"), OUTLINE, 4.5)
        cx.restore()
    # eye
    ex, ey = -46, -26
    if eye == "calm":
        curve(cx, (ex - 14, ey), (ex - 6, ey + 7), (ex + 6, ey + 7), (ex + 14, ey), OUTLINE, 4.5)
    else:
        rr = 15 if eye == "wide" else 13
        ellipse(cx, ex, ey, rr, rr * 1.15)
        fs(cx, (1, 1, 1, 1), OUTLINE, 4)
        circle(cx, ex - 4, ey + 2, 6.5)
        fs(cx, OUTLINE, None, 0)
        if eye == "angry":
            cx.save()
            ellipse(cx, ex, ey, rr + 1, rr * 1.15 + 1)
            cx.clip()
            poly(cx, [(ex - 20, ey - 26), (ex + 20, ey - 26), (ex + 20, ey - 2), (ex - 20, ey - 14)])
            src(cx, fur)
            cx.fill()
            cx.restore()
            line(cx, [(ex - 22, ey - 18), (ex + 20, ey - 4)], OUTLINE, 7)
    cx.restore()
    # dodo hitching a ride on the head
    if dodo_rider > 0:
        dodo(cx, -170 + 10, -480 + head_dip, 0.8, f=1, t=t, mood="smug", alpha=dodo_rider)
    cx.restore()
    if steam_a > 0:
        # angry steam from the head
        hx = x + (170 * s if f > 0 else -170 * s)
        for k in range(2):
            ph = (t * 2.2 + k * 0.5) % 1
            puff(cx, hx + (k * 60 - 30) * s, y - (500 + ph * 120) * s, (20 + ph * 26) * s, steam_a * (1 - ph),
                 (1, 1, 1), seed=k)


def lerpv(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ====================================================================== dodo-ish prehistoric bird
def dodo(cx, x, y, s=1.0, f=1, t=0.0, run_t=None, mood="calm", alpha=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f, s)
    if alpha < 1:
        cx.push_group()
    body = hexc("#8E9AA8")
    ph = 0 if run_t is None else run_t * 2 * math.pi * 4
    bob = 0 if run_t is None else -abs(math.sin(ph)) * 10
    # legs
    for k in (0, 1):
        sw = math.sin(ph + k * math.pi) * (24 if run_t is not None else 0)
        line(cx, [(-6 + k * 14, -40 + bob), (-6 + k * 14 + sw, 0)], hexc("#E8A23B"), 7)
        line(cx, [(-6 + k * 14 + sw - 8, 0), (-6 + k * 14 + sw + 12, 0)], hexc("#E8A23B"), 6)
    cx.translate(0, bob)
    # body
    ellipse(cx, 0, -84, 58, 50)
    fs(cx, body, OUTLINE, 5)
    # tail tuft
    for k in range(3):
        ellipse(cx, -58, -110 + k * 12, 16, 8, -0.5 + k * 0.3)
        fs(cx, hexc("#F2F2F2"), OUTLINE, 3)
    # wing
    ellipse(cx, -6, -84, 28, 20, 0.3 + (0.4 * math.sin(ph * 1.5) if run_t is not None else 0))
    fs(cx, shade(body, -0.2), OUTLINE, 4)
    # neck + head
    ellipse(cx, 40, -142, 30, 34)
    fs(cx, body, OUTLINE, 5)
    # beak
    cx.move_to(58, -152)
    cx.curve_to(100, -156, 112, -132, 96, -118)
    cx.curve_to(86, -126, 70, -128, 58, -128)
    cx.close_path()
    fs(cx, hexc("#E8C25A"), OUTLINE, 4)
    # eye
    if mood == "smug":
        ellipse(cx, 44, -150, 8, 9)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3)
        circle(cx, 46, -148, 4)
        fs(cx, OUTLINE, None, 0)
        line(cx, [(34, -160), (54, -158)], OUTLINE, 4)
    else:
        ellipse(cx, 44, -150, 8, 10 if mood != "scared" else 12)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3)
        circle(cx, 47, -150, 4)
        fs(cx, OUTLINE, None, 0)
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


# ====================================================================== stone tablet / rock microwave / fridge
def stone_tablet(cx, x, y, s=1.0, rot=0.0, t=0.0, crack=0.0, load=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    pts = [(-150, -270), (140, -280), (156, 260), (-146, 272)]
    smooth_poly(cx, pts, True, 0.25)
    fs(cx, hexc("#A9A49B"), OUTLINE, 7)
    smooth_poly(cx, [(-120, -240), (112, -248), (124, 230), (-116, 240)], True, 0.25)
    fs(cx, hexc("#C2BDB2"), None, 0)
    # carved app grid: burger, pizza, bowl, chicken leg
    ink = hexc("#6F6A61")
    for i, (gx, gy) in enumerate(((-58, -150), (58, -150), (-58, -30), (58, -30))):
        rrect(cx, gx - 44, gy - 44, 88, 88, 22)
        fs(cx, None, ink, 5)
        if i == 0:   # burger
            cx.move_to(gx - 26, gy - 2)
            cx.curve_to(gx - 26, gy - 30, gx + 26, gy - 30, gx + 26, gy - 2)
            cx.close_path()
            fs(cx, None, ink, 4)
            line(cx, [(gx - 28, gy + 8), (gx + 28, gy + 8)], ink, 4)
            rrect(cx, gx - 26, gy + 16, 52, 10, 5)
            fs(cx, None, ink, 4)
        elif i == 1:   # pizza
            poly(cx, [(gx - 26, gy - 22), (gx + 26, gy - 22), (gx, gy + 28)])
            fs(cx, None, ink, 4)
            circle(cx, gx - 6, gy - 8, 4)
            circle(cx, gx + 8, gy - 6, 4)
            fs(cx, ink, None, 0)
        elif i == 2:   # noodles
            cx.move_to(gx - 28, gy - 4)
            cx.curve_to(gx - 24, gy + 26, gx + 24, gy + 26, gx + 28, gy - 4)
            cx.close_path()
            fs(cx, None, ink, 4)
            line(cx, [(gx + 6, gy - 30), (gx - 8, gy - 4)], ink, 4)
            line(cx, [(gx + 18, gy - 26), (gx + 2, gy - 4)], ink, 4)
        else:   # drumstick
            ellipse(cx, gx - 6, gy - 6, 18, 22, 0.7)
            fs(cx, None, ink, 4)
            line(cx, [(gx + 8, gy + 8), (gx + 24, gy + 24)], ink, 5)
    # "loading" pebbles
    if load > 0:
        for k in range(8):
            a = k / 8 * 6.28 + t * 6
            circle(cx, math.cos(a) * 40, 130 + math.sin(a) * 40, 8)
            src(cx, (*ink[:3], 0.25 + 0.75 * ((k / 8 + t * 2) % 1) * load))
            cx.fill()
    # crack
    if crack > 0:
        pts = [(-150, 40), (-90, 20), (-40, 70), (10, 30), (60, 80), (110, 50), (156, 70)]
        n = max(2, int(len(pts) * crack + 0.999))
        line(cx, pts[:n], OUTLINE, 7)
    cx.restore()


def rock_microwave(cx, x, y, s=1.0, t=0.0, press=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    smooth_poly(cx, [(-180, 0), (-196, -120), (-130, -230), (20, -250), (150, -220), (196, -110), (184, 0)],
                True, 0.55)
    fs(cx, hexc("#9E978C"), OUTLINE, 6)
    ellipse(cx, -60, -200, 60, 18, -0.2)
    src(cx, (1, 1, 1, 0.18))
    cx.fill()
    # moss + cracks
    smooth_poly(cx, [(-120, -228), (-40, -248), (30, -246), (0, -232), (-80, -222)], True, 0.5)
    fs(cx, hexc("#7FA34A"), OUTLINE, 3)
    line(cx, [(150, -60), (120, -40), (130, -10)], OUTLINE, 3)
    # crudely scratched "door"
    smooth_poly(cx, [(-130, -170), (60, -176), (64, -40), (-126, -36)], True, 0.2)
    fs(cx, hexc("#8A8378"), OUTLINE, 4)
    # pebble buttons
    for k in range(3):
        circle(cx, 120, -150 + k * 42 + (4 * press if k == 0 else 0), 13)
        fs(cx, hexc("#D8D2C6"), OUTLINE, 3.5)
    cx.restore()


def fridge_outline(cx, x, y, s=1.0, door=0.0, a=1.0, t=0.0):
    """Imaginary fridge: dashed chalk outline; door swings open (door 0..1)."""
    if a <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.push_group()
    w, h = 300, 560
    rrect(cx, -w / 2, -h, w, h, 24)
    src(cx, (1, 1, 1, 0.22))
    cx.fill()
    if door > 0.05:
        # empty interior (light on)
        rrect(cx, -w / 2 + 14, -h + 14, w - 28, h - 28, 16)
        src(cx, (0.97, 0.99, 1.0, 0.75 * door))
        cx.fill()
        for k in range(3):
            line(cx, [(-w / 2 + 20, -h + 150 + k * 130), (w / 2 - 20, -h + 150 + k * 130)], (0.5, 0.6, 0.7, 0.6 * door), 4)
    cx.set_dash([18, 12])
    rrect(cx, -w / 2, -h, w, h, 24)
    src(cx, (1, 1, 1, 1))
    cx.set_line_width(7)
    cx.stroke()
    # door panel swinging toward the viewer (left hinge)
    dw = w * (1 - 1.6 * door) if door < 0.6 else -w * 0.6 * (door - 0.6) / 0.4 * 0.4 - 0.04 * w
    cx.move_to(-w / 2, -h)
    cx.line_to(-w / 2 + dw, -h - 30 * door)
    cx.line_to(-w / 2 + dw, 30 * door)
    cx.line_to(-w / 2, 0)
    cx.close_path()
    src(cx, (1, 1, 1, 0.18))
    cx.fill_preserve()
    src(cx, (1, 1, 1, 1))
    cx.stroke()
    hx = -w / 2 + dw * 0.86
    cx.set_dash([])
    line(cx, [(hx, -h * 0.62), (hx, -h * 0.42)], (1, 1, 1, 1), 9)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def tumbleweed(cx, x, y, r, rot, a=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    rr = random.Random(9)
    for k in range(14):
        a0 = rr.random() * 6.28
        cx.new_path()
        cx.arc(rr.random() * r * 0.3 - r * 0.15, rr.random() * r * 0.3 - r * 0.15, r * (0.5 + 0.5 * rr.random()),
               a0, a0 + 2.2)
        src(cx, (0.62, 0.48, 0.3, a))
        cx.set_line_width(4)
        cx.stroke()
    cx.restore()


def cricket(cx, x, y, s=1.0, t=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 22, 9)
    fs(cx, hexc("#5E7D3A"), OUTLINE, 3)
    line(cx, [(-8, 4), (-22, -16), (-34, 8)], OUTLINE, 3)
    line(cx, [(16, -4), (34, -30 + 6 * math.sin(t * 30))], OUTLINE, 2)
    line(cx, [(16, -4), (40, -22 + 6 * math.sin(t * 30 + 1))], OUTLINE, 2)
    cx.restore()


# ====================================================================== vortex
def vortex(cx, x, y, r, t, a=1.0, warm=True):
    """Violent time-vortex: spiral arms + orbiting Stone-Age debris."""
    if r <= 2 or a <= 0:
        return
    cx.save()
    g = cairo.RadialGradient(x, y, 0, x, y, r * 1.25)
    if warm:
        stops = [(0, (1, 0.98, 0.85, 0.98)), (0.3, (1.0, 0.68, 0.28, 0.9)), (0.7, (0.55, 0.3, 0.55, 0.7)),
                 (1, (0.35, 0.2, 0.45, 0))]
    else:
        stops = [(0, (1, 1, 1, 0.98)), (0.3, (0.55, 0.85, 1, 0.9)), (0.7, (0.3, 0.45, 0.95, 0.7)),
                 (1, (0.2, 0.3, 0.8, 0))]
    for o, c in stops:
        g.add_color_stop_rgba(o, c[0], c[1], c[2], c[3] * a)
    cx.set_source(g)
    circle(cx, x, y, r * 1.25)
    cx.fill()
    for arm in range(5):
        cx.new_path()
        base = arm * 2 * math.pi / 5 + t * 7
        for k in range(40):
            u = k / 39
            ang = base + u * 3.6
            rr = r * (0.06 + 0.98 * u)
            px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
            if k == 0:
                cx.move_to(px, py)
            else:
                cx.line_to(px, py)
        src(cx, (1, 1, 1, 0.7 * a))
        cx.set_line_width(7)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    # debris
    rr = random.Random(7)
    for k in range(9):
        ang = rr.random() * 6.28 + t * (4 + rr.random() * 3)
        d = r * (0.45 + 0.5 * rr.random())
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d
        kind = k % 3
        cx.save()
        cx.translate(px, py)
        cx.rotate(ang * 2)
        if kind == 0:
            smooth_poly(cx, [(-16, -10), (14, -14), (18, 10), (-12, 14)], True, 0.4)
            fs(cx, hexc("#A9A49B", a), hexc("#1C1C24", a), 3)
        elif kind == 1:
            ellipse(cx, 0, 0, 22, 9)
            fs(cx, hexc("#5DAA4A", a), hexc("#1C1C24", a), 3)
        else:
            rrect(cx, -18, -4, 36, 8, 4)
            fs(cx, hexc("#F4EBD9", a), hexc("#1C1C24", a), 3)
            circle(cx, -18, 0, 7)
            circle(cx, 18, 0, 7)
            fs(cx, hexc("#F4EBD9", a), hexc("#1C1C24", a), 3)
        cx.restore()
    cx.restore()


# ====================================================================== sets
def _bg(cx, top, bottom):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *hexc(top))
    g.add_color_stop_rgba(1, *hexc(bottom))
    cx.set_source(g)
    cx.paint()


def bedroom(cx, cam, t, tv=1.0, crack=0.0, glow=0.0):
    """Hero's room (vertical). Door on the left, TV on the right, beanbag centre."""
    _bg(cx, "#F7F4EE", "#F7F4EE")
    cx.save()
    cam.apply(cx)
    # wall + floor
    cx.rectangle(-600, -400, W + 1200, FLOOR + 400)
    src(cx, hexc("#F4EFE6"))
    cx.fill()
    cx.rectangle(-600, FLOOR - 26, W + 1200, 26)
    src(cx, hexc("#E4DACB"))
    cx.fill()
    cx.rectangle(-600, FLOOR, W + 1200, H)
    src(cx, hexc("#E9DFCF"))
    cx.fill()
    for k in range(9):
        line(cx, [(-400 + k * 220, FLOOR), (-700 + k * 300, H + 40)], hexc("#DCCFBC"), 4)
    line(cx, [(-600, FLOOR), (W + 600, FLOOR)], OUTLINE, 5)
    # door frame (left)
    dx, dy, dw, dh = 40, 880, 330, 600
    rrect(cx, dx - 18, dy - 18, dw + 36, dh + 18, 8)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    cx.rectangle(dx, dy, dw, dh)
    src(cx, hexc("#E8DCC6"))
    cx.fill()
    # hallway beyond the door (lighter)
    cx.rectangle(dx, dy, dw, dh)
    fs(cx, None, OUTLINE, 4)
    # poster
    rrect(cx, 520, 760, 190, 240, 8)
    fs(cx, BLUE, OUTLINE, 5)
    circle(cx, 615, 850, 46)
    fs(cx, hexc("#FFC857"), OUTLINE, 4)
    poly(cx, [(555, 975), (615, 905), (675, 975)])
    fs(cx, hexc("#2257B5"), OUTLINE, 4)
    # shelf
    rrect(cx, 760, 960, 260, 16, 4)
    fs(cx, hexc("#B07A45"), OUTLINE, 4)
    for k in range(4):
        rrect(cx, 780 + k * 28, 900 + (k % 2) * 8, 24, 60 - (k % 2) * 8, 3)
        fs(cx, hexc(["#E05A47", "#3478F6", "#FFC857", "#5DAA4A"][k]), OUTLINE, 3)
    rrect(cx, 920, 910, 46, 50, 6)
    fs(cx, hexc("#D96A4A"), OUTLINE, 4)
    for a in (-0.6, 0, 0.6):
        ellipse(cx, 943 + a * 30, 890, 12, 26, a)
        fs(cx, hexc("#5DAA4A"), OUTLINE, 3)
    # TV on a low stand (right), screen facing left toward the hero
    rrect(cx, 820, 1330, 300, 150, 10)
    fs(cx, hexc("#B07A45"), OUTLINE, 5)
    line(cx, [(840, 1405), (1100, 1405)], hexc("#8E5E33"), 4)
    rrect(cx, 930, 1300, 40, 34, 6)
    fs(cx, hexc("#2B2D36"), OUTLINE, 4)
    poly(cx, [(800, 1060), (1060, 1010), (1060, 1320), (800, 1300)])
    fs(cx, hexc("#2B2D36"), OUTLINE, 6)
    if tv > 0:
        flick = 0.85 + 0.15 * math.sin(t * 17) * math.sin(t * 5.3)
        poly(cx, [(816, 1074), (1046, 1030), (1046, 1302), (816, 1286)])
        src(cx, (0.42, 0.68, 1.0, tv * flick))
        cx.fill()
        # the game: ground strip, a jumping blocky hero, a coin
        poly(cx, [(816, 1250), (1046, 1244), (1046, 1302), (816, 1286)])
        src(cx, hexc("#5DAA4A"))
        cx.fill()
        jy = -abs(math.sin(t * 6)) * 60
        rrect(cx, 880, 1200 + jy, 34, 44, 4)
        fs(cx, hexc("#E05A47"), None, 0)
        circle(cx, 980 - (t * 90) % 140, 1160, 13)
        fs(cx, hexc("#FFC857"), None, 0)
        # glow spill on the floor + wall
        g = cairo.RadialGradient(900, 1200, 20, 900, 1200, 640)
        g.add_color_stop_rgba(0, 0.45, 0.7, 1.0, 0.28 * tv * flick)
        g.add_color_stop_rgba(1, 0.45, 0.7, 1.0, 0)
        cx.set_source(g)
        circle(cx, 900, 1200, 640)
        cx.fill()
    # floor crack (orange glow) for the time-quake
    if crack > 0:
        pts = [(-40, FLOOR + 90), (140, FLOOR + 50), (260, FLOOR + 130), (420, FLOOR + 40),
               (560, FLOOR + 140), (720, FLOOR + 60), (900, FLOOR + 150), (1120, FLOOR + 80)]
        n = max(2, int(len(pts) * crack + 0.999))
        line(cx, pts[:n], hexc("#FF9A3D", 0.6), 34 * crack)
        line(cx, pts[:n], hexc("#FFE9A8"), 10)
        line(cx, pts[:n], OUTLINE, 4)
    cx.restore()
    if glow > 0:
        tint(cx, (1.0, 0.6, 0.25), glow * 0.25)


def beanbag(cx, x, y, s=1.0, squash=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s * (1 + 0.06 * squash), s * (1 - 0.08 * squash))
    cx.move_to(-130, 0)
    cx.curve_to(-170, -60, -150, -170, -60, -180)
    cx.curve_to(10, -190, 120, -160, 140, -70)
    cx.curve_to(150, -20, 120, 6, 60, 8)
    cx.line_to(-80, 8)
    cx.curve_to(-110, 8, -126, 6, -130, 0)
    cx.close_path()
    fs(cx, hexc("#E8A23B"), OUTLINE, 5)
    curve(cx, (-80, -150), (-40, -110), (-30, -60), (-50, -10), hexc("#C9832A"), 4)
    cx.restore()


def stoneage(cx, cam, t, par_x=0.0, quake=0.0, sky_k=0.0):
    """Prehistoric landscape. par_x scrolls the layers (for chases)."""
    _bg(cx, "#FFD9A8", "#FFF2D6")
    # sun
    circle(cx, 820 - par_x * 0.02, 360, 110)
    src(cx, hexc("#FFE8A6"))
    cx.fill()

    def layer(par, fn):
        cx.save()
        cam.apply(cx, par)
        cx.translate(-par_x * par, 0)
        fn()
        cx.restore()

    def volcano():
        for rep in range(-1, 4):
            ox = rep * 2400
            poly(cx, [(ox - 200, 1130), (ox + 330, 640), (ox + 450, 640), (ox + 980, 1130)])
            fs(cx, hexc("#B98A86"), OUTLINE, 5)
            poly(cx, [(ox + 330, 640), (ox + 450, 640), (ox + 470, 700), (ox + 420, 690), (ox + 390, 720),
                      (ox + 350, 690), (ox + 310, 700)])
            fs(cx, hexc("#E0614A"), OUTLINE, 4)
            for k in range(3):
                ph = (t * 0.25 + k / 3) % 1
                circle(cx, ox + 390 + ph * 120, 600 - ph * 330, 40 + ph * 70)
                src(cx, (0.62, 0.58, 0.6, 0.5 * (1 - ph)))
                cx.fill()
            # distant hills
            poly(cx, [(ox + 700, 1130), (ox + 1050, 860), (ox + 1300, 960), (ox + 1600, 820), (ox + 2100, 1130)])
            fs(cx, hexc("#C9A59A"), OUTLINE, 5)

    def mid():
        for rep in range(-2, 8):
            ox = rep * 1100
            smooth_poly(cx, [(ox - 200, 1300), (ox + 150, 1110), (ox + 520, 1160), (ox + 900, 1080),
                             (ox + 1300, 1300)], False, 0.6)
            cx.line_to(ox + 1300, 1500)
            cx.line_to(ox - 200, 1500)
            cx.close_path()
            fs(cx, hexc("#A9BC6E"), OUTLINE, 5)
            # tree ferns
            for fx in (ox + 260, ox + 780):
                line(cx, [(fx, 1220), (fx + 10, 1010)], OUTLINE, 18)
                line(cx, [(fx, 1220), (fx + 10, 1010)], hexc("#8B5A33"), 11)
                for k in range(6):
                    a = -math.pi + k * math.pi / 5
                    x2, y2 = fx + 10 + math.cos(a) * 120, 1010 + math.sin(a) * 60 + 30
                    curve(cx, (fx + 10, 1010), (fx + 10 + math.cos(a) * 60, 990), (x2, y2 - 30), (x2, y2),
                          hexc("#4F8A3C"), 16)

    def ground():
        cx.rectangle(-4000, FLOOR - 60, 30000, H + 200)
        src(cx, hexc("#E2C48F"))
        cx.fill()
        line(cx, [(-4000, FLOOR - 60), (30000, FLOOR - 60)], OUTLINE, 5)
        rr = random.Random(3)
        for k in range(160):
            gx = -4000 + k * 190 + rr.random() * 80
            gy = FLOOR - 20 + rr.random() * 420
            ellipse(cx, gx, gy, 18 + rr.random() * 30, 8 + rr.random() * 10)
            src(cx, hexc("#CFAE78"))
            cx.fill()
        for k in range(40):
            gx = -4000 + k * 780 + rr.random() * 300
            smooth_poly(cx, [(gx - 40, FLOOR - 50), (gx - 30, FLOOR - 90), (gx + 20, FLOOR - 96),
                             (gx + 46, FLOOR - 50)], True, 0.5)
            fs(cx, hexc("#B8B1A5"), OUTLINE, 4)
            # grass tufts
            tx = gx + 360
            for j in range(4):
                line(cx, [(tx + j * 9, FLOOR - 56), (tx + j * 9 + (j - 1.5) * 6, FLOOR - 86)], hexc("#7FA34A"), 5)

    layer(0.25, volcano)
    layer(0.55, mid)
    layer(1.0, ground)
    if sky_k > 0:
        tint(cx, (1, 0.6, 0.3), sky_k)


def dining(cx, cam, t, warm=1.0):
    """Family dinner: warm wall, pendant lamp, window at dusk, table front edge drawn separately."""
    _bg(cx, "#FBEBD3", "#F6DDBA")
    cx.save()
    cam.apply(cx)
    cx.rectangle(-600, -400, W + 1200, 1500)
    src(cx, hexc("#F7E3C4"))
    cx.fill()
    # wainscot
    cx.rectangle(-600, 1100, W + 1200, 900)
    src(cx, hexc("#E9C9A0"))
    cx.fill()
    line(cx, [(-600, 1100), (W + 600, 1100)], OUTLINE, 5)
    for k in range(10):
        line(cx, [(-100 + k * 140, 1110), (-100 + k * 140, 1900)], hexc("#DDB98C"), 4)
    # window at dusk
    wx, wy, ww, wh = 70, 640, 260, 330
    rrect(cx, wx - 14, wy - 14, ww + 28, wh + 28, 10)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    cx.save()
    cx.rectangle(wx, wy, ww, wh)
    cx.clip()
    cx.set_source(vgrad(cx, 0, wy, 0, wy + wh, [(0, hexc("#5B6FB0")), (1, hexc("#F2A97A"))]))
    cx.paint()
    for i in range(6):
        cx.rectangle(wx + i * 55 - 10, wy + wh - 70 - (i % 3) * 30, 48, 200)
        src(cx, hexc("#3E4C6E"))
        cx.fill()
    cx.restore()
    line(cx, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], hexc("#FFFFFF"), 10)
    line(cx, [(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], hexc("#FFFFFF"), 10)
    # picture frame
    rrect(cx, 700, 700, 260, 190, 8)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    rrect(cx, 722, 722, 216, 146, 4)
    fs(cx, hexc("#BFD8EE"), None, 0)
    poly(cx, [(722, 868), (790, 790), (840, 830), (890, 775), (938, 868)])
    fs(cx, hexc("#7FB37A"), None, 0)
    # pendant lamp
    line(cx, [(540, -400), (540, 110)], OUTLINE, 5)
    cx.move_to(450, 190)
    cx.curve_to(450, 110, 630, 110, 630, 190)
    cx.close_path()
    fs(cx, hexc("#2F6FDB"), OUTLINE, 5)
    g = cairo.RadialGradient(540, 230, 20, 540, 230, 1100)
    g.add_color_stop_rgba(0, 1, 0.86, 0.55, 0.5 * warm)
    g.add_color_stop_rgba(1, 1, 0.86, 0.55, 0)
    cx.set_source(g)
    circle(cx, 540, 230, 1100)
    cx.fill()
    ellipse(cx, 540, 194, 46, 12)
    fs(cx, hexc("#FFF4C9"), OUTLINE, 3)
    cx.restore()


def dining_table(cx, cam, top=1400):
    cx.save()
    cam.apply(cx)
    # tabletop (front edge + cloth)
    rrect(cx, -80, top, W + 160, 46, 10)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    cx.move_to(-80, top + 40)
    cx.line_to(W + 80, top + 40)
    cx.line_to(W + 80, top + 300)
    for k in range(12, -1, -1):
        x = -80 + (W + 160) * k / 12
        cx.line_to(x + (W + 160) / 24, top + 320)
        cx.line_to(x, top + 300)
    cx.close_path()
    fs(cx, hexc("#FFFFFF"), OUTLINE, 5)
    for k in range(6):
        line(cx, [(-80 + k * 220, top + 40), (-80 + k * 220, top + 300)], hexc("#E6EEF9"), 26)
    cx.rectangle(-80, top + 300, W + 160, 900)
    src(cx, hexc("#B07A45"))
    cx.fill()
    line(cx, [(-80, top + 320), (W + 80, top + 320)], OUTLINE, 5)
    cx.restore()

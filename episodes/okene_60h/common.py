"""Helpers shared by the shots."""
import math
import random

import cairo

from cinecode.core import OUTLINE, Cam, circle, clamp, ease_io, ease_out, ellipse, fs, hexc, kf, line, prog, \
    rrect, shake, smooth, src
from . import look, sets
from .cast import DIVER, DIVER_ST, HARRISON, diver, harrison

UNDER_FOG = (0.02, 0.075, 0.085)
WL = 700                 # air-pocket water line (world y in the cabin)
SNOW = look.Snow(n=240, seed=3)
SNOW_FAR = look.Snow(n=160, seed=9, depth=(0.2, 0.6))


def cam_keys(t, keys, ease=ease_io):
    x, y, z = kf(t, keys, ease)
    return Cam(x, y, z)


def lamp_world(J, p, st=DIVER_ST):
    hx, hy = J["head"]
    R = st.head_r * p.s
    f = 1 if (p.f >= 0 or p.view != "side") else -1
    return hx + f * R * 1.25, hy - R * 0.95 + 17 * p.s


def helmet_lamp(F, cam, J, p, ang, reach=1500, spread=0.36, power=1.9, beam_alpha=0.22, st=DIVER_ST):
    """light + volumetric beam from a diver's helmet lamp. ang in screen radians."""
    lx, ly = cam.to_screen(*lamp_world(J, p, st))
    F.lights.spot(lx, ly, ang, spread=spread, reach=reach * cam.zoom, power=power)
    look.beam(F.ax, lx, ly, ang, length=reach * cam.zoom * 0.9, spread=spread * 0.8, alpha=beam_alpha)
    # light spilling back on the diver's own face/helmet
    hx, hy = cam.to_screen(*J["head"])
    F.lights.point(hx, hy, 150 * p.s * cam.zoom, (0.9, 0.85, 0.7), 0.55)
    return lx, ly


AMB_GAIN = 3.4      # readability: the reference keeps every set clearly lit, even when moody


def underwater(F, amt=0.22, ambient=(0.05, 0.11, 0.12)):
    F.fog = UNDER_FOG
    F.fog_amt = amt * 0.7
    F.lights.ambient[:] = [min(0.6, a * AMB_GAIN) for a in ambient]
    F.exposure = 1.22


def snow(F, t, cam, alpha=0.7):
    dx = (cam.x - 540) * 0.6
    dy = (cam.y - 960) * 0.6
    SNOW_FAR.draw(F.cx, t, alpha=alpha * 0.6, cam_dx=dx * 0.5, cam_dy=dy * 0.5)
    SNOW.draw(F.cx, t, alpha=alpha, cam_dx=dx, cam_dy=dy)


def debris(cx, t, items, seed=1):
    """floating junk: items = [(kind, x, y, s, rot0)]"""
    for i, (kind, x, y, s, r0) in enumerate(items):
        x += math.sin(t * 0.4 + i) * 12
        y += math.sin(t * 0.55 + i * 2) * 10
        rot = r0 + math.sin(t * 0.3 + i) * 0.25
        cx.save()
        cx.translate(x, y)
        cx.rotate(rot)
        cx.scale(s, s)
        if kind == "boot":
            rrect(cx, -30, -60, 44, 80, 12)
            fs(cx, hexc("#3a2a1e"), OUTLINE, 5)
            rrect(cx, -30, 10, 80, 30, 12)
            fs(cx, hexc("#3a2a1e"), OUTLINE, 5)
        elif kind == "bottle":
            rrect(cx, -14, -40, 28, 70, 10)
            fs(cx, (0.55, 0.75, 0.7, 0.8), OUTLINE, 4)
            rrect(cx, -6, -58, 12, 22, 4)
            fs(cx, (0.55, 0.75, 0.7, 0.8), OUTLINE, 4)
        elif kind == "cloth":
            cx.move_to(-60, -20)
            cx.curve_to(-20, -50, 20, 10, 60, -20)
            cx.curve_to(70, 20, 30, 40, 0, 30)
            cx.curve_to(-30, 50, -70, 20, -60, -20)
            fs(cx, hexc("#6d7f8a"), OUTLINE, 4)
        elif kind == "can":
            rrect(cx, -16, -24, 32, 48, 6)
            fs(cx, hexc("#9a2e2a"), OUTLINE, 4)
        elif kind == "plank":
            rrect(cx, -90, -12, 180, 24, 5)
            fs(cx, hexc("#6b5038"), OUTLINE, 4)
        elif kind == "cup":
            rrect(cx, -20, -22, 40, 44, 8)
            fs(cx, hexc("#d9d4c7"), OUTLINE, 4)
        cx.restore()


def swim(p, t, rate=1.4, amp=1.0):
    """slow underwater kick + arm sweep for an upright-rig figure that is rotated to swim."""
    s = math.sin(t * rate * 2 * math.pi)
    return p.but(hip_a=10 + 18 * s * amp, hip_b=10 - 18 * s * amp, knee_a=20 + 10 * s, knee_b=20 - 10 * s,
                 arm_a=70 + 30 * s * amp, arm_b=60 - 30 * s * amp, elb_a=30, elb_b=30)


def draw_rotated(cx, fig, p, angle, pivot=None):
    """draw a rig figure rotated around its hip (for swimming poses). Returns world joints."""
    st = fig.st
    hip_h = (st.thigh + st.shin) * p.s
    px, py = pivot or (p.x, p.y - hip_h)
    cx.save()
    cx.translate(px, py)
    cx.rotate(angle)
    cx.translate(-px, -py)
    J = fig.draw(cx, p)
    cx.restore()
    ca, sa = math.cos(angle), math.sin(angle)
    out = {}
    for k, v in J.items():
        if isinstance(v, tuple):
            dx, dy = v[0] - px, v[1] - py
            out[k] = (px + dx * ca - dy * sa, py + dx * sa + dy * ca)
        else:
            out[k] = v
    return out


def splash(cx, x, y, t, t0, s=1.0, alpha=1.0, seed=3):
    age = t - t0
    if age < 0 or age > 1.2:
        return
    rng = random.Random(seed)
    for i in range(22):
        a = -math.pi / 2 + rng.uniform(-1.2, 1.2)
        sp = rng.uniform(250, 700) * s
        px = x + math.cos(a) * sp * age
        py = y + math.sin(a) * sp * age + 900 * age * age * s
        r = rng.uniform(5, 14) * s * (1 - age / 1.2)
        src(cx, (0.85, 0.95, 1.0, alpha * (1 - age / 1.2)))
        cx.arc(px, py, max(0.5, r), 0, 6.283)
        cx.fill()
    # ring
    ellipse(cx, x, y, 60 * s + age * 260 * s, 10 * s + age * 30 * s)
    cx.set_source_rgba(0.85, 0.97, 1, alpha * (1 - age / 1.2) * 0.8)
    cx.set_line_width(4)
    cx.stroke()


def o2(cx, x, y, r=26, alpha=1.0, kind="o2"):
    """labelled molecule bubble: kind 'o2' (blue) or 'co2' (grey-red)."""
    from cinecode.core import text
    if kind == "o2":
        body, ink = (0.35, 0.7, 1.0, 0.85 * alpha), (1, 1, 1, alpha)
        label = "O"
    else:
        body, ink = (0.55, 0.42, 0.42, 0.85 * alpha), (1, 0.92, 0.9, alpha)
        label = "CO"
    circle(cx, x, y, r)
    src(cx, body)
    cx.fill_preserve()
    src(cx, (0.05, 0.08, 0.1, alpha))
    cx.set_line_width(3)
    cx.stroke()
    fsz = r * (0.9 if kind == "o2" else 0.7)
    text(cx, label, x - r * 0.12, y + fsz * 0.36, fsz, ink)
    text(cx, "2", x + r * (0.38 if kind == "o2" else 0.52), y + fsz * 0.62, fsz * 0.55, ink)

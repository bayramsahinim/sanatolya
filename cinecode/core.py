"""Cinecode core: canvas helpers, easing, keyframes, camera."""
import math
import os
import random

import cairo

# Frame size. Landscape episodes use the default; vertical Shorts set CINECODE_SIZE=1080x1920
# before importing cinecode (see episodes/zombie_ep01/__init__.py).
W, H = (int(v) for v in os.environ.get("CINECODE_SIZE", "1920x1080").lower().split("x"))
FPS = 30

OUTLINE = (0.11, 0.11, 0.14)


# ---------------------------------------------------------------- colours
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def mix(c1, c2, t):
    c1 = c1 if len(c1) == 4 else (*c1, 1.0)
    c2 = c2 if len(c2) == 4 else (*c2, 1.0)
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def shade(c, k):
    """k<0 darker, k>0 lighter."""
    c = c if len(c) == 4 else (*c, 1.0)
    if k < 0:
        return (c[0] * (1 + k), c[1] * (1 + k), c[2] * (1 + k), c[3])
    return (c[0] + (1 - c[0]) * k, c[1] + (1 - c[1]) * k, c[2] + (1 - c[2]) * k, c[3])


def src(cx, c, alpha=None):
    if len(c) == 3:
        c = (*c, 1.0)
    cx.set_source_rgba(c[0], c[1], c[2], c[3] if alpha is None else c[3] * alpha)


# ---------------------------------------------------------------- easing
def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def prog(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x, s=1.70158):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerpv(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


def win(t, a, b):
    """progress through [a,b] with smooth easing."""
    return smooth(prog(t, a, b))


def pulse(t, a, b, fade=0.15):
    """1 inside [a,b] with soft edges."""
    return min(smooth(prog(t, a - fade, a)), 1 - smooth(prog(t, b, b + fade)))


def kf(t, keys, ease=smooth):
    """Keyframe interpolation. keys = [(time, value), ...] value float or tuple."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            x = ease(prog(t, t0, t1))
            if isinstance(v0, tuple):
                return lerpv(v0, v1, x)
            return lerp(v0, v1, x)
    return keys[-1][1]


def noise1(x, seed=0):
    """Cheap smooth 1D value noise in [-1,1]."""
    i = math.floor(x)
    f = x - i

    def h(n):
        r = random.Random(n * 7919 + seed * 104729)
        return r.random() * 2 - 1

    a, b = h(i), h(i + 1)
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def shake(t, amp, freq=18, seed=1):
    return (noise1(t * freq, seed) * amp, noise1(t * freq, seed + 50) * amp)


# ---------------------------------------------------------------- shapes
def circle(cx, x, y, r):
    cx.new_sub_path()
    cx.arc(x, y, r, 0, 2 * math.pi)


def ellipse(cx, x, y, rx, ry, rot=0.0):
    cx.save()
    cx.translate(x, y)
    if rot:
        cx.rotate(rot)
    cx.scale(max(rx, 0.01), max(ry, 0.01))
    cx.new_sub_path()
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()


def rrect(cx, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    cx.new_sub_path()
    cx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cx.close_path()


def poly(cx, pts, close=True):
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    if close:
        cx.close_path()


def smooth_poly(cx, pts, close=True, k=0.5):
    """Catmull-Rom through points."""
    n = len(pts)
    if n < 3:
        poly(cx, pts, close)
        return
    P = pts + pts[:2] if close else [pts[0]] + pts + [pts[-1]]
    cx.move_to(*P[1] if close else P[1])
    rng = range(1, n + 1) if close else range(1, n)
    for i in rng:
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % len(P)], P[(i + 2) % len(P)]
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 3, p1[1] + (p2[1] - p0[1]) * k / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 3, p2[1] - (p3[1] - p1[1]) * k / 3)
        cx.curve_to(*c1, *c2, *p2)
    if close:
        cx.close_path()


def fill(cx, c, preserve=False):
    src(cx, c)
    cx.fill_preserve() if preserve else cx.fill()


def fs(cx, fillc, stroke=OUTLINE, lw=5.0):
    """fill + stroke current path."""
    if fillc is not None:
        src(cx, fillc)
        cx.fill_preserve()
    if stroke is not None and lw > 0:
        src(cx, stroke)
        cx.set_line_width(lw)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    else:
        cx.new_path()


def line(cx, pts, c=OUTLINE, lw=5.0, cap=cairo.LINE_CAP_ROUND):
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    src(cx, c)
    cx.set_line_width(lw)
    cx.set_line_cap(cap)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()


def curve(cx, p0, c1, c2, p1, c=OUTLINE, lw=5.0):
    cx.move_to(*p0)
    cx.curve_to(*c1, *c2, *p1)
    src(cx, c)
    cx.set_line_width(lw)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()


def vgrad(cx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in stops:
        c = c if len(c) == 4 else (*c, 1.0)
        g.add_color_stop_rgba(off, *c)
    return g


def rgrad(cx, x, y, r0, r1, stops):
    g = cairo.RadialGradient(x, y, r0, x, y, r1)
    for off, c in stops:
        c = c if len(c) == 4 else (*c, 1.0)
        g.add_color_stop_rgba(off, *c)
    return g


def text(cx, s, x, y, size, c=OUTLINE, align="center", font="Montserrat ExtraBold"):
    cx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    ext = cx.text_extents(s)
    if align == "center":
        x -= ext.width / 2 + ext.x_bearing
    elif align == "right":
        x -= ext.width + ext.x_bearing
    cx.move_to(x, y)
    src(cx, c)
    cx.show_text(s)


# ---------------------------------------------------------------- camera
class Cam:
    """World->screen. (x,y) is the world point shown at frame centre."""

    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0):
        self.x, self.y, self.zoom, self.rot = x, y, zoom, rot

    def apply(self, cx, parallax=1.0, py=None):
        py = parallax if py is None else py
        cx.translate(W / 2, H / 2)
        if self.rot:
            cx.rotate(self.rot)
        z = 1 + (self.zoom - 1) * parallax
        cx.scale(z, z)
        cx.translate(-(W / 2 + (self.x - W / 2) * parallax), -(H / 2 + (self.y - H / 2) * py))

    def to_screen(self, x, y):
        sx = (x - self.x) * self.zoom
        sy = (y - self.y) * self.zoom
        if self.rot:
            c, s = math.cos(self.rot), math.sin(self.rot)
            sx, sy = sx * c - sy * s, sx * s + sy * c
        return W / 2 + sx, H / 2 + sy


def cam_kf(t, keys, ease=ease_io):
    """keys: [(t, (x,y,zoom)), ...]"""
    v = kf(t, keys, ease)
    return Cam(*v)


def new_surface():
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

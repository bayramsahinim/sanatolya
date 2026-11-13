"""Cinematic look for the underwater short: lighting model, fog, bloom, grain, textures,
particles, beams, bubbles and water - everything that makes the flat 2D cast sit inside
a deep, moody environment.

Frame pipeline (see render.py):
    albedo (cairo)  ->  * light map (ambient + spot/point lights, computed at 1/4 res)
                    ->  + additive layer (beams, glows, lit particles; cairo)
                    ->  fog, bloom, grade, vignette, grain  ->  captions
"""
import math
import random

import cairo
import numpy as np
from PIL import Image, ImageFilter

from cinecode.core import H, W, circle, clamp, ellipse, hexc, smooth, src

LS = 4                      # light-map downscale
LW, LH = W // LS, H // LS
_YY, _XX = np.mgrid[0:LH, 0:LW].astype(np.float32)
_XX = (_XX + 0.5) * LS
_YY = (_YY + 0.5) * LS


# ------------------------------------------------------------------ surfaces <-> numpy
def surf_to_rgb(surf):
    """cairo ARGB32 (premultiplied BGRA) -> float32 RGB [0,1], composited on black."""
    surf.flush()
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))
    return a[:, :, 2::-1].astype(np.float32) * (1 / 255)


def rgb_to_bytes(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()


def np_to_surface(arr_rgba_f):
    """float RGBA (straight alpha) -> cairo surface."""
    h, w = arr_rgba_f.shape[:2]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    a = np.ndarray((h, w, 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))
    al = np.clip(arr_rgba_f[:, :, 3:4], 0, 1)
    rgb = np.clip(arr_rgba_f[:, :, :3], 0, 1) * al
    a[:, :, 0] = (rgb[:, :, 2] * 255).astype(np.uint8)
    a[:, :, 1] = (rgb[:, :, 1] * 255).astype(np.uint8)
    a[:, :, 2] = (rgb[:, :, 0] * 255).astype(np.uint8)
    a[:, :, 3] = (al[:, :, 0] * 255).astype(np.uint8)
    s.mark_dirty()
    return s


# ------------------------------------------------------------------ textures
def value_noise(w, h, scale, seed=0, octaves=4, persist=0.55):
    """fBm value noise in [0,1], shape (h,w)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gw, gh = max(2, int(w / s) + 2), max(2, int(h / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(g, mode="F").resize((int(gw * s), int(gh * s)), Image.BICUBIC)
        out += np.asarray(im)[:h, :w] * amp
        tot += amp
        amp *= persist
        s /= 2
    out /= tot
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)


def streaks(w, h, seed=0, length=180):
    """vertical rust/grime streaks in [0,1]."""
    rng = np.random.default_rng(seed)
    g = rng.random((max(2, h // length + 2), w // 3 + 2)).astype(np.float32) ** 3
    im = Image.fromarray(g, mode="F").resize((w, h + length), Image.BICUBIC)
    return np.clip(np.asarray(im)[:h, :w], 0, 1)


def blur(arr, r):
    from scipy.ndimage import gaussian_filter
    sig = (r, r) if arr.ndim == 2 else (r, r, 0)
    return gaussian_filter(arr.astype(np.float32), sig, mode="nearest")


# ------------------------------------------------------------------ lights
class Lights:
    """Collects lights for one frame (screen coordinates)."""

    def __init__(self, ambient=(0.1, 0.12, 0.14)):
        self.ambient = np.array(ambient, np.float32)
        self.items = []

    def spot(self, x, y, ang, spread=0.42, reach=1400, color=(1.0, 0.95, 0.82), power=1.6, soft=0.35):
        """cone from (x,y) toward angle `ang` (radians, screen space)."""
        self.items.append(("spot", x, y, ang, spread, reach, np.array(color, np.float32), power, soft))

    def point(self, x, y, r, color=(1, 0.9, 0.7), power=1.0):
        self.items.append(("point", x, y, r, np.array(color, np.float32), power))

    def rect_grad(self, y0, y1, color, power):
        """vertical gradient light (e.g. daylight from the surface): full at y0, zero at y1."""
        self.items.append(("vgrad", y0, y1, np.array(color, np.float32), power))

    def compute(self):
        L = np.empty((LH, LW, 3), np.float32)
        L[:] = self.ambient
        for it in self.items:
            if it[0] == "spot":
                _, x, y, ang, spread, reach, col, power, soft = it
                dx, dy = _XX - x, _YY - y
                d = np.sqrt(dx * dx + dy * dy) + 1e-3
                cosang = (dx * math.cos(ang) + dy * math.sin(ang)) / d
                a = np.arccos(np.clip(cosang, -1, 1))
                cone = np.clip((spread - a) / (spread * soft), 0, 1)
                cone = cone * cone * (3 - 2 * cone)
                fall = np.clip(1 - d / reach, 0, 1) ** 1.6
                near = np.clip(d / 60, 0, 1)
                k = (cone * fall * near * power)[..., None]
                L += k * col
            elif it[0] == "point":
                _, x, y, r, col, power = it
                d2 = ((_XX - x) ** 2 + (_YY - y) ** 2) / (r * r)
                L += (np.exp(-d2 * 2.2) * power)[..., None] * col
            elif it[0] == "vgrad":
                _, y0, y1, col, power = it
                k = np.clip((y1 - _YY) / (y1 - y0), 0, 1) ** 1.5 * power
                L += k[..., None] * col
        im = [np.asarray(Image.fromarray(L[:, :, i], mode="F").resize((W, H), Image.BILINEAR)) for i in range(3)]
        return np.stack(im, axis=2)


# ------------------------------------------------------------------ post
_VIG = None
_GRAIN = None


def vignette_mask(strength=0.55):
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        nx, ny = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
        r = np.sqrt(nx * nx * 1.0 + ny * ny * 0.75)
        _VIG = np.clip(1 - (r - 0.55) * 0.9, 0, 1) ** 1.5
    return 1 - strength + strength * _VIG[..., None]


def grain(frame_i, amt=0.011):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7)
        _GRAIN = [rng.standard_normal((H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    g = _GRAIN[frame_i % 6]
    g = np.repeat(np.repeat(g, 2, axis=0), 2, axis=1)
    return (g * amt)[..., None]


def bloom(img, thresh=0.72, radius=18, amt=0.55):
    small = img[::4, ::4]
    b = np.clip(small - thresh, 0, None)
    if b.max() <= 0:
        return img
    b = blur(b, radius / 4)
    up = np.stack([np.asarray(Image.fromarray(b[:, :, i], mode="F").resize((W, H), Image.BILINEAR)) for i in range(3)], 2)
    return img + up * amt


def finish(albedo, lights, add=None, fog=None, fog_amt=0.0, grade=None, bloom_amt=0.5, vig=0.55,
           frame_i=0, exposure=1.0, depth_fog=None):
    """Combine the layers into the final graded frame (float RGB)."""
    img = albedo * lights.compute() if lights is not None else albedo.copy()
    if add is not None:
        img += add
    if fog is not None and fog_amt > 0:
        fogc = np.array(fog, np.float32)
        if depth_fog is not None:  # (H,) per-row extra fog
            f = np.clip(fog_amt + depth_fog[:, None, None], 0, 1)
        else:
            f = fog_amt
        img = img * (1 - f) + fogc * f
    img *= exposure
    if bloom_amt:
        img = bloom(img, amt=bloom_amt)
    if grade is not None:
        lift, gain, sat = grade
        lum = img.mean(axis=2, keepdims=True)
        img = lum + (img - lum) * sat
        img = np.array(lift, np.float32) + img * np.array(gain, np.float32)
    # gentle filmic shoulder
    img = img / (1 + 0.18 * np.clip(img - 0.8, 0, None))
    img *= vignette_mask(vig)
    img += grain(frame_i)
    return img


# ------------------------------------------------------------------ additive helpers (cairo)
def new_add():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    return s, cairo.Context(s)


def beam(cx, x, y, ang, length=1400, spread=0.36, color=(1, 0.95, 0.8), alpha=0.22, t=0.0, seed=0):
    """volumetric light cone (additive layer)."""
    steps = 7
    for i in range(steps):
        k = (i + 1) / steps
        sp = spread * (0.35 + 0.65 * k)
        a = alpha * (1 - k * 0.75) / steps * 2.2
        cx.save()
        cx.translate(x, y)
        cx.rotate(ang)
        g = cairo.LinearGradient(0, 0, length, 0)
        g.add_color_stop_rgba(0, *color, a)
        g.add_color_stop_rgba(0.45, *color, a * 0.5)
        g.add_color_stop_rgba(1, *color, 0)
        cx.move_to(0, -6)
        cx.line_to(length, -math.tan(sp) * length)
        cx.line_to(length, math.tan(sp) * length)
        cx.line_to(0, 6)
        cx.close_path()
        cx.set_source(g)
        cx.fill()
        cx.restore()
    # bright source
    glow(cx, x, y, 46, color, alpha * 3.2)


def glow(cx, x, y, r, color=(1, 0.95, 0.8), alpha=0.6):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *color, alpha)
    g.add_color_stop_rgba(0.35, *color, alpha * 0.35)
    g.add_color_stop_rgba(1, *color, 0)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.fill()


def god_rays(cx, t, x0=-200, x1=1300, top=-100, length=1900, n=7, alpha=0.08, color=(0.6, 0.85, 0.9), seed=3):
    rng = random.Random(seed)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rng.random() * 0.6) / n
        wv = 60 + rng.random() * 120
        sway = math.sin(t * (0.3 + rng.random() * 0.3) + i) * 60
        a = alpha * (0.5 + 0.5 * math.sin(t * (0.5 + rng.random()) + i * 2.1) ** 2)
        g = cairo.LinearGradient(0, top, 0, top + length)
        g.add_color_stop_rgba(0, *color, a)
        g.add_color_stop_rgba(1, *color, 0)
        cx.move_to(x + sway, top)
        cx.line_to(x + sway + wv, top)
        cx.line_to(x + sway * 0.2 + wv * 2.6 + 160, top + length)
        cx.line_to(x + sway * 0.2 + 160, top + length)
        cx.close_path()
        cx.set_source(g)
        cx.fill()


class Snow:
    """Marine snow / suspended particles, drawn into the albedo so the lights reveal them."""

    def __init__(self, n=260, seed=1, depth=(0.4, 1.4)):
        rng = random.Random(seed)
        self.p = [(rng.random() * 1.4 - 0.2, rng.random(), rng.uniform(*depth), rng.random() * 6.28)
                  for _ in range(n)]

    def draw(self, cx, t, drift=(6, -10), alpha=0.85, color=(0.85, 0.92, 0.88), cam_dx=0.0, cam_dy=0.0):
        for (u, v, z, ph) in self.p:
            x = (u * W + drift[0] * t * z + math.sin(t * 0.6 + ph) * 14 * z - cam_dx * z) % (W * 1.2) - W * 0.1
            y = (v * H + drift[1] * t * z - cam_dy * z) % (H * 1.1) - H * 0.05
            r = 1.2 + 2.4 * z
            src(cx, (*color, alpha * min(1, 0.35 + z * 0.4)))
            cx.arc(x, y, r, 0, 6.2832)
            cx.fill()


def bubble(cx, x, y, r, alpha=1.0, rim=(0.85, 0.97, 1.0)):
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.08 * alpha)
    g.add_color_stop_rgba(0.75, *rim, 0.12 * alpha)
    g.add_color_stop_rgba(1, *rim, 0.75 * alpha)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 6.2832)
    cx.fill()
    src(cx, (1, 1, 1, 0.9 * alpha))
    cx.arc(x - r * 0.38, y - r * 0.38, max(0.8, r * 0.22), 0, 6.2832)
    cx.fill()


def bubble_stream(cx, x, y, t, t0=0.0, rate=10, rise=260, spread=22, size=(4, 12), seed=2, alpha=1.0,
                  life=2.4, burst=None):
    """bubbles emitted from (x,y) since t0. burst=(t_burst, count) for a sudden cloud."""
    rng = random.Random(seed)
    n = int(rate * 12)
    for i in range(n):
        te = t0 + i / rate + rng.random() * 0.05
        age = t - te
        if age < 0 or age > life:
            continue
        r = rng.uniform(*size) * (1 + age * 0.15)
        bx = x + math.sin(age * 5 + i) * spread * min(1, age) + rng.uniform(-6, 6)
        by = y - age * rise * (0.8 + rng.random() * 0.4) - age * age * 30
        bubble(cx, bx, by, r, alpha * (1 - age / life) ** 0.5)
    if burst:
        tb, cnt = burst
        age = t - tb
        if 0 <= age < 2.5:
            for i in range(cnt):
                a = rng.random() * 6.28
                sp = rng.uniform(80, 420)
                r = rng.uniform(3, 18)
                bx = x + math.cos(a) * sp * min(age, 0.35) * 2.2 + math.sin(age * 4 + i) * 10
                by = y + math.sin(a) * sp * min(age, 0.35) * 1.6 - age * age * 260 - age * 120
                bubble(cx, bx, by, r * (1 + age * 0.3), alpha * (1 - age / 2.5))


def water_surface_path(cx, y, t, x0=-100, x1=None, amp=6, k=0.018, speed=2.2, seed=0):
    x1 = W + 100 if x1 is None else x1
    cx.move_to(x0, y)
    xs = range(int(x0), int(x1) + 20, 20)
    for x in xs:
        yy = y + math.sin(x * k + t * speed + seed) * amp + math.sin(x * k * 2.3 - t * speed * 1.4 + seed * 2) * amp * 0.45
        cx.line_to(x, yy)


def water_body(cx, y, t, color=(0.06, 0.22, 0.24), alpha=0.62, x0=-100, x1=None, bottom=None, amp=6, seed=0,
               line_alpha=0.75):
    """translucent water from surface line y down (drawn OVER things to submerge them)."""
    x1 = W + 100 if x1 is None else x1
    bottom = H + 200 if bottom is None else bottom
    water_surface_path(cx, y, t, x0, x1, amp=amp, seed=seed)
    cx.line_to(x1, bottom)
    cx.line_to(x0, bottom)
    cx.close_path()
    g = cairo.LinearGradient(0, y, 0, y + 900)
    g.add_color_stop_rgba(0, *color, alpha * 0.75)
    g.add_color_stop_rgba(1, color[0] * 0.5, color[1] * 0.6, color[2] * 0.6, min(1, alpha * 1.25))
    cx.set_source(g)
    cx.fill()
    # surface highlight line
    water_surface_path(cx, y, t, x0, x1, amp=amp, seed=seed)
    cx.set_source_rgba(0.75, 0.95, 1.0, line_alpha)
    cx.set_line_width(4)
    cx.stroke()
    # glints
    rng = random.Random(seed + 9)
    for i in range(26):
        gx = x0 + (x1 - x0) * rng.random()
        ph = rng.random() * 6.28
        a = max(0, math.sin(t * 2.5 + ph)) * 0.7
        gy = y + math.sin(gx * 0.018 + t * 2.2 + seed) * amp + 6
        cx.set_source_rgba(0.85, 1, 1, a * line_alpha)
        cx.rectangle(gx, gy, 18 + rng.random() * 30, 2.5)
        cx.fill()


def caustics(cx, t, x0, y0, x1, y1, alpha=0.12, scale=1.0, seed=4, color=(0.7, 1, 0.95)):
    """animated caustic web (additive)."""
    rng = random.Random(seed)
    cx.save()
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    cx.clip()
    cx.set_line_width(3 * scale)
    for i in range(int((x1 - x0) * (y1 - y0) / (90000 * scale * scale)) + 4):
        cxp = x0 + rng.random() * (x1 - x0)
        cyp = y0 + rng.random() * (y1 - y0)
        r = (40 + rng.random() * 60) * scale
        ph = rng.random() * 6.28
        cx.new_path()
        for k in range(7):
            a = k / 6 * 6.2832
            rr = r * (1 + 0.25 * math.sin(t * 1.8 + ph + k * 1.7))
            px = cxp + math.cos(a) * rr + math.sin(t * 0.9 + ph) * 12 * scale
            py = cyp + math.sin(a) * rr * 0.6
            cx.line_to(px, py) if k else cx.move_to(px, py)
        cx.close_path()
        cx.set_source_rgba(*color, alpha * (0.6 + 0.4 * math.sin(t * 2 + ph)))
        cx.stroke()
    cx.restore()


def flash(img, amt, color=(1, 1, 1)):
    if amt <= 0:
        return img
    return img * (1 - amt) + np.array(color, np.float32) * amt

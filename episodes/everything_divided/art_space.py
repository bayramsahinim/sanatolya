"""Procedural Milky Way backdrop (numpy noise nebula + star field), cached."""
import math
import random

import cairo
import numpy as np
from PIL import Image

from episodes.everything_divided.common import H, W

_C = {}
GW, GH = int(W * 1.25), int(H * 1.25)   # oversized for slow parallax drift


def _noise(shape, scale, seed):
    rng = np.random.default_rng(seed)
    h, w = shape
    small = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0


def fbm(shape, seed, scales=(320, 160, 80, 40, 20)):
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for i, s in enumerate(scales):
        out += amp * _noise(shape, s, seed + i * 17)
        tot += amp
        amp *= 0.55
    return out / tot


def galaxy_surface():
    if "gal" in _C:
        return _C["gal"]
    h, w = GH, GW
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # galactic band: diagonal from lower-left to upper-right
    ang = math.radians(-58)
    nx, ny = -math.sin(ang), math.cos(ang)
    cxp, cyp = w * 0.52, h * 0.42
    d = ((xx - cxp) * math.cos(ang) + (yy - cyp) * math.sin(ang))    # distance across the band
    along = ((xx - cxp) * -math.sin(ang) + (yy - cyp) * math.cos(ang))
    n1 = fbm((h, w), 3)
    n2 = fbm((h, w), 9, (200, 100, 50, 25, 12))
    width = 260 + 90 * (n1 - 0.5) * 2
    band = np.exp(-((d + 60 * (n2 - 0.5)) / width) ** 2)
    core = np.exp(-(((xx - cxp) / 300) ** 2 + ((yy - cyp) / 220) ** 2))
    # base sky
    top = np.array([0.03, 0.04, 0.13], np.float32)
    bot = np.array([0.09, 0.05, 0.2], np.float32)
    v = (yy / h)[..., None]
    img = top * (1 - v) + bot * v
    # nebula colour layers
    neb_blue = np.array([0.25, 0.35, 0.85], np.float32)
    neb_mag = np.array([0.75, 0.25, 0.7], np.float32)
    neb_teal = np.array([0.15, 0.65, 0.75], np.float32)
    warm = np.array([1.0, 0.85, 0.65], np.float32)
    m1 = (band * (0.55 + 0.6 * n1))[..., None]
    img = img + neb_blue * m1 * 0.55
    m2 = (band * np.clip(n2 * 1.6 - 0.55, 0, 1))[..., None]
    img = img + neb_mag * m2 * 0.45
    m3 = (np.exp(-((d + 220) / 300) ** 2) * np.clip(fbm((h, w), 21) * 1.8 - 0.8, 0, 1))[..., None]
    img = img + neb_teal * m3 * 0.35
    img = img + warm * (core * (0.7 + 0.3 * n1))[..., None] * 0.6
    # dust lanes along the band centre
    dust = np.clip(fbm((h, w), 33, (120, 60, 30, 15)) * 2.0 - 0.95, 0, 1)
    lane = np.exp(-((d - 10 * (n1 - 0.5)) / 70) ** 2)
    img = img * (1 - (dust * lane * 0.75)[..., None])
    # unresolved star haze in the band
    rng = np.random.default_rng(5)
    haze = (rng.random((h, w)) < 0.02 * band + 0.002).astype(np.float32) * rng.random((h, w)) * 0.5
    img = img + haze[..., None] * np.array([0.9, 0.92, 1.0], np.float32)
    img = np.clip(img, 0, 1)
    rgb = (img * 255).astype(np.uint8)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    a = np.ndarray((h, w, 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))
    a[..., 0] = rgb[..., 2]
    a[..., 1] = rgb[..., 1]
    a[..., 2] = rgb[..., 0]
    a[..., 3] = 255
    s.mark_dirty()
    # resolved stars
    c = cairo.Context(s)
    rnd = random.Random(8)
    stars = []
    for _ in range(4200):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        dd = abs((x - cxp) * math.cos(ang) + (y - cyp) * math.sin(ang))
        if rnd.random() > 0.25 + 0.75 * math.exp(-(dd / 320) ** 2):
            continue
        r = rnd.choice([0.6, 0.8, 1.0, 1.0, 1.3, 1.6, 2.0])
        col = rnd.choice([(1, 1, 1), (0.8, 0.88, 1), (1, 0.92, 0.8), (0.85, 0.85, 1)])
        c.arc(x, y, r, 0, 2 * math.pi)
        c.set_source_rgba(*col, rnd.uniform(0.5, 1.0))
        c.fill()
        if r >= 1.6:
            g = cairo.RadialGradient(x, y, 0, x, y, r * 5)
            g.add_color_stop_rgba(0, *col, 0.35)
            g.add_color_stop_rgba(1, *col, 0)
            c.arc(x, y, r * 5, 0, 2 * math.pi)
            c.set_source(g)
            c.fill()
            stars.append((x, y, r, rnd.uniform(0, 6.28)))
    _C["gal"] = s
    _C["twinkle"] = stars
    return s


def galaxy(cx, t, alpha=1.0, drift=(0.0, 0.0)):
    s = galaxy_surface()
    ox = -(GW - W) / 2 + drift[0]
    oy = -(GH - H) / 2 + drift[1]
    cx.save()
    cx.set_source_surface(s, ox, oy)
    cx.paint_with_alpha(alpha)
    for x, y, r, ph in _C["twinkle"][::2]:
        a = 0.5 + 0.5 * math.sin(t * 2.5 + ph)
        xx, yy = x + ox, y + oy
        if -10 < xx < W + 10 and -10 < yy < H + 10:
            cx.move_to(xx - r * 4 * a, yy)
            cx.line_to(xx + r * 4 * a, yy)
            cx.move_to(xx, yy - r * 4 * a)
            cx.line_to(xx, yy + r * 4 * a)
            cx.set_source_rgba(1, 1, 1, 0.5 * a * alpha)
            cx.set_line_width(1.0)
            cx.stroke()
    cx.restore()


def star_glow(cx, x, y, r, t, alpha=1.0, ph=0.0, color=(1.0, 0.86, 0.45)):
    """A highlighted 'your star'."""
    k = 0.85 + 0.15 * math.sin(t * 3 + ph)
    g = cairo.RadialGradient(x, y, 0, x, y, r * 4.5)
    g.add_color_stop_rgba(0, *color, 0.55 * alpha)
    g.add_color_stop_rgba(1, *color, 0)
    cx.arc(x, y, r * 4.5, 0, 2 * math.pi)
    cx.set_source(g)
    cx.fill()
    cx.save()
    cx.translate(x, y)
    pts = []
    for i in range(10):
        rr = r * k if i % 2 == 0 else r * 0.45 * k
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    cx.close_path()
    cx.set_source_rgba(1, 0.93, 0.6, alpha)
    cx.fill_preserve()
    cx.set_source_rgba(0.55, 0.38, 0.05, alpha)
    cx.set_line_width(2)
    cx.stroke()
    cx.restore()

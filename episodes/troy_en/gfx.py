"""Vertical canvas, camera with parallax layers, depth blur, sticker halo, grading."""
import math

import cairo
import cv2
import numpy as np

from cinecode.core import hexc, kf, lerp, noise1, src

W, H = 1080, 1920
FPS = 30
PADX, PADY = 420, 360          # layers are rendered larger than the frame for camera moves
LW, LH = W + 2 * PADX, H + 2 * PADY


def surface(w=W, h=H):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)


def to_np(surf):
    surf.flush()
    a = np.ndarray((surf.get_height(), surf.get_stride() // 4, 4), np.uint8, surf.get_data())
    return a[:, :surf.get_width()]


def from_np(arr):
    arr = np.ascontiguousarray(arr)
    h, w = arr.shape[:2]
    s = surface(w, h)
    to_np(s)[:] = arr
    s.mark_dirty()
    return s


def blur_surface(surf, sigma):
    if sigma <= 0:
        return surf
    a = to_np(surf).astype(np.float32)
    k = int(sigma * 3) * 2 + 1
    b = cv2.GaussianBlur(a, (k, k), sigma)
    return from_np(np.clip(b, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ camera
class Cam:
    """(x, y) = world point at frame centre, zoom, rotation (rad)."""

    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0, sx=0.0, sy=0.0):
        self.x, self.y, self.zoom, self.rot, self.sx, self.sy = x, y, zoom, rot, sx, sy

    def apply(self, cx, par=1.0):
        cx.translate(W / 2 + self.sx * par, H / 2 + self.sy * par)
        if self.rot:
            cx.rotate(self.rot * par)
        z = 1 + (self.zoom - 1) * par
        cx.scale(z, z)
        cx.translate(-(W / 2 + (self.x - W / 2) * par), -(H / 2 + (self.y - H / 2) * par))

    def to_screen(self, x, y):
        return W / 2 + (x - self.x) * self.zoom + self.sx, H / 2 + (y - self.y) * self.zoom + self.sy


def cam_kf(t, keys, shake_amp=0.0, shake_t=None, seed=3):
    """keys: [(t, (x, y, zoom)), ...]; optional decaying shake [(t0, amp, dur), ...]."""
    x, y, z = kf(t, keys)
    c = Cam(x, y, z)
    for t0, amp, dur in (shake_t or []):
        if t0 <= t < t0 + dur:
            k = amp * (1 - (t - t0) / dur) ** 2
            c.sx += noise1(t * 26, seed) * k
            c.sy += noise1(t * 26, seed + 9) * k
    if shake_amp:
        c.sx += noise1(t * 1.3, seed + 3) * shake_amp
        c.sy += noise1(t * 1.1, seed + 5) * shake_amp
    return c


# ------------------------------------------------------------------ layers
class Layer:
    """A static painted layer in world space (covers [-PADX, W+PADX] x [-PADY, H+PADY])."""

    def __init__(self, draw, par=1.0, blur=0.0):
        self.draw_fn, self.par, self.blur = draw, par, blur
        self._s = None

    def surf(self):
        if self._s is None:
            s = surface(LW, LH)
            cx = cairo.Context(s)
            cx.translate(PADX, PADY)
            self.draw_fn(cx)
            self._s = blur_surface(s, self.blur)
        return self._s

    def paint(self, cx, cam, alpha=1.0):
        cx.save()
        cam.apply(cx, self.par)
        cx.set_source_surface(self.surf(), -PADX, -PADY)
        cx.get_source().set_filter(cairo.FILTER_GOOD)
        cx.paint_with_alpha(alpha) if alpha < 1 else cx.paint()
        cx.restore()


# ------------------------------------------------------------------ halo
HALO = (246, 236, 214)  # cream (RGB)


def halo_composite(dst_cx, char_surf, radius=7, shadow=True):
    """Paint `char_surf` onto dst with a cream sticker outline + soft drop shadow."""
    a = to_np(char_surf)
    al = a[:, :, 3]
    if not al.any():
        return
    r = max(2, int(radius))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    d = cv2.dilate(al, ker)
    d = cv2.GaussianBlur(d, (3, 3), 0.8)
    out = np.zeros_like(a)
    if shadow:
        sh = cv2.GaussianBlur(d, (0, 0), 9)
        sh = np.roll(np.roll(sh, 10, 0), 6, 1)
        out[:, :, 3] = (sh.astype(np.float32) * 0.35).astype(np.uint8)  # black, premultiplied
    # halo over shadow
    hf = d.astype(np.float32) / 255
    inv = 1 - hf
    o = out.astype(np.float32)
    for i, c in enumerate((HALO[2], HALO[1], HALO[0])):  # BGRA order in memory
        o[:, :, i] = c * hf + o[:, :, i] * inv
    o[:, :, 3] = 255 * hf + o[:, :, 3] * inv
    # character over halo
    af = al.astype(np.float32)[:, :, None] / 255
    o = a.astype(np.float32) + o * (1 - af)
    dst_cx.set_source_surface(from_np(np.clip(o, 0, 255).astype(np.uint8)), 0, 0)
    dst_cx.paint()


# ------------------------------------------------------------------ grading
def grade(cx, top=None, bottom=None, op=cairo.OPERATOR_SOFT_LIGHT, alpha=1.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bottom)
    cx.save()
    cx.set_operator(op)
    cx.set_source(g)
    cx.paint_with_alpha(alpha)
    cx.restore()


def vignette(cx, strength=0.55, color=(0.05, 0.03, 0.02)):
    g = cairo.RadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.5, H * 0.75)
    g.add_color_stop_rgba(0, *color, 0)
    g.add_color_stop_rgba(1, *color, strength)
    cx.save()
    cx.set_source(g)
    cx.paint()
    cx.restore()


def glow(cx, x, y, r, color, alpha=0.6, op=cairo.OPERATOR_ADD):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *color[:3], alpha)
    g.add_color_stop_rgba(0.4, *color[:3], alpha * 0.35)
    g.add_color_stop_rgba(1, *color[:3], 0)
    cx.save()
    cx.set_operator(op)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.fill()
    cx.restore()


def rays(cx, x, y, ang, spread, length, color, alpha=0.18, n=7, seed=1, t=0.0):
    """Soft volumetric light shafts from (x, y)."""
    import random
    r = random.Random(seed)
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    for i in range(n):
        a = ang + (i / max(1, n - 1) - 0.5) * spread + math.sin(t * 0.4 + i) * 0.01
        w = r.uniform(0.02, 0.06)
        g = cairo.LinearGradient(x, y, x + math.cos(a) * length, y + math.sin(a) * length)
        aa = alpha * r.uniform(0.5, 1.0)
        g.add_color_stop_rgba(0, *color[:3], aa)
        g.add_color_stop_rgba(1, *color[:3], 0)
        cx.move_to(x, y)
        cx.line_to(x + math.cos(a - w) * length, y + math.sin(a - w) * length)
        cx.line_to(x + math.cos(a + w) * length, y + math.sin(a + w) * length)
        cx.close_path()
        cx.set_source(g)
        cx.fill()
    cx.restore()


def contact_shadow(cx, x, y, w, alpha=0.35):
    cx.save()
    cx.translate(x, y)
    cx.scale(w, w * 0.18)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0.1, 0.06, 0.03, alpha)
    g.add_color_stop_rgba(1, 0.1, 0.06, 0.03, 0)
    cx.set_source(g)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.fill()
    cx.restore()

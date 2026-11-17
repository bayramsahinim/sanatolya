"""Visual identity for the vertical "numbers" short: Just Needy noir.

Dark charcoal sets drawn in soft glowing line-art, Just Needy round-headed characters,
the hero's blue hoodie as the only colour, and glowing numbers. Every frame is drawn into
two layers: the main canvas and a quarter-resolution glow layer that is blurred and added
on top (bloom), so lines and numbers really glow.
"""
import math

import cairo
import numpy as np
from PIL import Image, ImageFilter

from cinecode.core import back_out, clamp, ease_io, ease_out, hexc, lerp, mix, prog, smooth  # noqa: F401

W, H = 1080, 1920          # design space: every shot is drawn in these (vertical) coordinates
FPS = 30
XL, XR = -1700, W + 1700  # horizontal extent for "full width" set lines (wide enough for 16:9 framing)

# Output mode. Vertical renders design space 1:1. Landscape renders 1920x1080 through a per-shot
# view (design-space centre + scale), so the same shots are reframed for widescreen.
MODE = {"land": False}


def land():
    return MODE["land"]


def out_size():
    return (1920, 1080) if MODE["land"] else (W, H)
GS = 0.25  # glow layer scale

# ---------------------------------------------------------------- palette
BG_TOP = hexc("#14161c")
BG_BOT = hexc("#08090c")
INK = hexc("#0b0c10")          # character outline
LINE = hexc("#9aa0ad")         # set line-art
LINE_DIM = hexc("#5d626e")
PANEL = hexc("#1b1e25")        # filled set surfaces
PANEL2 = hexc("#23262f")
WHITE = hexc("#f5f5f8")
SKIN_SHADE = hexc("#d9d6ec")   # lavender crescent shading on heads
GREY1 = hexc("#c9ccd4")
GREY2 = hexc("#8d929e")
GREY3 = hexc("#5b606c")
GREY4 = hexc("#3a3e48")
BLUE = hexc("#1766f2")         # Just Needy hoodie
BLUE_D = hexc("#0e4cc2")
BLUE_L = hexc("#4f8dff")
GLOW_BLUE = hexc("#8fb6ff")
NUM = hexc("#ffffff")

FONT_NUM = "Inter Display"
FONT_UI = "Inter"


# ---------------------------------------------------------------- frame
class Frame:
    """Main canvas + glow layer. Use f.cx for normal drawing, f.gx for glow emitters."""

    def __init__(self, view=None):
        self.ow, self.oh = out_size()
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.ow, self.oh)
        self.gsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(self.ow * GS), int(self.oh * GS))
        self.cx = cairo.Context(self.surf)
        self.gx = cairo.Context(self.gsurf)
        self.gx.scale(GS, GS)
        for c in (self.cx, self.gx):
            c.set_line_join(cairo.LINE_JOIN_ROUND)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
        if view is not None:
            # landscape: design-space point (vx, vy) at the output centre, scaled by s
            vx, vy, sc = view
            for c in (self.cx, self.gx):
                c.translate(self.ow / 2, self.oh / 2)
                c.scale(sc, sc)
                c.translate(-vx, -vy)

    def save(self):
        self.cx.save()
        self.gx.save()

    def restore(self):
        self.cx.restore()
        self.gx.restore()

    def both(self, fn):
        fn(self.cx)
        fn(self.gx)

    def cam(self, x, y, z=1.0, rot=0.0):
        """Show world point (x, y) at frame centre with zoom z."""
        for c in (self.cx, self.gx):
            c.translate(W / 2, H / 2)
            if rot:
                c.rotate(rot)
            c.scale(z, z)
            c.translate(-x, -y)

    def to_rgb(self, glow=1.0, grain=None):
        W_, H_ = self.ow, self.oh
        a = np.ndarray((H_, W_, 4), np.uint8, self.surf.get_data()).astype(np.float32)
        g = np.ndarray((int(H_ * GS), int(W_ * GS), 4), np.uint8, self.gsurf.get_data())
        gi = Image.fromarray(g[:, :, :3][:, :, ::-1].copy())
        g1 = gi.filter(ImageFilter.GaussianBlur(3.0))
        g2 = gi.filter(ImageFilter.GaussianBlur(12.0))
        g1 = np.asarray(g1.resize((W_, H_), Image.BILINEAR), np.float32)
        g2 = np.asarray(g2.resize((W_, H_), Image.BILINEAR), np.float32)
        rgb = a[:, :, :3][:, :, ::-1]
        out = rgb + (g1 * 0.8 + g2 * 1.1) * glow
        if grain is not None:
            out += grain
        return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- primitives
def src(c, col, a=1.0):
    col = col if len(col) == 4 else (*col, 1.0)
    c.set_source_rgba(col[0], col[1], col[2], col[3] * a)


def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    c.close_path()


def ellipse(c, x, y, rx, ry):
    c.save()
    c.translate(x, y)
    c.scale(max(rx, 0.01), max(ry, 0.01))
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()


def bg(f, top=BG_TOP, bot=BG_BOT, spot=None, spot_r=900, spot_a=0.10):
    """Full-frame background (drawn in screen space)."""
    c = f.cx
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bot)
    c.set_source(g)
    c.paint()
    if spot:
        sx, sy = spot
        rg = cairo.RadialGradient(sx, sy, 0, sx, sy, spot_r)
        rg.add_color_stop_rgba(0, 1, 1, 1, spot_a)
        rg.add_color_stop_rgba(1, 1, 1, 1, 0)
        c.set_source(rg)
        c.paint()
    f.gx.set_source_rgba(0, 0, 0, 1)
    f.gx.paint()


def vignette(f, k=0.55):
    c = f.cx
    if land():
        # widescreen vignette in output space (independent of the shot's framing)
        c.save()
        c.identity_matrix()
        ow, oh = f.ow, f.oh
        c.translate(ow / 2, oh * 0.48)
        c.scale(ow / oh, 1.0)
        rg = cairo.RadialGradient(0, 0, oh * 0.32, 0, 0, oh * 0.82)
        rg.add_color_stop_rgba(0, 0, 0, 0, 0)
        rg.add_color_stop_rgba(1, 0, 0, 0, k)
        c.set_source(rg)
        c.paint()
        c.restore()
        return
    rg = cairo.RadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.48, H * 0.78)
    rg.add_color_stop_rgba(0, 0, 0, 0, 0)
    rg.add_color_stop_rgba(1, 0, 0, 0, k)
    c.set_source(rg)
    c.paint()


def gline(f, pts, col=LINE, lw=3.0, a=1.0, glow=0.55, close=False):
    """Glowing line-art stroke (main + glow layer)."""
    for c, w, al in ((f.cx, lw, a), (f.gx, lw * 2.2, a * glow)):
        if al <= 0:
            continue
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        if close:
            c.close_path()
        src(c, col, al)
        c.set_line_width(w)
        c.stroke()


def grect(f, x, y, w, h, r=0, col=LINE, lw=3.0, a=1.0, glow=0.55, fillc=None, fill_a=1.0):
    for c, ww, al, is_g in ((f.cx, lw, a, False), (f.gx, lw * 2.2, a * glow, True)):
        if r:
            rrect(c, x, y, w, h, r)
        else:
            c.rectangle(x, y, w, h)
        if fillc is not None and not is_g:
            src(c, fillc, fill_a * a)
            c.fill_preserve()
        if al > 0:
            src(c, col, al)
            c.set_line_width(ww)
            c.stroke()
        else:
            c.new_path()


def gcircle(f, x, y, r, col=LINE, lw=3.0, a=1.0, glow=0.55, fillc=None):
    for c, ww, al, is_g in ((f.cx, lw, a, False), (f.gx, lw * 2.2, a * glow, True)):
        c.arc(x, y, r, 0, 2 * math.pi)
        if fillc is not None and not is_g:
            src(c, fillc, a)
            c.fill_preserve()
        src(c, col, al)
        c.set_line_width(ww)
        c.stroke()


def glow_blob(f, x, y, r, col=WHITE, a=0.5):
    """Soft light source (glow layer only + faint main)."""
    for c, k in ((f.cx, 0.35), (f.gx, 1.0)):
        rg = cairo.RadialGradient(x, y, 0, x, y, r)
        rg.add_color_stop_rgba(0, col[0], col[1], col[2], a * k)
        rg.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        c.set_source(rg)
        c.arc(x, y, r, 0, 2 * math.pi)
        c.fill()


# ---------------------------------------------------------------- text
def font(c, family=FONT_UI, weight="bold", size=40):
    c.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if weight == "bold" else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)


def text_w(c, s, family=FONT_UI, weight="bold", size=40):
    font(c, family, weight, size)
    return c.text_extents(s).x_advance


def text(f_or_c, s, x, y, size, col=WHITE, a=1.0, align="center", family=FONT_UI, weight="bold",
         glow=0.0, layer_both=True):
    """Draw text; if glow>0 and a Frame is given, also emits into the glow layer."""
    ctxs = []
    if isinstance(f_or_c, Frame):
        ctxs.append((f_or_c.cx, a))
        if glow > 0:
            ctxs.append((f_or_c.gx, a * glow))
    else:
        ctxs.append((f_or_c, a))
    for c, al in ctxs:
        font(c, family, weight, size)
        e = c.text_extents(s)
        xx = x
        if align == "center":
            xx = x - e.x_advance / 2
        elif align == "right":
            xx = x - e.x_advance
        c.move_to(xx, y)
        src(c, col, al)
        c.show_text(s)
        c.new_path()


def fmt(n):
    return f"{int(round(n)):,}"


def number(f, n, x, y, size=120, a=1.0, glow=1.0, col=NUM, halo=True, roll=0.0):
    """A glowing number above a head. (x, y) = centre of the number. `n` may be str or float.
    `roll` in 0..1 adds a vertical slot-machine blur offset used while counting."""
    if a <= 0:
        return
    s = n if isinstance(n, str) else fmt(n)
    c = f.cx
    font(c, FONT_NUM, "bold", size)
    e = c.text_extents("0")
    by = y + e.height / 2
    if halo:
        glow_blob(f, x, y, size * 1.15, GLOW_BLUE, 0.13 * a)
    text(f, s, x, by + roll * size * 0.08, size, col, a, "center", FONT_NUM, "bold", glow=glow * 0.5)


def count(t, t0, t1, v0, v1, ease=ease_io):
    return v0 + (v1 - v0) * ease(prog(t, t0, t1))


# ---------------------------------------------------------------- grain
def make_grain(n=6, amp=2.5, seed=3):
    rng = np.random.default_rng(seed)
    ow, oh = out_size()
    out = []
    for _ in range(n):
        g = rng.normal(0, amp, (oh // 2, ow // 2, 1)).astype(np.float32)
        g = np.repeat(np.repeat(g, 2, axis=0), 2, axis=1)
        out.append(g)
    return out

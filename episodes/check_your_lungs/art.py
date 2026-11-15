"""Vector art for 'Check Your Lungs' (1080x1920): background, four lung illustrations,
emoji indicator, progress track. All original Cairo drawings."""
import math
import random

import cairo
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920

# ------------------------------------------------------------------ layout
TRACK_X = 470
TRACK_TOP = 330
TRACK_BOT = 1490
TRACK_W = 58           # outer width (white border included)
CPS = [470, 810, 1150, 1490]          # checkpoint centres (y)
CP_R = 48
EMOJI_R = 66
EMOJI_TOP_Y = 382                     # emoji resting position above checkpoint 1
LUNG_POS = [(200, 462), (750, 790), (204, 1140), (750, 1462)]
LUNG_S = 280                          # px per lung unit
RS = 1.3                              # supersample factor of pre-rendered lungs
LUNG_CANVAS = (520, 600)
LUNG_ORIGIN = (260, 350)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def src(cx, c, a=None):
    cx.set_source_rgba(c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * (1 if a is None else a))


def surf_to_np(s):
    s.flush()
    return np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))


def np_to_surf(arr):
    h, w = arr.shape[:2]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    surf_to_np(s)[:] = arr
    s.mark_dirty()
    return s


def with_shadow(surf, blur=10, dx=0, dy=10, alpha=0.38):
    a = surf_to_np(surf)[:, :, 3].copy()
    sh = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) * alpha
    h, w = a.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[max(0, dy):, max(0, dx):, 3] = sh[: h - max(0, dy), : w - max(0, dx)].astype(np.uint8)
    o = np_to_surf(out)
    c = cairo.Context(o)
    c.set_source_surface(surf, 0, 0)
    c.paint()
    return o


# ------------------------------------------------------------------ background
def make_background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # warm radial base, lit behind the track
    d = np.sqrt(((xx - 520) / 900) ** 2 + ((yy - 860) / 1250) ** 2)
    c_in = np.array([186, 96, 22], np.float32)
    c_mid = np.array([128, 58, 10], np.float32)
    c_out = np.array([58, 24, 5], np.float32)
    t = np.clip(d, 0, 1)[..., None]
    base = np.where(t < 0.55, c_in + (c_mid - c_in) * (t / 0.55), c_mid + (c_out - c_mid) * ((t - 0.55) / 0.45))
    # grid with glow
    grid = np.zeros((H, W), np.float32)
    gx = [int(x) for x in np.arange(-40, W + 1, 205)]
    gy = [int(y) for y in np.arange(150, H + 1, 170)]
    for x in gx:
        if 0 <= x < W:
            grid[:, max(0, x - 1):x + 2] = 1
    for y in gy:
        grid[max(0, y - 1):y + 2, :] = 1
    glow = np.asarray(Image.fromarray((grid * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255
    # grid fades a little toward the edges for depth
    fade = (1 - 0.55 * np.clip(d, 0, 1))
    line_col = np.array([255, 196, 92], np.float32)
    base = base + (line_col - base) * (grid * 0.42 * fade)[..., None]
    base = base + line_col * (glow * 0.55 * fade)[..., None] * 0.35
    # vignette + soft film grain
    vig = np.clip(1 - 0.55 * np.clip((d - 0.35) / 0.9, 0, 1) ** 1.6, 0, 1)
    base *= vig[..., None]
    rng = np.random.default_rng(3)
    base += rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
    rgb = np.clip(base, 0, 255).astype(np.uint8)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., 0] = rgb[..., 2]
    out[..., 1] = rgb[..., 1]
    out[..., 2] = rgb[..., 0]
    out[..., 3] = 255
    return np_to_surf(out)


class Particles:
    def __init__(self, n=44, seed=7):
        r = random.Random(seed)
        self.p = []
        for i in range(n):
            big = r.random() < 0.18
            self.p.append(dict(x=r.uniform(0, W), y=r.uniform(0, H), v=r.uniform(8, 26),
                               rad=r.uniform(9, 16) if big else r.uniform(2.5, 6),
                               a=r.uniform(0.25, 0.5) if big else r.uniform(0.45, 0.95),
                               ph=r.uniform(0, 6.28), wob=r.uniform(6, 22), tw=r.uniform(0.6, 1.6)))

    def draw(self, cx, t):
        for q in self.p:
            y = (q["y"] - q["v"] * t) % (H + 80) - 40
            x = q["x"] + q["wob"] * math.sin(t * 0.35 + q["ph"])
            a = q["a"] * (0.65 + 0.35 * math.sin(t * q["tw"] * 2 + q["ph"]))
            r = q["rad"]
            g = cairo.RadialGradient(x, y, 0, x, y, r * 2.4)
            g.add_color_stop_rgba(0, 1, 0.93, 0.55, a)
            g.add_color_stop_rgba(0.35, 1, 0.82, 0.3, a * 0.55)
            g.add_color_stop_rgba(1, 1, 0.7, 0.2, 0)
            cx.set_source(g)
            cx.arc(x, y, r * 2.4, 0, 2 * math.pi)
            cx.fill()


# ------------------------------------------------------------------ lungs
PINK_TOP = hexc("#FFBCC6")
PINK_BOT = hexc("#EE7F92")
OUT = hexc("#7A2433")


def lobe(cx, side, notch=0.0, round_=0.0):
    """side=-1 viewer-left lobe, +1 viewer-right. unit coordinates."""
    s = side
    r = round_
    cx.move_to(s * 0.06, -0.20)
    cx.curve_to(s * 0.07, -0.36, s * 0.13, -0.45 + r * 0.05, s * 0.21, -0.45 + r * 0.05)
    cx.curve_to(s * (0.37 + r * 0.04), -0.45 + r * 0.05, s * (0.48 + r * 0.02), -0.10, s * 0.485, 0.18)
    cx.curve_to(s * 0.49, 0.37, s * 0.42, 0.45, s * 0.30, 0.44)
    cx.curve_to(s * 0.20, 0.43, s * 0.10, 0.39, s * 0.055, 0.34)
    cx.curve_to(s * (0.03 + notch), 0.22, s * (0.035 + notch * 0.6), 0.02, s * 0.06, -0.20)
    cx.close_path()


def lobe_fill(cx, side, top=PINK_TOP, bot=PINK_BOT, notch=0.0, round_=0.0, lw=0.018):
    lobe(cx, side, notch, round_)
    g = cairo.LinearGradient(0, -0.45, 0, 0.45)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bot)
    cx.set_source(g)
    cx.fill_preserve()
    cx.save()
    cx.clip_preserve()
    # soft highlight upper-outer, shade lower-inner
    hg = cairo.RadialGradient(side * 0.30, -0.22, 0.0, side * 0.30, -0.22, 0.32)
    hg.add_color_stop_rgba(0, 1, 1, 1, 0.42)
    hg.add_color_stop_rgba(1, 1, 1, 1, 0)
    cx.set_source(hg)
    cx.paint()
    sg = cairo.RadialGradient(side * 0.10, 0.36, 0.0, side * 0.10, 0.36, 0.34)
    sg.add_color_stop_rgba(0, 0.55, 0.12, 0.2, 0.28)
    sg.add_color_stop_rgba(1, 0.55, 0.12, 0.2, 0)
    cx.set_source(sg)
    cx.paint()
    cx.restore()
    src(cx, OUT)
    cx.set_line_width(lw)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()


def trachea(cx, col=hexc("#E9586A"), ring=hexc("#B83A4D"), top=-0.62, w=0.075):
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    # outline pass then colour pass
    for lw, c in ((w + 0.036, OUT), (w, col)):
        cx.move_to(0, top)
        cx.line_to(0, -0.20)
        cx.move_to(-0.15, -0.07)
        cx.curve_to(-0.08, -0.12, -0.02, -0.16, 0, -0.20)
        cx.curve_to(0.02, -0.16, 0.08, -0.12, 0.15, -0.07)
        src(cx, c)
        cx.set_line_width(lw)
        cx.stroke()
    # cartilage rings
    src(cx, ring)
    cx.set_line_width(0.012)
    y = top + 0.05
    while y < -0.24:
        cx.move_to(-w / 2 + 0.008, y)
        cx.line_to(w / 2 - 0.008, y)
        cx.stroke()
        y += 0.055


def bronchi_tree(cx, side, col, width=0.026, depth=4, seed=1):
    r = random.Random(seed + (side > 0))

    def br(x, y, ang, ln, w, d):
        x2 = x + math.cos(ang) * ln
        y2 = y + math.sin(ang) * ln
        cx.move_to(x, y)
        cx.line_to(x2, y2)
        cx.set_line_width(w)
        cx.stroke()
        if d == 0:
            return
        spread = r.uniform(0.38, 0.6)
        br(x2, y2, ang - spread, ln * r.uniform(0.62, 0.74), w * 0.7, d - 1)
        br(x2, y2, ang + spread, ln * r.uniform(0.62, 0.74), w * 0.7, d - 1)

    src(cx, col)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    base_ang = math.pi / 2 - side * 0.95
    br(side * 0.13, -0.08, base_ang, 0.14, width, depth)


def blob(cx, x, y, r, seed, k=9, irr=0.35):
    rr = random.Random(seed)
    pts = []
    for i in range(k):
        a = i / k * 2 * math.pi
        rad = r * (1 + rr.uniform(-irr, irr))
        pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
    n = len(pts)
    cx.move_to(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        cx.curve_to(*c1, *c2, *p2)
    cx.close_path()


def smoke_puff(cx, circles, fill=hexc("#E4E4EA"), line=hexc("#8C8C99"), lw=0.016):
    for (x, y, r) in circles:
        cx.arc(x, y, r + lw, 0, 2 * math.pi)
        cx.new_sub_path()
    src(cx, line)
    cx.fill()
    for (x, y, r) in circles:
        cx.arc(x, y, r, 0, 2 * math.pi)
        cx.new_sub_path()
    src(cx, fill)
    cx.fill()
    # little shading
    for (x, y, r) in circles:
        cx.arc(x + r * 0.15, y + r * 0.2, r * 0.7, 0, 2 * math.pi)
        cx.new_sub_path()
    src(cx, hexc("#C9C9D3", 0.55))
    cx.fill()


def lung_smoky(cx):
    trachea(cx)
    lobe_fill(cx, -1)
    # viewer-right lobe: damaged, darker
    lobe_fill(cx, 1, top=hexc("#D9707E"), bot=hexc("#9E3346"), notch=0.05)
    cx.save()
    lobe(cx, -1)
    cx.clip()
    bronchi_tree(cx, -1, hexc("#D93A4E"), 0.028, 4, 3)
    rr = random.Random(11)
    for i in range(16):
        x, y = rr.uniform(-0.45, -0.1), rr.uniform(-0.3, 0.38)
        cx.arc(x, y, 0.022, 0, 2 * math.pi)
        src(cx, hexc("#BFE6F0"))
        cx.fill_preserve()
        src(cx, hexc("#6FA9BC"))
        cx.set_line_width(0.007)
        cx.stroke()
    cx.restore()
    cx.save()
    lobe(cx, 1, 0.05)
    cx.clip()
    rr = random.Random(5)
    for i in range(13):
        blob(cx, rr.uniform(0.1, 0.46), rr.uniform(-0.32, 0.4), rr.uniform(0.03, 0.06), i, 8, 0.3)
        src(cx, hexc("#5E1422", 0.8))
        cx.fill()
    cx.restore()
    # smoke draped across the right lobe
    smoke_puff(cx, [(0.30, 0.06, 0.075), (0.40, 0.01, 0.09), (0.50, 0.07, 0.07), (0.56, -0.02, 0.05)])
    smoke_puff(cx, [(0.30, -0.36, 0.06), (0.40, -0.40, 0.075), (0.50, -0.34, 0.05)])
    smoke_puff(cx, [(0.36, 0.36, 0.05), (0.46, 0.33, 0.065), (0.55, 0.37, 0.045)])


def lung_sooty(cx):
    trachea(cx, col=hexc("#3A2A2E"), ring=hexc("#1C1416"), top=-0.56)
    lobe_fill(cx, -1, top=hexc("#F7A0AE"), bot=hexc("#D9667C"))
    lobe_fill(cx, 1, top=hexc("#F7A0AE"), bot=hexc("#D9667C"), notch=0.05)
    for side in (-1, 1):
        cx.save()
        lobe(cx, side, 0.05 if side > 0 else 0)
        cx.clip()
        bronchi_tree(cx, side, hexc("#2B2024"), 0.03, 4, 8)
        rr = random.Random(20 + side)
        for i in range(11):
            blob(cx, side * rr.uniform(0.1, 0.5), rr.uniform(-0.38, 0.42), rr.uniform(0.04, 0.09), i * 3 + side, 10, 0.45)
            src(cx, hexc("#151012", 0.93))
            cx.fill()
        cx.restore()
        lobe(cx, side, 0.05 if side > 0 else 0)
        src(cx, OUT)
        cx.set_line_width(0.018)
        cx.stroke()
    # cigarette standing in the windpipe
    x0, x1 = -0.03, 0.03
    cx.rectangle(x0 - 0.008, -0.86, 0.076, 0.32)
    src(cx, OUT)
    cx.fill()
    cx.rectangle(x0, -0.85, 0.06, 0.22)
    src(cx, hexc("#FAFAF7"))
    cx.fill()
    cx.rectangle(x0, -0.63, 0.06, 0.09)
    src(cx, hexc("#E8892C"))
    cx.fill()
    for i in range(3):
        cx.arc(x0 + 0.015 + i * 0.016, -0.595 + (i % 2) * 0.02, 0.005, 0, 2 * math.pi)
        src(cx, hexc("#B5601A"))
        cx.fill()
    cx.rectangle(x0, -0.87, 0.06, 0.03)
    src(cx, hexc("#8D8A88"))
    cx.fill()
    cx.rectangle(x0 + 0.01, -0.875, 0.04, 0.012)
    src(cx, hexc("#FF6A1A"))
    cx.fill()


CIG_TIP = (0.0, -0.88)   # unit coords of the cigarette tip (for the animated wisp)


def lung_clean(cx):
    trachea(cx)
    lobe_fill(cx, -1)
    lobe_fill(cx, 1, notch=0.05)
    for side in (-1, 1):
        cx.save()
        lobe(cx, side, 0.05 if side > 0 else 0)
        cx.clip()
        bronchi_tree(cx, side, hexc("#E14A5E"), 0.03, 4, 2)
        # soft lobe fissure
        cx.move_to(side * 0.47, -0.02)
        cx.curve_to(side * 0.35, 0.05, side * 0.25, 0.15, side * 0.16, 0.30)
        src(cx, hexc("#D86A7E", 0.7))
        cx.set_line_width(0.012)
        cx.stroke()
        cx.restore()


def lung_cute(cx):
    # flexing arms (behind the lobes)
    arm = hexc("#4A2A2A")
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    for s in (-1, 1):
        for lw, c in ((0.09, OUT), (0.062, arm)):
            cx.move_to(s * 0.40, 0.06)
            cx.curve_to(s * 0.58, 0.10, s * 0.66, 0.02, s * 0.62, -0.10)
            src(cx, c)
            cx.set_line_width(lw)
            cx.stroke()
        # bicep bump + fist
        cx.arc(s * 0.555, 0.03, 0.055, 0, 2 * math.pi)
        src(cx, arm)
        cx.fill()
        cx.arc(s * 0.62, -0.14, 0.055, 0, 2 * math.pi)
        src(cx, OUT)
        cx.fill()
        cx.arc(s * 0.62, -0.14, 0.04, 0, 2 * math.pi)
        src(cx, arm)
        cx.fill()
    trachea(cx, col=hexc("#E9D9CF"), ring=hexc("#B9A396"), top=-0.66, w=0.07)
    top, bot = hexc("#FFB2BE"), hexc("#F27A8E")
    lobe_fill(cx, -1, top, bot, round_=0.6)
    lobe_fill(cx, 1, top, bot, notch=0.02, round_=0.6)
    for s in (-1, 1):
        ex = s * 0.27
        for dx in (-0.065, 0.065):
            cx.save()
            cx.translate(ex + dx, 0.02)
            cx.scale(1, 1.25)
            cx.arc(0, 0, 0.032, 0, 2 * math.pi)
            cx.restore()
            src(cx, hexc("#24161A"))
            cx.fill()
            cx.arc(ex + dx + 0.01, 0.005, 0.011, 0, 2 * math.pi)
            src(cx, (1, 1, 1, 1))
            cx.fill()
        # blush
        for dx in (-0.12, 0.12):
            cx.save()
            cx.translate(ex + dx, 0.09)
            cx.scale(1.5, 1)
            cx.arc(0, 0, 0.028, 0, 2 * math.pi)
            cx.restore()
            src(cx, hexc("#FF6F8A", 0.55))
            cx.fill()
        # smile
        cx.move_to(ex - 0.04, 0.10)
        cx.curve_to(ex - 0.02, 0.15, ex + 0.02, 0.15, ex + 0.04, 0.10)
        src(cx, hexc("#24161A"))
        cx.set_line_width(0.016)
        cx.stroke()


LUNG_FUNCS = [lung_smoky, lung_sooty, lung_clean, lung_cute]


def make_lung(i):
    w, h = LUNG_CANVAS
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cx = cairo.Context(s)
    cx.translate(*LUNG_ORIGIN)
    cx.scale(LUNG_S * RS * 1.1, LUNG_S * RS)
    # soft ground shadow (same for all four)
    g = cairo.RadialGradient(0, 0.5, 0, 0, 0.5, 0.45)
    g.add_color_stop_rgba(0, 0.18, 0.05, 0.01, 0.42)
    g.add_color_stop_rgba(1, 0.18, 0.05, 0.01, 0)
    cx.save()
    cx.translate(0, 0.5)
    cx.scale(1, 0.16)
    cx.translate(0, -0.5)
    cx.set_source(g)
    cx.arc(0, 0.5, 0.45, 0, 2 * math.pi)
    cx.fill()
    cx.restore()
    LUNG_FUNCS[i](cx)
    return with_shadow(s, blur=9, dy=12, alpha=0.4)


# ------------------------------------------------------------------ emoji
FACE_DARK = hexc("#5B330C")


def _closed_eye(cx, x, y, w, kind, R):
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.set_line_width(0.07 * R)
    src(cx, FACE_DARK)
    if kind == "calm":       # relaxed closed eyes (U)
        cx.move_to(x - w, y - 0.02 * R)
        cx.curve_to(x - w * 0.5, y + 0.11 * R, x + w * 0.5, y + 0.11 * R, x + w, y - 0.02 * R)
    elif kind == "flat":     # tight closed lines
        cx.move_to(x - w, y + 0.02 * R)
        cx.line_to(x + w, y + 0.02 * R)
    elif kind == "squeeze":  # > <
        d = 1 if x < 0 else -1
        cx.move_to(x - d * w, y - 0.09 * R)
        cx.line_to(x + d * w * 0.9, y + 0.01 * R)
        cx.line_to(x - d * w, y + 0.11 * R)
    elif kind == "happy":    # ^
        cx.move_to(x - w, y + 0.05 * R)
        cx.curve_to(x - w * 0.5, y - 0.1 * R, x + w * 0.5, y - 0.1 * R, x + w, y + 0.05 * R)
    cx.stroke()


def _drop(cx, x, y, s, a):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(0, -1.0)
    cx.curve_to(0.25, -0.5, 0.62, -0.05, 0.62, 0.32)
    cx.curve_to(0.62, 0.72, 0.3, 0.95, 0, 0.95)
    cx.curve_to(-0.3, 0.95, -0.62, 0.72, -0.62, 0.32)
    cx.curve_to(-0.62, -0.05, -0.25, -0.5, 0, -1.0)
    cx.close_path()
    g = cairo.LinearGradient(0, -1, 0, 1)
    g.add_color_stop_rgba(0, 0.75, 0.93, 1, a)
    g.add_color_stop_rgba(1, 0.33, 0.68, 0.98, a)
    cx.set_source(g)
    cx.fill_preserve()
    cx.set_source_rgba(0.12, 0.38, 0.7, a)
    cx.set_line_width(0.1)
    cx.stroke()
    cx.arc(-0.2, 0.35, 0.16, 0, 2 * math.pi)
    cx.set_source_rgba(1, 1, 1, 0.8 * a)
    cx.fill()
    cx.restore()


def draw_emoji(cx, x, y, R, e):
    """e: kind ('gasp'|'hold'|'relief'), mouth, blink, strain, puff, red, sweat, eye, sq."""
    # soft drop shadow
    g = cairo.RadialGradient(x + 3, y + 12, R * 0.6, x + 3, y + 12, R * 1.25)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.38)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cx.set_source(g)
    cx.arc(x + 3, y + 12, R * 1.25, 0, 2 * math.pi)
    cx.fill()
    cx.save()
    cx.translate(x, y)
    puff = e.get("puff", 0)
    sq = e.get("sq", 1.0)
    cx.scale((1 + 0.045 * puff) / math.sqrt(sq), sq)
    cx.arc(0, 0, R, 0, 2 * math.pi)
    g = cairo.RadialGradient(-0.3 * R, -0.38 * R, 0.05 * R, 0, 0, R * 1.05)
    g.add_color_stop_rgba(0, 1.0, 0.95, 0.6, 1)
    g.add_color_stop_rgba(0.5, 1.0, 0.80, 0.22, 1)
    g.add_color_stop_rgba(1, 0.95, 0.58, 0.06, 1)
    cx.set_source(g)
    cx.fill_preserve()
    red = e.get("red", 0)
    if red > 0:
        rg = cairo.RadialGradient(0, 0.55 * R, 0, 0, 0.3 * R, R * 1.25)
        rg.add_color_stop_rgba(0, 1.0, 0.32, 0.22, 0.8 * red)
        rg.add_color_stop_rgba(1, 1.0, 0.32, 0.22, 0.0)
        cx.save()
        cx.clip_preserve()
        cx.set_source(rg)
        cx.paint()
        cx.restore()
    cx.set_source_rgba(0.72, 0.38, 0.02, 0.7)
    cx.set_line_width(0.045 * R)
    cx.stroke()
    # glossy highlight
    cx.save()
    cx.translate(-0.33 * R, -0.55 * R)
    cx.rotate(-0.45)
    cx.scale(0.36 * R, 0.16 * R)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()
    cx.set_source_rgba(1, 1, 1, 0.5)
    cx.fill()

    kind = e["kind"]
    strain = e.get("strain", 0)
    # cheeks
    if kind == "hold" or kind == "relief":
        for s in (-1, 1):
            cx.save()
            cx.translate(s * 0.52 * R, 0.2 * R)
            cx.scale(0.2 * R * (1 + 0.25 * puff), 0.13 * R * (1 + 0.25 * puff))
            cx.arc(0, 0, 1, 0, 2 * math.pi)
            cx.restore()
            cx.set_source_rgba(1, 0.42, 0.4, 0.22 + 0.3 * puff)
            cx.fill()
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    if kind == "gasp":
        blink = e.get("blink", 0)
        for s in (-1, 1):
            cx.save()
            cx.translate(s * 0.31 * R, -0.13 * R)
            cx.scale(0.105 * R, max(0.012, 0.165 * (1 - blink)) * R)
            cx.arc(0, 0, 1, 0, 2 * math.pi)
            cx.restore()
            src(cx, FACE_DARK)
            cx.fill()
            if blink < 0.5:
                cx.arc(s * 0.31 * R + 0.035 * R, -0.19 * R, 0.035 * R, 0, 2 * math.pi)
                cx.set_source_rgba(1, 1, 1, 0.85)
                cx.fill()
            # raised brows
            cx.move_to(s * 0.43 * R, -0.42 * R)
            cx.curve_to(s * 0.36 * R, -0.52 * R, s * 0.24 * R, -0.52 * R, s * 0.17 * R, -0.44 * R)
            src(cx, FACE_DARK)
            cx.set_line_width(0.055 * R)
            cx.stroke()
        m = e.get("mouth", 0.5)
        cx.save()
        cx.translate(0, 0.40 * R)
        cx.scale((0.15 + 0.05 * m) * R, (0.17 + 0.1 * m) * R)
        cx.arc(0, 0, 1, 0, 2 * math.pi)
        cx.restore()
        src(cx, hexc("#4A2208"))
        cx.fill()
        cx.save()
        cx.translate(0, (0.40 + 0.1 * (0.17 + 0.1 * m)) * R)
        cx.scale((0.09 + 0.03 * m) * R, (0.07 + 0.03 * m) * R)
        cx.arc(0, 0.6, 1, math.pi, 2 * math.pi)
        cx.restore()
        src(cx, hexc("#C8475A"))
        cx.fill()
    elif kind == "hold":
        eye = e.get("eye", "calm")
        for s in (-1, 1):
            _closed_eye(cx, s * 0.31 * R, -0.12 * R, 0.13 * R, eye, R)
            # brows: flat -> worried (inner end up)
            k = min(1, strain * 1.2)
            cx.move_to(s * 0.45 * R, (-0.40 + 0.03 * k) * R)
            cx.line_to(s * 0.18 * R, (-0.40 - 0.10 * k) * R)
            src(cx, FACE_DARK)
            cx.set_line_width(0.055 * R)
            cx.stroke()
        # pressed lips: wavier as strain rises
        cx.set_line_width(0.065 * R)
        amp = 0.035 * R * min(1, max(0, strain - 0.3) / 0.6)
        w = 0.17 * R
        cx.move_to(-w, 0.42 * R)
        n = 24
        for i in range(1, n + 1):
            u = i / n
            xx = -w + 2 * w * u
            yy = 0.42 * R + amp * math.sin(u * math.pi * 3) - 0.025 * R * math.sin(u * math.pi) * (1 - strain)
            cx.line_to(xx, yy)
        src(cx, FACE_DARK)
        cx.stroke()
    elif kind == "relief":
        for s in (-1, 1):
            _closed_eye(cx, s * 0.31 * R, -0.12 * R, 0.13 * R, "happy", R)
        cx.move_to(-0.30 * R, 0.22 * R)
        cx.curve_to(-0.26 * R, 0.62 * R, 0.26 * R, 0.62 * R, 0.30 * R, 0.22 * R)
        cx.close_path()
        src(cx, hexc("#4A2208"))
        cx.fill()
        cx.save()
        cx.move_to(-0.30 * R, 0.22 * R)
        cx.curve_to(-0.26 * R, 0.62 * R, 0.26 * R, 0.62 * R, 0.30 * R, 0.22 * R)
        cx.close_path()
        cx.clip()
        cx.arc(0, 0.58 * R, 0.17 * R, 0, 2 * math.pi)
        src(cx, hexc("#E05A6E"))
        cx.fill()
        cx.rectangle(-0.3 * R, 0.2 * R, 0.6 * R, 0.07 * R)
        cx.set_source_rgba(1, 1, 1, 1)
        cx.fill()
        cx.restore()
    cx.restore()
    sw = e.get("sweat", 0)
    if sw > 0:
        _drop(cx, x + 0.72 * R, y - 0.42 * R + 0.06 * R * math.sin(e.get("t", 0) * 2), 0.17 * R * min(1, sw * 1.6), min(1, sw * 2))
    if sw > 0.55:
        k = (sw - 0.55) / 0.45
        _drop(cx, x - 0.78 * R, y - 0.18 * R, 0.13 * R * min(1, k * 1.6), min(1, k * 2))


def sparkle_star(cx, x, y, r, a, col=(1, 0.95, 0.65)):
    cx.move_to(x, y - r)
    cx.curve_to(x + r * 0.12, y - r * 0.12, x + r * 0.12, y - r * 0.12, x + r, y)
    cx.curve_to(x + r * 0.12, y + r * 0.12, x + r * 0.12, y + r * 0.12, x, y + r)
    cx.curve_to(x - r * 0.12, y + r * 0.12, x - r * 0.12, y + r * 0.12, x - r, y)
    cx.curve_to(x - r * 0.12, y - r * 0.12, x - r * 0.12, y - r * 0.12, x, y - r)
    cx.close_path()
    cx.set_source_rgba(*col, a)
    cx.fill()

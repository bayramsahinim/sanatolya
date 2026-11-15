"""2.5D drawing kit for the vertical short: lighting helpers + round-head character rig.

Everything is vector (Cairo). Depth comes from gradients, terminator shadows, rim light, contact shadows,
additive glows, blurred background layers and post (vignette, grain, grade)."""
import math

import cairo
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920
FPS = 30
INK = (0.10, 0.08, 0.12)
JP_FONT = "IPAGothic"
FONT = "Montserrat ExtraBold"


# ---------------------------------------------------------------- colour / easing
def hx(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def shade(c, k):
    c = c if len(c) == 4 else (*c, 1.0)
    if k < 0:
        return (c[0] * (1 + k), c[1] * (1 + k), c[2] * (1 + k), c[3])
    return (c[0] + (1 - c[0]) * k, c[1] + (1 - c[1]) * k, c[2] + (1 - c[2]) * k, c[3])


def mixc(a, b, t):
    a = a if len(a) == 4 else (*a, 1.0)
    b = b if len(b) == 4 else (*b, 1.0)
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def alpha(c, a):
    c = c if len(c) == 4 else (*c, 1.0)
    return (c[0], c[1], c[2], c[3] * a)


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= b)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eio(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    return 1 - (1 - clamp(x)) ** 3


def back_out(x, s=1.5):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def src(cx, c):
    cx.set_source_rgba(*(c if len(c) == 4 else (*c, 1.0)))


# ---------------------------------------------------------------- primitives
def lin(cx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(c if len(c) == 4 else (*c, 1.0)))
    cx.set_source(g)


def rad(cx, x, y, r0, r1, stops, x0=None, y0=None):
    g = cairo.RadialGradient(x if x0 is None else x0, y if y0 is None else y0, r0, x, y, r1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(c if len(c) == 4 else (*c, 1.0)))
    cx.set_source(g)


def rrect(cx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cx.new_sub_path()
    cx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cx.close_path()


def poly(cx, pts):
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    cx.close_path()


def ellipse(cx, x, y, rx, ry):
    cx.save()
    cx.translate(x, y)
    cx.scale(rx, ry)
    cx.new_sub_path()
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()


def ink(cx, w, c=INK):
    src(cx, c)
    cx.set_line_width(w)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()


def fill_ink(cx, col, w, c=INK):
    src(cx, col)
    cx.fill_preserve()
    ink(cx, w, c)


def glow(cx, x, y, r, col, a=1.0, sx=1.0, sy=1.0):
    """Additive soft light."""
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    cx.translate(x, y)
    cx.scale(sx, sy)
    rad(cx, 0, 0, 0, r, [(0, alpha(col, a)), (0.35, alpha(col, a * 0.45)), (1, alpha(col, 0))])
    cx.arc(0, 0, r, 0, 2 * math.pi)
    cx.fill()
    cx.restore()


def contact_shadow(cx, x, y, rx, ry, a=0.45):
    cx.save()
    cx.translate(x, y)
    cx.scale(rx, ry)
    rad(cx, 0, 0, 0, 1, [(0, (0, 0, 0, a)), (0.6, (0, 0, 0, a * 0.5)), (1, (0, 0, 0, 0))])
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.fill()
    cx.restore()


def light_cone(cx, x, y, w0, w1, h, col, a=0.25):
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    lin(cx, x, y, x, y + h, [(0, alpha(col, a)), (1, alpha(col, 0))])
    poly(cx, [(x - w0 / 2, y), (x + w0 / 2, y), (x + w1 / 2, y + h), (x - w1 / 2, y + h)])
    cx.fill()
    cx.restore()


def text(cx, s, x, y, size, col=(1, 1, 1, 1), font=FONT, anchor="c", outline=0, ocol=INK, bold=False,
         spacing=0.0):
    cx.save()
    cx.select_font_face(font, cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    if spacing:
        widths = [cx.text_extents(ch).x_advance for ch in s]
        tw = sum(widths) + spacing * (len(s) - 1)
    else:
        tw = cx.text_extents(s).x_advance
    x0 = x - tw / 2 if anchor == "c" else (x - tw if anchor == "r" else x)
    cx.new_path()
    if spacing:
        xx = x0
        for ch, wch in zip(s, widths):
            cx.move_to(xx, y)
            cx.text_path(ch)
            xx += wch + spacing
    else:
        cx.move_to(x0, y)
        cx.text_path(s)
    if outline:
        src(cx, ocol)
        cx.set_line_width(outline)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke_preserve()
    src(cx, col)
    cx.fill()
    cx.restore()
    return tw


def text_w(cx, s, size, font=FONT):
    cx.save()
    cx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    w = cx.text_extents(s).x_advance
    cx.restore()
    return w


# ---------------------------------------------------------------- surfaces
def surface(w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def arr(s):
    s.flush()
    return np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, s.get_data(),
                      strides=(s.get_stride(), 4, 1))


def blurred(s, r):
    """Gaussian-blurred copy of a (premultiplied) surface."""
    a = arr(s).copy()
    im = Image.fromarray(a, "RGBA").filter(ImageFilter.GaussianBlur(r))
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, s.get_width(), s.get_height())
    arr(out)[:] = np.asarray(im)
    out.mark_dirty()
    return out


_layer_cache = {}


def cached_layer(key, fn, blur=0, w=W, h=H):
    """Draw a static layer once (optionally blurred for depth of field) and reuse it."""
    if key not in _layer_cache:
        s, c = surface(w, h)
        fn(c)
        if blur:
            s = blurred(s, blur)
        _layer_cache[key] = s
    return _layer_cache[key]


def paint_layer(cx, s, x=0, y=0, a=1.0):
    cx.set_source_surface(s, x, y)
    cx.paint_with_alpha(a)


# ---------------------------------------------------------------- camera
def camera(cx, zoom=1.0, fx=W / 2, fy=H / 2, rot=0.0, ox=0.0, oy=0.0):
    """Focus point (fx, fy) in scene space lands on screen centre (+ offset) at the given zoom."""
    cx.translate(W / 2 + ox, H / 2 + oy)
    if rot:
        cx.rotate(rot)
    cx.scale(zoom, zoom)
    cx.translate(-fx, -fy)


def handheld(t, amt=1.0, seed=0):
    """Subtle organic drift (px, px, rad)."""
    f = lambda k, p: math.sin(t * k + p + seed)
    return (amt * (3.0 * f(0.9, 0.3) + 1.6 * f(2.1, 1.7)),
            amt * (2.6 * f(0.7, 2.2) + 1.2 * f(1.9, 0.4)),
            amt * 0.0016 * f(0.5, 1.1))


# ---------------------------------------------------------------- characters
SKIN = hx("#f1c7a1")
CAST = {
    "son": dict(body=hx("#283553"), sleeve=hx("#25304b"), hair=hx("#1c1a22"), tie=hx("#2e7050"),
                shirt=hx("#eef0f2"), legs=hx("#1d2236")),
    "mom": dict(body=hx("#6e3a63"), sleeve=hx("#663559"), hair=hx("#bdb8bd"), shirt=hx("#efe4cf"),
                legs=hx("#3d2c3b"), glasses=True),
    "rep": dict(body=hx("#3c4047"), sleeve=hx("#383c43"), hair=hx("#24242a"), cap=hx("#33363c"),
                shirt=hx("#b9bcc2"), legs=hx("#2a2c31"), stache=True),
    "mover": dict(body=hx("#3a3e45"), sleeve=hx("#363a41"), hair=hx("#24242a"), cap=hx("#30333a"),
                  shirt=hx("#4a4f57"), legs=hx("#2a2c31"), mask=True, gloves=True),
    "det": dict(body=hx("#b38f5c"), sleeve=hx("#a9854f"), hair=hx("#9d9a9e"), shirt=hx("#e9e6df"),
                legs=hx("#4a4a50"), glasses=True, trench=True, tie=hx("#6b2f2f")),
    "cop": dict(body=hx("#1f2b4a"), sleeve=hx("#1c2744"), hair=hx("#1c1a22"), cap=hx("#1a2440"),
                shirt=hx("#bcd0e6"), legs=hx("#1a2238"), badge=True, tie=hx("#1a2033")),
}


def _limb(cx, pts, width, col, ow):
    cx.new_path()
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    src(cx, INK)
    cx.set_line_width(width + 2 * ow)
    cx.stroke_preserve()
    src(cx, col)
    cx.set_line_width(width)
    cx.stroke()


def _arm(sh, a, e, L):
    """Shoulder point, upper-arm angle a (deg from straight down, + = outward to screen-right),
    elbow bend e (deg)."""
    a1 = math.radians(a)
    el = (sh[0] + math.sin(a1) * L, sh[1] + math.cos(a1) * L)
    a2 = a1 + math.radians(e)
    hd = (el[0] + math.sin(a2) * L * 0.95, el[1] + math.cos(a2) * L * 0.95)
    return el, hd


def person(cx, x, y, h, kind, pose=None, light=(1.0, hx("#ffd9a0")), t=0.0):
    """Draw a character with feet at (x, y), total height h.

    pose keys: arms=(la, le, ra, re) degrees; face='front'|'left'|'right'|'back'; eyes='dot'|'worried'|
    'closed'|'wide'|'sleepy'; look=(dx,dy); mouth='flat'|'frown'|'wavy'|'o'|'smile'|'smirk';
    brow='none'|'sad'|'angry'|'flat'; sweat=0..1; legs=True; lean=deg; hold=callable(cx, hand_l, hand_r, s)."""
    p = dict(arms=(10, 8, -10, -8), face="front", eyes="dot", look=(0, 0), mouth="flat", brow="none",
             sweat=0.0, legs=True, lean=0.0, hold=None, blink=None, squash=0.0)
    p.update(pose or {})
    C = CAST[kind]
    s = h / 100.0  # unit
    ow = 2.6 * s  # outline width
    lx, lcol = light
    cx.save()
    cx.translate(x, y)
    if p["lean"]:
        cx.rotate(math.radians(p["lean"]))
    # contact shadow
    if p["legs"]:
        contact_shadow(cx, 0, 0, 26 * s, 6 * s, 0.5)
    by = -30 * s  # body bottom
    body_h = 40 * s * (1 - p["squash"])
    body_w = 30 * s
    head_r = 19 * s
    hy = by - body_h - head_r * 0.62
    face = p["face"]
    fdx = {"front": 0, "left": -0.28, "right": 0.28, "back": 0}[face]
    # legs
    if p["legs"]:
        for sx_ in (-1, 1):
            lx0 = sx_ * 7 * s
            _limb(cx, [(lx0, by - 2 * s), (lx0, -3 * s)], 4.2 * s, C["legs"], ow * 0.7)
            # shoe
            ellipse(cx, lx0 + sx_ * 1.5 * s + fdx * 6 * s, -2.6 * s, 6 * s, 3.2 * s)
            fill_ink(cx, hx("#1a1a1f"), ow * 0.7)
    sh_y = by - body_h * 0.82
    L = 14 * s
    la, le, ra, re_ = p["arms"]
    shl = (-body_w * 0.42, sh_y)
    shr = (body_w * 0.42, sh_y)
    # back arm drawn behind when facing side
    arms_behind = []
    el_l, hd_l = _arm(shl, -la if False else -abs(la) if la >= 0 else abs(la), -le, L)
    # simpler: left arm angle measured outward to the left
    el_l, hd_l = _arm(shl, -la, -le, L)
    el_r, hd_r = _arm(shr, -ra, -re_, L)
    sleeve = C["sleeve"]
    if face == "left":
        arms_behind.append((shr, el_r, hd_r))
    elif face == "right":
        arms_behind.append((shl, el_l, hd_l))
    for a_ in arms_behind:
        _limb(cx, list(a_), 6.4 * s, shade(sleeve, -0.25), ow * 0.8)
        cx.arc(a_[2][0], a_[2][1], 3.6 * s, 0, 2 * math.pi)
        fill_ink(cx, shade(hx("#f4f4f4") if C.get("gloves") else SKIN, -0.2), ow * 0.6)
    # body
    cx.save()
    ellipse(cx, 0, by - body_h / 2, body_w / 2, body_h / 2)
    path = cx.copy_path()
    lin(cx, -body_w / 2, 0, body_w / 2, 0, [(0, shade(C["body"], 0.12 if lx < 0 else -0.25)),
                                             (0.5, C["body"]),
                                             (1, shade(C["body"], 0.12 if lx > 0 else -0.25))])
    cx.fill_preserve()
    cx.clip()
    # body details
    if face != "back":
        nx = fdx * body_w * 0.5
        top = by - body_h
        if C.get("trench"):
            poly(cx, [(nx - 9 * s, top), (nx + 9 * s, top), (nx, top + 18 * s)])
            src(cx, C["shirt"])
            cx.fill()
            _limb(cx, [(nx, top + 2 * s), (nx, top + 15 * s)], 3 * s, C["tie"], 0)
            for sx_ in (-1, 1):
                poly(cx, [(nx + sx_ * 9 * s, top), (nx + sx_ * 2 * s, top + 20 * s), (nx + sx_ * 12 * s, top + 6 * s)])
                src(cx, shade(C["body"], -0.12))
                cx.fill()
            cx.rectangle(-body_w, by - body_h * 0.38, body_w * 2, 4 * s)
            src(cx, shade(C["body"], -0.3))
            cx.fill()
        elif kind in ("son", "cop", "rep", "mover"):
            poly(cx, [(nx - 7 * s, top), (nx + 7 * s, top), (nx, top + 15 * s)])
            src(cx, C["shirt"])
            cx.fill()
            if kind in ("son", "cop"):
                poly(cx, [(nx - 1.8 * s, top + 3 * s), (nx + 1.8 * s, top + 3 * s), (nx + 2.6 * s, top + 22 * s),
                          (nx, top + 25 * s), (nx - 2.6 * s, top + 22 * s)])
                src(cx, C["tie"])
                cx.fill()
            if kind in ("rep", "mover"):
                for k in range(3):
                    cx.arc(nx, top + 18 * s + k * 7 * s, 1.1 * s, 0, 2 * math.pi)
                    src(cx, shade(C["body"], -0.4))
                    cx.fill()
            if kind == "cop":
                rrect(cx, nx - 11 * s, top + 9 * s, 5 * s, 4 * s, 1 * s)
                src(cx, hx("#d9b45a"))
                cx.fill()
        elif kind == "mom":
            poly(cx, [(nx - 6 * s, top), (nx + 6 * s, top), (nx, top + 10 * s)])
            src(cx, C["shirt"])
            cx.fill()
            for k in range(3):
                cx.arc(nx + 1.5 * s, top + 14 * s + k * 7 * s, 1.0 * s, 0, 2 * math.pi)
                src(cx, shade(C["body"], 0.35))
                cx.fill()
    # terminator shadow + rim
    ellipse(cx, -lx * body_w * 0.38, by - body_h / 2 + body_h * 0.08, body_w * 0.62, body_h * 0.62)
    cx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cx.rectangle(-body_w * 2, -body_h * 4, body_w * 4, body_h * 6)
    src(cx, (0.03, 0.02, 0.08, 0.22))
    cx.fill()
    cx.set_fill_rule(cairo.FILL_RULE_WINDING)
    cx.restore()
    cx.new_path()
    cx.append_path(path)
    ink(cx, ow)
    # rim light on body
    cx.save()
    cx.append_path(path)
    cx.clip()
    ellipse(cx, -lx * 2.4 * s, by - body_h / 2, body_w / 2, body_h / 2)
    cx.set_line_width(5 * s)
    src(cx, alpha(lcol, 0.0))
    cx.restore()
    # front arms
    fronts = []
    if face != "left":
        fronts.append((shr, el_r, hd_r))
    if face != "right":
        fronts.append((shl, el_l, hd_l))
    hand_col = hx("#f4f4f4") if C.get("gloves") else SKIN
    for a_ in fronts:
        _limb(cx, list(a_), 6.4 * s, sleeve, ow * 0.8)
        cx.arc(a_[2][0], a_[2][1], 3.6 * s, 0, 2 * math.pi)
        fill_ink(cx, hand_col, ow * 0.6)
    # head
    _head(cx, 0, hy, head_r, kind, C, p, s, ow, lx, lcol, t)
    if p["hold"]:
        p["hold"](cx, hd_l, hd_r, s)
    cx.restore()
    return {"head": (x, y + hy), "head_r": head_r, "hand_l": (x + hd_l[0], y + hd_l[1]),
            "hand_r": (x + hd_r[0], y + hd_r[1])}


def _head(cx, x, y, r, kind, C, p, s, ow, lx, lcol, t):
    face = p["face"]
    fdx = {"front": 0, "left": -0.30, "right": 0.30, "back": 0}[face] * r
    # hair back (mom bun)
    if kind == "mom":
        cx.arc(x - fdx * 0.6, y - r * 0.95, r * 0.36, 0, 2 * math.pi)
        fill_ink(cx, C["hair"], ow)
    cx.arc(x, y, r, 0, 2 * math.pi)
    hp = cx.copy_path()
    rad(cx, x, y, r * 0.05, r * 1.15,
        [(0, shade(SKIN, 0.30)), (0.55, SKIN), (1, shade(SKIN, -0.28))],
        x0=x + lx * r * 0.35, y0=y - r * 0.45)
    cx.fill()
    cx.save()
    cx.append_path(hp)
    cx.clip()
    # terminator
    cx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cx.arc(x + lx * r * 0.32, y - r * 0.12, r * 1.08, 0, 2 * math.pi)
    cx.rectangle(x - 3 * r, y - 3 * r, 6 * r, 6 * r)
    src(cx, (0.20, 0.05, 0.12, 0.25))
    cx.fill()
    cx.set_fill_rule(cairo.FILL_RULE_WINDING)
    # cheeks
    if face != "back":
        for sx_ in (-1, 1):
            glow(cx, x + fdx + sx_ * r * 0.55, y + r * 0.3, r * 0.22, hx("#ff8a7a"), 0.10)
    # hair
    _hair(cx, x, y, r, kind, C, face, fdx, s)
    # rim light
    cx.arc(x - lx * r * 0.12, y + r * 0.04, r, 0, 2 * math.pi)
    cx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cx.arc(x, y, r * 1.4, 0, 2 * math.pi)
    cx.restore()
    cx.new_path()
    # rim as stroked arc on light side
    cx.save()
    cx.append_path(hp)
    cx.clip()
    cx.new_path()
    a0 = 0 if lx > 0 else math.pi
    cx.arc(x, y, r - 1.5 * s, a0 - 1.1, a0 + 0.6) if lx > 0 else cx.arc(x, y, r - 1.5 * s, a0 - 0.6, a0 + 1.1)
    src(cx, alpha(lcol, 0.55))
    cx.set_line_width(3.2 * s)
    cx.stroke()
    cx.restore()
    cx.append_path(hp)
    ink(cx, ow)
    if face == "back":
        return
    # face features
    ex = r * 0.30
    ey = y + r * 0.02
    fx = x + fdx
    lkx, lky = p["look"]
    if p["mask"] if "mask" in p else C.get("mask"):
        pass
    eyes = p["eyes"]
    blink = p.get("blink")
    if blink is None:
        ph = (t * 0.31 + hash(kind) % 7 * 0.13) % 1.0
        blink = ph < 0.035
    for sx_ in (-1, 1):
        cxp = fx + sx_ * ex + lkx * r * 0.08
        cyp = ey + lky * r * 0.06
        if eyes == "closed" or blink:
            cx.new_path()
            cx.arc(cxp, cyp - 1 * s, r * 0.1, 0.2, math.pi - 0.2)
            ink(cx, 2.2 * s)
        elif eyes == "sleepy":
            ellipse(cx, cxp, cyp + 1 * s, r * 0.085, r * 0.05)
            src(cx, INK)
            cx.fill()
        else:
            er = r * (0.105 if eyes == "wide" else 0.085)
            ellipse(cx, cxp, cyp, er, er * 1.25)
            src(cx, INK)
            cx.fill()
            cx.arc(cxp - er * 0.3, cyp - er * 0.45, er * 0.32, 0, 2 * math.pi)
            src(cx, (1, 1, 1, 0.9))
            cx.fill()
    # brows
    br = p["brow"]
    if br != "none":
        for sx_ in (-1, 1):
            bx = fx + sx_ * ex
            by_ = ey - r * 0.27
            if br == "sad":
                pts = [(bx - sx_ * r * 0.13, by_ - r * 0.05), (bx + sx_ * r * 0.12, by_ + r * 0.04)]
                pts = [(bx - r * 0.12, by_ + (r * 0.04 if sx_ < 0 else -r * 0.05)),
                       (bx + r * 0.12, by_ + (-r * 0.05 if sx_ < 0 else r * 0.04))]
            elif br == "angry":
                pts = [(bx - r * 0.12, by_ + (-r * 0.04 if sx_ < 0 else r * 0.05)),
                       (bx + r * 0.12, by_ + (r * 0.05 if sx_ < 0 else -r * 0.04))]
            else:
                pts = [(bx - r * 0.11, by_), (bx + r * 0.11, by_)]
            cx.new_path()
            cx.move_to(*pts[0])
            cx.line_to(*pts[1])
            ink(cx, 2.6 * s)
    # glasses
    if C.get("glasses"):
        for sx_ in (-1, 1):
            cx.new_path()
            cx.arc(fx + sx_ * ex, ey, r * 0.2, 0, 2 * math.pi)
            ink(cx, 2.2 * s if kind == "mom" else 3.4 * s)
        cx.new_path()
        cx.move_to(fx - ex + r * 0.2, ey)
        cx.line_to(fx + ex - r * 0.2, ey)
        ink(cx, 2 * s)
    # mustache
    if C.get("stache"):
        cx.new_path()
        cx.move_to(fx - r * 0.24, y + r * 0.42)
        cx.curve_to(fx - r * 0.1, y + r * 0.30, fx + r * 0.1, y + r * 0.30, fx + r * 0.24, y + r * 0.42)
        ink(cx, 3.2 * s, hx("#3a3236"))
    # mask
    if C.get("mask"):
        cx.save()
        cx.arc(x, y, r - ow * 0.4, 0, 2 * math.pi)
        cx.clip()
        rrect(cx, fx - r * 0.6, y + r * 0.2, r * 1.2, r * 0.62, r * 0.28)
        lin(cx, 0, y + r * 0.2, 0, y + r, [(0, hx("#e6e9ee")), (1, hx("#b9bfc8"))])
        cx.fill_preserve()
        ink(cx, 1.6 * s)
        cx.restore()
        return
    mo = p["mouth"]
    my = y + r * 0.45
    cx.new_path()
    if mo == "flat":
        cx.move_to(fx - r * 0.1, my)
        cx.line_to(fx + r * 0.1, my)
        ink(cx, 2.4 * s)
    elif mo == "frown":
        cx.arc_negative(fx, my + r * 0.16, r * 0.15, -0.5, -math.pi + 0.5)
        ink(cx, 2.4 * s)
    elif mo == "smile":
        cx.arc(fx, my - r * 0.12, r * 0.17, 0.45, math.pi - 0.45)
        ink(cx, 2.4 * s)
    elif mo == "smirk":
        cx.move_to(fx - r * 0.1, my)
        cx.curve_to(fx, my + r * 0.04, fx + r * 0.1, my, fx + r * 0.16, my - r * 0.06)
        ink(cx, 2.4 * s)
    elif mo == "o":
        ellipse(cx, fx, my + r * 0.02, r * 0.07, r * 0.09)
        src(cx, hx("#3a1a22"))
        cx.fill()
    elif mo == "wavy":
        n = 4
        w = r * 0.3
        cx.move_to(fx - w / 2, my)
        for k in range(n):
            x0 = fx - w / 2 + w * (k + 0.5) / n
            cx.line_to(x0, my + (-1) ** k * r * 0.045)
        cx.line_to(fx + w / 2, my)
        ink(cx, 2.2 * s)
    # sweat
    if p["sweat"] > 0:
        sx0, sy0 = x + r * 0.78, y - r * 0.35 + (1 - p["sweat"]) * -r * 0.2
        cx.new_path()
        cx.move_to(sx0, sy0 - r * 0.22)
        cx.curve_to(sx0 + r * 0.14, sy0, sx0 + r * 0.1, sy0 + r * 0.12, sx0, sy0 + r * 0.12)
        cx.curve_to(sx0 - r * 0.1, sy0 + r * 0.12, sx0 - r * 0.14, sy0, sx0, sy0 - r * 0.22)
        src(cx, alpha(hx("#8fd0ff"), p["sweat"]))
        cx.fill_preserve()
        ink(cx, 1.6 * s, alpha(INK, p["sweat"]))


def _hair(cx, x, y, r, kind, C, face, fdx, s):
    hc = C["hair"]
    cx.new_path()
    if face == "back":
        cx.arc(x, y + r * 0.15, r * 1.02, math.pi, 2 * math.pi)
        cx.line_to(x + r, y + r * 0.35)
        cx.line_to(x - r, y + r * 0.35)
        cx.close_path()
        lin(cx, x, y - r, x, y + r, [(0, shade(hc, 0.12)), (1, shade(hc, -0.2))])
        cx.fill()
        if C.get("cap"):
            _cap(cx, x, y, r, C, 0, s, back=True)
        return
    if C.get("cap"):
        _cap(cx, x, y, r, C, fdx, s)
        return
    if kind == "son":
        cx.move_to(x - r * 1.05, y + r * 0.05)
        cx.curve_to(x - r * 1.1, y - r * 1.2, x + r * 1.1, y - r * 1.25, x + r * 1.05, y + r * 0.05)
        # bangs (zig-zag) shifted with face direction
        b0 = x + r * 1.0
        pts = [(b0, y - r * 0.18)]
        n = 6
        for k in range(n + 1):
            xx = x + r * 0.95 - 1.9 * r * k / n + fdx * 0.5
            yy = y - r * (0.30 if k % 2 == 0 else 0.48)
            pts.append((xx, yy))
        for p_ in pts:
            cx.line_to(*p_)
        cx.close_path()
        lin(cx, x, y - r, x, y, [(0, shade(hc, 0.18)), (1, hc)])
        cx.fill()
        # gloss
        cx.new_path()
        cx.arc(x - r * 0.15, y - r * 0.55, r * 0.5, math.pi * 1.15, math.pi * 1.55)
        src(cx, (1, 1, 1, 0.16))
        cx.set_line_width(2.4 * s)
        cx.stroke()
    elif kind == "mom":
        cx.move_to(x - r * 1.04, y + r * 0.1)
        n = 7
        for k in range(n + 1):
            a = math.pi + math.pi * k / n
            rr = r * (1.08 if k % 2 else 1.0)
            cx.line_to(x + math.cos(a) * rr, y - r * 0.05 + math.sin(a) * rr)
        cx.line_to(x + r * 1.04, y + r * 0.1)
        cx.curve_to(x + r * 0.6, y - r * 0.35, x - r * 0.2 + fdx, y - r * 0.5, x - r * 1.04, y + r * 0.1)
        lin(cx, x, y - r, x, y, [(0, shade(hc, 0.25)), (1, shade(hc, -0.05))])
        cx.fill()
    elif kind == "det":
        for sx_ in (-1, 1):
            cx.new_path()
            cx.arc(x + sx_ * r * 0.88, y - r * 0.15, r * 0.3, 0, 2 * math.pi)
            src(cx, hc)
            cx.fill()
        cx.new_path()
        cx.arc(x, y - r * 0.2, r * 1.0, math.pi * 1.12, math.pi * 1.88)
        cx.arc_negative(x, y - r * 0.3, r * 0.82, math.pi * 1.85, math.pi * 1.15)
        cx.close_path()
        src(cx, hc)
        cx.fill()
    else:
        cx.arc(x, y + r * 0.1, r * 1.02, math.pi * 1.05, math.pi * 1.95)
        cx.close_path()
        src(cx, hc)
        cx.fill()


def _cap(cx, x, y, r, C, fdx, s, back=False):
    cc = C["cap"]
    y = y - r * 0.2
    cx.new_path()
    cx.move_to(x - r * 1.02, y - r * 0.12)
    cx.curve_to(x - r * 1.0, y - r * 1.25, x + r * 1.0, y - r * 1.25, x + r * 1.02, y - r * 0.12)
    cx.close_path()
    lin(cx, x, y - r * 1.2, x, y, [(0, shade(cc, 0.18)), (1, shade(cc, -0.1))])
    cx.fill_preserve()
    ink(cx, 2.4 * s)
    if not back:
        cx.new_path()
        cx.move_to(x - r * 0.95 + fdx, y - r * 0.14)
        cx.curve_to(x - r * 0.3 + fdx, y + r * 0.06, x + r * 0.3 + fdx, y + r * 0.06, x + r * 0.95 + fdx, y - r * 0.14)
        cx.line_to(x + r * 0.95 + fdx, y - r * 0.24)
        cx.curve_to(x + r * 0.3, y - r * 0.08, x - r * 0.3, y - r * 0.08, x - r * 0.95 + fdx, y - r * 0.24)
        cx.close_path()
        src(cx, shade(cc, -0.35))
        cx.fill_preserve()
        ink(cx, 2.0 * s)
        if C.get("badge"):
            cx.arc(x + fdx * 0.6, y - r * 0.62, r * 0.13, 0, 2 * math.pi)
            src(cx, hx("#e2c060"))
            cx.fill_preserve()
            ink(cx, 1.4 * s)
        else:
            cx.new_path()
            cx.move_to(x - r * 0.9, y - r * 0.4)
            cx.curve_to(x - r * 0.3, y - r * 0.25, x + r * 0.3, y - r * 0.25, x + r * 0.9, y - r * 0.4)
            src(cx, shade(cc, -0.2))
            cx.set_line_width(3 * s)
            cx.stroke()


# ---------------------------------------------------------------- post
_vig = {}


def vignette(strength=0.55):
    if strength not in _vig:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
        _vig[strength] = (1 - strength * np.clip(d - 0.35, 0, 1) ** 1.6)[..., None].astype(np.float32)
    return _vig[strength]


_grain = None


def grain(frame_idx, amt=5.0):
    global _grain
    if _grain is None:
        rng = np.random.default_rng(7)
        _grain = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    g = _grain[frame_idx % 6]
    return np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * amt

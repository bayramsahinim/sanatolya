"""Visuals for the Kohnstamm doorway short (1080x1920, 30 fps).

One locked room, one doorway, the blue-hoodie hero. All shapes are drawn with Cairo.
"""
import math
import random

import cairo

from cinecode.characters import Figure, HeroStyle, Pose
from cinecode.core import (OUTLINE, back_out, circle, clamp, curve, ease_io, ease_out, ellipse, fs, hexc, kf,
                           lerp, line, mix, noise1, poly, prog, rgrad, rrect, shade, smooth, src, vgrad)

W, H = 1080, 1920
FPS = 30
FONT = "Montserrat ExtraBold"

# ------------------------------------------------------------------ layout
DOOR_CX = 540
DOOR_TOP = 404            # top of the opening
FLOOR_Y = 1350            # threshold / floor line
JAMB_IN = 156             # half width of the opening
JAMB_W = 36               # casing width
FEET_IN = 1342            # hero feet when standing in the doorway
S_IN = 2.3
FEET_OUT = 1478           # one step out into the room
S_OUT = 2.6
CAP_Y = 1585              # caption centre line (below the feet, above the Shorts UI)

COUNT_START = 10.0        # "30" appears; one number per real second
COUNT_END = 40.0          # "0" appears

# palette
WALL = hexc("#EBDDBD")
WALL_STRIPE = hexc("#E2D0AA")
WOOD = hexc("#B97A43")
WOOD_DK = hexc("#8A5428")
WOOD_LT = hexc("#D39A5E")
PANEL = hexc("#8F5C35")
CARPET = hexc("#B53B2D")
CARPET_TRIM = hexc("#E0954A")
COUNT_COL = hexc("#F6B23C")


# ------------------------------------------------------------------ characters
class ShortsHero(HeroStyle):
    """Same Just Needy hero (white round head, blue hoodie, thick outlines)."""
    outline_w = 5.5


class NeutralHoodie(HeroStyle):
    def __init__(self, base):
        self.blue = hexc(base)
        self.blue_dk = shade(self.blue, -0.18)
        self.blue_lt = shade(self.blue, 0.25)


HERO = Figure(ShortsHero(), seed=1)
GRAY = Figure(NeutralHoodie("#9AA0A8"), seed=5)
TAN = Figure(NeutralHoodie("#C2AE8E"), seed=6)

UPPER, FORE = HERO.st.upper, HERO.st.fore


def press_angle(s):
    """Shoulder angle that puts the back of the hand on the inner jamb edge."""
    hand_r = HERO.st.limb_w * 0.9
    target = JAMB_IN / s - hand_r - 30 + 1.5
    return math.degrees(math.asin(clamp(target / (UPPER + FORE), 0, 1)))


A_PRESS = press_angle(S_IN)


def pose(fig_seed, x, y, s, t, **kw):
    d = dict(x=x, y=y, s=s, t=t, view="front", blink_seed=fig_seed, eyes="dot", brows="neutral",
             mouth="smile", hip_a=3, hip_b=3, knee_a=0, knee_b=0, arm_a=5, arm_b=5, elb_a=4, elb_b=4)
    d.update(kw)
    return Pose(**d)


# ------------------------------------------------------------------ text helpers
def text_path(cx, s, x, y, size, align="center"):
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    e = cx.text_extents(s)
    if align == "center":
        x -= e.x_advance / 2
    cx.move_to(x, y)
    cx.text_path(s)
    return e


def outlined_text(cx, s, x, y, size, fill=(1, 1, 1, 1), stroke=OUTLINE, sw=None, alpha=1.0, shadow=True):
    sw = size * 0.17 if sw is None else sw
    if shadow:
        text_path(cx, s, x + size * 0.02, y + size * 0.07, size)
        cx.set_line_width(sw)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(cx, (0, 0, 0, 0.28), alpha)
        cx.stroke_preserve()
        cx.fill()
    text_path(cx, s, x, y, size)
    cx.set_line_width(sw)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    src(cx, stroke, alpha)
    cx.stroke_preserve()
    src(cx, fill, alpha)
    cx.fill()


# ------------------------------------------------------------------ set
_bg = None


def background():
    """Static room layer (cached)."""
    global _bg
    if _bg is not None:
        return _bg
    pad = 200
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W + 2 * pad, H + 2 * pad)
    cx = cairo.Context(surf)
    cx.translate(pad, pad)
    rng = random.Random(7)
    # wall + stripes
    cx.rectangle(-pad, -pad, W + 2 * pad, FLOOR_Y + pad)
    src(cx, WALL)
    cx.fill()
    for x in range(-pad, W + pad, 64):
        cx.rectangle(x, -pad, 22, FLOOR_Y + pad)
        src(cx, WALL_STRIPE, 0.75)
        cx.fill()
    # crown molding
    cx.rectangle(-pad, -pad, W + 2 * pad, pad + 120)
    src(cx, shade(WALL, -0.06))
    cx.fill()
    line(cx, [(-pad, 120), (W + pad, 120)], shade(WOOD, 0.1), 14, cairo.LINE_CAP_BUTT)
    line(cx, [(-pad, 129), (W + pad, 129)], shade(WOOD_DK, -0.1), 4, cairo.LINE_CAP_BUTT)
    # wainscoting
    wy = 1105
    cx.rectangle(-pad, wy, W + 2 * pad, FLOOR_Y - wy)
    src(cx, PANEL)
    cx.fill()
    for x0 in range(-pad + 10, W + pad, 150):
        rrect(cx, x0 + 14, wy + 40, 122, FLOOR_Y - wy - 88, 6)
        fs(cx, shade(PANEL, 0.08), shade(PANEL, -0.3), 4)
        line(cx, [(x0 + 18, wy + 44), (x0 + 132, wy + 44)], shade(PANEL, 0.22), 3)
    cx.rectangle(-pad, wy - 6, W + 2 * pad, 22)
    fs(cx, WOOD_DK, shade(WOOD_DK, -0.35), 3)
    cx.rectangle(-pad, FLOOR_Y - 26, W + 2 * pad, 26)
    fs(cx, shade(PANEL, -0.3), None, 0)
    # floor planks
    cx.rectangle(-pad, FLOOR_Y, W + 2 * pad, H - FLOOR_Y + pad)
    src(cx, hexc("#7C4C2C"))
    cx.fill()
    y = FLOOR_Y
    k = 0
    while y < H + pad:
        hgt = 26 + k * 7
        line(cx, [(-pad, y), (W + pad, y)], hexc("#5E361D"), 3, cairo.LINE_CAP_BUTT)
        off = rng.uniform(0, 300)
        x = -pad + off
        while x < W + pad:
            line(cx, [(x, y), (x, y + hgt)], hexc("#5E361D"), 2.5, cairo.LINE_CAP_BUTT)
            x += rng.uniform(260, 420)
        cx.rectangle(-pad, y + 3, W + 2 * pad, 5)
        src(cx, hexc("#8E5C37"), 0.5)
        cx.fill()
        y += hgt
        k += 1
    # carpet runner in perspective
    pts = [(DOOR_CX - 170, FLOOR_Y + 4), (DOOR_CX + 170, FLOOR_Y + 4), (DOOR_CX + 470, H + pad),
           (DOOR_CX - 470, H + pad)]
    poly(cx, pts)
    fs(cx, CARPET, shade(CARPET, -0.4), 5)
    inner = [(DOOR_CX - 150, FLOOR_Y + 22), (DOOR_CX + 150, FLOOR_Y + 22), (DOOR_CX + 410, H + pad),
             (DOOR_CX - 410, H + pad)]
    poly(cx, inner)
    fs(cx, None, CARPET_TRIM, 5)
    cx.save()
    poly(cx, pts)
    cx.clip()
    cx.rectangle(-pad, FLOOR_Y, W + 2 * pad, 140)
    cx.set_source(vgrad(cx, 0, FLOOR_Y, 0, FLOOR_Y + 140, [(0, (0, 0, 0, 0.25)), (1, (0, 0, 0, 0))]))
    cx.fill()
    cx.restore()

    # wall pictures
    def frame(x, y, w, h, kind):
        rrect(cx, x + 6, y + 8, w, h, 4)
        src(cx, (0, 0, 0, 0.12))
        cx.fill()
        rrect(cx, x, y, w, h, 4)
        fs(cx, hexc("#C8933F"), shade(WOOD_DK, -0.3), 4)
        ix, iy, iw, ih = x + 14, y + 14, w - 28, h - 28
        cx.rectangle(ix, iy, iw, ih)
        if kind == "hills":
            fs(cx, hexc("#EFE3C8"), shade(WOOD_DK, -0.2), 3)
            cx.save()
            cx.rectangle(ix, iy, iw, ih)
            cx.clip()
            curve(cx, (ix, iy + ih * 0.7), (ix + iw * 0.3, iy + ih * 0.3), (ix + iw * 0.6, iy + ih * 0.9),
                  (ix + iw, iy + ih * 0.45), hexc("#B3876A"), 4)
            circle(cx, ix + iw * 0.75, iy + ih * 0.3, 9)
            fs(cx, hexc("#E7B562"), None, 0)
            cx.restore()
        else:
            fs(cx, hexc("#A9CBD6"), shade(WOOD_DK, -0.2), 3)
            cx.save()
            cx.rectangle(ix, iy, iw, ih)
            cx.clip()
            curve(cx, (ix, iy + ih * 0.8), (ix + iw * 0.4, iy + ih * 0.5), (ix + iw * 0.6, iy + ih * 0.75),
                  (ix + iw, iy + ih * 0.55), hexc("#6E98A8"), 4)
            cx.restore()

    frame(70, 600, 180, 140, "hills")
    frame(95, 790, 130, 105, "sky")
    frame(838, 600, 168, 135, "hills")
    # wall lamp (sconce)
    lx, ly = 922, 925
    cx.set_source(rgrad(cx, lx, ly - 30, 0, 230, [(0, hexc("#FFE2A6", 0.55)), (1, hexc("#FFE2A6", 0.0))]))
    circle(cx, lx, ly - 30, 230)
    cx.fill()
    rrect(cx, lx - 14, ly, 28, 46, 6)
    fs(cx, hexc("#C8933F"), OUTLINE, 3.5)
    cx.move_to(lx - 30, ly - 6)
    cx.line_to(lx + 30, ly - 6)
    cx.line_to(lx + 18, ly - 62)
    cx.line_to(lx - 18, ly - 62)
    cx.close_path()
    fs(cx, hexc("#FBE6B5"), OUTLINE, 3.5)

    # doorway: hallway behind
    ox0, ox1 = DOOR_CX - JAMB_IN, DOOR_CX + JAMB_IN
    cx.rectangle(ox0, DOOR_TOP, ox1 - ox0, FLOOR_Y - DOOR_TOP)
    cx.set_source(vgrad(cx, 0, DOOR_TOP, 0, FLOOR_Y, [(0, hexc("#6B4A33")), (0.8, hexc("#8A6547")),
                                                       (1, hexc("#5A3A26"))]))
    cx.fill()
    # hallway floor + far wall line
    cx.rectangle(ox0, 1200, ox1 - ox0, FLOOR_Y - 1200)
    src(cx, hexc("#5C3920"))
    cx.fill()
    line(cx, [(ox0, 1200), (ox1, 1200)], hexc("#3E2615"), 3)
    # open door leaf against the right side of the opening
    leaf = [(ox1 - 92, DOOR_TOP + 18), (ox1, DOOR_TOP), (ox1, FLOOR_Y), (ox1 - 92, FLOOR_Y - 34)]
    poly(cx, leaf)
    fs(cx, hexc("#9B6339"), OUTLINE, 4)
    for (a, b) in ((0.08, 0.45), (0.52, 0.92)):
        y0 = lerp(DOOR_TOP + 40, FLOOR_Y - 50, a)
        y1 = lerp(DOOR_TOP + 40, FLOOR_Y - 50, b)
        poly(cx, [(ox1 - 76, y0 + 10), (ox1 - 18, y0 + 4), (ox1 - 18, y1 - 4), (ox1 - 76, y1 - 12)])
        fs(cx, hexc("#A96D41"), shade(hexc("#9B6339"), -0.35), 3)
    circle(cx, ox1 - 78, 890, 8)
    fs(cx, hexc("#E7B562"), OUTLINE, 3)
    # shadow inside the top of the opening
    cx.rectangle(ox0, DOOR_TOP, ox1 - ox0, 70)
    cx.set_source(vgrad(cx, 0, DOOR_TOP, 0, DOOR_TOP + 70, [(0, (0, 0, 0, 0.35)), (1, (0, 0, 0, 0))]))
    cx.fill()
    # casing
    for sx in (-1, 1):
        x0 = DOOR_CX + sx * JAMB_IN
        x1 = x0 + sx * JAMB_W
        cx.rectangle(min(x0, x1), DOOR_TOP - 4, JAMB_W, FLOOR_Y - DOOR_TOP + 4)
        fs(cx, WOOD, OUTLINE, 4.5)
        line(cx, [(x0 + sx * 9, DOOR_TOP + 4), (x0 + sx * 9, FLOOR_Y - 4)], WOOD_LT, 4, cairo.LINE_CAP_BUTT)
        line(cx, [(x1 - sx * 8, DOOR_TOP + 4), (x1 - sx * 8, FLOOR_Y - 4)], WOOD_DK, 4, cairo.LINE_CAP_BUTT)
        # plinth block
        cx.rectangle(min(x0, x1) - 3, FLOOR_Y - 60, JAMB_W + 6, 60)
        fs(cx, WOOD_DK, OUTLINE, 4)
    # head casing + cap
    hx0, hx1 = DOOR_CX - JAMB_IN - JAMB_W - 18, DOOR_CX + JAMB_IN + JAMB_W + 18
    cx.rectangle(hx0, DOOR_TOP - 48, hx1 - hx0, 48)
    fs(cx, WOOD, OUTLINE, 4.5)
    line(cx, [(hx0 + 6, DOOR_TOP - 12), (hx1 - 6, DOOR_TOP - 12)], WOOD_DK, 4, cairo.LINE_CAP_BUTT)
    rrect(cx, hx0 - 12, DOOR_TOP - 66, hx1 - hx0 + 24, 22, 4)
    fs(cx, WOOD_LT, OUTLINE, 4.5)
    # threshold
    cx.rectangle(DOOR_CX - JAMB_IN, FLOOR_Y - 6, 2 * JAMB_IN, 14)
    fs(cx, WOOD_DK, OUTLINE, 3)
    _bg = (surf, pad)
    return _bg


def vignette(cx):
    cx.set_source(rgrad(cx, W / 2, H * 0.45, H * 0.35, H * 0.85, [(0, (0.2, 0.1, 0.0, 0.0)),
                                                                   (1, (0.18, 0.08, 0.0, 0.38))]))
    cx.paint()


# ------------------------------------------------------------------ overlays
def question_marks(cx, t, t0, t1, y=330):
    items = [("?", DOOR_CX - 110, y + 6, 0.0, -10), ("?", DOOR_CX + 20, y - 18, 0.35, 8),
             ("!", DOOR_CX + 120, y + 4, 0.7, 12)]
    for ch, x, yy, d, rot in items:
        a = prog(t, t0 + d, t0 + d + 0.35)
        out = 1 - smooth(prog(t, t1, t1 + 0.3))
        if a <= 0 or out <= 0:
            continue
        sc = back_out(a)
        bob = math.sin((t + d) * 3.0) * 6
        cx.save()
        cx.translate(x, yy + bob)
        cx.rotate(math.radians(rot + math.sin(t * 2 + d * 5) * 4))
        cx.scale(sc, sc)
        outlined_text(cx, ch, 0, 0, 92, fill=hexc("#2B2B33"), stroke=(1, 1, 1, 1), sw=10, alpha=out,
                      shadow=False)
        cx.restore()


def press_arrows(cx, t, hands, a):
    """Little orange chevrons showing the outward push."""
    if a <= 0:
        return
    for k, (hx, hy) in enumerate(hands):
        sx = -1 if k == 0 else 1
        ph = (t * 1.6) % 1.0
        for j in range(2):
            off = 34 + 26 * j + 10 * ph
            x = hx + sx * off
            al = a * (0.95 - 0.35 * j)
            cx.save()
            cx.translate(x, hy)
            cx.scale(sx, 1)
            poly(cx, [(-10, -18), (8, 0), (-10, 18)], close=False)
            src(cx, OUTLINE, al)
            cx.set_line_width(15)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.set_line_join(cairo.LINE_JOIN_ROUND)
            cx.stroke_preserve()
            src(cx, hexc("#FF9F2E"), al)
            cx.set_line_width(8)
            cx.stroke()
            cx.restore()


def countdown(cx, t):
    if t < COUNT_START or t >= COUNT_END + 0.75:
        return
    n = 30 - int(math.floor(t - COUNT_START + 1e-9))   # exact: frame 300 -> 30, 1200 -> 0
    n = max(n, 0)
    since = (t - COUNT_START) - (30 - n)
    sc = 1.0 + 0.06 * (1 - smooth(prog(since, 0, 0.14)))
    a = 1.0 if t < COUNT_END + 0.5 else 1 - prog(t, COUNT_END + 0.5, COUNT_END + 0.75)
    col = COUNT_COL if n > 5 else mix(COUNT_COL, hexc("#F06B3A"), 0.6)
    cx.save()
    cx.translate(DOOR_CX, 560)
    cx.scale(sc, sc)
    outlined_text(cx, str(n), 0, 0, 190, fill=col, stroke=hexc("#2A1A10"), sw=14, alpha=a)
    cx.restore()


def let_go_banner(cx, t, t0, t1):
    a = prog(t, t0, t0 + 0.25)
    out = 1 - smooth(prog(t, t1, t1 + 0.3))
    if a <= 0 or out <= 0:
        return
    sc = back_out(a, 2.2)
    cx.save()
    cx.translate(DOOR_CX, DOOR_TOP - 40)
    cx.rotate(math.radians(-3))
    cx.scale(sc, sc)
    rrect(cx, -170, -58, 340, 104, 52)
    fs(cx, hexc("#E04A3A", out), (1, 1, 1, out), 8)
    outlined_text(cx, "LET GO!", 0, 22, 64, fill=(1, 1, 1, 1), stroke=hexc("#7A1E16"), sw=8, alpha=out,
                  shadow=False)
    cx.restore()


def safety_note(cx, t, t0, t1):
    a = smooth(prog(t, t0, t0 + 0.4)) * (1 - smooth(prog(t, t1, t1 + 0.4)))
    if a <= 0:
        return
    msg = "Don't force it. Stop if uncomfortable."
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(32)
    w = cx.text_extents(msg).x_advance
    rrect(cx, W / 2 - w / 2 - 26, 218, w + 52, 58, 29)
    src(cx, (0.1, 0.07, 0.05, 0.55 * a))
    cx.fill()
    text_path(cx, msg, W / 2, 258, 32)
    src(cx, (1, 1, 1, a))
    cx.fill()


def note_card(cx, t, t0, t1, label_t):
    """Paper note: 1915 + a figure whose arms float up (the source's 1915 card)."""
    a = prog(t, t0, t0 + 0.4)
    out = 1 - smooth(prog(t, t1, t1 + 0.35))
    if a <= 0 or out <= 0:
        return
    al = out
    cx.save()
    cx.translate(176 - 220 * (1 - ease_out(a)), 735)
    cx.rotate(math.radians(-6 + 2 * math.sin(t * 1.3)))
    cx.push_group()
    rrect(cx, -118 + 8, -150 + 10, 236, 300, 6)
    src(cx, (0, 0, 0, 0.18))
    cx.fill()
    rrect(cx, -118, -150, 236, 300, 6)
    fs(cx, hexc("#FBF5E6"), OUTLINE, 4.5)
    for k in range(9):
        y = -88 + k * 27
        line(cx, [(-104, y), (104, y)], hexc("#B7CDE0"), 2, cairo.LINE_CAP_BUTT)
    line(cx, [(-82, -146), (-82, 146)], hexc("#E59A9A"), 2, cairo.LINE_CAP_BUTT)
    outlined_text(cx, "1915", 8, -100, 52, fill=hexc("#2B2B33"), stroke=hexc("#FBF5E6"), sw=2, shadow=False)
    # stick figure with arms drifting up
    lift = 0.5 + 0.5 * math.sin((t - t0) * 1.4 - 1.2)
    ang = math.radians(20 + 55 * lift)
    fx, fy = 8, 40
    circle(cx, fx, fy - 70, 17)
    fs(cx, None, hexc("#2B2B33"), 4)
    line(cx, [(fx, fy - 53), (fx, fy + 20)], hexc("#2B2B33"), 4)
    line(cx, [(fx, fy + 20), (fx - 18, fy + 70)], hexc("#2B2B33"), 4)
    line(cx, [(fx, fy + 20), (fx + 18, fy + 70)], hexc("#2B2B33"), 4)
    for sx in (-1, 1):
        hx = fx + sx * math.sin(ang) * 52
        hy = fy - 40 + math.cos(ang) * 52
        line(cx, [(fx, fy - 40), (hx, hy)], hexc("#2B2B33"), 4)
        # motion arcs
        cx.new_path()
        if sx > 0:
            cx.arc(fx, fy - 40, 68, math.pi / 2 - ang - 0.15, math.pi / 2 - 0.25)
        else:
            cx.arc(fx, fy - 40, 68, math.pi / 2 + 0.25, math.pi / 2 + ang + 0.15)
        src(cx, hexc("#E0703A"))
        cx.set_line_width(3.5)
        cx.stroke()
    cx.pop_group_to_source()
    cx.paint_with_alpha(al)
    cx.restore()
    # name tag under the card
    b = prog(t, label_t, label_t + 0.3)
    if b > 0:
        cx.save()
        cx.translate(176, 935)
        cx.scale(0.9 + 0.1 * ease_out(b), 0.9 + 0.1 * ease_out(b))
        outlined_text(cx, "KOHNSTAMM", 0, 0, 38, fill=(1, 1, 1, 1), sw=7, alpha=b * out)
        outlined_text(cx, "PHENOMENON", 0, 42, 32, fill=hexc("#FFD27A"), sw=7, alpha=b * out)
        cx.restore()


def muscles(cx, J, s, a, t):
    """Subtle red overlay on the shoulder / upper-arm muscles."""
    if a <= 0:
        return
    for k, side in (("a", -1), ("b", 1)):
        sh, el = J["sh_" + k], J["elb_" + k]
        mx, my = lerp(sh[0], el[0], 0.38), lerp(sh[1], el[1], 0.38)
        ang = math.atan2(el[1] - sh[1], el[0] - sh[0])
        pulse = 0.5 + 0.5 * math.sin(t * 5.2 + (0 if side < 0 else 0.6))
        cx.save()
        cx.translate(mx, my)
        cx.rotate(ang)
        ellipse(cx, 0, 0, 30 * s / 2.3 * (1 + 0.06 * pulse), 17 * s / 2.3 * (1 + 0.06 * pulse))
        fs(cx, hexc("#F0442F", (0.78 + 0.17 * pulse) * a), (0.45, 0.06, 0.04, 0.9 * a), 3.5)
        for j in (-1, 0, 1):
            line(cx, [(-16 * s / 2.3, j * 6 * s / 2.3), (16 * s / 2.3, j * 6 * s / 2.3)],
                 (1, 0.75, 0.7, 0.75 * a), 2.2)
        cx.restore()
        # soft glow
        cx.set_source(rgrad(cx, mx, my, 0, 70 * s / 2.3, [(0, hexc("#FF5A40", 0.22 * a * (0.6 + 0.4 * pulse))),
                                                          (1, hexc("#FF5A40", 0))]))
        circle(cx, mx, my, 70 * s / 2.3)
        cx.fill()


def muscle_label(cx, t, t0, t1, J):
    a = smooth(prog(t, t0, t0 + 0.4)) * (1 - smooth(prog(t, t1, t1 + 0.4)))
    if a <= 0:
        return
    sh = J["sh_b"]
    lx, ly = 900, 1010
    line(cx, [(lx - 20, ly - 52), (sh[0] + 52, sh[1] + 30)], (1, 1, 1, 0.9 * a), 4)
    circle(cx, sh[0] + 52, sh[1] + 30, 6)
    fs(cx, (1, 1, 1, a), OUTLINE, 2)
    outlined_text(cx, "SHOULDER", lx + 40, ly - 30, 30, sw=6, alpha=a)
    outlined_text(cx, "MUSCLES", lx + 40, ly + 6, 30, sw=6, alpha=a)


def float_lines(cx, J, a, t):
    """Soft upward motion marks under the floating arms."""
    if a <= 0:
        return
    for k, sx in (("a", -1), ("b", 1)):
        el, ha = J["elb_" + k], J["hand_" + k]
        for j in range(2):
            ph = ((t * 0.9 + j * 0.5) % 1.0)
            x = lerp(el[0], ha[0], 0.35 + 0.4 * j)
            y = lerp(el[1], ha[1], 0.35 + 0.4 * j) + 46 - 20 * ph
            al = a * math.sin(math.pi * ph) * 0.9
            curve(cx, (x - 14, y + 6), (x - 6, y - 4), (x + 6, y - 4), (x + 14, y + 6), (1, 1, 1, al), 5)


def outcome_label(cx, x, y, txt, a, col=(1, 1, 1, 1)):
    if a <= 0:
        return
    cx.save()
    cx.translate(x, y + 18 * (1 - ease_out(a)))
    outlined_text(cx, txt, 0, 0, 42, fill=col, sw=8, alpha=a)
    cx.restore()

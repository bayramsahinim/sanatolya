"""Day 2 (rebuilt) drawing kit, mature/dark variant of the Day 2 kit.
Day 2 drawing kit, vertical 1080x1920, matching the Day 1 look:
off-white round head with dark outline, blue hoodie, black stick legs, warm desaturated sets,
bold Montserrat ExtraBold lettering in white and soft yellow."""
import math
import random

import cairo

from cinecode.core import (clamp, ellipse, fs, hexc, line, mix, noise1, rrect, shade, smooth, smooth_poly,
                           src)

W, H = 1080, 1920
FPS = 30

INK = hexc("#1f1c1a")
HEAD = hexc("#f5f2ea")
HOOD = hexc("#2f7fe3")
HOOD_D = hexc("#1f5fbf")
HOOD_DD = hexc("#1a4f9e")
LEG = hexc("#141414")
YEL = hexc("#ffd43b")
YEL_D = hexc("#3b2a10")
WHITE = (1, 1, 1, 1)


def vec(a, l):
    """angle from straight down, positive = toward screen right."""
    return math.sin(a) * l, math.cos(a) * l


# ============================================================ text
def label(cx, s, x, y, size, fill=YEL, outline=YEL_D, ow=None, alpha=1.0, spacing=0.0, scale=1.0, rot=0.0,
          shadow=True):
    if alpha <= 0.001:
        return
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(scale, scale)
    cx.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    # measure with spacing
    widths = [cx.text_extents(ch).x_advance for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    ext = cx.text_extents(s)
    by = -ext.y_bearing / 2 - ext.height / 2 + ext.height / 2 * 0  # baseline offset to centre caps
    capy = size * 0.36
    ow = size * 0.16 if ow is None else ow
    cx.push_group()
    for layer in (("shadow",) if shadow else ()) + ("stroke", "fill"):
        px = -total / 2
        for ch, w in zip(s, widths):
            cx.move_to(px + (4 if layer == "shadow" else 0), capy + (6 if layer == "shadow" else 0))
            cx.text_path(ch)
            px += w + spacing
        if layer == "shadow":
            src(cx, (0, 0, 0, 0.35))
            cx.set_line_width(ow)
            cx.set_line_join(cairo.LINE_JOIN_ROUND)
            cx.stroke_preserve()
            cx.fill()
        elif layer == "stroke":
            if outline is not None:
                src(cx, outline)
                cx.set_line_width(ow)
                cx.set_line_join(cairo.LINE_JOIN_ROUND)
                cx.stroke()
            else:
                cx.new_path()
        else:
            src(cx, fill)
            cx.fill()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def pop_scale(t, t0, dur=0.35):
    """0 -> overshoot -> 1 entrance."""
    x = clamp((t - t0) / dur)
    if x <= 0:
        return 0.0
    s = 1.70158 * 1.4
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ============================================================ hero
EXPR = {}


def _eye_oval(cx, x, y, rx, ry, look, blink, lid=0.0, hl=True):
    ry2 = ry * (1 - blink)
    if ry2 < 2:
        line(cx, [(x - rx, y), (x + rx, y)], INK, 6)
        return
    ellipse(cx, x + look[0] * rx * 0.25, y + look[1] * ry * 0.2, rx, ry2)
    src(cx, INK)
    cx.fill()
    if lid > 0:  # upper lid covering
        cx.save()
        cx.rectangle(x - rx * 1.6, y - ry * 1.4, rx * 3.2, ry * 2.8 * lid)
        src(cx, HEAD)
        cx.fill()
        cx.restore()
        ly = y - ry * 1.4 + ry * 2.8 * lid
        line(cx, [(x - rx * 1.25, ly), (x + rx * 1.25, ly)], INK, max(4, rx * 0.22))
    if hl and lid < 0.45 and blink < 0.4:
        ellipse(cx, x + look[0] * rx * 0.25 - rx * 0.32, y - ry2 * 0.38, rx * 0.26, ry2 * 0.22)
        src(cx, (1, 1, 1, 0.95))
        cx.fill()


def _eye_ring(cx, x, y, r, look, pupil, blink):
    if blink > 0.6:
        line(cx, [(x - r, y), (x + r, y)], INK, 6)
        return
    ellipse(cx, x, y, r, r * (1 - blink))
    fs(cx, (1, 1, 1, 1), INK, max(3, r * 0.1))
    ellipse(cx, x + look[0] * r * 0.45, y + look[1] * r * 0.4, r * pupil, r * pupil * (1 - blink))
    src(cx, INK)
    cx.fill()


def face(cx, hx, hy, R, expr="neutral", look=(0, 0), blink=0.0, t=0.0, turn=0.0, talk=0.0):
    """Draw the facial features. turn in [-1,1] shifts features sideways (head turning)."""
    ox = turn * R * 0.42
    ex = R * 0.30
    ey = -R * 0.05
    L = (hx + ox - ex * (1 - abs(turn) * 0.25), hy + ey)
    Rr = (hx + ox + ex * (1 - abs(turn) * 0.25), hy + ey)
    bw = R * 0.30
    blw = R * 0.085

    def brow(p, dy, ang, w=bw):
        x, y = p
        y += dy
        c, s = math.cos(ang), math.sin(ang)
        line(cx, [(x - c * w / 2, y - s * w / 2), (x + c * w / 2, y + s * w / 2)], INK, blw)

    def mouth_line(w, dy=0.0, curve=0.0):
        mx, my = hx + ox * 1.1, hy + R * 0.42 + dy
        cx.move_to(mx - w, my)
        cx.curve_to(mx - w / 2, my + curve, mx + w / 2, my + curve, mx + w, my)
        src(cx, INK)
        cx.set_line_width(R * 0.04)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()

    def mouth_o(rx, ry, dy=0.0):
        ellipse(cx, hx + ox * 1.1, hy + R * 0.45 + dy, rx, ry)
        src(cx, INK)
        cx.fill()

    def wobble(w, dy=0.0, amp=None):
        amp = R * 0.035 if amp is None else amp
        mx, my = hx + ox * 1.1, hy + R * 0.45 + dy
        pts = []
        n = 7
        for i in range(n):
            x = mx - w + 2 * w * i / (n - 1)
            pts.append((x, my + (amp if i % 2 else -amp)))
        line(cx, pts, INK, R * 0.035)

    if expr in ("neutral", "talk"):
        _eye_oval(cx, *L, R * 0.11, R * 0.15, look, blink)
        _eye_oval(cx, *Rr, R * 0.11, R * 0.15, look, blink)
        brow(L, -R * 0.27, 0.0)
        brow(Rr, -R * 0.27, 0.0)
        if talk > 0.05:
            mouth_o(R * 0.09, R * 0.03 + R * 0.07 * talk)
        else:
            mouth_line(R * 0.09)
    elif expr == "tired":
        _eye_oval(cx, *L, R * 0.12, R * 0.12, look, blink, lid=0.5)
        _eye_oval(cx, *Rr, R * 0.12, R * 0.12, look, blink, lid=0.5)
        brow(L, -R * 0.25, 0.08)
        brow(Rr, -R * 0.25, -0.08)
        for p in (L, Rr):  # eye bags
            cx.arc(p[0], p[1] + R * 0.07, R * 0.11, 0.25 * math.pi, 0.75 * math.pi)
            src(cx, shade(INK, 0.45))
            cx.set_line_width(R * 0.025)
            cx.stroke()
        mouth_line(R * 0.10, curve=-R * 0.03)
    elif expr == "worried":
        _eye_oval(cx, *L, R * 0.11, R * 0.14, look, blink)
        _eye_oval(cx, *Rr, R * 0.11, R * 0.14, look, blink)
        brow(L, -R * 0.30, -0.3)
        brow(Rr, -R * 0.30, 0.3)
        mouth_line(R * 0.08, curve=-R * 0.02)
    elif expr == "scared":
        _eye_ring(cx, *L, R * 0.15, look, 0.30, blink)
        _eye_ring(cx, *Rr, R * 0.15, look, 0.30, blink)
        brow(L, -R * 0.36, -0.3)
        brow(Rr, -R * 0.36, 0.3)
        mouth_o(R * 0.045, R * 0.035)
    elif expr == "terror":
        _eye_ring(cx, *L, R * 0.18, look, 0.16, blink)
        _eye_ring(cx, *Rr, R * 0.18, look, 0.16, blink)
        brow(L, -R * 0.42, -0.25)
        brow(Rr, -R * 0.42, 0.25)
        mouth_o(R * 0.06, R * 0.08)
    elif expr == "shock":
        _eye_oval(cx, *L, R * 0.13, R * 0.19, look, blink)
        _eye_oval(cx, *Rr, R * 0.13, R * 0.19, look, blink)
        brow(L, -R * 0.38, 0.12)
        brow(Rr, -R * 0.38, -0.12)
        mouth_o(R * 0.08, R * 0.11)
    elif expr == "confused":
        _eye_oval(cx, *L, R * 0.10, R * 0.13, look, blink)
        _eye_oval(cx, *Rr, R * 0.13, R * 0.16, look, blink)
        brow(L, -R * 0.22, 0.12)
        brow(Rr, -R * 0.40, -0.25)
        mx, my = hx + ox * 1.1, hy + R * 0.44
        line(cx, [(mx - R * 0.10, my + R * 0.02), (mx - R * 0.03, my - R * 0.02), (mx + R * 0.03, my + R * 0.02),
                  (mx + R * 0.10, my - R * 0.03)], INK, R * 0.035)
    elif expr == "flat":  # deadpan, half lids
        _eye_oval(cx, *L, R * 0.12, R * 0.12, look, blink, lid=0.45)
        _eye_oval(cx, *Rr, R * 0.12, R * 0.12, look, blink, lid=0.45)
        brow(L, -R * 0.24, 0.0)
        brow(Rr, -R * 0.24, 0.0)
        mouth_line(R * 0.10)
    elif expr == "confident":
        _eye_oval(cx, *L, R * 0.11, R * 0.14, look, blink)
        _eye_oval(cx, *Rr, R * 0.11, R * 0.14, look, blink)
        brow(L, -R * 0.30, 0.22)
        brow(Rr, -R * 0.30, -0.22)
        mx, my = hx + ox * 1.1, hy + R * 0.36
        cx.move_to(mx - R * 0.20, my)
        cx.curve_to(mx - R * 0.14, my + R * 0.20, mx + R * 0.14, my + R * 0.20, mx + R * 0.20, my)
        cx.close_path()
        fs(cx, INK, INK, R * 0.03)
        cx.move_to(mx - R * 0.15, my + R * 0.02)
        cx.line_to(mx + R * 0.15, my + R * 0.02)
        cx.line_to(mx + R * 0.12, my + R * 0.06)
        cx.line_to(mx - R * 0.12, my + R * 0.06)
        cx.close_path()
        src(cx, WHITE)
        cx.fill()
    elif expr == "relieved":
        for p in (L, Rr):
            cx.arc(p[0], p[1] + R * 0.04, R * 0.10, math.pi * 1.1, math.pi * 1.9)
            src(cx, INK)
            cx.set_line_width(R * 0.05)
            cx.stroke()
        brow(L, -R * 0.24, -0.15)
        brow(Rr, -R * 0.24, 0.15)
        mouth_line(R * 0.10, curve=R * 0.06)
    if False:
        # sweat drop
        sx, sy = hx + R * 0.70, hy - R * 0.38 + (t * 25 % 30)
        cx.move_to(sx, sy - R * 0.11)
        cx.curve_to(sx + R * 0.07, sy, sx + R * 0.06, sy + R * 0.07, sx, sy + R * 0.07)
        cx.curve_to(sx - R * 0.06, sy + R * 0.07, sx - R * 0.07, sy, sx, sy - R * 0.11)
        fs(cx, hexc("#7fc1ff"), INK, R * 0.02)


def hand_dot(cx, x, y, r, thumb=None):
    if thumb is not None:  # thumbs up: a little stub pointing in `thumb` angle
        dx, dy = math.sin(thumb), -math.cos(thumb)
        line(cx, [(x, y), (x + dx * r * 1.9, y + dy * r * 1.9)], INK, r * 0.95)
    ellipse(cx, x, y, r * 1.15, r)
    src(cx, INK)
    cx.fill()


def sleeve(cx, pts, w, col=HOOD):
    line(cx, pts, INK, w + 7)
    line(cx, pts, col, w)


class Pose(dict):
    def __getattr__(self, k):
        return self.get(k)


def hero(cx, x, gy, s=1.0, **kw):
    """Just Needy. (x, gy) = ground point between the feet.
    kw: expr, look, blink, t, crouch, walk (phase rad), arm_l/arm_r ((upper, fore) angles),
    hand_l/hand_r ('dot'|'thumb'|'none'), tilt (head, rad), lean (rad), turn, talk, shiver,
    flash ((ux,uy) direction of a flashlight held in the right hand) ."""
    p = Pose(kw)
    t = p.t or 0.0
    cx.save()
    shv = p.shiver or 0.0
    if shv:
        cx.translate(noise1(t * 30, 3) * shv * 4 * s, noise1(t * 30, 9) * shv * 2 * s)
    crouch = p.crouch or 0.0
    walk = p.walk
    R = 142 * s
    leg = 150 * s
    hip_y = gy - leg * (1 - 0.42 * crouch)
    bob = 0.0
    if walk is not None:
        bob = -abs(math.sin(walk)) * 8 * s
        hip_y += bob
    lean = p.lean or 0.0
    # ---------------- legs
    for side in (-1, 1):
        hx = x + side * 34 * s
        if walk is not None:
            a = math.sin(walk + (0 if side < 0 else math.pi)) * 0.22
            fx, fy = hx + math.sin(a) * leg, hip_y + math.cos(a) * leg
            lift = max(0, -math.cos(walk + (0 if side < 0 else math.pi))) * 16 * s
            fy = min(fy, gy) - lift
            kx, ky = (hx + fx) / 2 - 6 * s, (hip_y + fy) / 2
            line(cx, [(hx, hip_y), (kx, ky), (fx, fy)], LEG, 17 * s)
        else:
            fx = hx + side * (14 + 30 * crouch) * s
            kx = hx + side * (10 + 46 * crouch) * s
            ky = (hip_y + gy) / 2 - 6 * crouch * s
            line(cx, [(hx, hip_y), (kx, ky), (fx, gy)], LEG, 17 * s)
    # ---------------- torso (hoodie)
    cx.save()
    cx.translate(x, hip_y)
    cx.rotate(lean)
    sh = -205 * s
    body = [(-78 * s, sh), (78 * s, sh), (96 * s, 14 * s), (-96 * s, 14 * s)]
    cx.move_to(-78 * s, sh + 20 * s)
    cx.curve_to(-78 * s, sh, -60 * s, sh, -40 * s, sh)
    cx.line_to(40 * s, sh)
    cx.curve_to(60 * s, sh, 78 * s, sh, 78 * s, sh + 20 * s)
    cx.line_to(96 * s, 8 * s)
    cx.curve_to(96 * s, 18 * s, 90 * s, 20 * s, 80 * s, 20 * s)
    cx.line_to(-80 * s, 20 * s)
    cx.curve_to(-90 * s, 20 * s, -96 * s, 18 * s, -96 * s, 8 * s)
    cx.close_path()
    cloth = p.cloth or HOOD
    hood = p.hood if p.hood is not None else True
    g = cairo.LinearGradient(-96 * s, 0, 96 * s, 0)
    g.add_color_stop_rgba(0, *shade(cloth, -0.08))
    g.add_color_stop_rgba(0.5, *cloth)
    g.add_color_stop_rgba(1, *shade(cloth, -0.14))
    cx.set_source(g)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(4 * s)
    cx.stroke()
    # hem band
    if hood:
        cx.rectangle(-94 * s, 2 * s, 188 * s, 12 * s)
        src(cx, HOOD_DD)
        cx.fill()
        line(cx, [(-46 * s, -12 * s), (-36 * s, -72 * s), (36 * s, -72 * s), (46 * s, -12 * s)],
             shade(HOOD_DD, -0.1), 2.5 * s)
        for side in (-1, 1):
            line(cx, [(side * 20 * s, sh + 22 * s), (side * 23 * s, sh + 88 * s)], (0.9, 0.9, 0.9, 0.95), 7 * s)
        ellipse(cx, 0, sh + 2 * s, 118 * s, 46 * s)
        fs(cx, HOOD_D, INK, 4 * s)
    else:  # plain work shirt: collar, buttons, plaid lines, dirt
        for k in range(-3, 4):
            line(cx, [(k * 26 * s, sh + 4 * s), (k * 28 * s, 16 * s)], shade(cloth, -0.25), 3 * s)
        for k in range(1, 6):
            line(cx, [(-86 * s, sh + k * 38 * s), (86 * s, sh + k * 38 * s)], shade(cloth, -0.25), 3 * s)
        cx.move_to(-46 * s, sh + 2 * s)
        cx.line_to(0, sh + 46 * s)
        cx.line_to(46 * s, sh + 2 * s)
        fs(cx, None, INK, 4 * s)
        for k in range(4):
            ellipse(cx, 0, sh + 70 * s + k * 40 * s, 5 * s, 5 * s)
            src(cx, INK)
            cx.fill()
        if p.dirt:
            rr = random.Random(7)
            for k in range(6):
                ellipse(cx, rr.uniform(-70, 70) * s, rr.uniform(-180, 0) * s, rr.uniform(10, 22) * s,
                        rr.uniform(6, 14) * s, rr.uniform(0, 3))
                src(cx, (0.2, 0.16, 0.12, 0.45))
                cx.fill()
    shoulder_l = (-74 * s, sh + 26 * s)
    shoulder_r = (74 * s, sh + 26 * s)
    head_c = (0, sh - R * 0.66)
    cx.restore()

    def tw(px, py):  # torso local -> world
        c, sn = math.cos(lean), math.sin(lean)
        return x + px * c - py * sn, hip_y + px * sn + py * c

    hx, hy = tw(*head_c)
    hx += (p.head_dx or 0) * s
    hy += (p.head_dy or 0) * s + bob * 0.3
    # ---------------- head
    tilt = p.tilt or 0.0
    cx.save()
    cx.translate(hx, hy)
    cx.rotate(tilt)
    ellipse(cx, 0, 0, R, R * 0.985)
    gg = cairo.RadialGradient(-R * 0.3, -R * 0.35, R * 0.1, 0, 0, R * 1.05)
    gg.add_color_stop_rgba(0, *HEAD)
    gg.add_color_stop_rgba(1, *shade(HEAD, -0.06))
    cx.set_source(gg)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(4.5 * s)
    cx.stroke()
    if p.dirt:
        for (dx, dy, rr_) in ((-0.5, 0.42, 0.1),):
            ellipse(cx, dx * R, dy * R, rr_ * R, rr_ * R * 0.45, 0.3)
            src(cx, (0.3, 0.25, 0.2, 0.14))
            cx.fill()
    face(cx, 0, 0, R, p.expr or "neutral", p.look or (0, 0), p.blink or 0.0, t, p.turn or 0.0, p.talk or 0.0)
    if p.hat == "cap":
        cx.move_to(-R * 0.92, -R * 0.38)
        cx.curve_to(-R * 0.85, -R * 1.18, R * 0.85, -R * 1.18, R * 0.92, -R * 0.38)
        cx.close_path()
        fs(cx, p.hat_col or hexc("#4a4a3a"), INK, 4 * s)
        cx.move_to(-R * 0.92, -R * 0.38)
        cx.curve_to(-R * 0.2, -R * 0.52, R * 0.9, -R * 0.5, R * 1.3, -R * 0.3)
        cx.curve_to(R * 0.8, -R * 0.24, -R * 0.4, -R * 0.28, -R * 0.92, -R * 0.38)
        fs(cx, shade(p.hat_col or hexc("#4a4a3a"), -0.25), INK, 4 * s)
    elif p.hat == "beanie":
        cx.move_to(-R * 0.95, -R * 0.3)
        cx.curve_to(-R * 0.9, -R * 1.25, R * 0.9, -R * 1.25, R * 0.95, -R * 0.3)
        cx.close_path()
        fs(cx, p.hat_col or hexc("#5a4038"), INK, 4 * s)
        rrect(cx, -R * 0.98, -R * 0.42, R * 1.96, R * 0.2, R * 0.08)
        fs(cx, shade(p.hat_col or hexc("#5a4038"), -0.2), INK, 3 * s)
    cx.restore()
    # ---------------- arms (in front)
    upper, fore = 82 * s, 78 * s
    out = {}
    for side, sp, key in ((-1, shoulder_l, "arm_l"), (1, shoulder_r, "arm_r")):
        sx, sy = tw(*sp)
        if p.get(key) is not None:
            a1, a2 = p.get(key)
        elif walk is not None:
            sw = math.sin(walk + (math.pi if side < 0 else 0)) * 0.35
            a1, a2 = side * 0.18 + sw, side * 0.05 + sw * 1.2
        else:
            a1, a2 = side * 0.16, side * 0.06
        dx, dy = vec(a1, upper)
        ex_, ey_ = sx + dx, sy + dy
        dx, dy = vec(a2, fore)
        hx2, hy2 = ex_ + dx, ey_ + dy
        sleeve(cx, [(sx, sy), (ex_, ey_), (hx2, hy2)], 40 * s, col=p.cloth or HOOD)
        kind = p.get("hand_" + key[-1]) or "dot"
        if kind == "thumb":
            hand_dot(cx, hx2, hy2, 17 * s, thumb=-0.1 * side)
        elif kind != "none":
            hand_dot(cx, hx2, hy2, 17 * s)
        out[key] = (hx2, hy2)
    out["head"] = (hx, hy, R)
    out["hip"] = (x, hip_y)
    cx.restore()
    return out


# ============================================================ zombies
class Zed:
    def __init__(self, seed, skin="#8fae6b", shirt="#6b4a3a", pants="#3a3a44", R=88, size=1.0, eyes="mismatch",
                 mouth="teeth", hair="tuft", limp=0.5, reach=1, speed=1.0, tilt0=0.15, hat=None):
        self.seed = seed
        self.skin = hexc(skin)
        self.shirt = hexc(shirt)
        self.pants = hexc(pants)
        self.R = R
        self.size = size
        self.eyes = eyes
        self.mouth = mouth
        self.hair = hair
        self.limp = limp
        self.reach = reach      # 0 none, 1 one arm, 2 both
        self.speed = speed
        self.tilt0 = tilt0
        self.hat = hat


CAST = [
    Zed(1, "#93b06e", "#7a4b36", "#3b3a46", R=86, eyes="mismatch", mouth="teeth", hair="tuft", limp=0.7, reach=1,
        speed=0.9, tilt0=0.22),
    Zed(2, "#8aa7b4", "#4d5f7d", "#2f2f35", R=80, size=1.08, eyes="droopy", mouth="jaw", hair="bald", limp=0.3,
        reach=2, speed=0.7, tilt0=-0.18),
    Zed(3, "#a3b07a", "#8a6a3c", "#463a2f", R=92, size=0.92, eyes="stitch", mouth="tongue", hair="spiky", limp=0.9,
        reach=0, speed=1.15, tilt0=0.3),
    Zed(4, "#7f9e78", "#5b6b3f", "#2e2a28", R=84, size=1.0, eyes="wide", mouth="grin", hair="comb", limp=0.45,
        reach=1, speed=0.8, tilt0=-0.1),
    Zed(5, "#9bb59a", "#7d3f45", "#34343c", R=78, size=1.12, eyes="mismatch", mouth="jaw", hair="tuft", limp=0.6,
        reach=2, speed=0.6, tilt0=0.12),
    Zed(6, "#a6a882", "#46607a", "#3d342a", R=90, size=0.95, eyes="droopy", mouth="teeth", hair="spiky", limp=0.2,
        reach=1, speed=1.0, tilt0=-0.25),
]

MAILMAN = Zed(7, "#94ad7a", "#9fbad6", "#2d3c55", R=96, eyes="mismatch", mouth="jaw", hair="bald", limp=0.4,
              reach=2, speed=0.8, tilt0=0.18, hat="mail")


def zhead(cx, z, hx, hy, R, t, jaw=0.0, look=(0, 0), mood=0.0, blink=0.0, front_hair=True):
    r = random.Random(z.seed)
    sk = z.skin
    # head shape: slightly lumpy
    pts = []
    for i in range(14):
        a = i / 14 * 2 * math.pi
        rr = R * (1 + 0.035 * math.sin(a * 3 + z.seed) + 0.02 * math.sin(a * 5 + z.seed * 2))
        pts.append((hx + math.cos(a) * rr, hy + math.sin(a) * rr * 0.97))
    smooth_poly(cx, pts)
    g = cairo.RadialGradient(hx - R * 0.3, hy - R * 0.35, R * 0.1, hx, hy, R * 1.05)
    g.add_color_stop_rgba(0, *shade(sk, 0.12))
    g.add_color_stop_rgba(1, *shade(sk, -0.15))
    cx.set_source(g)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(R * 0.045)
    cx.stroke()
    # blotches
    for k in range(3):
        bx = hx + r.uniform(-0.55, 0.55) * R
        by = hy + r.uniform(-0.6, 0.1) * R
        ellipse(cx, bx, by, R * r.uniform(0.07, 0.13), R * r.uniform(0.05, 0.1), r.uniform(0, 3))
        src(cx, shade(sk, -0.22), 0.55)
        cx.fill()
    # stitch scar
    sx0, sy0 = hx + R * r.uniform(-0.5, 0.1), hy - R * r.uniform(0.45, 0.65)
    ang = r.uniform(-0.6, 0.6)
    L = R * 0.55
    ex, ey = sx0 + math.cos(ang) * L, sy0 + math.sin(ang) * L
    line(cx, [(sx0, sy0), (ex, ey)], INK, R * 0.03)
    for k in range(5):
        f = (k + 0.5) / 5
        mx, my = sx0 + (ex - sx0) * f, sy0 + (ey - sy0) * f
        nx, ny = -math.sin(ang) * R * 0.07, math.cos(ang) * R * 0.07
        line(cx, [(mx - nx, my - ny), (mx + nx, my + ny)], INK, R * 0.025)
    # hair
    if z.hair == "tuft":
        for k in range(3):
            a = -math.pi / 2 + (k - 1) * 0.25
            bx, by = hx + math.cos(a) * R * 0.95, hy + math.sin(a) * R * 0.95
            line(cx, [(bx, by), (bx + (k - 1) * R * 0.12 + noise1(t * 2, z.seed + k) * R * 0.04, by - R * 0.22)],
                 INK, R * 0.035)
    elif z.hair == "spiky":
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.22
            bx, by = hx + math.cos(a) * R * 0.93, hy + math.sin(a) * R * 0.93
            line(cx, [(bx, by), (bx + math.cos(a) * R * 0.2, by + math.sin(a) * R * 0.2)], shade(INK, 0.15),
                 R * 0.07)
    elif z.hair == "comb":
        cx.move_to(hx - R * 0.9, hy - R * 0.35)
        cx.curve_to(hx - R * 0.6, hy - R * 1.15, hx + R * 0.5, hy - R * 1.15, hx + R * 0.95, hy - R * 0.45)
        cx.curve_to(hx + R * 0.4, hy - R * 0.75, hx - R * 0.3, hy - R * 0.7, hx - R * 0.9, hy - R * 0.35)
        fs(cx, hexc("#3b3326"), INK, R * 0.03)
    # eyes
    ly, ry_ = hy - R * 0.08, hy - R * 0.08
    lx, rx = hx - R * 0.32, hx + R * 0.30
    twitch = 1 + 0.15 * max(0, noise1(t * 3.1, z.seed + 40))
    lk = (look[0] * R * 0.05, look[1] * R * 0.05)

    def socket(x, y, r):
        ellipse(cx, x, y, r * 1.18, r * 1.1)
        src(cx, shade(sk, -0.3), 0.7)
        cx.fill()

    def yellow_eye(x, y, r, pupil=0.32, lid=0.0):
        socket(x, y, r)
        ellipse(cx, x, y, r, r * (1 - blink))
        fs(cx, hexc("#f2edc8"), INK, R * 0.03)
        ellipse(cx, x + lk[0], y + lk[1], r * pupil, r * pupil * (1 - blink))
        src(cx, INK)
        cx.fill()
        if lid > 0:
            cx.save()
            ellipse(cx, x, y, r * 1.05, r * 1.05)
            cx.clip()
            cx.rectangle(x - r * 1.2, y - r * 1.2, r * 2.4, r * 2.4 * lid)
            src(cx, shade(sk, -0.1))
            cx.fill()
            cx.restore()
            line(cx, [(x - r, y - r + 2 * r * lid), (x + r, y - r + 2 * r * lid)], INK, R * 0.035)

    if z.eyes == "mismatch":
        yellow_eye(lx, ly, R * 0.15 * twitch, 0.25)
        yellow_eye(rx, ry_ + R * 0.04, R * 0.24, 0.18)
    elif z.eyes == "droopy":
        yellow_eye(lx, ly, R * 0.18, 0.3, lid=0.45)
        yellow_eye(rx, ry_ + R * 0.06, R * 0.18, 0.3, lid=0.62)
    elif z.eyes == "stitch":
        yellow_eye(lx, ly, R * 0.2 * twitch, 0.22)
        socket(rx, ry_, R * 0.16)
        for d in (-1, 1):
            line(cx, [(rx - R * 0.12, ry_ - d * R * 0.12), (rx + R * 0.12, ry_ + d * R * 0.12)], INK, R * 0.045)
    else:  # wide
        yellow_eye(lx, ly, R * 0.2, 0.16)
        yellow_eye(rx, ry_, R * 0.2 * twitch, 0.16)
    # brows: angry/sad asymmetry
    line(cx, [(lx - R * 0.16, ly - R * 0.3 - mood * R * 0.05), (lx + R * 0.14, ly - R * 0.22)], INK, R * 0.06)
    line(cx, [(rx - R * 0.12, ry_ - R * 0.24), (rx + R * 0.18, ry_ - R * 0.34 + mood * R * 0.04)], INK, R * 0.06)
    # mouth
    mx, my = hx + R * 0.02, hy + R * 0.42
    open_ = 0.25 + 0.75 * jaw
    if z.mouth in ("teeth", "jaw", "grin"):
        w = R * (0.42 if z.mouth == "grin" else 0.3)
        hgt = R * (0.10 + 0.22 * open_) * (1.5 if z.mouth == "jaw" else 1.0)
        cx.move_to(mx - w, my)
        cx.curve_to(mx - w * 0.5, my - R * 0.05, mx + w * 0.5, my - R * 0.03, mx + w, my + R * 0.02)
        cx.curve_to(mx + w * 0.8, my + hgt, mx - w * 0.6, my + hgt * 1.1, mx - w, my)
        cx.close_path()
        fs(cx, hexc("#3a1616"), INK, R * 0.035)
        n = 5 if z.mouth != "grin" else 7
        for k in range(n):
            if (k * 7 + z.seed) % 3 == 0 and z.mouth != "grin":
                continue  # missing teeth
            tx = mx - w * 0.8 + 2 * w * 0.8 * k / (n - 1)
            cx.move_to(tx - R * 0.04, my - R * 0.01)
            cx.line_to(tx + R * 0.04, my - R * 0.005)
            cx.line_to(tx, my + R * 0.08)
            cx.close_path()
            src(cx, hexc("#efe6c4"))
            cx.fill()
    elif z.mouth == "tongue":
        ellipse(cx, mx, my + R * 0.04, R * 0.2, R * 0.1 + R * 0.08 * open_)
        fs(cx, hexc("#3a1616"), INK, R * 0.035)
        ellipse(cx, mx + R * 0.08, my + R * 0.16 + R * 0.05 * open_, R * 0.08, R * 0.11, 0.3)
        fs(cx, hexc("#d06a7a"), INK, R * 0.03)


def zombie(cx, z, x, gy, s, t, face_dir=1, walking=True, phase=None, jaw=None, look=(0, 0), arms=None, sil=None,
           head_only=False, holding=None, lost_left=None, head_add=0.0, blink=None, still=False):
    """Draw zombie z with an irregular, asymmetric shamble. Returns head (x, y, R).
    phase: gait phase (if None derived from t*speed). sil: flat silhouette colour."""
    if sil is not None:
        cx.push_group()
    seed = z.seed
    sc = s * z.size
    R = z.R * sc
    leg = 140 * sc
    if phase is None:
        phase = t * z.speed * 2 * math.pi * 0.55 + seed
    ph = phase
    # irregular gait: limp side gets a short, dragging swing and a hitch in the body
    swing_l = 0.42 * (1 - 0.6 * z.limp)
    swing_r = 0.42
    hitch = math.sin(ph) * 0.5 + 0.5
    drop = (z.limp * 14 * sc * max(0, math.sin(ph))) if walking else 0
    hunch = getattr(z, "hunch", 0.0)
    thin = getattr(z, "thin", 1.0)
    arm_k = getattr(z, "arm", 1.0)
    jerk = 0.0 if still else noise1(t * 2.3, seed) * 0.08 + noise1(t * 7.0, seed + 5) * 0.03
    hip_y = gy - leg + drop - (abs(math.sin(ph)) * 6 * sc if walking else 0)
    lean = face_dir * (0.16 + 0.06 * math.sin(ph * 2 + 1)) + jerk if walking else face_dir * 0.08 + jerk * 0.5
    lean += face_dir * hunch * 0.6
    shoulder_tilt = (0.12 * z.limp * math.sin(ph) if walking else 0) + (0 if still else noise1(t * 1.3, seed + 11) * 0.06)
    shoulder_tilt += getattr(z, "tilt_sh", 0.0)
    # legs
    for side in (-1, 1):
        hx = x + side * 28 * sc
        if walking:
            sw = swing_l if side < 0 else swing_r
            a = face_dir * math.sin(ph + (0 if side < 0 else math.pi)) * sw
            fx, fy = hx + math.sin(a) * leg, hip_y + math.cos(a) * leg
            if side < 0 and z.limp > 0.4:  # dragged foot stays low, toe scrape
                fy = gy
            fy = min(fy, gy)
            kx = (hx + fx) / 2 + face_dir * 10 * sc
            ky = (hip_y + fy) / 2
        else:
            fx, fy = hx + side * 18 * sc, gy
            kx, ky = hx + side * 10 * sc + face_dir * 6 * sc, (hip_y + gy) / 2
        line(cx, [(hx, hip_y), (kx, ky), (fx, fy)], z.pants, 22 * sc)
        line(cx, [(fx, fy), (fx + face_dir * 18 * sc, fy)], INK, 16 * sc)
    # torso: torn shirt, slouched
    cx.save()
    cx.translate(x, hip_y)
    cx.rotate(lean)
    sh = -180 * sc
    cx.rotate(shoulder_tilt * 0.5)
    cx.scale(thin, 1)
    cx.move_to(-62 * sc, sh + 18 * sc)
    cx.curve_to(-62 * sc, sh, -40 * sc, sh, -30 * sc, sh)
    cx.line_to(30 * sc, sh)
    cx.curve_to(44 * sc, sh, 62 * sc, sh, 62 * sc, sh + 18 * sc)
    cx.line_to(72 * sc, 6 * sc)
    rr = random.Random(seed)
    jag = [(72 - k * 18 + rr.uniform(-4, 4), (14 if k % 2 else -4) + rr.uniform(-5, 8)) for k in range(9)]
    for jx, jy in jag:
        cx.line_to(jx * sc, jy * sc)
    cx.line_to(-72 * sc, 6 * sc)
    cx.close_path()
    fs(cx, z.shirt, INK, 4 * sc)
    # rips and stains
    for k in range(3):
        ex = rr.uniform(-40, 40) * sc
        ey = rr.uniform(-140, -30) * sc
        cx.move_to(ex, ey)
        for j in range(4):
            cx.line_to(ex + rr.uniform(-14, 14) * sc, ey + rr.uniform(-12, 12) * sc)
        cx.close_path()
        src(cx, shade(z.shirt, -0.35))
        cx.fill()
    if z.hat == "mail":  # uniform: patch + bag strap + pocket
        line(cx, [(-56 * sc, sh + 10 * sc), (60 * sc, -20 * sc)], hexc("#5b3b22"), 14 * sc)
        rrect(cx, -48 * sc, sh + 50 * sc, 34 * sc, 26 * sc, 5 * sc)
        fs(cx, hexc("#2d4f8a"), INK, 3 * sc)
        line(cx, [(-44 * sc, sh + 63 * sc), (-18 * sc, sh + 63 * sc)], hexc("#e6e1cf"), 4 * sc)
    neck = (0, sh - 4 * sc)
    shl = (-56 * sc * thin, sh + 20 * sc)
    shr = (56 * sc * thin, sh + 20 * sc)
    cx.restore()
    c, sn = math.cos(lean + shoulder_tilt * 0.5), math.sin(lean + shoulder_tilt * 0.5)

    def tw(px, py):
        return x + px * c - py * sn, hip_y + px * sn + py * c

    # head: lolls with irregular motion, lags the body
    if still:
        loll = z.tilt0 + head_add
    else:
        loll = (z.tilt0 + noise1(t * 1.1, seed + 21) * 0.16 + snaps(t, seed) + head_add
                + (0.08 * math.sin(ph + 0.7) if walking else 0.05 * math.sin(t * 1.3 + seed)))
    nx, ny = tw(*neck)
    hx = nx + math.sin(loll) * R * 0.85 + face_dir * R * (0.12 + 0.35 * hunch)
    hy = ny - math.cos(loll) * R * 0.78 + R * 0.35 * hunch
    # arms (asymmetric)
    upper, fore = 70 * sc * arm_k, 70 * sc * arm_k
    hands = {}
    for side, sp in ((-1, shl), (1, shr)):
        sx, sy = tw(*sp)
        k = 0 if side < 0 else 1
        if arms is not None:
            a1, a2 = arms[k]
        else:
            reaching = (z.reach == 2) or (z.reach == 1 and side == face_dir)
            if reaching:
                a1 = face_dir * (1.75 + 0.15 * math.sin(ph * 0.5 + side) + noise1(t * 2, seed + k) * 0.15)
                a2 = a1 + face_dir * (0.15 + 0.2 * noise1(t * 3, seed + 30 + k))
            else:  # dangling, pendulum lagging the gait
                a1 = side * 0.12 + 0.3 * math.sin(ph - 1.2) * (0.6 if walking else 0.2) + noise1(t, seed + 50) * 0.1
                a2 = a1 + 0.25 * math.sin(ph - 1.8)
        ex_, ey_ = sx + math.sin(a1) * upper, sy + math.cos(a1) * upper
        hx2, hy2 = ex_ + math.sin(a2) * fore, ey_ + math.cos(a2) * fore
        line(cx, [(sx, sy), (ex_, ey_)], INK, 30 * sc)
        line(cx, [(sx, sy), (ex_, ey_)], z.shirt, 24 * sc)
        if k == 0 and lost_left is not None:
            # the forearm has come off: it drops and tumbles away
            ft = max(0.0, lost_left)
            ox, oy = ex_, ey_ + 0.5 * 2600 * ft * ft * sc
            rot = ft * 9.0
            hx2, hy2 = ox + math.sin(a2 + rot) * fore, oy + math.cos(a2 + rot) * fore
            ex_, ey_ = ox, oy
            ellipse(cx, sx + math.sin(a1) * upper, sy + math.cos(a1) * upper, 9 * sc, 9 * sc)
            src(cx, hexc("#5a2020"))
            cx.fill()
        line(cx, [(ex_, ey_), (hx2, hy2)], INK, 16 * sc)
        line(cx, [(ex_, ey_), (hx2, hy2)], z.skin, 11 * sc)
        # claw fingers
        ang = math.atan2(hy2 - ey_, hx2 - ex_)
        for f in (-0.5, 0, 0.5):
            line(cx, [(hx2, hy2), (hx2 + math.cos(ang + f) * 16 * sc, hy2 + math.sin(ang + f) * 16 * sc)], INK, 5 * sc)
        hands[k] = (hx2, hy2)
    if holding:
        holding(cx, hands)
    j = jaw if jaw is not None else 0.4 + 0.4 * max(0, noise1(t * 1.7, seed + 60))
    if blink is None:
        bp = (t * (0.31 + 0.05 * (seed % 3)) + seed * 0.37) % 1.0
        blink = 1.0 if bp < 0.06 else 0.0
    if getattr(z, "grim", False):
        zhead_grim(cx, z, hx, hy, R, t, jaw=j, look=look, blink=blink)
    else:
        zhead(cx, z, hx, hy, R, t, jaw=j, look=look, blink=blink)
    if z.hat == "mail":
        mail_cap(cx, hx, hy, R, loll)
    if sil is not None:
        pat = cx.pop_group()
        src(cx, sil)
        cx.mask(pat)
    return hx, hy, R, hands


def snaps(t, seed, period=1.6, amp=0.32, dur=0.07):
    """Held head angles that change with sudden, jerky snaps at irregular times."""
    def cell(i):
        r = random.Random(i * 7919 + seed * 31)
        return r.uniform(0.15, 0.85), r.uniform(-amp, amp)
    i = math.floor(t / period)
    off, tgt = cell(i)
    ts = (i + off) * period
    _, prev = cell(i - 1)
    if t < ts:
        off2, prev2 = cell(i - 1)
        _, prev = cell(i - 2)
        ts2 = (i - 1 + off2) * period
        x = min(1.0, (t - ts2) / dur)
        return prev + (prev2 - prev) * x
    x = min(1.0, (t - ts) / dur)
    return prev + (tgt - prev) * x


def mail_cap(cx, hx, hy, R, tilt):
    cx.save()
    cx.translate(hx, hy)
    cx.rotate(tilt * 0.6 + 0.12)
    cx.move_to(-R * 0.86, -R * 0.42)
    cx.curve_to(-R * 0.8, -R * 1.2, R * 0.8, -R * 1.2, R * 0.86, -R * 0.42)
    cx.close_path()
    fs(cx, hexc("#2c4a7e"), INK, R * 0.04)
    cx.move_to(-R * 0.86, -R * 0.42)
    cx.curve_to(-R * 0.3, -R * 0.5, R * 0.6, -R * 0.5, R * 1.25, -R * 0.32)
    cx.curve_to(R * 0.7, -R * 0.24, -R * 0.4, -R * 0.3, -R * 0.86, -R * 0.42)
    fs(cx, hexc("#1e3358"), INK, R * 0.035)
    rrect(cx, -R * 0.14, -R * 0.86, R * 0.28, R * 0.2, R * 0.04)
    fs(cx, YEL, INK, R * 0.02)
    cx.restore()


def package(cx, x, y, w, h, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    rrect(cx, -w / 2, -h / 2, w, h, 6)
    fs(cx, hexc("#c49a62"), INK, 4)
    cx.rectangle(-w * 0.08, -h / 2, w * 0.16, h)
    src(cx, hexc("#d9c08f"))
    cx.fill()
    rrect(cx, w * 0.12, -h * 0.3, w * 0.3, h * 0.3, 3)
    fs(cx, hexc("#f4efe2"), INK, 2.5)
    for k in range(3):
        line(cx, [(w * 0.16, -h * 0.22 + k * h * 0.08), (w * 0.36, -h * 0.22 + k * h * 0.08)], INK, 2)
    # stains
    ellipse(cx, -w * 0.28, h * 0.2, w * 0.1, h * 0.07)
    src(cx, hexc("#6b7a3a"), 0.55)
    cx.fill()
    cx.restore()


# ============================================================ props
def cookie(cx, x, y, r, rot=0.0, bite=False):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    ellipse(cx, 0, 0, r, r * 0.96)
    fs(cx, hexc("#d49a52"), INK, r * 0.06)
    rr = random.Random(int(r))
    for k in range(6):
        a = rr.uniform(0, 6.28)
        d = rr.uniform(0.15, 0.7) * r
        ellipse(cx, math.cos(a) * d, math.sin(a) * d, r * 0.12, r * 0.1, a)
        src(cx, hexc("#4a2b17"))
        cx.fill()
    if bite:
        ellipse(cx, r * 0.85, -r * 0.5, r * 0.32, r * 0.32)
        src(cx, (0, 0, 0, 0))
    cx.restore()


def charger(cx, x, y, s, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    rrect(cx, -40 * s, -30 * s, 80 * s, 60 * s, 12 * s)
    fs(cx, hexc("#f1efe9"), INK, 4 * s)
    for d in (-14, 14):
        rrect(cx, (d - 5) * s, -52 * s, 10 * s, 24 * s, 2 * s)
        fs(cx, hexc("#b7b7b7"), INK, 3 * s)
    cx.move_to(0, 30 * s)
    cx.curve_to(0, 90 * s, 90 * s, 40 * s, 110 * s, 110 * s)
    src(cx, INK)
    cx.set_line_width(14 * s)
    cx.stroke()
    cx.move_to(0, 30 * s)
    cx.curve_to(0, 90 * s, 90 * s, 40 * s, 110 * s, 110 * s)
    src(cx, hexc("#f1efe9"))
    cx.set_line_width(8 * s)
    cx.stroke()
    rrect(cx, 98 * s, 104 * s, 24 * s, 34 * s, 4 * s)
    fs(cx, hexc("#e2e0da"), INK, 3 * s)
    cx.restore()


def sock(cx, x, y, s, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.move_to(-30 * s, -90 * s)
    cx.line_to(30 * s, -90 * s)
    cx.line_to(30 * s, 20 * s)
    cx.curve_to(30 * s, 60 * s, 90 * s, 40 * s, 95 * s, 75 * s)
    cx.curve_to(98 * s, 105 * s, 60 * s, 110 * s, 20 * s, 95 * s)
    cx.curve_to(-25 * s, 80 * s, -30 * s, 50 * s, -30 * s, 20 * s)
    cx.close_path()
    fs(cx, hexc("#e9e4d8"), INK, 4 * s)
    for k in range(3):
        line(cx, [(-30 * s, (-80 + k * 14) * s), (30 * s, (-80 + k * 14) * s)], hexc("#c0392b"), 6 * s)
    ellipse(cx, 70 * s, 85 * s, 12 * s, 9 * s)  # hole in the toe
    src(cx, INK)
    cx.fill()
    cx.restore()


def backpack(cx, x, y, s, open_=0.0, rot=0.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    line(cx, [(-30 * s, -110 * s), (-30 * s, -150 * s), (30 * s, -150 * s), (30 * s, -110 * s)], INK, 12 * s)
    rrect(cx, -95 * s, -120 * s, 190 * s, 230 * s, 50 * s)
    fs(cx, hexc("#c4532f"), INK, 5 * s)
    rrect(cx, -65 * s, 10 * s, 130 * s, 80 * s, 20 * s)
    fs(cx, hexc("#a8401f"), INK, 4 * s)
    # zipper line, opens
    zx = -80 * s + 160 * s * (1 - open_)
    line(cx, [(-80 * s, -60 * s), (80 * s, -60 * s)], INK, 4 * s)
    if open_ > 0:
        cx.move_to(zx, -60 * s)
        cx.curve_to(zx - 30 * s, -40 * s, 70 * s, -30 * s, 80 * s, -60 * s)
        src(cx, hexc("#2a120a"))
        cx.fill()
    rrect(cx, zx - 6 * s, -66 * s, 12 * s, 26 * s, 3 * s)
    fs(cx, hexc("#d9d9d9"), INK, 2.5 * s)
    cx.restore()


def flashlight(cx, x, y, ang, s=1.0, on=True):
    """ang: direction the lamp points (radians, screen)."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    rrect(cx, -40 * s, -11 * s, 62 * s, 22 * s, 6 * s)
    fs(cx, hexc("#3a3f47"), INK, 3 * s)
    rrect(cx, 18 * s, -17 * s, 22 * s, 34 * s, 5 * s)
    fs(cx, hexc("#5a616b"), INK, 3 * s)
    if on:
        ellipse(cx, 41 * s, 0, 4 * s, 14 * s)
        src(cx, hexc("#fff7cf"))
        cx.fill()
    cx.restore()


def hero_back(cx, x, y, s=1.0, cloth=None, t=0.0, turn=0.0):
    """Over-the-shoulder: the hero seen from behind. (x, y) = centre of the head."""
    cloth = cloth or HOOD
    R = 142 * s
    sh_y = y + R * 0.8
    cx.move_to(x - 210 * s, sh_y + 400 * s)
    cx.curve_to(x - 210 * s, sh_y + 60 * s, x - 170 * s, sh_y, x - 90 * s, sh_y)
    cx.line_to(x + 90 * s, sh_y)
    cx.curve_to(x + 170 * s, sh_y, x + 210 * s, sh_y + 60 * s, x + 210 * s, sh_y + 400 * s)
    cx.close_path()
    fs(cx, shade(cloth, -0.1), INK, 4 * s)
    # hood lying on the back
    cx.move_to(x - 130 * s, sh_y - 10 * s)
    cx.curve_to(x - 140 * s, sh_y + 170 * s, x + 140 * s, sh_y + 170 * s, x + 130 * s, sh_y - 10 * s)
    cx.close_path()
    fs(cx, shade(cloth, -0.28), INK, 4 * s)
    ellipse(cx, x + turn * 8 * s, y, R, R * 0.985)
    gg = cairo.RadialGradient(x - R * 0.3, y - R * 0.35, R * 0.1, x, y, R * 1.05)
    gg.add_color_stop_rgba(0, *HEAD)
    gg.add_color_stop_rgba(1, *shade(HEAD, -0.12))
    cx.set_source(gg)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(4.5 * s)
    cx.stroke()


def zhead_grim(cx, z, hx, hy, R, t, jaw=0.4, look=(0, 0), blink=0.0):
    """Unsettling, restrained infected face: grey skin, sunken clouded eyes, slack mouth, no cartoon teeth."""
    r = random.Random(z.seed * 13)
    sk = z.skin
    pts = []
    for i in range(16):
        a = i / 16 * 2 * math.pi
        rr = R * (1 + 0.03 * math.sin(a * 3 + z.seed) + 0.015 * math.sin(a * 7 + z.seed))
        pts.append((hx + math.cos(a) * rr, hy + math.sin(a) * rr * 1.02))
    smooth_poly(cx, pts)
    g = cairo.RadialGradient(hx - R * 0.35, hy - R * 0.4, R * 0.1, hx + R * 0.1, hy + R * 0.1, R * 1.1)
    g.add_color_stop_rgba(0, *shade(sk, 0.08))
    g.add_color_stop_rgba(0.7, *sk)
    g.add_color_stop_rgba(1, *shade(sk, -0.35))
    cx.set_source(g)
    cx.fill_preserve()
    src(cx, INK)
    cx.set_line_width(R * 0.04)
    cx.stroke()
    cx.save()
    smooth_poly(cx, pts)
    cx.clip()
    # bruising and a wound
    for k in range(4):
        ellipse(cx, hx + r.uniform(-0.6, 0.6) * R, hy + r.uniform(-0.5, 0.6) * R, R * r.uniform(0.12, 0.25),
                R * r.uniform(0.08, 0.16), r.uniform(0, 3))
        src(cx, (0.25, 0.22, 0.3, 0.18))
        cx.fill()
    wx, wy = hx + R * r.choice((-0.55, 0.5)), hy - R * r.uniform(0.1, 0.5)
    ellipse(cx, wx, wy, R * 0.12, R * 0.06, r.uniform(-0.5, 0.5))
    src(cx, (0.37, 0.15, 0.14, 0.75))
    cx.fill()
    line(cx, [(wx - R * 0.02, wy + R * 0.04), (wx + R * 0.02, wy + R * 0.2)], (0.37, 0.15, 0.14, 0.5), R * 0.025)
    cx.restore()
    # hair: thin, dark, uneven
    if z.hair != "bald":
        for k in range(7 if z.hair == "tuft" else 11):
            a = -math.pi / 2 + (k - 4) * 0.2 + r.uniform(-0.05, 0.05)
            bx, by = hx + math.cos(a) * R * 0.97, hy + math.sin(a) * R * 0.99
            line(cx, [(bx, by), (bx + math.cos(a + 0.5) * R * 0.22, by + math.sin(a + 0.5) * R * 0.25 + R * 0.1)],
                 (0.12, 0.12, 0.12, 0.9), R * 0.035)
    # sunken sockets + clouded eyes (pupils barely there), asymmetric
    lx, ly = hx - R * 0.32, hy - R * 0.06
    rx, ry = hx + R * 0.30, hy - R * 0.02
    for (ex, ey, er) in ((lx, ly, R * 0.15), (rx, ry, R * 0.12)):
        ellipse(cx, ex, ey + er * 0.1, er * 1.6, er * 1.35)
        src(cx, (0.08, 0.07, 0.09, 0.7))
        cx.fill()
        ry_ = er * (1 - blink)
        if ry_ > 1:
            ellipse(cx, ex, ey, er, ry_)
            fs(cx, hexc("#c8cbc2"), INK, R * 0.03)
            ellipse(cx, ex + look[0] * er * 0.4, ey + look[1] * er * 0.3, er * 0.22, er * 0.22 * (1 - blink))
            src(cx, (0.35, 0.36, 0.38, 0.8))
            cx.fill()
        # heavy upper lid
        line(cx, [(ex - er * 1.1, ey - er * 0.55), (ex + er * 1.1, ey - er * 0.35)], INK, R * 0.04)
    # slack mouth, slightly off-centre
    mx, my = hx + R * 0.05, hy + R * 0.45
    op = R * (0.05 + 0.14 * jaw)
    cx.move_to(mx - R * 0.2, my)
    cx.curve_to(mx - R * 0.1, my - R * 0.03, mx + R * 0.12, my - R * 0.02, mx + R * 0.18, my + R * 0.02)
    cx.curve_to(mx + R * 0.12, my + op, mx - R * 0.12, my + op * 1.1, mx - R * 0.2, my)
    cx.close_path()
    fs(cx, (0.1, 0.07, 0.07, 1), INK, R * 0.03)


def grim(seed, skin, shirt, pants, **kw):
    kw["R"] = kw.get("R", 84) * 0.8
    z = Zed(seed, skin, shirt, pants, **kw)
    z.grim = True
    return z


INFECTED = [
    # tall and thin, head hanging at a wrong angle, arms too long
    grim(11, "#5f6b62", "#3b3f3a", "#2b2d33", R=78, size=1.16, hair="tuft", limp=0.75, reach=0, speed=0.55,
         tilt0=0.62),
    # broad, deeply hunched, neck pushed forward
    grim(12, "#6b6c60", "#4d3530", "#2f2e2c", R=86, size=1.04, hair="bald", limp=0.3, reach=1, speed=0.45,
         tilt0=-0.3),
    # dragging leg, one arm hanging dead
    grim(13, "#5d6862", "#323c42", "#26282c", R=84, size=0.98, hair="comb", limp=0.95, reach=0, speed=0.65,
         tilt0=0.45),
    # small and crooked, shoulders twisted
    grim(14, "#6e6a5c", "#4a4538", "#2c2a26", R=80, size=0.9, hair="tuft", limp=0.5, reach=1, speed=0.5,
         tilt0=-0.55),
    # heavy coat, slow, reaching
    grim(15, "#5a6461", "#5b2e2c", "#2a2a2e", R=80, size=1.1, hair="bald", limp=0.6, reach=1, speed=0.4,
         tilt0=0.3),
]
for _z, (_h, _t, _a, _ts) in zip(INFECTED, ((0.2, 0.72, 1.4, 0.0), (0.6, 1.2, 1.15, 0.1), (0.25, 0.9, 1.3, -0.25),
                                           (0.4, 0.85, 1.1, 0.35), (0.3, 1.1, 1.25, 0.05))):
    _z.hunch, _z.thin, _z.arm, _z.tilt_sh = _h, _t, _a, _ts

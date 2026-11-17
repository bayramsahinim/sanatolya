"""Just Needy cast for the vertical short.

All characters share the channel design: big round white head, thick black outline, lavender
crescent shading, vertical oval eyes, thin brows, thin line mouth. The hero wears the blue
hoodie; everyone else is dressed in greys so the hero is the only colour on screen.

person(f, x, ground_y, R, spec, ...) draws a figure whose feet touch (x, ground_y) and whose
head radius is R. bust(...) draws the same character cropped at the chest.
"""
import math
from dataclasses import dataclass, field, replace

from .look import (BLUE, BLUE_D, BLUE_L, GREY1, GREY2, GREY3, GREY4, INK, SKIN_SHADE, WHITE, ellipse,
                   hexc, rrect, src)

D2R = math.pi / 180


@dataclass
class Spec:
    body: str = "hoodie"          # hoodie | sweater | cardigan | shirt | apron | jacket | tee | dress
    col: tuple = BLUE
    col_d: tuple = BLUE_D
    pants: tuple = hexc("#262a33")
    hair: str = ""                # bun | pigtails | ponytail | short | side | chef | beanie | long | part | cap
    hair_col: tuple = GREY4
    glasses: bool = False
    mustache: bool = False
    tie: bool = False
    grad_cap: bool = False
    backpack: bool = False
    outline: float = 0.065        # outline width relative to R

    def but(self, **kw):
        return replace(self, **kw)


HERO = Spec()
MOM = Spec(body="cardigan", col=hexc("#9a9fab"), col_d=hexc("#7a7f8b"), hair="bun", hair_col=hexc("#b9bcc6"),
           pants=hexc("#4a4e58"))
DAD = Spec(body="sweater", col=hexc("#6b707c"), col_d=hexc("#555a66"), hair="side", hair_col=hexc("#c9ccd4"),
           glasses=True, mustache=True, pants=hexc("#3a3e48"))
BAKER = Spec(body="apron", col=hexc("#e9eaee"), col_d=hexc("#c3c6ce"), hair="chef", pants=hexc("#3a3e48"))
COWORKER = Spec(body="shirt", col=hexc("#c9ccd4"), col_d=hexc("#a6aab4"), hair="part", hair_col=hexc("#2e323b"),
                tie=True)
FRIEND = Spec(body="jacket", col=hexc("#7d828e"), col_d=hexc("#636874"), hair="short", hair_col=hexc("#2e323b"))
DAUGHTER = Spec(body="dress", col=hexc("#b2b6c0"), col_d=hexc("#9095a0"), hair="pigtails", hair_col=hexc("#3a3e48"))

CROWD = [
    Spec(body="jacket", col=hexc("#5f6470"), col_d=hexc("#4a4f5b"), hair="short", hair_col=GREY4),
    Spec(body="coat", col=hexc("#8a8f9b"), col_d=hexc("#6f7480"), hair="long", hair_col=hexc("#3a3e48")),
    Spec(body="tee", col=hexc("#a3a7b1"), col_d=hexc("#868a95"), hair="cap", hair_col=hexc("#3a3e48")),
    Spec(body="sweater", col=hexc("#4c515c"), col_d=hexc("#3c414b"), hair="ponytail", hair_col=hexc("#2a2d35")),
    Spec(body="coat", col=hexc("#6e7380"), col_d=hexc("#585d69"), hair="side", hair_col=GREY2, glasses=True),
    Spec(body="shirt", col=hexc("#b8bcc6"), col_d=hexc("#9a9ea8"), hair="part", hair_col=hexc("#2a2d35")),
    Spec(body="jacket", col=hexc("#3f434d"), col_d=hexc("#30343d"), hair="beanie", hair_col=hexc("#6b707c")),
    Spec(body="cardigan", col=hexc("#959aa6"), col_d=hexc("#7a7f8b"), hair="bun", hair_col=hexc("#2e323b")),
]


@dataclass
class Face:
    look: tuple = (0.0, 0.0)      # -1..1 eye/feature offset (head turn)
    eyes: str = "open"            # open | closed | half | wide | happy
    brows: str = "neutral"        # neutral | raised | sad | worried | skeptic | soft | none
    mouth: str = "smile"          # smile | flat | sad | o | open | small | big | none | wobble
    blink: float = 0.0            # 0..1
    tear: float = 0.0
    view: str = "front"           # front | back

    def but(self, **kw):
        return replace(self, **kw)


def blink_at(t, seed=0, period=3.7):
    """0..1 blink amount, deterministic."""
    ph = (t + seed * 1.37) % (period + (seed % 3) * 0.6)
    if ph < 0.16:
        return math.sin(ph / 0.16 * math.pi)
    return 0.0


# ------------------------------------------------------------------ helpers
def _fs(c, fillc, lw, a=1.0, stroke=True):
    src(c, fillc, a)
    if stroke:
        c.fill_preserve()
        src(c, INK, a)
        c.set_line_width(lw)
        c.stroke()
    else:
        c.fill()


def _capsule(c, x0, y0, x1, y1, w):
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
    c.new_sub_path()
    c.move_to(x0 + nx, y0 + ny)
    c.line_to(x1 + nx, y1 + ny)
    c.arc(x1, y1, w / 2, ang + math.pi / 2, ang - math.pi / 2 + 2 * math.pi)
    c.line_to(x0 - nx, y0 - ny)
    c.arc(x0, y0, w / 2, ang - math.pi / 2, ang + math.pi / 2)
    c.close_path()


# ------------------------------------------------------------------ head
def head(c, x, y, R, spec, face, a=1.0):
    lw = R * spec.outline
    lx, ly = face.look
    _hair_back(c, x, y, R, spec, face, a)
    # base with lavender crescent shading on the left
    c.arc(x, y, R, 0, 2 * math.pi)
    src(c, SKIN_SHADE, a)
    c.fill()
    c.save()
    c.arc(x, y, R, 0, 2 * math.pi)
    c.clip()
    c.arc(x + R * 0.13, y - R * 0.04, R * 0.94, 0, 2 * math.pi)
    src(c, WHITE, a)
    c.fill()
    c.restore()
    _hair_front_fill(c, x, y, R, spec, face, a)
    c.arc(x, y, R, 0, 2 * math.pi)
    src(c, INK, a)
    c.set_line_width(lw)
    c.stroke()
    if face.view == "front":
        _face(c, x + lx * R * 0.3, y + ly * R * 0.12, R, face, spec, a)
    _hair_top(c, x, y, R, spec, face, a)


def _face(c, x, y, R, fc, spec, a):
    lw = R * 0.045
    ex = R * 0.25
    ey = y - R * 0.08
    erx, ery = R * 0.085, R * 0.175
    bl = max(fc.blink, 1.0 if fc.eyes == "closed" else 0.0)
    for s in (-1, 1):
        exx = x + s * ex
        if fc.eyes == "happy":
            c.arc(exx, ey + ery * 0.4, erx * 1.3, math.pi * 1.1, math.pi * 1.9)
            src(c, INK, a)
            c.set_line_width(lw)
            c.stroke()
            continue
        k = 1.0 - bl
        sc = {"half": 0.55, "wide": 1.15}.get(fc.eyes, 1.0)
        if k < 0.12:
            c.move_to(exx - erx * 1.2, ey + ery * 0.2)
            c.curve_to(exx - erx * 0.4, ey + ery * 0.45, exx + erx * 0.4, ey + ery * 0.45, exx + erx * 1.2, ey + ery * 0.2)
            src(c, INK, a)
            c.set_line_width(lw)
            c.stroke()
        else:
            hh = ery * sc * k
            ellipse(c, exx, ey + (ery - hh) * (0.6 if fc.eyes == "half" else 0.3), erx * (1.08 if fc.eyes == "wide" else 1), hh)
            src(c, INK, a)
            c.fill()
            if fc.eyes == "wide" and k > 0.5:
                c.arc(exx - erx * 0.25, ey - hh * 0.35, erx * 0.28, 0, 2 * math.pi)
                src(c, WHITE, a * 0.9)
                c.fill()
    # tear
    if fc.tear > 0:
        tx, ty = x + ex + R * 0.02, ey + ery + R * 0.05 + fc.tear * R * 0.25
        c.move_to(tx, ty - R * 0.07)
        c.curve_to(tx + R * 0.05, ty, tx + R * 0.045, ty + R * 0.06, tx, ty + R * 0.06)
        c.curve_to(tx - R * 0.045, ty + R * 0.06, tx - R * 0.05, ty, tx, ty - R * 0.07)
        src(c, hexc("#9cc0ff"), a * min(1, fc.tear * 3))
        c.fill()
    # brows: (outer, middle, inner) y offsets in R; outer end is away from the nose
    by = y - R * 0.42
    shapes = {
        "neutral": (0.02, -0.06, 0.0),
        "raised": (-0.02, -0.13, -0.05),
        "sad": (0.05, -0.01, -0.08),
        "worried": (0.07, 0.0, -0.11),
        "soft": (0.03, -0.04, 0.01),
        "frown": (-0.04, 0.0, 0.05),
    }
    if fc.brows != "none":
        for s in (-1, 1):
            name = fc.brows
            if name == "skeptic":
                name = "raised" if s > 0 else "neutral"
            yo, ym, yi = shapes[name]
            bx = x + s * ex
            p0 = (bx + s * R * 0.17, by + yo * R)
            p1 = (bx, by + ym * R)
            p2 = (bx - s * R * 0.15, by + yi * R)
            c.move_to(*p0)
            c.curve_to(p1[0], p1[1], p1[0], p1[1], p2[0], p2[1])
            src(c, INK, a)
            c.set_line_width(lw * 1.05)
            c.stroke()
    # mouth
    my = y + R * 0.33
    mw = R * 0.24
    c.set_line_width(lw)
    src(c, INK, a)
    m = fc.mouth
    if m == "smile":
        c.move_to(x - mw, my - R * 0.03)
        c.curve_to(x - mw * 0.4, my + R * 0.09, x + mw * 0.5, my + R * 0.09, x + mw * 1.05, my - R * 0.04)
        c.stroke()
    elif m == "big":
        c.move_to(x - mw * 1.1, my - R * 0.05)
        c.curve_to(x - mw * 0.6, my + R * 0.2, x + mw * 0.6, my + R * 0.2, x + mw * 1.1, my - R * 0.05)
        c.close_path()
        src(c, INK, a)
        c.fill()
    elif m == "small":
        c.move_to(x - mw * 0.5, my)
        c.curve_to(x - mw * 0.2, my + R * 0.05, x + mw * 0.2, my + R * 0.05, x + mw * 0.5, my)
        c.stroke()
    elif m == "flat":
        c.move_to(x - mw * 0.55, my + R * 0.02)
        c.line_to(x + mw * 0.55, my + R * 0.02)
        c.stroke()
    elif m == "sad":
        c.move_to(x - mw * 0.6, my + R * 0.06)
        c.curve_to(x - mw * 0.2, my - R * 0.02, x + mw * 0.2, my - R * 0.02, x + mw * 0.6, my + R * 0.06)
        c.stroke()
    elif m == "wobble":
        c.move_to(x - mw * 0.6, my + R * 0.04)
        c.curve_to(x - mw * 0.3, my - R * 0.02, x - mw * 0.1, my + R * 0.05, x + mw * 0.15, my + R * 0.01)
        c.curve_to(x + mw * 0.35, my - R * 0.02, x + mw * 0.5, my + R * 0.05, x + mw * 0.6, my + R * 0.04)
        c.stroke()
    elif m in ("o", "open"):
        rx, ry = (R * 0.06, R * 0.075) if m == "o" else (R * 0.11, R * 0.08)
        ellipse(c, x, my + R * 0.03, rx, ry)
        c.fill()


# ------------------------------------------------------------------ hair
def _hair_back(c, x, y, R, sp, fc, a):
    h = sp.hair
    if h == "bun":
        c.arc(x + (0 if fc.view == "back" else R * 0.05), y - R * 0.98, R * 0.33, 0, 2 * math.pi)
        _fs(c, sp.hair_col, R * sp.outline, a)
    elif h == "pigtails":
        for s in (-1, 1):
            ellipse(c, x + s * R * 1.0, y + R * 0.05, R * 0.24, R * 0.36)
            _fs(c, sp.hair_col, R * sp.outline, a)
    elif h == "ponytail":
        ellipse(c, x - R * 0.95, y + R * 0.1, R * 0.22, R * 0.45)
        _fs(c, sp.hair_col, R * sp.outline, a)
    elif h == "long":
        rrect(c, x - R * 1.06, y - R * 0.5, R * 2.12, R * 1.55, R * 0.6)
        _fs(c, sp.hair_col, R * sp.outline, a)


def _hair_front_fill(c, x, y, R, sp, fc, a):
    """Hair cap clipped to the head (drawn before the head outline)."""
    h = sp.hair
    if h in ("", "chef", "cap", "beanie", "side"):
        if h == "side":
            for s in (-1, 1):
                c.save()
                c.arc(x, y, R, 0, 2 * math.pi)
                c.clip()
                ellipse(c, x + s * R * 0.98, y - R * 0.05, R * 0.2, R * 0.38)
                src(c, sp.hair_col, a)
                c.fill()
                c.restore()
        return
    c.save()
    c.arc(x, y, R, 0, 2 * math.pi)
    c.clip()
    if fc.view == "back":
        ellipse(c, x, y - R * 0.1, R * 1.2, R * 1.0)
    elif h == "part":
        c.move_to(x - R * 1.1, y - R * 0.15)
        c.curve_to(x - R * 0.9, y - R * 0.6, x - R * 0.4, y - R * 0.5, x - R * 0.2, y - R * 0.62)
        c.curve_to(x + R * 0.3, y - R * 0.48, x + R * 0.9, y - R * 0.5, x + R * 1.1, y - R * 0.2)
        c.line_to(x + R * 1.1, y - R * 1.2)
        c.line_to(x - R * 1.1, y - R * 1.2)
        c.close_path()
    elif h == "short":
        c.move_to(x - R * 1.1, y - R * 0.2)
        for i in range(7):
            px = x - R * 0.95 + i * R * 0.32
            c.line_to(px + R * 0.12, y - R * 0.58 + (i % 2) * R * 0.1)
            c.line_to(px + R * 0.3, y - R * 0.5)
        c.line_to(x + R * 1.1, y - R * 0.2)
        c.line_to(x + R * 1.1, y - R * 1.2)
        c.line_to(x - R * 1.1, y - R * 1.2)
        c.close_path()
    else:  # bun, pigtails, ponytail, long: simple fringe with a soft middle part
        c.move_to(x - R * 1.1, y - R * 0.05)
        c.curve_to(x - R * 0.8, y - R * 0.55, x - R * 0.3, y - R * 0.65, x, y - R * 0.55)
        c.curve_to(x + R * 0.3, y - R * 0.65, x + R * 0.8, y - R * 0.55, x + R * 1.1, y - R * 0.05)
        c.line_to(x + R * 1.1, y - R * 1.2)
        c.line_to(x - R * 1.1, y - R * 1.2)
        c.close_path()
    src(c, sp.hair_col, a)
    c.fill()
    c.restore()


def _hair_top(c, x, y, R, sp, fc, a):
    lw = R * sp.outline
    h = sp.hair
    if h == "chef":
        top = y - R * 0.78
        rrect(c, x - R * 0.62, top - R * 0.3, R * 1.24, R * 0.42, R * 0.1)
        _fs(c, WHITE, lw, a)
        for dx, r in ((-0.4, 0.38), (0.0, 0.48), (0.4, 0.38)):
            c.arc(x + dx * R, top - R * 0.62, r * R, 0, 2 * math.pi)
            _fs(c, WHITE, lw, a)
        rrect(c, x - R * 0.62, top - R * 0.3, R * 1.24, R * 0.42, R * 0.1)
        _fs(c, WHITE, lw, a)
    elif h == "cap":
        c.arc(x, y - R * 0.18, R * 0.98, math.pi * 1.05, math.pi * 1.95)
        c.close_path()
        _fs(c, sp.hair_col, lw, a)
        if fc.view == "front":
            ellipse(c, x + R * 0.2, y - R * 0.28, R * 0.75, R * 0.12)
            _fs(c, sp.hair_col, lw, a)
    elif h == "beanie":
        c.arc(x, y - R * 0.12, R * 1.0, math.pi, 2 * math.pi)
        c.close_path()
        _fs(c, sp.hair_col, lw, a)
        rrect(c, x - R * 1.04, y - R * 0.32, R * 2.08, R * 0.3, R * 0.12)
        _fs(c, sp.hair_col, lw, a)
    if sp.grad_cap:
        c.move_to(x - R * 1.15, y - R * 0.85)
        c.line_to(x, y - R * 1.2)
        c.line_to(x + R * 1.15, y - R * 0.85)
        c.line_to(x, y - R * 0.55)
        c.close_path()
        _fs(c, hexc("#2e323b"), lw, a)
        c.move_to(x + R * 0.1, y - R * 0.85)
        c.line_to(x + R * 0.85, y - R * 0.7)
        c.line_to(x + R * 0.85, y - R * 0.35)
        src(c, WHITE, a)
        c.set_line_width(lw * 0.7)
        c.stroke()
    if fc.view == "front":
        lx = fc.look[0] * R * 0.3
        if sp.glasses:
            for s in (-1, 1):
                c.arc(x + lx + s * R * 0.25, y - R * 0.06, R * 0.2, 0, 2 * math.pi)
                src(c, INK, a)
                c.set_line_width(lw * 0.6)
                c.stroke()
            c.move_to(x + lx - R * 0.06, y - R * 0.08)
            c.line_to(x + lx + R * 0.06, y - R * 0.08)
            c.stroke()
        if sp.mustache:
            mx, my = x + lx, y + R * 0.2
            c.move_to(mx, my)
            c.curve_to(mx - R * 0.1, my - R * 0.08, mx - R * 0.3, my - R * 0.02, mx - R * 0.3, my + R * 0.06)
            c.curve_to(mx - R * 0.15, my + R * 0.02, mx - R * 0.05, my + R * 0.06, mx, my + R * 0.03)
            c.curve_to(mx + R * 0.05, my + R * 0.06, mx + R * 0.15, my + R * 0.02, mx + R * 0.3, my + R * 0.06)
            c.curve_to(mx + R * 0.3, my - R * 0.02, mx + R * 0.1, my - R * 0.08, mx, my)
            src(c, sp.hair_col if sp.hair_col != WHITE else GREY2, a)
            c.fill_preserve()
            src(c, INK, a)
            c.set_line_width(lw * 0.5)
            c.stroke()


# ------------------------------------------------------------------ body
@dataclass
class Arms:
    """Shoulder/elbow angles in degrees from straight down; + = outward from body."""
    l: tuple = (8.0, 0.0)
    r: tuple = (8.0, 0.0)
    phone: bool = False          # right hand holds a phone in front of chest
    wave: float = 0.0


def torso_path(c, x, ny, R, T, sp):
    sw = R * (0.98 if sp.body != "dress" else 0.8)
    bw = R * (0.9 if sp.body != "dress" else 1.1)
    c.move_to(x - R * 0.28, ny)
    c.curve_to(x - sw * 0.75, ny + R * 0.02, x - sw, ny + R * 0.18, x - sw, ny + R * 0.55)
    c.line_to(x - bw, ny + T - R * 0.12)
    c.curve_to(x - bw, ny + T, x - bw + R * 0.08, ny + T, x - bw + R * 0.15, ny + T)
    c.line_to(x + bw - R * 0.15, ny + T)
    c.curve_to(x + bw - R * 0.08, ny + T, x + bw, ny + T, x + bw, ny + T - R * 0.12)
    c.line_to(x + sw, ny + R * 0.55)
    c.curve_to(x + sw, ny + R * 0.18, x + sw * 0.75, ny + R * 0.02, x + R * 0.28, ny)
    c.close_path()


def body(c, x, ny, R, T, sp, fc, arms, a=1.0, legs=None):
    """Torso + arms. ny = neck base y. T = torso height. legs = leg length or None."""
    lw = R * sp.outline
    front = fc.view == "front"
    # legs
    if legs:
        for s in (-1, 1):
            rrect(c, x + s * R * 0.42 - R * 0.19, ny + T - R * 0.2, R * 0.38, legs + R * 0.2, R * 0.16)
            _fs(c, sp.pants, lw, a)
            ellipse(c, x + s * R * 0.45, ny + T + legs, R * 0.3, R * 0.14)
            _fs(c, hexc("#1d2027"), lw, a)
    # arms behind for back view are drawn the same; draw arms first then torso overlaps their tops
    shoulders = {}
    for s, (sh, el) in ((-1, arms.l), (1, arms.r)):
        sx, sy = x + s * R * 0.82, ny + R * 0.42
        la = R * 0.95
        a1 = (sh) * D2R
        ex_, ey_ = sx + s * math.sin(a1) * la, sy + math.cos(a1) * la
        a2 = (sh + el) * D2R
        hx, hy = ex_ + s * math.sin(a2) * la * 0.9, ey_ + math.cos(a2) * la * 0.9
        if s == 1 and arms.phone:
            ex_, ey_ = sx + R * 0.15, sy + R * 0.95
            hx, hy = x + R * 0.25, ny + R * 0.75
        shoulders[s] = (sx, sy, ex_, ey_, hx, hy)
    sleeve = sp.col_d if sp.body in ("hoodie", "jacket", "coat", "cardigan", "sweater") else sp.col
    if sp.body in ("tee", "dress", "apron"):
        sleeve = sp.col
    for s in (-1, 1):
        sx, sy, ex_, ey_, hx, hy = shoulders[s]
        if s == 1 and arms.phone:
            continue
        c.move_to(sx, sy)
        c.line_to(ex_, ey_)
        c.line_to(hx, hy)
        src(c, INK, a)
        c.set_line_width(R * 0.42 + lw * 2)
        c.stroke()
        c.move_to(sx, sy)
        c.line_to(ex_, ey_)
        c.line_to(hx, hy)
        src(c, sleeve if sp.body != "apron" else WHITE, a)
        c.set_line_width(R * 0.42)
        c.stroke()
        c.arc(hx, hy, R * 0.17, 0, 2 * math.pi)
        _fs(c, WHITE, lw * 0.8, a)
    # torso
    torso_path(c, x, ny, R, T, sp)
    _fs(c, sp.col, lw, a)
    # shading strip on the right
    c.save()
    torso_path(c, x, ny, R, T, sp)
    c.clip()
    c.rectangle(x + R * 0.62, ny, R * 0.6, T)
    src(c, sp.col_d, a * 0.55)
    c.fill()
    c.restore()
    torso_path(c, x, ny, R, T, sp)
    src(c, INK, a)
    c.set_line_width(lw)
    c.stroke()
    _clothing_details(c, x, ny, R, T, sp, fc, a)
    if arms.phone:
        sx, sy, ex_, ey_, hx, hy = shoulders[1]
        c.move_to(sx, sy)
        c.curve_to(sx + R * 0.1, sy + R * 0.6, ex_, ey_, hx + R * 0.1, hy + R * 0.05)
        src(c, INK, a)
        c.set_line_width(R * 0.42 + lw * 2)
        c.stroke()
        c.move_to(sx, sy)
        c.curve_to(sx + R * 0.1, sy + R * 0.6, ex_, ey_, hx + R * 0.1, hy + R * 0.05)
        src(c, sleeve, a)
        c.set_line_width(R * 0.42)
        c.stroke()
        # phone
        rrect(c, hx - R * 0.2, hy - R * 0.5, R * 0.4, R * 0.7, R * 0.07)
        _fs(c, hexc("#1b1e25"), lw * 0.7, a)
        rrect(c, hx - R * 0.15, hy - R * 0.44, R * 0.3, R * 0.56, R * 0.04)
        src(c, hexc("#cfe0ff"), a * 0.9)
        c.fill()
        c.arc(hx, hy + R * 0.05, R * 0.17, 0, 2 * math.pi)
        _fs(c, WHITE, lw * 0.8, a)


def _clothing_details(c, x, ny, R, T, sp, fc, a):
    lw = R * sp.outline
    front = fc.view == "front"
    b = sp.body
    if b == "hoodie":
        if front:
            # hood around the neck
            c.move_to(x - R * 0.62, ny + R * 0.05)
            c.curve_to(x - R * 0.7, ny + R * 0.32, x - R * 0.35, ny + R * 0.42, x, ny + R * 0.5)
            c.curve_to(x + R * 0.35, ny + R * 0.42, x + R * 0.7, ny + R * 0.32, x + R * 0.62, ny + R * 0.05)
            src(c, INK, a)
            c.set_line_width(lw * 0.9)
            c.stroke()
            # drawstrings
            for s in (-1, 1):
                sx = x + s * R * 0.14
                rrect(c, sx - R * 0.045, ny + R * 0.38, R * 0.09, R * 0.62, R * 0.045)
                _fs(c, BLUE_L, lw * 0.55, a)
                c.arc(sx, ny + R * 1.03, R * 0.06, 0, 2 * math.pi)
                _fs(c, BLUE_D, lw * 0.55, a)
            # pocket
            if T > R * 1.6:
                rrect(c, x - R * 0.55, ny + T - R * 0.62, R * 1.1, R * 0.45, R * 0.12)
                src(c, INK, a * 0.8)
                c.set_line_width(lw * 0.6)
                c.stroke()
        else:
            # hood on the back
            c.move_to(x - R * 0.6, ny - R * 0.05)
            c.curve_to(x - R * 0.75, ny + R * 0.5, x - R * 0.4, ny + R * 0.85, x, ny + R * 0.9)
            c.curve_to(x + R * 0.4, ny + R * 0.85, x + R * 0.75, ny + R * 0.5, x + R * 0.6, ny - R * 0.05)
            _fs(c, BLUE_D, lw * 0.9, a)
    elif b in ("cardigan", "jacket", "coat") and front:
        c.move_to(x, ny + R * 0.25)
        c.line_to(x, ny + T)
        src(c, INK, a)
        c.set_line_width(lw * 0.7)
        c.stroke()
        c.move_to(x - R * 0.3, ny + R * 0.02)
        c.line_to(x, ny + R * 0.45)
        c.line_to(x + R * 0.3, ny + R * 0.02)
        c.stroke()
        if b == "cardigan":
            for i in range(3):
                c.arc(x + R * 0.1, ny + R * (0.7 + i * 0.4), R * 0.04, 0, 2 * math.pi)
                src(c, INK, a)
                c.fill()
    elif b == "shirt" and front:
        c.move_to(x - R * 0.28, ny)
        c.line_to(x - R * 0.12, ny + R * 0.22)
        c.line_to(x, ny + R * 0.05)
        c.line_to(x + R * 0.12, ny + R * 0.22)
        c.line_to(x + R * 0.28, ny)
        src(c, INK, a)
        c.set_line_width(lw * 0.7)
        c.stroke()
        if sp.tie:
            c.move_to(x, ny + R * 0.08)
            c.line_to(x - R * 0.1, ny + R * 0.2)
            c.line_to(x - R * 0.06, ny + R * 1.0)
            c.line_to(x, ny + R * 1.12)
            c.line_to(x + R * 0.06, ny + R * 1.0)
            c.line_to(x + R * 0.1, ny + R * 0.2)
            c.close_path()
            _fs(c, hexc("#2e323b"), lw * 0.6, a)
    elif b == "apron" and front:
        rrect(c, x - R * 0.55, ny + R * 0.45, R * 1.1, T - R * 0.45, R * 0.12)
        _fs(c, hexc("#c3c6ce"), lw * 0.7, a)
        rrect(c, x - R * 0.3, ny + R * 1.0, R * 0.6, R * 0.32, R * 0.06)
        src(c, INK, a)
        c.set_line_width(lw * 0.5)
        c.stroke()
    elif b == "sweater" and front:
        c.arc(x, ny - R * 0.05, R * 0.34, math.pi * 0.15, math.pi * 0.85)
        src(c, INK, a)
        c.set_line_width(lw * 0.7)
        c.stroke()
        for yy in (T - R * 0.18,):
            c.move_to(x - R * 0.85, ny + yy)
            c.line_to(x + R * 0.85, ny + yy)
            c.stroke()
    if sp.backpack and front:
        for s in (-1, 1):
            c.move_to(x + s * R * 0.55, ny + R * 0.15)
            c.line_to(x + s * R * 0.6, ny + R * 1.1)
            src(c, hexc("#2e323b"), a)
            c.set_line_width(R * 0.12)
            c.stroke()


# ------------------------------------------------------------------ figures
def person(f_or_c, x, ground, R, spec, face=None, arms=None, a=1.0, T=None, legs=None, bob=0.0, tilt=0.0):
    """Full figure standing on `ground`. Returns head centre (x, y)."""
    c = f_or_c.cx if hasattr(f_or_c, "cx") else f_or_c
    face = face or Face()
    arms = arms or Arms()
    T = T if T is not None else R * 1.85
    legs = legs if legs is not None else R * 1.25
    ny = ground - legs - T + bob
    hy = ny - R * 0.95
    c.save()
    # neck
    rrect(c, x - R * 0.12, ny - R * 0.25, R * 0.24, R * 0.35, R * 0.05)
    _fs(c, WHITE, R * spec.outline * 0.8, a)
    body(c, x, ny, R, T, spec, face, arms, a, legs=legs)
    if face.view == "back" and spec.body == "hoodie":
        pass
    c.translate(x, hy + R * 0.9)
    c.rotate(tilt * D2R)
    c.translate(-x, -(hy + R * 0.9))
    head(c, x, hy, R, spec, face, a)
    c.restore()
    return x, hy


def bust(f_or_c, x, ny, R, spec, face=None, arms=None, a=1.0, T=None, tilt=0.0):
    """Character from the chest up; ny = neck base. Torso continues down T (default to frame bottom)."""
    c = f_or_c.cx if hasattr(f_or_c, "cx") else f_or_c
    face = face or Face()
    arms = arms or Arms()
    T = T if T is not None else R * 3.0
    hy = ny - R * 0.95
    c.save()
    rrect(c, x - R * 0.12, ny - R * 0.25, R * 0.24, R * 0.35, R * 0.05)
    _fs(c, WHITE, R * spec.outline * 0.8, a)
    body(c, x, ny, R, T, spec, face, arms, a, legs=None)
    c.translate(x, hy + R * 0.9)
    c.rotate(tilt * D2R)
    c.translate(-x, -(hy + R * 0.9))
    head(c, x, hy, R, spec, face, a)
    c.restore()
    return x, hy


def head_y(ground, R, T=None, legs=None, bob=0.0):
    T = T if T is not None else R * 1.85
    legs = legs if legs is not None else R * 1.25
    return ground - legs - T + bob - R * 0.95

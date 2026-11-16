"""Bust-shot character rig and table props for vertical Just Needy Shorts.

Characters follow the official mascot sheet: white circular head with a soft lavender
crescent on the shadow side, black oval eyes, simple brows, small mouth, hoodie with
hood collar, V-neck and drawstrings, heavy clean black outlines.
"""
import math

import cairo

from cinecode.core import (OUTLINE, circle, ellipse, fs, hexc, line, mix, rrect, shade, smooth_poly, src)

HEAD_FILL = hexc("#FBFAFD")
HEAD_SHADE = hexc("#DCD8EF")
NECK_FILL = hexc("#F4F2F8")
MOUTH_DARK = hexc("#3B1424")
TONGUE = hexc("#E86C7C")

HOODIES = {
    "blue": hexc("#0A66F5"),      # Just Needy hero
    "burgundy": hexc("#8E2338"),  # best friend
    "rose": hexc("#D88F9F"),
    "mustard": hexc("#D9A441"),
    "sage": hexc("#7FA58E"),
    "teal": hexc("#3E8C99"),
    "slate": hexc("#8B93A6"),
}


class Face:
    """Expression state. Units are fractions of head radius R."""

    def __init__(self, facing=0.0, look=(0.0, 0.0), blink=0.0, eyes="open", brow_l=(0.0, 0.0),
                 brow_r=(0.0, 0.0), mouth="smile", mouth_amt=0.5, tilt=0.0, bob=0.0, smirk=0.0):
        self.facing = facing      # -1 (turned left) .. 1 (turned right)
        self.look = look          # extra eye shift
        self.blink = blink        # 0 open .. 1 closed
        self.eyes = eyes          # "open" | "happy"
        self.brow_l = brow_l      # (raise, angle) angle>0 = angry (inner end down)
        self.brow_r = brow_r
        self.mouth = mouth        # smile | flat | frown | laugh | talk
        self.mouth_amt = mouth_amt
        self.tilt = tilt          # radians
        self.bob = bob            # vertical offset in R
        self.smirk = smirk        # lifts the mouth's right corner


# ---------------------------------------------------------------- body
def draw_body(cx, x, y, R, color, breathe=0.0):
    """Hoodie bust. (x, y) = head centre. Drawn before the head."""
    lw = R * 0.062
    dark = shade(color, -0.22)
    sy = 1 + breathe * 0.012
    cx.save()
    cx.translate(x, y + R * 0.9)
    cx.scale(1, sy)
    cx.translate(-x, -(y + R * 0.9))
    # torso / shoulders
    smooth_poly(cx, [
        (x - R * 0.55, y + R * 1.05), (x - R * 1.25, y + R * 1.35), (x - R * 1.62, y + R * 2.1),
        (x - R * 1.72, y + R * 3.4), (x + R * 1.72, y + R * 3.4), (x + R * 1.62, y + R * 2.1),
        (x + R * 1.25, y + R * 1.35), (x + R * 0.55, y + R * 1.05)], close=True, k=0.7)
    fs(cx, color, OUTLINE, lw)
    # sleeve folds
    for s in (-1, 1):
        cx.move_to(x + s * R * 1.12, y + R * 2.0)
        cx.curve_to(x + s * R * 1.18, y + R * 2.4, x + s * R * 1.12, y + R * 2.8, x + s * R * 1.04, y + R * 3.1)
        src(cx, OUTLINE)
        cx.set_line_width(lw * 0.7)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
        cx.move_to(x + s * R * 1.32, y + R * 1.75)
        cx.curve_to(x + s * R * 1.45, y + R * 2.1, x + s * R * 1.42, y + R * 2.5, x + s * R * 1.36, y + R * 2.9)
        src(cx, dark, 0.55)
        cx.set_line_width(lw * 1.4)
        cx.stroke()
    # hood collar (behind the neck, wraps the shoulders)
    smooth_poly(cx, [
        (x - R * 0.2, y + R * 0.78), (x - R * 0.9, y + R * 0.82), (x - R * 1.18, y + R * 1.08),
        (x - R * 1.02, y + R * 1.42), (x - R * 0.55, y + R * 1.38), (x, y + R * 1.62),
        (x + R * 0.55, y + R * 1.38), (x + R * 1.0, y + R * 1.4), (x + R * 1.12, y + R * 1.06),
        (x + R * 0.85, y + R * 0.82), (x + R * 0.2, y + R * 0.78)], close=True, k=0.75)
    fs(cx, color, OUTLINE, lw)
    # hood inner shadow
    cx.move_to(x - R * 0.95, y + R * 1.05)
    cx.curve_to(x - R * 0.8, y + R * 0.95, x - R * 0.55, y + R * 0.95, x - R * 0.38, y + R * 1.0)
    src(cx, dark, 0.8)
    cx.set_line_width(lw * 1.3)
    cx.stroke()
    # neck + V opening
    cx.move_to(x - R * 0.36, y + R * 0.86)
    cx.line_to(x + R * 0.36, y + R * 0.86)
    cx.line_to(x + R * 0.06, y + R * 1.5)
    cx.line_to(x - R * 0.02, y + R * 1.5)
    cx.close_path()
    fs(cx, NECK_FILL, OUTLINE, lw * 0.8)
    # drawstrings
    for s in (-1, 1):
        x0 = x + s * R * 0.32
        cx.move_to(x0, y + R * 1.42)
        cx.line_to(x0 + s * R * 0.02, y + R * 2.3)
        src(cx, OUTLINE)
        cx.set_line_width(lw * 1.9)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
        cx.move_to(x0, y + R * 1.42)
        cx.line_to(x0 + s * R * 0.02, y + R * 2.3)
        src(cx, shade(color, -0.05))
        cx.set_line_width(lw * 0.75)
        cx.stroke()
        circle(cx, x0 + s * R * 0.02, y + R * 2.36, R * 0.055)
        fs(cx, color, OUTLINE, lw * 0.6)
        circle(cx, x0 + s * R * 0.02, y + R * 1.42, R * 0.05)
        fs(cx, color, OUTLINE, lw * 0.6)
    cx.restore()


# ---------------------------------------------------------------- head
def _brow(cx, bx, by, R, side, raise_, angle, lw):
    """side -1 = viewer-left brow, +1 = viewer-right brow."""
    w = R * 0.34
    cx.save()
    cx.translate(bx, by - raise_ * R * 0.12)
    cx.rotate(side * -angle * 0.5)
    cx.move_to(-w / 2, R * 0.03)
    cx.curve_to(-w * 0.25, -R * 0.07, w * 0.25, -R * 0.08, w / 2, R * 0.02)
    src(cx, OUTLINE)
    cx.set_line_width(lw)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.restore()


def _mouth(cx, mx, my, R, f, lw, t):
    a = f.mouth_amt
    w = R * 0.3
    sm = f.smirk * R * 0.06
    if f.mouth == "smile":
        cx.move_to(mx - w, my - R * 0.02)
        cx.curve_to(mx - w * 0.5, my + R * 0.16 * a, mx + w * 0.4, my + R * 0.16 * a, mx + w * 0.95, my - R * 0.03 - sm)
        src(cx, OUTLINE)
        cx.set_line_width(lw * 0.85)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    elif f.mouth == "flat":
        cx.move_to(mx - w * 0.7, my + R * 0.03)
        cx.curve_to(mx - w * 0.2, my + R * 0.05, mx + w * 0.3, my + R * 0.05, mx + w * 0.7, my + R * 0.01 - sm)
        src(cx, OUTLINE)
        cx.set_line_width(lw * 0.85)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    elif f.mouth == "frown":
        cx.move_to(mx - w * 0.6, my + R * 0.09)
        cx.curve_to(mx - w * 0.25, my - R * 0.03 * (0.5 + a), mx + w * 0.25, my - R * 0.03 * (0.5 + a),
                    mx + w * 0.6, my + R * 0.09)
        src(cx, OUTLINE)
        cx.set_line_width(lw * 0.85)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    elif f.mouth in ("laugh", "talk"):
        if f.mouth == "laugh":
            ww, hh = w * 0.95, R * (0.16 + 0.12 * a)
            cx.move_to(mx - ww, my - R * 0.02)
            cx.curve_to(mx - ww * 0.4, my + R * 0.01, mx + ww * 0.4, my + R * 0.01, mx + ww, my - R * 0.02)
            cx.curve_to(mx + ww * 0.85, my + hh * 1.25, mx - ww * 0.85, my + hh * 1.25, mx - ww, my - R * 0.02)
            cx.close_path()
        else:
            ellipse(cx, mx, my + R * 0.03, w * 0.35 + R * 0.05 * a, R * (0.03 + 0.09 * a))
        cx.save()
        fs(cx, MOUTH_DARK, None, 0)
        cx.restore()
        # tongue (clipped)
        cx.save()
        if f.mouth == "laugh":
            cx.move_to(mx - ww, my - R * 0.02)
            cx.curve_to(mx - ww * 0.4, my + R * 0.01, mx + ww * 0.4, my + R * 0.01, mx + ww, my - R * 0.02)
            cx.curve_to(mx + ww * 0.85, my + hh * 1.25, mx - ww * 0.85, my + hh * 1.25, mx - ww, my - R * 0.02)
            cx.close_path()
            cx.clip()
            ellipse(cx, mx + ww * 0.1, my + hh * 1.05, ww * 0.55, hh * 0.45)
            fs(cx, TONGUE, None, 0)
        cx.restore()
        if f.mouth == "laugh":
            cx.move_to(mx - ww, my - R * 0.02)
            cx.curve_to(mx - ww * 0.4, my + R * 0.01, mx + ww * 0.4, my + R * 0.01, mx + ww, my - R * 0.02)
            cx.curve_to(mx + ww * 0.85, my + hh * 1.25, mx - ww * 0.85, my + hh * 1.25, mx - ww, my - R * 0.02)
            cx.close_path()
        else:
            ellipse(cx, mx, my + R * 0.03, w * 0.35 + R * 0.05 * a, R * (0.03 + 0.09 * a))
        fs(cx, None, OUTLINE, lw * 0.8)


def draw_head(cx, x, y, R, f, t=0.0):
    lw = R * 0.062
    y = y + f.bob * R
    cx.save()
    cx.translate(x, y + R * 0.9)
    cx.rotate(f.tilt)
    cx.translate(-x, -(y + R * 0.9))
    # skull + shadow crescent on the side turned away from the light
    circle(cx, x, y, R)
    cx.save()
    cx.clip_preserve()
    src(cx, HEAD_FILL)
    cx.fill()
    side = -1  # key light from upper right, as on the mascot sheet
    cx.push_group()
    circle(cx, x, y, R * 1.02)
    src(cx, HEAD_SHADE)
    cx.fill()
    cx.set_operator(cairo.OPERATOR_CLEAR)
    circle(cx, x - side * R * 0.2, y - R * 0.08, R * 0.95)
    cx.fill()
    cx.pop_group_to_source()
    cx.paint()
    cx.restore()
    circle(cx, x, y, R)
    fs(cx, None, OUTLINE, lw * 1.25)

    fx = f.facing * R * 0.2
    ex_off = R * 0.26
    lx, ly = f.look
    ey = y - R * 0.08 + ly * R
    exs = [x + fx - ex_off * (1 - 0.15 * max(0, f.facing)) + lx * R,
           x + fx + ex_off * (1 - 0.15 * max(0, -f.facing)) + lx * R]
    # brows
    _brow(cx, exs[0] - R * 0.03, ey - R * 0.33, R, -1, f.brow_l[0], f.brow_l[1], lw * 0.95)
    _brow(cx, exs[1] + R * 0.03, ey - R * 0.33, R, 1, f.brow_r[0], f.brow_r[1], lw * 0.95)
    # eyes
    for i, ex in enumerate(exs):
        if f.eyes == "happy":
            cx.move_to(ex - R * 0.1, ey + R * 0.05)
            cx.curve_to(ex - R * 0.06, ey - R * 0.08, ex + R * 0.06, ey - R * 0.08, ex + R * 0.1, ey + R * 0.05)
            src(cx, OUTLINE)
            cx.set_line_width(lw)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.stroke()
            continue
        ry = R * 0.155 * (1 - f.blink)
        if ry < R * 0.02:
            line(cx, [(ex - R * 0.08, ey), (ex + R * 0.08, ey)], OUTLINE, lw * 0.9)
        else:
            ellipse(cx, ex, ey, R * 0.078, ry)
            fs(cx, OUTLINE, None, 0)
    # mouth
    _mouth(cx, x + fx * 1.15 + lx * R * 0.5, y + R * 0.38, R, f, lw, t)
    cx.restore()


def draw_person(cx, x, y, R, color, f, t=0.0, breathe=0.0):
    draw_body(cx, x, y, R, color, breathe)
    draw_head(cx, x, y, R, f, t)


# ---------------------------------------------------------------- props
TEA = hexc("#A8321E")


def tea_glass(cx, x, y, s=1.0):
    """Tulip tea glass on a saucer; (x, y) = saucer centre."""
    lw = 3.2 * s
    ellipse(cx, x, y, 34 * s, 9 * s)
    fs(cx, hexc("#F5F1EA"), OUTLINE, lw)
    # glass body: narrow waist tulip
    pts = [(x - 17 * s, y - 2 * s), (x - 20 * s, y - 22 * s), (x - 13 * s, y - 40 * s),
           (x - 19 * s, y - 66 * s), (x + 19 * s, y - 66 * s), (x + 13 * s, y - 40 * s),
           (x + 20 * s, y - 22 * s), (x + 17 * s, y - 2 * s)]
    cx.save()
    smooth_poly(cx, pts, close=True, k=0.6)
    cx.clip()
    cx.rectangle(x - 30 * s, y - 56 * s, 60 * s, 60 * s)
    cx.set_source(_vg(x - 20 * s, x + 20 * s, TEA))
    cx.fill()
    cx.rectangle(x - 30 * s, y - 70 * s, 60 * s, 14 * s)
    src(cx, hexc("#FFFFFF", 0.55))
    cx.fill()
    # glint
    cx.move_to(x - 9 * s, y - 50 * s)
    cx.line_to(x - 12 * s, y - 28 * s)
    src(cx, hexc("#FFFFFF", 0.6))
    cx.set_line_width(4 * s)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.restore()
    smooth_poly(cx, pts, close=True, k=0.6)
    fs(cx, None, OUTLINE, lw)


def _vg(x0, x1, c):
    g = cairo.LinearGradient(x0, 0, x1, 0)
    g.add_color_stop_rgba(0, *shade(c, 0.15))
    g.add_color_stop_rgba(0.5, *c)
    g.add_color_stop_rgba(1, *shade(c, -0.3))
    return g


def ring_bread_plate(cx, x, y, s=1.0):
    lw = 3.2 * s
    ellipse(cx, x, y, 78 * s, 22 * s)
    fs(cx, hexc("#FBF8F2"), OUTLINE, lw)
    ellipse(cx, x, y, 60 * s, 15 * s)
    fs(cx, None, hexc("#D8D0C4"), 2 * s)
    # ring bread (sesame ring)
    ellipse(cx, x, y - 5 * s, 52 * s, 15 * s)
    fs(cx, hexc("#C8813C"), OUTLINE, lw)
    ellipse(cx, x, y - 6 * s, 30 * s, 7 * s)
    fs(cx, hexc("#FBF8F2"), OUTLINE, lw * 0.8)
    for i in range(18):
        a = i / 18 * 2 * math.pi
        r = 41 + (i % 3) * 3
        px, py = x + math.cos(a) * r * s, y - 6 * s + math.sin(a) * r * 0.3 * s
        ellipse(cx, px, py, 2.2 * s, 1.3 * s, a)
        src(cx, hexc("#F7E3B5"))
        cx.fill()


def card_box(cx, x, y, s=1.0, flaps=1.0):
    """Cardboard archive box sitting on the table, (x, y) = bottom centre."""
    lw = 4 * s
    body = hexc("#C9935C")
    w, h = 190 * s, 120 * s
    # back flap
    if flaps > 0.01:
        cx.move_to(x - w * 0.42, y - h)
        cx.line_to(x - w * 0.36, y - h - 40 * s * flaps)
        cx.line_to(x + w * 0.36, y - h - 40 * s * flaps)
        cx.line_to(x + w * 0.42, y - h)
        cx.close_path()
        fs(cx, shade(body, -0.18), OUTLINE, lw)
    rrect(cx, x - w / 2, y - h, w, h, 6 * s)
    fs(cx, body, OUTLINE, lw)
    # front flaps folded out
    for sd in (-1, 1):
        a = flaps
        cx.move_to(x + sd * w / 2, y - h)
        cx.line_to(x + sd * (w / 2 + 34 * s * a), y - h - 30 * s * a)
        cx.line_to(x + sd * (6 * s), y - h - 30 * s * a)
        cx.line_to(x, y - h)
        cx.close_path()
        fs(cx, shade(body, 0.12), OUTLINE, lw)
    # tape + label
    rrect(cx, x - 45 * s, y - h * 0.62, 90 * s, 40 * s, 5 * s)
    fs(cx, hexc("#F6EBD7"), OUTLINE, lw * 0.6)
    for k in range(2):
        line(cx, [(x - 32 * s, y - h * 0.62 + (13 + 13 * k) * s), (x + (20 - 18 * k) * s, y - h * 0.62 + (13 + 13 * k) * s)],
             hexc("#B9A48A"), 3.5 * s)


def polaroid(cx, x, y, s, rot, photo, faces, alpha=1.0):
    """Instant photo. faces: 'laugh' or 'angry' (two tiny friends)."""
    if alpha <= 0.01 or s <= 0.01:
        return
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    cx.push_group()
    # drop shadow
    rrect(cx, -62 + 6, -72 + 8, 124, 144, 8)
    src(cx, (0, 0, 0, 0.18))
    cx.fill()
    rrect(cx, -62, -72, 124, 144, 8)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 4.5)
    rrect(cx, -50, -60, 100, 96, 4)
    fs(cx, photo, OUTLINE, 3)
    for i, (hx, col) in enumerate(((-22, "blue"), (22, "burgundy"))):
        # tiny busts
        circle(cx, hx, 8, 20)
        cx.rectangle(hx - 22, 18, 44, 30)
        cx.new_path()
        cx.move_to(hx - 24, 36)
        cx.curve_to(hx - 22, 20, hx + 22, 20, hx + 24, 36)
        cx.close_path()
        fs(cx, HOODIES[col], OUTLINE, 2.5)
        circle(cx, hx, 0, 18)
        fs(cx, HEAD_FILL, OUTLINE, 3)
        if faces == "laugh":
            for ex in (-6, 6):
                cx.move_to(hx + ex - 4, -2)
                cx.curve_to(hx + ex - 2, -7, hx + ex + 2, -7, hx + ex + 4, -2)
                src(cx, OUTLINE)
                cx.set_line_width(2.4)
                cx.stroke()
            cx.move_to(hx - 7, 5)
            cx.curve_to(hx - 5, 14, hx + 5, 14, hx + 7, 5)
            cx.close_path()
            fs(cx, MOUTH_DARK, OUTLINE, 1.6)
        else:
            for sd, ex in ((-1, -6), (1, 6)):
                ellipse(cx, hx + ex, -1, 2.2, 3.4)
                fs(cx, OUTLINE, None, 0)
                line(cx, [(hx + ex - 5 * sd, -11), (hx + ex + 4 * sd, -7)], OUTLINE, 2.4)
            cx.move_to(hx - 6, 9)
            cx.curve_to(hx - 3, 5, hx + 3, 5, hx + 6, 9)
            src(cx, OUTLINE)
            cx.set_line_width(2.4)
            cx.stroke()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def zip_file(cx, x, y, s, open_amt=0.0, zip_amt=0.0, alpha=1.0):
    """Archive file with a zipper down the middle. zip_amt 0..1 = slider pulled down,
    open_amt 0..1 = the two halves spread apart."""
    if alpha <= 0.01 or s <= 0.01:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.push_group()
    body = hexc("#E9A23B")
    w, h = 170, 130
    rrect(cx, -w / 2 + 6, -h / 2 + 9, w, h, 14)
    src(cx, (0, 0, 0, 0.18))
    cx.fill()
    # folder tab
    rrect(cx, -w / 2, -h / 2 - 18, 70, 36, 9)
    fs(cx, shade(body, -0.1), OUTLINE, 5)
    spread = open_amt * 26
    zl = -h / 2 + zip_amt * h
    if open_amt > 0:
        g = cairo.RadialGradient(0, 0, 4, 0, 0, 90)
        g.add_color_stop_rgba(0, *hexc("#FFF4C8", open_amt))
        g.add_color_stop_rgba(1, *hexc("#FFD36B", 0.0))
        rrect(cx, -spread - 14, -h / 2, 2 * spread + 28, h, 6)
        cx.set_source(g)
        cx.fill()
    for sd in (-1, 1):
        cx.save()
        cx.translate(sd * spread, 0)
        cx.rotate(sd * open_amt * 0.12)
        cx.move_to(0, -h / 2)
        cx.line_to(sd * (w / 2 - 14), -h / 2)
        cx.curve_to(sd * w / 2, -h / 2, sd * w / 2, -h / 2, sd * w / 2, -h / 2 + 14)
        cx.line_to(sd * w / 2, h / 2 - 14)
        cx.curve_to(sd * w / 2, h / 2, sd * w / 2, h / 2, sd * (w / 2 - 14), h / 2)
        cx.line_to(0, h / 2)
        cx.close_path()
        fs(cx, body, OUTLINE, 5)
        # zipper teeth on this half
        for k in range(9):
            ty = -h / 2 + 9 + k * 14
            if ty < zl or open_amt < 0.01:
                cx.rectangle(sd * 2 if sd > 0 else -14, ty, 12, 7)
                fs(cx, hexc("#6B4A1E"), None, 0)
        cx.restore()
    # zipped teeth below the slider
    if open_amt < 0.99:
        for k in range(9):
            ty = -h / 2 + 9 + k * 14
            if ty >= zl:
                cx.rectangle(-8 + (k % 2) * 4, ty, 12, 7)
                fs(cx, hexc("#6B4A1E"), None, 0)
        # slider + pull
        rrect(cx, -11, zl - 8, 22, 22, 5)
        fs(cx, hexc("#C9CED8"), OUTLINE, 3.5)
        rrect(cx, -6, zl + 10, 12, 30, 6)
        fs(cx, hexc("#C9CED8"), OUTLINE, 3.5)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()

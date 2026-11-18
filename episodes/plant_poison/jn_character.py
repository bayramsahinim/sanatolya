"""Vector drawing of the official Just Needy character (3/4 view from the turnaround sheet,
facing right), plus the farm shot's watering can and its water. Drawn with cairo, natively at
output resolution.

Proportions are taken from the sheet, in units of the head diameter D, origin at the head
centre, y down: head 1 D; hoodie from 0.45 D to the hem at 1.41 D (as wide as the head);
black legs to 2.33 D; feet to 2.40 D. 3/4 face: eyes at x = +0.05 / +0.29 D.
The near (right) arm reaches out to hold the can by its top handle (two-bone IK, elbow down);
the far hand stays in the hoodie pocket, as on the sheet.
"""
import math

import cairo
import numpy as np

BLUE = (40 / 255, 90 / 255, 215 / 255)
BLUE_DARK = (30 / 255, 68 / 255, 170 / 255)
WHITE = (245 / 255, 245 / 255, 246 / 255)
INK = (0.04, 0.04, 0.05)
SHEET_D = 295.0


def _rr(cx, x, y, w, h, r):
    cx.new_sub_path()
    cx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cx.close_path()


def _fill_stroke(cx, fill, lw):
    cx.set_source_rgb(*fill)
    cx.fill_preserve()
    cx.set_source_rgb(*INK)
    cx.set_line_width(lw)
    cx.stroke()


def ik(s, w, l1, l2):
    """Elbow for shoulder s -> wrist w (elbow bends downward/back)."""
    s, w = np.asarray(s, float), np.asarray(w, float)
    d = w - s
    dist = min(np.linalg.norm(d), l1 + l2 - 1e-3)
    a = math.atan2(d[1], d[0])
    cosb = (l1 ** 2 + dist ** 2 - l2 ** 2) / (2 * l1 * dist)
    b = math.acos(max(-1, min(1, cosb)))
    ang = a + b  # +b puts the elbow below the shoulder->wrist line (screen y down)
    return s + l1 * np.array([math.cos(ang), math.sin(ang)])


# ---------------------------------------------------------------- watering can
# The farm shot's can, redrawn: units are px in the 720-wide source, origin = handle grip
CAN = dict(
    body=[(-33, 16), (35, 16), (31, 90), (-28, 90)],
    handle=((-18, 16), (-8, -4), (22, -6), (32, 16)),
    spout=[(30, 62), (108, 28), (113, 37), (34, 74)],
    rose=((111, 31), 8.5, 12.0, -24),
)
CAN_GREY = (150 / 255, 151 / 255, 150 / 255)
CAN_DARK = (118 / 255, 119 / 255, 120 / 255)


def can_rose_tip(grip, angle_deg, s):
    (rx, ry), _, _, _ = CAN["rose"]
    a = math.radians(angle_deg)
    x = rx * s * math.cos(a) - ry * s * math.sin(a)
    y = rx * s * math.sin(a) + ry * s * math.cos(a)
    return grip[0] + x, grip[1] + y, a + math.radians(-24)


def draw_can(cx, grip, angle_deg, s, lw):
    cx.save()
    cx.translate(*grip)
    cx.rotate(math.radians(angle_deg))
    cx.scale(s, s)
    lw = lw / s
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    # spout (behind body)
    cx.move_to(*CAN["spout"][0])
    for p in CAN["spout"][1:]:
        cx.line_to(*p)
    cx.close_path()
    _fill_stroke(cx, CAN_GREY, lw)
    (rx, ry), a, b, rot = CAN["rose"]
    cx.save()
    cx.translate(rx, ry)
    cx.rotate(math.radians(rot))
    cx.scale(a, b)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()
    _fill_stroke(cx, CAN_DARK, lw)
    # handle
    (x0, y0), c1, c2, (x1, y1) = CAN["handle"]
    cx.move_to(x0, y0)
    cx.curve_to(*c1, *c2, x1, y1)
    cx.set_source_rgb(*INK)
    cx.set_line_width(lw * 2.0)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    # body
    cx.move_to(*CAN["body"][0])
    for p in CAN["body"][1:]:
        cx.line_to(*p)
    cx.close_path()
    _fill_stroke(cx, CAN_GREY, lw)
    cx.restore()


# ---------------------------------------------------------------- water
WATER = (122 / 255, 92 / 255, 52 / 255)   # tobacco-soaked water, as in the original shot


def draw_water(cx, tip, t, flow, ground_y, s, seed=3):
    """Shower from the can's rose: a fan of thin streams + falling drops + small splashes.
    tip = (x, y, direction_rad); t = seconds (drives the animation); flow 0..1."""
    if flow <= 0.01:
        return
    x0, y0, a0 = tip
    rng = np.random.default_rng(seed)
    g = 900.0 * s                     # px/s^2
    v = 95.0 * s
    streams = 7
    for i in range(streams):
        da = (i - (streams - 1) / 2) * math.radians(7)
        a = a0 + da
        vx, vy = v * math.cos(a), v * math.sin(a)
        # time to reach the ground
        disc = vy * vy + 2 * g * (ground_y - y0)
        tg = (-vy + math.sqrt(max(disc, 0))) / g
        # continuous thin stream for the first part of the path
        steps = 16
        tl = tg * 0.55 * flow
        cx.move_to(x0, y0)
        for j in range(1, steps + 1):
            tt = tl * j / steps
            cx.line_to(x0 + vx * tt, y0 + vy * tt + 0.5 * g * tt * tt)
        cx.set_source_rgba(*WATER, 0.75 * flow)
        cx.set_line_width(2.1 * s)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
        # drops: fixed phase per drop, moving along the path
        for k in range(5):
            ph = (t * 1.6 + (k / 5) + rng.random() * 0.2) % 1.0
            tt = tg * (0.45 + 0.55 * ph)
            px, py = x0 + vx * tt, y0 + vy * tt + 0.5 * g * tt * tt
            vyy = vy + g * tt
            ang = math.atan2(vyy, vx)
            cx.save()
            cx.translate(px, py)
            cx.rotate(ang)
            cx.scale(3.0 * s, 1.7 * s)
            cx.arc(0, 0, 1, 0, 2 * math.pi)
            cx.restore()
            cx.set_source_rgba(*WATER, 0.85 * flow)
            cx.fill()
        # splash dots where the stream lands
        lx = x0 + vx * tg
        for k in range(2):
            ph = (t * 3.1 + k * 0.5 + i * 0.37) % 1.0
            sx = lx + (k * 2 - 1) * 4 * s * ph
            sy = ground_y - 6 * s * math.sin(math.pi * ph)
            cx.arc(sx, sy, 1.3 * s, 0, 2 * math.pi)
            cx.set_source_rgba(*WATER, 0.7 * flow * (1 - ph))
            cx.fill()


# ---------------------------------------------------------------- character
def draw_character(cx, head_c, D, grip, can_angle, lean=0.0, breath=0.0,
                   face=(0.0, 0.0), blink=0.0, can_scale=1.0, flow=0.0, t=0.0, ground_y=None, lw_can=3.0):
    """head_c = head centre (px), D = head diameter (px). grip = hand position (px).
    lean = degrees (upper body rotates about the hips), breath -1..1, face = (dx, dy) in D,
    blink 0..1. Draws legs, body, head, can, water and the near arm, in that order."""
    hx, hy = head_c
    lw = 0.045 * D
    U = lambda x, y: (hx + x * D, hy + y * D)
    hip = U(0.0, 1.40)

    # shadow on the ground
    fy = hy + 2.40 * D
    cx.save()
    cx.translate(hx + 0.05 * D, fy - 0.01 * D)
    cx.scale(0.55 * D, 0.07 * D)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()
    cx.set_source_rgba(0.12, 0.09, 0.06, 0.22)
    cx.fill()

    # legs + feet (black pants, black shoes)
    cx.set_source_rgb(*INK)
    for lx0, lx1, foot in [(-0.22, -0.10, (-0.30, 0.04)), (0.15, 0.27, (0.11, 0.42))]:
        _rr(cx, hx + lx0 * D, hy + 1.36 * D, (lx1 - lx0) * D, 1.00 * D, 0.05 * D)
        cx.fill()
        fx0, fx1 = foot
        # rounded shoe, toe toward the facing direction (right)
        cx.save()
        cx.translate(hx + (fx0 + fx1) / 2 * D, fy - 0.06 * D)
        cx.scale((fx1 - fx0) / 2 * D, 0.065 * D)
        cx.arc(0, 0, 1, 0, 2 * math.pi)
        cx.restore()
        cx.fill()

    # upper body: rotate about the hips for lean, scale for breathing
    cx.save()
    cx.translate(*hip)
    cx.rotate(math.radians(lean))
    cx.scale(1.0, 1.0 + 0.008 * breath)
    cx.translate(-hip[0], -hip[1])
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)

    # hood behind the head
    cx.save()
    cx.translate(*U(-0.02, 0.50))
    cx.scale(0.37 * D, 0.13 * D)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.restore()
    _fill_stroke(cx, BLUE, lw)

    # hoodie body (with the far arm, hand in the pocket)
    cx.move_to(*U(-0.30, 0.56))
    cx.curve_to(*U(-0.44, 0.60), *U(-0.47, 0.72), *U(-0.48, 0.88))
    cx.curve_to(*U(-0.50, 1.05), *U(-0.48, 1.18), *U(-0.40, 1.26))
    cx.line_to(*U(-0.34, 1.30))
    cx.line_to(*U(-0.33, 1.41))
    cx.curve_to(*U(-0.10, 1.43), *U(0.15, 1.43), *U(0.34, 1.41))
    cx.line_to(*U(0.35, 1.28))
    cx.curve_to(*U(0.42, 1.15), *U(0.43, 0.90), *U(0.40, 0.72))
    cx.curve_to(*U(0.38, 0.62), *U(0.30, 0.57), *U(0.22, 0.55))
    cx.close_path()
    _fill_stroke(cx, BLUE, lw)
    # hem band and pocket
    cx.set_source_rgb(*INK)
    cx.set_line_width(lw * 0.7)
    cx.move_to(*U(-0.32, 1.33))
    cx.curve_to(*U(-0.1, 1.35), *U(0.15, 1.35), *U(0.34, 1.33))
    cx.stroke()
    cx.move_to(*U(-0.20, 1.31))
    cx.line_to(*U(-0.18, 1.06))
    cx.curve_to(*U(-0.05, 1.03), *U(0.12, 1.03), *U(0.24, 1.06))
    cx.line_to(*U(0.27, 1.31))
    cx.stroke()
    # far sleeve crease going into the pocket
    cx.move_to(*U(-0.31, 0.74))
    cx.curve_to(*U(-0.36, 0.95), *U(-0.30, 1.10), *U(-0.19, 1.16))
    cx.stroke()
    # neck V + drawstrings
    cx.move_to(*U(-0.04, 0.47))
    cx.line_to(*U(0.13, 0.47))
    cx.line_to(*U(0.05, 0.60))
    cx.close_path()
    _fill_stroke(cx, (0.86, 0.86, 0.88), lw * 0.7)
    for sx in (0.03, 0.14):
        cx.move_to(*U(sx, 0.60))
        cx.line_to(*U(sx + 0.005, 0.84))
        cx.set_source_rgb(*INK)
        cx.set_line_width(0.035 * D)
        cx.stroke()
        cx.move_to(*U(sx, 0.60))
        cx.line_to(*U(sx + 0.005, 0.84))
        cx.set_source_rgb(*BLUE)
        cx.set_line_width(0.015 * D)
        cx.stroke()

    # head
    cx.arc(hx, hy, 0.5 * D, 0, 2 * math.pi)
    _fill_stroke(cx, WHITE, lw)
    fdx, fdy = face
    F = lambda x, y: U(x + fdx, y + fdy)
    for ex in (0.05, 0.29):
        cx.save()
        cx.translate(*F(ex, -0.03))
        cx.scale(0.036 * D, 0.085 * D * max(0.12, 1 - blink))
        cx.arc(0, 0, 1, 0, 2 * math.pi)
        cx.restore()
        cx.set_source_rgb(*INK)
        cx.fill()
    cx.set_line_width(0.028 * D)
    cx.move_to(*F(-0.02, -0.17))
    cx.curve_to(*F(0.02, -0.21), *F(0.08, -0.21), *F(0.11, -0.19))
    cx.stroke()
    cx.move_to(*F(0.23, -0.19))
    cx.curve_to(*F(0.27, -0.215), *F(0.32, -0.21), *F(0.35, -0.17))
    cx.stroke()
    cx.move_to(*F(-0.06, 0.17))
    cx.curve_to(*F(0.0, 0.23), *F(0.12, 0.25), *F(0.21, 0.19))
    cx.stroke()

    # shoulder of the near arm (in the leaned frame) -> world coords
    sdev = cx.user_to_device(*U(0.30, 0.68))
    cx.restore()
    shoulder = cx.device_to_user(*sdev)

    # can (held by its handle at the grip) + water
    draw_can(cx, grip, can_angle, can_scale, lw_can)
    if ground_y is not None:
        draw_water(cx, can_rose_tip(grip, can_angle, can_scale), t, flow, ground_y, can_scale)

    # near arm: shoulder -> elbow -> wrist, sleeve with outline, white mitten hand
    sw = 0.17 * D
    l1, l2 = 0.40 * D, 0.38 * D
    wrist = np.array(grip) + np.array([-0.06 * D, 0.03 * D])
    elbow = ik(shoulder, wrist, l1, l2)
    for width, col in ((sw + 2 * lw, INK), (sw, BLUE)):
        cx.move_to(*shoulder)
        cx.line_to(*elbow)
        cx.line_to(*wrist)
        cx.set_source_rgb(*col)
        cx.set_line_width(width)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    # merge the sleeve into the body (hide the outline cap inside the shoulder)
    cx.arc(*shoulder, sw * 0.5, 0, 2 * math.pi)
    cx.set_source_rgb(*BLUE)
    cx.fill()
    # cuff line
    d = (wrist - elbow) / (np.linalg.norm(wrist - elbow) + 1e-6)
    n = np.array([-d[1], d[0]])
    c0 = wrist - d * 0.05 * D
    cx.move_to(*(c0 + n * sw * 0.5))
    cx.line_to(*(c0 - n * sw * 0.5))
    cx.set_source_rgb(*INK)
    cx.set_line_width(lw * 0.6)
    cx.stroke()
    # hand (white mitten) over the handle
    cx.arc(grip[0] - 0.01 * D, grip[1], 0.085 * D, 0, 2 * math.pi)
    _fill_stroke(cx, WHITE, lw * 0.85)
    return dict(shoulder=shoulder, elbow=elbow, wrist=wrist)

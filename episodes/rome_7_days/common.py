"""Shared helpers for the Rome episode shots."""
import math

import cairo

from cinecode import props as P
from cinecode import sets as S
from cinecode.characters import (BOY, HERO, LUCIA, MAXIMUS, Figure, Pose, RomanSoldierStyle, boy_pose,
                                 breathe, hero_pose, lucia_pose, max_pose, roman, run, soldier, talk,
                                 walk)
from cinecode.core import (FPS, H, OUTLINE, W, Cam, cam_kf, circle, clamp, ease_in, ease_io, ease_out,
                           ellipse, fs, hexc, kf, lerp, line, mix, prog, pulse, rrect, shake, smooth, src,
                           text, win)
from cinecode.timeline import Shot

GROUND = S.GROUND
GY = GROUND + 40          # where characters stand in front of stalls

WET_MAX_STYLE = RomanSoldierStyle(crest=True, cape=True, wet=1.0)
WET_MAX = Figure(WET_MAX_STYLE, seed=2)


def fig(cx, sh, cam, f, pose, who=None):
    J = f.draw(cx, pose)
    if who and cam is not None:
        sh.track(who, J, cam)
    return J


def pick(t, keys):
    """keys = [(t0, value), ...] -> value of latest key with t0 <= t."""
    v = keys[0][1]
    for k, val in keys:
        if t >= k:
            v = val
    return v


def world(cx, cam):
    cx.save()
    cam.apply(cx)


def end(cx):
    cx.restore()


def vignette(cx, a=0.35):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    cx.set_source(g)
    cx.paint()


def tint(cx, c, a):
    if a <= 0:
        return
    cx.rectangle(0, 0, W, H)
    src(cx, (c[0], c[1], c[2], a))
    cx.fill()


def sepia(cx, a=0.6):
    cx.save()
    cx.set_operator(cairo.OPERATOR_HSL_SATURATION)
    cx.rectangle(0, 0, W, H)
    cx.set_source_rgba(0.5, 0.5, 0.5, a)
    cx.fill()
    cx.restore()
    tint(cx, (0.55, 0.38, 0.18), 0.22 * a)


def desaturate(cx, a=1.0):
    cx.save()
    cx.set_operator(cairo.OPERATOR_HSL_SATURATION)
    cx.rectangle(0, 0, W, H)
    cx.set_source_rgba(0.5, 0.5, 0.5, a)
    cx.fill()
    cx.restore()


def flash(cx, a):
    tint(cx, (1, 1, 1), a)


def black(cx):
    cx.set_source_rgb(0, 0, 0)
    cx.paint()


def insert_bg(cx, c1="#2B3A55", c2="#1B2338"):
    g = cairo.RadialGradient(W / 2, H / 2, 100, W / 2, H / 2, W * 0.7)
    g.add_color_stop_rgba(0, *hexc(c1))
    g.add_color_stop_rgba(1, *hexc(c2))
    cx.set_source(g)
    cx.paint()


def big_arm(cx, x0, y0, x1, y1, w=34, sleeve="#2F6FDB"):
    """A big close-up stick arm with hoodie sleeve, from off-screen (x0,y0) to the hand (x1,y1)."""
    line(cx, [(x0, y0), (x1, y1)], OUTLINE, w)
    mx, my = x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45
    line(cx, [(x0, y0), (mx, my)], OUTLINE, w * 3.2)
    line(cx, [(x0, y0), (mx, my)], hexc(sleeve), w * 2.6)
    circle(cx, x1, y1, w * 0.95)
    fs(cx, OUTLINE, None, 0)


def big_phone(cx, x, y, s, screen_fn=None, t=0.0, rot=0.0):
    """Phone close-up. screen_fn(cx, w, h) draws the screen contents in local coords."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    rrect(cx, -170, -320, 340, 640, 48)
    fs(cx, hexc("#1E1F26"), OUTLINE, 8)
    rrect(cx, -150, -295, 300, 590, 30)
    fs(cx, hexc("#F7F8FB"), None, 0)
    if screen_fn:
        cx.save()
        rrect(cx, -150, -295, 300, 590, 30)
        cx.clip()
        cx.translate(-150, -295)
        screen_fn(cx, 300, 590)
        cx.restore()
    rrect(cx, -40, -308, 80, 10, 5)
    fs(cx, hexc("#0E0E12"), None, 0)
    cx.restore()


def wifi_icon(cx, x, y, s=1.0, crossed=True, c=OUTLINE):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    for r in (16, 32, 48):
        cx.new_path()
        cx.arc(0, 0, r, -math.pi * 0.75, -math.pi * 0.25)
        src(cx, c)
        cx.set_line_width(8)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    circle(cx, 0, 0, 6)
    fs(cx, c, None, 0)
    if crossed:
        line(cx, [(-44, -60), (44, 8)], hexc("#E04848"), 9)
    cx.restore()


def battery_icon(cx, x, y, s, pct, blink=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, -60, -28, 110, 56, 10)
    fs(cx, None, OUTLINE, 7)
    rrect(cx, 52, -12, 12, 24, 4)
    fs(cx, OUTLINE, None, 0)
    w = max(4, 98 * pct / 100)
    rrect(cx, -54, -22, w, 44, 6)
    fs(cx, hexc("#E04848", blink) if pct < 15 else hexc("#3CB371"), None, 0)
    cx.restore()


def lamp_idea(cx, x, y, s, a):
    """Roman oil lamp lighting up above a head (our 'lightbulb moment')."""
    if a <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s * (0.8 + 0.2 * a), s * (0.8 + 0.2 * a))
    g = cairo.RadialGradient(30, -30, 4, 30, -30, 120)
    g.add_color_stop_rgba(0, 1, 0.9, 0.5, 0.8 * a)
    g.add_color_stop_rgba(1, 1, 0.9, 0.5, 0)
    cx.set_source(g)
    circle(cx, 30, -30, 120)
    cx.fill()
    cx.move_to(-50, 0)
    cx.curve_to(-50, -30, 40, -30, 50, -6)
    cx.line_to(70, -10)
    cx.line_to(56, 6)
    cx.curve_to(30, 20, -40, 20, -50, 0)
    cx.close_path()
    fs(cx, hexc("#C66B3D", a), hexc("#1C1C24", a), 5)
    circle(cx, -6, -14, 7)
    fs(cx, hexc("#3B2A20", a), None, 0)
    cx.move_to(62, -10)
    cx.curve_to(52, -40, 70, -50, 66, -70)
    cx.curve_to(84, -50, 80, -30, 62, -10)
    fs(cx, hexc("#FFB23D", a), hexc("#E06A1E", a), 3)
    cx.restore()


def thought_bubble(cx, x, y, w, h, a, tail_to=None):
    if a <= 0:
        return
    cx.save()
    cx.push_group()
    rrect(cx, x - w / 2, y - h / 2, w, h, h * 0.45)
    fs(cx, (1, 1, 1, 1), OUTLINE, 6)
    if tail_to:
        tx, ty = tail_to
        for k, r in enumerate((22, 15, 9)):
            px = x + (tx - x) * (0.55 + k * 0.17)
            py = y + h / 2 + (ty - y - h / 2) * (0.25 + k * 0.3)
            circle(cx, px, py, r)
            fs(cx, (1, 1, 1, 1), OUTLINE, 5)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def coins(cx, x, y, s=1.0):
    for k in range(9):
        row = [0, 0, 0, 0, 1, 1, 1, 2, 2][k]
        col = [0, 1, 2, 3, 0, 1, 2, 0, 1][k]
        ellipse(cx, x + (col - 1.5 + row * 0.5) * 34 * s, y - row * 18 * s, 18 * s, 8 * s)
        fs(cx, hexc("#FFC857"), OUTLINE, 3)


def rect_drawing(cx, x, y, s, a=1.0):
    """A Roman's wax-tablet drawing of the 'glowing rectangle'."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, -50, -36, 100, 72, 6)
    fs(cx, hexc("#8A5A2E", a), hexc("#1C1C24", a), 4)
    rrect(cx, -40, -27, 80, 54, 4)
    fs(cx, hexc("#E7C46A", a), None, 0)
    rrect(cx, -12, -20, 24, 40, 4)
    fs(cx, None, hexc("#5A3A26", a), 3)
    for k in range(6):
        ang = k * math.pi / 3
        line(cx, [(math.cos(ang) * 16, math.sin(ang) * 26), (math.cos(ang) * 24, math.sin(ang) * 34)],
             hexc("#5A3A26", a), 2.5)
    cx.restore()


def moth(cx, x, y, t, a=1.0):
    cx.save()
    cx.translate(x, y)
    fl = math.sin(t * 30) * 0.6
    for sx in (-1, 1):
        cx.save()
        cx.scale(sx, 1)
        cx.rotate(fl)
        ellipse(cx, 14, -6, 14, 9, -0.4)
        fs(cx, hexc("#C9BBA3", a), hexc("#1C1C24", a), 3)
        cx.restore()
    ellipse(cx, 0, 0, 5, 10)
    fs(cx, hexc("#7A6A55", a), hexc("#1C1C24", a), 2.5)
    cx.restore()


def stomach_growl_lines(cx, x, y, t, a=1.0):
    if a <= 0:
        return
    for k in range(3):
        r = 30 + k * 14 + 6 * math.sin(t * 20 + k)
        cx.new_path()
        cx.arc(x, y, r, -0.5, 0.5)
        src(cx, (0.11, 0.11, 0.14, a * (1 - k * 0.25)))
        cx.set_line_width(4)
        cx.stroke()
        cx.new_path()
        cx.arc(x, y, r, math.pi - 0.5, math.pi + 0.5)
        cx.stroke()


def zigzag_shake(t, amp):
    return math.sin(t * 60) * amp

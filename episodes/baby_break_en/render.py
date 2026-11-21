"""Shot-for-shot rebuild of the original baby-break short (native 1080x1920, 30 fps).

Everything is authored in ORIGINAL time (seconds of the Turkish source) so scene order, actions and
timing follow the source exactly. `warp()` maps each output frame (English timing) to original time,
anchored at every narration line start/end, so picture and English narration stay in sync.

The adult of the source is played by Just Needy (official sheet: round white head, black oval eyes,
no hair, blue hoodie with the hood down). The baby stays a baby and does exactly what it does in the source.

usage:
  python -m episodes.baby_break_en.render stills 0.5 8.5 ...   # original-time stills -> build/baby_break_en/stills
  python -m episodes.baby_break_en.render video                 # silent render -> build/baby_break_en/video_silent.mp4
"""
import json
import math
import os
import subprocess
import sys

import cairo
import numpy as np

from cinecode.core import (back_out, circle, clamp, ease_in, ease_io, ease_out, ellipse, hexc, lerp, mix, prog,
                           rrect, shade, smooth, src)
from episodes.ancestry_en import ui
from episodes.baby_break_en.script import CAP, LINES, ORIG_DURATION

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "baby_break_en")
W, H, FPS = 1080, 1920, 30

# ------------------------------------------------------------------ palette (sampled from the source)
INK = hexc("#2B221E")
WALL = hexc("#EEE2CF")
WALL_EDGE = hexc("#D8C8B0")
TRIM = hexc("#F5F0E9")
FLOOR_A = hexc("#EDC7AE")
FLOOR_B = hexc("#DDA38E")
SKIN = hexc("#EDB896")
SKIN_SH = hexc("#E0A584")
CHEEK = hexc("#E8837E")
HAIR = hexc("#9A6440")
ONESIE = hexc("#E8C062")
ONESIE_SH = hexc("#D7A947")
RATTLE = hexc("#E0675A")
RATTLE_IN = hexc("#F1B23B")
BLOCK = hexc("#C98943")
BALL = hexc("#7FA5C8")
WATER = hexc("#7FAEDB")
GLASS = hexc("#F7F4EF")
JN_BLUE = hexc("#2F5FE0")
JN_BLUE_DK = hexc("#1F45B5")
JN_BLUE_LT = hexc("#4C7DF0")
JN_INK = hexc("#151519")
WHITE = hexc("#FFFFFF")
RED = hexc("#D9534A")
HEART = hexc("#E0453F")
LW = 5.0


def fs(cx, fill, stroke=INK, lw=LW):
    if fill is not None:
        src(cx, fill)
        if stroke is not None:
            cx.fill_preserve()
        else:
            cx.fill()
    if stroke is not None:
        src(cx, stroke)
        cx.set_line_width(lw)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.new_path()


def stroke_line(cx, pts, c=INK, lw=LW, alpha=1.0):
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    src(cx, c, alpha)
    cx.set_line_width(lw)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()


def kf(t, keys, ease=ease_io):
    """keys: [(t, value or tuple)] -> interpolated value."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease(prog(t, t0, t1))
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]


def step(t, keys):
    v = keys[0][1]
    for t0, val in keys:
        if t >= t0:
            v = val
    return v


def win(t, a, b, fi=0.18, fo=0.18):
    return smooth(prog(t, a, a + fi)) * (1 - smooth(prog(t, b - fo, b)))


# ================================================================== props
def rattle(cx, x, y, ang, s=1.0, alpha=1.0):
    """Rattle gripped at (x, y); `ang` = direction of the stick (radians, 0 = up)."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    cx.push_group()
    rrect(cx, -9, -205, 18, 215, 8)
    fs(cx, RATTLE_IN)
    circle(cx, 0, -222, 58)
    fs(cx, RATTLE)
    circle(cx, 0, -222, 20)
    fs(cx, RATTLE_IN, INK, 4)
    ellipse(cx, -24, -244, 11, 7, -0.6)
    src(cx, WHITE, 0.55)
    cx.fill()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def rattle_head(x, y, ang, s=1.0):
    return x + math.sin(ang) * 222 * s, y - math.cos(ang) * 222 * s


def burst(cx, x, y, r0, r1, n=7, rot=0.0, alpha=1.0, lw=6.0, c=INK):
    if alpha <= 0.01:
        return
    for i in range(n):
        a = rot + i * 2 * math.pi / n
        stroke_line(cx, [(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)],
                    c, lw, alpha)


def block(cx, x, y, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.rotate(-0.12)
    # top + side faces
    cx.move_to(-48, -40)
    cx.line_to(-30, -58)
    cx.line_to(58, -52)
    cx.line_to(42, -34)
    cx.close_path()
    fs(cx, shade(BLOCK, 0.18))
    cx.move_to(42, -34)
    cx.line_to(58, -52)
    cx.line_to(56, 34)
    cx.line_to(40, 52)
    cx.close_path()
    fs(cx, shade(BLOCK, -0.18))
    rrect(cx, -48, -40, 90, 92, 4)
    fs(cx, BLOCK)
    # star
    cx.save()
    cx.translate(-3, 6)
    pts = []
    for i in range(10):
        r = 28 if i % 2 == 0 else 12
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((math.cos(a) * r, math.sin(a) * r))
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    cx.close_path()
    src(cx, hexc("#F6EBDD"))
    cx.fill()
    cx.restore()
    cx.restore()


def ball(cx, x, y, r=48):
    circle(cx, x, y, r)
    fs(cx, BALL)
    cx.save()
    circle(cx, x, y, r)
    cx.clip()
    cx.arc(x - r * 1.3, y + r * 0.2, r * 1.25, -0.7, 0.75)
    src(cx, hexc("#EAF2F9"))
    cx.set_line_width(5)
    cx.stroke()
    cx.arc(x + r * 0.2, y - r * 1.5, r * 1.35, 0.9, 2.2)
    cx.stroke()
    circle(cx, x + r * 0.35, y + r * 0.3, r * 0.9)
    src(cx, shade(BALL, -0.2), 0.25)
    cx.fill()
    cx.restore()
    circle(cx, x, y, r)
    fs(cx, None)


def heart(cx, x, y, s, alpha=1.0, c=HEART):
    if alpha <= 0.01 or s <= 0.01:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(0, 22)
    cx.curve_to(-38, -4, -30, -34, -12, -32)
    cx.curve_to(-4, -31, 0, -24, 0, -18)
    cx.curve_to(0, -24, 4, -31, 12, -32)
    cx.curve_to(30, -34, 38, -4, 0, 22)
    cx.close_path()
    src(cx, c, alpha)
    cx.fill()
    ellipse(cx, -14, -18, 7, 4.5, -0.6)
    src(cx, WHITE, 0.6 * alpha)
    cx.fill()
    cx.restore()


def pause_icon(cx, x, y, r, alpha=1.0):
    if alpha <= 0.01 or r <= 0.5:
        return
    cx.push_group()
    circle(cx, x, y + r * 0.06, r)
    src(cx, (0, 0, 0, 0.12))
    cx.fill()
    circle(cx, x, y, r)
    fs(cx, WHITE, INK, r * 0.075)
    for s in (-1, 1):
        rrect(cx, x + s * r * 0.22 - r * 0.11, y - r * 0.38, r * 0.22, r * 0.76, r * 0.05)
        src(cx, INK)
        cx.fill()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


# ================================================================== baby
class BabyPose:
    def __init__(self, yaw=0.0, look=(0.0, 0.0), eyes="open", brows="soft", mouth="flat", tilt=0.0, lid=0.0):
        self.yaw, self.look, self.eyes, self.brows, self.mouth, self.tilt, self.lid = yaw, look, eyes, brows, mouth, tilt, lid


def baby(cx, x, y, s, p, body=True, lw=LW):
    """Baby sitting; (x, y) = head centre, head radius = 88 * s. yaw < 0 turns the face to screen-left."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    lw = lw / s if s > 1.5 else lw
    if body:
        _baby_body(cx, lw)
    cx.save()
    cx.translate(0, 70)
    cx.rotate(p.tilt)
    cx.translate(0, -70)
    _baby_head(cx, p, lw)
    cx.restore()
    cx.restore()


def _baby_body(cx, lw):
    # feet
    for sx in (-1, 1):
        ellipse(cx, sx * 72, 292, 40, 26)
        fs(cx, SKIN, INK, lw)
    # onesie (pear shape)
    cx.move_to(-62, 66)
    cx.curve_to(-120, 80, -150, 150, -158, 230)
    cx.curve_to(-162, 285, -110, 300, -40, 298)
    cx.line_to(40, 298)
    cx.curve_to(110, 300, 162, 285, 158, 230)
    cx.curve_to(150, 150, 120, 80, 62, 66)
    cx.close_path()
    cx.save()
    fs_path = cx.copy_path()
    src(cx, ONESIE)
    cx.fill_preserve()
    cx.clip()
    ellipse(cx, 70, 230, 110, 120)
    src(cx, ONESIE_SH, 0.45)
    cx.fill()
    cx.restore()
    cx.append_path(fs_path)
    fs(cx, None, INK, lw)
    # collar
    cx.arc(0, 52, 52, 0.25 * math.pi, 0.75 * math.pi)
    src(cx, ONESIE_SH)
    cx.set_line_width(lw * 1.4)
    cx.stroke()
    # arms
    for sx in (-1, 1):
        cx.move_to(sx * 88, 92)
        cx.curve_to(sx * 140, 120, sx * 162, 190, sx * 150, 246)
        cx.curve_to(sx * 140, 262, sx * 118, 258, sx * 116, 240)
        cx.curve_to(sx * 122, 190, sx * 108, 150, sx * 78, 128)
        cx.close_path()
        fs(cx, ONESIE, INK, lw)
        stroke_line(cx, [(sx * 138, 160), (sx * 142, 200)], ONESIE_SH, lw * 1.3)
        circle(cx, sx * 140, 258, 22)
        fs(cx, SKIN, INK, lw)


def _baby_head(cx, p, lw):
    yaw = p.yaw
    # ears (the far ear hides as the head turns)
    for sx in (-1, 1):
        vis = 1 - clamp(-sx * yaw * 2.2)  # turning left (yaw<0) hides the right ear? no: shows right ear more
        ex = sx * (86 + 6 * sx * yaw * -1)
        if vis <= 0.05:
            continue
        ellipse(cx, ex - sx * 4 + yaw * 30, 18, 15 * vis + 2, 22)
        fs(cx, SKIN, INK, lw)
    # skull
    ellipse(cx, 0, 0, 90, 86)
    cx.save()
    src(cx, SKIN)
    cx.fill_preserve()
    cx.clip()
    ellipse(cx, 50 - yaw * 40, 10, 70, 110)
    src(cx, SKIN_SH, 0.35)
    cx.fill()
    cx.restore()
    ellipse(cx, 0, 0, 90, 86)
    fs(cx, None, INK, lw)
    # face features shift with yaw
    fx = yaw * 52
    fy = 6
    # hair curl
    cx.save()
    cx.translate(fx * 0.35, -84)
    cx.new_path()
    cx.arc(0, 0, 11, math.pi * 0.9, math.pi * 2.6)
    src(cx, HAIR)
    cx.set_line_width(lw * 1.25)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    for sx in (-1, 1):
        cx.arc(sx * 18, 6, 15, math.pi * (1.2 if sx < 0 else 1.5), math.pi * (1.5 if sx < 0 else 1.8))
        cx.stroke()
    cx.restore()
    # cheeks
    for sx in (-1, 1):
        squash = 1 - clamp(sx * yaw * 1.6) * 0.5
        ellipse(cx, fx + sx * 54 * (1 + sx * yaw * 0.3), fy + 34, 20 * squash, 12)
        src(cx, CHEEK, 0.42)
        cx.fill()
    # eyes
    lx, ly = p.look
    for sx in (-1, 1):
        ex = fx + sx * 33 * (1 + sx * yaw * 0.25)
        ey = fy - 2
        if p.eyes == "closed":
            cx.arc(ex, ey - 2, 12, 0.15 * math.pi, 0.85 * math.pi)
            src(cx, INK)
            cx.set_line_width(lw * 0.9)
            cx.stroke()
        elif p.eyes == "happy":
            cx.arc(ex, ey + 6, 11, 1.15 * math.pi, 1.85 * math.pi)
            src(cx, INK)
            cx.set_line_width(lw * 0.9)
            cx.stroke()
        else:
            ellipse(cx, ex + lx * 4, ey + ly * 3, 9.5, 12)
            src(cx, INK)
            cx.fill()
            ellipse(cx, ex + lx * 4 + 3, ey + ly * 3 - 4, 3.3, 3.3)
            src(cx, WHITE)
            cx.fill()
            if p.lid > 0.01:  # heavy upper lid (bored / annoyed)
                cx.save()
                cx.rectangle(ex - 16, ey - 20, 32, 8 + 16 * p.lid)
                cx.clip()
                ellipse(cx, ex + lx * 4, ey + ly * 3, 10.5, 13)
                src(cx, SKIN)
                cx.fill()
                cx.restore()
                stroke_line(cx, [(ex - 12, ey - 12 + 16 * p.lid), (ex + 12, ey - 12 + 16 * p.lid - sx * 1.5)], INK, lw * 0.9)
        # brows
        by = ey - 24
        if p.brows == "annoyed":
            stroke_line(cx, [(ex - 12 * sx * -1 - 1, by - 3), (ex + 12 * sx * -1, by + 3)], INK, lw * 0.8)
        elif p.brows == "up":
            cx.arc(ex, by + 8, 12, 1.2 * math.pi, 1.8 * math.pi)
            src(cx, HAIR, 0.8)
            cx.set_line_width(lw * 0.7)
            cx.stroke()
        else:
            cx.arc(ex, by + 10, 12, 1.25 * math.pi, 1.75 * math.pi)
            src(cx, HAIR, 0.6)
            cx.set_line_width(lw * 0.6)
            cx.stroke()
    # nose
    cx.arc(fx, fy + 16, 4, 0.1 * math.pi, 0.9 * math.pi)
    src(cx, INK, 0.8)
    cx.set_line_width(lw * 0.6)
    cx.stroke()
    # mouth
    mx, my = fx + lx * 2, fy + 36
    if p.mouth == "o":
        ellipse(cx, mx, my + 2, 6, 8)
        fs(cx, hexc("#7A2E2A"), INK, lw * 0.7)
    elif p.mouth == "smile":
        cx.arc(mx, my - 8, 13, 0.2 * math.pi, 0.8 * math.pi)
        src(cx, INK)
        cx.set_line_width(lw * 0.8)
        cx.stroke()
    elif p.mouth == "frown":
        cx.arc(mx, my + 12, 10, 1.25 * math.pi, 1.75 * math.pi)
        src(cx, INK)
        cx.set_line_width(lw * 0.8)
        cx.stroke()
    else:
        stroke_line(cx, [(mx - 8, my + 2), (mx + 8, my)], INK, lw * 0.8)


# ================================================================== Just Needy (sitting, cross-legged)
HIP = (790.0, 1615.0)


class JNPose:
    def __init__(self, lean=0.0, arm="shake", face="o", look=(-0.6, 0.35), brows=0.6, shake=0.0, rattle_a=None):
        self.lean, self.arm, self.face, self.look, self.brows, self.shake = lean, arm, face, look, brows, shake
        self.rattle_a = rattle_a


# arm targets in the upright body frame: (elbow, hand, rattle stick angle)
ARMS = {
    "shake": ((470.0, 1125.0), (525.0, 905.0), -0.16),
    "hold": ((585.0, 1420.0), (612.0, 1185.0), 0.1),
    "lap": ((628.0, 1478.0), (602.0, 1560.0), 0.86),
}


BODY_SC = 1.14
LEAN_ANG = -0.26
LEAN_DX = -70.0


def _body_tf(lean):
    return LEAN_ANG * lean, BODY_SC * (1.0 + 0.10 * lean), LEAN_DX * lean


def jn_sitting(cx, p, T=0.0, draw_legs=True):
    lean = p.lean
    ang, sc, dx = _body_tf(lean)
    hx, hy = HIP
    # legs (black, crossed) - stay on the floor
    if draw_legs:
        cx.save()
        cx.translate(hx + dx, hy + 30)
        cx.rotate(ang * 0.35)
        cx.translate(-hx, -hy - 30)
        for sx in (-1, 1):
            hip = (hx + sx * 80, hy - 10)
            knee = (hx + sx * 255, hy + 40)
            foot = (hx - sx * 40, hy + 88)
            stroke_line(cx, [hip, knee, foot], JN_INK, 34)
            ellipse(cx, foot[0] - sx * 28, foot[1] + 4, 32, 15, 0.0)
            src(cx, JN_INK)
            cx.fill()
        cx.restore()
    cx.save()
    cx.translate(hx + dx, hy)
    cx.rotate(ang)
    cx.scale(sc, sc)
    cx.translate(-hx, -hy)
    elbow, hand, ra = ARMS[p.arm] if isinstance(p.arm, str) else p.arm
    # arm targets are authored in world space (upright pose); convert to the scaled body frame
    elbow = (hx + (elbow[0] - hx) / BODY_SC, hy + (elbow[1] - hy) / BODY_SC)
    hand = (hx + (hand[0] - hx) / BODY_SC, hy + (hand[1] - hy) / BODY_SC)
    if p.rattle_a is not None:
        ra = p.rattle_a
    # hood behind neck
    ellipse(cx, 795, 1262, 96, 34)
    fs(cx, JN_BLUE_DK, JN_INK, 6)
    _jn_torso(cx)
    # right arm resting on the knee
    _sleeve(cx, (930, 1300), (985, 1450), (972, 1575))
    # drawstrings + neck
    for s in (-1, 1):
        stroke_line(cx, [(795 + s * 20, 1262), (795 + s * 23, 1352)], hexc("#F4F4F4"), 7)
    rrect(cx, 782, 1218, 26, 44, 8)
    fs(cx, WHITE, JN_INK, 5)
    # head
    _jn_head(cx, 795, 1112, 122, p, T)
    # the arm holding the rattle
    sh = (660.0, 1305.0)
    shake_a = math.sin(T * 2 * math.pi * 6.5) * 0.28 * p.shake
    shake_x = math.sin(T * 2 * math.pi * 6.5 + 0.6) * 10 * p.shake
    hand2 = (hand[0] + shake_x, hand[1])
    if p.arm != "lap":
        rattle(cx, hand2[0], hand2[1], ra + shake_a, s=1.0 / BODY_SC)
    _sleeve(cx, sh, elbow, hand2)
    if p.arm == "lap":
        rattle(cx, hand2[0], hand2[1], ra + shake_a, s=1.0 / BODY_SC)
        circle(cx, hand2[0], hand2[1], 27)
        fs(cx, WHITE, JN_INK, 5)
    cx.restore()
    return ang, sc, hand2, ra + shake_a


def body_to_world(pt, lean):
    """Body-frame coords -> world coords for the current lean."""
    ang, sc, ox = _body_tf(lean)
    dx, dy = pt[0] - HIP[0], pt[1] - HIP[1]
    c, s = math.cos(ang), math.sin(ang)
    return HIP[0] + ox + sc * (dx * c - dy * s), HIP[1] + sc * (dx * s + dy * c)


def _jn_torso(cx):
    cx.save()
    cx.translate(795, 0)
    cx.scale(1.1, 1)
    cx.translate(-795, 0)
    _jn_torso_inner(cx)
    cx.restore()


def _jn_torso_inner(cx):
    def path():
        cx.move_to(640, 1600)
        cx.curve_to(632, 1500, 618, 1390, 626, 1330)
        cx.curve_to(632, 1288, 670, 1262, 720, 1260)
        cx.line_to(870, 1260)
        cx.curve_to(920, 1262, 958, 1288, 964, 1330)
        cx.curve_to(972, 1390, 958, 1500, 950, 1600)
        cx.curve_to(950, 1622, 935, 1630, 915, 1630)
        cx.line_to(675, 1630)
        cx.curve_to(655, 1630, 640, 1622, 640, 1600)
        cx.close_path()
    path()
    cx.save()
    src(cx, JN_BLUE)
    cx.fill_preserve()
    cx.clip()
    cx.rectangle(600, 1585, 400, 60)
    src(cx, JN_BLUE_DK)
    cx.fill()
    cx.rectangle(860, 1260, 110, 330)
    src(cx, JN_BLUE_LT, 0.3)
    cx.fill()
    cx.restore()
    path()
    fs(cx, None, JN_INK, 6)
    stroke_line(cx, [(640, 1585), (950, 1585)], JN_INK, 4)
    # kangaroo pocket
    cx.move_to(700, 1580)
    cx.line_to(718, 1492)
    cx.line_to(872, 1492)
    cx.line_to(890, 1580)
    fs(cx, None, shade(JN_BLUE_DK, -0.25), 5)
    # bunched collar
    cx.move_to(740, 1262)
    cx.curve_to(756, 1292, 834, 1292, 850, 1262)
    fs(cx, None, JN_INK, 5)


def _sleeve(cx, sh, el, ha):
    stroke_line(cx, [sh, el, ha], JN_INK, 62)
    stroke_line(cx, [sh, el, ha], JN_BLUE, 50)
    # cuff + hand
    dx, dy = ha[0] - el[0], ha[1] - el[1]
    n = math.hypot(dx, dy) or 1
    cxp = (ha[0] - dx / n * 14, ha[1] - dy / n * 14)
    stroke_line(cx, [cxp, (cxp[0] + dx / n * 2, cxp[1] + dy / n * 2)], JN_BLUE_DK, 50)
    circle(cx, ha[0], ha[1], 27)
    fs(cx, WHITE, JN_INK, 5)


def _jn_head(cx, x, y, r, p, T):
    circle(cx, x, y, r)
    fs(cx, WHITE, JN_INK, 6.5)
    lx, ly = p.look
    ex0, ey0 = x + lx * r * 0.2, y - r * 0.1 + ly * r * 0.12
    blink = p.face not in ("laugh",) and (2.9 < (T % 3.7) < 3.02)
    for s_ in (-1, 1):
        ex = ex0 + s_ * r * 0.3 * (1 + s_ * lx * 0.12)
        if p.face == "laugh":
            cx.arc(ex, ey0 + r * 0.04, r * 0.1, 1.1 * math.pi, 1.9 * math.pi)
            src(cx, JN_INK)
            cx.set_line_width(r * 0.06)
            cx.stroke()
        elif blink:
            stroke_line(cx, [(ex - r * 0.08, ey0), (ex + r * 0.08, ey0)], JN_INK, r * 0.055)
        else:
            ellipse(cx, ex, ey0, r * 0.085, r * (0.15 + 0.02 * p.brows))
            src(cx, JN_INK)
            cx.fill()
        if p.brows > 0.05 and p.face != "laugh":
            cx.new_path()
            cx.arc(ex, ey0 - r * (0.16 + 0.08 * p.brows), r * 0.13, math.pi * 1.2, math.pi * 1.8)
            src(cx, JN_INK, min(1.0, p.brows * 1.5))
            cx.set_line_width(r * 0.05)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.stroke()
    mx, my = x + lx * r * 0.14, y + r * 0.08 + ly * r * 0.08
    cx.new_path()
    if p.face == "o":
        ellipse(cx, mx, my + r * 0.3, r * 0.085, r * 0.12)
        src(cx, JN_INK)
        cx.fill()
    elif p.face == "laugh":
        cx.arc(mx, my + r * 0.02, r * 0.34, math.pi * 0.12, math.pi * 0.88)
        cx.close_path()
        src(cx, JN_INK)
        cx.fill()
    else:
        cx.arc(mx, my, r * 0.36, math.pi * 0.25, math.pi * 0.75)
        src(cx, JN_INK)
        cx.set_line_width(r * 0.065)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()


def jn_badge(cx, x, y, r, face="smile", ring=None, alpha=1.0, look=(0.0, 0.0)):
    """Circular avatar of Just Needy's face (used for the 'your face' / 'your expressions' icons)."""
    if alpha <= 0.01 or r <= 0.5:
        return
    cx.push_group()
    circle(cx, x, y, r)
    fs(cx, hexc("#F3EDE4"), INK, r * 0.07)
    cx.save()
    circle(cx, x, y, r * 0.93)
    cx.clip()
    ellipse(cx, x, y + r * 1.08, r * 0.8, r * 0.45)
    fs(cx, JN_BLUE, JN_INK, r * 0.05)
    _jn_head(cx, x, y - r * 0.05, r * 0.6, JNPose(face=face, look=look, brows=0.8 if face == "o" else 0.0), 0.0)
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def speaker_badge(cx, x, y, r, alpha=1.0):
    if alpha <= 0.01:
        return
    cx.push_group()
    circle(cx, x, y, r)
    fs(cx, hexc("#F3EDE4"), INK, r * 0.07)
    s = r / 40
    cx.move_to(x - 18 * s, y - 8 * s)
    cx.line_to(x - 8 * s, y - 8 * s)
    cx.line_to(x + 4 * s, y - 18 * s)
    cx.line_to(x + 4 * s, y + 18 * s)
    cx.line_to(x - 8 * s, y + 8 * s)
    cx.line_to(x - 18 * s, y + 8 * s)
    cx.close_path()
    src(cx, INK)
    cx.fill()
    for k in (1, 2):
        cx.arc(x + 6 * s, y, 8 * s * k, -0.8, 0.8)
        src(cx, INK)
        cx.set_line_width(3.2 * s)
        cx.stroke()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def baby_badge(cx, x, y, r, pose, alpha=1.0, slash=0.0, bg=hexc("#F3EDE4")):
    if alpha <= 0.01 or r <= 0.5:
        return
    cx.push_group()
    circle(cx, x, y, r)
    fs(cx, bg, INK, max(2.0, r * 0.06))
    cx.save()
    circle(cx, x, y, r * 0.94)
    cx.clip()
    baby(cx, x, y + r * 0.02, r / 115.0, pose, lw=3.0)
    cx.restore()
    if slash > 0:
        a0 = (x - r * 0.72, y - r * 0.72)
        a1 = (x + r * 0.72 * (2 * slash - 1), y + r * 0.72 * (2 * slash - 1))
        stroke_line(cx, [a0, a1], RED, r * 0.11)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


# ================================================================== sets
def room(cx, baseboard=1250.0, floor_y=1535.0):
    """Wide room in world coords (world = opening frame, 1080x1920); drawn generously beyond the frame."""
    g = cairo.LinearGradient(0, -400, 0, floor_y)
    g.add_color_stop_rgba(0, *WALL[:3], 1)
    g.add_color_stop_rgba(1, *shade(WALL, -0.04)[:3], 1)
    cx.rectangle(-900, -900, 2900, floor_y + 900)
    cx.set_source(g)
    cx.fill()
    # baseboard rail
    cx.rectangle(-900, baseboard, 2900, 22)
    fs(cx, TRIM, INK, 4.5)
    # floor
    g = cairo.LinearGradient(0, floor_y, 0, 2300)
    g.add_color_stop_rgba(0, *FLOOR_A[:3], 1)
    g.add_color_stop_rgba(1, *FLOOR_B[:3], 1)
    cx.rectangle(-900, floor_y, 2900, 1400)
    cx.set_source(g)
    cx.fill()
    stroke_line(cx, [(-900, floor_y), (2000, floor_y)], INK, 4)
    # rug edge dashes
    for i in range(-20, 60):
        x = i * 46
        stroke_line(cx, [(x, floor_y + 30), (x + 22, floor_y + 30)], shade(FLOOR_B, -0.12), 4, 0.6)
    # soft dots on the rug
    rng = np.random.default_rng(3)
    for _ in range(26):
        x, y = rng.uniform(-300, 1400), rng.uniform(floor_y + 80, 2150)
        circle(cx, x, y, rng.uniform(8, 18))
        src(cx, WHITE, 0.22)
        cx.fill()


def shelf_wall(cx):
    """Close-up set: wall with a white shelf (glass sits on it) and the floor line behind the baby."""
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *WALL[:3], 1)
    g.add_color_stop_rgba(1, *shade(WALL, -0.05)[:3], 1)
    cx.rectangle(-200, -200, W + 400, H + 400)
    cx.set_source(g)
    cx.fill()
    cx.rectangle(-200, 855, W + 400, 95)
    src(cx, TRIM)
    cx.fill()
    for y in (855, 950):
        stroke_line(cx, [(-200, y), (W + 200, y)], INK, 9)
    stroke_line(cx, [(-200, 1772), (W + 200, 1772)], INK, 7)
    cx.rectangle(-200, 1775, W + 400, 300)
    src(cx, FLOOR_A)
    cx.fill()


def glass(cx, x, y_bot, level, alpha=1.0, wobble=0.0, overflow=0.0, T=0.0):
    """Water glass standing on the shelf. level 0..1 (>1 = brimming)."""
    top, bot, h = 100.0, 84.0, 240.0
    yt = y_bot - h

    def path():
        cx.move_to(x - top, yt)
        cx.line_to(x - bot, y_bot - 12)
        cx.curve_to(x - bot + 1, y_bot, x - bot + 8, y_bot, x - bot + 14, y_bot)
        cx.line_to(x + bot - 14, y_bot)
        cx.curve_to(x + bot - 8, y_bot, x + bot - 1, y_bot, x + bot, y_bot - 12)
        cx.line_to(x + top, yt)
        cx.close_path()
    path()
    src(cx, GLASS, 0.92 * alpha)
    cx.fill()
    if level > 0.001:
        lv = min(level, 1.0)
        wy = y_bot - 6 - (h - 8) * lv
        cx.save()
        path()
        cx.clip()
        cx.move_to(x - 140, wy)
        for i in range(29):
            xx = x - 140 + i * 10
            cx.line_to(xx, wy + math.sin(xx * 0.05 + T * 7) * 3.5 * wobble)
        cx.line_to(x + 140, y_bot + 10)
        cx.line_to(x - 140, y_bot + 10)
        cx.close_path()
        src(cx, WATER, alpha)
        cx.fill()
        stroke_line(cx, [(x - 140, wy), (x + 140, wy)], WHITE, 3, 0.55 * alpha)
        cx.restore()
    # highlight
    stroke_line(cx, [(x - top + 26, yt + 24), (x - bot + 24, y_bot - 40)], WHITE, 7, 0.75 * alpha)
    path()
    src(cx, INK, alpha)
    cx.set_line_width(7)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()
    # brimming: meniscus over the rim + drips down the sides
    if overflow > 0.01:
        ellipse(cx, x, yt + 2, top - 2, 7 * overflow)
        src(cx, WATER, alpha)
        cx.fill()
        for k, (sx, ph) in enumerate(((-1, 0.0), (1, 0.45), (-1, 0.7), (1, 0.2))):
            u = ((T * 0.55 + ph) % 1.0)
            dy = 20 + u * 190
            px = x + sx * (top - (top - bot) * dy / h) + sx * 6
            circle(cx, px, yt + dy, 9 * overflow * (1 - 0.3 * u))
            fs(cx, WATER, INK, 2.5)


# ================================================================== the original timeline (original seconds)
# baby in the wide shot
def baby_wide_pose(T):
    if T < 5.4:
        return BabyPose(yaw=-0.30, look=(-0.8, 0.5), mouth="flat", brows="soft", tilt=-0.04)
    if T < 12.8:
        k = smooth(prog(T, 5.4, 6.6))
        return BabyPose(yaw=lerp(-0.30, -0.42, k), look=(-1.0, 0.6), mouth="frown", brows="annoyed", lid=0.55 * k,
                        tilt=-0.06)
    if T < 14.5:
        return BabyPose(yaw=lerp(-0.42, -0.12, smooth(prog(T, 12.8, 13.4))), look=(0.2, 0.2), mouth="flat")
    if T < 35.9:  # shot 3: calm, still looking away a little
        return BabyPose(yaw=-0.18, look=(-0.7, 0.6), mouth="flat", brows="soft", tilt=-0.03)
    if T < 39.0:  # turns back toward Just Needy on their own, smiles
        k = smooth(prog(T, 36.4, 37.4))
        return BabyPose(yaw=lerp(-0.18, 0.26, k), look=(lerp(-0.7, 0.9, k), lerp(0.6, 0.0, k)),
                        mouth="smile" if T > 37.2 else "flat", eyes="happy" if 38.0 < T < 38.7 else "open")
    # shot 4: smiling, a slow content blink, then (loop) looks away again as the rattle comes back
    if T < 43.3:
        eyes = "happy" if 41.0 < T < 41.7 else "open"
        return BabyPose(yaw=0.12, look=(0.6, 0.0), mouth="smile", eyes=eyes)
    k = smooth(prog(T, 43.3, 44.3))
    return BabyPose(yaw=lerp(0.12, -0.30, k), look=(lerp(0.6, -0.8, k), lerp(0.0, 0.5, k)),
                    mouth="smile" if k < 0.5 else "flat", tilt=-0.04 * k)


def jn_pose(T):
    if T < 6.0:
        return JNPose(lean=0.0, arm="shake", face="o", look=(-0.65, 0.35), brows=0.7,
                      shake=win(T, -1, 1.6, 0.01, 0.35) + 0.15)
    if T < 12.5:
        lean = ease_io(prog(T, 6.0, 6.9))
        sh = 0.15 + 0.85 * win(T, 7.9, 9.6, 0.1, 0.3)
        return JNPose(lean=lean, arm="shake", face="o", look=(-0.8, 0.45), brows=0.8, shake=sh)
    if T < 14.5:
        k = ease_io(prog(T, 12.5, 13.3))
        el = tuple(lerp(a, b, k) for a, b in zip(ARMS["shake"][0], ARMS["hold"][0]))
        ha = tuple(lerp(a, b, k) for a, b in zip(ARMS["shake"][1], ARMS["hold"][1]))
        ra = lerp(ARMS["shake"][2], ARMS["hold"][2], k)
        return JNPose(lean=1 - k, arm=(el, ha, ra), face="smile" if k > 0.5 else "o", look=(-0.5 * (1 - k), 0.1),
                      brows=0.7 * (1 - k))
    if T < 39.0:
        face = "laugh" if 37.7 < T < 38.8 else "smile"
        look = (-0.35, 0.25) if T < 36.4 else (-0.55, 0.3)
        return JNPose(arm="lap", face=face, look=look, brows=0.0)
    if T < 41.9:
        return JNPose(arm="lap", face="smile", look=(-0.55, 0.3), brows=0.0)
    if T < 42.5:  # picks the rattle back up (loop to the opening)
        k = ease_io(prog(T, 41.9, 42.45))
        el = tuple(lerp(a, b, k) for a, b in zip(ARMS["lap"][0], ARMS["shake"][0]))
        ha = tuple(lerp(a, b, k) for a, b in zip(ARMS["lap"][1], ARMS["shake"][1]))
        ra = lerp(ARMS["lap"][2], ARMS["shake"][2], k)
        return JNPose(arm=(el, ha, ra), face="o" if k > 0.5 else "smile", look=(-0.65, 0.35), brows=0.7 * k)
    return JNPose(arm="shake", face="o", look=(-0.65, 0.35), brows=0.7, shake=0.15 + 0.85 * win(T, 43.6, 46, 0.2, 0.01))


# camera: (world x at screen centre, world y at screen centre, zoom)
CAM = [
    (0.0, (540, 960, 1.0)), (5.6, (530, 968, 1.03)), (6.8, (463, 1095, 1.1)), (12.4, (468, 1092, 1.12)),
    (13.3, (515, 960, 1.0)), (14.0, (515, 960, 1.0)),
    (29.0, (540, 960, 1.0)), (38.95, (545, 965, 1.03)),
    (39.0, (321, 1277, 1.7)), (41.95, (330, 1270, 1.76)), (42.45, (441, 1107, 1.3)), (42.95, (540, 965, 1.02)),
    (45.6, (540, 960, 1.0)),
]


def camera(T):
    # hard cuts at 39.0 (no easing across a cut)
    keys = [k for k in CAM if (k[0] < 39.0) == (T < 39.0)]
    return kf(T, keys)


def draw_wide(cx, T):
    camx, camy, z = camera(T)
    cx.save()
    cx.translate(W / 2, H / 2)
    cx.scale(z, z)
    cx.translate(-camx, -camy)
    room(cx)
    block(cx, 125, 1792)
    ball(cx, 500, 1782)
    # dashed personal-space circle (behind the baby)
    a_sp = win(T, 32.4, 35.9, 0.5, 0.5)
    if a_sp > 0.01:
        circle(cx, 268, 1500, 242 * (0.9 + 0.1 * ease_out(prog(T, 32.4, 33.0))))
        src(cx, WHITE, 0.25 * a_sp)
        cx.fill_preserve()
        src(cx, hexc("#9C8E80"), 0.9 * a_sp)
        cx.set_line_width(4)
        cx.set_dash([16, 12])
        cx.stroke()
        cx.set_dash([])
    p = jn_pose(T)
    baby(cx, 268, 1395, 1.0, baby_wide_pose(T))
    ang, sc, hand, ra = jn_sitting(cx, p, T)
    rh_body = rattle_head(hand[0], hand[1], ra, 1.0 / BODY_SC)
    rh = body_to_world(rh_body, p.lean)
    # rattle shake burst lines
    if p.arm == "shake" or isinstance(p.arm, tuple):
        a_b = clamp(p.shake - 0.2) / 0.8 if T < 6 or T > 42.5 else clamp((p.shake - 0.2) / 0.8)
        burst(cx, rh[0], rh[1], 78, 108, 7, rot=0.3 + 0.2 * math.sin(T * 9), alpha=a_b, lw=6)
    # prohibition sign over the rattle ("don't try to get their attention")
    a_no = win(T, 2.95, 5.35, 0.12, 0.3)
    if a_no > 0.01:
        k = back_out(prog(T, 2.95, 3.3))
        cx.save()
        cx.translate(rh[0], rh[1])
        cx.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k)
        cx.new_path()
        circle(cx, 0, 0, 125)
        src(cx, RED, 0.9 * a_no)
        cx.set_line_width(17)
        cx.stroke()
        stroke_line(cx, [(-88, -88), (88, 88)], RED, 17, 0.9 * a_no)
        cx.restore()
    # "Peekaboo!" (translation of the on-screen "Ce-eee!")
    a_pk = win(T, 7.95, 9.7, 0.1, 0.25)
    if a_pk > 0.01:
        k = back_out(prog(T, 7.95, 8.25))
        cx.save()
        cx.translate(rh[0] + 175, rh[1] - 10)
        cx.rotate(-0.16)
        cx.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
        ui.font(cx, 66)
        w = cx.text_extents("Peekaboo!").x_advance
        _outlined_text(cx, "Peekaboo!", -w / 2, 22, 66, a_pk, lw_k=0.16)
        cx.restore()
    # thought bubble: what we assume (baby bored / sleepy) - pops at "But it's actually the opposite"
    a_tb = win(T, 9.5, 13.05, 0.25, 0.08)
    if a_tb > 0.01:
        k = back_out(prog(T, 9.5, 9.95))
        head = body_to_world((795, 1112), p.lean)
        bx, by = 742, 690
        for i, (fx, rr) in enumerate(((0.25, 9), (0.5, 15))):
            if T > 9.5 + 0.08 * i:
                circle(cx, lerp(head[0] + 40, bx - 20, fx + 0.35), lerp(head[1] - 150, by + 130, fx + 0.35), rr)
                fs(cx, WHITE, INK, 3.5)
        cx.save()
        cx.translate(bx, by)
        cx.scale(k, k)
        baby_badge(cx, 0, 0, 112, BabyPose(eyes="closed", mouth="o", yaw=0.0), alpha=a_tb, bg=WHITE)
        ui.font(cx, 34)
        _outlined_text(cx, "z", 62, -58, 30, a_tb, fill=INK, outline=None)
        _outlined_text(cx, "z", 84, -82, 22, a_tb, fill=INK, outline=None)
        cx.restore()
    a_pop = win(T, 13.0, 14.0, 0.05, 0.5)
    if a_pop > 0.01:
        rr = 120 + 80 * ease_out(prog(T, 13.0, 13.6))
        burst(cx, 742, 690, rr, rr + 55, 8, rot=0.2, alpha=0.55 * a_pop, lw=5, c=hexc("#B8AA98"))
    # Just Needy follow card (replaces the source channel's follow card)
    a_card = win(T, 29.45, 31.65, 0.22, 0.25)
    if a_card > 0.01:
        follow_card(cx, 545, 690, a_card, back_out(prog(T, 29.45, 29.85)))
    # heart (heart rate slowing down): beats on the heartbeat sounds
    a_h = win(T, 33.0, 35.75, 0.25, 0.35)
    if a_h > 0.01:
        beat = max([math.exp(-((T - b) / 0.09) ** 2) for b in (33.3, 33.8, 34.3, 35.05)])
        heart(cx, 250, 1160, 1.3 * (1 + 0.22 * beat), a_h)
    a_h2 = win(T, 37.6, 39.0, 0.3, 0.3)
    if a_h2 > 0.01:
        u = prog(T, 37.6, 39.0)
        heart(cx, lerp(430, 540, u), lerp(1260, 1110, ease_out(u)), 0.85, a_h2)
    # pause icon of the last shot (pinned to the world, left of the baby)
    a_pz = win(T, 40.45, 43.25, 0.12, 0.4)
    if a_pz > 0.01:
        pause_icon(cx, 125, 1172, 58 * back_out(prog(T, 40.45, 40.75)), a_pz)
    cx.restore()


def follow_card(cx, x, y, a, k):
    cx.save()
    cx.translate(x, y)
    cx.rotate(-0.04)
    cx.scale(0.8 + 0.2 * k, 0.8 + 0.2 * k)
    cx.push_group()
    rrect(cx, -196, -122, 392, 254, 22)
    src(cx, (0, 0, 0, 0.16))
    cx.fill()
    rrect(cx, -196, -132, 392, 254, 22)
    fs(cx, WHITE, hexc("#E3DCD2"), 3)
    jn_badge(cx, -118, -48, 50, face="smile")
    ui.draw_text(cx, "JUST", 46, -60, 50, INK)
    ui.draw_text(cx, "NEEDY", 46, -8, 50, INK)
    ui.pill(cx, "Follow for more", 0, 70, 30, hexc("#A8693A"), fg=WHITE)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def close_pose(T):
    if T < 19.9:
        return BabyPose(yaw=0.0, look=(0.0, -0.2), eyes="open", brows="up", mouth="o")
    if T < 21.9:
        k = smooth(prog(T, 19.9, 20.4))
        return BabyPose(yaw=0.0, look=(0.0, 0.0), brows="annoyed", mouth="frown", lid=0.5 * k)
    if T < 27.4:
        k = smooth(prog(T, 21.9, 22.6))  # turns the head away
        return BabyPose(yaw=-0.42 * k, look=(-0.9 * k, 0.3 * k), brows="annoyed", mouth="frown", lid=0.45,
                        tilt=-0.08 * k)
    k = smooth(prog(T, 27.4, 27.9))
    return BabyPose(yaw=-0.42, look=(-0.9, 0.3), eyes="closed" if k > 0.5 else "open", brows="soft", mouth="frown",
                    lid=0.45, tilt=-0.08 - 0.05 * k)


def draw_close(cx, T):
    z = kf(T, [(14.0, 1.0), (29.0, 1.04)], ease=lambda x: x)
    cx.save()
    cx.translate(W / 2, H / 2)
    cx.scale(z, z)
    cx.translate(-W / 2, -H / 2)
    shelf_wall(cx)
    # water level: tiny bit -> fills with face / voice / expressions -> brimming -> eases off while breathing
    level = kf(T, [(14.4, 0.0), (14.9, 0.05), (17.4, 0.05), (18.0, 0.28), (18.6, 0.46), (19.2, 0.66), (20.2, 0.86),
                   (21.4, 1.0), (27.6, 1.0), (28.9, 0.74)], ease=smooth)
    over = win(T, 21.4, 28.4, 0.3, 0.6)
    a_g = smooth(prog(T, 14.2, 14.6))
    gy = 830 - 40 * (1 - back_out(prog(T, 14.2, 14.6)))
    glass(cx, 540, gy, level, alpha=a_g, wobble=0.6 + 0.6 * over, overflow=over, T=T)
    # icons falling into the glass: your face, your voice, your expressions
    for t0, kind in ((17.45, "face"), (18.45, "voice"), (19.05, "expr")):
        u = prog(T, t0, t0 + 0.9)
        if 0 < u < 1:
            a = 1 - smooth(prog(u, 0.75, 1.0))
            y = lerp(220, 660, ease_in(prog(u, 0.25, 1.0)))
            x = lerp(620, 548, prog(u, 0.25, 1.0))
            r = 38 * back_out(prog(u, 0.0, 0.2)) * (1 - 0.4 * prog(u, 0.6, 1.0))
            if kind == "face":
                jn_badge(cx, x, y, r, face="smile", alpha=a)
            elif kind == "voice":
                speaker_badge(cx, x, y, r, alpha=a)
            else:
                jn_badge(cx, x, y, r, face="o", alpha=a)
    # "I'm bored of you" icon, crossed out
    a_bb = win(T, 23.3, 25.3, 0.15, 0.2)
    if a_bb > 0.01:
        baby_badge(cx, 830, 720, 70 * back_out(prog(T, 23.3, 23.55)),
                   BabyPose(eyes="closed", mouth="o"), alpha=a_bb, slash=ease_out(prog(T, 24.45, 24.75)))
    a_p = win(T, 25.4, 29.2, 0.12, 0.01)
    if a_p > 0.01:
        pause_icon(cx, 890, 730, 86 * back_out(prog(T, 25.4, 25.7)), a_p)
    # the baby, big
    pose = close_pose(T)
    breath = 1 + 0.012 * math.sin(T * 2.2) + 0.02 * win(T, 27.5, 28.9, 0.6, 0.6) * math.sin((T - 27.5) * 4.0)
    cx.save()
    cx.translate(540, 1345 + 300)
    cx.scale(1.0, breath)
    cx.translate(-540, -(1345 + 300))
    baby(cx, 540, 1345, 3.18, pose, lw=9.0)
    cx.restore()
    # exhale puff
    a_ex = win(T, 27.9, 28.9, 0.15, 0.4)
    if a_ex > 0.01:
        u = prog(T, 27.9, 28.9)
        for i in range(3):
            xx = 300 - 60 * u - i * 18
            yy = 1490 + i * 22
            cx.arc(xx, yy, 26 + i * 6, 2.3, 3.6)
            src(cx, INK, 0.5 * a_ex)
            cx.set_line_width(5)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.stroke()
    cx.restore()


def _outlined_text(cx, s, x, y, size, a, lw_k=0.12, fill=WHITE, outline=hexc("#121318")):
    ui.font(cx, size)
    if outline is not None:
        cx.move_to(x, y + size * 0.06)
        cx.text_path(s)
        src(cx, (0, 0, 0, 0.35 * a))
        cx.fill()
        cx.move_to(x, y)
        cx.text_path(s)
        src(cx, outline, 0.95 * a)
        cx.set_line_width(size * lw_k)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke()
    cx.move_to(x, y)
    cx.text_path(s)
    src(cx, fill, a)
    cx.fill()


# ================================================================== post: vignette, cuts
_VIG = None
_VIG_ARR = None


def vignette():
    global _VIG, _VIG_ARR
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.6)) ** 2)
        a = np.clip((d - 0.55) / 0.6, 0, 1) ** 1.6 * 0.42
        # warm light pool behind the subjects (source has a soft spotlight on the wall)
        arr = np.zeros((H, W, 4), np.uint8)
        arr[..., 0] = 40
        arr[..., 1] = 52
        arr[..., 2] = 70
        arr[..., 3] = (a * 255).astype(np.uint8)
        # premultiply
        for c in range(3):
            arr[..., c] = (arr[..., c].astype(np.float32) * a).astype(np.uint8)
        _VIG_ARR = np.ascontiguousarray(arr)
        _VIG = cairo.ImageSurface.create_for_data(memoryview(_VIG_ARR), cairo.FORMAT_ARGB32, W, H)
    return _VIG


# ================================================================== timing (EN <-> original)
_TIMING = None


def timing():
    global _TIMING
    if _TIMING is None:
        _TIMING = json.load(open(os.path.join(BUILD, "timing.json")))
    return _TIMING


def anchors():
    tm = timing()
    en, orig = [0.0], [0.0]
    for l, o0, o1, _, _ in LINES:
        v = tm["lines"][l]
        for e, o in ((v["start"], o0), (v["end"], o1)):
            if e > en[-1] + 1e-3 and o > orig[-1] + 1e-3:
                en.append(e)
                orig.append(o)
    en.append(tm["duration"])
    orig.append(ORIG_DURATION)
    return np.array(en), np.array(orig)


def warp(t_en):
    en, orig = anchors()
    return float(np.interp(t_en, en, orig))


def unwarp(t_orig):
    en, orig = anchors()
    return float(np.interp(t_orig, orig, en))


_CAPS = None


def captions():
    global _CAPS
    if _CAPS is None:
        caps = {k: v.replace("*", "") for k, v in CAP.items()}
        _CAPS = ui.Captions(timing()["lines"], caps, [l[0] for l in LINES])
    return _CAPS


CAP_Y = 372
CAP_SIZE = 66


def draw_captions(cx, t):
    """Reference style: short chunks, bold white with a thin dark outline, whole chunk at once."""
    for t0, t1, words, _ in captions().chunks:
        if t0 <= t < t1:
            a = 1.0
            s = " ".join(w for w, _, _ in words)
            size = CAP_SIZE
            while ui.text_w(cx, s, size) > 940 and size > 44:
                size -= 2
            w = ui.text_w(cx, s, size)
            _outlined_text(cx, s, W / 2 - w / 2, CAP_Y, size, a, lw_k=0.13)


def frame(t_en, surf=None):
    surf = surf or cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    T = warp(t_en)
    if 14.0 <= T < 29.0:
        draw_close(cx, T)
    else:
        draw_wide(cx, T)
    cx.set_source_surface(vignette(), 0, 0)
    cx.paint()
    draw_captions(cx, t_en)
    return surf


def stills(times, orig=True):
    out = os.path.join(BUILD, "stills")
    os.makedirs(out, exist_ok=True)
    for s in times:
        t = float(s)
        te = unwarp(t) if orig else t
        surf = frame(te)
        p = os.path.join(out, f"s_{t:05.2f}.png")
        surf.write_to_png(p)
        print(p)


def _worker(job):
    i, a, b, path = job
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                             "-pix_fmt", "yuv420p", "-r", str(FPS), path], stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for f in range(a, b):
        frame(f / FPS, surf)
        surf.flush()
        proc.stdin.write(bytes(surf.get_data()))
    proc.stdin.close()
    proc.wait()
    return path


def video(workers=4):
    from multiprocessing import Pool
    dur = timing()["duration"]
    n = int(round(dur * FPS))
    seg = os.path.join(BUILD, "segments")
    os.makedirs(seg, exist_ok=True)
    k = 8
    bounds = [(i * n // k, (i + 1) * n // k) for i in range(k)]
    jobs = [(i, a, b, os.path.join(seg, f"seg_{i:02d}.mp4")) for i, (a, b) in enumerate(bounds)]
    with Pool(workers) as pool:
        paths = pool.map(_worker, jobs)
    lst = os.path.join(seg, "list.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    out = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print(out, n, "frames")


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills(sys.argv[2:])
    elif sys.argv[1] == "video":
        video()

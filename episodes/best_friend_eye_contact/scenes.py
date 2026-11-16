"""Shot-by-shot visuals, following the reference video's shot order and timing.

World space: one table with six friends. The camera frames it the way the reference
does (two-shot -> wide -> two-shot -> mid -> close-ups -> two-shot).
"""
import math

import cairo

from cinecode.core import (OUTLINE, circle, clamp, ease_io, ease_out, back_out, ellipse, fs, hexc, kf, line,
                           noise1, prog, rrect, shade, smooth, src, win, pulse)
from episodes.best_friend_eye_contact import rig
from episodes.best_friend_eye_contact.rig import Face, HOODIES
from episodes.best_friend_eye_contact.voice import layout, phrases

W, H = 1080, 1920
FPS = 30
DUR = 36.0

# ------------------------------------------------------------------ cast & world
HEAD_Y = 1120
R_MAIN = 132
R_BG = 124
TABLE_Y = 1468
YOU_X, FRIEND_X = 372, 708
SEATS = [  # (name, x, colour, R)
    ("far_left", -300, "teal", R_BG),
    ("speaker", 40, "rose", R_BG),
    ("you", YOU_X, "blue", R_MAIN),
    ("friend", FRIEND_X, "burgundy", R_MAIN),
    ("right", 1040, "mustard", R_BG),
    ("far_right", 1380, "sage", R_BG),
]

PURPLE = hexc("#8B67D8")
GOLD = hexc("#F2A93B")


def word_t(line_id, word, nth=0):
    for ln in layout():
        if ln["id"] == line_id:
            hits = [w for w in ln["words"] if w[0].strip(",.?!").lower() == word.lower()]
            return hits[nth][1]
    raise KeyError((line_id, word))


def line_t(line_id, which="start"):
    for ln in layout():
        if ln["id"] == line_id:
            return ln[which]
    raise KeyError(line_id)


# ------------------------------------------------------------------ camera
CLOSE = (540, 1010, 1.25)
WIDE = (540, 1050, 0.8)
MID = (540, 1000, 1.24)


def camera(t):
    """Returns (cx, cy, zoom). Hard cuts where the reference cuts; quick eased moves elsewhere."""
    if t < 24.0:
        keys = [(0.0, CLOSE[:2] + (1.25,)), (2.85, CLOSE[:2] + (1.31,)),
                (3.25, WIDE), (6.75, (540, 1045, 0.84)),
                (7.15, CLOSE[:2] + (1.27,)), (12.9, CLOSE[:2] + (1.33,)),
                (13.9, (540, 1000, 1.3)), (14.35, MID), (23.9, (540, 1000, 1.28))]
        return kf(t, keys, ease_io)
    if t < 26.5:   # cut: close-up on the friend
        z = 2.45 + 0.25 * smooth(prog(t, 24.0, 26.5))
        return (FRIEND_X - 10, HEAD_Y + 30, z)
    if t < 29.45:  # cut: close on you, archive opening above your head
        z = 1.95 + 0.08 * smooth(prog(t, 26.5, 29.45))
        return (YOU_X + 70, 1010, z)
    z = 1.22 + 0.08 * smooth(prog(t, 29.45, DUR))  # cut: back to the two of you
    return (540, 1010, z)


def apply_cam(cx, c):
    x, y, z = c
    cx.translate(W / 2, H / 2)
    cx.scale(z, z)
    cx.translate(-x, -y)


# ------------------------------------------------------------------ background
def draw_wall(cx, t):
    g = cairo.RadialGradient(W / 2, H * 0.38, 60, W / 2, H * 0.45, H * 0.75)
    g.add_color_stop_rgba(0, *hexc("#F6EEDF"))
    g.add_color_stop_rgba(0.55, *hexc("#EADDC7"))
    g.add_color_stop_rgba(1, *hexc("#CDBB9E"))
    cx.set_source(g)
    cx.paint()
    # soft warm lamp pool from above
    g = cairo.RadialGradient(W / 2, -200, 50, W / 2, -100, H * 0.85)
    g.add_color_stop_rgba(0, *hexc("#FFF6E2", 0.75))
    g.add_color_stop_rgba(1, *hexc("#FFF6E2", 0.0))
    cx.set_source(g)
    cx.paint()


def draw_end_glow(cx, t):
    a = smooth(prog(t, 31.7, 33.2))
    if a <= 0:
        return
    breathe = 1 + 0.03 * math.sin(t * 2.0)
    g = cairo.RadialGradient(540, 1060, 30, 540, 1080, 620 * breathe)
    g.add_color_stop_rgba(0, *hexc("#FFD98A", 0.55 * a))
    g.add_color_stop_rgba(0.5, *hexc("#FFE3A6", 0.28 * a))
    g.add_color_stop_rgba(1, *hexc("#FFE3A6", 0.0))
    cx.set_source(g)
    cx.paint()


def draw_table(cx):
    top = TABLE_Y
    # back edge shadow on bodies
    g = cairo.LinearGradient(0, top - 40, 0, top)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.18)
    cx.rectangle(-900, top - 40, 3000, 40)
    cx.set_source(g)
    cx.fill()
    # table top (seen slightly from above)
    g = cairo.LinearGradient(0, top, 0, top + 330)
    g.add_color_stop_rgba(0, *hexc("#C99A68"))
    g.add_color_stop_rgba(1, *hexc("#B5834F"))
    cx.rectangle(-900, top, 3000, 330)
    cx.set_source(g)
    cx.fill()
    for i, (yy, a) in enumerate(((top + 34, 0.18), (top + 78, 0.12), (top + 140, 0.15), (top + 215, 0.12), (top + 290, 0.14))):
        cx.move_to(-900, yy)
        for k in range(30):
            x = -900 + k * 100
            cx.line_to(x + 100, yy + math.sin(k * 1.7 + i) * 3)
        src(cx, hexc("#8A5A2E", a))
        cx.set_line_width(3)
        cx.stroke()
    line(cx, [(-900, top), (2100, top)], OUTLINE, 6)
    # front edge
    g = cairo.LinearGradient(0, top + 330, 0, top + 1400)
    g.add_color_stop_rgba(0, *hexc("#9E6E3F"))
    g.add_color_stop_rgba(0.08, *hexc("#8B5F35"))
    g.add_color_stop_rgba(1, *hexc("#6E4826"))
    cx.rectangle(-900, top + 330, 3000, 1400)
    cx.set_source(g)
    cx.fill()
    line(cx, [(-900, top + 330), (2100, top + 330)], OUTLINE, 6)
    cx.rectangle(-900, top + 336, 3000, 10)
    src(cx, hexc("#C99A68", 0.35))
    cx.fill()


def draw_table_props(cx):
    for x in (-470, -130, 205, 540, 875, 1210, 1550):
        rig.ring_bread_plate(cx, x, TABLE_Y + 92, 0.95) if x in (-130, 540, 1210) else None
    for x in (-380, -220, -40, 120, 290, 450, 630, 790, 960, 1120, 1300, 1460):
        rig.tea_glass(cx, x, TABLE_Y + 100 + (12 if (x // 10) % 3 == 0 else 0), 1.0)


# ------------------------------------------------------------------ character animation
def blink_amt(t, seed):
    # natural irregular blinks (~every 3-5 s), 0.16 s long
    period = 3.6 + (seed % 5) * 0.37
    phase = (t + seed * 1.37) % period
    return pulse(phase, 0.05, 0.11, 0.05)


def idle_face(name, t, seed):
    f = Face()
    f.blink = blink_amt(t, seed)
    f.bob = noise1(t * 0.6, seed) * 0.012
    f.tilt = noise1(t * 0.35, seed + 9) * 0.02
    f.look = (noise1(t * 0.25, seed + 3) * 0.02, 0.0)
    f.mouth = "smile"
    f.mouth_amt = 0.45
    return f


def face_speaker(t):
    f = idle_face("speaker", t, 2)
    f.facing = 0.35
    f.look = (0.03, 0.0)
    talking = t < 7.4
    if talking:
        f.mouth = "talk"
        f.mouth_amt = 0.35 + 0.65 * abs(math.sin(t * 13.0)) * (0.6 + 0.4 * noise1(t * 3, 4))
        f.brow_l = f.brow_r = (0.5, 0.0)
    return f


def face_you(t):
    f = idle_face("you", t, 7)
    f.facing = 0.15
    f.brow_l, f.brow_r = (0.05, 0.0), (0.0, 0.0)
    f.smirk = 0.3
    lock = word_t("L04", "lock")
    # 0-7: listening to the speaker on the left
    to_left = 1 - smooth(prog(t, lock - 0.45, lock))
    if t < lock:
        f.facing = 0.15 - 0.35 * to_left
        f.look = (-0.05 * to_left, 0.0)
        f.mouth_amt = 0.35
    # ridiculous remark: brows lift
    rid = word_t("L03", "ridiculous")
    f.brow_l = (f.brow_l[0] + 0.8 * pulse(t, rid, lock + 0.6, 0.25), 0)
    f.brow_r = (f.brow_r[0] + 0.5 * pulse(t, rid, lock + 0.6, 0.25), 0)
    # eye contact: turn toward friend
    if lock <= t < 24:
        k = smooth(prog(t, lock - 0.45, lock))
        f.facing = 0.15 + 0.35 * k
        f.look = (0.05 * k, 0.0)
    _shared_beats(f, t, side=-1)
    if t >= 29.45:
        f.facing = 0.45
        f.look = (0.05, 0.0)
        f.mouth_amt = 0.55 + 0.15 * smooth(prog(t, 31.7, 33.0))
    return f


def face_friend(t):
    f = idle_face("friend", t, 13)
    f.facing = -0.15
    f.smirk = -0.1
    lock = word_t("L04", "lock")
    to_left = 1 - smooth(prog(t, lock - 0.35, lock + 0.05))
    if t < lock + 0.05:
        f.facing = -0.15 - 0.2 * to_left
        f.look = (-0.06 * to_left, 0.0)
        f.mouth_amt = 0.35
    rid = word_t("L03", "ridiculous")
    f.brow_l = (0.7 * pulse(t, rid + 0.2, lock + 0.6, 0.25), 0)
    f.brow_r = (0.7 * pulse(t, rid + 0.2, lock + 0.6, 0.25), 0)
    if lock <= t < 24:
        k = smooth(prog(t, lock - 0.35, lock + 0.05))
        f.facing = -0.35 + (-0.45 + 0.35) * k
        f.look = (-0.06 + 0.0 * k, 0.0)
    _shared_beats(f, t, side=1)
    # close-up: the tiniest eyebrow lift
    if 24.0 <= t < 26.5:
        f.facing = -0.35
        f.look = (-0.04, 0.0)
        lift = word_t("L12", "lift")
        k = back_out(prog(t, lift - 0.05, lift + 0.3)) * (1 - 0.35 * smooth(prog(t, 25.9, 26.4)))
        f.brow_r = (0.9 * k, -0.15 * k)
        f.brow_l = (0.08 * k, 0.0)
        f.mouth = "smile"
        f.mouth_amt = 0.35 + 0.1 * k
        f.smirk = 0.6 * k
        f.blink = blink_amt(t + 0.9, 13) if t < lift - 0.3 or t > lift + 0.8 else 0
    if t >= 29.45:
        f.facing = -0.45
        f.look = (-0.05, 0.0)
        f.mouth_amt = 0.55 + 0.15 * smooth(prog(t, 31.7, 33.0))
    return f


def _shared_beats(f, t, side):
    """Expressions both friends share, mirrored by `side`."""
    every = word_t("L06", "everything")
    laugh_a, laugh_b = every - 0.15, line_t("L06", "end") + 0.45
    if laugh_a <= t < laugh_b:
        k = pulse(t, laugh_a + 0.1, laugh_b - 0.15, 0.12)
        f.eyes = "happy" if k > 0.5 else "open"
        f.mouth = "laugh" if k > 0.3 else f.mouth
        f.mouth_amt = 0.6 + 0.4 * abs(math.sin(t * 15))
        f.bob = -0.04 * abs(math.sin(t * 15)) * k
        f.tilt = side * -0.05 * k
        f.brow_l = f.brow_r = (0.6 * k, 0.0)
    # knowing look while "not a single word"
    if word_t("L05", "Not") <= t < laugh_a:
        k = smooth(prog(t, word_t("L05", "Not"), word_t("L05", "Not") + 0.3))
        if side < 0:
            f.brow_l = (0.75 * k, 0.0)
        else:
            f.brow_r = (0.75 * k, 0.0)
        f.mouth_amt = 0.4 + 0.25 * k
        f.smirk = 0.5 * k * (1 if side < 0 else -1)
    # mid shot: thinking, then reacting alike
    if 14.4 <= t < 18.9:
        f.look = (f.look[0], -0.03 * smooth(prog(t, 14.4, 15.0)))
    lt = line_t("L09")
    if lt - 0.1 <= t < line_t("L10") - 0.05:   # laughed at the same things
        k = pulse(t, lt, line_t("L10") - 0.2, 0.12)
        f.eyes = "happy" if k > 0.5 else "open"
        f.mouth = "laugh" if k > 0.3 else f.mouth
        f.mouth_amt = 0.6 + 0.4 * abs(math.sin(t * 14))
        f.bob = -0.035 * abs(math.sin(t * 14)) * k
        f.facing *= 0.4
        f.look = (0.0, 0.0)
    a0 = line_t("L10")
    if a0 - 0.05 <= t < line_t("L11") + 0.1:   # annoyed by the same people
        k = pulse(t, a0 + 0.05, line_t("L11") - 0.05, 0.15)
        f.brow_l = (-0.25 * k, 0.55 * k)
        f.brow_r = (-0.25 * k, 0.55 * k)
        f.mouth = "frown" if k > 0.4 else f.mouth
        f.mouth_amt = 0.6
        f.facing *= 0.4
        f.look = (0.0, 0.0)
    if line_t("L11") + 0.1 <= t < 24.0:  # building the archive: eyes follow the photos down
        f.facing *= 0.4
        f.look = (0.0, 0.03 * smooth(prog(t, line_t("L11") + 0.3, 23.5)))
        f.mouth_amt = 0.5


def draw_cast(cx, t):
    faces = {"speaker": face_speaker(t), "you": face_you(t), "friend": face_friend(t)}
    for i, (name, x, col, R) in enumerate(SEATS):
        f = faces.get(name) or idle_face(name, t, 20 + i * 3)
        if name not in faces:
            f.facing = 0.3 if x < 540 else -0.3
            f.look = (0.0 if t > 7.5 else -0.03, 0.0)
            # everyone hears the ridiculous remark, too
            if t < 7.4:
                rid = word_t("L03", "ridiculous")
                k = pulse(t, rid + 0.1 + i * 0.07, 7.0, 0.2)
                f.brow_l = f.brow_r = (0.6 * k, 0)
        rig.draw_person(cx, x, HEAD_Y + (6 if R < R_MAIN else 0), R, HOODIES[col], f, t,
                        breathe=math.sin(t * 1.6 + i))


# ------------------------------------------------------------------ overlays (world space)
def head_eye(name, t):
    """Approximate world position of the near eye used for the eye-contact line."""
    if name == "you":
        f = face_you(t)
        x, R = YOU_X, R_MAIN
        ex = x + f.facing * R * 0.2 + R * 0.26 * (1 - 0.15 * max(0, -f.facing)) + f.look[0] * R
    else:
        f = face_friend(t)
        x, R = FRIEND_X, R_MAIN
        ex = x + f.facing * R * 0.2 - R * 0.26 * (1 - 0.15 * max(0, f.facing)) + f.look[0] * R
    return ex, HEAD_Y - R * 0.08 + f.bob * R


def speech_bubble(cx, t):
    a = smooth(prog(t, 0.0, 0.25)) * (1 - smooth(prog(t, 8.5, 8.9)))
    if a <= 0:
        return
    pop = back_out(prog(t, word_t("L03", "Someone") - 0.05, word_t("L03", "Someone") + 0.3))
    grow = 1.0 + 0.12 * pop
    bx, by = 250, 760
    cx.save()
    cx.translate(bx, by)
    cx.scale(grow, grow)
    cx.push_group()
    w, h = 250, 112
    # tail toward the speaker
    cx.move_to(-w * 0.32, h * 0.32)
    cx.line_to(-w * 0.62, h * 1.28)
    cx.line_to(-w * 0.1, h * 0.42)
    cx.close_path()
    fs(cx, hexc("#FFFFFF"), OUTLINE, 6)
    rrect(cx, -w / 2, -h / 2, w, h, h / 2)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 6)
    cx.move_to(-w * 0.32 + 4, h * 0.32 - 6)
    cx.line_to(-w * 0.1 - 4, h * 0.42 - 8)
    src(cx, hexc("#FFFFFF"))
    cx.set_line_width(10)
    cx.stroke()
    # babble squiggles
    sp = 6 if t < 7.4 else 1.5
    for k in range(3):
        yy = -h * 0.24 + k * h * 0.24
        x0, x1 = -w * 0.32, w * (0.32 - 0.1 * (k == 2))
        n = 40
        for i in range(n + 1):
            u = i / n
            x = x0 + (x1 - x0) * u
            y = yy + math.sin(u * 5 * math.pi + t * sp + k) * 6
            (cx.move_to if i == 0 else cx.line_to)(x, y)
        src(cx, hexc("#8A7E6C"))
        cx.set_line_width(4.5)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def eye_line(cx, t, a_in, a_out, fade_out, glow=0.0):
    k = smooth(prog(t, a_in, a_in + 0.55))
    a = 1 - smooth(prog(t, a_out, a_out + fade_out))
    if k <= 0 or a <= 0:
        return
    (x0, y0), (x1, y1) = head_eye("you", t), head_eye("friend", t)
    x0 += 16
    x1 -= 16
    xe = x0 + (x1 - x0) * k
    ye = y0 + (y1 - y0) * k
    cx.save()
    if glow > 0:
        cx.move_to(x0, y0)
        cx.line_to(xe, ye)
        src(cx, hexc("#FFD27A", 0.35 * a * glow))
        cx.set_line_width(22)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.set_dash([2, 13], -t * 40)
    cx.move_to(x0, y0)
    cx.line_to(xe, ye)
    src(cx, GOLD, a)
    cx.set_line_width(7)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.restore()


def badge(cx, x, y, s, kind, alpha):
    if s <= 0.01 or alpha <= 0.01:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.push_group()
    circle(cx, 0, 0, 30)
    fs(cx, hexc("#FFFFFF"), OUTLINE, 4.5)
    if kind == "smile":
        circle(cx, 0, 0, 20)
        fs(cx, hexc("#FFC94A"), OUTLINE, 3)
        for ex in (-7, 7):
            cx.move_to(ex - 4, -2)
            cx.curve_to(ex - 2, -7, ex + 2, -7, ex + 4, -2)
            src(cx, OUTLINE)
            cx.set_line_width(2.6)
            cx.stroke()
        cx.move_to(-8, 4)
        cx.curve_to(-5, 13, 5, 13, 8, 4)
        cx.close_path()
        fs(cx, MOUTH, OUTLINE, 2)
    else:
        cx.select_font_face("Montserrat ExtraBold")
        cx.set_font_size(28)
        e = cx.text_extents("?!")
        cx.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
        src(cx, OUTLINE)
        cx.show_text("?!")
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


MOUTH = rig.MOUTH_DARK


def exchange_badges(cx, t):
    """One second where everything is said: a smiley travels along the look, '?!' answers."""
    t0 = word_t("L06", "one") - 0.2
    every = word_t("L06", "everything")
    (x0, y0), (x1, y1) = head_eye("you", t), head_eye("friend", t)
    u = ease_io(prog(t, t0, t0 + 0.75))
    a = smooth(prog(t, t0, t0 + 0.15)) * (1 - smooth(prog(t, every + 0.6, every + 0.9)))
    s = back_out(prog(t, t0, t0 + 0.3))
    bx = x1 - 30 + (x0 + 30 - (x1 - 30)) * u
    by = y1 - 60 - math.sin(u * math.pi) * 50
    badge(cx, bx, by, s * 0.9, "smile", a)
    t1 = every - 0.15
    a2 = smooth(prog(t, t1, t1 + 0.12)) * (1 - smooth(prog(t, line_t("L06", "end") + 0.4, line_t("L06", "end") + 0.7)))
    badge(cx, FRIEND_X + 105, HEAD_Y - 175, back_out(prog(t, t1, t1 + 0.3)) * 0.95, "q", a2)


def telepathy_zigzag(cx, t):
    t0 = line_t("L07") - 0.1
    isnt = word_t("L07", "isn't")
    grow = smooth(prog(t, t0, t0 + 0.35))
    gone = smooth(prog(t, isnt + 0.1, isnt + 0.35))
    if grow <= 0 or gone >= 1:
        return
    x0, x1 = YOU_X + 40, FRIEND_X - 40
    y = HEAD_Y - R_MAIN - 50
    n = 7
    pts = []
    for i in range(n + 1):
        u = i / n
        jitter = noise1(t * 22 + i * 3, 5) * 6
        pts.append((x0 + (x1 - x0) * u, y + (-28 if i % 2 else 22) + jitter))
    cx.save()
    cx.rectangle(x0 - 20, y - 80, (x1 - x0 + 40) * grow, 160)
    cx.clip()
    for w, c in ((20, hexc("#C9B6F5", 0.55 * (1 - gone))), (7, mix_alpha(PURPLE, 1 - gone))):
        cx.move_to(*pts[0])
        for p in pts[1:]:
            cx.line_to(*p)
        src(cx, c)
        cx.set_line_width(w)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.restore()


def mix_alpha(c, a):
    return (c[0], c[1], c[2], c[3] * a)


def thought_bubbles(cx, t):
    t0 = line_t("L08")
    t_big = word_t("L08", "react")
    a = smooth(prog(t, t0, t0 + 0.3)) * (1 - smooth(prog(t, line_t("L09") - 0.1, line_t("L09") + 0.15)))
    if a <= 0:
        return
    s = 0.55 + 0.45 * back_out(prog(t, t_big - 0.1, t_big + 0.35))
    sync = smooth(prog(t, word_t("L08", "similar") - 0.6, word_t("L08", "similar") + 0.2))
    for i, x in enumerate((YOU_X - 10, FRIEND_X + 10)):
        bx, by = x, HEAD_Y - R_MAIN - 175 - 40 * s
        pop = back_out(prog(t, t0 + i * 0.12, t0 + i * 0.12 + 0.35))
        cx.save()
        cx.push_group()
        circle(cx, x + (12 if i == 0 else -12), HEAD_Y - R_MAIN - 30, 9 * pop)
        fs(cx, hexc("#FFFFFF"), OUTLINE, 4)
        circle(cx, x + (22 if i == 0 else -22), HEAD_Y - R_MAIN - 70, 15 * pop)
        fs(cx, hexc("#FFFFFF"), OUTLINE, 4.5)
        rr = 78 * s * pop
        circle(cx, bx, by, rr)
        fs(cx, hexc("#FFFFFF"), OUTLINE, 5.5)
        # brain wave: phases drift into sync
        ph = (0 if i == 0 else 1.9) * (1 - sync)
        freq = 2.2 if i == 0 else 2.2 + 0.7 * (1 - sync)
        n = 48
        for j in range(n + 1):
            u = j / n
            xx = bx - rr * 0.62 + rr * 1.24 * u
            env = math.sin(u * math.pi) ** 0.8
            yy = by + math.sin(u * freq * 2 * math.pi + t * 5 + ph) * rr * 0.28 * env
            (cx.move_to if j == 0 else cx.line_to)(xx, yy)
        src(cx, PURPLE)
        cx.set_line_width(6 * s)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
        cx.pop_group_to_source()
        cx.paint_with_alpha(a)
        cx.restore()


BOX_X, BOX_Y = 540, TABLE_Y + 70


def archive(cx, t):
    """Shared memories: two photos, then a box they drop into."""
    if t >= 24.0:
        return
    p1 = word_t("L09", "laughed") + 0.05
    p2 = word_t("L10", "annoyed")
    bt = word_t("L11", "built")
    dt = word_t("L11", "archive")
    box_in = back_out(prog(t, bt - 0.05, bt + 0.35))
    drop = ease_io(prog(t, dt - 0.15, dt + 0.55))
    close = smooth(prog(t, dt + 0.45, dt + 0.85))
    photos = [(p1, 470, -0.12, hexc("#FFD98A"), "laugh"), (p2, 610, 0.1, hexc("#CDBDF2"), "angry")]
    # box body behind the photos
    if box_in > 0:
        cx.save()
        cx.translate(BOX_X, BOX_Y)
        cx.scale(box_in, box_in)
        rig.card_box(cx, 0, 0, 1.0, flaps=1 - close)
        cx.restore()
    for k, (tp, x, rot, col, faces) in enumerate(photos):
        s = back_out(prog(t, tp - 0.05, tp + 0.4))
        if s <= 0:
            continue
        y = 770 + k * 10 + math.sin(t * 1.8 + k) * 6
        tx, ty = BOX_X + (k - 0.5) * 30, BOX_Y - 150
        x2 = x + (tx - x) * drop
        y2 = y + (ty - y) * drop
        sc = (0.95 * s) * (1 - 0.6 * drop)
        a = 1 - smooth(prog(t, dt + 0.35, dt + 0.6))
        rig.polaroid(cx, x2, y2, sc, rot * (1 - drop), col, faces, a)
    if box_in > 0 and close > 0:  # closing flaps drawn over the dropped photos
        cx.save()
        cx.translate(BOX_X, BOX_Y)
        cx.scale(box_in, box_in)
        rig.card_box(cx, 0, 0, 1.0, flaps=1 - close)
        cx.restore()


def zip_over_head(cx, t):
    if not (26.5 <= t < 29.45):
        return
    t0 = line_t("L13")
    big = word_t("L13", "giant")
    s = 0.55 * back_out(prog(t, t0 + 0.1, t0 + 0.45)) + 0.45 * back_out(prog(t, big - 0.1, big + 0.35))
    zip_amt = ease_io(prog(t, word_t("L13", "ZIP") - 0.05, word_t("L13", "ZIP") + 0.6))
    open_amt = ease_out(prog(t, word_t("L13", "ZIP") + 0.5, word_t("L13", "ZIP") + 0.85))
    fade = 1 - smooth(prog(t, 29.0, 29.4))
    x, y = YOU_X, HEAD_Y - R_MAIN - 118
    rig.zip_file(cx, x, y + math.sin(t * 2.2) * 4, s * 1.05, open_amt, zip_amt, fade)
    if open_amt > 0:  # memories spill out as it opens
        for k, (dx, col, faces) in enumerate(((-70, hexc("#FFD98A"), "laugh"), (70, hexc("#CDBDF2"), "angry"),
                                               (0, hexc("#BFE3CF"), "laugh"))):
            u = ease_out(prog(t, word_t("L13", "ZIP") + 0.55 + k * 0.08, 29.2))
            rig.polaroid(cx, x + dx * u * 2.1, y - 20 - 45 * u - (25 if k == 2 else 0), 0.25 + 0.3 * u,
                         (k - 1) * 0.25 * u, col, faces, fade * smooth(prog(u, 0, 0.15)))
        # sparkle burst
        b = prog(t, word_t("L13", "ZIP") + 0.5, word_t("L13", "ZIP") + 1.0)
        if 0 < b < 1:
            for k in range(8):
                ang = k / 8 * 2 * math.pi
                r0, r1 = 110 + 80 * b, 130 + 120 * b
                line(cx, [(x + math.cos(ang) * r0, y + math.sin(ang) * r0 * 0.8),
                          (x + math.cos(ang) * r1, y + math.sin(ang) * r1 * 0.8)],
                     hexc("#FFC94A", 1 - b), 7)


# ------------------------------------------------------------------ captions (screen space)
CAP_Y = 300
CAP_SIZE = 66
CAP_MAXW = 940


def _wrap(cx, words):
    lines, cur = [], []
    for w in words:
        test = " ".join([x[0] for x in cur + [w]])
        if cx.text_extents(test).x_advance > CAP_MAXW and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    if len(lines) == 2 and len(lines[1]) == 1 and len(lines[0]) > 2:  # avoid orphans
        lines[1].insert(0, lines[0].pop())
    return lines


def draw_captions(cx, t):
    cur = None
    for i, p in enumerate(PHRASES):
        nxt = PHRASES[i + 1]["t0"] if i + 1 < len(PHRASES) else DUR
        hold_end = min(nxt - 0.02, p["t1"] + (0.55 if p["last_in_line"] else 0.15))
        if p["t0"] - 0.05 <= t < hold_end:
            cur = (p, hold_end)
            break
    if not cur:
        return
    p, hold_end = cur
    a = smooth(prog(t, p["t0"] - 0.05, p["t0"] + 0.06)) * (1 - smooth(prog(t, hold_end - 0.08, hold_end)))
    cx.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(CAP_SIZE)
    lines = _wrap(cx, p["words"])
    lh = CAP_SIZE * 1.18
    y0 = CAP_Y - (len(lines) - 1) * lh / 2
    for li, ws in enumerate(lines):
        s = " ".join(w[0] for w in ws)
        e = cx.text_extents(s)
        x = W / 2 - e.x_advance / 2
        y = y0 + li * lh + CAP_SIZE * 0.35
        for w, w0, _ in ws:
            spoken = t >= w0 - 0.04
            cx.move_to(x, y)
            cx.text_path(w)
            # outline + soft shadow
            cx.save()
            cx.translate(0, 5)
            src(cx, (0, 0, 0, 0.35 * a))
            cx.fill_preserve()
            cx.restore()
            src(cx, hexc("#1B1B22", a))
            cx.set_line_width(13)
            cx.set_line_join(cairo.LINE_JOIN_ROUND)
            cx.stroke_preserve()
            src(cx, hexc("#FFFFFF", a * (1.0 if spoken else 0.5)))
            cx.fill()
            x += cx.text_extents(w + " ").x_advance


PHRASES = phrases()


# ------------------------------------------------------------------ frame
def render(t, surface=None):
    surf = surface or cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    draw_wall(cx, t)
    draw_end_glow(cx, t)
    cam = camera(t)
    cx.save()
    apply_cam(cx, cam)
    # soft contact shadows behind the cast
    for name, x, col, R in SEATS:
        g = cairo.RadialGradient(x + 20, HEAD_Y + 40, R * 0.5, x + 20, HEAD_Y + 60, R * 2.0)
        g.add_color_stop_rgba(0, 0.35, 0.25, 0.1, 0.12)
        g.add_color_stop_rgba(1, 0.35, 0.25, 0.1, 0.0)
        cx.set_source(g)
        cx.paint()
    draw_cast(cx, t)
    draw_table(cx)
    draw_table_props(cx)
    archive(cx, t)
    speech_bubble(cx, t)
    lock = word_t("L04", "lock")
    if t < 24.0:
        eye_line(cx, t, lock - 0.1, line_t("L07") - 0.2, 0.25)
    if t >= 29.45:
        eye_line(cx, t, 29.6, 99, 0.1, glow=smooth(prog(t, 31.7, 33.0)))
    exchange_badges(cx, t)
    telepathy_zigzag(cx, t)
    thought_bubbles(cx, t)
    zip_over_head(cx, t)
    cx.restore()
    # gentle vignette
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.12, 0.07, 0.02, 0.28)
    cx.set_source(g)
    cx.paint()
    draw_captions(cx, t)
    return surf

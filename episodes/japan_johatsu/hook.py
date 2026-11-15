"""Opening hook (0:00-3:34): money counting -> secret payment -> he walks out, door closes -> empty apartment.

Replaces the original single hook shot. Everything from 3.34 s (the Night Movers neon cut) is untouched."""
import math
import random

import cairo

from episodes.japan_johatsu import sets as S
from episodes.japan_johatsu.art import (H, INK, JP_FONT, W, alpha, back_out, cached_layer, camera, contact_shadow,
                                        eio, ellipse, eout, fill_ink, glow, handheld, hx, ink, lerp, light_cone, lin,
                                        mixc, paint_layer, person, poly, prog, rad, rrect, shade, smooth, src, text)

WARM = hx("#ffcf8a")
SKIN = hx("#f1c7a1")
SLEEVE = hx("#283553")
NOTE_W, NOTE_H = 520, 250

# counting rhythm: bill k is peeled off the stack at FLICKS[k] and lands on the pile 0.17 s later
FLICKS = [-0.06, 0.13, 0.32, 0.51, 0.70]
CARRY = 0.17


# ---------------------------------------------------------------- props
def banknote(cx, x, y, rot=0.0, sc=1.0, a=1.0, blur=0):
    """Stylised ¥10,000 note centred at (x, y)."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(sc, sc)
    cx.push_group()
    w, h = NOTE_W, NOTE_H
    rrect(cx, -w / 2, -h / 2, w, h, 8)
    lin(cx, -w / 2, -h / 2, w / 2, h / 2, [(0, hx("#e9dfc2")), (0.5, hx("#ddd0ac")), (1, hx("#cbbb92"))])
    cx.fill_preserve()
    src(cx, hx("#7a6646"))
    cx.set_line_width(3)
    cx.stroke()
    # guilloche border
    rrect(cx, -w / 2 + 16, -h / 2 + 16, w - 32, h - 32, 6)
    src(cx, alpha(hx("#8a7350"), 0.8))
    cx.set_line_width(4)
    cx.stroke()
    cx.save()
    rrect(cx, -w / 2 + 16, -h / 2 + 16, w - 32, h - 32, 6)
    cx.clip()
    for k in range(-30, 30):
        cx.move_to(-w / 2 + k * 18, -h / 2)
        cx.curve_to(-w / 2 + k * 18 + 40, -h / 4, -w / 2 + k * 18 - 40, h / 4, -w / 2 + k * 18, h / 2)
    src(cx, alpha(hx("#a08a62"), 0.18))
    cx.set_line_width(1.5)
    cx.stroke()
    cx.restore()
    # watermark oval (right) with faint portrait silhouette
    ellipse(cx, w * 0.26, 0, 70, 88)
    src(cx, alpha(hx("#f3ecd8"), 0.9))
    cx.fill_preserve()
    src(cx, alpha(hx("#8a7350"), 0.6))
    cx.set_line_width(3)
    cx.stroke()
    ellipse(cx, w * 0.26, -14, 26, 32)
    src(cx, alpha(hx("#c9b98f"), 0.6))
    cx.fill()
    ellipse(cx, w * 0.26, 46, 44, 26)
    cx.fill()
    # denominations + label
    text(cx, "10000", -w / 2 + 34, -h / 2 + 62, 40, hx("#5b4a30"), anchor="l")
    text(cx, "壱万円", -40, 22, 66, hx("#5b4a30"), font=JP_FONT)
    text(cx, "日本銀行券", -40, 78, 26, hx("#6f5d40"), font=JP_FONT)
    cx.arc(w / 2 - 44, h / 2 - 44, 22, 0, 2 * math.pi)
    src(cx, alpha(hx("#c0453a"), 0.75))
    cx.fill()
    text(cx, "10000", w / 2 - 34, h / 2 - 30, 30, hx("#5b4a30"), anchor="r")
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def note_shadow(cx, x, y, rot, sc=1.0, a=0.45, lift=0.0):
    cx.save()
    cx.translate(x + 14 + lift * 30, y + 22 + lift * 46)
    cx.rotate(rot)
    cx.scale(sc * (1 + lift * 0.08), sc * (1 + lift * 0.08))
    for k, aa in enumerate((0.20, 0.14, 0.09)):
        g = 8 + k * 10 + lift * 20
        rrect(cx, -NOTE_W / 2 - g, -NOTE_H / 2 - g, NOTE_W + 2 * g, NOTE_H + 2 * g, 20 + g)
        src(cx, (0, 0, 0, aa * a * (1 - lift * 0.5)))
        cx.fill()
    cx.restore()


def stack(cx, x, y, n, rot=0.0, sc=1.0, seed=1):
    rng = random.Random(seed)
    note_shadow(cx, x, y, rot, sc, 0.7)
    for k in range(n):
        dx, dy, dr = rng.uniform(-5, 5), rng.uniform(-4, 4), rng.uniform(-0.03, 0.03)
        banknote(cx, x + dx, y - k * 3 + dy, rot + dr, sc)


def hand(cx, x, y, rot, sc=1.0, glove=False, grip=0.0, cuff=SLEEVE):
    """Cartoon hand in the cast's style (thick ink, shaded skin), wrist at (x, y), fingers toward +x."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(sc, sc)
    skin = hx("#1b1c21") if glove else SKIN
    lw = 7
    # sleeve
    rrect(cx, -330, -78, 300, 156, 50)
    lin(cx, 0, -78, 0, 78, [(0, shade(cuff, 0.18)), (1, shade(cuff, -0.3))])
    cx.fill_preserve()
    ink(cx, lw)
    if not glove:
        rrect(cx, -70, -66, 44, 132, 14)
        src(cx, hx("#eef0f2"))
        cx.fill_preserve()
        ink(cx, lw * 0.8)
    # fingers
    curl = grip
    for i, (fy, fl) in enumerate(((-44, 118), (-14, 132), (16, 126), (44, 104))):
        L = fl * (1 - 0.35 * curl)
        rrect(cx, 40, fy - 15, L, 30, 15)
        lin(cx, 0, fy - 15, 0, fy + 15, [(0, shade(skin, 0.2)), (1, shade(skin, -0.15))])
        cx.fill_preserve()
        ink(cx, lw)
    # palm
    rrect(cx, -40, -70, 130, 140, 50)
    rad(cx, 10, -20, 5, 140, [(0, shade(skin, 0.22)), (1, shade(skin, -0.2))])
    cx.fill_preserve()
    ink(cx, lw)
    # thumb
    cx.save()
    cx.translate(40, -64)
    cx.rotate(-0.9 + 0.5 * curl)
    rrect(cx, -10, -16, 96, 32, 16)
    lin(cx, 0, -16, 0, 16, [(0, shade(skin, 0.25)), (1, shade(skin, -0.1))])
    cx.fill_preserve()
    ink(cx, lw)
    cx.restore()
    if glove:
        # leather sheen + cuff seam
        cx.save()
        cx.set_operator(cairo.OPERATOR_ADD)
        ellipse(cx, 20, -38, 60, 14)
        src(cx, (1, 0.85, 0.6, 0.10))
        cx.fill()
        for i, fy in enumerate((-44, -14, 16, 44)):
            rrect(cx, 70, fy - 9, 50, 5, 3)
            src(cx, (1, 0.85, 0.6, 0.08))
            cx.fill()
        cx.restore()
        cx.move_to(-36, -60)
        cx.line_to(-36, 60)
        src(cx, hx("#3a3b42"))
        cx.set_line_width(4)
        cx.stroke()
    cx.restore()


def hand_tip(cx, tx, ty, rot, sc=1.0, **kw):
    """Hand whose middle fingertip lands on (tx, ty), fingers pointing along rot."""
    reach = 165 * sc
    hand(cx, tx - math.cos(rot) * reach, ty - math.sin(rot) * reach, rot, sc, **kw)


# ---------------------------------------------------------------- table + background
def table_bg(cx):
    lin(cx, 0, 0, 0, H, [(0, hx("#2a190e")), (0.45, hx("#4a2c18")), (1, hx("#20130a"))])
    cx.paint()
    rng = random.Random(14)
    for k in range(70):
        y = rng.uniform(0, H)
        cx.move_to(0, y)
        cx.curve_to(W * 0.3, y + rng.uniform(-30, 30), W * 0.7, y + rng.uniform(-30, 30), W, y + rng.uniform(-20, 20))
        src(cx, (0, 0, 0, rng.uniform(0.05, 0.16)))
        cx.set_line_width(rng.uniform(1, 5))
        cx.stroke()
    for k in range(10):
        cx.rectangle(0, k * 210 + 60, W, 3)
        src(cx, (0, 0, 0, 0.28))
        cx.fill()


def room_bokeh(cx):
    """Out-of-focus room above the table edge (blurred once for depth of field)."""
    lin(cx, 0, 0, 0, 520, [(0, hx("#120c10")), (1, hx("#2a1c18"))])
    cx.rectangle(0, 0, W, 520)
    cx.fill()
    S.skyline(cx, 640, 40, 380, 360, seed=3)
    cx.rectangle(560, 20, 80, 460)
    src(cx, hx("#1f4b3c"))
    cx.fill()
    S.books(cx, 60, 420, 14)
    glow(cx, 240, 120, 260, WARM, 0.45)
    for k in range(9):
        glow(cx, 700 + (k * 53) % 300, 80 + (k * 97) % 280, 30, hx("#ffd98a"), 0.4)
    cx.rectangle(0, 500, W, 40)
    src(cx, hx("#1a0f08"))
    cx.fill()


def table_layer(cx):
    table_bg(cx)
    paint_layer(cx, cached_layer("hook_bokeh", room_bokeh, blur=22))
    # table edge
    cx.rectangle(0, 520, W, 26)
    lin(cx, 0, 520, 0, 546, [(0, hx("#7a4f2e")), (1, hx("#3a2414"))])
    cx.fill()


def lamp_light(cx, k=1.0):
    glow(cx, 300, 560, 1300, WARM, 0.20 * k, sy=0.8)
    glow(cx, 520, 980, 700, WARM, 0.10 * k)


# ---------------------------------------------------------------- shots
def shot_count(cx, t, d, T):
    """0.00-0.80 extreme close-up: left hand holds the stack, right hand peels notes onto a pile."""
    ox, oy, r = handheld(T, 1.2, 3)
    camera(cx, lerp(1.05, 1.10, eio(t / d)), 540, 930, r, ox, oy)
    paint_layer(cx, cached_layer("hook_table", table_layer))
    lamp_light(cx)
    SC = 1.22
    sx, sy, srot = 560, 1040, -0.04   # stack (held by the left hand)
    px, py, prot = 520, 690, 0.06     # pile
    landed = sum(1 for f in FLICKS if T >= f + CARRY)
    remaining = 9 - sum(1 for f in FLICKS if T >= f)
    if landed:
        note_shadow(cx, px, py, prot, SC, 0.6)
        rng = random.Random(5)
        for k in range(landed):
            banknote(cx, px + rng.uniform(-14, 14), py - k * 3 + rng.uniform(-8, 8), prot + rng.uniform(-0.06, 0.06),
                     SC)
    stack(cx, sx, sy, remaining, srot, SC, seed=2)
    # left hand clamps the stack's left end (thumb over the top note)
    hand_tip(cx, sx - 200, sy - 10, -0.12, 1.45, grip=0.35)
    # right hand: fingertips on the right end of the moving note
    tip = None
    for f in FLICKS:
        k = (T - f) / CARRY
        if 0 <= k < 1:
            lift = math.sin(k * math.pi)
            for trail, a in ((0.12, 0.22), (0.06, 0.45), (0.0, 1.0)):
                kk = max(0.0, k - trail)
                ee = eio(kk)
                bx = lerp(sx, px, ee)
                by = lerp(sy, py, ee) - math.sin(kk * math.pi) * 70
                br = lerp(srot, prot, ee) - 0.18 * math.sin(kk * math.pi)
                if trail == 0.0:
                    note_shadow(cx, bx, by, br, SC, 0.5, lift)
                    tip = (bx + math.cos(br) * 250, by + math.sin(br) * 250)
                banknote(cx, bx, by, br, SC * (1 + 0.05 * lift), a)
            break
    if tip is None:
        prev = max([f for f in FLICKS if f + CARRY <= T] or [FLICKS[0]])
        nxt = min([f for f in FLICKS if f > T] or [prev + 0.19])
        kk = eio(prog(T, prev + CARRY, nxt))
        tip = (lerp(px + 250, sx + 250, kk), lerp(py, sy, kk) - math.sin(kk * math.pi) * 30)
    hand_tip(cx, tip[0], tip[1], math.pi + 0.15, 1.45, grip=0.3)
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    lin(cx, 0, 520, W, H, [(0, (1, 0.8, 0.5, 0.06)), (1, (1, 0.8, 0.5, 0.0))])
    cx.paint()
    cx.restore()


def shot_slide(cx, t, d, T):
    """0.80-1.25: both hands push the squared stack across the table, away from camera."""
    ox, oy, r = handheld(T, 1.0, 5)
    camera(cx, 1.04, 540, 930, r, ox, oy)
    paint_layer(cx, cached_layer("hook_table", table_layer))
    lamp_light(cx)
    k = eio(prog(T, 0.82, 1.22))
    y = lerp(1100, 720, k)
    SC = 1.22
    stack(cx, 540, y, 6, 0.0, SC, seed=3)
    hand_tip(cx, 300, y + 90, -math.pi / 2 + 0.35, 1.45, grip=0.05)
    hand_tip(cx, 780, y + 90, -math.pi / 2 - 0.35, 1.45, grip=0.05)


def shot_take(cx, t, d, T):
    """1.25-1.70: a black-gloved hand reaches in from the dark and pulls the money away."""
    ox, oy, r = handheld(T, 0.8, 7)
    camera(cx, 1.12, 540, 900, r, ox, oy)
    paint_layer(cx, cached_layer("hook_table", table_layer))
    lamp_light(cx, 0.8)
    SC = 1.22
    reach = eout(prog(T, 1.25, 1.42))
    pull = eio(prog(T, 1.47, 1.70))
    sy_ = lerp(860, -300, pull)
    stack(cx, 540, sy_, 6, 0.05 * pull, SC, seed=3)
    tip_y = lerp(-200, sy_ + 40, reach) if pull == 0 else sy_ + 40
    hand_tip(cx, 560, tip_y, math.pi / 2 + 0.05, 1.7, glove=True,
             grip=lerp(0.0, 0.8, prog(T, 1.39, 1.47)), cuff=hx("#2e3036"))
    lin(cx, 0, -200, 0, 560, [(0, (0, 0, 0, 0.8)), (1, (0, 0, 0, 0))])
    cx.rectangle(-200, -400, W + 400, 960)
    cx.fill()


# corridor: simple pinhole projection, world units (X right, Y down, Z forward)
F, CXP, CYP = 900, 680, 860
WALL_X, RAIL_X, FLOOR_Y, CEIL_Y = -1.3, 1.4, 1.6, -1.5


def P(X, Y, Z):
    return (CXP + F * X / Z, CYP + F * Y / Z)


def corridor_layer(cx):
    lin(cx, 0, 0, 0, H, [(0, hx("#070b1a")), (1, hx("#0d1226"))])
    cx.paint()
    z0, z1 = 1.0, 40.0
    # night city beyond the railing (right)
    S.skyline(cx, CXP, 300, W - CXP, 560, seed=17, lit=0.5)
    # ceiling
    poly(cx, [P(WALL_X, CEIL_Y, z0), P(RAIL_X, CEIL_Y, z0), P(RAIL_X, CEIL_Y, z1), P(WALL_X, CEIL_Y, z1)])
    src(cx, hx("#2a2f3a"))
    cx.fill()
    # left wall
    poly(cx, [P(WALL_X, CEIL_Y, z0), P(WALL_X, CEIL_Y, z1), P(WALL_X, FLOOR_Y, z1), P(WALL_X, FLOOR_Y, z0)])
    lin(cx, 0, 0, CXP, 0, [(0, hx("#5d6470")), (1, hx("#2a2f3a"))])
    cx.fill()
    # floor
    poly(cx, [P(WALL_X, FLOOR_Y, z0), P(RAIL_X + 0.5, FLOOR_Y, z0), P(RAIL_X, FLOOR_Y, z1), P(WALL_X, FLOOR_Y, z1)])
    lin(cx, 0, CYP, 0, H, [(0, hx("#1d212b")), (1, hx("#3c414c"))])
    cx.fill()
    for z in (2, 3, 4, 5.5, 7, 9, 12, 16, 22):
        a, b = P(WALL_X, FLOOR_Y, z), P(RAIL_X, FLOOR_Y, z)
        cx.move_to(*a)
        cx.line_to(*b)
        src(cx, (0, 0, 0, 0.25))
        cx.set_line_width(3)
        cx.stroke()
    # railing: low wall + top rail
    poly(cx, [P(RAIL_X, 0.55, z0), P(RAIL_X, 0.55, z1), P(RAIL_X, FLOOR_Y, z1), P(RAIL_X, FLOOR_Y, z0)])
    lin(cx, CXP, 0, W, 0, [(0, hx("#3a404c")), (1, hx("#7a808c"))])
    cx.fill()
    cx.move_to(*P(RAIL_X, 0.5, z0))
    cx.line_to(*P(RAIL_X, 0.5, z1))
    src(cx, hx("#9aa0aa"))
    cx.set_line_width(10)
    cx.stroke()
    # far doors on the left wall
    for zc in (6.0, 9.5, 13.0, 17.0):
        draw_door(cx, zc, 0.0, lit=False)
    # fluorescent ceiling lights + pools
    for z in (2.2, 4.6, 8.0, 12.5, 18):
        a = P(-0.25, CEIL_Y + 0.02, z)
        b = P(0.25, CEIL_Y + 0.02, z)
        cx.move_to(*a)
        cx.line_to(*b)
        src(cx, hx("#e8f6ff"))
        cx.set_line_width(max(3, 40 / z))
        cx.stroke()
        glow(cx, (a[0] + b[0]) / 2, a[1], 520 / z ** 0.7, hx("#cfe8ff"), 0.35)
        fp = P(0.0, FLOOR_Y, z + 0.3)
        glow(cx, fp[0], fp[1], 700 / z ** 0.8, hx("#bfe0ff"), 0.10, sy=0.35)
    # electricity meter box near the door
    poly(cx, [P(WALL_X, -0.3, 2.0), P(WALL_X, -0.3, 2.15), P(WALL_X, 0.2, 2.15), P(WALL_X, 0.2, 2.0)])
    src(cx, hx("#8a909a"))
    cx.fill()


DOOR_Z = (2.4, 3.5)  # near door span on the left wall


def draw_door(cx, zc, open_a, lit=True, w=1.1):
    za, zb = zc - w / 2, zc + w / 2
    top = -0.7
    # frame
    poly(cx, [P(WALL_X, top - 0.08, za - 0.08), P(WALL_X, top - 0.08, zb + 0.08), P(WALL_X, FLOOR_Y, zb + 0.08),
              P(WALL_X, FLOOR_Y, za - 0.08)])
    src(cx, hx("#2a2d33"))
    cx.fill()
    # doorway (interior light)
    poly(cx, [P(WALL_X, top, za), P(WALL_X, top, zb), P(WALL_X, FLOOR_Y, zb), P(WALL_X, FLOOR_Y, za)])
    src(cx, hx("#e8b770") if lit else hx("#141720"))
    cx.fill()
    if lit and open_a > 0.05:
        c = P(WALL_X, 0.4, zc)
        glow(cx, c[0] + 60, c[1], 420, WARM, 0.35 * min(1, open_a))
    # door panel hinged at the far edge (zb), opening outward into the corridor
    hx_, hz = WALL_X, zb
    ex, ez = WALL_X + w * math.sin(open_a), zb - w * math.cos(open_a)
    pts = [P(hx_, top, hz), P(ex, top, ez), P(ex, FLOOR_Y, ez), P(hx_, FLOOR_Y, hz)]
    poly(cx, pts)
    shadev = 0.15 + 0.25 * math.sin(open_a)
    lin(cx, pts[0][0], 0, pts[1][0], 0, [(0, mixc(hx("#5b6a8a"), hx("#000000"), shadev)),
                                         (1, mixc(hx("#7a88a6"), hx("#000000"), shadev))])
    cx.fill_preserve()
    ink(cx, 4, hx("#0c0d12"))
    # handle + number plate
    hp_ = P(lerp(hx_, ex, 0.86), 0.45, lerp(hz, ez, 0.86))
    cx.arc(hp_[0], hp_[1], max(3, 50 / zc), 0, 2 * math.pi)
    src(cx, hx("#c9ccd2"))
    cx.fill()
    if open_a < 0.05:
        np_ = P(WALL_X, -0.45, zc)
        sz = 120 / zc
        rrect(cx, np_[0] - sz * 0.6, np_[1] - sz * 0.25, sz * 1.2, sz * 0.5, 3)
        src(cx, hx("#d9dce2"))
        cx.fill()


def shot_corridor(cx, t, d, T):
    """1.70-2.80: night corridor. He steps out with a small bag, the door shuts, he walks off; hold on the door."""
    hold = eio(prog(T, 2.30, 2.80))
    ox, oy, r = handheld(T, 0.6, 9)
    camera(cx, lerp(1.0, 1.16, hold), lerp(560, 400, hold), lerp(980, 960, hold), r, ox, oy)
    paint_layer(cx, cached_layer("hook_corridor", corridor_layer))
    zc = sum(DOOR_Z) / 2
    # door: open while he steps out, swings shut at 2.24-2.46
    open_a = math.radians(78) * (1 - eio(prog(T, 2.24, 2.46)))
    if T >= 2.46:  # latch overshoot
        open_a = math.radians(1.2) * max(0.0, 1 - (T - 2.46) / 0.08)
    # walk path (world X, Z): out of the doorway, then away down the corridor
    k1 = eout(prog(T, 1.70, 2.02))
    k2 = prog(T, 2.02, 2.80)
    X = lerp(-1.6, -0.35, k1) + lerp(0, 0.6, k2)
    Z = lerp(zc - 0.15, zc - 0.3, k1) + 7.5 * k2 ** 1.3
    face = "right" if T < 2.02 else "back"
    bob = abs(math.sin(T * 11)) * 0.05
    foot = P(X, FLOOR_Y - bob, Z)
    h_px = F * 2.15 / Z

    def bag(c, hl, hr, s):
        x, y = hr if face != "back" else hl
        c.move_to(x, y)
        c.line_to(x, y + 6 * s)
        ink(c, 1.4 * s)
        rrect(c, x - 10 * s, y + 6 * s, 20 * s, 13 * s, 4 * s)
        src(c, hx("#3b3f47"))
        c.fill_preserve()
        ink(c, 1.6 * s)

    swing = math.sin(T * 11) * 14
    draw_son = lambda: person(cx, foot[0], foot[1], h_px, "son",
                              dict(face=face, eyes="dot", brow="sad", mouth="flat", look=(1, 0.3),
                                   arms=(10 + swing, 10, -14 - swing, -8), hold=bag),
                              light=(-1, WARM if Z < 4 else hx("#cfe8ff")), t=T)
    # depth order: while he is still in/near the doorway he is in front of the open panel
    if Z < DOOR_Z[1] + 0.2:
        draw_door(cx, zc, open_a)
        draw_son()
    else:
        draw_son()
        draw_door(cx, zc, open_a)
    # warm spill from the doorway falls away as the door shuts
    sp = P(-1.0, FLOOR_Y, zc)
    glow(cx, sp[0], sp[1], 380, WARM, 0.22 * (open_a / math.radians(78)), sy=0.4)


def shot_empty(cx, t, d, T):
    """2.80-3.34: match cut to the apartment he left: lamp on, tea still steaming, nobody there."""
    ox, oy, r = handheld(T, 0.8, 11)
    camera(cx, lerp(1.34, 1.40, eio(t / d)), 540, 1240, r, ox, oy)
    from episodes.japan_johatsu.shots import apt_bg
    apt_bg(cx, T)
    S.low_table(cx, 540, 1420)
    S.papers(cx, 650, 1470, 2)
    S.tea_cup(cx, 770, 1475, T, steam=1.0)


HOOK_SHOTS = [
    (0.00, 0.80, shot_count, 0),
    (0.80, 1.25, shot_slide, 0),
    (1.25, 1.70, shot_take, 0),
    (1.70, 2.80, shot_corridor, 0),
    (2.80, 3.34, shot_empty, 0.10),
]

"""Day 1 (remastered) - sets, props, lighting and the infected rig.

Portrait frame 1080x1920. Cold overcast morning: midnight blue / charcoal /
desaturated green / cold gray / muted brown. Everything is vector (Cairo),
lit with flat tints + rim light so characters sit inside the environment.
"""
import math
import random

import cairo

from cinecode.characters import (D2R, HERO, Figure, Pose, Style, hero_pose)
from cinecode.core import (OUTLINE, circle, clamp, ellipse, fs, hexc, line, mix, noise1,
                           poly, rgrad, rrect, shade, smooth, smooth_poly, src, vgrad)

FW, FH = 1080, 1920

# ---------------------------------------------------------------- palette
MIDNIGHT = hexc("#172334")
CHARCOAL = hexc("#171C22")
DGREEN = hexc("#35463E")
CGRAY = hexc("#71818B")
MBROWN = hexc("#574A42")
FOG = hexc("#8E9AA0")
SKY_TOP = hexc("#56636C")
SKY_LOW = hexc("#8C989D")
AMBER = hexc("#D9A55B")
SOFT_WHITE = hexc("#E9ECEA")
INK = hexc("#0E1116")

# light colours used on characters
TINT_DAY = hexc("#2A3A4C")       # exterior cold ambient
TINT_ROOM = hexc("#1B2533")      # dim interior
RIM_COLD = hexc("#C9D6DE")
RIM_WARM = hexc("#E8C894")


def paint_rect(cx, c, x=-600, y=-600, w=FW + 1200, h=FH + 1200):
    cx.rectangle(x, y, w, h)
    src(cx, c)
    cx.fill()


# ================================================================ lighting
def lit(cx, draw_fn, tint=TINT_DAY, amount=0.32, rim=RIM_COLD, rim_amt=0.35,
        rim_dir=1, box=None, shadow=0.25):
    """Draw something (draw_fn(cx)) and grade it inside its own alpha:
    an ambient tint, a shadow side and a soft rim light on the lit side."""
    cx.push_group()
    draw_fn(cx)
    cx.set_operator(cairo.OPERATOR_ATOP)
    src(cx, tint, amount)
    cx.paint()
    if box:
        x0, y0, x1, y1 = box
        g = cairo.LinearGradient(x0, 0, x1, 0)
        if rim_dir < 0:
            g = cairo.LinearGradient(x1, 0, x0, 0)
        g.add_color_stop_rgba(0.0, 0.03, 0.05, 0.08, shadow)
        g.add_color_stop_rgba(0.55, 0, 0, 0, 0)
        g.add_color_stop_rgba(0.82, rim[0], rim[1], rim[2], 0)
        g.add_color_stop_rgba(1.0, rim[0], rim[1], rim[2], rim_amt)
        cx.set_source(g)
        cx.paint()
    cx.set_operator(cairo.OPERATOR_OVER)
    cx.pop_group_to_source()
    cx.paint()


def draw_hero(cx, pose, tint=TINT_ROOM, amount=0.3, rim=RIM_COLD, rim_amt=0.4, rim_dir=1):
    s = pose.s
    box = (pose.x - 80 * s, 0, pose.x + 80 * s, 0)
    lit(cx, lambda c: HERO.draw(c, pose), tint, amount, rim, rim_amt, rim_dir, box)


# ================================================================ atmosphere
def sky(cx, t, horizon, top=SKY_TOP, low=SKY_LOW, drift=8.0, seed=0, y0=0):
    cx.rectangle(-600, y0 - 600, FW + 1200, horizon - y0 + 604)
    cx.set_source(vgrad(cx, 0, y0, 0, horizon, [(0, top), (1, low)]))
    cx.fill()
    rnd = random.Random(seed)
    # layered overcast cloud bands
    for k in range(9):
        yy = y0 + (horizon - y0) * (0.08 + 0.1 * k) + rnd.uniform(-20, 20)
        w = rnd.uniform(500, 900)
        x = (rnd.uniform(-300, FW) + t * drift * (0.6 + 0.15 * k)) % (FW + w) - w * 0.5
        c = mix(top, low, 0.25 + 0.08 * k)
        c = shade(c, rnd.uniform(-0.12, 0.05))
        ellipse(cx, x, yy, w * 0.6, rnd.uniform(26, 60))
        src(cx, c, 0.55)
        cx.fill()
    # pale sun disc diffused behind clouds
    cx.set_source(rgrad(cx, FW * 0.72, y0 + (horizon - y0) * 0.35, 0, 420,
                        [(0, hexc("#C9CFC9", 0.32)), (1, hexc("#C9CFC9", 0.0))]))
    cx.paint()


def tree_line(cx, horizon, color=hexc("#2E3B3A"), seed=3, h=60, t=0.0):
    rnd = random.Random(seed)
    cx.move_to(-20, horizon + 8)
    x = -20
    while x < FW + 40:
        bw = rnd.uniform(26, 70)
        bh = rnd.uniform(0.4, 1.0) * h
        cx.curve_to(x + bw * 0.1, horizon - bh, x + bw * 0.9, horizon - bh, x + bw, horizon - bh * 0.3)
        x += bw
    cx.line_to(FW + 40, horizon + 8)
    cx.close_path()
    src(cx, color)
    cx.fill()


def fog_layer(cx, t, y, height, alpha=0.35, speed=14, seed=1, color=FOG, count=7):
    rnd = random.Random(seed)
    for k in range(count):
        w = rnd.uniform(380, 760)
        x = (rnd.uniform(0, FW + w) + t * speed * rnd.uniform(0.6, 1.4)) % (FW + 2 * w) - w
        yy = y + rnd.uniform(-height * 0.4, height * 0.4) + math.sin(t * 0.3 + k) * 6
        cx.save()
        cx.translate(x, yy)
        cx.scale(w, height)
        cx.set_source(rgrad(cx, 0, 0, 0, 1, [(0, (*color[:3], alpha)), (1, (*color[:3], 0))]))
        cx.arc(0, 0, 1, 0, 2 * math.pi)
        cx.fill()
        cx.restore()


def ground_fog(cx, t, y, alpha=0.4):
    g = vgrad(cx, 0, y - 160, 0, y + 120, [(0, (*FOG[:3], 0)), (0.6, (*FOG[:3], alpha)), (1, (*FOG[:3], 0))])
    cx.rectangle(0, y - 160, FW, 280)
    cx.set_source(g)
    cx.fill()
    fog_layer(cx, t, y, 70, alpha * 0.8, seed=7)


def grass_tufts(cx, t, y0, y1, n=40, seed=5, color=hexc("#2C3A33"), wind=1.0, scale=1.0):
    rnd = random.Random(seed)
    for k in range(n):
        x = rnd.uniform(-20, FW + 20)
        y = rnd.uniform(y0, y1)
        sz = (0.6 + (y - y0) / max(1, (y1 - y0)) * 0.9) * scale
        sway = (math.sin(t * 1.7 + x * 0.01) * 0.6 + noise1(t * 0.8 + k, 9) * 0.5) * wind
        for b in range(5):
            bx = x + (b - 2) * 5 * sz
            hh = rnd.uniform(18, 34) * sz
            tip = (bx + sway * 10 * sz + (b - 2) * 3 * sz, y - hh)
            cx.move_to(bx - 2.5 * sz, y)
            cx.curve_to(bx + sway * 4 * sz, y - hh * 0.5, bx + sway * 4 * sz, y - hh * 0.5, *tip)
            cx.curve_to(bx + sway * 4 * sz + 2, y - hh * 0.5, bx + sway * 4 * sz + 2, y - hh * 0.5, bx + 2.5 * sz, y)
            cx.close_path()
        src(cx, shade(color, rnd.uniform(-0.2, 0.1)))
        cx.fill()


def vignette(cx, strength=0.55, color=CHARCOAL):
    g = cairo.RadialGradient(FW / 2, FH * 0.48, FH * 0.25, FW / 2, FH * 0.5, FH * 0.78)
    g.add_color_stop_rgba(0, color[0], color[1], color[2], 0)
    g.add_color_stop_rgba(1, color[0], color[1], color[2], strength)
    cx.set_source(g)
    cx.paint()


def light_shaft(cx, pts, alpha=0.12, color=hexc("#B9C6CC"), t=0.0):
    a = alpha * (0.85 + 0.15 * noise1(t * 0.5, 4))
    poly(cx, pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    g = vgrad(cx, 0, min(ys), 0, max(ys), [(0, (*color[:3], a)), (1, (*color[:3], 0))])
    cx.set_source(g)
    cx.fill()


def dust(cx, t, box, n=24, seed=2, alpha=0.35):
    x0, y0, x1, y1 = box
    rnd = random.Random(seed)
    for k in range(n):
        x = x0 + (rnd.uniform(0, 1) * (x1 - x0) + t * rnd.uniform(-6, 6) + noise1(t * 0.3 + k, 3) * 30) % (x1 - x0)
        y = y0 + (rnd.uniform(0, 1) * (y1 - y0) - t * rnd.uniform(2, 9)) % (y1 - y0)
        circle(cx, x, y, rnd.uniform(1.2, 2.6))
        src(cx, hexc("#D6DDE0", alpha * rnd.uniform(0.3, 1)))
        cx.fill()


# ================================================================ exterior props
def barn(cx, x, y, s=1.0, col=hexc("#5B3F3A")):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    w, h = 300, 190
    poly(cx, [(-w / 2, 0), (-w / 2, -h), (-w / 2 - 14, -h), (0, -h - 120), (w / 2 + 14, -h), (w / 2, -h), (w / 2, 0)])
    fs(cx, col, INK, 4)
    for k in range(-6, 7):
        line(cx, [(k * 22, -h + 4 + abs(k) * 0), (k * 22, -4)], shade(col, -0.25), 2.5)
    poly(cx, [(-w / 2 - 18, -h + 4), (0, -h - 124), (w / 2 + 18, -h + 4), (w / 2 + 6, -h + 4), (0, -h - 106), (-w / 2 - 6, -h + 4)])
    fs(cx, hexc("#2E2B2C"), INK, 3)
    rrect(cx, -55, -130, 110, 130, 2)
    fs(cx, shade(col, -0.3), INK, 4)
    line(cx, [(-55, -130), (55, 0)], hexc("#8D8578"), 5)
    line(cx, [(55, -130), (-55, 0)], hexc("#8D8578"), 5)
    rrect(cx, -22, -h - 60, 44, 40, 2)
    fs(cx, CHARCOAL, INK, 3)
    cx.restore()


def utility_pole(cx, x, y, h=520, s=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, -8, -h, 16, h, 3)
    fs(cx, hexc("#3B342F"), INK, 3)
    rrect(cx, -70, -h + 40, 140, 12, 3)
    fs(cx, hexc("#3B342F"), INK, 3)
    for dx in (-60, 0, 60):
        rrect(cx, dx - 5, -h + 26, 10, 16, 3)
        fs(cx, hexc("#6E7A7C"), INK, 2)
    # transformer can
    rrect(cx, 10, -h + 80, 34, 60, 8)
    fs(cx, hexc("#59646A"), INK, 3)
    cx.restore()


def wires(cx, pts_a, pts_b, t, sag=40, sway=1.0, color=hexc("#1A1F24")):
    for (ax, ay), (bx, by) in zip(pts_a, pts_b):
        w = math.sin(t * 1.3 + ax * 0.01) * 4 * sway
        cx.move_to(ax, ay)
        cx.curve_to(ax + (bx - ax) * 0.33, ay + sag + w, ax + (bx - ax) * 0.66, by + sag + w, bx, by)
        src(cx, color)
        cx.set_line_width(2.2)
        cx.stroke()


def fence(cx, y, t, x0=-40, x1=FW + 40, gap=150, h=110, s=1.0, col=hexc("#4A4038"), skip=None):
    xs = []
    x = x0
    while x <= x1:
        xs.append(x)
        x += gap * s
    for i, x in enumerate(xs):
        if skip and skip[0] <= x <= skip[1]:
            continue
        rrect(cx, x - 8 * s, y - h * s, 16 * s, h * s + 6, 3)
        fs(cx, col, INK, 3)
    for k, hy in enumerate((0.75, 0.35)):
        segs = [(xs[i], xs[i + 1]) for i in range(len(xs) - 1)]
        for a, b in segs:
            if skip and (skip[0] <= a <= skip[1] or skip[0] <= b <= skip[1]):
                continue
            rrect(cx, a, y - h * s * hy - 7 * s, b - a, 14 * s, 3)
            fs(cx, shade(col, 0.05), INK, 3)


def gate(cx, x, y, ang, s=1.0, col=hexc("#5A4C42")):
    """Farm gate hinged at x; ang 0 = closed (extends right), swings toward viewer (scale x)."""
    k = math.cos(ang)
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, -12, -150, 24, 156, 3)
    fs(cx, hexc("#3E352F"), INK, 3)
    L = 260 * k
    for hy in (-130, -90, -50, -14):
        poly(cx, [(0, hy - 7), (L, hy - 7 + math.sin(ang) * 18), (L, hy + 7 + math.sin(ang) * 18), (0, hy + 7)])
        fs(cx, col, INK, 3)
    line(cx, [(4, -14), (L - 6, -130 + math.sin(ang) * 18)], shade(col, -0.2), 9)
    rrect(cx, L - 8, -140 + math.sin(ang) * 18, 14, 140, 3)
    fs(cx, col, INK, 3)
    cx.restore()


def car(cx, x, y, s, t, door=0.0, hazard=True, col=hexc("#5E6870")):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # shadow
    ellipse(cx, 0, 4, 250, 16)
    src(cx, INK, 0.45)
    cx.fill()
    # body
    cx.move_to(-230, -30)
    cx.curve_to(-232, -70, -220, -86, -180, -92)
    cx.line_to(-120, -96)
    cx.curve_to(-90, -150, -60, -158, 0, -158)
    cx.line_to(60, -158)
    cx.curve_to(110, -156, 130, -120, 150, -98)
    cx.line_to(210, -88)
    cx.curve_to(236, -82, 240, -60, 238, -30)
    cx.line_to(230, -20)
    cx.line_to(-224, -20)
    cx.close_path()
    fs(cx, col, INK, 4)
    # windows
    poly(cx, [(-100, -100), (-70, -146), (-10, -148), (-10, -100)])
    fs(cx, hexc("#2C3943"), INK, 3)
    poly(cx, [(4, -100), (4, -148), (58, -148), (92, -140), (126, -100)])
    fs(cx, hexc("#2C3943"), INK, 3)
    line(cx, [(-60, -142), (-30, -108)], hexc("#7E8E98", 0.5), 4)
    # doors seam
    line(cx, [(-4, -98), (-4, -24)], shade(col, -0.35), 3)
    line(cx, [(128, -96), (128, -24)], shade(col, -0.35), 3)
    # wheels
    for wx in (-150, 150):
        circle(cx, wx, -20, 42)
        fs(cx, hexc("#16191C"), INK, 4)
        circle(cx, wx, -20, 20)
        fs(cx, hexc("#5B6268"), INK, 3)
    # hazard / tail light blinking amber
    on = hazard and (int(t * 1.6) % 2 == 0)
    rrect(cx, 222, -78, 16, 22, 4)
    fs(cx, hexc("#F0B252") if on else hexc("#6B4A2C"), INK, 2.5)
    if on:
        cx.set_source(rgrad(cx, 232, -66, 0, 70, [(0, hexc("#F0B252", 0.45)), (1, hexc("#F0B252", 0))]))
        cx.arc(232, -66, 70, 0, 2 * math.pi)
        cx.fill()
    # open driver door (swung toward viewer)
    if door > 0:
        dx = -4
        w = 104 * (1 - 0.45 * door)
        poly(cx, [(dx, -100 - 10 * door), (dx - w, -100 + 6 * door), (dx - w, -24 + 20 * door), (dx, -24)])
        fs(cx, shade(col, -0.12), INK, 4)
        poly(cx, [(dx - 8, -96 - 8 * door), (dx - w + 8, -96 + 6 * door), (dx - w + 6, -60 + 10 * door), (dx - 8, -60)])
        fs(cx, hexc("#28333C"), INK, 2.5)
    cx.restore()


def farmhouse_ext(cx, x, y, s=1.0, t=0.0, lit_win=0.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    wall = hexc("#7D8285")
    w, h = 420, 250
    rrect(cx, -w / 2, -h, w, h, 2)
    fs(cx, wall, INK, 4)
    for k in range(1, 12):
        line(cx, [(-w / 2 + 2, -h + k * 21), (w / 2 - 2, -h + k * 21)], shade(wall, -0.18), 2)
    poly(cx, [(-w / 2 - 30, -h + 4), (0, -h - 150), (w / 2 + 30, -h + 4)])
    fs(cx, hexc("#2F3337"), INK, 4)
    rrect(cx, 110, -h - 120, 30, 70, 2)
    fs(cx, MBROWN, INK, 3)
    for wx in (-130, 0, 130):
        if wx == 0:
            rrect(cx, -32, -150, 64, 150, 2)
            fs(cx, hexc("#3B3128"), INK, 4)
            continue
        rrect(cx, wx - 40, -190, 80, 100, 2)
        fs(cx, mix(hexc("#2B3640"), hexc("#E2B676"), lit_win * 0.6), INK, 4)
        line(cx, [(wx, -190), (wx, -90)], INK, 3)
        line(cx, [(wx - 40, -140), (wx + 40, -140)], INK, 3)
    # porch roof
    poly(cx, [(-w / 2 - 20, -170), (w / 2 + 20, -170), (w / 2 + 6, -200), (-w / 2 - 6, -200)])
    fs(cx, hexc("#3A3E42"), INK, 3)
    for px in (-w / 2 - 6, -70, 70, w / 2 + 6):
        rrect(cx, px - 5, -170, 10, 170, 2)
        fs(cx, hexc("#9EA2A2"), INK, 2.5)
    rrect(cx, -w / 2 - 30, -8, w + 60, 14, 2)
    fs(cx, hexc("#4A4038"), INK, 3)
    cx.restore()


def well_and_pump(cx, x, y, s=1.0, t=0.0, power=1.0, show_house=True):
    """Modern private well: casing + cap, buried line, small pump house with pressure tank,
    and the electric service line coming in."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    if show_house:
        # pump house
        poly(cx, [(40, 0), (40, -150), (110, -205), (180, -150), (180, 0)])
        fs(cx, hexc("#6A6560"), INK, 4)
        for k in range(1, 7):
            line(cx, [(42, -k * 22), (178, -k * 22)], hexc("#56514C"), 2)
        poly(cx, [(28, -146), (110, -214), (192, -146), (180, -140), (110, -198), (40, -140)])
        fs(cx, hexc("#33363A"), INK, 3)
        rrect(cx, 82, -110, 56, 110, 2)
        fs(cx, hexc("#3E3530"), INK, 3)
        # electric meter / disconnect box with status lamp
        rrect(cx, 150, -126, 22, 34, 3)
        fs(cx, hexc("#8C9496"), INK, 2.5)
        lamp = mix(hexc("#3A2E22"), hexc("#F2B65A"), power)
        circle(cx, 161, -114, 5)
        fs(cx, lamp, INK, 1.5)
        if power > 0.05:
            cx.set_source(rgrad(cx, 161, -114, 0, 26, [(0, hexc("#F2B65A", 0.5 * power)), (1, hexc("#F2B65A", 0))]))
            cx.arc(161, -114, 26, 0, 2 * math.pi)
            cx.fill()
        # conduit to roof (service line)
        line(cx, [(166, -126), (166, -170)], hexc("#2A2E31"), 5)
    # pipe from casing to house
    line(cx, [(0, -8), (40, -8)], hexc("#3A4045"), 7)
    # well casing + cap
    rrect(cx, -22, -70, 44, 70, 3)
    fs(cx, hexc("#7C8589"), INK, 4)
    rrect(cx, -30, -84, 60, 18, 6)
    fs(cx, hexc("#5C6569"), INK, 4)
    line(cx, [(-14, -70), (-14, -4)], hexc("#A3ABAE", 0.6), 3)
    cx.restore()


def rooster(cx, x, y, s, t, crow=0.0, head_turn=0.0, f=1):
    """A plain farm rooster, side view. crow 0..1 = neck stretch + open beak."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s * f, s)
    bob = math.sin(t * 2.2) * 2 * (1 - crow)
    # legs
    line(cx, [(-6, -40), (-10, 0)], hexc("#B08A3E"), 5)
    line(cx, [(10, -40), (8, 0)], hexc("#B08A3E"), 5)
    for fx in (-10, 8):
        line(cx, [(fx - 12, 1), (fx + 12, 1)], hexc("#B08A3E"), 4)
    # tail (dark, glossy green-black)
    for k, (dx, dy) in enumerate([(-95, -150), (-110, -120), (-104, -88), (-90, -66)]):
        cx.move_to(-40, -70)
        cx.curve_to(-60, -110 - k * 6, dx - 10, dy - 20, dx, dy)
        cx.curve_to(dx + 18, dy + 10, -50, -60, -30, -50)
        cx.close_path()
        src(cx, shade(hexc("#1F2A2A"), 0.05 * k))
        cx.fill_preserve()
        src(cx, INK)
        cx.set_line_width(2.5)
        cx.stroke()
    # body
    ellipse(cx, 0, -66 + bob, 52, 36, -0.15)
    fs(cx, hexc("#6E4630"), INK, 3.5)
    # wing
    cx.move_to(-30, -76 + bob)
    cx.curve_to(0, -92 + bob, 34, -74 + bob, 22, -52 + bob)
    cx.curve_to(0, -44 + bob, -24, -56 + bob, -30, -76 + bob)
    fs(cx, hexc("#4C3123"), INK, 3)
    # neck + head
    nx, ny = 34, -86 + bob
    hx = 52 + 10 * crow + head_turn * 4
    hy = -128 + bob - 26 * crow
    cx.move_to(nx - 20, ny + 8)
    cx.curve_to(nx - 10, ny - 30, hx - 16, hy + 10, hx - 10, hy)
    cx.line_to(hx + 12, hy + 4)
    cx.curve_to(hx + 10, hy + 26, nx + 24, ny - 6, nx + 20, ny + 10)
    cx.close_path()
    fs(cx, hexc("#9A6234"), INK, 3)
    ellipse(cx, hx, hy, 16, 14)
    fs(cx, hexc("#9A6234"), INK, 3)
    # comb + wattle (muted red)
    for k in range(4):
        circle(cx, hx - 10 + k * 7, hy - 14 - (k % 2) * 3, 6)
    fs(cx, hexc("#8E2F2A"), None, 0)
    ellipse(cx, hx + 8, hy + 18, 5, 9)
    fs(cx, hexc("#8E2F2A"), None, 0)
    # beak (opens when crowing)
    ob = 7 * crow
    poly(cx, [(hx + 12, hy - 4), (hx + 30, hy - 2 - ob * 0.4), (hx + 12, hy + 2)])
    fs(cx, hexc("#C99A45"), INK, 2)
    poly(cx, [(hx + 12, hy + 3), (hx + 27, hy + 4 + ob), (hx + 12, hy + 7)])
    fs(cx, hexc("#C99A45"), INK, 2)
    circle(cx, hx + 4, hy - 3, 2.6)
    fs(cx, INK, None, 0)
    cx.restore()


# ================================================================ interior
WALL = hexc("#2A3440")
WALL_DK = hexc("#202832")
WAINSCOT = hexc("#3A322D")
FLOOR = hexc("#2A241F")


def room_wall(cx, y_floor, t=0.0, x0=-400, x1=FW + 400, top=-400):
    cx.rectangle(x0, top, x1 - x0, y_floor - top)
    cx.set_source(vgrad(cx, 0, top, 0, y_floor, [(0, WALL_DK), (1, WALL)]))
    cx.fill()
    for k in range(int(x0) - 40, int(x1) + 40, 46):
        line(cx, [(k, top), (k, y_floor - 260)], hexc("#24303A"), 3)
    rrect(cx, x0 - 10, y_floor - 260, x1 - x0 + 20, 260, 0)
    src(cx, WAINSCOT)
    cx.fill()
    for k in range(int(x0) - 40, int(x1) + 40, 90):
        line(cx, [(k, y_floor - 240), (k, y_floor - 10)], shade(WAINSCOT, -0.25), 3)
    rrect(cx, x0 - 10, y_floor - 272, x1 - x0 + 20, 18, 0)
    src(cx, shade(WAINSCOT, 0.1))
    cx.fill()
    # floor
    cx.rectangle(x0, y_floor, x1 - x0, FH * 2)
    cx.set_source(vgrad(cx, 0, y_floor, 0, y_floor + 700, [(0, FLOOR), (1, shade(FLOOR, -0.4))]))
    cx.fill()
    for k in range(1, 12):
        yy = y_floor + k * k * 7
        line(cx, [(x0, yy), (x1, yy)], shade(FLOOR, -0.3), 2)


def curtains(cx, x, y, w, h, t, open_amt=1.0, wind=1.0, col=hexc("#4E5A55"), seed=0):
    """Two panels on a rod. open_amt 1 = pulled to the sides, 0 = closed."""
    line(cx, [(x - 30, y - 14), (x + w + 30, y - 14)], hexc("#2A241F"), 8)
    for side in (-1, 1):
        cover = 0.18 + 0.32 * (1 - open_amt)  # fraction of width per panel
        pw = w * cover + 26
        x_edge = x - 20 if side < 0 else x + w + 20
        x_in = x_edge - side * pw
        pts_top = []
        cx.move_to(x_edge, y - 14)
        cx.line_to(x_in, y - 14)
        n = 10
        for i in range(1, n + 1):
            yy = y - 14 + (h + 60) * i / n
            sway = (math.sin(t * 1.6 + i * 0.5 + seed + side) * 6 + noise1(t * 0.9 + i * 0.3, seed + 3 + side) * 8) * wind * (i / n)
            cx.line_to(x_in + sway - side * 6 * math.sin(i * 1.3), yy)
        cx.line_to(x_edge, y + h + 46)
        cx.close_path()
        cx.set_source(vgrad(cx, 0, y, 0, y + h, [(0, shade(col, -0.1)), (1, shade(col, -0.35))]))
        cx.fill_preserve()
        src(cx, INK)
        cx.set_line_width(3)
        cx.stroke()
        for k in range(1, 4):
            fx = x_edge - side * pw * k / 4
            line(cx, [(fx, y - 8), (fx + math.sin(t + k) * 3 * wind, y + h + 40)], shade(col, -0.45), 2.5)


def window(cx, x, y, w, h, t, outside, open_amt=1.0, wind=1.0, curtain=True, glass=0.12,
           frame_col=hexc("#3B3530")):
    """outside(cx) draws the exterior in frame coords, clipped to the glass."""
    cx.save()
    rrect(cx, x, y, w, h, 2)
    cx.clip()
    outside(cx)
    # glass sheen
    g = cairo.LinearGradient(x, y, x + w, y + h)
    g.add_color_stop_rgba(0, 0.8, 0.86, 0.9, glass)
    g.add_color_stop_rgba(0.5, 0.8, 0.86, 0.9, 0)
    g.add_color_stop_rgba(1, 0.8, 0.86, 0.9, glass * 0.6)
    cx.set_source(g)
    cx.paint()
    cx.restore()
    rrect(cx, x - 16, y - 16, w + 32, h + 32, 3)
    rrect(cx, x, y, w, h, 2)
    cx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fs(cx, frame_col, INK, 4)
    cx.set_fill_rule(cairo.FILL_RULE_WINDING)
    line(cx, [(x + w / 2, y), (x + w / 2, y + h)], frame_col, 12)
    line(cx, [(x, y + h / 2), (x + w, y + h / 2)], frame_col, 12)
    rrect(cx, x - 30, y + h + 12, w + 60, 20, 3)
    fs(cx, shade(frame_col, 0.08), INK, 3)
    if curtain:
        curtains(cx, x, y, w, h, t, open_amt, wind)


def ceiling_lamp(cx, x, y, on=1.0, sway=0.0, t=0.0, cord=200):
    a = math.sin(t * 0.9) * 0.02 * sway
    cx.save()
    cx.translate(x, y - cord)
    cx.rotate(a)
    line(cx, [(0, 0), (0, cord)], INK, 3)
    cx.translate(0, cord)
    if on > 0.01:
        cx.set_source(rgrad(cx, 0, 30, 0, 520, [(0, hexc("#E9C890", 0.35 * on)), (1, hexc("#E9C890", 0))]))
        cx.arc(0, 30, 520, 0, 2 * math.pi)
        cx.fill()
    circle(cx, 0, 30, 16)
    fs(cx, mix(hexc("#4B4A44"), hexc("#FFE6B0"), on), INK, 2)
    poly(cx, [(-16, 0), (16, 0), (54, 34), (-54, 34)])
    fs(cx, hexc("#3E4A48"), INK, 3)
    cx.restore()


def room_light(cx, on):
    """Warm bulb light washing the room (additive-ish)."""
    if on <= 0.01:
        return
    cx.set_source(rgrad(cx, FW / 2, FH * 0.3, 0, FH * 0.8, [(0, hexc("#C9A472", 0.16 * on)), (1, hexc("#C9A472", 0))]))
    cx.paint()


def door(cx, x, y, w, h, t, ang=0.0, bolt=0.0, pane=None, knob_hand=None):
    """Front door seen straight on. bolt 0..1 = deadbolt thrown. pane(cx) draws outside view."""
    rrect(cx, x - 22, y - 22, w + 44, h + 22, 2)
    fs(cx, hexc("#2B2622"), INK, 4)
    rrect(cx, x, y, w, h, 2)
    fs(cx, hexc("#4A3A30"), INK, 4)
    # panels
    for (px, py, pw, ph) in [(0.12, 0.42, 0.33, 0.24), (0.55, 0.42, 0.33, 0.24), (0.12, 0.72, 0.33, 0.22), (0.55, 0.72, 0.33, 0.22)]:
        rrect(cx, x + w * px, y + h * py, w * pw, h * ph, 4)
        fs(cx, hexc("#433429"), shade(hexc("#433429"), -0.35), 3)
    # small glass pane at top
    gx, gy, gw, gh = x + w * 0.16, y + h * 0.07, w * 0.68, h * 0.26
    cx.save()
    rrect(cx, gx, gy, gw, gh, 3)
    cx.clip()
    if pane:
        pane(cx, (gx, gy, gw, gh))
    else:
        paint_rect(cx, hexc("#6E7C84"), gx, gy, gw, gh)
    cx.restore()
    rrect(cx, gx, gy, gw, gh, 3)
    fs(cx, None, INK, 5)
    line(cx, [(gx + gw / 2, gy), (gx + gw / 2, gy + gh)], hexc("#3A2E26"), 8)
    # knob + deadbolt
    kx, ky = x + w * 0.86, y + h * 0.56
    circle(cx, kx, ky, 15)
    fs(cx, hexc("#8C7A55"), INK, 3)
    bx, by = kx, y + h * 0.47
    circle(cx, bx, by, 13)
    fs(cx, hexc("#8C7A55"), INK, 3)
    cx.save()
    cx.translate(bx, by)
    cx.rotate(bolt * math.pi / 2)
    rrect(cx, -3, -11, 6, 22, 3)
    fs(cx, hexc("#3F3626"), None, 0)
    cx.restore()


def faucet(cx, x, y, s, handle=0.0, flow=0.0, t=0.0, drips=None):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    # sink
    rrect(cx, -260, 40, 520, 60, 8)
    fs(cx, hexc("#7E878B"), INK, 4)
    rrect(cx, -230, 52, 460, 20, 8)
    fs(cx, hexc("#3D4448"), INK, 3)
    # base + spout
    rrect(cx, -30, 0, 60, 44, 6)
    fs(cx, hexc("#9AA2A5"), INK, 4)
    cx.move_to(-12, 2)
    cx.curve_to(-12, -120, 120, -130, 128, -40)
    cx.line_to(104, -40)
    cx.curve_to(100, -102, 12, -96, 12, 2)
    cx.close_path()
    fs(cx, hexc("#A9B1B4"), INK, 4)
    line(cx, [(-4, -40), (30, -96)], hexc("#E2E8EA", 0.6), 4)
    # handle (lever) rotates
    cx.save()
    cx.translate(0, -2)
    cx.rotate(-handle * 0.9)
    rrect(cx, -8, -70, 16, 70, 6)
    fs(cx, hexc("#B4BBBE"), INK, 3)
    cx.restore()
    # water
    if flow > 0.01:
        rrect(cx, 108, -40, 14 * flow, 92, 5)
        src(cx, hexc("#A9C3CF", 0.75))
        cx.fill()
    if drips:
        for d in drips:  # list of fall progress 0..1
            if 0 <= d <= 1:
                yy = -38 + d * 90
                ellipse(cx, 116, yy, 4, 6)
                src(cx, hexc("#B9D0DA", 0.9))
                cx.fill()
    cx.restore()


def shelf_supplies(cx, x, y, w, s=1.0):
    """Pantry shelves: jars, cans, flour sacks, water jugs. Muted."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    rrect(cx, 0, 0, w, 560, 2)
    fs(cx, hexc("#2E2722"), INK, 4)
    rnd = random.Random(11)
    for row, yy in enumerate((150, 320, 500)):
        rrect(cx, -8, yy, w + 16, 14, 2)
        fs(cx, hexc("#4E4239"), INK, 3)
        xx = 18
        while xx < w - 50:
            kind = rnd.choice(["can", "can", "jar", "sack", "box"])
            if kind == "can":
                cw, ch = 46, 64
                rrect(cx, xx, yy - ch, cw, ch, 4)
                fs(cx, rnd.choice([hexc("#7A6A55"), hexc("#5E6B66"), hexc("#7C5A4A")]), INK, 3)
                rrect(cx, xx, yy - ch * 0.66, cw, ch * 0.34, 0)
                src(cx, hexc("#C2B9A6", 0.55))
                cx.fill()
            elif kind == "jar":
                cw, ch = 54, 86
                rrect(cx, xx, yy - ch, cw, ch, 10)
                fs(cx, hexc("#8C8A6C", 0.85), INK, 3)
                rrect(cx, xx + 4, yy - ch - 10, cw - 8, 14, 3)
                fs(cx, hexc("#6F6656"), INK, 2.5)
            elif kind == "sack":
                cw, ch = 86, 112
                cx.move_to(xx, yy)
                cx.curve_to(xx - 4, yy - ch * 0.6, xx + 6, yy - ch, xx + 20, yy - ch)
                cx.line_to(xx + cw - 20, yy - ch)
                cx.curve_to(xx + cw - 6, yy - ch, xx + cw + 4, yy - ch * 0.6, xx + cw, yy)
                cx.close_path()
                fs(cx, hexc("#8E836E"), INK, 3)
            else:
                cw, ch = 70, 90
                rrect(cx, xx, yy - ch, cw, ch, 2)
                fs(cx, hexc("#6B5B48"), INK, 3)
            xx += cw + rnd.uniform(6, 16)
    cx.restore()


# ================================================================ the infected
class InfectedStyle(Style):
    """Pale, desaturated, torn clothes. Same rig as the hero so the series reads as one world."""
    limb = hexc("#272B2E")
    limb_w = 8.5
    shoe = hexc("#1F2224")

    def __init__(self, seed=0, shirt=None, skin=None, pants=None):
        rnd = random.Random(seed)
        self.seed = seed
        self.skin = skin or rnd.choice([hexc("#A9B0A7"), hexc("#9EA79F"), hexc("#B2B4AA"), hexc("#A2A9A6")])
        self.shirt = shirt or rnd.choice([hexc("#5B6670"), hexc("#6A5A4C"), hexc("#4F5A4D"), hexc("#6E6A63"), hexc("#55505A")])
        self.rnd_tears = [(rnd.uniform(-30, 30), rnd.uniform(-90, -20), rnd.uniform(6, 12)) for _ in range(3)]
        self.hem = [rnd.uniform(4, 22) for _ in range(9)]

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 33
        cx.move_to(-hw, 8)
        cx.line_to(-hw + 2, -T + 18)
        cx.curve_to(-hw + 4, -T, -hw + 16, -T - 2, -hw + 24, -T - 2)
        cx.line_to(hw - 24, -T - 2)
        cx.curve_to(hw - 16, -T - 2, hw - 4, -T, hw - 2, -T + 18)
        cx.line_to(hw, 8)
        # ragged hem
        n = len(self.hem)
        for i in range(n):
            xx = hw - (2 * hw) * (i + 0.5) / n
            cx.line_to(xx, 8 + self.hem[i])
        cx.close_path()
        fs(cx, self.shirt, INK, 4.5)
        # tears showing pale skin + grime
        for (tx, ty, r) in self.rnd_tears:
            poly(cx, [(tx - r, ty), (tx, ty - r * 1.4), (tx + r * 0.8, ty + r * 0.3), (tx - r * 0.2, ty + r)])
            fs(cx, shade(self.skin, -0.15), INK, 2.5)
        ellipse(cx, -10, -40, 18, 10, 0.4)
        src(cx, hexc("#2F2A26", 0.35))
        cx.fill()
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.45, sy + (ey - sy) * 0.45
        line(cx, [(sx, sy), (mx, my)], INK, 24)
        line(cx, [(sx, sy), (mx, my)], self.shirt, 16)

    def draw_head_front(self, cx, fig, J, p):
        # redraw head as slightly irregular pale shape with sunken eyes (no cartoon features)
        R = self.head_r
        hx, hy = J["head"]
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        smooth_poly(cx, [(R * math.cos(a) * (1.0 + 0.04 * math.sin(a * 3 + self.seed)),
                          R * math.sin(a) * (1.06 + 0.03 * math.cos(a * 2)))
                         for a in [k * 2 * math.pi / 14 for k in range(14)]])
        fs(cx, self.skin, INK, 4.5)
        # cold shadow under the brow + cheek hollows
        cx.save()
        circle(cx, 0, 0, R - 2)
        cx.clip()
        ellipse(cx, f * R * 0.2, -R * 0.02, R * 0.82, R * 0.3)
        src(cx, hexc("#3E4744", 0.32))
        cx.fill()
        ellipse(cx, -R * 0.5, R * 0.55, R * 0.7, R * 0.5)
        src(cx, hexc("#3E4744", 0.18))
        cx.fill()
        cx.restore()
        off = f * R * 0.24
        look = p.look
        for side in (-1, 1):
            ex = off + side * R * 0.32 * (0.9 if f else 1)
            ey = -R * 0.04 + (2 if side > 0 else -1)
            ellipse(cx, ex, ey, 12.5, 11 + (2 if side < 0 else 0))
            src(cx, hexc("#1A1D1F"))
            cx.fill()
            # dull pale pupil
            circle(cx, ex + look[0] * 4, ey + look[1] * 3, 3.4)
            src(cx, hexc("#C9CEC6", 0.85))
            cx.fill()
        # heavy flat brow line
        line(cx, [(off - R * 0.55, -R * 0.33), (off - R * 0.1, -R * 0.27)], hexc("#2A2E2C"), 4.5)
        line(cx, [(off + R * 0.12, -R * 0.29), (off + R * 0.56, -R * 0.36)], hexc("#2A2E2C"), 4.5)
        # slack, slightly open mouth (dark, no teeth)
        mo = p.mouth_open
        ellipse(cx, off * 1.1 + 3, R * 0.46, 11, 4 + 6 * mo, 0.08)
        src(cx, hexc("#1A1416"))
        cx.fill()
        # bruise / grime
        ellipse(cx, -off - R * 0.45, -R * 0.45, 9, 6, 0.6)
        src(cx, hexc("#5E6B63", 0.5))
        cx.fill()
        cx.restore()


def infected(seed, **kw):
    return Figure(InfectedStyle(seed=seed, **kw), seed=seed + 300)


def infected_pose(x, y, t, s=1.0, f=1, seed=0, speed=0.55, moving=1.0, head_turn=0.0, **kw):
    """Asymmetric shamble: one leg drags, torso pitched forward, irregular head jerks.
    moving 0..1 blends from walking to standing still."""
    ph = (t * speed + seed * 0.37) * 2 * math.pi
    s_ = math.sin(ph)
    c_ = math.cos(ph)
    m = moving
    hip_a = (-26 * s_) * m + 2
    hip_b = (14 * s_) * m - 4           # dragging leg: short stride
    knee_a = 10 + 34 * max(0, c_) * m
    knee_b = 4 + 8 * max(0, -c_) * m
    # hitch in the step when the bad leg plants
    hitch = max(0, math.sin(ph + 0.6)) ** 6 * 10 * m
    bob = (-abs(c_) * 4 + 3 + hitch) * m
    jerk = 0.0
    jp = (t * 0.7 + seed * 1.3) % 2.3
    if jp < 0.12:
        jerk = math.sin(jp / 0.12 * math.pi) * (12 if seed % 2 else -12)
    tilt = 10 + 6 * math.sin(t * 0.8 + seed) + jerk * (1 - abs(head_turn))
    p = Pose(x=x, y=y, s=s, f=f, t=t, blink=False, eyes="open", brows="none", mouth="flat",
             lean=12 + 3 * s_ * m + 4 * (1 - m), bob=bob,
             hip_a=hip_a, hip_b=hip_b, knee_a=knee_a, knee_b=knee_b,
             arm_a=24 + 8 * math.sin(ph + 1) * m, elb_a=30 + 6 * math.sin(ph),
             arm_b=-6 + 4 * math.sin(ph * 0.5) * m, elb_b=8,
             tilt=tilt, mouth_open=0.4 + 0.3 * math.sin(t * 1.3 + seed))
    p.view = "side" if abs(head_turn) < 0.5 else "front"
    p.look = (0.0, 0.0)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def draw_infected(cx, fig, pose, tint=TINT_DAY, amount=0.36, rim=RIM_COLD, rim_amt=0.3, rim_dir=1, fogged=0.0):
    s = pose.s
    box = (pose.x - 80 * s, 0, pose.x + 80 * s, 0)

    def d(c):
        fig.draw(c, pose)

    lit(cx, d, tint, amount, rim, rim_amt, rim_dir, box)
    if fogged > 0:
        # atmospheric perspective: distant figures fade into the fog
        cx.push_group()
        fig.draw(cx, pose)
        cx.set_operator(cairo.OPERATOR_ATOP)
        src(cx, FOG, fogged)
        cx.paint()
        cx.set_operator(cairo.OPERATOR_OVER)
        cx.pop_group_to_source()
        cx.paint()


def silhouette(cx, fig, pose, color=CHARCOAL, alpha=1.0):
    cx.push_group()
    fig.draw(cx, pose)
    cx.set_operator(cairo.OPERATOR_ATOP)
    src(cx, color)
    cx.paint()
    cx.set_operator(cairo.OPERATOR_OVER)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


# civilian runner (healthy person fleeing) - neutral gray jacket, white head like the hero's world
class CivilianStyle(Style):
    jacket = hexc("#6C7378")

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        rrect(cx, -32, -T, 64, T + 8, 18)
        fs(cx, self.jacket, INK, 4.5)
        line(cx, [(0, -T + 6), (0, 4)], shade(self.jacket, -0.3), 3)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        line(cx, [(sx, sy), (ex, ey)], INK, 24)
        line(cx, [(sx, sy), (ex, ey)], self.jacket, 16)


CIVILIAN = Figure(CivilianStyle(), seed=40)


# ================================================================ typography (series style)
FONT = "Montserrat ExtraBold"


def cairo_text(cx, s, x, y, size, col, align="center", outline=None, spacing=0.0):
    """Plain Montserrat text (used inside motion graphics). y = baseline."""
    cx.save()
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    ext = cx.text_extents(s)
    w = ext.x_advance + spacing * (len(s) - 1)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    cx.new_path()
    xx = x
    for ch in s:
        cx.move_to(xx, y)
        cx.text_path(ch)
        xx += cx.text_extents(ch).x_advance + spacing
    if outline:
        src(cx, outline)
        cx.set_line_width(size * 0.14)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke_preserve()
    src(cx, col)
    cx.fill()
    cx.restore()


def title(cx, s, x, y, size, a=1.0):
    """Soft-white bold title, subtle dark outline + soft shadow."""
    for k, al in ((10, 0.18), (5, 0.25)):
        cairo_text(cx, s, x, y + k * 0.6, size, (0, 0, 0, al * a), spacing=size * 0.06,
                   outline=(0, 0, 0, al * a))
    cairo_text(cx, s, x, y, size, (*SOFT_WHITE[:3], a), spacing=size * 0.06,
               outline=(*INK[:3], 0.85 * a))


def accent(cx, s, t, t0, t1, kind="accent"):
    """Short cinematic accent: fade + 8px settle in, fade out. Amber rule lines."""
    if t < t0 or t > t1 + 0.25:
        return
    a = min(smooth(clamp((t - t0) / 0.3)), 1 - clamp((t - t1) / 0.25))
    rise = 8 * (1 - smooth(clamp((t - t0) / 0.3)))
    if kind == "tag":
        y = 200 + rise
        cairo_text(cx, s, FW / 2, y, 50, (*SOFT_WHITE[:3], a), spacing=10, outline=(*INK[:3], 0.8 * a))
        line(cx, [(FW / 2 - 150, y - 18), (FW / 2 - 98, y - 18)], (*AMBER[:3], a), 3)
        line(cx, [(FW / 2 + 98, y - 18), (FW / 2 + 150, y - 18)], (*AMBER[:3], a), 3)
    else:
        y = 300 + rise
        cairo_text(cx, s, FW / 2, y, 66, (*SOFT_WHITE[:3], a), spacing=6, outline=(*INK[:3], 0.85 * a))
        line(cx, [(FW / 2 - 60, y + 26), (FW / 2 + 60, y + 26)], (*AMBER[:3], a), 4)

"""Dark, cinematic sets for Day 2 (rebuilt). Palette: charcoal #171C22, midnight #172334,
forest #35463E, cold grey #71818B, rust #7D3735; pale overcast light, dim warm windows, thin fog."""
import math
import random

import cairo
import numpy as np

from cinecode.core import ellipse, fs, hexc, line, rrect, shade, src
from episodes.zombie_day_2_rebuilt.draw import H, INK, W

CHAR = hexc("#171c22")
MID = hexc("#172334")
FOREST = hexc("#35463e")
COLD = hexc("#71818b")
RUST = hexc("#7d3735")
WARM = hexc("#c89a5a")
MUTED_WHITE = hexc("#e3e1da")
AMBER = hexc("#c8923a")

GROUND_Y = 1120          # horizon / back of the yard in exterior world coords
WORLD_W = 2900
CX0 = 1400               # parallax reference x


# ------------------------------------------------------------ post: grade, fog, grain, vignette
def grade(cx, tint, k=1.0):
    cx.save()
    cx.set_operator(cairo.OPERATOR_MULTIPLY)
    src(cx, tuple(1 - (1 - c) * k for c in tint[:3]) + (1,))
    cx.paint()
    cx.restore()


def vignette(cx, k=0.55):
    g = cairo.RadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.5, H * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, k)
    cx.set_source(g)
    cx.paint()


_GRAIN = None


def grain(cx, t, k=0.06):
    global _GRAIN
    if _GRAIN is None:
        r = np.random.default_rng(3)
        n = (r.random((H // 2, W // 2)) * 255).astype(np.uint8)
        a = np.zeros((H // 2, W // 2, 4), dtype=np.uint8)
        a[..., 0] = a[..., 1] = a[..., 2] = n
        a[..., 3] = 255
        _GRAIN = cairo.ImageSurface.create_for_data(memoryview(a.copy()), cairo.FORMAT_ARGB32, W // 2, H // 2)
    f = int(t * 30)
    rr = random.Random(f)
    cx.save()
    cx.set_operator(cairo.OPERATOR_OVERLAY)
    cx.scale(2, 2)
    p = cairo.SurfacePattern(_GRAIN)
    p.set_extend(cairo.EXTEND_REPEAT)
    m = cairo.Matrix()
    m.translate(rr.uniform(0, 500), rr.uniform(0, 900))
    p.set_matrix(m)
    cx.set_source(p)
    cx.paint_with_alpha(k)
    cx.restore()


def fog(cx, t, y0, y1, k=0.16, speed=14, seed=1, color=(0.62, 0.68, 0.72), x0=-200, x1=None):
    x1 = W + 200 if x1 is None else x1
    r = random.Random(seed)
    span = x1 - x0
    for i in range(9):
        y = r.uniform(y0, y1)
        rx = r.uniform(260, 520)
        ry = r.uniform(40, 110)
        x = x0 + (r.uniform(0, span) + t * speed * r.uniform(0.6, 1.4)) % (span + 2 * rx) - rx
        g = cairo.RadialGradient(x, y, 0, x, y, rx)
        g.add_color_stop_rgba(0, *color, k)
        g.add_color_stop_rgba(1, *color, 0)
        cx.save()
        cx.translate(x, y)
        cx.scale(1, ry / rx)
        cx.translate(-x, -y)
        cx.set_source(g)
        cx.arc(x, y, rx, 0, 2 * math.pi)
        cx.fill()
        cx.restore()


# ------------------------------------------------------------ exterior world
def layer(cx, cam, pf, zoom_pf=1.0):
    cx.translate(W / 2, H / 2)
    z = 1 + (cam[2] - 1) * zoom_pf
    cx.scale(z, z)
    cx.translate(-(cam[0] * pf + CX0 * (1 - pf)), -cam[1])


def sky(cx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *hexc("#0f151d"))
    g.add_color_stop_rgba(0.45, *hexc("#1d2a38"))
    g.add_color_stop_rgba(0.62, *hexc("#3d4a55"))
    g.add_color_stop_rgba(1, *hexc("#2a3238"))
    cx.set_source(g)
    cx.paint()
    # pale overcast light behind clouds
    g = cairo.RadialGradient(W * 0.68, H * 0.3, 10, W * 0.68, H * 0.3, 700)
    g.add_color_stop_rgba(0, 0.75, 0.8, 0.85, 0.22)
    g.add_color_stop_rgba(1, 0.75, 0.8, 0.85, 0)
    cx.set_source(g)
    cx.paint()
    r = random.Random(2)
    for k in range(10):
        x = (r.uniform(-300, W + 300) + t * r.uniform(4, 10)) % (W + 600) - 300
        y = r.uniform(150, 900)
        ellipse(cx, x, y, r.uniform(250, 500), r.uniform(30, 70))
        src(cx, (0.08, 0.1, 0.13, 0.35))
        cx.fill()


def treeline(cx, y, h, col, seed, x0=-800, x1=WORLD_W + 800, t=0.0):
    r = random.Random(seed)
    x = x0
    cx.move_to(x0, y + 400)
    while x < x1:
        w = r.uniform(40, 90)
        th = r.uniform(0.55, 1.0) * h
        sway = 4 * math.sin(t * 0.8 + x * 0.01)
        cx.line_to(x, y - th * 0.35)
        cx.line_to(x + w / 2 + sway, y - th)
        cx.line_to(x + w, y - th * 0.35)
        x += w * 0.7
    cx.line_to(x1, y + 400)
    cx.close_path()
    src(cx, col)
    cx.fill()


def farmhouse(cx, x, gy, t, door_figure=None, lit=1.0):
    """Weathered two-storey farmhouse; x = centre, gy = ground."""
    w, h = 620, 560
    wall = hexc("#6f706b")
    cx.move_to(x - w / 2 - 40, gy - h)
    cx.line_to(x, gy - h - 230)
    cx.line_to(x + w / 2 + 40, gy - h)
    cx.close_path()
    fs(cx, hexc("#2a2d31"), INK, 4)
    rrect(cx, x + 150, gy - h - 260, 60, 140, 3)
    fs(cx, hexc("#3a302c"), INK, 3)
    cx.rectangle(x - w / 2, gy - h, w, h)
    fs(cx, wall, INK, 4)
    for k in range(1, 18):
        line(cx, [(x - w / 2, gy - h + k * h / 18), (x + w / 2, gy - h + k * h / 18)], shade(wall, -0.15), 2)
    # stains and a broken board
    r = random.Random(9)
    for k in range(6):
        ellipse(cx, x + r.uniform(-280, 280), gy - r.uniform(40, 520), r.uniform(20, 60), r.uniform(30, 90))
        src(cx, (0.2, 0.2, 0.18, 0.18))
        cx.fill()
    for wx, wy, on in ((x - 200, gy - h + 70, 0.9), (x + 120, gy - h + 70, 0.0), (x - 200, gy - 300, 0.0),
                       (x + 120, gy - 300, 0.7)):
        cx.rectangle(wx, wy, 110, 140)
        flick = 0.85 + 0.15 * math.sin(t * 7.3 + wx)
        col = (0.78 * flick, 0.58 * flick, 0.32 * flick, 1) if on * lit > 0 else hexc("#1a1f25")
        fs(cx, col if on else hexc("#1a1f25"), INK, 4)
        line(cx, [(wx + 55, wy), (wx + 55, wy + 140)], hexc("#4b4c48"), 6)
        line(cx, [(wx, wy + 70), (wx + 110, wy + 70)], hexc("#4b4c48"), 6)
        if on:
            g = cairo.RadialGradient(wx + 55, wy + 70, 10, wx + 55, wy + 70, 260)
            g.add_color_stop_rgba(0, 0.85, 0.6, 0.3, 0.18 * lit)
            g.add_color_stop_rgba(1, 0.85, 0.6, 0.3, 0)
            cx.set_source(g)
            cx.arc(wx + 55, wy + 70, 260, 0, 2 * math.pi)
            cx.fill()
    # porch
    cx.rectangle(x - w / 2 - 30, gy - 30, w + 60, 30)
    fs(cx, hexc("#3c3732"), INK, 3)
    cx.move_to(x - w / 2 - 50, gy - 250)
    cx.line_to(x + w / 2 + 50, gy - 250)
    cx.line_to(x + w / 2 + 20, gy - 200)
    cx.line_to(x - w / 2 - 20, gy - 200)
    cx.close_path()
    fs(cx, hexc("#2c2f33"), INK, 3)
    for px in (x - w / 2 - 10, x - 90, x + 90, x + w / 2 + 10):
        line(cx, [(px, gy - 200), (px, gy - 30)], hexc("#4a453f"), 12)
    # front door
    rrect(cx, x - 55, gy - 210, 110, 180, 4)
    fs(cx, hexc("#2b2320"), INK, 4)
    if door_figure:
        door_figure(cx)


def barn(cx, x, gy):
    w, h = 460, 330
    cx.move_to(x - w / 2, gy)
    cx.line_to(x - w / 2, gy - h * 0.62)
    cx.line_to(x - w * 0.3, gy - h * 0.9)
    cx.line_to(x, gy - h)
    cx.line_to(x + w * 0.3, gy - h * 0.9)
    cx.line_to(x + w / 2, gy - h * 0.62)
    cx.line_to(x + w / 2, gy)
    cx.close_path()
    fs(cx, hexc("#4e2826"), INK, 4)
    for k in range(-8, 9):
        line(cx, [(x + k * 26, gy), (x + k * 26, gy - h * 0.6 - (8 - abs(k)) * 9)], hexc("#3f201f"), 3)
    cx.rectangle(x - 90, gy - 200, 180, 200)
    fs(cx, hexc("#2c1a19"), INK, 4)
    line(cx, [(x - 90, gy - 200), (x + 90, gy)], hexc("#6b5a52"), 5)
    line(cx, [(x + 90, gy - 200), (x - 90, gy)], hexc("#6b5a52"), 5)
    cx.rectangle(x - 30, gy - h * 0.72, 60, 50)
    fs(cx, hexc("#0e0f12"), INK, 3)


def tractor(cx, x, gy):
    ellipse(cx, x - 80, gy - 70, 70, 70)
    fs(cx, hexc("#1c1d1f"), INK, 4)
    ellipse(cx, x - 80, gy - 70, 30, 30)
    fs(cx, hexc("#4b2e26"), INK, 3)
    ellipse(cx, x + 90, gy - 40, 40, 40)
    fs(cx, hexc("#1c1d1f"), INK, 4)
    rrect(cx, x - 60, gy - 150, 190, 80, 8)
    fs(cx, hexc("#5a3328"), INK, 4)
    rrect(cx, x - 40, gy - 240, 80, 90, 4)
    fs(cx, None, hexc("#2a2a2a"), 6)
    line(cx, [(x + 100, gy - 150), (x + 100, gy - 200)], hexc("#2a2a2a"), 10)


def fence(cx, x0, x1, y, t=0.0, broken=None):
    for k in range(int((x1 - x0) / 70) + 1):
        px = x0 + k * 70
        lean = 0.15 if broken and k in broken else 0.0
        line(cx, [(px, y + 10), (px + 60 * lean, y - 90)], hexc("#2f2a25"), 10)
    line(cx, [(x0, y - 60), (x1, y - 55)], hexc("#2f2a25"), 7)
    line(cx, [(x0, y - 25), (x1, y - 22)], hexc("#2f2a25"), 7)


WIND_BIAS = 0.0


class Corn:
    """Cornfield rows with wind sway and an unnatural travelling disturbance."""

    def __init__(self, x0, x1, rows):
        self.x0, self.x1, self.rows = x0, x1, rows   # rows: list of (ground y, height, colour)
        r = random.Random(4)
        self.stalks = []
        for ri, (gy, h, col) in enumerate(rows):
            x = x0 + r.uniform(0, 20)
            row = []
            while x < x1:
                row.append((x, gy + r.uniform(-6, 6), h * r.uniform(0.85, 1.1), r.uniform(0, 6.28)))
                x += r.uniform(22, 34)
            self.stalks.append(row)

    def draw(self, cx, t, rows, disturb=None):
        """disturb: (x, strength) of something pushing through the rows."""
        for ri in rows:
            gy0, h0, col = self.rows[ri]
            for (x, gy, h, ph) in self.stalks[ri]:
                a = 0.04 * math.sin(t * 1.2 + ph) + 0.02 * math.sin(t * 2.7 + ph * 2)
                a += WIND_BIAS
                if disturb:
                    dx, k = disturb[0], disturb[1]
                    against = len(disturb) > 2 and disturb[2]
                    d = math.exp(-((x - dx) / (110 if against else 70)) ** 2) * k
                    if against:  # pushed hard the wrong way, against the wind
                        a += d * (-0.5 - WIND_BIAS * 2 + 0.12 * math.sin(t * 7 + ph))
                    else:
                        a += d * (0.35 * math.sin(t * 9 + ph) + (0.3 if x > dx else -0.3))
                tx, ty = x + math.sin(a) * h, gy - math.cos(a) * h
                mx, my = x + math.sin(a * 0.5) * h * 0.5, gy - math.cos(a * 0.5) * h * 0.5
                cx.move_to(x, gy)
                cx.curve_to(mx, my, mx, my, tx, ty)
                src(cx, col)
                cx.set_line_width(7)
                cx.stroke()
                for j, f in enumerate((0.35, 0.55, 0.75)):
                    lx = x + (tx - x) * f
                    ly = gy + (ty - gy) * f
                    side = 1 if (j + int(ph * 3)) % 2 else -1
                    la = a + side * (0.9 + 0.15 * math.sin(t * 1.5 + ph + j))
                    cx.move_to(lx, ly)
                    cx.curve_to(lx + math.sin(la) * 40, ly - math.cos(la) * 40, lx + math.sin(la) * 70,
                                ly - math.cos(la) * 20, lx + math.sin(la) * 90, ly + 10)
                    cx.set_line_width(5)
                    cx.stroke()


CORN = Corn(2050, 3000, [(1150, 300, hexc("#1f2a26")), (1180, 320, hexc("#243129")), (1215, 330, hexc("#28372e")),
                         (1250, 340, hexc("#2d3c32")), (1290, 350, hexc("#324235")), (1360, 400, hexc("#2f3e33")),
                         (1450, 470, hexc("#2b392f")), (1560, 540, hexc("#26332a"))])


def exterior(cx, t, cam, actors_mid=None, actors_corn=None, corn_disturb=None, door_figure=None, fog_k=1.0):
    """The farm, layered with parallax. cam = (x, y, zoom) in world coords.
    actors_mid(cx): figures in the yard (world coords). actors_corn(cx): something between corn rows."""
    sky(cx, t)
    cx.save()
    layer(cx, cam, 0.35, 0.4)
    treeline(cx, GROUND_Y - 60, 380, hexc("#1a2326"), 1, t=t)
    cx.restore()
    cx.save()
    layer(cx, cam, 0.35, 0.4)
    fog(cx, t, GROUND_Y - 250, GROUND_Y + 20, k=0.12 * fog_k, seed=3, x0=-600, x1=3000)
    cx.restore()
    cx.save()
    layer(cx, cam, 0.65, 0.7)
    treeline(cx, GROUND_Y - 10, 300, hexc("#151d1f"), 2, t=t)
    cx.restore()
    cx.save()
    layer(cx, cam, 1.0)
    # ground
    cx.rectangle(-1000, GROUND_Y, WORLD_W + 2000, H * 2)
    g = cairo.LinearGradient(0, GROUND_Y, 0, GROUND_Y + 900)
    g.add_color_stop_rgba(0, *hexc("#28332e"))
    g.add_color_stop_rgba(1, *hexc("#1a201d"))
    cx.set_source(g)
    cx.fill()
    # muddy track
    cx.move_to(560, GROUND_Y + 40)
    cx.curve_to(900, GROUND_Y + 200, 1300, GROUND_Y + 160, 1700, GROUND_Y + 60)
    src(cx, (0.2, 0.17, 0.14, 0.7))
    cx.set_line_width(80)
    cx.stroke()
    CORN.draw(cx, t, [0, 1], corn_disturb)
    if actors_corn:
        actors_corn(cx)
    CORN.draw(cx, t, [2, 3, 4, 5, 6, 7], corn_disturb)
    barn(cx, 1700, GROUND_Y + 60)
    tractor(cx, 1330, GROUND_Y + 110)
    farmhouse(cx, 520, GROUND_Y + 120, t, door_figure=door_figure)
    fence(cx, -200, 1150, GROUND_Y + 220, t, broken=(4, 9))
    if actors_mid:
        actors_mid(cx)
    fog(cx, t, GROUND_Y + 50, GROUND_Y + 450, k=0.14 * fog_k, seed=5, x0=-400, x1=3200, speed=18)
    cx.restore()
    # foreground: wet grass silhouettes and a leaning post, moving faster than the yard (parallax)
    cx.save()
    layer(cx, cam, 1.3, 1.1)
    r = random.Random(12)
    for k in range(420):
        x = -600 + k * 10 + r.uniform(-6, 6)
        base = GROUND_Y + 650 + r.uniform(-30, 60)
        h = r.uniform(60, 240) * (1.4 if (k // 9) % 3 == 0 else 1.0)
        a = 0.08 * math.sin(t * 1.4 + k * 0.37) + r.uniform(-0.25, 0.25)
        cx.move_to(x - 6, base + 200)
        cx.line_to(x + math.sin(a) * h, base - h)
        cx.line_to(x + 6, base + 200)
        src(cx, (0.05 + r.uniform(0, 0.03), 0.07 + r.uniform(0, 0.03), 0.06, 1))
        cx.fill()
    cx.rectangle(-1000, GROUND_Y + 700, WORLD_W + 2000, 1200)
    src(cx, (0.06, 0.08, 0.07, 1))
    cx.fill()
    for px in (300, 1250, 2350):
        line(cx, [(px, GROUND_Y + 900), (px + 25, GROUND_Y + 380)], (0.05, 0.06, 0.06, 1), 30)
    cx.restore()


# ------------------------------------------------------------ interiors
def panel_wall(cx, x0, y0, x1, y1, base=hexc("#33302c"), step=64):
    cx.rectangle(x0, y0, x1 - x0, y1 - y0)
    src(cx, base)
    cx.fill()
    x = x0
    k = 0
    while x < x1:
        line(cx, [(x, y0), (x, y1)], shade(base, -0.3), 3)
        if k % 3 == 1:
            cx.rectangle(x + 4, y0, step - 8, y1 - y0)
            src(cx, (0, 0, 0, 0.06))
            cx.fill()
        x += step
        k += 1


def floorboards(cx, y0, base=hexc("#2a2421")):
    cx.rectangle(0, y0, W, H - y0)
    src(cx, base)
    cx.fill()
    y, h = y0, 24
    while y < H:
        line(cx, [(0, y), (W, y)], shade(base, -0.35), 2)
        y += h
        h *= 1.13
    cx.rectangle(0, y0 - 24, W, 24)
    fs(cx, hexc("#3d3833"), INK, 3)


def hallway(cx, t, outside_draw=None, moon=1.0):
    """Front hallway: door left of centre, a narrow sidelight window beside it."""
    panel_wall(cx, 0, 0, W, 1500)
    floorboards(cx, 1500)
    # sidelight (outside visible)
    sx0, sy0, sw, sh = 650, 560, 150, 820
    cx.save()
    cx.rectangle(sx0, sy0, sw, sh)
    cx.clip()
    g = cairo.LinearGradient(0, sy0, 0, sy0 + sh)
    g.add_color_stop_rgba(0, *hexc("#4a5763"))
    g.add_color_stop_rgba(1, *hexc("#2b3238"))
    cx.set_source(g)
    cx.paint()
    if outside_draw:
        outside_draw(cx, (sx0, sy0, sw, sh))
    fog(cx, t, sy0 + 200, sy0 + sh, k=0.2, seed=8, x0=sx0 - 200, x1=sx0 + sw + 200, speed=10)
    cx.restore()
    cx.rectangle(sx0, sy0, sw, sh)
    fs(cx, None, hexc("#4a4640"), 14)
    for k in range(1, 4):
        line(cx, [(sx0, sy0 + k * sh / 4), (sx0 + sw, sy0 + k * sh / 4)], hexc("#4a4640"), 7)
    # door
    rrect(cx, 150, 460, 460, 1040, 6)
    fs(cx, hexc("#4a443d"), INK, 4)
    rrect(cx, 185, 495, 390, 1005, 4)
    fs(cx, hexc("#2f2722"), INK, 4)
    for py in (560, 1000):
        rrect(cx, 225, py, 140, 360, 6)
        fs(cx, None, hexc("#211b18"), 5)
        rrect(cx, 395, py, 140, 360, 6)
        fs(cx, None, hexc("#211b18"), 5)
    ellipse(cx, 540, 960, 18, 18)
    fs(cx, hexc("#6b5a3a"), INK, 3)
    rrect(cx, 520, 880, 40, 40, 6)   # deadbolt
    fs(cx, hexc("#5b4d33"), INK, 3)
    line(cx, [(540, 760), (570, 800), (560, 840)], hexc("#7a7a78"), 5)  # chain
    # moonlight shaft through the sidelight onto the floor
    cx.move_to(sx0, sy0 + sh)
    cx.line_to(sx0 + sw, sy0 + sh)
    cx.line_to(sx0 + sw + 420, H)
    cx.line_to(sx0 - 60, H)
    cx.close_path()
    g = cairo.LinearGradient(0, sy0 + sh, 0, H)
    g.add_color_stop_rgba(0, 0.65, 0.75, 0.9, 0.16 * moon)
    g.add_color_stop_rgba(1, 0.65, 0.75, 0.9, 0.0)
    cx.set_source(g)
    cx.fill()
    # small side table, coat hooks
    rrect(cx, 860, 1150, 180, 24, 4)
    fs(cx, hexc("#3b2f28"), INK, 3)
    line(cx, [(880, 1174), (880, 1500)], hexc("#3b2f28"), 10)
    line(cx, [(1020, 1174), (1020, 1500)], hexc("#3b2f28"), 10)
    for hx in (880, 960):
        line(cx, [(hx, 640), (hx + 16, 660)], hexc("#555555"), 6)
    cx.move_to(960, 660)
    cx.curve_to(930, 760, 1000, 860, 960, 960)
    cx.line_to(1010, 960)
    cx.curve_to(1030, 860, 1000, 760, 980, 660)
    fs(cx, hexc("#3f4a3e"), INK, 3)


def kitchen_dark(cx, t, window_draw=None, led=0.0):
    panel_wall(cx, 0, 0, W, 1380, base=hexc("#2f302e"), step=80)
    floorboards(cx, 1380, base=hexc("#262220"))
    # window over the sink
    wx, wy, ww, wh = 200, 330, 680, 560
    cx.save()
    cx.rectangle(wx, wy, ww, wh)
    cx.clip()
    if window_draw:
        window_draw(cx, (wx, wy, ww, wh))
    cx.restore()
    cx.rectangle(wx, wy, ww, wh)
    fs(cx, None, hexc("#4a4640"), 18)
    line(cx, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], hexc("#4a4640"), 10)
    line(cx, [(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], hexc("#4a4640"), 10)
    rrect(cx, wx - 30, wy + wh + 10, ww + 60, 26, 4)
    fs(cx, hexc("#4a4640"), INK, 3)
    # counter
    cx.rectangle(0, 1000, W, 380)
    fs(cx, hexc("#2b2724"), INK, 4)
    rrect(cx, -10, 980, W + 20, 30, 4)
    fs(cx, hexc("#4b4741"), INK, 3)
    for k in range(4):
        rrect(cx, 30 + k * 265, 1040, 235, 300, 6)
        fs(cx, None, hexc("#1d1a18"), 4)
    if led > 0:  # red emergency glow
        g = cairo.RadialGradient(540, 1450, 10, 540, 1450, 900)
        g.add_color_stop_rgba(0, 0.6, 0.12, 0.1, 0.22 * led)
        g.add_color_stop_rgba(1, 0.6, 0.12, 0.1, 0)
        cx.set_source(g)
        cx.paint()


def table_top(cx, y=1450, w=1000):
    rrect(cx, W / 2 - w / 2, y, w, 40, 6)
    fs(cx, hexc("#3a2e27"), INK, 4)
    for side in (-1, 1):
        line(cx, [(W / 2 + side * (w / 2 - 60), y + 40), (W / 2 + side * (w / 2 - 60), H + 20)], hexc("#2b221d"), 26)


def radio(cx, x, y, s=1.0, dial=0.0, t=0.0, led=1.0, static=1.0):
    """Battery emergency radio. dial 0..1 moves the tuning needle."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    line(cx, [(110, -110), (190, -330)], hexc("#8a8f93"), 7)       # antenna
    rrect(cx, -200, -120, 400, 240, 26)
    fs(cx, hexc("#2c3035"), INK, 5)
    rrect(cx, -170, -90, 170, 180, 14)                              # speaker grill
    fs(cx, hexc("#1d2024"), INK, 3)
    for k in range(7):
        line(cx, [(-155, -70 + k * 24), (-15, -70 + k * 24)], hexc("#3b4046"), 6)
    rrect(cx, 20, -90, 160, 70, 8)                                  # display
    fs(cx, hexc("#1f2a22"), INK, 3)
    cx.save()
    rrect(cx, 20, -90, 160, 70, 8)
    cx.clip()
    r = random.Random(int(t * 30))
    pts = [(24 + i * 4, -55 + (r.uniform(-22, 22) * static if static else 0)) for i in range(40)]
    line(cx, pts, (0.55, 0.8, 0.6, 0.85), 2)
    nx = 30 + 140 * dial
    line(cx, [(nx, -88), (nx, -22)], (0.85, 0.35, 0.25, 0.9), 3)
    cx.restore()
    cx.save()                                                       # tuning knob
    cx.translate(100, 40)
    ellipse(cx, 0, 0, 46, 46)
    fs(cx, hexc("#3b4046"), INK, 4)
    cx.rotate(dial * 5.5)
    line(cx, [(0, 0), (0, -36)], hexc("#c8c3b8"), 6)
    for k in range(12):
        a = k * math.pi / 6
        line(cx, [(math.cos(a) * 40, math.sin(a) * 40), (math.cos(a) * 46, math.sin(a) * 46)], INK, 3)
    cx.restore()
    ellipse(cx, 170, 90, 9, 9)                                      # red LED
    src(cx, (0.9 * led + 0.2, 0.15, 0.12, 1))
    cx.fill()
    if led > 0:
        g = cairo.RadialGradient(170, 90, 0, 170, 90, 60)
        g.add_color_stop_rgba(0, 1, 0.2, 0.15, 0.45 * led)
        g.add_color_stop_rgba(1, 1, 0.2, 0.15, 0)
        cx.set_source(g)
        cx.arc(170, 90, 60, 0, 2 * math.pi)
        cx.fill()
    cx.restore()

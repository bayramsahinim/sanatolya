"""Original vector recreations of the short's storytelling devices (1080x1920):
the tired eye with a phone reflected in the pupil, the 24-hour clock, the willpower
battery, the nightstand alarm clock + phone, and the Just Needy end card."""
import math
import random

import cairo

from cinecode.core import clamp, hexc, mix, rgrad, rrect, shade, src, vgrad

W, H = 1080, 1920
FONT = "Montserrat ExtraBold"


def text_c(cx, s, x, y, size, c, anchor="center"):
    """Text whose visual centre (cap height) sits on y."""
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    e = cx.text_extents(s)
    capH = cx.text_extents("H").height
    if anchor == "center":
        x0 = x - e.x_advance / 2
    elif anchor == "left":
        x0 = x
    else:
        x0 = x - e.x_advance
    cx.move_to(x0, y + capH / 2)
    src(cx, c)
    cx.show_text(s)
    return e.x_advance


def text_w(cx, s, size):
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    return cx.text_extents(s).x_advance


def pill(cx, x, y, label, size, bg, fg, alpha=1.0, scale=1.0, border=None, padx=None, pady=None):
    """Centred rounded label."""
    if alpha <= 0.001:
        return
    tw = text_w(cx, label, size)
    padx = size * 0.55 if padx is None else padx
    pady = size * 0.38 if pady is None else pady
    w = tw + 2 * padx
    h = size * 0.72 + 2 * pady
    cx.save()
    cx.translate(x, y)
    cx.scale(scale, scale)
    cx.push_group()
    rrect(cx, -w / 2, -h / 2, w, h, h * 0.32)
    src(cx, bg)
    cx.fill_preserve()
    if border:
        src(cx, border)
        cx.set_line_width(max(3, size * 0.07))
        cx.stroke()
    else:
        cx.new_path()
    text_c(cx, label, 0, 0, size, fg)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def watermark(cx, alpha=0.38):
    cx.save()
    text_c(cx, "JUST NEEDY", W - 70, H - 150, 24, (1, 1, 1, alpha), anchor="right")
    cx.restore()


# =====================================================================  EYE
SKIN_STOPS = [(0.00, hexc("#3e2620")), (0.10, hexc("#5a3a2e")), (0.30, hexc("#8a5d47")),
              (0.50, hexc("#7f5545")), (0.66, hexc("#6c4a58")), (0.78, hexc("#76618a")),
              (1.00, hexc("#9384b0"))]
EYE_CY = 1110
EYE_L, EYE_R = (-70, EYE_CY + 20), (W + 70, EYE_CY + 20)
IRIS = (540, 1092)
IRIS_R = 212
PUPIL_R = 98
SCREEN_PALETTES = [
    (hexc("#7fd6a8"), hexc("#b58cf0")),
    (hexc("#f58aa8"), hexc("#a99cf2")),
    (hexc("#8fb7ff"), hexc("#ffb86b")),
    (hexc("#c79cff"), hexc("#7fd6a8")),
    (hexc("#ffa57a"), hexc("#f58aa8")),
]


def _bez(p0, p1, p2, p3, s):
    u = 1 - s
    return (u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1])


def _upper(o):
    k = 375 * o - 30           # o=0 -> lid sits slightly below the corners (closed)
    return (EYE_L, (210, EYE_CY - k), (870, EYE_CY - k), EYE_R)


def _lower():
    return (EYE_L, (230, EYE_CY + 255), (850, EYE_CY + 255), EYE_R)


_rng = random.Random(7)
VEINS = []
for side in (-1, 1):
    for i in range(9):
        x0 = 40 if side < 0 else W - 40
        y0 = EYE_CY + _rng.uniform(-60, 90)
        pts = [(x0, y0)]
        x, y = x0, y0
        for j in range(4):
            x += -side * _rng.uniform(-40, -15) * -1
            x = x if side < 0 else x
            x += (_rng.uniform(25, 60)) * (1 if side < 0 else -1)
            y += _rng.uniform(-28, 28)
            pts.append((x, y))
        VEINS.append((pts, _rng.uniform(1.4, 3.0), _rng.uniform(0.35, 0.7)))
FIBERS = [(_rng.uniform(0, 2 * math.pi), _rng.uniform(0.55, 1.0), _rng.random()) for _ in range(170)]
BROW = []
for i in range(420):
    s = _rng.random()
    x = -60 + s * (W + 120)
    yc = 200 - 70 * math.sin(math.pi * clamp(s * 1.05)) + 25 * s
    BROW.append((x, yc + _rng.gauss(0, 20), _rng.uniform(45, 85), _rng.uniform(-0.15, 0.15), _rng.uniform(0.25, 0.75)))


def _lid_path(cx, o):
    up, lo = _upper(o), _lower()
    cx.move_to(*up[0])
    cx.curve_to(*up[1], *up[2], *up[3])
    cx.curve_to(*lo[2], *lo[1], *lo[0])
    cx.close_path()


def _phone(cx, x, y, scale, t, phase, rot=-0.17, alpha=0.95):
    """Phone screen reflection (feed scrolling)."""
    pw, ph = 66 * scale, 116 * scale
    a, b = SCREEN_PALETTES[phase % len(SCREEN_PALETTES)]
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.push_group()
    rrect(cx, -pw / 2, -ph / 2, pw, ph, 12 * scale)
    src(cx, hexc("#e9ecf5"))
    cx.fill()
    rrect(cx, -pw / 2 + 4 * scale, -ph / 2 + 4 * scale, pw - 8 * scale, ph - 8 * scale, 9 * scale)
    cx.save()
    cx.clip()
    cx.set_source(vgrad(cx, 0, -ph / 2, 0, ph / 2, [(0, shade(a, 0.35)), (1, shade(b, 0.2))]))
    cx.paint()
    # feed cards scrolling up
    off = (t * 34 * scale) % (44 * scale)
    for k in range(-1, 4):
        cy = -ph / 2 + 10 * scale + k * 44 * scale - off
        rrect(cx, -pw / 2 + 9 * scale, cy, pw - 18 * scale, 34 * scale, 5 * scale)
        src(cx, mix(a, b, (k % 2) * 0.8), 0.95)
        cx.fill()
        for ln in range(2):
            rrect(cx, -pw / 2 + 13 * scale, cy + (7 + ln * 9) * scale, (pw - 30 * scale) * (0.9 - 0.3 * ln),
                  4.5 * scale, 2 * scale)
            src(cx, (1, 1, 1, 0.75))
            cx.fill()
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def draw_eye(cx, t, o, zoom=1.0, phase=0, chip=None, focus=None):
    """o = openness 0..1 (1 wide open, ~0.8 tired), chip = (label, alpha, scale)."""
    cx.save()
    cx.set_source(vgrad(cx, 0, 0, 0, H, SKIN_STOPS))
    cx.paint()
    fx, fy = focus or IRIS
    cx.translate(fx, fy)
    cx.scale(zoom, zoom)
    cx.translate(-fx, -fy)
    # soft skin shading
    cx.set_source(rgrad(cx, 540, EYE_CY - 60, 200, 900, [(0, (1, 0.85, 0.75, 0.10)), (1, (0, 0, 0, 0))]))
    cx.paint()
    # under-eye bag
    cx.save()
    cx.translate(540, EYE_CY + 300)
    cx.scale(1.0, 0.32)
    cx.set_source(rgrad(cx, 0, 0, 50, 600, [(0, hexc("#4b2f55", 0.55)), (0.6, hexc("#4b2f55", 0.25)),
                                            (1, hexc("#4b2f55", 0))]))
    cx.arc(0, 0, 600, 0, 2 * math.pi)
    cx.fill()
    cx.restore()
    # eyebrow hairs
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    for x, y, ln, rot, a in BROW:
        ang = -0.25 + rot + (x - 540) / 2600
        cx.move_to(x, y)
        cx.rel_curve_to(ln * 0.4 * math.cos(ang), ln * 0.4 * math.sin(ang) - 6,
                        ln * 0.8 * math.cos(ang), ln * 0.8 * math.sin(ang) - 8,
                        ln * math.cos(ang), ln * math.sin(ang) - 4)
        src(cx, hexc("#24140f", a))
        cx.set_line_width(5)
        cx.stroke()
    # lid crease (fixed)
    for wdt, a in ((26, 0.10), (14, 0.16), (6, 0.22)):
        cx.move_to(20, EYE_CY - 70)
        cx.curve_to(260, EYE_CY - 330, 820, EYE_CY - 330, 1060, EYE_CY - 70)
        src(cx, hexc("#3d2219", a))
        cx.set_line_width(wdt)
        cx.stroke()
    # ---- eyeball inside the opening
    cx.save()
    _lid_path(cx, o)
    cx.clip()
    cx.set_source(rgrad(cx, 540, EYE_CY + 40, 100, 640, [(0, hexc("#fbf3ee")), (0.55, hexc("#efd9d3")),
                                                         (1, hexc("#c9918a"))]))
    cx.paint()
    for pts, lw, a in VEINS:
        cx.move_to(*pts[0])
        for p in pts[1:]:
            cx.line_to(*p)
        src(cx, (0.78, 0.12, 0.14, a))
        cx.set_line_width(lw)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke()
    ix, iy = IRIS
    # iris
    cx.arc(ix, iy, IRIS_R, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, ix, iy, PUPIL_R * 0.9, IRIS_R, [(0, hexc("#5e3608")), (0.18, hexc("#b8771b")),
                                                          (0.55, hexc("#dca137")), (0.86, hexc("#a8701c")),
                                                          (1, hexc("#4a2c08"))]))
    cx.fill()
    for ang, ln, sh in FIBERS:
        r0 = PUPIL_R + 6
        r1 = r0 + (IRIS_R - r0) * ln
        cx.move_to(ix + r0 * math.cos(ang), iy + r0 * math.sin(ang))
        cx.line_to(ix + r1 * math.cos(ang), iy + r1 * math.sin(ang))
        src(cx, (1, 0.9, 0.55, 0.20) if sh > 0.5 else (0.3, 0.16, 0.02, 0.25))
        cx.set_line_width(2.4)
        cx.stroke()
    cx.arc(ix, iy, IRIS_R - 3, 0, 2 * math.pi)
    src(cx, hexc("#3a2206", 0.8))
    cx.set_line_width(7)
    cx.stroke()
    # screen light on iris
    cx.arc(ix, iy, IRIS_R, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, ix + 10, iy - 10, 20, IRIS_R, [(0, (0.75, 0.82, 1, 0.22)), (1, (0.75, 0.82, 1, 0))]))
    cx.fill()
    # pupil
    cx.arc(ix, iy, PUPIL_R, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, ix, iy, 10, PUPIL_R, [(0, hexc("#0c0b10")), (1, hexc("#17141c"))]))
    cx.fill()
    # phone reflection (clipped to iris)
    cx.save()
    cx.arc(ix, iy, IRIS_R - 6, 0, 2 * math.pi)
    cx.clip()
    _phone(cx, ix + 8, iy - 4, 1.0, t, phase)
    cx.restore()
    # glints
    cx.save()
    cx.translate(ix - 92, iy - 88)
    cx.rotate(-0.6)
    cx.scale(1, 0.62)
    cx.arc(0, 0, 30, 0, 2 * math.pi)
    cx.restore()
    src(cx, (1, 1, 1, 0.82))
    cx.fill()
    cx.arc(ix + 70, iy + 64, 9, 0, 2 * math.pi)
    src(cx, (1, 1, 1, 0.5))
    cx.fill()
    # lid shadow on the eyeball
    up = _upper(o)
    for wdt, a in ((120, 0.16), (70, 0.22), (34, 0.25)):
        cx.move_to(*up[0])
        cx.curve_to(*up[1], *up[2], *up[3])
        src(cx, (0.25, 0.1, 0.08, a))
        cx.set_line_width(wdt)
        cx.stroke()
    cx.restore()
    # waterline + lower lid
    lo = _lower()
    cx.move_to(*lo[0])
    cx.curve_to(*lo[1], *lo[2], *lo[3])
    src(cx, hexc("#c27f78"))
    cx.set_line_width(12)
    cx.stroke()
    cx.move_to(lo[0][0], lo[0][1] + 8)
    cx.curve_to(lo[1][0], lo[1][1] + 8, lo[2][0], lo[2][1] + 8, lo[3][0], lo[3][1] + 8)
    src(cx, hexc("#4a2a22", 0.6))
    cx.set_line_width(4)
    cx.stroke()
    for i in range(40):
        s = 0.06 + 0.88 * i / 39
        px, py = _bez(*lo, s)
        side = s - 0.5
        cx.move_to(px, py + 8)
        cx.rel_line_to(side * 30, 18 + 10 * (1 - abs(side) * 2))
        src(cx, hexc("#24140f", 0.6))
        cx.set_line_width(2.6)
        cx.stroke()
    # upper lid edge + lashes
    cx.move_to(*up[0])
    cx.curve_to(*up[1], *up[2], *up[3])
    src(cx, hexc("#1c110d"))
    cx.set_line_width(15)
    cx.stroke()
    shut = clamp((0.42 - o) / 0.42)
    n = 92
    for i in range(n):
        s = 0.03 + 0.94 * i / (n - 1)
        px, py = _bez(*up, s)
        side = (s - 0.5) * 2
        ln = 70 + 45 * (1 - abs(side)) + 10 * math.sin(i * 1.7)
        dx = side * 0.9 + 0.12 * math.sin(i * 2.3)
        dy_up = -1.0
        dy_dn = 0.85
        dy = dy_up + (dy_dn - dy_up) * shut
        L_ = math.hypot(dx, dy)
        dx, dy = dx / L_, dy / L_
        cx.move_to(px, py)
        cx.curve_to(px + dx * ln * 0.35, py + dy * ln * 0.45,
                    px + dx * ln * 0.75 + side * 6, py + dy * ln * 0.9,
                    px + dx * ln * 1.05 + side * 16, py + dy * ln * 0.95 + (8 if shut < 0.5 else -8))
        src(cx, hexc("#160d0a"))
        cx.set_line_width(5.2)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    cx.restore()
    if chip and chip[1] > 0:
        label, a, sc = chip
        pill(cx, 540, 1505, label, 58, hexc("#1d2550", 0.95), (1, 1, 1, 1), a, sc, border=hexc("#6f7fd0"))


# =====================================================================  CLOCK
CC = (540, 1110)
CR = 400          # face radius
BEZ = 62
DAY = hexc("#eee4c8")
SECTORS = {
    # key: (h0, h1, colour, label, label colours (bg, fg))
    "trafficAM": (7.5, 8.5, hexc("#e8695f"), None, None),
    "work": (8.5, 16.5, hexc("#5a8fec"), "WORK", (hexc("#1f3f86"), hexc("#ffffff"))),
    "traffic": (16.5, 17.5, hexc("#e8695f"), "TRAFFIC", (hexc("#9c2a26"), hexc("#ffffff"))),
    "school": (17.5, 19.5, hexc("#a184e6"), "SCHOOL", (hexc("#4b3394"), hexc("#ffffff"))),
    "home": (19.5, 22.0, hexc("#52c08b"), "HOME", (hexc("#1e6b47"), hexc("#ffffff"))),
    "yours": (22.0, 24.0, hexc("#f5cb4c"), None, None),
}
_r2 = random.Random(3)
STARS = []
while len(STARS) < 60:
    a = _r2.uniform(0, 7.5) * 15
    r = _r2.uniform(0.12, 0.96)
    STARS.append((a, r, _r2.uniform(1.5, 4.0), _r2.uniform(0, 6.28)))


def ang(h):
    return math.radians(-90 + h * 15)


def _sector(cx, h0, h1, r):
    cx.move_to(*CC)
    cx.arc(CC[0], CC[1], r, ang(h0), ang(h1))
    cx.close_path()


def draw_clock_bg(cx, grey=0.0, t=0.0):
    top = mix(hexc("#0d1733"), hexc("#25232b"), grey)
    mid = mix(hexc("#16264f"), hexc("#3a3740"), grey)
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, top), (0.55, mid), (1, top)]))
    cx.paint()
    cx.set_source(rgrad(cx, 540, 1100, 100, 900, [(0, (1, 1, 1, 0.05)), (1, (0, 0, 0, 0))]))
    cx.paint()


def draw_clock(cx, st, t):
    """st: dict(hand, sectors{key:prog}, labels{key:alpha}, label_scale{key}, yours_glow,
    night_dim, sleep_label, badge(alpha, scale, pos), zoom, focus)."""
    cx.save()
    z = st.get("zoom", 1.0)
    fx, fy = st.get("focus", CC)
    cx.translate(540, 1110)
    cx.scale(z, z)
    cx.translate(-fx, -fy)
    x, y = CC
    # drop shadow
    cx.arc(x, y + 24, CR + BEZ + 30, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x, y + 24, CR, CR + BEZ + 40, [(0, (0, 0, 0, 0.55)), (1, (0, 0, 0, 0))]))
    cx.fill()
    # bezel
    cx.arc(x, y, CR + BEZ, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x, y, CR, CR + BEZ, [(0, hexc("#6d4c17")), (0.12, hexc("#c99a42")),
                                                (0.45, hexc("#f0d084")), (0.75, hexc("#c4943b")),
                                                (1, hexc("#7a5518"))]))
    cx.fill()
    cx.set_source(rgrad(cx, x - 200, y - 260, 50, CR + BEZ + 200, [(0, (1, 1, 1, 0.18)), (1, (1, 1, 1, 0))]))
    cx.arc(x, y, CR + BEZ, 0, 2 * math.pi)
    cx.arc_negative(x, y, CR, 2 * math.pi, 0)
    cx.fill()
    for i in range(96):
        a = math.radians(i * 3.75 - 90)
        major = i % 4 == 0
        r0 = CR + 12
        r1 = CR + (40 if major else 24)
        cx.move_to(x + r0 * math.cos(a), y + r0 * math.sin(a))
        cx.line_to(x + r1 * math.cos(a), y + r1 * math.sin(a))
        src(cx, hexc("#4b3210", 0.85 if major else 0.5))
        cx.set_line_width(5 if major else 2.5)
        cx.stroke()
    # face
    cx.arc(x, y, CR, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x, y, 30, CR, [(0, shade(DAY, 0.25)), (1, shade(DAY, -0.06))]))
    cx.fill()
    # night sector 0..7.5h
    dim = st.get("night_dim", 0.0)
    _sector(cx, 0, 7.5, CR)
    cx.set_source(rgrad(cx, x, y, 20, CR, [(0, mix(hexc("#2b3f95"), hexc("#3a3550"), dim)),
                                           (1, mix(hexc("#16205c"), hexc("#25213a"), dim))]))
    cx.fill()
    cx.save()
    _sector(cx, 0, 7.5, CR)
    cx.clip()
    for a, r, sz, ph in STARS:
        tw = 0.55 + 0.45 * math.sin(t * 2.2 + ph)
        aa = math.radians(-90 + a)
        cx.arc(x + r * CR * math.cos(aa), y + r * CR * math.sin(aa), sz * (0.7 + 0.3 * tw), 0, 2 * math.pi)
        src(cx, (1, 1, 0.92, 0.85 * tw * (1 - 0.5 * dim)))
        cx.fill()
    # moon
    ma = ang(3.2)
    mx, my = x + 0.6 * CR * math.cos(ma), y + 0.6 * CR * math.sin(ma)
    cx.arc(mx, my, 70, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, mx, my, 30, 70, [(0, (1, 0.95, 0.7, 0.25 * (1 - dim))), (1, (1, 0.95, 0.7, 0))]))
    cx.fill()
    cx.push_group()
    cx.arc(mx, my, 40, 0, 2 * math.pi)
    src(cx, mix(hexc("#fbf3d2"), hexc("#a9a28c"), dim))
    cx.fill()
    cx.set_operator(cairo.OPERATOR_CLEAR)
    cx.arc(mx + 17, my - 13, 35, 0, 2 * math.pi)
    cx.fill()
    cx.pop_group_to_source()
    cx.paint()
    cx.restore()
    # day sectors
    sec = st.get("sectors", {})
    for key, (h0, h1, col, label, lc) in SECTORS.items():
        p = sec.get(key, 0.0)
        if p <= 0:
            continue
        hh = h0 + (h1 - h0) * p
        c = col
        if key == "yours":
            glow = st.get("yours_glow", 0.0)
            c = mix(col, hexc("#ffe27a"), glow * 0.6)
        else:
            c = mix(col, shade(col, -0.35), st.get("others_dim", 0.0))
        _sector(cx, h0, hh, CR)
        cx.set_source(rgrad(cx, x, y, 20, CR, [(0, shade(c, 0.18)), (1, shade(c, -0.06))]))
        cx.fill()
        _sector(cx, h0, hh, CR)
        src(cx, (1, 1, 1, 0.22))
        cx.set_line_width(2)
        cx.stroke()
    yg = st.get("yours_glow", 0.0)
    if yg > 0 and sec.get("yours", 0) > 0:
        cx.save()
        _sector(cx, 22.0, 22.0 + 2.0 * sec["yours"], CR)
        cx.clip()
        cx.set_source(rgrad(cx, x, y, 0, CR, [(0, (1, 1, 0.8, 0)), (1, (1, 0.98, 0.75, 0.45 * yg))]))
        cx.paint()
        cx.restore()
    # inner rim
    cx.arc(x, y, CR, 0, 2 * math.pi)
    src(cx, hexc("#5a3d10", 0.9))
    cx.set_line_width(6)
    cx.stroke()
    cx.arc(x, y, CR - 3, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x, y, CR - 40, CR, [(0, (0, 0, 0, 0)), (1, (0, 0, 0, 0.22))]))
    cx.set_line_width(40)
    cx.stroke()
    # labels
    labs = st.get("labels", {})
    for key, (h0, h1, col, label, lc) in SECTORS.items():
        a_ = labs.get(key, 0.0)
        if not label or a_ <= 0:
            continue
        am = ang((h0 + h1) / 2)
        rr = {"work": 0.55, "traffic": 0.66, "school": 0.62, "home": 0.66}[key] * CR
        sc = st.get("label_scale", {}).get(key, 1.0)
        pill(cx, x + rr * math.cos(am), y + rr * math.sin(am), label, 34, lc[0], lc[1], a_, sc,
             border=(1, 1, 1, 0.55))
    sl = st.get("sleep_label", 0.0)
    if sl > 0:
        am = ang(4.6)
        pill(cx, x + 0.5 * CR * math.cos(am), y + 0.5 * CR * math.sin(am), "SLEEP", 34, hexc("#0f1640"),
             hexc("#cfd8ff"), sl, st.get("sleep_scale", 1.0), border=hexc("#8fa0ff", 0.7))
    # hand
    hand = st.get("hand", 0.0)
    a = ang(hand)
    L_ = CR * 0.9
    cx.save()
    cx.translate(x, y)
    cx.rotate(a)
    cx.move_to(-46, -8)
    cx.line_to(L_ * 0.86, -6)
    cx.line_to(L_, 0)
    cx.line_to(L_ * 0.86, 6)
    cx.line_to(-46, 8)
    cx.close_path()
    src(cx, (0, 0, 0, 0.3))
    cx.save()
    cx.translate(6, 8)
    cx.fill_preserve()
    cx.restore()
    cx.new_path()
    cx.move_to(-46, -8)
    cx.line_to(L_ * 0.86, -6)
    cx.line_to(L_, 0)
    cx.line_to(L_ * 0.86, 6)
    cx.line_to(-46, 8)
    cx.close_path()
    src(cx, hexc("#17161c"))
    cx.fill()
    cx.move_to(L_ * 0.8, -6.5)
    cx.line_to(L_, 0)
    cx.line_to(L_ * 0.8, 6.5)
    cx.close_path()
    src(cx, hexc("#e2453c"))
    cx.fill()
    cx.restore()
    cx.arc(x, y, 30, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, x - 8, y - 8, 2, 30, [(0, hexc("#f7dc94")), (1, hexc("#9a6f25"))]))
    cx.fill()
    cx.arc(x, y, 11, 0, 2 * math.pi)
    src(cx, hexc("#5a3d10"))
    cx.fill()
    cx.restore()
    # badge (screen space so it reads at any zoom)
    b = st.get("badge")
    if b and b[0] > 0:
        pill(cx, b[2][0], b[2][1], "YOURS", b[3] if len(b) > 3 else 92, hexc("#15151c", 0.94), hexc("#ffcf3f"),
             b[0], b[1], border=hexc("#ffcf3f", 0.85))


# =====================================================================  BATTERY
BX, BTOP, BW, BH = 540, 690, 400, 760


def bat_colour(p):
    stops = [(0, hexc("#e2412f")), (15, hexc("#e2412f")), (32, hexc("#e8792b")), (55, hexc("#e6bf32")),
             (75, hexc("#a9d23a")), (100, hexc("#79cf3b"))]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if p <= p1:
            return mix(c0, c1, (p - p0) / (p1 - p0) if p1 > p0 else 0)
    return stops[-1][1]


def draw_battery_bg(cx, low, warm=0.0):
    base_t = mix(hexc("#0b0c16"), hexc("#2c2826"), warm)
    base_b = mix(hexc("#151626"), hexc("#3d3733"), warm)
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, base_t), (0.6, base_b), (1, base_t)]))
    cx.paint()
    if low > 0:
        cx.save()
        cx.translate(540, BTOP + BH + 30)
        cx.scale(1.25, 0.55)
        cx.set_source(rgrad(cx, 0, 0, 0, 520, [(0, (0.85, 0.08, 0.06, 0.55 * low)), (1, (0.5, 0, 0, 0))]))
        cx.arc(0, 0, 520, 0, 2 * math.pi)
        cx.fill()
        cx.restore()


def _bolt(cx, x, y, s, alpha):
    pts = [(0.15, -1), (-0.55, 0.12), (-0.02, 0.12), (-0.2, 1), (0.55, -0.15), (0.02, -0.15), (0.25, -1)]
    cx.move_to(x + pts[0][0] * s, y + pts[0][1] * s)
    for px, py in pts[1:]:
        cx.line_to(x + px * s, y + py * s)
    cx.close_path()
    src(cx, hexc("#ffcc3a", alpha))
    cx.fill_preserve()
    src(cx, hexc("#6b4a00", alpha))
    cx.set_line_width(4)
    cx.stroke()


def draw_battery(cx, t, pct, tag_a=1.0, time_str=None, bolt=0.0, yesterday=0.0, shake=(0, 0), pct_text=None,
                 render_text=None):
    x0 = BX - BW / 2 + shake[0]
    y0 = BTOP + shake[1]
    cap_w, cap_h = 150, 48
    # cap
    rrect(cx, BX - cap_w / 2 + shake[0], y0 - cap_h + 8, cap_w, cap_h, 12)
    cx.set_source(vgrad(cx, 0, y0 - cap_h, 0, y0, [(0, hexc("#9aa0ad")), (1, hexc("#5a5f6b"))]))
    cx.fill()
    # body
    rrect(cx, x0, y0, BW, BH, 54)
    src(cx, hexc("#08080c"))
    cx.fill_preserve()
    src(cx, hexc("#c4c8d3"))
    cx.set_line_width(12)
    cx.stroke()
    ins = 20
    ix0, iy0, iw, ih = x0 + ins, y0 + ins, BW - 2 * ins, BH - 2 * ins
    cx.save()
    rrect(cx, ix0, iy0, iw, ih, 38)
    cx.clip()
    src(cx, hexc("#0c0c12"))
    cx.paint()
    p = clamp(pct / 100.0)
    level = iy0 + ih * (1 - p) if p < 0.995 else iy0 - 30
    col = bat_colour(pct)
    if p > 0:
        amp = 9 * (1 if p < 0.98 else 0)
        cx.move_to(ix0 - 5, iy0 + ih + 5)
        steps = 40
        for i in range(steps + 1):
            xx = ix0 - 5 + (iw + 10) * i / steps
            yy = level + amp * math.sin(i / steps * 2 * math.pi * 1.4 + t * 4.2) * 0.8 \
                + amp * 0.4 * math.sin(i / steps * 2 * math.pi * 2.6 - t * 3.1)
            cx.line_to(xx, yy)
        cx.line_to(ix0 + iw + 5, iy0 + ih + 5)
        cx.close_path()
        cx.set_source(vgrad(cx, ix0, 0, ix0 + iw, 0, [(0, shade(col, -0.25)), (0.35, shade(col, 0.12)),
                                                     (0.7, col), (1, shade(col, -0.3))]))
        cx.fill()
        # bubbles
        rnd = random.Random(5)
        for k in range(16):
            bx = ix0 + 25 + rnd.random() * (iw - 50)
            sp = 40 + rnd.random() * 60
            by = iy0 + ih - ((t * sp + rnd.random() * ih) % ih)
            if by > level + 12:
                cx.arc(bx, by, 3 + rnd.random() * 5, 0, 2 * math.pi)
                src(cx, (1, 1, 1, 0.22))
                cx.fill()
        # surface highlight
        cx.rectangle(ix0, level - 2, iw, 6)
        src(cx, (1, 1, 1, 0.12))
        cx.fill()
    # glass highlight
    rrect(cx, ix0 + 18, iy0 + 30, 26, ih - 60, 13)
    src(cx, (1, 1, 1, 0.07))
    cx.fill()
    cx.restore()
    cxm = BX + shake[0]
    # percentage
    s = pct_text if pct_text is not None else f"{int(round(pct))}%"
    if render_text:
        surf, w, h, pad = render_text(s, 150)
        cx.set_source_surface(surf, cxm - w / 2, y0 + 300 - h / 2)
        cx.paint()
    if yesterday > 0:
        pill(cx, cxm, y0 + 70, "YESTERDAY: 100%", 30, hexc("#101015", 0.92), hexc("#e8e8ee"), yesterday,
             border=hexc("#ffffff", 0.5))
    if tag_a > 0:
        pill(cx, cxm, y0 + 430, "WILLPOWER", 36, hexc("#16161d", 0.92), hexc("#ffffff"), tag_a,
             border=hexc("#ffffff", 0.6))
    if bolt > 0:
        _bolt(cx, cxm, y0 + 435, 62, bolt)
    if time_str:
        pill(cx, cxm, y0 + 590, time_str, 50, hexc("#121218", 0.9), hexc("#ffffff"), 1.0,
             border=hexc("#ffffff", 0.35), padx=26, pady=16)


# =====================================================================  NIGHTSTAND
SEG = {  # 7-seg: a b c d e f g
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd",
    "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg", " ": "",
}


def _seg_digit(cx, x, y, w, h, ch, on, off):
    th = w * 0.21
    sl = 0.0
    segs = {
        "a": ((0, 0), (1, 0)), "b": ((1, 0), (1, 0.5)), "c": ((1, 0.5), (1, 1)),
        "d": ((0, 1), (1, 1)), "e": ((0, 0.5), (0, 1)), "f": ((0, 0), (0, 0.5)), "g": ((0, 0.5), (1, 0.5)),
    }
    lit = SEG.get(ch, "")
    for k, ((ax, ay), (bx, by)) in segs.items():
        px0 = x + ax * w - (ay - 0.5) * sl * h
        py0 = y + ay * h
        px1 = x + bx * w - (by - 0.5) * sl * h
        py1 = y + by * h
        dx, dy = px1 - px0, py1 - py0
        L_ = math.hypot(dx, dy)
        ux, uy = dx / L_, dy / L_
        nx, ny = -uy, ux
        g = th * 0.12
        pts = [(px0 + ux * g, py0 + uy * g), (px0 + ux * (g + th / 2) + nx * th / 2, py0 + uy * (g + th / 2) + ny * th / 2),
               (px1 - ux * (g + th / 2) + nx * th / 2, py1 - uy * (g + th / 2) + ny * th / 2), (px1 - ux * g, py1 - uy * g),
               (px1 - ux * (g + th / 2) - nx * th / 2, py1 - uy * (g + th / 2) - ny * th / 2),
               (px0 + ux * (g + th / 2) - nx * th / 2, py0 + uy * (g + th / 2) - ny * th / 2)]
        cx.move_to(*pts[0])
        for p in pts[1:]:
            cx.line_to(*p)
        cx.close_path()
        src(cx, on if k in lit else off)
        cx.fill()


def _led(cx, s, ampm, x, y, on, off, dw=104, dh=190, gap=30):
    """Draw 'H:MM' style LED text centred at x, top y."""
    chars = list(s)
    widths = [dw if c != ":" else 34 for c in chars]
    total = sum(widths) + gap * (len(chars) - 1) + 110
    cxp = x - total / 2
    for c, wd in zip(chars, widths):
        if c == ":":
            for yy in (0.32, 0.7):
                cx.arc(cxp + wd / 2, y + dh * yy, 11, 0, 2 * math.pi)
                src(cx, on)
                cx.fill()
        else:
            _seg_digit(cx, cxp, y, dw, dh, c, on, off)
        cxp += wd + gap
    # AM / PM indicator
    text_c(cx, "AM", cxp + 40, y + 40, 34, on if ampm == "AM" else off)
    text_c(cx, "PM", cxp + 40, y + dh - 40, 34, on if ampm == "PM" else off)


def draw_night(cx, t, clock_str, ampm, red=0.0, flicker=1.0, phone_phase=0):
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, hexc("#0c1533")), (0.35, hexc("#16285e")), (1, hexc("#0b1430"))]))
    cx.paint()
    # faint window with moonlight
    rrect(cx, 90, 70, 300, 360, 10)
    src(cx, hexc("#2a3f7c", 0.35))
    cx.fill()
    for (wx, wy) in ((105, 85), (245, 85), (105, 255), (245, 255)):
        rrect(cx, wx, wy, 130, 160, 6)
        src(cx, hexc("#4c66b0", 0.22))
        cx.fill()
    # red alarm wash
    if red > 0:
        cx.set_source(rgrad(cx, 540, 640, 50, 1100, [(0, (0.9, 0.08, 0.06, 0.45 * red)), (1, (0.5, 0, 0, 0))]))
        cx.paint()
    # shelf
    cx.rectangle(0, 790, W, 46)
    cx.set_source(vgrad(cx, 0, 790, 0, 836, [(0, hexc("#8a5a36")), (0.25, hexc("#6b4428")), (1, hexc("#3e2716"))]))
    cx.fill()
    cx.rectangle(0, 836, W, 40)
    cx.set_source(vgrad(cx, 0, 836, 0, 876, [(0, (0, 0, 0, 0.45)), (1, (0, 0, 0, 0))]))
    cx.fill()
    # alarm clock
    bx, by, bw, bh = 170, 560, 740, 236
    rrect(cx, bx, by, bw, bh, 34)
    cx.set_source(vgrad(cx, 0, by, 0, by + bh, [(0, hexc("#2b2c33")), (1, hexc("#141418"))]))
    cx.fill()
    rrect(cx, bx + 4, by + 4, bw - 8, 30, 20)
    src(cx, (1, 1, 1, 0.06))
    cx.fill()
    rrect(cx, bx + 26, by + 24, bw - 52, bh - 48, 20)
    src(cx, hexc("#120405"))
    cx.fill()
    on = (1.0, 0.22, 0.16, flicker)
    off = (1.0, 0.2, 0.15, 0.06)
    cx.save()
    rrect(cx, bx + 26, by + 24, bw - 52, bh - 48, 20)
    cx.clip()
    # glow
    cx.set_source(rgrad(cx, 540, by + bh / 2, 20, 360, [(0, (1, 0.15, 0.1, 0.20 * flicker)), (1, (1, 0.1, 0.1, 0))]))
    cx.paint()
    _led(cx, clock_str, ampm, 540, by + 45, on, off, dw=96, dh=146, gap=26)
    cx.restore()
    cx.set_source(rgrad(cx, 540, by + bh / 2, 100, 520, [(0, (1, 0.15, 0.1, 0.10 * flicker)), (1, (1, 0.1, 0.1, 0))]))
    cx.paint()
    # bed / blanket
    cx.move_to(-20, 1080)
    cx.curve_to(250, 1010, 520, 1100, 760, 1040)
    cx.curve_to(900, 1005, 1010, 1030, W + 20, 1060)
    cx.line_to(W + 20, H + 20)
    cx.line_to(-20, H + 20)
    cx.close_path()
    cx.set_source(vgrad(cx, 0, 1000, 0, H, [(0, hexc("#2f53b8")), (0.5, hexc("#2140a0")), (1, hexc("#152a6f"))]))
    cx.fill()
    for (y1, a) in ((1300, 0.18), (1520, 0.14), (1720, 0.12)):
        cx.move_to(-20, y1)
        cx.curve_to(300, y1 - 90, 640, y1 + 70, W + 20, y1 - 40)
        src(cx, (0.05, 0.1, 0.3, a))
        cx.set_line_width(46)
        cx.stroke()
        cx.move_to(-20, y1 - 28)
        cx.curve_to(300, y1 - 118, 640, y1 + 42, W + 20, y1 - 68)
        src(cx, (0.6, 0.7, 1, a * 0.5))
        cx.set_line_width(10)
        cx.stroke()
    # phone light on blanket
    px, py = 560, 1360
    cx.save()
    cx.translate(px, py + 40)
    cx.scale(1.4, 0.75)
    cx.set_source(rgrad(cx, 0, 0, 30, 420, [(0, (0.75, 0.6, 1, 0.38 * flicker)), (1, (0.6, 0.5, 1, 0))]))
    cx.arc(0, 0, 420, 0, 2 * math.pi)
    cx.fill()
    cx.restore()
    # phone
    cx.save()
    cx.translate(px, py)
    cx.rotate(-0.33)
    pw, ph = 230, 430
    rrect(cx, -pw / 2 + 10, -ph / 2 + 16, pw, ph, 38)
    src(cx, (0, 0, 0, 0.35))
    cx.fill()
    rrect(cx, -pw / 2, -ph / 2, pw, ph, 38)
    src(cx, hexc("#101018"))
    cx.fill()
    rrect(cx, -pw / 2 + 10, -ph / 2 + 10, pw - 20, ph - 20, 30)
    cx.save()
    cx.clip()
    a_, b_ = SCREEN_PALETTES[phone_phase % len(SCREEN_PALETTES)]
    cx.set_source(vgrad(cx, 0, -ph / 2, 0, ph / 2, [(0, hexc("#f48ac4")), (0.5, hexc("#b597f2")),
                                                   (1, hexc("#6eaaf5"))]))
    cx.paint()
    off_ = (t * 60) % 120
    for k in range(-1, 5):
        yy = -ph / 2 + 50 + k * 120 - off_
        rrect(cx, -pw / 2 + 24, yy, pw - 48, 96, 14)
        src(cx, (1, 1, 1, 0.28))
        cx.fill()
        cx.arc(-pw / 2 + 50, yy + 26, 14, 0, 2 * math.pi)
        src(cx, mix(a_, b_, k % 2))
        cx.fill()
        rrect(cx, -pw / 2 + 74, yy + 18, 90, 12, 6)
        src(cx, (1, 1, 1, 0.75))
        cx.fill()
        rrect(cx, -pw / 2 + 36, yy + 52, pw - 80, 10, 5)
        src(cx, (1, 1, 1, 0.5))
        cx.fill()
    cx.restore()
    rrect(cx, -40, -ph / 2 + 18, 80, 16, 8)
    src(cx, hexc("#101018"))
    cx.fill()
    cx.restore()
    if red > 0:
        cx.set_source(rgrad(cx, 540, 700, 200, 1600, [(0, (0, 0, 0, 0)), (1, (0.3, 0, 0, 0.35 * red))]))
        cx.paint()


# =====================================================================  END CARD
def _logo(cx, x, y, r, a):
    """Just Needy mark: plain white head inside the blue hood."""
    cx.save()
    cx.push_group()
    cx.arc(x, y + r * 0.08, r * 1.32, 0, 2 * math.pi)
    src(cx, hexc("#2F6FDB"))
    cx.fill_preserve()
    src(cx, hexc("#1c1c24"))
    cx.set_line_width(r * 0.07)
    cx.stroke()
    cx.arc(x, y + r * 0.12, r, 0, 2 * math.pi)
    src(cx, hexc("#ffffff"))
    cx.fill_preserve()
    src(cx, hexc("#1c1c24"))
    cx.set_line_width(r * 0.07)
    cx.stroke()
    for dx in (-0.32, 0.32):
        cx.arc(x + dx * r, y, r * 0.085, 0, 2 * math.pi)
        src(cx, hexc("#1c1c24"))
        cx.fill()
    cx.arc(x, y + r * 0.3, r * 0.3, 0.2, math.pi - 0.2)
    src(cx, hexc("#1c1c24"))
    cx.set_line_width(r * 0.07)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def _icon(cx, kind, x, y, s, a, rot=0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.set_line_width(5)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    if kind == "moon":
        cx.push_group()
        cx.arc(0, 0, s, 0, 2 * math.pi)
        src(cx, hexc("#ffd66b"))
        cx.fill()
        cx.set_operator(cairo.OPERATOR_CLEAR)
        cx.arc(s * 0.45, -s * 0.35, s * 0.85, 0, 2 * math.pi)
        cx.fill()
        cx.pop_group_to_source()
        cx.paint_with_alpha(a)
    elif kind == "clock":
        cx.arc(0, 0, s, 0, 2 * math.pi)
        cx.move_to(0, 0)
        cx.line_to(0, -s * 0.6)
        cx.move_to(0, 0)
        cx.line_to(s * 0.45, s * 0.2)
        src(cx, hexc("#5ee0c8", a))
        cx.stroke()
    elif kind == "battery":
        rrect(cx, -s * 0.55, -s, s * 1.1, s * 2, s * 0.25)
        src(cx, hexc("#ff7a8a", a))
        cx.stroke()
        rrect(cx, -s * 0.35, s * 0.4, s * 0.7, s * 0.4, 4)
        cx.fill()
    elif kind == "bolt":
        pts = [(0.15, -1), (-0.55, 0.12), (-0.02, 0.12), (-0.2, 1), (0.55, -0.15), (0.02, -0.15), (0.25, -1)]
        cx.move_to(pts[0][0] * s, pts[0][1] * s)
        for px, py in pts[1:]:
            cx.line_to(px * s, py * s)
        cx.close_path()
        src(cx, hexc("#8c7bff", a))
        cx.stroke()
    cx.restore()


def draw_card(cx, t, lt, follow_p, render_text):
    """lt = local time since card start; follow_p 0..1 = tap on the follow button."""
    from cinecode.core import back_out, ease_out
    cx.set_source(vgrad(cx, 0, 0, 0, H, [(0, hexc("#0b0d2a")), (0.5, hexc("#1e1650")), (1, hexc("#2a1a5c"))]))
    cx.paint()
    cx.set_source(rgrad(cx, 540, 980, 50, 700, [(0, (0.55, 0.45, 1, 0.22)), (1, (0.3, 0.2, 0.8, 0))]))
    cx.paint()
    for kind, x, y, s, ph in (("moon", 190, 760, 34, 0.0), ("clock", 900, 720, 34, 1.3), ("battery", 170, 1280, 30, 2.2),
                              ("bolt", 910, 1260, 36, 3.1)):
        a = ease_out(clamp((lt - 0.15 - ph * 0.04) / 0.4)) * 0.9
        _icon(cx, kind, x, y + 10 * math.sin(t * 1.6 + ph), s, a, 0.1 * math.sin(t + ph))
    sc = back_out(clamp(lt / 0.45))
    cx.save()
    cx.translate(540, 840)
    cx.scale(sc, sc)
    cx.arc(0, 0, 210, 0, 2 * math.pi)
    cx.set_source(rgrad(cx, 0, 0, 60, 220, [(0, (1, 0.8, 0.35, 0.28)), (1, (1, 0.8, 0.35, 0))]))
    cx.fill()
    _logo(cx, 0, 0, 120, clamp(lt / 0.2))
    cx.restore()
    wa = ease_out(clamp((lt - 0.2) / 0.35))
    surf, w, h, pad = render_text("Just [Needy]", 112)
    cx.set_source_surface(surf, 540 - w / 2, 1110 - h / 2 + (1 - wa) * 30)
    cx.paint_with_alpha(wa)
    text_c(cx, "How things actually work.", 540, 1205 + (1 - wa) * 20, 40, hexc("#cfc8ff", wa))
    # follow button
    ba = ease_out(clamp((lt - 0.45) / 0.3))
    press = 1 - 0.08 * math.sin(math.pi * clamp((follow_p - 0.0) / 0.25)) if follow_p > 0 else 1
    done = follow_p > 0.12
    cx.save()
    cx.translate(540, 1345)
    cx.scale(press, press)
    if not done:
        pill(cx, 0, 0, "+  Follow", 50, hexc("#ffc857"), hexc("#16131f"), ba, padx=48, pady=24)
    else:
        pill(cx, 0, 0, "     Following", 50, hexc("#16131f", 0.6), hexc("#ffc857"), ba, border=hexc("#ffc857"),
             padx=48, pady=24)
        tw = text_w(cx, "     Following", 50)
        x0 = -tw / 2 + 4
        cx.move_to(x0, 2)
        cx.line_to(x0 + 14, 16)
        cx.line_to(x0 + 40, -14)
        src(cx, hexc("#ffc857", ba))
        cx.set_line_width(8)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke()
    cx.restore()
    # tap ripple
    if 0 < follow_p < 1:
        rr = 40 + 160 * follow_p
        cx.arc(540, 1345, rr, 0, 2 * math.pi)
        src(cx, (1, 0.85, 0.4, 0.5 * (1 - follow_p)))
        cx.set_line_width(6)
        cx.stroke()

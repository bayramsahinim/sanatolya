"""Procedural planet Earth: simplified continent outlines (lon, lat) drawn in orthographic
projection, with deserts, ice, glossy ocean shading. Used for the Earth-cake top."""
import math

import cairo

from cinecode.core import hexc, smooth_poly, src

CONT = {
    "namerica": [(-168, 66), (-162, 70), (-156, 71), (-140, 70), (-128, 70), (-115, 68), (-95, 72), (-82, 73), (-78, 68),
                 (-65, 60), (-62, 58), (-55, 52), (-60, 47), (-66, 45), (-70, 43), (-75, 38), (-76, 35), (-81, 31),
                 (-80, 25), (-82, 27), (-84, 30), (-90, 29), (-97, 27), (-97, 22), (-94, 18), (-90, 21), (-87, 21),
                 (-88, 16), (-84, 11), (-80, 8), (-78, 9), (-83, 8), (-86, 12), (-92, 14), (-98, 16), (-105, 20),
                 (-106, 23), (-112, 29), (-110, 23), (-115, 30), (-118, 34), (-123, 38), (-124, 42), (-124, 48),
                 (-130, 54), (-137, 58), (-145, 60), (-152, 59), (-158, 57), (-165, 55), (-160, 59), (-166, 62)],
    "greenland": [(-73, 78), (-60, 82), (-35, 83), (-20, 82), (-18, 76), (-22, 70), (-32, 66), (-42, 60), (-48, 61),
                  (-53, 66), (-55, 70), (-60, 76)],
    "samerica": [(-80, 9), (-75, 11), (-71, 12), (-62, 11), (-52, 5), (-50, 0), (-44, -2), (-35, -5), (-35, -9),
                 (-39, -14), (-41, -22), (-48, -26), (-53, -34), (-58, -38), (-62, -40), (-65, -45), (-68, -50),
                 (-69, -55), (-73, -53), (-75, -47), (-73, -40), (-71, -30), (-70, -18), (-76, -14), (-81, -6),
                 (-80, 0), (-78, 4), (-77, 8)],
    "eurasia": [(-9, 37), (-9, 43), (-2, 43.5), (-1.5, 46), (-4.5, 48), (-1, 49.5), (2, 51), (5, 53), (8, 54), (9, 55),
                (10, 54), (14, 54), (19, 54.5), (21, 57), (24, 59.5), (29, 60), (32, 64), (40, 66), (44, 68), (55, 69),
                (60, 70), (68, 73), (80, 73), (87, 75), (100, 78), (112, 74), (130, 72), (140, 72), (160, 70),
                (170, 69), (180, 68), (180, 65), (170, 60), (163, 58), (160, 53), (156, 51), (155, 57), (150, 59),
                (142, 59), (137, 55), (141, 52), (140, 48), (135, 43), (130, 42), (129, 36), (126, 35), (126, 38),
                (122, 40), (121, 37), (119, 35), (122, 31), (121, 28), (117, 23), (110, 21), (106, 19), (109, 12),
                (106, 9), (103, 10), (100, 13), (100, 8), (103, 1.5), (101, 3), (98, 8), (98, 16), (94, 17),
                (92, 22), (88, 22), (85, 20), (80, 15), (80, 10), (77, 8), (73, 17), (72, 21), (68, 24), (62, 25),
                (57, 26), (56, 27), (51, 28), (48, 30), (50, 26), (52, 24), (56, 24), (59, 22), (57, 19), (52, 16),
                (45, 13), (43, 15), (39, 22), (35, 28), (34, 31), (36, 36), (30, 36.5), (27, 37), (26, 40),
                (23, 40), (22, 37), (21, 39), (19, 42), (16, 45), (13.5, 45.5), (16, 42), (18, 40), (16, 38),
                (12, 41), (10, 44), (7, 44), (3, 43), (-1, 37), (-5, 36)],
    "scandinavia": [(5, 58), (5, 62), (10, 64), (14, 68), (18, 70), (25, 71), (30, 70), (29, 67), (25, 65.5),
                    (21, 64), (18, 61), (18, 59), (16, 56), (12, 56), (10, 59), (7, 58)],
    "africa": [(-17, 21), (-16, 28), (-10, 30), (-6, 35.8), (10, 37), (11, 33), (20, 31), (30, 31), (33, 31),
               (35, 28), (43, 12), (51, 12), (51, 10), (48, 4), (41, -2), (40, -10), (35, -18), (35, -24),
               (33, -28), (28, -33), (20, -35), (18, -32), (14, -23), (12, -17), (13, -11), (12, -5), (9, -1),
               (9, 4), (5, 6), (-3, 5), (-8, 4.5), (-13, 8), (-17, 14)],
    "madagascar": [(44, -25), (43, -22), (44, -17), (49, -12), (50, -16), (47, -25)],
    "uk": [(-5, 50), (1.5, 51), (1.7, 53), (-0.5, 54.5), (-2, 57), (-3, 58.6), (-5, 58.5), (-6, 56.5), (-5, 55),
           (-3, 54), (-4.5, 53), (-5, 52)],
    "ireland": [(-10, 52), (-6, 52), (-6, 55), (-8, 55.3), (-10, 54)],
    "iceland": [(-24, 64), (-22, 66), (-16, 66.5), (-13, 65), (-18, 63.4)],
    "japan": [(130, 31), (131, 34), (135, 34), (140, 36), (141, 40), (142, 45), (144, 43), (141, 38), (140, 35),
              (136, 33.5), (132, 33)],
    "sumatra": [(95, 5.5), (98, 4), (104, -2), (106, -6), (102, -4), (95, 2)],
    "borneo": [(109, 1), (110, -3), (116, -4), (119, 1), (117, 7), (113, 3)],
    "java": [(105, -6), (114, -7), (114, -8.5), (106, -7.5)],
    "newguinea": [(131, -1), (141, -3), (150, -10), (143, -9), (138, -8), (132, -4)],
    "australia": [(114, -22), (114, -34), (118, -35), (124, -33), (131, -31.5), (135, -35), (138, -34), (140, -38),
                  (146, -39), (150, -37), (153, -31), (153, -25), (146, -19), (145, -15), (142, -11), (141, -17),
                  (136, -12), (130, -11), (126, -14), (122, -17)],
    "nz": [(172, -35), (178, -38), (175, -41), (171, -44), (167, -46), (170, -42), (174, -39)],
}
WATER = {"blacksea": [(28, 41), (28, 46), (32, 46), (37, 47), (41, 42), (36, 41.5)],
         "caspian": [(47, 37), (49, 46), (53, 47), (54, 41), (53, 37)]}
DESERT = [
    [(-16, 18), (-10, 28), (0, 30), (10, 32), (20, 30), (32, 29), (35, 24), (33, 15), (20, 14), (5, 15), (-10, 15)],
    [(36, 29), (48, 29), (55, 24), (55, 18), (45, 15), (40, 20)],
    [(16, -19), (26, -20), (26, -28), (18, -28)],
    [(118, -20), (138, -20), (140, -28), (132, -31), (120, -30)],
    [(88, 38), (112, 40), (110, 45), (95, 46)],
    [(-118, 31), (-104, 31), (-105, 38), (-117, 40)],
    [(52, 37), (70, 37), (76, 44), (56, 47)],
    [(-72, -18), (-68, -18), (-66, -28), (-70, -30)],
]
FOREST = [  # deep-green regions
    [(-78, 2), (-50, 2), (-40, -8), (-50, -15), (-70, -14), (-77, -6)],
    [(10, 4), (30, 4), (30, -8), (14, -6)],
    [(95, 20), (108, 20), (112, -2), (100, 0)],
    [(30, 55), (90, 58), (140, 60), (130, 66), (60, 66), (30, 62)],
    [(-125, 50), (-60, 50), (-70, 58), (-120, 60)],
]
ICE = [CONT["greenland"]]

C_OCEAN_LIT = hexc("#3fa6e8")
C_OCEAN = hexc("#1f6fc6")
C_OCEAN_DEEP = hexc("#123f8c")
C_LAND = hexc("#5dbb4c")
C_LAND_DARK = hexc("#3f9a3a")
C_FOREST = hexc("#2f8a3a")
C_DESERT = hexc("#e3c27a")
C_ICE = hexc("#f4f8fb")


def _densify(poly, step=2.0):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        d = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        k = max(1, int(d / step))
        for j in range(k):
            u = j / k
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


_DENSE = {}


def _dense(key, poly):
    if key not in _DENSE:
        _DENSE[key] = _densify(poly)
    return _DENSE[key]


def project(lon, lat, lon0, lat0):
    la, lo = math.radians(lat), math.radians(lon - lon0)
    p0 = math.radians(lat0)
    x = math.cos(la) * math.sin(lo)
    y = math.cos(p0) * math.sin(la) - math.sin(p0) * math.cos(la) * math.cos(lo)
    c = math.sin(p0) * math.sin(la) + math.cos(p0) * math.cos(la) * math.cos(lo)
    if c < 0:  # behind the horizon: push to the limb
        r = math.hypot(x, y) or 1
        x, y = x / r, y / r
    return x, -y, c


def _path(cx, poly, lon0, lat0, R, ox, oy):
    pts = []
    vis = False
    for lon, lat in poly:
        x, y, c = project(lon, lat, lon0, lat0)
        vis = vis or c > 0
        pts.append((ox + x * R, oy + y * R))
    if not vis:
        return False
    smooth_poly(cx, pts, close=True, k=0.6)
    return True


def draw_globe(cx, ox, oy, R, lon0=15.0, lat0=22.0, gloss=True, shade_amt=1.0):
    """Draw the globe disc centred at (ox, oy) radius R (caller may pre-scale for an ellipse)."""
    cx.save()
    cx.new_path()
    cx.arc(ox, oy, R, 0, 2 * math.pi)
    cx.clip()
    g = cairo.RadialGradient(ox - R * 0.35, oy - R * 0.4, R * 0.05, ox, oy, R * 1.05)
    g.add_color_stop_rgba(0, *C_OCEAN_LIT)
    g.add_color_stop_rgba(0.55, *C_OCEAN)
    g.add_color_stop_rgba(1, *C_OCEAN_DEEP)
    cx.set_source(g)
    cx.paint()
    # land with soft dark rim (fondant thickness)
    for k, poly in CONT.items():
        d = _dense(k, poly)
        cx.save()
        cx.translate(R * 0.012, R * 0.018)
        if _path(cx, d, lon0, lat0, R, ox, oy):
            src(cx, (0.05, 0.2, 0.35, 0.35))
            cx.fill()
        cx.restore()
        if _path(cx, d, lon0, lat0, R, ox, oy):
            g = cairo.LinearGradient(ox - R, oy - R, ox + R, oy + R)
            g.add_color_stop_rgba(0, *C_LAND)
            g.add_color_stop_rgba(1, *C_LAND_DARK)
            cx.set_source(g)
            cx.fill_preserve()
            cx.set_source_rgba(1, 1, 1, 0.25)
            cx.set_line_width(R * 0.006)
            cx.stroke()
    for i, poly in enumerate(FOREST):
        if _path(cx, _dense(("f", i), poly), lon0, lat0, R, ox, oy):
            src(cx, C_FOREST, 0.55)
            cx.fill()
    for i, poly in enumerate(DESERT):
        if _path(cx, _dense(("d", i), poly), lon0, lat0, R, ox, oy):
            src(cx, C_DESERT, 0.92)
            cx.fill()
    for i, poly in enumerate(ICE):
        if _path(cx, _dense(("i", i), poly), lon0, lat0, R, ox, oy):
            src(cx, C_ICE, 0.9)
            cx.fill()
    for k, poly in WATER.items():
        if _path(cx, _dense(("w", k), poly), lon0, lat0, R, ox, oy):
            src(cx, C_OCEAN)
            cx.fill()
    # arctic cap
    cap = [(lon, 80) for lon in range(-180, 180, 10)]
    if _path(cx, _dense("cap", cap), lon0, lat0, R, ox, oy):
        src(cx, C_ICE, 0.85)
        cx.fill()
    # sphere shading
    if shade_amt > 0:
        g = cairo.RadialGradient(ox - R * 0.3, oy - R * 0.35, R * 0.2, ox, oy, R)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
        g.add_color_stop_rgba(0.7, 0, 0.05, 0.2, 0.08 * shade_amt)
        g.add_color_stop_rgba(1, 0, 0.03, 0.15, 0.45 * shade_amt)
        cx.set_source(g)
        cx.paint()
    if gloss:
        g = cairo.RadialGradient(ox - R * 0.38, oy - R * 0.42, 0, ox - R * 0.38, oy - R * 0.42, R * 0.55)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.38)
        g.add_color_stop_rgba(1, 1, 1, 1, 0.0)
        cx.set_source(g)
        cx.paint()
    cx.restore()


# ---------------------------------------------------------------- cached, feathered texture
_TEX = {}


def _surf(n):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)


def _blur(surf, radius):
    import numpy as np
    from PIL import Image, ImageFilter
    w, h = surf.get_width(), surf.get_height()
    surf.flush()
    a = np.ndarray((h, w, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1)).copy()
    im = Image.fromarray(a, "RGBA").filter(ImageFilter.GaussianBlur(radius))
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    b = np.ndarray((h, w, 4), np.uint8, out.get_data(), strides=(out.get_stride(), 4, 1))
    b[:] = np.asarray(im)
    out.mark_dirty()
    return out


def globe_texture(R, lon0=15.0, lat0=22.0, gloss=True):
    """Return a cairo surface (2R x 2R) of the globe. Cached by rounded longitude."""
    key = (int(R), round(lon0 * 4) / 4, round(lat0, 1), gloss)
    if key in _TEX:
        return _TEX[key]
    lon0, lat0 = key[1], key[2]
    n = int(2 * R) + 2
    o = n / 2
    base = _surf(n)
    c = cairo.Context(base)
    c.arc(o, o, R, 0, 2 * math.pi)
    c.clip()
    g = cairo.RadialGradient(o - R * 0.35, o - R * 0.4, R * 0.05, o, o, R * 1.05)
    g.add_color_stop_rgba(0, *C_OCEAN_LIT)
    g.add_color_stop_rgba(0.55, *C_OCEAN)
    g.add_color_stop_rgba(1, *C_OCEAN_DEEP)
    c.set_source(g)
    c.paint()
    # shallow-water halo around coasts
    halo = _surf(n)
    hc = cairo.Context(halo)
    for k, poly in CONT.items():
        if _path(hc, _dense(k, poly), lon0, lat0, R, o, o):
            hc.set_source_rgba(0.45, 0.85, 0.95, 0.75)
            hc.set_line_width(R * 0.03)
            hc.stroke_preserve()
            hc.fill()
    c.set_source_surface(_blur(halo, R * 0.02), 0, 0)
    c.paint_with_alpha(0.55)
    # land mask
    land = _surf(n)
    lc = cairo.Context(land)
    for k, poly in CONT.items():
        if _path(lc, _dense(k, poly), lon0, lat0, R, o, o):
            lc.set_source_rgba(1, 1, 1, 1)
            lc.fill()
    # land colour layer
    col = _surf(n)
    cc = cairo.Context(col)
    g = cairo.LinearGradient(o - R, o - R, o + R, o + R)
    g.add_color_stop_rgba(0, *C_LAND)
    g.add_color_stop_rgba(1, *C_LAND_DARK)
    cc.set_source(g)
    cc.paint()
    ov = _surf(n)
    oc = cairo.Context(ov)
    for i, poly in enumerate(FOREST):
        if _path(oc, _dense(("f", i), poly), lon0, lat0, R, o, o):
            src(oc, C_FOREST, 0.75)
            oc.fill()
    for i, poly in enumerate(DESERT):
        if _path(oc, _dense(("d", i), poly), lon0, lat0, R, o, o):
            src(oc, C_DESERT, 1.0)
            oc.fill()
    cc.set_source_surface(_blur(ov, R * 0.035), 0, 0)
    cc.paint()
    for i, poly in enumerate(ICE):
        if _path(cc, _dense(("i", i), poly), lon0, lat0, R, o, o):
            src(cc, C_ICE, 0.95)
            cc.fill()
    # drop shadow of the fondant land
    sh = _blur(land, R * 0.012)
    c.save()
    c.translate(R * 0.01, R * 0.016)
    c.set_source_rgba(0.03, 0.15, 0.3, 0.5)
    c.mask_surface(sh, 0, 0)
    c.restore()
    c.set_source_surface(col, 0, 0)
    c.mask_surface(land, 0, 0)
    for k, poly in WATER.items():
        if _path(c, _dense(("w", k), poly), lon0, lat0, R, o, o):
            src(c, C_OCEAN)
            c.fill()
    cap = [(lon, 80) for lon in range(-180, 180, 10)]
    if _path(c, _dense("cap", cap), lon0, lat0, R, o, o):
        src(c, C_ICE, 0.85)
        c.fill()
    # sugar-icing cloud wisps
    import random
    rnd = random.Random(7)
    for _ in range(14):
        lon = rnd.uniform(-180, 180)
        lat = rnd.uniform(-55, 60)
        x, y, vis = project(lon, lat, lon0, lat0)
        if vis < 0.15:
            continue
        c.save()
        c.translate(o + x * R, o + y * R)
        c.scale(1.0, 0.35 + 0.3 * vis)
        for j in range(3):
            c.arc(j * R * 0.04, rnd.uniform(-1, 1) * R * 0.01, R * rnd.uniform(0.018, 0.03), 0, 2 * math.pi)
            c.set_source_rgba(1, 1, 1, 0.55)
            c.fill()
        c.restore()
    g = cairo.RadialGradient(o - R * 0.3, o - R * 0.35, R * 0.2, o, o, R)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
    g.add_color_stop_rgba(0.7, 0, 0.05, 0.2, 0.08)
    g.add_color_stop_rgba(1, 0, 0.03, 0.15, 0.42)
    c.set_source(g)
    c.paint()
    if gloss:
        g = cairo.RadialGradient(o - R * 0.38, o - R * 0.42, 0, o - R * 0.38, o - R * 0.42, R * 0.55)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.35)
        g.add_color_stop_rgba(1, 1, 1, 1, 0.0)
        c.set_source(g)
        c.paint()
    if len(_TEX) > 40:
        _TEX.clear()
    _TEX[key] = base
    return base

"""Portrait icons (ancestors, modern people) and the Just Needy protagonist.

Ancestor portraits follow the reference infographic: a light circular badge with a
coloured ring, head-and-shoulders avatar inside. Just Needy follows the official
character sheet: round white head, black oval eyes, simple smile, no hair,
blue hoodie with the hood down, white drawstrings, black stick legs.
"""
import math
import random

import cairo

from cinecode.core import circle, ellipse, fs, hexc, line, rgrad, shade, src

INK = hexc("#151519")
JN_BLUE = hexc("#2F5FE0")
JN_BLUE_DK = hexc("#1F45B5")
JN_BLUE_LT = hexc("#4C7DF0")

SKIN = [hexc(c) for c in ("#F6D7C3", "#EFC3A4", "#E0A97E", "#C98B5E", "#A86B43", "#8A5235", "#6B3E26", "#F1CBB0")]
HAIR = [hexc(c) for c in ("#2A1C14", "#4A2E1C", "#121212", "#7A4A28", "#B8833E", "#D9D2C5", "#9C9C9C", "#5A3420")]
SHIRT = [hexc(c) for c in ("#3A7BD5", "#E4567B", "#3CB371", "#F2A93B", "#8E6FD8", "#2BB3B1", "#E06B3A", "#5C6B7A")]

RING_M = hexc("#4F8DFF")
RING_F = hexc("#FF6FA8")
GOLD = hexc("#FFD23F")


class Spec:
    def __init__(self, seed, female=None, age=None, ancient=False):
        r = random.Random(seed)
        self.seed = seed
        self.female = r.random() < 0.5 if female is None else female
        self.age = r.choice(["young", "adult", "adult", "old"]) if age is None else age
        self.ancient = ancient
        if ancient:
            self.skin = r.choice(SKIN[3:7])
            self.hair_c = r.choice([HAIR[0], HAIR[2], HAIR[1]])
            self.shirt = r.choice([hexc("#8B5A3C"), hexc("#A0703F"), hexc("#6E4B33"), hexc("#B07D4F")])
        else:
            self.skin = r.choice(SKIN)
            self.hair_c = HAIR[6] if self.age == "old" and r.random() < 0.8 else r.choice(HAIR[:6])
            if self.age == "old" and r.random() < 0.5:
                self.hair_c = HAIR[5]
            self.shirt = r.choice(SHIRT)
        if self.female:
            self.hair = r.choice(["long", "bob", "bun", "long", "scarf"] if not ancient else ["long", "curly", "bun"])
        else:
            self.hair = r.choice(["short", "short", "side", "bald", "curly"] if not ancient else ["curly", "short", "curly"])
        self.beard = (not self.female) and r.random() < (0.35 if not ancient else 0.5)
        self.glasses = (not ancient) and r.random() < (0.35 if self.age == "old" else 0.12)
        self.scarf_c = r.choice([hexc("#3C8D7A"), hexc("#7D4CA0"), hexc("#C0455A"), hexc("#2E6BA8")])

    @property
    def ring(self):
        return RING_F if self.female else RING_M


def _face(cx, sp, R):
    """Draw head & shoulders centred at origin, badge radius R (clip already applied)."""
    skin = sp.skin
    out = shade(skin, -0.45)
    lw = R * 0.035
    # shoulders / shirt
    cx.move_to(-R * 0.95, R * 1.05)
    cx.curve_to(-R * 0.9, R * 0.55, -R * 0.5, R * 0.42, 0, R * 0.42)
    cx.curve_to(R * 0.5, R * 0.42, R * 0.9, R * 0.55, R * 0.95, R * 1.05)
    cx.close_path()
    fs(cx, sp.shirt, shade(sp.shirt, -0.35), lw)
    # neck
    cx.rectangle(-R * 0.14, R * 0.18, R * 0.28, R * 0.3)
    fs(cx, shade(skin, -0.12), None, 0)
    ellipse(cx, 0, R * 0.44, R * 0.17, R * 0.07)
    fs(cx, shade(skin, -0.12), None, 0)
    hx, hy, hr = 0, -R * 0.12, R * 0.36
    hc = sp.hair_c
    # hair behind head
    if sp.hair in ("long",):
        cx.move_to(-hr * 1.15, hy)
        cx.curve_to(-hr * 1.3, hy + hr * 1.4, -hr * 0.9, hy + hr * 1.75, -hr * 0.6, hy + hr * 1.65)
        cx.line_to(hr * 0.6, hy + hr * 1.65)
        cx.curve_to(hr * 0.9, hy + hr * 1.75, hr * 1.3, hy + hr * 1.4, hr * 1.15, hy)
        cx.close_path()
        fs(cx, hc, shade(hc, -0.3), lw)
    if sp.hair == "bun":
        circle(cx, hx, hy - hr * 1.15, hr * 0.42)
        fs(cx, hc, shade(hc, -0.3), lw)
    if sp.hair == "scarf":
        ellipse(cx, hx, hy + hr * 0.15, hr * 1.32, hr * 1.42)
        fs(cx, sp.scarf_c, shade(sp.scarf_c, -0.3), lw)
        cx.move_to(-hr * 1.25, hy + hr * 0.5)
        cx.curve_to(-hr * 1.2, hy + hr * 1.9, hr * 1.2, hy + hr * 1.9, hr * 1.25, hy + hr * 0.5)
        fs(cx, sp.scarf_c, shade(sp.scarf_c, -0.3), lw)
    # ears
    for s in (-1, 1):
        ellipse(cx, hx + s * hr * 0.98, hy + hr * 0.1, hr * 0.16, hr * 0.22)
        fs(cx, skin, out, lw * 0.8)
    # head
    ellipse(cx, hx, hy, hr, hr * 1.1)
    fs(cx, skin, out, lw)
    # beard
    if sp.beard:
        cx.move_to(-hr * 0.92, hy + hr * 0.05)
        cx.curve_to(-hr * 0.9, hy + hr * 1.25, hr * 0.9, hy + hr * 1.25, hr * 0.92, hy + hr * 0.05)
        cx.curve_to(hr * 0.6, hy + hr * 0.6, -hr * 0.6, hy + hr * 0.6, -hr * 0.92, hy + hr * 0.05)
        fs(cx, hc, None, 0)
    # hair on top
    if sp.hair != "scarf":
        if sp.hair == "bald":
            cx.arc(hx, hy, hr * 1.02, math.pi * 1.0, math.pi * 1.12)
            cx.arc_negative(hx, hy, hr * 0.85, math.pi * 1.12, math.pi * 1.0)
            fs(cx, hc, None, 0)
            cx.arc(hx, hy, hr * 1.02, math.pi * 1.88, math.pi * 2.0)
            cx.arc_negative(hx, hy, hr * 0.85, math.pi * 2.0, math.pi * 1.88)
            fs(cx, hc, None, 0)
        elif sp.hair == "curly":
            rr = random.Random(sp.seed)
            for k in range(11):
                a = math.pi * (1.0 + k / 10)
                circle(cx, hx + math.cos(a) * hr * 0.95, hy + math.sin(a) * hr * 1.0 - hr * 0.05, hr * (0.28 + rr.random() * 0.06))
                fs(cx, hc, None, 0)
            ellipse(cx, hx, hy - hr * 0.55, hr * 0.9, hr * 0.45)
            fs(cx, hc, None, 0)
        else:
            cx.move_to(-hr * 1.04, hy + hr * (0.1 if sp.hair in ("long", "bob") else -0.05))
            cx.curve_to(-hr * 1.15, hy - hr * 1.35, hr * 1.15, hy - hr * 1.35, hr * 1.04, hy + hr * (0.1 if sp.hair in ("long", "bob") else -0.05))
            if sp.hair == "side":
                cx.curve_to(hr * 0.7, hy - hr * 0.55, -hr * 0.2, hy - hr * 0.7, -hr * 0.75, hy - hr * 0.35)
            else:
                cx.curve_to(hr * 0.6, hy - hr * 0.5, -hr * 0.6, hy - hr * 0.5, -hr * 1.04, hy + hr * (0.1 if sp.hair in ("long", "bob") else -0.05))
            cx.close_path()
            fs(cx, hc, shade(hc, -0.3), lw * 0.8)
            if sp.hair == "bob":
                for s in (-1, 1):
                    cx.move_to(s * hr * 1.04, hy)
                    cx.curve_to(s * hr * 1.2, hy + hr * 0.6, s * hr * 1.05, hy + hr * 0.9, s * hr * 0.8, hy + hr * 0.95)
                    cx.line_to(s * hr * 0.9, hy)
                    fs(cx, hc, None, 0)
    # face
    ey = hy + hr * 0.08
    for s in (-1, 1):
        ellipse(cx, hx + s * hr * 0.36, ey, hr * 0.085, hr * 0.11)
        fs(cx, hexc("#231A16"), None, 0)
        line(cx, [(hx + s * hr * 0.22, ey - hr * 0.26), (hx + s * hr * 0.5, ey - hr * 0.28)],
             shade(sp.hair_c if sp.hair != "bald" else out, -0.1), hr * 0.07)
    if sp.age == "old":
        for s in (-1, 1):
            line(cx, [(hx + s * hr * 0.55, ey + hr * 0.12), (hx + s * hr * 0.66, ey + hr * 0.2)], shade(skin, -0.3), hr * 0.03)
    if sp.glasses:
        for s in (-1, 1):
            circle(cx, hx + s * hr * 0.36, ey, hr * 0.22)
            fs(cx, None, hexc("#2B2B33"), hr * 0.05)
        line(cx, [(hx - hr * 0.14, ey), (hx + hr * 0.14, ey)], hexc("#2B2B33"), hr * 0.05)
    # nose + mouth
    line(cx, [(hx, ey + hr * 0.12), (hx - hr * 0.06, ey + hr * 0.3), (hx + hr * 0.04, ey + hr * 0.32)], shade(skin, -0.3), hr * 0.04)
    cx.arc(hx, ey + hr * 0.36, hr * 0.24, math.pi * 0.2, math.pi * 0.8)
    src(cx, hexc("#7A3328") if not sp.beard else hexc("#F2E6E0"))
    cx.set_line_width(hr * 0.07)
    cx.stroke()
    if sp.female and not sp.ancient:
        for s in (-1, 1):
            ellipse(cx, hx + s * hr * 0.55, ey + hr * 0.32, hr * 0.12, hr * 0.07)
            src(cx, hexc("#FF8A8A"), 0.45)
            cx.fill()


def _jn_bust(cx, R):
    """Just Needy head-and-shoulders inside badge radius R."""
    lw = R * 0.045
    # hoodie shoulders
    cx.move_to(-R * 1.0, R * 1.1)
    cx.curve_to(-R * 0.95, R * 0.58, -R * 0.62, R * 0.44, 0, R * 0.44)
    cx.curve_to(R * 0.62, R * 0.44, R * 0.95, R * 0.58, R * 1.0, R * 1.1)
    cx.close_path()
    fs(cx, JN_BLUE, INK, lw)
    # hood bunched behind the neck (hood down)
    cx.move_to(-R * 0.42, R * 0.47)
    cx.curve_to(-R * 0.4, R * 0.28, R * 0.4, R * 0.28, R * 0.42, R * 0.47)
    cx.curve_to(R * 0.2, R * 0.62, -R * 0.2, R * 0.62, -R * 0.42, R * 0.47)
    fs(cx, JN_BLUE_DK, INK, lw * 0.9)
    # neck
    cx.rectangle(-R * 0.07, R * 0.26, R * 0.14, R * 0.24)
    fs(cx, hexc("#FFFFFF"), INK, lw * 0.7)
    # drawstrings
    for s in (-1, 1):
        line(cx, [(s * R * 0.12, R * 0.56), (s * R * 0.14, R * 0.95)], hexc("#F4F4F4"), R * 0.045)
    # head: big white circle
    hy, hr = -R * 0.12, R * 0.42
    circle(cx, 0, hy, hr)
    fs(cx, hexc("#FFFFFF"), INK, lw)
    # eyes: black ovals
    for s in (-1, 1):
        ellipse(cx, s * hr * 0.3, hy - hr * 0.12, hr * 0.085, hr * 0.15)
        fs(cx, INK, None, 0)
    # smile
    cx.arc(0, hy + hr * 0.08, hr * 0.38, math.pi * 0.22, math.pi * 0.78)
    src(cx, INK)
    cx.set_line_width(hr * 0.07)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()


_CACHE = {}
BADGE_PX = 192  # cached badge raster size


def badge_surface(kind, spec=None, ring=None, bg=None):
    key = (kind, spec.seed if spec else None, ring, bg)
    if key in _CACHE:
        return _CACHE[key]
    S = BADGE_PX
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    cx = cairo.Context(surf)
    cx.translate(S / 2, S / 2)
    R = S / 2 - 2
    ring_c = ring or (GOLD if kind == "jn" else spec.ring)
    inner = R * 0.86
    circle(cx, 0, 0, R)
    fs(cx, ring_c, None, 0)
    circle(cx, 0, 0, inner + R * 0.04)
    fs(cx, hexc("#FFFFFF"), None, 0)
    if bg is None:
        bg = hexc("#FFF3C4") if kind == "jn" else (hexc("#FFE3EE") if spec.female else hexc("#E2EDFF"))
    cx.save()
    circle(cx, 0, 0, inner)
    cx.clip()
    cx.set_source(rgrad(cx, 0, -inner * 0.3, 0, inner * 1.2, [(0, shade(bg, 0.4)), (1, bg)]))
    cx.paint()
    if kind == "jn":
        _jn_bust(cx, inner)
    else:
        _face(cx, spec, inner)
    cx.restore()
    _CACHE[key] = surf
    return surf


def draw_badge(cx, x, y, r, kind="person", spec=None, alpha=1.0, ring=None, glow=None, glow_a=1.0, shadow=True):
    if r <= 0.5 or alpha <= 0.003:
        return
    if glow is not None:
        cx.set_source(rgrad(cx, x, y, r * 0.8, r * 2.2, [(0, (*glow[:3], 0.55 * glow_a * alpha)), (1, (*glow[:3], 0))]))
        circle(cx, x, y, r * 2.2)
        cx.fill()
    if shadow and r > 6:
        circle(cx, x, y + r * 0.08, r * 1.02)
        src(cx, (0, 0, 0, 0.35 * alpha))
        cx.fill()
    surf = badge_surface(kind, spec, ring)
    cx.save()
    cx.translate(x - r, y - r)
    k = 2 * r / BADGE_PX
    cx.scale(k, k)
    cx.set_source_surface(surf, 0, 0)
    cx.get_source().set_filter(cairo.FILTER_GOOD)
    cx.paint_with_alpha(alpha)
    cx.restore()


# ------------------------------------------------------------------ full body Just Needy
def draw_jn_full(cx, x, y, h, t=0.0, alpha=1.0, wave=0.0):
    """Front view, standing, hands in hoodie pocket. (x, y) = point between the feet; h = total height."""
    if alpha <= 0.003:
        return
    k = h / 600.0
    cx.push_group()
    cx.save()
    cx.translate(x, y)
    cx.scale(k, k)
    bob = math.sin(t * 2.2) * 2.0
    lw = 5.0
    # legs
    for s in (-1, 1):
        line(cx, [(s * 22, -250), (s * 24, -18)], INK, 13)
        ellipse(cx, s * 30, -10, 22, 10)
        fs(cx, INK, None, 0)
    cx.translate(0, bob)
    # hood behind neck
    ellipse(cx, 0, -432, 62, 26)
    fs(cx, JN_BLUE_DK, INK, lw)
    # torso hoodie (rounded shoulders, slight taper)
    def torso():
        cx.move_to(-70, -246)
        cx.curve_to(-74, -320, -86, -390, -84, -418)
        cx.curve_to(-82, -444, -60, -452, -36, -452)
        cx.line_to(36, -452)
        cx.curve_to(60, -452, 82, -444, 84, -418)
        cx.curve_to(86, -390, 74, -320, 70, -246)
        cx.curve_to(70, -236, 64, -232, 54, -232)
        cx.line_to(-54, -232)
        cx.curve_to(-64, -232, -70, -236, -70, -246)
        cx.close_path()
    torso()
    fs(cx, JN_BLUE, INK, lw)
    cx.save()
    torso()
    cx.clip()
    cx.rectangle(-90, -258, 180, 30)
    src(cx, JN_BLUE_DK)
    cx.fill()
    cx.rectangle(16, -450, 70, 192)
    src(cx, JN_BLUE_LT, 0.35)
    cx.fill()
    cx.restore()
    line(cx, [(-71, -258), (71, -258)], INK, 3)
    # neck opening: bunched hood collar
    cx.move_to(-40, -452)
    cx.curve_to(-30, -430, 30, -430, 40, -452)
    fs(cx, None, INK, 3.5)
    # sleeves going into pocket
    for s in (-1, 1):
        cx.move_to(s * 78, -430)
        cx.curve_to(s * 104, -400, s * 100, -330, s * 64, -306)
        cx.line_to(s * 40, -300)
        cx.curve_to(s * 66, -330, s * 72, -380, s * 66, -410)
        fs(cx, JN_BLUE, INK, lw)
    # kangaroo pocket
    cx.move_to(-56, -272)
    cx.line_to(-44, -326)
    cx.line_to(44, -326)
    cx.line_to(56, -272)
    fs(cx, None, shade(JN_BLUE_DK, -0.2), 4)
    # drawstrings
    for s in (-1, 1):
        line(cx, [(s * 12, -444), (s * 14, -386)], hexc("#F4F4F4"), 5)
    # neck
    cx.rectangle(-8, -470, 16, 26)
    fs(cx, hexc("#FFFFFF"), INK, 4)
    # head
    hy = -530 + math.sin(t * 2.2 + 0.4) * 1.5
    circle(cx, 0, hy, 72)
    fs(cx, hexc("#FFFFFF"), INK, lw + 0.5)
    blink = 1.7 < (t % 3.4) < 1.81
    for s in (-1, 1):
        if blink:
            line(cx, [(s * 22 - 7, hy - 8), (s * 22 + 7, hy - 8)], INK, 4)
        else:
            ellipse(cx, s * 22, hy - 8, 6.5, 11)
            fs(cx, INK, None, 0)
    cx.arc(0, hy + 6, 28, math.pi * 0.22, math.pi * 0.78)
    src(cx, INK)
    cx.set_line_width(5)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)

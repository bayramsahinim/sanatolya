"""Scenes 2-6 on the floating island: land, trees, birds & chickens, gold, ants."""
import math

import cairo

from cinecode.core import back_out, ease_in, ease_io, ease_out, kf, prog, smooth
from episodes.everything_divided import art_island as A
from episodes.everything_divided.common import (H, W, WHITE, YELLOW, L0, L1, header, pill, word_t, word_end)

I = A.ISLAND
HX, HY = I.S(*I.HERO_UV)

# ------------------------------------------------------------------ key times
T_IN = L0("land1") - 0.3
T_F1 = word_t("land2", "about")
T_F2 = word_t("land2", "two")
T_F3 = word_t("land2", "half")
T_TREE_Q = L0("tree1")
T_TREE_3T = word_t("tree2", "three")
T_TREE_GROW0 = L0("tree3") - 0.2
T_TREE_GROW1 = word_end("tree3", "trees") - 0.1
T_BIRDS = L0("bird1")
T_SIX = word_t("bird2", "six")
T_CHICK = word_t("bird2", "three")
T_GOLD_Q = L0("gold1")
T_CUBE = L0("gold2")
T_27 = word_t("gold2", "about")
T_OUNCE = L0("gold3")
T_SURPRISE = L0("ant1")
T_ANTS = word_t("ant1", "Ants")
T_ANT2 = L0("ant2")
T_MILLION = word_end("ant2", "ants", 1)
T_STAR = L0("star1")

CHICKENS = [(-160, 215, 1, 0), (85, 205, -1, 1), (-95, 268, 1, 2)]
BAR_UV = (20, 185)
BAR_S = 0.24


def trees_grown(t):
    early = 0.016 * smooth(prog(t, T_TREE_3T, T_TREE_3T + 1.0))     # first sprouts
    main = smooth(prog(t, T_TREE_GROW0, T_TREE_GROW1)) ** 0.9
    return max(early, main)


def tree_count(t):
    return int(round(trees_grown(t) * 375))


def bird_pos(k, t, t_in):
    """Six wild birds: fly in from the sides, then loop above the forest."""
    side = -1 if k % 2 == 0 else 1
    cx0 = 540 + (k - 2.5) * 125
    cy0 = 640 + (k % 3) * 55
    x = cx0 + math.sin(t * 0.9 + k * 1.3) * 70
    y = cy0 + math.sin(t * 1.4 + k * 2.1) * 30
    u = ease_out(prog(t, t_in + k * 0.12, t_in + k * 0.12 + 1.1))
    x = x + (1 - u) * side * 760
    y = y - (1 - u) * 160
    vx = math.cos(t * 0.9 + k * 1.3)
    facing = 1 if (vx > 0 if u >= 1 else side < 0) else -1
    return x, y, facing, u


def world(cx, t, P):
    """Draw the island and everything on it (camera already applied).
    P keys: rise, fields(list), field_alpha, badges(list), trees, birds_t, chick(list), bar, glint,
            hero(dict), cube(dict or None)"""
    rise = P.get("rise", 0.0)
    cx.save()
    cx.translate(0, rise)
    I.draw_base(cx)
    I.draw_fields(cx, P.get("fields", [1, 1, 1]), P.get("field_alpha", 1.0))
    items = []
    # hero
    hp = P.get("hero", {})
    items.append((I.HERO_UV[1], lambda c: A.hero(c, t, HX, HY, 0.3, **hp)))
    # chickens
    for (u, v, f, k), a in zip(CHICKENS, P.get("chick", [0, 0, 0])):
        if a <= 0:
            continue
        x, y = I.S(u, v)
        drop = (1 - ease_out(a)) * -120
        items.append((v, lambda c, x=x, y=y, f=f, k=k, a=a, drop=drop:
                      A.chicken(c, x, y + drop, 0.82 * back_out(min(1, a * 1.4)), t, k, f, min(1, a * 2))))
    # gold bar
    if P.get("bar", 0) > 0:
        bx, by = I.S(*BAR_UV)
        b = P["bar"]
        items.append((BAR_UV[1], lambda c: A.gold_bar(c, bx, by, BAR_S * back_out(b), t, P.get("glint", 0))))
    A.draw_trees(cx, t, P.get("trees", 0.0), items)
    # badges for the fields
    if any(x > 0 for x in P.get("badges", [])):
        I.field_badges(cx, P["badges"])
    cx.restore()
    # birds
    if P.get("birds_t") is not None:
        for k in range(6):
            x, y, f, u = bird_pos(k, t, P["birds_t"])
            if u > 0:
                A.bird(cx, x, y + rise, 1.3, t, k, f)
    if P.get("cube"):
        c = P["cube"]
        A.gold_cube(cx, c["x"], c["y"], c["size"], t, c.get("alpha", 1.0))


def state(t):
    P = {}
    P["rise"] = (1 - ease_out(prog(t, T_IN, T_IN + 1.0))) * 1100
    P["fields"] = [back_out(prog(t, T_F1, T_F1 + 0.45)), back_out(prog(t, T_F2, T_F2 + 0.45)),
                   back_out(prog(t, T_F3, T_F3 + 0.45))]
    P["badges"] = [prog(t, T_F1 + 0.1, T_F1 + 0.5), prog(t, T_F2 + 0.1, T_F2 + 0.5), prog(t, T_F3 + 0.1, T_F3 + 0.5)]
    fade_b = 1 - smooth(prog(t, T_TREE_Q - 0.3, T_TREE_Q + 0.2))
    P["badges"] = [b * fade_b for b in P["badges"]]
    P["trees"] = trees_grown(t)
    P["field_alpha"] = 1.0 - 0.35 * smooth(prog(t, T_TREE_GROW0, T_TREE_GROW1))
    P["birds_t"] = T_BIRDS if t >= T_BIRDS else None
    P["chick"] = [prog(t, T_CHICK + 0.15 * k, T_CHICK + 0.15 * k + 0.5) for k in range(3)]
    P["bar"] = prog(t, T_27 + 0.55, T_27 + 0.95)
    P["glint"] = smooth(prog(t, T_27 + 0.8, T_27 + 1.2))
    # hero acting
    look = (0, 0)
    mood = "smile"
    eyes = "open"
    if T_TREE_GROW0 < t < L1("tree4") + 0.3:
        look = (math.sin(t * 1.3) * 0.6, -0.4)
        mood = "grin"
    if T_BIRDS < t < T_GOLD_Q:
        look = (math.sin(t * 2.0) * 0.8, -0.8)
    if T_27 + 0.5 < t < L1("gold3") + 0.3:
        look = (0.6, 0.7)
        mood = "o" if t < T_27 + 1.6 else "grin"
    if T_ANTS < t < T_STAR:
        mood = "o"
        look = (0.7, 0.4)
    P["hero"] = {"mood": mood, "look": look}
    # gold cube: drops in, then shrinks onto your patch
    if T_CUBE - 0.1 < t < T_27 + 0.7:
        d = back_out(prog(t, T_CUBE - 0.1, T_CUBE + 0.5), 1.0)
        sh = ease_in(prog(t, T_27 - 0.05, T_27 + 0.65))
        bx, by = I.S(*BAR_UV)
        x = 540 + (bx - 540) * sh
        y = (-200 + (700 + 200) * d) + (by - 700) * sh
        size = 230 * (1 - sh) + 12 * sh
        P["cube"] = {"x": x - size * 0.27 * (1 - sh), "y": y, "size": size, "alpha": 1 - smooth(prog(sh, 0.85, 1))}
    return P


def camera(t):
    keys = [
        (T_IN, (540.0, 990.0, 1.0)),
        (T_TREE_GROW0, (540.0, 990.0, 1.0)),
        (T_TREE_GROW1 + 0.5, (540.0, 960.0, 1.07)),
        (T_BIRDS + 0.2, (540.0, 930.0, 1.0)),
        (T_27 + 0.1, (540.0, 930.0, 1.0)),
        (T_27 + 0.9, (HX + 25, HY - 40, 2.9)),
        (L1("gold3") + 0.15, (HX + 25, HY - 40, 3.0)),
        (T_SURPRISE + 0.6, (540.0, 960.0, 1.0)),
        (T_STAR, (540.0, 960.0, 1.0)),
    ]
    return kf(t, keys, ease_io)


# ------------------------------------------------------------------ magnifier
LENS = (700.0, 905.0, 150.0)


def lens_state(t):
    """(x, y, R, content_scale, alpha) in screen space, or None."""
    if not (T_ANTS - 0.4 < t < T_STAR + 0.2):
        return None
    sw = ease_out(prog(t, T_ANTS - 0.35, T_ANTS + 0.25))
    x0, y0, R0 = LENS
    x = x0 + (1 - sw) * 500
    y = y0 - (1 - sw) * 420
    zin = ease_in(prog(t, T_ANT2 + 0.05, T_ANT2 + 0.95))
    zout = ease_io(prog(t, T_MILLION + 0.05, T_MILLION + 0.75))
    z = zin * (1 - zout)
    R = R0 * (1 + 11 * z)
    x = x + (540 - x) * z
    y = y + (960 - y) * z
    alpha = sw * (1 - smooth(prog(t, T_STAR - 0.45, T_STAR - 0.05)))
    cs = 0.42 * (1 + 2.0 * z)
    return x, y, R, cs, alpha


def draw(cx, t):
    A.sky(cx)
    A.islets(cx, t)
    A.clouds(cx, t)
    fx, fy, z = camera(t)
    cx.save()
    cx.translate(W / 2, 960)
    cx.scale(z, z)
    cx.translate(-fx, -fy)
    P = state(t)
    world(cx, t, P)
    cx.restore()
    A.clouds(cx, t, front=True)
    # 'YOU' tag over the mascot while the land is introduced
    ya = smooth(prog(t, T_IN + 0.9, T_IN + 1.2)) * (1 - smooth(prog(t, T_TREE_GROW0, T_TREE_GROW0 + 0.3)))
    if ya > 0:
        A.you_tag(cx, W / 2 + (HX - fx) * z, 960 + (HY - 108 - fy) * z + (1 - ya) * -20, ya)
    # gold label in the close-up
    if T_27 + 0.8 < t < L1("gold3") + 0.25:
        bx, by = I.S(*BAR_UV)
        sx = W / 2 + (bx - fx) * z
        sy = 960 + (by - fy) * z
        al = smooth(prog(t, T_27 + 0.8, T_27 + 1.1)) * (1 - smooth(prog(t, L1("gold3"), L1("gold3") + 0.25)))
        lab = "27 g" if t < T_OUNCE else "27 g ≈ 0.87 oz"
        pill(cx, sx + 20, sy - 120, lab, size=40, alpha=al, scale=0.9 + 0.1 * al)
        cx.move_to(sx + 10, sy - 92)
        cx.line_to(sx + 6, sy - 40)
        cx.set_source_rgba(1, 1, 1, 0.85 * al)
        cx.set_line_width(4)
        cx.stroke()
    ls = lens_state(t)
    if ls:
        x, y, R, cs, al = ls
        A.magnifier(cx, x, y, R, ang=0.75, alpha=al,
                    content=lambda c: A.ground_closeup(c, t, x, y, cs))
    # ------------------------------------------------------------ header
    def tree_counter(tt):
        return f"{tree_count(tt)} TREES"

    def ant_counter(tt):
        u = smooth(prog(tt, T_ANT2 + 0.3, T_MILLION - 0.05))
        n = int(round(2_500_000 * u ** 1.6 / 1000)) * 1000
        return f"{n:,} ANTS"
    items = [
        {"t0": T_IN + 0.2, "t1": T_F1 - 0.05, "kick": "FIRST", "main": "THE LAND", "color": WHITE,
         "sub": "all of Earth's land, split 8 billion ways"},
        {"t0": T_F1 - 0.05, "t1": T_TREE_Q - 0.12, "kick": "YOUR SHARE OF LAND", "main": "ABOUT 2.5 SOCCER FIELDS",
         "sub": "~149 million km² ÷ 8 billion ≈ 18,600 m² each\nrough math - not all of it is usable land"},
        {"t0": T_TREE_Q - 0.12, "t1": T_TREE_3T - 0.05, "kick": "TREES", "main": "HOW MANY?", "color": WHITE},
        {"t0": T_TREE_3T - 0.05, "t1": T_TREE_GROW0, "kick": "TREES ON EARTH", "main": "ABOUT 3 TRILLION",
         "sub": "global estimate from forest surveys + satellite data"},
        {"t0": T_TREE_GROW0, "t1": T_BIRDS - 0.12, "kick": "YOUR FOREST", "main": tree_counter,
         "sub": "3 trillion ÷ 8 billion ≈ 375 trees each"},
        {"t0": T_BIRDS - 0.12, "t1": T_SIX - 0.05, "kick": "BIRDS", "main": "BIRDS TOO!", "color": WHITE},
        {"t0": T_SIX - 0.05, "t1": T_CHICK - 0.05, "kick": "YOUR BIRDS", "main": "6 WILD BIRDS",
         "sub": "~50 billion wild birds ÷ 8 billion"},
        {"t0": T_CHICK - 0.05, "t1": T_GOLD_Q - 0.12, "kick": "YOUR BIRDS", "main": "6 WILD BIRDS · 3 CHICKENS",
         "sub": "~50 billion wild birds · ~25 billion chickens\n÷ 8 billion (rough estimates)"},
        {"t0": T_GOLD_Q - 0.12, "t1": T_CUBE - 0.05, "kick": "GOLD", "main": "HOW MUCH?", "color": WHITE},
        {"t0": T_CUBE - 0.05, "t1": T_27 + 0.5, "kick": "ALL GOLD EVER MINED", "main": "≈ 220,000 TONNES",
         "sub": "it would fit in a cube about 22 m on each side"},
        {"t0": T_27 + 0.5, "t1": T_SURPRISE - 0.12, "kick": "YOUR SHARE", "main": "ABOUT 27 GRAMS OF GOLD",
         "sub": "220,000 t ÷ 8 billion - a hypothetical equal split"},
        {"t0": T_SURPRISE - 0.12, "t1": T_ANTS - 0.1, "kick": "THE REAL SURPRISE", "main": "? ? ?", "color": WHITE},
        {"t0": T_ANTS - 0.1, "t1": T_ANT2 + 0.3, "kick": "THE REAL SURPRISE", "main": "ANTS!"},
        {"t0": T_ANT2 + 0.3, "t1": T_MILLION, "kick": "YOUR ANTS", "main": ant_counter,
         "sub": "~20 quadrillion ants on Earth ÷ 8 billion"},
        {"t0": T_MILLION, "t1": T_STAR - 0.1, "kick": "YOUR ANTS", "main": "ABOUT 2.5 MILLION ANTS",
         "sub": "~20 quadrillion ants on Earth ÷ 8 billion"},
    ]
    header(cx, t, items)

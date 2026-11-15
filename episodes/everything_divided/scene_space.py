"""Scenes 7-8: the Milky Way (12 stars) and the final recap / question."""
import math

import cairo

from cinecode.core import back_out, ease_io, ease_out, kf, prog, smooth
from episodes.everything_divided import art_island as A
from episodes.everything_divided import art_space as S
from episodes.everything_divided import scene_island as SI
from episodes.everything_divided.common import (H, W, WHITE, YELLOW, L0, L1, header, pill, word_t, word_end)

T_STAR = L0("star1")
T_MW = L0("star2")
T_LEAST = word_t("star2", "at")
T_TWELVE = word_t("star2", "twelve")
T_END1 = L0("end1")
T_END2 = L0("end2")
T_END3 = L0("end3")
T_E_TREES = word_t("end3", "three")
T_E_BIRDS = word_t("end3", "six")
T_E_STARS = word_t("end3", "twelve")
T_E_ALL = word_t("end3", "it's")
T_END4 = L0("end4")
T_VOICE_END = L1("end4")

# twelve stars in a gentle arc: wide-shot layout and recap layout (screen coords)
def _arc(cx0, cy0, rx, ry, a0, a1):
    out = []
    for i in range(12):
        a = math.radians(a0 + i * (a1 - a0) / 11)
        out.append((cx0 + math.cos(a) * rx, cy0 + math.sin(a) * ry + (7 if i % 2 else -7)))
    return out


STARS_WIDE = _arc(540, 1150, 400, 420, 200, 340)
STARS_END = _arc(540, 990, 470, 470, 205, 335)


def camera(t):
    keys = [(T_STAR - 0.05, (540.0, 960.0, 1.0)), (T_MW + 0.5, (540.0, 560.0, 0.5)),
            (T_END1 - 0.2, (540.0, 560.0, 0.5)), (T_END1 + 1.1, (540.0, 900.0, 0.86))]
    return kf(t, keys, ease_io)


def night_world(cx, t, night):
    P = {"fields": [1, 1, 1], "field_alpha": 0.65, "trees": 1.0, "birds_t": SI.T_BIRDS,
         "chick": [1, 1, 1], "bar": 1.0, "glint": 1.0}
    wave = smooth(prog(t, T_END4, T_END4 + 0.3))
    P["hero"] = {"mood": "grin" if t > T_END1 else "o", "look": (0, -0.6) if t < T_END1 else (0, 0), "wave": wave}
    cx.push_group()
    SI.world(cx, t, P)
    if night > 0:
        cx.set_operator(cairo.OPERATOR_ATOP)
        cx.set_source_rgba(0.06, 0.08, 0.3, 0.42 * night)
        cx.paint()
        cx.set_operator(cairo.OPERATOR_OVER)
    cx.pop_group_to_source()
    cx.paint()


def stars_alpha(i, t):
    t0 = T_TWELVE - 0.35 + i * 0.07
    return smooth(prog(t, t0, t0 + 0.3))


RECAP = [  # label, screen pos at the end framing, appear order, pulse time
    ("375 TREES", (285, 835), 0, "trees"),
    ("6 WILD BIRDS", (820, 860), 1, "birds"),
    ("3 CHICKENS", (870, 1150), 2, None),
    ("27 g GOLD", (225, 1150), 3, None),
    ("2.5 M ANTS", (300, 1290), 4, None),
    ("2.5 SOCCER FIELDS", (760, 1290), 5, None),
    ("12 STARS", (540, 450), 6, "stars"),
]


def pulse_at(t, t0):
    return math.exp(-((t - t0 - 0.15) / 0.18) ** 2)


def draw(cx, t):
    night = smooth(prog(t, T_STAR - 0.1, T_MW + 0.2))
    # day sky fading into the galaxy
    if night < 1:
        A.sky(cx)
        A.islets(cx, t, 1 - night)
    cx.push_group()
    S.galaxy(cx, t, 1.0, drift=(math.sin(t * 0.05) * 40, t * -3))
    cx.pop_group_to_source()
    cx.paint_with_alpha(night)
    if night < 1:
        A.clouds(cx, t, 1 - night)
        A.clouds(cx, t, 1 - night, front=True)
    fx, fy, z = camera(t)
    cx.save()
    cx.translate(W / 2, 960)
    cx.scale(z, z)
    cx.translate(-fx, -fy)
    night_world(cx, t, night)
    cx.restore()
    # your twelve stars, around the island
    scale_end = smooth(prog(t, T_END1 - 0.2, T_END1 + 1.1))
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(STARS_WIDE, STARS_END)):
        a = stars_alpha(i, t)
        if a <= 0:
            continue
        sx, sy = x0 + (x1 - x0) * scale_end, y0 + (y1 - y0) * scale_end
        p = pulse_at(t, T_E_STARS) + pulse_at(t, T_E_ALL)
        S.star_glow(cx, sx, sy, (15 + 7 * min(1, p)) * back_out(a), t, a, ph=i)
    ya = smooth(prog(t, T_END1 + 0.6, T_END1 + 0.9))
    if ya > 0:
        A.you_tag(cx, W / 2 + (SI.HX - fx) * z, 960 + (SI.HY - 108 - fy) * z, ya, 0.85)
    # recap tags
    if t > T_END1 + 0.4:
        for label, (x, y), k, key in RECAP:
            t0 = T_END1 + 0.5 + k * 0.17
            a = prog(t, t0, t0 + 0.3)
            if a <= 0:
                continue
            p = pulse_at(t, T_E_ALL + k * 0.05)
            if key == "trees":
                p += pulse_at(t, T_E_TREES)
            if key == "birds":
                p += pulse_at(t, T_E_BIRDS)
            if key == "stars":
                p += pulse_at(t, T_E_STARS)
            pill(cx, x, y, label, size=34, alpha=min(1, a * 2), scale=back_out(a) * (1 + 0.18 * min(1, p)))
    header(cx, t, [
        {"t0": T_STAR - 0.1, "t1": T_MW + 0.1, "kick": "AND THE SKY", "main": "THE MILKY WAY", "color": WHITE},
        {"t0": T_MW + 0.1, "t1": T_LEAST - 0.05, "kick": "STARS IN OUR GALAXY", "main": "100-400 BILLION",
         "sub": "estimates vary widely"},
        {"t0": T_LEAST - 0.05, "t1": T_END1 - 0.12, "kick": "YOUR STARS", "main": "AT LEAST 12 STARS",
         "sub": "100 billion ÷ 8 billion ≈ 12.5 each\njust a thought experiment - nobody owns a star"},
        {"t0": T_END1 - 0.12, "t1": T_END2 - 0.1, "kick": "YOUR SHARE", "main": "WHICH WOULD YOU WANT MOST?",
         "color": WHITE},
        {"t0": T_END2 - 0.1, "t1": T_END3 - 0.1, "kick": "YOUR SHARE", "main": "TELL ME IN THE COMMENTS!",
         "color": WHITE},
        {"t0": T_END3 - 0.1, "t1": T_END4 - 0.1, "kick": "JUST IMAGINE", "main": "IT'S ALL YOUR SHARE",
         "color": YELLOW},
        {"t0": T_END4 - 0.1, "t1": T_VOICE_END + 0.25, "kick": "YOUR SHARE", "main": "TAKE GOOD CARE OF THEM!",
         "color": WHITE},
    ])

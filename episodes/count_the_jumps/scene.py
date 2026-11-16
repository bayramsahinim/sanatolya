"""Drawing for "Can You Count the Jumps?" — 1080x1920 vertical.

Everything here is a pure function of time, so any frame can be re-rendered exactly.
The experiment is fully deterministic: the rope's turn phase is a piecewise-linear
function through hand-placed keyframes, and every jump is centred on one rope pass.
"""
import math

import cairo

from cinecode.core import (OUTLINE, circle, clamp, ellipse, fs, hexc, line, mix, prog, rrect,
                           smooth, src)

W, H = 1080, 1920
FLOOR_Y = 1440           # feet line of the lineup
S = 1.72                 # character scale

# ------------------------------------------------------------------ palette
BLUE = hexc("#0B63F0")          # hoodie (matches the mascot sheet)
BLUE_DK = hexc("#0A4FC4")
BLUE_LT = hexc("#3C86FF")
WHITE_CL = hexc("#F4F3F8")      # background figures' clothes
WHITE_SH = hexc("#D9D7E4")
DARK_CL = hexc("#34303F")       # the "black team" in the gorilla-study illustration
DARK_SH = hexc("#26232F")
SHOE = hexc("#2B2B33")
ROPE = hexc("#FF5C8A")
GOLD = hexc("#FFC857")
PURPLE_TOP = hexc("#1C1440")
PURPLE_BOT = hexc("#3F2A7A")
ORANGE_TOP = hexc("#5A1F3A")
ORANGE_BOT = hexc("#E06A2C")
FLOOR_TOP = hexc("#251A47")
FLOOR_BOT = hexc("#120C26")

# ------------------------------------------------------------------ the experiment
# Rope revolutions per level. Each revolution = one rope pass under the jumpers = one jump.
GO_T = 2.95                       # rope starts turning on "Go!"
LEVELS = [(6, 0.70), (7, 0.57), (8, 0.48)]   # (jumps, seconds per rope turn)
LEAD = 0.42                       # time from rope start (top) to first pass under feet


def _schedule():
    """Rope-bottom times (one per jump) and level boundaries."""
    bottoms, lv_start = [], []
    t = GO_T + LEAD
    for n, per in LEVELS:
        lv_start.append(t - per / 2)
        for _ in range(n):
            bottoms.append(round(t, 4))
            t += per
    last_per = LEVELS[-1][1]
    end = bottoms[-1] + last_per / 2      # rope back at the top, stops
    return bottoms, lv_start, end


def set_go(t):
    """Place the experiment so the rope starts turning at `t` (the "Go!" in the narration)."""
    global GO_T, JUMPS, LEVEL_START, COUNT_END, N_JUMPS, SKY_T0, SKY_T1, PENG_T0, PENG_T1, SWAP_T
    GO_T = t
    JUMPS, LEVEL_START, COUNT_END = _schedule()
    N_JUMPS = len(JUMPS)
    assert N_JUMPS == 21
    # tricks (all happen during the count, none highlighted until the reveal)
    SKY_T0, SKY_T1 = GO_T + 1.2, COUNT_END - 0.6      # purple -> orange, slow and continuous
    PENG_T0, PENG_T1 = GO_T + 4.0, GO_T + 7.3         # penguin waddles right -> left IN FRONT of the line
    SWAP_T = LEVEL_START[2] + 0.02                    # left rope turner swapped as LEVEL 3 badge pops


set_go(GO_T)

X_TURN_L, X_HERO, X_MATE, X_TURN_R = 122, 403, 677, 958


def rope_phase(t):
    """Rope angle (radians). 0 = top, pi = bottom (passing under the jumpers' feet).

    Rope bottoms are exactly at JUMPS[k]; between them the angle advances linearly.
    Before GO it hangs low and swings a little; after the count it settles to the bottom."""
    if t < GO_T:
        return math.pi + 0.18 * math.sin(t * 2.6)   # resting, gentle sway
    knots = [(GO_T, 0.0)] + [(tb, math.pi + 2 * math.pi * k) for k, tb in enumerate(JUMPS)]
    knots.append((COUNT_END, knots[-1][1] + math.pi))
    if t >= COUNT_END:
        # finish the last turn then fall to rest at the bottom
        base = knots[-1][1]
        return base + math.pi * smooth(prog(t, COUNT_END, COUNT_END + 0.5))
    for (t0, a0), (t1, a1) in zip(knots, knots[1:]):
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            if t0 == GO_T:
                x = x * x * (2 - x)            # wind-up from rest
            return a0 + (a1 - a0) * x
    return knots[-1][1]


def period(k):
    """Rope-turn period around jump k (0-based)."""
    return LEVELS[0][1] if k < LEVELS[0][0] else LEVELS[1][1] if k < LEVELS[0][0] + LEVELS[1][0] else LEVELS[2][1]


def jump_height(t):
    """Jumper lift (px, world units before scale) — one parabola per rope pass."""
    h = 0.0
    for k, tb in enumerate(JUMPS):
        per = period(k)
        air = per * 0.56
        x = (t - tb) / (air / 2)
        if -1 < x < 1:
            h = max(h, 1 - x * x)
    return h * 78


def landing_squash(t):
    """Brief knee bend just after each landing / before each take-off (0..1)."""
    s = 0.0
    for k, tb in enumerate(JUMPS):
        per = period(k)
        air = per * 0.56
        for c in (tb - air / 2 - 0.05, tb + air / 2 + 0.05):
            d = abs(t - c) / 0.08
            if d < 1:
                s = max(s, 1 - d)
    return s


def jumps_completed(t):
    """How many full jumps have landed by time t (used by QA)."""
    n = 0
    for k, tb in enumerate(JUMPS):
        per = period(k)
        if t >= tb + per * 0.28:
            n += 1
    return n


# ------------------------------------------------------------------ background
def sky_mix(t):
    return smooth(prog(t, SKY_T0, SKY_T1))


def draw_background(cx, t, sky=None, dim=0.0):
    k = sky_mix(t) if sky is None else sky
    top = mix(PURPLE_TOP, ORANGE_TOP, k)
    bot = mix(PURPLE_BOT, ORANGE_BOT, k)
    g = cairo.LinearGradient(0, 0, 0, FLOOR_Y)
    g.add_color_stop_rgba(0, *top)
    g.add_color_stop_rgba(1, *bot)
    cx.rectangle(0, 0, W, FLOOR_Y + 2)
    cx.set_source(g)
    cx.fill()
    # subtle wall grid
    cx.set_line_width(1.2)
    src(cx, (1, 1, 1, 0.035))
    for x in range(0, W + 1, 60):
        cx.move_to(x, 0)
        cx.line_to(x, FLOOR_Y)
    for y in range(0, FLOOR_Y, 60):
        cx.move_to(0, y)
        cx.line_to(W, y)
    cx.stroke()
    # floor with perspective grid
    g = cairo.LinearGradient(0, FLOOR_Y, 0, H)
    g.add_color_stop_rgba(0, *FLOOR_TOP)
    g.add_color_stop_rgba(1, *FLOOR_BOT)
    cx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    cx.set_source(g)
    cx.fill()
    vx, vy = W / 2, FLOOR_Y - 900
    src(cx, (1, 1, 1, 0.07))
    cx.set_line_width(1.6)
    for i in range(-14, 15):
        xb = W / 2 + i * 130
        # line from floor top toward vanishing point direction, extended to bottom
        x_top = vx + (xb - vx) * (900 / (H - FLOOR_Y + 900))
        cx.move_to(x_top, FLOOR_Y)
        cx.line_to(xb, H)
    cx.stroke()
    y = FLOOR_Y
    step = 26
    while y < H:
        cx.move_to(0, y)
        cx.line_to(W, y)
        y += step
        step *= 1.32
    src(cx, (1, 1, 1, 0.05))
    cx.stroke()
    line(cx, [(0, FLOOR_Y), (W, FLOOR_Y)], (1, 1, 1, 0.10), 2)
    if dim > 0:
        cx.rectangle(0, 0, W, H)
        src(cx, (0.02, 0.01, 0.05, dim))
        cx.fill()


# ------------------------------------------------------------------ characters
HEAD_R = 50


def _limb(cx, pts, c=OUTLINE, w=9.0):
    line(cx, pts, c, w)


def draw_person(cx, x, y, t, kind="white", lift=0.0, squash=0.0, arms=None, face="neutral",
                look=(0, 0), seed=0, alpha=1.0, swapped=False, s=S):
    """Front-view figure; (x, y) = point on the ground between the feet.

    kind: "hero" (Just Needy blue hoodie) | "white" (plain background figure).
    arms: dict with 'l'/'r' -> (dx, dy) hand positions relative to the shoulder (world units),
          or None for relaxed arms.
    Returns screen positions of head centre and both hands."""
    cloth, cloth_sh = (DARK_CL, DARK_SH) if kind == "dark" else (WHITE_CL, WHITE_SH)
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    if alpha < 1:
        cx.push_group()
    sq = squash * 10
    body_y = -lift + sq                       # whole body offset
    hip_y = -116 + body_y
    torso_top = hip_y - 112 + sq * 0.4
    neck_y = torso_top
    head_y = neck_y - HEAD_R + 8
    # floor shadow (shrinks with height)
    k = clamp(1 - lift / 140, 0.4, 1)
    ellipse(cx, 0, 4, 46 * k, 9 * k)
    src(cx, (0, 0, 0, 0.28 * k))
    cx.fill()
    # legs
    tuck = clamp(lift / 78, 0, 1)
    for side in (-1, 1):
        hx = side * 15
        knee = (side * (17 + 6 * tuck + 3 * squash), hip_y + 58 - 14 * tuck - 4 * squash)
        foot = (side * 16, hip_y + 116 - 30 * tuck - sq * 0.5)
        if kind == "hero":
            _limb(cx, [(hx, hip_y), knee, foot])
        else:
            _limb(cx, [(hx, hip_y), knee, foot], OUTLINE, 17)
            _limb(cx, [(hx, hip_y), knee, foot], cloth, 10)
        cx.save()
        cx.translate(*foot)
        cx.scale(side, 1)
        rrect(cx, -12, -9, 34, 15, 7)
        fs(cx, SHOE if kind == "hero" else hexc("#3A3550"), OUTLINE, 3.5)
        cx.restore()
    # torso
    shoulder_y = torso_top + 14
    if kind == "hero":
        _hoodie(cx, hip_y, torso_top)
    else:
        rrect(cx, -32, torso_top, 64, hip_y - torso_top + 8, 26)
        fs(cx, cloth, OUTLINE, 5)
        cx.save()
        rrect(cx, -32, torso_top, 64, hip_y - torso_top + 8, 26)
        cx.clip()
        cx.rectangle(12, torso_top, 30, 200)
        src(cx, cloth_sh)
        cx.fill()
        cx.restore()
        rrect(cx, -32, torso_top, 64, hip_y - torso_top + 8, 26)
        fs(cx, None, OUTLINE, 5)
    # arms
    hands = {}
    for side, key in ((-1, "l"), (1, "r")):
        sh = (side * (34 if kind == "hero" else 30), shoulder_y)
        if arms and key in arms:
            dx, dy = arms[key]
            hand = (sh[0] + dx, sh[1] + dy)
            elbow = ((sh[0] + hand[0]) / 2 + side * 6, (sh[1] + hand[1]) / 2 + 10)
        else:
            sw = math.sin(t * 2.2 + seed) * 2 + tuck * 16
            elbow = (side * (38 + tuck * 10), shoulder_y + 48 - tuck * 10)
            hand = (side * (42 + sw + tuck * 20), shoulder_y + 96 - tuck * 34)
        if kind == "hero":
            _limb(cx, [sh, elbow, hand])
            mx, my = (sh[0] + elbow[0]) / 2, (sh[1] + elbow[1]) / 2
            line(cx, [sh, (mx, my)], OUTLINE, 27)
            line(cx, [sh, (mx, my)], BLUE, 18)
        else:
            _limb(cx, [sh, elbow, hand], OUTLINE, 17)
            _limb(cx, [sh, elbow, hand], cloth, 10)
        circle(cx, hand[0], hand[1], 8.5 if kind == "hero" else 9.5)
        fs(cx, OUTLINE if kind == "hero" else (1, 1, 1, 1), OUTLINE, 3)
        hands[key] = hand
    # head
    if kind == "hero":
        # hood rim behind the neck
        ellipse(cx, 0, neck_y - 4, 40, 18)
        fs(cx, BLUE_DK, OUTLINE, 5)
    circle(cx, 0, head_y, HEAD_R)
    fs(cx, (1, 1, 1, 1), OUTLINE, 5.5)
    # soft lavender shade on the left like the mascot sheet
    cx.save()
    circle(cx, 0, head_y, HEAD_R - 2.5)
    cx.clip()
    circle(cx, 16, head_y - 4, HEAD_R + 2)
    cx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    circle(cx, 0, head_y, HEAD_R + 10)
    src(cx, hexc("#DCD8F2"))
    cx.fill()
    cx.set_fill_rule(cairo.FILL_RULE_WINDING)
    cx.restore()
    if swapped:
        _swap_costume_back(cx, head_y)
    _face(cx, head_y, t, face, look, seed, kind, swapped)
    if swapped:
        _swap_costume_front(cx, head_y)
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()
    out = {"head": (x, y + head_y * s), "head_r": HEAD_R * s}
    for k_, (hx_, hy_) in hands.items():
        out[k_] = (x + hx_ * s, y + hy_ * s)
    return out


def _hoodie(cx, hip_y, top):
    def path():
        cx.new_path()
        cx.move_to(-38, hip_y + 8)
        cx.line_to(-42, top + 20)
        cx.curve_to(-42, top + 4, -32, top, -20, top)
        cx.line_to(20, top)
        cx.curve_to(32, top, 42, top + 4, 42, top + 20)
        cx.line_to(38, hip_y + 8)
        cx.close_path()
    path()
    fs(cx, BLUE, OUTLINE, 5.5)
    cx.save()
    path()
    cx.clip()
    cx.rectangle(-60, hip_y - 4, 120, 20)
    src(cx, BLUE_DK)
    cx.fill()
    cx.rectangle(14, top, 40, hip_y - top)
    src(cx, BLUE_LT, 0.35)
    cx.fill()
    cx.restore()
    path()
    fs(cx, None, OUTLINE, 5.5)
    # V-neck, drawstrings (white with black outline, like the sheet), pocket
    line(cx, [(-16, top + 2), (0, top + 22), (16, top + 2)], OUTLINE, 4)
    for side in (-1, 1):
        x0 = side * 8
        line(cx, [(x0, top + 12), (x0 + side * 1, top + 46)], OUTLINE, 7)
        line(cx, [(x0, top + 12), (x0 + side * 1, top + 46)], (1, 1, 1, 1), 3)
        circle(cx, x0 + side, top + 48, 3.6)
        fs(cx, (1, 1, 1, 1), OUTLINE, 2)
    cx.move_to(-22, hip_y - 6)
    cx.line_to(-15, hip_y - 36)
    cx.line_to(15, hip_y - 36)
    cx.line_to(22, hip_y - 6)
    fs(cx, None, hexc("#06378C"), 3.5)


def _blink(t, seed):
    period = 3.3 + (seed % 5) * 0.41
    return ((t + seed * 0.77) % period) < 0.11


def _face(cx, hy, t, face, look, seed, kind, swapped):
    lx, ly = look
    ex, ey = 18, hy - 6
    closed = _blink(t, seed) and face not in ("happy",)
    for side in (-1, 1):
        x = side * ex + lx * 4
        y = ey + ly * 3
        if closed:
            line(cx, [(x - 6, y + 1), (x + 6, y + 1)], OUTLINE, 4)
        elif face == "happy":
            cx.new_path()
            cx.arc(x, y + 4, 7, math.pi * 1.1, math.pi * 1.9)
            src(cx, OUTLINE)
            cx.set_line_width(4)
            cx.stroke()
        else:
            ry = 10.5 if face != "wide" else 12.5
            ellipse(cx, x, y, 5.8, ry)
            fs(cx, OUTLINE, None, 0)
            ellipse(cx, x - 1.6, y - ry * 0.45, 1.6, 2.4)
            src(cx, (1, 1, 1, 0.9))
            cx.fill()
    # brows — the mascot's signature asymmetric brows for the hero
    if kind == "hero":
        if face in ("neutral", "focus"):
            line(cx, [(-30, hy - 26), (-22, hy - 33), (-8, hy - 32)], OUTLINE, 4.2)
            line(cx, [(8, hy - 28), (20, hy - 27), (30, hy - 22)], OUTLINE, 4.2)
        elif face in ("wide", "happy"):
            line(cx, [(-30, hy - 30), (-20, hy - 38), (-8, hy - 36)], OUTLINE, 4.2)
            line(cx, [(8, hy - 36), (20, hy - 38), (30, hy - 30)], OUTLINE, 4.2)
    else:
        line(cx, [(-26, hy - 26), (-10, hy - 27)], OUTLINE, 3.6)
        line(cx, [(10, hy - 27), (26, hy - 26)], OUTLINE, 3.6)
    my = hy + 20
    if face == "wide":
        ellipse(cx, 2, my + 2, 6, 7)
        fs(cx, hexc("#3A1F22"), OUTLINE, 3)
    elif kind == "hero" or face == "happy":
        cx.new_path()
        cx.move_to(-14, my - 3)
        cx.curve_to(-6, my + 6, 8, my + 7, 16, my + 1)
        src(cx, OUTLINE)
        cx.set_line_width(4)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        cx.stroke()
    else:
        line(cx, [(-8, my + 1), (8, my + 1)], OUTLINE, 3.6)
    if swapped:
        # round glasses + moustache
        for side in (-1, 1):
            circle(cx, side * ex + lx * 4, ey + ly * 3, 13)
            fs(cx, None, OUTLINE, 3.6)
        line(cx, [(-5, ey), (5, ey)], OUTLINE, 3.2)
        cx.new_path()
        cx.move_to(-20, my - 3)
        cx.curve_to(-12, my - 13, -2, my - 10, 0, my - 6)
        cx.curve_to(2, my - 10, 12, my - 13, 20, my - 3)
        cx.curve_to(10, my - 5, 2, my - 3, 0, my - 4)
        cx.curve_to(-2, my - 3, -10, my - 5, -20, my - 3)
        cx.close_path()
        fs(cx, OUTLINE, OUTLINE, 2)


def _swap_costume_back(cx, hy):
    pass


def _swap_costume_front(cx, hy):
    # flat cap
    cx.new_path()
    cx.move_to(-48, hy - 22)
    cx.curve_to(-46, hy - 60, 40, hy - 64, 48, hy - 26)
    cx.curve_to(60, hy - 22, 66, hy - 14, 58, hy - 12)
    cx.curve_to(30, hy - 18, -20, hy - 20, -48, hy - 22)
    cx.close_path()
    fs(cx, hexc("#5A6372"), OUTLINE, 5)
    line(cx, [(-30, hy - 26), (40, hy - 24)], hexc("#454D5A"), 4)


# ------------------------------------------------------------------ rope
ROPE_TOP = FLOOR_Y - 690


def rope_points(hl, hr, ang, n=40):
    """Points of the rope between two hands for rope angle `ang` (0=top, pi=bottom)."""
    (x0, y0), (x1, y1) = hl, hr
    c = math.cos(ang)
    up = (y0 - ROPE_TOP) / 0.97        # arc clears the jumpers' heads at the top
    down = (FLOOR_Y + 22 - y0) / 0.97  # and skims the floor at the bottom
    amp = up if c > 0 else down
    pts = []
    for i in range(n + 1):
        u = i / n
        bx = x0 + (x1 - x0) * u
        by = y0 + (y1 - y0) * u
        bulge = math.sin(math.pi * u) ** 0.8
        pts.append((bx, by - c * amp * bulge + 26 * bulge))
    return pts, math.sin(ang)     # sin>0: rope in front half of its swing


def draw_rope(cx, pts, alpha=1.0, w=8.0):
    cx.new_path()
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    src(cx, (0.1, 0.05, 0.15, 0.55 * alpha))
    cx.set_line_width(w + 4)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    src(cx, ROPE, alpha)
    cx.set_line_width(w)
    cx.stroke()


# ------------------------------------------------------------------ penguin
PENG_S = 1.15     # ~0.62 of a stick figure's height: a normal penguin next to a person
PENG_FEET = FLOOR_Y + 78   # a step closer to the camera than the lineup -> drawn in the foreground


def penguin_x(t):
    return W + 170 - (W + 340) * prog(t, PENG_T0, PENG_T1)


def draw_penguin(cx, x, y, t, s=1.0, walking=True, alpha=1.0):
    """Side-ish penguin walking left. (x, y) = ground point."""
    step = t * 3.6 * 2 * math.pi if walking else 0
    rock = math.sin(step) * 0.09 if walking else 0
    bob = abs(math.sin(step)) * 6 if walking else 0
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    if alpha < 1:
        cx.push_group()
    ellipse(cx, 0, 4, 70, 12)
    src(cx, (0, 0, 0, 0.25))
    cx.fill()
    # feet
    for k, side in enumerate((-1, 1)):
        lift = max(0, math.sin(step + k * math.pi)) * 10 if walking else 0
        cx.save()
        cx.translate(side * 26 - 8, -6 - lift)
        ellipse(cx, -10, 0, 26, 10)
        fs(cx, hexc("#FF8C2B"), OUTLINE, 4)
        cx.restore()
    cx.translate(0, -bob)
    cx.rotate(rock)
    # body
    ellipse(cx, 0, -150, 92, 148)
    fs(cx, hexc("#1E2433"), OUTLINE, 6)
    # belly
    ellipse(cx, -12, -128, 62, 112)
    fs(cx, hexc("#F7F6FB"), None, 0)
    # flippers
    flap = math.sin(step * 1.0) * 0.18 if walking else 0
    for side in (-1, 1):
        cx.save()
        cx.translate(side * 82, -175)
        cx.rotate(side * (0.22 + flap * side))
        ellipse(cx, side * 10, 55, 20, 66)
        fs(cx, hexc("#151A26"), OUTLINE, 5)
        cx.restore()
    # face patch + eyes (looking left: walking direction)
    ellipse(cx, -26, -232, 44, 40)
    fs(cx, hexc("#F7F6FB"), None, 0)
    for ex in (-44, -12):
        ellipse(cx, ex, -238, 6.5, 10)
        fs(cx, OUTLINE, None, 0)
        circle(cx, ex - 2, -242, 2.2)
        src(cx, (1, 1, 1, 1))
        cx.fill()
    # beak
    cx.new_path()
    cx.move_to(-46, -214)
    cx.curve_to(-76, -214, -92, -206, -96, -200)
    cx.curve_to(-80, -194, -56, -196, -42, -202)
    cx.close_path()
    fs(cx, hexc("#FF8C2B"), OUTLINE, 4)
    if alpha < 1:
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)
    cx.restore()


# ------------------------------------------------------------------ full lineup
TURN_ARM = {"l": (60, 36), "r": (60, 36)}


def turner_arms(side, ang):
    """Rope turner's inner hand circles with the rope (side=+1 left turner, -1 right turner)."""
    r = 14
    dx, dy = 70 + r * math.sin(ang) * 0.4, 50 - r * math.cos(ang)
    if side > 0:
        return {"r": (dx, dy)}
    return {"l": (-dx, dy)}


def draw_lineup(cx, t, *, ang=None, lift=None, sq=None, penguin=True, swapped=None,
                hero_face="focus", sky=None, dim_others=0.0, show_rope=True, penguin_t=None,
                hide_hero=False, hero_alpha=1.0):
    """The main stage at time t. Returns dict of screen anchors."""
    ang = rope_phase(t) if ang is None else ang
    lift = jump_height(t) if lift is None else lift
    sq = landing_squash(t) if sq is None else sq
    swapped = (t >= SWAP_T) if swapped is None else swapped
    pt = t if penguin_t is None else penguin_t
    anchors = {}
    # turners' hands give rope ends (compute with a dry pass)
    oth_a = 1 - dim_others
    tmp = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    hl = draw_person(tmp, X_TURN_L, FLOOR_Y, t, arms=turner_arms(1, ang), swapped=swapped)["r"]
    hr = draw_person(tmp, X_TURN_R, FLOOR_Y, t, arms=turner_arms(-1, ang))["l"]
    pts, front = rope_points(hl, hr, ang)
    if show_rope and front <= 0:
        draw_rope(cx, pts, oth_a * 0.85 + 0.15)
    a = draw_person(cx, X_TURN_L, FLOOR_Y, t, arms=turner_arms(1, ang), swapped=swapped, seed=3,
                    alpha=oth_a * 0.6 + 0.4 if dim_others else 1, look=(0.6, 0))
    anchors["turner_l"] = a["head"]
    if not hide_hero:
        hero = draw_person(cx, X_HERO, FLOOR_Y, t, kind="hero", lift=lift, squash=sq, face=hero_face,
                           seed=1, alpha=hero_alpha)
        anchors["hero"] = hero["head"]
    draw_person(cx, X_MATE, FLOOR_Y, t, lift=lift, squash=sq, seed=5,
                alpha=oth_a * 0.6 + 0.4 if dim_others else 1)
    draw_person(cx, X_TURN_R, FLOOR_Y, t, arms=turner_arms(-1, ang), seed=7,
                alpha=oth_a * 0.6 + 0.4 if dim_others else 1, look=(-0.6, 0))
    if show_rope and front > 0:
        draw_rope(cx, pts, oth_a * 0.85 + 0.15)
    # the penguin walks in the FOREGROUND: drawn last, nearer the camera, with its own floor shadow
    if penguin and PENG_T0 <= pt <= PENG_T1:
        px = penguin_x(pt)
        draw_penguin(cx, px, PENG_FEET, pt, s=PENG_S)
        anchors["penguin"] = (px, PENG_FEET - 150 * PENG_S)
    return anchors

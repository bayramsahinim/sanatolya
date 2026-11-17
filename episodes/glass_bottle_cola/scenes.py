"""Shot list for the glass-bottle cola Short. render(cx, t) draws one 1080x1920 frame.

Scene order follows the Turkish master exactly:
  A  glass bottle hook (cap pops) -> can / glass / plastic line-up -> 4x gas squeezed in
  B  plastic bottle: looks solid, but it's a sieve (gas escapes through the wall) -> dive in
  C  plastic wall cross-section: CO2 seeping through polymer chains, ~2% / week
  D  week counter: gas 100% -> 83%, FLAT stamp (brief mascot reaction)
  E  tongue close-up: gas -> acid -> the bite
  F  aluminium can: gas stays in; thin plastic lining -> dive in
  G  can wall cross-section: lining absorbs the aromas, 2 weeks
  H  glass wall cross-section: nothing out, nothing absorbed
  I  glass bottle close-up pulls back; cap goes back on - just as it left the factory
"""
import math
import random

import cairo

from cinecode.captions import render_text
from cinecode.core import OUTLINE, clamp, ease_in, ease_io, ease_out, fs, kf, lerp, line, prog, smooth
from episodes.glass_bottle_cola import art
from episodes.glass_bottle_cola.art import H, SHELF_Y, W
from episodes.glass_bottle_cola.script import END
from episodes.glass_bottle_cola.timing import E, S, TL, we, word

# ------------------------------------------------------------------ beats (s)
T2, T2E = S("L02"), E("L02")
T2_CHANGES = word("L02", "changes")
T3, SQUEEZE = S("L03"), word("L03", "squeezed")
T4, SOLID = S("L04"), word("L04", "solid,")
T5, SIEVE_E = S("L05"), E("L05")
T6 = S("L06")
TWO_PCT = word("L07", "2")
T8, FLAT, T8E = S("L08"), word("L08", "flat,"), E("L08")
T9, ACID = S("L09"), word("L09", "acid")
T10 = S("L10")
T11 = S("L11")
LINED, THIN, PLASTIC = word("L12", "lined"), word("L12", "thin"), word("L12", "plastic.")
T13, TWO_WK = S("L13"), word("L13", "two")
T14, AND14 = S("L14"), word("L14", "and")
T14E = E("L14")
T15 = S("L15")
LEFT, FACTORY = word("L16", "left"), word("L16", "factory.")

# scene cut points
A_END = T4 - 0.2
B_ZOOM0, B_ZOOM1 = SIEVE_E - 0.05, SIEVE_E + 0.42
C_END = T8 - 0.25
D_END = T9 - 0.22
E_END = T11 - 0.28
F_ZOOM0, F_ZOOM1 = THIN - 0.1, PLASTIC + 0.25
G_END = T14 - 0.22
H_END = AND14 - 0.12
XF = 0.28                      # crossfade length

GLASS_S = 1.25
PET_S = 1.15


# ------------------------------------------------------------------ helpers
def bg(cx, tint="warm"):
    art.paint_surface(cx, art.wall_surface(tint))


def zoomed(cx, px, py, z, fn, t):
    cx.save()
    cx.translate(px, py)
    cx.scale(z, z)
    cx.translate(-px, -py)
    fn(cx, t)
    cx.restore()


def faded(cx, alpha, fn, t):
    if alpha <= 0.001:
        return
    cx.push_group()
    fn(cx, t)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def tri(v, lo, hi):
    """triangle-wave reflect v into [lo, hi] (bouncing)."""
    span = hi - lo
    m = (v - lo) % (2 * span)
    return lo + (m if m < span else 2 * span - m)


# ================================================================== A
_rA = random.Random(21)
GHOSTS = [(150, -1), (330, -1), (750, 1), (930, 1)]
GHOST_MOLS = [[(_rA.uniform(-0.62, 0.62), _rA.uniform(50, 520), _rA.uniform(0, 6.3), _rA.uniform(0, 6.3))
               for _ in range(11)] for _ in GHOSTS]
PUFF = [(_rA.uniform(-30, 30), _rA.uniform(0.0, 0.5), _rA.uniform(18, 34), _rA.uniform(-40, 40)) for _ in range(9)]


def scene_A(cx, t):
    bg(cx)
    gx = 540
    # line-up (can left, plastic right)
    k_in = ease_out(prog(t, T2 - 0.15, T2 + 0.4))
    k_out = ease_in(prog(t, T2E - 0.05, T2E + 0.4))
    can_x = lerp(-220, 200, k_in) - 520 * k_out
    pet_x = lerp(1300, 880, k_in) + 520 * k_out
    hop = [math.sin(math.pi * prog(t, T2_CHANGES + d, T2_CHANGES + d + 0.32)) * 26 for d in (0.0, 0.08, 0.16)]
    art.warm_glow(cx, gx, SHELF_Y - 380, 430, 0.28)
    if 0 < k_in and k_out < 1:
        art.contact_shadow(cx, can_x, 130)
        art.contact_shadow(cx, pet_x, 120)
    art.contact_shadow(cx, gx, 150)
    # ghost bottles packed with CO2 (4x volume)
    g_in = [ease_out(prog(t, T3 + 0.05 + i * 0.12, T3 + 0.45 + i * 0.12)) for i in range(4)]
    sq = ease_io(prog(t, SQUEEZE - 0.15, SQUEEZE + 0.6))
    if t > T3 - 0.1 and sq < 1:
        for i, (x0, side) in enumerate(GHOSTS):
            a = g_in[i] * (1 - sq)
            if a <= 0.01:
                continue
            x = lerp(x0, gx, sq)
            s = 0.78 * (1 - 0.35 * sq)
            cx.save()
            art._path(cx, art.GLASS, x, SHELF_Y, s)
            art.src(cx, (1, 1, 1, 0.22 * a))
            cx.fill_preserve()
            cx.set_dash([14, 10])
            art.src(cx, (0.25, 0.18, 0.12, 0.75 * a))
            cx.set_line_width(4)
            cx.stroke()
            cx.restore()
            for u, yy, ph, ang in GHOST_MOLS[i]:
                mx = x + u * art._hw_at(art.GLASS, yy) * s + math.sin(t * 3 + ph) * 5
                my = SHELF_Y - yy * s + math.cos(t * 2.6 + ph) * 5
                # molecules converge into the real bottle
                tx = gx + u * 0.6 * art._hw_at(art.GLASS, yy) * GLASS_S
                ty = SHELF_Y - (yy * 0.85 + 30) * GLASS_S
                art.co2(cx, lerp(mx, tx, sq), lerp(my, ty, sq), ang + t * 0.8, 0.62 * g_in[i], a)
    if 0 < k_in and k_out < 1:
        art.aluminum_can(cx, can_x, SHELF_Y - hop[0], 1.05, t)
        art.pet_bottle(cx, pet_x, SHELF_Y - hop[2], 1.08, t)
    # the glass bottle
    t_pop = 0.32
    u = clamp((t - t_pop) / 0.75)
    jig = math.sin(t * 60) * 3 * (1 - prog(t, 0.0, t_pop)) if t < t_pop else 0
    cap_off = (jig + 170 * u, -1500 * u + 600 * u * u, 7 * u)
    fizz = math.exp(-max(0, t - t_pop) / 1.3) if t > t_pop else 0.15
    bump = math.sin(math.pi * prog(t, SQUEEZE + 0.35, SQUEEZE + 0.75))
    art.glass_bottle(cx, gx, SHELF_Y - hop[1], GLASS_S, t, cap=1.0 if u < 1 else 0.0, cap_off=cap_off,
                     density=1.0 + 0.5 * fizz + 0.4 * sq, fizz=fizz, sx=1 + 0.045 * bump)
    # CO2 puff escaping the neck after the pop
    neck_y = SHELF_Y - 610 * GLASS_S
    for dx, d0, r, drift in PUFF:
        p = prog(t, t_pop + d0 * 0.6, t_pop + d0 * 0.6 + 1.6)
        if 0 < p < 1:
            a = math.sin(math.pi * p) * 0.75
            cx.arc(gx + dx + drift * p, neck_y - 30 - 330 * ease_out(p), r * (0.6 + 1.6 * p), 0, 2 * math.pi)
            art.src(cx, (1, 1, 1, 0.55 * a))
            cx.fill_preserve()
            art.src(cx, (0.35, 0.25, 0.2, 0.55 * a))
            cx.set_line_width(3)
            cx.stroke()
    art.paint_surface(cx, art.shelf_surface())


# ================================================================== B
_rB = random.Random(5)
LEAKS = [(_rB.choice((-1, 1)), _rB.uniform(90, 480), _rB.uniform(0, 6.3), i * 0.085) for i in range(22)]


def scene_B(cx, t):
    bg(cx)
    e = ease_io(prog(t, A_END, T4 + 0.3))
    gx = 540 - 980 * e
    px = 540 + 980 * (1 - e)
    art.warm_glow(cx, 540, SHELF_Y - 380, 430, 0.28)
    if e < 1:
        art.contact_shadow(cx, gx, 150)
        art.glass_bottle(cx, gx, SHELF_Y, GLASS_S, t, cap=0)
    art.contact_shadow(cx, px, 140)
    tap = math.sin(math.pi * prog(t, SOLID, SOLID + 0.3))
    glow = 0.6 * smooth(prog(t, T5 + 0.1, T5 + 0.6))
    art.pet_bottle(cx, px, SHELF_Y, PET_S, t, sx=1 + 0.02 * tap, wall_glow=glow * (0.7 + 0.3 * math.sin(t * 9)))
    # gas escaping straight through the plastic wall
    for side, yy, ph, d in LEAKS:
        p = prog(t, T5 + d, T5 + d + 1.15)
        if 0 < p < 1:
            hw = art._hw_at(art.PET, yy) * PET_S
            x = px + side * (hw - 40 + 210 * ease_out(p))
            y = SHELF_Y - yy * PET_S - 40 * p + math.sin(t * 5 + ph) * 6
            a = min(1, p * 5) * (1 - prog(p, 0.7, 1))
            art.co2(cx, x, y, ph + t * 1.5, 0.9, a)
    art.paint_surface(cx, art.shelf_surface())


# ================================================================== C
_rC = random.Random(8)
C_MOLS = [(90 + (i * 397) % 900 + _rC.uniform(-30, 30), -1.6 + i * 0.27, _rC.uniform(0, 6.3), _rC.uniform(1080, 1400))
          for i in range(15)]
BAND0, BAND1 = 640, 960


def _mol_c(t, x0, t0, ph, y0):
    d = t - (B_ZOOM1 - 0.6 + t0)
    if d < 0:
        return None
    vc, vb, va = 300, 125, 170
    tc = (y0 - BAND1) / vc
    tb = (BAND1 - BAND0) / vb
    if d < tc:
        y = y0 - vc * d
        x = x0 + 14 * math.sin(d * 3 + ph)
    elif d < tc + tb:
        y = BAND1 - vb * (d - tc)
        x = x0 + 46 * math.sin((d - tc) * 3.4 + ph)
    else:
        y = BAND0 - va * (d - tc - tb)
        x = x0 + 46 * math.sin(tb * 3.4 + ph) + 30 * (d - tc - tb)
    a = 1 - clamp((BAND0 - 140 - y) / 300)
    return x, y, a


def layer_tag(cx, x, y, txt, a=1.0):
    art.label_pill(cx, x, y, txt, a, size=30, fg=OUTLINE, bg=(1, 1, 1, 0.88))


def scene_C(cx, t):
    bg(cx)
    art.cola_field(cx, BAND1 - 10, t, seed=3)
    back, front = art.polymer_layers(BAND0, BAND1)
    art.paint_surface(cx, back)
    for x0, t0, ph, y0 in C_MOLS:
        m = _mol_c(t, x0, t0, ph, y0)
        if m and m[2] > 0:
            art.co2(cx, m[0], m[1], ph + t * 1.2, 2.0, m[2])
    art.paint_surface(cx, front)
    layer_tag(cx, 175, BAND0 - 58, "PLASTIC WALL", smooth(prog(t, B_ZOOM1 - 0.1, B_ZOOM1 + 0.3)))
    art.label_pill(cx, 540, 400, "~2% / week", ease_out(prog(t, TWO_PCT - 0.1, TWO_PCT + 0.3)), size=56)


# ================================================================== D
WEEKS = [(1, 100), (2, 98), (3, 94), (5, 91), (7, 88), (8, 85), (10, 83)]   # as shown in the original


def scene_D(cx, t):
    bg(cx)
    bx = 650
    art.warm_glow(cx, bx, SHELF_Y - 380, 420, 0.25)
    n = len(WEEKS)
    span = (FLAT - 0.2) - (T8 + 0.1)
    step = span / (n - 1)
    i = int(clamp((t - (T8 + 0.1)) / step, 0, n - 1))
    ti = T8 + 0.1 + i * step
    flip = prog(t, ti, ti + 0.28)
    wk, gas = WEEKS[i]
    prev = WEEKS[i - 1][0] if i > 0 else None
    gas_s = gas if flip > 0.5 or i == 0 else WEEKS[i - 1][1]
    art.calendar(cx, 255, 820, wk, flip, prev)
    # mascot peeks up from behind the shelf at the FLAT stamp
    up = ease_out(prog(t, FLAT - 0.05, FLAT + 0.4)) * (1 - ease_in(prog(t, T8E + 0.05, T8E + 0.4)))
    if up > 0:
        blink = 1.0 if 0 < (t - FLAT - 0.9) < 0.12 else 0.0
        art.mascot_peek(cx, 925, SHELF_Y + 160 - 330 * up, 108, look=(-1, 0.3), blink=blink)
    art.contact_shadow(cx, bx, 140)
    dens = lerp(0.25, 1.0, (gas_s - 83) / 17)
    stamp_k = ease_out(prog(t, FLAT, FLAT + 0.22))
    art.pet_bottle(cx, bx, SHELF_Y, 1.1, t, density=dens, label_stamp=stamp_k)
    nx, ny = bx + 34, SHELF_Y - 560 * 1.1
    tx, ty = bx + 150, SHELF_Y - 520 * 1.1
    line(cx, [(nx, ny), (tx - 70, ty - 6)], (0.3, 0.2, 0.15, 0.9), 2.5)
    art.gas_tag(cx, tx + 30, ty, gas_s, 1.0)
    art.paint_surface(cx, art.shelf_surface())


# ================================================================== E
_rE = random.Random(12)
DROPS = [(_rE.uniform(120, 960), T9 + 0.15 + i * 0.16, _rE.uniform(0, 6.3)) for i in range(12)]
SPARKS = [(_rE.uniform(40, 1040), _rE.uniform(0, 1), _rE.uniform(22, 50), _rE.uniform(0, 6.3), _rE.uniform(0, 1))
          for _ in range(46)]


def scene_E(cx, t):
    bg(cx, "pink")
    sh = math.sin(t * 40) * 2.2 * smooth(prog(t, T10, T10 + 0.3)) * (1 - prog(t, E_END - 0.4, E_END))
    cx.save()
    cx.translate(sh, 0)
    art.paint_surface(cx, art.tongue_surface())
    # gas falls onto the tongue and becomes acid (sparkles)
    for x, t0, ph in DROPS:
        hit = t0 + 0.55
        ye = art.tongue_edge(x) + 30
        if t0 < t < hit:
            p = ease_in(prog(t, t0, hit))
            art.co2(cx, x, lerp(-60, ye, p), ph + t * 2, 1.8)
        elif t >= hit:
            p = prog(t, hit, hit + 0.35)
            r = 48 * ease_out(p) * (0.75 + 0.25 * math.sin(t * 9 + ph))
            art.sparkle(cx, x, ye, r, 1.0)
            if p < 1:
                cx.arc(x, ye, 20 + 70 * p, 0, 2 * math.pi)
                art.src(cx, (1, 0.85, 0.5, 0.6 * (1 - p)))
                cx.set_line_width(4)
                cx.stroke()
    # "the bite": sparkles bloom across the whole tongue
    dens = smooth(prog(t, ACID + 0.1, T10 + 0.8))
    for x, yv, r, ph, th in SPARKS:
        if th > dens:
            continue
        y = art.tongue_edge(x) + 40 + yv * (H - 860)
        k = smooth(prog(dens, th, th + 0.15))
        art.sparkle(cx, x, y, r * k * (0.6 + 0.4 * math.sin(t * 7 + ph)), 0.95)
    cx.restore()


# ================================================================== F
_rF = random.Random(31)
CAN_MOLS = [(_rF.uniform(-70, 70), _rF.uniform(60, 280), _rF.choice((-1, 1)) * _rF.uniform(90, 150),
             _rF.choice((-1, 1)) * _rF.uniform(60, 120), _rF.uniform(0, 6.3)) for _ in range(6)]
CAN_S = 1.6


def scene_F(cx, t):
    bg(cx)
    art.warm_glow(cx, 540, SHELF_Y - 300, 380, 0.25)
    art.contact_shadow(cx, 540, 170)
    xr = smooth(prog(t, T11 + 0.15, T11 + 0.55))
    mols = []
    for x0, y0, vx, vy, ph in CAN_MOLS:
        mols.append((tri(x0 + vx * t, -70, 70), tri(y0 + vy * t, 50, 290), ph + t))
    art.aluminum_can(cx, 540, SHELF_Y, CAN_S, t, xray=xr, mols=mols if xr > 0.3 else None)
    # the thin plastic lining, traced along the inner wall
    k = smooth(prog(t, LINED - 0.1, LINED + 0.3))
    if k > 0:
        hw = 92 * CAN_S
        y0, y1 = SHELF_Y - 300 * CAN_S, SHELF_Y - 30 * CAN_S
        pulse = 0.75 + 0.25 * math.sin(t * 10)
        for xx in (540 - hw, 540 + hw):
            line(cx, [(xx, y0), (xx, lerp(y0, y1, k))], (1, 0.93, 0.7, 0.95 * pulse), 9)
        line(cx, [(540 - hw, y1), (540 - hw + 2 * hw * k, y1)], (1, 0.93, 0.7, 0.95 * pulse), 9)
    art.paint_surface(cx, art.shelf_surface())


# ================================================================== G
_rG = random.Random(44)
METAL1, LINER1 = 700, 762
G_AROMA = [(70 + (i * 431) % 940, _rG.uniform(900, 1800), i % 3, _rG.uniform(0, 6.3), i)
           for i in range(14)]
G_CO2 = [(_rG.uniform(80, 1000), _rG.uniform(900, 1800), _rG.uniform(0, 6.3)) for _ in range(6)]


def _wander(x0, y0, ph, t, ax=34, ay=26):
    return x0 + ax * math.sin(t * 0.9 + ph), y0 + ay * math.sin(t * 1.3 + ph * 1.7)


def scene_G(cx, t):
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    art.cola_field(cx, LINER1, t, seed=6, n=50)
    art.paint_surface(cx, art.metal_layers(METAL1, LINER1))
    n = len(G_AROMA)
    absorbed_until = TWO_WK + 0.2
    for x0, y0, kind, ph, i in G_AROMA:
        x, y = _wander(x0, y0, ph, t)
        a_start = T13 + 0.25 + (absorbed_until - T13 - 0.9) * (i / (n - 1))
        if i >= n - 2:          # "almost all": a couple stay free
            a_start = 1e9
        p = ease_io(prog(t, a_start, a_start + 0.75))
        dock_x = x0 + 20 * math.sin(ph)
        dock_y = METAL1 + 31
        xx, yy = lerp(x, dock_x, p), lerp(y, dock_y, p)
        art.aroma(cx, xx, yy, kind, ph + t * 0.6 * (1 - p), 2.0 - 0.6 * p, 1 - 0.3 * p)
    for x0, y0, ph in G_CO2:
        x, y = _wander(x0, y0, ph, t, 60, 70)
        art.co2(cx, x, y, ph + t * 0.8, 1.9)
    tag_a = smooth(prog(t, F_ZOOM1 - 0.1, F_ZOOM1 + 0.3))
    layer_tag(cx, 160, 640, "ALUMINUM", tag_a)
    layer_tag(cx, 175, 820, "PLASTIC LINING", tag_a)
    art.label_pill(cx, 540, 380, "2 weeks", ease_out(prog(t, TWO_WK - 0.1, TWO_WK + 0.3)), size=56)


# ================================================================== H
_rH = random.Random(52)
H_MOLS = [(_rH.uniform(70, 1010), _rH.uniform(0, 1.4), _rH.uniform(0, 6.3), _rH.random() < 0.5, _rH.randrange(3))
          for _ in range(10)]
GLASS1 = 760


def scene_H(cx, t):
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    art.cola_field(cx, GLASS1, t, seed=9, n=55)
    art.paint_surface(cx, art.glass_lattice(0, GLASS1))
    period = 1.5
    for x0, off, ph, is_co2, kind in H_MOLS:
        d = (t - G_END + off) % period
        u = d / period
        # rise to the glass, bounce off it, sink back
        y = GLASS1 + 44 + 640 * (2 * u - 1) ** 2
        x = x0 + 30 * math.sin(t + ph)
        if is_co2:
            art.co2(cx, x, y, ph + t, 1.9)
        else:
            art.aroma(cx, x, y, kind, ph + t * 0.5, 1.9)
        hp = abs(u - 0.5)
        if hp < 0.12:
            a = 1 - hp / 0.12
            for sgn in (-1, 1):
                cx.arc(x + sgn * 44, GLASS1 + 22, 26 + 14 * (1 - a), math.pi * (1.1 if sgn < 0 else 1.6),
                       math.pi * (1.4 if sgn < 0 else 1.9))
                art.src(cx, (1, 0.95, 0.8, 0.8 * a))
                cx.set_line_width(4)
                cx.stroke()
    layer_tag(cx, 120, GLASS1 - 50, "GLASS", smooth(prog(t, G_END, G_END + 0.4)))


# ================================================================== I
def scene_I(cx, t):
    bg(cx)
    art.warm_glow(cx, 540, SHELF_Y - 380, 430, 0.3)
    art.contact_shadow(cx, 540, 150)
    # cap goes back on: just as it left the factory
    drop = ease_in(prog(t, LEFT - 0.15, FACTORY + 0.05))
    bounce = math.sin(math.pi * prog(t, FACTORY + 0.05, FACTORY + 0.25)) * 18
    cap_y = -700 * (1 - drop) - bounce
    capa = 1.0 if t > LEFT - 0.15 else 0.0
    shine = prog(t, FACTORY + 0.35, FACTORY + 1.25)
    art.glass_bottle(cx, 540, SHELF_Y, GLASS_S, t, cap=capa, cap_off=(0, cap_y, 0), shine=shine if 0 < shine < 1 else 0)
    art.paint_surface(cx, art.shelf_surface())


# ================================================================== compositor
def render_scene(cx, t):
    if t < A_END:
        scene_A(cx, t)
    elif t < B_ZOOM0:
        scene_B(cx, t)
    elif t < B_ZOOM1:
        p = ease_in(prog(t, B_ZOOM0, B_ZOOM1))
        px = 540 + art._hw_at(art.PET, 330) * PET_S
        zoomed(cx, px, SHELF_Y - 330 * PET_S, 1 + 6 * p, scene_B, t)
        faded(cx, smooth(prog(t, B_ZOOM1 - XF, B_ZOOM1)), lambda c, tt: zoomed(c, 540, 800, 1.35 - 0.35 * p, scene_C, tt), t)
    elif t < C_END:
        z = 1 + 0.08 * (1 - ease_out(prog(t, B_ZOOM1, B_ZOOM1 + 0.6)))
        zoomed(cx, 540, 800, z, scene_C, t)
    elif t < C_END + XF:
        scene_C(cx, t)
        faded(cx, smooth(prog(t, C_END, C_END + XF)), scene_D, t)
    elif t < D_END:
        scene_D(cx, t)
    elif t < D_END + XF:
        scene_D(cx, t)
        faded(cx, smooth(prog(t, D_END, D_END + XF)), scene_E, t)
    elif t < E_END:
        scene_E(cx, t)
    elif t < E_END + XF:
        scene_E(cx, t)
        faded(cx, smooth(prog(t, E_END, E_END + XF)), scene_F, t)
    elif t < F_ZOOM0:
        scene_F(cx, t)
    elif t < F_ZOOM1:
        p = ease_in(prog(t, F_ZOOM0, F_ZOOM1))
        zoomed(cx, 540 + 92 * CAN_S, SHELF_Y - 170 * CAN_S, 1 + 7 * p, scene_F, t)
        faded(cx, smooth(prog(t, F_ZOOM1 - XF, F_ZOOM1)), lambda c, tt: zoomed(c, 540, 760, 1.35 - 0.35 * p, scene_G, tt), t)
    elif t < G_END:
        z = 1 + 0.08 * (1 - ease_out(prog(t, F_ZOOM1, F_ZOOM1 + 0.6)))
        zoomed(cx, 540, 760, z, scene_G, t)
    elif t < G_END + XF:
        scene_G(cx, t)
        faded(cx, smooth(prog(t, G_END, G_END + XF)), scene_H, t)
    elif t < H_END:
        scene_H(cx, t)
    else:
        # big glass close-up pulls back to the full bottle
        z = kf(t, [(H_END, 2.5), (T14E + 0.45, 1.0)], ease_io)
        zoomed(cx, 540, SHELF_Y - 330 * GLASS_S, z, scene_I, t)
        if t < H_END + XF:
            faded(cx, 1 - smooth(prog(t, H_END, H_END + XF)), scene_H, t)


# ================================================================== captions
CAP_SIZE = 78
CAP_Y = 1500
MAX_W = 960


def _wrap(txt):
    surf, w, h, pad = render_text(txt, CAP_SIZE)
    if w - 2 * pad <= MAX_W:
        return txt
    ws_ = txt.split()
    best = min(range(1, len(ws_)), key=lambda i: abs(len(" ".join(ws_[:i])) - len(" ".join(ws_[i:]))))
    return " ".join(ws_[:best]) + "\n" + " ".join(ws_[best:])


def caption_cues():
    cues = []
    flat = [(c, a, b) for l in TL for c, a, b in l["chunks"]]
    for i, (c, a, b) in enumerate(flat):
        t0 = a - 0.04
        nxt = flat[i + 1][1] - 0.04 if i + 1 < len(flat) else None
        if nxt is not None and nxt - b < 0.75:
            t1, cut = nxt, True
        else:
            t1, cut = b + 0.35, False
        cues.append({"text": _wrap(c), "t0": t0, "t1": t1, "cut_out": cut, "raw": c, "w0": a, "w1": b})
    for i, c in enumerate(cues):
        c["cut_in"] = i > 0 and cues[i - 1]["cut_out"]
    return cues


CUES = caption_cues()


def draw_captions(cx, t):
    for c in CUES:
        if t < c["t0"] or t >= c["t1"] + (0 if c["cut_out"] else 0.15):
            continue
        a_in = 1.0 if c["cut_in"] else ease_out(prog(t, c["t0"], c["t0"] + 0.12))
        a_out = 1.0 if c["cut_out"] else 1 - prog(t, c["t1"], c["t1"] + 0.15)
        a = min(a_in, a_out)
        sc = 0.96 + 0.04 * (1.0 if c["cut_in"] else a_in)
        surf, w, h, pad = render_text(c["text"], CAP_SIZE)
        cx.save()
        cx.translate(W / 2, CAP_Y)
        cx.scale(sc, sc)
        cx.set_source_surface(surf, -w / 2, -h / 2)
        cx.paint_with_alpha(a)
        cx.restore()


def render(cx, t):
    t = min(t, END - 1e-3)
    render_scene(cx, t)
    draw_captions(cx, t)

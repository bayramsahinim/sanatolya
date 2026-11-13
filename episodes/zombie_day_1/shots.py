"""Day 1 (remastered) - shot list. Each shot draws one 1080x1920 frame at global time t."""
import math
import random

import cairo

from cinecode.characters import Pose, breathe, hero_pose, run, walk
from cinecode.core import (circle, clamp, ease_in, ease_io, ease_out, ellipse, fs, hexc, kf, line,
                           mix, noise1, poly, prog, rgrad, rrect, shade, smooth, src, vgrad, win)
from . import world as Wd
from .world import (AMBER, CGRAY, CHARCOAL, DGREEN, FH, FOG, FW, INK, MBROWN, MIDNIGHT, RIM_COLD,
                    RIM_WARM, TINT_DAY, TINT_ROOM, CIVILIAN, draw_hero, draw_infected, infected,
                    infected_pose, silhouette)

Z1 = infected(1, shirt=hexc("#5B6670"))
Z2 = infected(2, shirt=hexc("#6A5A4C"))
Z3 = infected(3, shirt=hexc("#4F5A4D"))
Z4 = infected(4, shirt=hexc("#55505A"))
Z5 = infected(5, shirt=hexc("#6E6A63"))


# ---------------------------------------------------------------- helpers
def cam(cx, zoom=1.0, fx=FW / 2, fy=FH / 2, dx=0.0, dy=0.0, rot=0.0):
    """Zoom about focus point (fx,fy) then offset."""
    cx.translate(FW / 2 + dx, FH / 2 + dy)
    if rot:
        cx.rotate(rot)
    cx.scale(zoom, zoom)
    cx.translate(-fx, -fy)


def hshake(t, t0, amp, dur=0.35):
    k = prog(t, t0, t0 + dur)
    if k <= 0 or k >= 1:
        return 0.0, 0.0
    a = amp * (1 - k) ** 2
    return noise1(t * 40, 5) * a, noise1(t * 40, 9) * a


def fields(cx, horizon, t, base=hexc("#3A4A40"), far=hexc("#4A5853")):
    cx.rectangle(-600, horizon, FW + 1200, FH * 2)
    cx.set_source(vgrad(cx, 0, horizon, 0, FH, [(0, far), (0.35, base), (1, shade(base, -0.35))]))
    cx.fill()
    # furrow bands converging to horizon
    for k in range(14):
        yy = horizon + (k ** 1.8) * 6
        line(cx, [(-600, yy), (FW + 600, yy)], hexc("#2F3B35", 0.45), 1.5 + k * 0.3)


def yard_bg(cx, t, horizon, barn_at=None, pole_at=None, house_at=None, fog=0.38, seed=0, trees=True):
    Wd.sky(cx, t, horizon + 10, seed=seed)
    if trees:
        Wd.tree_line(cx, horizon, hexc("#45524F"), seed=seed + 3, h=50)
        Wd.fog_layer(cx, t, horizon - 20, 60, 0.35, seed=seed + 4)
        Wd.tree_line(cx, horizon + 6, hexc("#34403D"), seed=seed + 9, h=36)
    fields(cx, horizon, t)
    if pole_at:
        x, y, s = pole_at
        Wd.utility_pole(cx, x, y, 520, s)
    if barn_at:
        x, y, s = barn_at
        Wd.barn(cx, x, y, s)
    if house_at:
        x, y, s = house_at
        Wd.farmhouse_ext(cx, x, y, s, t)
    Wd.fog_layer(cx, t, horizon + 30, 90, fog, seed=seed + 11)


def dirt(cx, pts, col=hexc("#4E463E")):
    Wd.smooth_poly(cx, pts)
    src(cx, col)
    cx.fill()


# ================================================================ SCENE 1 - hook
def outside_hook(cx, t, x0, y0, w, h):
    """Farmyard seen through the window in the opening close-up."""
    cx.save()
    cx.translate(x0, y0)
    cx.scale(w / FW, w / FW)
    hz = 760
    Wd.sky(cx, t, hz + 10, seed=1)
    Wd.tree_line(cx, hz, hexc("#45524F"), seed=4, h=50)
    Wd.fog_layer(cx, t, hz - 20, 60, 0.35, seed=5)
    fields(cx, hz, t)
    Wd.barn(cx, 820, hz + 40, 0.55)
    Wd.fence(cx, hz + 230, t, gap=170, h=90, s=0.9)
    dirt(cx, [(-50, 1250), (300, 1010), (900, 980), (1200, 1100), (1200, 1500), (-50, 1500)])
    # runner crossing in the distance (right -> left)
    rt = t - 1.6
    if 0 <= rt <= 2.6:
        rx = 1180 - rt * 520
        p = run(Pose(x=rx, y=hz + 210, s=0.62, f=-1, t=t, eyes="wide", mouth="o", brows="worried"), t, 2.6)
        Wd.lit(cx, lambda c: CIVILIAN.draw(c, p), TINT_DAY, 0.4)
    # infected shambling across the yard (left -> right)
    zx = 120 + t * 85
    p = infected_pose(zx, 1140, t, s=1.05, f=1, seed=1)
    draw_infected(cx, Z1, p, fogged=0.12)
    Wd.fog_layer(cx, t, 1150, 70, 0.28, seed=21)
    cx.restore()


def s01(cx, t):
    lt = t
    z = 1.0 + 0.09 * ease_io(prog(lt, 0, 5.1))
    cx.save()
    cam(cx, z, 560, 900)
    Wd.room_wall(cx, 1900, t)
    wx, wy, ww, wh = 150, 300, 780, 900
    Wd.window(cx, wx, wy, ww, wh, t, lambda c: outside_hook(c, t, wx, wy, ww, wh), open_amt=1.0, wind=0.4)
    Wd.light_shaft(cx, [(wx, wy + wh), (wx + ww, wy + wh), (wx + ww + 260, FH + 200), (wx - 120, FH + 200)], 0.08, t=t)
    # protagonist close-up, profile, looking out
    freeze = win(lt, 2.0, 2.5)
    look_x = kf(lt, [(0, 0.5), (1.4, 0.7), (2.3, 0.9), (3.6, 0.2), (5.1, 0.4)])
    p = hero_pose(330, 2240, t, s=3.0, f=1, view="side", brows="worried", mouth="flat",
                  eyes="open", look=(look_x, -0.1 - 0.15 * freeze), tilt=-3 - 3 * freeze,
                  lean=-2 - 3 * freeze, arm_a=10, arm_b=60, elb_b=90)
    p = breathe(p, t, 1.0 - 0.8 * freeze)
    if freeze > 0.5:
        p = p.but(mouth="o", mouth_open=0.55)
    draw_hero(cx, p, TINT_ROOM, 0.26, RIM_COLD, 0.5, 1)
    Wd.dust(cx, t, (120, 400, 980, 1800), 30)
    cx.restore()


# ================================================================ SCENE 2 - the outbreak
def s02_car(cx, t):
    lt = t - 5.1
    cx.save()
    cam(cx, 1.05, 540 + lt * 12, 960)
    hz = 880
    yard_bg(cx, t, hz, house_at=(170, hz + 120, 0.55), pole_at=(930, hz + 140, 0.7), seed=2)
    Wd.wires(cx, [(930 - 42, hz + 140 - 345)], [(1200, hz + 120 - 330)], t)
    Wd.wires(cx, [(930 - 42, hz + 140 - 345)], [(-100, hz + 80)], t, sag=60)
    poly(cx, [(-300, 2100), (470, hz + 12), (560, hz + 12), (1400, 2100)])
    src(cx, hexc("#4E463E"))
    cx.fill()
    Wd.car(cx, 560, 1420, 1.45, t, door=1.0)
    Wd.ground_fog(cx, t, 1440, 0.32)
    Wd.grass_tufts(cx, t, 1700, 2000, 26, seed=3, wind=1.2, scale=1.6)
    cx.restore()


def s03_gate(cx, t):
    lt = t - 7.3
    cx.save()
    cam(cx, 1.08 - 0.03 * lt / 2.3, 540, 1000)
    hz = 900
    yard_bg(cx, t, hz, barn_at=(880, hz + 30, 0.42), seed=3)
    dirt(cx, [(330, 2000), (480, 1300), (560, hz + 30), (620, hz + 30), (700, 1300), (980, 2000)])
    # distant figure standing in the fog on the road
    p = infected_pose(600, hz + 120, t, s=0.42, f=-1, seed=4, moving=0.25)
    draw_infected(cx, Z4, p, fogged=0.55)
    Wd.fog_layer(cx, t, hz + 120, 80, 0.4, seed=31)
    Wd.fence(cx, 1340, t, gap=170, h=150, s=1.1, skip=(330, 760))
    ang = 1.05 + 0.18 * math.sin(lt * 1.6) + 0.08 * noise1(lt * 2, 7)
    Wd.gate(cx, 330, 1340, ang, 1.15)
    Wd.ground_fog(cx, t, 1360, 0.3)
    Wd.grass_tufts(cx, t, 1500, 1980, 30, seed=8, wind=1.3, scale=1.7)
    cx.restore()


def s04_runner(cx, t):
    lt = t - 9.6
    cx.save()
    cam(cx, 1.0, 540 - lt * 30, 960)
    hz = 1000
    yard_bg(cx, t, hz, barn_at=(150, hz + 20, 0.38), seed=4)
    Wd.fence(cx, hz + 190, t, gap=150, h=80, s=0.8)
    rx = 1150 - lt * 620
    p = run(Pose(x=rx, y=hz + 330, s=1.0, f=-1, t=t, eyes="wide", mouth="o", brows="worried",
                 mouth_open=0.7), t, 2.7, flail=False)
    Wd.lit(cx, lambda c: CIVILIAN.draw(c, p), TINT_DAY, 0.36, RIM_COLD, 0.3,
           1, (rx - 80, 0, rx + 80, 0))
    Wd.fog_layer(cx, t, hz + 320, 80, 0.25, seed=41)
    Wd.grass_tufts(cx, t, 1600, 1980, 30, seed=9, wind=1.4, scale=1.6)
    cx.restore()


def s05_infected(cx, t):
    lt = t - 10.9
    cx.save()
    cam(cx, 1.0 + 0.04 * lt / 2.1, 540, 1100)
    hz = 1180
    yard_bg(cx, t, hz, barn_at=(240, hz + 20, 0.55), seed=5)
    Wd.fence(cx, hz + 120, t, gap=150, h=90, s=0.8)
    zx = 760 - lt * 70
    p = infected_pose(zx, 1820, t, s=2.05, f=-1, seed=1)
    draw_infected(cx, Z2, p, rim_dir=1, rim_amt=0.4)
    Wd.ground_fog(cx, t, 1800, 0.35)
    Wd.grass_tufts(cx, t, 1820, 1990, 18, seed=10, wind=1.3, scale=2.0)
    cx.restore()


def window_outside_generic(t, wx, wy, ww, wh, darken=0.0, figures=None):
    def f(cx):
        cx.save()
        cx.translate(wx, wy)
        cx.scale(ww / FW, ww / FW)
        hz = 760
        Wd.sky(cx, t, hz + 10, seed=6)
        Wd.tree_line(cx, hz, hexc("#45524F"), seed=7, h=50)
        fields(cx, hz, t)
        Wd.fence(cx, hz + 230, t, gap=170, h=90, s=0.9)
        if figures:
            figures(cx)
        Wd.fog_layer(cx, t, hz + 200, 120, 0.4, seed=8)
        cx.restore()
        if darken:
            Wd.paint_rect(cx, (*CHARCOAL[:3], darken), wx, wy, ww, wh)
    return f


def s06_curtains(cx, t):
    lt = t - 13.0
    cx.save()
    cam(cx, 1.04, 540, 960)
    Wd.room_wall(cx, 1720, t)
    wx, wy, ww, wh = 300, 420, 600, 760
    close = ease_io(prog(lt, 0.25, 1.15))

    def figs(c):
        p = infected_pose(400 + t * 40, 1150, t, s=0.8, f=1, seed=2)
        draw_infected(c, Z3, p, fogged=0.2)

    Wd.window(cx, wx, wy, ww, wh, t, window_outside_generic(t, wx, wy, ww, wh, 0.0, figs),
              open_amt=1 - close, wind=0.3 * (1 - close) + 0.1)
    Wd.light_shaft(cx, [(wx, wy + wh), (wx + ww, wy + wh), (wx + ww + 200, FH), (wx - 100, FH)],
                   0.09 * (1 - close * 0.8), t=t)
    # hero pulling the curtain across: reaching arm, body turning away
    reach = 1 - smooth(prog(lt, 1.1, 1.4))
    hx = 210 + 40 * close
    p = hero_pose(hx, 1880, t, s=2.25, f=1, view="side", brows="worried", mouth="flat",
                  look=(0.6, -0.2), arm_b=150 * reach + 10 * (1 - reach), elb_b=-20 * reach + 10,
                  arm_a=120 * reach, elb_a=10, lean=-4)
    p = breathe(p, t)
    draw_hero(cx, p, TINT_ROOM, 0.3, RIM_COLD, 0.35, 1)
    Wd.vignette(cx, 0.3)
    cx.restore()


# ================================================================ SCENE 3 - the first decision
DX, DY, DW, DH = 330, 470, 400, 1060


def door_pane_view(t, crossing_t0=None, scale_fig=1.0):
    def pane(cx, rect):
        gx, gy, gw, gh = rect
        cx.save()
        cx.translate(gx, gy)
        k = gw / 520
        cx.scale(k, k)
        hz = 170
        Wd.sky(cx, t, hz, seed=9)
        cx.rectangle(0, hz, 600, 600)
        src(cx, hexc("#4A5853"))
        cx.fill()
        Wd.tree_line(cx, hz, hexc("#45524F"), seed=11, h=30)
        if crossing_t0 is not None:
            ct = t - crossing_t0
            if -0.5 < ct < 3.5:
                zx = -120 + ct * 230
                p = infected_pose(zx, 470, t, s=0.85 * scale_fig, f=1, seed=3, speed=0.65)
                draw_infected(cx, Z5, p, fogged=0.18)
        Wd.fog_layer(cx, t, 260, 60, 0.35, seed=12)
        cx.restore()
        Wd.paint_rect(cx, (0.55, 0.62, 0.66, 0.08), gx, gy, gw, gh)
    return pane


def s07a_door(cx, t):
    lt = t - 14.4
    cx.save()
    cam(cx, 1.0 + 0.05 * ease_io(prog(lt, 0, 2.9)), 600, 1060)
    Wd.room_wall(cx, DY + DH, t)
    Wd.door(cx, DX, DY, DW, DH, t, pane=door_pane_view(t, 14.6, 0.8))
    # cold daylight leaking under the door
    Wd.light_shaft(cx, [(DX, DY + DH), (DX + DW, DY + DH), (DX + DW + 120, DY + DH + 140), (DX - 120, DY + DH + 140)], 0.18, t=t)
    # reach -> hesitate -> pull back a little
    reach = kf(lt, [(0, 0.0), (0.5, 0.0), (1.4, 0.85), (1.9, 0.9), (2.5, 0.55), (2.9, 0.5)])
    tremble = math.sin(t * 23) * 2.5 * win(lt, 1.4, 1.8)
    p = hero_pose(900, 1820, t, s=2.2, f=-1, view="side", brows="worried", mouth="flat",
                  look=(-0.8, kf(lt, [(0, 0.1), (1.3, 0.25), (1.9, -0.3), (2.9, -0.35)])),
                  arm_b=12 + 78 * reach + tremble, elb_b=20 - 18 * reach, arm_a=10, elb_a=25,
                  lean=4 * reach, tilt=kf(lt, [(0, 0), (1.9, -6), (2.9, -4)]))
    p = breathe(p, t, 1.3)
    draw_hero(cx, p, TINT_ROOM, 0.3, RIM_COLD, 0.45, -1)
    Wd.vignette(cx, 0.35)
    cx.restore()


def s07b_pane(cx, t):
    lt = t - 17.3
    cx.save()
    gx, gy = DX + DW * 0.16, DY + DH * 0.07
    gw, gh = DW * 0.68, DH * 0.26
    cam(cx, 2.35 + 0.08 * lt / 2.9, gx + gw / 2, gy + gh / 2 + 120)
    Wd.room_wall(cx, DY + DH, t)
    Wd.door(cx, DX, DY, DW, DH, t, pane=door_pane_view(t, 17.3, 1.0))
    cx.restore()
    # over-the-shoulder: hero's head in the foreground, eyes tracking the infected
    track = kf(lt, [(0, -0.6), (1.0, -0.2), (2.0, 0.5), (2.9, 0.8)])
    p = hero_pose(980, 2500, t, s=3.4, f=-1, view="side", brows="worried", mouth="flat",
                  look=(-track, -0.2), tilt=-4, arm_a=10, arm_b=10)
    p = breathe(p, t, 1.4)
    draw_hero(cx, p, TINT_ROOM, 0.42, RIM_COLD, 0.3, -1)
    Wd.vignette(cx, 0.45)


def s08_bolt(cx, t):
    lt = t - 20.2
    cx.save()
    bx, by = DX + DW * 0.86, DY + DH * 0.47
    cam(cx, 3.4, bx - 30, by + 40)
    Wd.room_wall(cx, DY + DH, t)
    Wd.door(cx, DX, DY, DW, DH, t, bolt=ease_io(prog(lt, 0.85, 1.15)), pane=door_pane_view(t))
    # hand enters and turns the thumb-turn
    reach = ease_out(prog(lt, 0.2, 0.8)) - ease_in(prog(lt, 1.6, 2.2))
    hx = bx + 260 - 255 * reach
    hy = by + 140 - 120 * reach
    turn = ease_io(prog(lt, 0.85, 1.15))
    ex, ey = bx + 330, by + 260
    line(cx, [(ex + 200, ey + 300), (ex, ey), (hx + 4, hy + 6 - 6 * turn)], INK, 9)
    circle(cx, hx, hy - 4 * turn, 9)
    fs(cx, INK, None, 0)
    # sleeve
    line(cx, [(ex + 200, ey + 300), (ex + 40, ey + 40)], INK, 30)
    line(cx, [(ex + 200, ey + 300), (ex + 40, ey + 40)], hexc("#2F6FDB"), 22)
    Wd.paint_rect(cx, (*TINT_ROOM[:3], 0.22), bx - 400, by - 400, 1200, 1200)
    cx.restore()
    Wd.vignette(cx, 0.5)


# supplies - three quick practical inserts
def s09a_food(cx, t):
    lt = t - 22.5
    cx.save()
    cam(cx, 1.3, 540, 900 - lt * 50)
    Wd.room_wall(cx, 1800, t)
    Wd.shelf_supplies(cx, 180, 560, 720, 1.0)
    Wd.light_shaft(cx, [(1080, 400), (1080, 900), (300, 1700), (0, 1700), (0, 1300)], 0.08, t=t)
    Wd.dust(cx, t, (160, 500, 920, 1300), 20, seed=5)
    cx.restore()
    Wd.vignette(cx, 0.45)


def s09b_shelter(cx, t):
    lt = t - 23.4
    cx.save()
    cam(cx, 1.15 + 0.05 * lt, 540, 1080)
    hz = 960
    yard_bg(cx, t, hz, seed=12)
    Wd.farmhouse_ext(cx, 540, 1320, 1.75, t, lit_win=0.4)
    Wd.ground_fog(cx, t, 1330, 0.3)
    Wd.grass_tufts(cx, t, 1400, 1700, 24, seed=12, wind=1.1, scale=1.4)
    cx.restore()
    Wd.vignette(cx, 0.4)


def s09c_well(cx, t, power=1.0, lt0=24.25):
    lt = t - lt0
    cx.save()
    cam(cx, 1.12 + 0.04 * lt, 560, 1100)
    hz = 960
    yard_bg(cx, t, hz, pole_at=(980, 1330, 0.95), seed=13)
    Wd.wires(cx, [(980 - 42, 1330 - 494)], [(700, 1330 - 170 * 1.6 - 4)], t, sag=50)
    Wd.wires(cx, [(980 - 42, 1330 - 494)], [(1300, 1330 - 500)], t, sag=40)
    Wd.well_and_pump(cx, 440, 1330, 1.6, t, power=power)
    Wd.ground_fog(cx, t, 1340, 0.3)
    Wd.grass_tufts(cx, t, 1380, 1800, 30, seed=13, wind=1.1, scale=1.5)
    cx.restore()
    Wd.vignette(cx, 0.4)


# ================================================================ kitchen (safe moment / power fails)
def kitchen(cx, t, lamp_on, hero_fn=None, wind=0.25, extra=None):
    Wd.room_wall(cx, 1640, t)
    wx, wy, ww, wh = 560, 520, 420, 520
    Wd.window(cx, wx, wy, ww, wh, t, window_outside_generic(t, wx, wy, ww, wh, 0.0), open_amt=0.55, wind=wind)
    # counter + cabinets
    rrect(cx, 380, 1250, 760, 400, 4)
    fs(cx, hexc("#3B3A36"), INK, 4)
    rrect(cx, 360, 1220, 800, 40, 4)
    fs(cx, hexc("#6B6E6C"), INK, 4)
    for k in range(3):
        rrect(cx, 410 + k * 240, 1290, 210, 320, 4)
        fs(cx, hexc("#34332F"), INK, 3)
    rrect(cx, 80, 260, 380, 300, 4)
    fs(cx, hexc("#3A332D"), INK, 4)
    line(cx, [(270, 260), (270, 560)], INK, 4)
    if extra:
        extra(cx)
    Wd.ceiling_lamp(cx, 400, 330, on=lamp_on, sway=1.0, t=t, cord=330)
    Wd.light_shaft(cx, [(wx, wy + wh), (wx + ww, wy + wh), (wx + ww - 80, 1640), (wx - 300, 1640)], 0.10, t=t)
    if hero_fn:
        hero_fn(cx)
    Wd.room_light(cx, lamp_on)
    # when the power is gone the room sinks into cold shadow
    Wd.paint_rect(cx, (*MIDNIGHT[:3], 0.32 * (1 - lamp_on)))
    Wd.dust(cx, t, (500, 600, 1000, 1600), 22, seed=7, alpha=0.3)


def s10_safe(cx, t):
    lt = t - 25.4
    cx.save()
    cam(cx, 1.0 + 0.06 * ease_io(prog(lt, 0, 3.5)), 480, 1150)

    def hero(c):
        relax = win(lt, 0.6, 2.0)
        p = hero_pose(330, 1640, t, s=2.0, f=1, view="front",
                      brows="worried" if relax < 0.5 else "neutral", mouth="flat",
                      look=(kf(lt, [(0, 0.6), (1.2, 0.1), (3.5, 0.3)]), -0.1),
                      arm_a=8 + 4 * relax, arm_b=8 + 4 * relax, elb_a=12, elb_b=12)
        p = p.but(bob=4 * relax)
        p = breathe(p, t, 1.4 - 0.6 * relax)
        draw_hero(c, p, TINT_ROOM, 0.22, RIM_WARM, 0.3, 1)
    kitchen(cx, t, 1.0, hero)
    cx.restore()
    Wd.vignette(cx, 0.4)


def lamp_state(t):
    lt = t - 28.9
    if lt < 0.15:
        return 1.0
    if lt > 1.05:
        return 0.0
    # irregular flicker
    seq = [1, 0.15, 0.9, 0.0, 0.7, 0.05, 0.35, 0.0, 0.18, 0.0]
    i = int((lt - 0.15) / 0.09)
    return seq[min(i, len(seq) - 1)]


def s11_power(cx, t):
    lt = t - 28.9
    on = lamp_state(t)
    cx.save()
    cam(cx, 1.08, 450, 1050)

    def hero(c):
        up = win(lt, 0.2, 0.6)
        p = hero_pose(330, 1640, t, s=2.0, f=1, view="front", brows="worried", mouth="flat",
                      look=(-0.15, -0.9 * up), tilt=-6 * up, arm_a=12, arm_b=40 * win(lt, 1.0, 1.5), elb_b=60)
        p = breathe(p, t, 1.6)
        draw_hero(c, p, TINT_ROOM, 0.22 + 0.18 * (1 - on), mix(RIM_COLD, RIM_WARM, on), 0.35, 1)
    kitchen(cx, t, on, hero)
    cx.restore()
    Wd.vignette(cx, 0.45 + 0.15 * (1 - on))


def s12_faucet(cx, t):
    lt = t - 30.8
    cx.save()
    cam(cx, 1.0, 540, 1000)
    Wd.room_wall(cx, 1500, t, top=-200)
    rrect(cx, 600, 400, 420, 520, 4)
    src(cx, hexc("#4E5B62"))
    cx.fill()
    cx.restore()
    cx.save()
    cam(cx, 1.0 + 0.05 * lt / 2.4, 540, 1000)
    handle = ease_out(prog(lt, 0.25, 0.6))
    flow = 0.6 * (win(lt, 0.6, 0.7) - win(lt, 0.85, 1.05))
    drips = [prog(lt, 1.05, 1.45), prog(lt, 1.6, 2.05)]
    Wd.faucet(cx, 440, 1080, 2.4, handle=handle, flow=flow, t=t, drips=drips)
    # hand on the lever
    hx, hy = 440, 1080 - 2.4 * 2 - 2.4 * 70 * math.cos(handle * 0.9)
    hx += 2.4 * 70 * math.sin(handle * 0.9) * -1
    line(cx, [(-120, 760), (120, 820), (hx - 6, hy + 8)], INK, 18)
    circle(cx, hx, hy, 18)
    fs(cx, INK, None, 0)
    line(cx, [(-120, 760), (40, 800)], INK, 64)
    line(cx, [(-120, 760), (40, 800)], hexc("#2F6FDB"), 50)
    Wd.paint_rect(cx, (*MIDNIGHT[:3], 0.28), -500, -500, 2200, 3000)
    cx.restore()
    Wd.vignette(cx, 0.5)


# ================================================================ SCENE 4 - science
def flow_dots(cx, pts, t, speed, spacing, col, r, on=1.0, seed=0):
    """Particles moving along a polyline."""
    if on <= 0.01:
        return
    segs = []
    total = 0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L))
        total += L
    d = (t * speed) % spacing
    while d < total:
        acc = 0
        for a, b, L in segs:
            if acc + L >= d:
                k = (d - acc) / L
                x = a[0] + (b[0] - a[0]) * k
                y = a[1] + (b[1] - a[1]) * k
                circle(cx, x, y, r)
                src(cx, col, on)
                cx.fill()
                break
            acc += L
        d += spacing


def icon_bolt(cx, x, y, s, col):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    poly(cx, [(6, -40), (-18, 6), (-2, 6), (-8, 40), (18, -8), (2, -8), (10, -40)])
    src(cx, col)
    cx.fill()
    cx.restore()


def icon_pump(cx, x, y, s, col, ang):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    circle(cx, 0, 0, 30)
    cx.set_line_width(6)
    src(cx, col)
    cx.stroke()
    cx.rotate(ang)
    for k in range(4):
        cx.save()
        cx.rotate(k * math.pi / 2)
        poly(cx, [(0, -4), (22, -10), (22, 10), (0, 4)])
        src(cx, col)
        cx.fill()
        cx.restore()
    circle(cx, 0, 0, 6)
    src(cx, col)
    cx.fill()
    cx.restore()


def icon_drop(cx, x, y, s, col, level=1.0):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    cx.move_to(0, -38)
    cx.curve_to(16, -14, 28, 2, 28, 14)
    cx.curve_to(28, 32, 14, 42, 0, 42)
    cx.curve_to(-14, 42, -28, 32, -28, 14)
    cx.curve_to(-28, 2, -16, -14, 0, -38)
    cx.close_path()
    cx.set_line_width(5)
    src(cx, col)
    cx.stroke_preserve()
    cx.clip()
    cx.rectangle(-40, 42 - 82 * level, 80, 82 * level)
    src(cx, col)
    cx.fill()
    cx.restore()


def s13_science(cx, t):
    lt = t - 33.2
    # 1) exterior pump house (establish), power drops
    if lt < 1.5:
        s09c_well(cx, t, power=0.0, lt0=33.2)
        if lt > 1.2:
            Wd.paint_rect(cx, (*CHARCOAL[:3], 0.6 * prog(lt, 1.2, 1.5)))
        return
    g = lt - 1.5          # graphic time (0..~6.9)
    # blurred, darkened backdrop of the same location
    s09c_well(cx, t, power=0.0, lt0=33.2)
    Wd.paint_rect(cx, (*CHARCOAL[:3], 0.6 + 0.12 * prog(g, 0, 0.4)))
    a_in = ease_out(prog(g, 0, 0.5))
    off = prog(g, 2.4, 2.9)                # power switches off
    flow_on = 1 - smooth(prog(g, 2.6, 3.4))
    cx.save()
    cx.translate(0, 30 * (1 - a_in))
    # panel
    rrect(cx, 70, 300, 940, 1320, 28)
    src(cx, hexc("#121820", 0.82 * a_in))
    cx.fill_preserve()
    src(cx, hexc("#71818B", 0.35 * a_in))
    cx.set_line_width(2)
    cx.stroke()
    al = a_in
    soft = (*Wd.SOFT_WHITE[:3], al)
    dim = (*CGRAY[:3], al)
    amber = (*AMBER[:3], al)
    water = hexc("#8FB5C6", al)
    Wd.cairo_text(cx, "HOW MOST PRIVATE WELLS DELIVER WATER", 540, 382, 30, (*CGRAY[:3], al))
    # ---- cross-section diagram
    gy = 820                               # ground line
    line(cx, [(120, gy), (960, gy)], (*CGRAY[:3], 0.8 * al), 3)
    # soil hatch + aquifer
    cx.rectangle(120, gy, 840, 480)
    src(cx, hexc("#2A2622", 0.9 * al))
    cx.fill()
    cx.rectangle(120, gy + 330, 840, 150)
    src(cx, hexc("#24394A", 0.9 * al))
    cx.fill()
    Wd.cairo_text(cx, "GROUNDWATER", 830, gy + 420, 22, (*water[:3], 0.8 * al))
    # house + faucet (top right)
    hx0 = 700
    poly(cx, [(hx0, gy), (hx0, gy - 190), (hx0 + 120, gy - 290), (hx0 + 240, gy - 190), (hx0 + 240, gy)])
    cx.set_line_width(4)
    src(cx, soft)
    cx.stroke()
    # power line: pole -> pump cable down the casing
    px = 220
    line(cx, [(px, gy), (px, gy - 330)], dim, 6)
    line(cx, [(px - 40, gy - 310), (px + 40, gy - 310)], dim, 6)
    cable = [(px + 30, gy - 300), (420, gy - 120), (430, gy), (430, gy + 360)]
    cab_col = mix(AMBER, CGRAY, off)
    for a_, b_ in zip(cable, cable[1:]):
        line(cx, [a_, b_], (*cab_col[:3], 0.9 * al), 4)
    flow_dots(cx, cable, t, 260, 46, (*hexc("#FFD48A")[:3], al), 6, on=1 - off)
    # casing
    rrect(cx, 450, gy - 40, 50, 440, 6)
    src(cx, (*CGRAY[:3], 0.9 * al))
    cx.set_line_width(4)
    cx.stroke()
    # submersible pump in the aquifer
    pump_spin = t * 9 * flow_on
    rrect(cx, 452, gy + 330, 46, 90, 10)
    src(cx, (*mix(AMBER, CGRAY, off)[:3], al))
    cx.fill()
    icon_pump(cx, 475, gy + 375, 0.5, hexc("#121820", al), pump_spin)
    # water up the drop pipe -> to house
    level = 1 - smooth(prog(g, 2.8, 4.0))
    pipe = [(475, gy + 330), (475, gy - 30), (600, gy - 30), (600, gy - 90), (hx0 + 110, gy - 90)]
    for a_, b_ in zip(pipe, pipe[1:]):
        line(cx, [a_, b_], (*CGRAY[:3], 0.6 * al), 14)
        line(cx, [a_, b_], (*water[:3], 0.85 * al * level), 8)
    flow_dots(cx, pipe, t, 220, 40, (*hexc("#D5EEF7")[:3], al), 4, on=flow_on)
    # faucet in house
    line(cx, [(hx0 + 110, gy - 90), (hx0 + 140, gy - 90), (hx0 + 140, gy - 60)], soft, 8)
    if flow_on > 0.05:
        rrect(cx, hx0 + 134, gy - 56, 12, 50 * flow_on, 5)
        src(cx, (*water[:3], al * flow_on))
        cx.fill()
    Wd.cairo_text(cx, "ELECTRIC PUMP", 475 + 150, gy + 395, 22, (*mix(AMBER, CGRAY, off)[:3], al))
    # ---- icon chain: ELECTRICITY -> WELL PUMP -> RUNNING WATER
    cy = 1390
    nodes = [(220, "ELECTRICITY"), (540, "WELL PUMP"), (860, "RUNNING WATER")]
    seq_on = [prog(g, 0.4, 0.7), prog(g, 0.9, 1.2), prog(g, 1.4, 1.7)]
    states = [1 - off, 1 - smooth(prog(g, 2.7, 3.3)), 1 - smooth(prog(g, 3.1, 3.8))]
    for i, (x, lab) in enumerate(nodes):
        lvl = seq_on[i] * states[i]
        ring = mix(CGRAY, AMBER, lvl)
        circle(cx, x, cy, 92)
        src(cx, hexc("#0E1318", al))
        cx.fill_preserve()
        src(cx, (*ring[:3], al))
        cx.set_line_width(4)
        cx.stroke()
        col = (*mix(hexc("#46525A"), AMBER if i < 2 else hexc("#9CC7D8"), seq_on[i] * states[i])[:3], al)
        if i == 0:
            icon_bolt(cx, x, cy, 1.25, col)
        elif i == 1:
            icon_pump(cx, x, cy, 1.4, col, t * 6 * flow_on)
        else:
            icon_drop(cx, x, cy + 4, 1.25, col, level=max(0.0, states[i]))
        Wd.cairo_text(cx, lab, x, cy + 140, 25, (*mix(CGRAY, Wd.SOFT_WHITE, lvl)[:3], al))
        if i < 2:
            ax0, ax1 = x + 104, nodes[i + 1][0] - 104
            acol = mix(CGRAY, AMBER, seq_on[i + 1] * states[i + 1])
            line(cx, [(ax0, cy), (ax1 - 10, cy)], (*acol[:3], 0.9 * al), 4)
            poly(cx, [(ax1, cy), (ax1 - 16, cy - 10), (ax1 - 16, cy + 10)])
            src(cx, (*acol[:3], 0.9 * al))
            cx.fill()
    # power-off mark over the electricity node
    if off > 0:
        k = ease_out(off)
        line(cx, [(220 - 60, cy - 60), (220 - 60 + 120 * k, cy - 60 + 120 * k)], (*hexc("#C46A4F")[:3], al), 8)
    # accuracy note: backups exist, not all wells are electric
    na = prog(g, 4.2, 4.7) * al
    if na > 0:
        Wd.cairo_text(cx, "NO BACKUP POWER = NO PUMP", 540, 1570, 30, (*AMBER[:3], na))
    cx.restore()
    fa = prog(g, 4.9, 5.3)
    if fa > 0:
        Wd.cairo_text(cx, "Generators, battery backup or a hand pump", 540, 1690, 28, (*CGRAY[:3], fa))
        Wd.cairo_text(cx, "can keep a well usable during an outage.", 540, 1730, 28, (*CGRAY[:3], fa))
    Wd.vignette(cx, 0.3)


# ================================================================ realization
def s14_water(cx, t):
    lt = t - 41.6
    cx.save()
    cam(cx, 1.55 + 0.12 * ease_io(prog(lt, 0, 4.0)), 420, 1080)

    def extra(c):
        # nearly empty water jug on the counter
        rrect(c, 760, 1060, 120, 160, 18)
        src(c, hexc("#9AB1BA", 0.35))
        c.fill_preserve()
        src(c, INK)
        c.set_line_width(3)
        c.stroke()
        rrect(c, 762, 1190, 116, 28, 8)
        src(c, hexc("#8FB5C6", 0.6))
        c.fill()
        rrect(c, 795, 1036, 50, 28, 6)
        fs(c, hexc("#5C6569"), INK, 3)

    def hero(c):
        look_down = win(lt, 0.4, 1.2) - win(lt, 2.6, 3.2)
        p = hero_pose(400, 1640, t, s=2.0, f=1, view="front", brows="worried", mouth="flat",
                      look=(0.6 * look_down + 0.0, 0.5 * look_down - 0.1), tilt=6 * look_down,
                      arm_a=14, arm_b=18 + 6 * math.sin(t * 3.1), elb_b=30)
        p = breathe(p, t, 1.5)
        if lt > 2.9:
            p = p.but(mouth="frown")
        draw_hero(c, p, TINT_ROOM, 0.4, RIM_COLD, 0.4, 1)
    kitchen(cx, t, 0.0, hero, extra=extra)
    cx.restore()
    Wd.vignette(cx, 0.55)


def living_room(cx, t, open_amt=0.08, hero_fn=None, outside_figs=None, darken=0.0, wind=0.25):
    Wd.room_wall(cx, 1680, t)
    wx, wy, ww, wh = 420, 460, 520, 700
    Wd.window(cx, wx, wy, ww, wh, t, window_outside_generic(t, wx, wy, ww, wh, darken, outside_figs),
              open_amt=open_amt, wind=wind)
    Wd.light_shaft(cx, [(wx + ww * 0.4, wy + wh), (wx + ww * 0.6, wy + wh), (wx + ww * 0.9, 1900), (wx + ww * 0.2, 1900)],
                   0.12, t=t)
    # couch silhouette + lamp (off)
    rrect(cx, -60, 1380, 360, 300, 30)
    fs(cx, hexc("#2F3A36"), INK, 4)
    rrect(cx, -60, 1300, 360, 140, 30)
    fs(cx, hexc("#35413C"), INK, 4)
    if hero_fn:
        hero_fn(cx)
    Wd.paint_rect(cx, (*MIDNIGHT[:3], 0.25))


def s15_away(cx, t):
    lt = t - 45.6
    cx.save()
    cam(cx, 1.0, 540 - lt * 18, 1000)

    def hero(c):
        # slow, careful sidestep away from the window, eyes on it
        k = ease_io(prog(lt, 0.2, 2.6))
        x = 760 - 470 * k
        p = hero_pose(x, 1840, t, s=2.15, f=1, view="side", brows="worried", mouth="flat",
                      look=(0.9, -0.15), lean=-6)
        p = walk(p, t, 0.55, 0.45 * (1 - win(lt, 2.4, 2.8)), arms=False)
        p = p.but(arm_a=-10, elb_a=40, arm_b=30, elb_b=50)
        p = breathe(p, t, 0.8)
        draw_hero(c, p, TINT_ROOM, 0.36, RIM_COLD, 0.45, 1)
    living_room(cx, t, 0.08, hero)
    cx.restore()
    Wd.vignette(cx, 0.55)


# ================================================================ SCENE 5 - the rooster
def s16_rooster(cx, t):
    lt = t - 48.5
    cx.save()
    cam(cx, 1.0 + 0.05 * ease_io(prog(lt, 0, 3.4)), 560, 1150)
    hz = 1000
    yard_bg(cx, t, hz, barn_at=(250, hz + 40, 0.75), house_at=(900, hz + 70, 0.5), seed=16)
    Wd.fence(cx, 1460, t, gap=230, h=170, s=1.2)
    crow = win(lt, 1.75, 2.15) * (1 - win(lt, 3.0, 3.3))
    Wd.lit(cx, lambda c: Wd.rooster(c, 610, 1460 - 170 * 1.2 + 8, 1.65, t, crow=crow),
           TINT_DAY, 0.25, RIM_COLD, 0.3, 1, (480, 0, 760, 0))
    Wd.ground_fog(cx, t, 1500, 0.32)
    Wd.grass_tufts(cx, t, 1560, 1980, 28, seed=16, wind=1.1, scale=1.7)
    cx.restore()
    Wd.vignette(cx, 0.4)


def s17_stop(cx, t):
    lt = t - 51.9
    cx.save()
    cam(cx, 1.02, 540, 1050)
    hz = 960
    yard_bg(cx, t, hz, barn_at=(880, hz + 30, 0.5), seed=17)
    Wd.fence(cx, hz + 160, t, gap=150, h=80, s=0.8)
    stops = [0.45, 0.75, 0.6]
    figs = [(Z1, 1, 260, 1350, 1.0, 1), (Z3, 3, 640, 1240, 0.75, -1), (Z4, 4, 820, 1480, 1.2, -1)]
    for (fig, sd, x0, y, s, f), st in zip(figs, stops):
        m = 1 - smooth(prog(lt, st, st + 0.5))
        # integrate a bit of travel until they stop
        trav = min(lt, st + 0.25)
        x = x0 + f * trav * 55 * s
        p = infected_pose(x, y, t, s=s, f=f, seed=sd, moving=m)
        draw_infected(cx, fig, p, fogged=0.25 * (1.2 - s))
    Wd.ground_fog(cx, t, 1420, 0.3)
    Wd.grass_tufts(cx, t, 1600, 1980, 26, seed=17, wind=0.9, scale=1.6)
    cx.restore()
    Wd.vignette(cx, 0.45)


def turning_head(cx, t, lt, fig, seed, x, y, s, f, turn_at, fogged=0.0, push=0.0):
    k = smooth(prog(lt, turn_at, turn_at + 0.9))
    p = infected_pose(x, y, t, s=s, f=f, seed=seed, moving=0.0)
    if k > 0.5:
        p.view = "front"
        p.look = (0.0, -0.05)
        p.tilt = p.tilt * (1 - k) + 4
        p.arm_a, p.arm_b = 10, 6
    else:
        p.tilt = p.tilt + 18 * (k / 0.5)
    draw_infected(cx, fig, p, fogged=fogged, rim_amt=0.35)


def s18_turn1(cx, t):
    lt = t - 54.2
    cx.save()
    cam(cx, 1.0 + 0.1 * ease_io(prog(lt, 0, 1.6)), 540, 1050)
    hz = 1150
    yard_bg(cx, t, hz, barn_at=(180, hz + 20, 0.5), seed=18)
    Wd.fence(cx, hz + 120, t, gap=150, h=90, s=0.8)
    turning_head(cx, t, lt, Z4, 4, 560, 1820, 2.25, -1, 0.25)
    Wd.ground_fog(cx, t, 1820, 0.35)
    cx.restore()
    Wd.vignette(cx, 0.5)


def s19_turn2(cx, t):
    lt = t - 55.8
    cx.save()
    cam(cx, 1.05, 540, 1100)
    hz = 1050
    yard_bg(cx, t, hz, seed=19)
    Wd.fence(cx, hz + 160, t, gap=150, h=80, s=0.8)
    # first one, already facing us, soft in the background
    p = infected_pose(250, 1330, t, s=0.9, f=1, seed=4, moving=0.0, view="front", look=(0.0, -0.05))
    draw_infected(cx, Z4, p, fogged=0.35)
    turning_head(cx, t, lt, Z3, 3, 700, 1700, 1.75, 1, 0.1)
    Wd.ground_fog(cx, t, 1700, 0.35)
    cx.restore()
    Wd.vignette(cx, 0.5)


# ================================================================ SCENE 6 - they found me
def s20_approach(cx, t):
    lt = t - 56.8
    cx.save()
    cam(cx, 1.0, 540, 960, dy=lt * 10)
    hz = 1420      # low camera: horizon sits low, figures tower
    Wd.sky(cx, t, hz + 10, seed=20)
    Wd.farmhouse_ext(cx, 860, hz + 40, 1.0, t)
    Wd.tree_line(cx, hz, hexc("#34403D"), seed=21, h=30)
    fields(cx, hz, t)
    figs = [(Z5, 5, 860, 0.12, 1.9, 1700), (Z1, 1, 220, 0.0, 2.3, 1860), (Z3, 3, 560, 0.25, 2.9, 2060)]
    for fig, sd, x, ph, s, fy in figs:
        grow = 1 + 0.12 * lt
        p = infected_pose(x, fy + 40 * lt, t + ph, s=s * grow, f=1 if x < 540 else -1, seed=sd,
                          speed=0.5, view="front", look=(0.0, 0.2))
        p.lean = 4
        draw_infected(cx, fig, p, rim_amt=0.25)
    Wd.ground_fog(cx, t, hz + 330, 0.38)
    Wd.grass_tufts(cx, t, 1760, 1990, 30, seed=22, wind=1.0, scale=2.2, color=hexc("#232E29"))
    cx.restore()
    Wd.vignette(cx, 0.55)


def s21_stepback(cx, t):
    lt = t - 58.0
    cx.save()
    cam(cx, 1.02, 600, 1000)

    def figs(c):
        for fig, sd, x in [(Z1, 1, 360), (Z3, 3, 640)]:
            p = infected_pose(x, 1250, t, s=1.0, f=1, seed=sd, speed=0.45, view="front")
            silhouette(c, fig, p, hexc("#2C3439"), 0.85)

    def hero(c):
        k = ease_io(prog(lt, 0.15, 1.3))
        p = hero_pose(760 - 230 * k, 1880, t, s=2.3, f=1, view="side", brows="worried",
                      mouth="flat" if k < 0.6 else "o", mouth_open=0.4, eyes="wide" if k > 0.5 else "open",
                      look=(0.9, -0.1), lean=-8 * k)
        if 0.1 < k < 0.95:
            ph = (k * 1.0) * math.pi
            p = p.but(hip_a=-18 * math.sin(ph), hip_b=12 * math.sin(ph), knee_a=14, knee_b=8)
        p = p.but(arm_a=-20 * k, elb_a=40, arm_b=40 * k, elb_b=70)
        p = breathe(p, t, 2.0)
        draw_hero(c, p, TINT_ROOM, 0.36, RIM_COLD, 0.5, 1)
    living_room(cx, t, 0.5, hero, figs, wind=0.1)
    cx.restore()
    Wd.vignette(cx, 0.6)


def palm(cx, x, y, s, alpha=1.0, col=hexc("#9FA7A0")):
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 46, 54)
    for k, (dx, dy, l) in enumerate([(-34, -50, 44), (-12, -66, 54), (12, -68, 56), (32, -56, 46)]):
        rrect(cx, dx - 9, dy - l * 0.5, 18, l, 9)
    rrect(cx, 34, -10, 40, 18, 9)
    src(cx, col, alpha)
    cx.fill()
    cx.restore()


def s22_found(cx, t):
    lt = t - 59.5
    strike = 63.6
    sx, sy = hshake(t, strike, 22)
    cx.save()
    cam(cx, 1.0 + 0.12 * ease_io(prog(lt, 0, 4.1)), 640, 1000, dx=sx, dy=sy)
    rise = ease_out(prog(lt, 0.2, 1.4))

    def figs(c):
        # big silhouette right behind the glass
        p = infected_pose(560, 1980 + 1300 * (1 - rise), t, s=5.6, f=1, seed=2, moving=0.0, view="front")
        p.arm_a, p.arm_b = 10, 10
        silhouette(c, Z2, p, hexc("#1A2026"), 0.92)

    def outside(c):
        win_draw = window_outside_generic(t, 420, 460, 520, 700, 0.15, figs)
        win_draw(c)

    Wd.room_wall(cx, 1680, t)
    wx, wy, ww, wh = 420, 460, 520, 700
    Wd.window(cx, wx, wy, ww, wh, t, outside, open_amt=0.9, wind=0.08)
    # hand pressing against the glass
    press = ease_out(prog(lt, 1.6, 2.3))
    if press > 0:
        pull = ease_in(prog(t, strike - 0.25, strike - 0.03))
        hit = prog(t, strike - 0.03, strike + 0.02)
        hs = 1.15 + 0.12 * pull - 0.1 * hit
        cx.save()
        rrect(cx, wx, wy, ww, wh, 2)
        cx.clip()
        # condensation halo around the palm
        cx.set_source(rgrad(cx, 690, 760, 0, 160, [(0, hexc("#C9D3D6", 0.25 * press)), (1, hexc("#C9D3D6", 0))]))
        cx.paint()
        palm(cx, 690, 780 + 30 * (1 - press), hs, 0.95 * press * (1 - 0.35 * pull + 0.35 * hit))
        cx.restore()
    Wd.light_shaft(cx, [(wx + 100, wy + wh), (wx + ww - 100, wy + wh), (wx + ww + 60, 1900), (wx, 1900)], 0.1, t=t)
    # protagonist in the foreground, frozen
    p = hero_pose(250, 2120, t, s=2.6, f=1, view="side", brows="worried", mouth="flat",
                  eyes="wide" if lt > 1.9 else "open", look=(0.9, -0.35), lean=-6, tilt=-4,
                  arm_a=-10, elb_a=40, arm_b=20, elb_b=60, blink=lt < 1.6)
    p = breathe(p, t, 0.6 if lt > 2 else 1.8)
    draw_hero(cx, p, TINT_ROOM, 0.4, RIM_COLD, 0.55, 1)
    Wd.paint_rect(cx, (*MIDNIGHT[:3], 0.2), -400, -400, 2000, 3000)
    cx.restore()
    Wd.vignette(cx, 0.65)


def s23_end(cx, t):
    lt = t - 63.68
    Wd.paint_rect(cx, hexc("#07090C"))
    a = ease_out(prog(lt, 0.45, 0.9))
    if a > 0:
        Wd.title(cx, "THEY FOUND ME", 540, 960, 92, a)
    b = ease_out(prog(lt, 1.3, 1.7))
    if b > 0:
        Wd.cairo_text(cx, "PART 2", 540, 1080, 36, (*AMBER[:3], b))
        line(cx, [(440, 1102), (640, 1102)], (*AMBER[:3], 0.6 * b), 2)


# ================================================================ timeline
SHOTS = [
    (0.0, 5.1, s01),
    (5.1, 7.3, s02_car),
    (7.3, 9.6, s03_gate),
    (9.6, 10.9, s04_runner),
    (10.9, 13.0, s05_infected),
    (13.0, 14.4, s06_curtains),
    (14.4, 17.3, s07a_door),
    (17.3, 20.2, s07b_pane),
    (20.2, 22.5, s08_bolt),
    (22.5, 23.4, s09a_food),
    (23.4, 24.25, s09b_shelter),
    (24.25, 25.4, s09c_well),
    (25.4, 28.9, s10_safe),
    (28.9, 30.8, s11_power),
    (30.8, 33.2, s12_faucet),
    (33.2, 41.6, s13_science),
    (41.6, 45.6, s14_water),
    (45.6, 48.5, s15_away),
    (48.5, 51.9, s16_rooster),
    (51.9, 54.2, s17_stop),
    (54.2, 55.8, s18_turn1),
    (55.8, 56.8, s19_turn2),
    (56.8, 58.0, s20_approach),
    (58.0, 59.5, s21_stepback),
    (59.5, 63.68, s22_found),
    (63.68, 66.4, s23_end),
]
DURATION = 66.4

# short cinematic accents (text, t0, t1, style)
ACCENTS = [
    ("DAY 1", 0.35, 4.7, "tag"),
    ("POWER FAILURE", 29.35, 30.75, "accent"),
    ("NO RUNNING WATER", 31.75, 33.15, "accent"),
]


def shot_at(t):
    for a, b, fn in SHOTS:
        if a <= t < b:
            return fn
    return SHOTS[-1][2]

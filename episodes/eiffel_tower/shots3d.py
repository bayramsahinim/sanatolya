"""3D side of every shot: set, lighting, camera path, animated objects, character anchors.

usage: python -m episodes.eiffel_tower.shots3d <shot_id> [--test] [--frames a:b]
Writes build/frames/<shot>/bg_####.png (+ fg_####.png) and anchors.json.
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

from cinecode import b3d
from cinecode.b3d import hexrgb, interp_keys
from episodes.eiffel_tower import sets3d as S
from episodes.eiffel_tower.timeline import FPS, frames, shot

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "build", "frames")
SHOTS = {}


def reg(res=(540, 960), samples=16, fg=False):
    def deco(fn):
        SHOTS[fn.__name__] = dict(fn=fn, res=res, samples=samples, fg=fg)
        return fn
    return deco


class Ctx:
    """What a shot builder returns: camera keys + per-frame animation + anchors."""

    def __init__(self):
        self.cam_keys = None      # [(t, (cx,cy,cz, tx,ty,tz, lens))]
        self.anim = None          # fn(t)
        self.anchors = {}         # name -> point or fn(t)->point
        self.dof = None           # (focus_distance or target name, fstop)


def golden_day(sun_rot=(70, -125), energy=3.2, haze=(380, 2600, 0.85)):
    b3d.sun(energy, rot=(math.radians(sun_rot[0]), 0, math.radians(sun_rot[1])), color=(1.0, 0.78, 0.52), angle=1.0)
    b3d.world_gradient(hexrgb("#6d92bd"), hexrgb("#f6c98e"), 1.25, mid=hexrgb("#d8c7a6"),
                       sun_dir=_sun_vec(sun_rot), sun_glow=(0.9, 0.5, 0.2))
    return haze


def _sun_vec(sun_rot):
    from mathutils import Euler
    d = Vector((0, 0, 1))
    d.rotate(Euler((math.radians(sun_rot[0]), 0, math.radians(sun_rot[1]))))
    return tuple(d)


def city_world(m, lit=False):
    S.eiffel_tower(mats=m)
    S.city(m, lit=lit)


# ---------------------------------------------------------------- shots
@reg(res=(720, 1280), samples=20, fg=True)
def s01_deal(m, C):
    _salon(m, docs=False)
    b3d.use_collection(bpy.data.collections["FG"])
    S.paper("d1", S.T("contract"), 0.21, 0.29, (0.05, 0.25, 0.8), rot=(0, 0, 0.15))
    env = S.envelope("env", (-0.4, 0.0, 0.81), thick=0.022)
    cash = S.cash_stack("cashpeek", (0, 0.0, 0.0), n=2, size=(0.15, 0.07))
    cash.parent = env
    cash.location = (0.06, 0.0, 0.004)

    def anim(t):
        u = b3d.ease_io(min(1, max(0, (t - 0.05) / 1.15)))
        env.location = (-0.42 + 0.78 * u, -0.02 + 0.06 * u, 0.812)
        env.rotation_euler = (0, 0, 0.35 - 0.3 * u)
    C.anim = anim
    C.cam_keys = [(0, (0.0, -1.55, 1.12, 0.0, 0.5, 0.98, 30)), (1.75, (0.05, -1.35, 1.1, 0.05, 0.5, 0.98, 31))]
    C.anchors = {"env": lambda t: tuple(env.matrix_world.translation), "lustig": (0.55, 0.95, 0.0), "poisson": (-0.55, 0.95, 0.0)}
    C.dof = ("env", 2.0)


@reg(res=(540, 960), samples=12)
def s02_tower(m, C):
    city_world(m)
    h = golden_day((72, -140))
    b3d.add_haze(hexrgb("#efc996"), *h)
    C.cam_keys = [(0, (95, -170, 3, 0, 0, 120, 20)), (1.35, (88, -158, 14, 0, 0, 155, 20))]


@reg(res=(1080, 1920), samples=48)
def s03_problem(m, C):
    city_world(m)
    h = golden_day((70, -150))
    b3d.add_haze(hexrgb("#efc996"), *h)
    C.cam_keys = [(0, (1.0, -233.6, 1.05, -3, -180, 36, 22))]
    C.anchors = {"lustig": (0.35, -231.0, 0.0)}


@reg(res=(1080, 1920), samples=48)
def s04_own(m, C):
    city_world(m)
    h = golden_day((70, -150))
    b3d.add_haze(hexrgb("#efc996"), *h)
    C.cam_keys = [(0, (1.3, -233.4, 1.45, -1.0, -200, 7, 30))]
    C.anchors = {"lustig": (1.05, -229.6, 0.0)}


@reg(res=(540, 960), samples=12)
def s05_aerial(m, C):
    city_world(m)
    S.street_detail(m)
    car, wheels = S.vintage_car("car1", "#1d2a3a", m)
    car.location = (395, 25.5, 0)
    h = golden_day((70, -140))
    b3d.add_haze(hexrgb("#efc996"), *h)

    def anim(t):
        car.location = (395 + 7 * t, 25.5, 0)
    C.anim = anim
    C.cam_keys = [(0, (760, -260, 330, 200, 30, 40, 26)), (1.2, (580, 20, 110, 400, 26, 6, 28)),
                  (2.3, (447, 28.5, 12, 418, 23.5, 1.5, 28))]


def _cafe_common(m):
    city_world(m)
    S.street_detail(m)
    h = golden_day((68, -100))
    return h


@reg(res=(540, 960), samples=12)
def s06_cafe(m, C):
    h = _cafe_common(m)
    car, wheels = S.vintage_car("car1", "#1d2a3a", m)
    car.rotation_euler = (0, 0, math.pi)
    car2, w2 = S.vintage_car("car2", "#5a1e1a", m)
    b3d.add_haze(hexrgb("#efc996"), *h)

    def anim(t):
        car.location = (431 - 9.5 * t, 31.0, 0)
        for w in wheels:
            w.rotation_euler = (0, -t * 22, 0)
        car2.location = (395 + 7.0 * t, 25.0, 0)
    C.anim = anim
    C.cam_keys = [(0, (420.6, 21.75, 1.35, 416.3, 23.1, 1.25, 28)), (2.65, (420.1, 21.8, 1.35, 416.1, 23.2, 1.25, 28))]
    C.anchors = {"lustig": (417.72, 22.35, 0.63), "table": (417.1, 22.3, 0.91)}


@reg(res=(720, 1280), samples=14)
def s07_headline(m, C):
    h = _cafe_common(m)
    b3d.add_haze(hexrgb("#efc996"), *h)
    np_ = S.paper("news", S.T("newspaper"), 0.56, 0.76, (417.25, 22.35, 1.25), rot=(math.radians(90), 0, math.radians(-90)))

    def anim(t):
        np_.rotation_euler = (math.radians(90 + 2 * math.sin(t * 2)), 0, math.radians(-90 + 1.5 * math.sin(t * 1.3)))
    C.anim = anim
    C.cam_keys = [(0, (416.35, 22.42, 1.38, 417.25, 22.36, 1.42, 32)), (1.65, (416.62, 22.38, 1.44, 417.25, 22.36, 1.47, 32))]
    C.anchors = {"paper_l": (417.25, 22.07, 1.18), "paper_r": (417.25, 22.63, 1.18)}
    C.dof = (0.85, 2.0)


@reg(res=(1080, 1920), samples=40)
def s08_idea(m, C):
    h = _cafe_common(m)
    b3d.add_haze(hexrgb("#efc996"), *h)
    C.cam_keys = [(0, (415.5, 21.75, 1.25, 417.72, 22.35, 1.05, 34))]
    C.anchors = {"lustig": (417.72, 22.35, 0.63)}
    C.dof = (1.5, 2.8)


def _forge_letter(m):
    S.forge_desk(m)
    let = S.paper("letter", S.T("letter"), 0.21, 0.29, (0.0, -0.06, 0.7695))
    return let


@reg(res=(720, 1280), samples=24)
def s09_forge(m, C):
    let = _forge_letter(m)
    pen = S.fountain_pen("pen", m)
    # signature curve on the letter (letter texture: 1100x1500 px -> 0.21x0.29 m)
    pts = []
    for i in range(60):
        u = i / 59
        px = 620 + u * 330
        py = 1220 - 40 * math.sin(u * 14) * (1 - u * 0.5) - u * 30
        pts.append(((px / 1100 - 0.5) * 0.21, (0.5 - py / 1500) * 0.29 - 0.06, 0.7702))
    cd = bpy.data.curves.new("sig", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.0009
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1)
    sig = bpy.data.objects.new("sig", cd)
    b3d.link(sig)
    cd.materials.append(b3d.mat("ink", hexrgb("#141838"), rough=0.2))

    def anim(t):
        u = min(1, max(0, (t - 0.0) / 0.45))
        let.location = (0.25 * (1 - b3d.ease_io(u)), -0.06, 0.7695)
        s = min(1, max(0, (t - 0.6) / 1.1))
        cd.bevel_factor_end = max(0.001, s)
        k = min(len(pts) - 1, int(s * (len(pts) - 1)))
        tip = Vector(pts[k])
        lift = 0.0 if 0 < s < 1 else 0.03
        if t < 0.6:
            lift = 0.06 * (1 - (t / 0.6)) + 0.005
            tip = Vector(pts[0])
        pen.location = tip + Vector((0, 0, lift))
        pen.rotation_euler = (math.radians(-28), math.radians(18), 0)
    C.anim = anim
    C.cam_keys = [(0, (0.02, -0.42, 1.08, 0.04, -0.12, 0.77, 45)), (1.9, (0.06, -0.36, 1.0, 0.06, -0.15, 0.77, 48))]
    C.anchors = {"pen_top": lambda t: tuple(bpy.data.objects["pen"].matrix_world @ Vector((0, 0, 0.05)))}
    C.dof = ("pen_tip", 2.8)


@reg(res=(720, 1280), samples=24)
def s10_stamp(m, C):
    let = S.paper("letter", S.T("letter_signed"), 0.21, 0.29, (0.0, -0.06, 0.7695))
    S.forge_desk(m)
    mark = S.paper("mark", S.T("stamp_mark"), 0.07, 0.07, (-0.05, -0.155, 0.7705))
    _alpha_mat(mark)
    st = S.rubber_stamp("stamp", m)

    def anim(t):
        # down 0.15->0.38, hold, up 0.6->0.9
        if t < 0.38:
            z = 0.25 * (1 - b3d.ease_io(min(1, max(0, (t - 0.1) / 0.28))))
        elif t < 0.6:
            z = 0.0
        else:
            z = 0.2 * b3d.ease_io(min(1, (t - 0.6) / 0.35))
        st.location = (-0.05, -0.155, 0.7705 + z)
        mark.hide_render = t < 0.4
    C.anim = anim
    C.cam_keys = [(0, (0.2, -0.62, 1.12, -0.04, -0.13, 0.82, 38)), (1.1, (0.18, -0.58, 1.1, -0.04, -0.14, 0.82, 40))]
    C.anchors = {"knob": lambda t: tuple(bpy.data.objects["stamp"].matrix_world @ Vector((0, 0, 0.12)))}


def _alpha_mat(ob):
    m = ob.active_material
    nt = m.node_tree
    tex = [n for n in nt.nodes if n.type == "TEX_IMAGE"][0]
    b = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])


@reg(res=(720, 1280), samples=20, fg=True)
def s11_letters(m, C):
    fgc = b3d.collection("FG")
    S.office(m)
    S.paper("bill", S.T("contract"), 0.21, 0.29, (-0.4, 0.05, 0.775), rot=(0, 0, 0.3))
    for n in ("desk", "blotter", "lamp_base", "lamp_stem", "lamp_shade", "bill"):
        o = bpy.data.objects[n]
        for c in list(o.users_collection):
            c.objects.unlink(o)
        fgc.objects.link(o)
    b3d.use_collection(fgc)
    env = S.envelope("env", (0, -0.05, 0.79), addressed=True)
    b3d.use_collection(bpy.data.collections["BG"])

    def anim(t):
        u = min(1, max(0, t / 0.42))
        e = b3d.ease_io(u) if u < 1 else 1
        env.location = (0.3 * (1 - e) + 0.02, -0.12 - 0.15 * (1 - e), 0.79 + 0.55 * (1 - u) ** 2)
        env.rotation_euler = (0.6 * (1 - e), 0.2 * (1 - e), -0.15 + 0.9 * (1 - e))
    C.anim = anim
    C.cam_keys = [(0, (0.05, -1.25, 1.22, 0.0, 0.25, 0.95, 32)), (1.0, (0.05, -1.15, 1.2, 0.0, 0.25, 0.97, 33))]
    C.anchors = {"poisson": (0.0, 0.62, 0.47)}


@reg(res=(540, 960), samples=12)
def s12_lobby(m, C):
    S.lobby(m)

    def lpos(t):
        return (0.2, 5.0 + 1.3 * t, 0.0)
    C.cam_keys = [(0, (-1.6, 3.6, 1.5, 0.5, 7.0, 1.2, 26)), (1.2, (-1.4, 5.1, 1.5, 0.5, 8.6, 1.2, 26))]
    C.anchors = {"lustig": lpos}


def _salon(m, docs=True, fg=True, seed=0):
    fgc = b3d.collection("FG")
    S.meeting_room(m)
    b3d.use_collection(fgc)
    for n in ("table", "runner"):
        ob = bpy.data.objects[n]
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        fgc.objects.link(ob)
    S.table_dressing(m, docs=docs, seed=seed)
    b3d.use_collection(bpy.data.collections["BG"])


SALON_SEATS = {"d1": (-1.3, 1.02, 0.47), "poisson": (0.0, 1.02, 0.47), "d3": (1.3, 1.02, 0.47), "d4": (2.65, 0.0, 0.47),
               "lustig": (-2.45, 0.05, 0.0)}


@reg(res=(1080, 1920), samples=40, fg=True)
def s13_meeting(m, C):
    _salon(m)
    C.cam_keys = [(0, (0.6, -3.9, 1.6, -1.0, 0.5, 1.05, 22))]
    C.anchors = dict(SALON_SEATS)


@reg(res=(540, 960), samples=12)
def s14_plan(m, C):
    S.blueprint_set(m)
    bands = S.eiffel_tower(mats=m, banded=True)
    b3d.sun(3.0, rot=(math.radians(50), 0, math.radians(-150)), color=(1, 0.85, 0.65), angle=3)
    tag = S.paper("tag", S.T("tag_7000"), 70, 38, (0, -150, 40), rot=(math.radians(90), 0, 0))
    hb = [(0, 57), (57, 115), (115, 180), (180, 235), (235, 330)]
    lay = [(-330, -40), (-170, -40), (-20, -40), (120, -40), (250, -40)]

    def anim(t):
        rise = b3d.ease_io(min(1, t / 0.7))
        sep = b3d.ease_io(min(1, max(0, (t - 0.9) / 1.2)))
        fall = b3d.ease_io(min(1, max(0, (t - 2.85) / 1.5)))
        for k, ob in enumerate(bands):
            z0, z1 = hb[k]
            # stage 1: separate vertically & slightly outward
            dz = k * 22 * sep
            dx = (k - 2) * 14 * sep
            # stage 2: lay down as scrap piles
            cz = (z0 + z1) / 2
            lx, ly = lay[k]
            p_stand = Vector((dx, 0, dz))
            # when lying, rotate 90deg around x; centre of band goes to ground
            ob.rotation_euler = (math.radians(90) * fall, 0, 0)
            # position: pivot at origin -> centre point (0,0,cz) after rotation sits at (0,-cz*s,cz*c)
            ang = math.radians(90) * fall
            c_rot = Vector((0, -cz * math.sin(ang), cz * math.cos(ang)))
            target_lie = Vector((lx, ly, 12))
            cur = Vector((0, 0, cz)) + p_stand
            want = cur.lerp(target_lie, fall)
            ob.location = want - c_rot
            ob.scale = (1, 1, max(0.001, rise)) if fall == 0 else (1, 1, 1)
        s = b3d.ease_io(min(1, max(0, (t - 4.5) / 0.45)))
        tag.scale = (max(0.001, s), max(0.001, s), 1)
        tag.location = (-40, -230, 30)
    C.anim = anim
    C.cam_keys = [(0, (-260, -380, 120, 0, 0, 120, 24)), (2.8, (-120, -470, 170, 0, 0, 130, 24)),
                  (5.7, (60, -400, 150, -40, -60, 10, 24))]


@reg(res=(1080, 1920), samples=40, fg=True)
def s15_quiet(m, C):
    _salon(m)
    C.cam_keys = [(0, (-0.9, -2.5, 1.45, -1.0, 0.6, 1.0, 22))]
    C.anchors = dict(SALON_SEATS, lustig=(-2.0, 0.85, 0.0))


@reg(res=(1080, 1920), samples=40, fg=True)
def s16_poisson(m, C):
    _salon(m)
    C.cam_keys = [(0, (0.25, -1.05, 1.22, 0.0, 1.0, 1.12, 42))]
    C.anchors = dict(SALON_SEATS)


@reg(res=(1080, 1920), samples=40, fg=True)
def s17_doubts(m, C):
    _salon(m)
    C.cam_keys = [(0, (-0.5, -0.55, 1.08, 0.05, 1.0, 1.12, 40))]
    C.anchors = dict(SALON_SEATS)


@reg(res=(1080, 1920), samples=40, fg=True)
def s18_hint(m, C):
    _salon(m)
    C.cam_keys = [(0, (0.15, -1.7, 1.38, -0.35, 1.0, 1.25, 36))]
    C.anchors = dict(SALON_SEATS, lustig=(-0.72, 1.3, 0.0))


@reg(res=(1080, 1920), samples=40, fg=True)
def s19_glance(m, C):
    _salon(m)
    C.cam_keys = [(0, (-0.3, -0.85, 1.45, -0.33, 1.1, 1.38, 52))]
    C.anchors = dict(SALON_SEATS, lustig=(-0.72, 1.3, 0.0))


@reg(res=(720, 1280), samples=20, fg=True)
def s20_paid(m, C):
    _salon(m, docs=False)
    b3d.use_collection(bpy.data.collections["FG"])
    env = S.envelope("env", (0.1, 0.45, 0.81), thick=0.022)
    cash = S.cash_stack("cash", (0.1, 0.25, 0.83), n=2, size=(0.15, 0.07))

    def anim(t):
        u = b3d.ease_io(min(1, max(0, t / 0.45)))
        cash.location = (0.1 + 0.0 * u, 0.25 + 0.2 * u, 0.83 - 0.01 * u)
        cash.hide_render = t > 0.47
        v = b3d.ease_io(min(1, max(0, (t - 0.55) / 0.8)))
        env.location = (0.1 - 0.62 * v, 0.45 + 0.05 * v, 0.812)
        env.rotation_euler = (0, 0, -0.2 + 0.25 * v)
    C.anim = anim
    C.cam_keys = [(0, (0.0, -0.3, 0.98, -0.18, 0.5, 0.84, 34)), (1.5, (-0.08, -0.26, 0.97, -0.25, 0.5, 0.84, 36))]
    C.anchors = {"env": lambda t: tuple(env.matrix_world.translation), "cash": lambda t: tuple(cash.matrix_world.translation),
                 "lustig": (-0.72, 1.3, 0.0), "poisson": (0.15, 1.02, 0.47)}
    C.dof = ("env", 2.8)


@reg(res=(1080, 1920), samples=40)
def s21_exit(m, C):
    city_world(m)
    S.street_detail(m)
    car, _ = S.vintage_car("car1", "#1d2a3a", m)
    car.location = (326.0, 30.8, 0)
    car.rotation_euler = (0, 0, math.pi)
    h = golden_day((42, -25))
    b3d.add_haze(hexrgb("#efc996"), *h)
    C.cam_keys = [(0, (334.2, 25.5, 1.55, 329.6, 33.5, 1.9, 26))]
    C.anchors = {"door": (330, 34.6, 0.16)}


def _station_train(m):
    S.station(m)
    loco, wheels = S.locomotive("loco", m)
    h = golden_day((60, 160), energy=2.2, haze=(60, 400, 0.6))
    return loco, wheels, h


@reg(res=(540, 960), samples=12)
def s22_train(m, C):
    loco, wheels, h = _station_train(m)
    b3d.add_haze(hexrgb("#e8c49a"), *h)

    def x(t):
        return 2.0 + 6.0 * (t / 1.65) ** 1.7 * 1.65
    def anim(t):
        loco.location = (x(t), 0, 0)
        for w in wheels:
            w.rotation_euler = (0, -x(t) / 0.92, 0)
    C.anim = anim
    C.cam_keys = [(0, (-7, -4.2, 1.85, 3, 0.5, 2.4, 26)), (1.65, (-6.0, -4.2, 1.85, 6, 0.5, 2.4, 26))]
    C.anchors = {"stack": lambda t: (x(t) + 4.9, 0, 4.3), "window": lambda t: (x(t) - 10.5 - 1.0, -1.42, 2.4)}


@reg(res=(1080, 1920), samples=40, fg=True)
def s23_realize(m, C):
    fgc = b3d.collection("FG")
    S.office(m)
    b3d.use_collection(fgc)
    ob = bpy.data.objects["desk"]
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    fgc.objects.link(ob)
    for n in ("blotter", "lamp_base", "lamp_stem", "lamp_shade"):
        o = bpy.data.objects[n]
        for c in list(o.users_collection):
            c.objects.unlink(o)
        fgc.objects.link(o)
    S.paper("contract_d", S.T("contract"), 0.21, 0.29, (0.15, -0.1, 0.78), rot=(0, 0, -0.25))
    b3d.use_collection(bpy.data.collections["BG"])
    C.cam_keys = [(0, (0.15, -1.45, 1.3, -0.05, 0.6, 1.08, 34))]
    C.anchors = {"poisson": (0.0, 0.62, 0.47)}


@reg(res=(540, 960), samples=12)
def s24_empty(m, C):
    S.meeting_room(m)
    S.table_dressing(m, docs=True, seed=3)
    S.chair("lchair", m, (-1.0, -1.0, 0), rot_z=2.6)
    C.cam_keys = [(0, (-1.0, -3.6, 1.5, -0.6, 0.6, 1.0, 28)), (1.35, (-0.8, -3.0, 1.45, -0.6, 0.6, 1.0, 28))]


@reg(res=(1080, 1920), samples=40, fg=True)
def s25_silent(m, C):
    s23_realize(m, C)
    C.cam_keys = [(0, (-0.75, -1.2, 1.32, 0.12, 0.55, 1.08, 32))]


@reg(res=(540, 960), samples=12)
def s26_strange(m, C):
    loco, wheels, h = _station_train(m)
    b3d.add_haze(hexrgb("#e8c49a"), *h)

    def x(t):
        u = min(1, t / 1.3)
        return 2.0 + 26 * (1 - u) ** 2
    def anim(t):
        loco.location = (x(t), 0, 0)
        for w in wheels:
            w.rotation_euler = (0, -x(t) / 0.92, 0)
    C.anim = anim
    C.cam_keys = [(0, (-9.5, -6.0, 1.9, 3, -1.0, 1.9, 26)), (1.7, (-9.2, -5.7, 1.85, 2, -1.2, 1.85, 27))]
    C.anchors = {"stack": lambda t: (x(t) + 4.9, 0, 4.3), "lustig": lambda t: (-4.8 + 0.5 * t, -3.0, 1.0)}


@reg(res=(1080, 1920), samples=40, fg=True)
def s27_again(m, C):
    _salon(m, seed=5)
    C.cam_keys = [(0, (-0.2, -3.5, 1.6, -1.2, 0.5, 1.0, 22))]
    C.anchors = dict(SALON_SEATS)


@reg(res=(1080, 1920), samples=40, fg=True)
def s28_failed(m, C):
    _salon(m, seed=5)
    C.cam_keys = [(0, (0.7, -2.1, 1.45, -0.7, 0.8, 1.2, 30))]
    C.anchors = dict(SALON_SEATS)


@reg(res=(540, 960), samples=12)
def s29_final(m, C):
    city_world(m, lit=True)
    b3d.sun(2.6, rot=(math.radians(80), 0, math.radians(-110)), color=(1.0, 0.62, 0.32), angle=1.5)
    b3d.world_gradient(hexrgb("#4f6c9c"), hexrgb("#ffb46a"), 1.3, mid=hexrgb("#e59a6a"),
                       sun_dir=_sun_vec((80, -110)), sun_glow=(1.0, 0.45, 0.15))
    b3d.add_haze(hexrgb("#f0b47e"), 350, 2600, 0.88)
    C.cam_keys = [(0, (300, -330, 70, 0, 0, 150, 26)), (2.75, (470, -560, 150, 0, 0, 160, 26))]


# ---------------------------------------------------------------- driver
def build(sid):
    sc = b3d.reset()
    bg = b3d.collection("BG")
    b3d.use_collection(bg)
    m = S.M()
    C = Ctx()
    SHOTS[sid]["fn"](m, C)
    cam = b3d.camera()
    return sc, cam, C


def place_cam(cam, C, t):
    v = interp_keys(C.cam_keys, t)
    b3d.look_at(cam, v[0:3], v[3:6])
    cam.data.lens = v[6]
    return v


def _pt(a, t):
    return a(t) if callable(a) else a


def render_shot(sid, test=False, frange=None):
    spec = SHOTS[sid]
    sc, cam, C = build(sid)
    w, h = spec["res"]
    if test:
        w, h = w // 2, h // 2
    b3d.setup_render(w, h, samples=max(8, spec["samples"] // (2 if test else 1)))
    f0, f1 = frames(sid)
    n = f1 - f0
    mode = shot(sid)[3]
    out = os.path.join(OUT, sid)
    os.makedirs(out, exist_ok=True)
    idx = list(range(n)) if mode == "seq" else [0]
    if test:
        idx = [0, n - 1] if mode == "seq" else [0]
    if frange:
        idx = [i for i in idx if frange[0] <= i < frange[1]]
    anchors = {}
    apath = os.path.join(out, "anchors.json")
    if os.path.exists(apath):
        anchors = json.load(open(apath))
    # anchors for every frame (cheap)
    for i in range(n):
        t = i / FPS
        if C.anim:
            C.anim(t)
        place_cam(cam, C, t)
        bpy.context.view_layer.update()
        anchors[str(i)] = {k: b3d.anchor_info(sc, cam, _pt(a, t)) for k, a in C.anchors.items()}
    anchors["_meta"] = {"res": [w, h], "mode": mode, "n": n}
    json.dump(anchors, open(apath, "w"))
    if C.dof:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = C.dof[1]
    has_fg = spec["fg"] and "FG" in bpy.data.collections
    for i in idx:
        t = i / FPS
        if C.anim:
            C.anim(t)
        place_cam(cam, C, t)
        if C.dof:
            tgt = C.dof[0]
            if isinstance(tgt, str):
                p = _pt(C.anchors.get(tgt, C.anchors.get("env", (0, 0, 0))), t) if tgt in C.anchors else interp_keys(C.cam_keys, t)[3:6]
                cam.data.dof.focus_distance = (Vector(p) - cam.location).length
            else:
                cam.data.dof.focus_distance = tgt
        bpy.context.view_layer.update()
        t0 = time.time()
        if not test and os.path.exists(os.path.join(out, f"bg_{i:04d}.png")) and (
                not has_fg or os.path.exists(os.path.join(out, f"fg_{i:04d}.png"))):
            continue
        _render_pass(sc, os.path.join(out, f"bg_{i:04d}.png"), transparent=False)
        if has_fg:
            lc = bpy.context.view_layer.layer_collection.children
            lc["BG"].holdout = True
            sc.render.film_transparent = True
            sc.render.image_settings.color_mode = "RGBA"
            _render_pass(sc, os.path.join(out, f"fg_{i:04d}.png"), transparent=True)
            lc["BG"].holdout = False
            sc.render.film_transparent = False
            sc.render.image_settings.color_mode = "RGB"
        print(f"{sid} frame {i}/{n} {time.time()-t0:.1f}s", flush=True)


def _render_pass(sc, path, transparent):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    sid = sys.argv[1]
    test = "--test" in sys.argv
    fr = None
    if "--frames" in sys.argv:
        a, b = sys.argv[sys.argv.index("--frames") + 1].split(":")
        fr = (int(a), int(b))
    render_shot(sid, test=test, frange=fr)

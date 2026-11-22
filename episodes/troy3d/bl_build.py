"""Runs INSIDE Blender. Builds a 3D set + props, follows a per-frame job (camera + prop states),
renders colour PNG + depth EXR per frame.

blender -b --factory-startup --python episodes/troy3d/bl_build.py -- job.json
job.json = {"set": "beach", "out": dir, "res": [720, 1280], "samples": 16,
            "frames": [{"cam": [x,y,z], "target": [x,y,z], "lens": 35, "roll": 0,
                        "obj": {"Horse": {"loc": [..], "rot": [..], "scale": s, "hide": false}, ...},
                        "hatch": 0..1, "bow": 0..1, "time": t}, ...]}
World: metres, Z up. The sea is toward +X / +Y on the beach.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets", "troy3d")


# ================================================================ utils
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def mesh_ob(name, mesh_fn, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None, bevel=0.0):
    mesh_fn()
    ob = bpy.context.active_object
    ob.name = name
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    if mat:
        ob.data.materials.append(mat)
    if bevel:
        m = ob.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
    if parent:
        ob.parent = parent
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def cube(**kw):
    return lambda: bpy.ops.mesh.primitive_cube_add(size=1, **kw)


def cyl(v=24, **kw):
    return lambda: bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=0.5, depth=1, **kw)


def sphere(seg=24, ring=12, **kw):
    return lambda: bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=0.5, **kw)


def cone(**kw):
    return lambda: bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.5, radius2=0, depth=1, **kw)


def empty(name, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    link(ob)
    if parent:
        ob.parent = parent
    return ob


# ================================================================ materials
_MATS = {}


def pbr(name, tex=None, scale=1.0, tint=(1, 1, 1), rough=0.8, color=None, bump=0.4, emission=None, metal=0.0):
    key = (name, tex, scale, tuple(tint), color)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if tex:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

        def img(kind, non_color=False):
            p = os.path.join(ASSETS, f"{tex}_{kind}_1k.jpg")
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(p, check_existing=True)
            n.projection = "BOX"
            n.projection_blend = 0.25
            if non_color:
                n.image.colorspace_settings.name = "Non-Color"
            nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
            return n

        d = img("diff")
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(d.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        r = img("rough", True)
        nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
        n = img("nor", True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = bump
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    elif color:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emission[1]
    _MATS[key] = m
    return m


def flat(name, color, rough=0.6, emission=None):
    return pbr(name, color=color, rough=rough, emission=emission)


def water_mat(deep=(0.02, 0.25, 0.35), shallow=(0.1, 0.6, 0.65)):
    m = bpy.data.materials.new("Water")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*deep, 1)
    bsdf.inputs["Roughness"].default_value = 0.06
    bsdf.inputs["Specular IOR Level"].default_value = 0.7
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 0.6
    noise.inputs["Detail"].default_value = 6
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    noise.name = "waves"
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # fresnel-ish colour shift: shallow colour at grazing
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*shallow, 1)
    mix.inputs[7].default_value = (*deep, 1)
    nt.links.new(lw.outputs["Facing"], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


# ================================================================ world / lights
def world(hdri="kloofendal_43d_clear_puresky", strength=1.0, rot=0.0, tint=(1, 1, 1)):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ASSETS, f"{hdri}_2k.exr"), check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1
    mix.inputs[7].default_value = (*tint, 1)
    nt.links.new(env.outputs["Color"], mix.inputs[6])
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def sun(energy=3.5, rot=(math.radians(50), 0, math.radians(-40)), color=(1, 0.95, 0.85), angle=3):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.color = color
    d.angle = math.radians(angle)
    ob = bpy.data.objects.new("Sun", d)
    ob.rotation_euler = rot
    link(ob)
    return ob


def point(name, loc, energy=200, color=(1, 0.6, 0.3), radius=0.2):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    link(ob)
    return ob


# ================================================================ terrain
def ground(name, mat, size=400, loc=(0, 0, 0), disp=0.0, disp_scale=8.0, subdiv=6, seed=0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    if disp:
        m = ob.modifiers.new("sub", "SUBSURF")
        m.subdivision_type = "SIMPLE"
        m.levels = m.render_levels = subdiv
        t = bpy.data.textures.new(name + "_n", "CLOUDS")
        t.noise_scale = disp_scale
        d = ob.modifiers.new("disp", "DISPLACE")
        d.texture = t
        d.strength = disp
        d.texture_coords = "GLOBAL"
    return ob


def rock(name, loc, s=1.0, seed=0, mat=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=s, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    r = random.Random(seed)
    for v in ob.data.vertices:
        v.co *= 1 + r.uniform(-0.18, 0.18)
    ob.scale = (1, r.uniform(0.7, 1.1), r.uniform(0.5, 0.8))
    ob.data.materials.append(mat or pbr("Rock", "aerial_rocks_02", 0.5))
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ================================================================ architecture
STONE = None


def stone(scale=0.35, tint=(1.0, 0.93, 0.8)):
    return pbr("Stone", "castle_brick_02_white", scale, tint, bump=0.8)


def wall_segment(name, x0, x1, y, h=12, thick=4, mat=None, crenel=True, parent=None):
    mat = mat or stone()
    L = x1 - x0
    w = mesh_ob(name, cube(), mat, loc=((x0 + x1) / 2, y, h / 2), scale=(L, thick, h), parent=parent)
    if crenel:
        n = int(L / 2.2)
        for i in range(n):
            mesh_ob(f"{name}_c{i}", cube(), mat, loc=(x0 + 1.1 + i * 2.2, y - thick / 2 + 0.4, h + 0.6),
                    scale=(1.2, 0.8, 1.2), parent=parent)
    return w


def tower(name, x, y, w=7, h=18, mat=None, banner=(0.75, 0.12, 0.1)):
    mat = mat or stone()
    mesh_ob(name, cube(), mat, loc=(x, y, h / 2), scale=(w, w, h), bevel=0.05)
    for i in range(4):
        for k in range(3):
            dx = (k - 1) * w / 3
            for side in (-1, 1):
                mesh_ob(f"{name}_cr{i}{k}{side}", cube(), mat,
                        loc=(x + (dx if i < 2 else side * w / 2 * (1 if i == 2 else -1) * 0 + side * (w / 2 - 0.4)),
                             y + (side * (w / 2 - 0.4) if i < 2 else dx), h + 0.7), scale=(1.1, 1.1, 1.4))
    # banner hanging on the front face
    if banner:
        mesh_ob(name + "_ban", cube(), flat("Banner", banner, 0.8), loc=(x, y - w / 2 - 0.08, h - 4),
                scale=(2.2, 0.08, 5.5))
        mesh_ob(name + "_ban_sym", cyl(), flat("Gold", (0.85, 0.62, 0.2), 0.3), loc=(x, y - w / 2 - 0.14, h - 3),
                rot=(math.pi / 2, 0, 0), scale=(1.1, 1.1, 0.05))


def gate_wall(name, y=0.0, gate_w=7.0, gate_h=10.0, h=14, length=80, breach=False, mat=None):
    """Wall along X at y with an arched gate at x=0 (opening toward -Y)."""
    mat = mat or stone()
    wall_segment(name + "_L", -length / 2, -gate_w / 2 - 0.0, y, h, 5, mat)
    wall_segment(name + "_R", gate_w / 2, length / 2, y, h, 5, mat)
    # lintel above the gate with the arch cut out
    top = mesh_ob(name + "_top", cube(), mat, loc=(0, y, (gate_h + h) / 2), scale=(gate_w + 0.02, 5, h - gate_h + 2))
    arch = mesh_ob(name + "_arch", cyl(48), None, loc=(0, y, gate_h - gate_w / 2), rot=(math.pi / 2, 0, 0),
                   scale=(gate_w, gate_w, 6))
    top.location.z = (gate_h - gate_w / 2 + h) / 2
    top.scale.z = h - (gate_h - gate_w / 2)
    b = top.modifiers.new("arch", "BOOLEAN")
    b.object = arch
    b.operation = "DIFFERENCE"
    arch.hide_render = True
    arch.hide_viewport = True
    # dark inner gate passage
    mesh_ob(name + "_dark", cube(), flat("Dark", (0.03, 0.02, 0.015), 1.0), loc=(0, y + 2.6, gate_h / 2),
            scale=(gate_w + 0.1, 0.2, gate_h + 0.1))
    tower(name + "_T1", -gate_w / 2 - 4.5, y - 1, 8, h + 6)
    tower(name + "_T2", gate_w / 2 + 4.5, y - 1, 8, h + 6)
    return top


# ================================================================ PROP: the horse (giant, wooden, on wheels)
def build_horse(name="Horse"):
    root = empty(name)
    wood = pbr("HorseWood", "wood_planks", 1.3, (1.15, 0.85, 0.58), rough=0.7, bump=0.9)
    wood_dk = pbr("HorseWoodDk", "wood_planks", 1.3, (0.62, 0.42, 0.27), rough=0.8, bump=0.9)
    metal = flat("Iron", (0.35, 0.35, 0.38), 0.4)
    # +X = forward (head)
    mesh_ob(name + "_plat", cube(), wood_dk, (0, 0, 0.75), scale=(5.0, 2.4, 0.4), parent=root, bevel=0.06)
    for i, x in enumerate((-1.8, 1.8)):
        for j, y in enumerate((-1.35, 1.35)):
            w = mesh_ob(f"{name}_wheel{i}{j}", cyl(32), wood_dk, (x, y, 0.62), rot=(math.pi / 2, 0, 0),
                        scale=(1.24, 1.24, 0.25), parent=root, bevel=0.04)
            mesh_ob(f"{name}_hub{i}{j}", cyl(16), metal, (x, y * 1.1, 0.62), rot=(math.pi / 2, 0, 0),
                    scale=(0.35, 0.35, 0.12), parent=root)
    for i, (x, y) in enumerate(((-1.5, -0.65), (-1.5, 0.65), (1.4, -0.65), (1.4, 0.65))):
        mesh_ob(f"{name}_leg{i}", cube(), wood, (x, y, 2.35), scale=(0.55, 0.55, 2.9), parent=root, bevel=0.05)
        mesh_ob(f"{name}_hoof{i}", cube(), wood_dk, (x, y, 1.08), scale=(0.75, 0.7, 0.35), parent=root, bevel=0.04)
    body = mesh_ob(name + "_body", cyl(32), wood, (0, 0, 4.55), rot=(0, math.pi / 2, 0), scale=(2.6, 2.1, 4.0),
                   parent=root)
    for sx in (-1, 1):
        mesh_ob(f"{name}_butt{sx}", sphere(32, 16), wood, (sx * 2.0, 0, 4.55), scale=(1.4, 2.1, 2.6), parent=root)
    # belly hatch (pivot on the rear edge, opens downward)
    hp = empty(name + "_hatchpivot", (-0.55, 0, 3.28), parent=root)
    mesh_ob(name + "_hatchhole", cube(), flat("Dark", (0.03, 0.02, 0.015), 1.0), (0.0, 0, 3.29),
            scale=(1.2, 0.9, 0.02), parent=root)
    mesh_ob(name + "_hatch", cube(), wood_dk, (0.6, 0, 0), scale=(1.2, 0.9, 0.08), parent=hp)
    # neck (leans forward-up from the chest) + head (muzzle tilted down)
    mesh_ob(name + "_neck", cube(), wood, (2.6, 0, 6.3), rot=(0, math.radians(38), 0),
            scale=(1.35, 1.25, 3.8), parent=root, bevel=0.15)
    mesh_ob(name + "_head", cube(), wood, (4.35, 0, 7.85), rot=(0, math.radians(28), 0),
            scale=(2.6, 1.15, 1.2), parent=root, bevel=0.22)
    mesh_ob(name + "_muzzle", cube(), wood_dk, (5.5, 0, 7.25), rot=(0, math.radians(28), 0),
            scale=(0.6, 1.17, 0.95), parent=root, bevel=0.14)
    for s in (-1, 1):
        mesh_ob(f"{name}_ear{s}", cone(), wood, (3.55, s * 0.38, 8.75), rot=(0, math.radians(-12), 0),
                scale=(0.5, 0.32, 1.0), parent=root)
        mesh_ob(f"{name}_eye{s}", sphere(), flat("EyeW", (0.95, 0.95, 0.92), 0.3), (4.15, s * 0.6, 8.1),
                scale=(0.55, 0.14, 0.55), parent=root)
        mesh_ob(f"{name}_pupil{s}", sphere(), flat("EyeB", (0.02, 0.02, 0.02), 0.2), (4.25, s * 0.67, 8.06),
                scale=(0.26, 0.06, 0.26), parent=root)
        mesh_ob(f"{name}_nostril{s}", sphere(), flat("EyeB", (0.02, 0.02, 0.02), 0.2), (5.72, s * 0.3, 7.25),
                scale=(0.12, 0.12, 0.12), parent=root)
        mesh_ob(f"{name}_strap{s}", cube(), flat("Red", (0.6, 0.06, 0.05), 0.6), (4.85, s * 0.6, 7.55),
                rot=(0, math.radians(-62), 0), scale=(0.14, 0.05, 1.5), parent=root)
    mesh_ob(name + "_nose_strap", cube(), flat("Red", (0.6, 0.06, 0.05), 0.6), (5.15, 0, 7.4),
            rot=(0, math.radians(28), 0), scale=(0.16, 1.22, 1.0), parent=root)
    # mane: chunky plank tufts along the back of the neck
    for i in range(8):
        a = i / 7
        mesh_ob(f"{name}_mane{i}", cube(), wood_dk, (1.55 + a * 2.05, 0, 5.75 + a * 2.65),
                rot=(0, math.radians(38 - 60), 0), scale=(0.28, 0.75, 1.0), parent=root, bevel=0.03)
    # tail
    mesh_ob(name + "_tail", cone(), wood_dk, (-3.1, 0, 4.3), rot=(0, math.radians(-150), 0),
            scale=(0.75, 0.75, 2.6), parent=root)
    # gift bow (hidden unless used)
    bow = empty(name + "_bow", (3.35, 0, 6.0), parent=root)
    red = flat("BowRed", (0.8, 0.05, 0.08), 0.35)
    for s in (-1, 1):
        mesh_ob(f"{name}_bowloop{s}", sphere(), red, (0, s * 0.9, 0.35), rot=(math.radians(s * 25), 0, 0),
                scale=(0.5, 1.1, 0.7), parent=bow)
        mesh_ob(f"{name}_bowtail{s}", cube(), red, (0.05, s * 0.5, -0.9), rot=(math.radians(s * 20), 0, 0),
                scale=(0.08, 0.35, 1.4), parent=bow)
    mesh_ob(name + "_bowknot", sphere(), red, (0, 0, 0.3), scale=(0.55, 0.55, 0.55), parent=bow)
    # a band around the neck
    mesh_ob(name + "_band", cube(), red, (2.95, 0, 6.6), rot=(0, math.radians(38 + 90), 0), scale=(0.3, 1.4, 1.5),
            parent=root)
    return root


def set_horse_state(f):
    hp = bpy.data.objects.get("Horse_hatchpivot")
    if hp:
        hp.rotation_euler = (0, math.radians(100 * f.get("hatch", 0.0)), 0)
    bow = f.get("bow", 0.0)
    for ob in bpy.data.objects:
        if ob.name.startswith("Horse_bow") or ob.name == "Horse_band":
            ob.hide_render = bow < 0.01
    b = bpy.data.objects.get("Horse_bow")
    if b:
        s = max(0.01, bow)
        b.scale = (s, s, s)


# ================================================================ SETS
def set_beach(night=False):
    world("kloofendal_48d_partly_cloudy_puresky", 1.0, math.radians(30))
    sun(4.0, (math.radians(52), 0, math.radians(-35)))
    sand = pbr("Sand", "coast_sand_01", 0.25, (1.12, 0.97, 0.76), bump=0.5)
    ground("Beach", sand, 400, (0, -160, 0), disp=0.45, disp_scale=10)
    ground("Sea", water_mat(), 1200, (0, 640, -0.12))
    # Troy on a hill far away (-Y, toward the camera's left-back)
    hill = ground("Hill", pbr("Grass", "sparse_grass", 0.1, (0.9, 0.95, 0.7)), 120, (-60, -120, 0), disp=9,
                  disp_scale=40, subdiv=5)
    hill.scale = (1.6, 1, 1)
    for i, x in enumerate(range(-110, -10, 18)):
        wall_segment(f"TroyW{i}", x, x + 18, -125, 10, 3, stone(0.5))
        if i % 2 == 0:
            tower(f"TroyT{i}", x, -125, 6, 16)
    # dressing: campfires, spears, tents, rocks, broken amphora
    r = random.Random(4)
    char = flat("Char", (0.05, 0.04, 0.035), 1.0)
    logm = pbr("Log", "wood_planks", 1.0, (0.45, 0.3, 0.2))
    for k, (x, y) in enumerate(((-9, 10), (14, 22), (-22, 30), (6, -14))):
        mesh_ob(f"Ash{k}", cyl(24), char, (x, y, 0.05), scale=(2.2, 2.2, 0.06))
        for j in range(4):
            mesh_ob(f"Log{k}{j}", cyl(12), logm, (x, y, 0.2), rot=(math.pi / 2, 0, j * 0.8),
                    scale=(0.25, 0.25, 1.8))
    spear_wood = flat("SpearWood", (0.45, 0.3, 0.18), 0.6)
    bronze = flat("Bronze", (0.75, 0.55, 0.22), 0.3)
    for k in range(9):
        x, y = r.uniform(-30, 30), r.uniform(-6, 40)
        e = Euler((r.uniform(-0.4, 0.4), r.uniform(-0.4, 0.4), 0))
        sp = mesh_ob(f"Spear{k}", cyl(8), spear_wood, (x, y, 1.2), rot=e, scale=(0.07, 0.07, 2.6))
        tip = Vector((0, 0, 1.3))
        tip.rotate(e)
        mesh_ob(f"SpearTip{k}", cone(), bronze, Vector((x, y, 1.2)) + tip, rot=e, scale=(0.14, 0.14, 0.45))
    tent = flat("Canvas", (0.9, 0.85, 0.72), 0.9)
    for k, (x, y) in enumerate(((-26, 18), (24, 6), (30, 34))):
        mesh_ob(f"Pole{k}", cyl(8), spear_wood, (x, y, 1.8), rot=(0.15, 0, 0), scale=(0.12, 0.12, 3.6))
        mesh_ob(f"Cloth{k}", cube(), tent, (x + 0.8, y, 2.6), rot=(0.1, 0.4, 0.3), scale=(1.6, 0.05, 1.2))
    for k in range(14):
        rock(f"Rock{k}", (r.uniform(-60, 60), r.uniform(-30, 60), 0.1), r.uniform(0.3, 1.4), k)
    # Greek ships far out at sea
    for k in range(3):
        build_ship(f"BShip{k}", (40 + k * 30, 140 + k * 25, 0), 1.0 - k * 0.1, sail=(0.92, 0.88, 0.78))


def build_ship(name, loc, s=1.0, rot=0.0, sail=(0.92, 0.88, 0.78), stripe=(0.15, 0.35, 0.7)):
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot)
    root.scale = (s, s, s)
    hull = pbr("Hull", "wood_planks", 0.6, (0.55, 0.36, 0.22))
    mesh_ob(name + "_hull", sphere(32, 16), hull, (0, 0, 0.6), scale=(14, 3.4, 2.6), parent=root)
    mesh_ob(name + "_deck", cube(), hull, (0, 0, 1.6), scale=(12, 2.8, 0.3), parent=root)
    mesh_ob(name + "_stripe", cube(), flat("Stripe", stripe, 0.5), (0, 0, 1.35), scale=(12.5, 3.0, 0.3), parent=root)
    mesh_ob(name + "_bow", cone(), hull, (7.6, 0, 2.6), rot=(0, math.radians(-60), 0), scale=(0.8, 0.8, 3), parent=root)
    mesh_ob(name + "_stern", cone(), hull, (-7.4, 0, 3.0), rot=(0, math.radians(-30), 0), scale=(0.9, 0.9, 3.6),
            parent=root)
    mesh_ob(name + "_mast", cyl(8), hull, (0, 0, 7), scale=(0.3, 0.3, 11), parent=root)
    mesh_ob(name + "_sail", cube(), flat("Sail" + name, sail, 0.9), (0.3, 0, 8.2), scale=(0.08, 7.5, 6.5),
            parent=root)
    for k in (-2, 0, 2):
        mesh_ob(f"{name}_sstripe{k}", cube(), flat("Stripe", stripe, 0.5), (0.36, k * 1.6, 8.2),
                scale=(0.08, 0.6, 6.5), parent=root)
    mesh_ob(name + "_yard", cyl(8), hull, (0.2, 0, 11.5), rot=(math.pi / 2, 0, 0), scale=(0.25, 0.25, 8.5),
            parent=root)
    for k in range(7):
        for sd in (-1, 1):
            mesh_ob(f"{name}_oar{k}{sd}", cyl(6), hull, (-4.5 + k * 1.5, sd * 2.6, 0.6), rot=(sd * 1.0, 0, 0),
                    scale=(0.08, 0.08, 4.0), parent=root)
    for sd in (-1, 1):
        mesh_ob(f"{name}_eye{sd}", sphere(), flat("EyeW", (0.95, 0.95, 0.92), 0.3), (6.5, sd * 1.65, 1.2),
                scale=(0.7, 0.1, 0.5), parent=root)
        mesh_ob(f"{name}_pup{sd}", sphere(), flat("EyeB", (0.02, 0.02, 0.02), 0.2), (6.6, sd * 1.72, 1.2),
                scale=(0.3, 0.05, 0.3), parent=root)
    return root


SETS = {"beach": set_beach}


# ================================================================ render setup + job
def setup_render(res, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    vl = sc.view_layers[0]
    vl.use_pass_z = True
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers")
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], comp.inputs["Image"])
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.format.file_format = "OPEN_EXR"
    fo.format.color_depth = "32"
    fo.file_slots[0].path = "depth_"
    nt.links.new(rl.outputs["Depth"], fo.inputs[0])
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.sensor_width = 36
    cam_d.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_d)
    link(cam)
    sc.camera = cam
    return fo


def look_at(cam, loc, target, roll=0.0):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    cam.rotation_euler = q.to_euler()
    if roll:
        cam.rotation_euler.rotate_axis("Z", roll)


def run(job):
    clear()
    fo = setup_render(job.get("res", [720, 1280]), job.get("samples", 16))
    SETS[job["set"]](**job.get("set_args", {}))
    if job.get("horse", True):
        build_horse()
    cam = bpy.context.scene.camera
    out = job["out"]
    os.makedirs(out, exist_ok=True)
    fo.base_path = out
    sc = bpy.context.scene
    for i, f in enumerate(job["frames"]):
        idx = f.get("index", i)
        png = os.path.join(out, f"color_{idx:04d}.png")
        if os.path.exists(png) and not job.get("force"):
            continue
        sc.frame_set(idx)
        cam.data.lens = f.get("lens", 35)
        look_at(cam, f["cam"], f["target"], f.get("roll", 0.0))
        for name, st in f.get("obj", {}).items():
            ob = bpy.data.objects.get(name)
            if not ob:
                continue
            if "loc" in st:
                ob.location = st["loc"]
            if "rot" in st:
                ob.rotation_euler = st["rot"]
            if "scale" in st:
                s = st["scale"]
                ob.scale = (s, s, s) if isinstance(s, (int, float)) else s
            if "hide" in st:
                ob.hide_render = st["hide"]
                for c in ob.children_recursive:
                    c.hide_render = st["hide"]
        set_horse_state(f)
        wn = bpy.data.materials.get("Water")
        if wn:
            wn.node_tree.nodes["waves"].inputs["W"].default_value = f.get("time", idx / 30) * 0.3
        sc.render.filepath = png
        bpy.ops.render.render(write_still=True)
        # compositor file output names files depth_####.exr using the scene frame
        print("FRAME_DONE", idx, flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    run(json.load(open(argv[0])))

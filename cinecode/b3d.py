"""Blender (bpy) helpers for Cinecode 3D environment plates.

Environments are modelled procedurally and rendered with Cycles; 2D characters are
composited afterwards with Cairo at positions projected from 3D anchor empties.
"""
import json
import math
import os
import random

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

TEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "tex")


# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import addon_utils
    addon_utils.enable("cycles", default_set=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.fps = 30
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            sc.view_settings.view_transform = "Filmic"
        except Exception:
            pass
    return sc


def collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


_ACTIVE = [None]


def use_collection(c):
    _ACTIVE[0] = c


def link(ob):
    c = _ACTIVE[0] or bpy.context.scene.collection
    c.objects.link(ob)
    return ob


# ------------------------------------------------------------------ materials
def _nodes(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf


def _set(bsdf, key, val):
    names = {"spec": ["Specular IOR Level", "Specular"], "coat": ["Coat Weight", "Clearcoat"],
             "emit": ["Emission Color", "Emission"], "emit_s": ["Emission Strength"],
             "sheen": ["Sheen Weight", "Sheen"]}
    for n in names.get(key, [key]):
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = val
            return


def mat(name, color, rough=0.5, metal=0.0, spec=0.5, coat=0.0, emit=None, emit_s=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt, b = _nodes(name)
    b.inputs["Base Color"].default_value = (*color[:3], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    _set(b, "spec", spec)
    _set(b, "coat", coat)
    if emit is not None:
        _set(b, "emit", (*emit[:3], 1))
        _set(b, "emit_s", emit_s)
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def mat_noise(name, c1, c2, scale=4.0, rough=0.6, metal=0.0, bump=0.15, detail=6.0, coat=0.0,
              stretch=(1, 1, 1), kind="noise"):
    """Procedural two-tone material (stone, plaster, worn metal...)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt, b = _nodes(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = stretch
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    if kind == "wave":
        tx = nt.nodes.new("ShaderNodeTexWave")
        tx.inputs["Scale"].default_value = scale
        tx.inputs["Distortion"].default_value = 6.0
        tx.inputs["Detail"].default_value = detail
        tx.inputs["Detail Scale"].default_value = 1.5
    else:
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = scale
        tx.inputs["Detail"].default_value = detail
    nt.links.new(mp.outputs[0], tx.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1[:3], 1)
    ramp.color_ramp.elements[1].color = (*c2[:3], 1)
    if kind == "wave":
        ramp.color_ramp.elements[0].position = 0.25
        ramp.color_ramp.elements[1].position = 0.8
    else:
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(tx.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    _set(b, "coat", coat)
    if bump > 0:
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = bump
        nt.links.new(tx.outputs["Fac"], bn.inputs["Height"])
        nt.links.new(bn.outputs[0], b.inputs["Normal"])
    return m


def mat_image(name, path, rough=0.6, metal=0.0, emit=0.0, coat=0.0, interp="Linear", alpha=False,
              bump=0.0, extension="REPEAT"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, nt, b = _nodes(name)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path, check_existing=True)
    tx.interpolation = interp
    tx.extension = extension
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    _set(b, "coat", coat)
    if alpha:
        nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"])
    if emit > 0:
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"] if "Emission Color" in b.inputs else b.inputs["Emission"])
        _set(b, "emit_s", emit)
    if bump > 0:
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(tx.outputs["Color"], bw.inputs[0])
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = bump
        nt.links.new(bw.outputs[0], bn.inputs["Height"])
        nt.links.new(bn.outputs[0], b.inputs["Normal"])
    return m


def mat_emit(name, color, strength=5.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color[:3], 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def hexrgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # sRGB -> linear
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


# ------------------------------------------------------------------ primitives
def mesh_obj(name, verts, faces, material=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    link(ob)
    if material:
        ob.data.materials.append(material)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def box(name, center, size, material=None, rot=(0, 0, 0), bevel=0.0, uv_scale=None):
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, material)
    ob.location = center
    ob.rotation_euler = rot
    if bevel > 0:
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
    box_uv(ob, uv_scale)
    return ob


def box_uv(ob, scale=None):
    """Simple cube projection UVs in object space (meters -> uv * scale)."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    sc = scale or 1.0
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uv[li].uv = (u * sc, v * sc)


def cyl(name, p0, p1, r, material=None, verts=12, r1=None, cap=True):
    """Cylinder between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    r1 = r if r1 is None else r1
    vs, fs = [], []
    for i in range(verts):
        a = 2 * math.pi * i / verts
        vs.append((math.cos(a) * r, math.sin(a) * r, 0))
    for i in range(verts):
        a = 2 * math.pi * i / verts
        vs.append((math.cos(a) * r1, math.sin(a) * r1, L))
    for i in range(verts):
        j = (i + 1) % verts
        fs.append((i, j, verts + j, verts + i))
    if cap:
        fs.append(tuple(range(verts - 1, -1, -1)))
        fs.append(tuple(range(verts, 2 * verts)))
    ob = mesh_obj(name, vs, fs, material, smooth=True)
    ob.location = p0
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return ob


def plane(name, center, size, material=None, rot=(0, 0, 0), uv=(1, 1)):
    sx, sy = size[0] / 2, size[1] / 2
    ob = mesh_obj(name, [(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)], [(0, 1, 2, 3)], material)
    me = ob.data
    me.uv_layers.new()
    for li, (u, v) in zip(range(4), [(0, 0), (uv[0], 0), (uv[0], uv[1]), (0, uv[1])]):
        me.uv_layers.active.data[li].uv = (u, v)
    ob.location = center
    ob.rotation_euler = rot
    return ob


def join(objs, name):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    ctx = bpy.context
    for o in ctx.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    ctx.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = ctx.view_layer.objects.active
    ob.name = name
    return ob


def apply_mods(ob):
    ctx = bpy.context
    for o in ctx.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    ctx.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def struts_mesh(name, segs, material, w=0.3):
    """Many square-section beams (list of (p0,p1[,w])) as ONE mesh - fast lattice work."""
    vs, fs = [], []
    for s in segs:
        p0, p1 = Vector(s[0]), Vector(s[1])
        ww = s[2] if len(s) > 2 else w
        d = p1 - p0
        if d.length < 1e-6:
            continue
        z = d.normalized()
        x = z.cross(Vector((0, 0, 1)))
        if x.length < 1e-3:
            x = z.cross(Vector((1, 0, 0)))
        x.normalize()
        y = z.cross(x)
        h = ww / 2
        base = len(vs)
        for p in (p0, p1):
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                vs.append(tuple(p + x * sx * h + y * sy * h))
        for i in range(4):
            j = (i + 1) % 4
            fs.append((base + i, base + j, base + 4 + j, base + 4 + i))
        fs.append((base + 3, base + 2, base + 1, base + 0))
        fs.append((base + 4, base + 5, base + 6, base + 7))
    return mesh_obj(name, vs, fs, material)


# ------------------------------------------------------------------ lights / world
def sun(energy=3.5, rot=(math.radians(50), 0, math.radians(30)), color=(1.0, 0.85, 0.65), angle=1.5):
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new("sun", ld)
    link(ob)
    ob.rotation_euler = rot
    return ob


def point(loc, energy=200, color=(1, 0.8, 0.55), radius=0.1, name="pt", kind="POINT", size=1.0):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "POINT" or kind == "SPOT":
        ld.shadow_soft_size = radius
    if kind == "AREA":
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    link(ob)
    ob.location = loc
    return ob


def world_gradient(top, horizon, strength=1.0, mid=None, sun_dir=None, sun_glow=None):
    """Sky: vertical gradient on view direction Z (+ optional warm glow around the sun direction)."""
    w = bpy.data.worlds.new("world")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*horizon, 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (*top, 1)
    if mid:
        e = ramp.color_ramp.elements.new(0.12)
        e.color = (*mid, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    col = ramp.outputs[0]
    if sun_dir is not None:
        dp = nt.nodes.new("ShaderNodeVectorMath")
        dp.operation = "DOT_PRODUCT"
        nt.links.new(tc.outputs["Generated"], dp.inputs[0])
        v = Vector(sun_dir).normalized()
        dp.inputs[1].default_value = tuple(v)
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.use_clamp = True
        nt.links.new(dp.outputs["Value"], pw.inputs[0])
        pw.inputs[1].default_value = 6.0
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "ADD"
        nt.links.new(pw.outputs[0], mx.inputs["Factor"])
        nt.links.new(col, mx.inputs[6])
        mx.inputs[7].default_value = (*(sun_glow or (1.0, 0.6, 0.3)), 1)
        col = mx.outputs[2]
    nt.links.new(col, bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


def add_haze(color, d0, d1, maxf=0.85, gamma=1.0):
    """Aerial perspective: blend every material toward an emissive haze colour by camera distance."""
    for m in bpy.data.materials:
        if not m.use_nodes or m.get("hazed"):
            continue
        nt = m.node_tree
        outs = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not outs or not outs[0].inputs[0].links:
            continue
        out = outs[0]
        src_sock = out.inputs[0].links[0].from_socket
        cam = nt.nodes.new("ShaderNodeCameraData")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = d0
        mr.inputs["From Max"].default_value = d1
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = maxf
        mr.clamp = True
        nt.links.new(cam.outputs["View Distance"], mr.inputs["Value"])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*color, 1)
        em.inputs[1].default_value = 1.0
        ms = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mr.outputs[0], ms.inputs[0])
        nt.links.new(src_sock, ms.inputs[1])
        nt.links.new(em.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs[0])
        m["hazed"] = True


def fog(density=0.002, color=(0.9, 0.75, 0.55), anisotropy=0.3):
    """World volume scatter for aerial perspective / god rays."""
    w = bpy.context.scene.world
    nt = w.node_tree
    out = [n for n in nt.nodes if n.type == "OUTPUT_WORLD"][0]
    vs = nt.nodes.new("ShaderNodeVolumePrincipled")
    vs.inputs["Color"].default_value = (*color, 1)
    vs.inputs["Density"].default_value = density
    vs.inputs["Anisotropy"].default_value = anisotropy
    nt.links.new(vs.outputs[0], out.inputs["Volume"])


# ------------------------------------------------------------------ camera
def camera(lens=30, sensor=36, name="cam"):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = "AUTO"
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    cd.clip_start = 0.05
    cd.clip_end = 5000
    return ob


def look_at(ob, loc, target, roll=0.0):
    ob.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    e = q.to_euler()
    if roll:
        e.rotate_axis("Z", roll)
    ob.rotation_euler = e


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def interp_keys(keys, t, ease=ease_io):
    """keys: [(t, value_tuple)] -> tuple (eased per segment)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            x = ease((t - t0) / max(1e-6, t1 - t0))
            return tuple(a + (b - a) * x for a, b in zip(v0, v1))
    return keys[-1][1]


# ------------------------------------------------------------------ render / projection
def setup_render(w, h, samples=24, transparent=False, denoise=True, threads=0):
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = denoise
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.volume_bounces = 0
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    if threads:
        sc.render.threads_mode = "FIXED"
        sc.render.threads = threads


def project(scene, cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    co = world_to_camera_view(scene, cam, Vector(p))
    return co.x, 1 - co.y, co.z


def anchor_info(scene, cam, p, W=1080, H=1920):
    """screen position (px) + pixels-per-meter at that depth (using camera up vector)."""
    x, y, z = project(scene, cam, p)
    up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    x2, y2, _ = project(scene, cam, Vector(p) + up * 1.0)
    ppm = math.hypot((x2 - x) * W, (y2 - y) * H)
    return [x * W, y * H, ppm, z]

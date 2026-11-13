"""Procedural 3D sets for the Eiffel Tower episode (Blender / Cycles).

Units are meters. The tower stands at the origin; the city grid surrounds it.
"""
import math
import os
import random

import bpy
from mathutils import Vector

from cinecode import b3d
from cinecode.b3d import box, cyl, hexrgb, mat, mat_image, mat_noise, plane, struts_mesh

TEX = b3d.TEX_DIR


def T(name):
    return os.path.join(TEX, name + ".png")


# ======================================================================= materials
def M():
    return {
        "iron": mat_noise("iron", hexrgb("#4a3424"), hexrgb("#6e4e34"), scale=8, rough=0.55, metal=0.55, bump=0.1),
        "iron_dk": mat("iron_dk", hexrgb("#2e221a"), rough=0.6, metal=0.5),
        "stone": mat_noise("stone", hexrgb("#d9c7a4"), hexrgb("#c4ae88"), scale=3, rough=0.8, bump=0.05),
        "stone_lt": mat_noise("stone_lt", hexrgb("#e8dcc2"), hexrgb("#d3c19f"), scale=3, rough=0.8, bump=0.05),
        "slate": mat_image("slate", T("slate"), rough=0.5),
        "roof": mat_image("roof", T("roof"), rough=0.55),
        "cobble": mat_image("cobble", T("cobble"), rough=0.75, bump=0.25),
        "pavement": mat_image("pavement", T("pavement"), rough=0.8, bump=0.1),
        "grass": mat_noise("grass", hexrgb("#4f6b2e"), hexrgb("#6f8a3c"), scale=1.5, rough=0.9, bump=0.1),
        "tree": mat_noise("tree", hexrgb("#3d5a26"), hexrgb("#6b8436"), scale=6, rough=0.9, bump=0.4),
        "trunk": mat("trunk", hexrgb("#3b2a1e"), rough=0.9),
        "water": mat("water", hexrgb("#3e5866"), rough=0.08, spec=0.6),
        "black": mat("blackpaint", hexrgb("#141416"), rough=0.35, coat=0.6),
        "chrome": mat("chrome", (0.8, 0.78, 0.74), rough=0.15, metal=1.0),
        "brass": mat("brass", hexrgb("#c79a46"), rough=0.3, metal=1.0),
        "gold": mat("gold", hexrgb("#d9a948"), rough=0.25, metal=1.0),
        "glass": mat("glass_dark", hexrgb("#2b3440"), rough=0.08, spec=0.8),
        "lamp": b3d.mat_emit("lampglow", (1.0, 0.75, 0.42), 12.0),
        "wood": mat_noise("wood_dark", hexrgb("#3d2214"), hexrgb("#6b3d22"), scale=3, rough=0.32, bump=0.02,
                          kind="wave", stretch=(1, 1, 8), coat=0.6),
        "wood_mid": mat_noise("wood_mid", hexrgb("#5a3420"), hexrgb("#8a5a34"), scale=3, rough=0.4, bump=0.02,
                              kind="wave", stretch=(1, 1, 8), coat=0.3),
        "leather": mat_noise("leather", hexrgb("#4a2418"), hexrgb("#6b3422"), scale=20, rough=0.45, bump=0.1),
        "cloth_red": mat_noise("cloth_red", hexrgb("#7a1a1e"), hexrgb("#9a2a2a"), scale=40, rough=0.85, bump=0.05),
        "cloth_green": mat_noise("cloth_green", hexrgb("#1f3a2c"), hexrgb("#2c4c38"), scale=40, rough=0.85, bump=0.05),
        "white": mat("whitecloth", hexrgb("#eee6d6"), rough=0.7),
        "rubber": mat("rubber", hexrgb("#1a1a1a"), rough=0.8),
    }


# ======================================================================= Eiffel Tower
def _wo(z):
    """outer half-width of the tower at height z (m)."""
    ks = [(0, 62), (20, 50), (57, 37), (90, 26), (115, 20.5), (160, 14.5), (210, 10.5), (276, 6.5), (290, 5)]
    for (z0, w0), (z1, w1) in zip(ks, ks[1:]):
        if z <= z1:
            u = (z - z0) / (z1 - z0)
            return w0 + (w1 - w0) * u
    return ks[-1][1]


def _lw(z):
    ks = [(0, 24), (57, 17), (100, 15), (118, 20.5)]
    for (z0, w0), (z1, w1) in zip(ks, ks[1:]):
        if z <= z1:
            u = (z - z0) / (z1 - z0)
            return w0 + (w1 - w0) * u
    return 20.5


def _column_lattice(corners_at, z0, z1, step, w_main=1.2, w_brace=0.45, sub=True):
    """Generic square lattice column. corners_at(z) -> 4 (x,y) corners."""
    segs = []
    n = max(1, int(round((z1 - z0) / step)))
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    for i in range(n):
        za, zb = zs[i], zs[i + 1]
        ca, cb = corners_at(za), corners_at(zb)
        for k in range(4):
            segs.append(((*ca[k], za), (*cb[k], zb), w_main))
            k2 = (k + 1) % 4
            segs.append(((*ca[k], za), (*ca[k2], za), w_brace * 1.3))
            # X bracing
            segs.append(((*ca[k], za), (*cb[k2], zb), w_brace))
            segs.append(((*ca[k2], za), (*cb[k], zb), w_brace))
            if sub:
                zm = (za + zb) / 2
                cm = corners_at(zm)
                mid_a = ((ca[k][0] + ca[k2][0]) / 2, (ca[k][1] + ca[k2][1]) / 2)
                mid_b = ((cb[k][0] + cb[k2][0]) / 2, (cb[k][1] + cb[k2][1]) / 2)
                segs.append(((*mid_a, za), (*mid_b, zb), w_brace * 0.8))
                segs.append(((*cm[k], zm), (*cm[k2], zm), w_brace * 0.6))
    return segs


def tower_bands():
    """Return list of (zmin, zmax) bands used for dismantling animation."""
    return [(0, 57), (57, 115), (115, 180), (180, 235), (235, 330)]


def eiffel_tower(name="eiffel", loc=(0, 0, 0), scale=1.0, mats=None, banded=False, detail=1.0):
    """Build the tower. Returns list of objects (one per band if banded, else one)."""
    mats = mats or M()
    iron = mats["iron"]
    step = 6.0 / detail
    band_segs = {b: [] for b in tower_bands()}

    def band_of(z):
        for b in tower_bands():
            if b[0] <= z < b[1]:
                return b
        return tower_bands()[-1]

    def add(segs):
        for s in segs:
            zc = (s[0][2] + s[1][2]) / 2
            band_segs[band_of(zc)].append(s)

    # four legs up to 2nd platform
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        def corners(z, sx=sx, sy=sy):
            o = _wo(z)
            i = max(0.0, o - _lw(z))
            return [(sx * o, sy * o), (sx * i, sy * o), (sx * i, sy * i), (sx * o, sy * i)]
        add(_column_lattice(corners, 0, 57, step, 1.6, 0.55))
        add(_column_lattice(corners, 57, 116, step, 1.3, 0.5))

    # upper shaft
    def shaft(z):
        o = _wo(z)
        return [(o, o), (-o, o), (-o, -o), (o, -o)]
    add(_column_lattice(shaft, 116, 180, step * 1.2, 1.1, 0.42))
    add(_column_lattice(shaft, 180, 235, step * 1.3, 0.95, 0.38))
    add(_column_lattice(shaft, 235, 276, step * 1.3, 0.85, 0.34))

    # decorative arches between legs (each face)
    for face in range(4):
        ang = face * math.pi / 2
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for i in range(25):
            u = i / 24
            x = -34 + 68 * u
            z = 6 + 33 * math.sin(math.pi * u) ** 0.8
            pts.append((x, z))
        segs = []
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            for off, ww in ((0, 1.0), (2.2, 0.6)):
                yv = _wo(z0) - 2
                p0 = (ca * yv - sa * x0, sa * yv + ca * x0, z0 + off)
                p1 = (ca * yv - sa * x1, sa * yv + ca * x1, z1 + off)
                segs.append((p0, p1, ww))
            # little radial struts between arch and platform
            yv = _wo(z0) - 2
            if 2 <= i <= 22 and i % 2 == 0:
                segs.append(((ca * yv - sa * x0, sa * yv + ca * x0, z0), (ca * yv - sa * x0, sa * yv + ca * x0, 56), 0.3))
        add(segs)

    objs = []
    extra = {b: [] for b in tower_bands()}
    # platforms
    p1 = box(name + "_p1", (0, 0, 59), (2 * _wo(57) + 8, 2 * _wo(57) + 8, 5.5), mats["iron_dk"])
    extra[(57, 115)].append(p1)
    # platform 1 decorative frieze ring (lighter band)
    for k in range(4):
        ang = k * math.pi / 2
        w = _wo(57) + 4.2
        fr = box(name + f"_fr{k}", (math.cos(ang) * w, math.sin(ang) * w, 60.5), (0.6 if k % 2 == 0 else 2 * w, 2 * w if k % 2 == 0 else 0.6, 2.5),
                 mats["iron"])
        extra[(57, 115)].append(fr)
    p2 = box(name + "_p2", (0, 0, 117), (2 * _wo(115) + 6, 2 * _wo(115) + 6, 3.5), mats["iron_dk"])
    extra[(115, 180)].append(p2)
    p3 = box(name + "_p3", (0, 0, 278), (15, 15, 5), mats["iron_dk"])
    cab = box(name + "_cab", (0, 0, 283), (9, 9, 6), mats["iron"])
    dome = cyl(name + "_dome", (0, 0, 286), (0, 0, 292), 4.0, mats["iron_dk"], r1=1.2)
    ant = cyl(name + "_ant", (0, 0, 292), (0, 0, 318), 0.7, mats["iron_dk"], r1=0.25, verts=8)
    extra[(235, 330)] += [p3, cab, dome, ant]

    for b in tower_bands():
        ob = struts_mesh(f"{name}_band{b[0]}", band_segs[b], iron)
        parts = [ob] + extra[b]
        j = b3d.join(parts, f"{name}_band{b[0]}")
        objs.append(j)
    if not banded:
        objs = [b3d.join(objs, name)]
    for o in objs:
        o.location = Vector(loc) + o.location * 0
        o.scale = (scale, scale, scale)
        o.location = loc
    return objs


# ======================================================================= buildings
class Builder:
    """Accumulate quads per material, emit ONE object with material slots (fast for big cities)."""

    def __init__(self, name):
        self.name = name
        self.v, self.f, self.uv, self.mi = [], [], [], []
        self.mats = []

    def _m(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def quad(self, pts, uvs, m):
        b = len(self.v)
        self.v += [tuple(p) for p in pts]
        self.f.append(tuple(range(b, b + len(pts))))
        self.uv.append(uvs)
        self.mi.append(self._m(m))

    def box(self, c, size, m, uvs=0.5):
        x, y, z = c
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        P = [(x - hx, y - hy, z - hz), (x + hx, y - hy, z - hz), (x + hx, y + hy, z - hz), (x - hx, y + hy, z - hz),
             (x - hx, y - hy, z + hz), (x + hx, y - hy, z + hz), (x + hx, y + hy, z + hz), (x - hx, y + hy, z + hz)]
        for q, (a, bb) in [((0, 1, 5, 4), (size[0], size[2])), ((1, 2, 6, 5), (size[1], size[2])),
                           ((2, 3, 7, 6), (size[0], size[2])), ((3, 0, 4, 7), (size[1], size[2])),
                           ((4, 5, 6, 7), (size[0], size[1])), ((3, 2, 1, 0), (size[0], size[1]))]:
            self.quad([P[i] for i in q], [(0, 0), (a * uvs, 0), (a * uvs, bb * uvs), (0, bb * uvs)], m)

    def build(self):
        ob = b3d.mesh_obj(self.name, self.v, self.f)
        me = ob.data
        for m in self.mats:
            me.materials.append(m)
        me.uv_layers.new()
        ud = me.uv_layers.active.data
        for p, uvs, mi in zip(me.polygons, self.uv, self.mi):
            p.material_index = mi
            for li, uv in zip(p.loop_indices, uvs):
                ud[li].uv = uv
        return ob


def building(B, x, y, w, d, floors, mats, seed=0, lit=False, chimneys=True):
    """Haussmann block into builder B: textured walls + mansard roof. (x,y) = footprint centre."""
    fh = 3.6
    h = floors * fh
    k = seed % 4
    fac = mat_image(f"fac{'L' if lit else ''}{k}", T(f"facade_lit_{k}" if lit else f"facade_{k}"), rough=0.7, bump=0.05)
    hw, hd = w / 2, d / 2
    C = [(x - hw, y - hd), (x + hw, y - hd), (x + hw, y + hd), (x - hw, y + hd)]
    floors_tex = 6 + (k % 2)
    vt = floors / floors_tex
    tile_w = 5 * 3.6
    off = (seed * 0.37) % 1
    for i in range(4):
        a, bb = C[i], C[(i + 1) % 4]
        L = math.hypot(bb[0] - a[0], bb[1] - a[1])
        B.quad([(a[0], a[1], 0), (bb[0], bb[1], 0), (bb[0], bb[1], h), (a[0], a[1], h)],
               [(off, 0), (off + L / tile_w, 0), (off + L / tile_w, vt), (off, vt)], fac)
    rh, ins = 4.5, 2.4
    I = [(x - hw + ins, y - hd + ins), (x + hw - ins, y - hd + ins), (x + hw - ins, y + hd - ins), (x - hw + ins, y + hd - ins)]
    for i in range(4):
        a, bb = C[i], C[(i + 1) % 4]
        ia, ib = I[i], I[(i + 1) % 4]
        L = math.hypot(bb[0] - a[0], bb[1] - a[1])
        B.quad([(a[0], a[1], h), (bb[0], bb[1], h), (ib[0], ib[1], h + rh), (ia[0], ia[1], h + rh)],
               [(0, 0), (L / 18, 0), (L / 18, 1), (0, 1)], mats["roof"])
    B.quad([(p[0], p[1], h + rh) for p in I], [(0, 0), (w * 0.15, 0), (w * 0.15, d * 0.15), (0, d * 0.15)], mats["slate"])
    # cornice ledge
    B.box((x, y - hd - 0.25, h - 0.3), (w + 0.6, 0.5, 0.35), mats["stone_lt"])
    B.box((x, y + hd + 0.25, h - 0.3), (w + 0.6, 0.5, 0.35), mats["stone_lt"])
    if chimneys:
        rng = random.Random(seed)
        for c in range(max(1, int(w / 9))):
            cx0 = x - hw + ins + 1 + rng.random() * (w - 2 * ins - 2)
            cy0 = y + rng.choice([-1, 1]) * (hd - ins - 0.6)
            B.box((cx0, cy0, h + rh + 0.9), (1.8, 1.0, 2.4), mats["stone"])
            B.box((cx0, cy0, h + rh + 2.2), (2.0, 1.1, 0.25), mats["stone_lt"])


_TREE = {}


def tree(x, y, h=9, r=3.2, seed=0, mats=None):
    """Linked-duplicate tree (shared meshes => fast)."""
    mats = mats or M()
    if "crown" not in _TREE:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
        s = bpy.context.active_object
        s.data.materials.append(mats["tree"])
        disp = s.modifiers.new("d", "DISPLACE")
        tx = bpy.data.textures.new("tcl", "CLOUDS")
        tx.noise_scale = 0.45
        disp.texture = tx
        disp.strength = 0.35
        b3d.apply_mods(s)
        for p in s.data.polygons:
            p.use_smooth = True
        _TREE["crown"] = s.data
        bpy.data.objects.remove(s)
        tr = cyl("trunk_proto", (0, 0, 0), (0, 0, 1), 0.12, mats["trunk"], verts=6, r1=0.08)
        _TREE["trunk"] = tr.data
        bpy.data.objects.remove(tr)
    rng = random.Random(seed)
    c = bpy.data.objects.new(f"crown{seed}", _TREE["crown"])
    c.location = (x, y, h * 0.68)
    c.scale = (r, r, r * (0.85 + rng.random() * 0.25))
    c.rotation_euler = (0, 0, rng.random() * 6.28)
    b3d.link(c)
    t = bpy.data.objects.new(f"trunk{seed}", _TREE["trunk"])
    t.location = (x, y, 0)
    t.scale = (r * 0.6, r * 0.6, h * 0.6)
    b3d.link(t)
    return [c, t]


def _move_to_active(ob):
    c = b3d._ACTIVE[0]
    if c is None:
        return
    for col in list(ob.users_collection):
        col.objects.unlink(ob)
    c.objects.link(ob)


def lamp_post(x, y, mats, h=4.2, name="lamp", lit=True):
    parts = [cyl(name + "_p", (x, y, 0), (x, y, h), 0.08, mats["black"], verts=8, r1=0.06),
             cyl(name + "_b", (x, y, 0), (x, y, 0.6), 0.16, mats["black"], verts=8, r1=0.1),
             box(name + "_h", (x, y, h + 0.25), (0.42, 0.42, 0.5), mats["lamp"] if lit else mats["glass"]),
             cyl(name + "_c", (x, y, h + 0.5), (x, y, h + 0.85), 0.3, mats["black"], verts=8, r1=0.02)]
    return parts


# ======================================================================= vehicles
def _origin_to_world(ob):
    """Bake the object's transform into its mesh so its origin is the world origin."""
    from mathutils import Matrix
    ob.data.transform(ob.matrix_basis)
    ob.matrix_basis = Matrix.Identity(4)


def _parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def vintage_car(name="car", body_col="#1d2a3a", mats=None):
    """1920s town car, ~4.2m long, facing +x. Returns root empty (parented parts) and wheel list."""
    mats = mats or M()
    paint = mat(name + "_paint", hexrgb(body_col), rough=0.25, coat=1.0, spec=0.6)
    parts = []
    parts.append(box(name + "_chassis", (0, 0, 0.62), (4.0, 1.5, 0.35), paint, bevel=0.08))
    parts.append(box(name + "_hood", (1.25, 0, 0.98), (1.4, 1.05, 0.55), paint, bevel=0.1))
    parts.append(box(name + "_grille", (1.98, 0, 0.98), (0.1, 0.95, 0.62), mats["chrome"], bevel=0.03))
    parts.append(box(name + "_cab", (-0.55, 0, 1.35), (2.1, 1.42, 1.25), paint, bevel=0.1))
    parts.append(box(name + "_roof", (-0.55, 0, 2.02), (2.25, 1.5, 0.1), mats["black"], bevel=0.04))
    for s in (-1, 1):
        parts.append(box(name + f"_win{s}", (-0.45, s * 0.715, 1.55), (1.7, 0.02, 0.55), mats["glass"]))
        # fenders (half cylinders approximated)
        for fx in (1.35, -1.35):
            parts.append(cyl(name + f"_fend{s}{fx}", (fx, s * 0.62, 0.62), (fx, s * 0.95, 0.62), 0.5, mats["black"], verts=16))
        parts.append(box(name + f"_run{s}", (0, s * 0.85, 0.42), (1.8, 0.35, 0.06), mats["black"]))
        parts.append(cyl(name + f"_hl{s}", (2.05, s * 0.55, 1.08), (2.25, s * 0.55, 1.08), 0.16, mats["chrome"], verts=12))
    parts.append(box(name + "_wind", (0.38, 0, 1.6), (0.04, 1.3, 0.6), mats["glass"]))
    body = b3d.join(parts, name)
    _origin_to_world(body)
    wheels = []
    for fx in (1.35, -1.35):
        for s in (-1, 1):
            w = cyl(name + f"_wh{fx}{s}", (fx, s * 0.78, 0.42), (fx, s * 0.78 + s * 0.2, 0.42), 0.42, mats["rubber"], verts=20)
            hub = cyl(name + f"_hub{fx}{s}", (fx, s * 0.78 + s * 0.2, 0.42), (fx, s * 0.78 + s * 0.24, 0.42), 0.2, mats["chrome"], verts=12)
            ww = b3d.join([w, hub], name + f"_wheel{fx}{s}")
            _origin_to_world(ww)
            ww.parent = body
            wheels.append(ww)
    return body, wheels


# ======================================================================= city
def city(mats=None, seed=7, radius=900, lit=False, detail_zone=None, skip=None):
    """Paris around the tower: Champ de Mars, Seine, Haussmann blocks."""
    mats = mats or M()
    rng = random.Random(seed)
    ground = plane("ground", (0, 0, -0.05), (6000, 6000), mats["cobble"], uv=(600, 600))
    # Champ de Mars lawns (tower at 0,0; park toward -y)
    plane("lawn1", (-30, -330, 0.02), (40, 520), mats["grass"])
    plane("lawn2", (30, -330, 0.02), (40, 520), mats["grass"])
    plane("lawn3", (0, -110, 0.02), (150, 60), mats["grass"])
    plane("gravel", (0, -330, 0.01), (220, 560), mats["pavement"], uv=(40, 100))
    for i in range(26):
        for s in (-1, 1):
            tree(s * 85, -120 - i * 20, 10, 3.6, seed=i * 2 + (s > 0), mats=mats)
            tree(s * 60, -120 - i * 20, 9, 3.2, seed=i * 2 + 100 + (s > 0), mats=mats)
    # the Seine toward +y
    river = plane("seine", (0, 260, 0.05), (6000, 120), mats["water"])
    for s in (-1, 1):
        box(f"quay{s}", (0, 260 + s * 61, 0.6), (6000, 3, 1.4), mats["stone"])
    # bridge (Pont d'Iéna) in line with the tower
    box("bridge", (0, 260, 2.5), (35, 130, 1.5), mats["stone_lt"])
    for k in range(-2, 3):
        box(f"pier{k}", (0, 260 + k * 26, 1.0), (37, 4, 2.2), mats["stone"])
    # Haussmann blocks (one builder)
    B = Builder("city_blocks")
    for gx in range(-radius, radius + 1, 70):
        for gy in range(-radius - 4, radius + 1, 64):
            if abs(gx) < 130 and -700 < gy < 130:
                continue  # park
            if 180 < gy < 340:
                continue  # river corridor
            if math.hypot(gx, gy) > radius:
                continue
            if skip and skip(gx, gy):
                continue
            w = 58 + rng.uniform(-2, 2)
            dd = 50
            fl = rng.choice([6, 6, 7, 7, 5])
            if math.hypot(gx, gy) > 450:
                building(B, gx, gy, w, dd, fl, mats, seed=rng.randint(0, 999), lit=lit, chimneys=False)
            else:
                building(B, gx, gy - dd / 4, w, dd / 2 - 0.5, fl, mats, seed=rng.randint(0, 999), lit=lit)
                building(B, gx, gy + dd / 4, w, dd / 2 - 0.5, rng.choice([6, 7]), mats, seed=rng.randint(0, 999), lit=lit)
    # distant low-detail ring to the horizon
    for i in range(500):
        a = rng.random() * 6.283
        rr = radius + 60 + rng.random() * 1800
        gx, gy = math.cos(a) * rr, math.sin(a) * rr
        if 150 < gy < 370:
            continue
        building(B, gx, gy, 60, 50, rng.choice([5, 6, 7]), mats, seed=rng.randint(0, 999), lit=lit, chimneys=False)
    return B.build()


# ======================================================================= props
def paper(name, path, w, h, loc, rot=(0, 0, 0), rough=0.7):
    m = mat_image("pap_" + os.path.basename(path), path, rough=rough, extension="CLIP")
    ob = plane(name, loc, (w, h), m, rot=rot)
    return ob


def envelope(name, loc, rot=(0, 0, 0), thick=0.012, addressed=False, size=(0.24, 0.13)):
    m = mat_image("env_" + ("a" if addressed else "p"), T("envelope" if addressed else "envelope_plain"), rough=0.75,
                  extension="CLIP")
    side = mat("env_side", hexrgb("#d9c8a0"), rough=0.8)
    w, h = size
    ob = box(name, loc, (w, h, thick), side, rot=rot, bevel=0.003)
    top = plane(name + "_top", (0, 0, thick / 2 + 0.0005), (w, h), m)
    top.parent = ob
    # flap line
    return ob


def cash_stack(name, loc, n=1, rot=(0, 0, 0), size=(0.16, 0.085)):
    m = mat_image("banknote", T("banknote"), rough=0.7, extension="CLIP")
    root = box(name, loc, (size[0], size[1], 0.012 * n), mat("note_edge", hexrgb("#c9bb92"), rough=0.8), rot=rot)
    top = plane(name + "_top", (0, 0, 0.006 * n + 0.0005), size, m)
    top.parent = root
    band = box(name + "_band", (0, 0, 0), (0.03, size[1] + 0.004, 0.012 * n + 0.004), mat("band", hexrgb("#8a2b24"), rough=0.6))
    band.parent = root
    return root


def fountain_pen(name, mats):
    body = cyl(name + "_body", (0, 0, 0.02), (0, 0, 0.15), 0.0065, mat("pen_black", hexrgb("#121214"), rough=0.15, coat=1.0),
               verts=16, r1=0.0055)
    nib = cyl(name + "_nib", (0, 0, 0.0), (0, 0, 0.022), 0.0005, mats["gold"], verts=10, r1=0.0058)
    band = cyl(name + "_band", (0, 0, 0.1), (0, 0, 0.106), 0.0068, mats["gold"], verts=16)
    clip = box(name + "_clip", (0.007, 0, 0.13), (0.002, 0.003, 0.04), mats["gold"])
    pen = b3d.join([body, nib, band, clip], name)
    return pen


def rubber_stamp(name, mats):
    base = box(name + "_base", (0, 0, 0.015), (0.075, 0.075, 0.03), mats["wood"], bevel=0.004)
    pad = box(name + "_pad", (0, 0, 0.002), (0.07, 0.07, 0.006), mat("stamp_rubber", hexrgb("#6b1d22"), rough=0.7))
    stem = cyl(name + "_stem", (0, 0, 0.03), (0, 0, 0.08), 0.012, mats["brass"], verts=12)
    knob = cyl(name + "_knob", (0, 0, 0.08), (0, 0, 0.12), 0.026, mats["wood"], verts=20, r1=0.02)
    return b3d.join([base, pad, stem, knob], name)


def briefcase(name, mats, loc=(0, 0, 0)):
    body = box(name, (0, 0, 0.17), (0.44, 0.11, 0.32), mats["leather"], bevel=0.02)
    h = cyl(name + "_h", (-0.06, 0, 0.36), (0.06, 0, 0.36), 0.012, mats["leather"], verts=8)
    l1 = box(name + "_l1", (-0.12, 0.057, 0.3), (0.03, 0.006, 0.03), mats["brass"])
    l2 = box(name + "_l2", (0.12, 0.057, 0.3), (0.03, 0.006, 0.03), mats["brass"])
    ob = b3d.join([body, h, l1, l2], name)
    ob.location = loc
    return ob


def chair(name, mats, loc, rot_z=0.0, seat_col="cloth_red"):
    parts = []
    for sx in (-0.2, 0.2):
        for sy in (-0.2, 0.2):
            parts.append(box(f"{name}_leg{sx}{sy}", (sx, sy, 0.22), (0.045, 0.045, 0.44), mats["wood"]))
    parts.append(box(name + "_seat", (0, 0, 0.47), (0.48, 0.48, 0.07), mats[seat_col], bevel=0.02))
    parts.append(box(name + "_back", (0, 0.22, 0.85), (0.46, 0.06, 0.72), mats["wood"], bevel=0.02))
    parts.append(box(name + "_pad", (0, 0.19, 0.86), (0.36, 0.02, 0.52), mats[seat_col], bevel=0.01))
    ob = b3d.join(parts, name)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    return ob


def chandelier(name, mats, loc, r=0.7, lit=True):
    parts = [cyl(name + "_rod", (0, 0, 0.6), (0, 0, 2.0), 0.015, mats["brass"], verts=8),
             cyl(name + "_hub", (0, 0, 0.3), (0, 0, 0.6), 0.08, mats["brass"], verts=12, r1=0.03)]
    bulbs = []
    for i in range(8):
        a = i * math.pi / 4
        x, y = math.cos(a) * r, math.sin(a) * r
        parts.append(cyl(f"{name}_arm{i}", (0, 0, 0.35), (x, y, 0.3), 0.012, mats["brass"], verts=6))
        parts.append(cyl(f"{name}_cup{i}", (x, y, 0.28), (x, y, 0.34), 0.04, mats["brass"], verts=10, r1=0.05))
        bulbs.append(cyl(f"{name}_bulb{i}", (x, y, 0.34), (x, y, 0.42), 0.022, mats["lamp"], verts=8, r1=0.012))
    ob = b3d.join(parts + bulbs, name)
    ob.location = loc
    if lit:
        b3d.point((loc[0], loc[1], loc[2] + 0.3), 260, (1, 0.72, 0.42), radius=0.6, name=name + "_l")
    return ob


def room_shell(name, size, mats, wall_mat, floor_mat, ceil_mat=None, wainscot=1.1, open_side=None,
               windows=None, win_light=None):
    """Box room centred at origin on the floor. open_side in ('-y',...) removes that wall for cameras."""
    W, D, H = size
    parts = []
    parts.append(box(name + "_floor", (0, 0, -0.05), (W, D, 0.1), floor_mat))
    if ceil_mat:
        parts.append(box(name + "_ceil", (0, 0, H + 0.05), (W, D, 0.1), ceil_mat))
        parts.append(box(name + "_cornice", (0, D / 2 - 0.1, H - 0.15), (W, 0.25, 0.3), mats["gold"]))
    walls = {"+y": ((0, D / 2 + 0.05, H / 2), (W, 0.1, H)), "-y": ((0, -D / 2 - 0.05, H / 2), (W, 0.1, H)),
             "+x": ((W / 2 + 0.05, 0, H / 2), (0.1, D, H)), "-x": ((-W / 2 - 0.05, 0, H / 2), (0.1, D, H))}
    for k, (c, s) in walls.items():
        if open_side and k in open_side:
            continue
        parts.append(box(f"{name}_wall{k}", c, s, wall_mat, uv_scale=0.6))
        # wainscot panel
        c2 = list(c)
        s2 = list(s)
        c2[2] = wainscot / 2
        s2[2] = wainscot
        if k in ("+y", "-y"):
            c2[1] -= 0.04 * (1 if k == "+y" else -1)
        else:
            c2[0] -= 0.04 * (1 if k == "+x" else -1)
        parts.append(box(f"{name}_wain{k}", tuple(c2), tuple(s2), mats["wood"], bevel=0.01))
        c3 = list(c2)
        c3[2] = wainscot
        s3 = list(s2)
        s3[2] = 0.06
        parts.append(box(f"{name}_rail{k}", tuple(c3), tuple(s3), mats["gold"]))
    return parts


def window(name, mats, loc, w=1.4, h=2.6, wall="+y", sky=(1.0, 0.82, 0.55), strength=6.0, frame="white"):
    """A glowing window (emissive pane) with frame + glazing bars, placed on a wall plane."""
    pane = b3d.mat_emit(name + "_sky", sky, strength)
    rx = math.pi / 2
    x, y, z = loc
    parts = [box(name + "_pane", (x, y, z), (w, 0.02, h), pane)]
    fm = mats["white"] if frame == "white" else mats["wood"]
    for dx in (-w / 2, 0, w / 2):
        parts.append(box(f"{name}_v{dx}", (x + dx, y - 0.03, z), (0.07, 0.05, h + 0.07), fm))
    for dz in (-h / 2, -h / 6, h / 6, h / 2):
        parts.append(box(f"{name}_h{dz}", (x, y - 0.03, z + dz), (w + 0.07, 0.05, 0.06), fm))
    ob = b3d.join(parts, name)
    if wall == "-x":
        ob.rotation_euler = (0, 0, math.pi / 2)
    return ob


def painting(name, mats, loc, w=0.9, h=0.7, col=("#6b5a3a", "#2c3a44"), rot_z=0.0):
    canvas = mat_noise(name + "_cv", hexrgb(col[0]), hexrgb(col[1]), scale=2.0, rough=0.6, bump=0.05)
    f = box(name + "_f", (0, 0, 0), (w + 0.12, 0.05, h + 0.12), mats["gold"], bevel=0.015)
    c = box(name + "_c", (0, -0.02, 0), (w, 0.03, h), canvas)
    ob = b3d.join([f, c], name)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    return ob


# ======================================================================= interiors
def meeting_room(mats, dressing="day"):
    """Hotel salon. Table along x at origin (top z=0.78). Far wall +y has windows; camera side -y open."""
    paper_m = mat_image("wallpaper_red", T("wallpaper"), rough=0.8)
    parq = mat_image("parquet", T("parquet"), rough=0.35, coat=0.3)
    ceil = mat("ceiling", hexrgb("#e8dcc4"), rough=0.9)
    parts = room_shell("salon", (11, 8, 4.4), mats, paper_m, parq, ceil, open_side=("-y",))
    for i, x in enumerate((-3.2, 0, 3.2)):
        window(f"win{i}", mats, (x, 3.95, 2.0), 1.5, 2.8, sky=(1.0, 0.78, 0.5), strength=2.2)
        # curtains
        for s in (-1, 1):
            box(f"curt{i}{s}", (x + s * 1.05, 3.85, 2.05), (0.5, 0.12, 3.6), mats["cloth_red"], bevel=0.05)
        box(f"pelmet{i}", (x, 3.82, 3.75), (2.7, 0.18, 0.35), mats["gold"], bevel=0.03)
    # sunlight through windows
    s = b3d.sun(2.2, rot=(math.radians(60), 0, math.radians(195)), color=(1.0, 0.78, 0.5), angle=2)
    for i, x in enumerate((-3.2, 0, 3.2)):
        b3d.point((x, 3.7, 2.0), 60, (1, 0.8, 0.55), name=f"winl{i}", kind="AREA", size=1.4).rotation_euler = (math.radians(90), 0, 0)
    painting("paint1", mats, (-5.44, 0.5, 2.4), 1.2, 0.9, rot_z=math.pi / 2)
    painting("paint2", mats, (5.44, 0.5, 2.4), 1.0, 1.2, ("#7a4a2a", "#3a4a32"), rot_z=math.pi / 2)
    # table
    top = box("table_top", (0, 0, 0.76), (4.4, 1.5, 0.07), mats["wood"], bevel=0.02)
    apron = box("table_apron", (0, 0, 0.68), (4.2, 1.3, 0.12), mats["wood"])
    legs = [cyl(f"tleg{i}", (x, y, 0), (x, y, 0.66), 0.05, mats["wood"], verts=12, r1=0.04)
            for i, (x, y) in enumerate([(-1.95, -0.55), (1.95, -0.55), (-1.95, 0.55), (1.95, 0.55)])]
    table = b3d.join([top, apron] + legs, "table")
    runner = box("runner", (0, 0, 0.797), (3.6, 0.42, 0.004), mats["cloth_green"])
    # chairs on the far side (behind seated dealers)
    for i, x in enumerate((-1.3, 0.0, 1.3)):
        chair(f"chair{i}", mats, (x, 1.12, 0), rot_z=0.0)
    chair("chair_end", mats, (2.75, 0.0, 0), rot_z=math.pi / 2)
    chandelier("chand", mats, (0, 0, 2.6))
    # dressing
    lamp_t = b3d.point((0, 0, 2.2), 80, (1, 0.75, 0.45), radius=1.0, name="fill")
    return {"table_z": 0.795}


def table_dressing(mats, docs=True, seed=0):
    rng = random.Random(seed)
    objs = []
    if docs:
        for i, (x, y, r) in enumerate([(-1.3, 0.3, 0.2), (0.0, 0.35, -0.1), (1.3, 0.3, 0.15), (-0.5, -0.2, 0.05), (0.7, -0.25, -0.2)]):
            objs.append(paper(f"doc{i}", T("letter_stamped" if i % 2 else "contract"), 0.21, 0.29, (x, y, 0.80 + i * 0.0004),
                              rot=(0, 0, r)))
    inkwell = cyl("inkwell", (1.85, -0.3, 0.8), (1.85, -0.3, 0.87), 0.045, mats["glass"], verts=16, r1=0.03)
    carafe = cyl("carafe", (-1.85, 0.25, 0.8), (-1.85, 0.25, 1.05), 0.07, mat("crystal", (0.9, 0.85, 0.75), rough=0.05, spec=0.9),
                 verts=20, r1=0.025)
    for i in range(3):
        cyl(f"glass{i}", (-1.65 + i * 0.12, 0.45, 0.8), (-1.65 + i * 0.12, 0.45, 0.9), 0.03,
            mat("crystal", (0.9, 0.85, 0.75), rough=0.05, spec=0.9), verts=14, r1=0.035)
    return objs


def office(mats):
    """Poisson's office: desk at origin (top z=0.76), window behind (+y) onto the scrapyard."""
    wall = mat_image("wallpaper_green", T("wallpaper_green"), rough=0.8)
    parq = mat_image("parquet", T("parquet"), rough=0.35, coat=0.3)
    parts = room_shell("office", (6, 5, 3.4), mats, wall, parq, mat("ceil2", hexrgb("#d9cdb4"), rough=0.9), open_side=("-y",))
    window("owin", mats, (0.4, 2.45, 1.75), 2.2, 2.0, sky=(0.95, 0.8, 0.6), strength=3.0, frame="wood")
    # scrapyard visible outside: girder stacks
    yard = []
    for i in range(10):
        x = -3 + i * 0.75
        yard.append(box(f"gird{i}", (x, 8 + (i % 3), 0.3 + (i % 4) * 0.35), (5, 0.3, 0.3), mats["iron"], rot=(0, 0, 0.3 * (i % 2))))
    box("yard_wall", (0, 14, 2), (30, 0.5, 4), mats["stone"])
    b3d.point((0.4, 4.0, 2.2), 800, (1, 0.82, 0.6), name="yardsun", kind="AREA", size=4)
    sign_m = mat_image("office_sign", T("office_sign"), rough=0.5)
    plane("osign", (-1.9, 2.44, 2.65), (1.6, 0.23), sign_m, rot=(math.radians(90), 0, math.pi))
    # desk
    top = box("desk_top", (0, 0, 0.74), (1.8, 0.85, 0.06), mats["wood"], bevel=0.015)
    pd1 = box("desk_ped1", (-0.6, 0, 0.36), (0.5, 0.78, 0.72), mats["wood_mid"], bevel=0.01)
    pd2 = box("desk_ped2", (0.6, 0, 0.36), (0.5, 0.78, 0.72), mats["wood_mid"], bevel=0.01)
    blotter = box("blotter", (0, -0.05, 0.773), (0.7, 0.45, 0.006), mats["cloth_green"])
    b3d.join([top, pd1, pd2], "desk")
    # green banker's lamp
    lamp_m = mat("lampshade", hexrgb("#1f6b45"), rough=0.2, coat=1.0, spec=0.6)
    cyl("lamp_base", (0.65, 0.2, 0.77), (0.65, 0.2, 0.8), 0.07, mats["brass"], verts=16)
    cyl("lamp_stem", (0.65, 0.2, 0.8), (0.65, 0.2, 1.08), 0.01, mats["brass"], verts=8)
    shade = cyl("lamp_shade", (0.5, 0.2, 1.1), (0.8, 0.2, 1.1), 0.07, lamp_m, verts=16, r1=0.07)
    b3d.point((0.65, 0.15, 1.02), 25, (1, 0.8, 0.5), radius=0.05, name="desklamp")
    # cabinet + shelves
    box("cabinet", (2.4, 1.8, 0.7), (0.9, 0.6, 1.4), mats["wood_mid"], bevel=0.01)
    box("shelf", (-2.6, 1.5, 1.2), (0.6, 1.6, 2.4), mats["wood"], bevel=0.01)
    for i in range(12):
        box(f"book{i}", (-2.45, 0.9 + i * 0.1, 1.5 + (i % 3) * 0.02), (0.25, 0.07, 0.32),
            mat(f"book{i%4}", hexrgb(["#5a1e1e", "#1e3a5a", "#3a4a22", "#6b4a1e"][i % 4]), rough=0.7))
    chair("ochair", mats, (0, 0.75, 0), seat_col="leather")
    b3d.point((0, -1.5, 2.6), 120, (1, 0.85, 0.65), radius=1.5, name="ofill", kind="AREA", size=2.5).rotation_euler = (math.radians(30), 0, 0)
    return {"desk_z": 0.776}


def forge_desk(mats):
    """Lustig's hotel-room writing desk at night: one warm lamp, dark room."""
    wall = mat_image("wallpaper_red", T("wallpaper"), rough=0.8)
    parq = mat_image("parquet", T("parquet"), rough=0.35, coat=0.3)
    room_shell("froom", (5, 4, 3.4), mats, wall, parq, None, open_side=("-y",))
    window("fwin", mats, (1.4, 1.95, 1.8), 1.2, 2.0, sky=(0.12, 0.18, 0.35), strength=1.5)
    top = box("fdesk", (0, 0, 0.74), (1.4, 0.75, 0.05), mats["wood"], bevel=0.012)
    box("fdesk_body", (0, 0.05, 0.4), (1.3, 0.6, 0.65), mats["wood_mid"])
    box("fblot", (0, -0.05, 0.768), (0.62, 0.42, 0.005), mats["leather"])
    # lamp with warm shade
    cyl("flamp_b", (-0.45, 0.2, 0.765), (-0.45, 0.2, 0.79), 0.07, mats["brass"], verts=16)
    cyl("flamp_s", (-0.45, 0.2, 0.79), (-0.45, 0.2, 1.1), 0.012, mats["brass"], verts=8)
    shade_m = mat("fshade", hexrgb("#d9a25a"), rough=0.6, emit=(1, 0.65, 0.3), emit_s=1.5)
    cyl("flamp_sh", (-0.45, 0.2, 1.05), (-0.45, 0.2, 1.22), 0.16, shade_m, verts=24, r1=0.09, cap=False)
    b3d.point((-0.45, 0.2, 1.08), 40, (1, 0.72, 0.4), radius=0.06, name="flamp")
    # inkwell, blotter, candle, papers stack
    cyl("finkw", (0.45, 0.22, 0.765), (0.45, 0.22, 0.83), 0.04, mats["glass"], verts=16, r1=0.028)
    for i in range(4):
        paper(f"fstack{i}", T("letter"), 0.21, 0.29, (0.42, -0.05, 0.768 + i * 0.002), rot=(0, 0, 0.05 * i))
    b3d.point((0.5, -1.2, 1.6), 6, (0.5, 0.6, 1.0), radius=1, name="moonfill", kind="AREA", size=2)
    return {"desk_z": 0.7685}


def lobby(mats):
    """Grand hotel lobby: long marble hall along +y, carpet runner, columns, chandeliers."""
    marble = mat_image("marble", T("marble"), rough=0.12, coat=0.6)
    wall = mat_noise("lobbywall", hexrgb("#e6d6b4"), hexrgb("#d6c29a"), scale=2, rough=0.7, bump=0.02)
    ceil = mat("lobbyceil", hexrgb("#efe4cc"), rough=0.8)
    W, D, H = 12, 26, 7
    box("lfloor", (0, D / 2 - 3, -0.05), (W, D, 0.1), marble, uv_scale=0.25)
    box("lceil", (0, D / 2 - 3, H), (W, D, 0.1), ceil)
    for s in (-1, 1):
        box(f"lwall{s}", (s * W / 2, D / 2 - 3, H / 2), (0.2, D, H), wall)
        for i in range(6):
            y = i * 4.2
            cyl(f"col{s}{i}", (s * 4.3, y, 0), (s * 4.3, y, H), 0.38, marble, verts=24)
            box(f"colb{s}{i}", (s * 4.3, y, 0.25), (1.0, 1.0, 0.5), mats["stone_lt"], bevel=0.04)
            box(f"colc{s}{i}", (s * 4.3, y, H - 0.35), (1.05, 1.05, 0.7), mats["gold"], bevel=0.05)
            if i < 5:
                window(f"lw{s}{i}", mats, (s * 5.85, y + 2.1, 3.2), 1.6, 3.6, strength=6.0)
                ob = bpy.data.objects[f"lw{s}{i}"]
                ob.rotation_euler = (0, 0, math.pi / 2)
                ob.location = (s * 5.88, y + 2.1, 3.2)
    box("lend", (0, D - 3, H / 2), (W, 0.2, H), wall)
    # double doors at the end (to the salon) with warm light
    door_m = b3d.mat_emit("doorglow", (1, 0.78, 0.5), 3.0)
    box("ldoor", (0, D - 3.12, 1.6), (2.2, 0.05, 3.2), mats["wood"], bevel=0.02)
    box("ldoor_glow", (0, D - 3.15, 1.6), (0.12, 0.04, 3.1), door_m)
    box("ldoor_frame", (0, D - 3.1, 3.4), (2.6, 0.1, 0.35), mats["gold"])
    box("carpet", (0, D / 2 - 3, 0.005), (2.4, D, 0.01), mats["cloth_red"])
    for i in range(3):
        chandelier(f"lch{i}", mats, (0, 2 + i * 7, H - 2.2), r=1.0)
    # reception desk + palms
    box("recep", (-3.4, 6, 0.55), (0.9, 3.5, 1.1), mats["wood"], bevel=0.03)
    box("recep_top", (-3.4, 6, 1.12), (1.0, 3.6, 0.06), marble)
    for i, (x, y) in enumerate([(2.8, 3), (2.8, 10), (-2.8, 14)]):
        cyl(f"pot{i}", (x, y, 0), (x, y, 0.6), 0.32, mats["brass"], verts=20, r1=0.38)
        for k in range(7):
            a = k * 0.9
            leaf = box(f"leaf{i}{k}", (x + math.cos(a) * 0.45, y + math.sin(a) * 0.45, 1.3), (0.9, 0.18, 0.02), mats["tree"],
                       rot=(0, -0.6, a))
    b3d.sun(2.0, rot=(math.radians(55), 0, math.radians(80)), color=(1, 0.8, 0.55))
    return {}


def station(mats):
    """Paris terminus platform with iron/glass train shed; track along +x at y=0."""
    plat = box("platform", (0, -3.2, 0.5), (200, 4.4, 1.0), mats["stone"], uv_scale=0.5)
    box("plat_edge", (0, -1.05, 0.98), (200, 0.3, 0.06), mats["stone_lt"])
    box("plat2", (0, 6.5, 0.5), (200, 4.4, 1.0), mats["stone"])
    plane("ballast", (0, 2.2, 0.0), (200, 9), mat_noise("ballast", hexrgb("#4a4440"), hexrgb("#6a625a"), scale=60, rough=0.95, bump=0.4))
    for y in (-0.72, 0.72, 3.7, 5.14):
        box(f"rail{y}", (0, y, 0.12), (200, 0.08, 0.12), mats["chrome"])
    for i in range(-100, 100, 1):
        box(f"sleeper{i}", (i * 0.9, 0.0, 0.04), (0.25, 2.4, 0.1), mats["trunk"]) if i % 1 == 0 else None
    # train shed: arched trusses
    segs = []
    for i in range(-12, 13):
        x = i * 6.0
        for s in (-1, 1):
            segs.append(((x, s * 11, 0), (x, s * 11, 9), 0.4))
        prev = None
        for k in range(17):
            u = k / 16
            y = -11 + 22 * u
            z = 9 + 7 * math.sin(math.pi * u)
            if prev:
                segs.append((prev, (x, y, z), 0.35))
                segs.append(((prev[0], prev[1], prev[2] - 0.8), (x, y, z - 0.8), 0.18))
                segs.append((prev, (x, y, z - 0.8), 0.12))
            prev = (x, y, z)
        if i < 12:
            for k in range(0, 17, 4):
                u = k / 16
                y = -11 + 22 * u
                z = 9 + 7 * math.sin(math.pi * u)
                segs.append(((x, y, z), (x + 6, y, z), 0.2))
    struts_mesh("shed", segs, mats["iron_dk"])
    glass = mat("roofglass", (0.85, 0.8, 0.7), rough=0.3, spec=0.3, emit=(1.0, 0.85, 0.6), emit_s=1.2)
    # glass roof as strips
    vs, fs = [], []
    for k in range(16):
        u0, u1 = k / 16, (k + 1) / 16
        y0, y1 = -11 + 22 * u0, -11 + 22 * u1
        z0, z1 = 9 + 7 * math.sin(math.pi * u0) + 0.2, 9 + 7 * math.sin(math.pi * u1) + 0.2
        b = len(vs)
        vs += [(-75, y0, z0), (75, y0, z0), (75, y1, z1), (-75, y1, z1)]
        fs.append((b, b + 1, b + 2, b + 3))
    b3d.mesh_obj("shed_glass", vs, fs, glass)
    sm = mat_image("station_sign", T("station_sign"), rough=0.5)
    for x in (-6, 14):
        plane(f"ssign{x}", (x, -2.2, 3.4), (3.5, 0.5), sm, rot=(math.radians(90), 0, 0))
        cyl(f"ssp{x}a", (x - 1.6, -2.2, 1.0), (x - 1.6, -2.2, 3.7), 0.05, mats["black"], verts=8)
        cyl(f"ssp{x}b", (x + 1.6, -2.2, 1.0), (x + 1.6, -2.2, 3.7), 0.05, mats["black"], verts=8)
    for i in range(-6, 7):
        lamp_post(i * 9 + 4, -4.6, mats, h=3.4, name=f"slamp{i}")
        for k in range(len(lamp_post.__defaults__ or ())):
            pass
    b3d.sun(2.5, rot=(math.radians(55), 0, math.radians(150)), color=(1, 0.8, 0.55), angle=3)
    return {}


def locomotive(name, mats):
    """Steam locomotive facing +x, length ~13m. Returns root object (parented parts) and wheel list."""
    black = mat("loco_black", hexrgb("#16171a"), rough=0.35, coat=0.5)
    red = mat("loco_red", hexrgb("#7a1f1a"), rough=0.4, coat=0.3)
    green = mat("coach_green", hexrgb("#2d4a38"), rough=0.4, coat=0.5)
    parts = [cyl(name + "_boiler", (-1.5, 0, 2.35), (5.6, 0, 2.35), 0.95, black, verts=28),
             cyl(name + "_smoke", (5.6, 0, 2.35), (5.8, 0, 2.35), 1.0, mats["iron_dk"], verts=28),
             cyl(name + "_stack", (4.9, 0, 3.0), (4.9, 0, 4.25), 0.3, black, verts=16, r1=0.38),
             cyl(name + "_dome", (2.0, 0, 3.0), (2.0, 0, 3.55), 0.42, mats["brass"], verts=16, r1=0.3),
             box(name + "_cab", (-2.6, 0, 2.8), (2.4, 2.6, 2.4), black, bevel=0.05),
             box(name + "_cabroof", (-2.6, 0, 4.05), (2.8, 2.8, 0.15), black, bevel=0.03),
             box(name + "_frame", (1.5, 0, 1.1), (11.5, 2.2, 0.5), red),
             box(name + "_buffer", (6.3, 0, 1.2), (0.3, 2.6, 0.4), red),
             box(name + "_tender", (-5.6, 0, 2.2), (3.2, 2.7, 2.0), black, bevel=0.05)]
    for s in (-1, 1):
        parts.append(box(name + f"_cabwin{s}", (-2.6, s * 1.31, 3.1), (1.0, 0.02, 0.7), mats["lamp"]))
        parts.append(box(name + f"_rod{s}", (1.4, s * 1.2, 0.95), (4.5, 0.08, 0.12), mats["chrome"]))
    parts.append(cyl(name + "_lamp", (6.0, 0, 1.75), (6.25, 0, 1.75), 0.18, mats["lamp"], verts=12))
    body = b3d.join(parts, name)
    _origin_to_world(body)
    wheels = []
    for i, x in enumerate((-0.6, 1.4, 3.4)):
        for s in (-1, 1):
            w = cyl(name + f"_w{i}{s}", (x, s * 1.05, 0.95), (x, s * 1.2, 0.95), 0.92, red, verts=24)
            _origin_to_world(w)
            w.parent = body
            wheels.append(w)
    for i, x in enumerate((5.0, -4.6, -6.6)):
        for s in (-1, 1):
            w = cyl(name + f"_sw{i}{s}", (x, s * 1.05, 0.55), (x, s * 1.2, 0.55), 0.5, red, verts=16)
            _origin_to_world(w)
            w.parent = body
    # coaches
    for c in range(3):
        cx = -10.5 - c * 13.5
        co = [box(f"{name}_coach{c}", (cx, 0, 2.35), (12.8, 2.8, 2.6), green, bevel=0.06),
              box(f"{name}_croof{c}", (cx, 0, 3.75), (13.0, 2.9, 0.25), black, bevel=0.1),
              box(f"{name}_cfr{c}", (cx, 0, 0.95), (12.0, 2.2, 0.35), black)]
        for wv in range(6):
            for s in (-1, 1):
                co.append(box(f"{name}_cw{c}{wv}{s}", (cx - 5 + wv * 2.0, s * 1.41, 2.6), (1.2, 0.02, 0.9), mats["lamp"]))
        for wx in (-4.5, 4.5):
            for s in (-1, 1):
                co.append(cyl(f"{name}_cwh{c}{wx}{s}", (cx + wx, s * 1.0, 0.5), (cx + wx, s * 1.15, 0.5), 0.48, black, verts=14))
        cj = b3d.join(co, f"{name}_coach{c}")
        _origin_to_world(cj)
        cj.parent = body
    return body, wheels


def blueprint_set(mats):
    bp = mat_image("blueprint", T("blueprint"), rough=0.8)
    plane("bp_paper", (0, 0, 0), (3000, 3000), bp, uv=(12, 12))
    b3d.world_gradient(b3d.hexrgb("#e8d6b2"), b3d.hexrgb("#f1e2c2"), 1.0)
    return {}


# ======================================================================= street level
def street_detail(mats, x0=150, x1=900, y_street=28.0, half=7.0, cafe_x=420, hotel_x=330, cars=True):
    """Sidewalks, café terrace, Morris column, lamps, trees, hotel entrance along the street y=y_street (runs along x)."""
    yS = y_street - half  # south facade line
    yN = y_street + half
    for s, yy in ((-1, yS + 1.6), (1, yN - 1.6)):
        box(f"walk{s}", ((x0 + x1) / 2, yy, 0.08), (x1 - x0, 3.2, 0.16), mats["pavement"], uv_scale=0.3)
        box(f"curb{s}", ((x0 + x1) / 2, yy - s * 1.6, 0.09), (x1 - x0, 0.25, 0.18), mats["stone_lt"])
    for i, x in enumerate(range(int(x0) + 10, int(x1), 22)):
        lamp_post(x, yS + 2.8, mats, name=f"sl{i}a", lit=False)
        lamp_post(x + 11, yN - 2.8, mats, name=f"sl{i}b", lit=False)
        if abs(x + 5 - cafe_x) > 9:
            tree(x + 5, yS + 2.6, 8, 2.6, seed=300 + i, mats=mats)
        if abs(x + 16 - hotel_x) > 12:
            tree(x + 16, yN - 2.6, 8, 2.6, seed=400 + i, mats=mats)
    # café terrace on the south side
    aw = mat_image("awning", T("awning"), rough=0.8)
    a = plane("cafe_awning", (cafe_x, yS + 1.2, 3.6), (14, 2.6), aw, rot=(math.radians(-25), 0, 0), uv=(5, 1))
    box("cafe_front", (cafe_x, yS + 0.08, 1.6), (14, 0.15, 3.2), mats["wood"])
    glow = b3d.mat_emit("cafe_glow", (1, 0.72, 0.42), 2.2)
    for k in range(4):
        box(f"cafe_win{k}", (cafe_x - 5.2 + k * 3.45, yS + 0.18, 1.55), (2.8, 0.04, 2.2), glow)
    sg = mat_image("cafe_sign", T("cafe_sign"), rough=0.5)
    plane("cafe_signp", (cafe_x, yS + 0.2, 3.05), (5.5, 0.9), sg, rot=(math.radians(90), 0, 0))
    tables = []
    for k in range(5):
        tx = cafe_x - 5.5 + k * 2.6
        ty = yS + 1.3
        tables.append(bistro_table(f"bt{k}", mats, (tx, ty, 0.16)))
        for c in (-1, 1):
            bistro_chair(f"bc{k}{c}", mats, (tx + c * 0.62, ty, 0.16), math.pi / 2 * c)
    # Morris column
    mc = mat("morris", hexrgb("#2c4a38"), rough=0.5)
    cyl("morris", (cafe_x + 10, yS + 2.4, 0.16), (cafe_x + 10, yS + 2.4, 3.6), 0.65, mc, verts=24)
    cyl("morris_p", (cafe_x + 10, yS + 2.4, 1.0), (cafe_x + 10, yS + 2.4, 3.0), 0.68, mat_noise("posters", hexrgb("#d9b77a"), hexrgb("#a8502e"), 8, rough=0.8), verts=24)
    cyl("morris_top", (cafe_x + 10, yS + 2.4, 3.6), (cafe_x + 10, yS + 2.4, 4.2), 0.75, mc, verts=24, r1=0.1)
    # hotel entrance on the north side
    hs = mat_image("hotel_sign", T("hotel_sign"), rough=0.4)
    box("hotel_canopy", (hotel_x, yN - 1.5, 3.4), (5.0, 3.0, 0.18), mats["iron_dk"], bevel=0.04)
    for s in (-1, 1):
        cyl(f"hcan_post{s}", (hotel_x + s * 2.3, yN - 2.9, 0.16), (hotel_x + s * 2.3, yN - 2.9, 3.35), 0.06, mats["brass"], verts=10)
        cyl(f"hcol{s}", (hotel_x + s * 2.0, yN - 0.35, 0.16), (hotel_x + s * 2.0, yN - 0.35, 4.6), 0.3, mats["stone_lt"], verts=20)
        cyl(f"hpot{s}", (hotel_x + s * 3.0, yN - 0.8, 0.16), (hotel_x + s * 3.0, yN - 0.8, 0.8), 0.3, mats["brass"], verts=16, r1=0.36)
        tree(hotel_x + s * 3.0, yN - 0.8, 2.0, 0.5, seed=600 + s, mats=mats)
    plane("hotel_signp", (hotel_x, yN - 3.0, 3.7), (4.6, 0.85), hs, rot=(math.radians(90), 0, 0))
    box("hotel_door", (hotel_x, yN - 0.1, 1.5), (2.4, 0.1, 3.0), b3d.mat_emit("hdoor", (1, 0.75, 0.45), 2.5))
    box("hotel_carpet", (hotel_x, yN - 2.0, 0.17), (1.6, 3.8, 0.02), mats["cloth_red"])
    box("hotel_steps", (hotel_x, yN - 0.6, 0.24), (3.6, 1.0, 0.16), mats["stone_lt"])
    return {"yS": yS, "yN": yN}


def bistro_table(name, mats, loc):
    top = cyl(name + "_t", (0, 0, 0.72), (0, 0, 0.75), 0.33, mat("marbletop", hexrgb("#e9e2d4"), rough=0.2, coat=0.5), verts=24)
    st = cyl(name + "_s", (0, 0, 0.0), (0, 0, 0.72), 0.03, mats["black"], verts=8)
    ft = cyl(name + "_f", (0, 0, 0.0), (0, 0, 0.04), 0.22, mats["black"], verts=16)
    ob = b3d.join([top, st, ft], name)
    ob.location = loc
    return ob


def bistro_chair(name, mats, loc, rz):
    rat = mat_noise("rattan", hexrgb("#b88a4a"), hexrgb("#d9b170"), scale=60, rough=0.7, bump=0.2)
    parts = [cyl(name + "_seat", (0, 0, 0.45), (0, 0, 0.48), 0.22, rat, verts=16)]
    for sx, sy in ((-0.15, -0.15), (0.15, -0.15), (0.15, 0.15), (-0.15, 0.15)):
        parts.append(cyl(f"{name}_l{sx}{sy}", (sx * 1.1, sy * 1.1, 0), (sx, sy, 0.45), 0.015, mats["wood"], verts=6))
    parts.append(box(name + "_back", (0, 0.2, 0.75), (0.38, 0.03, 0.4), rat, bevel=0.02))
    ob = b3d.join(parts, name)
    ob.location = loc
    ob.rotation_euler = (0, 0, rz)
    return ob

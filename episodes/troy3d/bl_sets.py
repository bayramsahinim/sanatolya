"""Stylized 3D sets for the Troy episode (runs inside Blender, imported by bl_build.run).

Conventions: metres, Z up. Walls run along X at y=0 with the gate at x=0; the outside is -Y.
Colours are sRGB (toon() converts).
"""
import math
import random

import bpy
from mathutils import Vector

from bl_build import (bush, cloud, cone, cube, cyl, empty, grass_field, lin, lowpoly_rock, mesh_ob, pbr, point,
                      sky_world, sphere, sun, toon, water_mat, build_ship)

NIGHT_SKY = ((0.0, (0.24, 0.32, 0.55)), (0.25, (0.11, 0.17, 0.38)), (0.7, (0.04, 0.07, 0.2)))
DAY_SKY = ((0.0, (0.72, 0.88, 1.0)), (0.18, (0.36, 0.66, 1.0)), (0.6, (0.13, 0.38, 0.92)))


# ---------------------------------------------------------------- shared pieces
def clouds(n, seed, rng_x=(-260, 260), rng_y=(80, 420), z=(45, 110), size=(14, 30), night=False):
    r = random.Random(seed)
    mat = toon("CloudN", (0.42, 0.48, 0.66), 0.05, 0.9) if night else None
    for k in range(n):
        cloud(f"Cloud{seed}_{k}", (r.uniform(*rng_x), r.uniform(*rng_y), r.uniform(*z)), r.uniform(*size), k + seed,
              mat=mat)


def moon(loc=(-120, 300, 140), r=14):
    mesh_ob("Moon", sphere(32, 16), toon("MoonM", (1, 0.98, 0.9), 0.02, 1.0, emission=((1, 0.97, 0.88), 6.0)),
            loc, scale=(r, r, r)).visible_shadow = False


def night_light(moon_dir=(math.radians(40), 0, math.radians(150))):
    sky_world(NIGHT_SKY, 1.0)
    sun(1.5, moon_dir, (0.55, 0.65, 1.0), angle=1)


def day_light(rot=(math.radians(55), 0, math.radians(-50))):
    sky_world(DAY_SKY, 1.0)
    sun(3.2, rot, (1.0, 0.92, 0.78), angle=2)


def torch(name, loc, h=2.6, energy=160):
    wood = toon("TorchWood", (0.42, 0.26, 0.14), 0.1)
    mesh_ob(name + "_pole", cyl(8), wood, (loc[0], loc[1], loc[2] + h / 2), scale=(0.12, 0.12, h))
    mesh_ob(name + "_cup", cyl(10), toon("Iron2", (0.25, 0.22, 0.2), 0.1), (loc[0], loc[1], loc[2] + h),
            scale=(0.35, 0.35, 0.3))
    fl = mesh_ob(name + "_flame", cone(), toon("Flame", (1.0, 0.7, 0.25), 0.1, 1.0, emission=((1.0, 0.55, 0.15), 30)),
                 (loc[0], loc[1], loc[2] + h + 0.45), scale=(0.35, 0.35, 0.8))
    fl.visible_shadow = False
    point(name + "_light", (loc[0], loc[1], loc[2] + h + 0.6), energy, (1.0, 0.55, 0.22), 0.3)


def stone_mat(night=False):
    return toon("WallStone", (0.93, 0.85, 0.68) if not night else (0.93, 0.85, 0.68), 0.08, 0.85, scale=0.08)


def block_wall(name, x0, x1, y, h, thick, mat, crenel=True, bevel=0.15):
    L = x1 - x0
    mesh_ob(name, cube(), mat, ((x0 + x1) / 2, y, h / 2), scale=(L, thick, h), bevel=bevel)
    # horizontal stone courses for a hand-made look
    for k in range(1, int(h / 1.6)):
        mesh_ob(f"{name}_course{k}", cube(), toon("Course", (0.78, 0.7, 0.55), 0.05), ((x0 + x1) / 2, y - thick / 2 - 0.02,
                                                                                         k * 1.6), scale=(L, 0.06, 0.08))
    if crenel:
        n = int(L / 2.4)
        for i in range(n):
            mesh_ob(f"{name}_cr{i}", cube(), mat, (x0 + 1.2 + i * 2.4, y - thick / 2 + 0.5, h + 0.7),
                    scale=(1.3, 1.0, 1.4), bevel=0.08)


def big_tower(name, x, y, w, h, mat, banner=(0.75, 0.1, 0.1)):
    mesh_ob(name, cube(), mat, (x, y, h / 2), scale=(w, w, h), bevel=0.2)
    for k in range(1, int(h / 1.6)):
        mesh_ob(f"{name}_course{k}", cube(), toon("Course", (0.78, 0.7, 0.55), 0.05), (x, y - w / 2 - 0.02, k * 1.6),
                scale=(w, 0.06, 0.08))
    for i in range(4):
        a = i * math.pi / 2
        for k in range(3):
            off = (k - 1) * w / 3
            cxp = x + math.cos(a) * (w / 2 - 0.5) - math.sin(a) * off
            cyp = y + math.sin(a) * (w / 2 - 0.5) + math.cos(a) * off
            mesh_ob(f"{name}_cr{i}{k}", cube(), mat, (cxp, cyp, h + 0.8), scale=(1.4, 1.4, 1.6), bevel=0.08)
    if banner:
        mesh_ob(name + "_ban", cube(), toon("BannerR", banner, 0.05, 0.8), (x, y - w / 2 - 0.1, h - 4.5),
                scale=(2.6, 0.1, 6.5), bevel=0.02)
        mesh_ob(name + "_bansym", cyl(24), toon("GoldB", (0.95, 0.75, 0.25), 0.05, 0.3), (x, y - w / 2 - 0.18, h - 3.2),
                rot=(math.pi / 2, 0, 0), scale=(1.4, 1.4, 0.06))
        mesh_ob(name + "_banrod", cyl(8), toon("TorchWood", (0.42, 0.26, 0.14), 0.1), (x, y - w / 2 - 0.15, h - 1.2),
                rot=(0, math.pi / 2, 0), scale=(0.12, 0.12, 3.2))


def city_wall(night=False, breach=False, length=120, h=15, gate_w=6.5, gate_h=8.0):
    mat = stone_mat(night)
    block_wall("WallL", -length / 2, -gate_w / 2, 0, h, 6, mat)
    if breach:
        # torn-down section to the right of the gate: low ragged stumps + rubble, the city visible behind
        block_wall("WallR1", gate_w / 2, gate_w / 2 + 2, 0, h, 6, mat)
        r = random.Random(3)
        x = gate_w / 2 + 2
        while x < gate_w / 2 + 20:
            hh = r.uniform(1.0, 4.5)
            mesh_ob(f"Stump{x:.0f}", cube(), mat, (x + 1, 0, hh / 2), scale=(2.1, 6, hh), bevel=0.2)
            x += 2.0
        block_wall("WallR2", gate_w / 2 + 20, length / 2, 0, h, 6, mat)
        for k in range(70):
            lowpoly_rock(f"Rubble{k}", (r.uniform(gate_w / 2, gate_w / 2 + 22), r.uniform(-9, 5), 0.2),
                         r.uniform(0.4, 1.3), k, color=(0.88, 0.8, 0.63))
    else:
        block_wall("WallR", gate_w / 2, length / 2, 0, h, 6, mat)
    # lintel + arch
    top = mesh_ob("GateTop", cube(), mat, (0, 0, (gate_h - gate_w / 2 + h) / 2), scale=(gate_w + 0.1, 6, h - (gate_h - gate_w / 2)))
    arch = mesh_ob("GateArch", cyl(48), None, (0, 0, gate_h - gate_w / 2), rot=(math.pi / 2, 0, 0),
                   scale=(gate_w, gate_w, 8))
    b = top.modifiers.new("arch", "BOOLEAN")
    b.object = arch
    b.operation = "DIFFERENCE"
    arch.hide_render = True
    # arch voussoirs
    for k in range(11):
        a = math.pi - k * math.pi / 10
        mesh_ob(f"Vous{k}", cube(), toon("Course", (0.78, 0.7, 0.55), 0.05),
                (math.cos(a) * (gate_w / 2 + 0.45), -3.05, gate_h - gate_w / 2 + math.sin(a) * (gate_w / 2 + 0.45)),
                rot=(0, -a + math.pi / 2, 0), scale=(0.7, 0.2, 0.9), bevel=0.05)
    # dark passage behind the gate
    mesh_ob("GateDark", cube(), toon("Dark", (0.06, 0.04, 0.03), 0.02, 1.0), (0, 2.8, gate_h / 2),
            scale=(gate_w + 0.2, 0.3, gate_h + 0.2))
    # gate doors (hinged, closed by default)
    door = toon("Door", (0.48, 0.3, 0.16), 0.1, 0.8)
    iron = toon("Iron2", (0.25, 0.22, 0.2), 0.1)
    for side in (-1, 1):
        hinge = empty(f"DoorHinge{side}", (side * gate_w / 2, -2.6, 0))
        mesh_ob(f"Door{side}", cube(), door, (-side * gate_w / 4, 0, (gate_h - 0.4) / 2), scale=(gate_w / 2, 0.35, gate_h - 0.4),
                parent=hinge, bevel=0.04)
        for k in range(4):
            mesh_ob(f"DoorBand{side}{k}", cube(), iron, (-side * gate_w / 4, -0.2, 1.4 + k * 2.4),
                    scale=(gate_w / 2, 0.06, 0.25), parent=hinge)
    big_tower("TowerL", -gate_w / 2 - 5.5, -1.5, 9, h + 7, mat, (0.78, 0.1, 0.1) if not night else (0.35, 0.05, 0.08))
    big_tower("TowerR", gate_w / 2 + 5.5 + (24 if breach else 0), -1.5, 9, h + 7, mat,
              (0.78, 0.1, 0.1) if not night else (0.35, 0.05, 0.08))
    # city roofs peeking over the wall
    rr = random.Random(5)
    for k in range(14):
        x = rr.uniform(-55, 55)
        y = rr.uniform(12, 40)
        hh = rr.uniform(6, 14)
        mesh_ob(f"CityHouse{k}", cube(), toon("Plaster", (0.95, 0.86, 0.7), 0.06), (x, y, hh / 2), scale=(7, 7, hh))
        mesh_ob(f"CityRoof{k}", cyl(4), toon("Terracotta", (0.78, 0.33, 0.2), 0.08), (x, y, hh + 1.2),
                rot=(0, 0, math.pi / 4), scale=(10.5, 10.5, 2.4))


def set_walls(night=False, breach=False):
    if night:
        night_light()
        moon((-60, 260, 120))
        clouds(8, 31, night=True)
    else:
        day_light()
        clouds(16, 3, rng_y=(60, 400))
    city_wall(night, breach)
    gmat = toon("Dirt", (0.78, 0.62, 0.4), 0.1, 0.9, scale=0.1)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, -150, 0))
    bpy.context.active_object.data.materials.append(gmat)
    # road + grass verges
    mesh_ob("Road", cube(), toon("Road", (0.7, 0.55, 0.36), 0.12, 0.9, scale=0.2), (0, -40, 0.01), scale=(9, 80, 0.02))
    for side in (-1, 1):
        grass_field(f"Verge{side}", 40, (side * 26, -26, 0.02), 22, (0.38, 0.68, 0.18), 0.42, 5 + side)
    r = random.Random(9)
    for k in range(14):
        bush(f"WBush{k}", (r.choice((-1, 1)) * r.uniform(8, 40), r.uniform(-50, -6), 0), r.uniform(0.7, 1.6), k)
    for k in range(10):
        lowpoly_rock(f"WRock{k}", (r.choice((-1, 1)) * r.uniform(6, 40), r.uniform(-45, -4), 0.1), r.uniform(0.3, 1.0), k)
    if night:
        for k, x in enumerate((-6.5, 6.5)):
            torch(f"GateTorch{k}", (x, -4.2, 0), 3.2, 260)


# ---------------------------------------------------------------- plaza (inside the city)
def set_plaza(night=False):
    if night:
        night_light((math.radians(35), 0, math.radians(200)))
        moon((60, 220, 110), 12)
        clouds(6, 41, night=True)
    else:
        day_light((math.radians(58), 0, math.radians(-120)))
        clouds(12, 4)
    # paving
    tile = toon("Pave", (0.9, 0.8, 0.62), 0.12, 0.85, scale=0.6)
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(tile)
    for i in range(-20, 21):
        mesh_ob(f"PaveX{i}", cube(), toon("Grout", (0.72, 0.62, 0.46), 0.05), (i * 2.0, 0, 0.005), scale=(0.08, 120, 0.01))
        mesh_ob(f"PaveY{i}", cube(), toon("Grout", (0.72, 0.62, 0.46), 0.05), (0, i * 2.0 + 10, 0.005), scale=(120, 0.08, 0.01))
    # temple at the back (+Y)
    marble = toon("Marble", (0.97, 0.95, 0.9), 0.04, 0.5)
    mesh_ob("Stylobate", cube(), marble, (0, 42, 1.0), scale=(30, 16, 2.0), bevel=0.1)
    for k in range(8):
        x = -13 + k * 26 / 7
        mesh_ob(f"Col{k}", cyl(16), marble, (x, 35.5, 2 + 5.5), scale=(1.5, 1.5, 11), bevel=0.05)
        mesh_ob(f"ColCap{k}", cube(), marble, (x, 35.5, 13.2), scale=(2.0, 2.0, 0.5))
    mesh_ob("Entab", cube(), marble, (0, 42, 14.2), scale=(30, 16, 1.6), bevel=0.05)
    mesh_ob("Frieze", cube(), toon("FriezeBlue", (0.25, 0.45, 0.75), 0.05), (0, 33.95, 14.2), scale=(30, 0.1, 0.7))
    # pediment: a real triangular prism
    me = bpy.data.meshes.new("Pediment")
    hw, hh, y0, y1, z0 = 15.5, 4.0, 34.0, 50.0, 15.0
    v = [(-hw, y0, z0), (hw, y0, z0), (0, y0, z0 + hh), (-hw, y1, z0), (hw, y1, z0), (0, y1, z0 + hh)]
    me.from_pydata(v, [], [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
    me.update()
    ped = bpy.data.objects.new("Pediment", me)
    ped.data.materials.append(marble)
    bpy.context.scene.collection.objects.link(ped)
    mesh_ob("TempleDark", cube(), toon("Dark", (0.06, 0.04, 0.03), 0.02, 1.0), (0, 40, 7.5), scale=(22, 0.2, 11))
    # houses left/right
    r = random.Random(12)
    plaster = [(0.96, 0.87, 0.7), (0.93, 0.78, 0.6), (0.98, 0.92, 0.8), (0.9, 0.72, 0.55)]
    for side in (-1, 1):
        for k in range(5):
            x = side * r.uniform(19, 24)
            y = -18 + k * 11
            hh = r.uniform(6, 11)
            mesh_ob(f"House{side}{k}", cube(), toon(f"Plaster{k % 4}", plaster[k % 4], 0.05), (x, y, hh / 2),
                    scale=(9, 9.5, hh), bevel=0.15)
            mesh_ob(f"Roof{side}{k}", cyl(4), toon("Terracotta", (0.78, 0.33, 0.2), 0.08), (x, y, hh + 1.3),
                    rot=(0, 0, math.pi / 4), scale=(13.5, 13.5, 2.6))
            for j in range(2):
                win_emit = ((1.0, 0.65, 0.3), 8.0) if night else None
                mesh_ob(f"Win{side}{k}{j}", cube(), toon("WinN" if night else "Win",
                                                         (1.0, 0.75, 0.4) if night else (0.25, 0.18, 0.12), 0.05,
                                                         emission=win_emit),
                        (x - side * 4.52, y - 2.2 + j * 4.4, hh * 0.55), scale=(0.1, 1.4, 1.8))
    if not night:
        # festival: garlands + flags across the plaza
        for k in range(4):
            y = -6 + k * 9
            pts = [(-18 + i * 3, y, 8.5 - 2.2 * math.sin(i / 12 * math.pi)) for i in range(13)]
            for i, p in enumerate(pts):
                col = [(0.95, 0.3, 0.35), (1.0, 0.75, 0.15), (1, 1, 1), (0.35, 0.65, 0.95)][(i + k) % 4]
                mesh_ob(f"Flag{k}_{i}", cone(), toon(f"Flag{(i + k) % 4}", col, 0.05, 0.8), (p[0], p[1], p[2] - 0.5),
                        rot=(math.pi, 0, 0), scale=(0.9, 0.12, 1.1))
            mesh_ob(f"Rope{k}", cube(), toon("RopeC", (0.6, 0.45, 0.25), 0.05), (0, y, 7.6), scale=(36, 0.05, 0.05))
    for k, (x, y) in enumerate(((-12, -6), (12, -6), (-12, 14), (12, 14))):
        torch(f"PTorch{k}", (x, y, 0), 2.6, 220 if night else 0)


# ---------------------------------------------------------------- inside the horse
def set_belly(night=False):
    """Inside the horse: a cramped plank room. Camera stands near y=-6 looking +Y at the back wall."""
    w = bpy.data.worlds.new("Inside")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.015, 0.01, 1)
    tint = (1.5, 1.1, 0.75) if not night else (1.1, 0.8, 0.55)
    wood = pbr("BellyWood", "brown_planks_05", 0.9, tint, rough=0.8, bump=0.8)
    dark = pbr("BellyWoodDk", "brown_planks_05", 0.9, tuple(t * 0.55 for t in tint), rough=0.8, bump=0.8)
    W_, D_, H_ = 9.0, 8.0, 4.6
    mesh_ob("BackWall", cube(), wood, (0, 2.0, H_ / 2), scale=(W_, 0.3, H_))
    for side in (-1, 1):
        mesh_ob(f"SideWall{side}", cube(), wood, (side * W_ / 2, -2.0, H_ / 2), scale=(0.3, D_, H_))
        # sloped roof planes meeting at the ridge
        mesh_ob(f"Roof{side}", cube(), dark, (side * W_ / 4, -2.0, H_ + 0.9), rot=(0, side * math.radians(-22), 0),
                scale=(W_ / 2 + 0.6, D_, 0.25))
    mesh_ob("Floor", cube(), dark, (0, -2.0, 0.0), scale=(W_, D_, 0.2))
    for k in range(5):
        x = -3.6 + k * 1.8
        mesh_ob(f"Rib{k}", cube(), dark, (x, 1.75, H_ / 2), scale=(0.35, 0.35, H_), bevel=0.05)
    mesh_ob("Ridge", cube(), dark, (0, -2.0, H_ + 1.7), scale=(0.4, D_, 0.4))
    mesh_ob("CrossBeam", cube(), dark, (0, 1.6, H_ - 0.4), scale=(W_, 0.35, 0.35))
    # nails / pegs
    import random as _r
    rr = _r.Random(3)
    for k in range(40):
        mesh_ob(f"Peg{k}", cyl(8), toon("Iron2", (0.25, 0.22, 0.2), 0.1), (rr.uniform(-4.2, 4.2), 1.83, rr.uniform(0.4, 4.2)),
                rot=(math.pi / 2, 0, 0), scale=(0.06, 0.06, 0.06))
    if night:
        point("Lamp", (2.8, 0.6, 2.8), 60, (1.0, 0.55, 0.25), 0.15)
        mesh_ob("LampGlow", sphere(), toon("LampF", (1, 0.7, 0.3), 0.05, emission=((1, 0.55, 0.2), 25)), (2.8, 0.6, 2.8),
                scale=(0.2, 0.2, 0.3)).visible_shadow = False
        for k in range(4):
            mesh_ob(f"Crack{k}", cube(), toon("CrackN", (1, 0.6, 0.3), 0.05, emission=((1, 0.55, 0.25), 15)),
                    (-3 + k * 2.0, 1.84, 2.2 + (k % 2) * 1.1), scale=(0.8, 0.02, 0.05))
        point("Moonfill", (0, -5, 3.5), 25, (0.5, 0.6, 1.0), 1.5)
    else:
        point("Fill", (0, -4, 3.5), 220, (1.0, 0.85, 0.6), 1.5)
        for k in range(5):
            mesh_ob(f"Crack{k}", cube(), toon("Crack", (1, 0.95, 0.8), 0.05, emission=((1, 0.9, 0.7), 20)),
                    (-3.2 + k * 1.6, 1.84, 2.0 + (k % 3) * 0.8), scale=(0.9, 0.02, 0.05))
        spot = bpy.data.lights.new("Shaft", "SPOT")
        spot.energy = 1500
        spot.spot_size = math.radians(25)
        spot.spot_blend = 0.6
        spot.color = (1, 0.85, 0.6)
        ob = bpy.data.objects.new("Shaft", spot)
        ob.location = (-1.0, -1.0, H_ + 1.2)
        bpy.context.scene.collection.objects.link(ob)


# ---------------------------------------------------------------- open sea + island + fleet
def set_sea(night=False, ships=8):
    if night:
        night_light((math.radians(30), 0, math.radians(170)))
        moon((-40, 400, 90), 16)
        clouds(10, 51, rng_y=(150, 500), night=True)
        water = water_mat((0.01, 0.05, 0.12), (0.08, 0.16, 0.3))
    else:
        day_light((math.radians(50), 0, math.radians(-30)))
        clouds(18, 5, rng_y=(100, 500))
        water = water_mat((0.0, 0.32, 0.52), (0.1, 0.75, 0.78))
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(water)
    bpy.context.active_object.name = "Ocean"
    # Tenedos: green island
    mesh_ob("Island", sphere(48, 24), toon("IslandGrass", (0.3, 0.6, 0.2) if not night else (0.12, 0.22, 0.14), 0.12,
                                               0.9, scale=0.05), (60, 320, -14), scale=(110, 55, 36))
    mesh_ob("IslandBeach", sphere(48, 24), toon("IslandSand", (0.92, 0.8, 0.55), 0.05), (60, 318, -16),
            scale=(118, 60, 30))
    r = random.Random(3)
    for k in range(ships):
        build_ship(f"Ship{k}", (r.uniform(-30, 120), r.uniform(150, 280), 0), 1.0, r.uniform(-0.3, 0.3),
                   sail=(0.95, 0.9, 0.8), stripe=(0.15, 0.35, 0.7))
        bpy.data.objects[f"Ship{k}"].hide_render = True
        for c in bpy.data.objects[f"Ship{k}"].children_recursive:
            c.hide_render = True
    # serpents: bevelled curves (shape set per frame from the job)
    for k in range(2):
        cu = bpy.data.curves.new(f"Serpent{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 1.5
        cu.bevel_resolution = 4
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(7)
        ob = bpy.data.objects.new(f"Serpent{k}", cu)
        ob.data.materials.append(toon("SerpentG", (0.25, 0.62, 0.3), 0.15, 0.4, scale=1.5))
        bpy.context.scene.collection.objects.link(ob)
        ob.hide_render = True
        head = mesh_ob(f"SerpentHead{k}", sphere(), toon("SerpentG", (0.25, 0.62, 0.3), 0.15, 0.4, scale=1.5),
                       (0, 0, -50), scale=(4.0, 2.8, 2.2))
        for s_ in (-1, 1):
            mesh_ob(f"SerpentEye{k}{s_}", sphere(), toon("SnakeEye", (1, 0.85, 0.2), 0.02, 0.3), (0.5, s_ * 0.45, 0.35),
                    scale=(0.25, 0.2, 0.25), parent=head)
        head.hide_render = True


def set_serpents(states):
    """states: [{"pts": [[x,y,z]*8], "visible": bool}, ...]"""
    for k, st in enumerate(states or []):
        ob = bpy.data.objects.get(f"Serpent{k}")
        head = bpy.data.objects.get(f"SerpentHead{k}")
        if not ob:
            continue
        vis = st.get("visible", True)
        ob.hide_render = not vis
        head.hide_render = not vis
        for c in head.children:
            c.hide_render = not vis
        bp = ob.data.splines[0].bezier_points
        pts = st["pts"]
        for i, p in enumerate(pts[:len(bp)]):
            bp[i].co = p
            bp[i].handle_left_type = bp[i].handle_right_type = "AUTO"
        a, b = Vector(pts[-2]), Vector(pts[-1])
        head.location = b + (b - a).normalized() * 1.0
        head.rotation_euler = (b - a).to_track_quat("X", "Z").to_euler()


# ---------------------------------------------------------------- reeds (Sinon's hiding place)
def set_reeds():
    day_light((math.radians(48), 0, math.radians(-70)))
    clouds(14, 61)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(toon("Mud", (0.72, 0.62, 0.4), 0.1, 0.9, scale=0.15))
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 260, -0.05))
    bpy.context.active_object.data.materials.append(water_mat((0.0, 0.32, 0.52), (0.1, 0.75, 0.78)))
    for k, (x, y, s) in enumerate(((-6, 6, 5), (8, 10, 6), (2, -6, 4))):
        mesh_ob(f"Pool{k}", cyl(32), water_mat((0.05, 0.4, 0.5), (0.2, 0.7, 0.75)), (x, y, 0.02), scale=(s, s * 0.7, 0.02))
    # reed tuft object: tall thin stems with brown cattail heads
    r = random.Random(4)
    parts = []
    for k in range(7):
        h = r.uniform(2.2, 3.4)
        ang = (r.uniform(-0.15, 0.15), r.uniform(-0.15, 0.15), 0)
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.035, depth=h,
                                            location=(r.uniform(-0.2, 0.2), r.uniform(-0.2, 0.2), h / 2), rotation=ang)
        parts.append(bpy.context.active_object)
        if k % 2 == 0:
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.09, depth=0.45,
                                                location=(parts[-1].location.x + ang[1] * h * 0.5,
                                                          parts[-1].location.y - ang[0] * h * 0.5, h * 0.92))
            parts.append(bpy.context.active_object)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    tuft = bpy.context.active_object
    tuft.name = "ReedTuft"
    tuft.data.materials.append(toon("Reed", (0.5, 0.66, 0.24), 0.2, 0.7, scale=0.4))
    tuft.location = (0, 0, -100)
    tuft.hide_render = True
    # scatter reeds on a big plane, leaving a clearing in front of the camera
    for k, (x, y, sz, dens) in enumerate(((-14, 14, 26, 1.6), (14, 16, 26, 1.6), (0, 26, 50, 1.4), (-24, -4, 18, 1.4),
                                          (24, -4, 18, 1.4))):
        g = grass_field(f"ReedBed{k}", sz, (x, y, 0.01), dens, (0.5, 0.66, 0.24), 3.0, 10 + k,
                        ground_mat=toon("Mud", (0.72, 0.62, 0.4), 0.1, 0.9, scale=0.15))
        ng = g.modifiers["scatter"].node_group
        for n in ng.nodes:
            if n.bl_idname == "GeometryNodeObjectInfo":
                n.inputs["Object"].default_value = tuft
    grass_field("ReedGrass", 30, (0, 0, 0.015), 10, (0.42, 0.66, 0.2), 0.35, 2,
                ground_mat=toon("Mud", (0.72, 0.62, 0.4), 0.1, 0.9, scale=0.15))


SETS = {
    "walls": lambda: set_walls(False, False),
    "walls_breach": lambda: set_walls(False, True),
    "walls_night": lambda: set_walls(True, True),
    "plaza": lambda: set_plaza(False),
    "plaza_night": lambda: set_plaza(True),
    "belly": lambda: set_belly(False),
    "belly_night": lambda: set_belly(True),
    "sea": lambda: set_sea(False),
    "sea_night": lambda: set_sea(True),
    "reeds": set_reeds,
}

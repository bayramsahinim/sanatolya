"""2D characters inside the Blender-rendered 3D world.

Same pinhole camera as bl_build.look_at (sensor 36 mm, horizontal fit). Characters are billboards
standing at a 3D foot point; their pixel scale comes from the depth, and the Blender depth pass hides
them behind anything nearer to the camera (occlusion).
"""
import math
import os

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cairo  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402

from episodes.troy_en import gfx  # noqa: E402

W, H = 1080, 1920
HUMAN_M = 1.75         # a standing character is this tall in metres
HUMAN_PX = 330.0       # ... and this many px tall at pose scale s=1 (cast rig)


class Cam3:
    def __init__(self, loc, target, lens=35.0, roll=0.0, res_x=W, res_y=H):
        self.loc = np.array(loc, float)
        self.target = np.array(target, float)
        self.lens = lens
        self.roll = roll
        self.fpx = lens / 36.0 * res_x
        self.res = (res_x, res_y)
        f = self.target - self.loc
        f /= np.linalg.norm(f)
        up0 = np.array([0, 0, 1.0])
        r = np.cross(f, up0)
        if np.linalg.norm(r) < 1e-6:
            r = np.array([1.0, 0, 0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            r, u = r * c + u * s, -r * s + u * c
        self.f, self.r, self.u = f, r, u

    def project(self, p):
        d = np.array(p, float) - self.loc
        x, y, z = d @ self.r, d @ self.u, d @ self.f
        if z <= 0.05:
            return None
        return (self.res[0] / 2 + self.fpx * x / z, self.res[1] / 2 - self.fpx * y / z, z)

    def scale_at(self, z, height_m=HUMAN_M):
        """pose scale s for a character standing at depth z"""
        return self.fpx * height_m / z / HUMAN_PX

    def job(self):
        return {"cam": self.loc.tolist(), "target": self.target.tolist(), "lens": self.lens, "roll": self.roll}


def load_bg(png, exr):
    bg = cv2.imread(png, cv2.IMREAD_COLOR)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LANCZOS4)
    try:
        import OpenEXR
        z = list(OpenEXR.File(exr).channels().values())[0].pixels.astype(np.float32)
        if z.ndim == 3:
            z = z[:, :, 0]
        z = cv2.resize(z, (W, H), interpolation=cv2.INTER_NEAREST)
    except Exception:
        z = np.full((H, W), 1e9, np.float32)
    return bg, z


class Actor:
    """fig: cast Figure; pose_fn(s, x, y) -> Pose; pos: 3D foot point; h: height multiplier (1 = human)."""

    def __init__(self, fig, pos, pose_fn, h=1.0, shadow=True):
        self.fig, self.pos, self.pose_fn, self.h, self.shadow = fig, pos, pose_fn, h, shadow


SPR_W, SPR_H, SPR_FOOT, SPR_S = 600, 1000, 50, 2.2


def write_sprite(actor, path):
    """Character silhouette for Blender's shadow card. Returns the card description for the job."""
    surf = gfx.surface(SPR_W, SPR_H)
    cx = cairo.Context(surf)
    actor.fig.draw(cx, actor.pose_fn(SPR_S, SPR_W / 2, SPR_H - SPR_FOOT))
    surf.write_to_png(path)
    mpp = HUMAN_M * actor.h / (HUMAN_PX * SPR_S * actor.h)
    mpp = HUMAN_M / (HUMAN_PX * SPR_S) * actor.h
    return {"img": os.path.abspath(path), "pos": list(map(float, actor.pos)), "w": SPR_W * mpp, "h": SPR_H * mpp,
            "foot": SPR_FOOT / SPR_H}


def fog(bg, zbuf, color=(0.86, 0.9, 1.0), dist=180.0, amount=0.55):
    """Aerial perspective: far geometry fades toward the horizon colour (sky untouched)."""
    f = (1 - np.exp(-zbuf / dist)) * amount
    f[zbuf > 5e3] = 0
    col = np.array([color[2], color[1], color[0]], np.float32) * 255
    return (bg.astype(np.float32) * (1 - f[:, :, None]) + col * f[:, :, None]).astype(np.uint8)


def composite(bg, zbuf, cam, actors, tint=(1.0, 0.98, 0.94), halo=True, draw_extra=None, fog_args=None):
    """bg: BGR uint8 (H, W, 3); returns cairo surface with actors composited (far to near, occluded)."""
    if fog_args is not None:
        bg = fog(bg, zbuf, **fog_args)
    out = np.zeros((H, W, 4), np.uint8)
    out[:, :, :3] = bg
    out[:, :, 3] = 255
    base = gfx.from_np(out)
    bcx = cairo.Context(base)
    placed = []
    for a in actors:
        pr = cam.project(a.pos)
        if pr is None:
            continue
        x, y, z = pr
        s = cam.scale_at(z, HUMAN_M * a.h) / a.h * a.h
        placed.append((z, x, y, s, a))
    placed.sort(key=lambda t: -t[0])
    # soft contact occlusion right under the feet (the cast shadow comes from Blender)
    for z, x, y, s, a in placed:
        if a.shadow:
            gfx.contact_shadow(bcx, x, y, 60 * s, 0.3)
    layer = np.zeros((H, W, 4), np.float32)
    joints = {}
    for z, x, y, s, a in placed:
        surf = gfx.surface()
        cx = cairo.Context(surf)
        J = a.fig.draw(cx, a.pose_fn(s, x, y))
        joints[id(a)] = J
        arr = gfx.to_np(surf).astype(np.float32)
        al = arr[:, :, 3:4] / 255.0
        if al.max() == 0:
            continue
        vis = (zbuf > z - 0.35).astype(np.float32)[:, :, None]
        arr *= vis
        # light the character with the scene tint
        arr[:, :, 0] *= tint[2]
        arr[:, :, 1] *= tint[1]
        arr[:, :, 2] *= tint[0]
        layer = arr + layer * (1 - arr[:, :, 3:4] / 255.0)
    ch = gfx.from_np(np.clip(layer, 0, 255).astype(np.uint8))
    if halo:
        gfx.halo_composite(bcx, ch, radius=6)
    else:
        bcx.set_source_surface(ch, 0, 0)
        bcx.paint()
    if draw_extra:
        draw_extra(bcx, joints)
    return base

"""The Troy episode in 3D: same 26-shot timeline / transitions as episodes.troy_en (audio is reused),
but every shot has a real 3D camera path in a Blender set, 3D prop states and 2D characters placed in
the world (comp3d). Characters animate on 12 fps steps; the camera is smooth.
"""
import math
import random

import numpy as np

from cinecode.core import (back_out, clamp, ease_in, ease_io, ease_out, hexc, lerp, line, poly, prog, smooth, src,
                           fs, circle, ellipse, rrect)
from episodes.troy3d.comp3d import Actor, Cam3
from episodes.troy_en import cast as C
from episodes.troy_en import gfx
from episodes.troy_en import shots as S2
from episodes.troy_en import world as Wd

WS = S2.WS
P = C.pose
CHAR_FPS = 12
HORSE_SCALE = 1.0


def step(t):
    return math.floor(t * CHAR_FPS) / CHAR_FPS


def kf3(t, keys):
    """keys: [(t, (loc, target, lens))]; eased."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease_io(prog(t, t0, t1))
            return (tuple(lerp(x, y, u) for x, y in zip(a[0], b[0])), tuple(lerp(x, y, u) for x, y in zip(a[1], b[1])),
                    lerp(a[2], b[2], u))
    return keys[-1][1]


TINT = {"day": (1.0, 0.98, 0.94), "night": (0.62, 0.68, 0.92), "inside": (1.0, 0.86, 0.7),
        "inside_night": (0.85, 0.7, 0.62)}
FOG = {"day": dict(color=(0.75, 0.86, 1.0), dist=160, amount=0.5),
       "night": dict(color=(0.1, 0.14, 0.3), dist=120, amount=0.5), "inside": None, "inside_night": None}


class Shot3:
    set = "beach2"
    horse = True
    light = "day"
    keys = [(0, ((0, -12, 1.6), (0, 0, 3), 24))]

    def __init__(self, src_shot):
        self.src = src_shot
        self.t0, self.t1 = src_shot.t0, src_shot.t1
        self.trans_in, self.trans_out = src_shot.trans_in, src_shot.trans_out

    def w(self, line_id, k):
        return WS(line_id, k) - self.t0

    # ---- overridable
    def set_at(self, t):
        return self.set

    def objs(self, t):
        return {}

    def frame_extra(self, t):
        return {}

    def actors(self, t):
        return []

    def overlay(self, cx, t, cam, J):
        pass

    def tags(self, t):
        return self.src.tags(t)

    def shakes(self):
        try:
            return list(self.src.shakes)
        except Exception:
            return []

    # ---- camera (with transitions)
    def cam(self, t, res=(1080, 1920)):
        loc, tg, lens = kf3(t, self.keys)
        loc, tg = np.array(loc, float), np.array(tg, float)
        D = self.t1 - self.t0
        for tr, out in ((self.trans_out, True), (self.trans_in, False)):
            if not tr:
                continue
            kind, arg, d = tr
            k = ease_in(prog(t, D - d, D)) if out else 1 - ease_out(prog(t, 0, d))
            if k <= 0:
                continue
            fwd = tg - loc
            if kind == "whip":
                dx = arg[0] if arg else 1
                ang = math.radians(38) * k * (1 if out else -1) * dx
                c, s_ = math.cos(-ang), math.sin(-ang)
                fwd = np.array([fwd[0] * c - fwd[1] * s_, fwd[0] * s_ + fwd[1] * c, fwd[2]])
                tg = loc + fwd
            elif kind == "push":
                if out:
                    loc = loc + fwd * 0.75 * k
                    lens = lens * (1 + 0.8 * k)
                else:
                    loc = loc + fwd * 0.35 * k
            elif kind == "pull":
                loc = loc - fwd * (0.35 * k if out else -0.3 * k)
        # shakes
        for t0, amp, dur in self.shakes():
            if t0 <= t < t0 + dur:
                a = amp * 0.004 * (1 - (t - t0) / dur) ** 2
                tg = tg + np.array([math.sin(t * 90) * a * 6, 0, math.cos(t * 77) * a * 6])
        return Cam3(loc, tg, lens, res_x=res[0], res_y=res[1])

    def job_frame(self, t, idx):
        c = self.cam(t, (720, 1280))
        f = dict(c.job(), index=idx, time=t)
        f["obj"] = self.objs(t)
        f.update(self.frame_extra(t))
        return f


# ---------------------------------------------------------------- shared helpers
def horse_at(loc, rot_z, **kw):
    d = {"Horse": {"loc": list(loc), "rot": [0, 0, rot_z], "scale": HORSE_SCALE}}
    return d


def a(fig, pos, fn, h=1.0):
    return Actor(fig, pos, fn, h)


def look_up(t, f=1, **kw):
    return lambda s, x, y: P(x, y, t, s=s, f=f, **kw)


# Beach layout: horse at origin facing -X (head on screen-left when looking +Y), sea toward +Y.
BEACH_HORSE = horse_at((0, 0, 0), math.pi)


class B01(Shot3):  # horse reveal, Greeks trudge to the ships
    keys = [(0, ((1.2, -8.5, 0.35), (-0.5, 0, 1.0), 18)), (2.6, ((-1.0, -15.5, 1.5), (-0.6, 0, 5.4), 22))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)
        return [a(C.greek_soldier(i), (4.5 + i * 1.6, 5 + ts * 1.5 + i * 0.6, 0),
                  (lambda i: lambda s, x, y: C.walk(P(x, y, ts, s=s, f=1, mouth="flat", eyes="half", seed=i), ts + i * 0.3,
                                                    1.2))(i)) for i in range(3)]


class B02(Shot3):  # gift bow pops on, tag TO: TROY
    keys = [(0, ((-1.3, -6.0, 5.0), (-3.3, 0, 5.9), 30)), (1.5, ((-1.8, -5.0, 5.3), (-3.3, 0, 5.9), 32))]

    def objs(self, t):
        return BEACH_HORSE

    def frame_extra(self, t):
        return {"bow": max(0.01, back_out(prog(t, 0.08, 0.38)))}

    def overlay(self, cx, t, cam, J):
        if t > 0.3:
            p = cam.project((-3.3, -1.0, 5.0))
            if p:
                x, y, _ = p
                sw = math.sin(t * 2.4) * 0.06
                cx.save()
                cx.translate(x, y)
                cx.rotate(sw)
                line(cx, [(0, 0), (0, 120)], hexc("#7A4E2D"), 5)
                cx.translate(0, 120)
                rrect(cx, -120, 0, 240, 150, 14)
                fs(cx, hexc("#FFF4D6"), hexc("#1C1C24"), 6)
                circle(cx, 0, 24, 9)
                fs(cx, hexc("#7A4E2D"), hexc("#1C1C24"), 2)
                from cinecode.core import text
                text(cx, "TO:", 0, 84, 46, hexc("#1C1C24"))
                text(cx, "TROY", 0, 132, 44, hexc("#C0392B"))
                cx.restore()
        if t > 0.1:
            k = max(0, 1 - (t - 0.1) / 0.6)
            gfx.glow(cx, 540, 900, 420, (1, 0.95, 0.7), 0.5 * k)


class B03(Shot3):  # ships sail home
    set, horse = "sea", False
    keys = [(0, ((0, -6, 2.2), (8, 80, 5), 34)), (1.4, ((0, -6, 2.4), (12, 80, 5.5), 36))]

    def objs(self, t):
        o = {}
        for k in range(5):
            o[f"Ship{k}"] = {"hide": False, "loc": [-6 + k * 16, 34 + k * 22 + t * 6, 0], "rot": [0, 0, math.pi / 2],
                             "scale": 1.0}
        return o

    def actors(self, t):
        ts = step(t)
        wave = math.sin(ts * 12) * 25
        return [a(C.greek_soldier(0), (-6.5, 28 + t * 6, 1.9),
                  lambda s, x, y: P(x, y, ts, s=s, f=-1, mouth="grin", eyes="happy", arm_b=160 + wave, elb_b=20))]


class W04(Shot3):  # Trojans rush out of the gate
    set, horse = "walls", False
    keys = [(0, ((0, -15, 1.3), (0, -3, 3.2), 24)), (1.7, ((0, -16, 1.35), (0, -3, 3.0), 24))]

    def frame_extra(self, t):
        return {"doors": 1.0}

    def actors(self, t):
        ts = step(t)
        r = random.Random(4)
        out = []
        for i in range(8):
            u = max(0, ts - i * 0.12)
            x = r.uniform(-2.5, 2.5) + (i % 2 * 2 - 1) * u * 0.8
            y = -1 - u * 7.5
            fig = C.trojan_soldier(i) if i % 3 == 0 else C.trojan_citizen(i)
            out.append(a(fig, (x, y, 0), (lambda i, f: lambda s, x_, y_: C.run(
                P(x_, y_, ts, s=s, f=f, seed=i, mouth="grin", eyes="wide"), ts + i * 0.13, 2.4))(i, 1 if i % 2 else -1)))
        return out


class B05(Shot3):  # No army. No ships. Just a horse.
    keys = [(0, ((0, -12.8, 1.0), (0, -2, 2.6), 26)), (2.0, ((0, -11.8, 1.1), (0, -2, 3.0), 26))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)
        no1, no2, up = self.w("beach", 6), self.w("beach", 8), self.w("beach", 10)
        out = []
        for i, x in enumerate((-2.7, -0.9, 0.9, 2.7)):
            skid = 1 - ease_out(prog(ts, 0, 0.35))
            if ts < no2:
                look, f = ((-1, 0) if ts > no1 else (0, 0)), -1
            elif ts < up:
                look, f = (1, 0), 1
            else:
                look, f = (0, -1), (1 if i < 2 else -1)
            fig = C.trojan_soldier(i) if i % 2 == 0 else C.trojan_citizen(i + 3)
            out.append(a(fig, (x - skid * 1.5, -8.2 - (i % 2) * 0.6, 0), (lambda f, look, i: lambda s, x_, y_: C.breathe(P(
                x_, y_, ts, s=s, f=f, seed=i, look=look, mouth="o" if ts > up else "flat", eyes="wide" if ts > up else "open",
                lean=-12 * skid, tilt=-10 if ts > up else 0), ts))(f, look, i)))
        return out


class B06(Shot3):  # Laocoön marches in and hurls the spear
    keys = [(0, ((-7.2, -10.2, 1.3), (-5.6, -6.0, 1.6), 28)), (1.9, ((-6.6, -9.8, 1.3), (-5.0, -6.0, 1.8), 30))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)
        throw = self.w("spear", 4)
        x = lerp(-8.5, -5.6, smooth(prog(ts, 0, 0.9)))

        def fn(s, x_, y_):
            p = P(x_, y_, ts, s=s, f=1, seed=11, brows="angry", mouth="yell" if ts > throw else "frown", eyes="angry")
            if ts < 0.9:
                p = C.walk(p, ts, 1.4)
            wind = smooth(prog(ts, throw - 0.5, throw - 0.1))
            rel = ease_out(prog(ts, throw - 0.1, throw + 0.12))
            return p.but(arm_b=lerp(lerp(10, -150, wind), 100, rel), elb_b=lerp(30, 10, rel), lean=lerp(-8, 14, rel) * wind)
        return [a(C.LAOCOON, (x, -6.0, 0), fn)]

    def objs_spear(self, t):
        pass

    def overlay(self, cx, t, cam, J):
        throw = self.w("spear", 4)
        if t < throw:
            for k, Jd in J.items():
                hx, hy = Jd["hand_b"]
                line(cx, [(hx - 80, hy + 55), (hx + 150, hy - 100)], hexc("#1C1C24"), 16)
                line(cx, [(hx - 80, hy + 55), (hx + 150, hy - 100)], hexc("#8A5A33"), 9)
        else:
            u = t - throw
            x, y = 560 + u * 2200, 980 - u * 900 + u * u * 400
            cx.save()
            cx.translate(x, y)
            cx.rotate(-0.38 + u * 0.4)
            line(cx, [(-200, 0), (50, 0)], hexc("#1C1C24"), 16)
            line(cx, [(-200, 0), (50, 0)], hexc("#8A5A33"), 9)
            poly(cx, [(50, -16), (50, 16), (104, 0)])
            fs(cx, hexc("#D9A441"), hexc("#1C1C24"), 4)
            cx.restore()


class B07(Shot3):  # spear hits the flank (3D spear)
    keys = [(0, ((2.2, -6.5, 4.2), (-0.4, -1.0, 4.6), 34)), (1.2, ((1.9, -6.0, 4.3), (-0.4, -1.0, 4.6), 36))]

    def objs(self, t):
        o = dict(BEACH_HORSE)
        hit = 0.3
        u = prog(t, 0, hit)
        tip = np.array([-0.2, -1.15, 4.6])
        d = np.array([0.75, 0.45, 0.35])
        d /= np.linalg.norm(d)
        pos = tip - d * (1 - u) * 9
        wob = math.sin((t - hit) * 40) * 0.12 * math.exp(-(t - hit) * 5) if t > hit else 0
        yaw = math.atan2(d[1], d[0])
        pitch = -math.asin(d[2])
        o["Spear3D"] = {"loc": pos.tolist(), "rot": [0, pitch + wob, yaw]}
        return o

    def overlay(self, cx, t, cam, J):
        hit = 0.3
        if t > hit:
            p = cam.project((-0.2, -1.15, 4.6))
            if p:
                for k in range(8):
                    ang = k * math.pi / 4
                    rr = 30 + (t - hit) * 320
                    al = max(0, 1 - (t - hit) * 3)
                    line(cx, [(p[0] + math.cos(ang) * rr, p[1] + math.sin(ang) * rr),
                              (p[0] + math.cos(ang) * (rr + 36), p[1] + math.sin(ang) * (rr + 36))], (1, 0.95, 0.7, al), 7)


class I08(Shot3):  # inside: the spear tip pokes through between Odysseus and Anticlus
    set, horse, light = "belly", False, "inside"
    keys = [(0, ((0, -3.9, 1.45), (0, 1.8, 1.55), 28)), (2.0, ((0, -3.4, 1.5), (0, 1.8, 1.6), 30))]

    def objs(self, t):
        u = ease_out(prog(t, 0.05, 0.18))
        return {"Spear3D": {"loc": [-0.15, 1.95 - 0.9 * u, 2.45], "rot": [0, 0, -math.pi / 2]}}

    def actors(self, t):
        ts = step(t)
        hol = self.w("spear", 13)
        sc = ts > hol - 0.1
        figs = [C.greek_soldier(1), C.ODYSSEUS, C.ANTICLUS, C.greek_soldier(2)]
        out = []
        for i, (fig, x) in enumerate(zip(figs, (-2.9, -1.2, 0.9, 2.6))):
            f = 1 if x < 0 else -1
            out.append(a(fig, (x, 0.6, 0.1), (lambda f, i: lambda s, x_, y_: P(
                x_, y_, ts, s=s, f=f, seed=30 + i, eyes="wide" if sc else "open",
                mouth=("wavy" if i % 2 else "o") if sc else "flat", look=(0.8 * f, -0.5) if sc else (0, 0),
                sweat=prog(ts, hol, hol + 0.4) if sc else 0, brows="worried" if sc else "neutral"))(f, i)))
        return out


class B09(Shot3):  # BEWARE of Greeks bearing gifts
    keys = [(0, ((-5.6, -10.6, 1.0), (-5.2, -6.0, 2.0), 32)), (1.7, ((-5.5, -9.6, 1.05), (-5.2, -6.0, 2.1), 34))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)

        def shrug(i):
            def fn(s, x, y):
                k = smooth(prog(ts, 0.6 + i * 0.1, 0.9 + i * 0.1)) * (1 - smooth(prog(ts, 1.4, 1.7)))
                return P(x, y, ts, s=s, f=-1, seed=i, mouth="flat", eyes="half", arm_a=lerp(10, 80, k),
                         arm_b=lerp(-10, 80, k), elb_a=lerp(10, -90, k), elb_b=lerp(10, -90, k))
            return fn
        return [a(C.trojan_citizen(1), (-2.8, -2.0, 0), shrug(0)), a(C.trojan_citizen(2), (-1.4, -1.0, 0), shrug(1)),
                a(C.LAOCOON, (-5.2, -6.0, 0), lambda s, x, y: C.talk(P(x, y, ts, s=s, view="front", seed=11, brows="angry",
                                                                        eyes="angry", mouth="yell"), ts, 11).but(
                    arm_b=170 + math.sin(ts * 10) * 6, elb_b=-10, arm_a=-20, elb_a=40))]


class R10(Shot3):  # Sinon dragged out of the reeds
    set, horse = "reeds", False
    keys = [(0, ((0, -7.5, 1.5), (0, 3.0, 1.3), 26)), (3.9, ((0, -6.3, 1.5), (0, 3.0, 1.4), 28))]

    def actors(self, t):
        ts = step(t)
        name = self.w("sinon", 10)
        y = lerp(7.5, 1.5, smooth(prog(ts, 0, 1.8)))
        moving = ts < 1.8
        look = ts > name
        out = []
        for i, dx in enumerate((-1.1, 1.1)):
            def fn(s, x, y_, i=i):
                p = P(x, y_, ts, s=s, f=-1 if dx > 0 else 1, seed=50 + i, brows="angry", mouth="frown", arm_b=60, elb_b=10)
                return C.walk(p, ts + i * 0.2, 1.3, arms=False) if moving else p
            out.append(a(C.trojan_soldier(i + 1), (dx, y + 0.3, 0), fn))
        out.append(a(C.SINON, (0, y, 0), lambda s, x, y_: P(x, y_, ts, s=s, f=1, view="front" if look else "side", seed=52,
                                                            eyes="closed" if not look else "open",
                                                            mouth="wavy" if not look else "grin", brows="worried",
                                                            arm_a=30, arm_b=30, elb_a=70, elb_b=70)))
        return out


class R11(Shot3):  # Sinon sobbing (fake)
    set, horse = "reeds", False
    keys = [(0, ((0, -2.6, 1.4), (0, 2.0, 1.35), 34)), (4.4, ((0, -1.9, 1.45), (0, 2.0, 1.4), 36))]

    def actors(self, t):
        ts = step(t)
        sob = math.sin(ts * 9) * 0.5 + 0.5
        return [a(C.trojan_soldier(2), (1.6, 2.6, 0), lambda s, x, y: P(x, y, ts, s=s, f=-1, seed=61, eyes="closed",
                                                                         mouth="wavy", brows="worried", arm_b=150, elb_b=60)),
                a(C.trojan_citizen(4), (-1.7, 2.4, 0), lambda s, x, y: P(x, y, ts, s=s, f=1, seed=62, eyes="half",
                                                                          mouth="frown", brows="worried")),
                a(C.SINON, (0, 0.5, 0), lambda s, x, y: P(x, y, ts, s=s, view="front", seed=52, eyes="squeeze",
                                                          mouth="scream", mouth_open=0.6 + 0.4 * sob, brows="worried",
                                                          arm_a=-30, arm_b=-30, elb_a=-80, elb_b=-80, bob=sob * 6))]

    def overlay(self, cx, t, cam, J):
        for Jd in J.values():
            if Jd.get("_fig") is not C.SINON:
                continue
            hx, hy = Jd["head"]
            R = Jd["head_rad"]
            for side in (-1, 1):
                ex, ey = hx + side * R * 0.35, hy - R * 0.05
                for k in range(9):
                    u = ((t * 1.6 + k / 9) % 1)
                    x = ex + side * u * 300
                    y = ey - 70 * math.sin(u * math.pi) + u * 260
                    ellipse(cx, x, y, 13, 18)
                    fs(cx, hexc("#7FD1F5"), hexc("#1C1C24"), 3)


GATE_TOP = 8.0
HORSE_TOP = 9.25


class W12(Shot3):  # horse vs gate measurement
    set = "walls"
    keys = [(0, ((-16, -24, 2.5), (0, -6, 5.5), 24)), (2.7, ((-15, -22.5, 2.6), (0, -6, 5.5), 24))]

    def objs(self, t):
        return horse_at((0, -12, 0), math.pi / 2)

    def overlay(self, cx, t, cam, J):
        from episodes.troy_en.shots import label
        g = ease_out(prog(t, 0.15, 0.6))
        hh = ease_out(prog(t, 1.0, 1.6))
        for (x, y, top, k, lab, col) in ((-4.0, -3.4, GATE_TOP, g, "GATE", "#FFFFFF"),
                                         (2.2, -12, HORSE_TOP, hh, "HORSE", "#FFD60A")):
            if k <= 0:
                continue
            p0 = cam.project((x, y, 0))
            p1 = cam.project((x, y, top * k))
            if not p0 or not p1:
                continue
            line(cx, [p0[:2], p1[:2]], hexc("#14141A"), 18)
            line(cx, [p0[:2], p1[:2]], hexc(col), 9)
            for pp in (p0, p1):
                line(cx, [(pp[0] - 34, pp[1]), (pp[0] + 34, pp[1])], hexc("#14141A"), 16)
                line(cx, [(pp[0] - 34, pp[1]), (pp[0] + 34, pp[1])], hexc(col), 8)
            label(cx, lab, p1[0], p1[1] - 56, 50, hexc(col), alpha=k)
        if t > 2.0:
            sc = back_out(prog(t, 2.0, 2.3))
            cx.save()
            cx.translate(540, 360)
            cx.scale(sc, sc)
            label(cx, "HORSE  >  GATE", 0, 0, 78, hexc("#FFD60A"))
            cx.restore()


class S13(Shot3):  # sea serpents rise
    set, horse = "sea", False
    keys = [(0, ((0, -4, 2.2), (2, 24, 6), 28)), (3.0, ((0, -2.8, 1.8), (2, 24, 7.5), 30))]

    def objs(self, t):
        return {"Ship0": {"hide": False, "loc": [60, 230, 0], "rot": [0, 0, 1.2]}}

    def frame_extra(self, t):
        sts = []
        for k, (bx, ph) in enumerate(((-6, 0.0), (9, 0.45))):
            rise = ease_out(prog(t, 0.2 + ph, 1.7 + ph))
            pts = []
            for i in range(8):
                u = i / 7
                z = -4 + u * 14 * rise
                x = bx + math.sin(u * 5 + t * 3 + k) * 1.6 * (0.4 + u)
                y = 22 + k * 5 + math.cos(u * 4 + t * 2) * 1.2
                pts.append([x, y, z])
            sts.append({"pts": pts, "visible": rise > 0.01})
        return {"serpents": sts}


class B14(Shot3):  # coils wrap Laocoön, he gets yanked away
    keys = [(0, ((-5.4, -11.0, 1.3), (-5.2, -6.0, 1.9), 30)), (1.8, ((-5.4, -10.6, 1.3), (-5.2, -6.0, 1.9), 31))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)
        yank = ease_in(prog(ts, 1.1, 1.5))
        wrap = smooth(prog(ts, 0.15, 0.7))
        return [a(C.LAOCOON, (-5.2 - yank * 9, -6.0, 0), lambda s, x, y: P(
            x, y, ts, s=s, view="front", seed=11, eyes="spiral" if wrap > 0.6 else "wide",
            mouth="scream" if wrap > 0.3 else "yell", brows="worried", arm_a=lerp(-20, 150, wrap),
            arm_b=lerp(170, 150, wrap), elb_a=20, elb_b=20, squash=1 - 0.08 * wrap, lean=-20 * yank))]

    def overlay(self, cx, t, cam, J):
        wrap = smooth(prog(t, 0.15, 0.7))
        for Jd in J.values():
            hx, hy = Jd["hip"]
            R = Jd["head_rad"]
            sc = R / 52
            if wrap > 0:
                for k in range(3):
                    wk = clamp(wrap * 3 - k)
                    if wk <= 0:
                        continue
                    y = hy - 150 * sc + k * 75 * sc
                    ellipse(cx, hx, y, 105 * sc * wk, 30 * sc)
                    fs(cx, hexc("#3F8F4E"), hexc("#1C1C24"), 6)
                pts = [(hx - 900, hy + 120), (hx - 600, hy - 30), (hx - 330, hy + 40), (hx - 70, hy - 190 * sc)]
                Wd.serpent(cx, pts, t, 66 * sc)


class B15(Shot3):  # Message received: the horse is sacred
    keys = [(0, ((0, -13.0, 0.9), (0, 0, 4.2), 24)), (2.1, ((0, -15.5, 1.0), (0, 0, 4.6), 24))]

    def objs(self, t):
        return BEACH_HORSE

    def actors(self, t):
        ts = step(t)
        sac = self.w("snakes", 19) - 0.25
        look = int(ts * 2.2) % 2
        bow = smooth(prog(ts, sac, sac + 0.5))
        out = []
        for i, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
            fig = C.trojan_soldier(i) if i % 2 == 0 else C.trojan_citizen(i + 3)
            f0 = 1 if (i + look) % 2 == 0 else -1
            out.append(a(fig, (x, -7.5 - (i % 2) * 0.5, 0), (lambda f0, x: lambda s, x_, y_: P(
                x_, y_, ts, s=s, f=f0 if bow < 0.1 else (1 if x < 0 else -1), seed=i,
                eyes="half" if bow < 0.5 else "closed", mouth="flat", brows="flat", lean=40 * bow,
                arm_a=lerp(10, 70, bow), arm_b=lerp(-10, 70, bow), head_dy=10 * bow))(f0, x)))
        return out

    def overlay(self, cx, t, cam, J):
        k = smooth(prog(t, 1.3, 2.0))
        if k:
            p = cam.project((0, 0, 9))
            if p:
                gfx.rays(cx, p[0], p[1] - 300, math.pi / 2, 0.6, 1900, (1, 0.92, 0.6), 0.22 * k, 9, t=t)
                gfx.glow(cx, p[0], p[1] + 200, 600, (1, 0.9, 0.6), 0.35 * k)


class W16(Shot3):  # pulling the horse to the gate: BONK
    set = "walls"
    keys = [(0, ((-12, -21, 2.4), (0, -12, 4.0), 24)), (2.4, ((-11, -15.5, 2.6), (0, -6, 5.0), 24))]

    def hit(self):
        return self.w("walls", 12) - 0.12

    def hy(self, t):
        h = self.hit()
        y = lerp(-26, -8.9, ease_io(prog(t, 0, h)))
        if t > h:
            y -= math.sin((t - h) * 30) * 0.15 * math.exp(-(t - h) * 6) + 0.25 * smooth(prog(t, h, h + 0.15))
        return y

    def shakes(self):
        return [(self.hit(), 26, 0.45)]

    def objs(self, t):
        return horse_at((0, self.hy(t), 0), math.pi / 2)

    def actors(self, t):
        ts = step(t)
        h = self.hit()
        y = self.hy(t)
        out = []
        for i in range(3):
            def fn(s, x, y_, i=i):
                p = P(x, y_, ts, s=s, f=1, seed=70 + i, mouth="grin" if ts < h else "o",
                      eyes="squeeze" if ts < h else "wide", lean=18 if ts < h else -8, arm_a=-60, arm_b=-50,
                      elb_a=-20, elb_b=-10)
                return C.walk(p, ts, 1.1, arms=False) if ts < h else p
            out.append(a(C.trojan_citizen(i + 6), (-1.6 + i * 1.6, y + 7.5 + (i % 2) * 0.6, 0), fn))
        return out

    def overlay(self, cx, t, cam, J):
        y = self.hy(t)
        anchor = cam.project((0, y + 3.0, 5.3))
        for Jd in J.values():
            if anchor:
                Wd.rope(cx, Jd["hand_b"], anchor[:2], 40, 7)
        h = self.hit()
        if t > h:
            p = cam.project((0, y + 5.4, 9.3))
            if p:
                for k in range(3):
                    an = (t - h) * 6 + k * 2.1
                    circle(cx, p[0] + math.cos(an) * 80, p[1] - 40 + math.sin(an) * 24, 18)
                    fs(cx, hexc("#FFE066"), hexc("#1C1C24"), 3)


class W17(Shot3):  # tearing down their own walls
    keys = [(0, ((9, -13.5, 1.7), (9, -4, 3.0), 24)), (2.2, ((9, -15, 2.0), (9, -4, 3.4), 24))]
    horse = False

    def hit(self):
        return self.w("walls", 18) - 0.9

    def set_at(self, t):
        return "walls_breach" if t > self.hit() + 0.25 else "walls"

    def shakes(self):
        return [(self.hit(), 40, 0.9)]

    def actors(self, t):
        ts = step(t)
        swing = (ts * 2.6) % 1
        out = []
        for i, (x, f) in enumerate(((6.0, 1), (8.2, -1), (10.6, -1), (12.6, -1))):
            hitting = ts < self.hit() + 0.3
            ph = (swing + i * 0.25) % 1
            ang = lerp(170, 60, ease_in(ph)) if hitting else 20
            fig = C.trojan_soldier(i) if i % 2 else C.trojan_citizen(i + 8)
            out.append(a(fig, (x, -4.5 - (i % 2) * 0.8, 0), (lambda f, ang, i, hitting: lambda s, x_, y_: P(
                x_, y_, ts, s=s, f=f, seed=80 + i, mouth="grin", eyes="happy" if hitting else "wide",
                arm_b=ang, arm_a=ang - 10, elb_b=10, elb_a=10))(f, ang, i, hitting)))
        return out

    def overlay(self, cx, t, cam, J):
        if t < self.hit() + 0.3:
            for Jd in J.values():
                hx, hy = Jd["hand_b"]
                Wd.pickaxe(cx, hx, hy, -0.4, Jd["head_rad"] / 52 * 1.1)
        if t > self.hit():
            p = cam.project((10, -3.5, 3))
            if p:
                u = t - self.hit()
                r = random.Random(9)
                for k in range(22):
                    x = p[0] + r.uniform(-320, 320) + r.uniform(-300, 300) * u
                    y = p[1] + r.uniform(-500, 0) + r.uniform(-200, 50) * u + 2200 * u * u
                    if y < 1800:
                        Wd.stone(cx, x, y, r.uniform(40, 100), u * r.uniform(-4, 4), hexc("#E8D7B0"))
                Wd.dust(cx, p[0], p[1] + 150, t, self.hit(), 18, 220, 3)


PLAZA_HORSE = horse_at((1.5, 9.0, 0), math.radians(200))


class P18(Shot3):  # Cassandra screams
    set = "plaza"
    keys = [(0, ((-2.2, -7.9, 1.45), (-1.6, 2, 2.4), 28)), (2.8, ((-2.4, -7.3, 1.45), (-1.8, 2, 2.5), 30))]

    def objs(self, t):
        return PLAZA_HORSE

    def frame_extra(self, t):
        return {"bow": 1.0}

    def actors(self, t):
        ts = step(t)
        out = [a(C.trojan_citizen(i + 12), (1.5 + ts * 0.8 + i * 3, 2 + i * 1.5, 0),
                 (lambda i: lambda s, x, y: C.walk(P(x, y, ts, s=s, f=1, seed=90 + i, mouth="grin", eyes="happy"), ts, 1.3))(i))
               for i in range(2)]
        out.append(a(C.CASSANDRA, (-2.6, -4.4, 0), lambda s, x, y: C.talk(P(
            x, y, ts, s=s, f=1, seed=3, eyes="wide", mouth="scream", brows="worried", arm_b=110 + math.sin(ts * 14) * 8,
            elb_b=0, arm_a=150 + math.sin(ts * 12) * 10, elb_a=30), ts, 12)))
        return out


class P19(Shot3):  # nobody believes her; cursed
    set = "plaza"
    keys = [(0, ((-3.0, -8.6, 1.5), (-2.0, 2, 2.4), 26)), (3.6, ((-3.2, -9.1, 1.5), (-2.0, 2, 2.4), 26))]

    def objs(self, t):
        return PLAZA_HORSE

    def frame_extra(self, t):
        return {"bow": 1.0}

    def actors(self, t):
        ts = step(t)
        cur = self.w("cass", 12) - 0.25
        out = []
        for i in range(6):
            x = -9 + ((ts * 2.6 + i * 3.2) % 19)
            out.append(a(C.trojan_citizen(i + 20), (x, -2.5 + (i % 3) * 1.2, 0), (lambda i: lambda s, x_, y_: C.walk(P(
                x_, y_, ts, s=s, f=1, seed=100 + i, mouth="grin", eyes="happy", arm_b=120, elb_b=20), ts + i * 0.3, 1.4))(i)))
        out.append(a(C.CASSANDRA, (-3.4, -5.2, 0), lambda s, x, y: (lambda p: C.talk(p, ts, 12) if ts < cur else p)(P(
            x, y, ts, s=s, f=1, seed=3, eyes="half" if ts > cur else "wide", mouth="flat" if ts > cur else "yell",
            brows="flat" if ts > cur else "worried", arm_b=110 if ts < cur else -10, elb_b=0, arm_a=-10))))
        return out

    def overlay(self, cx, t, cam, J):
        for k in range(16):
            u = ((t * 0.5 + k * 0.071) % 1)
            Wd.petal(cx, 420 + k * 45 + math.sin(t * 2 + k) * 40, 700 + u * 1000, t * 3 + k,
                     hexc(["#E94F64", "#F7B32B", "#FFFFFF"][k % 3]), 1.3)
        cur = self.w("cass", 12) - 0.25
        if t > cur:
            for Jd in J.values():
                if Jd.get("_fig") is C.CASSANDRA:
                    hx, hy = Jd["head_top"]
                    Wd.storm_cloud(cx, hx, hy - 130, t, 1.2 * back_out(prog(t, cur, cur + 0.3)))


class P20(Shot3):  # Helen at night, imitating the wives
    set, light = "plaza_night", "night"
    keys = [(0, ((-3.2, -6.8, 1.5), (-1.0, 2, 2.6), 26)), (4.0, ((-2.2, -6.6, 1.5), (0.0, 2, 2.8), 26))]

    def objs(self, t):
        return PLAZA_HORSE

    def frame_extra(self, t):
        return {"bow": 1.0}

    def actors(self, t):
        ts = step(t)
        x = lerp(-4.0, 0.5, smooth(prog(ts, 0, 3.8)))
        call = self.w("helen", 5) - 0.1
        return [a(C.HELEN, (x, -2.5, 0), lambda s, x_, y_: (lambda p: C.talk(p, ts, 8) if ts > call else p)(C.walk(P(
            x_, y_, ts, s=s, f=1, seed=4, eyes="half", mouth="o" if ts > call else "smirk", arm_a=40, elb_a=80,
            arm_b=150 if ts > call else 60, elb_b=50 if ts > call else 60), ts, 0.9, arms=False)))]

    def overlay(self, cx, t, cam, J):
        call = self.w("helen", 5) - 0.1
        for Jd in J.values():
            hx, hy = Jd["hand_a"]
            sc = Jd["head_rad"] / 52
            Wd.torch(cx, hx, hy + 60 * sc, t, 0.55 * sc, 7)
            gfx.glow(cx, hx, hy - 80 * sc, 380 * sc, (1.0, 0.62, 0.25), 0.55)
            if t > call:
                tx, ty = Jd["head_top"]
                S2.bubble(cx, tx + 170, ty - 150, "Honeyyy? It's me!", back_out(prog(t, call, call + 0.3)))


class I21(Shot3):  # Anticlus about to answer
    set, horse, light = "belly_night", False, "inside_night"
    keys = [(0, ((0.4, -3.6, 1.55), (0.4, 1.5, 1.75), 30)), (1.9, ((0.7, -3.1, 1.6), (0.7, 1.5, 1.8), 33))]

    def actors(self, t):
        ts = step(t)
        lean = smooth(prog(ts, 0.3, 1.2))
        return [a(C.ODYSSEUS, (-1.0, 0.6, 0.1), lambda s, x, y: P(x, y, ts, s=s, f=1, seed=5, eyes="half", mouth="flat",
                                                                  brows="flat")),
                a(C.ANTICLUS, (0.7, 0.6, 0.1), lambda s, x, y: P(x, y, ts, s=s, f=1, seed=6, eyes="wide",
                                                                 mouth="grin" if lean < 0.7 else "o", brows="up",
                                                                 lean=18 * lean, blush=1.0, arm_b=lerp(-10, 120, lean),
                                                                 elb_b=lerp(10, 40, lean))),
                a(C.greek_soldier(2), (2.3, 0.7, 0.1), lambda s, x, y: P(x, y, ts, s=s, f=-1, seed=7, eyes="wide",
                                                                         mouth="o", brows="worried", sweat=lean))]

    def overlay(self, cx, t, cam, J):
        for Jd in J.values():
            if Jd.get("_fig") is C.ANTICLUS:
                hx, hy = Jd["head"]
                for k in range(3):
                    u = (t * 0.8 + k / 3) % 1
                    S2.heart(cx, hx + 110 + k * 36, hy - 100 - u * 190, 22 * (1 - u * 0.5), 1 - u)


class I22(Shot3):  # Odysseus clamps a hand over his mouth
    set, horse, light = "belly_night", False, "inside_night"
    keys = [(0, ((0.1, -2.9, 1.6), (0.1, 1.5, 1.8), 34)), (2.3, ((0.1, -2.6, 1.62), (0.1, 1.5, 1.82), 36))]

    def clamp(self):
        return self.w("hand", 8) - 0.05

    def shakes(self):
        return [(self.clamp(), 12, 0.3)]

    def actors(self, t):
        ts = step(t)
        c = self.clamp()
        k = ease_out(prog(ts, c - 0.15, c))
        return [a(C.ANTICLUS, (0.75, 0.6, 0.1), lambda s, x, y: P(x, y, ts, s=s, f=-1, seed=6, eyes="wide", mouth="o",
                                                                  brows="up" if k < 1 else "worried", lean=-10 * k)),
                a(C.ODYSSEUS, (-0.75, 0.6, 0.1), lambda s, x, y: P(x, y, ts, s=s, f=1, seed=5,
                                                                   eyes="angry" if k > 0 else "half", mouth="flat",
                                                                   brows="angry", arm_b=lerp(-10, 95, k),
                                                                   elb_b=lerp(10, -10, k), lean=12 * k))]

    def overlay(self, cx, t, cam, J):
        c = self.clamp()
        k = ease_out(prog(t, c - 0.15, c))
        if k <= 0:
            return
        an = od = None
        for Jd in J.values():
            if Jd.get("_fig") is C.ANTICLUS:
                an = Jd
            elif Jd.get("_fig") is C.ODYSSEUS:
                od = Jd
        if not an or not od:
            return
        hx, hy = an["head"]
        R = an["head_rad"]
        mx, my = hx - R * 0.15, hy + R * 0.45
        sx0, sy0 = od["sh_b"]
        sx, sy = lerp(sx0 + 60, mx, k), lerp(sy0, my, k)
        sc = R / 52
        line(cx, [(sx0, sy0), (sx, sy)], hexc("#1C1C24"), 22 * sc)
        line(cx, [(sx0, sy0), (sx, sy)], C.ODYSSEUS.st.skin, 15 * sc)
        ellipse(cx, sx, sy, 50 * sc, 38 * sc)
        fs(cx, C.ODYSSEUS.st.skin, hexc("#1C1C24"), 6)


class P23(Shot3):  # midnight: Sinon opens the hatch
    set, light = "plaza_night", "night"
    keys = [(0, ((-3.2, -5.2, 0.45), (0, 0.6, 3.2), 22)), (1.8, ((-3.4, -5.8, 0.5), (0, 0.6, 3.4), 22))]
    HP = (0, 1.0, 0)

    def op(self):
        return self.w("night", 3) - 0.05

    def objs(self, t):
        return horse_at(self.HP, math.pi)

    def frame_extra(self, t):
        return {"hatch": ease_out(prog(t, self.op(), self.op() + 0.4)), "bow": 1.0}

    def actors(self, t):
        ts = step(t)
        out = [a(C.SINON, (1.6, -1.6, 0), lambda s, x, y: P(x, y, ts, s=s, f=-1, seed=52, eyes="half", mouth="smirk",
                                                            brows="skeptic",
                                                            arm_b=lerp(20, 140, smooth(prog(ts, self.op() - 0.4, self.op()))),
                                                            elb_b=20))]
        if ts > self.op() + 0.45:
            u = ease_out(prog(ts, self.op() + 0.45, self.op() + 0.9))
            out.append(a(C.greek_soldier(1), (0, 1.0, 3.3 - 1.4 * u), lambda s, x, y: P(x, y, ts, s=s, f=-1, seed=8,
                                                                                         eyes="open", mouth="smirk",
                                                                                         view="front")))
        return out

    def overlay(self, cx, t, cam, J):
        if t > self.op() + 0.3:
            k = ease_out(prog(t, self.op() + 0.3, self.op() + 0.6))
            top = cam.project((0, 1.0, 3.25))
            bot = cam.project((0, 1.0, 3.25 - 3.2 * k))
            if top and bot:
                for dx in (-26, 26):
                    line(cx, [(top[0] + dx, top[1]), (bot[0] + dx, bot[1])], hexc("#1C1C24"), 10)
                    line(cx, [(top[0] + dx, top[1]), (bot[0] + dx, bot[1])], hexc("#C9A66B"), 6)
                y = top[1] + 40
                while y < bot[1]:
                    line(cx, [(top[0] - 26, y), (top[0] + 26, y)], hexc("#C9A66B"), 7)
                    y += 50


class W24(Shot3):  # the gates swing open at night
    set, light, horse = "walls_night", "night", False
    keys = [(0, ((0, -11, 1.5), (0, -2, 3.0), 28)), (1.2, ((0, -10.4, 1.5), (0, -2, 3.0), 28))]

    def frame_extra(self, t):
        return {"doors": ease_io(prog(t, 0.0, 0.9))}

    def actors(self, t):
        ts = step(t)
        return [a(C.greek_soldier(i), (x, -3.6, 0), (lambda i: lambda s, x_, y_: (C.walk(P(
            x_, y_, ts, s=s, f=-1 if i else 1, seed=120 + i, eyes="half", mouth="smirk", brows="skeptic",
            arm_b=160 if i == 0 else 20, elb_b=10), ts, 0.8, arms=False) if ts < 0.6 else P(
            x_, y_, ts, s=s, f=-1 if i else 1, seed=120 + i, eyes="half", mouth="smirk", brows="skeptic",
            arm_b=160 if i == 0 else 20, elb_b=10)))(i)) for i, x in enumerate((-1.2, 1.2))]


class S25(Shot3):  # the fleet sails back from behind Tenedos
    set, light, horse = "sea_night", "night", False
    keys = [(0, ((0, -6, 3.0), (25, 160, 6), 30)), (2.8, ((0, -6, 2.6), (15, 100, 4), 28))]

    def objs(self, t):
        o = {}
        goals = [(-14, 34), (8, 28), (26, 44), (-4, 58), (18, 66), (40, 62), (-26, 70), (34, 90)]
        for k, (gx, gy) in enumerate(goals):
            u = ease_out(clamp((t - k * 0.2) / 2.4))
            o[f"Ship{k}"] = {"hide": u <= 0, "loc": [lerp(100 + k * 5, gx, u), lerp(300, gy, u), 0],
                             "rot": [0, 0, -math.pi / 2 - 0.3], "scale": 1.0}
        return o

    def overlay(self, cx, t, cam, J):
        from episodes.troy_en.shots import label
        k = smooth(prog(t, 0.6, 1.0))
        p = cam.project((60, 320, 30))
        if k and p:
            label(cx, "TENEDOS", p[0], p[1] - 40, 44, hexc("#FFFFFF"), alpha=k)


class Split26(Shot3):
    """Finale: top = Greeks with a battering ram against intact walls (10 YEARS);
    bottom (from 'The Trojans') = Trojans tearing it down, horse rolling in (1 AFTERNOON)."""
    split = True

    def __init__(self, src_shot):
        super().__init__(src_shot)
        self.top = SplitHalf(src_shot, "greeks")
        self.bottom = SplitHalf(src_shot, "trojans")

    def b0(self):
        return self.w("end", 9) - 0.1


class SplitHalf(Shot3):
    def __init__(self, src_shot, kind):
        super().__init__(src_shot)
        self.kind = kind
        self.trans_in = self.trans_out = None
        if kind == "greeks":
            self.set, self.horse = "walls", False
            self.keys = [(0, ((-6.5, -14.0, 1.1), (-7, -6, 1.4), 26)), (8, ((-6.5, -13.5, 1.1), (-7, -6, 1.4), 26))]
        else:
            self.set, self.horse = "walls_breach", True
            self.keys = [(0, ((10, -13, 1.6), (10, -4, 2.2), 26)), (8, ((10, -12.5, 1.6), (10, -4, 2.2), 26))]

    def shakes(self):
        if self.kind == "greeks":
            return [(k * 0.9 + 0.35, 10, 0.25) for k in range(8)]
        return [(0.3, 22, 0.6), (1.2, 18, 0.5)]

    def objs(self, t):
        if self.kind == "trojans":
            return horse_at((lerp(32, 11, ease_io(prog(t, 1.4, 3.2))), -10, 0), math.pi)
        return {}

    def actors(self, t):
        ts = step(t)
        out = []
        if self.kind == "greeks":
            ph = (ts % 0.9) / 0.9
            push = math.sin(min(ph, 0.4) / 0.4 * math.pi / 2) if ph < 0.4 else 1 - (ph - 0.4) / 0.6
            for i in range(3):
                out.append(a(C.greek_soldier(i), (-8.6 + i * 1.3 + push * 0.8, -8.0, 0), (lambda i: lambda s, x, y: P(
                    x, y, ts, s=s, f=1, seed=130 + i, eyes="squeeze" if push > 0.8 else "half", mouth="teeth",
                    brows="angry", arm_b=-80, arm_a=-70, elb_a=-30, elb_b=-30, sweat=1.0, lean=16 * push))(i)))
            self._push = push
        else:
            swing = (ts * 2.4) % 1
            for i, (x, f) in enumerate(((6.5, 1), (8.5, 1), (11.5, -1), (13.5, -1))):
                ph = (swing + i * 0.25) % 1
                ang = lerp(170, 60, ease_in(ph))
                fig = C.trojan_soldier(i) if i % 2 else C.trojan_citizen(i + 30)
                out.append(a(fig, (x, -5.2, 0), (lambda f, ang, i: lambda s, x_, y_: P(
                    x_, y_, ts, s=s, f=f, seed=140 + i, mouth="grin", eyes="happy", arm_b=ang, arm_a=ang - 10, elb_b=10,
                    elb_a=10))(f, ang, i)))
        return out

    def overlay(self, cx, t, cam, J):
        if self.kind == "greeks":
            push = getattr(self, "_push", 0)
            p0 = cam.project((-9.8 + push * 0.8, -7.8, 0.75))
            p1 = cam.project((-5.2 + push * 0.8, -7.8, 0.75))
            if p0 and p1:
                w = (p1[0] - p0[0])
                rrect(cx, p0[0], p0[1] - w * 0.07, w, w * 0.14, w * 0.07)
                fs(cx, hexc("#8A5A33"), hexc("#1C1C24"), 6)
                circle(cx, p1[0], p0[1], w * 0.075)
                fs(cx, hexc("#C9A13B"), hexc("#1C1C24"), 5)
        else:
            for Jd in J.values():
                hx, hy = Jd["hand_b"]
                Wd.pickaxe(cx, hx, hy, -0.4, Jd["head_rad"] / 52)
            p = cam.project((10, -3.5, 2))
            if p:
                Wd.dust(cx, p[0] + 150, p[1] + 200, t, 0.2, 8, 90, 5)


ORDER = [B01, B02, B03, W04, B05, B06, B07, I08, B09, R10, R11, W12, S13, B14, B15, W16, W17, P18, P19, P20, I21, I22,
         P23, W24, S25, Split26]


def build():
    return [cls(src) for cls, src in zip(ORDER, S2.SHOTS)]


SHOTS3 = build()


def shot_at(T):
    for s in SHOTS3:
        if s.t0 <= T < s.t1:
            return s
    return SHOTS3[-1]

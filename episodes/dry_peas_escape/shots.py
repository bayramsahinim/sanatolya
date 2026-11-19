"""Shots for "The Prisoner Who Escaped With Dry Peas" - scene-for-scene with the Turkish reference.

Every shot spans a fixed global window [g0, g1] (from the narration schedule). draw() works in
GLOBAL time T, so story beats can be keyed straight to the words that describe them.
"""
import math

import cairo

from cinecode.core import (OUTLINE, H, W, Cam, clamp, ease_io, ease_out, hexc, kf, lerp, line, prog, smooth,
                           src, text, win)
from cinecode.characters import breathe, talk, walk
from cinecode.timeline import Shot
from episodes.dry_peas_escape import world as Wd
from episodes.dry_peas_escape.cast import GENT, GUARD_A, GUARD_B, LADY, PRISONER, WARDEN, pose
from episodes.dry_peas_escape.timing import SCHED, TOTAL, WORDS, find_word

G = Wd.GROUND
BASE = [None]   # frame base matrix (set by the episode renderer; honours draft scaling)


def screen(cx):
    """switch to frame (screen) coordinates."""
    if BASE[0] is not None:
        cx.set_matrix(BASE[0])
    else:
        cx.identity_matrix()


def wt(lid, word, end=False, nth=0):
    return find_word(lid, word, end, nth)


def speaking(T, lid, k0=0, k1=None):
    """True while words k0..k1 of a line are being spoken (for lip-sync of quoted lines)."""
    ws = WORDS[lid]
    k1 = len(ws) - 1 if k1 is None else k1
    return ws[k0][1] - 0.02 <= T <= ws[k1][2] - 0.05


def mouth_for(T, lid, k0, k1, base="smile", talk_kind="yell"):
    if speaking(T, lid, k0, k1):
        v = 0.5 + 0.5 * math.sin(T * 17) * math.sin(T * 6.3 + 1)
        return dict(mouth=talk_kind, mouth_open=0.35 + 0.75 * abs(v))
    return dict(mouth=base)


def tint(cx, rgb, a):
    if a <= 0:
        return
    cx.save()
    screen(cx)
    cx.set_operator(cairo.OPERATOR_MULTIPLY)
    cx.rectangle(0, 0, W, H)
    src(cx, (lerp(1, rgb[0], a), lerp(1, rgb[1], a), lerp(1, rgb[2], a), 1))
    cx.fill()
    cx.restore()


def vignette(cx, a=0.45):
    cx.save()
    screen(cx)
    g = cairo.RadialGradient(W / 2, H * 0.48, H * 0.32, W / 2, H * 0.48, H * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    cx.rectangle(0, 0, W, H)
    cx.set_source(g)
    cx.fill()
    cx.restore()


def laugh_pose(p, T, k=1.0, seed=0):
    b = abs(math.sin(T * 9 + seed)) * 10 * k
    return p.but(bob=p.bob + b, tilt=-8 * k + math.sin(T * 9 + seed) * 4 * k, eyes="happy", mouth="grin",
                 mouth_open=0.8 + 0.3 * abs(math.sin(T * 9 + seed)), brows="up")


class PShot(Shot):
    g0 = 0.0
    g1 = 0.0
    music = "quirky"
    music_gain = 1.0
    amb = "prison"
    amb_gain = 1.0

    def plan(self, P):
        for lid, (a, b) in SCHED.items():
            if self.g0 - 0.01 <= a < self.g1 - 0.01:
                P.t = a - self.g0
                P.say(lid, gap=0)
        self.sounds(P)
        P.t = self.g1 - self.g0

    def sounds(self, P):
        pass

    def fx(self, P, name, T, vol=1.0):
        P.sfx(name, T - self.g0, vol)

    def draw(self, cx, t):
        T = self.g0 + t
        cx.save()
        self.paint(cx, T, t)
        cx.restore()

    def paint(self, cx, T, t):
        pass


def cam_apply(cx, x, y, z, shake=(0, 0)):
    Cam(x + shake[0], y + shake[1], z).apply(cx)


def shake_xy(T, amp, seed=1):
    from cinecode.core import shake
    return shake(T, amp, 22, seed)


# ---------------------------------------------------------------- 1  hook
class S01Hook(PShot):
    """L01 - he spoons his dinner into the wall; guards behind the bars crack up."""
    g0, g1 = 0.0, 7.0

    def sounds(self, P):
        for k in range(8):
            self.fx(P, "pea_tick", 0.9 + k * 0.62, 0.5)
        self.fx(P, "laugh", wt("L01", "guards") - 0.2, 0.55)

    def paint(self, cx, T, t):
        lg = smooth(prog(T, wt("L01", "and") - 0.3, wt("L01", "guards")))
        z = kf(T, [(0, 0.97), (7, 1.08)], ease_io)
        cam_apply(cx, 745, 1040 - 20 * (z - 1), z)

        def guards(cx):
            pa = pose(300, G + 10, T, s=1.9, f=1, seed=5, mouth="smile")
            pb = pose(520, G + 10, T, s=1.9, f=1, seed=6, mouth="smile")
            if lg > 0:
                pa = laugh_pose(pa, T, lg).but(arm_a=40, elb_a=80, arm_b=60 * lg, elb_b=90)
                pb = laugh_pose(pb, T, lg, 1.3).but(arm_b=120 * lg, elb_b=-20, arm_a=10)
            GUARD_A.draw(cx, pa)
            GUARD_B.draw(cx, pb)

        fill = 0.3 + 0.2 * prog(T, 0.5, 7.0)
        Wd.cell(cx, T, dict(fill=fill), behind_bars=guards)
        ph = (T * 1.6) % 1
        scoop = math.sin(ph * 2 * math.pi)
        ab = 88 + 12 * scoop
        p = pose(965, G + 60, T, s=2.3, f=1, seed=1, mouth="smile", brows="neutral",
                 arm_b=ab, elb_b=-14 + 10 * scoop, arm_a=38, elb_a=62, look=(0.6, 0.1))
        J = PRISONER.draw(cx, breathe(p, T))
        hx, hy = J["hand_a"]
        Wd.bowl(cx, hx + 18, hy + 6, 1.25, fill=1.0 - fill * 0.6)
        Wd.spoon(cx, *J["hand_b"], -0.15 + 0.15 * scoop, 1.45, has_pea=scoop < 0.3)
        vignette(cx, 0.3)


# ---------------------------------------------------------------- 2  dry peas
class S02Peas(PShot):
    """L02 - close: every single dry pea, spooned into the crack."""
    g0, g1 = 7.0, 10.05

    def sounds(self, P):
        for k in range(6):
            self.fx(P, "pea_tick", 7.3 + k * 0.45, 0.7)

    def paint(self, cx, T, t):
        z = kf(T, [(7.0, 2.25), (10.05, 2.45)], ease_io)
        cam_apply(cx, 1180, 1180, z)
        fill = 0.5 + 0.12 * prog(T, 7.0, 10.0)
        Wd.cell(cx, T, dict(fill=fill))
        ph = (T - 7.0) / 0.45
        u = ph % 1
        push = math.sin(u * math.pi)
        p = pose(965, G + 60, T, s=2.3, f=1, seed=1, arm_b=92 + 10 * push, elb_b=-16 + 8 * push, arm_a=38,
                 elb_a=62, look=(1, 0), mouth="smile", brows="neutral")
        J = PRISONER.draw(cx, p)
        Wd.bowl(cx, J["hand_a"][0] + 18, J["hand_a"][1] + 6, 1.25, fill=0.6)
        Wd.spoon(cx, *J["hand_b"], -0.1, 1.45, has_pea=u < 0.55)
        # "dry pea" highlight: one pea, big, in the spoon at the start
        a = 1 - smooth(prog(T, 8.6, 9.0))
        if a > 0:
            screen(cx)
            Wd.label_chip(cx, W / 2, 560, "DRY PEAS", 40, alpha=a * smooth(prog(T, 7.6, 7.9)))


# ---------------------------------------------------------------- 3  water + good night
class S03Water(PShot):
    """L03 - pours his one cup of water in, wishes the wall good night, pats it."""
    g0, g1 = 10.05, 14.25

    def sounds(self, P):
        self.fx(P, "pour", 10.45, 0.6)
        for k in range(3):
            self.fx(P, "pat", wt("L03", "pats") + k * 0.28, 0.6)

    def paint(self, cx, T, t):
        cut = wt("L03", "wishes") - 0.1
        if T < cut:
            cam_apply(cx, 1180, 1050, 2.2)
            Wd.cell(cx, T, dict(fill=0.6, wet=smooth(prog(T, 10.6, 11.5))))
            tilt = kf(T, [(10.1, 0.0), (10.5, 1.6), (11.4, 1.7)])
            p = pose(965, G + 60, T, s=2.3, f=1, seed=1, arm_b=128, elb_b=-30, arm_a=10, elb_a=10,
                     look=(1, -0.4), mouth="smile")
            J = PRISONER.draw(cx, p)
            hx, hy = J["hand_b"]
            Wd.cup(cx, hx, hy, 1.4, tilt, water=1 - prog(T, 10.6, 11.6))
            a = smooth(prog(T, 10.45, 10.6)) * (1 - smooth(prog(T, 11.5, 11.7)))
            Wd.water_stream(cx, hx + 70 * math.cos(tilt) - 20, hy + 60 * math.sin(tilt) - 30, Wd.CRACK_X - 10,
                            1060, T, 14, a)
        else:
            cam_apply(cx, 1060, 1060, 1.45)
            Wd.cell(cx, T, dict(fill=0.6, wet=0.6))
            pat = math.sin((T - wt("L03", "pats")) * 22) if T > wt("L03", "pats") else 0
            reach = smooth(prog(T, cut, cut + 0.4))
            p = pose(1000, G + 60, T, s=2.3, f=1, seed=1, arm_b=40 + 62 * reach, elb_b=-8 + 6 * pat, arm_a=10,
                     elb_a=10, eyes="happy" if T > wt("L03", "good") else "open", mouth="smile", tilt=6,
                     look=(1, 0))
            PRISONER.draw(cx, breathe(p, T))
        vignette(cx, 0.28)


# ---------------------------------------------------------------- 4  dessert
class S04Dessert(PShot):
    """L04-L05 - "Want some dessert?" - a huge sausage waved under his nose. He doesn't flinch."""
    g0, g1 = 14.25, 19.2

    def sounds(self, P):
        self.fx(P, "sizzle", 14.4, 0.35)
        self.fx(P, "whoosh_soft", wt("L05", "waving"), 0.4)

    def paint(self, cx, T, t):
        z = kf(T, [(14.25, 1.3), (16.2, 1.3), (17.0, 1.45), (19.2, 1.52)], ease_io)
        cam_apply(cx, kf(T, [(14.25, 800), (16.2, 800), (17.0, 830)]), 1010, z)
        Wd.cell(cx, T, dict(fill=0.62, wet=0.3))
        wave = smooth(prog(T, wt("L05", "waving"), wt("L05", "waving") + 0.4))
        sw = math.sin((T - 16.2) * 7) * 18 * wave
        gx = kf(T, [(14.25, 440), (15.6, 520)])
        g = pose(gx, G + 60, T, s=2.2, f=1, seed=5, arm_b=104 + 10 * wave + sw * 0.4, elb_b=14, arm_a=8,
                 brows="up", **mouth_for(T, "L04", 0, 2, base="smirk", talk_kind="grin"))
        g = breathe(g, T)
        Jg = GUARD_A.draw(cx, g)
        p = pose(1010, G + 60, T, s=2.3, f=-1, seed=1, eyes="half", brows="flat", mouth="flat",
                 arm_a=6, arm_b=-6, look=(0.0, 0.0))
        PRISONER.draw(cx, breathe(p, T, 0.6))
        hx, hy = Jg["hand_b"]
        Wd.sausage_fork(cx, hx, hy, -0.05 + sw * 0.004, 1.15, T, steam=1.0)


# ---------------------------------------------------------------- 5  mouth waters / last pea
class S05LastPea(PShot):
    """L06 - his mouth waters... but the last pea goes to the wall too."""
    g0, g1 = 19.2, 22.9

    def sounds(self, P):
        self.fx(P, "gulp", wt("L06", "waters") + 0.1, 0.55)
        self.fx(P, "pea_tick", wt("L06", "wall") + 0.05, 0.9)
        self.fx(P, "pop", wt("L06", "wall") + 0.07, 0.35)

    def paint(self, cx, T, t):
        turn = wt("L06", "but") - 0.05
        if T < turn:
            cam_apply(cx, 900, 990, 2.4)
            Wd.cell(cx, T, dict(fill=0.62, wet=0.3))
            p = pose(1010, G + 60, T, s=2.3, f=-1, seed=1, eyes="half", brows="worried", mouth="o", mouth_open=0.7,
                     look=(-0.6, 0.3), arm_a=6, arm_b=-6)
            J = PRISONER.draw(cx, p)
            hx, hy = J["head"]
            R = J["head_rad"]
            Wd.drool(cx, hx - R * 0.25, hy + R * 0.62, smooth(prog(T, 19.6, 20.6)), 2.2)
            Wd.sausage_fork(cx, hx - 330, hy + 30 + math.sin(T * 7) * 12, -0.05, 1.15, T, steam=1.0)
        else:
            u = smooth(prog(T, turn, turn + 0.6))
            cam_apply(cx, lerp(1060, 1150, u), lerp(800, 1100, u), lerp(2.0, 2.3, u))
            fill = 0.62 + 0.03 * prog(T, wt("L06", "wall"), wt("L06", "wall") + 0.2)
            Wd.cell(cx, T, dict(fill=fill, wet=0.3))
            push = smooth(prog(T, wt("L06", "pea") - 0.2, wt("L06", "wall")))
            p = pose(965, G + 60, T, s=2.3, f=1, seed=1, arm_b=80 + 22 * push, elb_b=-14, arm_a=38, elb_a=62,
                     look=(1, 0), eyes="closed" if push > 0.95 else "open", mouth="smile")
            J = PRISONER.draw(cx, p)
            Wd.bowl(cx, J["hand_a"][0] + 18, J["hand_a"][1] + 6, 1.25, fill=0.0)
            Wd.spoon(cx, *J["hand_b"], -0.12, 1.45, has_pea=push < 0.98)


# ---------------------------------------------------------------- 6  warden laughs + order
class S06Warden(PShot):
    """L07-L09 - the warden comes, laughs till he cries, orders double portions for the wall."""
    g0, g1 = 22.9, 29.0

    def sounds(self, P):
        for k in range(4):
            self.fx(P, "step_heavy", 23.05 + k * 0.42, 0.35)
        self.fx(P, "keys", 23.1, 0.4)
        self.fx(P, "laugh_big", wt("L08", "laughs") - 0.05, 0.6)

    def paint(self, cx, T, t):
        arrive = 24.5
        z = kf(T, [(22.9, 1.0), (24.3, 1.0), (25.0, 1.45), (27.3, 1.5), (27.6, 1.75)], ease_io)
        cy = kf(T, [(22.9, 1000), (24.3, 1000), (25.0, 830), (27.6, 800)], ease_io)
        cxx = kf(T, [(22.9, 760), (24.3, 760), (25.0, 640)], ease_io)
        cam_apply(cx, cxx, cy, z)

        def inc(cx):
            PRISONER.draw(cx, pose(1060, G, T, s=2.2, f=1, seed=1, arm_b=95, elb_b=-14))

        Wd.corridor(cx, T, dict(fill=0.64), in_cell=inc, cell_x0=900, crack_off=300,
                    torches=((300, 760),))
        wx = kf(T, [(22.9, 60), (arrive, 600)], lambda x: x)
        p = pose(wx, G + 60, T, s=2.45, f=1, seed=7, mouth="flat", brows="neutral", look=(1, 0))
        if T < arrive:
            p = walk(p, T, 1.2, 0.8)
        lt0, lt1 = wt("L08", "laughs") - 0.1, wt("L08", "order", end=True)
        order = wt("L09", "Double") - 0.25
        if lt0 <= T < order:
            k = smooth(prog(T, lt0, lt0 + 0.25)) * (1 - smooth(prog(T, lt1 - 0.2, order)))
            p = laugh_pose(p, T, k).but(arm_a=40, elb_a=90 * k, arm_b=40, elb_b=90 * k, look=(0, 0))
            if k < 0.2:
                p = p.but(eyes="open", mouth="smile")
        elif T >= order:
            u = smooth(prog(T, order, order + 0.3))
            p = p.but(arm_b=40 + 55 * u, elb_b=40 * u, brows="angry",
                      **mouth_for(T, "L09", 0, 4, base="smile", talk_kind="yell"))
            p = p.but(look=(0.3, 0))
        J = WARDEN.draw(cx, breathe(p, T))
        if lt0 <= T < order:
            hx, hy = J["head"]
            Wd.tears(cx, hx, hy, J["head_rad"], T, smooth(prog(T, wt("L08", "until"), wt("L08", "cries"))))
        if T >= order:
            hx, hy = J["hand_b"]
            line(cx, [(hx, hy), (hx + 4, hy - 52)], OUTLINE, 12)


# ---------------------------------------------------------------- 7  double portions
class S07Double(PShot):
    """L10 - the wall eats twice as much."""
    g0, g1 = 29.0, 31.05

    def sounds(self, P):
        for k in range(8):
            self.fx(P, "pea_tick", 29.1 + k * 0.24, 0.55)

    def paint(self, cx, T, t):
        cam_apply(cx, 1060, 1060, 1.5)
        fill = 0.66 + 0.3 * prog(T, 29.0, 31.0)
        Wd.cell(cx, T, dict(fill=fill, bulge=0.0))
        ph = (T * 3.2) % 1
        scoop = math.sin(ph * 2 * math.pi)
        p = pose(965, G + 60, T, s=2.3, f=1, seed=1, arm_b=90 + 12 * scoop, elb_b=-14 + 10 * scoop, arm_a=38,
                 elb_a=62, look=(1, 0), mouth="smile", brows="up")
        J = PRISONER.draw(cx, p)
        hx, hy = J["hand_a"]
        Wd.bowl(cx, hx + 18, hy + 6, 1.25, fill=1.0)
        Wd.bowl(cx, hx + 18, hy - 40, 1.25, fill=1.0, seed=5)
        Wd.spoon(cx, *J["hand_b"], -0.15 + 0.15 * scoop, 1.45, has_pea=scoop < 0.3)
        screen(cx)
        a = smooth(prog(T, 29.2, 29.5))
        Wd.label_chip(cx, W / 2, 540, "x2", 64, alpha=a)


# ---------------------------------------------------------------- 8  licks spoon
class S08Lick(PShot):
    """L11 - the prisoner just licks his spoon."""
    g0, g1 = 31.05, 32.7

    def sounds(self, P):
        self.fx(P, "lick", 31.45, 0.5)
        self.fx(P, "lick", 32.0, 0.4)

    def paint(self, cx, T, t):
        cam_apply(cx, 1010, 990, 2.5)
        Wd.cell(cx, T, dict(fill=0.96))
        p = pose(965, G + 60, T, s=2.3, f=1, seed=1, eyes="happy", mouth="o", mouth_open=0.8,
                 arm_b=150, elb_b=-118, arm_a=6, look=(0, 0))
        J = PRISONER.draw(cx, p)
        hx, hy = J["head"]
        R = J["head_rad"]
        lk = math.sin((T - 31.3) * 9) * 0.5 + 0.5 if T > 31.3 else 0
        # tongue
        mx, my = hx + R * 0.24, hy + R * 0.5
        cx.save()
        cx.translate(mx, my)
        cx.rotate(-0.5)
        from cinecode.core import rrect, fs
        rrect(cx, -8, -6, 34 + 12 * lk, 16, 8)
        fs(cx, hexc("#F27C93"), OUTLINE, 3.5)
        cx.restore()
        Wd.spoon(cx, mx + 30, my + 40 + 10 * lk, -1.45, 1.45)


# ---------------------------------------------------------------- 9  beanstalk
class S09Beanstalk(PShot):
    """L12 - "He's growing a beanstalk!" ... and the laughter stops."""
    g0, g1 = 32.7, 36.75

    def sounds(self, P):
        self.fx(P, "laugh", 32.75, 0.45)
        self.fx(P, "record_stop", wt("L12", "laughter") - 0.1, 0.45)

    def paint(self, cx, T, t):
        stop = wt("L12", "laughter") - 0.15
        z = kf(T, [(32.7, 1.05), (stop, 1.15), (stop + 0.4, 1.35)], ease_io)
        cam_apply(cx, kf(T, [(32.7, 720), (stop + 0.4, 760)]), kf(T, [(32.7, 1000), (stop + 0.4, 930)]), z)

        def inc(cx):
            PRISONER.draw(cx, pose(1060, G, T, s=2.2, f=1, seed=1, arm_b=95, elb_b=-14))

        Wd.corridor(cx, T, dict(fill=0.98, sprout=smooth(prog(T, 32.7, 34.0)) * 0.45), in_cell=inc, cell_x0=900,
                    crack_off=300)
        lk = 1 - smooth(prog(T, stop, stop + 0.25))
        flat = 1 - lk
        for fig, x, sd, s in ((WARDEN, 330, 7, 2.4), (GUARD_A, 560, 5, 2.25), (GUARD_B, 790, 6, 2.25)):
            p = pose(x, G + 60, T, s=s, f=1, seed=sd, look=(1, 0))
            if lk > 0.05:
                p = laugh_pose(p, T, lk, sd)
            if fig is GUARD_B:
                if speaking(T, "L12", 0, 3):
                    p = p.but(eyes="wide", brows="up", arm_b=96, elb_b=-6,
                              **mouth_for(T, "L12", 0, 3, talk_kind="o"))
                elif T < stop:
                    p = p.but(eyes="wide", brows="up", mouth="o", arm_b=96, elb_b=-6)
            if flat > 0.5:
                p = p.but(eyes="wide", brows="worried", mouth="flat" if fig is not GUARD_B else "o", mouth_open=0.5,
                          sweat=smooth(prog(T, stop + 0.2, stop + 0.8)))
            fig.draw(cx, breathe(p, T))


# ---------------------------------------------------------------- 10 three weeks later
class S10Weeks(PShot):
    """L13a - three weeks and ten thousand peas later (time-lapse)."""
    g0, g1 = 36.75, 38.95

    def sounds(self, P):
        for k in range(14):
            self.fx(P, "pea_tick", 36.8 + k * 0.15, 0.35)
        self.fx(P, "timelapse", 36.8, 0.4)

    def paint(self, cx, T, t):
        u = prog(T, 36.75, 38.95)
        cam_apply(cx, 1060, 1040, 1.25)
        day = 0.5 + 0.5 * math.cos(u * 2 * math.pi * 3.5)
        Wd.cell(cx, T, dict(fill=1.0, bulge=0.2 + 0.6 * u, sprout=0.45 + 0.4 * u, window=day))
        ph = (T * 5) % 1
        scoop = math.sin(ph * 2 * math.pi)
        p = pose(965, G + 60, T, s=2.3, f=1, seed=1, arm_b=90 + 12 * scoop, elb_b=-14 + 10 * scoop, arm_a=38,
                 elb_a=62, look=(1, 0), mouth="flat", eyes="half", extra={"thin": 0.6 * u})
        J = PRISONER.draw(cx, p)
        Wd.bowl(cx, J["hand_a"][0] + 18, J["hand_a"][1] + 6, 1.25, fill=1.0)
        Wd.spoon(cx, *J["hand_b"], -0.15 + 0.15 * scoop, 1.45, has_pea=scoop < 0.3)
        tint(cx, (0.35, 0.45, 0.8), 0.55 * (1 - day))
        screen(cx)
        # tally of peas (the "10,000" of the source)
        n = int(10000 * smooth(prog(T, 37.6, 38.6)))
        a = smooth(prog(T, 37.5, 37.7))
        if a > 0:
            Wd.label_chip(cx, W / 2, 520, f"{n:,} PEAS", 54, alpha=a)


# ---------------------------------------------------------------- 11 tickets
class S11Tickets(PShot):
    """L13b - the warden sells tickets to watch the wall sprout."""
    g0, g1 = 38.95, 42.15

    def sounds(self, P):
        self.fx(P, "murmur_soft", 38.95, 0.35)
        for k, tt in enumerate((40.0, 40.9, 41.6)):
            self.fx(P, "coin", tt, 0.55)

    def paint(self, cx, T, t):
        cam_apply(cx, kf(T, [(38.95, 640), (42.15, 700)]), 980, 1.12)

        def inc(cx):
            pass

        def props(cx):
            Wd.sign_board(cx, 450, 700)

        Wd.corridor(cx, T, dict(fill=1.0, bulge=0.8, sprout=0.9), in_cell=inc, cell_x0=980, crack_off=300,
                    torches=((90, 760),), props=props)
        # queue
        LADY.draw(cx, breathe(pose(260, G + 60, T, s=2.1, f=1, seed=9, mouth="smile", look=(1, 0)), T))
        give = math.sin(max(0, T - 39.9) * 3) > 0.3
        GENT.draw(cx, breathe(pose(500, G + 60, T, s=2.2, f=1, seed=8, mouth="smile", look=(1, 0),
                                   arm_b=70 if give else 20, elb_b=10), T))
        Jw = WARDEN.draw(cx, breathe(pose(820, G + 60, T, s=2.4, f=-1, seed=7, mouth="grin", mouth_open=0.7,
                                          eyes="happy", arm_b=60 + 10 * math.sin(T * 6), elb_b=20), T))
        Wd.table(cx, 680, G + 60, w=330, h=230)
        for k in range(int(6 + 4 * prog(T, 39, 42))):
            Wd.coin(cx, 600 + k * 14, G + 60 - 236 - (k % 3) * 6, 14)
        Wd.ticket(cx, Jw["hand_b"][0] - 30, Jw["hand_b"][1], -0.3, 1.1)


# ---------------------------------------------------------------- 12 hungry guard steals
class S12Steal(PShot):
    """L14a - that evening, a hungry guard steals a handful of peas from the wall."""
    g0, g1 = 42.15, 45.5

    def sounds(self, P):
        self.fx(P, "growl", 42.6, 0.5)
        for k in range(3):
            self.fx(P, "tiptoe", 42.3 + k * 0.35, 0.4)
        self.fx(P, "grab", wt("L14", "handful"), 0.5)

    def paint(self, cx, T, t):
        cam_apply(cx, 1060, 1040, 1.35)
        grab = wt("L14", "handful") - 0.1
        took = T > grab + 0.2
        Wd.cell(cx, T, dict(fill=1.0, bulge=0.8 - (0.1 if took else 0), sprout=0.9, window=0.0))
        # prisoner asleep on the cot in the background
        gx = kf(T, [(42.15, 700), (grab - 0.3, 1010)], lambda x: x)
        g = pose(gx, G + 60, T, s=2.25, f=1, seed=6, eyes="half", brows="worried", mouth="wavy", look=(1, 0))
        if T < grab - 0.3:
            g = walk(g, T, 1.6, 0.6).but(bob=-abs(math.sin(T * 10)) * 8)
        else:
            reach = smooth(prog(T, grab - 0.3, grab)) * (1 - smooth(prog(T, grab + 0.3, grab + 0.7)))
            g = g.but(arm_b=40 + 60 * reach, elb_b=-8, mouth="smirk", eyes="open", brows="neutral")
        J = GUARD_B.draw(cx, g)
        if took:
            hx, hy = J["hand_b"]
            for k in range(5):
                Wd.pea(cx, hx - 10 + k * 8, hy - 12 - (k % 2) * 8, 10)
        tint(cx, (1.0, 0.7, 0.5), 0.32)
        vignette(cx, 0.45)


# ---------------------------------------------------------------- 13 stash in the jug
class S13Stash(PShot):
    """L14b - and hides them in his water jug. *WORST STASH EVER*"""
    g0, g1 = 45.5, 47.25

    def sounds(self, P):
        self.fx(P, "plop", wt("L14", "jug") - 0.25, 0.6)

    def paint(self, cx, T, t):
        cam_apply(cx, 520, 1060, 1.55)
        Wd.corridor(cx, T, dict(fill=1.0, sprout=0.9), cell_x0=1100, torches=())
        Wd.chair(cx, 280, G + 60, f=1)
        drop = smooth(prog(T, wt("L14", "hides") - 0.1, wt("L14", "jug") - 0.25))
        g = pose(420, G + 60, T, s=2.25, f=1, seed=6, mouth="smirk", brows="skeptic", eyes="half",
                 arm_b=60 + 40 * drop, elb_b=-10, look=(1, 0.4))
        J = GUARD_B.draw(cx, breathe(g, T))
        Wd.table(cx, 760, G + 60, w=320, h=230)
        Wd.lantern(cx, 860, G + 60 - 230, 1.0, T)
        Wd.jug(cx, 700, G + 60 - 230, 1.0, peas=smooth(prog(T, wt("L14", "jug") - 0.25, wt("L14", "jug"))))
        if T < wt("L14", "jug") - 0.25:
            hx, hy = J["hand_b"]
            for k in range(5):
                Wd.pea(cx, hx - 10 + k * 8, hy - 12 - (k % 2) * 8, 10)
        tint(cx, (1.0, 0.6, 0.38), 0.5)
        vignette(cx, 0.5)


# ---------------------------------------------------------------- 14 skin and bones
class S14Thirsty(PShot):
    """L15-L16 - skin and bones, the prisoner finally speaks: "The wall is thirsty." """
    g0, g1 = 47.25, 52.1

    def sounds(self, P):
        self.fx(P, "wind_low", 47.3, 0.25)

    def paint(self, cx, T, t):
        z = kf(T, [(47.25, 1.3), (50.4, 1.45), (50.8, 1.95), (52.1, 2.05)], ease_io)
        cam_apply(cx, kf(T, [(47.25, 1080), (50.8, 1080)]), kf(T, [(47.25, 1040), (50.8, 860)]), z)
        Wd.cell(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0, window=0.6))
        lift = smooth(prog(T, wt("L15", "finally") - 0.2, wt("L15", "speaks")))
        p = pose(1000, G + 60, T, s=2.3, f=-1, seed=1, eyes="half", brows="flat", look=(-0.3, 0),
                 arm_a=150 * lift + 6, elb_a=-60 * lift, arm_b=-4, extra={"thin": 1.0},
                 **mouth_for(T, "L16", 0, 3, base="flat", talk_kind="chew"))
        PRISONER.draw(cx, breathe(p, T, 0.4))
        tint(cx, (0.85, 0.9, 1.0), 0.25)


# ---------------------------------------------------------------- 15 water the beanstalk
class S15Bucket(PShot):
    """L17 - "Water the beanstalk!" the warden roars, grabs a bucket and soaks the crack himself."""
    g0, g1 = 52.1, 56.8

    def sounds(self, P):
        self.fx(P, "bucket_grab", wt("L17", "grabs"), 0.5)
        self.fx(P, "splash", wt("L17", "soaks"), 0.75)

    def paint(self, cx, T, t):
        cut = wt("L17", "then") - 0.05
        soak = wt("L17", "soaks") - 0.1
        if T < cut:
            sh = shake_xy(T, 6 * smooth(prog(T, 52.2, 52.5)))
            cam_apply(cx, 700, 985, 2.2, sh)
            Wd.corridor(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0), cell_x0=1100, torches=((300, 760),))
            p = pose(700, G + 60, T, s=2.45, f=1, seed=7, brows="angry", eyes="angry", arm_b=28, elb_b=40,
                     arm_a=-20, elb_a=40, lean=6,
                     **mouth_for(T, "L17", 0, 2, base="yell", talk_kind="yell"))
            WARDEN.draw(cx, p)
        else:
            u = smooth(prog(T, soak - 0.35, soak))
            z = kf(T, [(cut, 1.3), (soak - 0.2, 1.35), (soak + 0.1, 1.9)], ease_io)
            cam_apply(cx, kf(T, [(cut, 1000), (soak + 0.1, 1150)]), kf(T, [(cut, 1050), (soak + 0.1, 1080)]), z)
            Wd.cell(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0, wet=smooth(prog(T, soak, soak + 0.4))))
            pp = pose(1560, G + 60, T, s=2.3, f=-1, seed=1, eyes="wide", mouth="o", extra={"thin": 1.0})
            PRISONER.draw(cx, pp)
            wx = kf(T, [(cut, 620), (soak - 0.5, 900)], ease_out)
            w = pose(wx, G + 60, T, s=2.45, f=1, seed=7, brows="angry", mouth="yell", mouth_open=0.6,
                     arm_b=40 + 80 * u, elb_b=-20 - 30 * u, arm_a=30 + 70 * u, elb_a=-10, lean=8 * u)
            if T < soak - 0.5:
                w = walk(w, T, 1.6, 0.9).but(arm_b=40, elb_b=-20, brows="angry", mouth="yell", mouth_open=0.6)
            J = WARDEN.draw(cx, w)
            hx, hy = J["hand_b"]
            Wd.bucket(cx, hx, hy - 20, 1.1, rot=-1.9 * u, water=u < 0.9)
            if T > soak - 0.05:
                Wd.splash(cx, Wd.CRACK_X - 40, 1080, prog(T, soak - 0.05, soak + 0.8), 1.2)
                a = 1 - prog(T, soak + 0.1, soak + 0.5)
                Wd.water_stream(cx, hx + 60, hy + 40, Wd.CRACK_X - 20, 1080, T, 40, max(0, a))
        vignette(cx, 0.35)


# ---------------------------------------------------------------- 16 jug explodes
class S16Bang(PShot):
    """L18 - that night, the guard's jug of stolen peas explodes with a loud bang."""
    g0, g1 = 56.8, 60.95
    music = "night"

    def sounds(self, P):
        self.fx(P, "snore", 57.0, 0.45)
        self.fx(P, "snore", 58.6, 0.4)
        self.fx(P, "creak_glass", 59.3, 0.4)
        self.fx(P, "bang", wt("L18", "bang") - 0.12, 0.9)

    def paint(self, cx, T, t):
        bang = wt("L18", "bang") - 0.12
        sh = shake_xy(T, 14 * (1 - prog(T, bang, bang + 0.5)) if T > bang else 0)
        z = kf(T, [(56.8, 1.3), (bang - 0.6, 1.55)], ease_io)
        cam_apply(cx, 560, 1140, z, sh)
        Wd.corridor(cx, T, dict(fill=1.0, sprout=1.0, wet=1.0), cell_x0=1100, torches=())
        Wd.chair(cx, 330, G + 60, f=1)
        woke = T > bang
        if not woke:
            g = pose(360, G + 50, T, s=2.25, f=1, seed=6, eyes="closed", mouth="o", mouth_open=0.4 + 0.2 *
                     math.sin(T * 2.5), tilt=14, hip_a=-80, knee_a=-90, hip_b=-76, knee_b=-90, bob=78, arm_a=20,
                     arm_b=20, elb_b=40, blink=False)
        else:
            u = smooth(prog(T, bang, bang + 0.15))
            g = pose(360, G + 50 - 60 * u, T, s=2.25, f=1, seed=6, eyes="wide", brows="up", mouth="scream",
                     hip_a=-80, knee_a=-90, hip_b=-76, knee_b=-90, bob=78, arm_a=150, arm_b=160, elb_a=20, elb_b=20)
        J = GUARD_B.draw(cx, g)
        Wd.table(cx, 760, G + 60, w=320, h=230)
        Wd.lantern(cx, 870, G + 60 - 230, 1.0, T, lit=0.8)
        sw = smooth(prog(T, 57.6, bang))
        if T < bang + 0.05:
            Wd.jug(cx, 700, G + 60 - 230, 1.0, peas=1.0, swell=sw, shake=prog(T, 59.2, bang),
                   crack=prog(T, 59.6, bang), t=T)
        Wd.jug_burst(cx, 700, G + 60 - 230, 1.0, prog(T, bang, bang + 0.9))
        if not woke:
            hx, hy = J["head"]
            Wd.zzz(cx, hx + 50, hy - 60, T)
        tint(cx, (0.42, 0.5, 0.82), 0.5)
        if woke:
            cx.save()
            screen(cx)
            a = 1 - prog(T, bang, bang + 0.3)
            cx.rectangle(0, 0, W, H)
            src(cx, (1, 0.95, 0.8, 0.6 * a))
            cx.fill()
            cx.restore()
        vignette(cx, 0.5)


# ---------------------------------------------------------------- 17 the wall cracks
class S17Crack(PShot):
    """L19 - then the wall starts to crack."""
    g0, g1 = 60.95, 62.75
    music = "night"

    def sounds(self, P):
        self.fx(P, "rumble", 61.0, 0.7)
        self.fx(P, "crackle", 61.3, 0.6)

    def paint(self, cx, T, t):
        fr = smooth(prog(T, 61.1, 62.6))
        sh = shake_xy(T, 3 + 6 * fr, 3)
        cam_apply(cx, 1300, 1080, kf(T, [(60.95, 1.0), (62.75, 1.12)]), sh)
        Wd.cell(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0, wet=0.6, swell=0.3 * fr, fracture=fr, window=0.0))
        p = pose(1610, G + 60, T, s=2.3, f=-1, seed=1, eyes="wide", brows="worried", mouth="o", mouth_open=0.6,
                 look=(-1, 0), extra={"thin": 1.0}, arm_a=20, arm_b=-10)
        PRISONER.draw(cx, p)
        # dust
        cx.save()
        for k in range(10):
            ph = (T * 0.9 + k * 0.137) % 1
            x = Wd.CRACK_X + math.sin(k * 7.1) * 120
            y = 760 + ph * 700
            from cinecode.core import circle
            circle(cx, x, y, 3 + (k % 3))
            src(cx, (0.85, 0.85, 0.8, 0.7 * fr * (1 - ph)))
            cx.fill()
        cx.restore()
        tint(cx, (0.42, 0.5, 0.82), 0.5)
        vignette(cx, 0.5)


# ---------------------------------------------------------------- 18 dry peas swell
class S18Swell(PShot):
    """L20 - dry peas swell when they get wet (educational close-up)."""
    g0, g1 = 62.75, 64.85
    music = "night"

    def sounds(self, P):
        self.fx(P, "swell", 62.9, 0.55)
        self.fx(P, "crackle", 63.6, 0.45)

    def paint(self, cx, T, t):
        sw = smooth(prog(T, 62.95, 64.5))
        cam_apply(cx, Wd.CRACK_X + 10, 1150, kf(T, [(62.75, 2.6), (64.85, 2.9)]), shake_xy(T, 2 + 3 * sw, 5))
        Wd.cell(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0, wet=1.0, swell=0.3 + 0.7 * sw, fracture=0.6 + 0.4 * sw,
                            window=0.0))
        tint(cx, (0.4, 0.5, 0.82), 0.45)
        screen(cx)
        # inset diagram: dry pea + water -> swollen pea
        a = smooth(prog(T, 62.85, 63.15))
        if a > 0:
            cx.save()
            cx.push_group()
            from cinecode.core import rrect, fs
            rrect(cx, 110, 250, 860, 420, 44)
            fs(cx, (1, 1, 1, 0.94), OUTLINE, 6)
            Wd.pea(cx, 280, 440, 40, 0.0, 0.0, 0.3, lw=5)
            Wd.label_chip(cx, 280, 590, "DRY", 34)
            # water drop + arrow
            dx, dy = 470, 440
            cx.move_to(dx, dy - 50)
            cx.curve_to(dx + 34, dy - 4, dx + 34, dy + 30, dx, dy + 30)
            cx.curve_to(dx - 34, dy + 30, dx - 34, dy - 4, dx, dy - 50)
            fs(cx, hexc("#6CC1FF"), OUTLINE, 5)
            line(cx, [(560, 440), (640, 440)], OUTLINE, 8)
            line(cx, [(620, 420), (642, 440), (620, 460)], OUTLINE, 8)
            g = 0.3 + 0.7 * smooth(prog(T, 63.3, 64.3))
            Wd.pea(cx, 790, 440, 40 * (1 + 0.6 * g) / 1.55, g, 1.0, 0.3, lw=5)
            for k in range(4):
                ang = k * math.pi / 2 + math.pi / 4
                r0 = 80 + 10 * math.sin(T * 8)
                line(cx, [(790 + math.cos(ang) * r0, 440 + math.sin(ang) * r0),
                          (790 + math.cos(ang) * (r0 + 26), 440 + math.sin(ang) * (r0 + 26))],
                     (*OUTLINE[:3], g), 6)
            Wd.label_chip(cx, 790, 590, "WET", 34, fill_c=hexc("#E3F4FF"))
            cx.pop_group_to_source()
            cx.paint_with_alpha(a)
            cx.restore()


# ---------------------------------------------------------------- 19 burst
class S19Burst(PShot):
    """L21a - ten thousand peas burst the prison wall..."""
    g0, g1 = 64.85, 66.75
    music = "quirky"

    def sounds(self, P):
        self.fx(P, "rumble", 64.9, 0.6)
        self.fx(P, "wall_burst", wt("L21", "burst") - 0.35, 0.95)
        self.fx(P, "pea_rain", wt("L21", "burst") - 0.25, 0.6)

    def paint(self, cx, T, t):
        b0 = wt("L21", "burst") - 0.4
        u = prog(T, b0, b0 + 1.1)
        sh = shake_xy(T, 6 + 14 * (u > 0) * (1 - u), 9)
        z = kf(T, [(64.85, 1.4), (b0, 1.5)], ease_io)
        cam = (Wd.CRACK_X, 1120, z)
        # behind the wall: the outside
        cx.save()
        cam_apply(cx, 540 + (cam[0] - Wd.CRACK_X) * 0.3, 1100, 1.0)
        Wd.outside(cx, T)
        cx.restore()
        # the wall with a growing hole
        cx.push_group()
        cx.save()
        cam_apply(cx, *cam, sh)
        Wd.cell(cx, T, dict(fill=1.0, bulge=1.0, sprout=1.0, wet=1.0, swell=1.0, fracture=1.0, window=0.0))
        tint(cx, (0.42, 0.5, 0.82), 0.45 * (1 - u))
        if u > 0:
            import random
            rnd = random.Random(2)
            hr = 900 * ease_out(u)
            cx.set_operator(cairo.OPERATOR_CLEAR)
            pts = []
            for k in range(18):
                a = k / 18 * 2 * math.pi
                r = hr * rnd.uniform(0.7, 1.15)
                pts.append((Wd.CRACK_X + math.cos(a) * r * 0.75, 1120 + math.sin(a) * r))
            from cinecode.core import poly
            poly(cx, pts)
            cx.fill()
            cx.set_operator(cairo.OPERATOR_OVER)
        cx.restore()
        cx.pop_group_to_source()
        cx.paint()
        # flying chunks + peas towards camera
        if u > 0:
            import random
            rnd = random.Random(4)
            cx.save()
            cx.translate(W / 2, H * 0.55)
            from cinecode.core import rrect, fs
            for k in range(46):
                a = rnd.uniform(0, 2 * math.pi)
                v = rnd.uniform(300, 1100)
                sc = 1 + 2.2 * u * rnd.uniform(0.5, 1.2)
                px, py = math.cos(a) * v * u, math.sin(a) * v * u + 500 * u * u
                if k % 3 == 0:
                    cx.save()
                    cx.translate(px, py)
                    cx.rotate(a + u * 5)
                    cx.scale(sc, sc)
                    rrect(cx, -36, -20, 72, 40, 8)
                    fs(cx, Wd.STONE, OUTLINE, 4)
                    cx.restore()
                else:
                    Wd.pea(cx, px, py, 16 * sc, 1.0, 1.0, a, lw=4)
            cx.restore()
        if 0 < u < 0.25:
            cx.rectangle(0, 0, W, H)
            src(cx, (1, 1, 0.9, 0.7 * (1 - u / 0.25)))
            cx.fill()


# ---------------------------------------------------------------- 20 outside
class S20Free(PShot):
    """L21b - ...wide open. Outside at sunset, knee-deep in peas."""
    g0, g1 = 66.75, TOTAL
    music = "quirky"

    def sounds(self, P):
        self.fx(P, "pea_rain", 66.8, 0.4)
        self.fx(P, "poof", 68.55, 0.5)
        self.fx(P, "sparkle", 68.65, 0.45)

    def paint(self, cx, T, t):
        import random
        cam_apply(cx, 540, kf(T, [(66.75, 1000), (TOTAL, 1060)]), kf(T, [(66.75, 1.0), (TOTAL, 1.08)]))
        Wd.outside(cx, T)
        # prison wall with the hole (left side)
        from cinecode.core import poly, fs
        cx.save()
        cx.push_group()
        Wd.blocks(cx, -400, 600, 420, 1500, 150, 84, Wd.STONE, Wd.MORTAR, seed=8, r=8, lw=6)
        cx.set_operator(cairo.OPERATOR_CLEAR)
        poly(cx, [(150, 760), (330, 700), (440, 900), (460, 1200), (380, 1520), (60, 1520), (-20, 1100), (40, 880)])
        cx.fill()
        cx.pop_group_to_source()
        cx.paint()
        cx.restore()
        # pea flood
        rnd = random.Random(8)
        flow = smooth(prog(T, 66.75, 67.6))
        for k in range(260):
            x = rnd.uniform(-300, 1400)
            yb = 1420 + rnd.uniform(0, 600)
            hump = 230 * math.exp(-((x - 250) / 380) ** 2)
            y = yb - hump * rnd.random() * flow
            Wd.pea(cx, x, y, rnd.uniform(16, 22), 1.0, 0.6, rnd.uniform(0, 6), lw=3.5)
        # rolling peas
        for k in range(14):
            ph = (T * 0.8 + k / 14) % 1
            x = 250 + ph * 900
            y = 1500 + 200 * math.sin(k) - 120 * math.sin(math.pi * ph)
            Wd.pea(cx, x, y, 18, 1.0, 0.6, ph * 10, lw=3.5)
        poof_t = 68.55
        p = pose(600, 1640, T, s=2.4, view="front", seed=1, eyes="wide", brows="up", mouth="o", mouth_open=0.8,
                 look=(0, 0), arm_a=30, arm_b=30, elb_a=20, elb_b=20)
        if T > poof_t + 0.2:
            p = p.but(eyes="happy", mouth="smile")
        J = PRISONER.draw(cx, breathe(p, T))
        for k in range(60):
            x = rnd.uniform(380, 820)
            y = 1640 - rnd.uniform(-40, 70)
            Wd.pea(cx, x, y, rnd.uniform(16, 22), 1.0, 0.6, rnd.uniform(0, 6), lw=3.5)
        hx, hy = J["head"]
        Wd.poof(cx, hx + 120, hy + 40, prog(T, poof_t, poof_t + 0.6), 70)
        if T > poof_t + 0.1:
            k = ease_out(prog(T, poof_t + 0.1, poof_t + 0.45))
            Wd.bunny(cx, hx + 130, hy + 120, 1.5 * k, 1.0, T)


def scenes():
    return [S01Hook(), S02Peas(), S03Water(), S04Dessert(), S05LastPea(), S06Warden(), S07Double(), S08Lick(),
            S09Beanstalk(), S10Weeks(), S11Tickets(), S12Steal(), S13Stash(), S14Thirsty(), S15Bucket(), S16Bang(),
            S17Crack(), S18Swell(), S19Burst(), S20Free()]

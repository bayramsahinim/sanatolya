"""Troy cast: egg-headed characters on the Cinecode rig.

Look: warm skin, thick dark outline, skin-coloured outlined limbs, one signature accessory each.
Every character is drawn on a separate layer that later gets a cream "sticker" halo (gfx.halo).
"""
import math
import random

from cinecode import characters as ch
from cinecode.characters import Figure, Pose, Style, draw_face
from cinecode.core import OUTLINE, circle, curve, ellipse, fs, hexc, line, rrect, shade, smooth, src

SKIN = hexc("#F4CFA8")
SKIN_DK = hexc("#E2B184")
BRONZE = hexc("#D9A441")
BRONZE_DK = hexc("#A8772A")
CREAM = hexc("#F6EBD5")
INK = OUTLINE


class TroyStyle(Style):
    head_r = 52
    torso = 104
    thigh = 56
    shin = 54
    upper = 48
    fore = 46
    limb_w = 12.0
    outline_w = 5.5
    shoe = hexc("#7A4A26")

    def __init__(self, tunic="#B8322E", trim="#E9C46A", body="tunic", helmet=None, crest="#C8302B",
                 hair=None, hair_c="#3B2A20", beard=None, beard_c=None, diadem=False, cape=None,
                 mud=False, rope=False, skin=None, earrings=False, wreath=False, seed=0):
        self.tunic = hexc(tunic)
        self.trim = hexc(trim) if trim else None
        self.body = body
        self.helmet = helmet
        self.crest = hexc(crest)
        self.hair = hair
        self.hair_c = hexc(hair_c)
        self.beard = beard
        self.beard_c = hexc(beard_c) if beard_c else self.hair_c
        self.diadem = diadem
        self.cape = hexc(cape) if cape else None
        self.mud = mud
        self.rope = rope
        self.skin = hexc(skin) if skin else SKIN
        self.earrings = earrings
        self.wreath = wreath
        self.seed = seed

    # ------------------------------------------------------------ back
    def draw_back(self, cx, fig, J, p):
        if self.cape is None:
            return
        sx, sy = J["shoulder"]
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(sx, sy)
        cx.rotate(J["lean_r"])
        sway = math.sin(p.t * 3) * 4 + p.extra.get("cape_flow", 0)
        cx.move_to(-f * 8 - 32, 2)
        cx.curve_to(-f * 26 - 46, 60, -f * (36 + sway) - 48, 120, -f * (44 + sway * 2) - 36, 156)
        cx.line_to(-f * (44 + sway * 2) + 38, 158)
        cx.curve_to(-f * 26 + 42, 110, -f * 18 + 36, 50, -f * 8 + 32, 2)
        cx.close_path()
        fs(cx, self.cape, INK, self.outline_w)
        cx.restore()

    def draw_head_back(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        if self.hair == "long":
            cx.move_to(-R * 1.02, -R * 0.4)
            cx.curve_to(-R * 1.25, R * 0.6, -R * 1.1, R * 1.5, -R * 0.7, R * 1.75)
            cx.line_to(R * 0.7, R * 1.75)
            cx.curve_to(R * 1.1, R * 1.5, R * 1.25, R * 0.6, R * 1.02, -R * 0.4)
            cx.close_path()
            fs(cx, self.hair_c, INK, self.outline_w)
        elif self.hair == "wild":
            r = random.Random(7)
            for i in range(11):
                a = math.pi * (0.85 + i * 0.13)
                rr = R * (1.0 + 0.12 * r.random())
                circle(cx, math.cos(a) * rr * 1.05, math.sin(a) * rr * 0.95 + R * 0.25, 20 + 6 * r.random())
            fs(cx, self.hair_c, INK, 4.5)
        elif self.hair == "bun":
            circle(cx, -f * R * 0.75, -R * 0.95, 24)
            fs(cx, self.hair_c, INK, self.outline_w)
        cx.restore()

    # ------------------------------------------------------------ torso
    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        low = {"tunic": 40, "robe": 104, "dress": 104}[self.body]
        flare = 46 if self.body != "tunic" else 40
        cx.move_to(-30, -T + 8)
        cx.curve_to(-34, -T * 0.45, -38, 0, -flare, low)
        cx.curve_to(-16, low + 8, 16, low + 8, flare, low)
        cx.curve_to(38, 0, 34, -T * 0.45, 30, -T + 8)
        cx.curve_to(14, -T - 4, -14, -T - 4, -30, -T + 8)
        cx.close_path()
        fs(cx, self.tunic, INK, self.outline_w)
        # soft shading on the back side, highlight on the front
        cx.save()
        cx.move_to(-30, -T + 8)
        cx.curve_to(-34, -T * 0.45, -38, 0, -flare, low)
        cx.curve_to(-16, low + 8, 16, low + 8, flare, low)
        cx.curve_to(38, 0, 34, -T * 0.45, 30, -T + 8)
        cx.curve_to(14, -T - 4, -14, -T - 4, -30, -T + 8)
        cx.close_path()
        cx.clip()
        fsgn = p.f if p.view == "side" else 1
        cx.rectangle(-60 if fsgn > 0 else 14, -T - 10, 46, T + low + 20)
        src(cx, shade(self.tunic, -0.22), 0.55)
        cx.fill()
        if self.trim is not None:
            cx.rectangle(-60, low - 12, 120, 20)
            src(cx, self.trim)
            cx.fill()
        if self.mud:
            r = random.Random(3)
            for _ in range(7):
                ellipse(cx, r.uniform(-34, 34), r.uniform(-T * 0.6, low - 6), r.uniform(5, 11), r.uniform(4, 8))
                src(cx, hexc("#6B4E2E"), 0.75)
                cx.fill()
        cx.restore()
        # belt
        if self.body == "tunic" or self.helmet:
            rrect(cx, -36, -18, 72, 12, 4)
            fs(cx, hexc("#6B4428"), INK, 3.2)
        if self.body == "robe" and self.trim is not None:
            line(cx, [(-24, -T + 6), (30, low - 14)], self.trim, 7)
        if self.helmet:
            # bronze breastplate
            cx.move_to(-31, -T + 10)
            cx.curve_to(-33, -T * 0.5, -32, -40, -30, -20)
            cx.line_to(30, -20)
            cx.curve_to(32, -40, 33, -T * 0.5, 31, -T + 10)
            cx.curve_to(12, -T - 2, -12, -T - 2, -31, -T + 10)
            cx.close_path()
            fs(cx, BRONZE, INK, 4.5)
            curve(cx, (-16, -T + 30), (-8, -T + 40), (8, -T + 40), (16, -T + 30), BRONZE_DK, 3.5)
            line(cx, [(0, -T + 44), (0, -28)], BRONZE_DK, 3)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.45, sy + (ey - sy) * 0.45
        line(cx, [(sx, sy), (mx, my)], INK, 30)
        line(cx, [(sx, sy), (mx, my)], self.tunic, 20)

    def draw_shoe(self, cx, foot, dirx, p):
        cx.save()
        cx.translate(*foot)
        cx.scale(dirx, 1)
        rrect(cx, -10, -7, 32, 12, 6)
        fs(cx, self.shoe, INK, 3.5)
        line(cx, [(-2, -7), (4, -20)], self.shoe, 3)
        cx.restore()

    # ------------------------------------------------------------ head front
    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        if self.beard:
            big = self.beard == "full"
            cx.move_to(-R * 0.86, R * 0.05)
            if big:
                cx.curve_to(-R * 0.95, R * 1.3, -R * 0.3, R * 1.85, f * R * 0.1, R * 1.95)
                cx.curve_to(R * 0.3, R * 1.85, R * 0.95, R * 1.3, R * 0.86, R * 0.05)
            else:
                cx.curve_to(-R * 0.8, R * 0.95, -R * 0.3, R * 1.25, f * R * 0.1, R * 1.25)
                cx.curve_to(R * 0.3, R * 1.25, R * 0.8, R * 0.95, R * 0.86, R * 0.05)
            cx.curve_to(R * 0.5, R * 0.5, -R * 0.5, R * 0.5, -R * 0.86, R * 0.05)
            cx.close_path()
            fs(cx, self.beard_c, INK, 4.5)
            if self.beard == "curly":
                for i in range(5):
                    circle(cx, -R * 0.5 + i * R * 0.25 + f * 8, R * 0.95 + (i % 2) * 8, 6)
                    fs(cx, None, shade(self.beard_c, -0.3), 3)
            # mustache + mouth on top of the beard
            mx = f * R * 0.22 * 1.1
            curve(cx, (mx - 24, R * 0.42), (mx - 10, R * 0.30), (mx + 10, R * 0.30), (mx + 24, R * 0.42),
                  shade(self.beard_c, -0.25), 9)
            ch._mouth(cx, mx, R * 0.52, p.mouth, p.mouth_open, f)
        if self.hair in ("short", "long", "bun", "wild"):
            cx.move_to(-R * 1.0, -R * 0.15)
            cx.curve_to(-R * 1.05, -R * 1.3, R * 1.05, -R * 1.3, R * 1.0, -R * 0.15)
            cx.curve_to(R * 0.6, -R * 0.62, -R * 0.2, -R * 0.75, -R * 1.0, -R * 0.15)
            cx.close_path()
            fs(cx, self.hair_c, INK, self.outline_w)
        elif self.hair == "curly":
            for i in range(8):
                a = math.pi * (1.0 + i * 0.143)
                circle(cx, math.cos(a) * R * 0.92, math.sin(a) * R * 0.98, 15)
            fs(cx, self.hair_c, INK, 4)
        elif self.hair == "bald":
            ellipse(cx, -R * 0.35, -R * 0.75, 12, 6, -0.5)
            src(cx, (1, 1, 1, 0.55))
            cx.fill()
            for sgn in (-1, 1):
                ellipse(cx, sgn * R * 0.92, -R * 0.1, 12, 22)
                fs(cx, self.hair_c, INK, 4)
        if self.diadem:
            cx.move_to(-R * 0.85, -R * 0.62)
            cx.curve_to(-R * 0.3, -R * 0.95, R * 0.3, -R * 0.95, R * 0.85, -R * 0.62)
            src(cx, INK)
            cx.set_line_width(13)
            cx.stroke_preserve()
            src(cx, BRONZE)
            cx.set_line_width(8)
            cx.stroke()
            circle(cx, f * R * 0.2, -R * 0.92, 9)
            fs(cx, hexc("#5BC0EB"), INK, 3)
        if self.wreath:
            for i in range(9):
                a = math.pi * (1.08 + i * 0.105)
                ellipse(cx, math.cos(a) * R * 0.98, math.sin(a) * R * 0.98, 13, 7, a + 1.2)
                fs(cx, hexc("#7DB26A"), INK, 3)
        if self.earrings:
            for sgn in (-1, 1):
                circle(cx, sgn * R * 0.9, R * 0.35, 7)
                fs(cx, BRONZE, INK, 2.5)
        if self.helmet:
            self._helmet(cx, R, f, p)
        cx.restore()

    def _helmet(self, cx, R, f, p):
        # crest (horse hair) first, then the bronze bowl over it
        sway = math.sin(p.t * 5 + self.seed) * 3
        cx.move_to(-R * 0.9 - f * 10, -R * 0.7)
        cx.curve_to(-R * 0.9 - f * 20, -R * 1.85, R * 0.9 - f * 20 + sway, -R * 1.95, R * 0.95 + sway - f * 4, -R * 0.75)
        cx.curve_to(R * 0.5, -R * 1.25, -R * 0.5, -R * 1.25, -R * 0.9 - f * 10, -R * 0.7)
        cx.close_path()
        fs(cx, self.crest, INK, 4.5)
        for k in range(5):
            x = -R * 0.6 + k * R * 0.3
            line(cx, [(x, -R * 1.15), (x + 4 + sway * 0.3, -R * 1.55)], shade(self.crest, -0.25), 3)
        # bowl
        cx.move_to(-R * 1.06, -R * 0.05)
        cx.curve_to(-R * 1.12, -R * 1.3, R * 1.12, -R * 1.3, R * 1.06, -R * 0.05)
        cx.line_to(R * 0.82, -R * 0.12)
        cx.curve_to(R * 0.6, -R * 0.42, -R * 0.6, -R * 0.42, -R * 0.82, -R * 0.12)
        cx.close_path()
        fs(cx, BRONZE, INK, 5)
        ellipse(cx, -R * 0.45, -R * 0.78, 16, 7, -0.4)
        src(cx, (1, 0.96, 0.8, 0.6))
        cx.fill()
        # cheek guard on the back side
        if p.view == "side":
            gx = -f * R * 0.72
            cx.move_to(gx - 16, -R * 0.12)
            cx.line_to(gx + 16, -R * 0.12)
            cx.line_to(gx + 10, R * 0.45)
            cx.curve_to(gx, R * 0.55, gx - 12, R * 0.5, gx - 16, R * 0.4)
            cx.close_path()
            fs(cx, BRONZE, INK, 4)


class TroyFigure(Figure):
    """Egg head + skin-coloured outlined limbs."""

    def _limb(self, cx, pts):
        st = self.st
        line(cx, pts, INK, st.limb_w + 7)
        line(cx, pts, st.skin, st.limb_w)

    def _leg(self, cx, J, k, p):
        st = self.st
        hip, knee, foot = J["hip_" + k], J["knee_" + k], J["foot_" + k]
        self._limb(cx, [hip, knee, foot])
        f = 1 if p.f >= 0 else -1
        if p.view == "front":
            f = -1 if k == "a" else 1
        st.draw_shoe(cx, foot, f, p)

    def _arm(self, cx, J, k, p):
        st = self.st
        sh, el, ha = J["sh_" + k], J["elb_" + k], J["hand_" + k]
        self._limb(cx, [sh, el, ha])
        st.sleeve(cx, sh, el, p)
        circle(cx, ha[0], ha[1], st.limb_w * 0.95)
        fs(cx, st.skin, INK, 3.5)
        if getattr(st, "rope", False) and k == "b":
            circle(cx, ha[0], ha[1] - 6, st.limb_w * 0.9)
            fs(cx, None, hexc("#C9A66B"), 5)

    def _head(self, cx, J, p):
        st = self.st
        R = st.head_r
        hx, hy = J["head"]
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # egg: slightly taller than wide, fuller at the bottom
        cx.move_to(0, -R * 1.08)
        cx.curve_to(R * 0.78, -R * 1.08, R * 1.02, -R * 0.35, R * 1.0, R * 0.18)
        cx.curve_to(R * 0.98, R * 0.78, R * 0.55, R * 1.02, 0, R * 1.02)
        cx.curve_to(-R * 0.55, R * 1.02, -R * 0.98, R * 0.78, -R * 1.0, R * 0.18)
        cx.curve_to(-R * 1.02, -R * 0.35, -R * 0.78, -R * 1.08, 0, -R * 1.08)
        cx.close_path()
        fs(cx, st.skin, INK, st.outline_w)
        # cheek blush + nose
        f = p.f if p.view == "side" else 0
        for side in (-1, 1):
            ellipse(cx, f * R * 0.2 + side * R * 0.5, R * 0.32, 12, 7)
            src(cx, hexc("#F29A86"), 0.45)
            cx.fill()
        if p.view == "side":
            ellipse(cx, f * R * 0.95, R * 0.12, 10, 11)
            fs(cx, st.skin, INK, 3.5)
        cx.restore()
        draw_face(cx, J, p, R, st)
        st.draw_head_front(cx, self, J, p)
        if p.sweat > 0:
            fx = p.f if p.view == "side" else 1
            cx.save()
            cx.translate(hx, hy)
            cx.rotate(J["head_r"])
            sx, sy = -fx * R * 0.85, -R * 0.35 + 14 * smooth(p.sweat)
            cx.move_to(sx, sy - 16)
            cx.curve_to(sx + 10, sy - 2, sx + 10, sy + 8, sx, sy + 8)
            cx.curve_to(sx - 10, sy + 8, sx - 10, sy - 2, sx, sy - 16)
            src(cx, hexc("#8FD3FF"), p.sweat)
            cx.fill_preserve()
            src(cx, INK, p.sweat)
            cx.set_line_width(3)
            cx.stroke()
            cx.restore()


# ------------------------------------------------------------------ cast
def trojan_soldier(seed=0):
    return TroyFigure(TroyStyle(tunic=["#B8322E", "#A92B2B", "#C0392B"][seed % 3], trim="#E9C46A",
                                helmet=True, crest="#D7263D", seed=seed), seed=20 + seed)


def greek_soldier(seed=0, **kw):
    d = dict(tunic=["#2E6FB8", "#2B5DA9", "#3A7BC8"][seed % 3], trim="#F1F1F1", helmet=True, crest="#2D9CDB",
             seed=seed)
    d.update(kw)
    return TroyFigure(TroyStyle(**d), seed=40 + seed)


def trojan_citizen(seed=0):
    r = random.Random(seed * 31 + 5)
    female = r.random() < 0.45
    pal = ["#C9533A", "#E0A84A", "#6F9FC9", "#8CB369", "#D98BA0", "#B5838D", "#E8C9A0", "#7FB7BE",
           "#C97B4A", "#9C89B8"]
    return TroyFigure(TroyStyle(tunic=r.choice(pal), trim=r.choice(["#F3E3B5", "#E9C46A", None]),
                                body="dress" if female else "tunic",
                                hair=r.choice(["long", "bun"]) if female else r.choice(["short", "curly", "bald"]),
                                hair_c=r.choice(["#3B2A20", "#5A3A26", "#2A1E18", "#7A5230", "#B9B4AE"]),
                                beard=(None if female or r.random() < 0.6 else "short"),
                                skin=r.choice(["#F4CFA8", "#E8B98E", "#D9A274", "#F6D6B6"]),
                                earrings=female and r.random() < 0.5, seed=seed), seed=60 + seed)


LAOCOON = TroyFigure(TroyStyle(tunic="#F2EEE4", trim="#D4A72C", body="robe", hair="bald", hair_c="#E8E8E8",
                               beard="full", beard_c="#F4F4F4", skin="#EDC39B", wreath=True, seed=1), seed=1)
SINON = TroyFigure(TroyStyle(tunic="#9A7B55", trim=None, body="tunic", hair="wild", hair_c="#4A3322",
                             beard=None, mud=True, rope=True, skin="#E7BB91", seed=2), seed=2)
CASSANDRA = TroyFigure(TroyStyle(tunic="#7B3FA0", trim="#E9C46A", body="dress", hair="wild", hair_c="#24161C",
                                 earrings=True, skin="#E9BE97", seed=3), seed=3)
HELEN = TroyFigure(TroyStyle(tunic="#F7E7EF", trim="#E0B04A", body="dress", hair="long", hair_c="#E8B64C",
                             diadem=True, earrings=True, skin="#F7D6B7", seed=4), seed=4)
ODYSSEUS = TroyFigure(TroyStyle(tunic="#24508F", trim="#F1F1F1", helmet=True, crest="#2D9CDB",
                                beard="curly", beard_c="#3A2618", seed=5), seed=5)
ANTICLUS = TroyFigure(TroyStyle(tunic="#3A7BC8", trim="#F1F1F1", helmet=True, crest="#56CCF2", seed=6,
                                skin="#F6D6B6"), seed=6)


def pose(x, y, t, s=1.0, seed=0, **kw):
    d = dict(x=x, y=y, s=s, t=t, blink_seed=seed)
    d.update(kw)
    return Pose(**d)


walk, run, breathe, talk = ch.walk, ch.run, ch.breathe, ch.talk

"""Cast for the dry-peas prison episode, all in the Just Needy visual language:
round white heads, solid black oval eyes, short brows, small mouths, black stick limbs,
clean dark outlines. Wardrobe is what tells them apart.

* PRISONER - the official Just Needy character, in an orange prison uniform instead of the hoodie.
  pose.extra["thin"] (0..1) = "skin and bones" late in the story.
* GUARD_A (moustache), GUARD_B (clean-shaven, round belly) - olive uniforms, peaked caps.
* WARDEN - red coat, gold epaulettes, bicorne, white mutton chops, key ring.
* GENT, LADY - ticket-buying visitors.
"""
import math

from cinecode.characters import Figure, Pose, Style
from cinecode.core import OUTLINE, circle, curve, ellipse, fs, hexc, line, rrect, shade, src

ORANGE = hexc("#F07A1E")
ORANGE_DK = hexc("#C95E10")
ORANGE_LT = hexc("#FF9A45")


def _lean(cx, J):
    cx.translate(*J["hip"])
    cx.rotate(J["lean_r"])


class PrisonerStyle(Style):
    """Just Needy: plain white round head, black oval eyes, black limbs; orange prison uniform."""
    dot_eyes = True
    head_r = 57
    torso = 112
    shoe = hexc("#2b2b33")

    def _hw(self, p):
        return 36 - 11 * p.extra.get("thin", 0.0)

    def body_path(self, cx, hw, T):
        cx.move_to(-hw + 1, 2)
        cx.line_to(-hw + 3, -T + 18)
        cx.curve_to(-hw + 3, -T + 4, -hw + 14, -T, -hw + 22, -T)
        cx.line_to(hw - 22, -T)
        cx.curve_to(hw - 14, -T, hw - 3, -T + 4, hw - 3, -T + 18)
        cx.line_to(hw - 1, 2)
        cx.curve_to(hw - 1, 10, hw - 6, 12, hw - 12, 12)
        cx.line_to(-hw + 12, 12)
        cx.curve_to(-hw + 6, 12, -hw + 1, 10, -hw + 1, 2)
        cx.close_path()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        thin = p.extra.get("thin", 0.0)
        hw = self._hw(p)
        cx.save()
        _lean(cx, J)
        self.body_path(cx, hw, T)
        fs(cx, ORANGE, OUTLINE, self.outline_w)
        cx.save()
        self.body_path(cx, hw, T)
        cx.clip()
        # waist band + soft side shading
        cx.rectangle(-60, -4, 120, 20)
        src(cx, ORANGE_DK)
        cx.fill()
        cx.rectangle(-60 if p.f < 0 else hw * 0.25, -T, hw * 0.75 + 4, T - 6)
        src(cx, ORANGE_LT, 0.35)
        cx.fill()
        if thin > 0:
            # loose, hanging fabric folds
            for k in (-1, 1):
                curve(cx, (k * hw * 0.5, -T + 30), (k * hw * 0.2, -T * 0.55), (k * hw * 0.6, -T * 0.35),
                      (k * hw * 0.3, -10), (*ORANGE_DK[:3], 0.7 * thin), 3)
        cx.restore()
        if p.view == "front":
            # V collar
            cx.move_to(-15, -T + 1)
            cx.line_to(0, -T + 24)
            cx.line_to(15, -T + 1)
            fs(cx, None, OUTLINE, 3.6)
            # number patch
            rrect(cx, 4, -T + 36, 24, 15, 3)
            fs(cx, hexc("#FFF4E0"), OUTLINE, 2.5)
            for k in range(3):
                line(cx, [(8 + k * 6, -T + 40), (8 + k * 6, -T + 47)], OUTLINE, 2)
            # placket buttons
            for k in range(3):
                circle(cx, 0, -T + 34 + k * 22, 2.6)
                fs(cx, ORANGE_DK, None, 0)
        else:
            f = p.f
            cx.move_to(f * 2, -T + 1)
            cx.line_to(f * 14, -T + 22)
            cx.line_to(f * 26, -T + 3)
            fs(cx, None, OUTLINE, 3.6)
            rrect(cx, f * 6 - (24 if f < 0 else 0), -T + 36, 24, 15, 3)
            fs(cx, hexc("#FFF4E0"), OUTLINE, 2.5)
            for k in range(3):
                x0 = f * 6 - (24 if f < 0 else 0)
                line(cx, [(x0 + 5 + k * 6, -T + 40), (x0 + 5 + k * 6, -T + 47)], OUTLINE, 2)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.55, sy + (ey - sy) * 0.55
        thin = p.extra.get("thin", 0.0)
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 27 - 4 * thin)
        line(cx, [(sx, sy), (mx, my)], ORANGE, 18 - 4 * thin)

    def draw_head_front(self, cx, fig, J, p):
        thin = p.extra.get("thin", 0.0)
        if thin <= 0:
            return
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        off = f * R * 0.22
        # tired eye bags + sunken cheeks
        for s in (-1, 1):
            x = off + s * R * 0.34
            curve(cx, (x - 9, 14), (x - 4, 19), (x + 4, 19), (x + 9, 14), (*OUTLINE[:3], 0.55 * thin), 2.6)
            curve(cx, (off + s * R * 0.62, 6), (off + s * R * 0.55, 20), (off + s * R * 0.56, 28),
                  (off + s * R * 0.62, 36), (*OUTLINE[:3], 0.45 * thin), 2.6)
        cx.restore()


class GuardStyle(Style):
    dot_eyes = True
    head_r = 50
    torso = 118
    limb_w = 9.5
    shoe = hexc("#1E1E22")
    coat = hexc("#6B8E3D")
    coat_dk = hexc("#4F6E2A")
    coat_lt = hexc("#86A955")
    gold = hexc("#E2B23A")

    def __init__(self, moustache=False, belly=0.0, coat=None):
        self.moustache = moustache
        self.belly = belly
        if coat:
            self.coat = hexc(coat)
            self.coat_dk = shade(self.coat, -0.25)
            self.coat_lt = shade(self.coat, 0.2)

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        hw = 38
        b = self.belly * 14
        cx.save()
        _lean(cx, J)
        cx.move_to(-hw, 10)
        cx.curve_to(-hw - 2 - b, -T * 0.35, -hw - 2, -T + 10, -hw + 18, -T)
        cx.line_to(hw - 18, -T)
        cx.curve_to(hw + 2, -T + 10, hw + 2 + b, -T * 0.35, hw, 10)
        cx.curve_to(hw * 0.4, 16, -hw * 0.4, 16, -hw, 10)
        cx.close_path()
        fs(cx, self.coat, OUTLINE, self.outline_w)
        # collar
        rrect(cx, -22, -T - 4, 44, 14, 5)
        fs(cx, self.coat_dk, OUTLINE, 3.5)
        # belt
        rrect(cx, -hw - 1 - b * 0.5, -26, 2 * hw + 2 + b, 13, 4)
        fs(cx, hexc("#2E2A26"), OUTLINE, 3)
        rrect(cx, -8, -27, 16, 15, 3)
        fs(cx, self.gold, OUTLINE, 2.5)
        # buttons
        xo = 0 if p.view == "front" else p.f * 10
        for k in range(3):
            circle(cx, xo, -T + 24 + k * 24, 4)
            fs(cx, self.gold, OUTLINE, 2)
        # pocket flaps
        if p.view == "front":
            for s in (-1, 1):
                rrect(cx, s * 22 - 10, -T + 26, 20, 9, 3)
                fs(cx, self.coat_dk, OUTLINE, 2.5)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.8, sy + (ey - sy) * 0.8
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 26)
        line(cx, [(sx, sy), (mx, my)], self.coat, 17)

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        if self.moustache:
            off = f * R * 0.22 * 1.1
            y = R * 0.30
            for s in (-1, 1):
                cx.move_to(off, y - 2)
                cx.curve_to(off + s * 10, y - 9, off + s * 22, y - 6, off + s * 26, y + 2)
                cx.curve_to(off + s * 18, y + 2, off + s * 8, y + 3, off, y + 3)
                cx.close_path()
                fs(cx, hexc("#3B2A20"), OUTLINE, 2.5)
        # peaked cap
        cx.translate(0, -R * 0.62)
        cx.move_to(-R * 0.86, 6)
        cx.line_to(-R * 1.02, -R * 0.62)
        cx.curve_to(-R * 0.6, -R * 0.86, R * 0.6, -R * 0.86, R * 1.02, -R * 0.62)
        cx.line_to(R * 0.86, 6)
        cx.close_path()
        fs(cx, self.coat_dk, OUTLINE, self.outline_w)
        rrect(cx, -R * 0.88, -8, R * 1.76, 15, 4)
        fs(cx, hexc("#2E2A26"), OUTLINE, 3)
        circle(cx, 0, -R * 0.36, 8)
        fs(cx, self.gold, OUTLINE, 2.5)
        # visor
        vx = f * R * 0.35
        cx.move_to(vx - R * 0.62, 6)
        cx.curve_to(vx - R * 0.3, 20, vx + R * 0.3, 20, vx + R * 0.62 + f * 18, 6)
        cx.close_path()
        fs(cx, hexc("#24221F"), OUTLINE, 3)
        cx.restore()


class WardenStyle(Style):
    dot_eyes = True
    head_r = 54
    torso = 132
    thigh = 56
    shin = 56
    limb_w = 10.0
    shoe = hexc("#1B1B1F")
    coat = hexc("#C73A2E")
    coat_dk = hexc("#9E2A20")
    gold = hexc("#EBBE45")

    def draw_back(self, cx, fig, J, p):
        # coat tails
        cx.save()
        _lean(cx, J)
        f = p.f if p.view == "side" else 0
        cx.move_to(-40, -20)
        cx.line_to(-44 - f * 14, 40)
        cx.curve_to(-20, 46, 20, 46, 44 - f * 14, 40)
        cx.line_to(40, -20)
        cx.close_path()
        fs(cx, self.coat_dk, OUTLINE, self.outline_w)
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        hw = 50
        cx.save()
        _lean(cx, J)
        cx.move_to(-hw + 6, 14)
        cx.curve_to(-hw - 20, -T * 0.3, -hw - 8, -T + 14, -hw + 20, -T)
        cx.line_to(hw - 20, -T)
        cx.curve_to(hw + 8, -T + 14, hw + 20, -T * 0.3, hw - 6, 14)
        cx.curve_to(hw * 0.4, 22, -hw * 0.4, 22, -hw + 6, 14)
        cx.close_path()
        fs(cx, self.coat, OUTLINE, self.outline_w)
        # white sash-front + gold buttons
        xo = 0 if p.view == "front" else p.f * 12
        line(cx, [(xo, -T + 8), (xo, 10)], self.coat_dk, 4)
        for k in range(5):
            for s in ((-1, 1) if p.view == "front" else (1,)):
                circle(cx, xo + s * 12, -T + 22 + k * 24, 4.2)
                fs(cx, self.gold, OUTLINE, 2)
        # belt
        rrect(cx, -hw - 8, -30, 2 * hw + 16, 14, 4)
        fs(cx, hexc("#2A2522"), OUTLINE, 3)
        rrect(cx, xo - 10, -32, 20, 18, 3)
        fs(cx, self.gold, OUTLINE, 2.5)
        # epaulettes
        for s in ((-1, 1) if p.view == "front" else (-p.f, p.f)):
            cx.save()
            cx.translate(s * (hw - 12), -T + 6)
            ellipse(cx, 0, 0, 24, 10)
            fs(cx, self.gold, OUTLINE, 3)
            for k in range(-3, 4):
                line(cx, [(k * 6, 8), (k * 6.5, 22)], self.gold, 3.2)
            cx.restore()
        # collar
        rrect(cx, -24, -T - 6, 48, 16, 6)
        fs(cx, self.coat_dk, OUTLINE, 3.5)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.85, sy + (ey - sy) * 0.85
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 28)
        line(cx, [(sx, sy), (mx, my)], self.coat, 19)

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # mutton chops + moustache
        for s in ((-1, 1) if p.view == "front" else (-f,)):
            cx.move_to(s * R * 0.96, -R * 0.15)
            cx.curve_to(s * R * 1.18, R * 0.25, s * R * 1.05, R * 0.75, s * R * 0.62, R * 0.70)
            cx.curve_to(s * R * 0.52, R * 0.42, s * R * 0.70, R * 0.10, s * R * 0.80, -R * 0.20)
            cx.close_path()
            fs(cx, hexc("#F4F4F2"), OUTLINE, 3)
        off = f * R * 0.24
        y = R * 0.30
        for s in (-1, 1):
            cx.move_to(off, y - 3)
            cx.curve_to(off + s * 12, y - 12, off + s * 26, y - 8, off + s * 32, y - 2)
            cx.curve_to(off + s * 22, y + 4, off + s * 8, y + 4, off, y + 2)
            cx.close_path()
            fs(cx, hexc("#F4F4F2"), OUTLINE, 2.6)
        # bicorne
        cx.translate(0, -R * 0.5)
        cx.move_to(-R * 1.35, 4)
        cx.curve_to(-R * 1.0, -R * 0.15, -R * 0.6, -R * 1.05, 0, -R * 1.05)
        cx.curve_to(R * 0.6, -R * 1.05, R * 1.0, -R * 0.15, R * 1.35, 4)
        cx.curve_to(R * 0.6, -R * 0.12, -R * 0.6, -R * 0.12, -R * 1.35, 4)
        cx.close_path()
        fs(cx, hexc("#1F1F26"), OUTLINE, self.outline_w)
        cx.move_to(-R * 1.25, -1)
        cx.curve_to(-R * 0.6, -R * 0.22, R * 0.6, -R * 0.22, R * 1.25, -1)
        src(cx, self.gold)
        cx.set_line_width(5)
        cx.stroke()
        circle(cx, f * R * 0.2, -R * 0.55, 10)
        fs(cx, hexc("#C73A2E"), OUTLINE, 2.5)
        cx.restore()
        # key ring at the hip
        kx, ky = J["hip"]
        s0 = -1 if p.view == "front" else -p.f
        cx.save()
        cx.translate(kx + s0 * 46, ky - 8)
        sw = math.sin(p.t * 5) * 0.25
        cx.rotate(sw)
        circle(cx, 0, 10, 10)
        fs(cx, None, self.gold, 3.5)
        for k, a in enumerate((-0.5, -0.1, 0.35)):
            cx.save()
            cx.translate(0, 18)
            cx.rotate(a)
            line(cx, [(0, 0), (0, 26)], self.gold, 4)
            line(cx, [(0, 20), (6, 20)], self.gold, 3)
            line(cx, [(0, 25), (5, 25)], self.gold, 3)
            cx.restore()
        cx.restore()


class GentStyle(Style):
    dot_eyes = True
    torso = 116
    suit = hexc("#6E3D8C")

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        _lean(cx, J)
        cx.move_to(-34, 30)
        cx.line_to(-36, -T + 14)
        cx.curve_to(-36, -T, -28, -T - 2, -18, -T - 2)
        cx.line_to(18, -T - 2)
        cx.curve_to(28, -T - 2, 36, -T, 36, -T + 14)
        cx.line_to(34, 30)
        cx.close_path()
        fs(cx, self.suit, OUTLINE, self.outline_w)
        cx.move_to(-14, -T)
        cx.line_to(0, -T + 40)
        cx.line_to(14, -T)
        cx.close_path()
        fs(cx, (1, 1, 1, 1), OUTLINE, 3)
        # bow tie
        cx.move_to(0, -T + 6)
        cx.line_to(-10, -T)
        cx.line_to(-10, -T + 12)
        cx.close_path()
        cx.move_to(0, -T + 6)
        cx.line_to(10, -T)
        cx.line_to(10, -T + 12)
        cx.close_path()
        fs(cx, hexc("#C73A2E"), OUTLINE, 2)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        line(cx, [shoulder, elbow], OUTLINE, 24)
        line(cx, [shoulder, elbow], self.suit, 16)

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        rrect(cx, -R * 1.0, -R * 0.95, R * 2.0, 12, 5)
        fs(cx, hexc("#1E1E24"), OUTLINE, 3.5)
        rrect(cx, -R * 0.62, -R * 2.05, R * 1.24, R * 1.15, 6)
        fs(cx, hexc("#1E1E24"), OUTLINE, 4)
        cx.rectangle(-R * 0.62, -R * 1.12, R * 1.24, 10)
        src(cx, hexc("#C73A2E"))
        cx.fill()
        cx.restore()


class LadyStyle(Style):
    dot_eyes = True
    torso = 108
    dress = hexc("#F2C230")
    hair = hexc("#F5D97A")

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        _lean(cx, J)
        cx.move_to(-28, -T + 6)
        cx.curve_to(-34, -T * 0.4, -48, 40, -56, 98)
        cx.curve_to(-20, 104, 20, 104, 56, 98)
        cx.curve_to(48, 40, 34, -T * 0.4, 28, -T + 6)
        cx.curve_to(12, -T - 4, -12, -T - 4, -28, -T + 6)
        cx.close_path()
        fs(cx, self.dress, OUTLINE, self.outline_w)
        line(cx, [(-32, -T * 0.45), (32, -T * 0.45)], hexc("#8C4FB0"), 7)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        line(cx, [shoulder, elbow], OUTLINE, 22)
        line(cx, [shoulder, elbow], self.dress, 14)

    def draw_head_back(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        for k in range(3):
            circle(cx, -f * 26 + (k - 1) * 22, -R * 0.9 - (k == 1) * 14, 24)
        fs(cx, self.hair, OUTLINE, 4)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        cx.move_to(-R - 3, -R * 0.02)
        cx.curve_to(-R - 4, -R * 1.3, R + 4, -R * 1.3, R + 3, -R * 0.02)
        cx.curve_to(R * 0.4, -R * 0.66, -R * 0.4, -R * 0.66, -R - 3, -R * 0.02)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, 4)
        cx.restore()


PRISONER = Figure(PrisonerStyle(), seed=1)
GUARD_A = Figure(GuardStyle(moustache=True), seed=5)
GUARD_B = Figure(GuardStyle(belly=1.0, coat="#5F8A45"), seed=6)
WARDEN = Figure(WardenStyle(), seed=7)
GENT = Figure(GentStyle(), seed=8)
LADY = Figure(LadyStyle(), seed=9)
LADY.st.lashes = True


def pose(x, y, t, s=2.2, seed=1, **kw):
    d = dict(x=x, y=y, s=s, t=t, blink_seed=seed)
    d.update(kw)
    return Pose(**d)

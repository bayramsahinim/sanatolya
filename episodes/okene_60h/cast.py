"""Cast for the Okene short, built on the channel stick-figure rig.

* Harrison Okene - ship's cook: warm brown head, short black hair, wet grey tank top.
* Rescue divers  - commercial diving helmet (yellow shell, faceplate showing the face),
                   black drysuit, harness, headlamp and umbilical hose.
"""
import math

import cairo

from cinecode.characters import Figure, Pose, Style
from cinecode.core import OUTLINE, circle, ellipse, fs, hexc, line, rrect, shade, src

D2R = math.pi / 180


class HarrisonStyle(Style):
    skin = hexc("#8A5A3B")
    shirt = hexc("#9AA3A6")
    shirt_dk = hexc("#737C80")
    wet = 1.0

    def draw_head_back(self, cx, fig, J, p):
        pass

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # short hair cap
        cx.save()
        circle(cx, 0, 0, R)
        cx.clip()
        f = p.f if p.view == "side" else 0
        cx.move_to(-R - 4, -R * 0.42 + (6 if f > 0 else 0))
        cx.curve_to(-R * 0.5, -R * 0.62, R * 0.5, -R * 0.62, R + 4, -R * 0.42 + (6 if f < 0 else 0))
        cx.line_to(R + 4, -R - 6)
        cx.line_to(-R - 4, -R - 6)
        cx.close_path()
        src(cx, hexc("#1d1714"))
        cx.fill()
        cx.restore()
        circle(cx, 0, 0, R)
        fs(cx, None, OUTLINE, self.outline_w)
        # wet sheen
        if self.wet:
            ellipse(cx, -R * 0.42, -R * 0.2, R * 0.12, R * 0.22, -0.5)
            src(cx, (1, 1, 1, 0.28 * self.wet))
            cx.fill()
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 34
        cx.move_to(-hw + 2, 6)
        cx.line_to(-hw + 4, -T + 22)
        cx.curve_to(-hw + 6, -T + 4, -18, -T, -14, -T)
        cx.curve_to(-10, -T + 22, 10, -T + 22, 14, -T)
        cx.curve_to(18, -T, hw - 6, -T + 4, hw - 4, -T + 22)
        cx.line_to(hw - 2, 6)
        cx.close_path()
        fs(cx, shade(self.shirt, -0.25 * self.wet), OUTLINE, self.outline_w)
        # wet darkening blotch + folds
        cx.save()
        cx.move_to(-hw + 2, 6)
        cx.line_to(-hw + 4, -T + 22)
        cx.line_to(hw - 4, -T + 22)
        cx.line_to(hw - 2, 6)
        cx.close_path()
        cx.clip()
        ellipse(cx, 6, -10, 44, 40)
        src(cx, shade(self.shirt_dk, -0.3), 0.55 * self.wet)
        cx.fill()
        cx.restore()
        line(cx, [(-12, -T * 0.55), (-4, -T * 0.45)], shade(self.shirt_dk, -0.2), 3)
        line(cx, [(10, -T * 0.3), (18, -T * 0.22)], shade(self.shirt_dk, -0.2), 3)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        pass


class DiverStyle(Style):
    """Commercial diver. The rig's white head circle is the face behind the faceplate."""
    head_r = 46
    limb = hexc("#17191d")
    limb_w = 15.0
    suit = hexc("#22252b")
    suit_lt = hexc("#3a3f48")
    shell = hexc("#E8B620")
    shell_dk = hexc("#B98A0E")
    shoe = hexc("#111215")

    def __init__(self, lamp_on=True, hose=True, shell=None):
        self.lamp_on = lamp_on
        self.hose = hose
        if shell:
            self.shell = hexc(shell)
            self.shell_dk = shade(self.shell, -0.22)

    def draw_back(self, cx, fig, J, p):
        # bailout tank on the back
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        f = p.f if p.view == "side" else 0
        if p.view == "side":
            rrect(cx, -f * 52 - 20, -self.torso + 10, 40, 92, 18)
            fs(cx, hexc("#C9CED6"), OUTLINE, 4.5)
            rrect(cx, -f * 52 - 20, -self.torso + 10, 40, 16, 8)
            fs(cx, hexc("#E04B3A"), OUTLINE, 3.5)
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 40
        rrect(cx, -hw, -T, hw * 2, T + 10, 22)
        fs(cx, self.suit, OUTLINE, 5)
        # harness straps + chest plate
        line(cx, [(-hw + 12, -T + 4), (-8, -10)], hexc("#3b3b3b"), 9)
        line(cx, [(hw - 12, -T + 4), (8, -10)], hexc("#3b3b3b"), 9)
        rrect(cx, -14, -T * 0.62, 28, 22, 5)
        fs(cx, hexc("#8c9097"), OUTLINE, 3)
        rrect(cx, -hw + 2, -14, hw * 2 - 4, 14, 5)
        fs(cx, hexc("#2e2e2e"), OUTLINE, 3)
        # suit highlight
        rrect(cx, -hw + 8, -T + 10, 14, T * 0.6, 7)
        src(cx, self.suit_lt, 0.5)
        cx.fill()
        cx.restore()

    def draw_head_back(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        f = p.f if p.view == "side" else 0
        # umbilical hose leaving the back of the helmet
        if self.hose and p.extra.get("hose", True):
            hl = p.extra.get("hose_len", 260)
            cx.move_to(-f * R * 0.9, -R * 0.4)
            cx.curve_to(-f * (R + 80), -R * 1.2, -f * (R + 140), R * 0.4 - 40, -f * (R + hl), -R * 0.8 + p.extra.get("hose_dy", 0))
            src(cx, OUTLINE)
            cx.set_line_width(17)
            cx.stroke_preserve()
            src(cx, hexc("#C9A227"))
            cx.set_line_width(10)
            cx.stroke()
        # helmet shell
        ellipse(cx, -f * 6, -4, R * 1.48, R * 1.42)
        fs(cx, self.shell, OUTLINE, 5.5)
        # shell shading
        cx.save()
        ellipse(cx, -f * 6, -4, R * 1.48, R * 1.42)
        cx.clip()
        ellipse(cx, -f * 6 + R * 0.5, R * 0.5, R * 1.4, R * 1.2)
        src(cx, self.shell_dk, 0.45)
        cx.fill()
        ellipse(cx, -f * 6 - R * 0.75, -R * 0.75, R * 0.35, R * 0.22, -0.6)
        src(cx, (1, 1, 1, 0.45))
        cx.fill()
        cx.restore()
        # neck dam / collar
        rrect(cx, -R * 1.05, R * 1.05, R * 2.1, R * 0.42, 10)
        fs(cx, hexc("#2b2b2b"), OUTLINE, 4)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        f = p.f if p.view == "side" else 0
        # faceplate frame ring
        circle(cx, 0, 0, R + 7)
        src(cx, hexc("#2a2c30"))
        cx.set_line_width(12)
        cx.stroke()
        circle(cx, 0, 0, R + 7)
        fs(cx, None, OUTLINE, 3)
        # glass glare
        cx.save()
        circle(cx, 0, 0, R)
        cx.clip()
        cx.move_to(-R, -R * 0.2)
        cx.line_to(-R * 0.2, -R)
        cx.line_to(R * 0.1, -R)
        cx.line_to(-R, R * 0.1)
        cx.close_path()
        src(cx, (0.8, 0.95, 1.0, 0.35))
        cx.fill()
        cx.restore()
        # regulator block under the faceplate
        rrect(cx, -R * 0.35 + f * 10, R * 0.95, R * 0.7, R * 0.42, 8)
        fs(cx, hexc("#3a3d42"), OUTLINE, 3.5)
        # side lamp
        lx = (R * 1.25) * (1 if f >= 0 else -1)
        rrect(cx, lx - 14, -R * 0.95, 28, 34, 8)
        fs(cx, hexc("#2f3237"), OUTLINE, 3.5)
        circle(cx, lx, -R * 0.95 + 17, 9)
        fs(cx, (1, 0.97, 0.85, 1) if self.lamp_on else hexc("#555555"), OUTLINE, 2.5)
        cx.restore()

    def draw_shoe(self, cx, foot, dirx, p):
        cx.save()
        cx.translate(*foot)
        cx.scale(dirx, 1)
        rrect(cx, -12, -12, 40, 20, 8)
        fs(cx, self.shoe, OUTLINE, 3.5)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        pass


HARRISON_ST = HarrisonStyle()
HARRISON = Figure(HARRISON_ST, seed=5)
DIVER_ST = DiverStyle()
DIVER = Figure(DIVER_ST, seed=6)
DIVER2 = Figure(DiverStyle(shell="#E07B22"), seed=7)


def harrison(x, y, t, **kw):
    d = dict(x=x, y=y, s=1.0, t=t, blink_seed=5, mouth="flat", brows="worried")
    d.update(kw)
    return Pose(**d)


def diver(x, y, t, **kw):
    d = dict(x=x, y=y, s=1.0, t=t, blink_seed=6, mouth="flat", brows="flat", eyes="open")
    d.update(kw)
    return Pose(**d)


def lamp_point(J, p, st=DIVER_ST):
    """screen position of the diver's helmet lamp (after Figure.draw)."""
    hx, hy = J["head"]
    R = st.head_r * p.s
    f = 1 if (p.f >= 0 or p.view != "side") else -1
    a = J.get("head_r_w", 0.0)
    return hx + f * R * 1.25, hy - R * 0.95 + 17 * p.s


# ------------------------------------------------------------------ close-up hands
def glove_hand(cx, x, y, s=1.0, rot=0.0, grip=0.0, color="#16181c"):
    """Big diver's glove for the hand-grab insert. Fingers point along +x."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    c = hexc(color)
    # cuff / sleeve back to the left
    rrect(cx, -420, -70, 360, 140, 40)
    fs(cx, hexc("#22252b"), OUTLINE, 7)
    rrect(cx, -90, -78, 40, 156, 14)
    fs(cx, hexc("#3b3f46"), OUTLINE, 6)
    # palm
    rrect(cx, -60, -80, 150, 160, 60)
    fs(cx, c, OUTLINE, 7)
    # fingers (curl with grip)
    for i, fy in enumerate((-54, -18, 18, 52)):
        ln = (95 - abs(i - 1.5) * 12) * (1 - 0.45 * grip)
        rrect(cx, 70, fy - 17, ln, 34, 17)
        fs(cx, shade(c, 0.08), OUTLINE, 6)
    # thumb
    cx.save()
    cx.translate(30, -70)
    cx.rotate(-0.9 + grip * 0.5)
    rrect(cx, 0, -16, 80, 32, 16)
    fs(cx, shade(c, 0.08), OUTLINE, 6)
    cx.restore()
    # rubber texture highlight
    rrect(cx, -40, -60, 90, 22, 11)
    src(cx, (1, 1, 1, 0.08))
    cx.fill()
    cx.restore()


def bare_hand(cx, x, y, s=1.0, rot=0.0, grip=0.0, skin="#8A5A3B", spread=0.0):
    """Harrison's hand (cartoon, 4 fingers). Fingers point along +x; forearm to -x."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(s, s)
    c = hexc(skin)
    # forearm (thin like the rig's limbs, but at close-up scale)
    rrect(cx, -620, -34, 600, 68, 34)
    fs(cx, c, OUTLINE, 7)
    # palm
    ellipse(cx, 30, 0, 78, 70)
    fs(cx, c, OUTLINE, 7)
    for i, fy in enumerate((-48, -16, 16, 46)):
        ln = (100 - abs(i - 1.5) * 14) * (1 - 0.55 * grip)
        ang = (i - 1.5) * 0.18 * spread
        cx.save()
        cx.translate(80, fy * (1 + 0.3 * spread))
        cx.rotate(ang + grip * 0.9)
        rrect(cx, -10, -15, ln + 10, 30, 15)
        fs(cx, shade(c, 0.05), OUTLINE, 6)
        cx.restore()
    cx.save()
    cx.translate(20, -58)
    cx.rotate(-1.0 + grip * 0.7)
    rrect(cx, 0, -15, 78, 30, 15)
    fs(cx, shade(c, 0.05), OUTLINE, 6)
    cx.restore()
    # wrinkled, water-logged highlight
    ellipse(cx, 10, -20, 30, 12, -0.3)
    src(cx, (1, 1, 1, 0.12))
    cx.fill()
    cx.restore()

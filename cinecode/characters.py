"""Stick-figure character rig shared by every character in the channel.

Coordinates: a Figure is drawn with its origin on the ground between the feet.
Angles are in degrees measured from straight down; positive = toward the
direction the figure faces ("forward"). Arms are posed in world angles.
"""
import math
import random
from dataclasses import dataclass, field, replace

from .core import (OUTLINE, circle, clamp, curve, ellipse, fs, hexc, line, poly, rrect,
                   shade, smooth, smooth_poly, src)

D2R = math.pi / 180


# ------------------------------------------------------------------ pose
@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    s: float = 1.0          # overall scale
    f: float = 1.0          # facing: +1 right, -1 left
    view: str = "side"      # "side" | "front"
    lean: float = 0.0       # torso lean (deg, + forward)
    bob: float = 0.0        # vertical body offset (px, + down)
    squash: float = 1.0     # vertical squash of whole body
    # legs: hip angle, knee bend
    hip_a: float = -4.0
    knee_a: float = 4.0
    hip_b: float = 4.0
    knee_b: float = 4.0
    foot_a: float = 0.0     # lift foot (px) - used when sitting etc.
    # arms: shoulder angle, elbow bend
    arm_a: float = 12.0
    elb_a: float = 10.0
    arm_b: float = -10.0
    elb_b: float = 10.0
    # head
    tilt: float = 0.0
    head_dy: float = 0.0
    # face
    eyes: str = "open"
    look: tuple = (0.0, 0.0)
    brows: str = "neutral"
    mouth: str = "smile"
    mouth_open: float = 1.0
    blink_seed: int = 0
    t: float = 0.0          # time, for auto blink
    blink: bool = True
    sweat: float = 0.0      # 0..1 sweat drop
    blush: float = 0.0
    alpha: float = 1.0
    extra: dict = field(default_factory=dict)

    def but(self, **kw):
        return replace(self, **kw)


# ------------------------------------------------------------------ styles
class Style:
    head_r = 50
    torso = 112
    thigh = 58
    shin = 58
    upper = 50
    fore = 48
    limb_w = 9.0
    shoulder_w = 30
    hip_w = 30
    skin = (1, 1, 1, 1)
    limb = OUTLINE
    shoe = hexc("#2b2b33")
    outline_w = 5.0
    lashes = False

    def draw_back(self, cx, fig, J, p):
        pass

    def draw_torso(self, cx, fig, J, p):
        pass

    def draw_head_back(self, cx, fig, J, p):
        pass

    def draw_head_front(self, cx, fig, J, p):
        pass

    def draw_shoe(self, cx, foot, dirx, p):
        cx.save()
        cx.translate(*foot)
        cx.scale(dirx, 1)
        rrect(cx, -9, -9, 33, 15, 7)
        fs(cx, self.shoe, OUTLINE, 3.5)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        pass


def _rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


class HeroStyle(Style):
    """The Just Needy guy: plain white head, blue hoodie, black stick limbs."""
    blue = hexc("#2F6FDB")
    blue_dk = hexc("#2257B5")
    blue_lt = hexc("#4A86EA")
    shoe = hexc("#2b2b33")
    robe = None  # set to a colour to wear the ceremonial robe over the hoodie

    def torso_path(self, cx, p, hw_s, hw_h, T):
        cx.move_to(-hw_h, 0)
        cx.line_to(-hw_s + 2, -T + 16)
        cx.curve_to(-hw_s + 2, -T + 2, -hw_s + 12, -T, -hw_s + 20, -T)
        cx.line_to(hw_s - 20, -T)
        cx.curve_to(hw_s - 12, -T, hw_s - 2, -T + 2, hw_s - 2, -T + 16)
        cx.line_to(hw_h, 0)
        cx.curve_to(hw_h, 6, hw_h - 4, 8, hw_h - 10, 8)
        cx.line_to(-hw_h + 10, 8)
        cx.curve_to(-hw_h + 4, 8, -hw_h, 6, -hw_h, 0)
        cx.close_path()

    def draw_head_back(self, cx, fig, J, p):
        # hood bunched behind the neck
        hx, hy = J["neck"]
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["lean_r"])
        ellipse(cx, -f * 22, -16, 44, 26)
        fs(cx, self.blue_dk, OUTLINE, self.outline_w)
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 36
        self.torso_path(cx, p, hw, hw - 1, T)
        fs(cx, self.blue, OUTLINE, self.outline_w)
        # hem band
        cx.save()
        self.torso_path(cx, p, hw, hw - 1, T)
        cx.clip()
        cx.rectangle(-60, -6, 120, 20)
        src(cx, self.blue_dk)
        cx.fill()
        # soft highlight
        cx.rectangle(-60 if p.f < 0 else 8, -T, 52, T - 10)
        src(cx, self.blue_lt, 0.35)
        cx.fill()
        cx.restore()
        if p.view == "front":
            # kangaroo pocket
            cx.move_to(-20, -10)
            cx.line_to(-14, -38)
            cx.line_to(14, -38)
            cx.line_to(20, -10)
            fs(cx, None, shade(self.blue_dk, -0.15), 3.5)
            # drawstrings
            line(cx, [(-8, -T + 4), (-10, -T + 34)], hexc("#F2F2F2"), 3.5)
            line(cx, [(8, -T + 4), (10, -T + 34)], hexc("#F2F2F2"), 3.5)
        else:
            f = p.f
            cx.move_to(f * 4, -12)
            cx.line_to(f * 8, -40)
            cx.line_to(f * 30, -40)
            fs(cx, None, shade(self.blue_dk, -0.15), 3.5)
            line(cx, [(f * 18, -T + 6), (f * 20, -T + 36)], hexc("#F2F2F2"), 3.5)
        if self.robe is not None:
            # oversized ceremonial robe draped over the hoodie
            cx.move_to(-hw - 8, -T + 6)
            cx.curve_to(-hw - 20, -T * 0.4, -hw - 30, 20, -hw - 26, 70)
            cx.line_to(hw + 26, 70)
            cx.curve_to(hw + 30, 20, hw + 20, -T * 0.4, hw + 8, -T + 6)
            cx.curve_to(hw * 0.4, -T - 6, -hw * 0.4, -T - 6, -hw - 8, -T + 6)
            cx.close_path()
            fs(cx, self.robe, OUTLINE, self.outline_w)
            # gold trim
            line(cx, [(-hw - 22, 62), (hw + 22, 62)], hexc("#E9B949"), 6)
            # open front showing hoodie
            cx.move_to(-12, -T + 4)
            cx.line_to(-18, 64)
            cx.line_to(18, 64)
            cx.line_to(12, -T + 4)
            cx.close_path()
            fs(cx, self.blue, OUTLINE, 3.5)
            line(cx, [(-12, -T + 4), (-18, 62)], hexc("#E9B949"), 5)
            line(cx, [(12, -T + 4), (18, 62)], hexc("#E9B949"), 5)
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        # short hoodie sleeve cap
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.5, sy + (ey - sy) * 0.5
        col = self.robe if self.robe is not None else self.blue
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 27)
        line(cx, [(sx, sy), (mx, my)], col, 18)


class RomanSoldierStyle(Style):
    head_r = 50
    torso = 126
    thigh = 64
    shin = 62
    upper = 56
    fore = 52
    limb_w = 11.0
    shoe = hexc("#6B4428")
    tunic = hexc("#B8322E")
    armor = hexc("#A7B0BA")
    armor_dk = hexc("#7D8792")
    bronze = hexc("#C99A3E")
    cape = hexc("#8E1F23")
    crest = True
    wet = 0.0

    def __init__(self, crest=True, cape=True, wet=0.0, helmet=True):
        self.crest = crest
        self.has_cape = cape
        self.wet = wet
        self.helmet = helmet

    def _w(self, c):
        return shade(c, -0.25 * self.wet) if self.wet else c

    def draw_back(self, cx, fig, J, p):
        if not self.has_cape:
            return
        sx, sy = J["shoulder"]
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(sx, sy)
        cx.rotate(J["lean_r"])
        sway = math.sin(p.t * 3) * 4 + p.extra.get("cape_flow", 0)
        cx.move_to(-f * 10 - 34, 4)
        cx.curve_to(-f * 30 - 50, 60, -f * (40 + sway) - 52, 130, -f * (48 + sway * 2) - 38, 170)
        cx.line_to(-f * (48 + sway * 2) + 40, 172)
        cx.curve_to(-f * 30 + 44, 120, -f * 20 + 38, 50, -f * 10 + 34, 4)
        cx.close_path()
        fs(cx, self._w(self.cape), OUTLINE, self.outline_w)
        cx.restore()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw = 46
        # tunic skirt + leather strips
        cx.move_to(-hw + 2, -10)
        cx.line_to(-hw - 6, 44)
        cx.curve_to(-hw / 2, 50, hw / 2, 50, hw + 6, 44)
        cx.line_to(hw - 2, -10)
        cx.close_path()
        fs(cx, self._w(self.tunic), OUTLINE, self.outline_w)
        for i in range(-3, 4):
            x = i * 12
            rrect(cx, x - 5, -4, 10, 40, 3)
            fs(cx, self._w(hexc("#7A4E2D")), OUTLINE, 3)
        # armour body
        cx.move_to(-hw, 0)
        cx.line_to(-hw - 2, -T + 22)
        cx.curve_to(-hw - 2, -T + 2, -hw + 18, -T - 2, -hw + 28, -T - 2)
        cx.line_to(hw - 28, -T - 2)
        cx.curve_to(hw - 18, -T - 2, hw + 2, -T + 2, hw + 2, -T + 22)
        cx.line_to(hw, 0)
        cx.close_path()
        fs(cx, self._w(self.armor), OUTLINE, self.outline_w)
        # segmented bands
        for k in range(1, 5):
            y = -k * 22
            line(cx, [(-hw + 2, y), (hw - 2, y)], self._w(self.armor_dk), 4)
        # shoulder plates
        for sxn in (-1, 1):
            ellipse(cx, sxn * (hw - 6), -T + 8, 22, 15)
            fs(cx, self._w(self.armor), OUTLINE, 4)
        # belt
        rrect(cx, -hw - 1, -14, 2 * hw + 2, 14, 4)
        fs(cx, self._w(hexc("#6B4428")), OUTLINE, 3.5)
        circle(cx, 0, -7, 6)
        fs(cx, self.bronze, OUTLINE, 2.5)
        # red neck scarf
        ellipse(cx, 0, -T + 2, 30, 10)
        fs(cx, self._w(self.tunic), OUTLINE, 3.5)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        if not self.helmet:
            if self.wet:
                # soggy hair
                hx, hy = J["head"]
                R = self.head_r
                cx.save()
                cx.translate(hx, hy)
                cx.rotate(J["head_r"])
                cx.arc(0, 0, R, math.pi * 1.08, math.pi * 1.92)
                cx.curve_to(R * 0.4, -R * 0.55, -R * 0.4, -R * 0.55, -R * 0.9, -R * 0.4)
                fs(cx, hexc("#3B2A20"), OUTLINE, 4)
                cx.restore()
            return
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        if p.extra.get("helmet_off", 0) > 0:
            cx.translate(0, -p.extra["helmet_off"])
        cx.translate(0, -R * 0.2)  # sit high enough that the brows stay visible
        # crest (behind dome)
        if self.crest:
            red = self._w(hexc("#C8322B"))
            if p.view == "side":
                cx.move_to(-f * 50, -R * 0.78)
                cx.curve_to(-f * 70, -R * 1.95, f * 46, -R * 2.15, f * 50, -R * 0.92)
                cx.curve_to(f * 20, -R * 1.05, -f * 20, -R * 1.0, -f * 50, -R * 0.78)
                cx.close_path()
                fs(cx, red, OUTLINE, self.outline_w)
                for i in range(6):
                    a = 0.1 + i * 0.16
                    x0 = -f * 44 + f * 90 * a
                    top = -R * (1.25 + 0.55 * math.sin(math.pi * a))
                    line(cx, [(x0, -R * 0.98), (x0 - f * 8, top)], shade(red, -0.3), 3)
            else:
                rrect(cx, -15, -R * 2.0, 30, R * 1.3, 13)
                fs(cx, red, OUTLINE, self.outline_w)
            rrect(cx, -9, -R * 1.18, 18, 16, 4)
            fs(cx, self.bronze, OUTLINE, 3)
        # dome
        cx.move_to(-R - 5, -R * 0.62)
        cx.curve_to(-R - 2, -R * 1.5, R + 2, -R * 1.5, R + 5, -R * 0.62)
        cx.close_path()
        fs(cx, self._w(self.armor), OUTLINE, self.outline_w)
        ellipse(cx, -R * 0.35, -R * 0.98, 12, 6, -0.4)
        fs(cx, (1, 1, 1, 0.45), None, 0)
        # brim
        rrect(cx, -R - 10, -R * 0.8, 2 * R + 20, 12, 6)
        fs(cx, self.bronze, OUTLINE, 4)
        if p.view == "side":
            # neck guard
            cx.move_to(-f * (R + 2), -R * 0.5)
            cx.line_to(-f * (R + 26), -R * 0.12)
            cx.line_to(-f * (R - 2), -R * 0.1)
            cx.close_path()
            fs(cx, self._w(self.armor), OUTLINE, 4)
        # cheek guards
        for sx in ((-1, 1) if p.view == "front" else (-f,)):
            cx.move_to(sx * (R - 1), -R * 0.62)
            cx.line_to(sx * (R + 3), R * 0.38)
            cx.curve_to(sx * (R - 1), R * 0.56, sx * (R - 12), R * 0.54, sx * (R - 14), R * 0.4)
            cx.line_to(sx * (R - 16), -R * 0.62)
            cx.close_path()
            fs(cx, self.bronze, OUTLINE, 4)
        cx.restore()


class LuciaStyle(Style):
    head_r = 48
    torso = 108
    thigh = 56
    shin = 56
    limb_w = 8.5
    lashes = True
    dress = hexc("#5E9A6E")
    dress_dk = hexc("#477C55")
    apron = hexc("#F4E7C9")
    hair = hexc("#4A2E22")
    scarf = hexc("#D2693C")
    shoe = hexc("#7A4E2D")
    floury = 0.0

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        sway = math.sin(p.t * 2.2) * 2
        cx.move_to(-30, -T + 6)
        cx.curve_to(-34, -T * 0.4, -44, 30, -52 + sway, 92)
        cx.curve_to(-20, 98, 20, 98, 52 + sway, 92)
        cx.curve_to(44, 30, 34, -T * 0.4, 30, -T + 6)
        cx.curve_to(14, -T - 4, -14, -T - 4, -30, -T + 6)
        cx.close_path()
        fs(cx, self.dress, OUTLINE, self.outline_w)
        # apron
        f = p.f if p.view == "side" else 0
        ax = f * 10
        cx.move_to(ax - 22, -T * 0.42)
        cx.line_to(ax - 30, 80)
        cx.curve_to(ax - 10, 86, ax + 10, 86, ax + 30, 80)
        cx.line_to(ax + 22, -T * 0.42)
        cx.close_path()
        fs(cx, self.apron, OUTLINE, 3.5)
        if self.floury:
            for i in range(6):
                circle(cx, ax - 14 + i * 6, 20 + (i * 37 % 30), 3)
                fs(cx, (1, 1, 1, 0.8), None, 0)
        # belt cord
        line(cx, [(-32, -T * 0.42), (32, -T * 0.42)], self.scarf, 6)
        cx.restore()

    def draw_head_back(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # bun
        circle(cx, -f * 30, -R * 0.85, 26)
        fs(cx, self.hair, OUTLINE, self.outline_w)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # hair cap
        cx.move_to(-R - 2, -R * 0.05)
        cx.curve_to(-R - 4, -R * 1.25, R + 4, -R * 1.25, R + 2, -R * 0.05)
        cx.curve_to(R * 0.5, -R * 0.62, -R * 0.5, -R * 0.62, -R - 2, -R * 0.05)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, self.outline_w)
        # scarf band
        cx.move_to(-R * 0.86, -R * 0.52)
        cx.curve_to(-R * 0.5, -R * 0.86, R * 0.5, -R * 0.86, R * 0.86, -R * 0.52)
        src(cx, OUTLINE)
        cx.set_line_width(16)
        cx.stroke()
        cx.move_to(-R * 0.86, -R * 0.52)
        cx.curve_to(-R * 0.5, -R * 0.86, R * 0.5, -R * 0.86, R * 0.86, -R * 0.52)
        src(cx, self.scarf)
        cx.set_line_width(9)
        cx.stroke()
        # earrings
        for sx in ((-1, 1) if p.view == "front" else (-f,)):
            circle(cx, sx * (R - 4), R * 0.32, 5)
            fs(cx, hexc("#E9B949"), OUTLINE, 2.5)
        cx.restore()


class BoyStyle(Style):
    head_r = 52
    torso = 82
    thigh = 44
    shin = 44
    upper = 38
    fore = 36
    limb_w = 8.0
    tunic = hexc("#E8A23B")
    hair = hexc("#5A3A26")
    shoe = hexc("#7A4E2D")

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        cx.move_to(-26, -T + 6)
        cx.curve_to(-30, -T * 0.5, -36, 10, -38, 34)
        cx.curve_to(-14, 40, 14, 40, 38, 34)
        cx.curve_to(36, 10, 30, -T * 0.5, 26, -T + 6)
        cx.curve_to(12, -T - 4, -12, -T - 4, -26, -T + 6)
        cx.close_path()
        fs(cx, self.tunic, OUTLINE, self.outline_w)
        line(cx, [(-31, -8), (31, -8)], hexc("#8B5A2B"), 5)
        cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        cx.move_to(-R - 2, -R * 0.15)
        cx.curve_to(-R - 2, -R * 1.2, R + 2, -R * 1.2, R + 2, -R * 0.15)
        cx.line_to(R * 0.6, -R * 0.5)
        cx.line_to(R * 0.3, -R * 0.38)
        cx.line_to(0, -R * 0.55)
        cx.line_to(-R * 0.3, -R * 0.4)
        cx.line_to(-R * 0.6, -R * 0.52)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, self.outline_w)
        # tuft
        cx.move_to(f * 4 - 6, -R * 0.98)
        cx.curve_to(f * 8 - 4, -R * 1.4, f * 24 + 4, -R * 1.35, f * 26 + 2, -R * 1.2)
        cx.curve_to(f * 18, -R * 1.18, f * 12, -R * 1.05, f * 8 + 6, -R * 0.96)
        cx.close_path()
        fs(cx, self.hair, OUTLINE, 4)
        # freckles
        for sx in (-1, 1):
            for k in range(3):
                circle(cx, f * 8 + sx * 24 + (k - 1) * 6, 14 + (k % 2) * 4, 2)
                fs(cx, hexc("#C98A5A"), None, 0)
        cx.restore()


class RomanStyle(Style):
    """Generic Roman citizen for crowds / customers."""

    def __init__(self, seed=0, tunic=None, hair=None, female=None, toga=None, scale_body=1.0):
        r = random.Random(seed)
        pal = ["#C9533A", "#E0A84A", "#6F9FC9", "#8CB369", "#D98BA0", "#B5838D", "#E8C9A0",
               "#7FB7BE", "#C97B4A", "#9C89B8", "#F0DFB4", "#A3C4BC"]
        self.tunic_c = hexc(tunic or r.choice(pal))
        self.female = r.random() < 0.4 if female is None else female
        self.hair_kind = hair or r.choice(["short", "short", "curly", "bald", "grey"] if not self.female
                                          else ["bun", "bun", "long"])
        self.hair_c = hexc(r.choice(["#3B2A20", "#5A3A26", "#2A1E18", "#7A5230"])) \
            if self.hair_kind != "grey" else hexc("#B9B4AE")
        self.toga = (r.random() < 0.25) if toga is None else toga
        self.torso = 104 * scale_body
        self.beard = (not self.female) and r.random() < 0.3

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        low = 86 if self.female else 34
        cx.move_to(-30, -T + 6)
        cx.curve_to(-32, -T * 0.4, -38, 6, -42, low)
        cx.curve_to(-14, low + 6, 14, low + 6, 42, low)
        cx.curve_to(38, 6, 32, -T * 0.4, 30, -T + 6)
        cx.curve_to(14, -T - 4, -14, -T - 4, -30, -T + 6)
        cx.close_path()
        fs(cx, self.tunic_c, OUTLINE, self.outline_w)
        if self.toga:
            cx.move_to(-28, -T + 4)
            cx.curve_to(0, -T * 0.6, 20, -T * 0.2, 40, low - 4)
            cx.line_to(24, low)
            cx.curve_to(6, -T * 0.1, -10, -T * 0.4, -30, -T + 30)
            cx.close_path()
            fs(cx, hexc("#F3EEE2"), OUTLINE, 3.5)
            line(cx, [(-26, -T + 10), (36, low - 6)], hexc("#7E3B8A"), 4)
        else:
            line(cx, [(-32, -T * 0.32), (32, -T * 0.32)], shade(self.tunic_c, -0.35), 5)
        cx.restore()

    def draw_head_back(self, cx, fig, J, p):
        if self.hair_kind == "bun":
            hx, hy = J["head"]
            f = p.f if p.view == "side" else 0
            cx.save()
            cx.translate(hx, hy)
            cx.rotate(J["head_r"])
            circle(cx, -f * 30, -self.head_r * 0.85, 22)
            fs(cx, self.hair_c, OUTLINE, self.outline_w)
            cx.restore()
        if self.hair_kind == "long":
            hx, hy = J["head"]
            cx.save()
            cx.translate(hx, hy)
            rrect(cx, -self.head_r - 6, -self.head_r * 0.6, 2 * self.head_r + 12, self.head_r * 1.5, 22)
            fs(cx, self.hair_c, OUTLINE, self.outline_w)
            cx.restore()

    def draw_head_front(self, cx, fig, J, p):
        hx, hy = J["head"]
        R = self.head_r
        f = p.f if p.view == "side" else 0
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        k = self.hair_kind
        if k in ("short", "grey", "bun", "long"):
            cx.move_to(-R - 2, -R * 0.1)
            cx.curve_to(-R - 2, -R * 1.22, R + 2, -R * 1.22, R + 2, -R * 0.1)
            cx.curve_to(R * 0.5, -R * 0.6, -R * 0.5, -R * 0.6, -R - 2, -R * 0.1)
            cx.close_path()
            fs(cx, self.hair_c, OUTLINE, self.outline_w)
        elif k == "curly":
            for i in range(7):
                a = math.pi * (1.05 + i * 0.15)
                circle(cx, math.cos(a) * R * 0.9, math.sin(a) * R * 0.9, 14)
            fs(cx, self.hair_c, OUTLINE, 4)
        elif k == "bald":
            # laurel-free shine
            ellipse(cx, -R * 0.3, -R * 0.62, 10, 5, -0.5)
            fs(cx, (0.85, 0.88, 0.92, 1), None, 0)
        if self.beard:
            cx.move_to(-R * 0.78, R * 0.25)
            cx.curve_to(-R * 0.6, R * 1.15, R * 0.6, R * 1.15, R * 0.78, R * 0.25)
            cx.curve_to(R * 0.4, R * 0.55, -R * 0.4, R * 0.55, -R * 0.78, R * 0.25)
            cx.close_path()
            fs(cx, self.hair_c, OUTLINE, 4)
        cx.restore()


# ------------------------------------------------------------------ figure
class Figure:
    def __init__(self, style, seed=0):
        self.st = style
        self.seed = seed

    # -- kinematics -------------------------------------------------------
    def joints(self, p):
        st = self.st
        f = 1 if p.f >= 0 else -1
        lean = p.lean * D2R * f
        hip_h = st.thigh + st.shin

        def leg(hip, a, k, dx=0.0):
            a1 = a * D2R
            knee = (hip[0] + f * math.sin(a1) * st.thigh + dx, hip[1] + math.cos(a1) * st.thigh)
            a2 = (a - k) * D2R
            foot = (knee[0] + f * math.sin(a2) * st.shin, knee[1] + math.cos(a2) * st.shin)
            return knee, foot

        hip = (0.0, -hip_h + p.bob)
        J = {"lean_r": lean}
        if p.view == "front":
            ha = (hip[0] - 14, hip[1])
            hb = (hip[0] + 14, hip[1])
            fa = 1 if p.f >= 0 else -1
            # front view: legs splay sideways
            ka = (ha[0] - math.sin(p.hip_a * D2R) * st.thigh * 0.4, ha[1] + math.cos(p.hip_a * D2R) * st.thigh)
            fta = (ka[0] - math.sin((p.hip_a - p.knee_a) * D2R) * st.shin * 0.4, ka[1] + math.cos((p.hip_a - p.knee_a) * D2R) * st.shin)
            kb = (hb[0] + math.sin(p.hip_b * D2R) * st.thigh * 0.4, hb[1] + math.cos(p.hip_b * D2R) * st.thigh)
            ftb = (kb[0] + math.sin((p.hip_b - p.knee_b) * D2R) * st.shin * 0.4, kb[1] + math.cos((p.hip_b - p.knee_b) * D2R) * st.shin)
            J.update(hip_a=ha, knee_a=ka, foot_a=fta, hip_b=hb, knee_b=kb, foot_b=ftb)
        else:
            ka, fta = leg(hip, p.hip_a, p.knee_a)
            kb, ftb = leg(hip, p.hip_b, p.knee_b)
            J.update(hip_a=hip, knee_a=ka, foot_a=fta, hip_b=hip, knee_b=kb, foot_b=ftb)
        J["foot_a"] = (J["foot_a"][0], J["foot_a"][1] - p.foot_a)
        J["hip"] = hip
        sh = _rot((0, -st.torso + 8), lean)
        shoulder = (hip[0] + sh[0], hip[1] + sh[1])
        J["shoulder"] = shoulder
        nk = _rot((0, -st.torso), lean)
        J["neck"] = (hip[0] + nk[0], hip[1] + nk[1])
        hr = lean * 0.6 + p.tilt * D2R * f
        J["head_r"] = hr
        hv = _rot((0, -st.torso - st.head_r + 6 + p.head_dy), lean * 0.7)
        J["head"] = (hip[0] + hv[0], hip[1] + hv[1])

        def arm(sh_pt, a, e, side):
            a1 = a * D2R
            dx = side * math.sin(a1)
            elbow = (sh_pt[0] + dx * st.upper, sh_pt[1] + math.cos(a1) * st.upper)
            a2 = (a + e) * D2R
            hand = (elbow[0] + side * math.sin(a2) * st.fore, elbow[1] + math.cos(a2) * st.fore)
            return elbow, hand

        if p.view == "front":
            sa = (shoulder[0] - 30, shoulder[1] + 6)
            sb = (shoulder[0] + 30, shoulder[1] + 6)
            ea, ha_ = arm(sa, p.arm_a, p.elb_a, -1)
            eb, hb_ = arm(sb, p.arm_b, p.elb_b, 1)
        else:
            sa = (shoulder[0] - f * 6, shoulder[1] + 4)
            sb = (shoulder[0] + f * 6, shoulder[1] + 4)
            ea, ha_ = arm(sa, p.arm_a, p.elb_a, f)
            eb, hb_ = arm(sb, p.arm_b, p.elb_b, f)
        J.update(sh_a=sa, elb_a=ea, hand_a=ha_, sh_b=sb, elb_b=eb, hand_b=hb_)
        return J

    # -- drawing ------------------------------------------------------------
    def draw(self, cx, p):
        """Draw and return joints in world coordinates."""
        st = self.st
        J = self.joints(p)
        cx.save()
        cx.translate(p.x, p.y)
        cx.scale(p.s, p.s * p.squash)
        if p.alpha < 1:
            cx.push_group()
        st.draw_back(cx, self, J, p)
        self._arm(cx, J, "a", p)
        self._leg(cx, J, "a", p)
        self._leg(cx, J, "b", p)
        st.draw_head_back(cx, self, J, p)
        st.draw_torso(cx, self, J, p)
        self._head(cx, J, p)
        self._arm(cx, J, "b", p)
        if p.alpha < 1:
            cx.pop_group_to_source()
            cx.paint_with_alpha(p.alpha)
        cx.restore()
        # world-space joints
        out = {}
        for k, v in J.items():
            if isinstance(v, tuple):
                out[k] = (p.x + v[0] * p.s, p.y + v[1] * p.s * p.squash)
        out["head_top"] = (out["head"][0], out["head"][1] - st.head_r * p.s)
        out["head_rad"] = st.head_r * p.s
        return out

    def _leg(self, cx, J, k, p):
        st = self.st
        hip, knee, foot = J["hip_" + k], J["knee_" + k], J["foot_" + k]
        line(cx, [hip, knee, foot], st.limb, st.limb_w)
        f = 1 if p.f >= 0 else -1
        if p.view == "front":
            f = -1 if k == "a" else 1
        if p.extra.get("shoe_flap") and k == "b":
            # sole peeling off - flaps with the stride
            fl = p.extra["shoe_flap"]
            cx.save()
            cx.translate(*foot)
            cx.scale(f, 1)
            rrect(cx, -9, -9, 33, 12, 6)
            fs(cx, st.shoe, OUTLINE, 3.5)
            cx.translate(-8, 3)
            cx.rotate(fl)
            rrect(cx, 0, 0, 34, 6, 3)
            fs(cx, hexc("#E8E3D8"), OUTLINE, 3)
            cx.restore()
            return
        st.draw_shoe(cx, foot, f, p)

    def _arm(self, cx, J, k, p):
        st = self.st
        sh, el, ha = J["sh_" + k], J["elb_" + k], J["hand_" + k]
        line(cx, [sh, el, ha], st.limb, st.limb_w)
        st.sleeve(cx, sh, el, p)
        circle(cx, ha[0], ha[1], st.limb_w * 0.9)
        fs(cx, st.limb, None, 0)

    def _head(self, cx, J, p):
        st = self.st
        R = st.head_r
        hx, hy = J["head"]
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        circle(cx, 0, 0, R)
        fs(cx, st.skin, OUTLINE, st.outline_w)
        cx.restore()
        draw_face(cx, J, p, R, st)
        st.draw_head_front(cx, self, J, p)
        if p.sweat > 0:
            f = p.f if p.view == "side" else 1
            cx.save()
            cx.translate(hx, hy)
            cx.rotate(J["head_r"])
            sx, sy = -f * R * 0.85, -R * 0.35 + 14 * smooth(p.sweat)
            cx.move_to(sx, sy - 16)
            cx.curve_to(sx + 10, sy - 2, sx + 10, sy + 8, sx, sy + 8)
            cx.curve_to(sx - 10, sy + 8, sx - 10, sy - 2, sx, sy - 16)
            src(cx, hexc("#8FD3FF"), p.sweat)
            cx.fill_preserve()
            src(cx, OUTLINE, p.sweat)
            cx.set_line_width(3)
            cx.stroke()
            cx.restore()


def is_blinking(t, seed):
    period = 3.1 + (seed % 7) * 0.37
    ph = (t + seed * 0.913) % period
    return ph < 0.11


def draw_face(cx, J, p, R, st):
    hx, hy = J["head"]
    cx.save()
    cx.translate(hx, hy)
    cx.rotate(J["head_r"])
    f = p.f if p.view == "side" else 0.0
    off = f * R * 0.22
    eyes = p.eyes
    if p.blink and eyes in ("open", "wide", "half", "tiny", "angry") and is_blinking(p.t, p.blink_seed):
        eyes = "closed"
    ex = R * 0.34
    ey = -R * 0.06
    lx, ly = p.look
    for side in (-1, 1):
        x = off + side * ex
        if p.view == "side":
            x = off + side * ex * 0.92
        _eye(cx, x, ey, eyes, lx, ly, side, st, p)
    _brows(cx, off, ex, ey, p.brows, side_f=f)
    _mouth(cx, off * 1.1, R * 0.44, p.mouth, p.mouth_open, f)
    if p.blush > 0:
        for side in (-1, 1):
            ellipse(cx, off + side * ex * 1.25, R * 0.3, 11, 6)
            src(cx, hexc("#FF8A8A"), 0.55 * p.blush)
            cx.fill()
    cx.restore()


def _eye(cx, x, y, kind, lx, ly, side, st, p):
    rx, ry = 11.5, 15.0
    if kind in ("open", "angry", "half", "wide", "spiral"):
        if kind == "wide":
            rx, ry = 14.5, 19
        ellipse(cx, x, y, rx, ry)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3.6)
        pr = 6.8 if kind != "wide" else 4.6
        px, py = x + lx * (rx - pr - 2), y + ly * (ry - pr - 2)
        if kind == "spiral":
            for k in range(3):
                circle(cx, x, y, 3 + k * 3.6)
            fs(cx, None, OUTLINE, 2.4)
        else:
            circle(cx, px, py, pr)
            fs(cx, OUTLINE, None, 0)
            circle(cx, px - pr * 0.35, py - pr * 0.38, pr * 0.32)
            fs(cx, (1, 1, 1, 1), None, 0)
        if kind == "half":
            cx.save()
            ellipse(cx, x, y, rx + 1, ry + 1)
            cx.clip()
            cx.rectangle(x - rx - 2, y - ry - 2, 2 * rx + 4, ry + 1)
            src(cx, st.skin)
            cx.fill()
            cx.restore()
            line(cx, [(x - rx, y - 1), (x + rx, y - 1)], OUTLINE, 3.8)
        if kind == "angry":
            cx.save()
            ellipse(cx, x, y, rx + 1, ry + 1)
            cx.clip()
            cx.move_to(x - rx - 2, y - ry - 2 + (2 if side < 0 else 16))
            cx.line_to(x + rx + 2, y - ry - 2 + (16 if side < 0 else 2))
            cx.line_to(x + rx + 2, y - ry - 6)
            cx.line_to(x - rx - 2, y - ry - 6)
            cx.close_path()
            src(cx, st.skin)
            cx.fill()
            cx.restore()
            line(cx, [(x - rx, y - ry + (0 if side < 0 else 14)), (x + rx, y - ry + (14 if side < 0 else 0))],
                 OUTLINE, 3.8)
        if st.lashes:
            line(cx, [(x + side * rx * 0.7, y - ry * 0.7), (x + side * (rx + 5), y - ry - 2)], OUTLINE, 3)
    elif kind == "closed":
        curve(cx, (x - rx, y + 2), (x - rx * 0.4, y + 8), (x + rx * 0.4, y + 8), (x + rx, y + 2), OUTLINE, 3.8)
    elif kind == "happy":
        curve(cx, (x - rx, y + 5), (x - rx * 0.5, y - 9), (x + rx * 0.5, y - 9), (x + rx, y + 5), OUTLINE, 4.2)
    elif kind == "squeeze":
        line(cx, [(x - rx, y - 6), (x + side * 4, y), (x - rx, y + 6)] if side > 0 else
             [(x + rx, y - 6), (x - 4, y), (x + rx, y + 6)], OUTLINE, 4)
    elif kind == "tiny":
        circle(cx, x + lx * 3, y + ly * 3, 4.2)
        fs(cx, OUTLINE, None, 0)
    elif kind == "x":
        line(cx, [(x - 8, y - 8), (x + 8, y + 8)], OUTLINE, 4)
        line(cx, [(x + 8, y - 8), (x - 8, y + 8)], OUTLINE, 4)


def _brows(cx, off, ex, ey, kind, side_f=0):
    y = ey - 26
    for side in (-1, 1):
        x = off + side * ex
        inner = x - side * 9
        outer = x + side * 9
        if kind == "neutral":
            pts = [(inner, y - 1), (outer, y - 3)]
        elif kind == "up":
            pts = [(inner, y - 9), (outer, y - 11)]
        elif kind == "worried":
            pts = [(inner, y - 9), (outer, y - 1)]
        elif kind == "angry":
            pts = [(inner, y + 6), (outer, y - 5)]
        elif kind == "skeptic":
            pts = [(inner, y - (10 if side > 0 else 0)), (outer, y - (13 if side > 0 else -2))]
        elif kind == "flat":
            pts = [(inner, y + 2), (outer, y + 2)]
        elif kind == "none":
            continue
        else:
            pts = [(inner, y - 1), (outer, y - 3)]
        line(cx, pts, OUTLINE, 5.2)


def _mouth(cx, x, y, kind, op, f):
    if kind == "smile":
        curve(cx, (x - 13, y - 2), (x - 6, y + 8), (x + 6, y + 8), (x + 13, y - 2), OUTLINE, 4.2)
    elif kind == "grin":
        cx.move_to(x - 18, y - 4)
        cx.curve_to(x - 14, y + 20 * op, x + 14, y + 20 * op, x + 18, y - 4)
        cx.close_path()
        fs(cx, hexc("#3A1F22"), OUTLINE, 3.8)
        cx.save()
        cx.move_to(x - 18, y - 4)
        cx.curve_to(x - 14, y + 20 * op, x + 14, y + 20 * op, x + 18, y - 4)
        cx.close_path()
        cx.clip()
        cx.rectangle(x - 20, y - 6, 40, 7)
        src(cx, (1, 1, 1, 1))
        cx.fill()
        ellipse(cx, x, y + 16 * op, 9, 5)
        src(cx, hexc("#E86A6A"))
        cx.fill()
        cx.restore()
    elif kind == "flat":
        line(cx, [(x - 10, y + 2), (x + 10, y + 2)], OUTLINE, 4.2)
    elif kind == "o":
        ellipse(cx, x, y + 3, 6.5 * op, 8.5 * op)
        fs(cx, hexc("#3A1F22"), OUTLINE, 3.4)
    elif kind == "scream":
        ellipse(cx, x, y + 6, 15 * op, 20 * op)
        fs(cx, hexc("#3A1F22"), OUTLINE, 3.8)
        ellipse(cx, x, y + 6 + 12 * op, 9 * op, 6 * op)
        src(cx, hexc("#E86A6A"))
        cx.fill()
    elif kind == "frown":
        curve(cx, (x - 12, y + 6), (x - 6, y - 3), (x + 6, y - 3), (x + 12, y + 6), OUTLINE, 4.2)
    elif kind == "wavy":
        cx.move_to(x - 14, y + 2)
        for i in range(1, 8):
            cx.line_to(x - 14 + i * 4, y + 2 + (3 if i % 2 else -3))
        src(cx, OUTLINE)
        cx.set_line_width(3.8)
        cx.set_line_join(1)
        cx.stroke()
    elif kind == "smirk":
        curve(cx, (x - 10, y + 3), (x - 2, y + 6), (x + 6, y + 4), (x + 13, y - 4), OUTLINE, 4.2)
    elif kind == "teeth":
        rrect(cx, x - 16, y - 6, 32, 16, 5)
        fs(cx, (1, 1, 1, 1), OUTLINE, 3.6)
        line(cx, [(x - 15, y + 2), (x + 15, y + 2)], OUTLINE, 2.4)
        for k in (-8, 0, 8):
            line(cx, [(x + k, y - 5), (x + k, y + 9)], OUTLINE, 2.2)
    elif kind == "chew":
        ellipse(cx, x, y + 2, 10, 4 + 3 * op)
        fs(cx, hexc("#3A1F22"), OUTLINE, 3.2)
    elif kind == "yell":
        h = 20 * op
        cx.move_to(x - 15, y - 3)
        cx.line_to(x + 15, y - 3)
        cx.line_to(x + 12, y + h)
        cx.line_to(x - 12, y + h)
        cx.close_path()
        fs(cx, hexc("#3A1F22"), OUTLINE, 3.8)
        cx.save()
        cx.move_to(x - 15, y - 3)
        cx.line_to(x + 15, y - 3)
        cx.line_to(x + 12, y + h)
        cx.line_to(x - 12, y + h)
        cx.close_path()
        cx.clip()
        cx.rectangle(x - 16, y - 4, 32, 6)
        src(cx, (1, 1, 1, 1))
        cx.fill()
        cx.rectangle(x - 16, y + h - 5, 32, 6)
        cx.fill()
        cx.restore()


# ------------------------------------------------------------------ motion
def walk(p, t, speed=1.0, amp=1.0, arms=True):
    """Walk cycle. speed = cycles per second."""
    ph = t * speed * 2 * math.pi
    s = math.sin(ph)
    c = math.cos(ph)
    a = 24 * amp
    p = p.but(hip_a=-a * s, hip_b=a * s,
              knee_a=8 + 28 * amp * max(0, c), knee_b=8 + 28 * amp * max(0, -c),
              bob=-abs(math.cos(ph)) * 5 * amp + 3, lean=p.lean + 3)
    if arms:
        p = p.but(arm_a=a * 0.9 * s, arm_b=-a * 0.9 * s, elb_a=14 + 10 * max(0, s), elb_b=14 + 10 * max(0, -s))
    return p


def run(p, t, speed=2.2, amp=1.0, arms=True, flail=False):
    ph = t * speed * 2 * math.pi
    s = math.sin(ph)
    c = math.cos(ph)
    a = 46 * amp
    p = p.but(hip_a=-a * s + 8, hip_b=a * s + 8,
              knee_a=20 + 70 * amp * max(0, c), knee_b=20 + 70 * amp * max(0, -c),
              bob=-abs(math.cos(ph)) * 14 * amp + 8, lean=p.lean + 14 * amp)
    if arms:
        if flail:
            p = p.but(arm_a=150 + 25 * s, arm_b=150 - 25 * s, elb_a=20 + 25 * c, elb_b=20 - 25 * c)
        else:
            p = p.but(arm_a=-50 * s * amp + 10, arm_b=50 * s * amp + 10, elb_a=80, elb_b=80)
    return p


def breathe(p, t, amt=1.0):
    return p.but(bob=p.bob + math.sin(t * 2.4) * 1.6 * amt,
                 arm_a=p.arm_a + math.sin(t * 2.4 + 0.5) * 1.5 * amt,
                 arm_b=p.arm_b - math.sin(t * 2.4 + 0.5) * 1.5 * amt)


def talk(p, t, rate=9.0):
    """Mouth flap for speaking characters."""
    v = 0.5 + 0.5 * math.sin(t * rate) * math.sin(t * rate * 0.37 + 1)
    return p.but(mouth_open=0.4 + 0.8 * abs(v))


# ------------------------------------------------------------------ cast
HERO = Figure(HeroStyle(), seed=1)
MAXIMUS_STYLE = RomanSoldierStyle(crest=True, cape=True)
MAXIMUS = Figure(MAXIMUS_STYLE, seed=2)
LUCIA = Figure(LuciaStyle(), seed=3)
BOY = Figure(BoyStyle(), seed=4)


def soldier(seed):
    st = RomanSoldierStyle(crest=False, cape=False)
    st.tunic = hexc(["#B8322E", "#A92B2B", "#BE3A30"][seed % 3])
    return Figure(st, seed=seed + 10)


def roman(seed, **kw):
    return Figure(RomanStyle(seed=seed, **kw), seed=seed + 100)


# Default poses
HERO_SCALE = 1.0
MAX_SCALE = 1.32
LUCIA_SCALE = 1.0
BOY_SCALE = 0.72


def hero_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=HERO_SCALE, t=t, blink_seed=1)
    d.update(kw)
    return Pose(**d)


def max_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=MAX_SCALE, t=t, blink_seed=2, brows="angry", mouth="frown")
    d.update(kw)
    return Pose(**d)


def lucia_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=LUCIA_SCALE, t=t, blink_seed=3, eyes="half", mouth="flat", brows="flat")
    d.update(kw)
    return Pose(**d)


def boy_pose(x, y, t, **kw):
    d = dict(x=x, y=y, s=BOY_SCALE, t=t, blink_seed=4, mouth="grin")
    d.update(kw)
    return Pose(**d)

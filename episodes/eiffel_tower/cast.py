"""1920s cast for the Eiffel Tower episode, on the shared Cinecode stick-figure rig.

Victor Lustig: charcoal-navy double-breasted suit, black homburg, pencil moustache, white pocket square.
André Poisson: brown tweed three-piece, bowler hat, round spectacles, bushy moustache.
"""
import math

from cinecode.characters import Figure, Pose, Style, _rot
from cinecode.core import OUTLINE, circle, curve, ellipse, fs, hexc, line, rrect, shade, src

D2R = math.pi / 180


class SuitStyle(Style):
    head_r = 54
    torso = 112
    thigh = 64
    shin = 64
    upper = 52
    fore = 50
    limb_w = 8.5
    limb = hexc("#2a1f1c")
    shoe = hexc("#1b1716")

    def __init__(self, suit="#2b3446", shirt="#f1ece2", tie="#6b1f24", hat="homburg", hat_col="#17181c",
                 band="#5a1e22", mous="pencil", glasses=False, vest=None, square=True, hair=None, beard=False,
                 width=1.0, kepi=False):
        self.suit = hexc(suit)
        self.suit_dk = shade(self.suit, -0.25)
        self.suit_lt = shade(self.suit, 0.18)
        self.shirt = hexc(shirt)
        self.tie = hexc(tie)
        self.hat = hat
        self.hat_col = hexc(hat_col)
        self.band = hexc(band)
        self.mous = mous
        self.glasses = glasses
        self.vest = hexc(vest) if vest else None
        self.square = square
        self.hair = hexc(hair) if hair else None
        self.beard = beard
        self.width = width
        self.kepi = kepi

    # ---------------------------------------------------------------- torso
    def _path(self, cx, hw_s, hw_h, T):
        # rounded jacket: slightly pear shaped like the reference figures
        cx.move_to(-hw_h, 4)
        cx.curve_to(-hw_h - 6, -T * 0.35, -hw_s - 2, -T * 0.8, -hw_s + 14, -T)
        cx.line_to(hw_s - 14, -T)
        cx.curve_to(hw_s + 2, -T * 0.8, hw_h + 6, -T * 0.35, hw_h, 4)
        cx.curve_to(hw_h - 2, 14, hw_h - 10, 16, hw_h - 18, 16)
        cx.line_to(-hw_h + 18, 16)
        cx.curve_to(-hw_h + 10, 16, -hw_h + 2, 14, -hw_h, 4)
        cx.close_path()

    def draw_torso(self, cx, fig, J, p):
        T = self.torso
        cx.save()
        cx.translate(*J["hip"])
        cx.rotate(J["lean_r"])
        hw_s = 38 * self.width
        hw_h = 42 * self.width
        self._path(cx, hw_s, hw_h, T)
        fs(cx, self.suit, OUTLINE, 5)
        cx.save()
        self._path(cx, hw_s, hw_h, T)
        cx.clip()
        f = p.f if p.view == "side" else 0
        # soft light from upper left
        cx.rectangle(-60 if f >= 0 else 0, -T, 60 if f >= 0 else 60, T + 20)
        src(cx, self.suit_lt, 0.18)
        cx.fill()
        cx.rectangle(-60, -12, 120, 30)
        src(cx, self.suit_dk, 0.5)
        cx.fill()
        if p.view == "front":
            # shirt V, tie, lapels
            cx.move_to(-20, -T - 2)
            cx.line_to(0, -T + 52)
            cx.line_to(20, -T - 2)
            cx.close_path()
            fs(cx, self.vest if self.vest is not None else self.shirt, OUTLINE, 3)
            if self.vest is not None:
                cx.move_to(-10, -T - 2)
                cx.line_to(0, -T + 26)
                cx.line_to(10, -T - 2)
                cx.close_path()
                fs(cx, self.shirt, OUTLINE, 2.5)
            cx.move_to(-5, -T + 4)
            cx.line_to(5, -T + 4)
            cx.line_to(7, -T + 38)
            cx.line_to(0, -T + 46)
            cx.line_to(-7, -T + 38)
            cx.close_path()
            fs(cx, self.tie, OUTLINE, 2.5)
            line(cx, [(-22, -T), (-4, -T + 58), (-2, -10)], shade(self.suit_dk, -0.2), 3)
            line(cx, [(22, -T), (4, -T + 58)], shade(self.suit_dk, -0.2), 3)
            for by in (-T + 66, -T + 86):
                for bx in (-9, 9):
                    circle(cx, bx, by, 3.6)
                    fs(cx, shade(self.suit_dk, -0.3), None, 0)
            if self.square:
                rrect(cx, 14, -T + 30, 16, 9, 2)
                fs(cx, (0.97, 0.96, 0.92, 1), OUTLINE, 2)
        else:
            # profile: lapel & shirt front toward facing side
            cx.move_to(f * 12, -T)
            cx.line_to(f * 28, -T + 2)
            cx.line_to(f * 22, -T + 40)
            cx.close_path()
            fs(cx, self.shirt, OUTLINE, 2.5)
            line(cx, [(f * 22, -T + 6), (f * 23, -T + 34)], self.tie, 6)
            line(cx, [(f * 8, -T), (f * 18, -T + 56), (f * 28, -T + 70)], shade(self.suit_dk, -0.2), 3)
            if self.square:
                rrect(cx, f * 2 - 8, -T + 34, 16, 8, 2)
                fs(cx, (0.97, 0.96, 0.92, 1), OUTLINE, 2)
        cx.restore()
        cx.restore()

    def sleeve(self, cx, shoulder, elbow, p):
        sx, sy = shoulder
        ex, ey = elbow
        mx, my = sx + (ex - sx) * 0.7, sy + (ey - sy) * 0.7
        line(cx, [(sx, sy), (mx, my)], OUTLINE, 22)
        line(cx, [(sx, sy), (mx, my)], self.suit, 15)

    # ---------------------------------------------------------------- head
    def draw_head_back(self, cx, fig, J, p):
        if self.hair is not None and self.hat is None:
            pass

    def draw_head_front(self, cx, fig, J, p):
        R = self.head_r
        hx, hy = J["head"]
        f = p.f if p.view == "side" else 0.0
        off = f * R * 0.22
        cx.save()
        cx.translate(hx, hy)
        cx.rotate(J["head_r"])
        # moustache
        my = R * 0.27
        if self.mous == "pencil":
            for s in (-1, 1):
                curve(cx, (off + s * 2, my), (off + s * 8, my - 3), (off + s * 15, my - 2), (off + s * 19, my + 1), OUTLINE, 3.6)
        elif self.mous == "bushy":
            cx.move_to(off - 24, my + 6)
            cx.curve_to(off - 20, my - 10, off - 4, my - 8, off, my - 2)
            cx.curve_to(off + 4, my - 8, off + 20, my - 10, off + 24, my + 6)
            cx.curve_to(off + 12, my + 2, off + 4, my + 4, off, my + 2)
            cx.curve_to(off - 4, my + 4, off - 12, my + 2, off - 24, my + 6)
            cx.close_path()
            fs(cx, hexc("#4a3426"), OUTLINE, 2.5)
        elif self.mous == "grey":
            cx.move_to(off - 22, my + 4)
            cx.curve_to(off - 16, my - 8, off - 4, my - 6, off, my - 1)
            cx.curve_to(off + 4, my - 6, off + 16, my - 8, off + 22, my + 4)
            cx.curve_to(off + 8, my + 2, off - 8, my + 2, off - 22, my + 4)
            cx.close_path()
            fs(cx, hexc("#8f877e"), OUTLINE, 2.5)
        if self.beard:
            cx.move_to(-R * 0.75 + off, R * 0.2)
            cx.curve_to(-R * 0.7 + off, R * 1.05, R * 0.7 + off, R * 1.05, R * 0.75 + off, R * 0.2)
            cx.curve_to(R * 0.4 + off, R * 0.55, -R * 0.4 + off, R * 0.55, -R * 0.75 + off, R * 0.2)
            cx.close_path()
            fs(cx, hexc("#5b4636"), OUTLINE, 3)
        if self.glasses:
            ex = R * 0.34
            for s in (-1, 1):
                x = off + s * ex * (0.92 if p.view == "side" else 1)
                circle(cx, x, -R * 0.06, 17)
                fs(cx, (0.85, 0.92, 1.0, 0.18), hexc("#3a2a1a"), 3.2)
            line(cx, [(off - ex + 17, -R * 0.1), (off + ex - 17, -R * 0.1)], hexc("#3a2a1a"), 3)
        # hats
        if self.hat == "homburg":
            self._brim_hat(cx, R, f, crown_h=R * 0.78, crown_w=R * 0.86, brim=R * 1.22, dent=True)
        elif self.hat == "bowler":
            cx.move_to(-R * 0.8 + off * 0.3, -R * 0.62)
            cx.curve_to(-R * 0.82, -R * 1.55, R * 0.82, -R * 1.55, R * 0.8 + off * 0.3, -R * 0.62)
            cx.close_path()
            fs(cx, self.hat_col, OUTLINE, 4.5)
            ellipse(cx, off * 0.2, -R * 0.62, R * 1.1, R * 0.16)
            fs(cx, self.hat_col, OUTLINE, 4.5)
            line(cx, [(-R * 0.78, -R * 0.74), (R * 0.78, -R * 0.74)], self.band, 7)
            ellipse(cx, -R * 0.25, -R * 1.15, R * 0.22, R * 0.1, -0.3)
            src(cx, (1, 1, 1, 0.18))
            cx.fill()
        elif self.hat == "cap":
            cx.move_to(-R * 0.92, -R * 0.45)
            cx.curve_to(-R * 0.95, -R * 1.25, R * 0.8, -R * 1.3, R * 0.95, -R * 0.55)
            cx.close_path()
            fs(cx, self.hat_col, OUTLINE, 4.5)
            sgn = f if f else 1
            cx.move_to(sgn * R * 0.5, -R * 0.52)
            cx.curve_to(sgn * R * 1.05, -R * 0.62, sgn * R * 1.35, -R * 0.5, sgn * R * 1.25, -R * 0.4)
            cx.line_to(sgn * R * 0.4, -R * 0.42)
            cx.close_path()
            fs(cx, shade(self.hat_col, -0.2), OUTLINE, 4)
        elif self.hat == "kepi":
            rrect(cx, -R * 0.68, -R * 1.45, R * 1.36, R * 0.95, 8)
            fs(cx, self.hat_col, OUTLINE, 4.5)
            line(cx, [(-R * 0.66, -R * 0.66), (R * 0.66, -R * 0.66)], hexc("#b01e24"), 10)
            sgn = f if f else 1
            cx.move_to(sgn * R * 0.1, -R * 0.56)
            cx.curve_to(sgn * R * 0.7, -R * 0.6, sgn * R * 1.05, -R * 0.5, sgn * R * 0.98, -R * 0.4)
            cx.line_to(sgn * R * 0.0, -R * 0.45)
            cx.close_path()
            fs(cx, hexc("#151515"), OUTLINE, 3.5)
        elif self.hat is None:
            if self.hair is not None:
                cx.move_to(-R * 0.98, -R * 0.15)
                cx.curve_to(-R * 1.05, -R * 1.3, R * 1.05, -R * 1.3, R * 0.98, -R * 0.15)
                cx.curve_to(R * 0.7, -R * 0.62, -R * 0.7, -R * 0.62, -R * 0.98, -R * 0.15)
                cx.close_path()
                fs(cx, self.hair, OUTLINE, 3.5)
            else:
                # bald: shine + side tufts
                for s in (-1, 1):
                    ellipse(cx, s * R * 0.92, -R * 0.05, R * 0.14, R * 0.3)
                    fs(cx, hexc("#9a9088"), OUTLINE, 2.5)
                ellipse(cx, -R * 0.3, -R * 0.7, R * 0.2, R * 0.08, -0.4)
                src(cx, (1, 1, 1, 0.6))
                cx.fill()
        cx.restore()

    def _brim_hat(self, cx, R, f, crown_h, crown_w, brim, dent):
        # crown
        top = -R * 0.62 - crown_h
        cx.move_to(-crown_w, -R * 0.62)
        cx.curve_to(-crown_w - 2, top + 16, -crown_w + 10, top, -crown_w * 0.4, top + 2)
        if dent:
            cx.curve_to(-crown_w * 0.15, top + 12, crown_w * 0.15, top + 12, crown_w * 0.4, top + 2)
        cx.curve_to(crown_w - 10, top, crown_w + 2, top + 16, crown_w, -R * 0.62)
        cx.close_path()
        fs(cx, self.hat_col, OUTLINE, 4.5)
        # band
        cx.rectangle(-crown_w + 1, -R * 0.62 - 16, 2 * crown_w - 2, 13)
        src(cx, self.band)
        cx.fill()
        # brim with slight curl
        cx.move_to(-brim, -R * 0.66)
        cx.curve_to(-brim * 0.8, -R * 0.52, brim * 0.8, -R * 0.52, brim, -R * 0.66)
        cx.curve_to(brim * 0.9, -R * 0.5, -brim * 0.9, -R * 0.5, -brim, -R * 0.66)
        cx.close_path()
        fs(cx, self.hat_col, OUTLINE, 4)
        # sheen
        cx.move_to(-crown_w * 0.7, top + 14)
        cx.curve_to(-crown_w * 0.6, top + 30, -crown_w * 0.62, -R * 0.62 - 26, -crown_w * 0.7, -R * 0.62 - 22)
        src(cx, (1, 1, 1, 0.16))
        cx.set_line_width(5)
        cx.stroke()


LUSTIG_STYLE = SuitStyle(suit="#283246", tie="#7a1e26", hat="homburg", hat_col="#141519", band="#2b2b33",
                         mous="pencil", square=True)
POISSON_STYLE = SuitStyle(suit="#6b4a30", tie="#2f4a3a", hat="bowler", hat_col="#2a2220", band="#151212",
                          mous="bushy", glasses=True, vest="#8a6a44", square=False, width=1.12)
DEALER_STYLES = [
    SuitStyle(suit="#4a4f55", tie="#5a1e22", hat="bowler", hat_col="#1c1c1f", mous="grey", square=False, width=1.05),
    SuitStyle(suit="#5a4636", tie="#24364a", hat="cap", hat_col="#4e4a44", mous=None, square=False),
    SuitStyle(suit="#3a3d4a", tie="#6b5a2a", hat=None, hair=None, mous="grey", square=False, width=1.15),
    SuitStyle(suit="#55402e", tie="#4a1e1e", hat="homburg", hat_col="#4a3a2c", band="#2a1f18", mous="bushy", square=False),
]
NEW_DEALER_STYLES = [
    SuitStyle(suit="#3c4a3e", tie="#7a5a24", hat=None, hair=None, mous=None, beard=True, square=False, width=1.15),
    SuitStyle(suit="#5e5a52", tie="#2a2a44", hat="bowler", hat_col="#38302a", mous="pencil", square=False),
    SuitStyle(suit="#4a3a46", tie="#2a3a2a", hat="cap", hat_col="#5a5048", mous="grey", square=False, width=1.05),
]
GENDARME_STYLE = SuitStyle(suit="#24304a", tie="#24304a", hat="kepi", hat_col="#1e2a44", mous="bushy", square=False)

LUSTIG = Figure(LUSTIG_STYLE, seed=11)
POISSON = Figure(POISSON_STYLE, seed=12)
DEALERS = [Figure(s, seed=20 + i) for i, s in enumerate(DEALER_STYLES)]
NEW_DEALERS = [Figure(s, seed=40 + i) for i, s in enumerate(NEW_DEALER_STYLES)]
GENDARME = Figure(GENDARME_STYLE, seed=50)

# rig height (feet to top of head) in rig units, used to convert metres -> scale
RIG_H = SuitStyle.thigh + SuitStyle.shin + SuitStyle.torso + 2 * SuitStyle.head_r - 6


def pose_for(px, py, ppm, height_m=1.78, t=0.0, seed=0, **kw):
    s = ppm * height_m / RIG_H
    d = dict(x=px, y=py, s=s, t=t, blink_seed=seed, mouth="flat", brows="neutral")
    d.update(kw)
    return Pose(**d)


def seated(p, hip_dz=0):
    """Seated pose: thighs forward, shins down. Anchor y should be the SEAT height point."""
    return p.but(hip_a=86, knee_a=88, hip_b=80, knee_b=84, bob=0)

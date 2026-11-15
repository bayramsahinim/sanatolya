"""The Earth cake: layered cake whose top is planet Earth, a chef's knife, radial cuts and
one wedge ('your slice') that slides out."""
import math
import random

import cairo

from cinecode.core import hexc, mix, shade, src
from episodes.everything_divided.earth import globe_texture

TAU = 2 * math.pi

# side bands, as fractions of the cake height: (f0, f1, colour)
BANDS = [
    (0.00, 0.17, hexc("#2a7fd6")),   # ocean-blue glaze
    (0.17, 0.40, hexc("#f4c56a")),   # vanilla sponge
    (0.40, 0.47, hexc("#fff4e0")),   # cream
    (0.47, 0.70, hexc("#e8674f")),   # strawberry sponge
    (0.70, 0.77, hexc("#fff4e0")),   # cream
    (0.77, 1.00, hexc("#f2b85a")),   # vanilla sponge
]


class Cake:
    def __init__(self, X=540, Y=820, R=390, k=0.42, Hc=270):
        self.X, self.Y, self.R, self.r, self.Hc = X, Y, R, R * k, Hc
        rnd = random.Random(3)
        self.drips = [(rnd.uniform(0, math.pi), rnd.uniform(0.25, 1.0), rnd.uniform(0.05, 0.09)) for _ in range(16)]
        self.dollops = 30

    def P(self, th, f=0.0, rr=1.0, off=(0, 0)):
        return (self.X + off[0] + self.R * rr * math.cos(th), self.Y + off[1] + self.r * rr * math.sin(th) + f * self.Hc)

    # -------------------------------------------------------------- pieces
    def _ell_arc(self, cx, a0, a1, f, off=(0, 0), neg=False):
        n = max(2, int(abs(a1 - a0) / 0.03))
        for i in range(n + 1):
            th = a0 + (a1 - a0) * i / n
            x, y = self.P(th, f, off=off)
            if i == 0 and not neg:
                cx.move_to(x, y)
            else:
                cx.line_to(x, y)

    def side(self, cx, a0, a1, off=(0, 0), alpha=1.0):
        """Front side surface between angles a0<a1 (within [0, pi])."""
        a0, a1 = max(a0, 0.0), min(a1, math.pi)
        if a1 <= a0:
            return
        for f0, f1, col in BANDS:
            cx.new_path()
            self._ell_arc(cx, a0, a1, f0, off)
            self._ell_arc(cx, a1, a0, f1, off, neg=True)
            cx.close_path()
            src(cx, col, alpha)
            cx.fill()
        # sponge crumb texture lines (subtle)
        # cylindrical shading
        x0 = self.X + off[0] - self.R
        g = cairo.LinearGradient(x0, 0, x0 + 2 * self.R, 0)
        g.add_color_stop_rgba(0.0, 0, 0, 0.08, 0.42 * alpha)
        g.add_color_stop_rgba(0.28, 0, 0, 0, 0.0)
        g.add_color_stop_rgba(0.36, 1, 1, 1, 0.16 * alpha)
        g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
        g.add_color_stop_rgba(0.8, 0, 0, 0.08, 0.14 * alpha)
        g.add_color_stop_rgba(1.0, 0, 0, 0.1, 0.5 * alpha)
        cx.new_path()
        self._ell_arc(cx, a0, a1, 0, off)
        self._ell_arc(cx, a1, a0, 1, off, neg=True)
        cx.close_path()
        cx.set_source(g)
        cx.fill()
        # glaze drips over the vanilla layer
        for th, ln, wd in self.drips:
            if not (a0 + wd < th < a1 - wd):
                continue
            x, y = self.P(th, 0.17, off=off)
            dl = ln * self.Hc * 0.16
            ww = wd * self.R * 0.5
            cx.new_path()
            cx.move_to(x - ww, y - 4)
            cx.curve_to(x - ww, y + dl * 0.6, x - ww * 0.6, y + dl, x, y + dl)
            cx.curve_to(x + ww * 0.6, y + dl, x + ww, y + dl * 0.6, x + ww, y - 4)
            cx.close_path()
            src(cx, BANDS[0][2], alpha)
            cx.fill()
            cx.arc(x - ww * 0.3, y + dl * 0.7, ww * 0.22, 0, TAU)
            cx.set_source_rgba(1, 1, 1, 0.35 * alpha)
            cx.fill()
        # glaze gloss line
        cx.new_path()
        self._ell_arc(cx, max(a0, 0.25), min(a1, 1.6), 0.05, off)
        cx.set_source_rgba(1, 1, 1, 0.3 * alpha)
        cx.set_line_width(5)
        cx.stroke()

    def cut_face(self, cx, th, off=(0, 0), alpha=1.0, darken=0.0):
        """Vertical cross-section from the axis to the rim at angle th."""
        cxp = (self.X + off[0], self.Y + off[1])
        rim = self.P(th, 0, off=off)
        for f0, f1, col in BANDS:
            cx.new_path()
            cx.move_to(cxp[0], cxp[1] + f0 * self.Hc)
            cx.line_to(rim[0], rim[1] + f0 * self.Hc)
            cx.line_to(rim[0], rim[1] + f1 * self.Hc)
            cx.line_to(cxp[0], cxp[1] + f1 * self.Hc)
            cx.close_path()
            c = col if f0 > 0 else hexc("#4f9be6")
            src(cx, shade(c, -0.12 - darken), alpha)
            cx.fill()
        # crumb speckles
        rnd = random.Random(int(th * 1000))
        for _ in range(40):
            u, v = rnd.random(), rnd.uniform(0.2, 0.98)
            x = cxp[0] + (rim[0] - cxp[0]) * u
            y = cxp[1] + (rim[1] - cxp[1]) * u + v * self.Hc
            cx.arc(x, y, rnd.uniform(1.5, 3.5), 0, TAU)
            cx.set_source_rgba(0.55, 0.3, 0.1, 0.18 * alpha)
            cx.fill()

    def top(self, cx, a_skip=None, off=(0, 0), only=None, alpha=1.0, lon0=12.0):
        """Earth top (ellipse). a_skip=(a0,a1) removes a sector; only=(a0,a1) draws just that sector."""
        tex = globe_texture(self.R, lon0=lon0, lat0=24.0)
        X, Y = self.X + off[0], self.Y + off[1]
        cx.save()
        cx.translate(X, Y)
        cx.scale(1.0, self.r / self.R)
        cx.new_path()
        if only:
            cx.move_to(0, 0)
            cx.arc(0, 0, self.R, only[0], only[1])
            cx.close_path()
        elif a_skip:
            cx.move_to(0, 0)
            cx.arc(0, 0, self.R, a_skip[1], a_skip[0] + TAU)
            cx.close_path()
        else:
            cx.arc(0, 0, self.R, 0, TAU)
        cx.clip()
        cx.set_source_surface(tex, -tex.get_width() / 2, -tex.get_height() / 2)
        cx.paint_with_alpha(alpha)
        cx.restore()
        # rim highlight
        cx.save()
        cx.translate(X, Y)
        cx.scale(1.0, self.r / self.R)
        cx.arc(0, 0, self.R - 2, math.pi * 1.05, math.pi * 1.95)
        cx.restore()
        cx.set_source_rgba(1, 1, 1, 0.35 * alpha)
        cx.set_line_width(4)
        cx.stroke()

    def cuts(self, cx, angles, alpha=1.0, skip=None):
        n = len(angles)
        dense = n > 24
        r0 = 0.0 if not dense else min(0.35, 0.04 + n / 1400)   # keep the centre from turning black
        lw = 3.2 if not dense else max(1.0, 3.2 * 24 / n ** 0.9)
        for th in angles:
            if skip and skip[0] - 0.01 <= th % TAU <= skip[1] + 0.01:
                continue
            x0, y0 = self.P(th, 0, rr=r0)
            x, y = self.P(th, 0, rr=0.985)
            cx.move_to(x0, y0)
            cx.line_to(x, y)
            cx.set_source_rgba(0.05, 0.08, 0.2, 0.5 * alpha)
            cx.set_line_width(lw)
            cx.stroke()
            cx.move_to(x0 + 1.5, y0 + 1.5)
            cx.line_to(x + 1.5, y + 1.5)
            cx.set_source_rgba(1, 1, 1, 0.3 * alpha)
            cx.set_line_width(lw * 0.45)
            cx.stroke()
            s = math.sin(th)
            if s > 0.05 and n <= 40:  # continue the cut down the visible side
                cx.move_to(x, y + 2)
                cx.line_to(x, y + self.Hc * 0.98)
                cx.set_source_rgba(0.25, 0.1, 0.05, 0.3 * alpha * s * min(1, 24 / max(n, 1)))
                cx.set_line_width(2.2)
                cx.stroke()
        if dense:
            # the knife has scored the centre into a fine glittering star
            g = cairo.RadialGradient(self.X, self.Y, 0, self.X, self.Y, self.R * r0 * 1.2)
            g.add_color_stop_rgba(0, 1, 1, 1, 0.5 * alpha)
            g.add_color_stop_rgba(1, 1, 1, 1, 0)
            cx.save()
            cx.translate(self.X, self.Y)
            cx.scale(1, self.r / self.R)
            cx.translate(-self.X, -self.Y)
            cx.arc(self.X, self.Y, self.R * r0 * 1.2, 0, TAU)
            cx.set_source(g)
            cx.fill()
            cx.restore()

    def dollop(self, cx, x, y, s, alpha=1.0):
        g = cairo.RadialGradient(x - s * 0.35, y - s * 0.5, s * 0.1, x, y, s * 1.2)
        g.add_color_stop_rgba(0, 1, 1, 1, alpha)
        g.add_color_stop_rgba(0.6, 0.97, 0.95, 0.92, alpha)
        g.add_color_stop_rgba(1, 0.78, 0.76, 0.8, alpha)
        cx.new_path()
        cx.move_to(x - s, y + s * 0.25)
        cx.curve_to(x - s * 1.05, y - s * 0.55, x - s * 0.3, y - s * 0.75, x - s * 0.1, y - s * 1.25)
        cx.curve_to(x + s * 0.15, y - s * 0.8, x + s * 1.05, y - s * 0.6, x + s, y + s * 0.25)
        cx.curve_to(x + s * 0.6, y + s * 0.55, x - s * 0.6, y + s * 0.55, x - s, y + s * 0.25)
        cx.close_path()
        cx.set_source(g)
        cx.fill_preserve()
        cx.set_source_rgba(0.6, 0.6, 0.7, 0.35 * alpha)
        cx.set_line_width(1.5)
        cx.stroke()
        cx.arc(x - s * 0.35, y - s * 0.3, s * 0.18, 0, TAU)
        cx.set_source_rgba(1, 1, 1, 0.8 * alpha)
        cx.fill()

    def piping(self, cx, skip=None, off=(0, 0), only=None, alpha=1.0, front=None):
        """front=None both halves, True only front (sin>0), False only back."""
        n = self.dollops
        items = []
        for i in range(n):
            th = (i + 0.5) / n * TAU
            if skip and skip[0] <= th <= skip[1]:
                continue
            if only and not (only[0] <= th <= only[1]):
                continue
            s = math.sin(th)
            if front is True and s < 0:
                continue
            if front is False and s >= 0:
                continue
            items.append((s, th))
        for s, th in sorted(items):
            x, y = self.P(th, 0, rr=0.96, off=off)
            self.dollop(cx, x, y - 6, 17 + 5 * (s + 1) / 2, alpha)

    def plate(self, cx, alpha=1.0):
        X, Y = self.X, self.Y + self.Hc
        R, r = self.R * 1.3, self.r * 1.3
        cx.save()
        cx.translate(X, Y + 30)
        cx.scale(1, r / R)
        g = cairo.RadialGradient(0, 0, R * 0.6, 0, 0, R * 1.15)
        g.add_color_stop_rgba(0, 0, 0, 0.05, 0.45 * alpha)
        g.add_color_stop_rgba(1, 0, 0, 0.05, 0)
        cx.arc(0, 0, R * 1.15, 0, TAU)
        cx.set_source(g)
        cx.fill()
        cx.restore()
        cx.save()
        cx.translate(X, Y + 12)
        cx.scale(1, r / R)
        cx.arc(0, 0, R, 0, TAU)
        g = cairo.LinearGradient(0, -R, 0, R)
        g.add_color_stop_rgba(0, 0.98, 0.98, 1, alpha)
        g.add_color_stop_rgba(1, 0.72, 0.75, 0.85, alpha)
        cx.set_source(g)
        cx.fill()
        cx.arc(0, 0, R * 0.8, 0, TAU)
        cx.set_source_rgba(0.85, 0.87, 0.95, alpha)
        cx.fill()
        cx.restore()
        # contact shadow under cake
        cx.save()
        cx.translate(X, Y + 4)
        cx.scale(1, self.r / self.R)
        g = cairo.RadialGradient(0, 0, self.R * 0.85, 0, 0, self.R * 1.08)
        g.add_color_stop_rgba(0, 0, 0, 0.1, 0.35 * alpha)
        g.add_color_stop_rgba(1, 0, 0, 0.1, 0)
        cx.arc(0, 0, self.R * 1.08, 0, TAU)
        cx.set_source(g)
        cx.fill()
        cx.restore()

    # -------------------------------------------------------------- full draw
    def draw(self, cx, cut_angles=(), cut_alpha=1.0, wedge=None, pull=0.0, flag=0.0, lon0=12.0):
        """wedge=(a0, a1) in (0, pi): the slice that is pulled out by `pull` (0..1)."""
        self.plate(cx)
        if wedge and pull > 0:
            a0, a1 = wedge
            self.piping(cx, skip=(a0, a1), front=False)
            self.side(cx, 0, a0)
            self.side(cx, a1, math.pi)
            # hole: the two inner faces of the remaining cake
            self.cut_face(cx, a0, darken=0.08)
            self.cut_face(cx, a1, darken=0.0)
            self.top(cx, a_skip=(a0, a1), lon0=lon0)
            self.cuts(cx, cut_angles, cut_alpha, skip=(a0, a1))
            self.piping(cx, skip=(a0, a1), front=True)
            self.draw_wedge(cx, a0, a1, pull, flag, cut_angles, cut_alpha, lon0)
        else:
            self.piping(cx, front=False)
            self.side(cx, 0, math.pi)
            self.top(cx, lon0=lon0)
            self.cuts(cx, cut_angles, cut_alpha)
            self.piping(cx, front=True)

    def wedge_offset(self, a0, a1, pull):
        thc = 0.5 * (a0 + a1)
        d = pull * 0.95
        return (math.cos(thc) * self.R * d + pull * 70, math.sin(thc) * self.r * d + pull * 20)

    def draw_wedge(self, cx, a0, a1, pull, flag, cut_angles, cut_alpha, lon0):
        off = self.wedge_offset(a0, a1, pull)
        # shadow
        cx.save()
        x, y = self.X + off[0] + math.cos(0.5 * (a0 + a1)) * self.R * 0.55, self.Y + off[1] + self.Hc + 20
        cx.translate(x, y)
        cx.scale(1, 0.25)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, self.R * 0.6)
        g.add_color_stop_rgba(0, 0, 0, 0.1, 0.35)
        g.add_color_stop_rgba(1, 0, 0, 0.1, 0)
        cx.arc(0, 0, self.R * 0.6, 0, TAU)
        cx.set_source(g)
        cx.fill()
        cx.restore()
        self.cut_face(cx, a1, off=off, darken=0.02)
        self.side(cx, a0, a1, off=off)
        self.cut_face(cx, a0, off=off, darken=0.12) if math.cos(a0) < 0 else None
        self.top(cx, only=(a0, a1), off=off, lon0=lon0)
        self.piping(cx, only=(a0, a1), off=off)
        if flag > 0:
            # toothpick flag "YOU" planted on the wedge
            thc = 0.5 * (a0 + a1)
            bx, by = self.P(thc, 0, rr=0.62, off=off)
            hgt = 150 * flag
            cx.move_to(bx, by)
            cx.line_to(bx, by - hgt)
            cx.set_source_rgba(0.95, 0.88, 0.7, 1)
            cx.set_line_width(6)
            cx.stroke()
            if flag > 0.3:
                fw = 120 * min(1, (flag - 0.3) / 0.7)
                cx.new_path()
                cx.move_to(bx + 2, by - hgt)
                cx.curve_to(bx + fw * 0.4, by - hgt - 8, bx + fw * 0.7, by - hgt + 8, bx + fw, by - hgt + 2)
                cx.line_to(bx + fw, by - hgt + 58)
                cx.curve_to(bx + fw * 0.7, by - hgt + 64, bx + fw * 0.4, by - hgt + 48, bx + 2, by - hgt + 56)
                cx.close_path()
                cx.set_source_rgba(0.93, 0.22, 0.32, 1)
                cx.fill_preserve()
                cx.set_source_rgba(0.06, 0.06, 0.08, 1)
                cx.set_line_width(4)
                cx.stroke()
                if fw > 90:
                    from episodes.everything_divided.common import outlined
                    outlined(cx, "YOU", bx + fw / 2 + 2, by - hgt + 42, 34, ow=0, shadow=False)


# ------------------------------------------------------------------ knife
def knife(cx, x, y, ang, s=1.0, blur=0.0):
    """Chef's knife; (x, y) = blade tip, ang = rotation (rad), blade extends toward +x."""
    cx.save()
    cx.translate(x, y)
    cx.rotate(ang)
    cx.scale(s, s)
    L, Bw = 430, 78
    # drop shadow
    cx.save()
    cx.translate(10, 22)
    cx.new_path()
    cx.move_to(0, 0)
    cx.curve_to(120, -6, 300, -Bw * 0.9, L, -Bw)
    cx.line_to(L + 210, -Bw * 0.78)
    cx.line_to(L + 210, -Bw * 0.22)
    cx.line_to(L, -Bw * 0.1)
    cx.curve_to(260, 10, 120, 8, 0, 0)
    cx.set_source_rgba(0, 0, 0.05, 0.25)
    cx.fill()
    cx.restore()
    # blade
    cx.new_path()
    cx.move_to(0, 0)
    cx.curve_to(120, -6, 300, -Bw * 0.9, L, -Bw)
    cx.line_to(L, 0)
    cx.curve_to(300, 6, 120, 6, 0, 0)
    cx.close_path()
    g = cairo.LinearGradient(0, -Bw, 0, 6)
    g.add_color_stop_rgba(0, 0.96, 0.97, 1, 1)
    g.add_color_stop_rgba(0.45, 0.78, 0.81, 0.88, 1)
    g.add_color_stop_rgba(0.8, 0.6, 0.64, 0.72, 1)
    g.add_color_stop_rgba(1, 0.92, 0.94, 0.98, 1)
    cx.set_source(g)
    cx.fill_preserve()
    cx.set_source_rgba(0.12, 0.13, 0.18, 1)
    cx.set_line_width(4)
    cx.stroke()
    # bevel + edge glint
    cx.move_to(30, -2)
    cx.curve_to(150, -4, 320, -14, L - 6, -16)
    cx.set_source_rgba(1, 1, 1, 0.7)
    cx.set_line_width(3)
    cx.stroke()
    cx.move_to(60, -10)
    cx.curve_to(170, -26, 300, -Bw * 0.62, L - 10, -Bw * 0.72)
    cx.set_source_rgba(1, 1, 1, 0.35)
    cx.set_line_width(6)
    cx.stroke()
    # bolster
    cx.rectangle(L - 4, -Bw - 4, 26, Bw + 8)
    g = cairo.LinearGradient(0, -Bw, 0, 4)
    g.add_color_stop_rgba(0, 0.9, 0.9, 0.95, 1)
    g.add_color_stop_rgba(1, 0.5, 0.52, 0.6, 1)
    cx.set_source(g)
    cx.fill_preserve()
    cx.set_source_rgba(0.12, 0.13, 0.18, 1)
    cx.set_line_width(4)
    cx.stroke()
    # handle
    cx.new_path()
    cx.move_to(L + 22, -Bw * 0.86)
    cx.curve_to(L + 120, -Bw * 0.9, L + 200, -Bw * 0.86, L + 214, -Bw * 0.62)
    cx.curve_to(L + 222, -Bw * 0.45, L + 214, -Bw * 0.2, L + 196, -Bw * 0.14)
    cx.curve_to(L + 120, -Bw * 0.08, L + 60, -Bw * 0.12, L + 22, -Bw * 0.1)
    cx.close_path()
    g = cairo.LinearGradient(0, -Bw, 0, 0)
    g.add_color_stop_rgba(0, 0.55, 0.3, 0.18, 1)
    g.add_color_stop_rgba(0.5, 0.36, 0.18, 0.1, 1)
    g.add_color_stop_rgba(1, 0.22, 0.1, 0.06, 1)
    cx.set_source(g)
    cx.fill_preserve()
    cx.set_source_rgba(0.1, 0.06, 0.05, 1)
    cx.set_line_width(4)
    cx.stroke()
    for k in range(3):
        cx.arc(L + 60 + k * 55, -Bw * 0.48, 7, 0, TAU)
        cx.set_source_rgba(0.88, 0.88, 0.92, 1)
        cx.fill_preserve()
        cx.set_source_rgba(0.2, 0.2, 0.25, 1)
        cx.set_line_width(2)
        cx.stroke()
    cx.move_to(L + 40, -Bw * 0.78)
    cx.curve_to(L + 120, -Bw * 0.82, L + 180, -Bw * 0.78, L + 200, -Bw * 0.66)
    cx.set_source_rgba(1, 0.85, 0.7, 0.35)
    cx.set_line_width(4)
    cx.stroke()
    cx.restore()

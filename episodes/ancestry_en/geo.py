"""Earth globe (orthographic), Africa map and flat world map, from Natural Earth
(world-atlas 2.0.2, public domain) polygons stored in assets/geo."""
import json
import math
import os
import random

import cairo
import numpy as np

from cinecode.core import circle, hexc, rgrad, src

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEO = os.path.join(ROOT, "assets", "geo")

AFRICA = {
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
    "Central African Rep.", "Chad", "Comoros", "Congo", "Côte d'Ivoire", "Dem. Rep. Congo", "Djibouti", "Egypt",
    "Eq. Guinea", "Eritrea", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Morocco", "Mozambique", "Namibia", "Niger",
    "Nigeria", "Rwanda", "S. Sudan", "São Tomé and Principe", "Senegal", "Sierra Leone", "Somalia", "Somaliland",
    "South Africa", "Sudan", "Swaziland", "eSwatini", "Tanzania", "Togo", "Tunisia", "Uganda", "W. Sahara", "Zambia",
    "Zimbabwe",
}

OCEAN_IN = hexc("#2E7FD6")
OCEAN_OUT = hexc("#15418A")
LAND = hexc("#4FA64A")
LAND_DK = hexc("#3A8A3C")
LIGHT = hexc("#FFE89A")


def _load(name):
    return json.load(open(os.path.join(GEO, name)))


# ------------------------------------------------------------------ globe
class Globe:
    def __init__(self):
        rings = []
        for f in _load("land110.json"):
            for poly in f["polys"]:
                for ring in poly[:1]:
                    a = np.radians(np.array(ring, dtype=np.float64))
                    if len(a) >= 4:
                        rings.append(a)
        self.rings = rings
        self.lights = self._make_lights(2600)

    @staticmethod
    def _make_lights(n):
        """Land points weighted toward populous regions (for the city-light dots)."""
        from PIL import Image, ImageDraw
        Wm, Hm = 720, 360
        img = Image.new("L", (Wm, Hm), 0)
        d = ImageDraw.Draw(img)
        for f in _load("land110.json"):
            for poly in f["polys"]:
                pts = [((lo + 180) * 2, (90 - la) * 2) for lo, la in poly[0]]
                if len(pts) > 2:
                    d.polygon(pts, fill=255)
        mask = np.array(img) > 0
        hubs = [(78, 23, 1.0), (113, 30, 1.0), (10, 48, 0.8), (8, 9, 0.6), (31, 29, 0.5), (110, -6, 0.6),
                (-80, 38, 0.6), (-46, -20, 0.5), (-100, 20, 0.45), (138, 36, 0.5), (36, 0, 0.45), (45, 33, 0.4),
                (-118, 36, 0.3), (37, 55, 0.4), (30, 40, 0.4), (-60, -34, 0.3), (151, -33, 0.15), (28, -26, 0.3)]
        rnd = np.random.default_rng(7)
        out = []
        while len(out) < n:
            lo = rnd.uniform(-180, 180)
            la = rnd.uniform(-56, 72)
            if not mask[int((90 - la) * 2) % Hm, int((lo + 180) * 2) % Wm]:
                continue
            w = 0.03 + sum(k * math.exp(-((lo - a) ** 2 + (la - b) ** 2) / 120.0) for a, b, k in hubs)
            if rnd.random() < min(1.0, w):
                out.append((math.radians(lo), math.radians(la)))
        rnd.shuffle(out)
        return np.array(out)

    @staticmethod
    def project(lon, lat, lon0, lat0):
        dl = lon - lon0
        x = np.cos(lat) * np.sin(dl)
        y = math.cos(lat0) * np.sin(lat) - math.sin(lat0) * np.cos(lat) * np.cos(dl)
        z = math.sin(lat0) * np.sin(lat) + math.cos(lat0) * np.cos(lat) * np.cos(dl)
        return x, y, z

    def screen(self, lon_deg, lat_deg, X, Y, R, lon0, lat0, alt=0.0):
        x, y, z = self.project(math.radians(lon_deg), math.radians(lat_deg), math.radians(lon0), math.radians(lat0))
        return X + R * (1 + alt) * x, Y - R * (1 + alt) * y, z

    def draw(self, cx, X, Y, R, lon0, lat0, lights=1.0, t=0.0, halo=1.0):
        l0, b0 = math.radians(lon0), math.radians(lat0)
        # halo rings
        if halo > 0:
            cx.set_source(rgrad(cx, X, Y, R * 0.98, R * 1.32, [(0, (0.35, 0.55, 1.0, 0.30 * halo)), (0.45, (0.25, 0.4, 0.9, 0.12 * halo)), (1, (0.2, 0.3, 0.8, 0))]))
            circle(cx, X, Y, R * 1.32)
            cx.fill()
            circle(cx, X, Y, R * 1.12)
            src(cx, (0.16, 0.26, 0.55, 0.35 * halo))
            cx.fill()
        # ocean
        cx.set_source(rgrad(cx, X - R * 0.3, Y - R * 0.35, R * 0.1, R * 1.25, [(0, OCEAN_IN), (1, OCEAN_OUT)]))
        circle(cx, X, Y, R)
        cx.fill()
        cx.save()
        circle(cx, X, Y, R)
        cx.clip()
        # graticule
        cx.set_line_width(max(1.0, R * 0.003))
        src(cx, (1, 1, 1, 0.07))
        for lo in range(-180, 180, 30):
            lats = np.radians(np.linspace(-85, 85, 40))
            x, y, z = self.project(np.full_like(lats, math.radians(lo)), lats, l0, b0)
            self._stroke_vis(cx, X + R * x, Y - R * y, z)
        for la in range(-60, 90, 30):
            lons = np.radians(np.linspace(-180, 180, 90))
            x, y, z = self.project(lons, np.full_like(lons, math.radians(la)), l0, b0)
            self._stroke_vis(cx, X + R * x, Y - R * y, z)
        # land
        for ring in self.rings:
            x, y, z = self.project(ring[:, 0], ring[:, 1], l0, b0)
            if (z < 0).all():
                continue
            nrm = np.sqrt(x * x + y * y) + 1e-9
            back = z < 0
            x = np.where(back, x / nrm, x)
            y = np.where(back, y / nrm, y)
            sx, sy = X + R * x, Y - R * y
            cx.move_to(sx[0], sy[0])
            for i in range(1, len(sx)):
                cx.line_to(sx[i], sy[i])
            cx.close_path()
        src(cx, LAND)
        cx.fill_preserve()
        src(cx, LAND_DK)
        cx.set_line_width(max(1.0, R * 0.006))
        cx.stroke()
        # city lights
        n = int(len(self.lights) * max(0.0, min(1.0, lights)))
        if n:
            L = self.lights[:n]
            x, y, z = self.project(L[:, 0], L[:, 1], l0, b0)
            vis = z > 0.05
            rr = max(1.2, R * 0.0055)
            for sx, sy, zz in zip(X + R * x[vis], Y - R * y[vis], z[vis]):
                cx.rectangle(sx - rr, sy - rr, 2 * rr, 2 * rr)
            src(cx, (*LIGHT[:3], 0.85))
            cx.fill()
        # shading: terminator-ish vignette + highlight
        cx.set_source(rgrad(cx, X - R * 0.35, Y - R * 0.4, R * 0.2, R * 1.45, [(0, (1, 1, 1, 0.10)), (0.55, (0, 0, 0, 0.0)), (1, (0, 0.02, 0.1, 0.55))]))
        cx.paint()
        cx.restore()
        # rim light
        circle(cx, X, Y, R)
        src(cx, (0.6, 0.8, 1.0, 0.35))
        cx.set_line_width(max(1.5, R * 0.01))
        cx.stroke()

    @staticmethod
    def _stroke_vis(cx, sx, sy, z):
        pen = False
        for i in range(len(sx)):
            if z[i] > 0:
                if pen:
                    cx.line_to(sx[i], sy[i])
                else:
                    cx.move_to(sx[i], sy[i])
                    pen = True
            else:
                pen = False
        cx.stroke()

    def arc(self, cx, a, b, X, Y, R, lon0, lat0, frac=1.0, color=(1.0, 0.85, 0.3), alpha=0.6, lw=2.0, lift=0.18):
        """Great-circle arc lifted above the surface from a=(lon,lat) to b, partially drawn up to frac."""
        if frac <= 0:
            return
        la1, lo1 = math.radians(a[1]), math.radians(a[0])
        la2, lo2 = math.radians(b[1]), math.radians(b[0])
        p1 = np.array([math.cos(la1) * math.cos(lo1), math.cos(la1) * math.sin(lo1), math.sin(la1)])
        p2 = np.array([math.cos(la2) * math.cos(lo2), math.cos(la2) * math.sin(lo2), math.sin(la2)])
        om = math.acos(max(-1, min(1, p1 @ p2)))
        if om < 1e-4:
            return
        n = 40
        ts = np.linspace(0, frac, n)
        pts = (np.sin((1 - ts)[:, None] * om) * p1 + np.sin(ts[:, None] * om) * p2) / math.sin(om)
        lat = np.arcsin(np.clip(pts[:, 2], -1, 1))
        lon = np.arctan2(pts[:, 1], pts[:, 0])
        h = 1 + lift * om / math.pi * 2 * np.sin(np.pi * ts)
        x, y, z = self.project(lon, lat, math.radians(lon0), math.radians(lat0))
        sx, sy = X + R * h * x, Y - R * h * y
        # visible if in front or outside the disc silhouette
        vis = (z > 0) | ((x * x * h * h + y * y * h * h > 1.0) & (z > -0.35))
        cx.set_line_width(lw)
        cx.set_line_cap(cairo.LINE_CAP_ROUND)
        src(cx, (*color, alpha))
        self._stroke_vis(cx, sx, sy, np.where(vis, 1, -1))


# ------------------------------------------------------------------ Africa map
class AfricaMap:
    LON0, LON1, LAT0, LAT1 = -19.0, 52.5, 38.5, -35.5

    def __init__(self):
        self.polys = []
        for f in _load("countries50.json"):
            if f["name"] in AFRICA:
                for poly in f["polys"]:
                    self.polys.append(np.array(poly[0]))

    def draw(self, cx, x, y, w, alpha=1.0, fill=hexc("#3A2830"), stroke=hexc("#1A1015")):
        """Map's top-left at (x, y), width w."""
        if alpha <= 0:
            return
        k = w / (self.LON1 - self.LON0)
        cx.push_group()
        for p in self.polys:
            cx.move_to(x + (p[0, 0] - self.LON0) * k, y + (self.LAT0 - p[0, 1]) * k)
            for lo, la in p[1:]:
                cx.line_to(x + (lo - self.LON0) * k, y + (self.LAT0 - la) * k)
            cx.close_path()
        src(cx, fill)
        cx.fill_preserve()
        src(cx, stroke)
        cx.set_line_width(2.0)
        cx.stroke()
        cx.pop_group_to_source()
        cx.paint_with_alpha(alpha)

    def height(self, w):
        return w * (self.LAT0 - self.LAT1) / (self.LON1 - self.LON0)


# ------------------------------------------------------------------ flat world map
class FlatMap:
    """Equirectangular map, longitudes -25..355 so the Pacific/Americas sit east of Asia."""
    LON0, LON1, LAT0, LAT1 = -25.0, 355.0, 82.0, -58.0
    PPD = 14.0  # pixels per degree in the cached raster

    def __init__(self):
        self.w = int((self.LON1 - self.LON0) * self.PPD)
        self.h = int((self.LAT0 - self.LAT1) * self.PPD)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        cx = cairo.Context(surf)
        cx.set_source(cairo.LinearGradient(0, 0, 0, self.h))
        g = cairo.LinearGradient(0, 0, 0, self.h)
        g.add_color_stop_rgba(0, *hexc("#1B3F7A"))
        g.add_color_stop_rgba(0.5, *hexc("#1F4C8E"))
        g.add_color_stop_rgba(1, *hexc("#173A72"))
        cx.set_source(g)
        cx.paint()
        for f in _load("countries50.json"):
            if f["name"] == "Antarctica":
                continue
            for poly in f["polys"]:
                p = np.array(poly[0], dtype=float)
                if p[:, 0].max() - p[:, 0].min() > 180:  # crosses the antimeridian (Russia, Fiji)
                    p[p[:, 0] < 0, 0] += 360
                elif p[:, 0].mean() < self.LON0:
                    p[:, 0] += 360
                sx, sy = self.xy(p[:, 0], p[:, 1])
                cx.move_to(sx[0], sy[0])
                for i in range(1, len(sx)):
                    cx.line_to(sx[i], sy[i])
                cx.close_path()
        src(cx, hexc("#3F8A44"))
        cx.fill_preserve()
        src(cx, hexc("#2C6631"))
        cx.set_line_width(1.6)
        cx.stroke()
        self.surf = surf

    def xy(self, lon, lat):
        return (np.asarray(lon) - self.LON0) * self.PPD, (self.LAT0 - np.asarray(lat)) * self.PPD

    def pt(self, lon, lat):
        if lon < self.LON0:
            lon += 360
        x, y = self.xy(lon, lat)
        return float(x), float(y)

    def draw(self, cx, cam_x, cam_y, zoom, W, H):
        """Show map point (cam_x, cam_y) (raster px) at screen centre, scale zoom."""
        cx.save()
        cx.translate(W / 2, H / 2)
        cx.scale(zoom, zoom)
        cx.translate(-cam_x, -cam_y)
        cx.set_source_surface(self.surf, 0, 0)
        cx.get_source().set_filter(cairo.FILTER_GOOD)
        cx.paint()
        cx.restore()

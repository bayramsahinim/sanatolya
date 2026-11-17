"""Shots 1-12: waking up, the numbers, the mirror, subway, baker, coworker, Mom."""
import math

from .cast import (BAKER, COWORKER, CROWD, HERO, MOM, Arms, Face, blink_at, bust, person)
from .frame import Shot
from .look import (BLUE, GLOW_BLUE, GREY1, GREY2, H, LINE, LINE_DIM, W, WHITE, XL, XR, back_out, bg, clamp, count, land,
                   ease_io, ease_out, gline, glow_blob, grect, hexc, lerp, number, prog, rrect, smooth,
                   src, text, vignette)
from . import sets as S


# ------------------------------------------------------------------ helpers
def pop(t, t0, d=0.35):
    """0..1 appear amount with a soft overshoot."""
    x = prog(t, t0, t0 + d)
    return back_out(x) if x < 1 else 1.0


def num_pop(f, n, x, y, size, t, t0, a=1.0, glow=1.0):
    k = prog(t, t0, t0 + 0.4)
    if k <= 0:
        return
    sc = 0.7 + 0.3 * back_out(k)
    f.save()
    for c in (f.cx, f.gx):
        c.translate(x, y)
        c.scale(sc, sc)
        c.translate(-x, -y)
    flash = 1.0 + 0.8 * (1 - prog(t, t0, t0 + 0.6))
    number(f, n, x, y, size, a * smooth(k), glow * flash)
    f.restore()


def rolling(t, t0, t1, v0, v1):
    return count(t, t0, t1, v0, v1, ease_io)


def push(f, t, dur, z0=1.0, z1=1.08, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    k = ease_io(prog(t, 0, dur))
    f.cam(cx + dx * k, cy + dy * k, lerp(z0, z1, k))


def back_face():
    return Face(view="back")


# ------------------------------------------------------------------ S1
class S01Wake(Shot):
    lines = ["L01"]
    lead = 0.9
    tail = 0.45

    def sfx(self):
        return [(0.0, "amb_room", 0.5), (0.25, "chime_soft", 0.5)]

    def draw(self, f, t):
        bg(f, spot=(540, 900), spot_a=0.06)
        f.save()
        push(f, t, self.dur, 1.0, 1.07, cy=930)
        light = smooth(prog(t, 0.0, 2.2))
        S.room(f, back=(230, 470, 850, 1130))
        S.window(f, 400, 560, 280, 330, light=light)
        # dawn beam
        c = f.cx
        c.move_to(400, 890)
        c.line_to(680, 890)
        c.line_to(900, 1400)
        c.line_to(260, 1400)
        c.close_path()
        src(c, hexc("#dfe8ff"), 0.05 * light)
        c.fill()
        # hero sits up behind the blanket
        up = ease_io(prog(t, 0.55, 1.6))
        ny = lerp(1330, 1150, up)
        face = Face(eyes="closed" if t < 1.0 else "open", brows="neutral", mouth="flat",
                    blink=blink_at(t, 1), look=(0.0 if t < 1.7 else math.sin((t - 1.7) * 2.2) * 0.5, -0.1))
        bust(f, 540, ny, 105, HERO, face, Arms(l=(10, 0), r=(10, 0)), T=400, tilt=lerp(-14, 0, up))
        # bed / blanket front
        rrect(c, 120, 1240, 840, 420, 40)
        src(c, hexc("#262a33"))
        c.fill()
        grect(f, 120, 1240, 840, 420, 40, LINE, 3, glow=0.5)
        for i in range(4):
            gline(f, [(160 + i * 210, 1270), (220 + i * 210, 1400)], LINE_DIM, 2, 0.6, glow=0)
        grect(f, 70, 1080, 50, 600, 10, LINE, 3, fillc=hexc("#1b1e25"))
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S2
CROWD_NUMS = [47, 6845, 774, 11, 1180, 495, 36, 1033, 809]


class S02Numbers(Shot):
    lines = ["L02", "L03", "L04"]
    lead = 0.3
    tail = 0.45

    def sfx(self):
        out = [(0.0, "amb_street", 0.6)]
        for i in range(len(CROWD_NUMS)):
            out.append((self.s("L02", 0.25) + i * 0.17, "num_tick", 0.35))
        out.append((self.s("L04"), "swell", 0.35))
        return out

    def draw(self, f, t):
        bg(f, spot=(540, 820), spot_a=0.07)
        f.save()
        z = lerp(1.0, 1.0, 0)
        kpush = ease_io(prog(t, self.s("L04") - 0.2, self.e("L04")))
        f.cam(540, lerp(960, 860, kpush), lerp(1.0, 1.16, kpush))
        # street: faint buildings + pavement lines
        blds = ((-20, 260, 900), (250, 230, 720), (490, 300, 1000), (800, 300, 820))
        if land():
            blds = ((-1060, 280, 860), (-770, 250, 980), (-500, 240, 760), (-270, 260, 940)) + blds + \
                   ((1110, 270, 940), (1390, 240, 780), (1640, 300, 900), (1950, 260, 820))
        for i, (bx, bw, bh) in enumerate(blds):
            grect(f, bx, 1000 - bh, bw, bh, 4, LINE_DIM, 2.2, 0.8, glow=0.25, fillc=hexc("#12151b"))
            for r in range(int(bh / 110)):
                for k in range(int(bw / 80)):
                    if (r * 7 + k * 3 + i) % 4 == 0:
                        f.cx.rectangle(bx + 25 + k * 80, 1000 - bh + 40 + r * 110, 40, 55)
                        src(f.cx, hexc("#e7ecf7"), 0.18)
                        f.cx.fill()
        gline(f, [(XL, 1000), (XR, 1000)], LINE, 2.4, 0.9)
        for i in range(-14 if land() else -6, 15 if land() else 7):
            gline(f, [(540 + i * 60, 1000), (540 + i * 260, 1600)], LINE_DIM, 1.4, 0.35, glow=0)
        # crowd: back row then front row
        pos = [(120, 1110, 46), (330, 1100, 46), (540, 1105, 46), (750, 1100, 46), (960, 1110, 46),
               (225, 1290, 60), (435, 1300, 60), (645, 1295, 60), (855, 1290, 60)]
        t_num = self.s("L02", 0.25)
        nums = list(CROWD_NUMS)
        if land():
            # widescreen: the crowd continues to both sides (numbers pop with the same ticks)
            pos = [(-300, 1105, 46), (-90, 1110, 46), (1170, 1105, 46), (1380, 1110, 46),
                   (-405, 1295, 60), (15, 1290, 60), (1065, 1295, 60), (1485, 1290, 60)] + pos
            nums = [62, 3, 920, 15, 2310, 8, 140, 27] + nums
        order = list(range(len(pos)))
        for i, ((x, g, R), sp) in enumerate(zip(pos, CROWD * 4)):
            sw = math.sin(t * 1.3 + i) * 3
            fc = Face(look=(math.sin(t * 0.4 + i * 1.7) * 0.4, 0), mouth=["small", "flat", "smile"][i % 3],
                      blink=blink_at(t, i + 3))
            hx, hy = person(f, x + sw, g, R, sp, fc)
            # numbers: L03 dims them to grey "labels", L04 brightens
            dim = 1.0 - 0.45 * (prog(t, self.s("L03"), self.s("L03") + 0.3) - prog(t, self.s("L04") - 0.2, self.s("L04") + 0.3))
            num_pop(f, nums[i], hx, hy - R * 1.75, 44 if R < 55 else 52, t, t_num + (i % 9) * 0.17, a=dim,
                    glow=0.8 + 0.6 * kpush)
        # L03: "not their age / not their IQ" strike tags
        for k, (lab, xx, yy, frac) in enumerate((("AGE", 330, 560, 0.0), ("IQ", 740, 600, 0.5))):
            t0 = self.s("L03", frac)
            a = smooth(prog(t, t0, t0 + 0.25)) * (1 - smooth(prog(t, self.s("L04") - 0.3, self.s("L04"))))
            if a > 0:
                text(f, lab, xx, yy, 64, GREY1, a, glow=0.3)
                ks = prog(t, t0 + 0.35, t0 + 0.6)
                gline(f, [(xx - 70, yy - 22), (xx - 70 + 140 * ks, yy - 22)], WHITE, 6, a * (ks > 0), glow=0.8)
        # hero from behind, foreground
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S3 / S23 mirror
def mirror_scene(f, t, face, above=None, extras=0.0, blur_num=0.0, dur=4.0):
    bg(f, spot=(540, 650), spot_a=0.06)
    S.room(f, back=(170, 230, 910, 1250), a=0.8, floor_lines=1)
    mx, my, mw, mh = 220, 240, 640, 780
    inner = S.mirror(f, mx, my, mw, mh)
    c = f.cx
    c.save()
    rrect(c, inner[0], inner[1], inner[2], inner[3], 24)
    c.clip()
    f.gx.save()
    rrect(f.gx, inner[0], inner[1], inner[2], inner[3], 24)
    f.gx.clip()
    # reflection: back wall + people behind + hero facing us
    if extras > 0:
        from .cast import DAUGHTER, FRIEND
        for (sp, x, R, fc) in ((MOM, 330, 58, Face(mouth="smile", brows="soft")),
                                (FRIEND, 760, 58, Face(mouth="smile")),
                                (DAUGHTER.but(hair="ponytail"), 640, 52, Face(mouth="smile", look=(-0.3, 0)))):
            bust(f, x, 760, R, sp, fc, a=0.55 * extras, T=300)
    bust(f, 540, 830, 105, HERO, face, a=0.92, T=400)
    if blur_num > 0:
        # an unreadable glowing number above the reflection: only others can read it
        glow_blob(f, 540, 520, 150, WHITE, 0.55 * blur_num)
        glow_blob(f, 540, 520, 90, GLOW_BLUE, 0.4 * blur_num)
    # glass tint
    c.rectangle(inner[0], inner[1], inner[2], inner[3])
    src(c, hexc("#a8b8d8"), 0.06)
    c.fill()
    c.restore()
    f.gx.restore()
    if above is not None:
        a = above
        # a faint dashed ring where a number should be... and nothing
        for i in range(16):
            th = i / 16 * 2 * math.pi + t * 0.2
            x0, y0 = 540 + math.cos(th) * 70, 545 + math.sin(th) * 40
            x1, y1 = 540 + math.cos(th + 0.18) * 70, 545 + math.sin(th + 0.18) * 40
            gline(f, [(x0, y0), (x1, y1)], WHITE, 3, a * 0.5, glow=0.5)
    S.sink(f, 540, 1060, 520)
    # hero from behind in the foreground
    vignette(f)


class S03Mirror(Shot):
    lines = ["L05"]
    lead = 0.25
    tail = 0.5

    def sfx(self):
        return [(0.0, "amb_room", 0.4), (self.s("L05", 0.55), "empty_tone", 0.4)]

    def draw(self, f, t):
        f.save()
        push(f, t, self.dur, 1.0, 1.12, cy=900, dy=-140)
        k = prog(t, self.s("L05", 0.5), self.s("L05", 0.5) + 0.6)
        mirror_scene(f, t, Face(look=(0, -0.6 * k), brows="raised" if k > 0.3 else "neutral", mouth="flat",
                                eyes="open", blink=blink_at(t, 2)),
                     above=smooth(k) * (1 - smooth(prog(t, self.dur - 0.6, self.dur))))
        f.restore()


# ------------------------------------------------------------------ S4 subway
class S04Subway(Shot):
    lines = ["L06", "L07"]
    lead = 0.3
    tail = 0.5

    def sfx(self):
        return [(0.0, "amb_subway", 0.7), (self.s("L06", 0.8), "num_tick", 0.3), (self.s("L06", 0.85), "num_tick", 0.25),
                (self.s("L07"), "low_note", 0.45), (self.s("L07", 0.6), "doors", 0.35)]

    def draw(self, f, t):
        bg(f)
        f.save()
        k = ease_io(prog(t, self.s("L07") - 0.2, self.e("L07")))
        f.cam(540, lerp(960, 820, k), lerp(1.0, 1.18, k))
        sway = math.sin(t * 2.1) * 1.0
        S.subway(f, t, sway=sway)
        tn = self.s("L06", 0.78)
        leave = smooth(prog(t, self.s("L07", 0.55), self.e("L07") + 0.3))
        people = [(300, 1120, 46, CROWD[1]), (430, 1110, 44, CROWD[0]), (650, 1110, 44, CROWD[3]),
                  (780, 1120, 46, CROWD[2]), (120, 1330, 66, CROWD[5]), (960, 1330, 66, CROWD[4])]
        if land():
            people = [(-330, 1330, 66, CROWD[6]), (-120, 1120, 46, CROWD[7]), (1200, 1120, 46, CROWD[0]),
                      (1410, 1330, 66, CROWD[3])] + people
        for i, (x, g, R, sp) in enumerate(people):
            a = 1 - leave * (0.85 if i % 2 == 0 else 1.0)
            fc = Face(look=(0.5 if x < 540 else -0.5, 0.2), mouth="flat", eyes="half" if i % 3 == 0 else "open",
                      blink=blink_at(t, i))
            hx, hy = person(f, x + sway * (1 + i % 2), g, R, sp, fc, a=a)
            num_pop(f, "1", hx, hy - R * 1.7, 64 if R > 55 else 54, t, tn + (i % 6) * 0.06, a=a, glow=1.0 + 0.5 * k)
        # hero standing, holding the pole, front view, looking around
        fc = Face(look=(math.sin(t * 0.9) * 0.7, -0.2), brows="raised", mouth="flat", blink=blink_at(t, 5))
        person(f, 540 + sway * 2, 1330, 80, HERO, fc, Arms(l=(8, 0), r=(150, 20)))
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S5 bakery
class S05Baker(Shot):
    lines = ["L08"]
    lead = 0.25
    tail = 0.4

    def sfx(self):
        t0 = self.s("L08", 0.5)
        return [(0.0, "amb_shop", 0.55), (0.1, "bell", 0.35), (t0, "count_up", 0.45)]

    def draw(self, f, t):
        bg(f, spot=(540, 700), spot_a=0.08)
        f.save()
        push(f, t, self.dur, 1.0, 1.06, cy=900)
        S.bakery(f)
        fc = Face(mouth="big" if (t % 1.6) < 0.8 else "smile", brows="raised", eyes="happy" if t > self.s("L08", 0.6) else "open",
                  blink=blink_at(t, 7), look=(0.2, 0.1))
        hx, hy = person(f, 540, 1200, 92, BAKER, fc, Arms(l=(25, 30), r=(30, 40)))
        S.counter(f, -380 if land() else 120, 1080, 1840 if land() else 840, 330)
        # bread on counter
        for i, bx in enumerate((300, 780)):
            from .look import ellipse
            ellipse(f.cx, bx, 1062, 60, 26)
            src(f.cx, hexc("#9a9fab"))
            f.cx.fill_preserve()
            src(f.cx, hexc("#0b0c10"))
            f.cx.set_line_width(3)
            f.cx.stroke()
        t0 = self.s("L08", 0.5)
        v = rolling(t, t0, t0 + 1.1, 0, 2140)
        num_pop(f, v, hx, hy - 175, 92, t, t0 - 0.1)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S6 coworker
class S06Coworker(Shot):
    lines = ["L09"]
    lead = 0.3
    tail = 0.4

    def sfx(self):
        t0 = self.s("L09", 0.55)
        return [(0.0, "amb_office", 0.5), (t0, "count_up", 0.45)]

    def draw(self, f, t):
        bg(f)
        f.save()
        push(f, t, self.dur, 1.0, 1.06, cy=960)
        S.office(f)
        # coworker leaning over the partition, talking
        talk = (t * 5) % 1 < 0.5 and t < self.e("L09")
        fc = Face(mouth="open" if talk else "big", brows="raised", look=(-0.4, 0), blink=blink_at(t, 9))
        hx, hy = person(f, 760, 1260, 92, COWORKER, fc, Arms(l=(40, 60), r=(10, 0)))
        S.desk(f, 60, 1130, 520, monitor=True, plant=True)
        # hero at the desk: flat, unimpressed
        fc2 = Face(look=(0.6, 0), brows="frown", mouth="flat", eyes="half", blink=blink_at(t, 2))
        bust(f, 300, 1250, 92, HERO, fc2, T=260)
        grect(f, 30, 1360, 600, 300, 8, LINE, 3, fillc=hexc("#1b1e25"))
        t0 = self.s("L09", 0.55)
        v = rolling(t, t0, t0 + 1.1, 0, 3900)
        num_pop(f, v, hx, hy - 175, 92, t, t0 - 0.1)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S7 who you see most
class S07Chosen(Shot):
    lines = ["L10"]
    lead = 0.35
    tail = 0.55

    def sfx(self):
        return [(0.0, "amb_void", 0.6), (0.2, "swell", 0.3)]

    def draw(self, f, t):
        bg(f, spot=(540, 900), spot_a=0.06)
        f.save()
        k = ease_io(prog(t, 0, self.dur))
        f.cam(540, 930, lerp(1.12, 1.0, k))
        gline(f, [(XL, 1110), (XR, 1110)], LINE_DIM, 2, 0.6)
        people = [(220, 1110, 56, CROWD[1], "1", 0.55), (540, 1110, 70, BAKER, "2,140", 0.85), (860, 1110, 76, COWORKER, "3,900", 1.0)]
        for i, (x, g, R, sp, n, br) in enumerate(people):
            fc = Face(look=(0, 0), mouth="smile" if i else "flat", blink=blink_at(t, i + 4))
            hx, hy = person(f, x, g, R, sp, fc, a=0.9)
            number(f, n, hx, hy - R * 1.9, 46 + R * 0.5, a=br * smooth(prog(t, 0.1 + i * 0.25, 0.5 + i * 0.25)), glow=br)
        # hero, small, front, looking up at them
        fc = Face(look=(0.3, -0.7), brows="sad", mouth="flat", blink=blink_at(t, 1))
        person(f, 540, 1580, 72, HERO, fc)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S8 Mom calls
class S08Call(Shot):
    lines = ["L11"]
    lead = 0.5
    tail = 0.4

    def sfx(self):
        return [(0.05, "buzz", 0.5), (0.85, "buzz", 0.45), (self.s("L11", 0.3), "pickup", 0.4)]

    def draw(self, f, t):
        bg(f, spot=(540, 760), spot_a=0.05)
        f.save()
        push(f, t, self.dur, 1.0, 1.05, cy=900)
        picked = t > self.s("L11", 0.3)
        shake = math.sin(t * 60) * 5 * (1 - picked) * (math.sin(t * 6) > 0)
        sx, sy, sw, sh = S.phone(f, 540 + shake, 780, 500, 900)
        cx = 540 + shake
        if not picked:
            for r in range(3):
                ph = (t * 0.9 + r / 3) % 1
                from .look import gcircle
                gcircle(f, cx, 640, 90 + ph * 140, WHITE, 3, (1 - ph) * 0.5, glow=0.5)
        S.avatar(f, cx, 640, 90)
        text(f, "Mom", cx, 800, 64, WHITE, glow=0.4)
        if not picked:
            text(f, "calling...", cx, 856, 32, GREY2)
            for bx, col in ((cx - 140, hexc("#e14b4b")), (cx + 140, hexc("#3fbf6a"))):
                f.cx.arc(bx, 1100, 52, 0, 2 * math.pi)
                src(f.cx, col, 0.85)
                f.cx.fill()
        else:
            secs = int(t - self.s("L11", 0.3))
            text(f, f"00:{secs:02d}", cx, 856, 32, GREY1)
            # voice bars: Mom (white) then you (blue)
            mine = t > self.s("L11", 0.62)
            speaking = (t < self.s("L11", 0.55)) or (self.s("L11", 0.66) < t < self.e("L11") - 0.6)
            for i in range(9):
                hgt = 18 + (abs(math.sin(t * 9 + i * 1.3)) * 70 if speaking else 6)
                rrect(f.cx, cx - 180 + i * 42, 960 - hgt / 2, 16, hgt, 8)
                src(f.cx, BLUE if mine else WHITE, 0.9)
                f.cx.fill()
                rrect(f.gx, cx - 180 + i * 42, 960 - hgt / 2, 16, hgt, 8)
                src(f.gx, BLUE if mine else WHITE, 0.6)
                f.gx.fill()
            f.cx.arc(cx, 1100, 52, 0, 2 * math.pi)
            src(f.cx, hexc("#e14b4b"), 0.85)
            f.cx.fill()
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S9-S12 Mom's door
def mom_door(f, t, openk, light, mom_face, num=None, num_a=1.0, hero=True, hero_face=None, num_t0=None, mom_a=1.0):
    bg(f, top=hexc("#121419"), bot=hexc("#07080a"))
    # house wall
    for i in range(14):
        x0, x1 = (XL, XR) if land() else (0, W)
        gline(f, [(x0, 260 + i * 80), (x1, 260 + i * 80)], LINE_DIM, 1.2, 0.18, glow=0)
    S.wall_lamp(f, 200, 520, on=light)
    if land():
        S.wall_lamp(f, 880, 520, on=light)
        S.window(f, -420, 560, 300, 360, 0.6, light=0.25 * light)
        S.window(f, 1200, 560, 300, 360, 0.6, light=0.25 * light)
    S.door(f, 330, 470, 420, 820, openk=openk, inside_light=light * openk)
    if openk > 0.3:
        a = smooth(prog(openk, 0.3, 0.8)) * mom_a
        hx, hy = person(f, 520, 1290, 90, MOM, mom_face, a=a)
        if num is not None:
            if num_t0 is not None:
                num_pop(f, num, hx, hy - 170, 110, t, num_t0, a=a * num_a)
            else:
                number(f, num, hx, hy - 170, 110, a=a * num_a)


class S09Door(Shot):
    lines = ["L12"]
    lead = 0.3
    tail = 0.5

    def sfx(self):
        return [(0.0, "amb_night", 0.5), (0.25, "knock", 0.5), (self.s("L12", 0.35), "door_open", 0.45),
                (self.s("L12", 0.86), "num_reveal", 0.5)]

    def draw(self, f, t):
        f.save()
        push(f, t, self.dur, 1.0, 1.08, cy=920, dy=-40)
        openk = ease_io(prog(t, self.s("L12", 0.35), self.s("L12", 0.35) + 0.9))
        mom_door(f, t, openk, 1.0, Face(mouth="big", brows="raised", eyes="happy" if t > self.s("L12", 0.7) else "open",
                                      blink=blink_at(t, 3)), num=17, num_t0=self.s("L12", 0.86))
        f.restore()
        vignette(f)


class S10Math(Shot):
    lines = ["L13"]
    lead = 0.3
    tail = 0.45

    def sfx(self):
        out = [(0.0, "amb_void", 0.4)]
        t0, t1 = self.s("L13", 0.18), self.s("L13", 0.78)
        for i in range(17):
            out.append((t0 + (t1 - t0) * i / 16, "num_tick", 0.22))
        out.append((self.s("L13", 0.85), "chime_soft", 0.5))
        return out

    def draw(self, f, t):
        bg(f, spot=(540, 820), spot_a=0.05)
        f.save()
        push(f, t, self.dur, 1.04, 1.0, cy=900)
        if land():
            # widescreen: Mom beside the card instead of behind it
            hx, hy = person(f, 1120, 1240, 110, MOM, Face(mouth="smile", look=(-0.3, 0), blink=blink_at(t, 2)), a=0.85)
            x, y, w, h = -230, 300, 840, 900
        else:
            # Mom faint in the background
            person(f, 540, 1500, 120, MOM, Face(mouth="smile", blink=blink_at(t, 2)), a=0.25)
            x, y, w, h = 120, 300, 840, 900
        # glass card
        rrect(f.cx, x, y, w, h, 40)
        src(f.cx, hexc("#151821"), 0.88)
        f.cx.fill()
        grect(f, x, y, w, h, 40, WHITE, 3, 0.9, glow=0.6)
        text(f, "A year: 2 holidays + her birthday", x + 50, y + 80, 34, GREY1, align="left")
        gline(f, [(x + 50, y + 110), (x + w - 50, y + 110)], LINE_DIM, 2, 0.6, glow=0)
        t0, t1 = self.s("L13", 0.18), self.s("L13", 0.78)
        lit = int(clamp((t - t0) / (t1 - t0)) * 17 + (1 if t >= t0 else 0))
        lit = min(lit, 17)
        kinds = ["star", "star", "cake"]
        for i in range(18):
            r, k = divmod(i, 3)
            ix, iy = x + 90 + k * 110, y + 190 + r * 115
            on = i < lit
            S.icon(f, kinds[k], ix, iy, 64, a=1.0 if on else 0.18, col=WHITE if on else GREY2)
            if k == 0:
                text(f, f"year {r + 1}", ix - 40, iy + 50, 20, GREY2, 0.7 if on else 0.3, align="left")
        # counter
        ok = prog(t, self.s("L13", 0.85), self.s("L13", 0.85) + 0.4)
        number(f, lit, x + 640, y + 470, 230, a=1.0, glow=1.0 + ok, halo=True)
        text(f, "times", x + 640, y + 600, 36, GREY1)
        if ok > 0:
            gline(f, [(x + 560, y + 660), (x + 600, y + 700), (x + 720, y + 620)], hexc("#7fe0a0"), 9, smooth(ok), glow=0.8)
        f.restore()
        vignette(f)


class S11Stay(Shot):
    lines = ["L14"]
    lead = 0.3
    tail = 0.35

    def sfx(self):
        return [(0.0, "amb_night", 0.5), (0.0, "crickets", 0.25)]

    def draw(self, f, t):
        f.save()
        hero_turn = t > self.s("L14", 0.55)
        k = ease_io(prog(t, 0, self.dur))
        f.cam(lerp(560, 620, k), 960, 1.12)
        mom_face = Face(mouth="small" if not hero_turn else "sad", brows="soft" if not hero_turn else "sad",
                        blink=blink_at(t, 6), look=(0.4, 0.2))
        mom_door(f, t, 1.0, 1.0, mom_face, num=17, hero=False)
        # hero front-ish at the right, looking away when answering
        hf = Face(look=(-0.6, 0) if not hero_turn else (0.7, 0.1), mouth="small" if not hero_turn else "flat",
                  brows="neutral" if not hero_turn else "sad", blink=blink_at(t, 2))
        person(f, 900, 1640, 105, HERO, hf, Arms(l=(8, 0), r=(8, 0)))
        f.restore()
        vignette(f)


class S12Close(Shot):
    lines = ["L15"]
    lead = 0.15
    tail = 0.75

    def sfx(self):
        return [(0.0, "amb_night", 0.45), (0.1, "door_close", 0.6), (self.s("L15", 0.82), "num_drop", 0.55)]

    def draw(self, f, t):
        f.save()
        push(f, t, self.dur, 1.0, 1.1, cy=900, dy=-60)
        openk = 1 - ease_io(prog(t, 0.05, 0.75))
        mom_face = Face(mouth="sad", brows="sad", blink=blink_at(t, 6), look=(0.4, 0.2))
        mom_door(f, t, openk, 1.0, mom_face, num=None, hero=False)
        tc = self.s("L15", 0.82)
        roll = prog(t, tc, tc + 0.35)
        n = "17" if roll < 0.5 else "16"
        y = 560 + (roll * 30 if roll < 0.5 else (1 - roll) * -30)
        glow = 1.0 + 1.2 * (1 - prog(t, tc + 0.2, tc + 1.0)) * (roll > 0.5)
        number(f, n, 540, y, 150, a=1.0 - 0.4 * abs(math.sin(roll * math.pi)), glow=glow)
        f.restore()
        vignette(f)


SHOTS_A = [S01Wake, S02Numbers, S03Mirror, S04Subway, S05Baker, S06Coworker, S07Chosen, S08Call, S09Door,
           S10Math, S11Stay, S12Close]

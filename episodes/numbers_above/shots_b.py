"""Shots 13-24: the city, daughter, Dad, contacts, best friend, coffee, the turn, the mirror, ending."""
import math
import random

from .cast import (COWORKER, CROWD, DAD, DAUGHTER, FRIEND, HERO, MOM, Arms, Face, blink_at, bust, person)
from .frame import Shot
from .look import (BLUE, BLUE_L, GLOW_BLUE, GREY1, GREY2, GREY3, H, INK, LINE, LINE_DIM, W, WHITE, XL, XR, bg, clamp, land,
                   ease_io, ease_out, gcircle, gline, glow_blob, grect, hexc, lerp, number, prog, rrect, smooth,
                   src, text, text_w, vignette, fmt)
from .shots_a import back_face, mom_door, mirror_scene, num_pop, push, rolling
from . import sets as S


# ------------------------------------------------------------------ S13 city
class S13City(Shot):
    lines = ["L16", "L17"]
    lead = 0.4
    tail = 0.5

    def sfx(self):
        return [(0.0, "amb_city", 0.6), (0.1, "swell", 0.25)]

    def draw(self, f, t):
        bg(f, top=hexc("#10131a"), bot=hexc("#07080b"))
        # moon + faint stars
        rng = random.Random(2)
        for i in range(130 if land() else 60):
            x, y = (XL * 0.6 + rng.random() * (XR - XL) * 0.6) if land() else rng.random() * W, rng.random() * 700
            f.cx.arc(x, y, 1.6, 0, 6.3)
            src(f.cx, WHITE, 0.25 + 0.2 * math.sin(t * 2 + i))
            f.cx.fill()
        glow_blob(f, 800, 300, 160, hexc("#dfe8ff"), 0.25)
        gcircle(f, 800, 300, 46, WHITE, 3, 0.8, glow=0.8, fillc=hexc("#1c2230"))
        f.save()
        k = ease_io(prog(t, 0, self.dur))
        f.cam(540, lerp(1050, 900, k), lerp(1.0, 1.1, k))
        S.city(f, t, nums=[3, 12, 41, 7, 260, 18, 95, 4, 33, 150, 2, 64, 9, 1], seed=11)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S14 daughter
DAUGHTER_STAGES = [  # (R, spec tweaks, number at end of stage)
    (52, dict(hair="pigtails"), 6400),
    (60, dict(hair="pigtails", backpack=True), 4742),
    (66, dict(hair="ponytail", grad_cap=True, body="coat"), 1630),
    (68, dict(hair="long", body="coat"), 96),
]


class S14Daughter(Shot):
    lines = ["L18", "L19", "L20"]
    lead = 0.3
    tail = 0.55
    gaps = {"L20": 0.6}

    def sfx(self):
        out = [(0.0, "amb_void", 0.5), (self.s("L18", 0.3), "num_reveal", 0.4), (self.s("L18", 0.6), "count_down", 0.4)]
        for fr in (0.0, 0.33, 0.66):
            out.append((self.s("L19", fr), "num_tick", 0.35))
        out.append((self.s("L20"), "phone_hum", 0.3))
        return out

    def stage(self, t):
        a18, b19 = self.s("L18", 0.55), self.s("L19")
        if t < a18:
            return 0, 0.0
        if t < b19:
            return 0, prog(t, a18, b19)
        e19 = self.e("L19")
        return 1 + min(2, int((t - b19) / ((e19 - b19) / 3))), prog(t, b19, e19)

    def number_at(self, t):
        a = self.s("L18", 0.3)
        if t < a:
            return None
        v = 6400
        v = rolling(t, self.s("L18", 0.55), self.e("L18"), 6400, 5849)
        v = rolling(t, self.s("L19"), self.s("L19", 0.33), v, 4742) if t > self.s("L19") else v
        v = rolling(t, self.s("L19", 0.33), self.s("L19", 0.66), v, 1630) if t > self.s("L19", 0.33) else v
        v = rolling(t, self.s("L19", 0.66), self.e("L19"), v, 380) if t > self.s("L19", 0.66) else v
        v = rolling(t, self.s("L20"), self.e("L20"), v, 96) if t > self.s("L20") else v
        return v

    def draw(self, f, t):
        bg(f, spot=(540, 820), spot_a=0.06)
        in20 = prog(t, self.s("L20") - 0.4, self.s("L20") + 0.2)
        n = self.number_at(t)
        # --- daughter growing up (fades back when L20 starts)
        f.save()
        f.cam(540, 960, lerp(1.0, 0.82, ease_io(in20)))
        gline(f, [(XL, 1180), (XR, 1180)], LINE_DIM, 2, 0.5)
        grow = ease_io(prog(t, self.s("L18", 0.55), self.e("L19")))
        R = lerp(50, 70, grow)
        si = 0 if t < self.s("L19") else 1 + min(2, int((t - self.s("L19")) / max(0.1, (self.e("L19") - self.s("L19")) / 3)))
        _, tweaks, _ = DAUGHTER_STAGES[si]
        sp = DAUGHTER.but(**tweaks)
        walk = 0.0
        if si == 3:
            walk = ease_io(prog(t, self.s("L19", 0.7), self.e("L20")))
        x = lerp(540, 820, walk)
        da = 1 - 0.55 * in20
        fc = Face(mouth="big" if si == 0 else ("smile" if si < 3 else "small"), eyes="happy" if si == 0 and (t % 2) < 1 else "open",
                  look=(lerp(0, 0.6, walk), 0), blink=blink_at(t, 4))
        hx, hy = person(f, x, 1180, R, sp, fc, a=da, T=R * (1.7 + 0.25 * grow), legs=R * (1.0 + 0.4 * grow))
        if si == 3:
            # suitcase
            grect(f, x + R * 1.1, 1180 - R * 1.2, R * 0.9, R * 1.2, 10, LINE, 3, da, fillc=hexc("#2b2f39"))
        if n is not None:
            num_pop(f, n, hx, hy - R * 2.0, 96, t, self.s("L18", 0.3), a=da)
        # stage captions as icons
        if t >= self.s("L19"):
            for k, kind in enumerate(("school", "star", "plane")):
                t0 = self.s("L19", k / 3)
                a = smooth(prog(t, t0, t0 + 0.3)) * (1 - in20)
                S.icon(f, kind if kind != "star" else "school", 260 + k * 280, 560, 80, a=a * (1.0 if k == si - 1 else 0.45))
        f.restore()
        # --- L20: you, on the couch, lit by your phone
        if in20 > 0:
            a = smooth(in20)
            c = f.cx
            # couch
            cx0, cw = (-160, 1150) if land() else (90, 900)
            grect(f, cx0, 1160, cw, 260, 40, LINE, 3, a, fillc=hexc("#1d2129"))
            grect(f, cx0 - 30, 1060, 120, 360, 30, LINE, 3, a, fillc=hexc("#22262f"))
            if land():
                S.window(f, 1150, 640, 300, 360, a * 0.7, light=0.1)
            fc = Face(look=(0.15, 0.75), eyes="half", brows="neutral", mouth="flat", blink=blink_at(t, 1))
            bust(f, 400, 1110, 95, HERO, fc, Arms(phone=True), a=a, T=230)
            glow_blob(f, 440, 1080, 170, hexc("#9cc0ff"), 0.35 * a)
        vignette(f)


# ------------------------------------------------------------------ S15 Dad
class S15Dad(Shot):
    lines = ["L21", "L22", "L23"]
    lead = 0.3
    tail = 0.4

    def sfx(self):
        out = [(0.0, "amb_room", 0.5), (0.0, "clock", 0.35), (self.s("L21", 0.8), "num_reveal_low", 0.5)]
        for k, fr in enumerate((0.38, 0.62, 0.8)):
            out.append((self.s("L22", fr), "pop_soft", 0.35))
        return out

    def draw(self, f, t):
        bg(f, spot=(540, 760), spot_a=0.06)
        f.save()
        k = ease_io(prog(t, self.s("L23") - 0.3, self.e("L23")))
        f.cam(lerp(540, 470, k), lerp(960, 900, k), lerp(1.0, 1.15, k))
        S.kitchen(f)
        talking = self.s("L22", 0.2) < t < self.e("L22") and (t * 5.5) % 1 < 0.55
        dad_f = Face(mouth="open" if talking else "smile", brows="soft", look=(-0.35, 0.05), blink=blink_at(t, 8))
        hx, hy = bust(f, 690, 1060, 92, DAD, dad_f, T=300)
        # hero at left: wants to say something, can't
        want = self.s("L23") < t < self.s("L23", 0.55)
        cant = t >= self.s("L23", 0.55)
        hero_f = Face(look=(0.5, 0.0) if not cant else (0.2, 0.6), mouth="o" if want else ("sad" if cant else "flat"),
                      brows="worried" if (want or cant) else "neutral", blink=blink_at(t, 3), eyes="half" if cant else "open")
        bust(f, 380, 1080, 92, HERO, hero_f, T=300)
        S.table_front(f, 120, 1240, 840, h=200)
        S.tea_glass(f, 470, 1240)
        S.tea_glass(f, 620, 1240)
        num_pop(f, "1", hx, hy - 175, 110, t, self.s("L21", 0.8))
        # dad's small talk bubbles
        for j, (kind, fr) in enumerate((("cloud", 0.38), ("ball", 0.62), ("tomato", 0.8))):
            t0 = self.s("L22", fr)
            a = smooth(prog(t, t0, t0 + 0.25)) * (1 - smooth(prog(t, self.s("L23") - 0.2, self.s("L23") + 0.3)))
            if a > 0:
                bx, by = 820 + (j - 1) * 30, 640 - j * 110
                S.bubble(f, bx, by, 130, 96, a, tail=-1)
                S.icon(f, kind, bx, by - 4, 52, a)
        # your empty bubble that never fills
        if t > self.s("L23", 0.1):
            a = smooth(prog(t, self.s("L23", 0.1), self.s("L23", 0.3))) * (1 - smooth(prog(t, self.s("L23", 0.6), self.e("L23"))))
            S.bubble(f, 250, 720, 200, 110, a, tail=1)
            for d in range(3):
                f.cx.arc(210 + d * 40, 715, 7, 0, 6.3)
                src(f.cx, WHITE, a * (0.4 + 0.6 * ((t * 3 + d * 0.3) % 1 < 0.5)))
                f.cx.fill()
        f.restore()
        vignette(f)


class S16Zero(Shot):
    lines = ["L24"]
    lead = 0.3
    tail = 1.3

    def sfx(self):
        return [(0.0, "amb_room", 0.4), (0.15, "steps", 0.4), (self.s("L24", 0.8), "zero_hit", 0.6)]

    def draw(self, f, t):
        bg(f, top=hexc("#111318"), bot=hexc("#060709"))
        f.save()
        k = ease_io(prog(t, self.s("L24", 0.75), self.dur))
        f.cam(lerp(540, 470, k), lerp(960, 860, k), lerp(1.0, 1.12, k))
        # Dad, small, at the table in the distance
        S.room(f, back=(200, 520, 880, 1060), a=0.7, floor_lines=4)
        dad_f = Face(mouth="smile", brows="soft", look=(0.4, 0.1), blink=blink_at(t, 8))
        hx, hy = bust(f, 470, 900, 58, DAD, dad_f, T=200)
        S.table_front(f, 300, 1000, 380, h=160, a=0.9)
        tz = self.s("L24", 0.8)
        z = prog(t, tz, tz + 0.5)
        n = "1" if z < 0.5 else "0"
        dim = 1.0 if z < 0.5 else lerp(1.0, 0.55, prog(t, tz + 0.3, tz + 1.6))
        number(f, n, hx, hy - 120, 110, a=dim * (1 - 0.6 * math.sin(z * math.pi)), glow=dim)
        # doorway frame in the foreground; you, turning back
        grect(f, 600, 380, 420, 1200, 6, LINE, 4, glow=0.5)
        turn = ease_io(prog(t, 0.2, self.s("L24", 0.6)))
        fc = Face(view="front" if turn > 0.5 else "back", look=(-0.7, 0.05), brows="sad", mouth="flat",
                  eyes="open", blink=blink_at(t, 2), tear=prog(t, tz + 0.6, tz + 1.6))
        person(f, 820, 1640, 105, HERO, fc)
        f.restore()
        vignette(f, 0.65)


# ------------------------------------------------------------------ S17 contacts
CONTACTS = [("Aaron", 22), ("Baker Joe", "2,140"), ("Dad", 0), ("Dentist", 14), ("Emma", 2), ("Ethan", 64),
            ("Grandma", 5), ("Jake", 9), ("Liam", 30), ("Mike (work)", "3,900"), ("Mom", 16), ("Noah", 7),
            ("Olivia", 41), ("Ryan", 2), ("Sam", 11)]


def contacts(f, t, scroll, hl=None, hl_a=0.0, a=1.0, x=540, y=830, dim_others=0.0):
    sx, sy, sw, sh = S.phone(f, x, y, 560, 1080, a=a)
    text(f, "Contacts", sx + 30, sy + 70, 48, WHITE, a, "left")
    rrect(f.cx, sx + 24, sy + 100, sw - 48, 54, 27)
    src(f.cx, hexc("#1f232c"), a)
    f.cx.fill()
    text(f, "Search", sx + 60, sy + 136, 26, GREY3, a, "left", weight="normal")
    c = f.cx
    c.save()
    c.rectangle(sx, sy + 170, sw, sh - 180)
    c.clip()
    f.gx.save()
    f.gx.rectangle(sx, sy + 170, sw, sh - 180)
    f.gx.clip()
    for i, (name, num) in enumerate(CONTACTS):
        ry = sy + 230 + i * 92 - scroll
        if ry < sy + 120 or ry > sy + sh + 40:
            continue
        is_h = (name == hl)
        oa = a * (1 - dim_others * (0 if is_h else 0.75))
        S.contact_row(f, sx + 20, ry, sw - 40, name, num, oa, hl=hl_a if is_h else 0.0)
    c.restore()
    f.gx.restore()
    return sx, sy, sw, sh


class S17Contacts(Shot):
    lines = ["L25", "L26"]
    lead = 0.3
    tail = 0.45

    def sfx(self):
        return [(0.0, "amb_night", 0.45), (self.s("L25", 0.55), "scroll", 0.35), (self.e("L26") - 0.35, "select", 0.45)]

    def scroll(self, t):
        a, b = self.s("L25", 0.55), self.e("L26") - 0.4
        return 640 * ease_out(prog(t, a, b)) + 30 * math.sin(prog(t, a, b) * math.pi)

    def draw(self, f, t):
        bg(f, top=hexc("#0d0f14"), bot=hexc("#050608"))
        f.save()
        intro = smooth(prog(t, self.s("L25", 0.35), self.s("L25", 0.6)))
        if intro < 1:
            # you in bed, awake, phone glow on the face
            a = 1 - intro
            S.window(f, 380, 330, 320, 380, a * 0.8, light=0.05)
            fc = Face(look=(0, 0.6), eyes="open", mouth="flat", brows="neutral", blink=blink_at(t, 2))
            bust(f, 540, 1080, 110, HERO, fc, Arms(phone=True), a=a, T=300)
            glow_blob(f, 570, 1040, 200, hexc("#9cc0ff"), 0.35 * a)
            rrect(f.cx, 100, 1230, 880, 400, 40)
            src(f.cx, hexc("#232730"), a)
            f.cx.fill()
            grect(f, 100, 1230, 880, 400, 40, LINE, 3, a)
        if intro > 0:
            hl_a = smooth(prog(t, self.e("L26") - 0.45, self.e("L26") - 0.1))
            contacts(f, t, self.scroll(t), hl="Jake", hl_a=hl_a, a=intro, dim_others=hl_a * 0.6)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S18 best friend
def kid_hero():
    return HERO


class S18Friend(Shot):
    lines = ["L27", "L28", "L29", "L30"]
    lead = 0.3
    tail = 0.5

    def sfx(self):
        return [(0.0, "flashback", 0.45), (0.2, "kids", 0.25), (self.s("L28"), "whoosh_soft", 0.35),
                (self.s("L29", 0.3), "pop_soft", 0.25), (self.s("L29", 0.5), "pop_soft", 0.25),
                (self.s("L29", 0.7), "pop_soft", 0.25), (self.s("L30"), "low_note", 0.35)]

    def draw(self, f, t):
        bg(f, spot=(540, 820), spot_a=0.06)
        p28, p29, p30 = self.s("L28") - 0.15, self.s("L29"), self.s("L30") - 0.2
        if t < p28:
            # 2014: school desks side by side, laughing
            S.room(f, back=(170, 400, 910, 1000), a=0.8)
            grect(f, 260, 440, 560, 250, 10, LINE, 3, fillc=hexc("#141820"))
            text(f, "2 + 2 = 4", 330, 540, 54, WHITE, 0.85, "left", glow=0.4)
            text(f, "12.06.2014", 760, 650, 30, GREY1, 0.8, "right")
            laugh = (t * 2.2) % 2 < 1.2
            for x, sp, lk in ((350, HERO, 0.5), (730, FRIEND, -0.5)):
                fc = Face(look=(lk, 0), eyes="happy" if laugh else "open", mouth="big" if laugh else "smile",
                          brows="raised", blink=blink_at(t, int(x)))
                bust(f, x, 1080, 78, sp, fc, T=200, tilt=math.sin(t * 6 + x) * 3 if laugh else 0)
                grect(f, x - 160, 1180, 320, 26, 6, LINE, 3, fillc=hexc("#22262f"))
                gline(f, [(x - 140, 1206), (x - 140, 1400)], LINE, 3)
                gline(f, [(x + 140, 1206), (x + 140, 1400)], LINE, 3)
            # a paper note flying between them
            ph = (t * 0.6) % 1
            nx = lerp(420, 660, ph)
            ny = 1000 - math.sin(ph * math.pi) * 120
            grect(f, nx - 22, ny - 16, 44, 32, 4, WHITE, 2.4, 0.9, glow=0.4, fillc=hexc("#e9eaee"))
            vignette(f)
            # flashback tint
            f.cx.rectangle(XL, -2000, XR - XL, H + 4000)
            src(f.cx, hexc("#d9d0b8"), 0.04)
            f.cx.fill()
            return
        f.save()
        if t < p30:
            # adults, drifting apart; life fills the space between
            apart = ease_io(prog(t, p29, p29 + (self.e("L29") - p29) * 0.9))
            gline(f, [(XL, 1250), (XR, 1250)], LINE_DIM, 2, 0.5)
            for side, sp in ((-1, HERO), (1, FRIEND)):
                x = 540 + side * lerp(120, 560 if land() else 360, apart)
                fc = Face(look=(-side * 0.4 * (1 - apart) + side * 0.5 * apart, 0), mouth="smile" if apart < 0.2 else "flat",
                          blink=blink_at(t, side + 2))
                person(f, x, 1250, 80, sp, fc)
            for j, (kind, fr, yy) in enumerate((("case", 0.3, 760), ("house", 0.5, 950), ("phone", 0.7, 1140), ("ring", 0.45, 600))):
                t0 = self.s("L29", fr)
                a = smooth(prog(t, t0, t0 + 0.3))
                if a > 0:
                    S.icon(f, kind, 540 + (j % 2 - 0.5) * (220 if land() else 70), yy - (1 - a) * 30, 90, a)
        elif land():
            # widescreen split: Jake on the left, you on the right
            k = smooth(prog(t, p30, p30 + 0.4))
            gline(f, [(540, 420), (540, 1400)], LINE_DIM, 2, 0.5 * k)
            fc = Face(look=(0.2, 0.5), mouth="smile", eyes="open", blink=blink_at(t, 5))
            bust(f, 160, 1010, 90, FRIEND, fc, Arms(phone=True), a=k, T=420)
            glow_blob(f, 190, 990, 150, hexc("#dfe8ff"), 0.25 * k)
            S.window(f, 1080, 600, 260, 320, k * 0.6, light=0.1)
            fc2 = Face(look=(-0.4, 0.3), mouth="sad", brows="sad", eyes="half", blink=blink_at(t, 2))
            bust(f, 860, 1010, 90, HERO, fc2, a=k, T=420)
            number(f, "0", 1180, 790, 70, a=0.35 * k, glow=0.3)
        else:
            # Jake, happy in his own life; you, alone with the 0
            k = smooth(prog(t, p30, p30 + 0.4))
            gline(f, [(60, 940), (1020, 940)], LINE_DIM, 2, 0.5 * k)
            fc = Face(look=(0.2, 0.5), mouth="smile", eyes="open", blink=blink_at(t, 5))
            bust(f, 540, 660, 82, FRIEND, fc, Arms(phone=True), a=k, T=240)
            glow_blob(f, 570, 640, 140, hexc("#dfe8ff"), 0.25 * k)
            S.window(f, 140, 1010, 230, 260, k * 0.6, light=0.1)
            fc2 = Face(look=(-0.4, 0.3), mouth="sad", brows="sad", eyes="half", blink=blink_at(t, 2))
            bust(f, 640, 1290, 82, HERO, fc2, a=k, T=200)
            number(f, "0", 880, 1100, 70, a=0.35 * k, glow=0.3)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S19 nine
class S19Nine(Shot):
    lines = ["L31"]
    lead = 0.25
    tail = 0.45

    def sfx(self):
        return [(0.0, "amb_night", 0.4), (self.s("L31", 0.15), "num_reveal", 0.4),
                (self.s("L31", 0.42), "pop_soft", 0.3), (self.s("L31", 0.55), "pop_soft", 0.3),
                (self.s("L31", 0.72), "pop_soft", 0.3)]

    def draw(self, f, t):
        bg(f, top=hexc("#0d0f14"), bot=hexc("#050608"))
        f.save()
        k = ease_io(prog(t, 0, self.s("L31", 0.3)))
        if land():
            f.cam(lerp(540, 820, k), 830, lerp(1.0, 1.1, k))
        else:
            f.cam(540, lerp(830, 560, k), lerp(1.0, 1.15, k))
        contacts(f, t, 640, hl="Jake", hl_a=1.0, dim_others=0.8)
        f.restore()
        # icons for the few remaining times: weddings and chance meetings, with "9" big
        a9 = smooth(prog(t, self.s("L31", 0.12), self.s("L31", 0.35)))
        nx, ny, iy, ix0 = (1150, 760, 960, 940) if land() else (540, 330, 520, 330)
        number(f, "9", nx, ny, 200, a=a9, glow=1.0)
        for j, (kind, fr) in enumerate((("ring", 0.4), ("ring", 0.5), ("star", 0.66), ("star", 0.74))):
            x = ix0 + j * 140
            t0 = self.s("L31", fr)
            a = smooth(prog(t, t0, t0 + 0.3)) * (1 - 0.6 * smooth(prog(t, self.s("L31", 0.88), self.e("L31"))))
            if a > 0:
                S.icon(f, kind, x, iy, 70, a)
        vignette(f)


# ------------------------------------------------------------------ S20 chat
class S20Chat(Shot):
    lines = ["L32", "L33"]
    lead = 0.3
    tail = 0.55
    gaps = {"L33": 0.5}

    def sfx(self):
        out = [(0.0, "amb_night", 0.4)]
        ty = self.s("L32", 0.0)
        for i in range(10):
            out.append((ty + i * 0.09, "key", 0.25))
        dl = self.s("L32", 0.3)
        for i in range(6):
            out.append((dl + i * 0.06, "key", 0.2))
        tt = self.s("L32", 0.55)
        for i in range(12):
            out.append((tt + i * 0.07, "key", 0.25))
        out.append((self.e("L32") - 0.2, "send", 0.5))
        out.append((self.s("L33", 0.62), "receive", 0.6))
        return out

    def draw(self, f, t):
        bg(f, top=hexc("#0d0f14"), bot=hexc("#050608"))
        f.save()
        sx, sy, sw, sh = S.phone(f, 540, 790, 560, 1060)
        # header
        S.avatar(f, sx + 60, sy + 50, 34)
        text(f, "Jake", sx + 112, sy + 46, 36, WHITE, 1, "left")
        reply_typing = self.s("L33", 0.35) < t < self.s("L33", 0.62)
        status = "typing..." if reply_typing else "last seen 2 years ago"
        text(f, status, sx + 112, sy + 82, 22, BLUE_L if reply_typing else GREY2, 1, "left", weight="normal")
        gline(f, [(sx, sy + 110), (sx + sw, sy + 110)], hexc("#2a2e38"), 1.5, 1, glow=0)
        # input text: type, delete, type, send
        t1, t2, t3, t4 = self.s("L32"), self.s("L32", 0.28), self.s("L32", 0.5), self.e("L32") - 0.2
        draft1, draft2 = "Hey, long time no...", "Coffee this weekend?"
        if t < t2:
            s = draft1[:int(len(draft1) * prog(t, t1, t1 + 0.9))]
        elif t < t3:
            s = draft1[:int(len(draft1) * (1 - prog(t, t2, t2 + 0.4)))]
        elif t < t4:
            s = draft2[:int(len(draft2) * prog(t, t3, t3 + 0.85))]
        else:
            s = ""
        iy = sy + sh - 70
        rrect(f.cx, sx + 20, iy - 34, sw - 110, 68, 34)
        src(f.cx, hexc("#1b1e25"))
        f.cx.fill()
        grect(f, sx + 20, iy - 34, sw - 110, 68, 34, LINE_DIM, 2, glow=0)
        text(f, s + ("|" if (t * 2) % 1 < 0.5 and t < t4 else ""), sx + 46, iy + 10, 28, WHITE, 1, "left", weight="normal")
        f.cx.arc(sx + sw - 50, iy, 30, 0, 6.3)
        src(f.cx, BLUE)
        f.cx.fill()
        # sent bubble
        if t >= t4:
            k = ease_out(prog(t, t4, t4 + 0.35))
            S.msg_bubble(f, sx + sw - 20, lerp(iy - 60, sy + 520, k), draft2, mine=True, a=k)
            text(f, "Delivered", sx + sw - 24, sy + 520 + 60, 20, GREY2, k, "right", weight="normal")
        # 30 seconds
        tt = self.s("L33")
        if t > tt:
            a = smooth(prog(t, tt, tt + 0.3)) * (1 - smooth(prog(t, self.s("L33", 0.55), self.s("L33", 0.65))))
            secs = int(rolling(t, tt, tt + 1.1, 0, 30))
            if land():
                number(f, f"0:{secs:02d}", 1240, 760, 130, a=a, glow=0.8)
            else:
                number(f, f"0:{secs:02d}", 540, 220, 110, a=a, glow=0.8)
        if reply_typing:
            S.bubble(f, sx + 110, sy + 680, 120, 64, 1.0, tail=-1, glow=0.2)
            for d in range(3):
                f.cx.arc(sx + 80 + d * 30, sy + 680, 7, 0, 6.3)
                src(f.cx, WHITE, 0.4 + 0.6 * ((t * 3 + d * 0.3) % 1 < 0.5))
                f.cx.fill()
        tr = self.s("L33", 0.62)
        if t > tr:
            k = ease_out(prog(t, tr, tr + 0.3))
            f.save()
            bx, by = sx + 20, sy + 680
            for c in (f.cx, f.gx):
                c.translate(bx, by)
                c.scale(0.8 + 0.2 * k, 0.8 + 0.2 * k)
                c.translate(-bx, -by)
            S.msg_bubble(f, bx, by, "Finally! Yes!", mine=False, a=k, glow=0.12 * (1 + (1 - prog(t, tr, tr + 1.2))))
            f.restore()
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S21 coffee
class S21Coffee(Shot):
    lines = ["L34"]
    lead = 0.3
    tail = 1.0

    def sfx(self):
        return [(0.0, "amb_cafe", 0.6), (0.0, "rain", 0.35), (self.s("L34", 0.78), "count_up_big", 0.55)]

    def draw(self, f, t):
        bg(f, spot=(540, 700), spot_a=0.05)
        f.save()
        push(f, t, self.dur, 1.0, 1.08, cy=900)
        S.cafe(f, t)
        talk = (t * 4) % 2 < 1
        tc = self.s("L34", 0.78)
        up = t > tc
        jf = Face(look=(-0.5, 0.1), mouth="big" if talk else "smile", eyes="happy" if up and talk else "open",
                  brows="raised", blink=blink_at(t, 7))
        hx, hy = bust(f, 790, 1080, 88, FRIEND, jf, T=300)
        yf = Face(look=(0.5, 0.1), mouth="big" if up else "smile", eyes="happy" if (up and not talk) else "open",
                  brows="soft", blink=blink_at(t, 1))
        bust(f, 290, 1080, 88, HERO, yf, T=300)
        S.cafe_table(f, 540, 1200, steam_t=t)
        v = rolling(t, tc, tc + 1.2, 9, 150)
        if t < tc:
            v = 9
        glow = 1.0 + 0.8 * prog(t, tc, tc + 1.2)
        number(f, v, hx, hy - 170, 120, glow=glow)
        if up:
            # warm sparkles rising
            rng = random.Random(5)
            for i in range(14):
                ph = ((t - tc) * 0.6 + rng.random()) % 1
                x = hx + (rng.random() - 0.5) * 300
                y = hy - 120 - ph * 380
                f.cx.arc(x, y, 3 + rng.random() * 3, 0, 6.3)
                src(f.cx, WHITE, (1 - ph) * 0.7 * prog(t, tc, tc + 0.5))
                f.cx.fill()
                f.gx.arc(x, y, 8, 0, 6.3)
                src(f.gx, GLOW_BLUE, (1 - ph) * 0.6 * prog(t, tc, tc + 0.5))
                f.gx.fill()
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S22 not fate
class S22NotFate(Shot):
    lines = ["L35", "L36"]
    lead = 0.3
    tail = 0.45

    def sfx(self):
        return [(0.0, "amb_void", 0.5), (self.s("L36"), "swell", 0.4), (self.s("L36", 0.6), "shimmer", 0.4)]

    def draw(self, f, t):
        bg(f, spot=(540, 900), spot_a=0.06)
        rng = random.Random(9)
        change = prog(t, self.s("L36", 0.4), self.e("L36"))
        for i in range(70 if land() else 34):
            x = (-760 + rng.random() * 2600) if land() else rng.random() * W
            y0 = rng.random() * 1300 + 100
            v0 = rng.choice([1, 2, 3, 5, 7, 9, 11, 14, 16, 22, 41, 64, 120])
            v1 = v0 * rng.choice([3, 4, 6, 8, 10])
            y = y0 - t * (12 + rng.random() * 18) - ease_io(change) * 80
            v = lerp(v0, v1, ease_io(prog(change, rng.random() * 0.3, 0.7 + rng.random() * 0.3)))
            sz = 26 + rng.random() * 40
            a = 0.25 + 0.45 * rng.random()
            number(f, v, x, y, sz, a=a, glow=0.5 + 0.8 * change, halo=False)
        fc = Face(look=(0, -0.6), brows="raised" if change > 0 else "soft", mouth="small" if change < 0.5 else "smile",
                  blink=blink_at(t, 3))
        bust(f, 540, 1230, 100, HERO, fc, T=400)
        vignette(f)


# ------------------------------------------------------------------ S23 call Mom again
class S23CallMom(Shot):
    lines = ["L37"]
    lead = 0.3
    tail = 0.55

    def sfx(self):
        return [(0.0, "amb_room", 0.4), (0.1, "dial", 0.35), (self.s("L37", 0.55), "count_up_big", 0.5)]

    def draw(self, f, t):
        bg(f, spot=(540, 700), spot_a=0.05)
        # Mom at her door (top), you on the phone (bottom)
        f.save()
        k = ease_io(prog(t, 0, self.dur))
        f.cam(540, lerp(980, 940, k), 1.0)
        up = prog(t, self.s("L37", 0.55), self.e("L37"))
        mf = Face(mouth="big" if up > 0.2 else "smile", eyes="happy" if up > 0.5 else "open", brows="raised",
                  blink=blink_at(t, 6), look=(-0.2, 0))
        L = land()
        f.save()
        for c in (f.cx, f.gx):
            if L:
                c.translate(1000, 900)
                c.scale(0.85, 0.85)
                c.translate(-540, -880)
            else:
                c.translate(540, 360)
                c.scale(0.75, 0.75)
                c.translate(-540, -760)
        mom_door(f, t, 1.0, 1.0, mf, num=None, hero=False)
        f.restore()
        v = 16 if up <= 0 else rolling(t, self.s("L37", 0.55), self.e("L37"), 16, 39)
        if L:
            number(f, v, 983, 650, 100, glow=1.0 + up * 0.6)
        else:
            number(f, v, 540, 290, 100, glow=1.0 + up * 0.6)
        fc = Face(look=(0.25, 0.0) if L else (0.0, 0.0), mouth="big" if t > self.s("L37", 0.4) else "smile", eyes="open",
                  brows="soft", blink=blink_at(t, 1))
        if L:
            bust(f, 120, 1150, 100, HERO, fc, Arms(phone=True), T=400)
        else:
            bust(f, 540, 1230, 100, HERO, fc, Arms(phone=True), T=400)
        f.restore()
        vignette(f)


# ------------------------------------------------------------------ S24 mirror again
class S24Mirror(Shot):
    lines = ["L38", "L39", "L40"]
    lead = 0.35
    tail = 0.8
    gaps = {"L40": 0.6}

    def sfx(self):
        return [(0.0, "amb_room", 0.4), (self.s("L39", 0.3), "shimmer", 0.35), (self.s("L40"), "low_note", 0.3)]

    def draw(self, f, t):
        f.save()
        push(f, t, self.dur, 1.0, 1.12, cy=900, dy=-140)
        extras = smooth(prog(t, self.s("L39", 0.2), self.s("L39", 0.6))) * (1 - 0.6 * smooth(prog(t, self.s("L40"), self.e("L40"))))
        blur = smooth(prog(t, self.s("L39", 0.5), self.e("L39"))) * (1 - smooth(prog(t, self.s("L40", 0.3), self.e("L40") + 0.4)))
        k = prog(t, self.s("L38", 0.5), self.s("L38", 0.5) + 0.6)
        mirror_scene(f, t, Face(look=(0, -0.5 * k * (1 - extras)), brows="soft", mouth="small" if t > self.s("L40") else "flat",
                                blink=blink_at(t, 2)),
                     above=smooth(k) * (1 - smooth(prog(t, self.s("L39"), self.s("L39", 0.3)))),
                     extras=extras, blur_num=blur)
        f.restore()


# ------------------------------------------------------------------ S25 ending
class S25End(Shot):
    lines = ["L41", "L42"]
    lead = 0.45
    tail = 1.2
    gaps = {"L42": 0.7}

    def sfx(self):
        return [(0.0, "amb_void", 0.4), (self.s("L41", 0.7), "num_reveal", 0.45), (self.s("L42", 0.1), "count_up_big", 0.4),
                (self.s("L42", 0.55), "key", 0.2), (self.s("L42", 0.62), "key", 0.2), (self.s("L42", 0.7), "key", 0.2)]

    def draw(self, f, t):
        bg(f, spot=(540, 820), spot_a=0.07)
        # a silhouette of "someone" with a question mark
        sil = smooth(prog(t, self.s("L41", 0.2), self.s("L41", 0.6)))
        c = f.cx
        x, g, R = 540, 1060, 90
        if sil > 0:
            hy = g - R * 1.25 - R * 1.85 - R * 0.95
            for cc, lw, al in ((f.cx, 4, sil), (f.gx, 10, sil * 0.6)):
                cc.arc(x, hy, R, 0, 6.3)
                src(cc, WHITE, al)
                cc.set_line_width(lw)
                cc.stroke()
                cc.move_to(x - R * 0.98, g)
                cc.curve_to(x - R, hy + R * 1.2, x - R * 0.6, hy + R * 1.05, x, hy + R * 1.05)
                cc.curve_to(x + R * 0.6, hy + R * 1.05, x + R, hy + R * 1.2, x + R * 0.98, g)
                cc.stroke()
            c.arc(x, hy, R, 0, 6.3)
            src(c, WHITE, 0.06 * sil)
            c.fill()
            # "?" then a growing number
            tq = self.s("L41", 0.7)
            grow = prog(t, self.s("L42", 0.05), self.s("L42", 0.45))
            if grow <= 0:
                num_pop(f, "?", x, hy - R * 1.9, 120, t, tq)
            else:
                v = rolling(t, self.s("L42", 0.05), self.s("L42", 0.45), 1, 52)
                number(f, v, x, hy - R * 1.9, 120 + 30 * grow, glow=1.0 + grow)
        # comment box
        cb = smooth(prog(t, self.s("L42", 0.5), self.s("L42", 0.65)))
        if cb > 0:
            bx, by, bw, bh = 120, 1170 - (1 - cb) * 30, 840, 92
            S.avatar(f, bx + 10, by + bh / 2, 30, cb, GREY1)
            rrect(c, bx + 60, by, bw - 60, bh, 46)
            src(c, hexc("#15181f"), cb)
            c.fill()
            grect(f, bx + 60, by, bw - 60, bh, 46, WHITE, 3, cb, glow=0.6)
            typed = "Add a comment..."
            cur = "|" if (t * 2) % 1 < 0.5 else ""
            text(f, cur + typed, bx + 100, by + 58, 32, GREY2, cb, "left", weight="normal")
        vignette(f)


def end_card(f, t, dur):
    bg(f, spot=(540, 860), spot_a=0.06)
    a = smooth(prog(t, 0.0, 0.5)) * (1 - smooth(prog(t, dur - 0.5, dur)))
    fc = Face(mouth="smile", brows="neutral", look=(0.25, 0.0), blink=blink_at(t, 3))
    if land():
        bust(f, 300, 1150, 130, HERO, fc, a=a, T=500)
        text(f, "JUST NEEDY", 860, 1090, 72, WHITE, a, glow=0.4)
    else:
        bust(f, 540, 1080, 120, HERO, fc, a=a, T=420)
        text(f, "JUST NEEDY", 540, 1560, 54, WHITE, a, glow=0.4)
    vignette(f)


SHOTS_B = [S13City, S14Daughter, S15Dad, S16Zero, S17Contacts, S18Friend, S19Nine, S20Chat, S21Coffee,
           S22NotFate, S23CallMom, S24Mirror, S25End]

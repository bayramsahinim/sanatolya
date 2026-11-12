"""Scenes 5-7: the rooster, something is wrong, the cliffhanger."""
from .common import *  # noqa

ROOSTER_LAG = 0.42      # rooster shot starts this long after the crow begins


# ================================================================ SCENE 5 - THE ROOSTER
class S5Tiptoe(Shot):
    """'Okay. Fine. I'll be quiet and figure this out.' ... then COCK-A-DOODLE-DOO."""
    scene = "s5"
    music = "dread"
    music_gain = 0.45
    amb = "house_dark"

    def plan(self, P):
        P.wait(0.1)
        a = P.say("l12", gap=0.0)
        d = P.voice.dur("l12")
        for k in range(9):
            P.sfx("tiptoe" if k % 2 else "tiptoe2", t=a + 1.3 + k * 0.33, vol=0.5)
        self.music_until = a + d + 0.1
        P.wait(0.62)                      # silence. clock ticks.
        self.crow = P.t
        P.sfx("rooster", t=self.crow, vol=0.85)
        P.wait(ROOSTER_LAG)

    def draw(self, cx, t):
        a = self.mt("l12")
        cr = self.crow
        walk_t = max(0.0, t - (a + 1.25))
        x = 380 + min(walk_t, 3.2) * 120
        cam = Cam(x + 120, 1150, 1.45)

        def fg(c):
            jump = back_out(prog(t, cr + 0.02, cr + 0.25), 2.5) if t > cr else 0
            if t < a + 0.35:            # 'Okay.' stops
                hp = hero_pose(x, 1600, t, s=1.45, f=1, eyes="open", brows="flat", mouth="flat")
            elif t < a + 1.25:          # 'Fine.' nod, finger to lips
                hp = hero_pose(x, 1600, t, s=1.45, f=1, view="front", eyes="half", brows="flat", mouth="flat",
                               arm_b=150, elb_b=-160, tilt=6 * math.sin(prog(t, a + 0.7, a + 1.0) * math.pi))
            else:                       # exaggerated tiptoe
                ph = walk_t * 1.5 * 2 * math.pi
                hp = hero_pose(x, 1600, t, s=1.45, f=1, eyes="open", brows="worried", mouth="o", mouth_open=0.5,
                               look=(0.2, 0), arm_b=150, elb_b=-160, arm_a=-30, elb_a=60,
                               hip_a=30 * math.sin(ph) + 10, hip_b=-30 * math.sin(ph) + 10,
                               knee_a=40 + 50 * max(0, math.cos(ph)), knee_b=40 + 50 * max(0, -math.cos(ph)),
                               bob=-10 - 12 * abs(math.sin(ph)), lean=4)
            if t > cr:
                hp = hp.but(view="front", eyes="wide", brows="up", mouth="scream", mouth_open=1.0, sweat=1.0,
                            arm_a=160, arm_b=160, elb_a=-10, elb_b=-10, bob=-120 * jump,
                            squash=1.0 + 0.15 * jump, hip_a=20, hip_b=20, knee_a=30, knee_b=30, blink=False)
            shadow(c, x, 1600, 70 * (1 - 0.4 * (t > cr)))
            fig(c, self, cam, HERO, hp, "hero")
        F.kitchen(cx, cam, t, power=0.0, curtains=1.0, table=False, before_fg=fg)
        cold_grade(cx, 0.6)
        if t > cr:
            sx, sy = shake(t, 10, 30)
            cx.translate(sx, sy)
        vignette(cx, 0.5)


class S5Rooster(Shot):
    """The rooster on the fence, proud, in broad daylight. 'That's when our rooster decided it was sunrise. Again.'"""
    scene = "s5"
    music = None
    amb = "farm"

    def plan(self, P):
        P.wait(0.6)                          # let the crow land
        a = P.say("l13", gap=0.0)
        self.again = a + 3.0
        P.wait(0.25)
        self.crow2 = P.t
        P.sfx("rooster_small", t=self.crow2, vol=0.55)
        P.wait(0.45)

    def draw(self, cx, t):
        lag = ROOSTER_LAG
        crow1 = 1 - prog(t + lag, 1.5, 1.85)
        inhale = pulse(t, self.again - 0.1, self.crow2, 0.12)
        crow2 = prog(t, self.crow2, self.crow2 + 0.1)
        crow = max(crow1, crow2)
        z = 1.0 + 0.05 * t
        cam = Cam(540, 1030, z)
        # bright, obviously-not-sunrise daylight
        F.sky(cx, t)
        cx.save()
        cam.apply(cx, 0.1)
        F._sun(cx, 820, 330, 1.0)
        F._cloud_strip(cx, t, 520, 3, 0.5)
        cx.restore()
        cx.save()
        cam.apply(cx, 0.4)
        F._treeline(cx, 1260, -800, 2000, 4, F.col("far"), 60, 90)
        cx.restore()
        world(cx, cam)
        cx.rectangle(-800, 1300, 2800, 1200)
        src(cx, F.col("grass"))
        cx.fill()
        F.barn(cx, 700, 1300, 460)
        # fence post close-up
        rrect(cx, 330, 1180, 120, 900, 8)
        fs(cx, F.col("fence"), OUTLINE, 7)
        rrect(cx, -400, 1300, 1900, 40, 8)
        fs(cx, shade(F.col("fence"), 0.08), OUTLINE, 6)
        rrect(cx, -400, 1560, 1900, 40, 8)
        fs(cx, shade(F.col("fence"), 0.08), OUTLINE, 6)
        rooster(cx, 395, 1190, 3.1, 1, t, crow=crow, puff=max(crow, inhale * 1.3), look=0.0)
        # sound lines while crowing
        if crow > 0.5:
            for k in range(3):
                r = 60 + ((t * 3 + k / 3) % 1) * 160
                cx.new_path()
                cx.arc(720, 620, r, -0.9, 0.2)
                src(cx, (1, 1, 1, 0.8 * (1 - (r - 60) / 160)))
                cx.set_line_width(8)
                cx.stroke()
        end(cx)
        warm_grade(cx, 1.2)
        vignette(cx, 0.3)


class S5Stop(Shot):
    """'The zombies outside stopped.'"""
    scene = "s5"
    music = "dread"
    music_gain = 0.55
    amb = "farm"

    def plan(self, P):
        P.sfx("groan_far1", t=0.0, vol=0.45)
        P.wait(0.12)
        a = P.say("l14", gap=0.2)
        self.stop = a + 1.0
        P.sfx("freeze", t=self.stop - 0.15, vol=0.35)

    def draw(self, cx, t):
        st = self.stop
        tz = min(t, st)
        cam = Cam(1150, 1280, 0.9)
        zs = [(ZOMBIE_B, 760, 1450, -1, 0.0), (NEIGHBOR, 1200, 1500, -1, 1.7), (ZOMBIE_C, 1560, 1440, -1, 3.1)]

        def chars(c):
            for f, x0, y, fc, seed in zs:
                x = x0 - tz * 60
                shadow(c, x, y, 70)
                p = shamble(zombie_pose(x, y, tz, s=1.25, f=fc), tz, 0.9, 1.0, seed)
                if t > st:     # frozen mid-lurch, a tiny wobble
                    p = p.but(tilt=p.tilt + 2 * math.sin((t - st) * 9 + seed))
                fig(c, self, None, f, p)
        F.farm_exterior(cx, cam, t, before_fg=chars, fog=0.6)
        cold_grade(cx, 0.35)
        vignette(cx, 0.4)


class S5Turn(Shot):
    """'Slowly turned.' Three heads toward the house. BIG MISTAKE."""
    scene = "s5"
    music = "dread"
    music_gain = 0.6
    amb = "farm"

    def plan(self, P):
        P.wait(0.1)
        a = P.say("l15", gap=0.0)
        P.sfx("groan2", t=a + 0.7, vol=0.4)
        P.accent("[BIG MISTAKE]", t=a + P.voice.dur("l15") - 0.1, dur=0.72, size=ACCENT_SIZE,
                 pos=(W / 2, ACCENT_Y))
        P.wait(0.85)

    def draw(self, cx, t):
        turn = ease_io(prog(t, 0.15, 1.4))
        cam = Cam(1180, 1330, 1.35 + 0.18 * ease_io(prog(t, 0, 2.2)))
        zs = [(ZOMBIE_B, 760, 1450, 0.0), (NEIGHBOR, 1200, 1500, 1.7), (ZOMBIE_C, 1560, 1440, 3.1)]

        def chars(c):
            for k, (f, x0, y, seed) in enumerate(zs):
                x = x0 - 2.0 * 60
                tk = clamp(turn * 1.25 - k * 0.12)
                p = shamble(zombie_pose(x, y, 2.0, s=1.25, f=-1), 2.0, 0.9, 1.0, seed)
                if tk > 0.5:
                    p = p.but(view="front", f=1, arm_a=p.arm_a - 60, arm_b=p.arm_b - 60)
                p = p.but(look=(lerp(-1, 0, tk), 0.15), eyes="wide" if tk < 0.9 else "angry", t=t,
                          tilt=lerp(p.tilt, 4, tk), mouth="teeth")
                J = fig(c, self, None, f, p)
                if tk > 0.95:
                    hx, hy = J["head"]
                    glint(c, hx - 18, hy - 6, 26, pulse(t, 1.5 + k * 0.08, 1.7 + k * 0.08, 0.08))
        F.farm_exterior(cx, cam, t, before_fg=chars, fog=0.6, dark=0.25 * turn)
        cold_grade(cx, 0.5)
        vignette(cx, 0.5)


class S5Feathers(Shot):
    """'Great. My security system has feathers.' Deadpan."""
    scene = "s5"
    music = None
    amb = "house_dark"

    def plan(self, P):
        P.wait(0.15)
        a = P.say("l16", gap=0.0)
        P.wait(0.45)
        self.button = P.t
        P.sfx("rooster_small", t=self.button, vol=0.28)
        P.wait(0.6)

    def draw(self, cx, t):
        a = self.mt("l16")
        z = 1.7 + 0.35 * ease_io(prog(t, 0, 3.5))
        cam = Cam(560, 1080, z)
        side = ease_io(prog(t, a + 0.75, a + 1.0))

        def outside(c, x, y, w, h):
            c.save()
            c.translate(x + w / 2 - W / 2, y + h / 2 - H / 2)
            vc = Cam(760, 1180, 0.8)

            def roo(cc):
                rr = prog(t, self.button, self.button + 0.1) * (1 - prog(t, self.button + 0.7, self.button + 0.9))
                rooster(cc, 760, 1400, 1.2, 1, t, crow=rr, puff=0.5 + 0.5 * rr)
                rrect(cc, 715, 1395, 90, 300, 6)
                fs(cc, F.col("fence"), OUTLINE, 5)
            F.farm_exterior(c, vc, t, before_fg=roo, fence_fg=False, house=False)
            c.restore()

        def fg(c):
            hp = hero_pose(560, 1620, t, s=1.6, f=1, view="front", eyes="half", brows="flat", mouth="flat",
                           look=(lerp(0, 0.9, side) * (1 - prog(t, self.button, self.button + 0.2)), 0),
                           arm_a=12, arm_b=12, blink=True)
            fig(c, self, cam, HERO, hp, "hero")
        F.kitchen(cx, cam, t, power=0.0, curtains=0.0, table=False, before_fg=fg, window_view=outside, dim=0.0)
        cold_grade(cx, 0.4)
        vignette(cx, 0.45)


# ================================================================ SCENE 6 - SOMETHING IS WRONG
class S6Window(Shot):
    """'I ran to shut the window.'"""
    scene = "s6"
    music = "dread"
    music_gain = 0.75
    amb = "house_dark"

    def plan(self, P):
        P.wait(0.05)
        a = P.say("l17", gap=0.0)
        self.slam = a + 1.25
        P.sfx("window_slam", t=self.slam, vol=0.85)
        for k in range(4):
            P.sfx("step_wood2", t=a + 0.1 + k * 0.24, vol=0.35)
        self.music_until = self.slam
        P.t = self.slam + 0.45

    def draw(self, cx, t):
        sl = self.slam
        u = prog(t, 0, sl - 0.25)
        x = lerp(1050, 560, ease_out(u))
        cam = Cam(lerp(800, 560, ease_io(u)), 1020, 1.35)
        close = ease_in(prog(t, sl - 0.2, sl))
        tc = t

        def outside(c, xx, y, w, h):
            c.save()
            c.translate(xx + w / 2 - W / 2, y + h / 2 - H / 2)
            vc = Cam(1100, 1300, 0.62)

            def zz(cc):
                for k, (f, x0, sd) in enumerate([(ZOMBIE_B, 700, 0), (NEIGHBOR, 1100, 1.7), (ZOMBIE_C, 1450, 3.1)]):
                    cc_x = x0 - tc * 30
                    p = shamble(zombie_pose(cc_x, 1520 + k * 20, tc, s=1.3, f=-1, view="front"), tc, 0.9, 1, sd)
                    f.draw(cc, p)
            F.farm_exterior(c, vc, tc, before_fg=zz, fence_fg=False, dark=0.2)
            c.restore()

        def fg(c):
            if t < sl - 0.25:
                hp = run(hero_pose(x, 1600, t, s=1.5, f=-1, eyes="wide", brows="worried", mouth="scream",
                                   mouth_open=0.7, sweat=1, blink=False), t, 2.6, 1.0)
            else:
                hp = hero_pose(x, 1600, t, s=1.5, f=-1, view="front", eyes="squeeze" if t < sl + 0.25 else "wide",
                               brows="worried", mouth="teeth", arm_a=lerp(170, 150, close), elb_a=-10,
                               arm_b=lerp(170, 150, close), elb_b=-10, lean=0, blink=False, sweat=1)
            fig(c, self, cam, HERO, hp, "hero")
        F.kitchen(cx, cam, t, power=0.0, curtains=0.0, table=False, before_fg=fg, window_view=outside,
                  window_open=1 - close)
        if t > sl:
            sx, sy = shake(t, 9 * (1 - prog(t, sl, sl + 0.3)), 30)
            cx.translate(sx, sy)
        cold_grade(cx, 0.55)
        vignette(cx, 0.5)


class S6Creak(Shot):
    """Relief... creak. He freezes. 'Then I heard footsteps... inside the house.'"""
    scene = "s6"
    music = None
    amb = "house_dark"
    amb_gain = 0.8

    def plan(self, P):
        P.wait(0.25)
        self.creak = P.t
        P.sfx("creak", t=self.creak, vol=0.9)
        P.wait(0.62)
        a = P.say("l18", gap=0.0)
        P.sfx("step_wood", t=a + 0.95, vol=0.35)
        P.sfx("heartbeat", t=a + 0.2, vol=0.45)
        P.sfx("heartbeat", t=a + 1.05, vol=0.5)
        cut_at(P, "l18", 1.45)

    def draw(self, cx, t):
        ck = self.creak
        frozen = t > ck + 0.05
        z = 2.6 + 0.4 * ease_io(prog(t, ck, ck + 2.6))
        cam = Cam(560, 1090, z)
        eyes_dart = math.sin((t - ck) * 3.0) if frozen else 0

        def fg(c):
            if not frozen:
                hp = hero_pose(560, 1600, t, s=1.5, f=1, view="front", eyes="closed", brows="up", mouth="o",
                               mouth_open=0.5, arm_a=25, arm_b=25, bob=4 * math.sin(t * 6))
            else:
                hp = hero_pose(560, 1600, t, s=1.5, f=1, view="front", eyes="wide", brows="worried", mouth="flat",
                               look=(0.9 * eyes_dart, 0), arm_a=8, arm_b=8, sweat=prog(t, ck + 0.3, ck + 0.8),
                               blink=False, squash=1 - 0.02 * pulse(t, ck, ck + 0.15, 0.05))
            fig(c, self, cam, HERO, hp, "hero")
        F.kitchen(cx, cam, t, power=0.0, curtains=0.0, table=False, before_fg=fg,
                  window_view=lambda c, x, y, w, h: (c.rectangle(x, y, w, h), src(c, hexc("#8D96A0")), c.fill()))
        cold_grade(cx, 0.7)
        F.grade_dark(cx, 0.15)
        vignette(cx, 0.6)


class S6Hallway(Shot):
    """The camera drifts into the dark hallway. Nothing there. Or is there."""
    scene = "s6"
    music = None
    amb = "house_dark"
    amb_gain = 0.8

    def plan(self, P):
        rem = P.voice.dur("l18") - 1.45
        P.sfx("step_wood2", t=rem + 0.15, vol=0.35)
        P.sfx("heartbeat", t=0.4, vol=0.5)
        P.sfx("heartbeat", t=1.25, vol=0.55)
        P.wait(rem + 0.55)

    def draw(self, cx, t):
        z = 1.0 + 0.45 * ease_in(prog(t, 0, 2.6))
        cam = Cam(540, 920, z)
        F.hallway(cx, cam, t, light=0.32)
        # a shadow slides across the far end of the hall
        s = prog(t, 1.0, 1.7)
        if 0 < s < 1:
            x, y = cam.to_screen(lerp(380, 700, s), 1000)
            ellipse(cx, x, y, 60 * cam.zoom, 140 * cam.zoom)
            src(cx, (0, 0, 0, 0.55 * math.sin(math.pi * s)))
            cx.fill()
        cold_grade(cx, 0.8)
        vignette(cx, 0.7)


# ================================================================ SCENE 7 - CLIFFHANGER
class S7Door(Shot):
    """He turns toward the kitchen. The back door is open. Cold light. Muddy footprints."""
    scene = "s7"
    music = None
    amb = "house_dark"
    amb_gain = 0.8

    def plan(self, P):
        P.sfx("door_creak", t=0.0, vol=0.45)
        P.wait(0.42)
        P.say("l19", gap=0.42)

    def draw(self, cx, t):
        z = 1.25 + 0.2 * ease_io(prog(t, 0, 2.6))
        cam = Cam(lerp(1980, 2120, ease_io(prog(t, 0, 2.6))), 1080, z)
        sway = 0.92 + 0.04 * math.sin(t * 1.4)

        def fg(c):
            # muddy footprints from the door toward the hallway (camera left)
            for k in range(7):
                fx = 2080 - k * 150
                fy = 1330 + (k % 2) * 60 + k * 18
                ellipse(c, fx, fy, 26, 12, -0.1)
                src(c, (0.16, 0.11, 0.07, 0.92 - k * 0.08))
                c.fill()
                ellipse(c, fx - 30, fy - 2, 10, 8)
                c.fill()
        F.kitchen(cx, cam, t, power=0.0, curtains=0.0, table=True, door_open=sway, before_fg=fg,
                  window_view=lambda c, x, y, w, h: (c.rectangle(x, y, w, h), src(c, hexc("#8D96A0")), c.fill()))
        # his shoulder + head in the foreground, slowly turning
        tn = ease_io(prog(t, 0, 1.2))
        world(cx, Cam(540, 960, 1.0))
        hp = hero_pose(lerp(80, 150, tn), 2350, t, s=3.4, f=1, eyes="wide", brows="worried", mouth="flat",
                       look=(1, 0), blink=False, arm_a=0, arm_b=0)
        cx.push_group()
        HERO.draw(cx, hp)
        cx.pop_group_to_source()
        cx.paint_with_alpha(1.0)
        end(cx)
        cold_grade(cx, 0.6)
        vignette(cx, 0.55)


class S7Face(Shot):
    """'But I locked that door.' Close-up, then cut to black."""
    scene = "s7"
    music = None
    amb = "house_dark"
    amb_gain = 0.7

    def plan(self, P):
        P.sfx("heartbeat", t=0.0, vol=0.55)
        P.sfx("heartbeat", t=0.8, vol=0.6)
        P.wait(0.15)
        P.say("l20", gap=0.0)
        P.wait(0.12)

    def draw(self, cx, t):
        z = 3.2 + 0.45 * ease_in(prog(t, 0, 1.6))
        cam = Cam(560, 1000, z)
        cx.rectangle(0, 0, W, H)
        src(cx, hexc("#1A1F28"))
        cx.fill()
        world(cx, cam)
        F._wallpaper(cx, 0, 1200, 0, 1240)
        hp = hero_pose(560, 1600, t, s=1.6, f=1, view="front", eyes="wide", brows="worried", mouth="wavy",
                       look=(0.35, 0), sweat=1.0, blink=False,
                       tilt=1.5 * math.sin(t * 40) * prog(t, 0.6, 1.2))
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)
        F.grade_dark(cx, 0.45)
        # cold light from the open door, camera right
        g = cairo.LinearGradient(W, 0, 0, 0)
        g.add_color_stop_rgba(0, 0.8, 0.9, 1.0, 0.32)
        g.add_color_stop_rgba(0.6, 0.8, 0.9, 1.0, 0.0)
        cx.set_source(g)
        cx.paint()
        cold_grade(cx, 0.6)
        vignette(cx, 0.7)


class S7Black(Shot):
    scene = "s7"
    music = None
    amb = None

    def plan(self, P):
        P.sfx("end_tone", t=0.0, vol=0.8)
        P.wait(1.6)

    def draw(self, cx, t):
        black(cx)

"""Scenes 1-4: hook, the neighbor, false confidence, the survival fact."""
from .common import *  # noqa


# ================================================================ SCENE 1 - HOOK
def farm_view(cam, t, before_fg=None, dark=0.0, **kw):
    """Draw the farm exterior into a window rect (x, y, w, h) through `cam`."""
    def view(cx, x, y, w, h):
        cx.save()
        cx.translate(x + w / 2 - W / 2, y + h / 2 - H / 2)
        F.farm_exterior(cx, cam, t, dark=dark, before_fg=before_fg, fence_fg=False, **kw)
        cx.restore()
    return view


class S1Window(Shot):
    """Over-the-shoulder: our guy at the farmhouse window; a zombie lurches across the yard."""
    scene = "s1"
    music = "dread"
    music_gain = 0.8
    amb = "house"

    def plan(self, P):
        P.sfx("groan_va_far", t=0.0, vol=0.7)
        P.wait(0.12)
        P.say("l01", gap=0.0)
        P.accent("DAY [1]", t=0.22, dur=1.35, size=64, pos=(W / 2, 205))
        cut_at(P, "l01", 1.52)

    def draw(self, cx, t):
        cam = Cam(540, 960, 1.0 + 0.05 * ease_io(prog(t, 0, 1.8)))
        zx = lerp(560, 1180, t / 1.8)

        def zomb(c):
            fig(c, self, None, ZOMBIE_B, shamble(zombie_pose(zx, 1440, t, s=1.35, f=1), t, 1.4, 1.2))
        view_cam = Cam(860, 1230, 0.62)
        world(cx, cam)
        F._wallpaper(cx, -200, 1300, -200, 2200)
        F._wainscot(cx, -200, 1300, top=1500, y1=2200)
        F.interior_window(cx, 150, 330, 780, 1000, view=farm_view(view_cam, t, zomb), curtains=0.0, t=t)
        # our guy, side-on in the foreground, peeking with a hand on the curtain
        lean = 6 + 4 * math.sin(t * 2)
        hp = hero_pose(330, 2140, t, s=2.7, f=1, eyes="wide", brows="worried", mouth="o", mouth_open=0.7,
                       look=(1, 0.1), lean=lean, arm_b=128, elb_b=-40, arm_a=20, elb_a=40, sweat=0.6)
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)
        cold_grade(cx, 0.35)
        vignette(cx, 0.45)


class S1FaceCU(Shot):
    """Outside looking in: his shocked face behind the glass, a zombie reflected in the pane."""
    scene = "s1"
    music = "dread"
    music_gain = 0.8
    amb = "farm"

    def plan(self, P):
        P.sfx("sting", t=0.0, vol=0.55)
        P.wait(0.62 + 0.3)

    def draw(self, cx, t):
        z = 1.0 + 0.12 * ease_out(prog(t, 0, 1.1))
        sx, sy = shake(t, 6 * (1 - prog(t, 0, 0.35)), 22)
        cam = Cam(540 + sx, 930 + sy, z)
        world(cx, cam)
        # clapboard wall
        cx.rectangle(-300, -300, 1700, 2600)
        src(cx, F.col("house"))
        cx.fill()
        for k in range(60):
            line(cx, [(-300, -300 + k * 44), (1400, -300 + k * 44)], F.col("house_sh"), 4)
        wx, wy, ww, wh = 150, 380, 780, 1100
        cx.rectangle(wx - 34, wy - 34, ww + 68, wh + 68)
        fs(cx, F.col("trim"), OUTLINE, 7)
        cx.save()
        cx.rectangle(wx, wy, ww, wh)
        cx.clip()
        cx.rectangle(wx, wy, ww, wh)
        src(cx, hexc("#2E3440"))
        cx.fill()
        # dim room behind him
        rrect(cx, wx + 520, wy + 120, 160, 220, 6)
        fs(cx, hexc("#3A4250"), None, 0)
        p = prog(t, 0.0, 0.25)
        hp = hero_pose(540, 1980, t, s=4.6, f=1, view="front", eyes="wide", brows="worried",
                       mouth="scream" if t > 0.2 else "o", mouth_open=0.5 + 0.4 * ease_out(p),
                       look=(0, 0), sweat=1.0, blink=False, arm_a=10, arm_b=10)
        hp = hp.but(head_dy=-10 * back_out(p))
        J = fig(cx, self, cam, HERO, hp, "hero")
        # zombie reflection sliding across the glass
        rx = lerp(1300, -200, t / 1.2)
        cx.push_group()
        ZOMBIE_C.draw(cx, shamble(zombie_pose(rx, 1700, t, s=3.0, f=-1), t, 1.3))
        cx.pop_group_to_source()
        cx.paint_with_alpha(0.16)
        # glass sheen
        poly(cx, [(wx + 60, wy + wh), (wx + 330, wy), (wx + 470, wy), (wx + 200, wy + wh)])
        src(cx, (1, 1, 1, 0.08))
        cx.fill()
        cx.restore()
        cx.rectangle(wx, wy, ww, wh)
        fs(cx, None, OUTLINE, 6)
        end(cx)
        cold_grade(cx, 0.25)
        vignette(cx, 0.5)


# ================================================================ SCENE 2 - THE NEIGHBOR
class S2Bed(Shot):
    """Woken by screaming: bolt upright in bed."""
    scene = "s2"
    trans_in = ("flash", 0.18)
    music = "dread"
    music_gain = 0.7
    amb = "house"

    def plan(self, P):
        P.sfx("scream_far", t=0.0, vol=0.6)
        P.sfx("bed_jolt", t=0.22, vol=0.7)
        P.wait(0.12)
        P.say("l02", gap=0.0)
        cut_at(P, "l02", 1.32)

    def draw(self, cx, t):
        cam = Cam(430, 1000, 2.0 + 0.08 * t)
        F.bedroom(cx, cam, t)
        world(cx, cam)
        up = back_out(prog(t, 0.22, 0.48), 2.2)
        ang = lerp(-math.pi / 2, 0, clamp(up, 0, 1.15))
        px, py = 470, 1150
        cx.save()
        cx.translate(px, py)
        cx.rotate(ang)
        sat = clamp(up)          # legs swing forward under the quilt as he sits up
        hp = hero_pose(0, 116, t, s=1.0, f=1, view="side",
                       eyes="closed" if t < 0.22 else "wide", brows="neutral" if t < 0.22 else "worried",
                       mouth="smile" if t < 0.22 else "scream", mouth_open=0.7, sweat=1.0 if t > 0.3 else 0,
                       arm_a=50 if up > 0.5 else 10, arm_b=70 if up > 0.5 else 10, elb_a=30, elb_b=30,
                       look=(0.8, -0.2) if t > 0.7 else (1, 0), blink=False,
                       hip_a=88 * sat, hip_b=86 * sat, knee_a=2, knee_b=0)
        HERO.draw(cx, hp)
        cx.restore()
        end(cx)
        F.quilt(cx, cam, lift=-10 + 20 * clamp(up, 0, 1))
        # Zzz before the jolt, alarm lines after
        if t < 0.22:
            world(cx, cam)
            text(cx, "z", 420, 980 - t * 120, 48, (1, 1, 1, 0.8))
            end(cx)
        tint(cx, (0.95, 0.75, 0.55), 0.06)
        vignette(cx, 0.4)


class S2Chase(Shot):
    """Out in the yard: the neighbor chasing the mailman."""
    scene = "s2"
    music = "dread"
    music_gain = 0.75
    amb = "farm"

    def plan(self, P):
        P.sfx("scream_far2", t=0.15, vol=0.7)
        P.sfx("groan_vb", t=0.5, vol=0.55)
        for k in range(10):
            P.sfx("step", t=0.1 + k * 0.21, vol=0.25)
        P.sfx("paper", t=0.9, vol=0.4)
        d = P.voice.dur("l02") - 1.32
        P.wait(d + 0.25)

    def draw(self, cx, t):
        mx = lerp(250, 1700, t / 3.4)
        nx = mx - lerp(560, 300, t / 3.4)
        cam = Cam(lerp(560, 1250, ease_io(t / 3.4)), 1330, 1.3)

        def chars(c):
            shadow(c, nx, 1500, 70)
            shadow(c, mx, 1500, 60)
            np_ = run(zombie_pose(nx, 1500, t, s=1.25, f=1, mouth="teeth"), t, 2.2, 0.8)
            np_ = np_.but(arm_a=88 + 10 * math.sin(t * 13), arm_b=82 - 10 * math.sin(t * 13), elb_a=0, elb_b=0,
                          extra={"drool": 0.6})
            fig(c, self, None, NEIGHBOR, np_)
            mp = run(Pose(x=mx, y=1500, s=1.25, f=1, t=t, eyes="wide", mouth="scream", brows="worried", sweat=1,
                          look=(-1, 0), blink=False), t, 2.7, 1.0, flail=True)
            fig(c, self, None, MAILMAN, mp)
            letters(c, max(0, t - 0.9), mx - 40, 1380, 6)
        F.farm_exterior(cx, cam, t, before_fg=chars, curtains=0.0)
        vignette(cx, 0.35)


class S2Crawl(Shot):
    """...on all fours."""
    scene = "s2"
    music = "dread"
    music_gain = 0.6
    amb = "farm"

    def plan(self, P):
        P.sfx("whoosh_soft", t=0.0, vol=0.5)
        P.sfx("groan1", t=0.15, vol=0.5)
        P.wait(0.12)
        P.say("l03", gap=0.35)
        for k in range(12):
            P.sfx("step", t=k * 0.15, vol=0.18)

    def draw(self, cx, t):
        speed = 900
        cam = Cam(540 + t * speed, 1320, 1.25)

        def chars(c):
            x = 540 + t * speed - 80
            shadow(c, x, 1500, 120)
            p = crawl(zombie_pose(x, 1500, t, s=1.6, f=1, mouth="teeth", eyes="wide", look=(1, -0.3),
                                  extra={"drool": 1.0}), t, 3.4)
            fig(c, self, None, NEIGHBOR, p)
            # the mailman's legs just ahead, frame right
            mp = run(Pose(x=x + 560, y=1500, s=1.6, f=1, t=t), t, 2.9, 1.0)
            fig(c, self, None, MAILMAN, mp)
        F.farm_exterior(cx, cam, t, before_fg=chars, house=False)
        speed_lines(cx, t, 0, W, 900, 1700, 12, 0.35)
        vignette(cx, 0.35)


class S2Curtains(Shot):
    """Panic: yank the curtains shut."""
    scene = "s2"
    music = "dread"
    music_gain = 0.6
    amb = "house"

    def plan(self, P):
        P.sfx("curtain", t=0.18, vol=0.8)
        P.wait(0.05)
        P.say("l04", gap=0.22)

    def draw(self, cx, t):
        cam = Cam(560, 870, 1.32)
        cur = ease_out(prog(t, 0.14, 0.42))
        tc = t

        def outside(c, x, y, w, h):
            vc = Cam(1150, 1260, 0.55)
            c.save()
            c.translate(x + w / 2 - W / 2, y + h / 2 - H / 2)

            def z(cc):
                p = crawl(zombie_pose(900 + tc * 260, 1480, tc, s=1.3, f=1, extra={"drool": 1}), tc, 3.4)
                NEIGHBOR.draw(cc, p)
            F.farm_exterior(c, vc, tc, before_fg=z, fence_fg=False)
            c.restore()

        def fg(c):
            # arms out to the curtain edges, then turns to us with a Very Good Idea
            turned = t > 0.75
            hx = 550
            hp = hero_pose(hx, 1500, t, s=1.65, f=1, view="front",
                           eyes="wide" if not turned else "open", brows="worried" if not turned else "up",
                           mouth="scream" if not turned else "smirk", mouth_open=0.6, sweat=0 if turned else 1,
                           arm_a=lerp(150, 30, prog(t, 0.45, 0.75)), arm_b=lerp(150, 165, prog(t, 0.75, 0.95)),
                           elb_a=lerp(-20, 40, prog(t, 0.45, 0.75)), elb_b=lerp(-20, -150, prog(t, 0.75, 0.95)),
                           look=(0, 0), bob=-6 * pulse(t, 0.15, 0.4, 0.1))
            fig(c, self, cam, HERO, hp, "hero")
        F.kitchen(cx, cam, t, power=1.0, curtains=cur, window_view=outside, table=False, before_fg=fg)
        vignette(cx, 0.38)


class S2Lock(Shot):
    """Deadbolt. Chain."""
    scene = "s2"
    music = "dread"
    music_gain = 0.55
    amb = "house"

    def plan(self, P):
        P.wait(0.05)
        P.say("l05", gap=0.0)
        P.sfx("lock", t=P.m["l05"][0] + 0.32, vol=0.6)
        P.sfx("chain", t=P.m["l05"][0] + 0.72, vol=0.55)
        cut_at(P, "l05", 1.6)

    def draw(self, cx, t):
        a = self.mt("l05")
        bolt = ease_out(prog(t, a + 0.25, a + 0.45))
        chain = ease_io(prog(t, a + 0.65, a + 1.1))
        z = 1.0 + 0.04 * t
        cx.save()
        cx.translate(W / 2, H / 2)
        cx.scale(z, z)
        cx.translate(-W / 2, -H / 2)
        F.front_door_close(cx, t, bolt, chain, light=0.85)
        # his hand on the bolt, then on the chain
        if t < a + 0.6:
            hx, hy = 750 + 60 * math.cos(-math.pi / 2 * (1 - bolt)), 960 + 60 * math.sin(-math.pi / 2 * (1 - bolt))
            big_hand(cx, -200, 1800, hx, hy)
        else:
            hx, hy = lerp(820, 1010, chain), lerp(760, 540, chain)
            big_hand(cx, -200, 1500, hx, hy)
        cx.restore()
        vignette(cx, 0.45)


def big_hand(cx, x0, y0, x1, y1, w=26, sleeve="#2F6FDB"):
    line(cx, [(x0, y0), (x1, y1)], OUTLINE, w)
    mx, my = x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.55
    line(cx, [(x0, y0), (mx, my)], OUTLINE, w * 3.4)
    line(cx, [(x0, y0), (mx, my)], hexc(sleeve), w * 2.8)
    circle(cx, x1, y1, w * 1.05)
    fs(cx, OUTLINE, None, 0)


class S2Breakfast(Shot):
    """...and made breakfast."""
    scene = "s2"
    music = "confident"
    music_gain = 0.85
    amb = "house"

    def plan(self, P):
        P.sfx("dishes", t=0.15, vol=0.35)
        P.sfx("chew", t=1.15, vol=0.5)
        P.sfx("groan_vb_far", t=1.0, vol=0.45)
        rem = P.voice.dur("l05") - 1.6
        P.wait(rem + 0.8)

    def draw(self, cx, t):
        cam = Cam(560, 1250, 1.45 - 0.05 * t)
        chew = t > 1.0

        def outside(c, x, y, w, h):
            c.rectangle(x, y, w, h)
            src(c, hexc("#C9C3B5"))
            c.fill()

        def fg(c):
            # chair
            rrect(c, 380, 1080, 26, 520, 6)
            fs(c, hexc("#6E4F37"), OUTLINE, 5)
            fork_up = 0.5 + 0.5 * math.sin(t * 6.5) if chew else 0.2
            hp = hero_pose(560, 1600, t, s=1.45, f=1, view="front", eyes="happy" if chew else "closed",
                           brows="neutral", mouth="chew" if chew else "smile", mouth_open=0.4 + 0.6 * fork_up,
                           arm_a=30, elb_a=20, arm_b=lerp(40, 150, fork_up), elb_b=lerp(30, -150, fork_up))
            hp = sit(hp).but(bob=hp.bob + 46)
            fig(c, self, cam, HERO, hp, "hero")
            F.kitchen_table(c, 250, 1460, 620)
            F.breakfast(c, 520, 1450, 1.1, eaten=prog(t, 0.6, 2.8) * 0.7, t=t)
        F.kitchen(cx, cam, t, power=1.0, curtains=1.0, window_view=outside, table=False, before_fg=fg)
        _curtain_shadow(cx, cam, t)
        warm_grade(cx, 1)
        vignette(cx, 0.3)


def _curtain_shadow(cx, cam, t):
    """A lurching silhouette crossing behind the closed curtains."""
    x0, y0 = cam.to_screen(330, 470)
    x1, y1 = cam.to_screen(770, 940)
    sx = lerp(x0 - 200, x1 + 200, prog(t, 0.5, 3.0))
    cx.save()
    cx.rectangle(x0 - 60 * cam.zoom, y0, (x1 - x0) + 120 * cam.zoom, (y1 - y0) + 60 * cam.zoom)
    cx.clip()
    cx.translate(sx, y1 + 220 * cam.zoom)
    cx.scale(cam.zoom * 1.25, cam.zoom * 1.25)
    cx.push_group()
    ZOMBIE_B.draw(cx, shamble(zombie_pose(0, 0, t, s=1.0, f=1), t, 1.1))
    pat = cx.pop_group()
    cx.set_source_rgba(0.18, 0.08, 0.06, 0.42)
    cx.mask(pat)
    cx.restore()


# ================================================================ SCENE 3 - FALSE CONFIDENCE
class S3Montage(Shot):
    """'I mean, it's a farm. We have food, space, and a well.' Quick, sunny, confident."""
    scene = "s3"
    music = "confident"
    music_gain = 0.85
    amb = "farm"

    def plan(self, P):
        P.wait(0.12)
        a = P.say("l06", gap=0.18)
        for off in (0.72, 2.42, 3.05, 3.58, 4.75):
            P.sfx("whoosh_soft", t=a + off - 0.05, vol=0.35)
        self.cuts = [a + 0.74, a + 2.44, a + 3.06, a + 3.6, a + 4.77]

    def draw(self, cx, t):
        c = self.cuts
        if t < c[0]:
            # 'I mean' - arms wide, very sure of himself, in the kitchen
            cam = Cam(560, 1180, 1.5)

            def fg(x):
                hp = hero_pose(560, 1600, t, s=1.5, f=1, view="front", eyes="happy", brows="up", mouth="grin",
                               mouth_open=0.6, arm_a=lerp(30, 120, ease_out(prog(t, 0, 0.4))), elb_a=-10,
                               arm_b=lerp(30, 120, ease_out(prog(t, 0, 0.4))), elb_b=-10)
                fig(x, self, cam, HERO, hp, "hero")
            F.kitchen(cx, cam, t, power=1.0, curtains=1.0, table=False, before_fg=fg)
            warm_grade(cx, 1)
        elif t < c[1]:
            u = t - c[0]
            cam = Cam(lerp(500, 900, u / 1.8), 1050, 0.6)
            F.farm_exterior(cx, cam, t, fog=0.35, win_glow=0.2)
            warm_grade(cx, 1.5)
        elif t < c[2]:
            u = t - c[1]
            cam = Cam(850, 1240, 2.6 + 0.2 * u)
            F.farm_exterior(cx, cam, t, fence_fg=False)
            warm_grade(cx, 1.5)
        elif t < c[3]:
            u = t - c[2]
            F.pantry(cx, Cam(540, 900 - 40 * u, 1.05 + 0.08 * u), t, light=0.95)
            warm_grade(cx, 1.5)
        elif t < c[4]:
            u = t - c[3]
            cam = Cam(lerp(1800, 2300, u / 1.2), 1000, 0.5)
            F.farm_exterior(cx, cam, t, fog=0.3, fence_fg=False)
            warm_grade(cx, 1.5)
        else:
            u = t - c[4]
            cam = Cam(1060, 1180 - 30 * u, 1.65 + 0.1 * u)
            F.farm_exterior(cx, cam, t, fence_fg=False)
            warm_grade(cx, 1.5)
        vignette(cx, 0.3)


class S3Smug(Shot):
    """'What could go wrong?' ... 'Then the lights died.'"""
    scene = "s3"
    music = "confident"
    music_gain = 0.85
    amb = "house"

    def plan(self, P):
        P.wait(0.05)
        P.say("l07", gap=0.3)
        a = P.say("l08", gap=0.0)
        self.off_t = a + 0.5
        P.sfx("power_down", t=self.off_t, vol=0.5)
        self.music_until = self.off_t
        P.accent("NO [POWER]", t=self.off_t + 0.4, dur=a + P.voice.dur("l08") + 0.6 - self.off_t - 0.65,
                 size=ACCENT_SIZE, pos=(W / 2, ACCENT_Y))
        P.wait(0.6)

    def draw(self, cx, t):
        off = self.off_t
        flick = 1.0
        if t > off:
            u = t - off
            flick = 0.0 if u > 0.32 else (1.0 if int(u * 28) % 3 else 0.15) * (1 - u / 0.32)
        cam = Cam(560, 1150, 1.45 + 0.05 * t)

        def fg(c):
            rrect(c, 380, 1080, 26, 520, 6)
            fs(c, hexc("#6E4F37"), OUTLINE, 5)
            dark = t > off + 0.3
            look_up = ease_out(prog(t, off + 0.7, off + 1.0))
            hp = hero_pose(560, 1600, t, s=1.45, f=1, view="front",
                           eyes="happy" if not dark else ("open" if look_up < 0.5 else "half"),
                           brows="up" if not dark else "flat", mouth="grin" if t < off + 0.9 else "flat",
                           mouth_open=0.7, arm_a=165, elb_a=-150, arm_b=165, elb_b=-150,
                           look=(0, -1.0 * look_up), tilt=-6 + 4 * math.sin(t * 2) * (not dark))
            hp = sit(hp).but(bob=hp.bob + 40, lean=-8)
            fig(c, self, cam, HERO, hp, "hero")
            F.kitchen_table(c, 250, 1460, 620)
            F.breakfast(c, 520, 1450, 1.1, eaten=0.7, t=t, steam=flick)
        F.kitchen(cx, cam, t, power=flick, curtains=1.0, table=False, before_fg=fg,
                  window_view=lambda c, x, y, w, h: (c.rectangle(x, y, w, h), src(c, hexc("#C9C3B5")), c.fill()))
        if t < off:
            warm_grade(cx, 1)
        else:
            cold_grade(cx, 0.6)
        vignette(cx, 0.35 + 0.2 * (t > off))


# ================================================================ SCENE 4 - SURVIVAL FACT
class S4Faucet(Shot):
    scene = "s4"
    music = "dread"
    music_gain = 0.55
    amb = "house_dark"

    def plan(self, P):
        P.sfx("faucet", t=0.0, vol=0.45)
        P.wait(0.15)
        P.say("l09", gap=0.0)
        P.accent("NO [WATER]", t=0.95, dur=1.0, size=ACCENT_SIZE, pos=(W / 2, ACCENT_Y))
        cut_at(P, "l09", 0.98)

    def draw(self, cx, t):
        cam = Cam(1440, 960, 1.75 + 0.06 * t)
        h = ease_out(prog(t, 0.05, 0.3))

        def fg(c):
            lean_in = ease_io(prog(t, 0.6, 1.0))
            hp = hero_pose(1250, 1300, t, s=1.3, f=1, eyes="wide" if lean_in > 0.5 else "open",
                           brows="skeptic", mouth="flat", arm_b=lerp(70, 115, h), elb_b=lerp(30, 10, h),
                           arm_a=10, lean=12 + 16 * lean_in, look=(0.6, 0.6))
            fig(c, self, cam, HERO, hp, "hero")
            # one sad drip
            if 0.95 < t < 1.25:
                dy = (t - 0.95) * 600
                ellipse(c, 1494, 978 + dy, 6, 9)
                fs(c, hexc("#8FD3FF"), OUTLINE, 2)
        F.kitchen(cx, cam, t, power=0.0, curtains=1.0, before_fg=fg, faucet_handle=h, table=False)
        cold_grade(cx, 0.6)
        vignette(cx, 0.45)


class S4Pump(Shot):
    scene = "s4"
    music = "dread"
    music_gain = 0.55
    amb = "house_dark"

    def plan(self, P):
        P.sfx("pump_stop", t=0.0, vol=0.8)
        rem = P.voice.dur("l09") - 0.98
        P.wait(rem + 0.3)

    def draw(self, cx, t):
        cam = Cam(540, 1000, 1.0 + 0.05 * t)
        on = 1.0 - prog(t, 0.05, 0.5)
        flick = on if on < 0.05 or on > 0.95 else (1.0 if int(t * 30) % 2 else 0.2) * on
        cx.rectangle(0, 0, W, H)
        src(cx, hexc("#4A4640"))
        cx.fill()
        world(cx, cam)
        cx.rectangle(-300, 1500, 1700, 900)
        src(cx, hexc("#3A3530"))
        cx.fill()
        line(cx, [(-300, 1500), (1400, 1500)], OUTLINE, 5)
        F.pump_unit(cx, 640, 1480, 1.3, flick, t, needle=1 - prog(t, 0.2, 1.2))
        # he peeks in with a flashlight
        u = ease_out(prog(t, 0.1, 0.6))
        hp = hero_pose(lerp(-60, 120, u), 1700, t, s=1.5, f=1, eyes="wide", brows="worried", mouth="frown",
                       arm_b=95, elb_b=-5, lean=8, look=(1, -0.2))
        J = fig(cx, self, cam, HERO, hp, "hero")
        hx, hy = J["hand_b"]
        cx.save()
        g = cairo.RadialGradient(hx, hy, 10, hx + 420, hy - 180, 360)
        g.add_color_stop_rgba(0, 1, 0.97, 0.8, 0.35)
        g.add_color_stop_rgba(1, 1, 0.97, 0.8, 0)
        cx.set_source(g)
        poly(cx, [(hx, hy - 10), (hx + 900, hy - 520), (hx + 900, hy + 260), (hx, hy + 10)])
        cx.fill()
        cx.restore()
        rrect(cx, hx - 10, hy - 14, 50, 28, 8)
        fs(cx, hexc("#2B2B33"), OUTLINE, 3)
        end(cx)
        F.grade_dark(cx, 0.35)
        vignette(cx, 0.55)


class S4Diagram(Shot):
    """ELECTRICITY -> WELL PUMP -> WATER, then the chain breaks; then stored drinking water."""
    scene = "s4"
    music = "dread"
    music_gain = 0.45
    amb = "house_dark"

    def plan(self, P):
        P.sfx("pop_in", t=0.12, vol=0.5)
        P.sfx("pop_in", t=0.32, vol=0.5)
        P.sfx("pop_in", t=0.52, vol=0.5)
        P.wait(0.1)
        a = P.say("l10", gap=0.0)
        self.a = a
        P.sfx("power_down", t=a + 1.05, vol=0.35)
        P.sfx("pop_in", t=a + 2.5, vol=0.5)
        P.sfx("pop_in", t=a + 2.65, vol=0.5)
        P.sfx("pop_in", t=a + 2.8, vol=0.5)
        P.wait(0.1)

    def draw(self, cx, t):
        a = self.a
        g = cairo.RadialGradient(W / 2, H * 0.45, 100, W / 2, H * 0.45, H * 0.8)
        g.add_color_stop_rgba(0, *hexc("#2E3B4A"))
        g.add_color_stop_rgba(1, *hexc("#151B24"))
        cx.set_source(g)
        cx.paint()
        for k in range(0, W, 60):
            line(cx, [(k, 0), (k, H)], (1, 1, 1, 0.03), 2)
        for k in range(0, H, 60):
            line(cx, [(0, k), (W, k)], (1, 1, 1, 0.03), 2)
        swap = ease_io(prog(t, a + 2.35, a + 2.75))
        cx.save()
        cx.translate(-W * 1.1 * swap, 0)
        nodes = [(560, "ELECTRICITY", _icon_bolt), (1000, "WELL PUMP", _icon_pump), (1440, "WATER", _icon_drop)]
        offs = [a + 1.0, a + 1.3, a + 1.6]
        for k, (y, label, icon) in enumerate(nodes):
            pin = back_out(prog(t, 0.12 + k * 0.2, 0.42 + k * 0.2))
            dead = ease_out(prog(t, offs[k], offs[k] + 0.25))
            if pin <= 0:
                continue
            cx.save()
            cx.translate(330, y)
            cx.scale(pin, pin)
            circle(cx, 0, 0, 120)
            fs(cx, mix(hexc("#F3EEE2"), hexc("#6B7280"), dead), OUTLINE, 7)
            icon(cx, dead, t)
            if dead > 0.5:
                line(cx, [(-80, -80), (80, 80)], hexc("#E04848"), 14)
            cx.restore()
            _label(cx, label, 470, y, 58, pin, dead)
            if k < 2:
                flow = prog(t, 0.5 + k * 0.2, 0.8 + k * 0.2) * (1 - dead)
                _arrow(cx, 330, y + 135, 330, y + 305, t, flow, dead)
        cx.restore()
        if swap > 0:
            cx.save()
            cx.translate(W * (1 - swap), 0)
            for k in range(3):
                pin = back_out(prog(t, a + 2.5 + k * 0.15, a + 2.8 + k * 0.15))
                if pin > 0:
                    cx.save()
                    cx.translate(270 + k * 270, 1200)
                    cx.scale(pin, pin)
                    F.water_jug(cx, 0, 0, 1.45)
                    cx.restore()
            _label(cx, "1 GALLON\nPER PERSON, PER DAY", W / 2, 700, 64, ease_out(prog(t, a + 2.9, a + 3.2)), 0,
                   center=True, hi=True)
            cx.restore()
        vignette(cx, 0.4)


def _label(cx, s, x, y, size, a, dead, center=False, hi=False):
    if a <= 0:
        return
    if hi:
        s = s.split("\n")
        s = "[" + s[0] + "]\n" + s[1] if len(s) > 1 else "[" + s[0] + "]"
    surf, w, h, pad = captions.render_text(s, size)
    cx.save()
    cx.translate(x - (w / 2 if center else pad), y - h / 2)
    cx.set_source_surface(surf, 0, 0)
    cx.paint_with_alpha(a * (1 - 0.55 * dead))
    cx.restore()


def _arrow(cx, x0, y0, x1, y1, t, flow, dead):
    c = mix(hexc("#FFD43B"), hexc("#6B7280"), dead)
    line(cx, [(x0, y0), (x1, y1 - 20)], c, 10)
    poly(cx, [(x1 - 28, y1 - 34), (x1, y1), (x1 + 28, y1 - 34)])
    src(cx, c)
    cx.fill()
    if flow > 0:
        for k in range(3):
            u = ((t * 1.6 + k / 3) % 1)
            circle(cx, x0, y0 + (y1 - y0) * u, 9)
            src(cx, (1, 1, 1, 0.9 * flow))
            cx.fill()


def _icon_bolt(cx, dead, t):
    c = mix(hexc("#FFD43B"), hexc("#9CA3AF"), dead)
    poly(cx, [(10, -80), (-50, 10), (-6, 10), (-20, 80), (52, -14), (8, -14), (24, -80)])
    fs(cx, c, OUTLINE, 6)


def _icon_pump(cx, dead, t):
    rrect(cx, -60, -70, 80, 140, 30)
    fs(cx, mix(hexc("#3E6FA8"), hexc("#7B8794"), dead), OUTLINE, 6)
    rrect(cx, 26, -50, 50, 70, 8)
    fs(cx, hexc("#BFC3C7"), OUTLINE, 5)
    circle(cx, 51, -26, 11)
    fs(cx, mix(hexc("#55F06A"), hexc("#3A3D40"), dead), OUTLINE, 3)
    if dead < 0.5:
        a = t * 8
        line(cx, [(51, 2), (51 + 12 * math.cos(a), 2 + 12 * math.sin(a))], OUTLINE, 3)


def _icon_drop(cx, dead, t):
    s = 1 - 0.25 * dead
    cx.save()
    cx.scale(s, s)
    cx.move_to(0, -80)
    cx.curve_to(30, -30, 62, 0, 62, 26)
    cx.curve_to(62, 66, 30, 84, 0, 84)
    cx.curve_to(-30, 84, -62, 66, -62, 26)
    cx.curve_to(-62, 0, -30, -30, 0, -80)
    cx.close_path()
    fs(cx, mix(hexc("#5DB8F0"), hexc("#9CA3AF"), dead), OUTLINE, 6)
    ellipse(cx, -22, 20, 10, 18, 0.3)
    src(cx, (1, 1, 1, 0.6))
    cx.fill()
    cx.restore()


class S4Bottle(Shot):
    """'A farm doesn't magically make you self-sufficient.' One tiny bottle of water."""
    scene = "s4"
    music = "dread"
    music_gain = 0.5
    amb = "house_dark"

    def plan(self, P):
        P.wait(0.05)
        P.say("l11", gap=0.25)

    def draw(self, cx, t):
        cam = Cam(700, 1120, 1.55 + 0.05 * t)

        def fg(c):
            look_cam = t > 1.6
            hp = hero_pose(700, 1560, t, s=1.45, f=-1, view="front", eyes="half" if look_cam else "open",
                           brows="skeptic" if not look_cam else "worried", mouth="flat" if not look_cam else "wavy",
                           arm_b=125, elb_b=-110, arm_a=15, elb_a=20, look=(0.7, -0.3) if not look_cam else (0, 0),
                           sweat=prog(t, 1.8, 2.3))
            J = fig(c, self, cam, HERO, hp, "hero")
            hx, hy = J["hand_b"]
            # a sad little bottle
            rrect(c, hx - 16, hy - 70, 32, 70, 10)
            fs(c, hexc("#DCEBF5", 0.95), OUTLINE, 4)
            rrect(c, hx - 16, hy - 40, 32, 40, 8)
            src(c, hexc("#7FC4F0", 0.6))
            c.fill()
            rrect(c, hx - 10, hy - 82, 20, 14, 4)
            fs(c, hexc("#2F6FDB"), OUTLINE, 3)
        F.kitchen(cx, cam, t, power=0.0, curtains=1.0, table=False, before_fg=fg)
        cold_grade(cx, 0.55)
        vignette(cx, 0.45)

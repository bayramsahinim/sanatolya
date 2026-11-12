"""Scene 1 (cold open) and Scene 2 (Day 1: the worst purchase)."""
from .common import *  # noqa


# =============================================================== SCENE 1
class S1ColdOpen(Shot):
    scene = "s1"
    music = "chase"
    amb = "street"

    def plan(self, P):
        P.sfx("step", t=0.0, vol=0.0)  # (anchor)
        P.wait(1.5)
        a = P.say("s1_01", gap=0.25)
        P.accent("[$12] TIME MACHINE", t=a + 0.25, dur=self_dur(P, "s1_01") - 0.1, size=92)
        P.say("s1_02", gap=0.15)
        tf = P.mark("freeze")
        P.sfx("scratch", t=tf - 0.05, vol=0.9)
        P.sfx("freeze", t=tf, vol=0.7)
        P.wait(0.45)
        P.say("s1_03", gap=0.55)
        P.say("s1_04", gap=0.25)
        self.tail = 0.1
        # footsteps
        for k in range(int(tf / 0.23)):
            P.sfx("step", t=k * 0.23, vol=0.35)
            P.sfx("step_heavy", t=k * 0.27 + 0.1, vol=0.3)
        P.sfx("clank", t=0.4, vol=0.4)
        P.sfx("clank", t=1.7, vol=0.35)
        P.sfx("whoosh", t=tf - 0.7, vol=0.5)

    def state(self, t):
        tf = self.mt("freeze")
        ta = min(t, tf)
        hx = 300 + 560 * ta
        gap = lerp(430, 120, ease_in(prog(ta, 0.6, tf)))
        return ta, tf, hx, gap

    def draw(self, cx, t):
        ta, tf, hx, gap = self.state(t)
        frozen = t >= tf
        z = 1.0 if not frozen else 1.0 + 0.10 * ease_out(prog(t, tf, tf + 2.2))
        cam = Cam(hx - 170, 640 if not frozen else 660, 1.3 * z)
        if not frozen:
            sx, sy = shake(ta, 4, 9)
            cam.x += sx
        S.rome_street(cx, cam, ta, x0=-1500, x1=8000)
        world(cx, cam)
        # pursuers
        for i in range(2):
            px = hx - gap - 230 - i * 170
            fig(cx, self, cam, soldier(i), run(max_pose(px, GY - 10, ta + i * 0.3, s=1.12, mouth="yell",
                                                      brows="angry"), ta + i * 0.3, 2.1, 0.9))
        mx = hx - gap
        mp = run(max_pose(mx, GY, ta, mouth="yell", eyes="angry", brows="angry"), ta, 2.0, 0.95)
        reach = ease_out(prog(ta, tf - 1.3, tf - 0.15))
        mp = mp.but(arm_b=lerp(mp.arm_b, 92, reach), elb_b=lerp(mp.elb_b, -8, reach), lean=mp.lean + 10 * reach)
        J = fig(cx, self, cam, WET_MAX, mp, "max")
        P.drips(cx, mx, J["head"][1] + 40, 120, ta, 6, 0.8)
        # hero
        stumble = ease_out(prog(ta, tf - 0.55, tf))
        hp = run(hero_pose(hx, GY, ta, eyes="wide", mouth="scream", brows="worried", sweat=1.0,
                           look=(-1, 0) if stumble > 0.3 else (0.6, 0)), ta, 2.4, 1.0, flail=stumble > 0.3)
        hp = hp.but(lean=hp.lean + 18 * stumble, tilt=-25 * stumble, bob=hp.bob - 30 * stumble,
                    hip_b=lerp(hp.hip_b, -40, stumble), knee_b=lerp(hp.knee_b, 80, stumble))
        hJ = fig(cx, self, cam, HERO, hp, "hero")
        # Maximus' fingers nearly on the hood
        if reach > 0.6:
            hood = (hJ["neck"][0] - 30, hJ["neck"][1] - 10)
            hand = J["hand_b"]
            line(cx, [hand, hood], hexc("#2257B5"), 10 * (reach - 0.6) / 0.4)
        P.motion_puffs(cx, hx - 30, GY, ta, 3, 0.8)
        end(cx)
        if frozen:
            k = prog(t, tf, tf + 0.15)
            flash(cx, 0.85 * (1 - k))
            desaturate(cx, 0.35)
            vignette(cx, 0.45)


def self_dur(P, lid):
    return P.voice.dur(lid)


class S1Rewind(Shot):
    scene = "s1"
    music = None
    amb = None

    def __init__(self, cold):
        super().__init__()
        self.cold = cold

    def plan(self, P):
        P.sfx("rewind", t=0.0, vol=0.8)
        P.wait(2.3)
        P.accent("7 DAYS EARLIER", t=1.2, dur=1.4, size=100, pos=(W / 2, H / 2))

    def draw(self, cx, t):
        tf = self.cold.mt("freeze")
        tt = max(0.0, tf - (t * 2.6) ** 1.3)
        self.cold.draw(cx, tt)
        self.heads = {}
        desaturate(cx, 0.6)
        tint(cx, (0.1, 0.15, 0.35), 0.25 + 0.4 * prog(t, 1.2, 2.3))
        # tape lines
        import random
        r = random.Random(int(t * 30))
        for k in range(5):
            y = r.random() * H
            cx.rectangle(0, y, W, 3 + r.random() * 6)
            src(cx, (1, 1, 1, 0.15 + 0.2 * r.random()))
            cx.fill()
        # rewind glyph
        for k in range(2):
            x0 = 90 + k * 46
            cx.move_to(x0 + 40, 70)
            cx.line_to(x0, 100)
            cx.line_to(x0 + 40, 130)
            cx.close_path()
            src(cx, (1, 1, 1, 0.9))
            cx.fill()


# =============================================================== SCENE 2
class S2Room(Shot):
    scene = "s2"
    trans_in = ("dip", 0.45)
    music = "room"
    amb = "room"

    def plan(self, P):
        P.accent("DAY 1", t=0.35, dur=1.7, size=120)
        P.wait(0.9)
        P.say("s2_01", gap=0.5)

    def draw(self, cx, t):
        cam = cam_kf(t, [(0, (900, 680, 1.5)), (6, (880, 700, 1.65))])
        S.room(cx, cam, t)
        world(cx, cam)
        P.product_box(cx, 620, GROUND + 14, 1.0, open_=1.0)
        lift = win(t, 1.0, 1.8)
        p = breathe(hero_pose(980, GROUND + 20, t, f=-1, eyes="open", mouth="grin" if lift > 0.5 else "smile",
                               look=(-0.8, -0.6) if lift > 0.5 else (-0.5, 0.2)), t)
        p = p.but(arm_b=lerp(-8, 125, lift), elb_b=lerp(10, 60, lift), tilt=-8 * lift)
        J = fig(cx, self, cam, HERO, p, "hero")
        P.wrist_watch_small(cx, *J["hand_b"], 1.2, 0.3, 0.6 * lift)
        if lift > 0.8:
            P.sparkles(cx, J["hand_b"][0], J["hand_b"][1], t, 40, 4, 0.8)
        end(cx)


class S2Reviews(Shot):
    scene = "s2"
    music = "room"
    amb = "room"

    def plan(self, P):
        P.wait(0.25)
        P.say("s2_02", gap=0.3)
        a = P.say("s2_03", gap=0.35)
        d = P.voice.dur("s2_03")
        for k in range(3):
            P.mark(f"star{k}", a + d * k / 3)
            P.sfx("pop", t=a + d * k / 3 + 0.05, vol=0.6)
        b = P.say("s2_04", gap=0.6)
        P.mark("fridge", b)
        P.sfx("slide_up", t=b, vol=0.35)

    def draw(self, cx, t):
        insert_bg(cx, "#F3D9B1", "#E5B98A")
        scroll = 170 * win(t, self.mt("fridge") - 0.2, self.mt("fridge") + 0.4)

        def screen(c, w, h):
            c.rectangle(0, 0, w, 64)
            src(c, hexc("#2F6FDB"))
            c.fill()
            text(c, "TIME MACHINE  $12", w / 2, 42, 20, (1, 1, 1, 1))
            c.translate(0, -scroll)
            for k in range(4):
                key = f"star{k}" if k < 3 else "fridge"
                a = ease_out(prog(t, self.mt(key), self.mt(key) + 0.25))
                if a <= 0:
                    continue
                y = 90 + k * 128
                c.save()
                c.translate(w / 2, y + 50)
                c.scale(0.9 + 0.1 * a, 0.9 + 0.1 * a)
                c.translate(-w / 2, -(y + 50))
                rrect(c, 14, y, w - 28, 110, 14)
                fs(c, hexc("#FFFFFF", a), hexc("#D0D4DC", a), 2)
                circle(c, 46, y + 32, 18)
                fs(c, hexc(["#E8A23B", "#5E9A6E", "#9C5BA8", "#D9534F"][k], a), None, 0)
                for s in range(5):
                    P.star(c, 82 + s * 30, y + 32, 12, hexc("#FFC857", a))
                lines = ["Best purchase ever!!", "Works great. 10/10", "WOW. Just wow.",
                         "Turned my dog into a"][k]
                text(c, lines, 30, y + 78, 17, hexc("#30323A", a), align="left")
                if k == 3:
                    text(c, "refrigerator.", 30, y + 100, 17, hexc("#30323A", a), align="left")
                    # fridge with a wagging tail
                    fx, fy = w - 62, y + 64
                    rrect(c, fx - 22, fy - 40, 44, 74, 6)
                    fs(c, hexc("#EEF2F6", a), OUTLINE, 3)
                    line(c, [(fx - 22, fy - 12), (fx + 22, fy - 12)], OUTLINE, 2.5)
                    line(c, [(fx + 14, fy - 32), (fx + 14, fy - 20)], OUTLINE, 3)
                    wag = math.sin(t * 16) * 0.6
                    c.save()
                    c.translate(fx + 22, fy + 10)
                    c.rotate(-0.6 + wag)
                    line(c, [(0, 0), (20, -6), (28, -18)], hexc("#B07A45", a), 5)
                    c.restore()
                c.restore()

        big_phone(cx, W / 2, H / 2 + 40, 1.45, screen, t)
        big_arm(cx, W / 2 + 130, H + 200, W / 2 + 150, H / 2 + 380)


class S2Shrug(Shot):
    scene = "s2"
    music = "room"
    amb = "room"

    def plan(self, P):
        P.wait(0.15)
        P.say("s2_05", gap=0.35)

    def draw(self, cx, t):
        cam = Cam(960, 640, 1.7)
        S.room(cx, cam, t)
        world(cx, cam)
        sh = win(t, 0.3, 0.8) - win(t, 1.6, 2.0)
        p = breathe(hero_pose(960, GROUND + 20, t, view="front", eyes="happy" if sh > 0.3 else "open",
                               mouth="grin" if sh > 0.3 else "smile", brows="up"), t)
        p = p.but(arm_a=lerp(10, 70, sh), arm_b=lerp(10, 70, sh), elb_a=lerp(8, -110, sh),
                  elb_b=lerp(8, -110, sh), head_dy=8 * sh, tilt=6 * sh)
        fig(cx, self, cam, HERO, p, "hero")
        end(cx)


class S2Button(Shot):
    scene = "s2"
    music = "room"
    amb = "room"

    def plan(self, P):
        a = P.say("s2_06", gap=0.0)
        d = P.voice.dur("s2_06")
        tp = a + d * 0.86
        P.mark("press", tp)
        P.sfx("click", t=tp, vol=0.8)
        P.sfx("zap", t=tp + 0.05, vol=0.9)
        P.wait(0.55)

    def draw(self, cx, t):
        insert_bg(cx, "#F1D9B5", "#E2C49A")
        tp = self.mt("press")
        push = ease_in(prog(t, tp - 0.5, tp))
        P.watch(cx, W / 2 - 60, H / 2 + 20, 4.0, -0.08, display="12:00", lcd_glow=0.2 + 0.8 * prog(t, tp, tp + 0.2),
                button=push)
        # wrist under the watch
        line(cx, [(-100, H / 2 + 250), (W / 2 - 60, H / 2 + 20)], OUTLINE, 0)
        # finger approaching the red button
        fx = lerp(W + 120, W / 2 + 230, ease_out(prog(t, 0.0, tp - 0.4))) - 22 * push
        fy = H / 2 + 10
        big_arm(cx, W + 300, fy + 260, fx, fy, w=30)
        if t > tp:
            flash(cx, ease_in(prog(t, tp, tp + 0.35)))


class S2Vanish(Shot):
    scene = "s2"
    trans_in = ("flash", 0.5)
    music = "room"
    amb = "room"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s2_07", gap=0.1)
        tp = a + P.voice.dur("s2_07") - 0.1
        P.mark("poof", tp)
        P.sfx("poof", t=tp, vol=0.8)
        P.sfx("sparkle", t=tp, vol=0.5)
        P.wait(0.35)

    def draw(self, cx, t):
        cam = Cam(900, 600, 1.2)
        S.room(cx, cam, t)
        world(cx, cam)
        tp = self.mt("poof")
        P.product_box(cx, 620, GROUND + 14, 1.0, open_=1.0)
        if t < tp:
            glow = prog(t, 0, tp)
            p = hero_pose(980, GROUND + 20, t, view="front", eyes="wide", mouth="o", brows="up",
                          arm_a=20, arm_b=20, blink=False)
            p = p.but(bob=-10 * glow * abs(math.sin(t * 30)))
            fig(cx, self, cam, HERO, p, "hero")
            P.sparkles(cx, 980, GROUND - 160, t, 160, 8, glow)
        else:
            k = prog(t, tp, tp + 0.5)
            circle(cx, 980, GROUND - 150, 60 + 160 * k)
            fs(cx, (1, 1, 1, 0.9 * (1 - k)), None, 0)
            P.sparkles(cx, 980, GROUND - 160, t, 200, 10, 1 - k)
        end(cx)


class S2Arrive(Shot):
    scene = "s2"
    trans_in = None
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.25)
        P.mark("land", 0.9)
        P.sfx("whoosh", t=0.25, vol=0.6)
        P.sfx("thud", t=0.9, vol=0.9)
        P.sfx("gasp", t=1.0, vol=0.5)
        a = P.say("s2_08", lead=0.4, gap=0.6)

    def draw(self, cx, t):
        tl = self.mt("land")
        sx, sy = shake(t, 10 * (1 - prog(t, tl, tl + 0.4)) * (t > tl), 25)
        cam = Cam(980 + sx, 660 + sy, 1.3)
        S.market(cx, cam, t)
        world(cx, cam)
        S.crowd(cx, t, -60, 700, GY - 10, 5, seed=3, s=0.82, mood="gasp", mood_t=t - tl, view="side")
        S.crowd(cx, t, 1250, 1980, GY - 10, 4, seed=4, s=0.82, mood="gasp", mood_t=t - tl, view="side")
        P.portal(cx, 980, 120, 120 * (1 - prog(t, 0.2, 1.0)), t, 1 - prog(t, 0.6, 1.0))
        if t < tl:
            k = ease_in(prog(t, 0.2, tl))
            y = lerp(-200, GY - 60, k)
            p = hero_pose(980, y, t, eyes="wide", mouth="scream", brows="worried",
                          arm_a=160, arm_b=150, elb_a=20, elb_b=30, hip_a=-30, hip_b=40, knee_a=60, knee_b=20)
            cx.save()
            cx.translate(980, y - 150)
            cx.rotate(math.pi * 0.9 * k)
            cx.translate(-980, -(y - 150))
            fig(cx, self, cam, HERO, p, "hero")
            cx.restore()
        else:
            # face-plant: upside-down, legs in the air, wobbling
            wob = math.sin((t - tl) * 14) * 8 * math.exp(-(t - tl) * 3)
            cx.save()
            cx.translate(980, GY - 10)
            cx.rotate(math.pi + wob * 0.01)
            p = hero_pose(0, 0, t, eyes="spiral", mouth="wavy", brows="worried",
                          arm_a=60, arm_b=-30, elb_a=40, elb_b=40, hip_a=20 + wob, hip_b=-15, knee_a=30, knee_b=50,
                          blink=False)
            J = HERO.draw(cx, p)
            cx.restore()
            P.motion_puffs(cx, 980, GY, t - tl, 4, 1 - prog(t, tl, tl + 1.0))
            P.dizzy_stars(cx, 980, GY - 10, t, 70, 1 - prog(t, tl + 1.6, tl + 2.2))
            self.heads["hero"] = cam.to_screen(980, GY - 50) + (50,)
        end(cx)


class S2NoWifi(Shot):
    scene = "s2"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.3)
        a = P.say("s2_09", gap=0.4)
        P.accent("NO WI-FI.", t=a + 0.05, dur=P.voice.dur("s2_09") + 0.25, size=100, pos=(W / 2, 190))
        b = P.say("s2_10", gap=0.4)
        P.accent("NO [MONEY.]", t=b + 0.05, dur=P.voice.dur("s2_10") + 0.35, size=100, pos=(W / 2, 190))
        P.sfx("flap", t=b + 0.4, vol=0.4)
        c = P.say("s2_11", gap=0.55)

    def draw(self, cx, t):
        b = self.mt("s2_10")
        c = self.mt("s2_11")
        cam = cam_kf(t, [(0, (960, 690, 1.75)), (c, (960, 690, 1.75)), (c + 0.6, (960, 620, 1.3))])
        S.market(cx, cam, t)
        world(cx, cam)
        if t >= c:
            S.crowd(cx, t, 300, 640, GY - 20, 2, seed=8, s=0.84, mood="confused", mood_t=t - c, view="side")
            S.crowd(cx, t, 1300, 1640, GY - 20, 2, seed=9, s=0.84, mood="stare", mood_t=t - c, view="side")
        if t < b:
            # phone held high searching for signal
            sway = math.sin(t * 5) * 25
            p = hero_pose(960, GY, t, eyes="open", mouth="wavy", brows="worried", look=(0.4, -1),
                          arm_b=165 + sway * 0.3, elb_b=5, arm_a=20, f=1)
            J = fig(cx, self, cam, HERO, p, "hero")
            P.phone(cx, J["hand_b"][0], J["hand_b"][1] - 30, 1.2, 0.1, screen="on")
            wifi_icon(cx, J["hand_b"][0] + 110, J["hand_b"][1] + 10, 0.6)
        elif t < c:
            # pockets out, a moth flies away
            k = win(t, b, b + 0.3)
            p = hero_pose(960, GY, t, view="front", eyes="open", mouth="flat", brows="worried",
                          look=(0, 0.6), arm_a=lerp(10, 35, k), arm_b=lerp(10, 35, k), elb_a=-30, elb_b=-30)
            J = fig(cx, self, cam, HERO, p, "hero")
            for side in (-1, 1):
                ellipse(cx, 960 + side * 26, GY - 140, 14 * k, 18 * k)
                fs(cx, hexc("#F2F2F2"), OUTLINE, 3)
            mt = t - b - 0.35
            if mt > 0:
                moth(cx, 960 + mt * 90 + math.sin(mt * 8) * 20, GY - 150 - mt * 160, t)
        else:
            look = pick(t - c, [(0, (-1, 0)), (0.7, (1, 0)), (1.4, (0, -0.3))])
            p = breathe(hero_pose(960, GY, t, view="front", eyes="open", mouth="o", mouth_open=0.6,
                                  brows="worried", look=look, tilt=8 * math.sin((t - c) * 3)), t)
            fig(cx, self, cam, HERO, p, "hero")
            P.exclaim(cx, 1010, GY - 400, 0.9, win(t, c + 0.3, c + 0.5), mark="?")
        end(cx)


class S2Battery(Shot):
    scene = "s2"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s2_12", gap=0.45)
        d = P.voice.dur("s2_12")
        sw = a + d * 0.47
        P.mark("swap", sw)
        P.accent("[3%] BATTERY", t=a + 0.5, dur=sw - a - 0.6, size=96, pos=(W / 2, 170))
        P.accent("RECHARGING: [7 DAYS]", t=sw + 0.25, dur=a + d - sw + 0.4, size=88, pos=(W / 2, 170))
        P.sfx("beep2", t=a + 0.5, vol=0.4)
        P.sfx("beep", t=sw + 0.2, vol=0.4)

    def draw(self, cx, t):
        sw = self.mt("swap")
        insert_bg(cx, "#CFE6F5", "#9CC6E4")
        if t < sw:
            blink = 0.35 + 0.65 * (math.sin(t * 9) > 0)

            def screen(c, w, h):
                c.rectangle(0, 0, w, h)
                src(c, hexc("#1E2433"))
                c.fill()
                battery_icon(c, w / 2 - 6, h / 2 - 40, 2.0, 3, blink)
                text(c, "3%", w / 2, h / 2 + 110, 72, hexc("#E04848", blink))

            big_phone(cx, W / 2, H / 2 + 90, 1.12, screen, t)
            big_arm(cx, W / 2 - 150, H + 200, W / 2 - 160, H / 2 + 400)
        else:
            k = ease_out(prog(t, sw, sw + 0.3))
            P.watch(cx, W / 2, H / 2 + 120, 3.3 + 0.2 * k, 0.0, display="7 DAYS", lcd_glow=0.4)


class S2SevenDays(Shot):
    scene = "s2"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.25)
        P.say("s2_13", gap=0.7)
        P.sfx("crickets", t=0.4, vol=0.25)
        a = P.say("s2_14", gap=0.5)
        for k in range(3):
            P.sfx("swish", t=a + 0.3 + k * 0.55, vol=0.35)

    def draw(self, cx, t):
        a = self.mt("s2_14")
        cam = Cam(960, GY - 250, 2.6)
        S.market(cx, cam, t)
        world(cx, cam)
        if t < a:
            p = hero_pose(960, GY, t, view="front", eyes="tiny", mouth="flat", brows="flat", blink=False)
            fig(cx, self, cam, HERO, p, "hero")
        else:
            ph = (t - a) * 1.8
            up = max(0, math.sin(ph * math.pi))
            p = hero_pose(960, GY, t, view="front", eyes="wide" if up > 0.5 else "open", mouth="teeth",
                          brows="worried", look=(0.6, -0.2) if up > 0.5 else (0, 0.4), sweat=1.0,
                          arm_b=lerp(10, 115, up), elb_b=lerp(10, 70, up), tilt=4 * math.sin(t * 40))
            J = fig(cx, self, cam, HERO, p, "hero")
            if up > 0.2:
                P.phone(cx, J["hand_b"][0], J["hand_b"][1] - 20, 1.0, -0.2, screen="battery", battery=3)
        end(cx)


class S2Shadow(Shot):
    scene = "s2"
    music = "suspense"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.sfx("dun", t=0.4, vol=0.6)
        P.say("s2_15", gap=0.6)
        P.sfx("step_heavy", t=0.5, vol=0.6)
        P.sfx("step_heavy", t=1.1, vol=0.6)

    def draw(self, cx, t):
        cam = Cam(960, 640, 1.5)
        S.market(cx, cam, t)
        world(cx, cam)
        k = ease_io(prog(t, 0.2, 1.6))
        turn = win(t, 1.2, 1.8)
        p = hero_pose(900, GY, t, f=1 if turn < 0.5 else -1, eyes="wide" if turn > 0.5 else "open",
                      mouth="wavy" if turn > 0.5 else "flat", brows="worried", look=(1, -0.6) if turn > 0.5 else (0, 0),
                      sweat=turn, arm_b=-8, arm_a=10)
        if turn > 0.5:
            p = p.but(f=1)
        fig(cx, self, cam, HERO, p, "hero")
        # Maximus steps into frame; his shadow falls across the hero
        mx = lerp(1700, 1290, k)
        mp = max_pose(mx, GY, t, f=-1, eyes="open", brows="angry", mouth="frown")
        mp = walk(mp, t, 0.9, 0.6) if k < 1 else mp
        fig(cx, self, cam, MAXIMUS, mp, "max")
        end(cx)
        g = cairo.LinearGradient(W * (1.1 - 0.6 * k), 0, W * (0.3 - 0.3 * k), 0)
        g.add_color_stop_rgba(0, 0.05, 0.05, 0.12, 0.45 * k)
        g.add_color_stop_rgba(1, 0.05, 0.05, 0.12, 0.0)
        cx.set_source(g)
        cx.paint()


class S2Flashlight(Shot):
    scene = "s2"
    music = "suspense"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s2_16", gap=0.3)
        d = P.voice.dur("s2_16")
        P.mark("light", a + d * 0.75)
        P.sfx("flashlight", t=a + d * 0.75, vol=0.7)
        P.sfx("ooh", t=a + d * 0.75 + 0.2, vol=0.35)
        b = P.dlg("d_max_wizard", "max", "A [WIZARD!]", gap=0.35)
        P.sfx("gasp", t=b + 0.1, vol=0.6)
        c = P.say("s2_17", gap=0.6)
        P.mark("bow", c + 0.6)

    def draw(self, cx, t):
        tl = self.mt("light")
        b = self.mt("d_max_wizard")
        bow = self.mt("bow")
        cam = cam_kf(t, [(0, (1100, 640, 1.25)), (b, (1100, 640, 1.25)), (b + 0.3, (1150, 600, 1.15))])
        S.market(cx, cam, t)
        world(cx, cam)
        S.crowd(cx, t, 1500, 2300, GY - 30, 4, seed=12, s=0.82, mood="gasp" if t < bow else "cheer",
                mood_t=t - b, view="side", look=(-1, 0))
        on = t >= tl
        # Maximus
        back = ease_out(prog(t, tl, tl + 0.5))
        mp = breathe(max_pose(1380 + 60 * back, GY, t, f=-1, eyes="wide" if on else "open", brows="up" if on else "angry",
                              mouth="o" if on else "frown", mouth_open=1.3, lean=-10 * back, blink=not on), t)
        if t >= b:
            mp = talk(mp.but(mouth="yell", arm_b=100, elb_b=-10), t) if t < b + self.m["d_max_wizard"][1] - b else \
                mp.but(arm_b=100, elb_b=-10, mouth="grin", eyes="happy")
        fig(cx, self, cam, MAXIMUS, mp, "max")
        # hero with phone
        raise_ = win(t, 0.4, 1.4)
        hp = hero_pose(980, GY, t, f=1, eyes="wide", mouth="wavy", brows="worried", sweat=1.0,
                       arm_b=lerp(-8, 80, raise_), elb_b=lerp(10, 20, raise_), look=(1, -0.5))
        if on:
            hp = hp.but(eyes="open", look=(1, -0.3))
        J = fig(cx, self, cam, HERO, hp, "hero")
        P.phone(cx, J["hand_b"][0] + 10, J["hand_b"][1] - 10, 1.1, 1.3, screen="on", glow=1.0 if on else 0)
        if on:
            P.flash_beam(cx, J["hand_b"][0] + 30, J["hand_b"][1] - 12, -0.38, 650, 0.22,
                         0.9 * (1 - 0.3 * prog(t, b + 2, b + 4)))
        end(cx)


class S2Problem(Shot):
    scene = "s2"
    music = "suspense"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.say("s2_18", gap=1.0)

    def draw(self, cx, t):
        cam = Cam(960, GY - 250, 2.7)
        S.market(cx, cam, t)
        tint(cx, (0.05, 0.05, 0.15), 0.35)
        world(cx, cam)
        p = hero_pose(960, GY, t, view="front", eyes="open", mouth="teeth", brows="worried", look=(1, 0),
                      sweat=1.0, arm_b=60, elb_b=40)
        J = fig(cx, self, cam, HERO, p, "hero")
        P.phone(cx, J["hand_b"][0], J["hand_b"][1] - 10, 1.0, 0.0, screen="on", glow=1)
        # under-lighting on the face
        g = cairo.RadialGradient(960, GY - 300, 10, 960, GY - 300, 120)
        g.add_color_stop_rgba(0, 1, 1, 0.85, 0.35)
        g.add_color_stop_rgba(1, 1, 1, 0.85, 0)
        cx.set_source(g)
        circle(cx, 960, GY - 300, 120)
        cx.fill()
        end(cx)
        vignette(cx, 0.5)


def scenes():
    cold = S1ColdOpen()
    return [cold, S1Rewind(cold), S2Room(), S2Reviews(), S2Shrug(), S2Button(), S2Vanish(), S2Arrive(),
            S2NoWifi(), S2Battery(), S2SevenDays(), S2Shadow(), S2Flashlight(), S2Problem()]

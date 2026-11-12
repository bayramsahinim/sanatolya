"""Scene 5 (Day 4: fake wizard), Scene 6 (Day 5: predictions), Scene 7 (Day 6: rain + plan)."""
from .common import *  # noqa

WEATHER_MAN = 77       # same Roman in Day 5 and Day 6
RICH_MAN = 78


def ring_crowd(cx, t, n_visible, mood="idle", mood_t=0.0, look=(0, 0)):
    """Semicircle crowd in the square; n_visible grows as people gather."""
    figs = S.crowd_figs(21, 16)
    for i, f in enumerate(figs):
        if i >= n_visible:
            break
        row = i % 2
        k = i // 2
        side = 1 if k % 2 else -1
        x = 960 + side * (380 + (k // 2) * 150) + (60 if row else 0) * side
        y = GY - 40 - row * 30
        if row == 1:
            y -= 10
        pp = Pose(x=x, y=y, s=0.8 - row * 0.05, f=-side, t=t + i, blink_seed=i + 50, mouth="smile",
                  look=(-side * 0.6, 0), arm_a=8, arm_b=8)
        pp = breathe(pp, t + i)
        jit = (i * 0.37) % 0.3
        m = mood if mood_t > jit else "idle"
        if m == "stare":
            pp = pp.but(eyes="open", mouth="flat", brows="neutral", look=look)
        elif m == "gasp":
            pp = pp.but(eyes="wide", mouth="o", brows="up", arm_a=40, arm_b=40, elb_a=100, elb_b=100)
        elif m == "cheer":
            ph = t * 3 + i
            pp = pp.but(eyes="happy", mouth="grin", arm_a=150 + 20 * math.sin(ph), arm_b=150 - 20 * math.sin(ph),
                        elb_a=15, elb_b=15, bob=-abs(math.sin(ph)) * 16)
        f.draw(cx, pp)


# =============================================================== SCENE 5
class S5Gather(Shot):
    scene = "s5"
    trans_in = ("dip", 0.5)
    music = "quirky"
    amb = "crowd"
    amb_gain = 0.7

    def plan(self, P):
        P.accent("DAY 4", t=0.4, dur=1.7, size=120)
        P.wait(1.6)
        P.dlg("d_max_show", "max", "Show them your [power!]", gap=0.35)
        P.say("s5_01", gap=0.3)
        a = P.say("s5_02", gap=0.25)
        P.sfx("pop", t=a + 0.2, vol=0.3)
        b = P.say("s5_03", gap=0.5)
        P.sfx("murmur", t=b, vol=0.5)

    def draw(self, cx, t):
        a = self.mt("s5_02")
        b = self.mt("s5_03")
        cam = cam_kf(t, [(0, (900, 640, 1.35)), (a, (960, 640, 1.35)), (b + 1.0, (960, 620, 1.1))])
        S.square(cx, cam, t, festival=False)
        world(cx, cam)
        n = int(2 + 6 * prog(t, 0.5, a) + 8 * prog(t, a, b + 0.8))
        ring_crowd(cx, t, n)
        drag = ease_io(prog(t, 0.0, 1.6))
        mx = lerp(500, 1150, drag)
        talking = self.mt("d_max_show") <= t <= self.mt("d_max_show", 1)
        mp = max_pose(mx, GY, t, f=1, mouth="grin", brows="up", eyes="open", arm_a=-40, elb_a=-60)
        if drag < 1:
            mp = walk(mp, t, 0.9, 0.7)
            mp = mp.but(arm_a=-40, elb_a=-60)
        if talking:
            mp = talk(mp.but(mouth="yell", arm_b=140, elb_b=10, f=-1), t)
        if t > self.mt("d_max_show", 1):
            mp = mp.but(f=-1, arm_b=90, elb_b=0)
        MJ = fig(cx, self, cam, MAXIMUS, breathe(mp, t), "max")
        hx = mx - 190 if drag < 1 else 960
        hp = hero_pose(hx, GY, t, f=1, eyes="wide", mouth="wavy", brows="worried", sweat=1.0,
                       lean=-25 * (1 - drag), hip_a=20, hip_b=30, knee_a=0, knee_b=0, arm_a=130, elb_a=30)
        if drag >= 1:
            hx = lerp(hx, 960, 1)
            hp = breathe(hero_pose(960, GY, t, view="front", eyes="wide", mouth="teeth", brows="worried", sweat=1,
                                   look=(-1 if math.sin(t * 2) > 0 else 1, 0)), t)
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)


class S5Pressure(Shot):
    scene = "s5"
    music = "quirky"
    amb = "crowd"
    amb_gain = 0.6

    def plan(self, P):
        P.wait(0.2)
        P.say("s5_04", gap=0.45)
        a = P.say("s5_05", gap=0.6)
        P.sfx("heartbeat", t=a, vol=0.6)
        P.sfx("heartbeat", t=a + 0.8, vol=0.6)

    def draw(self, cx, t):
        a = self.mt("s5_05")
        lie = t >= a
        cam = Cam(960, 700 if not lie else GY - 150, 1.9 if not lie else 1.6)
        S.square(cx, cam, t, festival=False)
        world(cx, cam)
        if not lie:
            hp = breathe(hero_pose(960, GY, t, view="front", eyes="half", mouth="smirk", brows="up",
                                   arm_a=40, arm_b=40, elb_a=-110, elb_b=-110), t)
        else:
            k = math.sin(t * 40)
            hp = hero_pose(960 + k * 2, GY, t, view="front", eyes="wide", mouth="teeth", brows="worried", sweat=1.0,
                           hip_a=-6 + 6 * k, hip_b=-6 - 6 * k, knee_a=-14, knee_b=-14, arm_a=30, arm_b=30, elb_a=60,
                           elb_b=60, tilt=2 * k)
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)


class S5Dead(Shot):
    scene = "s5"
    music = "suspense"
    amb = "crowd"
    amb_gain = 0.4

    def plan(self, P):
        P.wait(0.2)
        P.say("s5_06", gap=0.3)
        P.sfx("beep", t=0.4, vol=0.3)
        a = P.say("s5_07", gap=0.35)
        P.mark("watch", a - 0.1)
        b = P.say("s5_08", gap=0.3)
        P.mark("stare", b - 0.1)
        P.sfx("crickets", t=b + 0.3, vol=0.3)
        P.wait(1.1)

    def draw(self, cx, t):
        w = self.mt("watch")
        s = self.mt("stare")
        if t < w:
            insert_bg(cx, "#D9CBB0", "#B5A381")
            bl = 0.3 + 0.7 * (math.sin(t * 10) > 0)

            def screen(c, ww, hh):
                c.rectangle(0, 0, ww, hh)
                src(c, hexc("#14161E"))
                c.fill()
                battery_icon(c, ww / 2 - 6, hh / 2 - 30, 2.0, 0, bl)
                text(c, "0%", ww / 2, hh / 2 + 110, 72, hexc("#E04848", bl))

            big_phone(cx, W / 2, H / 2 + 60, 1.1, screen, t)
            big_arm(cx, W / 2 - 150, H + 200, W / 2 - 160, H / 2 + 370)
        elif t < s:
            insert_bg(cx, "#D9CBB0", "#B5A381")
            P.watch(cx, W / 2, H / 2 + 20, 3.4, 0.0, display="3 DAYS", lcd_glow=0.3)
        else:
            k = prog(t, s, s + 3.0)
            cam = Cam(lerp(500, 1420, ease_io(k)), 560, 1.6)
            S.square(cx, cam, t, festival=False)
            world(cx, cam)
            ring_crowd(cx, t, 16, mood="stare", mood_t=5, look=(0, 0))
            fig(cx, self, cam, HERO, hero_pose(960, GY, t, view="front", eyes="wide", mouth="teeth", brows="worried",
                                              sweat=1, look=(1 if k > 0.5 else -1, 0)), "hero")
            end(cx)


class S5Tray(Shot):
    scene = "s5"
    music = "quirky"
    amb = "crowd"
    amb_gain = 0.6

    def plan(self, P):
        P.wait(0.2)
        P.mark("grab", 0.9)
        P.sfx("swish", t=0.6, vol=0.5)
        P.sfx("clank", t=0.95, vol=0.4)
        P.wait(0.9)
        a = P.say("s5_09", gap=0.2)
        d = P.voice.dur("s5_09")
        P.mark("beam", a + d * 0.55)
        P.sfx("sparkle", t=a + d * 0.55, vol=0.6)
        P.mark("jump", a + d * 0.8)
        P.sfx("boing", t=a + d * 0.8, vol=0.5)
        P.sfx("gasp", t=a + d * 0.85, vol=0.4)
        P.say("s5_10", gap=0.3)
        P.say("s5_11", gap=0.35)
        P.say("s5_12", gap=0.4)

    def draw(self, cx, t):
        g = self.mt("grab")
        bm = self.mt("beam")
        jp = self.mt("jump")
        cam = Cam(1080, 610, 1.3)
        S.square(cx, cam, t, festival=False)
        world(cx, cam)
        ring_crowd(cx, t, 16, mood="gasp" if t > jp else "stare", mood_t=t - jp, look=(0.5, 0))
        # Maximus
        back = ease_out(prog(t, jp, jp + 0.35))
        mp = breathe(max_pose(1330 + 120 * back, GY - 20 * math.sin(math.pi * back), t, f=-1,
                              eyes="squeeze" if bm < t < jp + 1.2 else "angry", brows="angry" if t < bm else "worried",
                              mouth="frown" if t < bm else "o", lean=-14 * back, arm_a=90 * back, arm_b=120 * back,
                              elb_a=60, elb_b=60), t)
        MJ = fig(cx, self, cam, MAXIMUS, mp, "max")
        # hero: grab tray, tilt it toward the sun
        if t < g:
            k = prog(t, 0.0, g)
            hp = hero_pose(lerp(960, 760, k), GY, t, f=-1, eyes="wide", mouth="o", brows="worried",
                           look=(-1, 0), lean=20)
            hp = run(hp, t, 2.0, 0.6)
            J = fig(cx, self, cam, HERO, hp, "hero")
            P.tray(cx, 640, GROUND - 100, 0.8, tilt=0.25)
            S.counter(cx, 640, 220, GROUND - 90)
        else:
            k = win(t, g, g + 0.6)
            proud = t > self.mt("s5_10")
            hp = breathe(hero_pose(lerp(760, 960, k), GY, t, f=1, eyes="half" if proud else "open",
                                   mouth="smirk" if proud else "teeth", brows="up" if proud else "worried",
                                   look=(1, -0.6), arm_b=120, elb_b=-10, arm_a=100, elb_a=10), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            S.counter(cx, 640, 220, GROUND - 90)
            tx, ty = J["hand_b"][0] + 20, J["hand_b"][1] - 30
            P.tray(cx, tx, ty, 0.9, rot=-0.5, shine=win(t, bm - 0.2, bm), tilt=0.85)
            if t > bm:
                a = 1 - prog(t, bm + 2.2, bm + 2.8)
                P.sun_ray(cx, tx - 400, 0, tx, ty, 0.6 * a, 34)
                P.sun_ray(cx, tx, ty, MJ["head"][0] - 10, MJ["head"][1] - 20, 0.9 * a, 30)
        end(cx)


class S5Pigeon(Shot):
    scene = "s5"
    music = None
    amb = "crowd"
    amb_gain = 0.3

    def plan(self, P):
        P.wait(0.3)
        a = P.say("s5_13", gap=0.3)
        P.mark("land", a + P.voice.dur("s5_13") * 0.85)
        P.sfx("flap", t=a + 0.2, vol=0.6)
        P.sfx("coo", t=a + P.voice.dur("s5_13") + 0.3, vol=0.6)
        P.sfx("gasp", t=a + P.voice.dur("s5_13") + 0.5, vol=0.6)
        P.wait(2.2)
        b = P.say("s5_14", gap=0.5)
        P.mark("cheer", b + P.voice.dur("s5_14") * 0.7)
        P.sfx("cheer", t=b + P.voice.dur("s5_14") * 0.65, vol=0.8)

    def draw(self, cx, t):
        ld = self.mt("land")
        ch = self.mt("cheer")
        cam = cam_kf(t, [(0, (1250, 520, 2.0)), (ld + 1.2, (1250, 520, 2.0)), (ch - 0.3, (1100, 610, 1.2))])
        S.square(cx, cam, t, festival=False)
        world(cx, cam)
        ring_crowd(cx, t, 16, mood="cheer" if t > ch else ("gasp" if t > ld + 0.3 else "stare"),
                   mood_t=t - (ch if t > ch else ld), look=(0.5, -0.5))
        mp = breathe(max_pose(1300, GY, t, f=-1, eyes="wide" if t > ld else "angry", brows="up" if t > ld else "angry",
                              mouth="o" if t > ld else "frown", look=(0, -1) if t > ld else (-1, 0), blink=t < ld,
                              arm_a=10, arm_b=10), t)
        if t > ch:
            mp = mp.but(look=(-0.6, 0), eyes="open", mouth="flat", brows="skeptic")
        MJ = fig(cx, self, cam, MAXIMUS, mp, "max")
        top = (MJ["head"][0] - 10, MJ["head"][1] - 125)
        if t < ld:
            k = ease_out(prog(t, 0, ld))
            px, py = lerp(top[0] + 600, top[0], k), lerp(top[1] - 400, top[1], k)
            P.pigeon(cx, px, py, 1.1, -1, t, flap=1.0)
        else:
            P.pigeon(cx, top[0], top[1], 1.1, -1, t, flap=max(0, 1 - (t - ld) * 4), coo=1)
        hp = breathe(hero_pose(960, GY, t, f=1, eyes="wide" if t < ch else "open", mouth="o" if t < ch else "teeth",
                               brows="up" if t < ch else "worried", look=(1, -0.6), arm_b=70, elb_b=30, arm_a=60, elb_a=40), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        P.tray(cx, J["hand_b"][0] + 10, J["hand_b"][1] - 20, 0.8, rot=-0.3, tilt=0.6)
        end(cx)


class S5Kneel(Shot):
    scene = "s5"
    music = "festival"
    music_gain = 0.7
    amb = "crowd"
    amb_gain = 0.7

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s5_15", gap=0.3)
        P.sfx("thud", t=a + 0.5, vol=0.5)
        P.sfx("clank", t=a + 0.5, vol=0.5)
        b = P.say("s5_16", gap=0.3)
        P.mark("point", b + 0.4)
        P.say("s5_17", gap=0.4)
        c = P.say("s5_18", gap=0.8)
        P.accent("ROME'S LEAST QUALIFIED\n[MAGICIAN]", t=c + 0.3, dur=P.voice.dur("s5_18") + 0.6, size=72,
                 pos=(W / 2, 170))
        P.sfx("cheer", t=c + 0.2, vol=0.5)

    def draw(self, cx, t):
        a = self.mt("s5_15")
        pt = self.mt("point")
        c = self.mt("s5_18")
        pan = win(t, pt, pt + 0.8) * (1 - win(t, c - 0.6, c))
        cam = Cam(lerp(1100, 2100, pan), 620, 1.2)
        S.square(cx, cam, t, festival=pan > 0.3 or t > pt)
        world(cx, cam)
        if pan > 0.05:
            S.stage(cx, 2400, GROUND - 150, 600)
        ring_crowd(cx, t, 16, mood="cheer", mood_t=1 if t > c else 0)
        kn = win(t, a + 0.2, a + 0.6)
        pointing = t > pt
        mp = breathe(max_pose(1300, GY, t, f=1 if pointing else -1, eyes="open" if pointing else "closed",
                              mouth="grin", brows="up", lean=20 * kn,
                              hip_a=lerp(-4, 85, kn), knee_a=lerp(4, 125, kn),
                              hip_b=lerp(4, -5, kn), knee_b=lerp(4, 95, kn), bob=lerp(0, 55, kn),
                              arm_b=125 if pointing else lerp(10, 70, kn), elb_b=0, arm_a=lerp(10, 40, kn)), t)
        MJ = fig(cx, self, cam, MAXIMUS, mp, "max")
        P.pigeon(cx, MJ["head"][0] - 10, MJ["head"][1] - 125, 1.1, -1, t)
        wave = t > c
        hp = breathe(hero_pose(960, GY, t, view="front", eyes="open", mouth="teeth" if not wave else "grin",
                               brows="worried", sweat=1 if not wave else 0.5,
                               arm_b=150 + 20 * math.sin(t * 8) if wave else 60, elb_b=10, arm_a=50, elb_a=40), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        P.tray(cx, J["hand_a"][0], J["hand_a"][1] - 20, 0.8, rot=0.3, tilt=0.6)
        end(cx)


# =============================================================== SCENE 6
TABLE_X = 960


def prediction_set(cx, t, cam, sh, hero_kw, customers=(), sky_dark=0.0):
    S.market(cx, cam, t, stalls=False)
    if sky_dark:
        tint(cx, (0.1, 0.12, 0.2), 0.35 * sky_dark)
    world(cx, cam)
    hp = breathe(hero_pose(TABLE_X, GY - 30, t, **hero_kw), t)
    J = fig(cx, sh, cam, HERO, hp, "hero")
    P.table(cx, TABLE_X, GY + 10, 380, 120, cloth="#6B3FA0")
    # "crystal ball": an upside-down fish bowl with an orange in it
    circle(cx, TABLE_X - 110, GY - 150, 36)
    fs(cx, (0.8, 0.92, 1, 0.6), OUTLINE, 4)
    circle(cx, TABLE_X - 110, GY - 145, 15)
    fs(cx, hexc("#F09A2B"), OUTLINE, 3)
    P.sign(cx, TABLE_X, GY - 470, "FUTURE PREDICTIONS", 460, 80, 0.03, 32)
    line(cx, [(TABLE_X - 200, GY - 430), (TABLE_X - 200, GY - 110)], hexc("#8A5A2E"), 8)
    line(cx, [(TABLE_X + 200, GY - 430), (TABLE_X + 200, GY - 110)], hexc("#8A5A2E"), 8)
    for f, p in customers:
        f.draw(cx, p)
    return J


class S6Table(Shot):
    scene = "s6"
    trans_in = ("dip", 0.5)
    music = "quirky"
    amb = "market"

    def plan(self, P):
        P.accent("DAY 5", t=0.4, dur=1.7, size=120)
        P.wait(0.9)
        P.say("s6_01", gap=0.3)
        P.say("s6_02", gap=0.3)
        P.say("s6_03", gap=0.4)
        a = P.say("s6_04", gap=0.6)
        P.sfx("crickets", t=a + 0.3, vol=0.25)

    def draw(self, cx, t):
        a = self.mt("s6_03")
        b = self.mt("s6_04")
        cam = cam_kf(t, [(0, (1100, 620, 1.2)), (a, (1100, 620, 1.2)), (b, (TABLE_X, GY - 260, 2.4))])
        cust = []
        for i in range(4):
            p = breathe(Pose(x=1350 + i * 150, y=GY, s=0.85, f=-1, t=t, blink_seed=i + 70, look=(-1, 0),
                             mouth="smile"), t + i)
            cust.append((roman(RICH_MAN + i if i else RICH_MAN), p))
        if t < a:
            kw = dict(f=1, eyes="open", mouth="grin", brows="up", look=(1, 0))
        elif t < b:
            kw = dict(view="front", eyes="half", mouth="smirk", brows="up", arm_a=60, arm_b=60, elb_a=-120, elb_b=-120)
        else:
            kw = dict(view="front", eyes="tiny", mouth="flat", brows="flat", blink=False)
        prediction_set(cx, t, cam, self, kw, cust)
        if t > b:
            ft = t - b
            moth(cx, TABLE_X + 140 * math.cos(ft * 2), GY - 330 + 40 * math.sin(ft * 3), t, 0.9)
        end(cx)


class S6Rich(Shot):
    scene = "s6"
    music = "quirky"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.say("s6_05", gap=0.3)
        a = P.say("s6_06", gap=0.4)
        P.mark("run", a + P.voice.dur("s6_06") + 0.1)
        P.sfx("sparkle", t=a + 0.8, vol=0.4)
        P.sfx("whoosh", t=a + P.voice.dur("s6_06") + 0.1, vol=0.5)
        P.wait(0.5)

    def draw(self, cx, t):
        a = self.mt("s6_06")
        rn = self.mt("run")
        cam = Cam(1080, 640, 1.6)
        gest = math.sin((t - a) * 6) if t > a else 0
        if t < rn:
            rp = Pose(x=1260, y=GY, s=0.88, f=-1, t=t, blink_seed=71, look=(-1, 0), lean=12,
                      eyes="wide" if t > a + 0.6 else "open", mouth="o" if t < a + 0.6 else "grin",
                      brows="up", arm_b=70, elb_b=60)
        else:
            rp = run(Pose(x=1260 + (t - rn) * 900, y=GY, s=0.88, f=1, t=t, blink_seed=71, eyes="happy", mouth="grin"),
                     t, 2.4)
        kw = dict(f=1, eyes="open", mouth="smile", brows="up", look=(1, 0),
                  arm_b=100 + 25 * gest if t > a else 20, elb_b=40 * gest, arm_a=60 if t > a else 10, elb_a=-30)
        J = prediction_set(cx, t, cam, self, kw, [(roman(RICH_MAN), rp)])
        if a + 0.4 < t < rn + 0.5:
            # a little house drawn in the air
            hx, hy = J["head"][0] + 120, J["head"][1] - 120
            cx.move_to(hx - 40, hy)
            cx.line_to(hx, hy - 36)
            cx.line_to(hx + 40, hy)
            cx.line_to(hx + 30, hy)
            cx.line_to(hx + 30, hy + 40)
            cx.line_to(hx - 30, hy + 40)
            cx.line_to(hx - 30, hy)
            cx.close_path()
            fs(cx, (1, 1, 1, 0.5), (1, 0.9, 0.5, 0.95), 5)
        end(cx)


class S6Weather(Shot):
    scene = "s6"
    music = "quirky"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.say("s6_07", gap=0.3)
        a = P.say("s6_08", gap=0.3)
        P.mark("sky", a + P.voice.dur("s6_08") * 0.6)
        b = P.say("s6_09", gap=0.4)
        c = P.say("s6_10", gap=0.6)
        P.mark("back", c - 0.1)
        P.accent("[100%] SUNSHINE", t=c + 0.4, dur=P.voice.dur("s6_10") + 0.5, size=100, pos=(W / 2, 170))
        P.sfx("ding", t=c + 0.5, vol=0.4)

    def draw(self, cx, t):
        sky = self.mt("sky")
        bk = self.mt("back")
        if sky <= t < bk:
            # empty blue sky
            g = cairo.LinearGradient(0, 0, 0, H)
            g.add_color_stop_rgba(0, *hexc("#5DB4EC"))
            g.add_color_stop_rgba(1, *hexc("#BDE6FF"))
            cx.set_source(g)
            cx.paint()
            k = prog(t, sky, bk)
            gg = cairo.RadialGradient(1500, 260 - 60 * k, 10, 1500, 260 - 60 * k, 300)
            gg.add_color_stop_rgba(0, 1, 1, 0.85, 1)
            gg.add_color_stop_rgba(0.3, 1, 0.95, 0.6, 0.6)
            gg.add_color_stop_rgba(1, 1, 0.95, 0.6, 0)
            cx.set_source(gg)
            cx.paint()
            circle(cx, 1500, 260 - 60 * k, 90)
            fs(cx, hexc("#FFF4C2"), OUTLINE, 5)
            return
        cam = Cam(1060, 640, 1.6)
        cust = Pose(x=1280, y=GY, s=0.88, f=-1, t=t, blink_seed=72, look=(-1, 0), mouth="smile",
                    eyes="open", arm_b=20)
        thumbs = t >= bk
        kw = dict(f=1, eyes="open", mouth="smile", look=(0.6, -1) if t > self.mt("s6_08") else (1, 0))
        if thumbs:
            k = win(t, bk, bk + 0.3)
            kw = dict(view="front", eyes="happy", mouth="grin", brows="up", arm_b=lerp(10, 120, k), elb_b=lerp(0, 60, k))
        J = prediction_set(cx, t, cam, self, kw, [(roman(WEATHER_MAN), cust)])
        if thumbs:
            line(cx, [J["hand_b"], (J["hand_b"][0] - 2, J["hand_b"][1] - 24)], OUTLINE, 9)
        end(cx)


class S6Genius(Shot):
    scene = "s6"
    music = "quirky"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s6_11", gap=0.4)
        P.sfx("cheer", t=a + 0.3, vol=0.3)
        b = P.say("s6_12", gap=0.3)
        P.mark("cloud", b + 0.3)
        P.sfx("thunder", t=b + 0.6, vol=0.5)
        P.mark("drop", b + P.voice.dur("s6_12") + 0.9)
        P.sfx("drip", t=b + P.voice.dur("s6_12") + 0.9, vol=0.9)
        P.wait(1.9)
        self.music_cut = True

    def draw(self, cx, t):
        cl = self.mt("cloud")
        dp = self.mt("drop")
        dark = win(t, cl, cl + 1.5)
        cam = cam_kf(t, [(0, (1000, 630, 1.4)), (cl, (1000, 630, 1.4)), (dp - 0.4, (TABLE_X, GY - 270, 2.4))])
        glow = 1 - dark
        kw = dict(view="front", eyes="happy" if dark < 0.5 else "open", mouth="grin" if dark < 0.5 else "flat",
                  brows="up" if dark < 0.5 else "neutral", look=(0, -1) if dark > 0.5 else (0, 0),
                  blink=dark < 0.5, arm_a=150 if dark < 0.3 else 10, arm_b=150 if dark < 0.3 else 10, elb_a=10, elb_b=10)
        if t > dp:
            kw.update(eyes="tiny", mouth="flat", look=(0, 0))
        cust = []
        for i in range(3):
            ph = t * 6 + i
            p = Pose(x=1320 + i * 150, y=GY, s=0.85, f=-1, t=t, blink_seed=i + 80, eyes="happy", mouth="grin",
                     arm_a=60 + 20 * math.sin(ph), arm_b=60 - 20 * math.sin(ph), elb_a=90, elb_b=90)
            if dark > 0.3:
                p = p.but(eyes="open", mouth="o", look=(0, -1), arm_a=10, arm_b=10, brows="up")
            cust.append((roman(80 + i), p))
        J = prediction_set(cx, t, cam, self, kw, cust, sky_dark=dark)
        if glow > 0.2:
            P.sparkles(cx, J["head"][0], J["head"][1], t, 110, 8, glow)
        # storm cloud sliding over
        if t > cl - 0.2:
            k = ease_io(prog(t, cl, cl + 1.6))
            P.storm_cloud(cx, lerp(2200, TABLE_X + 40, k), J["head"][1] - 330, 1.6, 1.0)
        if t > dp - 0.6:
            k = ease_in(prog(t, dp - 0.6, dp))
            if t < dp:
                P.raindrop(cx, J["head"][0], lerp(J["head"][1] - 300, J["head"][1] - J["head_rad"], k), 1.4)
            else:
                k2 = prog(t, dp, dp + 0.3)
                for s in (-1, 1):
                    P.raindrop(cx, J["head"][0] + s * 30 * k2, J["head"][1] - J["head_rad"] - 20 * math.sin(math.pi * k2),
                               0.6, 1 - k2)
        end(cx)
        if t > dp + 1.2:
            black(cx)


# =============================================================== SCENE 7
class S7Rain(Shot):
    scene = "s7"
    music = "rain"
    music_gain = 0.7
    amb = "rain"
    amb_gain = 1.4

    def plan(self, P):
        P.wait(0.8)
        P.accent("DAY 6", t=0.9, dur=1.7, size=120)
        P.sfx("thunder", t=0.2, vol=0.7)
        P.say("s7_01", lead=0.2, gap=0.35)
        P.say("s7_02", gap=0.4)
        a = P.say("s7_03", gap=0.6)
        P.mark("more", a)
        P.sfx("thunder", t=a + 0.2, vol=0.6)

    def draw(self, cx, t):
        if t < 0.6:
            black(cx)
            return
        more = self.mt("more")
        hx = -200 + 520 * min(t - 0.6, 2.4)
        cam = Cam(700, 620, 1.3)
        S.market(cx, cam, t, weather="rain", wet=1.0)
        world(cx, cam)
        under = t > 3.0
        hp = hero_pose(min(hx, 1050), GY, t, f=1, eyes="squeeze" if not under else "half", mouth="wavy" if not under else "flat",
                       brows="worried", arm_a=160, arm_b=150, elb_a=40, elb_b=40)
        if not under:
            hp = run(hp, t, 2.4, 0.9, arms=False)
        else:
            hp = breathe(hp.but(arm_a=10, arm_b=10, elb_a=10, elb_b=10), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        P.drips(cx, J["head"][0], J["head"][1] + 20, 90, t, 6, 0.9)
        end(cx)
        dens = 1.2 + 1.6 * win(t, more, more + 0.8)
        P.rain(cx, t, 0, W, 0, H, density=dens, alpha=1.0)
        tint(cx, (0.1, 0.12, 0.2), 0.15)


class S7Angry(Shot):
    scene = "s7"
    music = "rain"
    music_gain = 0.7
    amb = "rain"
    amb_gain = 1.2

    def plan(self, P):
        P.wait(0.2)
        P.say("s7_04", gap=0.35)
        P.say("s7_05", gap=0.5)

    def draw(self, cx, t):
        cam = Cam(1150, 620, 1.55)
        S.market(cx, cam, t, weather="rain", wet=1.0)
        world(cx, cam)
        J = fig(cx, self, cam, HERO, breathe(hero_pose(1050, GY, t, f=1, eyes="open", mouth="teeth", brows="worried",
                                                       sweat=0.6, lean=-6), t), "hero")
        ph = math.sin(t * 3)
        up = ph > 0
        p = Pose(x=1300, y=GY, s=0.88, f=-1, t=t, blink_seed=72, brows="angry", mouth="yell",
                 mouth_open=0.6 + 0.4 * abs(math.sin(t * 9)),
                 arm_b=160 if up else 95, elb_b=0, look=(0, -1) if up else (-1, 0))
        RJ = roman(WEATHER_MAN).draw(cx, p)
        P.drips(cx, RJ["head"][0], RJ["head"][1] + 20, 80, t, 5, 0.9, seed=2)
        P.anger_mark(cx, RJ["head"][0] + 40, RJ["head"][1] - 50, 1.0, 1)
        end(cx)
        P.rain(cx, t, 0, W, 0, H, density=2.4)
        tint(cx, (0.1, 0.12, 0.2), 0.15)


class S7Max(Shot):
    scene = "s7"
    music = "suspense"
    amb = "rain"
    amb_gain = 1.2

    def plan(self, P):
        P.wait(0.2)
        P.sfx("dun", t=0.25, vol=0.6)
        P.say("s7_06", gap=0.35)
        a = P.say("s7_07", gap=0.3)
        b = P.say("s7_08", gap=0.4)
        P.mark("jail", b)
        P.sfx("clank", t=b + 0.3, vol=0.5)
        c = P.say("s7_09", gap=0.6)
        P.mark("deadpan", c - 0.1)

    def draw(self, cx, t):
        jl = self.mt("jail")
        dp = self.mt("deadpan")
        a = self.mt("s7_07")
        if t >= dp:
            cam = Cam(960, GY - 250, 2.7)
        else:
            cam = Cam(1100, 600, 1.35)
        S.market(cx, cam, t, weather="rain", wet=1.0)
        world(cx, cam)
        if t >= dp:
            fig(cx, self, cam, HERO, hero_pose(960, GY, t, view="front", eyes="half", mouth="flat", brows="flat"), "hero")
            P.drips(cx, 960, GY - 230, 90, t, 5, 0.9)
        else:
            k = ease_out(prog(t, 0, 0.8))
            mp = max_pose(lerp(1800, 1330, k), GY, t, f=-1, eyes="angry", brows="angry", mouth="yell",
                          mouth_open=0.7 + 0.3 * abs(math.sin(t * 8)),
                          arm_b=130 if t > a else 40, elb_b=-10)
            if k < 1:
                mp = walk(mp, t, 1.1, 0.8)
            MJ = fig(cx, self, cam, WET_MAX, mp, "max")
            P.drips(cx, MJ["head"][0], MJ["head"][1] + 40, 120, t, 7, 0.9)
            P.anger_mark(cx, MJ["head"][0] + 60, MJ["head"][1] - 90, 1.3, 1)
            hp = breathe(hero_pose(980, GY, t, f=1, eyes="wide", mouth="teeth", brows="worried", sweat=1, lean=-10,
                                   look=(1, -0.5)), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            ja = win(t, jl, jl + 0.3)
            if ja > 0:
                bx, by = J["head"][0] - 260, J["head"][1] - 230
                thought_bubble(cx, bx, by, 300, 200, ja, tail_to=(J["head"][0] - 40, J["head"][1] - 50))
                cx.save()
                cx.push_group()
                # tiny sad prisoner behind bars
                HERO.draw(cx, hero_pose(bx, by + 90, t, s=0.4, view="front", eyes="open", mouth="frown",
                                        brows="worried", arm_a=150, arm_b=150, elb_a=30, elb_b=30))
                for k in range(5):
                    line(cx, [(bx - 110 + k * 55, by - 80), (bx - 110 + k * 55, by + 90)], hexc("#5E5E66"), 9)
                cx.pop_group_to_source()
                cx.paint_with_alpha(ja)
                cx.restore()
        end(cx)
        P.rain(cx, t, 0, W, 0, H, density=2.2)
        tint(cx, (0.1, 0.12, 0.2), 0.15)


def bakery_rainy(cx, cam, t):
    S.bakery(cx, cam, t)
    world(cx, cam)
    cx.save()
    cx.move_to(1480, 560)
    cx.line_to(1480, 300)
    cx.arc(1600, 300, 120, math.pi, 2 * math.pi)
    cx.line_to(1720, 560)
    cx.close_path()
    cx.clip()
    cx.rectangle(1400, 150, 400, 420)
    src(cx, hexc("#6E7C90"))
    cx.fill()
    P.rain(cx, t, 1450, 1750, 150, 570, density=4)
    cx.restore()
    end(cx)


class S7Plan(Shot):
    scene = "s7"
    trans_in = ("dip", 0.4)
    music = "quirky"
    amb = "bakery"

    def plan(self, P):
        P.wait(0.3)
        P.say("s7_10", gap=0.3)
        P.say("s7_11", gap=0.3)
        P.say("s7_12", gap=0.4)
        a = P.say("s7_13", gap=0.3)
        P.mark("diagram", a - 0.1)
        P.say("s7_14", gap=0.3)
        P.say("s7_15", gap=0.5)

    def draw(self, cx, t):
        dg = self.mt("diagram")
        if t < dg:
            cam = Cam(960, 640, 1.6)
            bakery_rainy(cx, cam, t)
            world(cx, cam)
            terrible = self.mt("s7_11") <= t < self.mt("s7_12")
            hp = breathe(hero_pose(960, GY, t, f=1, eyes="half" if not terrible else "open",
                                   mouth="smirk" if not terrible else "teeth", brows="up",
                                   arm_b=80, elb_b=50, arm_a=70, elb_a=60), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            # wax tablet
            rrect(cx, J["hand_b"][0] - 10, J["hand_b"][1] - 70, 110, 80, 6)
            fs(cx, hexc("#8A5A2E"), OUTLINE, 4)
            rrect(cx, J["hand_b"][0] - 2, J["hand_b"][1] - 62, 94, 64, 4)
            fs(cx, hexc("#3A2A20"), None, 0)
            end(cx)
            return
        # wax-tablet diagram, drawn stroke by stroke
        insert_bg(cx, "#8A5A2E", "#5E3A1E")
        rrect(cx, 260, 120, 1400, 840, 30)
        fs(cx, hexc("#3A2A20"), OUTLINE, 10)
        ink = hexc("#E9D7A6")
        k = prog(t, dg, dg + 3.2)
        steps = [
            lambda: line(cx, [(560, 820), (560, 330), (1360, 330), (1360, 820)], ink, 10),   # frame
            lambda: line(cx, [(480, 820), (1440, 820)], ink, 10),                           # stage
            lambda: P.bucket(cx, 960, 380, 1.2, rot=0.0, water=False),                      # bucket
            lambda: line(cx, [(960, 340), (1500, 340), (1500, 700)], ink, 7),                # rope
            lambda: HERO.draw(cx, hero_pose(960, 820, t, s=0.9, view="front", eyes="happy", mouth="grin",
                                            arm_a=150, arm_b=150, elb_a=10, elb_b=10)),
        ]
        n = int(k * len(steps) + 0.999) if k > 0 else 0
        for i in range(min(n, len(steps))):
            steps[i]()
        if t > self.mt("s7_14"):
            for i in range(14):
                yy = 480 + ((t * 300 + i * 53) % 300)
                P.raindrop(cx, 820 + (i % 7) * 45, yy, 0.8, 0.9)


class S7Machine(Shot):
    scene = "s7"
    music = None
    amb = "bakery"

    def plan(self, P):
        P.wait(0.4)
        P.say("s7_16", gap=0.25)
        P.say("s7_17", gap=0.25)
        P.say("s7_18", gap=0.4)
        P.say("s7_19", gap=0.4)
        a = P.say("s7_20", gap=0.9)
        P.sfx("crickets", t=a + 0.2, vol=0.3)

    def draw(self, cx, t):
        cam = Cam(1000, 590, 1.25)
        bakery_rainy(cx, cam, t)
        world(cx, cam)
        cx.save()
        cx.translate(0, 150)
        S.rain_rig(cx, 900, 300, t=t)
        cx.restore()
        P.bucket(cx, 900, 470, 0.9)
        P.rope(cx, [(900, 450), (1260, 450), (1260, 760)])
        tgt = pick(t, [(0, (-1, -0.6)), (self.mt("s7_17"), (-0.4, 0.2)), (self.mt("s7_18"), (-1, -0.6))])
        if t > self.mt("s7_19"):
            tgt = (-0.4, 0.2)
        lp = breathe(lucia_pose(1450, GY, t, f=-1, look=tgt, eyes="half", mouth="flat",
                                tilt=-6 if tgt[1] < 0 else 0, arm_a=60, arm_b=60, elb_a=-110, elb_b=-110,
                                view="side"), t)
        fig(cx, self, cam, LUCIA, lp, "lucia")
        sw = win(t, self.mt("s7_19"), self.mt("s7_19") + 1.0)
        hp = breathe(hero_pose(780, GY, t, view="front", eyes="open", mouth="grin" if sw < 0.5 else "teeth",
                               brows="up" if sw < 0.5 else "worried", sweat=sw, look=(1, 0),
                               arm_a=150 if sw < 0.5 else 10, arm_b=150 if sw < 0.5 else 10, elb_a=10, elb_b=10), t)
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)


class S7Bucket(Shot):
    scene = "s7"
    music = None
    amb = "bakery"

    def plan(self, P):
        P.wait(0.3)
        P.mark("tug", 0.8)
        P.sfx("creak", t=0.8, vol=0.5)
        P.mark("hit", 1.35)
        P.sfx("bonk", t=1.35, vol=0.9)
        P.sfx("splash", t=1.38, vol=0.6)
        P.sfx("drip", t=2.6, vol=0.5)
        P.sfx("drip", t=3.3, vol=0.5)
        P.wait(3.4)
        P.say("s7_21", gap=0.9)

    def draw(self, cx, t):
        tg = self.mt("tug")
        hit = self.mt("hit")
        cam = Cam(960, 600, 1.45)
        bakery_rainy(cx, cam, t)
        world(cx, cam)
        cx.save()
        cx.translate(0, 150)
        S.rain_rig(cx, 900, 300, t=t)
        cx.restore()
        k = win(t, tg, tg + 0.2)
        bp = boy_pose(1280, GY, t, f=-1, eyes="happy" if t < hit else "wide", mouth="grin" if t < hit else "o",
                      arm_b=lerp(60, 130, k), elb_b=-20, arm_a=lerp(60, 120, k), elb_a=-20, lean=-10 * k)
        BJ = fig(cx, self, cam, BOY, bp, "boy")
        hx = 900
        if t < hit:
            hp = breathe(hero_pose(hx, GY, t, view="front", eyes="happy", mouth="grin", brows="up",
                                   arm_a=40, arm_b=40, elb_a=-100, elb_b=-100), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            fall = ease_in(prog(t, tg + 0.1, hit))
            by = lerp(470, J["head"][1] - 70, fall)
            P.bucket(cx, hx, by, 0.9, rot=math.pi * fall)
            P.rope(cx, [(hx, by), (1260, 450), BJ["hand_b"]])
        else:
            squash = 1 - 0.12 * math.exp(-(t - hit) * 6) * abs(math.cos((t - hit) * 20))
            hp = hero_pose(hx, GY, t, view="front", eyes="open", mouth="flat", brows="flat", squash=squash,
                           arm_a=8, arm_b=8, blink=False)
            J = fig(cx, self, cam, HERO, hp, "hero")
            P.bucket(cx, hx, J["head"][1] + 18, 0.9, rot=math.pi, water=False)
            P.water_splash(cx, hx, J["head"][1], t - hit, 0.7)
            P.drips(cx, hx, J["head"][1] + 30, 110, t, 6, 1.0)
            P.rope(cx, [(hx, J["head"][1] - 40), (1260, 450), BJ["hand_b"]])
        end(cx)


def scenes():
    return [S5Gather(), S5Pressure(), S5Dead(), S5Tray(), S5Pigeon(), S5Kneel(),
            S6Table(), S6Rich(), S6Weather(), S6Genius(),
            S7Rain(), S7Angry(), S7Max(), S7Plan(), S7Machine(), S7Bucket()]

"""Scene 8 (Day 7: the great miracle), Scene 9 (everything goes wrong), Scene 10 (the escape)."""
from .common import *  # noqa

ROBE = hexc("#6B3FA0")
STAGE_X = 960
STAGE_TOP = GROUND - 150
RIG_Y = 250
BUCKET = (STAGE_X, RIG_Y + 60)
ROPE_X = 1265
HERO_STAGE_X = 1150


def robed(on=True):
    HERO.st.robe = ROBE if on else None


def festival_bg(cx, cam, t, mood="cheer", mood_t=1.0, look=(0, 0), rig=True, collapse=0.0, bucket_rot=0.0,
                bucket_vis=True, pigeon=True, coo=0.0):
    S.square(cx, cam, t, festival=True, stage_x=STAGE_X)
    world(cx, cam)
    S.crowd(cx, t, -900, 560, GY + 10, 7, seed=31, s=0.85, mood=mood, mood_t=mood_t, view="side", look=look,
            rows=2, row_dy=-34)
    S.crowd(cx, t, 1420, 2900, GY + 10, 7, seed=32, s=0.85, mood=mood, mood_t=mood_t, view="side", look=look,
            rows=2, row_dy=-34)
    S.stage(cx, STAGE_X, STAGE_TOP, 760)
    if rig:
        if bucket_vis:
            P.bucket(cx, BUCKET[0], BUCKET[1] + collapse * 120, 0.8, rot=bucket_rot)
        S.rain_rig(cx, STAGE_X, RIG_Y, collapse=collapse, t=t)
        if pigeon and collapse < 0.2:
            P.pigeon(cx, STAGE_X - 220, RIG_Y - 16, 0.9, 1, t, coo=coo)


def rope_to(cx, hand):
    P.rope(cx, [(STAGE_X, RIG_Y + 14), (ROPE_X, RIG_Y + 14), hand])


# =============================================================== SCENE 8
class S8Arrive(Shot):
    scene = "s8"
    trans_in = ("dip", 0.5)
    music = "festival"
    amb = "crowd"

    def plan(self, P):
        P.accent("DAY 7", t=0.4, dur=1.7, size=120)
        P.sfx("cheer", t=0.2, vol=0.6)
        P.wait(1.0)
        P.say("s8_01", gap=0.3)
        P.say("s8_02", gap=0.4)
        a = P.say("s8_03", gap=0.5)
        P.mark("pan", a)

    def draw(self, cx, t):
        pn = self.mt("pan")
        k = ease_io(prog(t, pn, pn + 3.5))
        cam = Cam(960 + 700 * math.sin(math.pi * k), 580, 1.0 + 0.2 * math.sin(math.pi * k))
        festival_bg(cx, cam, t, mood="cheer", mood_t=1.0)
        robed(True)
        wk = prog(t, 0, 3.2)
        hx = lerp(STAGE_X - 360, HERO_STAGE_X, ease_out(wk))
        hp = hero_pose(hx, STAGE_TOP, t, f=1, eyes="wide", mouth="teeth", brows="worried", sweat=1.0, look=(0.5, 0))
        hp = walk(hp, t, 0.8, 0.5) if wk < 1 else breathe(hp.but(arm_a=20, arm_b=20), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        mp = breathe(max_pose(1460, GY + 5, t, f=-1, view="front", arm_a=60, arm_b=60, elb_a=-115, elb_b=-115,
                              eyes="angry", brows="angry", mouth="frown"), t)
        fig(cx, self, cam, MAXIMUS, mp, "max")
        end(cx)


class S8Inventory(Shot):
    scene = "s8"
    music = "festival"
    music_gain = 0.6
    amb = "crowd"
    amb_gain = 0.6

    def plan(self, P):
        P.wait(0.2)
        P.say("s8_04", gap=0.35)
        a = P.say("s8_05", gap=0.35)
        P.mark("rope", a - 0.1)
        b = P.say("s8_06", gap=0.5)
        P.mark("face", b - 0.1)

    def draw(self, cx, t):
        rp = self.mt("rope")
        fc = self.mt("face")
        if t < rp:
            cam = Cam(STAGE_X, RIG_Y + 70, 2.6)
            festival_bg(cx, cam, t)
            # peek behind the cloth
            cx.save()
            P.bucket(cx, BUCKET[0], BUCKET[1] + 10, 0.8)
            cx.restore()
            P.sparkles(cx, BUCKET[0], BUCKET[1] + 40, t, 70, 4, 0.8)
            end(cx)
        elif t < fc:
            cam = Cam(ROPE_X - 40, STAGE_TOP - 140, 2.6)
            festival_bg(cx, cam, t)
            robed(True)
            hp = hero_pose(HERO_STAGE_X, STAGE_TOP, t, f=1, eyes="open", mouth="flat", brows="worried",
                           look=(1, 0), arm_b=40, elb_b=20)
            J = fig(cx, self, cam, HERO, hp, "hero")
            robed(False)
            rope_to(cx, (ROPE_X, STAGE_TOP - 120))
            P.sparkles(cx, ROPE_X, STAGE_TOP - 140, t, 50, 3, 0.7)
            end(cx)
        else:
            cam = Cam(HERO_STAGE_X, STAGE_TOP - 250, 2.8)
            festival_bg(cx, cam, t)
            robed(True)
            k = math.sin(t * 45)
            fig(cx, self, cam, HERO, hero_pose(HERO_STAGE_X + k * 2, STAGE_TOP, t, view="front", eyes="wide",
                                               mouth="teeth", brows="worried", sweat=1.0, tilt=2 * k), "hero")
            robed(False)
            end(cx)


class S8News(Shot):
    scene = "s8"
    music = "suspense"
    amb = "crowd"
    amb_gain = 0.6

    def plan(self, P):
        P.wait(0.2)
        P.say("s8_07", gap=0.25)
        a = P.say("s8_08", gap=0.35)
        P.sfx("beep", t=a + 0.3, vol=0.3)
        b = P.say("s8_09", gap=0.25)
        c = P.say("s8_10", gap=0.4)
        P.sfx("beep", t=c + 0.3, vol=0.3)
        d = P.say("s8_11", gap=0.3)
        P.mark("max", d - 0.1)
        P.sfx("clank", t=d + 0.8, vol=0.5)
        P.sfx("clank", t=d + 1.0, vol=0.5)
        P.dlg("d_max_rain", "max", "Now, wizard.\nMake it [RAIN!]", gap=0.4)

    def draw(self, cx, t):
        mx = self.mt("max")
        if t < mx:
            insert_bg(cx, "#E9D3A6", "#C8A46E")
            bad = t >= self.mt("s8_09")
            P.watch(cx, W / 2, H / 2 + 20, 3.4, 0.0, display="98%" if not bad else "10 MIN",
                    lcd_glow=0.5 + 0.5 * (math.sin(t * 6) > 0))
            return
        cam = Cam(1460, GY - 400, 2.2)
        festival_bg(cx, cam, t)
        crack = pulse(t, mx + 0.7, mx + 1.2)
        dl = self.m["d_max_rain"]
        mp = breathe(max_pose(1460, GY + 5, t, f=-1, view="front", eyes="angry", brows="angry", mouth="frown",
                              arm_a=60 + 20 * crack, arm_b=60 + 20 * crack, elb_a=-115, elb_b=-115), t)
        if dl[0] <= t <= dl[1]:
            mp = talk(mp.but(mouth="yell", arm_b=120, elb_b=0, view="side"), t)
        fig(cx, self, cam, MAXIMUS, mp, "max")
        end(cx)


class S8Ritual(Shot):
    scene = "s8"
    music = None
    amb = "crowd"
    amb_gain = 0.25

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s8_12", gap=0.3)
        P.sfx("sparkle", t=a + 0.3, vol=0.3)
        P.say("s8_13", gap=0.3)
        b = P.say("s8_14", gap=0.5)
        P.mark("face", b - 0.1)
        c = P.say("s8_15", gap=0.5)
        P.mark("pull", c - 0.1)
        P.sfx("heartbeat", t=c + 0.2, vol=0.5)
        d = P.say("s8_16", gap=0.5)
        P.sfx("creak", t=d - 0.3, vol=0.4)
        e = P.say("s8_17", gap=0.5)
        P.sfx("creak", t=e - 0.2, vol=0.6)

    def draw(self, cx, t):
        fc = self.mt("face")
        pl = self.mt("pull")
        robed(True)
        if t < fc:
            cam = Cam(1060, 560, 1.25)
            festival_bg(cx, cam, t, mood="stare", mood_t=5, look=(0.5, -0.3))
            up = win(t, 0.2, 0.8)
            hp = breathe(hero_pose(HERO_STAGE_X, STAGE_TOP, t, view="front", eyes="open", mouth="flat", brows="up",
                                   arm_a=lerp(10, 155, up), arm_b=lerp(10, 155, up), elb_a=10, elb_b=10,
                                   look=(0, -1) if t > self.mt("s8_13") else (0, 0)), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            rope_to(cx, (ROPE_X, STAGE_TOP - 120))
            end(cx)
        elif t < pl:
            cam = Cam(HERO_STAGE_X, STAGE_TOP - 260, 3.0)
            festival_bg(cx, cam, t, mood="stare", mood_t=5)
            hp = hero_pose(HERO_STAGE_X, STAGE_TOP, t, view="front", eyes="half", mouth="smirk", brows="skeptic",
                           arm_a=155, arm_b=155, elb_a=10, elb_b=10, look=(0.3, -0.6), tilt=-6, blink=False)
            fig(cx, self, cam, HERO, hp, "hero")
            end(cx)
        else:
            cam = Cam(HERO_STAGE_X + 40, STAGE_TOP - 170, 1.9)
            festival_bg(cx, cam, t, mood="stare", mood_t=5, look=(0.5, -0.3))
            tug1 = pulse(t, self.mt("s8_16") - 0.3, self.mt("s8_16") + 0.2, 0.1)
            tug2 = pulse(t, self.mt("s8_17") - 0.2, self.mt("s8_17") + 0.5, 0.1)
            tug = max(tug1 * 0.6, tug2)
            hp = hero_pose(HERO_STAGE_X, STAGE_TOP, t, f=1, eyes="half" if tug < 0.3 else "squeeze",
                           mouth="smirk" if tug < 0.3 else "teeth", brows="skeptic" if tug < 0.3 else "worried",
                           arm_a=155, elb_a=10, arm_b=lerp(70, 40, tug), elb_b=lerp(20, 60, tug), lean=-10 * tug,
                           sweat=tug2, look=(0, -1))
            J = fig(cx, self, cam, HERO, hp, "hero")
            rope_to(cx, J["hand_b"])
            end(cx)
        robed(False)


class S8Awkward(Shot):
    scene = "s8"
    music = None
    amb = "crowd"
    amb_gain = 0.2

    def plan(self, P):
        P.wait(0.3)
        P.sfx("coo", t=0.4, vol=0.7)
        P.sfx("crickets", t=1.0, vol=0.3)
        P.wait(1.6)
        P.say("s8_18", gap=0.4)
        P.say("s8_19", gap=0.9)
        P.sfx("wah", t=P.t - 1.4, vol=0.4)

    def draw(self, cx, t):
        if t < 1.3:
            cam = Cam(STAGE_X - 220, RIG_Y - 40, 3.0)
            festival_bg(cx, cam, t, coo=1)
            end(cx)
            return
        cam = Cam(960, 600, 1.05)
        festival_bg(cx, cam, t, mood="confused", mood_t=1.0)
        robed(True)
        hp = hero_pose(HERO_STAGE_X, STAGE_TOP, t, view="front", eyes="open", mouth="teeth", brows="worried",
                       arm_a=lerp(155, 10, win(t, 3, 3.6)), arm_b=lerp(155, 10, win(t, 3, 3.6)), elb_a=10,
                       elb_b=10, sweat=1, look=(-1, 0))
        J = fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        rope_to(cx, (ROPE_X, STAGE_TOP - 120))
        mp = breathe(max_pose(1460, GY + 5, t, f=-1, eyes="angry", brows="angry", mouth="frown"), t)
        fig(cx, self, cam, MAXIMUS, mp, "max")
        P.anger_mark(cx, 1500, GY - 520, 1.2, win(t, 2.0, 2.3))
        end(cx)


# =============================================================== SCENE 9
class S9Grab(Shot):
    scene = "s9"
    music = "chase"
    music_gain = 0.8
    amb = "crowd"
    amb_gain = 0.6

    def plan(self, P):
        P.sfx("step_heavy", t=0.2, vol=0.6)
        P.sfx("step_heavy", t=0.5, vol=0.6)
        P.wait(0.3)
        a = P.say("s9_01", gap=0.25)
        P.mark("grab", a + 0.4)
        P.sfx("swish", t=a + 0.4, vol=0.6)
        P.sfx("click", t=a + 0.8, vol=0.5)
        b = P.say("s9_02", gap=0.25)
        P.mark("rope", b + 0.2)
        c = P.say("s9_03", gap=0.25)
        P.mark("yank", c + 0.2)
        P.sfx("creak", t=c + 0.2, vol=0.7)
        d = P.say("s9_04", gap=0.3)
        P.mark("collapse", d + 0.3)
        P.sfx("crash_wood", t=d + 0.3, vol=0.7)
        P.mark("pour", d + 0.75)
        P.sfx("splash", t=d + 0.8, vol=0.9)
        P.wait(0.6)
        e = P.say("s9_05", gap=0.35)
        P.say("s9_06", gap=0.35)
        f = P.say("s9_07", gap=0.4)
        P.mark("laugh", f + 0.2)
        P.sfx("laugh", t=f + 0.2, vol=0.8)
        P.wait(1.0)

    def draw(self, cx, t):
        g = self.mt("grab")
        rp = self.mt("rope")
        yk = self.mt("yank")
        co = self.mt("collapse")
        po = self.mt("pour")
        lg = self.mt("laugh")
        if t < g:
            cam = Cam(1100, 560, 1.3)
        elif t < lg:
            cam = Cam(1060, 480, 1.45)
        else:
            cam = cam_kf(t, [(lg, (1060, 480, 1.45)), (lg + 0.8, (960, 580, 1.05))])
        if co < t < co + 0.5:
            sx, sy = shake(t, 8, 20)
            cam.x += sx
            cam.y += sy
        coll = ease_in(prog(t, co, co + 0.4))
        tip = ease_out(prog(t, co, po))
        festival_bg(cx, cam, t, mood="laugh" if t > lg else ("gasp" if t > co else "stare"), mood_t=t - (lg if t > lg else co),
                    collapse=coll * 0.4, bucket_vis=False)
        # Maximus storms the stage
        walk_k = ease_out(prog(t, 0, g))
        mx = lerp(1460, STAGE_X + 40, walk_k)
        my = lerp(GY + 5, STAGE_TOP, walk_k)
        wet = t > po + 0.15
        st = WET_MAX if wet else MAXIMUS
        mp = max_pose(mx, my, t, f=1, eyes="angry", brows="angry", mouth="yell", arm_b=lerp(30, 70, win(t, g - 0.2, g)),
                      elb_b=-20, arm_a=20, elb_a=40)
        if walk_k < 1:
            mp = walk(mp.but(f=-1), t, 1.2, 0.8)
        if wet:
            mp = mp.but(eyes="squeeze" if t < po + 1.0 else "angry", mouth="flat", brows="angry", arm_b=70, elb_b=-20)
        MJ = fig(cx, self, cam, st, mp, "max")
        # hero dangling from Maximus' fist
        robed(True)
        if t < g:
            hp = breathe(hero_pose(HERO_STAGE_X, STAGE_TOP, t, f=-1, eyes="wide", mouth="scream", brows="worried",
                                   sweat=1, arm_a=10, arm_b=10), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
        else:
            lift = ease_out(prog(t, g, g + 0.3))
            hx, hy = MJ["hand_b"][0] + 40, MJ["hand_b"][1] + 330 - 90 * lift
            kick = math.sin(t * 16)
            reach = win(t, rp - 0.2, rp + 0.2)
            hp = hero_pose(hx, hy, t, f=-1, eyes="wide", mouth="scream", brows="worried", sweat=1,
                           hip_a=20 * kick, hip_b=-20 * kick, knee_a=30, knee_b=30,
                           arm_b=lerp(40 + 30 * kick, -150, reach) if t < yk else -150, elb_b=10,
                           arm_a=40 - 30 * kick, elb_a=30)
            J = fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        # the watch, ripped from his wrist into Maximus' other hand
        if t > g + 0.4:
            P.wrist_watch_small(cx, MJ["hand_a"][0], MJ["hand_a"][1], 1.3)
        elif t > g:
            k = prog(t, g, g + 0.4)
            P.wrist_watch_small(cx, lerp(J["hand_b"][0], MJ["hand_a"][0], k), lerp(J["hand_b"][1], MJ["hand_a"][1], k) - 40 * math.sin(math.pi * k), 1.3)
        # rope + bucket
        if t < rp:
            rope_to(cx, (ROPE_X, STAGE_TOP - 120))
        else:
            rope_to(cx, J["hand_b"])
        bx = BUCKET[0] + 30 * coll
        by = BUCKET[1] + 80 * coll
        if t < po + 1.2:
            P.bucket(cx, bx, by, 0.8, rot=math.pi * 0.85 * tip, water=t < po)
        if po - 0.05 < t < po + 1.0:
            a = 1 - prog(t, po + 0.6, po + 1.0)
            slow = 1.0
            P.water_pour(cx, MJ["head"][0], by + 10, MJ["head"][1] + 20, 70, a, t)
            P.water_splash(cx, MJ["head"][0], MJ["head"][1] - 30, (t - po - 0.3) * 0.7, 1.0)
        if wet:
            P.drips(cx, MJ["head"][0], MJ["head"][1] + 40, 140, t, 8, 1.0)
        end(cx)


class S9Helmet(Shot):
    scene = "s9"
    music = None
    amb = "crowd"
    amb_gain = 0.5

    def plan(self, P):
        P.wait(0.4)
        P.mark("off", 0.6)
        P.sfx("splash", t=1.6, vol=0.5)
        P.wait(1.5)
        P.say("s9_08", gap=0.35)
        P.mark("clank", P.t)
        P.sfx("clank", t=P.t, vol=0.6)
        P.wait(0.5)
        a = P.say("s9_09", gap=0.3)
        P.mark("run", a + 0.2)
        P.sfx("whoosh", t=a + 0.2, vol=0.8)
        P.accent("RUN!", t=a + 0.15, dur=1.2, size=140, pos=(W / 2, 200))
        P.wait(0.3)

    def draw(self, cx, t):
        off = self.mt("off")
        ck = self.mt("clank")
        rn = self.mt("run")
        cam = Cam(STAGE_X + 80, STAGE_TOP - 330, 1.9)
        festival_bg(cx, cam, t, mood="laugh", mood_t=2, collapse=0.4, bucket_vis=False)
        lift = win(t, off, off + 0.8) * (1 - win(t, ck - 0.3, ck))
        mp = max_pose(STAGE_X + 40, STAGE_TOP, t, f=1, view="front", eyes="half", brows="angry", mouth="flat",
                      arm_a=lerp(10, 150, lift), arm_b=lerp(10, 150, lift), elb_a=lerp(10, -15, lift),
                      elb_b=lerp(10, -15, lift), extra={"helmet_off": 45 * lift}, blink=False)
        WET_MAX_STYLE.helmet = True
        MJ = fig(cx, self, cam, WET_MAX, mp, "max")
        P.drips(cx, MJ["head"][0], MJ["head"][1] + 40, 140, t, 8, 1.0)
        if 1.4 < t < 2.4 and lift > 0.5:
            P.water_pour(cx, MJ["head"][0] + 20, MJ["head"][1] - 90, MJ["head"][1] + 40, 30, 1 - prog(t, 2.0, 2.4), t)
        # hero zips off
        robed(True)
        if t < rn:
            hp = hero_pose(STAGE_X + 300, STAGE_TOP, t, f=-1, eyes="wide", mouth="teeth", brows="worried", sweat=1)
            fig(cx, self, cam, HERO, hp, "hero")
        else:
            k = prog(t, rn, rn + 0.35)
            hp = run(hero_pose(STAGE_X + 300 + 1400 * k, STAGE_TOP, t, f=1, eyes="wide", mouth="scream",
                               brows="worried"), t, 3, 1.0)
            fig(cx, self, cam, HERO, hp, "hero")
            P.motion_puffs(cx, STAGE_X + 300, STAGE_TOP, t - rn, 4, 1 - prog(t, rn + 0.3, rn + 0.9))
        robed(False)
        end(cx)


class S9Chase(Shot):
    scene = "s9"
    music = "chase"
    amb = "market"

    def plan(self, P):
        P.wait(1.6)
        P.mark("basket", 1.2)
        P.sfx("crash_wood", t=1.2, vol=0.5)
        P.mark("cart", 2.5)
        P.sfx("cart", t=2.5, vol=0.6)
        P.say("s9_10", gap=0.3)
        P.mark("trip", P.t + 0.2)
        P.sfx("thud", t=P.t + 0.3, vol=0.7)
        P.sfx("clank", t=P.t + 0.35, vol=0.6)
        for k in range(int(P.t / 0.2) + 6):
            P.sfx("step", t=k * 0.2, vol=0.3)
        P.wait(1.2)

    def draw(self, cx, t):
        hx = 200 + 600 * t
        cam = Cam(hx + 80, 620, 1.2)
        S.market(cx, cam, t)
        world(cx, cam)
        bk = self.mt("basket")
        ca = self.mt("cart")
        tr = self.mt("trip")
        # fruit flying from a knocked basket
        bx = 200 + 600 * bk + 60
        if t < bk:
            P.basket(cx, bx, GY - 20, 1.0, "oranges")
        else:
            k = t - bk
            P.basket(cx, bx + 40 * min(k, 0.3), GY - 20, 1.0, "oranges", rot=min(k * 6, 1.6))
            for i in range(6):
                fx = bx + (i - 2) * 50 * k * 3
                fy = GY - 80 - 500 * k + 900 * k * k + i * 4
                if fy < GY:
                    P.rolling_fruit(cx, fx, fy, 14, "#F09A2B", k * 8)
                else:
                    P.rolling_fruit(cx, fx, GY + 10, 14, "#F09A2B", k * 8)
        # cart rolls into the soldiers' path
        cart_x = 200 + 600 * ca + 140 - 260 * max(0, t - ca)
        P.fruit_cart(cx, cart_x, GY + 10, 0.9, wheel_rot=-(t - ca) * 6 if t > ca else 0,
                     rot=0.0 if t < tr else -0.3 * min(1, (t - tr) * 3))
        # soldiers
        for i in range(3):
            sx = hx - 520 - i * 170
            if t > tr and sx > cart_x - 380:
                sx = cart_x - 380 - i * 60
                k = min(1, (t - tr) * 3)
                p = max_pose(sx, GY, t, s=1.12, f=1, eyes="spiral", mouth="wavy", brows="worried", lean=70 * k,
                             bob=60 * k, arm_a=150, arm_b=150)
                fig(cx, self, cam, soldier(i), p)
                P.dizzy_stars(cx, sx + 40, GY - 200, t, 50, k)
            else:
                fig(cx, self, cam, soldier(i), run(max_pose(sx, GY, t + i * 0.2, s=1.12, f=1, mouth="yell",
                                                            brows="angry", eyes="angry"), t + i * 0.2, 2.2))
        robed(True)
        hp = run(hero_pose(hx, GY, t, f=1, eyes="wide", mouth="scream", brows="worried", sweat=1,
                           look=(-1, 0) if 1.0 < t < 1.6 else (1, 0)), t, 2.6, 1.0, flail=True)
        fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        P.motion_puffs(cx, hx - 30, GY, t, 3, 0.8)
        end(cx)


class S9Shoe(Shot):
    scene = "s9"
    music = "chase"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.say("s9_11", gap=0.3)
        for k in range(8):
            P.sfx("step", t=k * 0.2, vol=0.4)

    def draw(self, cx, t):
        hx = 500 + 600 * t
        cam = Cam(hx + 10, GY - 50, 3.0)
        S.market(cx, cam, t)
        world(cx, cam)
        hp = run(hero_pose(hx, GY, t, f=1, eyes="wide", mouth="scream"), t, 2.6, 1.0, flail=True)
        hp = hp.but(extra={"shoe_flap": 0.5 + 0.5 * math.sin(t * 2.6 * 2 * math.pi)})
        robed(True)
        fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        P.motion_puffs(cx, hx - 30, GY, t, 3, 0.8)
        end(cx)


class S9Wrist(Shot):
    scene = "s9"
    music = "suspense"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s9_12", gap=0.3)
        P.sfx("beep2", t=a + 0.6, vol=0.5)
        P.mark("look", a + P.voice.dur("s9_12") * 0.65)
        P.sfx("beep2", t=a + P.voice.dur("s9_12") + 0.1, vol=0.5)
        b = P.say("s9_13", gap=0.4)
        P.mark("max", b + P.voice.dur("s9_13") + 0.1)
        P.sfx("dun", t=b + P.voice.dur("s9_13") + 0.1, vol=0.6)
        c = P.say("s9_14", gap=0.6)
        P.accent("[10 SECONDS] LEFT", t=self_max(P), dur=P.t - self_max(P) - 0.2, size=96, pos=(W / 2, 170))
        for k in range(4):
            P.sfx("beep", t=self_max(P) + 0.4 + k * 0.9, vol=0.4)

    def draw(self, cx, t):
        lk = self.mt("look")
        mx = self.mt("max")
        if t < mx:
            cam = Cam(960, GY - 240, 2.3)
            S.market(cx, cam, t)
            world(cx, cam)
            look = t > lk
            robed(True)
            hp = breathe(hero_pose(960, GY, t, view="front", eyes="wide" if look else "open",
                                   mouth="o" if look else "teeth", brows="worried", sweat=1,
                                   arm_b=lerp(10, 95, win(t, lk - 0.3, lk)), elb_b=lerp(0, 70, win(t, lk - 0.3, lk)),
                                   look=(0.6, 0.5) if look else (-1, 0)), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            robed(False)
            if t > lk + 0.4:
                P.exclaim(cx, J["head"][0] + 90, J["head"][1] - 70, 1.0, 1.0)
            end(cx)
        else:
            cam = Cam(1150, GY - 380, 2.0)
            S.market(cx, cam, t)
            world(cx, cam)
            mp = breathe(max_pose(1150, GY, t, f=-1, eyes="half", brows="angry", mouth="smirk", arm_b=135, elb_b=-20), t)
            MJ = fig(cx, self, cam, WET_MAX, mp, "max")
            P.drips(cx, MJ["head"][0], MJ["head"][1] + 40, 120, t, 5, 0.8)
            blink = 1.0 if (t * 2) % 1 < 0.5 else 0.2
            P.watch(cx, MJ["hand_b"][0], MJ["hand_b"][1] - 40, 0.7, 0.0, display="0:10", lcd_glow=blink, label=False)
            end(cx)


def self_max(P):
    return P.m["max"][0]


# =============================================================== SCENE 10
CORNER_X = 700


class S10Corner(Shot):
    scene = "s10"
    music = "suspense"
    amb = "market"

    def plan(self, P):
        P.wait(0.3)
        P.say("s10_01", gap=0.35)
        a = P.say("s10_02", gap=0.4)
        P.mark("flash_a", a - 0.1)
        b = P.say("s10_03", gap=0.3)
        P.mark("flash_b", b - 0.1)
        P.mark("snatch", b + P.voice.dur("s10_03") * 0.45)
        P.sfx("whoosh", t=b + P.voice.dur("s10_03") * 0.45, vol=0.7)
        P.sfx("gasp", t=b + P.voice.dur("s10_03") * 0.5, vol=0.4)
        c = P.dlg("d_boy_catch", "boy", "[Catch!]", gap=0.2)
        P.mark("throw", c + 0.2)
        P.sfx("swish", t=c + 0.25, vol=0.6)
        d = P.say("s10_04", gap=0.3)
        P.mark("catch", c + 1.4)
        P.sfx("pop", t=c + 1.4, vol=0.6)
        e = P.say("s10_05", gap=0.5)
        P.sfx("tada", t=e + 0.3, vol=0.4)

    def draw(self, cx, t):
        fa, fb = self.mt("flash_a"), self.mt("flash_b")
        sn = self.mt("snatch")
        th = self.mt("throw")
        ca = self.mt("catch")
        if fa <= t < fb:
            # flashback: sharing the bread on day 2
            cam = Cam(960, 650, 1.5)
            S.market(cx, cam, 3.0)
            world(cx, cam)
            HERO.draw(cx, hero_pose(860, GY, 3.0, f=1, eyes="happy", mouth="smile", arm_b=80, elb_b=0, blush=0.4))
            BOY.draw(cx, boy_pose(1090, GY, 3.0, f=-1, eyes="happy", mouth="grin", arm_b=80, elb_b=0))
            P.bread(cx, 975, GY - 190, 0.45, 0)
            P.sparkles(cx, 1090, GY - 240, t, 70, 5, 0.9)
            end(cx)
            sepia(cx, 0.9)
            vignette(cx, 0.6)
            return
        cam = Cam(960, 600, 1.25)
        S.market(cx, cam, t)
        world(cx, cam)
        P.fruit_cart(cx, CORNER_X - 220, GY + 10, 0.9)
        for i in range(2):
            fig(cx, self, cam, soldier(i), breathe(max_pose(1500 + i * 160, GY, t, s=1.12, f=-1, mouth="smirk",
                                                             brows="angry"), t + i))
        mx = 1180
        has = t < sn
        mp = breathe(max_pose(mx, GY, t, f=-1, eyes="half" if has else "wide", brows="angry" if has else "up",
                              mouth="smirk" if has else "o", arm_b=160 if has else lerp(160, 40, win(t, sn, sn + 0.5)),
                              elb_b=0), t)
        MJ = fig(cx, self, cam, WET_MAX, mp, "max")
        if has:
            P.watch(cx, MJ["hand_b"][0], MJ["hand_b"][1] - 30, 0.5, 0, display="0:07", lcd_glow=0.6, label=False)
        # the boy
        if t >= sn - 0.4:
            k = prog(t, sn - 0.4, sn + 0.2)
            bx = lerp(1900, 1000, ease_out(k))
            throwing = th <= t
            bp = boy_pose(bx, GY, t, f=-1, eyes="happy" if not throwing else "open", mouth="grin",
                          arm_b=160 if t < th else lerp(160, 60, win(t, th, th + 0.2)), elb_b=0)
            if k < 1:
                bp = run(bp, t, 3, 1.0, arms=False)
            if t > ca:
                bp = bp.but(arm_b=110, elb_b=60, eyes="happy")
            BJ = fig(cx, self, cam, BOY, bp, "boy")
            if t < th:
                P.watch(cx, BJ["hand_b"][0], BJ["hand_b"][1] - 20, 0.4, 0, display="0:05", lcd_glow=0.6, label=False)
        # hero cornered
        caught = t >= ca
        robed(True)
        hp = breathe(hero_pose(CORNER_X, GY, t, f=1, eyes="wide", mouth="teeth" if not caught else "grin",
                               brows="worried" if not caught else "up", sweat=0 if caught else 1,
                               arm_b=110 if t > th else 20, elb_b=0, arm_a=20 if t < th else 90, elb_a=20,
                               look=(1, -0.4)), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        robed(False)
        if th <= t < ca:
            k = prog(t, th, ca)
            sx, sy = 1000 + 30, GY - 300
            wx = lerp(sx, J["hand_b"][0], k)
            wy = lerp(sy, J["hand_b"][1], k) - 260 * math.sin(math.pi * k)
            P.watch(cx, wx, wy, 0.4, k * 12, display="", label=False)
        elif t >= ca:
            P.watch(cx, J["hand_b"][0], J["hand_b"][1] - 30, 0.45, 0, display="0:04", lcd_glow=0.6, label=False)
            P.sparkles(cx, J["hand_b"][0], J["hand_b"][1] - 30, t, 60, 4, 1 - prog(t, ca + 1, ca + 2))
        end(cx)


class S10Countdown(Shot):
    scene = "s10"
    music = None
    amb = "market"
    amb_gain = 0.5

    def plan(self, P):
        P.wait(0.2)
        for i, lid in enumerate(("s10_06", "s10_07", "s10_08")):
            a = P.say(lid, gap=0.45)
            P.mark(f"n{i}", a)
            P.sfx("beep", t=a, vol=0.6)
            P.sfx("heartbeat", t=a + 0.1, vol=0.4)

    def draw(self, cx, t):
        insert_bg(cx, "#3B2A55", "#1B1530")
        n = 3
        for i in range(3):
            if t >= self.mt(f"n{i}"):
                n = 3 - i
        glow = (math.sin(t * 8) > 0) * 0.5 + 0.5
        k = 1 + 0.05 * (3 - n)
        g = cairo.RadialGradient(W / 2, H / 2, 50, W / 2, H / 2, 700)
        g.add_color_stop_rgba(0, 0.6, 0.85, 1, 0.25 * (4 - n) / 3)
        g.add_color_stop_rgba(1, 0.6, 0.85, 1, 0)
        cx.set_source(g)
        cx.paint()
        P.watch(cx, W / 2, H / 2, 3.6 * k, 0.0, display=f"00:0{n}", lcd_glow=glow)


class S10Portal(Shot):
    scene = "s10"
    music = None
    amb = "market"
    amb_gain = 0.5

    def plan(self, P):
        P.wait(0.15)
        a = P.say("s10_09", gap=0.2)
        P.mark("press", a + P.voice.dur("s10_09") * 0.8)
        P.sfx("click", t=a + P.voice.dur("s10_09") * 0.8, vol=0.8)
        b = P.say("s10_10", gap=0.2)
        P.mark("open", b - 0.2)
        P.sfx("portal", t=b - 0.2, vol=0.8)
        c = P.say("s10_11", gap=0.15)
        P.mark("jump", c + 0.1)
        P.sfx("boing", t=c + 0.1, vol=0.4)
        d = P.say("s10_12", gap=0.2)
        P.mark("grab", d + 0.6)
        P.mark("suck", d + P.voice.dur("s10_12") + 0.1)
        P.sfx("suck", t=d + P.voice.dur("s10_12") + 0.05, vol=0.9)
        P.wait(0.45)

    def draw(self, cx, t):
        op = self.mt("open")
        jp = self.mt("jump")
        gb = self.mt("grab")
        sk = self.mt("suck")
        cam = Cam(900, 580, 1.25)
        S.market(cx, cam, t)
        tint(cx, (0.15, 0.1, 0.35), 0.25 * win(t, op, op + 0.6))
        world(cx, cam)
        px, py = 420, GY - 220
        r = 200 * ease_out(prog(t, op, op + 0.8))
        P.portal(cx, px, py, r, t)
        suck = ease_in(prog(t, sk - 0.05, sk + 0.4))
        # Maximus lunging
        mk = ease_out(prog(t, jp, gb))
        mx = lerp(1300, 760, mk)
        mp = max_pose(mx, GY, t, f=-1, eyes="angry", brows="angry", mouth="yell", lean=30 * mk,
                      arm_b=lerp(30, 95, mk), elb_b=-10)
        if mk < 1 and t > jp:
            mp = run(mp, t, 2.2, 0.8, arms=False)
        if t > sk:
            mp = mp.but(eyes="wide", mouth="scream", brows="worried")
        # hero
        jk = prog(t, jp, jp + 0.6)
        hx = lerp(820, px + 60, ease_in(jk)) if t > jp else 820
        hy = GY - 220 * math.sin(math.pi * min(1, jk)) if t > jp else GY
        hp = hero_pose(hx, hy, t, f=-1, eyes="wide" if t < jp else "squeeze", mouth="o" if t < jp else "scream",
                       brows="up" if t < jp else "worried", arm_b=95 if t < jp else 160, elb_b=10, arm_a=40 if t < jp else 160)
        if t > jp:
            hp = hp.but(lean=35, hip_a=-40, hip_b=40, knee_a=60, knee_b=20)
        for f_, p, who in ((WET_MAX, mp, "max"), (HERO, hp, "hero")):
            cx.save()
            if suck > 0:
                # pulled toward the portal centre, shrinking + spinning
                jx, jy = p.x, p.y - 200
                cx.translate(lerp(jx, px, suck), lerp(jy, py, suck))
                cx.rotate(suck * 6)
                cx.scale(1 - 0.95 * suck, 1 - 0.95 * suck)
                cx.translate(-jx, -jy)
            robed(who == "hero")
            J = fig(cx, self, cam if suck == 0 else None, f_, p, who if suck == 0 else None)
            robed(False)
            if who == "hero":
                hJ = J
            if who == "hero" and t < self.mt("press") + 0.3:
                P.watch(cx, J["hand_b"][0], J["hand_b"][1] - 30, 0.45, 0, display="0:01", lcd_glow=1.0, label=False)
            cx.restore()
        if t > gb and suck == 0:
            line(cx, [(mx - 120, GY - 330), (hJ["neck"][0] + 20, hJ["neck"][1])], hexc("#2257B5"), 9)
        end(cx)
        if t > sk + 0.3:
            flash(cx, ease_in(prog(t, sk + 0.3, sk + 0.45)))


class S10Black(Shot):
    scene = "s10"
    music = None
    amb = None

    def plan(self, P):
        P.wait(1.0)

    def draw(self, cx, t):
        black(cx)


class S10Desert(Shot):
    scene = "s10"
    music = "egypt"
    music_gain = 0.35
    amb = "desert"

    def plan(self, P):
        P.mark("land1", 0.35)
        P.sfx("thud", t=0.35, vol=0.8)
        P.mark("land2", 0.85)
        P.sfx("thud", t=0.85, vol=0.9)
        P.sfx("clank", t=0.9, vol=0.5)
        P.wait(2.4)
        P.mark("turn", 1.6)
        P.say("s10_13", gap=0.35)
        P.say("s10_14", gap=0.5)
        a = P.say("s10_15", gap=0.7)
        P.mark("look", a)
        b = P.say("s10_16", gap=0.6)
        c = P.say("s10_17", gap=0.5)
        P.sfx("dun", t=c + P.voice.dur("s10_17") + 0.1, vol=0.5)

    def draw(self, cx, t):
        lk = self.mt("look")
        cam = cam_kf(t, [(0, (960, 600, 1.2)), (lk, (960, 600, 1.2)), (lk + 0.6, (1000, GY - 280, 1.9))])
        S.desert(cx, cam, t)
        world(cx, cam)
        l1, l2 = self.mt("land1"), self.mt("land2")
        # Maximus drops in, sits up, looks around
        if t < l2:
            k = ease_in(prog(t, 0.3, l2))
            mp = max_pose(1150, lerp(-300, GY, k), t, f=-1, eyes="spiral", mouth="scream", brows="worried",
                          arm_a=160, arm_b=150)
        else:
            look = pick(t - l2, [(0, (-1, 0)), (0.9, (1, 0)), (1.8, (0, -0.4)), (2.8, (-1, 0))])
            mp = max_pose(1150, GY, t, f=-1, eyes="wide", mouth="o", brows="up", look=look,
                          hip_a=80, knee_a=0, hip_b=85, knee_b=0, bob=110, lean=-10,
                          arm_a=60, arm_b=60, elb_a=20, elb_b=20)
            if t > lk:
                mp = mp.but(look=(-1, 0), mouth="o", eyes="open", brows="up")
        MJ = fig(cx, self, cam, WET_MAX, mp, "max")
        if t > l2:
            P.motion_puffs(cx, 1150, GY, t - l2, 4, 1 - prog(t, l2, l2 + 1))
            P.exclaim(cx, MJ["head"][0] + 70, MJ["head"][1] - 80, 0.9, pulse(t, l2 + 0.5, l2 + 2.5), mark="?")
        # hero: lands face-down, gets up, slowly turns toward Maximus
        if t < l1:
            k = ease_in(prog(t, 0.0, l1))
            hp = hero_pose(820, lerp(-300, GY, k), t, f=1, eyes="squeeze", mouth="scream", arm_a=160, arm_b=160)
        else:
            turn = win(t, lk - 0.5, lk + 0.6)
            hp = breathe(hero_pose(820, GY, t, f=1, view="side" if turn > 0.5 else "front",
                                   eyes="open" if turn < 0.5 else "half", mouth="flat", brows="flat",
                                   look=(lerp(0, 1, turn), 0), blink=turn < 0.5), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        end(cx)


class S10NextStop(Shot):
    scene = "s10"
    music = "egypt"
    amb = "desert"

    def plan(self, P):
        P.sfx("beep2", t=0.2, vol=0.5)
        P.accent("NEXT STOP:\n[ANCIENT EGYPT]", t=0.35, dur=2.3, size=92, pos=(W / 2, 200))
        P.wait(2.8)

    def draw(self, cx, t):
        S.desert(cx, Cam(960, 600, 1.2), t)
        tint(cx, (0.1, 0.05, 0.0), 0.35)
        P.watch(cx, W / 2, H / 2 + 120, 3.2, 0.0, display="EGYPT", lcd_glow=0.5 + 0.5 * (math.sin(t * 8) > 0))


class S10Run(Shot):
    scene = "s10"
    music = "egypt"
    amb = "desert"

    def plan(self, P):
        P.wait(0.3)
        P.sfx("dun", t=0.2, vol=0.4)
        P.mark("run", 0.9)
        P.sfx("whoosh", t=0.9, vol=0.7)
        P.wait(1.2)
        P.say("s10_18", gap=0.5)
        self.tail = 2.6
        for k in range(12):
            P.sfx("step", t=1.0 + k * 0.22, vol=0.3)

    def draw(self, cx, t):
        rn = self.mt("run")
        cam = cam_kf(t, [(0, (1000, 650, 1.5)), (rn, (1000, 650, 1.5)), (rn + 1.0, (960, 600, 1.0))])
        S.desert(cx, cam, t)
        world(cx, cam)
        if t < rn:
            reach = win(t, 0.2, 0.6)
            mp = breathe(max_pose(1150, GY, t, f=-1, eyes="angry", brows="angry", mouth="yell",
                                  arm_b=lerp(20, 95, reach), elb_b=-10, lean=15 * reach), t)
            fig(cx, self, cam, WET_MAX, mp, "max")
            P.anger_mark(cx, 1220, GY - 520, 1.3, reach)
            hp = hero_pose(820, GY, t, f=1, eyes="wide", mouth="teeth", brows="worried", sweat=1,
                           lean=-10 * reach)
            fig(cx, self, cam, HERO, hp, "hero")
        else:
            k = t - rn
            hx = 820 - 520 * k
            mx = 1150 - 470 * max(0, k - 0.35)
            fig(cx, self, cam, WET_MAX, run(max_pose(mx, GY, t, f=-1, eyes="angry", brows="angry", mouth="yell"),
                                            t, 2.1, 0.9))
            fig(cx, self, cam, HERO, run(hero_pose(hx, GY, t, f=-1, eyes="wide", mouth="scream", brows="worried",
                                                   sweat=1), t, 2.6, 1.0, flail=True))
            P.motion_puffs(cx, hx + 30, GY, t, 3, 0.8)
        end(cx)
        end_k = prog(t, self.dur - 1.2, self.dur)
        if end_k > 0:
            tint(cx, (0, 0, 0), smooth(end_k))


def scenes():
    return [S8Arrive(), S8Inventory(), S8News(), S8Ritual(), S8Awkward(),
            S9Grab(), S9Helmet(), S9Chase(), S9Shoe(), S9Wrist(),
            S10Corner(), S10Countdown(), S10Portal(), S10Black(), S10Desert(), S10NextStop(), S10Run()]

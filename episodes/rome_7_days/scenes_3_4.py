"""Scene 3 (Day 2: trying to eat) and Scene 4 (Day 3: inventing disappointment)."""
from .common import *  # noqa

STALL_X = 410   # Lucia's bread stall centre (MARKET_STALLS[2])


def lucia_stall(cx, t, sh, cam, lp, goods=True):
    """Lucia behind her bread counter."""
    J = fig(cx, sh, cam, LUCIA, lp, "lucia")
    S.counter(cx, STALL_X, 520, GROUND - 85)
    if goods:
        for j in range(3):
            P.round_loaf(cx, STALL_X - 200 + j * 70, GROUND - 105 - (j % 2) * 8, 1.0)
    return J


# =============================================================== SCENE 3
class S3Walk(Shot):
    scene = "s3"
    trans_in = ("dip", 0.5)
    music = "market"
    amb = "market"

    def plan(self, P):
        P.accent("DAY 2", t=0.4, dur=1.7, size=120)
        P.sfx("growl", t=1.2, vol=0.8)
        P.wait(0.8)
        P.say("s3_01", gap=0.4)
        a = P.say("s3_02", gap=0.4)
        P.mark("palms", a)

    def draw(self, cx, t):
        hx = -300 + 175 * t
        cam = Cam(hx + 120, 650, 1.3)
        S.market(cx, cam, t)
        world(cx, cam)
        palms = self.mt("palms")
        for i, vx in enumerate([-700, -170, 1030, 1590]):
            reach = win(t, palms + i * 0.25, palms + i * 0.25 + 0.3) * (abs(hx - vx) < 650)
            p = breathe(Pose(x=vx, y=GROUND - 10, s=0.9, f=-1 if vx > hx else 1, t=t, blink_seed=i + 20,
                             mouth="smile", look=(-1 if vx > hx else 1, 0), arm_b=lerp(8, 82, reach),
                             elb_b=lerp(8, -20, reach)), t + i)
            roman(40 + i).draw(cx, p)
            S.counter(cx, vx, 300, GROUND - 120)
        growl = pulse(t, 1.2, 2.4)
        p = walk(hero_pose(hx, GY, t, eyes="open", mouth="wavy" if growl > 0.3 else "flat",
                           brows="worried", look=(1, 0.2)), t, 0.95, 0.8)
        J = fig(cx, self, cam, HERO, p, "hero")
        stomach_growl_lines(cx, J["hip"][0] + 10, J["hip"][1] - 50, t, growl)
        end(cx)


class S3ApplePay(Shot):
    scene = "s3"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s3_03", gap=0.35)
        P.sfx("beep", t=a + 0.9, vol=0.3)
        P.say("s3_04", gap=0.3)
        b = P.say("s3_05", gap=0.25)
        d = P.voice.dur("s3_05")
        P.mark("apple", b + d * 0.55)
        P.sfx("pop", t=b + d * 0.55 + 0.35, vol=0.6)
        c = P.say("s3_06", gap=0.4)
        P.accent("[APPLE] PAY", t=b + d * 0.75, dur=c + P.voice.dur("s3_06") - (b + d * 0.75), size=104,
                 pos=(W / 2 + 330, 190))
        P.mark("bite", c + P.voice.dur("s3_06") + 0.1)
        P.sfx("bite", t=c + P.voice.dur("s3_06") + 0.15, vol=0.8)
        P.wait(0.7)

    def draw(self, cx, t):
        cam = Cam(STALL_X - 40, 620, 1.75)
        S.market(cx, cam, t)
        world(cx, cam)
        a = self.mt("s3_03")
        g = self.mt("s3_04")
        ta = self.mt("apple")
        c = self.mt("s3_06")
        tb = self.mt("bite")
        give = win(t, ta - 0.4, ta + 0.35)
        lp = breathe(lucia_pose(STALL_X + 120, GROUND - 6, t, f=-1, look=(-1, 0.1)), t)
        if g <= t < ta - 0.4:
            lp = lp.but(brows="skeptic", eyes="open", tilt=8)
        lp = lp.but(arm_b=lerp(-6, 82, give) if t < ta + 0.6 else lerp(82, -6, win(t, ta + 0.6, ta + 1.0)),
                    elb_b=lerp(10, 0, give))
        LJ = lucia_stall(cx, t, self, cam, lp)
        if g + 0.5 <= t < ta - 0.4:
            P.exclaim(cx, LJ["head"][0] + 20, LJ["head"][1] - 80, 0.9, 1.0, mark="?")
        hx = STALL_X - 330
        if t < g:
            k = win(t, a + 0.2, a + 0.8)
            hp = hero_pose(hx, GY, t, f=1, eyes="open", mouth="grin", brows="up", look=(1, -0.2),
                           arm_b=lerp(-8, 85, k), elb_b=lerp(10, 0, k))
            J = fig(cx, self, cam, HERO, hp, "hero")
            P.phone(cx, J["hand_b"][0] + 10, J["hand_b"][1] - 6, 1.1, 1.57, screen="on")
        elif t < ta + 0.35:
            ph = (t - g) * 7
            hp = hero_pose(hx, GY, t, f=1, eyes="open", mouth="o", mouth_open=0.8, brows="up", look=(1, -0.3),
                           arm_b=80 + 40 * math.sin(ph), elb_b=30 * math.cos(ph), arm_a=60 + 25 * math.sin(ph + 1),
                           elb_a=40, bob=-3 * abs(math.sin(ph)))
            if t > ta - 0.4:
                hp = hp.but(arm_b=80, elb_b=0, mouth="flat", eyes="open")
            J = fig(cx, self, cam, HERO, hp, "hero")
            P.phone(cx, J["hand_a"][0], J["hand_a"][1] - 6, 1.1, 0.4, screen="on")
        else:
            look_cam = t > c
            hp = hero_pose(hx, GY, t, f=1, eyes="open", mouth="flat", brows="flat",
                           look=(0, 0.2) if look_cam else (0.4, 0.3), arm_b=70, elb_b=60, view="front" if look_cam else "side")
            if t > tb:
                hp = hp.but(arm_b=lerp(70, 125, win(t, tb - 0.3, tb)), mouth="chew", mouth_open=abs(math.sin(t * 9)))
            J = fig(cx, self, cam, HERO, hp, "hero")
        # the apple travelling from Lucia's hand into his
        if ta - 0.4 <= t:
            k = ease_io(prog(t, ta, ta + 0.35))
            ax = lerp(LJ["hand_b"][0], J["hand_b"][0], k)
            ay = lerp(LJ["hand_b"][1], J["hand_b"][1], k) - 30 * math.sin(math.pi * k)
            if t > tb:
                ax, ay = J["hand_b"]
            P.apple(cx, ax, ay - 14, 1.0)
            if t > tb:
                circle(cx, ax + 16, ay - 20, 10)
                fs(cx, hexc("#F6E7C0"), OUTLINE, 3)
        end(cx)


class S3Job(Shot):
    scene = "s3"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.2)
        P.say("s3_07", gap=0.35)
        a = P.say("s3_08", gap=0.35)
        P.mark("stack", a + 0.6)
        P.sfx("dishes", t=a + 0.7, vol=0.6)
        P.sfx("slide_up", t=a + 0.9, vol=0.3)
        b = P.say("s3_09", gap=0.5)
        P.sfx("ding", t=b + 0.4, vol=0.35)
        c = P.say("s3_10", gap=0.9)
        P.sfx("crickets", t=c + P.voice.dur("s3_10"), vol=0.2)

    def draw(self, cx, t):
        a = self.mt("s3_07")
        st = self.mt("stack")
        b = self.mt("s3_09")
        c = self.mt("s3_10")
        cam = cam_kf(t, [(0, (STALL_X + 120, 620, 2.0)), (st - 0.3, (STALL_X + 120, 620, 2.0)),
                         (st + 0.2, (STALL_X - 60, 610, 1.45))])
        S.market(cx, cam, t)
        world(cx, cam)
        point = win(t, st - 0.3, st)
        lp = breathe(lucia_pose(STALL_X + 120, GROUND - 6, t, f=-1, view="front" if t < st - 0.3 else "side",
                                arm_a=60 if t < st - 0.3 else 10, arm_b=60 if t < st - 0.3 else lerp(10, 95, point),
                                elb_a=-120 if t < st - 0.3 else 10, elb_b=-120 if t < st - 0.3 else 0,
                                look=(-1, 0)), t)
        lucia_stall(cx, t, self, cam, lp)
        if t >= st - 0.4:
            n = int(3 + 14 * ease_out(prog(t, st, st + 0.8)))
            dish_x = STALL_X - 270
            P.dish_stack(cx, dish_x, GY + 20, n, 1.1, wobble=0.6, t=t)
            hk = t >= b
            thumb = win(t, b, b + 0.3)
            hp = breathe(hero_pose(STALL_X - 430, GY, t, f=1 if not hk else -1, view="side" if not hk else "front",
                                   eyes="open" if t < c else "open", mouth="grin" if hk else "o",
                                   brows="up" if hk else "worried", look=(1, -0.6) if not hk else (0, 0),
                                   arm_b=lerp(-8, 110, thumb), elb_b=lerp(10, 50, thumb)), t)
            if t > c + 0.4:
                hp = hp.but(mouth="teeth", eyes="open", sweat=win(t, c + 0.4, c + 1.0))
            J = fig(cx, self, cam, HERO, hp, "hero")
            if thumb > 0.5:
                line(cx, [J["hand_b"], (J["hand_b"][0] + 4, J["hand_b"][1] - 22)], OUTLINE, 8)
        end(cx)


class S3Wash(Shot):
    scene = "s3"
    music = "market"
    amb = "market"

    def plan(self, P):
        P.wait(0.3)
        for k, tt in enumerate((0.6, 1.9, 3.1)):
            P.sfx("splash", t=tt, vol=0.55)
        P.sfx("dishes", t=1.4, vol=0.5)
        P.mark("boy", 2.0)
        P.wait(1.6)
        P.say("s3_11", gap=0.35)
        a = P.say("s3_12", gap=0.3)
        P.sfx("splash", t=a + 0.6, vol=0.7)
        P.sfx("laugh", t=a + 0.7, vol=0.25)
        P.say("s3_13", gap=0.5)

    def draw(self, cx, t):
        cam = Cam(900, 640, 1.6)
        S.market(cx, cam, t)
        world(cx, cam)
        tub_x = 900
        splash_times = [0.6, 1.9, 3.1, self.mt("s3_12") + 0.6]
        # boy peeking & laughing
        bt = self.mt("boy")
        bk = win(t, bt, bt + 0.5)
        laugh = t > bt + 0.6
        bp = boy_pose(lerp(1300, 1160, bk), GY, t, f=-1, eyes="happy" if laugh else "open", mouth="grin",
                      mouth_open=0.8 + 0.4 * abs(math.sin(t * 12)), look=(-1, 0))
        if laugh:
            bp = bp.but(lean=-10 + 8 * math.sin(t * 12), arm_b=70, elb_b=-30, arm_a=40, elb_a=80,
                        bob=-6 * abs(math.sin(t * 12)))
        fig(cx, self, cam, BOY, bp, "boy")
        # hero scrubbing
        scrub = math.sin(t * 14)
        wet = min(1.0, sum(1 for s in splash_times if t > s) / 3)
        hp = hero_pose(tub_x - 40, GY, t, f=1, eyes="squeeze" if any(0 < t - s < 0.5 for s in splash_times) else "open",
                       mouth="wavy", brows="worried", look=(0.6, 0.6), arm_b=60 + 15 * scrub, elb_b=30 + 20 * scrub,
                       arm_a=50 - 15 * scrub, elb_a=40, lean=10)
        J = fig(cx, self, cam, HERO, hp, "hero")
        P.wash_tub(cx, tub_x + 120, GY + 10, 1.0, t=t)
        P.plate(cx, J["hand_b"][0] + 10, J["hand_b"][1], 0.9, dirty=1 - wet * 0.8, rot=0.3 * scrub)
        for s in splash_times:
            P.water_splash(cx, tub_x + 120, GY - 80, t - s, 0.6, 0.9, seed=int(s * 10))
        if wet > 0:
            P.drips(cx, J["head"][0], J["head"][1] + 30, 80, t, int(4 * wet), 0.9)
        # a plate slips and flies out
        if 1.4 < t < 2.4:
            k = prog(t, 1.4, 2.4)
            P.plate(cx, tub_x + 120 + 300 * k, GY - 120 - 420 * k + 520 * k * k, 0.9, rot=k * 12)
        end(cx)


class S3Share(Shot):
    scene = "s3"
    music = "warm"
    amb = "market"

    def plan(self, P):
        P.wait(0.3)
        P.mark("break", 0.6)
        P.sfx("bite", t=0.6, vol=0.5)
        P.mark("give", 1.4)
        P.sfx("sparkle", t=1.6, vol=0.4)
        P.wait(1.6)
        P.say("s3_14", gap=0.6)
        P.mark("walk")
        P.wait(2.2)

    def draw(self, cx, t):
        cam = Cam(960, 650, 1.5)
        S.market(cx, cam, t)
        world(cx, cam)
        w = self.mt("walk")
        brk = win(t, 0.4, 0.7)
        give = win(t, 1.1, 1.5)
        hx = 860 + (0 if t < w else -150 * (t - w))
        if t < w:
            hp = breathe(hero_pose(hx, GY, t, f=1, eyes="happy" if t > 1.5 else "open", mouth="smile",
                                   look=(1, 0.4), arm_b=lerp(50, 80, give), elb_b=lerp(40, 0, give),
                                   arm_a=50, elb_a=40, blush=0.4), t)
        else:
            hp = walk(hero_pose(hx, GY, t, f=-1, eyes="open", mouth="smile"), t - w, 0.9, 0.8)
            hp = hp.but(arm_b=-30, elb_b=20 + 30 * math.sin(t * 6))
        J = fig(cx, self, cam, HERO, hp, "hero")
        if t < w:
            P.bread(cx, J["hand_a"][0], J["hand_a"][1] - 6, 0.75, 0.3, bite=brk > 0.5)
        bx = 1090
        bp = boy_pose(bx, GY, t, f=-1, eyes="open" if t < 1.5 else "happy", mouth="o" if t < 1.5 else "grin",
                      look=(-1, -0.3), arm_b=lerp(-6, 80, give) if t < w else 140 + 20 * math.sin(t * 9),
                      elb_b=0 if t < w else 20)
        BJ = fig(cx, self, cam, BOY, bp, "boy")
        if give > 0 and t < w:
            k = give
            px = lerp(J["hand_b"][0], BJ["hand_b"][0], k)
            py = lerp(J["hand_b"][1], BJ["hand_b"][1], k)
            P.bread(cx, px, py - 6, 0.45, 0)
        if t > 1.5 and t < w:
            P.sparkles(cx, BJ["head"][0], BJ["head"][1], t, 70, 5, 0.9)
        end(cx)


# =============================================================== SCENE 4
INGR_Y = GROUND - 150


def ingredients(cx, x, t):
    # cheese wedge
    cx.move_to(x - 160, INGR_Y)
    cx.line_to(x - 90, INGR_Y - 46)
    cx.line_to(x - 60, INGR_Y)
    cx.close_path()
    fs(cx, hexc("#F4D06F"), OUTLINE, 4)
    circle(cx, x - 92, INGR_Y - 14, 6)
    fs(cx, hexc("#E2B84E"), None, 0)
    # olive bowl
    ellipse(cx, x + 10, INGR_Y - 10, 44, 18)
    fs(cx, hexc("#C77B4E"), OUTLINE, 4)
    for k in range(5):
        circle(cx, x - 16 + k * 13, INGR_Y - 24 + (k % 2) * 4, 8)
        fs(cx, hexc("#2E3A2A"), OUTLINE, 2)
    # herbs
    for k in range(4):
        ellipse(cx, x + 100 + k * 12, INGR_Y - 18, 6, 18, -0.4 + k * 0.25)
        fs(cx, hexc("#6E9B5A"), OUTLINE, 2)
    # dough ball
    ellipse(cx, x + 220, INGR_Y - 18, 50, 24)
    fs(cx, hexc("#F3E3C3"), OUTLINE, 4)


class S4Idea(Shot):
    scene = "s4"
    trans_in = ("dip", 0.5)
    music = "quirky"
    amb = "bakery"

    def plan(self, P):
        P.accent("DAY 3", t=0.4, dur=1.7, size=120)
        P.wait(0.7)
        a = P.say("s4_01", gap=0.3)
        P.mark("lamp", a + P.voice.dur("s4_01") * 0.6)
        P.sfx("ding", t=a + P.voice.dur("s4_01") * 0.6, vol=0.6)
        P.say("s4_02", gap=0.25)
        P.say("s4_03", gap=0.35)
        b = P.say("s4_04", gap=0.25)
        P.mark("dream", b + 0.3)
        P.sfx("sparkle", t=b + 0.3, vol=0.4)
        P.say("s4_05", gap=0.35)
        c = P.say("s4_06", gap=0.3)
        P.sfx("scratch", t=c - 0.05, vol=0.8)
        d = P.say("s4_07", gap=0.5)
        P.accent("NO [TOMATOES.]", t=d + 0.1, dur=P.voice.dur("s4_07") + 0.8, size=108, pos=(W / 2, 180))

    def draw(self, cx, t):
        lamp = self.mt("lamp")
        dream = self.mt("dream")
        c = self.mt("s4_06")
        d = self.mt("s4_07")
        cam = cam_kf(t, [(0, (960, 640, 1.45)), (d - 0.2, (960, 640, 1.45)), (d + 0.2, (1060, 680, 1.7))])
        S.bakery(cx, cam, t)
        world(cx, cam)
        smug = self.mt("s4_02") <= t < c
        search = t >= d
        hx = 800
        if search:
            ph = (t - d) * 3
            hp = hero_pose(hx + 150, GY, t, f=1, eyes="wide", mouth="o", brows="worried", lean=30,
                           look=(0.6, 1), arm_b=110 + 30 * math.sin(ph * 4), elb_b=40, arm_a=90, elb_a=40, sweat=1)
        elif smug:
            hp = breathe(hero_pose(hx, GY, t, view="front", eyes="half", mouth="smirk", brows="up",
                                   arm_a=60, arm_b=60, elb_a=-120, elb_b=-120, tilt=-6), t)
        else:
            hp = breathe(hero_pose(hx, GY, t, f=1, eyes="open" if t < lamp else "wide", mouth="smile" if t < lamp else "grin",
                                   look=(0.6, 0.6) if t < lamp else (0, -1), arm_b=40, elb_b=60), t)
        J = fig(cx, self, cam, HERO, hp, "hero")
        S.counter(cx, 1200, 620, GROUND - 120)
        ingredients(cx, 1150, t)
        if search:
            # empty crate he is digging through
            P.crate(cx, 1300, GROUND - 120, 150, 80)
            for k in range(3):
                kk = ((t - d) * 2 + k * 0.33) % 1
                P.round_loaf(cx, 1300 + 120 * kk - 40 * k, GROUND - 200 - 200 * kk + 260 * kk * kk, 0.6)
        lamp_idea(cx, J["head"][0] + 10, J["head"][1] - 130, 1.0, win(t, lamp, lamp + 0.2) * (1 - win(t, dream, dream + 0.2)))
        # thought bubble: coins + pizza
        ba = win(t, dream, dream + 0.3) * (1 - win(t, c - 0.05, c + 0.1))
        if ba > 0:
            bx, by = J["head"][0] + 300, J["head"][1] - 220
            thought_bubble(cx, bx, by, 420, 230, ba, tail_to=(J["head"][0] + 40, J["head"][1] - 40))
            cx.save()
            cx.push_group()
            coins(cx, bx - 90, by + 50, 1.2)
            # modern pizza slice (with tomato!) in the dream
            cx.move_to(bx + 40, by - 60)
            cx.line_to(bx + 160, by - 60)
            cx.line_to(bx + 100, by + 70)
            cx.close_path()
            fs(cx, hexc("#F3C969"), OUTLINE, 4)
            line(cx, [(bx + 40, by - 60), (bx + 160, by - 60)], hexc("#C98A45"), 14)
            for k, (px, py) in enumerate([(bx + 80, by - 30), (bx + 120, by - 30), (bx + 100, by + 10)]):
                circle(cx, px, py, 11)
                fs(cx, hexc("#D93A3A"), OUTLINE, 2.5)
            cx.pop_group_to_source()
            cx.paint_with_alpha(ba)
            cx.restore()
        end(cx)


def sad_flatbread(cx, x, y, s, sad, bite=0.0, t=0.0):
    """Flatbread whose olive smiley droops into a frown as `sad` goes 0->1."""
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 0, 92, 30)
    fs(cx, hexc("#E3B46A"), OUTLINE, 5)
    ellipse(cx, 0, -2, 78, 23)
    fs(cx, hexc("#F6E7B0"), None, 0)
    for ox in (-26, 26):
        ellipse(cx, ox, -8 + 3 * sad, 9, 6 - 2 * sad)
        fs(cx, hexc("#2E3A2A"), OUTLINE, 2.5)
    for k in range(5):
        a = math.pi * (0.15 + k * 0.175)
        yy = math.sin(a) * 12
        yy = lerp(2 + yy, 14 - yy, sad)
        ellipse(cx, math.cos(a) * 40, yy, 7, 5)
        fs(cx, hexc("#2E3A2A"), OUTLINE, 2.5)
    if bite > 0:
        cx.set_operator(cairo.OPERATOR_CLEAR)
        circle(cx, 92, -4, 24 * bite)
        cx.fill()
        cx.set_operator(cairo.OPERATOR_OVER)
    cx.restore()


class S4Present(Shot):
    scene = "s4"
    music = "quirky"
    amb = "bakery"

    def plan(self, P):
        P.sfx("tada", t=0.25, vol=0.55)
        P.wait(0.4)
        P.say("s4_08", gap=0.4)
        P.mark("close")
        P.say("s4_09", gap=0.45)
        a = P.say("s4_10", gap=0.7)
        P.sfx("slide_down", t=a + 0.2, vol=0.4)

    def draw(self, cx, t):
        cl = self.mt("close")
        if t < cl:
            cam = Cam(960, 640, 1.45)
            S.bakery(cx, cam, t)
            world(cx, cam)
            k = win(t, 0.0, 0.4)
            hp = breathe(hero_pose(840, GY, t, f=1, eyes="happy", mouth="grin", brows="up", arm_b=lerp(40, 95, k),
                                   elb_b=lerp(40, -10, k), arm_a=lerp(20, 95, k), elb_a=-10, lean=-6), t)
            J = fig(cx, self, cam, HERO, hp, "hero")
            S.counter(cx, 1200, 620, GROUND - 120)
            sad_flatbread(cx, J["hand_b"][0] + 70, J["hand_b"][1] - 20, 1.0, 0.0)
            P.sparkles(cx, J["hand_b"][0] + 70, J["hand_b"][1] - 30, t, 90, 6, 0.9)
            end(cx)
        else:
            insert_bg(cx, "#F2D2A4", "#D9A879")
            sad = win(t, self.mt("s4_10") + 0.1, self.mt("s4_10") + 1.2)
            S_ = 6.0 + 0.4 * prog(t, cl, cl + 4)
            cx.save()
            ellipse(cx, W / 2, H / 2 + 190, 640, 120)
            fs(cx, hexc("#C77B4E"), OUTLINE, 6)
            cx.restore()
            sad_flatbread(cx, W / 2, H / 2 + 150, S_, sad)


class S4Bite(Shot):
    scene = "s4"
    music = None
    amb = "bakery"

    def plan(self, P):
        P.wait(0.3)
        a = P.say("s4_11", gap=0.4)
        P.mark("bite", a + 0.7)
        P.sfx("bite", t=a + 0.75, vol=0.9)
        P.sfx("chew", t=a + 1.1, vol=0.5)
        P.sfx("crickets", t=a + P.voice.dur("s4_11"), vol=0.3)
        P.wait(1.3)
        b = P.say("s4_12", gap=0.4)
        P.mark("drop", b + 0.5)
        P.sfx("thud", t=b + 0.7, vol=0.4)
        P.sfx("wah", t=b + P.voice.dur("s4_12") * 0.5, vol=0.55)
        P.wait(1.6)

    def draw(self, cx, t):
        tb = self.mt("bite")
        dr = self.mt("drop")
        cam = cam_kf(t, [(0, (1000, 650, 1.6)), (tb + 1.5, (1080, 600, 2.2))])
        S.bakery(cx, cam, t)
        world(cx, cam)
        chewing = tb < t < tb + 2.0
        stare = t > tb + 0.8
        lift = win(t, 0.3, tb) * (1 - win(t, dr, dr + 0.4))
        lp = breathe(lucia_pose(1180, GY, t, f=-1, eyes="tiny" if stare else "half", mouth="chew" if chewing else "flat",
                                mouth_open=abs(math.sin(t * 5)) * (1 - prog(t, tb, tb + 2.0)), look=(-1, 0),
                                arm_b=lerp(-6, 105, lift), elb_b=lerp(10, 60, lift), blink=not stare), t)
        LJ = fig(cx, self, cam, LUCIA, lp, "lucia")
        if lift > 0.05:
            sad_flatbread(cx, LJ["hand_b"][0] - 30, LJ["hand_b"][1] - 10, 0.55, 1.0, bite=1.0 if t > tb else 0)
        elif t > dr:
            sad_flatbread(cx, 1040, GROUND - 140, 0.55, 1.0, bite=1.0)
        hp = breathe(hero_pose(800, GY, t, f=1, eyes="open" if t < tb + 0.8 else "wide", mouth="grin" if t < tb else "teeth",
                               brows="up" if t < tb else "worried", look=(1, -0.3), sweat=win(t, tb + 1, tb + 2)), t)
        fig(cx, self, cam, HERO, hp, "hero")
        S.counter(cx, 1000, 260, GROUND - 120)
        end(cx)


class S4Maximus(Shot):
    scene = "s4"
    music = "suspense"
    amb = "bakery"

    def plan(self, P):
        P.wait(0.2)
        a = P.say("s4_13", gap=0.2)
        P.mark("enter", a + 0.3)
        P.sfx("crash_wood", t=a + 0.3, vol=0.5)
        P.sfx("dun", t=a + 0.4, vol=0.6)
        P.dlg("d_max_found", "max", "THAT'S HIM!\nThe [wizard!]", gap=0.3)
        b = P.say("s4_14", gap=0.4)
        P.accent("[MAXIMUS]", t=b + 0.2, dur=P.voice.dur("s4_14") + 0.6, size=124, pos=(W / 2 - 300, 190))
        c = P.say("s4_15", gap=0.5)
        P.mark("crowd", c + 0.2)
        P.sfx("murmur", t=c + 0.2, vol=0.5)

    def draw(self, cx, t):
        en = self.mt("enter")
        dl = self.m["d_max_found"]
        cr = self.mt("crowd")
        cam = cam_kf(t, [(0, (1150, 630, 1.25)), (cr, (1150, 630, 1.25)), (cr + 0.5, (1250, 600, 1.15))])
        S.bakery(cx, cam, t)
        world(cx, cam)
        # curious Romans gather in the window and doorway
        if t > cr:
            for i in range(5):
                k = win(t, cr + i * 0.25, cr + i * 0.25 + 0.4)
                if k <= 0:
                    continue
                f = roman(60 + i)
                x = 1520 + i * 75 - (i // 3) * 200
                y = (GROUND - 240 if i < 3 else GY) + (1 - k) * 80
                p = Pose(x=x, y=y, s=0.75, f=-1, t=t, blink_seed=i, eyes="wide", mouth="o", brows="up",
                         look=(-1, 0), arm_b=100 if i % 2 else 10, elb_b=-10)
                if i < 3:
                    cx.save()
                    cx.move_to(1480, 560)
                    cx.line_to(1480, 300)
                    cx.arc(1600, 300, 120, math.pi, 2 * math.pi)
                    cx.line_to(1720, 560)
                    cx.close_path()
                    cx.clip()
                    f.draw(cx, p)
                    cx.restore()
                else:
                    f.draw(cx, p)
        k = ease_out(prog(t, en, en + 0.6))
        mx = lerp(2050, 1420, k)
        talking = dl[0] <= t <= dl[1]
        mp = max_pose(mx, GY, t, f=-1, eyes="wide" if t > en + 0.6 else "angry", brows="up", mouth="grin",
                      arm_b=95 if t > en + 0.5 else 30, elb_b=-5, look=(-1, 0))
        if k < 1:
            mp = run(mp, t, 1.6, 0.7)
        if talking:
            mp = talk(mp.but(mouth="yell"), t)
        fig(cx, self, cam, MAXIMUS, breathe(mp, t), "max")
        hp = breathe(hero_pose(900, GY, t, f=1, eyes="wide" if t > en else "open", mouth="o" if t > en else "flat",
                               brows="worried", look=(1, -0.3), sweat=win(t, en, en + 0.5),
                               lean=-8 * win(t, en, en + 0.3)), t)
        fig(cx, self, cam, HERO, hp, "hero")
        end(cx)


class S4Great(Shot):
    scene = "s4"
    music = "suspense"
    amb = "bakery"

    def plan(self, P):
        P.wait(0.25)
        P.say("s4_16", gap=0.6)

    def draw(self, cx, t):
        cam = Cam(960, GY - 250, 2.7)
        S.bakery(cx, cam, t)
        world(cx, cam)
        fig(cx, self, cam, HERO, hero_pose(960, GY, t, view="front", eyes="half", mouth="flat", brows="flat",
                                           blink=False), "hero")
        end(cx)


class S4Worship(Shot):
    scene = "s4"
    music = "quirky"
    music_gain = 0.8
    amb = "bakery"

    def plan(self, P):
        P.wait(0.2)
        P.say("s4_17", gap=0.3)
        a = P.say("s4_18", gap=0.8)
        P.mark("bow", a + 0.3)
        P.sfx("ooh", t=a + 0.4, vol=0.4)

    def draw(self, cx, t):
        bow = self.mt("bow")
        cam = Cam(1000, 640, 1.3)
        S.bakery(cx, cam, t)
        world(cx, cam)
        hp = breathe(hero_pose(760, GY, t, view="front", eyes="open", mouth="teeth", brows="worried", sweat=1.0,
                               look=(1, 0.3)), t)
        fig(cx, self, cam, HERO, hp, "hero")
        k = win(t, bow, bow + 0.6)
        for i in range(4):
            x = 1020 + i * 170
            p = Pose(x=x, y=GY + 10, s=0.8, f=-1, t=t, blink_seed=i + 30, eyes="closed" if k > 0.5 else "wide",
                     mouth="smile", lean=lerp(0, 55, k), hip_a=lerp(-4, 60, k), knee_a=lerp(4, 110, k),
                     hip_b=lerp(4, 70, k), knee_b=lerp(4, 120, k), bob=lerp(0, 40, k),
                     arm_a=lerp(10, 120, k), arm_b=lerp(10, 110, k), elb_a=10, elb_b=10, look=(-1, 0))
            J = roman(60 + i).draw(cx, p)
            if i == 0:
                rect_drawing(cx, J["hand_b"][0] - 10, J["hand_b"][1] - 20, 0.9)
            elif i == 2:
                P.round_loaf(cx, J["hand_b"][0] - 10, J["hand_b"][1] - 10, 0.9)
            elif i == 3:
                P.apple(cx, J["hand_b"][0] - 10, J["hand_b"][1] - 16, 0.9)
        end(cx)


def scenes():
    return [S3Walk(), S3ApplePay(), S3Job(), S3Wash(), S3Share(),
            S4Idea(), S4Present(), S4Bite(), S4Maximus(), S4Great(), S4Worship()]

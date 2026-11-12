"""Shots for "I Complained About Mom's Cooking. Big Mistake." (vertical Short).

Each shot plans its narration/dialogue against the real voice clips (P.say / P.dlg), places SFX,
on-screen accent text ("jn_accent" cues, drawn by episode.py) and music sections ("music" cues).
"""
from .common import *  # noqa

GY = 1530             # ground line in the Stone Age shots (feet)
HS = 1.5              # hero scale for wide shots


def accent(P, text, t, dur, y=330, size=104):
    P.cues.append({"type": "jn_accent", "text": text, "t0": t, "t1": t + dur, "y": y, "size": size})


def music(P, name, t, gain=1.0, fade=0.25):
    """Start a music section (name=None stops the music) at shot-local time t."""
    P.cues.append({"type": "music", "name": name, "t0": t, "gain": gain, "fade": fade})


def say_at(P, lid, t):
    """Place a line at shot-local time t without moving the planner cursor."""
    keep = P.t
    P.t = t
    s = P.say(lid, gap=0.0)
    P.t = keep
    return s


def hero_spin(cx, center, ang, k, draw):
    cx.save()
    cx.translate(*center)
    cx.rotate(ang)
    cx.scale(k, k)
    cx.translate(-center[0], -center[1])
    draw()
    cx.restore()


# ====================================================================== SCENE 1 — hook
class S1Room(Shot):
    """Gaming -> Mom brings dinner -> eye roll + thumbs down -> time-quake -> sucked into the past."""
    scene = "s1"
    HX = 500

    def plan(self, P):
        music(P, "room", 0.0, 0.8)
        P.wait(0.10)
        P.say("n1a", gap=0.20)
        P.say("n1b", gap=0.28)
        tc = P.say("n1c", gap=0.0)
        accent(P, "BIG [MISTAKE.]", tc - 0.02, 1.55)
        self.m["quake"] = (tc - 0.25, tc - 0.25)
        self.m["open"] = (tc + 0.05, tc + 0.05)
        self.m["suck"] = (tc + 0.75, tc + 0.75)
        P.t = tc + 1.55
        music(P, None, tc - 0.3, fade=0.12)
        # sound
        for k, tt in enumerate([0.05, 0.22, 0.31, 0.52, 0.66, 0.83, 1.05, 1.2, 1.38]):
            P.sfx("game", t=tt, vol=0.22, seed=k)
        P.sfx("step", t=0.28, vol=0.3)
        P.sfx("plate", t=0.45, vol=0.35)
        P.sfx("eyeroll", t=1.12, vol=0.5)
        P.sfx("raspberry", t=1.78, vol=0.45)
        P.sfx("rumble", t=tc - 0.3, vol=0.55)
        P.sfx("crack", t=tc - 0.2, vol=0.6)
        P.sfx("portal", t=tc + 0.05, vol=0.55)
        P.sfx("suck", t=tc + 0.75, vol=0.7)
        P.sfx("whoosh", t=tc + 1.1, vol=0.7)

    def draw(self, cx, t):
        tq, to, ts = self.mt("quake"), self.mt("open"), self.mt("suck")
        quake = prog(t, tq, tq + 0.3)
        sx, sy = shake(t, 16 * quake + 10 * prog(t, to, ts), 22)
        z = kf(t, [(0, 1.32), (1.0, 1.32), (1.6, 1.4), (tq, 1.4), (ts + 0.6, 1.46)])
        cam = Cam(560 + sx, 1160 + sy, z)
        bedroom(cx, cam, t, tv=1.0, crack=prog(t, tq, tq + 0.45), glow=prog(t, to, ts))
        world(cx, cam)
        # ---- Mom in the doorway with the casserole
        m_in = ease_out(prog(t, 0.25, 0.6))
        if t >= 0.25:
            mx = lerp(-60, 255, m_in)
            scared = t >= tq + 0.1
            meh = t >= 2.0 and not scared
            mp = mom_pose(mx, FLOOR, t, s=1.45, f=1, arm_a=74, elb_a=26, arm_b=80, elb_b=18,
                          mouth="o" if scared else ("flat" if meh else "smile"),
                          eyes="wide" if scared else ("half" if meh else "open"),
                          brows="worried" if scared else ("flat" if meh else "up"))
            if not scared:
                mp = breathe(mp, t)
                if t < 0.6:
                    mp = walk(mp, t, 2.2, 0.8, arms=False)
            else:
                mp = mp.but(lean=-8, arm_a=110, elb_a=20)
            J = fig(cx, self, cam, MOM, mp, "mom")
            hx, hy = J["hand_b"]
            casserole_plate(cx, hx + 20, hy - 6, 1.05, t, steam_a=1.0 if not scared else 0.0)
        # ---- beanbag + hero
        bx, by = self.HX + 10, FLOOR
        squash = 0.0
        beanbag(cx, bx, by + 6, 1.45, squash)
        lift = ease_in(prog(t, ts - 0.35, ts + 0.5))
        spin = ease_in(prog(t, ts - 0.2, ts + 0.6)) * 9
        shrink = 1 - 0.95 * ease_in(prog(t, ts, ts + 0.6))
        # vortex (behind the hero, over the room)
        vr = 430 * ease_out(prog(t, to, to + 0.5)) * (1 + 0.2 * prog(t, ts, ts + 0.8))
        vc = (self.HX, 1180)
        if vr > 2:
            end(cx)
            sc = cam.to_screen(*vc)
            vortex(cx, sc[0], sc[1], vr * cam.zoom, t, 1.0)
            world(cx, cam)
        hp = self.hero_pose(t)
        hy0 = hp.y
        hp = hp.but(y=lerp(hy0, vc[1] + 160, lift), x=lerp(hp.x, vc[0], lift))

        def draw_hero():
            J = fig(cx, self, cam, HERO, hp, "hero")
            self.props(cx, t, J, hp)
        if t < ts + 0.62:
            hero_spin(cx, (hp.x, hp.y - 160), spin, shrink, draw_hero)
        end(cx)
        # final flash into the past
        flash(cx, 0.9 * prog(t, ts + 0.45, ts + 0.75), (1.0, 0.85, 0.6))

    def hero_pose(self, t):
        tq = self.mt("quake")
        p = hero_pose(self.HX, FLOOR - 70, t, s=HS, f=1, eyes="half", brows="flat", mouth="flat",
                      look=(1, 0.1), arm_a=44, elb_a=72, arm_b=56, elb_b=60, lean=6)
        p = sit(p, seat_h=60)
        if t < 0.9:   # button mashing, glued to the TV
            j = math.sin(t * 40) * 4
            p = p.but(arm_a=44 + j, arm_b=56 - j, eyes="open", brows="angry", look=(1, 0.1))
        elif t < 1.12:   # side-eye at Mom
            p = p.but(look=(-1, 0), eyes="open", brows="skeptic", tilt=-4)
        elif t < 1.72:   # eye roll
            a = (t - 1.12) / 0.6 * 2 * math.pi
            p = p.but(look=(-math.cos(a) * 0.9, -abs(math.sin(a)) * 0.9 - 0.2), eyes="open", brows="flat",
                      tilt=-6 * math.sin(a / 2), mouth="flat")
        elif t < 2.55:   # thumbs down + "bleh"
            k = ease_out(prog(t, 1.72, 1.9))
            p = p.but(arm_b=lerp(56, -78, k), elb_b=lerp(60, -6, k), eyes="squeeze", brows="angry",
                      mouth="wavy", look=(-1, 0), lean=4, tilt=-8)
        elif t < tq:     # "I did." smug turn back to the game
            p = p.but(eyes="half", brows="skeptic", mouth="smirk", look=(1, 0))
        else:            # panic
            p = p.but(eyes="wide", brows="worried", mouth="scream", look=(-0.3, -0.6), sweat=1.0,
                      arm_a=150 + 20 * math.sin(t * 30), elb_a=20, arm_b=-150 - 20 * math.sin(t * 30 + 1),
                      elb_b=20, lean=-6, mouth_open=1.1)
        if t >= tq:
            p = p.but(bob=p.bob - 30 * abs(math.sin(t * 18)))
        return p

    def props(self, cx, t, J, p):
        tq = self.mt("quake")
        if t < tq:
            hx = (J["hand_a"][0] + J["hand_b"][0]) / 2 if t < 1.72 else J["hand_a"][0] + 8
            hy = (J["hand_a"][1] + J["hand_b"][1]) / 2 if t < 1.72 else J["hand_a"][1]
            controller(cx, hx + 4, hy, 0.62 * p.s, 0.1)
            if 1.72 <= t < 2.55:
                thumb(cx, J["hand_b"][0], J["hand_b"][1] + 6, p.s * 0.9, True)
                mx = J["head"][0] - 0.22 * J["head_rad"] * 0.0 + 0.22 * J["head_rad"]
                tongue(cx, mx + 6, J["head"][1] + 0.5 * J["head_rad"], p.s * 0.9)
        else:
            controller(cx, J["hand_a"][0] + 160 * prog(t, tq, tq + 0.6), J["hand_a"][1] - 120 * prog(t, tq, tq + 0.6),
                       0.62 * p.s, t * 8)


# ====================================================================== SCENE 2 — Stone Age
class S2Land(Shot):
    """Crash-landing 10,000 years ago; spots a mammoth; thinks it's dinner."""
    scene = "s2"
    trans_in = ("white", 0.3)

    def plan(self, P):
        music(P, "stone", 0.25, 0.9)
        P.sfx("thud", t=0.42, vol=0.8)
        P.sfx("poof", t=0.45, vol=0.4)
        P.wait(0.30)
        s = P.say("n2", gap=0.0)
        accent(P, "[10,000] YEARS AGO", 0.35, 1.9)
        self.m["spot"] = (s + 1.95, s + 1.95)
        self.m["fork"] = (s + 2.75, s + 2.75)
        P.sfx("pop", t=s + 1.95, vol=0.5)
        P.sfx("ding", t=s + 2.35, vol=0.35)
        P.sfx("swish", t=s + 2.75, vol=0.5)
        P.sfx("slurp", t=s + 3.25, vol=0.35)
        P.t = s + P.voice.dur("n2") + 0.55

    def draw(self, cx, t):
        ts, tf = self.mt("spot"), self.mt("fork")
        z = kf(t, [(0, 1.6), (ts - 0.1, 1.6), (ts + 0.55, 1.22)], ease_io)
        cxw = kf(t, [(0, 330), (ts - 0.1, 330), (ts + 0.55, 540)], ease_io)
        cyw = kf(t, [(0, 1260), (ts - 0.1, 1260), (ts + 0.55, 1180)], ease_io)
        land = 0.45
        sh = shake(t, 14 * (1 - prog(t, land, land + 0.35)) * (t > land), 30)
        cam = Cam(cxw + sh[0], cyw + sh[1], z)
        stoneage(cx, cam, t)
        world(cx, cam)
        # mammoth, grazing peacefully
        mammoth(cx, 820, GY, 0.95, f=-1, t=t, eye="calm", head_dip=40, chew=0.5 + 0.5 * math.sin(t * 8))
        # hero falls from the sky
        x = 280
        fall = prog(t, 0.0, land)
        if t < land:
            y = lerp(GY - 1500, GY, ease_in(fall))
            p = hero_pose(x, y, t, s=HS, eyes="wide", mouth="scream", brows="worried",
                          arm_a=160, arm_b=-160, elb_a=20, elb_b=20, hip_a=-30, hip_b=40, knee_a=40, knee_b=60)
            hero_spin(cx, (x, y - 180), t * 9, 1.0, lambda: fig(cx, self, cam, HERO, p, "hero"))
        else:
            sq = kf(t, [(land, 0.62), (land + 0.12, 1.12), (land + 0.25, 0.96), (land + 0.36, 1.0)])
            p = hero_pose(x, GY, t, s=HS, squash=sq, f=1)
            if t < ts:
                # dazed, looks around
                lk = kf(t, [(land + 0.4, (0.0, 0.0)), (land + 0.8, (-1.0, 0.0)), (land + 1.3, (-1.0, 0.0)),
                            (land + 1.6, (1.0, 0.0))])
                p = p.but(eyes="open", brows="neutral", mouth="o" if t < land + 0.6 else "flat", look=lk,
                          f=-1 if land + 0.8 < t < land + 1.5 else 1, mouth_open=0.7)
                p = breathe(p, t)
            elif t < tf:
                k = back_out(prog(t, ts, ts + 0.25))
                p = p.but(eyes="wide", brows="up", mouth="o", look=(1, -0.2), head_dy=-10 * k, mouth_open=1.0)
            else:
                k = ease_out(prog(t, tf, tf + 0.2))
                bounce = abs(math.sin((t - tf) * 9)) * 18
                p = p.but(eyes="happy", brows="up", mouth="grin", look=(1, 0), arm_a=lerp(10, 34, k),
                          elb_a=lerp(10, 112, k), arm_b=lerp(-10, 44, k), elb_b=lerp(10, 106, k), bob=-bounce)
            J = fig(cx, self, cam, HERO, p, "hero")
            if t < land + 0.5:
                puff(cx, x, GY - 10, 90 * ease_out(prog(t, land, land + 0.4)), 1 - prog(t, land + 0.2, land + 0.5))
            if ts <= t < ts + 0.7:
                P.exclaim(cx, J["head"][0] + 30, J["head_top"][1] - 30, 1.6, 1 - prog(t, ts + 0.5, ts + 0.7))
            if t >= tf:
                fork(cx, J["hand_a"][0] - 4, J["hand_a"][1] - 34, 1.3, -0.1)
                knife(cx, J["hand_b"][0] + 2, J["hand_b"][1] - 34, 1.3, 0.1)
                drool = prog(t, tf + 0.4, tf + 0.9)
                if drool > 0:
                    hx, hy = J["head"]
                    line(cx, [(hx + 30, hy + 44), (hx + 30, hy + 44 + 40 * drool)], hexc("#8FD3FF"), 6)
                # thought bubble: a giant roast drumstick
                a = ease_out(prog(t, tf + 0.25, tf + 0.5))
                hx, hy = J["head_top"]

                def dish(c):
                    drumstick(c, hx + 150, hy - 250, 1.6 * a + 0.01, 0.6)
                    P.sparkles(c, hx + 150, hy - 250, t, 80, 5, a)
                thought(cx, hx + 150, hy - 250, 300, 230, a, (hx + 30, hy - 10), dish)
        end(cx)


class S2Notice(Shot):
    """The mammoth notices. The food looks back. Silent scream. Zoom."""
    scene = "s2"

    def plan(self, P):
        P.sfx("eye_open", t=0.05, vol=0.6)
        P.sfx("dun", t=0.3, vol=0.45)
        P.sfx("trumpet", t=0.62, vol=0.75)
        P.sfx("zip", t=1.3, vol=0.75)
        music(P, "chase", 0.62, 0.95, fade=0.05)
        P.wait(1.6)

    def draw(self, cx, t):
        tr = 0.62
        z = kf(t, [(0, 1.22), (0.6, 1.3), (0.62, 1.44), (1.6, 1.48)], ease_out)
        sh = shake(t, 18 * pulse(t, tr, tr + 0.5, 0.05), 30)
        cam = Cam(540 + sh[0], 1180 + sh[1], z)
        stoneage(cx, cam, t + 5)
        world(cx, cam)
        eye = pick(t, [(0, "calm"), (0.08, "wide"), (0.35, "angry")])
        tu = ease_out(prog(t, tr - 0.1, tr + 0.15)) * (1 - 0.5 * prog(t, 1.2, 1.6))
        mammoth(cx, 820, GY, 0.95, f=-1, t=t, eye=eye, trunk_up=tu, head_dip=40 * (1 - prog(t, 0.05, 0.3)),
                steam_a=prog(t, 0.4, 0.6))
        x = 280
        if t < 1.3:
            p = hero_pose(x, GY, t, s=HS, f=1, eyes="happy", mouth="grin", brows="up", arm_a=34, elb_a=112,
                          arm_b=44, elb_b=106)
            if t > 0.3:
                k = prog(t, 0.3, 0.5)
                p = p.but(eyes="open", mouth="flat", brows="neutral", sweat=k, look=(1, 0),
                          elb_a=lerp(112, 70, k), elb_b=lerp(106, 60, k))
            if t > tr + 0.05:
                k = back_out(prog(t, tr + 0.05, tr + 0.2))
                p = p.but(eyes="wide", mouth="scream", brows="worried", sweat=1.0, look=(1, -0.3),
                          squash=lerp(1.0, 1.18, k), head_dy=-12 * k, arm_a=150, arm_b=-150, elb_a=30, elb_b=-30,
                          mouth_open=1.25, bob=-60 * k)
            J = fig(cx, self, cam, HERO, p, "hero")
            if t < tr + 0.05:
                fork(cx, J["hand_a"][0] - 4, J["hand_a"][1] - 34, 1.3, -0.1)
                knife(cx, J["hand_b"][0] + 2, J["hand_b"][1] - 34, 1.3, 0.1)
            else:
                k = ease_in(prog(t, tr + 0.05, tr + 0.5))
                fork(cx, x + 60, GY - 420 + 380 * k, 1.3, -0.1 + 3 * k)
                knife(cx, x + 110, GY - 430 + 390 * k, 1.3, 0.1 - 4 * k)
            if t > tr:
                sweat_fly(cx, J["head"][0], J["head_top"][1], t, 1.0, 1.4)
        else:
            # zipped off: afterimage + dust cloud
            k = prog(t, 1.3, 1.6)
            puff(cx, x, GY - 30, 120, 1 - k, seed=4)
            P.speed_lines(cx, -200, GY - 420, x, GY - 60, t, 10, 0.8 * (1 - k), dirx=-1)
            fork(cx, x + 60, GY - 40, 1.3, 2.9)
            knife(cx, x + 110, GY - 40, 1.3, -3.9)
        end(cx)


class S2Chase(Shot):
    """Ridiculously fast run; the 'dinner' is now chasing him."""
    scene = "s2"

    def plan(self, P):
        for k in range(26):
            P.sfx("patter", t=k * 0.075, vol=0.35, seed=k)
        for k in range(5):
            P.sfx("stomp", t=0.12 + k * 0.42, vol=0.75)
        P.sfx("trumpet", t=1.35, vol=0.45)
        P.wait(2.05)

    def draw(self, cx, t):
        sh = shake(t, 9 + 6 * abs(math.sin(t * 7.5)), 30)
        cam = Cam(560 + sh[0], 1170 + sh[1], 1.2)
        dist = -2600 * t
        stoneage(cx, cam, t, par_x=dist)
        world(cx, cam)
        speed_lines_v(cx, t, 0.55, n=14, dirx=1, y0=500, y1=1500)
        # mammoth gaining
        mx = 820 - 70 * ease_io(prog(t, 0, 2.0)) + 20 * math.sin(t * 3)
        mammoth(cx, mx, GY + 10, 0.92, f=-1, t=t, run_t=t, eye="angry", trunk_up=0.6 + 0.3 * math.sin(t * 5))
        dust_trail(cx, mx + 120, GY, t, 1.4, dirx=-1, a=0.9)
        # hero, legs a blur
        hx = 300 + 14 * math.sin(t * 9)
        p = hero_pose(hx, GY, t, s=1.6, f=-1, eyes="wide", mouth="scream", brows="worried", sweat=1.0,
                      look=(-0.6, -0.2), mouth_open=1.2)
        p = run(p, t, speed=5.5, amp=1.1, flail=True)
        J = fig(cx, self, cam, HERO, p, "hero")
        leg_wheel(cx, hx + 6, GY - 70, t, HS, 0.8)
        dust_trail(cx, hx + 40, GY, t + 0.3, 1.0, dirx=-1, a=0.8, n=5)
        sweat_fly(cx, J["head"][0], J["head_top"][1], t, 1.0, 1.4)
        end(cx)


class S2Face(Shot):
    """Quick zoom into the terrified face (mid-run)."""
    scene = "s2"

    def plan(self, P):
        P.sfx("zoom", t=0.0, vol=0.6)
        P.sfx("heartbeat", t=0.15, vol=0.4)
        P.wait(0.85)

    def draw(self, cx, t):
        z = lerp(2.6, 4.4, ease_out(prog(t, 0, 0.35))) + 0.2 * t
        hx = 300
        p = hero_pose(hx, GY, t, s=HS, f=-1, eyes="wide", mouth="scream", brows="worried", sweat=1.0,
                      look=(0.9, -0.1), mouth_open=1.35, tilt=4 * math.sin(t * 30))
        p = run(p, t, speed=5.5, amp=1.1).but(look=(0.9, -0.1), arm_a=-8, arm_b=-4, elb_a=-10, elb_b=-10, lean=2)
        J0 = HERO.joints(p.but(bob=0))
        head = (hx + J0["head"][0] * HS, GY + J0["head"][1] * HS)
        sh = shake(t, 6, 40)
        cam = Cam(head[0] - 10 + sh[0], head[1] + 40 + sh[1], z)
        stoneage(cx, cam, t, par_x=-2600 * (t + 2))
        world(cx, cam)
        J = fig(cx, self, cam, HERO, p, "hero")
        sweat_fly(cx, J["head"][0], J["head_top"][1], t, 1.0, 1.0)
        end(cx)
        speed_lines_v(cx, t * 1.4, 0.6, n=22, dirx=1)
        # the mammoth's tusk sliding into frame
        k = ease_out(prog(t, 0.25, 0.8))
        cx.save()
        cx.translate(W + 260 - 300 * k, H * 0.62)
        cx.scale(3.2, 3.2)
        cx.move_to(0, 0)
        cx.curve_to(-60, 20, -120, -10, -140, -60)
        cx.curve_to(-110, -30, -60, -20, 0, -40)
        cx.close_path()
        fs(cx, hexc("#F4EBD9"), OUTLINE, 3)
        cx.restore()
        vignette(cx, 0.35)


# ====================================================================== SCENE 3 — dinner disaster montage
class MontageShot(Shot):
    scene = "s3"

    def bg(self, cx, t, cam=None, par=0.0):
        cam = cam or Cam(W / 2, H / 2 - 40, 1.0)
        stoneage(cx, cam, t + 8, par_x=par)
        return cam


class S3Fridge(MontageShot):
    def plan(self, P):
        music(P, "stone", 0.0, 0.9, fade=0.15)
        P.sfx("swish", t=0.18, vol=0.4)
        P.sfx("creak", t=0.36, vol=0.4)
        P.wait(0.12)
        P.say("n3a", gap=0.0)
        P.sfx("crickets", t=0.95, vol=0.35)
        self.tail = 0.55

    def draw(self, cx, t):
        cam = self.bg(cx, t, Cam(560, 1160, 1.3))
        world(cx, cam)
        door = ease_out(prog(t, 0.36, 0.75))
        fridge_outline(cx, 740, GY, 0.95, door, ease_out(prog(t, 0.16, 0.36)), t)
        x = 330
        p = hero_pose(x, GY, t, s=1.65, f=1, eyes="open", brows="up", mouth="smile", look=(1, 0))
        reach = ease_out(prog(t, 0.08, 0.32))
        pull = ease_io(prog(t, 0.36, 0.75))
        p = p.but(arm_b=lerp(-10, 82, reach) - 40 * pull, elb_b=lerp(10, 4, reach), lean=-6 * pull)
        if t > 0.85:
            k = prog(t, 0.85, 1.05)
            p = p.but(eyes="half", brows="flat", mouth="flat", look=(lerp(1, 0.2, k), 0.15), arm_b=-8, elb_b=10,
                      lean=0)
        p = breathe(p, t)
        fig(cx, self, cam, HERO, p, "hero")
        # a lone moth flutters out
        if t > 0.75:
            k = prog(t, 0.75, 1.6)
            mx, my = 760 - 260 * k + 30 * math.sin(t * 9), GY - 360 - 260 * k
            cx.save()
            cx.translate(mx, my)
            fl = math.sin(t * 34) * 0.6
            for sx in (-1, 1):
                cx.save()
                cx.scale(sx, 1)
                cx.rotate(fl)
                ellipse(cx, 16, -6, 16, 10, -0.4)
                fs(cx, hexc("#C9BBA3"), OUTLINE, 3)
                cx.restore()
            ellipse(cx, 0, 0, 5, 11)
            fs(cx, hexc("#7A6A55"), OUTLINE, 2.5)
            cx.restore()
        end(cx)


class S3Tablet(MontageShot):
    def plan(self, P):
        for k, tt in enumerate((0.12, 0.3, 0.48, 0.66)):
            P.sfx("tap", t=tt, vol=0.5, seed=k)
        P.wait(0.08)
        s = P.say("n3b", gap=0.0)
        accent(P, "NO [DELIVERY.]", s, 1.55)
        P.sfx("crack", t=1.02, vol=0.7)
        self.tail = 0.6

    def draw(self, cx, t):
        cam = self.bg(cx, t, Cam(540, 1150, 1.5))
        world(cx, cam)
        x = 540
        crack = ease_out(prog(t, 1.02, 1.18))
        p = hero_pose(x, GY, t, s=1.65, view="front", eyes="open", brows="up", mouth="smile", look=(0, 0.9),
                      arm_a=14, elb_a=-104, arm_b=14, elb_b=-104)
        if crack > 0:
            p = p.but(eyes="wide", brows="worried", mouth="wavy", look=(0, -0.2), sweat=crack)
        else:
            p = p.but(elb_b=-104 + 10 * abs(math.sin(t * 17)))
        p = breathe(p, t)
        J = fig(cx, self, cam, HERO, p, "hero")
        tx = x
        ty = J["neck"][1] + 150
        stone_tablet(cx, tx, ty, 0.4, 0.04 + 0.03 * crack, t, crack, load=1 - crack)
        # hands on top of the slab
        for k in ("hand_a", "hand_b"):
            circle(cx, J[k][0], J[k][1], 12)
            fs(cx, OUTLINE, None, 0)
        if crack > 0:
            P.impact_star(cx, tx, ty + 10, 40 * crack, 1 - prog(t, 1.2, 1.4))
        end(cx)


class S3Microwave(MontageShot):
    def plan(self, P):
        P.wait(0.08)
        P.sfx("thunk", t=0.25, vol=0.5)
        P.sfx("click", t=0.62, vol=0.6)
        P.sfx("click", t=0.82, vol=0.6)
        P.say("n3c", gap=0.0)
        P.sfx("crickets", t=1.15, vol=0.35)
        self.tail = 0.45

    def draw(self, cx, t):
        cam = self.bg(cx, t, Cam(560, 1170, 1.3))
        world(cx, cam)
        rx = 720
        rock_microwave(cx, rx, GY, 1.0, t, press=pulse(t, 0.62, 0.68, 0.04) + pulse(t, 0.82, 0.88, 0.04))
        # potato on the rock
        place = ease_out(prog(t, 0.1, 0.3))
        x = 360
        p = hero_pose(x, GY, t, s=1.65, f=1, eyes="open", brows="up", mouth="smile", look=(1, 0.2))
        reach = ease_out(prog(t, 0.05, 0.25)) * (1 - prog(t, 0.95, 1.1))
        p = p.but(arm_b=lerp(-10, 70, reach), elb_b=lerp(10, 20, reach), lean=6 * reach)
        if t > 1.05:
            p = p.but(view="front", eyes="half", brows="flat", mouth="flat", look=(0, 0), arm_a=12, arm_b=12,
                      elb_a=10, elb_b=10, lean=0)
        p = breathe(p, t)
        J = fig(cx, self, cam, HERO, p, "hero")
        if t < 0.3:
            potato(cx, J["hand_b"][0] + 10, J["hand_b"][1] - 12, 1.1)
        else:
            potato(cx, rx - 40, GY - 232, 1.1)
        # "..." from the rock
        for k in range(3):
            a = prog(t, 0.95 + k * 0.12, 1.0 + k * 0.12)
            circle(cx, rx - 30 + k * 30, GY - 300, 9)
            src(cx, (0.11, 0.11, 0.14, a))
            cx.fill()
        if t > 1.2:
            cricket(cx, rx + 120, GY - 214, 0.9, t)
        end(cx)


class S3ChaseFood(MontageShot):
    def plan(self, P):
        for k in range(14):
            P.sfx("patter", t=k * 0.1, vol=0.3, seed=k)
            if k % 2 == 0:
                P.sfx("squawk", t=0.1 + k * 0.1, vol=0.15, seed=k)
        P.wait(0.05)
        P.say("n4a", gap=0.0)
        self.tail = 0.3

    def draw(self, cx, t):
        par = 1500 * t
        cam = self.bg(cx, t, Cam(560, 1180, 1.2), par)
        world(cx, cam)
        speed_lines_v(cx, t, 0.4, n=10, dirx=-1, y0=700, y1=1500)
        dodo(cx, 760 + 20 * math.sin(t * 7), GY, 1.25, f=1, t=t, run_t=t, mood="scared")
        hx = 330
        p = hero_pose(hx, GY, t, s=HS, f=1, eyes="angry", brows="angry", mouth="teeth", look=(1, 0))
        p = run(p, t, speed=3.4, amp=0.95)
        p = p.but(arm_b=160 + 10 * math.sin(t * 20), elb_b=20)
        J = fig(cx, self, cam, HERO, p, "hero")
        club(cx, J["hand_b"][0], J["hand_b"][1], 1.15, 0.3 + 0.25 * math.sin(t * 20))
        dust_trail(cx, hx - 30, GY, t, 1.0, dirx=1, a=0.7, n=4)
        end(cx)


class S3ChasedByFood(MontageShot):
    def plan(self, P):
        P.sfx("stomp", t=0.0, vol=0.7)
        P.sfx("skid", t=0.05, vol=0.55)
        P.sfx("trumpet", t=0.3, vol=0.6)
        P.say("n4b", gap=0.0)
        P.sfx("zip", t=0.62, vol=0.5)
        for k in range(16):
            P.sfx("patter", t=0.7 + k * 0.08, vol=0.18, seed=k)
        for k in range(3):
            P.sfx("stomp", t=0.85 + k * 0.42, vol=0.35)
        self.tail = 0.15

    def draw(self, cx, t):
        turn = 0.62
        run_t = max(0.0, t - turn)
        par = 1500 * 0.4 * (1 - prog(t, 0, 0.3)) * t - 2400 * run_t
        sh = shake(t, 22 * pulse(t, 0.0, 0.25, 0.05) + 8 * (t > turn), 30)
        cam = self.bg(cx, t, Cam(560 + sh[0], 1170 + sh[1], 1.15), par)
        world(cx, cam)
        # mammoth (with the dodo riding on its head, very smug)
        mx = lerp(1400, 830, ease_out(prog(t, 0.0, 0.2))) - 60 * ease_io(prog(t, turn, 1.8))
        mammoth(cx, mx, GY + 10, 0.92, f=-1, t=t, run_t=run_t if t > turn else None, eye="angry",
                trunk_up=pulse(t, 0.28, 0.6, 0.08), dodo_rider=1.0)
        if t > turn:
            dust_trail(cx, mx + 120, GY, t, 1.4, dirx=-1, a=0.9)
        hx = 380 + 30 * ease_out(prog(t, 0, 0.2))
        if t < turn:
            p = hero_pose(hx, GY, t, s=HS, f=1, eyes="wide", brows="worried", mouth="o", look=(1, -0.2),
                          lean=-22, hip_a=30, knee_a=10, hip_b=-20, knee_b=30, arm_b=150, elb_b=20, arm_a=110,
                          sweat=prog(t, 0.2, 0.4), mouth_open=1.0)
            J = fig(cx, self, cam, HERO, p, "hero")
            club(cx, J["hand_b"][0], J["hand_b"][1], 1.15, 0.3 - 2.5 * prog(t, 0.3, 0.6))
            puff(cx, hx + 40, GY - 20, 60, 1 - prog(t, 0.1, 0.5), seed=2)
        else:
            p = hero_pose(hx, GY, t, s=HS, f=-1, eyes="wide", mouth="scream", brows="worried", sweat=1.0,
                          look=(0.8, -0.2), mouth_open=1.2)
            p = run(p, run_t, speed=5.5, amp=1.1, flail=True)
            J = fig(cx, self, cam, HERO, p, "hero")
            leg_wheel(cx, hx + 6, GY - 70, t, HS, 0.8)
            sweat_fly(cx, J["head"][0], J["head_top"][1], t, 1.0, 1.3)
            speed_lines_v(cx, t, 0.5, n=12, dirx=1, y0=600, y1=1500)
        end(cx)


class S3Fire(MontageShot):
    """'...and somehow burned a potato.' Stick-rubbing, ignition, instant charcoal."""

    def plan(self, P):
        P.wait(0.05)
        s = P.say("n4c", gap=0.0)
        for k in range(9):
            P.sfx("rub", t=0.05 + k * 0.11, vol=0.4, seed=k)
        P.sfx("ignite", t=1.05, vol=0.75)
        P.sfx("crackle", t=1.1, vol=0.35)
        self.m["burn"] = (s + 1.72, s + 1.72)
        P.sfx("burn", t=s + 1.72, vol=0.8)
        self.tail = 0.45

    def draw(self, cx, t):
        tb = self.mt("burn")
        cam = self.bg(cx, t, Cam(540, 1190, 1.35))
        world(cx, cam)
        fx, fy = 590, GY - 10
        ign = ease_out(prog(t, 1.05, 1.25))
        campfire(cx, fx, fy, 0.95, t, fire=ign * (1 + 0.35 * pulse(t, tb, tb + 0.25, 0.05)),
                 smoke=prog(t, 0.3, 1.0) * (1 - ign) + 0.4 * ign)
        x = 330
        p = hero_pose(x, GY, t, s=1.6, f=1, eyes="angry", brows="angry", mouth="teeth", look=(1, 0.6))
        # sitting on the ground
        p = p.but(hip_a=78, knee_a=-30, hip_b=88, knee_b=10, bob=104, lean=10)
        if t < 1.05:   # rubbing a stick between the palms, over the fire pit
            rub = math.sin(t * 46)
            p = p.but(arm_a=70 + 6 * rub, elb_a=14, arm_b=70 - 6 * rub, elb_b=14)
        elif t < 1.35:   # FWOOMP - singed
            p = p.but(eyes="wide", brows="up", mouth="o", lean=-14, arm_a=120, arm_b=120, elb_a=20, elb_b=20,
                      look=(1, 0))
        elif t < tb + 0.1:   # holding the potato over the fire on a stick
            p = p.but(eyes="open", brows="up", mouth="smile", arm_b=78, elb_b=10, arm_a=40, elb_a=40, look=(1, 0.3))
        else:   # stares at the result
            p = p.but(eyes="open", brows="flat", mouth="flat", arm_b=78, elb_b=10, arm_a=40, elb_a=40,
                      look=(1, 0.3))
        J = fig(cx, self, cam, HERO, p, "hero")
        soot(cx, J, prog(t, 1.05, 1.15))
        if t < 1.05:
            hx = (J["hand_a"][0] + J["hand_b"][0]) / 2
            hy = (J["hand_a"][1] + J["hand_b"][1]) / 2
            stick(cx, hx, hy - 30, fx + 6 * math.sin(t * 46), fy - 14, 9)
            smoke_wisps(cx, fx, fy - 30, t, prog(t, 0.2, 0.8), 3, 0.7)
        elif t >= 1.35:
            hx, hy = J["hand_b"]
            ex, ey = fx + 10, fy - 150
            stick(cx, hx, hy, ex, ey, 8)
            burnt = ease_out(prog(t, tb, tb + 0.12))
            shrink = 1 - 0.35 * ease_out(prog(t, tb + 0.1, tb + 0.4))
            potato(cx, ex, ey - 4, 1.35 * shrink, burnt, 0.2)
            if t > tb:
                k = prog(t, tb, tb + 0.6)
                puff(cx, ex, ey - 40 - 60 * k, 50 + 50 * k, 0.9 * (1 - k), (0.25, 0.25, 0.27), seed=6)
        if 1.05 <= t < 1.3:
            flash(cx, 0.5 * (1 - prog(t, 1.05, 1.3)), (1.0, 0.8, 0.4))
        end(cx)


class S3Defeat(MontageShot):
    def plan(self, P):
        P.sfx("wind", t=0.3, vol=0.45)
        P.sfx("crickets", t=0.1, vol=0.3)
        P.wait(1.15)

    def draw(self, cx, t):
        cam = self.bg(cx, t, Cam(W / 2, H / 2 + 300, 1.9))
        world(cx, cam)
        tumbleweed(cx, lerp(-200, 1300, prog(t, 0.0, 1.6)), GY - 60 - abs(math.sin(t * 6)) * 40, 46, t * 6)
        draw_defeat(cx, self, cam, t)
        end(cx)


def draw_defeat(cx, sh, cam, t, crumble_t=0.35):
    x = 540
    p = hero_pose(x, GY, t, s=1.65, view="front", eyes="half", brows="worried", mouth="flat", look=(0, 0.5),
                  arm_a=-2, elb_a=-110, arm_b=12, elb_b=10, head_dy=6, lean=0)
    p = breathe(p, t, 0.6)
    J = fig(cx, sh, cam, HERO, p, "hero")
    soot(cx, J, 1.0)
    hx, hy = J["hand_a"]
    k = prog(t, crumble_t, crumble_t + 0.5)
    if k < 1:
        potato(cx, hx, hy - 16, 0.62 * (1 - 0.6 * k), 1.0, 0.2)
    # ash blowing away
    r = random.Random(11)
    for i in range(16):
        ph = clamp((t - crumble_t - r.random() * 0.2) / 0.9)
        if ph <= 0 or ph >= 1:
            continue
        ax = hx + ph * (200 + 200 * r.random())
        ay = hy - 16 - ph * 60 * r.random() + math.sin(ph * 9 + i) * 10
        circle(cx, ax, ay, 4 + 4 * r.random())
        src(cx, (0.3, 0.3, 0.32, 1 - ph))
        cx.fill()
    for k2 in ("hand_a",):
        circle(cx, J[k2][0], J[k2][1], 9)
        fs(cx, OUTLINE, None, 0)
    return J


# ====================================================================== SCENE 4 — back home
class S4Return(MontageShot):
    """'Then suddenly…' the vortex grabs him again; smash cut on 'I was back home'."""
    scene = "s4"

    def plan(self, P):
        P.wait(0.12)
        s = say_at(P, "n5", P.t)
        P.sfx("portal", t=s + 0.2, vol=0.5)
        P.sfx("suck", t=s + 0.85, vol=0.6)
        P.t = s + 1.27      # cut lands on "I was back home" (the line keeps playing over the next shot)

    def draw(self, cx, t):
        cam = self.bg(cx, t + 1.15, Cam(W / 2, H / 2 + 300, 1.9))
        vr = 520 * ease_out(prog(t, 0.25, 0.7))
        end_ = 1.39
        sc = cam.to_screen(540, GY - 420)
        vortex(cx, sc[0], sc[1], vr, t, 1.0)
        world(cx, cam)
        k = ease_in(prog(t, 0.85, end_))
        cx.save()
        cx.translate(540, GY - 300)
        cx.rotate(k * 6)
        cx.scale(1 - 0.9 * k, 1 - 0.9 * k)
        cx.translate(-540, -(GY - 300))
        x = 540
        p = hero_pose(x, GY, t, s=1.65, view="front", eyes="wide" if t > 0.3 else "half", brows="up",
                      mouth="o" if t > 0.3 else "flat", look=(0, -0.6) if t > 0.3 else (0, 0.5),
                      arm_a=-2, elb_a=-110, arm_b=12, elb_b=10, sweat=prog(t, 0.6, 0.8))
        J = fig(cx, self, cam, HERO, p, "hero")
        soot(cx, J, 1.0)
        cx.restore()
        end(cx)


class S4Home(Shot):
    """Smash cut: the dinner table. The chicken. The light."""
    scene = "s4"
    trans_in = ("flash", 0.18)

    def plan(self, P):
        music(P, "warm", 0.15, 1.0, fade=0.1)
        P.sfx("smash", t=0.0, vol=0.6)
        P.sfx("choir", t=0.55, vol=0.55)
        P.sfx("sparkle", t=0.6, vol=0.5)
        P.wait(2.35)

    def draw(self, cx, t):
        z = kf(t, [(0, 1.0), (2.35, 1.06)], ease_io)
        cam = Cam(W / 2, H / 2 + 40, z)
        dining(cx, cam, t)
        glow = ease_out(prog(t, 0.5, 0.9))
        world(cx, cam)
        light_rays(cx, 470, 1380, t, glow, 1100)
        draw_family(cx, self, cam, t, phase="home")
        end(cx)
        dining_table(cx, cam)
        world(cx, cam)
        roast_chicken(cx, 470, 1425, 1.35, t, 0.0, glow)
        steam(cx, 470, 1335, t, 0.45, 1.0)
        P.sparkles(cx, 470, 1300, t, 240, 8, glow)
        end(cx)


def draw_family(cx, sh, cam, t, phase="home", st=None):
    """Hero (front, centre) behind the table; Mom (side, right) at the table."""
    st = st or {}
    # Mom
    mx = 880
    mp = mom_pose(mx, 1705, t, s=2.15, f=-1, arm_a=24, elb_a=62, arm_b=30, elb_b=58, look=(-0.6, 0.1))
    mp = mp.but(hip_a=86, knee_a=86, hip_b=82, knee_b=84, bob=-4)
    if st.get("mom_talk"):
        mp = talk(mp, t)
        mp = mp.but(mouth=st.get("mom_mouth", "grin"), mouth_open=mp.mouth_open * 0.55)
    mp = mp.but(**st.get("mom", {}))
    mp = breathe(mp, t, 0.7)
    fig(cx, sh, cam, MOM, mp, "mom")
    # Hero
    hp = hero_pose(450, 1712, t, s=2.4, view="front", eyes="wide", brows="up", mouth="o", look=(0, 0.7),
                   arm_a=8, elb_a=10, arm_b=8, elb_b=10)
    if phase == "home":
        k = back_out(prog(t, 0.3, 0.6))
        hp = hp.but(head_dy=-14 * k, mouth_open=0.6 + 0.5 * k, blink=False, arm_a=lerp(8, 60, k),
                    elb_a=lerp(10, 90, k), arm_b=lerp(8, 60, k), elb_b=lerp(10, 90, k))
        if t > 1.5:
            hp = hp.but(eyes="wide", mouth="grin", mouth_open=0.7)
    hp = hp.but(**st.get("hero", {}))
    if not st.get("frozen"):
        hp = breathe(hp, t)
    J = fig(cx, sh, cam, HERO, hp, "hero")
    if phase == "home":
        eye_sparkle(cx, J, hp, ease_out(prog(t, 0.55, 0.8)))
        if t > 1.1:   # tears of joy
            for side in (-1, 1):
                k = (t * 1.6 + (side + 1) * 0.25) % 1
                hx = J["head"][0] + side * J["head_rad"] * 0.42
                hy = J["head"][1] + J["head_rad"] * 0.15 + k * 70
                ellipse(cx, hx, hy, 6, 9)
                src(cx, hexc("#8FD3FF", 1 - k))
                cx.fill()
    return J


# ====================================================================== SCENE 5 — punchline
class S5Punch(Shot):
    scene = "s5"

    def plan(self, P):
        P.wait(0.12)
        d1 = P.dlg("d1", "mom", "", gap=0.32)
        d2 = P.dlg("d2", "hero", "", gap=0.38)
        accent(P, "BEST MEAL OF\n[MY LIFE!]", d2 - 0.03, P.voice.dur("d2") + 0.15, y=470)
        d3 = P.dlg("d3", "mom", "", gap=0.0)
        music(P, None, d3 - 0.06, fade=0.03)          # abrupt silence before the punchline
        tfz = d3 + P.voice.dur("d3") - 0.25
        self.m["freeze"] = (tfz, tfz + 0.75)
        P.t = tfz + 0.75
        d4 = P.dlg("d4", "hero", "", gap=0.0)
        self.m["fast"] = (d4 + P.voice.dur("d4") - 0.25, 0)
        music(P, "stone", d4 + P.voice.dur("d4") - 0.2, 0.9, fade=0.05)
        P.t = d4 + P.voice.dur("d4") + 0.75
        # eating sounds
        for k in range(5):
            P.sfx("bite" if k % 2 == 0 else "chew", t=0.2 + k * 0.45, vol=0.35)
        P.sfx("gulp", t=d2 - 0.25, vol=0.4)
        P.sfx("bite", t=d3 - 0.3, vol=0.35)
        P.sfx("freeze", t=tfz, vol=0.25)
        tf = self.m["fast"][0]
        for k in range(7):
            P.sfx("chew" if k % 2 else "bite", t=tf + k * 0.1, vol=0.4)
        # bubbles are not used in this Short (no captions); drop them
        P.cues[:] = [c for c in P.cues if c["type"] != "bubble"]

    def draw(self, cx, t):
        d1 = self.mt("d1"), self.mt("d1", 1)
        d2 = self.mt("d2"), self.mt("d2", 1)
        d3 = self.mt("d3"), self.mt("d3", 1)
        d4 = self.mt("d4"), self.mt("d4", 1)
        tfz0, tfz1 = self.m["freeze"]
        tf = self.m["fast"][0]
        z = kf(t, [(0, 1.06), (d3[0], 1.1), (tfz0, 1.1), (tfz0 + 0.12, 1.22), (d4[1], 1.22), (tf + 0.1, 1.08)],
               ease_out)
        cam = Cam(W / 2 + (30 if tfz0 <= t < d4[1] else 0), H / 2 + 40 - (60 if tfz0 <= t < d4[1] else 0), z)
        dining(cx, cam, t)
        world(cx, cam)
        st = {"hero": {}, "mom": {}}
        frozen = tfz0 <= t < d4[0]
        # ---- Mom
        if d1[0] <= t <= d1[1] or d3[0] <= t <= d3[1]:
            st["mom_talk"] = True
            st["mom_mouth"] = "grin"
        if t < d3[0]:
            st["mom"] = dict(eyes="open", brows="up", mouth="smile", look=(-0.7, 0))
        else:
            st["mom"] = dict(eyes="half", brows="flat", mouth="flat", look=(-0.8, 0.1))
        # ---- Hero
        eat_rate = 2.4
        bite_k = 0.5 + 0.5 * math.sin(t * eat_rate * 2 * math.pi)     # 1 = at mouth
        h = {}
        if t < d2[0] - 0.1:
            h = dict(eyes="happy", brows="up", mouth="chew", mouth_open=0.4 + 0.6 * abs(math.sin(t * 12)),
                     arm_b=lerp(26, -12, bite_k), elb_b=lerp(-60, -150, bite_k), arm_a=-10, elb_a=-60,
                     look=(0, 0.3))
        elif t < d3[0] - 0.05:
            k = ease_out(prog(t, d2[0] - 0.1, d2[0] + 0.15))
            h = dict(eyes="happy", brows="up", mouth="yell", mouth_open=0.7 + 0.4 * abs(math.sin(t * 9)),
                     arm_b=lerp(-12, 150, k), elb_b=lerp(-150, 10, k), arm_a=lerp(-10, 120, k), elb_a=10,
                     head_dy=-8 * k, look=(0, -0.3))
            if t > d2[1] - 0.1:
                kk = ease_io(prog(t, d2[1] - 0.1, d3[0] - 0.05))
                h.update(arm_b=lerp(150, -12, kk), elb_b=lerp(10, -150, kk), arm_a=lerp(120, -10, kk),
                         elb_a=lerp(10, -60, kk), mouth="chew")
        elif t < tfz0:
            # mid-bite while Mom talks
            h = dict(eyes="happy", brows="up", mouth="chew", mouth_open=0.4 + 0.6 * abs(math.sin(t * 12)),
                     arm_b=-12, elb_b=-150, arm_a=-10, elb_a=-60, look=(-0.3, 0.3))
        elif t < d4[0]:
            # FREEZE: eyes wide, drumstick in mouth
            h = dict(eyes="wide", brows="neutral", mouth="chew", mouth_open=0.6, arm_b=-12, elb_b=-150,
                     arm_a=-10, elb_a=-60, look=(0.5, 0.0), blink=False)
        elif t < tf:
            # "Even better."  — dry, confident
            h = dict(eyes="half", brows="skeptic", mouth="smirk", look=(0.6, 0.0), arm_b=-4, elb_b=-120,
                     arm_a=-10, elb_a=-60, tilt=-6)
            if t < d4[1] - 0.2:
                h["mouth"] = "smirk" if math.sin(t * 22) > 0 else "flat"
        else:
            # eats even faster
            fk = 0.5 + 0.5 * math.sin(t * 7.5 * 2 * math.pi)
            fk2 = 0.5 + 0.5 * math.sin(t * 7.5 * 2 * math.pi + math.pi)
            h = dict(eyes="happy", brows="up", mouth="chew", mouth_open=0.3 + 0.7 * fk,
                     arm_b=lerp(26, -12, fk), elb_b=lerp(-60, -150, fk), arm_a=lerp(26, -12, fk2),
                     elb_a=lerp(-60, -150, fk2), look=(0, 0.3), bob=-6 * fk)
        st["hero"] = h
        st["frozen"] = frozen
        J = draw_family(cx, self, cam, t, phase="eat", st=st)
        end(cx)
        dining_table(cx, cam)
        world(cx, cam)
        eaten = 0.35 * prog(t, 0, d3[0]) + 0.65 * prog(t, tf, tf + 0.7)
        roast_chicken(cx, 470, 1425, 1.35, t, eaten, 0.0)
        if t < tf:
            steam(cx, 470, 1335, t, 0.35, 1.0)
        # drumstick in the hero's hand
        hx, hy = J["hand_b"]
        drumstick(cx, hx - 6, hy - 40, 1.25, -0.25 if t < d2[0] or t > d3[0] else 0.4,
                  bite=min(1.0, 0.3 + prog(t, 0, tf + 0.6)))
        if t >= tf:
            hx2, hy2 = J["hand_a"]
            drumstick(cx, hx2 + 6, hy2 - 40, 1.25, 0.25, bite=0.6)
            # crumbs flying
            r = random.Random(int(t * 30))
            for k in range(6):
                cx_, cy_ = J["head"][0] + r.uniform(-60, 60), J["head"][1] + 50 + r.uniform(-20, 60)
                circle(cx, cx_, cy_, r.uniform(3, 7))
                fs(cx, hexc("#D98B3A"), None, 0)
        end(cx)


class S6Loop(S1Room):
    """Very quick cut back to the opening gaming position: the Short loops into frame 1."""
    scene = "s6"

    def plan(self, P):
        P.sfx("smash", t=0.0, vol=0.35)
        P.sfx("game", t=0.05, vol=0.22, seed=0)
        P.sfx("game", t=0.22, vol=0.22, seed=1)
        self.m["quake"] = (99, 99)
        self.m["open"] = (99, 99)
        self.m["suck"] = (99, 99)
        P.wait(0.5)

    def draw(self, cx, t):
        # identical to the first frames of S1 (Mom not yet in the door)
        super().draw(cx, min(t * 0.4, 0.2))


def scenes():
    return [S1Room(), S2Land(), S2Notice(), S2Chase(), S2Face(),
            S3Fridge(), S3Tablet(), S3Microwave(), S3ChaseFood(), S3ChasedByFood(), S3Fire(), S3Defeat(),
            S4Return(), S4Home(), S5Punch(), S6Loop()]

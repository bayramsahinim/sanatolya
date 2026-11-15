"""Shot list. Times are global seconds on the narration take (see timing.py cue printout).
Each shot: (start, end, fn, crossfade_in). fn(cx, t_local, dur, T_global)."""
import math
import random

import cairo

from episodes.japan_johatsu import sets as S
from episodes.japan_johatsu.art import (FONT, H, INK, JP_FONT, W, alpha, back_out, cached_layer, camera, clamp,
                                        contact_shadow, eio, ellipse, eout, fill_ink, glow, handheld, hx, ink, lerp,
                                        light_cone, lin, mixc, paint_layer, person, poly, prog, rad, rrect, shade,
                                        smooth, src, text, text_w)

MONO = "Courier 10 Pitch"
WARM = hx("#ffcf8a")
COLD = hx("#8fb0ff")
END = 68.0


def cam(cx, t, d, z0=1.0, z1=1.06, f0=(W / 2, H / 2), f1=None, hh=1.0, seed=0):
    f1 = f1 or f0
    k = eio(t / d)
    ox, oy, r = handheld(t, hh, seed)
    camera(cx, lerp(z0, z1, k), lerp(f0[0], f1[0], k), lerp(f0[1], f1[1], k), r, ox, oy)


def card(cx, x, y, w, h, a=1.0, fill=hx("#11141f"), edge=hx("#ffffff"), r=26, sc=1.0):
    cx.save()
    cx.translate(x + w / 2, y + h / 2)
    cx.scale(sc, sc)
    cx.translate(-w / 2, -h / 2)
    cx.push_group()
    cx.save()
    cx.translate(0, 16)
    rrect(cx, 0, 0, w, h, r)
    src(cx, (0, 0, 0, 0.4))
    cx.fill()
    cx.restore()
    rrect(cx, 0, 0, w, h, r)
    src(cx, fill)
    cx.fill_preserve()
    src(cx, alpha(edge, 0.18))
    cx.set_line_width(3)
    cx.stroke()
    return a


def card_end(cx, a):
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def pop(t, t0, d=0.25):
    k = prog(t, t0, t0 + d)
    return k, lerp(0.86, 1.0, back_out(k, 2.0)) if k > 0 else 0.86


# ================================================================ shots
def apt_layer():
    return cached_layer("apt", lambda c: S.apartment_static(c))


def apt_bg(cx, t, lamp=1.0, books_keep=1.0, photo=True, dim=0.0):
    paint_layer(cx, apt_layer())
    S.books(cx, 640, 878, 14, keep=books_keep)
    if photo:
        S.photo_frame(cx, 930, 878)
    S.pendant_lamp(cx, 540, 430, lamp)
    if dim:
        cx.rectangle(-500, -500, W + 1000, H + 1000)
        src(cx, (0.02, 0.03, 0.08, dim))
        cx.fill()


def puff(cx, x, y, k, n=14, seed=3, r0=60, r1=260):
    if k <= 0 or k >= 1:
        return
    rng = random.Random(seed)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        dist = eout(k) * rng.uniform(r0, r1)
        rr = lerp(40, 130, eout(k)) * rng.uniform(0.6, 1.2)
        cx.arc(x + math.cos(a) * dist, y + math.sin(a) * dist * 0.8 - k * 80, rr, 0, 2 * math.pi)
        src(cx, (0.95, 0.95, 0.97, 0.85 * (1 - k) ** 1.2))
        cx.fill()


def shot_hook(cx, t, d, T):
    cam(cx, t, d, 1.3, 1.42, (540, 1230), (540, 1250))
    apt_bg(cx, t)
    van_k = prog(T, 2.18, 2.75)
    gone = T > 2.45
    # son seated behind table
    if not gone:
        reach = smooth(prog(T, 0.75, 1.3))
        cx.push_group()
        person(cx, 540, 1690, 800, "son",
               dict(legs=False, arms=(lerp(5, -35, reach), lerp(10, -40, reach), lerp(-5, 35, reach),
                                      lerp(-10, 40, reach)),
                    eyes="dot", brow="sad", mouth="wavy", sweat=0.7, look=(0, 0.6)), light=(1, WARM), t=T)
        cx.pop_group_to_source()
        cx.paint_with_alpha(1 - prog(T, 2.25, 2.45))
    S.low_table(cx, 540, 1420)
    cash_a = 1 - prog(T, 2.25, 2.45)
    if cash_a > 0:
        S.cash_stack(cx, lerp(430, 470, smooth(prog(T, 0.75, 1.4))), 1462, 5, cash_a)
    S.papers(cx, 650, 1470, 2)
    S.tea_cup(cx, 770, 1475, T, steam=1.0)
    puff(cx, 540, 1180, van_k)


def neon_sign(cx, x, y, T, flick=1.0):
    # housing
    rrect(cx, x - 400, y - 150, 800, 330, 18)
    src(cx, hx("#14101c"))
    cx.fill_preserve()
    ink(cx, 6, hx("#05040a"))
    on = flick * (0.85 + 0.15 * math.sin(T * 37) * (1 if (T % 2.3) < 0.12 else 0))
    glow(cx, x, y, 520, hx("#ff3d9a"), 0.35 * on, sy=0.55)
    for lw, a in ((26, 0.10), (14, 0.22), (6, 0.6)):
        text(cx, "夜逃げ屋", x, y + 60, 190, alpha(hx("#ff5fb0"), a * on), font=JP_FONT, outline=lw,
             ocol=alpha(hx("#ff5fb0"), a * on))
    text(cx, "夜逃げ屋", x, y + 60, 190, mixc(hx("#ffd6ec"), hx("#ffffff"), 0.5), font=JP_FONT)
    for lw, a in ((12, 0.15), (5, 0.5)):
        text(cx, "NIGHT MOVERS", x, y + 145, 58, alpha(hx("#5fe8ff"), a * on), outline=lw,
             ocol=alpha(hx("#5fe8ff"), a * on), spacing=4)
    text(cx, "NIGHT MOVERS", x, y + 145, 58, hx("#e6fbff"), spacing=4)


def alley_static(cx):
    lin(cx, 0, 0, 0, H, [(0, hx("#090611")), (0.5, hx("#140d22")), (1, hx("#07050c"))])
    cx.paint()
    # walls in perspective
    poly(cx, [(0, 0), (300, 500), (300, 1420), (0, 1700)])
    lin(cx, 0, 0, 300, 0, [(0, hx("#1d1630")), (1, hx("#2a2140"))])
    cx.fill()
    poly(cx, [(W, 0), (780, 500), (780, 1420), (W, 1700)])
    lin(cx, 780, 0, W, 0, [(0, hx("#2a2140")), (1, hx("#18122a"))])
    cx.fill()
    # far end glow
    cx.rectangle(300, 500, 480, 920)
    lin(cx, 0, 500, 0, 1420, [(0, hx("#1b1438")), (1, hx("#2c2350"))])
    cx.fill()
    S.skyline(cx, 300, 860, 480, 300, seed=8, lit=0.4)
    # ground
    poly(cx, [(0, 1700), (300, 1420), (780, 1420), (W, 1700), (W, H), (0, H)])
    lin(cx, 0, 1420, 0, H, [(0, hx("#1a1424")), (1, hx("#0a0810"))])
    cx.fill()
    # vending machine right
    poly(cx, [(830, 1040), (1000, 980), (1000, 1560), (830, 1500)])
    lin(cx, 830, 0, 1000, 0, [(0, hx("#c9e6ff")), (1, hx("#7fb1df"))])
    cx.fill()
    for k in range(4):
        poly(cx, [(850, 1080 + k * 70), (980, 1035 + k * 70), (980, 1080 + k * 70), (850, 1125 + k * 70)])
        src(cx, hx("#ff6f7a") if k % 2 else hx("#ffd36f"))
        cx.fill()
    glow(cx, 915, 1250, 420, hx("#9fd2ff"), 0.22)
    # pipes / ac units left
    for k in range(3):
        cx.rectangle(40 + k * 18, 600 + k * 260, 150, 90)
        src(cx, hx("#2d2540"))
        cx.fill()
    # reflections
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    lin(cx, 0, 1430, 0, H, [(0, alpha(hx("#ff4fa3"), 0.22)), (1, alpha(hx("#ff4fa3"), 0))])
    poly(cx, [(300, 1430), (780, 1430), (900, H), (180, H)])
    cx.fill()
    lin(cx, 0, 1500, 0, H, [(0, alpha(hx("#9fd2ff"), 0.15)), (1, alpha(hx("#9fd2ff"), 0))])
    poly(cx, [(840, 1500), (1000, 1560), (1060, H), (880, H)])
    cx.fill()
    cx.restore()


def shot_neon(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.08, (540, 760), (540, 1020))
    paint_layer(cx, cached_layer("alley", alley_static))
    neon_sign(cx, 540, 470, T)
    light = (0, hx("#ff6fb6"))
    card_k = prog(T, 5.6, 5.9)
    person(cx, 540, 1640, 980, "rep",
           dict(arms=(-30, -60, lerp(30, -100, card_k) if card_k else 30, lerp(60, -20, card_k) if card_k else 60),
                mouth="smile" if T > 5.6 else "smirk", eyes="dot", look=(0, 0.3)),
           light=(-1, hx("#ff6fb6")), t=T)
    glow(cx, 540, 600, 700, hx("#ff3d9a"), 0.06)
    # business card
    if card_k > 0:
        k, sc = pop(T, 5.6, 0.3)
        a = card(cx, 120, 260, 840, 520, k, fill=hx("#0f0d18"), sc=sc)
        cx.rectangle(60, 70, 18, 120)
        src(cx, hx("#ffc847"))
        cx.fill()
        text(cx, "NIGHT MOVERS", 110, 150, 78, hx("#ffffff"), anchor="l")
        text(cx, "夜逃げ屋", 112, 235, 60, hx("#ff8cc6"), font=JP_FONT, anchor="l")
        cx.rectangle(60, 290, 720, 3)
        src(cx, (1, 1, 1, 0.15))
        cx.fill()
        text(cx, "24/7  ·  LEAVE NO TRACE", 60, 370, 44, hx("#ffc847"), anchor="l")
        text(cx, "Confidentiality guaranteed.", 60, 440, 38, (1, 1, 1, 0.75), anchor="l")
        card_end(cx, a)


def office_box_hold(cx, hl, hr, s):
    x = (hl[0] + hr[0]) / 2
    y = (hl[1] + hr[1]) / 2 + 6 * s
    S.box(cx, x, y + 10 * s, 34 * s, 20 * s, taped=False)
    # plant + mug sticking out
    cx.rectangle(x - 10 * s, y - 26 * s, 2.5 * s, 10 * s)
    src(cx, hx("#3f7a4a"))
    cx.fill()
    for dx, dy in ((-12, -28), (-7, -31), (-14, -24)):
        ellipse(cx, x + dx * s, y + dy * s, 4 * s, 2.2 * s)
        src(cx, hx("#4f9a5a"))
        cx.fill_preserve()
        ink(cx, 1.2 * s)
    rrect(cx, x + 4 * s, y - 20 * s, 7 * s, 8 * s, 1.5 * s)
    src(cx, hx("#e9e4da"))
    cx.fill_preserve()
    ink(cx, 1.4 * s)


def shot_lostjob(cx, t, d, T):
    cam(cx, t, d, 1.25, 1.32, (540, 1120), (540, 1100))
    apt_bg(cx, T)
    person(cx, 520, 1780, 900, "son",
           dict(arms=(-28, -55, 28, 55), eyes="dot", brow="sad", mouth="frown", look=(0, 0.8),
                hold=office_box_hold), light=(1, WARM), t=T)


def debt_sheet(cx, x, y, rot, title, jp, amount, stamp_k, sc=1.0):
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(sc, sc)
    cx.save()
    cx.translate(14, 22)
    rrect(cx, -260, -340, 520, 680, 6)
    src(cx, (0, 0, 0, 0.35))
    cx.fill()
    cx.restore()
    rrect(cx, -260, -340, 520, 680, 6)
    lin(cx, 0, -340, 0, 340, [(0, hx("#f7f3ea")), (1, hx("#e6dfcf"))])
    cx.fill()
    text(cx, jp, -220, -255, 46, hx("#1b1b22"), font=JP_FONT, anchor="l")
    text(cx, title, -220, -195, 40, hx("#1b1b22"), anchor="l")
    for k in range(5):
        cx.rectangle(-220, -140 + k * 42, 440 - (k % 3) * 70, 12)
        src(cx, hx("#c9c1b0"))
        cx.fill()
    text(cx, "AMOUNT DUE", -220, 120, 28, hx("#6a6a72"), anchor="l")
    text(cx, amount, -220, 190, 64, hx("#1b1b22"), anchor="l")
    if stamp_k > 0:
        sk = back_out(stamp_k, 2.2)
        cx.save()
        cx.translate(90, 255)
        cx.rotate(-0.22)
        cx.scale(lerp(1.8, 1.0, sk), lerp(1.8, 1.0, sk))
        rrect(cx, -150, -46, 300, 92, 10)
        src(cx, alpha(hx("#d2232a"), 0.9 * min(1, stamp_k * 3)))
        cx.set_line_width(8)
        cx.stroke()
        text(cx, "OVERDUE", 0, 22, 56, alpha(hx("#d2232a"), 0.9 * min(1, stamp_k * 3)))
        cx.restore()
    cx.restore()


def shot_debt(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.1, (540, 900), (540, 880), hh=1.5)
    # dark wood table top-down
    lin(cx, 0, 0, W, H, [(0, hx("#3a2416")), (1, hx("#1d120b"))])
    cx.paint()
    for k in range(26):
        cx.rectangle(0, k * 76, W, 3)
        src(cx, (0, 0, 0, 0.18))
        cx.fill()
    glow(cx, 540, 700, 900, WARM, 0.12)
    sheets = [(7.93, 300, 760, -0.18, "DEBT NOTICE", "督促状", "¥96,400"),
              (8.25, 760, 860, 0.16, "FINAL NOTICE", "最終催告", "¥1,250,000"),
              (8.6, 520, 1020, -0.05, "PAYMENT DEMAND", "支払督促", "¥480,000")]
    for t0, x, y, r, ti, jp, am in sheets:
        k = eout(prog(T, t0, t0 + 0.28))
        if k <= 0:
            continue
        debt_sheet(cx, lerp(x + 700 * (1 if x > 540 else -1), x, k), lerp(y - 300, y, k), r * k, ti, jp, am,
                   prog(T, t0 + 0.35, t0 + 0.55), sc=0.95)
    cx.rectangle(-300, -300, W + 600, H + 600)
    src(cx, (0, 0, 0, 0.0))
    cx.fill()


def shot_family(cx, t, d, T):
    k = eio(prog(T, 9.9, 10.9))
    cam(cx, t, d, lerp(1.3, 1.9, k), lerp(1.3, 1.9, k), (620, 1060), (lerp(620, 900, k), lerp(1060, 860, k)))
    apt_bg(cx, T)
    glow(cx, 930, 820, 160, WARM, 0.2 * k)
    person(cx, 420, 1700, 880, "son",
           dict(face="left", eyes="dot", brow="sad", mouth="wavy", look=(-1, 0.6), sweat=1.0,
                arms=(5, 10, -5, -10)), light=(1, WARM), t=T)


def screen_call(cx, w, h, T, t):
    lin(cx, 0, 0, 0, h, [(0, hx("#1b2a3c")), (1, hx("#0b1018"))])
    cx.paint()
    S.status_bar(cx, w, T, time_s="23:58")
    text(cx, "calling...", w / 2, 230, 34, (1, 1, 1, 0.6))
    # avatar
    pul = 0.5 + 0.5 * math.sin(t * 6)
    cx.arc(w / 2, 420, 110 + pul * 18, 0, 2 * math.pi)
    src(cx, (1, 0.78, 0.28, 0.12))
    cx.fill()
    cx.arc(w / 2, 420, 100, 0, 2 * math.pi)
    src(cx, hx("#ffc847"))
    cx.fill()
    text(cx, "夜", w / 2, 455, 100, hx("#1b1b22"), font=JP_FONT)
    text(cx, "Night Movers", w / 2, 610, 52, hx("#ffffff"))
    text(cx, "夜逃げ屋  ·  0120-24-00", w / 2, 670, 30, (1, 1, 1, 0.6), font=JP_FONT)
    for k, ic in enumerate(("mute", "keypad", "speaker")):
        cx.arc(w / 2 + (k - 1) * 150, 840, 52, 0, 2 * math.pi)
        src(cx, (1, 1, 1, 0.14))
        cx.fill()
    cx.arc(w / 2, 1000, 62, 0, 2 * math.pi)
    src(cx, hx("#ff3b30"))
    cx.fill()
    cx.save()
    cx.translate(w / 2, 1000)
    cx.rotate(2.36)
    rrect(cx, -32, -10, 64, 20, 10)
    src(cx, (1, 1, 1, 1))
    cx.fill()
    cx.restore()


def screen_lock(cx, w, h, T, t):
    lin(cx, 0, 0, w, h, [(0, hx("#2a1458")), (0.6, hx("#6b2a8a")), (1, hx("#c0397a"))])
    cx.paint()
    S.status_bar(cx, w, T, time_s="23:59" if T < 12.45 else "00:00")
    text(cx, "Friday, March 13", w / 2, 230, 34, (1, 1, 1, 0.8))
    flip = prog(T, 12.38, 12.5)
    clock = "23:59" if T < 12.44 else "00:00"
    cx.save()
    cx.translate(w / 2, 400)
    cx.scale(1, 1 - 0.85 * math.sin(flip * math.pi))
    text(cx, clock, 0, 60, 190, (1, 1, 1, 0.96))
    cx.restore()
    nk = eout(prog(T, 12.55, 12.85))
    if nk > 0:
        y = lerp(560, 640, nk)
        cx.push_group()
        rrect(cx, 30, y, w - 60, 190, 30)
        src(cx, (1, 1, 1, 0.22))
        cx.fill()
        rrect(cx, 60, y + 34, 44, 44, 10)
        src(cx, hx("#ffc847"))
        cx.fill()
        text(cx, "夜", 82, y + 70, 34, hx("#1b1b22"), font=JP_FONT)
        text(cx, "NIGHT MOVERS", 124, y + 68, 28, (1, 1, 1, 0.9), anchor="l")
        text(cx, "now", w - 60, y + 68, 24, (1, 1, 1, 0.6), anchor="r")
        text(cx, "Crew on the way.", 60, y + 122, 34, (1, 1, 1, 1), anchor="l")
        text(cx, "Keep the lights off.", 60, y + 166, 34, (1, 1, 1, 1), anchor="l")
        cx.pop_group_to_source()
        cx.paint_with_alpha(nk)


def screen_dead(cx, w, h, T, t):
    lin(cx, 0, 0, 0, h, [(0, hx("#2a0a10")), (1, hx("#0c0306"))])
    cx.paint()
    S.status_bar(cx, w, T, signal=False, time_s="00:41")
    k = eout(prog(T, 20.2, 20.5))
    cx.save()
    cx.translate(w / 2, 420)
    cx.scale(lerp(0.6, 1, k), lerp(0.6, 1, k))
    # antenna icon crossed
    cx.move_to(0, 90)
    cx.line_to(0, -40)
    for r in (40, 75):
        cx.new_sub_path()
        cx.arc(0, -40, r, -2.4, -0.74)
    src(cx, alpha(hx("#ff4d5a"), k))
    cx.set_line_width(14)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.move_to(-110, 110)
    cx.line_to(110, -150)
    cx.set_line_width(16)
    cx.stroke()
    cx.restore()
    text(cx, "LINE", w / 2, 680, 76, alpha(hx("#ffffff"), k))
    text(cx, "CANCELLED", w / 2, 765, 76, alpha(hx("#ffffff"), k))
    text(cx, "This number is no longer in service.", w / 2, 850, 27, alpha(hx("#ffb3b9"), k * 0.85))


def phone_bg(cx, T, tint=WARM):
    lin(cx, 0, 0, 0, H, [(0, hx("#2b1a10")), (1, hx("#120a06"))])
    cx.paint()
    for k in range(30):
        cx.rectangle(0, k * 66 + 20, W, 3)
        src(cx, (0, 0, 0, 0.22))
        cx.fill()
    glow(cx, 540, 820, 800, tint, 0.10)


def shot_phone(screen):
    def fn(cx, t, d, T):
        cam(cx, t, d, 1.0, 1.05, (540, 900), (540, 880), hh=1.3)
        tint = {screen_call: hx("#7fb0ff"), screen_lock: hx("#c35cff"), screen_dead: hx("#ff4d5a")}[screen]
        phone_bg(cx, T, tint)
        S.phone(cx, 540, 860, 600, 1200, lambda c, w, h: screen(c, w, h, T, t), tilt=-0.03)
        glow(cx, 540, 860, 520, tint, 0.10)
    return fn


def shot_van_arrive(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.07, (560, 1120), (600, 1180))
    paint_layer(cx, cached_layer("street", S.street_static))
    k = eout(prog(T, 13.0, 14.6))
    x = lerp(1450, 640, k)
    lights = 1.0 if T < 14.15 else max(0.0, 1 - (T - 14.15) * 8)
    S.van(cx, x, 1560, 1.05, lights=lights, t=-x / 50)
    cx.rectangle(-400, -400, W + 800, H + 800)
    src(cx, (0.0, 0.0, 0.05, 0.12 * (1 - lights)))
    cx.fill()


def shot_crew(cx, t, d, T):
    cam(cx, t, d, 1.2, 1.26, (520, 1150), (500, 1140))
    apt_bg(cx, T, lamp=0.35, dim=0.28)
    # door opening: dark doorway in shoji
    k = eout(prog(T, 15.6, 16.0))
    cx.rectangle(50, 380, 300 * 0.55 * k, 800)
    src(cx, hx("#06070c"))
    cx.fill()
    for i, (x1, t0) in enumerate(((210, 15.75), (420, 16.05), (630, 16.35))):
        kk = eout(prog(T, t0, t0 + 0.9))
        if kk <= 0:
            continue
        x = lerp(80, x1, kk)
        bob = abs(math.sin(T * 9 + i)) * 10 * (1 - kk)
        person(cx, x, 1700 + i * 18 - bob, 820, "mover",
               dict(face="right" if kk < 1 else "front", arms=(8, 15, -8, -15), eyes="dot", look=(0.6, 0)),
               light=(1, WARM), t=T + i)
    person(cx, 900, 1760, 840, "son",
           dict(face="left", eyes="dot", brow="sad", mouth="flat", look=(-1, 0.2), arms=(5, 10, -5, -10)),
           light=(-1, COLD), t=T)
    glow(cx, 330, 1150, 200, COLD, 0.1)


def shot_pack(cx, t, d, T):
    cam(cx, t, d, 1.2, 1.24, (540, 1150), (540, 1140))
    k = prog(T, 17.45, 18.9)
    apt_bg(cx, T, lamp=0.35, books_keep=1 - k, photo=k < 0.6, dim=0.28)
    # boxes stacking on left
    spots = [(170, 1720, 230, 170), (420, 1740, 220, 160), (180, 1550, 210, 150), (660, 1760, 200, 150)]
    for i, (x, y, w, h) in enumerate(spots):
        t0 = 17.5 + i * 0.35
        kk = back_out(prog(T, t0, t0 + 0.25), 1.6)
        if kk <= 0:
            continue
        cx.save()
        cx.translate(x, y)
        cx.scale(1, kk)
        S.box(cx, 0, 0, w, h)
        cx.restore()
    mover_x = lerp(780, 300, smooth((T * 0.8) % 1.0))
    person(cx, mover_x, 1640, 780, "mover",
           dict(face="left", arms=(-35, -50, 35, 50), eyes="dot",
                hold=lambda c, hl, hr, s: S.box(c, (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2 + 10 * s, 34 * s,
                                                24 * s)), light=(1, WARM), t=T)
    person(cx, 920, 1780, 820, "son",
           dict(face="front", eyes="dot", brow="sad", mouth="flat", look=(-0.6, 0.5), arms=(-25, -50, 25, 50),
                hold=lambda c, hl, hr, s: plant(c, (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2, s)),
           light=(-1, COLD), t=T)


def plant(cx, x, y, s):
    poly(cx, [(x - 8 * s, y - 6 * s), (x + 8 * s, y - 6 * s), (x + 6 * s, y + 8 * s), (x - 6 * s, y + 8 * s)])
    src(cx, hx("#b5653c"))
    cx.fill_preserve()
    ink(cx, 1.4 * s)
    for dx, dy, r in ((-6, -14, 0.6), (5, -16, -0.5), (0, -22, 0.1), (-9, -20, 0.9), (8, -9, -1.0)):
        cx.save()
        cx.translate(x + dx * s, y + dy * s)
        cx.rotate(r)
        ellipse(cx, 0, 0, 3.5 * s, 7 * s)
        src(cx, hx("#4f9a5a"))
        cx.fill_preserve()
        ink(cx, 1.2 * s)
        cx.restore()


def shot_boxlabel(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.06, (540, 900), (540, 900))
    lin(cx, 0, 0, 0, H, [(0, hx("#2a1d14")), (1, hx("#120b07"))])
    cx.paint()
    glow(cx, 540, 700, 900, WARM, 0.15)
    # box front close-up
    rrect(cx, 60, 300, 960, 1500, 10)
    lin(cx, 60, 0, 1020, 0, [(0, hx("#c99a5a")), (1, hx("#a87c42"))])
    cx.fill()
    cx.rectangle(470, 300, 140, 1500)
    src(cx, hx("#e2cc9a"))
    cx.fill()
    for k in range(40):
        cx.rectangle(60, 300 + k * 38, 960, 2)
        src(cx, (0, 0, 0, 0.04))
        cx.fill()
    cx.save()
    cx.translate(540, 820)
    cx.rotate(-0.04)
    rrect(cx, -330, -200, 660, 400, 8)
    src(cx, hx("#f7f2e4"))
    cx.fill()
    text(cx, "BOX 1/4", 0, -40, 120, hx("#1d1d26"))
    k = prog(T, 19.4, 20.0)
    s_ = "inside: everything"
    n = int(len(s_) * k)
    text(cx, s_[:n], 0, 100, 58, hx("#2a3c8a"), font=MONO, bold=True)
    cx.restore()


def fee_card(cx, T):
    k, sc = pop(T, 22.0, 0.3)
    if k <= 0:
        return
    a = card(cx, 90, 190, 900, 560, k, fill=hx("#f6f0e2"), sc=sc)
    rrect(cx, 0, 0, 900, 120, 26)
    src(cx, hx("#1a2140"))
    cx.fill()
    cx.rectangle(0, 80, 900, 40)
    cx.fill()
    text(cx, "SERVICE FEE", 450, 82, 54, hx("#ffc847"), spacing=3)
    # amount
    if T < 22.86:
        val = None
    elif T < 23.9:
        val = 50000
    else:
        val = int(lerp(50000, 300000, eio(prog(T, 23.9, 24.6))) / 1000) * 1000
    if val:
        s_ = "¥{:,}".format(val)
        text(cx, s_, 450, 330, 150, hx("#16161c"))
    else:
        text(cx, "¥ ?", 450, 330, 150, hx("#9a958a"))
    lbl_k = prog(T, 24.6, 24.9)
    if T >= 22.86 and T < 24.0:
        text(cx, "AROUND  ·  simple move", 450, 420, 42, hx("#55606f"))
    if lbl_k > 0:
        text(cx, "UP TO  ·  complicated move", 450, 420, 42, alpha(hx("#b2342e"), lbl_k))
    text(cx, "Prices vary by company and job", 450, 505, 30, hx("#8a8577"))
    card_end(cx, a)


def office_static(cx):
    lin(cx, 0, 0, 0, H, [(0, hx("#1a1424")), (1, hx("#0d0a12"))])
    cx.paint()
    # window blinds with neon
    cx.rectangle(140, 820, 800, 520)
    lin(cx, 0, 820, 0, 1340, [(0, hx("#3a1b4a")), (1, hx("#ff4fa3"))])
    cx.fill()
    for k in range(18):
        cx.rectangle(140, 820 + k * 29, 800, 14)
        src(cx, hx("#1d1426"))
        cx.fill()
    glow(cx, 540, 1100, 600, hx("#ff4fa3"), 0.15)
    # desk
    poly(cx, [(-50, 1560), (1130, 1560), (1130, H), (-50, H)])
    lin(cx, 0, 1560, 0, H, [(0, hx("#4a2c1a")), (1, hx("#1e110a"))])
    cx.fill()
    cx.rectangle(-50, 1540, 1180, 30)
    src(cx, hx("#6a412a"))
    cx.fill()


def shot_fee(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.05, (540, 1000), (540, 980))
    paint_layer(cx, cached_layer("office", office_static))
    person(cx, 540, 1840, 960, "rep",
           dict(legs=False, arms=(-35, -70, 35, 70), mouth="smirk" if int(T * 7) % 3 else "o", look=(0, 0.2)),
           light=(-1, hx("#ff8cc6")), t=T)
    cx.rectangle(-50, 1560, 1180, 400)
    lin(cx, 0, 1560, 0, H, [(0, hx("#5a3520")), (1, hx("#1e110a"))])
    cx.fill()
    cx.rectangle(-50, 1540, 1180, 30)
    src(cx, hx("#7a4a2e"))
    cx.fill()
    # folder + pen
    poly(cx, [(300, 1580), (720, 1580), (760, 1700), (260, 1700)])
    src(cx, hx("#2c3550"))
    cx.fill_preserve()
    ink(cx, 4)
    fee_card(cx, T)


def flipboard(cx, T, x, y):
    w, h = 900, 300
    rrect(cx, x - w / 2, y, w, h, 20)
    src(cx, hx("#101216"))
    cx.fill_preserve()
    ink(cx, 6, hx("#000000"))
    text(cx, "DESTINATION", x, y + 60, 38, hx("#ffc847"), spacing=6)
    names = ["TOKYO", "SENDAI", "NAGOYA", "OSAKA", "FUKUOKA", "SAPPORO", "?????", "SHINMACHI"]
    k = prog(T, 27.2, 28.6)
    idx = min(len(names) - 1, int(k * (len(names) - 1) + 0.0001)) if k < 1 else len(names) - 1
    name = names[idx]
    sub = k * (len(names) - 1) % 1.0 if k < 1 else 0
    rrect(cx, x - w / 2 + 40, y + 95, w - 80, 170, 12)
    src(cx, hx("#1f232b"))
    cx.fill()
    cx.rectangle(x - w / 2 + 40, y + 178, w - 80, 4)
    src(cx, hx("#000000"))
    cx.fill()
    cx.save()
    cx.translate(x, y + 180)
    cx.scale(1, 1 - 0.8 * math.sin(sub * math.pi) if k < 1 else 1)
    if name == "SHINMACHI":
        text(cx, "新町", -250, 40, 96, hx("#ffffff"), font=JP_FONT)
        text(cx, "SHINMACHI", 110, 36, 82, hx("#ffffff"))
    else:
        text(cx, name, 0, 36, 96, hx("#ffffff"), spacing=8)
    cx.restore()


def highway_static(cx):
    lin(cx, 0, 0, 0, 1200, [(0, hx("#2a3a6e")), (0.55, hx("#9b7aa0")), (1, hx("#f2a76b"))])
    cx.rectangle(0, 0, W, 1250)
    cx.fill()
    glow(cx, 780, 1150, 520, hx("#ffcf8a"), 0.5)
    # mountains
    for k, (col, base, amp) in enumerate(((hx("#5a5a86"), 1080, 220), (hx("#3e3f6a"), 1180, 160))):
        cx.move_to(0, 1300)
        for i in range(0, 1101, 50):
            cx.line_to(i, base - amp * (0.5 + 0.5 * math.sin(i * 0.008 + k * 2) * math.cos(i * 0.013)))
        cx.line_to(W, 1300)
        cx.close_path()
        src(cx, col)
        cx.fill()
    S.skyline(cx, 560, 1100, 400, 140, seed=21, dawn=0.8, lit=0.2)
    # elevated road
    poly(cx, [(0, 1330), (W, 1250), (W, 1420), (0, 1560)])
    lin(cx, 0, 1250, 0, 1560, [(0, hx("#3a3a4e")), (1, hx("#22222e"))])
    cx.fill()
    poly(cx, [(0, 1560), (W, 1420), (W, 1460), (0, 1610)])
    src(cx, hx("#7a7a90"))
    cx.fill()
    for k in range(6):
        cx.rectangle(80 + k * 190, 1460 + (5 - k) * 0, 30, 600)
        src(cx, hx("#2a2a38"))
        cx.fill()
    lin(cx, 0, 1600, 0, H, [(0, hx("#2a2440")), (1, hx("#120f1e"))])
    cx.rectangle(0, 1610, W, H)
    cx.fill()


def shot_highway(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.04, (540, 1000), (560, 1000))
    paint_layer(cx, cached_layer("hwy", highway_static))
    x = lerp(900, 380, t / d)
    S.van(cx, x, 1450 - (x - 540) * 0.075, 0.85, lights=0.6, t=-x / 30, dawn=0.6)
    flipboard(cx, T, 540, 300)


def small_room_static(cx, dawn=1.0):
    lin(cx, 0, 0, 0, 1300, [(0, hx("#8d8577")), (1, hx("#b3a993"))])
    cx.rectangle(0, 0, W, 1300)
    cx.fill()
    # single window
    wx, wy, ww, wh = 600, 420, 300, 360
    S.skyline(cx, wx, wy, ww, wh, seed=31, dawn=dawn, lit=0.3)
    glow(cx, wx + ww / 2, wy + wh, 420, hx("#ffcf8a"), 0.35 * dawn)
    for (rx, ry, rw, rh) in [(wx - 14, wy - 14, ww + 28, 14), (wx - 14, wy + wh, ww + 28, 18),
                             (wx - 14, wy, 14, wh), (wx + ww, wy, 14, wh), (wx + ww / 2 - 5, wy, 10, wh)]:
        cx.rectangle(rx, ry, rw, rh)
        src(cx, hx("#e9e3d6"))
        cx.fill()
    # light shaft on floor
    cx.save()
    cx.set_operator(cairo.OPERATOR_ADD)
    lin(cx, 0, 1300, 0, 1900, [(0, alpha(hx("#ffcf8a"), 0.18 * dawn)), (1, alpha(hx("#ffcf8a"), 0))])
    poly(cx, [(560, 1300), (920, 1300), (1000, 1900), (380, 1900)])
    cx.fill()
    cx.restore()
    lin(cx, 0, 1300, 0, H, [(0, hx("#7a6b55")), (1, hx("#4a3f30"))])
    cx.rectangle(0, 1300, W, H)
    cx.fill()
    cx.rectangle(0, 1290, W, 14)
    src(cx, hx("#5a4c3a"))
    cx.fill()
    S.box(cx, 180, 1420, 200, 150)
    S.box(cx, 220, 1290, 160, 120)


def shot_newroom(cx, t, d, T):
    cam(cx, t, d, 1.15, 1.22, (560, 1180), (560, 1160))
    paint_layer(cx, cached_layer("smallroom", small_room_static))
    k = eout(prog(T, 29.2, 29.7))
    awake = T > 30.15
    person(cx, 600, lerp(1960, 1780, k), 820, "son",
           dict(legs=False, eyes="wide" if awake else "sleepy", mouth="o" if awake else "flat", brow="sad",
                look=(-0.8 if awake else 0, 0), arms=(10, 20, -60, -100) if not awake else (30, 40, -30, -40)),
           light=(1, hx("#ffd59a")), t=T)
    # futon + blanket
    poly(cx, [(170, 1640), (980, 1640), (1040, 1860), (110, 1860)])
    src(cx, hx("#e9e4d8"))
    cx.fill_preserve()
    ink(cx, 5)
    poly(cx, [(260, 1610), (1000, 1600), (1060, 1840), (220, 1860)])
    lin(cx, 0, 1600, 0, 1860, [(0, hx("#3c5a8a")), (1, hx("#25406a"))])
    cx.fill_preserve()
    ink(cx, 5)
    for k_ in range(5):
        for j in range(4):
            cx.rectangle(300 + k_ * 150, 1630 + j * 55, 60, 22)
            src(cx, (1, 1, 1, 0.08))
            cx.fill()


def lane_static(cx):
    lin(cx, 0, 0, 0, 900, [(0, hx("#9aa6b5")), (1, hx("#c9cdd3"))])
    cx.rectangle(0, 0, W, 900)
    cx.fill()
    S.skyline(cx, 0, 560, W, 340, seed=41, dawn=0.35, lit=0.05)
    # houses both sides in perspective
    poly(cx, [(0, 200), (330, 560), (330, 1400), (0, 1600)])
    lin(cx, 0, 0, 330, 0, [(0, hx("#7d6f65")), (1, hx("#a29384"))])
    cx.fill()
    for k in range(3):
        poly(cx, [(20, 700 + k * 240), (230, 760 + k * 230), (230, 880 + k * 220), (20, 850 + k * 230)])
        src(cx, hx("#5b5a63"))
        cx.fill()
    poly(cx, [(W, 300), (740, 600), (740, 1380), (W, 1560)])
    lin(cx, 740, 0, W, 0, [(0, hx("#d9d4cc")), (1, hx("#b3aca2"))])
    cx.fill()
    # koban on right
    poly(cx, [(760, 900), (1000, 820), (1000, 1420), (760, 1370)])
    src(cx, hx("#efefef"))
    cx.fill()
    poly(cx, [(740, 900), (1020, 800), (1020, 840), (740, 930)])
    src(cx, hx("#3a4660"))
    cx.fill()
    cx.arc(880, 790, 22, 0, 2 * math.pi)
    src(cx, hx("#ff3b30"))
    cx.fill()
    glow(cx, 880, 790, 120, hx("#ff3b30"), 0.4)
    poly(cx, [(800, 1080), (950, 1040), (950, 1400), (800, 1390)])
    src(cx, hx("#7fa0c0"))
    cx.fill()
    # sign
    poly(cx, [(780, 950), (990, 885), (990, 980), (780, 1040)])
    src(cx, hx("#ffffff"))
    cx.fill_preserve()
    ink(cx, 4)
    cx.save()
    cx.translate(885, 980)
    cx.rotate(-0.3)
    text(cx, "交番", -40, 0, 50, hx("#1a2240"), font=JP_FONT)
    text(cx, "KOBAN", 58, -4, 30, hx("#1a2240"))
    cx.restore()
    # ground
    poly(cx, [(0, 1600), (330, 1400), (740, 1380), (W, 1560), (W, H), (0, H)])
    lin(cx, 0, 1380, 0, H, [(0, hx("#8a8c91")), (1, hx("#55575c"))])
    cx.fill()


def shot_mom_street(cx, t, d, T):
    cam(cx, t, d, 1.05, 1.12, (480, 1250), (620, 1200))
    paint_layer(cx, cached_layer("lane", lane_static))
    k = prog(T, 30.9, 33.3)
    x = lerp(220, 660, k)
    bob = abs(math.sin(T * 10)) * 14
    person(cx, x, 1700 - bob, 760, "mom",
           dict(face="right", eyes="dot", brow="sad", mouth="wavy", look=(1, 0), sweat=0.6,
                arms=(-30 * math.sin(T * 10), -10, 30 * math.sin(T * 10), 10)), light=(-1, hx("#e8eef8")), t=T)


def koban_static(cx):
    lin(cx, 0, 0, 0, 1300, [(0, hx("#e8ecef")), (1, hx("#cfd6dc"))])
    cx.rectangle(0, 0, W, 1300)
    cx.fill()
    for i, (x, col) in enumerate(((140, hx("#d84a3a")), (600, hx("#2f6ab0")), (800, hx("#e2a830")))):
        rrect(cx, x, 760, 170, 230, 6)
        src(cx, hx("#ffffff"))
        cx.fill_preserve()
        ink(cx, 3, hx("#9aa3ad"))
        cx.rectangle(x, 760, 170, 50)
        src(cx, col)
        cx.fill()
        for k in range(4):
            cx.rectangle(x + 18, 840 + k * 30, 130 - k * 15, 10)
            src(cx, hx("#c3cad1"))
            cx.fill()
    lin(cx, 0, 1300, 0, H, [(0, hx("#b9c0c6")), (1, hx("#8a9299"))])
    cx.rectangle(0, 1300, W, H)
    cx.fill()
    for k in range(10):
        cx.rectangle(k * 120, 1300, 3, 700)
        src(cx, (1, 1, 1, 0.2))
        cx.fill()
    light_cone(cx, 540, 0, 400, 1100, 1400, hx("#ffffff"), 0.08)


def checklist(cx, T):
    k, sc = pop(T, 33.5, 0.3)
    if k <= 0:
        return
    a = card(cx, 110, 170, 860, 560, k, fill=hx("#ffffff"), sc=sc)
    rows = [("ADULT", 33.83, True), ("LEFT BY CHOICE", 34.68, True), ("SIGN OF A CRIME", 36.27, False)]
    for i, (lbl, t0, ok) in enumerate(rows):
        y = 110 + i * 120
        text(cx, lbl, 60, y, 50, hx("#2a3550"), anchor="l")
        kk = prog(T, t0, t0 + 0.2)
        if kk > 0:
            cx.save()
            cx.translate(770, y - 18)
            cx.scale(back_out(kk), back_out(kk))
            if ok:
                cx.move_to(-30, 0)
                cx.line_to(-8, 24)
                cx.line_to(34, -28)
                src(cx, hx("#2fa36b"))
            else:
                cx.move_to(-26, -26)
                cx.line_to(26, 26)
                cx.move_to(26, -26)
                cx.line_to(-26, 26)
                src(cx, hx("#d8392f"))
            cx.set_line_width(13)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.stroke()
            cx.restore()
    cx.rectangle(60, 395, 740, 4)
    src(cx, hx("#d8392f"))
    cx.fill()
    kk = prog(T, 37.4, 37.7)
    if kk > 0:
        text(cx, "→ USUALLY NO ACTIVE SEARCH", 60, 480, 46, alpha(hx("#d8392f"), kk), anchor="l")
    card_end(cx, a)


def shot_koban(cx, t, d, T):
    k = eio(prog(T, 37.3, 38.4))
    cam(cx, t, d, lerp(1.0, 1.25, k), lerp(1.04, 1.25, k), (540, 1100), (lerp(540, 690, k), lerp(1100, 1050, k)))
    paint_layer(cx, cached_layer("koban", koban_static))
    person(cx, 700, 1760, 860, "cop",
           dict(legs=False, eyes="dot", mouth="flat" if T < 37.3 else "wavy", brow="none" if T < 37.3 else "sad",
                sweat=prog(T, 37.4, 37.8), look=(-0.7, 0.2), arms=(-30, -60, 30, 60)),
           light=(-1, hx("#ffffff")), t=T)
    # counter
    poly(cx, [(-50, 1450), (1130, 1450), (1130, H), (-50, H)])
    lin(cx, 0, 1450, 0, H, [(0, hx("#d9dde2")), (1, hx("#9aa1a8"))])
    cx.fill()
    cx.rectangle(-50, 1430, 1180, 34)
    src(cx, hx("#6b7480"))
    cx.fill()
    person(cx, 260, 1900, 900, "mom",
           dict(face="right", eyes="dot", brow="sad", mouth="frown", look=(1, -0.2), arms=(-10, -20, -60, -90)),
           light=(1, hx("#ffffff")), t=T)
    checklist(cx, T)


def shot_cabinet(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.05, (540, 960), (540, 980), hh=1.2)
    lin(cx, 0, 0, 0, H, [(0, hx("#1d222b")), (1, hx("#0c0f14"))])
    cx.paint()
    light_cone(cx, 540, 0, 200, 1100, 1600, hx("#cfe0ff"), 0.07)
    rrect(cx, 190, 260, 700, 1500, 14)
    lin(cx, 190, 0, 890, 0, [(0, hx("#6a7280")), (0.5, hx("#8c94a2")), (1, hx("#5a616d"))])
    cx.fill_preserve()
    ink(cx, 6)
    k = eio(prog(T, 38.85, 39.2))
    for i in range(4):
        y = 300 + i * 360
        out = 0 if i != 1 else lerp(160, 0, k)
        cx.save()
        cx.translate(0, 0)
        if out:
            poly(cx, [(225, y), (855, y), (855 + out * 0.3, y - out * 0.5), (225 + out * 0.3, y - out * 0.5)])
            src(cx, hx("#a9b0bb"))
            cx.fill()
            # folder sticking
            rrect(cx, 400, y - out * 0.5 - 60, 280, 90, 6)
            src(cx, hx("#e6c88a"))
            cx.fill_preserve()
            ink(cx, 3)
        rrect(cx, 225 + out * 0.3, y + 10 - out * 0.5 * 0, 630, 320, 10)
        lin(cx, 0, y, 0, y + 320, [(0, hx("#9aa2ae")), (1, hx("#757d89"))])
        cx.fill_preserve()
        ink(cx, 4)
        rrect(cx, 440, y + 210, 200, 34, 12)
        src(cx, hx("#3a404a"))
        cx.fill()
        if i == 1:
            rrect(cx, 380, y + 60, 320, 110, 6)
            src(cx, hx("#f4f1e8"))
            cx.fill_preserve()
            ink(cx, 3)
            text(cx, "CLOSED", 540, y + 108, 44, hx("#1d1d26"))
            text(cx, "CASES", 540, y + 152, 36, hx("#1d1d26"))
        cx.restore()
    if T > 39.2:
        shake = (1 - prog(T, 39.2, 39.45)) * 8
        cx.translate(math.sin(T * 90) * shake, 0)


def det_static(cx):
    lin(cx, 0, 0, 0, H, [(0, hx("#3a2617")), (1, hx("#1a0f08"))])
    cx.paint()
    for k in range(12):
        cx.rectangle(k * 96, 0, 4, H)
        src(cx, (0, 0, 0, 0.18))
        cx.fill()
    # corkboard
    rrect(cx, 120, 260, 840, 720, 10)
    src(cx, hx("#5a3a1c"))
    cx.fill()
    rrect(cx, 140, 280, 800, 680, 6)
    src(cx, hx("#c79a62"))
    cx.fill()
    rng = random.Random(9)
    pins = []
    for i, (x, y) in enumerate(((260, 400), (520, 360), (790, 430), (330, 700), (650, 660), (820, 820))):
        cx.save()
        cx.translate(x, y)
        cx.rotate(rng.uniform(-0.15, 0.15))
        cx.rectangle(-80, -70, 160, 140)
        src(cx, hx("#f2efe6"))
        cx.fill()
        cx.rectangle(-64, -56, 128, 100)
        src(cx, hx("#7d8a99") if i != 1 else hx("#9cc3d9"))
        cx.fill()
        if i == 1:
            cx.arc(0, -16, 22, 0, 2 * math.pi)
            src(cx, hx("#f1c7a1"))
            cx.fill()
            cx.arc(0, -22, 23, math.pi, 2 * math.pi)
            src(cx, hx("#1c1a22"))
            cx.fill()
            ellipse(cx, 0, 30, 30, 20)
            src(cx, hx("#283553"))
            cx.fill()
        else:
            text(cx, "?", 0, 18, 64, hx("#ffffff"))
        cx.restore()
        pins.append((x, y - 64))
    cx.move_to(*pins[0])
    for p in pins[1:]:
        cx.line_to(*p)
    src(cx, hx("#c8242a"))
    cx.set_line_width(4)
    cx.stroke()
    for p in pins:
        cx.arc(p[0], p[1], 9, 0, 2 * math.pi)
        src(cx, hx("#d8392f"))
        cx.fill()
    # desk lamp glow
    glow(cx, 920, 1300, 500, WARM, 0.25)
    poly(cx, [(-50, 1600), (1130, 1600), (1130, H), (-50, H)])
    lin(cx, 0, 1600, 0, H, [(0, hx("#4a2c1a")), (1, hx("#1e110a"))])
    cx.fill()


def magnifier(cx, hl, hr, s):
    x, y = hr
    cx.move_to(x, y)
    cx.line_to(x + 6 * s, y - 14 * s)
    src(cx, hx("#3a2616"))
    cx.set_line_width(4 * s)
    cx.stroke()
    cx.arc(x + 9 * s, y - 21 * s, 8 * s, 0, 2 * math.pi)
    src(cx, (0.7, 0.85, 1.0, 0.35))
    cx.fill_preserve()
    src(cx, hx("#c9a24a"))
    cx.set_line_width(2.6 * s)
    cx.stroke()


def shot_detective(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.08, (540, 1000), (540, 1060))
    paint_layer(cx, cached_layer("det", det_static))
    person(cx, 540, 1880, 980, "det",
           dict(eyes="dot", brow="angry", mouth="frown", look=(0.6, -0.4), arms=(10, 20, -60, -110),
                hold=magnifier), light=(1, WARM), t=T)


def shot_denied(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.08, (540, 900), (540, 880), hh=1.2)
    lin(cx, 0, 0, 0, H, [(0, hx("#0b0e16")), (1, hx("#05060a"))])
    cx.paint()
    # monitor
    rrect(cx, 80, 260, 920, 760, 30)
    src(cx, hx("#2a2d35"))
    cx.fill_preserve()
    ink(cx, 6, hx("#000000"))
    rrect(cx, 120, 300, 840, 680, 16)
    lin(cx, 0, 300, 0, 980, [(0, hx("#0c1a2c")), (1, hx("#08111d"))])
    cx.fill()
    cx.rectangle(470, 1020, 140, 120)
    src(cx, hx("#22252c"))
    cx.fill()
    rrect(cx, 330, 1130, 420, 40, 10)
    cx.fill()
    flick = 1 if (int(T * 12) % 9) else 0.7
    text(cx, "> records search: SUBJECT", 160, 380, 34, alpha(hx("#7fe0a0"), flick), font=MONO, anchor="l",
         bold=True)
    k = prog(T, 42.3, 42.5)
    if k > 0:
        blink = 1.0 if T < 43.0 or int(T * 4) % 2 else 0.75
        rrect(cx, 190, 470, 700, 300, 12)
        src(cx, alpha(hx("#d8233a"), k * blink))
        cx.fill()
        text(cx, "ACCESS", 540, 590, 96, alpha(hx("#ffffff"), k))
        text(cx, "DENIED", 540, 700, 96, alpha(hx("#ffffff"), k))
        text(cx, "Personal data  ·  No authorization", 540, 850, 34, alpha(hx("#ff9aa6"), k))
    glow(cx, 540, 640, 650, hx("#d8233a"), 0.22 * k)
    # detective over-shoulder (back of head)
    person(cx, 860, 2260, 1150, "det", dict(face="back"), light=(-1, hx("#ff6f7a")), t=T)


DOTS = S.map_dots(150)
MAPC = (560, 920, 54)


def map_bg(cx, T, dim=0.0):
    lin(cx, 0, 0, 0, H, [(0, hx("#0f2140")), (1, hx("#081326"))])
    cx.paint()
    for k in range(0, W, 60):
        cx.rectangle(k, 0, 1, H)
        src(cx, (1, 1, 1, 0.05))
        cx.fill()
    for k in range(0, H, 60):
        cx.rectangle(0, k, W, 1)
        src(cx, (1, 1, 1, 0.05))
        cx.fill()
    text(cx, "JAPAN", 120, 640, 34, (1, 1, 1, 0.5), anchor="l", spacing=6)
    text(cx, "日本", 120, 690, 40, (1, 1, 1, 0.35), font=JP_FONT, anchor="l")
    cx.save()
    cx.translate(10, 14)
    S.japan_map(cx, *MAPC, fill=(0, 0, 0, 0.35), line=(0, 0, 0, 0), lw=1)
    cx.restore()
    S.japan_map(cx, *MAPC, fill=mixc(hx("#efe6cf"), hx("#3a4660"), dim), line=hx("#0a1020"), lw=5)


def draw_dots(cx, T, appear=(45.0, 49.8), found_t=52.0, vanish_t=54.4):
    for i, (lo, la, r1, r2) in enumerate(DOTS):
        t0 = lerp(appear[0], appear[1], r1)
        k = back_out(prog(T, t0, t0 + 0.25), 2.0)
        if k <= 0:
            continue
        x, y = S.map_xy(lo, la, *MAPC)
        missing = r2 < 0.07
        fk = prog(T, found_t + r1 * 0.9, found_t + r1 * 0.9 + 0.25)
        col = hx("#ffc847")
        if fk > 0 and not missing:
            col = mixc(col, hx("#3ccf7a"), fk)
        a = 1.0
        if missing and T > 52.5:
            col = mixc(col, hx("#e9eef7"), prog(T, 52.5, 53.0))
            a = 1 - prog(T, vanish_t + r1 * 0.6, vanish_t + r1 * 0.6 + 0.5)
            if 53.1 < T < vanish_t + 0.6:
                glow(cx, x, y, 40, hx("#ffffff"), 0.25)
            if a < 1:
                cx.arc(x, y, 9 + (1 - a) * 40, 0, 2 * math.pi)
                src(cx, (1, 1, 1, a * 0.6))
                cx.set_line_width(3)
                cx.stroke()
        if a <= 0:
            continue
        cx.arc(x, y, 9 * k, 0, 2 * math.pi)
        src(cx, alpha(col, a))
        cx.fill_preserve()
        src(cx, alpha(hx("#0a1020"), a))
        cx.set_line_width(2.5)
        cx.stroke()


def stat_card(cx, T):
    k, sc = pop(T, 45.4, 0.3)
    if k <= 0:
        return
    a = card(cx, 90, 120, 900, 400, k, fill=hx("#0b1427"), edge=hx("#ffc847"), sc=sc)
    cx.rectangle(0, 0, 900, 8)
    src(cx, hx("#ffc847"))
    cx.fill()
    v = int(80486 * eout(prog(T, 46.3, 48.3)))
    text(cx, "{:,}".format(v), 450, 175, 150, hx("#ffc847"))
    text(cx, "MISSING-PERSON REPORTS · 2025", 450, 250, 36, hx("#ffffff"))
    kk = prog(T, 49.8, 50.2)
    text(cx, "All causes: illness, family, work, money & more", 450, 310, 30, alpha(hx("#aab8d0"), max(0.0, kk)))
    text(cx, "Source: National Police Agency of Japan", 450, 362, 26, alpha(hx("#7d8aa3"), 1.0))
    card_end(cx, a)


def shot_map(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.04, (540, 900), (540, 900), hh=0.6)
    map_bg(cx, T)
    draw_dots(cx, T)
    stat_card(cx, T)


def shot_found(cx, t, d, T):
    cam(cx, t, d, 1.04, 1.12, (540, 900), (560, 930), hh=0.6)
    map_bg(cx, T)
    draw_dots(cx, T)
    k, sc = pop(T, 52.0, 0.3)
    a = card(cx, 240, 170, 600, 130, k, fill=hx("#3ccf7a"), sc=sc)
    text(cx, "MOST ARE FOUND", 300, 85, 52, hx("#0b1427"))
    card_end(cx, a * (1 - prog(T, 53.0, 53.3)))
    k2, sc2 = pop(T, 53.3, 0.3)
    if k2 > 0:
        a = card(cx, 110, 170, 860, 130, k2, fill=hx("#e9eef7"), sc=sc2)
        text(cx, "SOME ARE NEVER HEARD FROM", 430, 85, 42, hx("#0b1427"))
        card_end(cx, a)


def kanji_evap(cx, T, x, y):
    k = prog(T, 55.7, 56.3)
    ev = prog(T, 58.9, 60.2)
    if k <= 0:
        return
    rng = random.Random(4)
    # solid kanji fading as particles rise
    a = k * (1 - ev)
    for lw, aa in ((30, 0.08), (14, 0.15)):
        text(cx, "蒸発", x, y, 300, alpha(hx("#ffffff"), aa * a), font=JP_FONT, outline=lw,
             ocol=alpha(hx("#ffffff"), aa * a))
    text(cx, "蒸発", x, y, 300, alpha(hx("#ffffff"), a), font=JP_FONT)
    if ev > 0:
        for i in range(90):
            px = x + rng.uniform(-300, 300)
            py = y - rng.uniform(0, 260)
            dy = ev * rng.uniform(150, 600)
            dx = math.sin(ev * 4 + i) * 40 * ev
            rr = rng.uniform(6, 22) * (1 + ev * 2)
            cx.arc(px + dx, py - dy, rr, 0, 2 * math.pi)
            src(cx, (1, 1, 1, 0.35 * (1 - ev) * rng.uniform(0.4, 1)))
            cx.fill()
    k2 = prog(T, 57.6, 58.1)
    text(cx, "JŌHATSU", x, y + 130, 84, alpha(hx("#ffc847"), k2), spacing=10)
    k3 = prog(T, 58.95, 59.3)
    text(cx, "“the evaporated”", x, y + 210, 54, alpha(hx("#dfe7f5"), k3))


def shot_johatsu(cx, t, d, T):
    cam(cx, t, d, 1.12, 1.18, (560, 930), (560, 900), hh=0.5)
    map_bg(cx, T, dim=0.7)
    draw_dots(cx, T)
    cx.rectangle(-300, -300, W + 600, H + 600)
    src(cx, (0.02, 0.04, 0.09, 0.55))
    cx.fill()
    kanji_evap(cx, T, 560, 760)


def kitchen_static(cx):
    lin(cx, 0, 0, 0, 1300, [(0, hx("#3d3328")), (1, hx("#6a5a46"))])
    cx.rectangle(0, 0, W, 1300)
    cx.fill()
    # window dark
    cx.rectangle(120, 380, 320, 420)
    lin(cx, 0, 380, 0, 800, [(0, hx("#0c1430")), (1, hx("#1d2a55"))])
    cx.fill()
    for (rx, ry, rw, rh) in [(110, 370, 340, 12), (110, 800, 340, 14), (110, 370, 12, 440), (440, 370, 12, 440),
                             (275, 370, 8, 440)]:
        cx.rectangle(rx, ry, rw, rh)
        src(cx, hx("#2a2018"))
        cx.fill()
    # cupboards right
    for k in range(2):
        rrect(cx, 640 + k * 210, 300, 190, 300, 6)
        src(cx, hx("#8a6a48"))
        cx.fill_preserve()
        ink(cx, 4)
    cx.rectangle(0, 1290, W, H)
    lin(cx, 0, 1290, 0, H, [(0, hx("#4a3a2a")), (1, hx("#1e160f"))])
    cx.fill()


def report_hold(cx, hl, hr, s):
    x = (hl[0] + hr[0]) / 2
    y = (hl[1] + hr[1]) / 2 + 18 * s
    poly(cx, [(x - 22 * s, y - 28 * s), (x + 22 * s, y - 28 * s), (x + 24 * s, y + 4 * s), (x - 24 * s, y + 4 * s)])
    src(cx, hx("#f3ead6"))
    cx.fill_preserve()
    ink(cx, 1.8 * s)
    text(cx, "REPORT", x, y - 18 * s, 6 * s, hx("#1d1d26"), font=MONO, bold=True)
    for k in range(4):
        cx.rectangle(x - 16 * s, y - 12 * s + k * 4 * s, 32 * s - k * 4 * s, 1.2 * s)
        src(cx, hx("#a59c88"))
        cx.fill()


def shot_mom_report(cx, t, d, T):
    cam(cx, t, d, 1.15, 1.32, (540, 1150), (540, 1100))
    paint_layer(cx, cached_layer("kitchen", kitchen_static))
    S.pendant_lamp(cx, 540, 560, 0.9)
    person(cx, 540, 1800, 900, "mom",
           dict(legs=False, eyes="dot", brow="sad", mouth="frown", look=(0, 0.9), arms=(-12, -28, 12, 28),
                hold=report_hold), light=(1, WARM), t=T)
    poly(cx, [(80, 1560), (1000, 1560), (1060, 1700), (20, 1700)])
    lin(cx, 0, 1560, 0, 1700, [(0, hx("#8a5a34")), (1, hx("#6a4226"))])
    cx.fill_preserve()
    ink(cx, 5)
    cx.rectangle(20, 1700, 1040, 30)
    src(cx, hx("#4a2c18"))
    cx.fill()
    S.tea_cup(cx, 860, 1600, T, steam=0.0)


def shot_report(cx, t, d, T):
    cam(cx, t, d, 1.0, 1.1, (540, 900), (540, 960), hh=0.5)
    lin(cx, 0, 0, 0, H, [(0, hx("#3a2416")), (1, hx("#140b06"))])
    cx.paint()
    glow(cx, 540, 800, 900, WARM, 0.2)
    cx.save()
    cx.translate(540, 900)
    cx.rotate(-0.025)
    cx.save()
    cx.translate(16, 24)
    rrect(cx, -420, -620, 840, 1240, 6)
    src(cx, (0, 0, 0, 0.4))
    cx.fill()
    cx.restore()
    rrect(cx, -420, -620, 840, 1240, 6)
    lin(cx, 0, -620, 0, 620, [(0, hx("#f7f0de")), (1, hx("#e8dcc0"))])
    cx.fill()
    text(cx, "REPORT", -350, -480, 70, hx("#1d1d26"), font=MONO, anchor="l", bold=True)
    cx.rectangle(-350, -455, 700, 4)
    src(cx, hx("#1d1d26"))
    cx.fill()
    text(cx, "Subject: missing-person inquiry", -350, -390, 32, hx("#3a3a44"), font=MONO, anchor="l", bold=True)
    text(cx, "Result:", -350, -320, 32, hx("#3a3a44"), font=MONO, anchor="l", bold=True)
    full = [("Your son", 63.25, 64.1), ("chose to leave.", 64.5, 65.6)]
    for i, (s_, a_, b_) in enumerate(full):
        n = int(len(s_) * prog(T, a_, b_) + 0.999) if T > a_ else 0
        text(cx, s_[:n], -350, -170 + i * 100, 68, hx("#14141a"), font=MONO, anchor="l", bold=True)
    for k in range(6):
        cx.rectangle(-350, 160 + k * 60, 700, 3)
        src(cx, hx("#d9ccb0"))
        cx.fill()
    cx.restore()


def shot_end(cx, t, d, T):
    cam(cx, t, d, 1.1, 1.22, (600, 1100), (650, 1000), hh=0.4)
    paint_layer(cx, cached_layer("smallroom_night", lambda c: small_room_static(c, dawn=0.0)))
    cx.rectangle(-400, -400, W + 800, H + 800)
    src(cx, (0.02, 0.03, 0.1, 0.35))
    cx.fill()
    glow(cx, 750, 600, 260, hx("#9fb8ff"), 0.18)
    person(cx, 720, 1820, 900, "son", dict(face="back"), light=(1, hx("#9fb8ff")), t=T)
    k = prog(T, 66.6, 67.9)
    if k > 0:
        cx.rectangle(-400, -400, W + 800, H + 800)
        src(cx, (0, 0, 0, smooth(k)))
        cx.fill()


from episodes.japan_johatsu.hook import HOOK_SHOTS  # noqa: E402

SHOTS = [
    *HOOK_SHOTS,  # 0.00-3.34 (revised opening; shot_hook above is the original)
    (3.34, 6.86, shot_neon, 0),
    (6.86, 7.93, shot_lostjob, 0),
    (7.93, 9.26, shot_debt, 0),
    (9.26, 11.06, shot_family, 0),
    (11.06, 12.13, shot_phone(screen_call), 0),
    (12.13, 13.00, shot_phone(screen_lock), 0),
    (13.00, 15.71, shot_van_arrive, 0.2),
    (15.71, 17.45, shot_crew, 0),
    (17.45, 19.11, shot_pack, 0),
    (19.11, 20.07, shot_boxlabel, 0),
    (20.07, 21.91, shot_phone(screen_dead), 0),
    (21.91, 27.02, shot_fee, 0),
    (27.02, 29.17, shot_highway, 0.25),
    (29.17, 30.88, shot_newroom, 0.25),
    (30.88, 33.25, shot_mom_street, 0),
    (33.25, 38.49, shot_koban, 0),
    (38.49, 39.53, shot_cabinet, 0),
    (39.53, 41.98, shot_detective, 0),
    (41.98, 44.66, shot_denied, 0),
    (44.66, 51.66, shot_map, 0.3),
    (51.66, 55.58, shot_found, 0),
    (55.58, 60.16, shot_johatsu, 0.4),
    (60.16, 63.19, shot_mom_report, 0.4),
    (63.19, 65.90, shot_report, 0),
    (65.90, END, shot_end, 0.5),
]

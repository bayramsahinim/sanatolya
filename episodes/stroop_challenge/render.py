"""Frame renderer for the Stroop challenge Short (1080x1920, vertical).

Visual language follows the reference: dark navy radial background, cream challenge
cards, yellow HUD (level label + timer bar + level tiles), word-by-word captions at
the top. The Just Needy mascot only appears outside gameplay, in the lower third.
"""
import math

import cairo

from cinecode.characters import HERO, Pose, talk
from cinecode.core import clamp, ease_in, ease_io, ease_out, hexc, mix, rrect, src
from episodes.stroop_challenge import timeline as tl
from episodes.stroop_challenge.script import INK, LEVELS, TOTAL

W, H = 1080, 1920
FONT = "Montserrat ExtraBold"

NAVY_C = hexc("#1F3266")
NAVY_M = hexc("#0E1838")
NAVY_E = hexc("#050815")
CREAM = hexc("#F2ECDD")
CREAM_DK = hexc("#D9D0BA")
HUD = hexc("#F7B928")       # level 1-2 accent
HUD3 = hexc("#FF5533")      # level 3 accent
TRACK = hexc("#1A2547")
WHITE = (1, 1, 1)
DIM = hexc("#8E9BBE")
OK_G = hexc("#1E9E4A")
BAD_R = hexc("#E5352B")

CARD_Y, CARD_H, CARD_X, CARD_W = 625, 360, 45, 990
TOP_CAP_Y = 300


# ============================================================ helpers
def P(t, a, b):
    """0..1 progress of t through [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def font(cx, size):
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)


def tw(cx, s, size):
    font(cx, size)
    return cx.text_extents(s).x_advance


def ctext(cx, s, x, y, size, c, a=1.0, spacing=0.0):
    """Centered text; y is the baseline."""
    font(cx, size)
    if spacing:
        widths = [cx.text_extents(ch).x_advance for ch in s]
        total = sum(widths) + spacing * (len(s) - 1)
        xx = x - total / 2
        src(cx, c, a)
        for ch, w in zip(s, widths):
            cx.move_to(xx, y)
            cx.show_text(ch)
            xx += w + spacing
        return total
    e = cx.text_extents(s)
    cx.move_to(x - e.x_advance / 2, y)
    src(cx, c, a)
    cx.show_text(s)
    return e.x_advance


def fit_size(cx, s, max_w, max_size):
    w = tw(cx, s, 100)
    return min(max_size, 100 * max_w / max(w, 1))


def shadow_rrect(cx, x, y, w, h, r, a=0.5, spread=26, dy=16):
    for i in range(8, 0, -1):
        k = i / 8
        rrect(cx, x - spread * k * 0.5, y + dy - spread * k * 0.3, w + spread * k, h + spread * k, r + spread * k * 0.5)
        src(cx, (0, 0, 0), a * 0.09)
        cx.fill()


def glow(cx, x, y, r, c, a):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    cx.set_source(g)
    cx.arc(x, y, r, 0, 2 * math.pi)
    cx.fill()


def group(cx, alpha, fn, *a, **kw):
    if alpha <= 0.002:
        return
    if alpha >= 0.998:
        fn(*a, **kw)
        return
    cx.push_group()
    fn(*a, **kw)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)


def check_mark(cx, x, y, s, c, lw=None):
    cx.move_to(x - s * 0.5, y)
    cx.line_to(x - s * 0.12, y + s * 0.38)
    cx.line_to(x + s * 0.55, y - s * 0.4)
    src(cx, c)
    cx.set_line_width(lw or s * 0.22)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()


def cross_mark(cx, x, y, s, c, lw=None):
    for dx in (-1, 1):
        cx.move_to(x - s * 0.42 * dx, y - s * 0.42)
        cx.line_to(x + s * 0.42 * dx, y + s * 0.42)
    src(cx, c)
    cx.set_line_width(lw or s * 0.2)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()


def lock_icon(cx, x, y, s, c):
    rrect(cx, x - s * 0.45, y - s * 0.1, s * 0.9, s * 0.7, s * 0.12)
    src(cx, c)
    cx.fill()
    cx.arc(x, y - s * 0.12, s * 0.28, math.pi, 0)
    cx.set_line_width(s * 0.14)
    cx.stroke()


def speaker_icon(cx, x, y, s, c):
    cx.move_to(x - s * 0.5, y - s * 0.18)
    cx.line_to(x - s * 0.22, y - s * 0.18)
    cx.line_to(x + s * 0.08, y - s * 0.45)
    cx.line_to(x + s * 0.08, y + s * 0.45)
    cx.line_to(x - s * 0.22, y + s * 0.18)
    cx.line_to(x - s * 0.5, y + s * 0.18)
    cx.close_path()
    src(cx, c)
    cx.fill()
    cx.set_line_width(s * 0.1)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    for r in (0.3, 0.55):
        cx.arc(x + s * 0.12, y, s * r, -0.8, 0.8)
        cx.stroke()


def pill(cx, x, y, label, bg, fg=WHITE, size=40, icon=None, a=1.0, scale=1.0):
    """Centered pill; returns its width. `scale` is an appear progress (0..1+): the pill
    fades in while growing from 92% to 100% - no overshoot, no hard pop."""
    a *= clamp(scale)
    scale = 0.92 + 0.08 * clamp(scale)
    font(cx, size)
    w = cx.text_extents(label).x_advance
    iw = size * 1.15 if icon else 0
    pw, ph = w + iw + size * 1.2, size * 1.7
    cx.save()
    cx.translate(x, y)
    cx.scale(scale, scale)
    cx.push_group()
    shadow_rrect(cx, -pw / 2, -ph / 2, pw, ph, ph / 2, a=0.35, spread=14, dy=8)
    rrect(cx, -pw / 2, -ph / 2, pw, ph, ph / 2)
    src(cx, bg)
    cx.fill()
    tx = -pw / 2 + size * 0.6
    cx.move_to(tx, size * 0.36)
    src(cx, fg)
    cx.show_text(label)
    if icon == "check":
        check_mark(cx, tx + w + size * 0.68, 0, size * 0.62, fg)
    elif icon == "cross":
        cross_mark(cx, tx + w + size * 0.66, 0, size * 0.55, fg)
    elif icon == "speaker":
        speaker_icon(cx, tx + w + size * 0.62, 0, size * 0.7, fg)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()
    return pw


# ============================================================ background + HUD
def background(cx, t, tint=0.0):
    g = cairo.RadialGradient(W / 2, 820, 40, W / 2, 900, 1250)
    c = mix(NAVY_C, hexc("#3A2030"), tint)
    g.add_color_stop_rgb(0, *c[:3])
    g.add_color_stop_rgb(0.45, *NAVY_M[:3])
    g.add_color_stop_rgb(1, *NAVY_E[:3])
    cx.set_source(g)
    cx.paint()
    # very soft drifting dust for life
    for i in range(18):
        x = (i * 211.7 + t * (6 + i % 5)) % W
        y = (i * 397.3 + math.sin(t * 0.4 + i) * 30) % H
        glow(cx, x, y, 5 + i % 4, (0.7, 0.8, 1.0), 0.06)


def header(cx, label, c, a=1.0):
    ctext(cx, label, W / 2, 548, 40, c, a, spacing=2)


def timer_bar(cx, frac, c, a=1.0, y=585):
    x0, w, h = 135, 810, 16
    rrect(cx, x0, y, w, h, h / 2)
    src(cx, TRACK, a)
    cx.fill()
    fw = max(0.0, w * clamp(frac))
    if fw > 1:
        rrect(cx, x0, y, max(fw, h), h, h / 2)
        g = cairo.LinearGradient(x0, 0, x0 + w, 0)
        g.add_color_stop_rgba(0, *mix(c, (1, 1, 1), -0.0)[:3], a)
        g.add_color_stop_rgba(1, *mix(c, (1, 1, 1), 0.25)[:3], a)
        cx.set_source(g)
        cx.fill()
        glow(cx, x0 + fw, y + h / 2, 26, mix(c, (1, 1, 1), 0.5), 0.8 * a)


def tiles(cx, states, y=1175, size=62, gap=22, accent=HUD, pulse=0.0):
    """states: list of 'locked' | 'active' | 'done' for levels 1..3."""
    n = len(states)
    total = n * size + (n - 1) * gap
    x = W / 2 - total / 2
    for i, st in enumerate(states):
        cx.save()
        cx.translate(x + size / 2, y)
        s = 1.0 + (0.06 * pulse if st == "active" else 0)
        cx.scale(s, s)
        acc = HUD3 if (i == 2 and st == "active") else accent
        if st == "active":
            glow(cx, 0, 0, size * 1.1, acc, 0.35)
        rrect(cx, -size / 2, -size / 2, size, size, size * 0.18)
        src(cx, hexc("#121B38"))
        cx.fill_preserve()
        src(cx, acc if st == "active" else hexc("#3A4876"))
        cx.set_line_width(size * 0.06)
        cx.stroke()
        num_c = acc if st == "active" else (WHITE if st == "done" else hexc("#B9C3DE"))
        ctext(cx, str(i + 1), -size * 0.06 if st == "locked" else 0, size * 0.2, size * 0.56, num_c)
        if st == "locked":
            lock_icon(cx, size * 0.22, size * 0.2, size * 0.28, hexc("#B9C3DE"))
        if st == "done":
            cx.arc(size * 0.42, -size * 0.42, size * 0.22, 0, 2 * math.pi)
            src(cx, HUD)
            cx.fill()
            check_mark(cx, size * 0.42, -size * 0.42, size * 0.22, hexc("#121B38"), size * 0.06)
        cx.restore()
        x += size + gap


# ============================================================ cards
def card(cx, word, ink, x=CARD_X, y=CARD_Y, w=CARD_W, h=CARD_H, scale=1.0, a=1.0, bg=None,
         word_c=None, word_a=1.0, glow_word=0.0, max_size=205):
    cx.save()
    cx.translate(x + w / 2, y + h / 2)
    cx.scale(scale, scale)
    cx.push_group()
    shadow_rrect(cx, -w / 2, -h / 2, w, h, 22, a=0.55)
    # base edge (gives the card a little thickness like the reference)
    rrect(cx, -w / 2, -h / 2 + 8, w, h, 22)
    src(cx, CREAM_DK if bg is None else mix(bg, (0, 0, 0), 0.2))
    cx.fill()
    rrect(cx, -w / 2, -h / 2, w, h, 22)
    if bg is None:
        g = cairo.LinearGradient(0, -h / 2, 0, h / 2)
        g.add_color_stop_rgb(0, *mix(CREAM, (1, 1, 1), 0.35)[:3])
        g.add_color_stop_rgb(1, *CREAM[:3])
        cx.set_source(g)
    else:
        src(cx, bg)
    cx.fill()
    if word:
        size = fit_size(cx, word, w * 0.84, max_size * (h / CARD_H))
        font(cx, size)
        e = cx.text_extents(word)
        bx = -e.x_advance / 2
        by = -(e.y_bearing + e.height / 2)
        if glow_word > 0:
            for k in range(6, 0, -1):
                cx.move_to(bx, by)
                cx.text_path(word)
                src(cx, (1, 0.95, 0.8), 0.07 * glow_word)
                cx.set_line_width(k * 7)
                cx.set_line_join(cairo.LINE_JOIN_ROUND)
                cx.stroke()
        cx.move_to(bx, by)
        src(cx, word_c if word_c is not None else hexc(INK[ink]), word_a)
        cx.show_text(word)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def mini_card(cx, word, ink, x, y, w, h, a=1.0, dim=0.0):
    rrect(cx, x, y + 4, w, h, 8)
    src(cx, CREAM_DK, a)
    cx.fill()
    rrect(cx, x, y, w, h, 8)
    src(cx, mix(CREAM, hexc("#7C8296"), dim), a)
    cx.fill()
    size = fit_size(cx, word, w * 0.8, h * 0.55)
    font(cx, size)
    e = cx.text_extents(word)
    cx.move_to(x + w / 2 - e.x_advance / 2, y + h / 2 - (e.y_bearing + e.height / 2))
    src(cx, mix(hexc(INK[ink]), hexc("#9A9AA6"), dim * 0.6), a)
    cx.show_text(word)


# ============================================================ captions
def caption(cx, t):
    """Reference-style top caption: words appear as spoken, newest word bright."""
    T = tl.build()
    best = None
    for lid in T["order"]:
        L = T["lines"][lid]
        if L["start"] - 0.05 <= t <= L["end"] + 0.35:
            best = L
    if best is None:
        return
    words = best["text"].split()
    times = best["words"]
    a_line = 1.0 - P(t, best["end"] + 0.15, best["end"] + 0.35)
    size = 56
    font(cx, size)
    sp = cx.text_extents(" ").x_advance
    # wrap into lines
    rows, cur, cw = [], [], 0
    for i, w in enumerate(words):
        ww = cx.text_extents(w).x_advance
        if cur and cw + sp + ww > 940:
            rows.append(cur)
            cur, cw = [], 0
        cur.append((i, w, ww))
        cw += (sp if len(cur) > 1 else 0) + ww
    rows.append(cur)
    y = TOP_CAP_Y - (len(rows) - 1) * size * 0.62
    spoken = [i for i in range(len(words)) if t >= times[i] - 0.04]
    newest = spoken[-1] if spoken else -1
    for row in rows:
        rw = sum(r[2] for r in row) + sp * (len(row) - 1)
        x = W / 2 - rw / 2
        for i, w, ww in row:
            if t >= times[i] - 0.04:
                k = P(t, times[i] - 0.04, times[i] + 0.1)
                c = WHITE if i == newest else mix(DIM, WHITE, 0.25)
                cx.move_to(x, y + (1 - ease_out(k)) * 10)
                # dark contour for legibility
                cx.text_path(w)
                src(cx, (0.02, 0.03, 0.08), 0.6 * k * a_line)
                cx.set_line_width(7)
                cx.set_line_join(cairo.LINE_JOIN_ROUND)
                cx.stroke()
                cx.move_to(x, y + (1 - ease_out(k)) * 10)
                src(cx, c, k * a_line)
                cx.show_text(w)
            x += ww + sp
        y += size * 1.24


# ============================================================ mascot
def mascot(cx, t, x, y, s, brows="neutral", mouth="smile", eyes="open", look=(0, 0), tilt=0.0,
           a=1.0, arm=None):
    speaking = any(L["start"] <= t <= L["end"] for L in tl.build()["lines"].values())
    p = Pose(x=x, y=y, s=s, t=t, view="front", brows=brows, mouth=mouth, eyes=eyes, look=look,
             tilt=tilt + math.sin(t * 1.3) * 1.5, blink_seed=1, alpha=a,
             bob=math.sin(t * 2.4) * 1.6, arm_a=10, elb_a=12, arm_b=10, elb_b=12)
    if arm == "point":
        p = p.but(arm_b=150, elb_b=-10)
    elif arm == "wave":
        p = p.but(arm_b=150 + 14 * math.sin(t * 9), elb_b=-25)
    elif arm == "shrug":
        p = p.but(arm_a=75, elb_a=-70, arm_b=75, elb_b=-70)
    if speaking and mouth in ("smile", "grin", "smirk", "flat"):
        p = talk(p.but(mouth="grin"), t, rate=11)
    HERO.draw(cx, p)


# ============================================================ scenes
def tlines():
    return tl.build()["lines"]


def word_t(lid, idx):
    return tlines()[lid]["words"][idx]


def sc_hook(cx, t, t0, t1):
    k = ease_out(P(t, t0, t0 + 0.5))
    # big question mark card teaser in the card slot
    cx.save()
    cx.translate(0, (1 - k) * 60)
    card(cx, "?", "BLUE", word_c=hexc("#283765"), scale=0.9 + 0.1 * k, a=k, max_size=230)
    cx.restore()


def sc_rule(cx, t, t0, t1):
    k = ease_out(P(t, t0, t0 + 0.3))
    header(cx, "SAY THE COLOR", HUD)
    timer_bar(cx, 1.0, HUD)
    card(cx, "RED", "GREEN", scale=0.95 + 0.05 * k, a=k)
    tiles(cx, ["locked"] * 3)
    # quick example: RED is crossed out on "word", GREEN is confirmed on "color"
    t_red = word_t("rule", 3)
    t_green = word_t("rule", 6)
    if t >= t_red:
        a = 1 - P(t, t_green - 0.2, t_green)
        pill(cx, W / 2, 1075, "RED", BAD_R, icon="cross", size=54, a=a, scale=P(t, t_red, t_red + 0.25))
        if t < t_green:
            pr = ease_out(P(t, t_red + 0.05, t_red + 0.4))
            cx.move_to(W / 2 - 230, CARD_Y + CARD_H / 2)
            cx.line_to(W / 2 - 230 + 460 * pr, CARD_Y + CARD_H / 2)
            src(cx, BAD_R, 0.85 * a)
            cx.set_line_width(12)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.stroke()
    if t >= t_green:
        pill(cx, W / 2, 1075, "GREEN", OK_G, icon="check", size=54, scale=P(t, t_green, t_green + 0.25))


def level_intro(cx, t, t0, t1, li):
    acc = HUD3 if li == 2 else HUD
    header(cx, LEVELS[li]["name"], acc)
    timer_bar(cx, ease_out(P(t, t0, t0 + 0.6)), acc)
    # pulsing "get ready" glow in the card slot (reference: soft light orb)
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    glow(cx, W / 2, CARD_Y + CARD_H / 2, 150 + 15 * pulse, mix(acc, (1, 1, 1), 0.6), 0.35)
    glow(cx, W / 2, CARD_Y + CARD_H / 2, 40, (1, 1, 1), 0.9)
    ctext(cx, LEVELS[li]["label"], W / 2, CARD_Y + CARD_H / 2 + 150 + 40, 34, mix(acc, (1, 1, 1), 0.3),
          P(t, t0 + 0.2, t0 + 0.5), spacing=6)
    st = ["done"] * li + ["active"] + ["locked"] * (2 - li)
    tiles(cx, st, pulse=pulse)


def sc_intro1(cx, t, t0, t1):
    level_intro(cx, t, t0, t1, 0)


def sc_intro2(cx, t, t0, t1):
    L = tlines()
    if t < L["go2"]["start"] - 0.1:
        level_intro(cx, t, t0, t1, 1)
    else:
        level_intro(cx, t, t0, t1, 1)
        tg = L["go2"]["start"]
        pill(cx, W / 2, 1075, "NONE OF THEM MATCH", hexc("#1C2B5E"), size=46, scale=P(t, tg, tg + 0.25))


def sc_intro3(cx, t, t0, t1):
    acc = HUD3
    header(cx, "LEVEL 3", acc)
    timer_bar(cx, ease_out(P(t, t0, t0 + 0.6)), acc)
    # big tiles 1 done, 2 done, 3 burning
    size, gap = 170, 50
    x0 = W / 2 - (3 * size + 2 * gap) / 2
    for i in range(3):
        cx.save()
        cx.translate(x0 + size / 2 + i * (size + gap), 800)
        if i == 2:
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            glow(cx, 0, 0, 170 + 12 * pulse, acc, 0.35)
        rrect(cx, -size / 2, -size / 2, size, size, 28)
        src(cx, hexc("#3A1410") if i == 2 else hexc("#121B38"))
        cx.fill_preserve()
        src(cx, acc if i == 2 else hexc("#3A4876"))
        cx.set_line_width(7)
        cx.stroke()
        ctext(cx, str(i + 1), 0, 34, 100, acc if i == 2 else WHITE)
        if i < 2:
            cx.arc(size * 0.42, -size * 0.42, 30, 0, 2 * math.pi)
            src(cx, HUD)
            cx.fill()
            check_mark(cx, size * 0.42, -size * 0.42, 30, hexc("#121B38"), 8)
        cx.restore()
    ti = word_t("final3", 2)            # "ignore"
    tt = word_t("final3", 5)            # "only trust..."
    if t >= ti:
        pill(cx, W / 2, 1060, "IGNORE MY VOICE", hexc("#B8361F"), icon="speaker", size=48,
             scale=P(t, ti, ti + 0.25))
    if t >= tt:
        pill(cx, W / 2, 1195, "TRUST THE COLOR", OK_G, icon="check", size=48, scale=P(t, tt, tt + 0.25))


def play(cx, t, t0, t1, li):
    T = tl.build()
    lv = T["levels"][li]
    L = LEVELS[li]
    acc = HUD3 if li == 2 else HUD
    header(cx, L["name"], acc)
    n = len(L["cards"])
    k = 0
    for i, (a, b) in enumerate(lv["cards"]):
        if t >= a:
            k = i
    a, b = lv["cards"][k]
    frac = 1 - P(t, a, b)
    if t >= lv["end"]:
        frac = 0
    timer_bar(cx, frac, acc)
    word, ink = L["cards"][k]
    pop = ease_out(P(t, a, a + 0.14))
    # previous card flicks out to the left
    if k > 0 and t < a + 0.12:
        pw, pink = L["cards"][k - 1]
        q = ease_in(P(t, a, a + 0.12))
        card(cx, pw, pink, x=CARD_X - 200 * q, a=1 - q, scale=1 - 0.04 * q)
    card(cx, word, ink, scale=0.96 + 0.04 * pop, a=clamp(P(t, a, a + 0.08)))
    ctext(cx, f"{k + 1} / {n}", W / 2, 1072, 40, hexc("#C9D2EA"))
    st = ["done"] * li + ["active"] + ["locked"] * (2 - li)
    tiles(cx, st)


def sc_play1(cx, t, t0, t1):
    play(cx, t, t0, t1, 0)


def sc_play2(cx, t, t0, t1):
    play(cx, t, t0, t1, 1)


def sc_play3(cx, t, t0, t1):
    play(cx, t, t0, t1, 2)


def sc_matched(cx, t, t0, t1):
    """Stacked recap of level 1: the two congruent cards get checkmarks."""
    cards = LEVELS[0]["cards"]
    t_two = word_t("matched", 4)
    w, h, gap = 420, 92, 18
    y0 = 520
    for i, (wd, ink) in enumerate(cards):
        ti = t0 + i * 0.07
        k = ease_out(P(t, ti, ti + 0.3))
        match = wd == ink
        dim = 0.0 if (match or t < t_two) else ease_io(P(t, t_two, t_two + 0.3)) * 0.7
        y = y0 + i * (h + gap) + (1 - k) * 40
        mini_card(cx, wd, ink, W / 2 - w / 2, y, w, h, a=k, dim=dim)
        if match and t >= t_two:
            kk = ease_out(P(t, t_two + i * 0.08, t_two + i * 0.08 + 0.25))
            cx.save()
            cx.translate(W / 2 + w / 2 + 50, y + h / 2)
            cx.scale(max(kk, 1e-3), max(kk, 1e-3))
            cx.arc(0, 0, 30, 0, 2 * math.pi)
            src(cx, OK_G)
            cx.fill()
            check_mark(cx, 0, 0, 30, WHITE, 7)
            cx.restore()
    tiles(cx, ["done", "locked", "locked"])


def sc_pause(cx, t, t0, t1):
    """Last level-2 card stays; a tiny 'hitch' appears before the answer."""
    word, ink = LEVELS[1]["cards"][-1]
    t_tiny = word_t("pause", 4)
    card(cx, word, ink)
    if t >= t_tiny:
        pill(cx, W / 2, 1075, "...", hexc("#1C2B5E"), size=44, scale=P(t, t_tiny, t_tiny + 0.25))
    tiles(cx, ["done", "done", "locked"])


def sc_race(cx, t, t0, t1):
    """Reading vs naming the color: two lanes, reading always wins."""
    L = tlines()
    word, ink = LEVELS[1]["cards"][-1]          # RED in brown
    k = ease_out(P(t, t0, t0 + 0.4))
    card(cx, word, ink, x=W / 2 - 230, y=470, w=460, h=170, a=k)
    t_start = L["interfere"]["start"] + 0.3
    lanes = [("READING", "RED", WHITE, hexc("#1A1F33"), 1.25), ("NAMING THE COLOR", "BROWN", hexc(INK["BROWN"]), WHITE, 2.6)]
    x0, x1 = 150, 900
    for i, (lab, chip, chip_bg, chip_fg, dur) in enumerate(lanes):
        y = 790 + i * 190
        a = P(t, t0 + 0.1 + i * 0.1, t0 + 0.4 + i * 0.1)
        ctext(cx, lab, W / 2, y - 50, 34, mix(DIM, WHITE, 0.4), a, spacing=2)
        rrect(cx, x0 - 30, y - 30, x1 - x0 + 100, 76, 38)
        src(cx, hexc("#121B38"), a)
        cx.fill()
        # finish line
        for j in range(6):
            cx.rectangle(x1 + 30, y - 26 + j * 12, 6, 7)
        src(cx, WHITE, 0.6 * a)
        cx.fill()
        pr = ease_io(P(t, t_start, t_start + dur))
        cxp = x0 + 60 + (x1 - x0 - 90) * pr
        font(cx, 32)
        cwid = cx.text_extents(chip).x_advance + 50
        rrect(cx, cxp - cwid / 2, y - 22, cwid, 60, 30)
        src(cx, chip_bg, a)
        cx.fill()
        ctext(cx, chip, cxp, y + 19, 32, chip_fg, a)
        if i == 0:
            tf = t_start + 1.35
            if t >= tf:
                kk = ease_out(P(t, tf, tf + 0.25))
                cx.save()
                cx.translate(cxp + cwid / 2 - 6, y - 26)
                cx.scale(max(kk, 1e-3), max(kk, 1e-3))
                cx.arc(0, 0, 30, 0, 2 * math.pi)
                src(cx, HUD)
                cx.fill()
                ctext(cx, "1st", 0, 9, 24, hexc("#121B38"))
                cx.restore()
    tiles(cx, ["done", "done", "locked"])


def sc_end(cx, t, t0, t1):
    """STOP on the frozen last card, then a clean three-element score screen."""
    L = tlines()
    ts = L["stop"]["start"]
    tc = L["comment"]["start"]
    tg = L["stop"]["end"] + 0.05
    xf = P(t, tg, tg + 0.3)

    def stop_state():
        word, ink = LEVELS[2]["cards"][-1]
        card(cx, word, ink)
        header(cx, "LEVEL 3", HUD3)
        timer_bar(cx, 0, HUD3)
        if t >= ts:
            pill(cx, W / 2, 1075, "STOP!", BAD_R, size=60, scale=P(t, ts, ts + 0.15))
        tiles(cx, ["done", "done", "done"])

    if xf < 1:
        group(cx, 1 - xf, stop_state)
    if t < tg:
        return
    # 1) big question
    for i, row in enumerate(["HOW MANY", "DID YOU GET", "RIGHT?"]):
        k = ease_out(P(t, tg + 0.05 + i * 0.08, tg + 0.4 + i * 0.08))
        ctext(cx, row, W / 2, 560 + i * 118 + (1 - k) * 24, 104, WHITE, k)
    # 2) ? / 19
    sk = ease_out(P(t, tg + 0.35, tg + 0.7))
    cx.save()
    cx.translate(W / 2, 1000)
    cx.scale(0.92 + 0.08 * sk, 0.92 + 0.08 * sk)
    cx.push_group()
    rrect(cx, -250, -100, 500, 200, 100)
    src(cx, hexc("#121B38"))
    cx.fill_preserve()
    src(cx, HUD)
    cx.set_line_width(9)
    cx.stroke()
    font(cx, 128)
    q, rest = "?", f" / {TOTAL}"
    wq = cx.text_extents(q).x_advance
    wr = cx.text_extents(rest).x_advance
    cx.move_to(-(wq + wr) / 2, 46)
    src(cx, HUD, 0.75 + 0.25 * math.sin(t * 3))
    cx.show_text(q)
    cx.move_to(-(wq + wr) / 2 + wq, 46)
    src(cx, WHITE)
    cx.show_text(rest)
    cx.pop_group_to_source()
    cx.paint_with_alpha(sk)
    cx.restore()
    # 3) call to action
    if t >= tc:
        pill(cx, W / 2, 1215, "COMMENT YOUR SCORE!", hexc("#1E5EE6"), size=54, scale=P(t, tc, tc + 0.3))


SCENES = {
    "hook": sc_hook, "rule": sc_rule, "intro1": sc_intro1, "play1": sc_play1, "matched": sc_matched,
    "intro2": sc_intro2, "play2": sc_play2, "pause": sc_pause, "race": sc_race, "intro3": sc_intro3,
    "play3": sc_play3, "end": sc_end,
}
# scenes that cut hard (gameplay must be crisp); others cross-fade
HARD_IN = {"play1", "play2", "play3", "end"}
XF = 0.22


# ============================================================ mascot plan
def mascot_state(t):
    """(visible 0..1, kwargs) — mascot only appears outside gameplay."""
    L = tlines()
    T = tl.build()
    lv = T["levels"]
    plans = [
        # (t_in, t_out, kwargs)
        (0.0, L["rule"]["end"] + 0.2, dict(brows="neutral", mouth="smirk")),
        (lv[0]["end"] + 0.15, L["matched"]["end"], dict(brows="skeptic", mouth="grin")),
        (lv[1]["end"] + 0.15, L["pause"]["end"] + 0.1, dict(brows="skeptic", mouth="smirk")),
        (L["final3"]["start"], L["go3"]["start"] - 0.2, dict(brows="angry", mouth="smirk")),
        (L["howmany"]["start"] + 0.4, T["end"] + 1, dict(brows="skeptic", mouth="smirk")),
    ]
    for a, b, kw in plans:
        if a - 0.01 <= t <= b + 0.35:
            v = ease_out(P(t, a, a + 0.35)) * (1 - ease_in(P(t, b, b + 0.35)))
            return v, kw, a
    return 0.0, {}, 0.0


def draw_mascot(cx, t):
    v, kw, a = mascot_state(t)
    if v <= 0.001:
        return
    L = tlines()
    hook_end = L["hook"]["end"] + 0.15
    # during the hook the mascot is big and central; afterwards it sits in the lower third
    if t < L["rule"]["start"] + 0.5:
        m = ease_io(P(t, hook_end, L["rule"]["start"] + 0.45))
        x = W / 2 + 0 * m
        y = 2050 - 30 * (1 - m)
        s = 2.6 - 0.6 * m
    else:
        x, y, s = W / 2, 2050, 2.0
    y += (1 - v) * 520
    kw = dict(kw)
    arm = None
    if t < hook_end:
        arm = "wave" if t < 0.9 else None
    if L["believe"]["start"] <= t:
        arm = "shrug"
    mouth = kw.pop("mouth", "smile")
    mascot(cx, t, x, y, s, mouth=mouth, arm=arm, **kw)


# ============================================================ frame
def frame(cx, t):
    background(cx, t, tint=0.0)
    sc = tl.scenes()
    cur = None
    for i, (n, a, b) in enumerate(sc):
        if a <= t < b or (i == len(sc) - 1 and t >= a):
            cur = i
    n, a, b = sc[cur]
    # cross-fade from the previous scene
    if cur > 0 and n not in HARD_IN and t < a + XF:
        pn, pa, pb = sc[cur - 1]
        k = P(t, a, a + XF)
        group(cx, 1 - k, SCENES[pn], cx, t, pa, pb)
        group(cx, k, SCENES[n], cx, t, a, b)
    else:
        SCENES[n](cx, t, a, b)
    draw_mascot(cx, t)
    L = tlines()
    if not (L["howmany"]["start"] - 0.05 <= t < L["believe"]["start"] - 0.05):
        caption(cx, t)
    # global fade in/out
    T = tl.build()
    fo = P(t, T["end"] - 0.25, T["end"])
    if fo > 0:
        src(cx, (0, 0, 0), fo)
        cx.paint()


def render_png(t, path):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(s)
    frame(cx, t)
    s.write_to_png(path)

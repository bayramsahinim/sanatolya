"""Artwork for "Can You Swallow Four Times?" (vertical 1080x1920).

* front bust of the Just Needy guy (white head, channel face, blue hoodie) with a visible neck
  so the swallow reads as a small, believable larynx lift
* the four countdown circles
* the profile + cutaway lens used for the explanation (dimensional shading, still the same guy)
"""
import math

import cairo

from cinecode.characters import HeroStyle, Pose, draw_face
from cinecode.core import (OUTLINE, back_out, circle, clamp, curve, ease_io, ease_out, ellipse,
                           fs, hexc, line, mix, noise1, prog, rgrad, rrect, shade, smooth, src, vgrad)

W, H = 1080, 1920
LW = 13.0                                  # main outline width at this scale

BLUE = HeroStyle.blue
BLUE_DK = HeroStyle.blue_dk
BLUE_LT = HeroStyle.blue_lt
WHITE = (1, 1, 1, 1)
STRING = hexc("#F2F2F2")
GREEN = hexc("#38A85A")
GREEN_DK = hexc("#23803F")
AMBER = hexc("#F2B33D")
AMBER_DK = hexc("#C98A1C")
NEUTRAL = hexc("#A79C8C")
BG_IN = hexc("#F7F1E6")
BG_OUT = hexc("#DCCDB5")

CIRCLE_Y = 318
CIRCLE_X = [315, 465, 615, 765]
CIRCLE_R = 54


# ------------------------------------------------------------------ background
def background(cx, glow=1.0):
    cx.rectangle(0, 0, W, H)
    cx.set_source(rgrad(cx, W / 2, 860, 60, 1250, [(0, BG_IN), (0.55, mix(BG_IN, BG_OUT, 0.45)), (1, BG_OUT)]))
    cx.fill()
    # soft back-light behind the character (gives the flat set some depth)
    cx.rectangle(0, 0, W, H)
    cx.set_source(rgrad(cx, W / 2, 900, 0, 560, [(0, (1, 1, 1, 0.38 * glow)), (1, (1, 1, 1, 0))]))
    cx.fill()


# ------------------------------------------------------------------ countdown circles
def _check_path(cx, x, y, s, prog_):
    pts = [(x - 0.42 * s, y + 0.02 * s), (x - 0.12 * s, y + 0.32 * s), (x + 0.45 * s, y - 0.30 * s)]
    l1 = math.dist(pts[0], pts[1])
    l2 = math.dist(pts[1], pts[2])
    d = prog_ * (l1 + l2)
    cx.move_to(*pts[0])
    if d <= l1:
        k = d / l1
        cx.line_to(pts[0][0] + (pts[1][0] - pts[0][0]) * k, pts[0][1] + (pts[1][1] - pts[0][1]) * k)
    else:
        cx.line_to(*pts[1])
        k = (d - l1) / l2
        cx.line_to(pts[1][0] + (pts[2][0] - pts[1][0]) * k, pts[1][1] + (pts[2][1] - pts[1][1]) * k)


def _text_c(cx, s, x, y, size, col):
    cx.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    e = cx.text_extents(s)
    cx.move_to(x - e.width / 2 - e.x_bearing, y - e.height / 2 - e.y_bearing)
    src(cx, col)
    cx.show_text(s)


def draw_circle(cx, i, st, t):
    """st: dict(active, done, warn, pulse, alpha)."""
    x, y, r = CIRCLE_X[i], CIRCLE_Y, CIRCLE_R
    active, done, warn = st.get("active", 0), st.get("done", 0), st.get("warn", 0)
    a = st.get("alpha", 1.0)
    pop = st.get("pulse", 0.0)
    sc = 1 + 0.10 * active * (1 - done) * (1 - warn) + 0.12 * pop
    if done > 0:
        sc *= 0.85 + 0.15 * back_out(done) if done < 1 else 1.0
    rot = 0.0
    if warn > 0:
        rot = 0.07 * warn * math.sin(t * 9.0) * st.get("wobble", 1.0)
    cx.save()
    cx.translate(x, y)
    cx.rotate(rot)
    cx.scale(sc, sc)
    cx.push_group()
    # contact shadow
    ellipse(cx, 0, r * 0.95, r * 0.8, r * 0.18)
    src(cx, (0.25, 0.18, 0.1, 0.10))
    cx.fill()
    # neutral base: white with dashed outline
    circle(cx, 0, 0, r)
    cx.set_source(rgrad(cx, -r * 0.3, -r * 0.4, r * 0.1, r * 1.3, [(0, WHITE), (1, hexc("#EEE8DE"))]))
    cx.fill()
    n_alpha = 1 - max(done, warn)
    if n_alpha > 0:
        circle(cx, 0, 0, r)
        if active < 0.5:
            cx.set_dash([10, 8])
        src(cx, mix(NEUTRAL, BLUE, active), n_alpha)
        cx.set_line_width(5 + 3 * active)
        cx.stroke()
        cx.set_dash([])
        _text_c(cx, str(i + 1), 0, 2, 50, mix(NEUTRAL, OUTLINE, active) if True else None)
    # done: green disc + drawn check
    if done > 0:
        k = clamp(done * 1.6)
        circle(cx, 0, 0, r * (0.25 + 0.75 * ease_out(k)))
        cx.set_source(rgrad(cx, -r * 0.35, -r * 0.45, r * 0.05, r * 1.25, [(0, shade(GREEN, 0.18)), (1, GREEN_DK)]))
        cx.fill_preserve()
        src(cx, OUTLINE)
        cx.set_line_width(5)
        cx.stroke()
        cp = clamp((done - 0.35) / 0.65)
        if cp > 0:
            _check_path(cx, 0, 0, r * 0.95, smooth(cp))
            src(cx, WHITE)
            cx.set_line_width(11)
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.set_line_join(cairo.LINE_JOIN_ROUND)
            cx.stroke()
        # glossy highlight
        ellipse(cx, -r * 0.3, -r * 0.48, r * 0.38, r * 0.16, -0.5)
        src(cx, (1, 1, 1, 0.22 * k))
        cx.fill()
    # warn: amber disc with hesitation dots
    if warn > 0:
        k = ease_out(warn)
        circle(cx, 0, 0, r * (0.3 + 0.7 * k))
        cx.set_source(rgrad(cx, -r * 0.35, -r * 0.45, r * 0.05, r * 1.25, [(0, shade(AMBER, 0.2)), (1, AMBER_DK)]))
        cx.fill_preserve()
        src(cx, OUTLINE)
        cx.set_line_width(5)
        cx.stroke()
        for j in range(3):
            ph = (t * 2.2 - j * 0.22) % 1.0
            lift = math.sin(min(ph, 0.5) * 2 * math.pi) * 5 if ph < 0.5 else 0
            circle(cx, (j - 1) * r * 0.36, -lift + 2, r * 0.11)
            src(cx, WHITE, k)
            cx.fill()
        ellipse(cx, -r * 0.3, -r * 0.48, r * 0.38, r * 0.16, -0.5)
        src(cx, (1, 1, 1, 0.22 * k))
        cx.fill()
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


def draw_circles(cx, states, t):
    # faint connecting rail so the four read as one sequence
    y = CIRCLE_Y
    line(cx, [(CIRCLE_X[0], y), (CIRCLE_X[-1], y)], (0.4, 0.33, 0.25, 0.16), 6)
    for i in range(4):
        draw_circle(cx, i, states[i], t)


# ------------------------------------------------------------------ front bust
HX, HY = 540, 800            # head centre
S = 4.3                      # channel rig scale (head_r 50 -> 215)
R = 50 * S
NECK_W = 184
NECK_TOP = HY + R * 0.72
NECK_BOT = 1196


def _hood_shapes(cx, dy):
    """Hood rolled around the neck: back part."""
    ellipse(cx, HX, 1170 + dy, 232, 92)


def _torso_path(cx, dy):
    y0 = 1150 + dy
    cx.move_to(-40, H + 20)
    cx.line_to(-30, 1560 + dy)
    cx.curve_to(-20, 1380 + dy, 40, 1260 + dy, 170, 1215 + dy)
    cx.curve_to(260, 1184 + dy, 330, y0 + 10, HX, y0)
    cx.curve_to(W - 330, y0 + 10, W - 260, 1184 + dy, W - 170, 1215 + dy)
    cx.curve_to(W - 40, 1260 + dy, W + 20, 1380 + dy, W + 30, 1560 + dy)
    cx.line_to(W + 40, H + 20)
    cx.close_path()


def draw_front(cx, st, t):
    """st: sw (0..1 larynx lift), strain, dy (body bob), head_dy, tilt, eyes, brows, mouth, look, blink."""
    dy = st.get("dy", 0.0)
    sw = st.get("sw", 0.0)
    strain = st.get("strain", 0.0)
    head_dy = st.get("head_dy", 0.0) + dy * 0.6
    tilt = st.get("tilt", 0.0)

    # --- soft cast shadow of the whole bust on the backdrop (depth)
    cx.save()
    cx.translate(16, 22)
    _torso_path(cx, dy)
    circle(cx, HX, HY + head_dy, R + 6)
    cx.set_source_rgba(0.3, 0.2, 0.1, 0.07)
    cx.fill()
    cx.restore()

    # --- hood (back roll)
    _hood_shapes(cx, dy)
    cx.set_source(vgrad(cx, 0, 1080 + dy, 0, 1260 + dy, [(0, shade(BLUE_DK, -0.25)), (1, BLUE_DK)]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()

    # --- neck
    nx0, nx1 = HX - NECK_W / 2, HX + NECK_W / 2
    pinch = 7 * sw + 4 * strain
    cx.move_to(nx0, NECK_TOP + head_dy - 40)
    cx.curve_to(nx0 + pinch, 1020 + dy, nx0 + pinch * 0.5, 1110 + dy, nx0 - 4, NECK_BOT + dy)
    cx.line_to(nx1 + 4, NECK_BOT + dy)
    cx.curve_to(nx1 - pinch * 0.5, 1110 + dy, nx1 - pinch, 1020 + dy, nx1, NECK_TOP + head_dy - 40)
    cx.close_path()
    path = cx.copy_path()
    cx.set_source(vgrad(cx, nx0, 0, nx1, 0, [(0, hexc("#E9E9EF")), (0.35, WHITE), (0.7, WHITE), (1, hexc("#E4E4EB"))]))
    cx.fill()
    # under-chin shadow (moves with the head)
    cx.save()
    cx.append_path(path)
    cx.clip()
    ellipse(cx, HX, NECK_TOP + head_dy + 8, NECK_W * 0.75, 70)
    src(cx, (0.55, 0.55, 0.65, 0.30))
    cx.fill()
    # larynx: a small bump that lifts during a swallow
    ly = 1100 + dy - 34 * sw + 2.5 * strain * math.sin(t * 40)
    bump_a = 0.42 + 0.35 * max(sw, strain * 0.8)
    curve(cx, (HX - 17, ly + 6), (HX - 9, ly - 8), (HX + 9, ly - 8), (HX + 17, ly + 6), (0.12, 0.12, 0.16, bump_a), 6)
    curve(cx, (HX - 9, ly + 22), (HX - 4, ly + 16), (HX + 4, ly + 16), (HX + 9, ly + 22), (0.12, 0.12, 0.16, bump_a * 0.55), 5)
    # neck muscles tense slightly during the effort
    m = 0.22 * max(sw, strain)
    if m > 0.01:
        line(cx, [(HX - 54, 1040 + dy), (HX - 26, 1150 + dy)], (0.12, 0.12, 0.16, m), 5)
        line(cx, [(HX + 54, 1040 + dy), (HX + 26, 1150 + dy)], (0.12, 0.12, 0.16, m), 5)
    cx.restore()
    cx.append_path(path)
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()

    # --- torso (hoodie) with dimensional shading
    _torso_path(cx, dy)
    tp = cx.copy_path()
    cx.set_source(vgrad(cx, 0, 1150 + dy, 0, H, [(0, BLUE_LT), (0.25, BLUE), (1, shade(BLUE, -0.22))]))
    cx.fill()
    cx.save()
    cx.append_path(tp)
    cx.clip()
    # side falloff
    for sx in (-120, W + 120):
        cx.rectangle(0, 0, W, H)
        cx.set_source(rgrad(cx, sx, 1700, 50, 520, [(0, (0.05, 0.12, 0.3, 0.40)), (1, (0.05, 0.12, 0.3, 0))]))
        cx.fill()
    # shoulder highlights
    for sx in (190, W - 190):
        ellipse(cx, sx, 1258 + dy, 120, 40, -0.35 if sx < W / 2 else 0.35)
        src(cx, (1, 1, 1, 0.13))
        cx.fill()
    # kangaroo pocket + centre seam
    cx.move_to(300, H + 10)
    cx.line_to(345, 1720 + dy)
    cx.curve_to(350, 1700 + dy, 370, 1690 + dy, 395, 1690 + dy)
    cx.line_to(W - 395, 1690 + dy)
    cx.curve_to(W - 370, 1690 + dy, W - 350, 1700 + dy, W - 345, 1720 + dy)
    cx.line_to(W - 300, H + 10)
    fs(cx, None, shade(BLUE_DK, -0.2), 7)
    # sleeve seams
    curve(cx, (150, 1225 + dy), (110, 1360 + dy), (100, 1520 + dy), (110, 1700 + dy), shade(BLUE_DK, -0.15), 6)
    curve(cx, (W - 150, 1225 + dy), (W - 110, 1360 + dy), (W - 100, 1520 + dy), (W - 110, 1700 + dy), shade(BLUE_DK, -0.15), 6)
    cx.restore()
    cx.append_path(tp)
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()

    # --- hood front roll (collar) hugging the neck
    yy = 1150 + dy
    cx.move_to(HX - 215, yy - 22)
    cx.curve_to(HX - 190, yy + 70, HX - 90, yy + 104, HX, yy + 104)
    cx.curve_to(HX + 90, yy + 104, HX + 190, yy + 70, HX + 215, yy - 22)
    cx.curve_to(HX + 170, yy + 20, HX + 100, yy + 46, HX, yy + 46)
    cx.curve_to(HX - 100, yy + 46, HX - 170, yy + 20, HX - 215, yy - 22)
    cx.close_path()
    cx.set_source(vgrad(cx, 0, yy, 0, yy + 104, [(0, BLUE_LT), (1, BLUE)]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW * 0.85)
    cx.stroke()
    # drawstrings
    for sx, ex in ((HX - 58, HX - 70), (HX + 58, HX + 70)):
        sway = 3 * math.sin(t * 1.3 + sx)
        pts = [(sx, yy + 92), (ex + sway, yy + 300 + dy * 0.2)]
        line(cx, pts, OUTLINE, 17)
        line(cx, pts, STRING, 9)
        rrect(cx, ex + sway - 9, yy + 296, 18, 34, 6)
        fs(cx, hexc("#D9D9DE"), OUTLINE, 5)
        circle(cx, sx, yy + 88, 10)
        fs(cx, hexc("#CFCFD6"), OUTLINE, 5)

    # --- head
    hy = HY + head_dy
    cx.save()
    cx.translate(HX, hy)
    cx.rotate(tilt)
    circle(cx, 0, 0, R)
    cx.set_source(rgrad(cx, -R * 0.35, -R * 0.45, R * 0.1, R * 1.25,
                        [(0, WHITE), (0.62, WHITE), (1, hexc("#E3E3EA"))]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()
    # face (channel face rig, scaled up)
    cx.scale(S, S)
    p = Pose(view="front", eyes=st.get("eyes", "open"), brows=st.get("brows", "neutral"),
             mouth=st.get("mouth", "smile"), look=st.get("look", (0, 0)), t=t, blink=st.get("blink", True),
             blink_seed=3, blush=st.get("blush", 0.0))
    J = {"head": (0, 0), "head_r": 0.0}
    draw_face(cx, J, p, 50, HeroStyle())
    cx.restore()


# ------------------------------------------------------------------ profile + cutaway lens
PHX, PHY = 380, 640
PS = 4.0
PR = 50 * PS
LENS = (560, 1118, 318)


def draw_profile_body(cx, t, dy=0.0):
    # cast shadow
    cx.save()
    cx.translate(18, 22)
    circle(cx, PHX, PHY, PR + 4)
    cx.set_source_rgba(0.3, 0.2, 0.1, 0.07)
    cx.fill()
    cx.restore()
    # hood bunched at the back
    ellipse(cx, PHX - 150, 1205 + dy, 150, 92, 0.25)
    fs(cx, shade(BLUE_DK, -0.15), OUTLINE, LW)
    # neck
    cx.move_to(PHX - 90, PHY + PR * 0.6)
    cx.curve_to(PHX - 95, 1000, PHX - 100, 1120, PHX - 110, 1260 + dy)
    cx.line_to(PHX + 100, 1260 + dy)
    cx.curve_to(PHX + 80, 1130, PHX + 70, 1020, PHX + 60, PHY + PR * 0.8)
    cx.close_path()
    cx.set_source(vgrad(cx, PHX - 100, 0, PHX + 100, 0, [(0, hexc("#E4E4EB")), (0.5, WHITE), (1, hexc("#EDEDF2"))]))
    fs(cx, None, None, 0) if False else None
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()
    # torso in profile (facing right)
    y0 = 1210 + dy
    cx.move_to(-60, H + 20)
    cx.line_to(-40, 1400 + dy)
    cx.curve_to(0, 1280 + dy, 120, y0, PHX - 40, y0 - 10)
    cx.curve_to(PHX + 160, y0 - 6, 760, 1260 + dy, 830, 1400 + dy)
    cx.curve_to(880, 1520 + dy, 900, 1700 + dy, 910, H + 20)
    cx.close_path()
    cx.set_source(vgrad(cx, 0, y0, 0, H, [(0, BLUE_LT), (0.3, BLUE), (1, shade(BLUE, -0.22))]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()
    # collar roll
    cx.move_to(PHX - 170, y0 - 30)
    cx.curve_to(PHX - 60, y0 + 50, PHX + 120, y0 + 50, PHX + 170, y0 - 14)
    cx.curve_to(PHX + 100, y0 + 10, PHX - 60, y0 + 6, PHX - 170, y0 - 30)
    cx.close_path()
    fs(cx, BLUE_LT, OUTLINE, LW * 0.8)
    # drawstring
    line(cx, [(PHX + 120, y0 + 20), (PHX + 140, y0 + 250)], OUTLINE, 17)
    line(cx, [(PHX + 120, y0 + 20), (PHX + 140, y0 + 250)], STRING, 9)


def draw_profile_head(cx, t, st):
    cx.save()
    cx.translate(PHX, PHY + st.get("head_dy", 0))
    circle(cx, 0, 0, PR)
    cx.set_source(rgrad(cx, PR * 0.2, -PR * 0.45, PR * 0.1, PR * 1.25,
                        [(0, WHITE), (0.62, WHITE), (1, hexc("#E3E3EA"))]))
    cx.fill_preserve()
    src(cx, OUTLINE)
    cx.set_line_width(LW)
    cx.stroke()
    cx.scale(PS, PS)
    p = Pose(view="side", f=1, eyes=st.get("eyes", "open"), brows=st.get("brows", "neutral"),
             mouth=st.get("mouth", "smile"), look=st.get("look", (0.3, 0)), t=t, blink_seed=5)
    draw_face(cx, {"head": (0, 0), "head_r": 0.0}, p, 50, HeroStyle())
    cx.restore()


# tissue palette
TISSUE = hexc("#F2B8AE")
TISSUE_DK = hexc("#D98C86")
CAVITY = hexc("#6E2633")
TONGUE = hexc("#E2737F")
SALIVA = hexc("#8FD0FF")


def _wet_streak(cx, pts, wet, width=7):
    if wet <= 0.02:
        return
    cx.move_to(*pts[0])
    for p in pts[1:]:
        cx.line_to(*p)
    src(cx, (1, 1, 1, 0.55 * wet))
    cx.set_line_width(width)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()


def draw_lens_content(cx, st, t):
    """Sagittal cutaway of mouth + throat in lens-local coords (origin = lens centre, radius ~292).
    st: sw (swallow progress 0..1), bolus (saliva amount 0..1), wet (0..1), signal (0..1),
        empty (0..1 dashed 'missing saliva' outline), strain (0..1), stall (bolus-less swallow)."""
    sw = st.get("sw", 0.0)
    amount = st.get("bolus", 1.0)
    wet = st.get("wet", 1.0)
    strain = st.get("strain", 0.0)
    dry = 1 - wet
    tissue = mix(TISSUE, hexc("#E7C2B5"), dry * 0.6)
    tissue_dk = mix(TISSUE_DK, hexc("#CFA49A"), dry * 0.6)
    cavity = mix(CAVITY, hexc("#7C4148"), dry * 0.5)

    # phases of a swallow
    p_tongue = smooth(prog(sw, 0.0, 0.35)) * (1 - smooth(prog(sw, 0.75, 1.0)))
    p_epi = smooth(prog(sw, 0.2, 0.4)) * (1 - smooth(prog(sw, 0.7, 0.9)))
    lar = 16 * p_epi

    # tissue field
    cx.rectangle(-400, -400, 800, 800)
    cx.set_source(rgrad(cx, 60, -40, 20, 420, [(0, shade(tissue, 0.12)), (1, tissue_dk)]))
    cx.fill()
    # spine (back, left)
    for k in range(5):
        y = -250 + k * 112
        rrect(cx, -300, y, 92, 96, 26)
        cx.set_source(vgrad(cx, 0, y, 0, y + 96, [(0, hexc("#F6EBD8")), (1, hexc("#DCC9A8"))]))
        cx.fill_preserve()
        src(cx, (0.45, 0.3, 0.25, 0.8))
        cx.set_line_width(5)
        cx.stroke()
    # palate (roof of mouth)
    cx.move_to(400, -300)
    cx.line_to(-30, -300)
    cx.curve_to(-60, -300, -80, -270, -70, -240)
    cx.curve_to(-20, -250, 140, -236, 400, -232)
    cx.close_path()
    fs(cx, shade(tissue, 0.25), (0.45, 0.2, 0.22, 0.7), 5)
    # pharynx + oral cavity (dark air space)
    uv = 14 * p_tongue
    cx.move_to(400, -232)
    cx.curve_to(140, -236, -20, -250, -70, -240 - uv)          # roof back to soft palate
    cx.curve_to(-118, -228, -150, -200, -158, -140)            # back of throat wall
    cx.curve_to(-165, -60, -150, 0, -146, 40 - lar)            # down to the split
    cx.line_to(-30, 40 - lar)
    cx.curve_to(-40, -40, -40, -120, 20, -170 + 20 * p_tongue)   # tongue base (front of pharynx)
    cx.curve_to(110, -214 + 26 * p_tongue, 260, -206, 400, -150)
    cx.close_path()
    cx.set_source(rgrad(cx, -60, -120, 10, 340, [(0, shade(cavity, -0.1)), (1, cavity)]))
    cx.fill()
    # soft palate / uvula
    cx.move_to(-20, -250)
    cx.curve_to(-60, -250 - uv, -96, -236 - uv * 1.6, -100, -200 - uv * 1.6)
    cx.curve_to(-80, -196 - uv * 1.6, -64, -214 - uv, -30, -226)
    cx.close_path()
    fs(cx, tissue, (0.45, 0.2, 0.22, 0.8), 5)
    # esophagus (behind, collapsed tube)
    ex0, ex1 = -150, -84
    cx.rectangle(ex0, 30 - lar, ex1 - ex0, 400)
    cx.set_source(vgrad(cx, ex0, 0, ex1, 0, [(0, tissue_dk), (0.5, shade(tissue, 0.08)), (1, tissue_dk)]))
    cx.fill()
    # trachea (front) with cartilage rings
    tx0, tx1 = -64, 26
    cx.rectangle(tx0, 40 - lar, tx1 - tx0, 400)
    cx.set_source(vgrad(cx, tx0, 0, tx1, 0, [(0, hexc("#E9D6D2")), (0.5, hexc("#F7ECEA")), (1, hexc("#E2CBC6"))]))
    cx.fill()
    for k in range(6):
        y = 70 - lar + k * 46
        rrect(cx, tx0 + 4, y, tx1 - tx0 - 8, 22, 10)
        src(cx, (0.75, 0.6, 0.58, 0.55))
        cx.fill()
    line(cx, [(tx0, 40 - lar), (tx0, 400)], (0.45, 0.2, 0.22, 0.7), 5)
    line(cx, [(tx1, 40 - lar), (tx1, 400)], (0.45, 0.2, 0.22, 0.7), 5)
    # esophagus lumen line
    line(cx, [((ex0 + ex1) / 2, 40 - lar), ((ex0 + ex1) / 2, 400)], (0.45, 0.15, 0.2, 0.55), 4)
    # tongue (dimensional)
    tp = p_tongue
    cx.move_to(400, -40)
    cx.line_to(400, -150 + 6 * tp)
    cx.curve_to(260, -200 - 14 * tp, 110, -216 + 18 * tp - 30 * tp, 20, -172 + 20 * tp)
    cx.curve_to(-30, -130 + 10 * tp, -44, -60, -40, 0)
    cx.curve_to(40, 40, 260, 40, 400, -40)
    cx.close_path()
    cx.set_source(rgrad(cx, 160, -170, 10, 300, [(0, shade(TONGUE, 0.22)), (0.6, TONGUE), (1, shade(TONGUE, -0.25))]))
    cx.fill_preserve()
    src(cx, (0.4, 0.12, 0.17, 0.9))
    cx.set_line_width(6)
    cx.stroke()
    # epiglottis: flap over the airway, folds down while swallowing
    cx.save()
    cx.translate(-38, 34 - lar)
    cx.rotate(-0.15 - 1.05 * p_epi)
    cx.move_to(0, 0)
    cx.curve_to(-6, -40, -16, -70, -34, -86)
    cx.curve_to(-14, -80, 8, -50, 12, 0)
    cx.close_path()
    fs(cx, shade(tissue, 0.1), (0.45, 0.2, 0.22, 0.9), 5)
    cx.restore()
    # wet highlights (disappear as the throat dries)
    _wet_streak(cx, [(230, -196), (140, -206), (60, -186)], wet, 8)
    _wet_streak(cx, [(-140, -170), (-150, -100), (-146, -30)], wet, 6)
    _wet_streak(cx, [(-30, -60), (-34, -10)], wet, 5)

    # reflex signal: a glowing pulse travelling from the throat wall up toward the brain
    sig = st.get("signal", 0.0)
    if sig > 0:
        pts = [(-152, -60), (-180, -170), (-200, -260), (-230, -340)]
        k = st.get("signal_pos", 0.0)
        cx.move_to(*pts[0])
        cx.curve_to(*pts[1], *pts[2], *pts[3])
        cx.set_dash([4, 12])
        src(cx, (1, 0.95, 0.6, 0.85 * sig))
        cx.set_line_width(5)
        cx.stroke()
        cx.set_dash([])
        # bezier point
        u = clamp(k)
        bx = ((1 - u) ** 3 * pts[0][0] + 3 * (1 - u) ** 2 * u * pts[1][0] + 3 * (1 - u) * u * u * pts[2][0] + u ** 3 * pts[3][0])
        by = ((1 - u) ** 3 * pts[0][1] + 3 * (1 - u) ** 2 * u * pts[1][1] + 3 * (1 - u) * u * u * pts[2][1] + u ** 3 * pts[3][1])
        cx.arc(bx, by, 40, 0, 2 * math.pi)
        cx.set_source(rgrad(cx, bx, by, 0, 40, [(0, (1, 0.95, 0.55, 0.95 * sig)), (1, (1, 0.9, 0.4, 0))]))
        cx.fill()
        circle(cx, bx, by, 9)
        src(cx, (1, 1, 0.85, sig))
        cx.fill()

    # saliva bolus: sits at the back of the tongue, then travels down the oesophagus
    b = st.get("bolus_pos", 0.0)      # 0 resting on tongue .. 1 gone down
    if amount > 0.01 and b < 0.999:
        path = [(-10, -176), (-80, -150), (-120, -60), (-118, 40), (-117, 200), (-117, 420)]
        segs = len(path) - 1
        u = clamp(b) * segs
        i = min(int(u), segs - 1)
        f = u - i
        bx = path[i][0] + (path[i + 1][0] - path[i][0]) * f
        by = path[i][1] + (path[i + 1][1] - path[i][1]) * f
        r = 30 * math.sqrt(amount)
        stretch_y = 1 + 0.6 * smooth(prog(b, 0.35, 0.55))
        stretch_x = 1 / math.sqrt(stretch_y)
        if b > 0.5:   # peristaltic squeeze ring just above the bolus
            ry = by - r * stretch_y - 14
            line(cx, [(ex0 - 4, ry), (ex0 + 18, ry + 6)], (0.55, 0.2, 0.25, 0.9), 9)
            line(cx, [(ex1 + 4, ry), (ex1 - 18, ry + 6)], (0.55, 0.2, 0.25, 0.9), 9)
        ellipse(cx, bx, by, r * stretch_x, r * stretch_y)
        cx.set_source(rgrad(cx, bx - r * 0.3, by - r * 0.4, r * 0.1, r * 1.4,
                            [(0, (0.92, 0.98, 1, 0.95)), (0.5, (*SALIVA[:3], 0.85)), (1, (0.35, 0.65, 0.9, 0.85))]))
        cx.fill_preserve()
        src(cx, (0.1, 0.3, 0.5, 0.9))
        cx.set_line_width(4)
        cx.stroke()
        ellipse(cx, bx - r * 0.3 * stretch_x, by - r * 0.35 * stretch_y, r * 0.28, r * 0.16, -0.5)
        src(cx, (1, 1, 1, 0.8))
        cx.fill()
    # empty placeholder where saliva should be
    em = st.get("empty", 0.0)
    if em > 0:
        x, y, r = -10, -176, 30
        cx.move_to(x, y - r * 1.5)
        cx.curve_to(x + r * 1.1, y - r * 0.2, x + r, y + r, x, y + r)
        cx.curve_to(x - r, y + r, x - r * 1.1, y - r * 0.2, x, y - r * 1.5)
        cx.set_dash([7, 7])
        src(cx, (1, 1, 1, 0.9 * em))
        cx.set_line_width(4.5)
        cx.stroke()
        cx.set_dash([])
    # strain marks when trying to swallow with nothing there
    if strain > 0:
        for k, (x, y, a) in enumerate([(-190, -110, 0.3), (-195, -40, 0.0), (-188, 30, -0.3)]):
            j = 3 * math.sin(t * 30 + k)
            line(cx, [(x + j, y), (x - 26 + j, y - 12 * math.tan(a))], (1, 0.75, 0.3, 0.95 * strain), 7)


def draw_lens(cx, st, t, appear=1.0):
    if appear <= 0:
        return
    x, y, r = LENS
    k = back_out(appear, 1.2) if appear < 1 else 1.0
    cx.save()
    cx.translate(x, y)
    cx.scale(k, k)
    # drop shadow
    circle(cx, 10, 18, r + 22)
    cx.set_source(rgrad(cx, 10, 18, r * 0.8, r + 40, [(0, (0.2, 0.12, 0.08, 0.30)), (1, (0.2, 0.12, 0.08, 0))]))
    cx.fill()
    # content
    cx.save()
    circle(cx, 0, 0, r)
    cx.clip()
    cx.save()
    cx.scale(r / 292, r / 292)
    draw_lens_content(cx, st, t)
    cx.restore()
    # inner shadow (glass depth)
    circle(cx, 0, 0, r)
    cx.set_source(rgrad(cx, 0, 0, r * 0.75, r, [(0, (0, 0, 0, 0)), (1, (0.15, 0.05, 0.08, 0.35))]))
    cx.fill()
    # glass highlight
    cx.arc(0, 0, r - 26, math.radians(200), math.radians(250))
    src(cx, (1, 1, 1, 0.35))
    cx.set_line_width(12)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke()
    cx.restore()
    # rim (metallic, dimensional)
    circle(cx, 0, 0, r + 11)
    cx.set_source(vgrad(cx, 0, -r, 0, r, [(0, hexc("#F3F5F8")), (0.5, hexc("#B9C3CF")), (1, hexc("#7D8896"))]))
    cx.set_line_width(24)
    cx.stroke()
    circle(cx, 0, 0, r + 24)
    src(cx, OUTLINE)
    cx.set_line_width(7)
    cx.stroke()
    circle(cx, 0, 0, r - 1)
    src(cx, OUTLINE)
    cx.set_line_width(5)
    cx.stroke()
    cx.restore()


def draw_label(cx, txt, x, y, tx, ty, a):
    """Small diagram tag with a leader line to (tx,ty)."""
    if a <= 0:
        return
    cx.push_group()
    line(cx, [(x, y), (tx, ty)], OUTLINE, 5)
    circle(cx, tx, ty, 8)
    fs(cx, WHITE, OUTLINE, 4)
    cx.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(44)
    e = cx.text_extents(txt)
    w, h = e.x_advance + 48, 72
    rrect(cx, x - w / 2, y - h / 2, w, h, 36)
    fs(cx, WHITE, OUTLINE, 5)
    cx.move_to(x - e.x_advance / 2, y - e.height / 2 - e.y_bearing)
    src(cx, OUTLINE)
    cx.show_text(txt)
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)


def draw_thought(cx, x, y, a, t, src_pt):
    """Thought bubble with an empty (dashed) droplet inside."""
    if a <= 0:
        return
    k = back_out(min(1, a * 1.0)) if a < 1 else 1.0
    cx.push_group()
    sx, sy = src_pt
    for i, (f, r) in enumerate([(0.25, 11), (0.5, 17)]):
        circle(cx, sx + (x - sx) * f, sy + (y - sy) * f, r * k)
        fs(cx, WHITE, OUTLINE, 5)
    cx.save()
    cx.translate(x, y)
    cx.scale(k, k)
    pts = []
    n = 9
    for i in range(n):
        ang = i / n * 2 * math.pi
        pts.append((math.cos(ang) * 120, math.sin(ang) * 96))
    cx.new_path()
    for i in range(n):
        a0 = i / n * 2 * math.pi
        a1 = (i + 1) / n * 2 * math.pi
        p0 = (math.cos(a0) * 120, math.sin(a0) * 96)
        p1 = (math.cos(a1) * 120, math.sin(a1) * 96)
        mid = ((a0 + a1) / 2)
        c = (math.cos(mid) * 168, math.sin(mid) * 136)
        if i == 0:
            cx.move_to(*p0)
        cx.curve_to(p0[0] + (c[0] - p0[0]) * 0.8, p0[1] + (c[1] - p0[1]) * 0.8,
                    p1[0] + (c[0] - p1[0]) * 0.8, p1[1] + (c[1] - p1[1]) * 0.8, *p1)
    cx.close_path()
    fs(cx, WHITE, OUTLINE, 6)
    # dashed empty drop
    r = 40
    cx.move_to(0, -r * 1.55)
    cx.curve_to(r * 1.1, -r * 0.25, r, r, 0, r)
    cx.curve_to(-r, r, -r * 1.1, -r * 0.25, 0, -r * 1.55)
    cx.set_dash([9, 8], (t * 18) % 17)
    src(cx, hexc("#5AA7E0"))
    cx.set_line_width(6)
    cx.stroke()
    cx.set_dash([])
    cx.restore()
    cx.pop_group_to_source()
    cx.paint_with_alpha(min(1, a * 1.5))

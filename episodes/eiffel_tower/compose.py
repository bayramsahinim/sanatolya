"""2D layer: characters, hands, steam, captions, grade - composited over the Cycles plates.

usage: python -m episodes.eiffel_tower.compose preview <frame> [<frame> ...]
       python -m episodes.eiffel_tower.compose render     (pipes frames to ffmpeg -> build/video_noaudio.mp4)
"""
import json
import math
import os
import subprocess
import sys
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image

from cinecode.characters import breathe, talk, walk
from cinecode.core import OUTLINE, circle, ellipse, fs, hexc, line, src
from episodes.eiffel_tower import cast as K
from episodes.eiffel_tower.timeline import FPS, NFRAMES, SHOTS, frames, shot_at_frame

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FR = os.path.join(ROOT, "build", "frames")
W, H = 1080, 1920
WORDS = json.load(open(os.path.join(ROOT, "assets", "audio", "tts_eiffel", "words.json")))


# ======================================================================= helpers
def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def win(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= b)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


@lru_cache(maxsize=64)
def _load(path, size=(W, H)):
    im = Image.open(path)
    mode = im.mode
    im = im.convert("RGBA")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    a = np.asarray(im).astype(np.uint16)
    # premultiply for cairo (BGRA)
    al = a[..., 3:4]
    rgb = (a[..., :3] * al // 255).astype(np.uint8)
    out = np.empty((size[1], size[0], 4), np.uint8)
    out[..., 0] = rgb[..., 2]
    out[..., 1] = rgb[..., 1]
    out[..., 2] = rgb[..., 0]
    out[..., 3] = a[..., 3]
    return out


def surf_from(arr):
    arr = np.ascontiguousarray(arr)
    h, w = arr.shape[:2]
    s = cairo.ImageSurface.create_for_data(memoryview(arr).cast("B"), cairo.FORMAT_ARGB32, w, h)
    return s, arr


def paint_img(cx, path, alpha=1.0):
    if not os.path.exists(path):
        return False
    s, keep = surf_from(_load(path).copy())
    cx.set_source_surface(s, 0, 0)
    cx.paint_with_alpha(alpha)
    return True


def solve_arm(fig, p, which, target):
    """2-bone IK: set arm angles so the hand reaches world `target`."""
    st = fig.st
    J = fig.joints(p)
    sh = J["sh_" + which]
    tx = (target[0] - p.x) / p.s
    ty = (target[1] - p.y) / (p.s * p.squash)
    if p.view == "front":
        side = -1 if which == "a" else 1
    else:
        side = 1 if p.f >= 0 else -1
    dx, dy = tx - sh[0], ty - sh[1]
    U, F = st.upper, st.fore
    L = max(1e-3, min(math.hypot(dx, dy), U + F - 0.5))
    phi = math.atan2(side * dx, dy)
    ca = (U * U + L * L - F * F) / (2 * U * L)
    alpha = math.acos(max(-1, min(1, ca)))
    a = phi - alpha  # elbow outward/down
    ex, ey = side * math.sin(a) * U, math.cos(a) * U
    hx, hy = side * math.sin(phi) * L, math.cos(phi) * L
    e = math.atan2(side * (hx - ex), hy - ey) - a
    kw = {"arm_" + which: math.degrees(a), "elb_" + which: math.degrees(e)}
    return p.but(**kw)


def stand(fig, A, name, t, h=1.78, **kw):
    x, y, ppm = A[name][0], A[name][1], A[name][2]
    return K.pose_for(x, y, ppm, h, t=t, seed=fig.seed, **kw)


def sit(fig, A, name, t, h=1.78, **kw):
    """Seat anchor = hip point."""
    x, y, ppm = A[name][0], A[name][1], A[name][2]
    p = K.pose_for(x, y, ppm, h, t=t, seed=fig.seed, **kw)
    st = fig.st
    p = K.seated(p)
    return p.but(y=y + p.s * (st.thigh + st.shin))


def shadow(cx, x, y, w, alpha=0.35):
    g = cairo.RadialGradient(x, y, 0, x, y, w)
    g.add_color_stop_rgba(0, 0.08, 0.05, 0.03, alpha)
    g.add_color_stop_rgba(1, 0.08, 0.05, 0.03, 0)
    cx.save()
    cx.translate(x, y)
    cx.scale(1, 0.22)
    cx.translate(-x, -y)
    cx.arc(x, y, w, 0, 2 * math.pi)
    cx.set_source(g)
    cx.fill()
    cx.restore()


def draw_fig(cx, fig, p, shadow_w=None):
    if shadow_w:
        shadow(cx, p.x, p.y, shadow_w * p.s)
    return fig.draw(cx, p)


def hand_line(cx, pts, ppm, sleeve=None, col=K.SuitStyle.limb):
    """A stick arm for close-ups (sizes in metres via pixels-per-metre)."""
    lw = 0.011 * ppm
    if sleeve:
        line(cx, pts[:2], OUTLINE, 0.042 * ppm)
        line(cx, pts[:2], sleeve, 0.032 * ppm)
        line(cx, pts[1:], col, lw)
    else:
        line(cx, pts, col, lw)
    circle(cx, pts[-1][0], pts[-1][1], 0.014 * ppm)
    fs(cx, col, None, 0)


def arm_to(x, y, ppm, dx, dy, ex=0.0, ey=0.0):
    """Arm reaching to (x,y) from a shoulder dx,dy metres away (screen-space); elbow offset ex,ey."""
    sx, sy = x + dx * ppm, y + dy * ppm
    mx, my = (x + sx) / 2 + ex * ppm, (y + sy) / 2 + ey * ppm
    return [(sx, sy), (mx, my), (x, y)]


def steam(cx, x, y, t, scale=1.0, seed=0, n=10, drift=(-60, -160), alpha=0.75):
    rng = np.random.default_rng(seed)
    offs = rng.random(n)
    for k in range(n):
        ph = (t * 0.9 + offs[k]) % 1.0
        r = (18 + 70 * ph) * scale
        px = x + drift[0] * ph * scale + math.sin(k * 3 + t * 2) * 12 * scale
        py = y + drift[1] * ph * scale * 2.2
        a = alpha * (1 - ph) * min(1, ph * 6)
        g = cairo.RadialGradient(px, py, 0, px, py, r)
        g.add_color_stop_rgba(0, 0.97, 0.95, 0.92, a)
        g.add_color_stop_rgba(1, 0.97, 0.95, 0.92, 0)
        cx.arc(px, py, r, 0, 2 * math.pi)
        cx.set_source(g)
        cx.fill()


def speaking(t, t0, t1):
    return t0 <= t <= t1


# ======================================================================= per-shot 2D layers
DRAW = {}
POST = []  # callables drawn after the foreground (objects on tables) layer
PUSH = {}  # sid -> (z0, z1, fx, fy) plate push-in


def d(sid, push=None):
    def deco(fn):
        DRAW[sid] = fn
        if push:
            PUSH[sid] = push
        return fn
    return deco


def T(sid):
    return [s for s in SHOTS if s[0] == sid][0][1]


@d("s01_deal")
def _s01(cx, t, A):
    # Poisson (left) slides the envelope; Lustig (right) receives it. Both behind the table.
    env = A["env"]
    pl = stand(K.POISSON, A, "poisson", t, view="side", f=1, mouth="flat", brows="worried", look=(0.6, 0.3))
    ll = stand(K.LUSTIG, A, "lustig", t, view="side", f=-1, mouth="smirk", brows="skeptic", look=(-0.5, 0.4), eyes="half")
    u = win(t, 0.05, 1.2)
    ptgt = (env[0] - 40, env[1] - 10) if u < 0.75 else (env[0] - 120 * (u - 0.75) * 4 - 40, env[1] - 30 * (u - 0.75) * 4 - 10)
    pl = solve_arm(K.POISSON, pl, "b", ptgt)
    lt = (env[0] + 40, env[1] - 6) if u > 0.85 else (A["lustig"][0] - 90, A["lustig"][1] - 0.95 * A["lustig"][2])
    ll = solve_arm(K.LUSTIG, ll, "b", lt)
    Jp = draw_fig(cx, K.POISSON, breathe(pl, t))
    Jl = draw_fig(cx, K.LUSTIG, breathe(ll, t))

    def arms(cx, Jp=Jp, Jl=Jl, sp=pl.s, sl=ll.s):
        for J, st, s in ((Jp, K.POISSON_STYLE, sp), (Jl, K.LUSTIG_STYLE, sl)):
            pts = [J["sh_b"], J["elb_b"], J["hand_b"]]
            line(cx, pts[:2], OUTLINE, 22 * s)
            line(cx, pts[:2], st.suit, 15 * s)
            line(cx, pts[1:], st.limb, st.limb_w * s)
            circle(cx, pts[2][0], pts[2][1], st.limb_w * 0.9 * s)
            fs(cx, st.limb, None, 0)
    POST.append(arms)


@d("s03_problem", push=(1.0, 1.07, 0.5, 0.62))
def _s03(cx, t, A):
    A = dict(A, lustig=[0.66 * W, 0.975 * H, 0.44 * H / 1.78, 3.0])
    p = stand(K.LUSTIG, A, "lustig", t, view="front", mouth="smirk", brows="neutral", look=(0.2, -0.1))
    # tips his hat with a proud little lean
    lift = win(t, 0.5, 0.9) - win(t, 1.4, 1.8)
    p = p.but(arm_b=-170 * lift + 15 * (1 - lift), elb_b=-25 * lift + 10, lean=-2 * lift, tilt=-6 * lift)
    p = p.but(arm_a=25, elb_a=60)
    draw_fig(cx, K.LUSTIG, breathe(p, t), shadow_w=70)


@d("s04_own", push=(1.0, 1.12, 0.5, 0.42))
def _s04(cx, t, A):
    p = stand(K.LUSTIG, A, "lustig", t, view="front", mouth="smirk" if t > 0.55 else "flat",
              brows="skeptic" if t > 0.5 else "neutral", look=(-0.3 if t < 0.5 else 0.5, 0.0), eyes="half" if t > 0.5 else "open")
    shrug = win(t, 0.5, 0.8) - win(t, 1.2, 1.5)
    p = p.but(arm_a=15 + 35 * shrug, elb_a=20 + 70 * shrug, arm_b=15 + 35 * shrug, elb_b=20 + 70 * shrug, head_dy=6 * shrug,
              tilt=5 * shrug)
    draw_fig(cx, K.LUSTIG, breathe(p, t), shadow_w=70)


def _reading(cx, t, A, low, fig=None, look=(0, 0.6), **kw):
    fig = fig or K.LUSTIG
    p = sit(fig, A, "lustig", t, view="front", look=look, **kw)
    p = p.but(arm_a=20, elb_a=95, arm_b=20, elb_b=95)
    J = fig.draw(cx, breathe(p, t, 0.5))
    s = p.s
    hx, hy = J["head"]
    top = hy + (-40 + low * 250) * s
    hgt = 420 * s * (1 - 0.5 * low)
    wdt = 190 * s
    img = _load(os.path.join(ROOT, "build", "tex", "newspaper.png"), (700, 950))
    sf, keep = surf_from(img.copy())
    cx.save()
    cx.translate(hx - wdt, top)
    cx.scale(2 * wdt / 700, hgt / 950)
    cx.set_source_surface(sf, 0, 0)
    cx.paint()
    cx.restore()
    cx.rectangle(hx - wdt, top, 2 * wdt, hgt)
    fs(cx, None, OUTLINE, 4 * s)
    for sx in (-1, 1):
        circle(cx, hx + sx * (wdt - 6 * s), top + 40 * s, 9 * s)
        fs(cx, K.SuitStyle.limb, None, 0)
    return p, J


@d("s06_cafe")
def _s06(cx, t, A):
    _reading(cx, t, A, 0.45, mouth="flat", brows="neutral", eyes="half", look=(0.0, 0.9))


@d("s07_headline")
def _s07(cx, t, A):
    for k, side in (("paper_l", -1), ("paper_r", 1)):
        x, y, ppm = A[k]
        hand_line(cx, arm_to(x, y, ppm, side * 0.12, 0.45, side * 0.05, 0.02), ppm, sleeve=K.LUSTIG_STYLE.suit)


@d("s08_idea", push=(1.02, 1.1, 0.5, 0.45))
def _s08(cx, t, A):
    low = 0.62 * win(t, 0.05, 0.45)
    p, J = _reading(cx, t, A, low, mouth="smirk" if t > 0.55 else "flat", brows="skeptic" if t > 0.5 else "neutral",
                    eyes="half" if t > 0.45 else "open", look=(0.0, 0.0) if t < 0.5 else (0.7, -0.2))
    g = win(t, 0.55, 0.7) - win(t, 0.85, 1.0)
    if g > 0:
        hx, hy = J["head"]
        _glint(cx, hx + 75 * p.s, hy - 70 * p.s, 26 * p.s * g, g)


def _glint(cx, x, y, r, a):
    cx.save()
    cx.translate(x, y)
    for k in range(4):
        cx.rotate(math.pi / 4)
        cx.move_to(0, -r)
        cx.line_to(r * 0.18, 0)
        cx.line_to(0, r)
        cx.line_to(-r * 0.18, 0)
        cx.close_path()
        src(cx, (1, 0.93, 0.7, a))
        cx.fill()
    cx.restore()


@d("s09_forge")
def _s09(cx, t, A):
    x, y, ppm = A["pen_top"][:3]
    hand_line(cx, arm_to(x, y + 0.004 * ppm, ppm, 0.32, 0.5, 0.1, -0.02), ppm, sleeve=K.LUSTIG_STYLE.suit)


@d("s10_stamp")
def _s10(cx, t, A):
    x, y, ppm = A["knob"][:3]
    hand_line(cx, arm_to(x, y - 0.01 * ppm, ppm, -0.25, -0.55, -0.12, 0.0), ppm, sleeve=K.LUSTIG_STYLE.suit)


@d("s11_letters")
def _s11(cx, t, A):
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="o" if t > 0.5 else "flat",
            brows="up" if t > 0.5 else "neutral", eyes="wide" if t > 0.5 else "open", look=(0, 0.7))
    p = p.but(arm_a=30, elb_a=70, arm_b=30, elb_b=70, lean=6 * win(t, 0.5, 0.8))
    K.POISSON.draw(cx, breathe(p, t))


@d("s12_lobby")
def _s12(cx, t, A):
    p = stand(K.LUSTIG, A, "lustig", t, view="side", f=1, mouth="smirk", brows="neutral")
    p = walk(p, t, speed=1.0, amp=0.8)
    s = p.s
    draw_fig(cx, K.LUSTIG, p, shadow_w=70)


def _salon_people(cx, t, A, lustig=True, talk_win=None, lean=0.0, poisson_kw=None, lustig_kw=None, dealers=None, look=None):
    dealers = dealers if dealers is not None else K.DEALERS
    # far-side seated dealers (+ Poisson centre)
    seats = [("d1", dealers[0]), ("poisson", K.POISSON if dealers is K.DEALERS else dealers[1]), ("d3", dealers[2] if len(dealers) > 2 else dealers[0])]
    out = {}
    for k, (name, fig) in enumerate(seats):
        kw = dict(view="front", mouth="flat", brows="neutral", look=look or (-0.6, 0.1))
        if name == "poisson" and poisson_kw:
            kw.update(poisson_kw)
        p = sit(fig, A, name, t, **kw)
        p = p.but(arm_a=35, elb_a=60, arm_b=35, elb_b=60, lean=lean)
        out[name] = fig.draw(cx, breathe(p, t + k))
    if "d4" in A and dealers is K.DEALERS:
        p = sit(K.DEALERS[3], A, "d4", t, view="side", f=-1, mouth="flat", brows="neutral", look=(-0.5, 0))
        p = p.but(lean=lean * 1.3, arm_b=60, elb_b=40)
        out["d4"] = K.DEALERS[3].draw(cx, breathe(p, t + 7))
    if lustig:
        kw = dict(view="side", f=1, mouth="smile", brows="neutral")
        kw.update(lustig_kw or {})
        p = stand(K.LUSTIG, A, "lustig", t, **kw)
        if talk_win and talk_win[0] <= t <= talk_win[1]:
            p = talk(p.but(mouth="grin"), t)
            g = math.sin(t * 5) * 12
            p = p.but(arm_b=70 + g, elb_b=50)
        out["lustig"] = draw_fig(cx, K.LUSTIG, breathe(p, t), shadow_w=80)
    return out


@d("s13_meeting", push=(1.0, 1.06, 0.45, 0.5))
def _s13(cx, t, A):
    _salon_people(cx, t, A, talk_win=(0.0, 0.6), look=(-0.7, 0.0))


@d("s15_quiet", push=(1.0, 1.08, 0.4, 0.5))
def _s15(cx, t, A):
    lean = 14 * win(t, 0.3, 1.0)
    _salon_people(cx, t, A, lustig=False, lean=lean, look=(-0.2, 0.8) if 0.6 < t < 1.6 else (-0.7, 0.0))
    # Lustig: finger to his lips - keep quiet
    shh = win(t, 1.5, 1.8) * (1 - win(t, 2.9, 3.1))
    p = stand(K.LUSTIG, A, "lustig", t, view="front", mouth="o" if shh > 0.5 else "flat", brows="skeptic", eyes="half",
              look=(0.7, 0.0))
    p = p.but(arm_a=20, elb_a=25)
    J = K.LUSTIG.joints(p)
    hx = p.x + J["head"][0] * p.s
    hy = p.y + (J["head"][1] + K.SuitStyle.head_r * 0.42) * p.s
    rest = (p.x + 45 * p.s, p.y - 120 * p.s)
    tgt = (rest[0] + (hx + 8 * p.s - rest[0]) * shh, rest[1] + (hy - rest[1]) * shh)
    p = solve_arm(K.LUSTIG, p, "b", tgt)
    Jw = draw_fig(cx, K.LUSTIG, breathe(p, t), shadow_w=80)
    if shh > 0.5:
        line(cx, [(tgt[0], tgt[1] + 6 * p.s), (tgt[0], tgt[1] - 26 * p.s)], K.SuitStyle.limb, 7 * p.s)


@d("s16_poisson", push=(1.0, 1.1, 0.5, 0.45))
def _s16(cx, t, A):
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="flat", brows="up", eyes="open", look=(-0.5, 0.3))
    p = p.but(arm_a=30, elb_a=80, arm_b=30, elb_b=80, lean=4)
    K.POISSON.draw(cx, breathe(p, t))
    for name, fig, kk in (("d1", K.DEALERS[0], 0), ("d3", K.DEALERS[2], 2)):
        q = sit(fig, A, name, t, view="front", mouth="flat", look=(-0.6, 0.2))
        fig.draw(cx, breathe(q.but(arm_a=35, elb_a=60, arm_b=35, elb_b=60), t + kk))


@d("s17_doubts", push=(1.02, 1.12, 0.5, 0.42))
def _s17(cx, t, A):
    want = t < 0.9
    p = sit(K.POISSON, A, "poisson", t, view="front",
            mouth="smile" if want else ("frown" if t > 1.3 else "flat"),
            brows="up" if want else "worried", eyes="wide" if want else "open",
            look=(0.0, 0.8) if t < 1.6 else (0.6, -0.1), sweat=win(t, 1.6, 2.2))
    p = p.but(arm_a=40, elb_a=80, arm_b=20 + 120 * win(t, 1.2, 1.6), elb_b=120 * win(t, 1.2, 1.6), lean=5)
    K.POISSON.draw(cx, breathe(p, t))


@d("s18_hint", push=(1.0, 1.08, 0.4, 0.42))
def _s18(cx, t, A):
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="flat", brows="worried", look=(-0.8, -0.2))
    p = p.but(arm_a=35, elb_a=60, arm_b=35, elb_b=60)
    K.POISSON.draw(cx, breathe(p, t))
    lean = 16 * win(t, 0.1, 0.6)
    q = stand(K.LUSTIG, A, "lustig", t, view="side", f=1, mouth="smirk", brows="skeptic", eyes="half", look=(0.8, 0.3))
    q = q.but(lean=lean)
    if 0.7 < t < 2.0:
        q = talk(q.but(mouth="smile"), t, 7)
    # rubs thumb and fingers: money gesture
    rub = math.sin(t * 16) * 6 * win(t, 0.8, 1.0)
    q = q.but(arm_b=75 + rub, elb_b=70, arm_a=20, elb_a=30)
    draw_fig(cx, K.LUSTIG, breathe(q, t), shadow_w=70)


@d("s19_glance", push=(1.0, 1.06, 0.45, 0.4))
def _s19(cx, t, A):
    # exchange of glances: eyes slide back and forth, then Poisson gives a small nod
    ph = t
    p_look = (-0.9, 0.0) if ph < 0.6 else ((0.9, 0.3) if ph < 1.1 else (-0.9, 0.0))
    nod = math.sin(max(0, ph - 1.3) * 9) * 4 * win(ph, 1.3, 1.4) * (1 - win(ph, 1.8, 2.0))
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="flat", brows="worried", look=p_look,
            sweat=0.6)
    p = p.but(arm_a=35, elb_a=60, arm_b=35, elb_b=60, head_dy=nod)
    K.POISSON.draw(cx, breathe(p, t))
    q = stand(K.LUSTIG, A, "lustig", t, view="side", f=1, mouth="smirk", brows="skeptic", eyes="half",
              look=(0.9, 0.3) if ph < 1.1 else (0.8, 0.5))
    q = q.but(lean=16, arm_b=40, elb_b=40, arm_a=20, elb_a=30)
    draw_fig(cx, K.LUSTIG, breathe(q, t), shadow_w=70)


@d("s20_paid")
def _s20(cx, t, A):
    POST.append(lambda c: _s20_hands(c, t, A))


def _s20_hands(cx, t, A):
    env, cash = A["env"], A["cash"]
    ppm = env[2]
    tgt = (cash[0] + 0.07 * ppm, cash[1]) if t < 0.5 else (env[0] + 0.12 * ppm, env[1])
    hand_line(cx, arm_to(tgt[0], tgt[1], ppm, 0.28, -0.42, 0.08, 0.0), ppm, sleeve=K.POISSON_STYLE.suit)
    a = win(t, 0.95, 1.35)
    lx, ly = env[0] - 0.1 * ppm, env[1] - 0.01 * ppm
    sx, sy = lx - 0.35 * ppm, ly - 0.55 * ppm
    cur = (sx + (lx - sx) * (0.4 + 0.6 * a), sy + (ly - sy) * (0.4 + 0.6 * a))
    hand_line(cx, arm_to(cur[0], cur[1], ppm, -0.3, -0.45, -0.08, 0.0), ppm, sleeve=K.LUSTIG_STYLE.suit)


@d("s21_exit", push=(1.0, 1.05, 0.5, 0.55))
def _s21(cx, t, A):
    door = A["door"]
    # walks out of the hotel door toward camera-left
    u = win(t, 0.0, 1.5)
    x = door[0] - 260 * u
    y = door[1] + 520 * u
    ppm = door[2] * (1 + 1.1 * u)
    p = K.pose_for(x, y, ppm, 1.78, t=t, seed=11, view="side", f=-1, mouth="smirk", brows="neutral", eyes="half")
    p = walk(p, t, 1.1, 0.8)
    p = p.but(arm_a=10, elb_a=10)
    J = draw_fig(cx, K.LUSTIG, p, shadow_w=80)
    # briefcase in the far hand
    hx, hy = J["hand_a"]
    s = p.s
    cx.save()
    cx.translate(hx, hy + 6 * s)
    from cinecode.core import rrect
    rrect(cx, -40 * s, 0, 80 * s, 58 * s, 7 * s)
    fs(cx, hexc("#5a2e1e"), OUTLINE, 4 * s)
    line(cx, [(-40 * s, 18 * s), (40 * s, 18 * s)], hexc("#3a1e14"), 3 * s)
    cx.restore()


@d("s22_train")
def _s22(cx, t, A):
    st = A["stack"]
    s = st[2] / 40
    steam(cx, st[0], st[1], t * 1.6, scale=s * 1.2, seed=3, n=14, drift=(-90, -60))
    w = A["window"]
    if w[3] > 0 and -100 < w[0] < W + 100:
        pass


@d("s23_realize", push=(1.0, 1.16, 0.5, 0.42))
def _s23(cx, t, A):
    real = win(t, 1.2, 1.6)
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="o" if real > 0.5 else "flat",
            brows="worried" if real > 0.5 else "neutral", eyes="wide" if real > 0.5 else "open",
            look=(0.3, 0.8) if t < 1.2 else (0.0, 0.0), sweat=win(t, 1.6, 2.2))
    shake = math.sin(t * 40) * 1.5 * real
    p = p.but(arm_a=30, elb_a=95, arm_b=30, elb_b=95, lean=8 - 6 * real, head_dy=shake)
    K.POISSON.draw(cx, breathe(p, t))


@d("s25_silent", push=(1.0, 1.05, 0.55, 0.45))
def _s25(cx, t, A):
    p = sit(K.POISSON, A, "poisson", t, view="front", mouth="wavy", brows="worried", eyes="closed" if t > 1.2 else "open",
            look=(0.6, 0.5), blush=win(t, 0.3, 1.0))
    # pulls the bowler down over his eyes, then a finger to the lips
    pull = win(t, 1.0, 1.5)
    shh = win(t, 2.2, 2.6)
    p = p.but(arm_b=170 * pull * (1 - shh) + 150 * shh, elb_b=-30 * pull * (1 - shh) + 40 * shh, arm_a=30, elb_a=70,
              head_dy=5 * pull)
    K.POISSON.draw(cx, breathe(p, t))


@d("s26_strange")
def _s26(cx, t, A):
    st = A["stack"]
    steam(cx, st[0], st[1], t * 1.2, scale=st[2] / 40 * 1.2, seed=5, n=14, drift=(60, -50))
    a = A["lustig"]
    p = K.pose_for(a[0], a[1], a[2], 1.78, t=t, seed=11, view="side", f=1, mouth="smirk", brows="skeptic", eyes="half")
    p = walk(p, t, 0.9, 0.7)
    p = p.but(arm_a=60, elb_a=80)
    J = draw_fig(cx, K.LUSTIG, p, shadow_w=80)
    # new folder of documents under his arm
    hx, hy = J["hand_a"]
    s = p.s
    cx.save()
    cx.translate(hx, hy)
    cx.rotate(-0.4)
    from cinecode.core import rrect
    rrect(cx, -10 * s, -50 * s, 70 * s, 90 * s, 4 * s)
    fs(cx, hexc("#b88a52"), OUTLINE, 4 * s)
    cx.restore()


@d("s27_again", push=(1.0, 1.07, 0.45, 0.5))
def _s27(cx, t, A):
    _salon_people(cx, t, A, dealers=K.NEW_DEALERS, talk_win=(0.2, 2.6), look=(-0.7, 0.0))


@d("s28_failed", push=(1.0, 1.1, 0.4, 0.45))
def _s28(cx, t, A):
    # the bearded dealer stands, slaps the documents back; Lustig's smile drops; a gendarme appears
    stand_u = win(t, 0.1, 0.5)
    a = A["poisson"]
    fig = K.NEW_DEALERS[0]
    p = sit(fig, A, "poisson", t, view="front", mouth="yell" if 0.4 < t < 1.2 else "frown", brows="angry", look=(-0.8, 0))
    st = fig.st
    p = p.but(y=p.y - stand_u * p.s * 60, hip_a=86 * (1 - stand_u), knee_a=88 * (1 - stand_u),
              hip_b=80 * (1 - stand_u), knee_b=84 * (1 - stand_u), arm_a=40 + 90 * stand_u, elb_a=30, arm_b=30, elb_b=50)
    if 0.4 < t < 1.2:
        p = talk(p, t, 11)
    fig.draw(cx, breathe(p, t))
    for name, f2, k in (("d1", K.NEW_DEALERS[1], 0), ("d3", K.NEW_DEALERS[2], 1)):
        q = sit(f2, A, name, t, view="front", mouth="o" if t > 0.6 else "flat", brows="up", look=(0.3, 0) if t > 0.6 else (-0.7, 0))
        f2.draw(cx, breathe(q.but(arm_a=35, elb_a=60, arm_b=35, elb_b=60), t + k))
    drop = win(t, 0.6, 0.9)
    q = stand(K.LUSTIG, A, "lustig", t, view="side", f=1, mouth="flat" if drop > 0.5 else "smile",
              brows="worried" if drop > 0.5 else "neutral", look=(0.8, 0) if t < 1.2 else (-0.9, 0), sweat=win(t, 1.0, 1.4),
              eyes="open")
    q = q.but(lean=-6 * drop, arm_b=20, elb_b=20)
    draw_fig(cx, K.LUSTIG, breathe(q, t), shadow_w=80)
    # gendarme steps in from the left edge
    g = win(t, 1.1, 1.8)
    lx = A["lustig"]
    gx = -160 + 260 * g
    gp = K.pose_for(gx, lx[1] + 60, lx[2] * 1.12, 1.8, t=t, seed=50, view="side", f=1, mouth="frown", brows="angry")
    if 0 < g < 1:
        gp = walk(gp, t, 1.2, 0.8)
    draw_fig(cx, K.GENDARME, gp, shadow_w=80)


# ======================================================================= captions
CAP_SIZE = 74
CAP_Y = 1330


KEEP = {("Eiffel", "Tower"), ("André", "Poisson"), ("Victor", "Lustig"), ("seven", "thousand"),
        ("thousand", "tons"), ("scrap-metal", "dealers"), ("luxury", "hotel")}


def split_balanced(ws, max_chars, max_words, target):
    """DP split of one sentence's words into readable chunks."""
    n = len(ws)
    INF = 1e9
    best = [0.0] + [INF] * n
    prev = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - max_words), j):
            chunk = ws[i:j]
            txt = " ".join(x["w"] for x in chunk)
            L = len(txt)
            if L > max_chars and j - i > 1:
                continue
            c = (L - target) ** 2 * 0.05
            if j - i == 1 and len(chunk[0]["w"]) <= 4 and n > 1:
                c += 8  # avoid orphaned short words
            if j < n and chunk[-1]["w"][-1] in ",.?!\u2014":
                c -= 3  # natural pause
            if j < n and (chunk[-1]["w"], ws[j]["w"].strip(".,?!")) in KEEP:
                c += 30
            if j < n and ws[j]["start"] - chunk[-1]["end"] > 0.22:
                c -= 2
            if j < n and chunk[-1]["w"].lower() in ("the", "a", "to", "of", "and", "his", "its", "did", "he", "was", "were"):
                c += 4  # don't end on a function word
            if best[i] + c < best[j]:
                best[j] = best[i] + c
                prev[j] = i
    out, j = [], n
    while j > 0:
        out.append(ws[prev[j]:j])
        j = prev[j]
    return out[::-1]


def caption_chunks():
    """Group words into 1-3 word cues following speech rhythm."""
    lines = {}
    for w in WORDS:
        lines.setdefault(w["line"], []).append(w)
    chunks = []
    for li in sorted(lines):
        chunks += split_balanced(lines[li], 17, 3, 10)
    cues = []
    for k, c in enumerate(chunks):
        st = c[0]["start"] - 0.04
        en = c[-1]["end"] + 0.15
        if k + 1 < len(chunks):
            nst = chunks[k + 1][0]["start"] - 0.04
            en = nst if nst - c[-1]["end"] < 0.5 else min(en + 0.2, nst)
        cues.append((st, en, " ".join(x["w"] for x in c).replace("\u2014 ", "\u2014")))
    return cues


CUES = caption_chunks()


@lru_cache(maxsize=256)
def _cap_surface(txt):
    tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
    tc = cairo.Context(tmp)
    tc.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    tc.set_font_size(CAP_SIZE)
    ext = tc.text_extents(txt)
    pad = 40
    w, h = int(ext.x_advance + 2 * pad), int(CAP_SIZE * 1.6 + 2 * pad)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cx = cairo.Context(s)
    cx.select_font_face("Montserrat ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(CAP_SIZE)
    base = pad + CAP_SIZE * 1.05
    # soft drop shadow
    cx.move_to(pad, base + 5)
    cx.text_path(txt)
    cx.set_source_rgba(0, 0, 0, 0.35)
    cx.set_line_width(CAP_SIZE * 0.3)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    cx.fill()
    cx.new_path()
    cx.move_to(pad, base)
    cx.text_path(txt)
    cx.set_source_rgb(0.04, 0.04, 0.05)
    cx.set_line_width(CAP_SIZE * 0.24)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    cx.set_source_rgb(1, 1, 1)
    cx.fill()
    return s, w, h, base


def draw_caption(cx, gt):
    for st, en, txt in CUES:
        if st <= gt < en:
            s, w, h, base = _cap_surface(txt)
            cx.set_source_surface(s, W / 2 - w / 2, CAP_Y - base + CAP_SIZE * 0.35)
            cx.paint()
            return


# ======================================================================= grade
_rng = np.random.default_rng(1)
_GRAIN = [(_rng.normal(0, 1, (H // 2, W // 2)) * 3.2).astype(np.float32) for _ in range(8)]
yy, xx = np.mgrid[0:H, 0:W]
_VIG = (1 - 0.38 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)).clip(0.45, 1).astype(np.float32)
del yy, xx


def grade(arr, f, sid):
    """arr: HxWx4 BGRA uint8 -> graded RGB uint8."""
    rgb = arr[..., [2, 1, 0]].astype(np.float32)
    # warm golden grade: lift shadows toward brown, highlights toward cream
    lum = rgb.mean(axis=2, keepdims=True) / 255
    warm = np.array([1.04, 1.0, 0.92], np.float32)
    rgb = rgb * warm
    rgb = rgb + (1 - lum) * np.array([6, 3, 0], np.float32)
    rgb *= _VIG[..., None]
    g = _GRAIN[f % 8]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    rgb += g[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ======================================================================= frame
_anchor_cache = {}


def anchors(sid):
    if sid not in _anchor_cache:
        p = os.path.join(FR, sid, "anchors.json")
        _anchor_cache[sid] = json.load(open(p)) if os.path.exists(p) else {}
    return _anchor_cache[sid]


def render_frame(f):
    (sid, a, b, mode), i, n = shot_at_frame(f)
    t = i / FPS
    gt = f / FPS
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    fi = i if mode == "seq" else 0
    bgp = os.path.join(FR, sid, f"bg_{fi:04d}.png")
    fgp = os.path.join(FR, sid, f"fg_{fi:04d}.png")
    if mode == "seq" and not os.path.exists(bgp):
        # fall back to nearest rendered frame (tests)
        import glob
        fsx = sorted(glob.glob(os.path.join(FR, sid, "bg_*.png")))
        if fsx:
            bgp = min(fsx, key=lambda p: abs(int(p[-8:-4]) - fi))
            fgp = bgp.replace("bg_", "fg_")
    an = anchors(sid)
    A = an.get(str(i), {})
    cx.save()
    if sid in PUSH:
        z0, z1, fx, fy = PUSH[sid]
        z = z0 + (z1 - z0) * smooth(t / max(1e-3, n / FPS))
        cx.translate(fx * W, fy * H)
        cx.scale(z, z)
        cx.translate(-fx * W, -fy * H)
    paint_img(cx, bgp)
    if sid in DRAW:
        DRAW[sid](cx, t, A)
    paint_img(cx, fgp)
    for fn in POST:
        fn(cx)
    POST.clear()
    cx.restore()
    draw_caption(cx, gt)
    surf.flush()
    arr = np.ndarray((H, W, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1)).copy()
    return grade(arr, f, sid)


def _post_draw_order():
    pass


def preview(fs_):
    out = os.path.join(ROOT, "build", "preview")
    os.makedirs(out, exist_ok=True)
    for f in fs_:
        Image.fromarray(render_frame(f)).save(os.path.join(out, f"f{f:04d}.png"))


def _worker(args):
    a, b, path = args
    with open(path, "wb") as fh:
        for f in range(a, b):
            fh.write(render_frame(f).tobytes())
    return path


def render_all(out_mp4, procs=4):
    from multiprocessing import Pool
    tmp = os.path.join(ROOT, "build", "raw")
    os.makedirs(tmp, exist_ok=True)
    step = 60
    jobs = [(a, min(NFRAMES, a + step), os.path.join(tmp, f"chunk_{a:05d}.raw")) for a in range(0, NFRAMES, step)]
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
    with Pool(procs) as pool:
        for path in pool.imap(_worker, jobs):
            ff.stdin.write(open(path, "rb").read())
            os.remove(path)
            print("chunk", path, flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        preview([int(x) for x in sys.argv[2:]])
    elif sys.argv[1] == "render":
        render_all(os.path.join(ROOT, "build", "video_noaudio.mp4"))

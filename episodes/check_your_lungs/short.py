"""JUST NEEDY — CHECK YOUR LUNGS (vertical short, 1080x1920, 30 fps).

usage:
  python -m episodes.check_your_lungs.short audio      # voice split, music, sfx, mix, SRT
  python -m episodes.check_your_lungs.short video      # render frames + mux
  python -m episodes.check_your_lungs.short still 12.5 # one preview frame
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np
from scipy.signal import resample_poly

from cinecode import audio as A
from cinecode import captions as C
from cinecode.tts import read_wav
from episodes.check_your_lungs import art
from episodes.check_your_lungs.make_voice import take_path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "check_your_lungs")
OUTDIR = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_CHECK_YOUR_LUNGS_FINAL"
FPS = 30
DUR = 52.0
W, H = art.W, art.H

# ------------------------------------------------------------------ timeline
T_SWEEP0, T_SWEEP1 = 2.8, 7.9        # "breathe in" sweep down (as in the original)
T_RISE1 = 9.3                        # back to the top
T_HOLD0, T_HOLD1 = 9.6, 48.6         # the hold: one continuous, constant-speed descent
Y0, Y1 = art.EMOJI_TOP_Y, art.TRACK_BOT

# voice: (key, take window [a, b], video start, caption groups as (text, take-time start))
VOICE = [
    ("open", (0.00, 2.60), 0.00, [("Can you follow", 0.28), ("this breathing", 1.22), ("challenge?", 1.90)]),
    ("inhale", (3.25, 4.90), 2.65, [("Breathe in...", 3.41)]),
    ("ready", (7.90, 8.80), 7.95, [("Ready?", 8.01)]),
    ("hold", (12.60, 13.40), 8.85, [("Hold.", 12.74)]),
    ("out", (17.20, 18.70), 48.85, [("Breathe out.", 17.35)]),
    ("howfar", (19.85, 20.95), 50.25, [("How far", 19.98), ("did you get?", 20.35)]),
]
CAP_Y = 1712
CAP_SIZE = 86


def hold_p(t):
    return min(1.0, max(0.0, (t - T_HOLD0) / (T_HOLD1 - T_HOLD0)))


def cp_p(i):
    return (art.CPS[i] - Y0) / (Y1 - Y0)


HOLD_HITS = [T_HOLD0 + cp_p(i) * (T_HOLD1 - T_HOLD0) for i in range(4)]


def sweep_y(t):
    u = (t - T_SWEEP0) / (T_SWEEP1 - T_SWEEP0)
    u = min(1, max(0, u))
    # gentle ease at both ends, near-constant in the middle
    s = u * u * (3 - 2 * u) * 0.25 + u * 0.75
    return Y0 + (Y1 - Y0) * s


def emoji_y(t):
    if t < T_SWEEP0:
        return Y0 + 4 * math.sin(t * 2.4)          # idle bob
    if t < T_SWEEP1:
        return sweep_y(t)
    if t < T_RISE1:
        u = 0.5 - 0.5 * math.cos(math.pi * min(1, (t - T_SWEEP1) / (T_RISE1 - T_SWEEP1)))
        return Y1 + (Y0 - Y1) * u
    if t < T_HOLD0:
        return Y0
    return Y0 + (Y1 - Y0) * hold_p(t)


SWEEP_HITS = []
for _i in range(4):
    # first time sweep_y crosses CPS[i]
    tt = T_SWEEP0
    while tt < T_SWEEP1 and sweep_y(tt) < art.CPS[_i]:
        tt += 0.002
    SWEEP_HITS.append(tt)


def ease_out(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def back_out(x, s=1.9):
    x = min(1, max(0, x))
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def pulse(t, t0, d=0.5):
    """0 -> 1 -> 0 bump."""
    if t < t0 or t > t0 + d:
        return 0.0
    return math.sin(math.pi * (t - t0) / d)


def emoji_state(t):
    e = {"t": t}
    if t < T_HOLD0 - 0.2:
        e["kind"] = "gasp"
        # blinks while idle, mouth opens wide during the inhale sweep
        e["blink"] = max(pulse(t, 1.3, 0.16), pulse(t, 7.95 + 0.6, 0.16))
        m = 0.25
        if T_SWEEP0 <= t < T_SWEEP1 + 0.3:
            m = 0.25 + 0.75 * min(1, (t - T_SWEEP0) / 1.2)
        elif t >= T_SWEEP1 + 0.3:
            m = 1.0
        e["mouth"] = m
        e["sq"] = 1 - 0.06 * pulse(t, T_SWEEP0, 0.3)
        return e
    if t < T_HOLD1 + 0.05:
        p = hold_p(t)
        e["kind"] = "hold"
        n = sum(1 for h in HOLD_HITS[:3] if t >= h)
        e["eye"] = ["calm", "calm", "flat", "squeeze"][n]
        e["strain"] = p
        e["puff"] = 0.35 + 0.65 * min(1, p * 1.3)
        e["red"] = max(0, (p - 0.3) / 0.7) * 0.85
        e["sweat"] = max(0, (p - 0.42) / 0.58)
        sq = 1 - 0.1 * pulse(t, T_HOLD0 - 0.2, 0.35)
        for h in HOLD_HITS[:3]:
            sq -= 0.07 * pulse(t, h, 0.3)
        e["sq"] = sq
        return e
    e["kind"] = "relief"
    e["sq"] = 1 - 0.12 * pulse(t, T_HOLD1 + 0.05, 0.4)
    return e


# ------------------------------------------------------------------ drawing
_static = {}


def static():
    if not _static:
        _static["bg"] = art.make_background()
        _static["lungs"] = [art.make_lung(i) for i in range(4)]
        _static["parts"] = art.Particles()
        _static["title"] = C.render_text("BREATHING CHALLENGE", 72)
        _static["note"] = C.render_text("Just for fun. Stop if uncomfortable.", 38)
    return _static


def rrect(cx, x, y, w, h, r):
    cx.new_sub_path()
    cx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cx.close_path()


def paint_text(cx, item, x, y, alpha, scale=1.0):
    surf, w, h, pad = item
    cx.save()
    cx.translate(x, y)
    cx.scale(scale, scale)
    cx.set_source_surface(surf, -w / 2, -h / 2)
    cx.paint_with_alpha(alpha)
    cx.restore()


def cp_lit(t, i):
    """how 'lit' checkpoint i is (hold progress), and time since lit."""
    h = HOLD_HITS[i]
    if T_HOLD0 <= t and t >= h:
        return 1.0, t - h
    return 0.0, None


def draw_track(cx, t, ey):
    x = art.TRACK_X
    tw = art.TRACK_W
    top, bot = art.TRACK_TOP, art.TRACK_BOT
    # soft glow around the track
    g = cairo.LinearGradient(x - 70, 0, x + 70, 0)
    g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0)
    g.add_color_stop_rgba(0.5, 1, 0.85, 0.5, 0.16)
    g.add_color_stop_rgba(1, 1, 0.8, 0.4, 0)
    cx.set_source(g)
    cx.rectangle(x - 70, top - 30, 140, bot - top + 60)
    cx.fill()
    rrect(cx, x - tw / 2, top - 6, tw, bot - top + 12, tw / 2)
    cx.set_source_rgba(1, 1, 1, 1)
    cx.fill()
    inner = tw - 20
    rrect(cx, x - inner / 2, top + 4, inner, bot - top - 8, inner / 2)
    cx.set_source_rgba(0.06, 0.05, 0.06, 1)
    cx.fill()
    # progress fill: cool "air" during the breath-in, warm during the hold
    fill_to = None
    if T_SWEEP0 <= t < T_RISE1:
        fill_to, cols = ey, ((0.62, 0.9, 1.0), (0.35, 0.7, 1.0))
    elif t >= T_HOLD0:
        fill_to, cols = ey, ((1.0, 0.86, 0.3), (1.0, 0.5, 0.12))
    if fill_to is not None and fill_to > top + 10:
        fi = inner - 8
        g = cairo.LinearGradient(0, top, 0, bot)
        g.add_color_stop_rgba(0, *cols[0], 1)
        g.add_color_stop_rgba(1, *cols[1], 1)
        rrect(cx, x - fi / 2, top + 8, fi, fill_to - top - 8, fi / 2)
        cx.set_source(g)
        cx.fill()
        # glossy streak
        cx.rectangle(x - fi / 2 + 5, top + 14, 5, max(0, fill_to - top - 26))
        cx.set_source_rgba(1, 1, 1, 0.35)
        cx.fill()
    # checkpoints
    for i, cy in enumerate(art.CPS):
        lit, since = cp_lit(t, i)
        pop = 0.0
        if since is not None:
            pop = 0.22 * pulse(since, 0, 0.35)
        # quick glint as the breath-in sweep passes
        sw = pulse(t, SWEEP_HITS[i], 0.35) if t < T_RISE1 else 0
        r = art.CP_R * (1 + pop + 0.1 * sw)
        if lit:
            g = cairo.RadialGradient(x, cy, r * 0.6, x, cy, r * 2.0)
            g.add_color_stop_rgba(0, 1, 0.8, 0.3, 0.45)
            g.add_color_stop_rgba(1, 1, 0.7, 0.2, 0)
            cx.set_source(g)
            cx.arc(x, cy, r * 2.0, 0, 2 * math.pi)
            cx.fill()
        cx.arc(x, cy, r, 0, 2 * math.pi)
        cx.set_source_rgba(1, 1, 1, 1)
        cx.fill()
        ri = r * 0.68
        cx.arc(x, cy, ri, 0, 2 * math.pi)
        if lit:
            g = cairo.RadialGradient(x - ri * 0.3, cy - ri * 0.3, 0, x, cy, ri)
            g.add_color_stop_rgba(0, 1, 0.9, 0.45, 1)
            g.add_color_stop_rgba(1, 1, 0.55, 0.1, 1)
            cx.set_source(g)
        elif sw > 0:
            cx.set_source_rgba(0.06 + 0.5 * sw, 0.05 + 0.75 * sw, 0.06 + 0.9 * sw, 1)
        else:
            cx.set_source_rgba(0.06, 0.05, 0.06, 1)
        cx.fill()
        # ripple + sparkles on a hold checkpoint
        if since is not None and since < 0.9:
            u = since / 0.9
            big = 1.6 if i == 3 else 1.0
            cx.arc(x, cy, r + 70 * big * ease_out(u), 0, 2 * math.pi)
            cx.set_source_rgba(1, 0.9, 0.5, 0.75 * (1 - u))
            cx.set_line_width(6 * (1 - u) + 1)
            cx.stroke()
            n = 14 if i == 3 else 8
            for k in range(n):
                a = k / n * 2 * math.pi + i
                d = r + (40 + 90 * big) * ease_out(u)
                art.sparkle_star(cx, x + math.cos(a) * d, cy + math.sin(a) * d, 13 * (1 - u * 0.6), 1 - u)


def draw_lungs(cx, t):
    L = static()["lungs"]
    for i, (lx, ly) in enumerate(art.LUNG_POS):
        lit, since = cp_lit(t, i)
        breathe = 1 + 0.012 * math.sin(t * 1.6 + i * 1.3)
        sc = breathe
        if since is not None:
            sc *= 1 + 0.10 * back_out(min(1, since / 0.35)) * (1 - 0.6 * min(1, since / 0.9)) \
                if since < 0.9 else 1.04
        if lit:
            ha = 0.42 if since > 1.0 else 0.42 + 0.35 * (1 - since)
            g = cairo.RadialGradient(lx, ly - 20, 20, lx, ly - 20, 220)
            g.add_color_stop_rgba(0, 1, 0.85, 0.45, ha)
            g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
            cx.set_source(g)
            cx.arc(lx, ly - 20, 220, 0, 2 * math.pi)
            cx.fill()
        cx.save()
        cx.translate(lx, ly)
        cx.scale(sc / art.RS, sc / art.RS)
        cx.set_source_surface(L[i], -art.LUNG_ORIGIN[0], -art.LUNG_ORIGIN[1])
        cx.paint()
        cx.restore()
        if i == 1:   # animated wisp from the cigarette tip
            tx = lx + art.CIG_TIP[0] * art.LUNG_S * sc * 1.1
            ty = ly + art.CIG_TIP[1] * art.LUNG_S * sc
            for k in range(4):
                u = ((t * 0.45 + k / 4) % 1.0)
                wx = tx + 10 * math.sin(u * 5 + k) * u
                wy = ty - 6 - 70 * u
                cx.arc(wx, wy, 5 + 13 * u, 0, 2 * math.pi)
                cx.set_source_rgba(0.88, 0.88, 0.92, 0.38 * (1 - u) * min(1, u * 5))
                cx.fill()


def draw_exhale_cloud(cx, t, x, y, R):
    t0 = T_HOLD1 + 0.15
    if t < t0 or t > t0 + 2.2:
        return
    u = (t - t0) / 2.2
    for k, (dx, dy, r) in enumerate([(0, 0, 0.22), (0.22, -0.08, 0.28), (0.45, 0.02, 0.2)]):
        cxp = x + R * 0.55 + R * (0.4 + 1.6 * ease_out(u)) * (1 + dx)
        cyp = y + R * 0.35 + R * dy - 30 * u
        rr = R * r * (0.6 + 0.9 * ease_out(u))
        cx.arc(cxp, cyp, rr, 0, 2 * math.pi)
        cx.set_source_rgba(1, 1, 1, 0.8 * (1 - u) * min(1, u * 8))
        cx.fill()


def caption_cues():
    cues = []
    for key, (a, b), v0, groups in VOICE:
        off = v0 - a
        for j, (txt, ts) in enumerate(groups):
            t0 = ts + off
            t1 = (groups[j + 1][1] + off - 0.02) if j + 1 < len(groups) else (b + off - 0.05)
            cues.append({"text": txt, "t0": round(t0, 3), "t1": round(t1, 3)})
    # one caption on screen at a time: each one has faded out before the next appears
    for c, n in zip(cues, cues[1:]):
        c["t1"] = round(min(c["t1"], n["t0"] - C.OUT_T - 0.01), 3)
    return cues


def ui_alpha(t, t_in, t_out, d_in=0.25, d_out=0.5):
    if t < t_in:
        return 0.0
    a = min(1, (t - t_in) / d_in) if d_in > 0 else 1
    if t_out is not None:
        a = min(a, max(0, 1 - (t - t_out) / d_out))
    return a


def draw_frame(cx, t, cues):
    st = static()
    cx.set_source_surface(st["bg"], 0, 0)
    cx.paint()
    # slow-breathing soft light behind the track
    la = 0.10 + 0.04 * math.sin(t * 0.9)
    g = cairo.RadialGradient(art.TRACK_X, 900, 50, art.TRACK_X, 900, 900)
    g.add_color_stop_rgba(0, 1, 0.75, 0.35, la)
    g.add_color_stop_rgba(1, 1, 0.6, 0.2, 0)
    cx.set_source(g)
    cx.paint()
    st["parts"].draw(cx, t)
    draw_lungs(cx, t)
    ey = emoji_y(t)
    draw_track(cx, t, ey)
    e = emoji_state(t)
    ex = art.TRACK_X
    if e["kind"] == "hold" and e["strain"] > 0.72:
        k = (e["strain"] - 0.72) / 0.28
        ex += 1.6 * k * math.sin(t * 31)
    art.draw_emoji(cx, ex, ey, art.EMOJI_R, e)
    draw_exhale_cloud(cx, t, ex, ey, art.EMOJI_R)
    # title + safety note (opening)
    a = ui_alpha(t, 0.0, 9.4, 0.0, 0.5)
    if a > 0:
        paint_text(cx, st["title"], W / 2, 150, a)
    a = ui_alpha(t, 0.0, 13.5, 0.0, 0.6)
    if a > 0:
        surf, w, h, pad = st["note"]
        pw, ph = w - 2 * pad + 52, h - 2 * pad + 22
        rrect(cx, W / 2 - pw / 2, 238 - ph / 2, pw, ph, ph / 2)
        cx.set_source_rgba(0.1, 0.04, 0.02, 0.55 * a)
        cx.fill()
        paint_text(cx, st["note"], W / 2, 238, a)
    for cue in cues:
        C.draw_accent(cx, t, dict(cue, size=CAP_SIZE, pos=(W / 2, CAP_Y)))


# ------------------------------------------------------------------ render
def render_chunk(args):
    idx, f0, f1, path = args
    cues = caption_cues()
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
           "-pix_fmt", "yuv420p", "-profile:v", "high", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    for f in range(f0, f1):
        cx.save()
        draw_frame(cx, f / FPS, cues)
        cx.restore()
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return path


def render_video():
    os.makedirs(BUILD, exist_ok=True)
    n = int(round(DUR * FPS))
    k = os.cpu_count() or 4
    step = math.ceil(n / k)
    jobs = [(i, i * step, min(n, (i + 1) * step), os.path.join(BUILD, f"part{i}.mp4")) for i in range(k)]
    with Pool(k) as pool:
        parts = pool.map(render_chunk, jobs)
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(BUILD, "silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", os.path.join(BUILD, "mix.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print("->", out)


def still(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    draw_frame(cx, t, caption_cues())
    os.makedirs(BUILD, exist_ok=True)
    p = os.path.join(BUILD, f"still_{t:05.2f}.png")
    surf.write_to_png(p)
    print(p)


# ------------------------------------------------------------------ audio
SR = A.SR


def voice_clips():
    take = read_wav(take_path())
    take = resample_poly(take, 2, 1).astype(np.float32)       # 24k -> 48k
    clips = []
    for key, (a, b), v0, groups in VOICE:
        x = take[int(a * SR):int(b * SR)].copy()
        x = A.fade(x, 0.01, 0.06)
        clips.append((key, v0, x))
    return clips


def music(dur):
    """Warm, unobtrusive ambient bed in D major, 80 bpm: pads + soft plucked arpeggio."""
    beat = 0.75
    buf = np.zeros(int((dur + 4) * SR), np.float32)
    # Dmaj9 - Bm7 - Gmaj7 - A6sus  (each 2 bars of 4 beats = 6 s)
    chords = [[50, 57, 62, 64, 66, 69], [47, 54, 59, 62, 66, 69], [43, 50, 55, 59, 62, 66], [45, 52, 57, 62, 64, 66]]
    bar_len = 8 * beat
    t = 0.0
    k = 0
    end_t = T_HOLD1   # the progression resolves when the indicator reaches the bottom
    while t < end_t - 0.01:
        ch = chords[k % 4]
        d = min(bar_len, end_t - t)
        for m in ch[1:4]:
            A.add(buf, A.pad(m, d + 0.6, 0.22) * 0.20, t)
        A.add(buf, A.pad(ch[0] - 12, d + 0.6, 0.12) * 0.22, t)
        # arpeggio: sparse at first, a touch busier in the last third (gentle build)
        n8 = int(d / (beat / 2))
        for j in range(n8):
            tt = t + j * beat / 2
            dense = tt > 34
            if j % 2 and not dense and j % 4 != 3:
                continue
            m = ch[[2, 3, 4, 5, 4, 3, 2, 3][j % 8]] + 12
            A.add(buf, A.pluck(m, 0.9, 0.35, seed=j) * (0.10 if j % 2 == 0 else 0.07), tt)
        t += bar_len
        k += 1
    # resolution chord at the bottom
    for m in [50, 57, 62, 66, 69, 74]:
        A.add(buf, A.pad(m, 3.6, 0.25) * 0.18, end_t)
    for j, m in enumerate([74, 78, 81, 86]):
        A.add(buf, A.glock(m, 1.6) * 0.32, end_t + 0.05 + j * 0.09)
    buf = A.lp(buf, 6000).astype(np.float32)
    # stereo-ish width via short delay
    return buf[: int(dur * SR)]


def chime(m, amp=1.0):
    x = A.glock(m, 1.4) * 0.9
    x[: int(0.9 * SR)] += A.glock(m + 12, 0.9) * 0.25
    return x * amp


def soft_swoosh(d, f0, f1, amp):
    x = A.sweep(f0, f1, d) * 0.4 + A.bp(A.noise(d, 9), 600, 3000) * 0.15
    t = np.arange(len(x)) / SR
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return A.lp(x * env, 2500) * amp


def sfx_track(dur):
    buf = np.zeros(int((dur + 3) * SR), np.float32)
    A.add(buf, A.get_sfx("sparkle") * 0.18, 0.02)                       # interface shimmer at frame 1
    A.add(buf, soft_swoosh(1.4, 260, 620, 0.22), T_SWEEP0 - 0.1)        # breath-in sweep starts
    for i, h in enumerate(SWEEP_HITS):
        A.add(buf, A.woodblock(True) * 0.10, h)                         # light passes
    A.add(buf, soft_swoosh(1.0, 700, 300, 0.2), T_SWEEP1)               # rise back to the top
    A.add(buf, A.get_sfx("pop") * 0.30, T_HOLD0 - 0.2)                  # hold starts
    notes = [69, 71, 73, 76]
    for i, h in enumerate(HOLD_HITS):
        A.add(buf, chime(notes[i] + 12, 0.55 if i < 3 else 0.45), h)
        A.add(buf, A.get_sfx("sparkle") * (0.10 if i < 3 else 0.3), h + 0.02)
    A.add(buf, A.get_sfx("ding") * 0.22, T_HOLD1 + 0.02)               # small ending cue
    return buf[: int(dur * SR)]


def make_srt(cues):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out = []
    for i, c in enumerate(cues, 1):
        out.append(f"{i}\n{ts(c['t0'])} --> {ts(c['t1'] + 0.1)}\n{c['text']}\n")
    return "\n".join(out)


def make_audio():
    os.makedirs(BUILD, exist_ok=True)
    n = int(DUR * SR)
    vo = np.zeros(n, np.float32)
    for key, v0, x in voice_clips():
        A.add(vo, x, v0)
    vo = A.hp(vo, 80).astype(np.float32)
    mus = music(DUR)
    # duck the music under the narration
    env = np.abs(vo)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1 - 0.5 * np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    mus = mus * duck
    sfx = sfx_track(DUR)
    mix = vo * 1.0 + mus * 0.55 + sfx * 0.6
    # tiny fade at the very end so the loop point is clean
    mix[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))
    mix = np.stack([mix, mix], 1)
    raw = os.path.join(BUILD, "mix_raw.wav")
    import soundfile as sf
    sf.write(raw, mix, SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000",
                    os.path.join(BUILD, "mix.wav")], check=True)
    # stems for QA
    sf.write(os.path.join(BUILD, "stem_vo.wav"), vo, SR)
    sf.write(os.path.join(BUILD, "stem_music.wav"), mus * 0.55, SR)
    sf.write(os.path.join(BUILD, "stem_sfx.wav"), sfx * 0.6, SR)
    os.makedirs(OUTDIR, exist_ok=True)
    open(os.path.join(OUTDIR, NAME + ".srt"), "w").write(make_srt(caption_cues()))
    print("audio + srt done; hold hits:", [round(h, 2) for h in HOLD_HITS], "sweep hits:",
          [round(h, 2) for h in SWEEP_HITS])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "audio":
        make_audio()
    elif cmd == "video":
        render_video()
    elif cmd == "still":
        for a in sys.argv[2:]:
            still(float(a))

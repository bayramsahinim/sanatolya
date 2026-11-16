"""Assemble the Kohnstamm doorway short: animation, captions, soundtrack, SRT.

python -m episodes.kohnstamm_short.episode audio      # soundtrack + SRT
python -m episodes.kohnstamm_short.episode still 12.5 # one frame -> scratch png
python -m episodes.kohnstamm_short.episode video      # final mp4
"""
import math
import multiprocessing as mp
import os
import subprocess
import sys

import cairo
import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode.core import OUTLINE, back_out, ease_io, ease_out, kf, lerp, noise1, prog, smooth
from . import scene as S
from .timing import ROOT, caption_groups, clip, schedule, srt, word_time

NAME = "JUST_NEEDY_KOHNSTAMM_ARM_CHALLENGE_ENGLISH"
OUT = os.path.join(ROOT, "output")
BUILD = os.path.join(ROOT, "build", "kohnstamm")
SCHED = schedule()
CAPS = caption_groups(SCHED)
DUR = round(SCHED[-1][2] + 0.38, 2)
NFRAMES = int(round(DUR * S.FPS))

T_KOHN = word_time(SCHED, 5, "Kohnstamm")
T_VARY = word_time(SCHED, 16, "vary")
T_LITTLE = word_time(SCHED, 16, "little")
T_NOTHING = word_time(SCHED, 16, "nothing")

# key times
STEP_IN = (5.85, 6.95)
PRESS = (8.0, 9.3)
RELEASE = 40.1
STEP_OUT = (41.15, 42.2)
FLOAT = (43.45, 47.9)
OUTRO = (48.2, 48.6)


# ------------------------------------------------------------------ hero animation
def hero_pose(t):
    """Main shot: pose + flags for the blue-hoodie hero."""
    # depth: forward -> doorway -> forward
    if t < STEP_IN[1] or t >= STEP_OUT[0]:
        if t < STEP_IN[1]:
            u = ease_io(prog(t, *STEP_IN))
        else:
            u = 1 - ease_io(prog(t, *STEP_OUT))
    else:
        u = 1.0
    feet = lerp(S.FEET_OUT, S.FEET_IN, u)
    s = lerp(S.S_OUT, S.S_IN, u)
    walking = STEP_IN[0] < t < STEP_IN[1] or STEP_OUT[0] < t < STEP_OUT[1]
    bob = 0.0
    hip_a = hip_b = 3.0
    knee_a = knee_b = 0.0
    if walking:
        ph = (t - (STEP_IN[0] if t < 20 else STEP_OUT[0])) * 2 * math.pi * 1.9
        bob = -abs(math.sin(ph)) * 7
        knee_a = 18 * max(0, math.sin(ph))
        knee_b = 18 * max(0, -math.sin(ph))

    kw = dict(eyes="dot", brows="neutral", mouth="smile", mouth_open=1.0)
    arm_a = arm_b = 5.0
    elb = 4.0
    if t < 5.0:
        # hook: arms drift up by themselves, then drop
        up = kf(t, [(0.45, 5.0), (3.3, 72.0), (4.25, 72.0), (4.85, 5.0)], ease_io)
        lag = kf(t - 0.18, [(0.45, 5.0), (3.3, 72.0), (4.25, 72.0), (4.85, 5.0)], ease_io)
        wob = noise1(t * 1.3, 3) * 1.6 if 0.5 < t < 4.3 else 0
        arm_a, arm_b = lag + wob, up - wob
        elb = 4 + 6 * prog(t, 0.45, 3.3) * (1 - prog(t, 4.25, 4.85))
        if 0.9 < t < 4.3:
            kw.update(eyes="dotwide", brows="up", mouth="o", mouth_open=0.9 + 0.2 * smooth(prog(t, 0.9, 1.4)))
        elif t <= 0.9:
            kw.update(mouth="flat")
        kw["look"] = (noise1(t * 0.8, 9) * 0.6, -0.2) if 1.2 < t < 4.2 else (0, 0)
    elif t < PRESS[0]:
        if walking:
            sw = math.sin((t - STEP_IN[0]) * 2 * math.pi * 1.9) * 4
            arm_a, arm_b = 6 + sw, 6 - sw
        if t > 7.4:
            kw.update(mouth="flat")
    elif t < RELEASE:
        a = ease_io(prog(t, *PRESS))
        arm_a = arm_b = lerp(5.0, S.A_PRESS, a)
        elb = lerp(4.0, 0.0, a)
        if t > PRESS[1]:
            # effort: tiny tension tremor + breathing, hands stay on the frame
            trem = noise1(t * 7, 4) * 0.25
            arm_a, arm_b = S.A_PRESS + trem, S.A_PRESS - trem
            bob = math.sin(t * 2.2) * 1.2
        if t < 10.0:
            kw.update(mouth="flat")
        elif t < 20.0:
            kw.update(brows="flat", mouth="flat")
        else:
            kw.update(eyes="dotfocus", brows="angry", mouth="flat")
        if t > 36.6:
            kw.update(eyes="dotfocus", brows="angry", mouth="wavy")
    elif t < FLOAT[0]:
        a = ease_out(prog(t, RELEASE, RELEASE + 0.45))
        arm_a = arm_b = lerp(S.A_PRESS, 4.0, a)
        elb = lerp(0.0, 6.0, a)
        if walking:
            sw = math.sin((t - STEP_OUT[0]) * 2 * math.pi * 1.9) * 3
            arm_a, arm_b = 5 + sw, 5 - sw
        kw.update(brows="up", mouth="o", mouth_open=0.6, look=(0, -0.3))
        if t > STEP_OUT[1]:
            # relaxed, letting the arms hang loose
            kw.update(brows="neutral", mouth="flat", eyes="dot", look=(0, 0.4))
            sway = math.sin((t - STEP_OUT[1]) * 2.6) * 1.2
            arm_a, arm_b = 4 + sway, 4 - sway
    else:
        # the reveal: slow, smooth, unforced float
        f0, f1 = FLOAT
        ua = smooth(prog(t, f0, f1)) ** 1.15
        ub = smooth(prog(t, f0 + 0.18, f1 + 0.1)) ** 1.15
        arm_a = 4 + 59 * ua + noise1(t * 0.9, 21) * 1.4 * ua
        arm_b = 4 + 59 * ub + noise1(t * 0.9, 22) * 1.4 * ub
        elb = 6 + 7 * ua
        bob = math.sin(t * 1.8) * 1.5 * ua
        if t < 44.25:
            kw.update(mouth="flat", look=(0, 0.4))
        elif t < 47.3:
            kw.update(eyes="dotwide", brows="up", mouth="o", mouth_open=1.1,
                      look=((-0.7 if t < 45.6 else 0.7) * smooth(prog(t, 44.3, 44.7)), 0.2))
        else:
            kw.update(eyes="dotwide", brows="up", mouth="grin", mouth_open=0.7)
    p = S.pose(1, S.DOOR_CX, feet, s, t, bob=bob, hip_a=hip_a, hip_b=hip_b, knee_a=knee_a, knee_b=knee_b,
               arm_a=arm_a, arm_b=arm_b, elb_a=elb, elb_b=elb, **kw)
    return p, s


def camera(t):
    z = 1.0 + 0.1 * ease_io(prog(t, 44.0, 48.2))
    fx, fy = 540, lerp(960, 1010, ease_io(prog(t, 44.0, 48.2)))
    return z, fx, fy


def apply_cam(cx, t):
    z, fx, fy = camera(t)
    cx.translate(S.W / 2, S.H / 2)
    cx.scale(z, z)
    cx.translate(-fx, -fy)


# ------------------------------------------------------------------ frames
def draw_main(cx, t):
    bg, pad = S.background()
    cx.save()
    apply_cam(cx, t)
    cx.set_source_surface(bg, -pad, -pad)
    cx.paint()
    S.note_card(cx, t, 14.6, 24.3, T_KOHN)
    # floor shadow
    p, s = hero_pose(t)
    from cinecode.core import ellipse, src
    ellipse(cx, p.x, p.y + 4, 74 * s / 2.3, 13 * s / 2.3)
    src(cx, (0, 0, 0, 0.25))
    cx.fill()
    J = S.HERO.draw(cx, p)
    # explanatory overlays (all secondary)
    S.press_arrows(cx, t, [J["hand_a"], J["hand_b"]],
                   smooth(prog(t, 8.6, 9.0)) * (1 - smooth(prog(t, 10.8, 11.3))))
    ma = smooth(prog(t, 28.0, 28.8)) * (1 - smooth(prog(t, RELEASE, RELEASE + 0.4)))
    ma = max(ma, 0.5 * smooth(prog(t, 44.0, 45.0)))
    S.muscles(cx, J, s, ma, t)
    S.muscle_label(cx, t, 28.0, 35.4, J)
    # (no extra motion marks: the float itself must read as the payoff)
    cx.restore()
    # screen-space elements that stay put when the camera pushes in
    cx.save()
    apply_cam(cx, t) if t < 44.0 else None
    S.question_marks(cx, t, 0.95, 4.3)
    S.countdown(cx, t)
    S.let_go_banner(cx, t, 40.05, 43.0)
    cx.restore()
    if t >= 44.0:
        S.question_marks(cx, t, 44.9, 48.6, y=250)
    S.safety_note(cx, t, 10.2, 40.0)


def draw_outro(cx, t):
    bg, pad = S.background()
    cx.set_source_surface(bg, -pad, -pad)
    cx.paint()
    feet, s = S.FEET_OUT, 1.55
    from cinecode.core import ellipse, src
    xs = {"gray": 205, "hero": 540, "tan": 875}
    slide = ease_out(prog(t, OUTRO[0], OUTRO[1] + 0.25))
    for k, x in xs.items():
        ellipse(cx, x, feet + 4, 74 * s / 2.3, 13 * s / 2.3)
        src(cx, (0, 0, 0, 0.22))
        cx.fill()
    # small lift (gray)
    g = smooth(prog(t, 49.2, 51.6))
    ga = 4 + 24 * g + noise1(t, 31) * g
    gx = lerp(-140, xs["gray"], slide)
    pg = S.pose(5, gx, feet, s, t, arm_a=ga, arm_b=ga - 1.5, elb_a=6, elb_b=6, eyes="dot", brows="up",
                mouth="o" if g > 0.2 else "flat", mouth_open=0.7)
    # no effect (tan): relaxed shrug, still smiling
    sh = math.sin(math.pi * prog(t, 49.7, 50.6))
    tx = lerp(S.W + 140, xs["tan"], slide)
    pt = S.pose(6, tx, feet, s, t, arm_a=5 + 10 * sh, arm_b=5 + 10 * sh, elb_a=4 + 70 * sh, elb_b=4 + 70 * sh,
                bob=-6 * sh, eyes="dot", brows="worried" if sh > 0.2 else "neutral", mouth="smile")
    # hero keeps floating
    hb = 63 + math.sin(t * 1.6) * 1.5
    ph = S.pose(1, xs["hero"], feet, s, t, arm_a=hb, arm_b=hb + 0.8, elb_a=13, elb_b=13, eyes="dotwide",
                brows="up", mouth="grin", mouth_open=0.7)
    S.GRAY.draw(cx, pg)
    S.TAN.draw(cx, pt)
    S.HERO.draw(cx, ph)
    ly = feet - 330 * s - 70
    S.outcome_label(cx, xs["hero"], ly - 30, "BIG LIFT", prog(t, T_VARY, T_VARY + 0.3), (1, 0.84, 0.45, 1))
    S.outcome_label(cx, xs["gray"], ly + 40, "A LITTLE", prog(t, T_LITTLE, T_LITTLE + 0.3))
    S.outcome_label(cx, xs["tan"], ly + 40, "NOTHING", prog(t, T_NOTHING, T_NOTHING + 0.3))


def draw_captions(cx, t):
    for txt, a, b in CAPS:
        if a - 0.001 <= t < b:
            al = min(1.0, (t - a) / 0.08 + 0.35)
            S.outlined_text(cx, txt, S.W / 2, S.CAP_Y + 28, 80, sw=15, alpha=min(al, 1.0))
            break


def render_frame(i):
    t = i / S.FPS
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S.W, S.H)
    cx = cairo.Context(surf)
    if t < OUTRO[0]:
        draw_main(cx, t)
    elif t >= OUTRO[1]:
        draw_outro(cx, t)
    else:
        draw_main(cx, t)
        a = smooth(prog(t, *OUTRO))
        cx.push_group()
        draw_outro(cx, t)
        cx.pop_group_to_source()
        cx.paint_with_alpha(a)
    S.vignette(cx)
    draw_captions(cx, t)
    surf.flush()
    return bytes(surf.get_data())


# ------------------------------------------------------------------ audio
def build_audio():
    sr = A.SR
    n = int((DUR + 0.5) * sr)
    narr = np.zeros(n)
    for i, st, en, text, words in SCHED:
        x = A.resample(clip(i).astype(np.float64), 24000, sr)
        A.add(narr, x, st)
    mus = np.zeros(n)
    sfx = np.zeros(n)
    # --- opening: soft mysterious bed + accent as the arms drift up
    A.add(mus, A.pad(45, 10.6, 0.12) * 0.55, 0.0)
    A.add(mus, A.pad(52, 10.6, 0.1) * 0.35, 0.0)
    swell = A.lp(A.noise(1.4, 3), 1800) * np.linspace(0, 1, int(1.4 * sr)) ** 2 * 0.18
    A.add(sfx, A.fade(swell, 0.01, 0.15), 0.0)
    for k, m in enumerate([81, 76, 84, 79]):
        A.add(sfx, A.glock(m, 1.6) * 0.32, 0.55 + k * 0.42)
    # footsteps
    for k, tt in enumerate([5.95, 6.5, 41.25, 41.8]):
        A.add(sfx, A.sfx_step(k) * 0.35, tt)
    # soft "contact" taps when the hands meet the frame
    A.add(sfx, A.sfx_thud(160, 0.18) * 0.18, PRESS[1] - 0.05)
    # --- countdown: very quiet evolving chords, no ticking
    chords = [(45, 52, 57, 60), (41, 48, 57, 60), (48, 55, 60, 64), (43, 50, 59, 62)]
    for k in range(8):
        t0 = 10.0 + k * 3.75
        br = 0.08 + 0.3 * k / 7
        for j, m in enumerate(chords[k % 4]):
            A.add(mus, A.pad(m, 4.3, br) * (0.42 if j == 0 else 0.22), t0)
        for b in range(0, 4, 2):
            A.add(mus, A.pluck(chords[k % 4][2] + 12, 1.2, 0.25, seed=k + b) * 0.07, t0 + b * 0.94)
    # --- release + reveal
    A.add(sfx, A.sfx_whoosh(0.5, 900, 300) * 0.16, 40.05)
    cue_t = FLOAT[0] + 0.15
    A.add(sfx, A.sfx_sparkle() * 0.22, cue_t)
    A.add(mus, A.pad(69, 4.6, 0.25) * 0.35, cue_t)
    A.add(mus, A.pad(76, 4.6, 0.25) * 0.22, cue_t + 0.3)
    A.add(mus, A.pad(57, 4.6, 0.15) * 0.4, cue_t)
    # --- resolution
    for m, g in ((48, 0.45), (55, 0.25), (64, 0.22)):
        A.add(mus, A.pad(m, DUR - OUTRO[0] + 0.3, 0.2) * g, OUTRO[0])
    for k, m in enumerate([72, 76, 79]):
        A.add(sfx, A.glock(m, 1.4) * 0.22, OUTRO[0] + 0.1 + k * 0.16)
    # room tone
    room = A.amb_loop("room")
    amb = np.tile(room, n // len(room) + 1)[:n] * 0.5
    # duck music under the voice
    env = A.envelope_follow(narr, 0.03, 0.4)
    env = env / (env.max() + 1e-9)
    mus *= 1 - 0.55 * np.clip(env * 3, 0, 1)
    fade_out = np.ones(n)
    k0 = int((DUR - 0.6) * sr)
    fade_out[k0:] = np.linspace(1, 0, n - k0) ** 2
    mix = narr * 1.0 + mus * 0.16 + sfx * 0.55 + amb * 0.25
    mix[:int(DUR * sr)] *= 1
    mix *= fade_out
    mix = mix[:int(DUR * sr)]
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    os.makedirs(BUILD, exist_ok=True)
    path = os.path.join(BUILD, "mix.wav")
    sf.write(path, mix.astype(np.float32), sr)
    return path


# ------------------------------------------------------------------ outputs
def make_srt():
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, NAME + ".srt")
    n = srt(SCHED, p)
    print("srt cues:", n, "->", p)


def render_video(draft=False):
    os.makedirs(OUT, exist_ok=True)
    wav = build_audio()
    out = os.path.join(OUT, NAME + ("_draft" if draft else "") + ".mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{S.W}x{S.H}",
           "-r", str(S.FPS), "-i", "-", "-i", wav,
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
           "-c:v", "libx264", "-preset", "veryfast" if draft else "slow", "-crf", "26" if draft else "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.Pool(os.cpu_count()) as pool:
        for k, fr in enumerate(pool.imap(render_frame, range(NFRAMES), chunksize=4)):
            ff.stdin.write(fr)
            if k % 150 == 0:
                print(f"  frame {k}/{NFRAMES}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("video ->", out, f"({DUR:.2f}s, {NFRAMES} frames)")


def still(t, path):
    surf = cairo.ImageSurface.create_for_data(bytearray(render_frame(int(round(t * S.FPS)))),
                                              cairo.FORMAT_ARGB32, S.W, S.H)
    surf.write_to_png(path)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "audio":
        print(build_audio())
        make_srt()
    elif cmd == "still":
        out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(BUILD, f"still_{sys.argv[2]}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        still(float(sys.argv[2]), out)
        print(out)
    elif cmd == "video":
        make_srt()
        render_video(draft="--draft" in sys.argv)

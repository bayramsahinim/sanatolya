"""Day 1 (remastered) - soundtrack (narration + cinematic sound design + drone) and SRT.

usage: python -m episodes.zombie_day_1.mix
"""
import json
import os

import numpy as np
import soundfile as sf

from cinecode import align, tts
from cinecode.audio import (SR, add, bp, envelope_follow, exp_env, fade, hp, lp, noise, norm,
                            resample, sfx_step, sfx_thud, t_arr)
from .make_voice import take_path
from .script import LINES
from .shots import DURATION

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "zombie_day_1")

# where each narration line starts on the picture timeline (s)
LINE_T = [0.35, 5.1, 9.7, 10.9, 14.5, 16.3, 20.3, 22.6, 25.6, 29.0, 30.9, 33.3, 41.7, 44.5,
          46.0, 48.6, 52.0, 54.3, 55.9, 58.1, 59.6, 62.1]
STRIKE = 63.6
CUT = 63.68
rng = np.random.default_rng(3)


# ---------------------------------------------------------------- sound design
def wind(d, seed=1, amt=1.0):
    t = t_arr(d)
    n = noise(d, seed)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t + 1) * np.sin(2 * np.pi * 0.047 * t)
    x = bp(n, 180, 900) * gust + bp(noise(d, seed + 1), 1200, 3200) * 0.18 * gust ** 2
    return norm(x, 0.5) * amt


def siren(d, f0=720, seed=0):
    """Distant wailing emergency siren: slow sweep, low-passed, with a slow echo."""
    t = t_arr(d)
    f = f0 + 260 * np.sin(2 * np.pi * 0.16 * t + seed)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    x = lp(x, 1400)
    e = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.5)
    x = x * e
    echo = np.zeros_like(x)
    k = int(0.31 * SR)
    echo[k:] = x[:-k] * 0.35
    return norm(x + echo, 0.5)


def groan(d=1.6, f0=95, seed=0):
    """Faint infected groan: wobbling glottal buzz through vowel-ish formants."""
    t = t_arr(d)
    r = np.random.default_rng(seed)
    f = f0 * (1 + 0.08 * np.sin(2 * np.pi * 3.1 * t) + 0.15 * np.sin(2 * np.pi * 0.6 * t + r.random()))
    f *= 1 - 0.12 * t / d
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = sum(np.sin(k * ph) / k for k in range(1, 18))
    buzz += lp(noise(d, seed + 9), 1500) * 0.6
    x = bp(buzz, 300, 900) + 0.6 * bp(buzz, 900, 1400) + 0.4 * lp(buzz, 200)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return norm(x * e, 0.55)


def footsteps_run(d, rate=3.2, seed=0):
    out = np.zeros(int(d * SR))
    k = 0
    tt = 0.0
    while tt < d - 0.15:
        add(out, sfx_step(seed + k, heavy=False) * (0.8 + 0.2 * rng.random()), tt)
        tt += 1 / rate + rng.uniform(-0.02, 0.02)
        k += 1
    return lp(out, 2500)


def shuffle_steps(d, seed=0):
    """Irregular dragging footsteps."""
    out = np.zeros(int(d * SR))
    tt = 0.1
    k = 0
    while tt < d - 0.4:
        st = sfx_step(seed + k, heavy=True) * 0.8
        add(out, st, tt)
        drag = lp(noise(0.35, seed + 50 + k), 700) * exp_env(int(0.35 * SR), 0.12) * 0.25
        add(out, drag, tt + 0.05)
        tt += rng.uniform(0.55, 0.95)
        k += 1
    return out


def lock_clunk():
    d = 0.35
    x = hp(noise(0.03, 70), 1500) * exp_env(int(0.03 * SR), 0.006)
    out = np.zeros(int(d * SR))
    add(out, x * 0.8, 0)
    add(out, sfx_thud(180, 0.15) * 0.6, 0.06)
    m = hp(noise(0.05, 71), 2500) * exp_env(int(0.05 * SR), 0.01)
    add(out, m * 0.7, 0.09)
    return norm(out, 0.7)


def latch_click():
    x = hp(noise(0.04, 72), 2000) * exp_env(int(0.04 * SR), 0.005)
    return norm(x, 0.5)


def power_down(d=1.3):
    """Mains hum + fridge-type whine collapsing, relay clicks, then nothing."""
    t = t_arr(d)
    f = 60 * (1 - 0.6 * np.clip((t - 0.9) / 0.4, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = np.sin(ph) * 0.6 + np.sin(2 * ph) * 0.4 + np.sin(3 * ph) * 0.2
    flick = np.ones_like(t)
    for a, b in [(0.15, 0.24), (0.33, 0.42), (0.51, 0.6), (0.69, 0.78), (0.87, 1.3)]:
        flick[(t > a) & (t < b)] = 0.1
    hum *= flick * np.clip(1 - (t - 0.95) / 0.3, 0, 1)
    out = hum * 0.5
    for a in (0.15, 0.33, 0.51, 0.69, 0.87):
        add(out, latch_click() * 0.6, a)
    whine = np.sin(2 * np.pi * np.cumsum(1800 * (1 - 0.7 * t / d)) / SR) * 0.04 * np.clip(1 - t / 1.1, 0, 1)
    return out + whine


def faucet_sputter():
    d = 1.8
    out = np.zeros(int(d * SR))
    # lever squeak/click
    add(out, latch_click() * 0.8, 0.25)
    # short sputter of air + water then dry
    sp = bp(noise(0.45, 80), 600, 5000)
    env = np.abs(np.sin(np.linspace(0, 18, len(sp)))) * np.exp(-np.linspace(0, 4, len(sp)))
    add(out, sp * env * 0.6, 0.6)
    # two drips
    for tt in (1.1, 1.65):
        dd = 0.08
        tt_ = t_arr(dd)
        dr = np.sin(2 * np.pi * (900 + 1500 * tt_ / dd) * tt_) * exp_env(len(tt_), 0.015)
        add(out, dr * 0.35, tt)
    return out


def rooster_crow():
    """Synthesised rooster crow: four strained harmonic syllables with a long last one."""
    sylls = [(0.0, 0.16, 650, 820), (0.2, 0.18, 780, 900), (0.42, 0.22, 860, 760), (0.7, 0.75, 900, 560)]
    d = 1.6
    out = np.zeros(int(d * SR))
    for st, du, fa, fb in sylls:
        t = t_arr(du)
        f = fa + (fb - fa) * (t / du) + 25 * np.sin(2 * np.pi * 28 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum((0.9 ** k) * np.sin(k * ph) for k in range(1, 14))
        x += bp(noise(du, int(fa)), 1500, 5000) * 0.6   # raspy edge
        x = bp(x, 700, 4200)
        e = np.minimum(1, t / 0.02) * np.minimum(1, (du - t) / 0.05)
        add(out, x * e, st)
    # yard reflection
    echo = np.zeros_like(out)
    k = int(0.18 * SR)
    echo[k:] = lp(out[:-k], 2500) * 0.25
    return norm(out + echo, 0.8)


def glass_hit():
    d = 1.2
    out = np.zeros(int(d * SR))
    add(out, sfx_thud(85, 0.45) * 1.0, 0)
    t = t_arr(0.9)
    rattle = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dd) for f, dd in
                 [(1730, 9), (2470, 12), (3320, 15), (4410, 18)])
    add(out, rattle * 0.12, 0.005)
    add(out, hp(noise(0.06, 90), 1800) * exp_env(int(0.06 * SR), 0.01) * 0.5, 0)
    return norm(out, 0.95)


def impact_boom(d=3.0):
    t = t_arr(d)
    f = 55 * np.exp(-t * 0.6) + 28
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(len(t), 0.9)
    x += lp(noise(d, 91), 160) * exp_env(len(t), 0.5) * 0.8
    return norm(x, 0.9)


def drone(d, root=43.65, seed=0):
    """Low cinematic drone (F1 + dark cluster), slow beating, no melody."""
    t = t_arr(d)
    x = np.zeros_like(t)
    for k, (mul, a) in enumerate([(1, 1.0), (1.5, 0.5), (2.0, 0.45), (2.38, 0.22), (3.0, 0.18)]):
        f = root * mul
        x += a * np.sin(2 * np.pi * f * t + k) * (0.75 + 0.25 * np.sin(2 * np.pi * (0.07 + 0.03 * k) * t))
        x += a * 0.6 * np.sin(2 * np.pi * f * 1.004 * t)
    x += lp(noise(d, seed + 60), 300) * 0.25
    return norm(lp(x, 900), 0.5)


def room_tone(d):
    return norm(lp(noise(d, 95), 220) + bp(noise(d, 96), 300, 800) * 0.2, 0.5)


def env_line(n, keys):
    """Piecewise-linear gain automation: keys [(t, gain), ...]."""
    tt = np.arange(n) / SR
    return np.interp(tt, [k[0] for k in keys], [k[1] for k in keys])


# ---------------------------------------------------------------- narration
def narration(n):
    take = tts.read_wav(take_path())
    segs = align.align(take, LINES)
    voice = np.zeros(n)
    timings = []
    for (s, e), t0, txt in zip(segs, LINE_T, LINES):
        a = int(max(0, s - 0.03) * tts.SR)
        b = int(min(len(take) / tts.SR, e + 0.08) * tts.SR)
        clip = take[a:b].astype(np.float64)
        clip = fade(resample(clip, tts.SR, SR), 0.01, 0.05)
        add(voice, clip, t0)
        timings.append((t0, t0 + len(clip) / SR, txt))
    # gentle voice polish: high-pass rumble, light presence lift
    voice = hp(voice, 80) + 0.12 * bp(voice, 2500, 5000)
    return voice, timings


def srt(timings, path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out = []
    i = 1
    for j, (a, b, txt) in enumerate(timings):
        nxt = timings[j + 1][0] if j + 1 < len(timings) else b + 1.0
        # split the long science line into two readable cues at the colon
        if len(txt) > 84 and ": " in txt:
            head, tail = txt.split(": ", 1)
            sub = tail.split(". ")
            parts = [head + ":", sub[0] + ".", sub[1]] if len(sub) == 2 else [head + ":", tail]
            lens = np.array([len(p) for p in parts], float)
            cuts = a + (b - a) * np.concatenate([[0], np.cumsum(lens) / lens.sum()])
            for k, p in enumerate(parts):
                out.append(f"{i}\n{ts(cuts[k])} --> {ts(cuts[k + 1] - 0.02)}\n{p}\n")
                i += 1
            continue
        out.append(f"{i}\n{ts(a)} --> {ts(min(b + 0.25, nxt - 0.05))}\n{txt}\n")
        i += 1
    open(path, "w").write("\n".join(out))


def main():
    os.makedirs(BUILD, exist_ok=True)
    n = int(DURATION * SR)
    voice, timings = narration(n)

    fx = np.zeros(n)
    # exterior wind bed: loud outside shots, muffled through walls inside
    w = wind(DURATION, 1)
    outside = env_line(n, [(0, 0.45), (5.0, 0.45), (5.1, 1.0), (12.9, 1.0), (13.0, 0.35), (23.3, 0.35), (23.4, 0.9),
                           (25.3, 0.9), (25.4, 0.3), (33.2, 0.3), (33.3, 0.8), (34.6, 0.8), (34.8, 0.25),
                           (48.4, 0.25), (48.5, 0.9), (51.8, 0.8), (51.9, 0.9), (56.7, 0.9), (56.8, 1.0),
                           (57.9, 1.0), (58.0, 0.3), (CUT, 0.3), (CUT + 0.01, 0.0), (DURATION, 0.0)])
    inside_lp = lp(w, 450)
    is_out = (outside > 0.6).astype(float)
    is_out = np.convolve(is_out, np.ones(2400) / 2400, mode="same")
    fx += (w * is_out + inside_lp * (1 - is_out)) * outside * 0.22
    # room tone indoors
    rt = room_tone(DURATION)
    fx += rt * (1 - is_out) * 0.05 * env_line(n, [(0, 1), (CUT, 1), (CUT + 0.01, 0), (DURATION, 0)])

    # distant sirens through the opening and the outbreak montage
    add(fx, siren(11.0, 720, 0) * 0.07, 0.0)
    add(fx, siren(8.0, 640, 2) * 0.05, 6.0)
    add(fx, siren(7.0, 800, 1) * 0.03, 25.0)        # far away while he thinks he's safe
    # running footsteps (runner)
    add(fx, footsteps_run(2.4, 3.0, 5) * 0.12, 1.7)
    add(fx, footsteps_run(1.3, 3.3, 9) * 0.3, 9.6)
    # faint groans - sparse, never constant
    for tt, f0, g in [(2.4, 92, 0.05), (11.3, 88, 0.12), (17.9, 96, 0.05), (52.4, 84, 0.06),
                      (54.6, 90, 0.1), (56.0, 98, 0.08), (57.0, 80, 0.12)]:
        add(fx, groan(1.6, f0, int(tt * 10)) * g, tt)
    # shuffling steps
    add(fx, shuffle_steps(2.0, 1) * 0.12, 10.9)
    add(fx, shuffle_steps(1.2, 2) * 0.2, 56.8)
    add(fx, shuffle_steps(5.0, 3) * 0.05, 58.0)
    # gate creak in the wind
    t = t_arr(0.8)
    creak = bp(np.sin(2 * np.pi * np.cumsum(260 + 80 * np.sin(2 * np.pi * 1.3 * t)) / SR) * (1 + 0.5 * np.sign(np.sin(2 * np.pi * 37 * t))), 300, 2400)
    add(fx, norm(creak * np.sin(np.pi * t / 0.8), 0.5) * 0.12, 7.6)
    add(fx, norm(creak * np.sin(np.pi * t / 0.8), 0.5) * 0.09, 8.7)
    # car hazard ticks
    for k in range(7):
        add(fx, latch_click() * 0.12, 5.15 + k * 0.3125)
    # curtains swish
    add(fx, norm(bp(noise(0.9, 30), 800, 5000) * np.sin(np.pi * t_arr(0.9) / 0.9), 0.4) * 0.15, 13.25)
    # floorboard creak + nervous breath near the door
    add(fx, norm(bp(noise(0.5, 31), 200, 1200) * np.sin(np.pi * t_arr(0.5) / 0.5), 0.4) * 0.08, 14.9)
    add(fx, norm(bp(noise(0.7, 32), 400, 2200) * np.sin(np.pi * t_arr(0.7) / 0.7) ** 2, 0.4) * 0.05, 16.0)
    # deadbolt
    add(fx, lock_clunk() * 0.55, 21.05)
    add(fx, latch_click() * 0.15, 20.45)
    # pantry/wood creak, well shot wind
    add(fx, norm(bp(noise(0.4, 33), 150, 900) * np.sin(np.pi * t_arr(0.4) / 0.4), 0.4) * 0.05, 22.6)
    # lamp hum while on, then power down
    hum_t = t_arr(4.0)
    hum = (np.sin(2 * np.pi * 60 * hum_t) * 0.5 + np.sin(2 * np.pi * 120 * hum_t) * 0.3) * 0.02
    add(fx, hum * np.minimum(1, hum_t / 0.5), 25.4)
    add(fx, power_down() * 0.35, 28.9)
    add(fx, faucet_sputter() * 0.5, 30.8)
    # science graphic: soft UI ticks as nodes light, low tone on power-off
    for tt in (34.7 + 0.4, 34.7 + 0.9, 34.7 + 1.4):
        tk = np.sin(2 * np.pi * 1500 * t_arr(0.06)) * exp_env(int(0.06 * SR), 0.012)
        add(fx, tk * 0.05, tt)
    add(fx, power_down(0.9)[: int(0.9 * SR)] * 0.15, 37.1)
    add(fx, sfx_thud(48, 0.8) * 0.18, 37.1)
    # sudden silence + rooster
    add(fx, rooster_crow() * 0.42, 50.3)
    # heartbeat-like low pulses in the last scene
    for k, tt in enumerate(np.arange(58.2, 63.2, 0.82)):
        add(fx, sfx_thud(52, 0.3) * 0.12 * (0.6 + 0.08 * k), tt)
    add(fx, lp(noise(0.6, 40), 900) * np.sin(np.pi * t_arr(0.6) / 0.6) * 0.06, 61.0)  # palm on glass squeak/press
    add(fx, glass_hit() * 0.8, STRIKE)
    add(fx, impact_boom() * 0.55, CUT + 0.45)

    # music: low drone, enters after the hook, drops out for silence before the rooster,
    # comes back as the infected react and swells to the hit; total silence after the cut.
    dr = drone(DURATION, 43.65, 1)
    dr2 = drone(DURATION, 41.2, 2)
    mus_gain = env_line(n, [(0, 0.0), (1.0, 0.18), (12.0, 0.25), (24.0, 0.18), (28.8, 0.22), (29.6, 0.3),
                            (41.0, 0.3), (45.5, 0.15), (47.0, 0.0), (51.4, 0.0), (52.6, 0.35), (58.0, 0.5),
                            (63.0, 0.75), (CUT - 0.02, 0.8), (CUT, 0.0), (DURATION, 0.0)])
    mus = dr * mus_gain + dr2 * np.clip(mus_gain - 0.3, 0, 1) * 1.2
    # automatic ducking under narration
    ve = envelope_follow(voice, 0.03, 0.45)
    duck = 1 - 0.55 * np.clip(ve / 0.08, 0, 1)
    mus *= duck
    fx_duck = 1 - 0.35 * np.clip(ve / 0.08, 0, 1)
    fx *= fx_duck

    mixdown = voice * 1.0 + fx + mus * 0.6
    mixdown = hp(mixdown, 25)
    # final silence after the end card fades
    mixdown *= env_line(n, [(0, 1), (DURATION - 0.6, 1), (DURATION, 0)])
    peak = np.max(np.abs(mixdown))
    mixdown = mixdown / peak * 0.89
    stereo = np.stack([mixdown, mixdown], axis=1)
    sf.write(os.path.join(BUILD, "mix.wav"), stereo, SR, subtype="PCM_16")
    srt(timings, os.path.join(BUILD, "day1.srt"))
    json.dump(timings, open(os.path.join(BUILD, "timings.json"), "w"), indent=1)
    print("voice peak", np.max(np.abs(voice)), "mix normalised from", peak)


if __name__ == "__main__":
    main()

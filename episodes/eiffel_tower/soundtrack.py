"""Soundtrack: original procedural underscore scored to the cut, sound design, ambiences, ducked mix.

usage: python -m episodes.eiffel_tower.soundtrack   -> build/mix.wav
"""
import json
import math
import os

import numpy as np
import soundfile as sf

from cinecode.audio import (SR, add, bp, env_adsr, exp_env, fade, hp, lp, midi_f, noise, norm, pad, pluck,
                            resample, sfx_step, sfx_thud, sfx_whoosh, t_arr, envelope_follow, _babble, glock)
from episodes.eiffel_tower.timeline import DURATION

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NARR = os.path.join(ROOT, "assets", "audio", "tts_eiffel", "narration_final.wav")
WORDS = json.load(open(os.path.join(ROOT, "assets", "audio", "tts_eiffel", "words.json")))
N = int(DURATION * SR) + SR // 2
rng = np.random.default_rng(7)


def word_t(w, nth=0):
    k = 0
    for x in WORDS:
        if x["w"].strip(".,?!—").lower() == w.lower():
            if k == nth:
                return x["start"]
            k += 1
    raise KeyError(w)


# ======================================================================= instruments
def clarinet(m, d, vel=0.8):
    t = t_arr(d)
    f = midi_f(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t * 2.5, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph) + 0.06 * np.sin(7 * ph)
    x += lp(noise(d, int(m) + 900), 2500) * 0.03
    e = env_adsr(len(t), 0.05, 0.15, 0.8, 0.12)
    return fade(x * e * 0.22 * vel, 0.005, 0.05)


def pizz(m, d=0.35, vel=1.0, seed=0):
    return pluck(m, d, 0.35, seed) * 0.55 * vel


def upright(m, d=0.5, vel=1.0):
    t = t_arr(d)
    f = midi_f(m)
    x = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t)
    x *= np.exp(-t * 5.5)
    x += lp(noise(d, int(m)), 900) * np.exp(-t * 60) * 0.4
    return fade(x * 0.5 * vel, 0.002, 0.04)


def brush(d=0.18, vel=1.0, seed=0):
    x = bp(noise(d, 300 + seed), 1800, 9000) * env_adsr(int(d * SR), 0.01, 0.06, 0.25, 0.08)
    return x * 0.22 * vel


def hat(vel=1.0, seed=0):
    d = 0.05
    return hp(noise(d, 400 + seed), 7000) * exp_env(int(d * SR), 0.012) * 0.16 * vel


def low_hit(vel=1.0):
    d = 2.2
    t = t_arr(d)
    x = np.sin(2 * np.pi * 45 * t * (1 - 0.15 * t / d)) * np.exp(-t * 2.2)
    x += lp(noise(d, 77), 220) * np.exp(-t * 3.0) * 0.6
    x += pad(38, d, 0.2) * 0.6
    return x * 0.8 * vel


def swell(d=1.6, vel=1.0, seed=0):
    """reverse-cymbal style swell"""
    t = t_arr(d)
    x = bp(noise(d, 500 + seed), 3000, 12000) * (t / d) ** 2.5
    return fade(x * 0.35 * vel, 0.01, 0.02)


def strings(chord, d, vel=1.0, bright=0.25):
    x = np.zeros(int(d * SR))
    for m in chord:
        p = pad(m, d, bright)
        x[:len(p)] += p[:len(x)]
    return x * vel


# ======================================================================= score
DM = [50, 53, 57]       # D minor
BB = [46, 50, 53]       # Bb
GM = [43, 46, 50]       # G minor
A7 = [45, 49, 52, 55]   # A7
DMAJ = [50, 54, 57, 62]


def music():
    buf = np.zeros(N)
    bpm = 104
    beat = 60 / bpm
    # ---- hook: low hit + string chord on the deal, shimmer for the tower
    add(buf, low_hit(0.8), 0.02)
    add(buf, strings(DM, 1.8, 0.7, 0.2), 0.0)
    add(buf, swell(1.0, 0.5), 0.8)
    for k, m in enumerate([74, 77, 81, 86]):
        add(buf, glock(m, 1.2) * 0.7, 1.78 + k * 0.09)
    add(buf, strings([62, 65, 69, 74], 1.4, 0.35, 0.4), 1.75)
    # "There was just one problem. He didn't own it." -> sneaky pizz pickup, stop-time hit on "own it"
    t0 = 3.05
    for i, m in enumerate([50, 53, 57, 56, 55, 54]):
        add(buf, pizz(m + 12, 0.3, 0.9, i), t0 + i * beat * 0.5)
    hit = word_t("own")
    add(buf, upright(38, 0.9, 1.0), hit)
    add(buf, strings([50, 53, 56], 1.2, 0.5, 0.15), hit)
    # ---- groove 6.9 -> 20.9 and 52.1 -> 55.1 (walking bass + brushes + pizz + clarinet)
    walk_notes = [38, 41, 45, 44, 43, 41, 40, 37, 38, 45, 43, 41, 40, 43, 45, 37]
    chords_bar = [DM, DM, GM, A7]

    def groove(a, b, melody=True, dense=1.0, seed=0):
        nb = int((b - a) / beat)
        for i in range(nb):
            t = a + i * beat
            add(buf, upright(walk_notes[(i + seed) % 16], beat * 0.95, 0.85), t)
            if i % 2 == 1:
                add(buf, brush(0.2, 0.9, i), t)
            add(buf, hat(0.6, i), t + beat * 0.66)
            if dense > 0.5 and i % 4 in (0, 2):
                ch = chords_bar[(i // 4) % 4]
                for k, m in enumerate(ch):
                    add(buf, pizz(m + 12, 0.25, 0.45, i + k), t + beat * 0.5)
        if melody:
            mel = [(0, 62, 0.5), (0.5, 65, 0.5), (1, 69, 1.0), (2.5, 68, 0.5), (3, 67, 1.0), (4, 65, 0.5),
                   (4.5, 64, 0.5), (5, 62, 1.5), (8, 69, 0.5), (8.5, 70, 0.5), (9, 69, 1.0), (10, 65, 1.0),
                   (11, 67, 0.5), (11.5, 64, 1.5)]
            for st, m, dd in mel:
                tt = a + 1.0 + st * beat
                if tt + dd * beat < b - 0.2:
                    add(buf, clarinet(m, dd * beat * 0.95, 0.75), tt)
    groove(6.95, 20.9, melody=True)
    # ---- the pitch (20.95 -> 26.65): build with strings + glock arpeggios + more drums
    prog = [DM, BB, GM, A7, DM, BB]
    for k, ch in enumerate(prog):
        t = 20.95 + k * 0.95
        add(buf, strings([m + 12 for m in ch], 1.0, 0.55, 0.3 + 0.05 * k), t)
        add(buf, upright(ch[0] - 12, 0.9, 1.0), t)
        for j in range(4):
            add(buf, glock(ch[j % len(ch)] + 24, 0.5) * 0.35, t + j * 0.24)
        add(buf, brush(0.2, 1.0, k), t + 0.47)
    add(buf, swell(1.2, 0.6, 2), 25.4)
    # ---- sneaky section (26.65 -> 38.4): ticking, staccato pizz, sustained low strings
    a, b = 26.65, 38.4
    add(buf, strings([38, 45], b - a, 0.45, 0.12), a)
    i = 0
    t = a
    while t < b - 0.1:
        add(buf, hat(0.5, i) * 0.8, t)
        if i % 2 == 1:
            add(buf, pizz([62, 65, 64, 62, 60, 62, 65, 69][(i // 2) % 8], 0.2, 0.55, i), t)
        if i % 8 == 0:
            add(buf, upright(38, 0.6, 0.7), t)
        t += beat * 0.5
        i += 1
    for st, m, dd in [(30.0, 69, 0.8), (31.0, 68, 0.8), (32.4, 67, 1.6), (34.4, 65, 0.6), (35.2, 64, 0.6), (36.0, 62, 1.6)]:
        add(buf, clarinet(m, dd, 0.55), st)
    # "Poisson paid." accent
    add(buf, low_hit(0.55), word_t("paid") - 0.02)
    add(buf, strings([50, 53, 57, 60], 1.4, 0.45, 0.3), word_t("paid"))
    # ---- getaway (39.95 -> 43.1): brisk
    groove(39.95, 43.1, melody=False, dense=1.0, seed=4)
    # ---- realization (43.1 -> 50.4)
    add(buf, strings([38, 45, 50], 7.3, 0.5, 0.12), 43.1)
    for k, m in enumerate([69, 67, 65, 64, 62, 61, 62]):
        add(buf, pizz(m, 0.6, 0.6, k), 43.3 + k * 0.95)
    add(buf, low_hit(0.6), word_t("fake") - 0.02)
    # ---- "And the strangest part?" near silence + swell into the twist
    add(buf, glock(81, 1.4) * 0.5, word_t("strangest"))
    add(buf, swell(1.2, 0.6, 3), 52.1 - 1.2)
    # ---- second attempt groove (52.1 -> 55.1)
    groove(52.1, 55.0, melody=False, dense=1.0, seed=8)
    # ---- "This time, he failed." stop + hit
    add(buf, upright(38, 1.2, 0.7), word_t("failed") + 0.05)
    add(buf, strings([50, 53, 56], 1.0, 0.3, 0.12), word_t("failed") + 0.05)
    # ---- final: warm resolution under the tower
    add(buf, swell(1.0, 0.45, 4), 57.15 - 1.0)
    add(buf, strings([50, 54, 57, 62, 66], DURATION - 57.15 + 0.4, 0.75, 0.35), 57.15)
    add(buf, upright(38, 2.0, 0.8), 57.15)
    for k, m in enumerate([74, 78, 81, 86, 90]):
        add(buf, glock(m, 1.6) * 0.45, 57.2 + k * 0.16)
    for st, m, dd in [(57.6, 74, 0.5), (58.1, 73, 0.5), (58.6, 74, 1.0)]:
        add(buf, clarinet(m, dd, 0.6), st)
    add(buf, pizz(62, 0.5, 1.0), word_t("sell") + 0.32)
    add(buf, upright(38, 0.6, 1.0), word_t("sell") + 0.32)
    # gentle fade over the last 0.3s
    e = int(DURATION * SR)
    buf[e - int(0.3 * SR):e] *= np.linspace(1, 0, int(0.3 * SR))
    buf[e:] = 0
    return buf


# ======================================================================= sound design
def verb(x, d=1.2, mix=0.35):
    ir = noise(d, 1700) * np.exp(-t_arr(d) * 4.5)
    ir = lp(ir, 3500)
    from scipy.signal import fftconvolve
    w = fftconvolve(x, ir)[: len(x) + int(d * SR)]
    w = w / (np.abs(w).max() + 1e-9) * np.abs(x).max()
    y = np.zeros(len(w))
    y[: len(x)] += x
    return y + w * mix


def paper_slide(d=0.9, vel=1.0, seed=0):
    t = t_arr(d)
    x = bp(noise(d, 600 + seed), 900, 6000) * env_adsr(len(t), 0.08, 0.2, 0.7, 0.3)
    return x * 0.25 * vel


def rustle(d=0.5, vel=1.0, seed=0):
    x = np.zeros(int(d * SR))
    r = np.random.default_rng(seed)
    for k in range(int(d * 40)):
        g = bp(noise(0.03, 700 + seed * 50 + k), 1500, 9000) * exp_env(int(0.03 * SR), 0.01)
        add(x, g * r.uniform(0.3, 1.0), r.uniform(0, d - 0.04))
    return x * 0.5 * vel


def pen_scratch(d=1.1, seed=0):
    x = np.zeros(int(d * SR))
    r = np.random.default_rng(seed)
    t = 0
    while t < d - 0.1:
        L = r.uniform(0.06, 0.16)
        g = bp(noise(L, 800 + int(t * 100)), 2500, 7000) * env_adsr(int(L * SR), 0.01, 0.03, 0.8, 0.03)
        add(x, g * 0.35, t)
        t += L + r.uniform(0.01, 0.05)
    return x


def stamp_thump():
    x = sfx_thud(95, 0.3) * 0.9
    x[: int(0.02 * SR)] += hp(noise(0.02, 901), 1500) * 0.4
    return x


def metal_clank(f=180, d=0.9, vel=1.0, seed=0):
    t = t_arr(d)
    x = np.zeros_like(t)
    for k, mult in enumerate([1, 2.41, 3.77, 5.12]):
        x += np.sin(2 * np.pi * f * mult * t + seed) * np.exp(-t * (6 + 4 * k)) / (1 + k)
    x += lp(noise(d, 950 + seed), 900) * np.exp(-t * 25) * 0.8
    return x * 0.35 * vel


def chuff(vel=1.0, seed=0):
    d = 0.22
    return lp(noise(d, 1000 + seed), 1800) * exp_env(int(d * SR), 0.06) * 0.6 * vel


def hiss(d=1.2, vel=1.0):
    t = t_arr(d)
    return hp(noise(d, 1100), 2500) * env_adsr(len(t), 0.05, 0.2, 0.6, 0.5) * 0.25 * vel


def whistle(d=0.8, vel=1.0):
    t = t_arr(d)
    x = np.zeros_like(t)
    for f in (587, 740, 880):
        x += np.sin(2 * np.pi * f * t) * 0.33
    x += bp(noise(d, 1200), 800, 3000) * 0.2
    return fade(x * env_adsr(len(t), 0.06, 0.1, 0.8, 0.2) * 0.3 * vel, 0.01, 0.1)


def police_whistle(d=0.55):
    t = t_arr(d)
    f = 2900 + 120 * np.sign(np.sin(2 * np.pi * 28 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return fade(np.sin(ph) * env_adsr(len(t), 0.02, 0.05, 0.8, 0.1) * 0.12, 0.01, 0.05)


def car_pass(d=2.6, vel=1.0):
    t = t_arr(d)
    f0 = 38 * (1 + 0.06 * np.tanh((d / 2 - t) * 3))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = np.sign(np.sin(ph)) * 0.3 + np.sin(ph * 2) * 0.3
    x = lp(x, 500) + lp(noise(d, 1300), 300) * 0.4
    e = np.exp(-((t - d / 2) / (d / 3)) ** 2)
    return x * e * 0.35 * vel


def clock_tick(n, period=0.5):
    x = np.zeros(int(n * period * SR) + SR // 4)
    for k in range(n):
        d = 0.03
        tk = bp(noise(d, 1400 + k % 2), 2000, 6000) * exp_env(int(d * SR), 0.005) * (0.3 if k % 2 else 0.22)
        add(x, tk, k * period)
    return x


def door(vel=1.0):
    d = 0.5
    x = sfx_thud(110, 0.35) * 0.4
    y = np.zeros(int(d * SR))
    add(y, x, 0.0)
    add(y, bp(noise(0.12, 1500), 1200, 4000) * exp_env(int(0.12 * SR), 0.03) * 0.2, 0.0)
    return y * vel


def ambience(kind, d, seed=0):
    t = t_arr(d)
    if kind == "street":
        x = lp(noise(d, 2000 + seed), 450) * 0.22 + _babble(d, 2001 + seed, voices=6, lo=250, hi=2200) * 0.12
        for k in range(int(d * 2)):
            add(x, sfx_step(k) * 0.05, rng.uniform(0, d - 0.2))
    elif kind == "room":
        x = lp(noise(d, 2100 + seed), 220) * 0.06
    elif kind == "lobby":
        x = lp(noise(d, 2200), 300) * 0.06 + _babble(d, 2201, voices=8, lo=250, hi=1800) * 0.07
    elif kind == "wind":
        x = bp(noise(d, 2300 + seed), 120, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)) * 0.18
    elif kind == "station":
        x = lp(noise(d, 2400), 400) * 0.14 + _babble(d, 2401, voices=10, lo=250, hi=2000) * 0.08
    elif kind == "night":
        x = lp(noise(d, 2500), 180) * 0.05
    elif kind == "office":
        x = lp(noise(d, 2600), 300) * 0.05 + bp(noise(d, 2601), 600, 2000) * 0.01
    return fade(x.astype(np.float64), 0.08, 0.08)


AMB = [  # (start, end, kind, gain)
    (0.0, 1.75, "room", 1.0), (1.75, 6.95, "wind", 1.0), (1.75, 6.95, "street", 0.5),
    (6.95, 9.25, "wind", 1.4), (8.4, 14.55, "street", 1.0), (14.55, 17.55, "night", 1.0),
    (17.55, 18.55, "office", 1.0), (18.55, 19.75, "lobby", 1.0), (19.75, 20.95, "room", 1.0),
    (20.95, 26.65, "room", 0.6), (26.65, 39.95, "room", 1.0), (39.95, 41.45, "street", 1.0),
    (41.45, 43.1, "station", 1.0), (43.1, 45.65, "office", 1.0), (45.65, 47.0, "room", 1.2),
    (47.0, 50.4, "office", 1.0), (50.4, 52.1, "station", 1.0), (52.1, 57.15, "room", 1.0),
    (57.15, DURATION, "wind", 1.2), (57.15, DURATION, "street", 0.4),
]


def sfx_track():
    buf = np.zeros(N)
    E = []  # (time, sound, gain)
    # s01 envelope across the desk
    E += [(0.08, paper_slide(1.1, 1.0, 1), 1.0)]
    E += [(1.6, sfx_whoosh(0.4, 300, 1800), 0.25)]
    # s03 a small shoe scuff / hat tip
    E += [(3.65, rustle(0.25, 0.6, 2), 0.6)]
    # s05 aerial whoosh into the street
    E += [(6.9, sfx_whoosh(1.0, 200, 1400), 0.35)]
    # s06 newspaper + a car passing
    E += [(9.3, rustle(0.6, 1.0, 3), 0.8), (9.4, car_pass(2.6, 1.0), 1.0)]
    E += [(13.6, rustle(0.5, 1.0, 4), 1.0)]
    # s09 letter slides in, pen signs
    E += [(14.56, paper_slide(0.45, 1.0, 5), 0.9), (15.2, lp(pen_scratch(1.1, 6), 6000), 0.6)]
    # s10 stamp
    E += [(16.45 + 0.38, lp(stamp_thump(), 3000), 0.7)]
    # s11 letter lands on the desk
    E += [(17.55 + 0.4, rustle(0.25, 1.0, 7), 1.0), (17.55 + 0.42, sfx_thud(160, 0.12), 0.25)]
    # s12 footsteps in the lobby
    for k in range(3):
        E += [(18.6 + k * 0.5, sfx_step(k), 0.45)]
    # s13 door / chairs settle
    E += [(19.8, door(0.6), 0.5)]
    # s14 the plan: iron separating & landing
    E += [(20.95, sfx_whoosh(0.6, 400, 2200), 0.25)]
    for k in range(5):
        E += [(21.9 + k * 0.22, verb(metal_clank(150 + k * 30, 0.8, 0.6, k)), 0.5)]
    for k in range(5):
        E += [(23.9 + k * 0.28, verb(metal_clank(90 + k * 15, 1.2, 1.0, k + 5)), 0.7),
              (23.95 + k * 0.28, sfx_thud(70, 0.3), 0.35)]
    E += [(25.45, rustle(0.25, 1.0, 8), 0.8)]
    # s15 dealers lean in: chair creaks / papers
    E += [(27.6, rustle(0.6, 0.7, 9), 0.6)]
    # s20 notes into envelope, envelope slides
    E += [(38.45, rustle(0.45, 1.0, 10), 0.9), (39.0, paper_slide(0.8, 1.0, 11), 1.0)]
    # s21 hotel door + footsteps out to the street
    E += [(39.97, door(), 0.7)]
    for k in range(3):
        E += [(40.1 + k * 0.45, sfx_step(k + 3), 0.5)]
    # s22 train departs
    E += [(41.45, hiss(1.0, 1.0), 0.8), (41.5, whistle(0.7), 0.5)]
    tt, gap = 41.7, 0.42
    while tt < 43.2:
        E += [(tt, chuff(1.0, int(tt * 10)), 0.8)]
        tt += gap
        gap = max(0.18, gap * 0.85)
    # s23 paper
    E += [(43.3, rustle(0.5, 1.0, 12), 0.8)]
    # s24 empty room: a clock ticks
    E += [(45.7, clock_tick(3, 0.45), 1.0)]
    # s25 hat pulled down, drawer
    E += [(48.05, rustle(0.3, 1.0, 13), 0.7)]
    # s26 train arrives: brakes + slowing chuffs
    E += [(50.4, hiss(1.6, 1.0), 0.6)]
    tt, gap = 50.45, 0.2
    while tt < 51.8:
        E += [(tt, chuff(0.8, int(tt * 10)), 0.6)]
        tt += gap
        gap *= 1.25
    for k in range(3):
        E += [(50.8 + k * 0.55, sfx_step(k + 6), 0.45)]
    # s27 papers on the table
    E += [(52.3, rustle(0.5, 1.0, 14), 0.7)]
    # s28 table slap, chair scrape, police whistle
    E += [(55.1 + 0.12, bp(noise(0.35, 1600), 200, 1200) * exp_env(int(0.35 * SR), 0.1) * 0.3, 0.8),
          (55.1 + 0.45, sfx_thud(85, 0.3), 0.9), (55.1 + 0.47, rustle(0.25, 1.0, 15), 0.8)]
    # s29 reveal accent
    E += [(57.15, sfx_whoosh(0.6, 200, 1200), 0.2)]
    for t, x, g in E:
        add(buf, np.asarray(x, dtype=np.float64) * g, t)
    for a, b, kind, g in AMB:
        x = ambience(kind, b - a + 0.16, seed=int(a))
        add(buf, x * g, max(0, a - 0.08))
    return buf


# ======================================================================= mix
def db(x):
    return 10 ** (x / 20)


def mix(out=os.path.join(ROOT, "build", "mix.wav")):
    nar, sr = sf.read(NARR)
    if nar.ndim > 1:
        nar = nar.mean(1)
    nar = resample(nar, sr, SR)
    voice = np.zeros(N)
    voice[:min(N, len(nar))] = nar[:N]
    # gentle presence EQ + compression feel
    voice = voice + hp(voice, 2500) * 0.12
    mus = music()
    fx = sfx_track()
    env = envelope_follow(voice, 0.03, 0.45)
    env = env / (env.max() + 1e-9)
    duck = 1 - 0.62 * np.clip(env * 3.0, 0, 1)
    mus = norm(mus, 0.9) * db(-14) * duck
    fx = fx * db(-6) * (1 - 0.3 * np.clip(env * 3, 0, 1))
    voice = norm(voice, 0.95)
    m = voice + mus + fx
    # stereo: slight width for music/fx via short delay
    L = voice + mus + fx
    R = voice + np.roll(mus, 240) + np.roll(fx, 160)
    st = np.stack([L, R], 1)
    st = st / (np.abs(st).max() + 1e-9) * 0.89
    st = st[: int(DURATION * SR)]
    sf.write(out, st.astype(np.float32), SR)
    # loudness normalise for Shorts (-14 LUFS, -1.5 dBTP)
    final = out.replace(".wav", "_ln.wav")
    os.system(f'ffmpeg -v error -y -i "{out}" -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 "{final}"')
    print("mix ->", final)
    return final


if __name__ == "__main__":
    mix()

"""Part 3 soundtrack: narration placement, radio voice, procedural sound design, score, mix, SRT.

usage: python -m episodes.zombie_part3.soundtrack   -> build/p3/soundtrack.wav + output SRT
"""
import glob
import json
import math
import os

import numpy as np
import soundfile as sf
from scipy import signal

from cinecode import align, tts
from cinecode.audio import (SR, add, bp, env_adsr, envelope_follow, exp_env, fade, hp, lp, noise, resample, t_arr)
from episodes.zombie_part3.script import NARRATION, RADIO

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
DUR = TL["duration"]
N = int(DUR * SR)
TTS_DIR = os.path.join(ROOT, "assets", "audio", "tts", "zombie_p3")
BUILD = os.path.join(ROOT, "build", "p3")
OUT_SRT = os.path.join(ROOT, "output", "JUST_NEEDY_ZOMBIE_PART_3_FINAL.srt")
rng = np.random.default_rng(303)


def sramp(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def n1(t, seed):
    """Same value-noise as the renderer's n1() is not needed bit-exact; smooth random in [-1,1]."""
    r = np.random.default_rng(seed)
    knots = r.uniform(-1, 1, int(DUR * 60) + 8)
    x = np.asarray(t) * 1.0
    i = np.floor(x).astype(int)
    f = x - i
    f = f * f * (3 - 2 * f)
    i = np.clip(i, 0, len(knots) - 2)
    return knots[i] * (1 - f) + knots[i + 1] * f


def at(t):
    return int(t * SR)


def tt():
    return np.arange(N) / SR


# ------------------------------------------------------------------ voices
def narration_clips():
    take = glob.glob(os.path.join(TTS_DIR, "narration_*.wav"))[0]
    a = tts.read_wav(take)
    segs = align.align(a, [t for _, t in NARRATION])
    clips = {}
    for (lid, text), (s, e) in zip(NARRATION, segs):
        c = align.trim(a, s, e, pre=0.06, post=0.14)
        clips[lid] = (resample(c.astype(np.float64), tts.SR, SR), e - s)
    return clips


def radio_voice():
    p = glob.glob(os.path.join(TTS_DIR, "radio_*.wav"))[0]
    a = tts.read_wav(p).astype(np.float64)
    pz, db, thr = align.find_pauses(a, 0.05)
    v = np.where(db >= thr)[0]
    s, e = v[0] * align.HOP / tts.SR, (v[-1] + 1) * align.HOP / tts.SR
    a = align.trim(a, s, e, 0.04, 0.2)
    x = resample(a, tts.SR, SR)
    # small, failing emergency-radio speaker: band-limit, saturate, dropouts, hum
    x = bp(x, 380, 2900, order=3)
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 2.2) * 0.6
    t = np.arange(len(x)) / SR
    drop = 1 - 0.55 * (np.sin(2 * np.pi * 7.3 * t + 1.1) > 0.92) - 0.25 * (np.sin(2 * np.pi * 3.1 * t) > 0.97)
    x *= lp(drop, 60)
    x += bp(noise(len(x) / SR, 501), 800, 5000) * 0.05
    x += np.sin(2 * np.pi * 120 * t) * 0.012
    return x, e - s


# ------------------------------------------------------------------ sound design primitives
def burst(d, lo, hi, tau, seed, amp=1.0):
    return bp(noise(d, seed), lo, hi) * exp_env(int(d * SR), tau) * amp


def wet_step(seed, splash=False):
    x = burst(0.18, 120, 900, 0.035, seed, 0.8)  # mud squelch
    x += burst(0.18, 1500, 6000, 0.02, seed + 1, 0.25)
    if splash:
        s = burst(0.5, 900, 7000, 0.09, seed + 2, 0.7)
        for k in range(10):  # droplets
            d = np.zeros(int(0.5 * SR))
            st = int(rng.uniform(0.04, 0.42) * SR)
            f = rng.uniform(1800, 4200)
            n = int(0.04 * SR)
            d[st:st + n] += np.sin(2 * np.pi * f * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.008 * SR)) * 0.15
            s += d
        x = np.concatenate([x, np.zeros(len(s) - len(x))]) + s
    return fade(x)


def groan(d, f0, seed, rough=0.5):
    """Breathy vocal groan: glottal saw through two formants, slow pitch drift."""
    t = t_arr(d)
    r = np.random.default_rng(seed)
    f = f0 * (1 + 0.06 * np.sin(2 * np.pi * 0.7 * t + r.uniform(0, 6)) - 0.12 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = (2 * ((ph / (2 * np.pi)) % 1) - 1) * (1 - rough) + noise(d, seed) * rough * 0.6
    x = bp(src, 300, 900) * 0.6 + bp(src, 900, 1600) * 0.3
    return x * env_adsr(len(t), 0.25, 0.3, 0.8, 0.5)


def whimper(d, seed):
    t = t_arr(d)
    f = 340 + 60 * np.sin(2 * np.pi * 5.5 * t) - 80 * t / d
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = np.sin(ph) + 0.4 * np.sin(2 * ph) + noise(d, seed) * 0.5
    return bp(src, 400, 2400) * env_adsr(len(t), 0.05, 0.1, 0.7, 0.2) * 0.4


def breath(d, seed, inhale=True):
    x = bp(noise(d, seed), 500, 3500)
    e = np.sin(np.pi * np.linspace(0, 1, len(x))) ** (1.5 if inhale else 0.8)
    return x * e


def creak(d, f0, seed, amp=1.0):
    """Wood/metal creak: stick-slip pulse train with wandering rate, resonated."""
    t = t_arr(d)
    r = np.random.default_rng(seed)
    rate = f0 * (1 + 0.5 * np.sin(2 * np.pi * r.uniform(.5, 2) * t + r.uniform(0, 6)) + 0.3 * n1(t * 6, seed))
    ph = np.cumsum(rate) / SR
    pulses = np.diff(np.floor(ph), prepend=0) > 0
    x = pulses.astype(float) * (0.5 + 0.5 * r.random(len(t)))
    out = np.zeros_like(x)
    for fr, q in [(f0 * 3.1, 18), (f0 * 7.3, 25), (f0 * 12.8, 30)]:
        b, a = signal.iirpeak(min(fr, SR / 2 - 100), q, fs=SR)
        out += signal.lfilter(b, a, x)
    return out * env_adsr(len(t), 0.05, 0.1, 0.9, 0.15) * amp


def metal_grind(d, seed):
    t = t_arr(d)
    x = creak(d, 38, seed, 1.0) * 1.3
    x += bp(noise(d, seed + 1), 1800, 5200) * 0.12 * (0.5 + 0.5 * np.abs(n1(t * 9, seed + 2)))
    # resonant pipe ring underneath
    for f in (96, 143, 211):
        x += np.sin(2 * np.pi * f * t) * 0.03 * (0.5 + 0.5 * n1(t * 2, seed + 3 + f))
    return x


def knock(f, seed, amp=1.0):
    d = 0.22
    t = t_arr(d)
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * 28)
    x += burst(d, 800, 4000, 0.01, seed, 0.3)
    return x * amp


def tink(seed, f=None):
    d = 0.25
    t = t_arr(d)
    f = f or rng.uniform(3200, 5200)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t * 32) * 0.3


def impact(d=3.2):
    t = t_arr(d)
    boom = np.sin(2 * np.pi * (34 + 30 * np.exp(-t * 6)) * t) * np.exp(-t * 1.4)
    clang = sum(np.sin(2 * np.pi * f * t + i) * np.exp(-t * dk) * a for i, (f, dk, a) in
                enumerate([(87, 1.6, .5), (131, 1.9, .4), (203, 2.4, .3), (317, 3.0, .22), (466, 3.6, .16), (731, 5, .1)]))
    hit = burst(d, 60, 3000, 0.03, 801, 1.2)
    return (boom * 1.0 + clang * 0.8 + hit) * 0.9


def static(d, seed, density=1.0):
    t = t_arr(d)
    x = bp(noise(d, seed), 1200, 7000) * 0.35 * (0.6 + 0.4 * np.abs(n1(t * 7, seed)))
    # crackles
    n = int(d * 40 * density)
    for k in range(n):
        st = rng.uniform(0, d - 0.02)
        c = hp(noise(0.006, seed + k + 9), 2500) * rng.uniform(.3, 1.4)
        add(x, c, st)
    # tuning whistle
    x += np.sin(2 * np.pi * np.cumsum(1900 + 300 * n1(t * .8, seed + 4)) / SR) * 0.015
    return x


# ------------------------------------------------------------------ score
def pad(freqs, d, bright=600, detune=0.004, seed=0):
    t = t_arr(d)
    x = np.zeros(len(t))
    r = np.random.default_rng(seed)
    for f in freqs:
        for k in (-1, 0, 1):
            ff = f * (1 + k * detune)
            ph = r.uniform(0, 1)
            x += 2 * ((ff * t + ph) % 1) - 1
    return lp(x / (len(freqs) * 3), bright, order=2)


def score():
    t = tt()
    m = np.zeros(N)
    # 1) dark low drone (A1 + E2 + Bb2 rub) from the start, very quiet, rising
    d = pad([55, 82.4, 116.5], DUR, 380, seed=1)
    m += d * (0.10 + 0.10 * sramp(t, 20, 45)) * (1 - sramp(t, 56.55, 56.75))
    # 2) sub pulse (heartbeat-like) from the fence onward, accelerating
    pulse = np.zeros(N)
    bt = 29.6
    while bt < 56.6:
        k = int(bt * SR)
        x = np.sin(2 * np.pi * 46 * t_arr(.35)) * np.exp(-t_arr(.35) * 12)
        add(pulse, x * 0.5, bt)
        add(pulse, x * 0.3, bt + 0.22)
        bt += 1.15 - 0.45 * np.clip((bt - 30) / 26, 0, 1)
    m += pulse * 0.55
    # 3) high string cluster tremolo for the last stretch (hatch -> radio)
    cl = pad([622.3, 659.3, 698.5, 932.3], DUR, 2400, detune=0.003, seed=3)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 11 * t)
    m += cl * trem * 0.07 * sramp(t, 41.5, 49) * (1 - sramp(t, 56.55, 56.7)) + cl * 0.03 * sramp(t, 36.5, 41.5) * (1 - sramp(t, 56.55, 56.7))
    # 4) sparse low piano-like notes for mystery (scene 2-3)
    for tn, f in [(5.5, 110), (8.2, 103.8), (12.9, 98), (16.3, 87.3), (21.0, 92.5), (25.4, 82.4)]:
        d = 3.5
        tx = t_arr(d)
        nte = (np.sin(2 * np.pi * f * tx) + 0.35 * np.sin(2 * np.pi * 2 * f * tx) + 0.12 * np.sin(2 * np.pi * 3.01 * f * tx)) * np.exp(-tx * 1.2)
        add(m, nte * 0.08, tn)
    # 5) rising shepard-like swell under the hatch (36.6 - 46) and radio (49 - 56.6)
    def riser(a, b, f0, f1, amp):
        d = b - a
        tx = t_arr(d)
        f = f0 * (f1 / f0) ** (tx / d)
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = (np.sin(ph) + 0.5 * np.sin(1.5 * ph)) * sramp(tx, 0, d) * amp
        add(m, x, a)
    riser(41.6, 46.0, 70, 105, 0.05)
    riser(49.0, 56.6, 60, 120, 0.06)
    return m


# ------------------------------------------------------------------ sound design timeline
def design():
    t = tt()
    amb = np.zeros(N)     # beds (ducked under speech)
    fx = np.zeros(N)      # spot effects (lightly ducked)
    # shot map for perspective (inside / outside)
    inside = np.zeros(N)
    for a, b in [(5.45, 7.4), (12.85, 16.3), (25.3, 26.05), (48.8, 56.6)]:
        inside[at(a):at(b)] = 1
    inside = lp(inside, 30)
    science = np.zeros(N)
    science[at(16.3):at(25.3)] = 1
    science = lp(science, 15)
    black = np.zeros(N)
    black[at(58.35):] = 1

    # wind through corn (outdoors), leaves; muffled indoors
    wind = bp(noise(DUR, 11), 180, 2200) * (0.55 + 0.45 * np.abs(n1(t * .25, 12)))
    leaves = hp(noise(DUR, 13), 2500) * (0.3 + 0.7 * np.clip(n1(t * 1.5, 14), 0, 1)) * 0.35
    out_bed = (wind * 0.25 + leaves * 0.12)
    in_bed = lp(wind, 500) * 0.12 + lp(noise(DUR, 15), 160) * 0.05  # room tone
    amb += out_bed * (1 - inside) * (1 - science) + in_bed * inside
    amb += lp(noise(DUR, 16), 220) * 0.06 * science  # sub air for the diorama
    # silence before the impact, then silence on black
    hush = 1 - sramp(t, 56.75, 57.0) * (1 - sramp(t, 57.85, 57.95)) * 0.85
    amb *= hush * (1 - black * sramp(t, 58.4, 59.6))

    # ---- scene 1: zombie run
    ph = lambda x: 2 * np.pi * (2.5 * x + .12 * np.sin(3.1 * x) + .05 * np.sin(7.3 * x))
    ts = np.linspace(0, 2.95, 3000)
    sv = np.sin(ph(ts))
    steps = ts[1:][np.diff(np.sign(sv)) != 0]
    puddles = [(-6.8, 15.5), (-6.2, 11.2), (-5.2, 8.4)]
    for i, s in enumerate(steps):
        k = s / 2.95
        z = 20.4 - k * 15.2
        wet = any(abs(z - pz) < 0.9 for _, pz in puddles)
        add(fx, wet_step(100 + i, splash=wet) * (0.55 if wet else 0.4), s)
    add(fx, wet_step(140, True) * 0.4, 2.98)  # skid into cover
    # panicked ragged breathing while running, whimpering in hiding
    for i, s in enumerate(np.arange(0.05, 2.9, 0.42)):
        add(fx, breath(0.22, 200 + i) * 0.16, s)
    add(fx, whimper(0.9, 210) * 0.5, 3.7)
    add(fx, whimper(0.7, 211) * 0.4, 4.75)
    for i, s in enumerate(np.arange(3.1, 5.4, 0.3)):
        add(fx, breath(0.16, 220 + i) * 0.09, s)
    # distant infected groans (far, filtered)
    for s, f, a in [(0.6, 95, .10), (6.8, 85, .07), (19.0, 90, .0), (33.0, 80, .05), (38.5, 88, .045)]:
        g = lp(groan(2.4, f, int(s * 10)), 1200) * a
        add(amb, g, s)
    # porch creak as the zombie hides
    add(fx, creak(0.7, 9, 230, 0.5), 3.0)

    # ---- scene 2: corn rustle along the line (strong in the tracking shot)
    rust_env = sramp(t, 6.0, 7.0) * (1 - sramp(t, 12.3, 12.85))
    shot_gain = np.where((t > 7.4) & (t < 11.7), 1.0, 0.35)
    rust = hp(noise(DUR, 31), 1800) * (0.4 + 0.6 * np.abs(n1(t * 6, 32))) + bp(noise(DUR, 33), 300, 1500) * 0.3 * np.abs(n1(t * 4, 34))
    fx += rust * rust_env * lp(shot_gain, 20) * 0.16
    # stalk snaps
    for s in [8.1, 8.9, 9.6, 10.6]:
        add(fx, burst(0.08, 1500, 6000, 0.008, int(s * 100), 0.3), s)
    # house creak
    add(amb, creak(1.2, 6, 240, 0.25), 6.6)

    # ---- vibration rumble + glass (python twin of vib(t) in main.js)
    env = sramp(t, 12.4, 14.6) * (1 - sramp(t, 26, 30) * .6)
    pulse = np.maximum(0, np.sin(t * 6.1 + np.sin(t * 1.3) * 2)) ** 6 * .7 + .3 * (n1(t * 9, 21) * .5 + .5)
    v = env * pulse
    rumble = lp(noise(DUR, 41), 70, order=4) * 3.0 + np.sin(2 * np.pi * 38 * t) * 0.25
    fx += rumble * lp(v, 25) * 0.35 * (1 - black) * (1 - sramp(t, 25.3, 26.5) * 0.5) * hush
    # glass + plate rattle on the table (only near the table shots)
    near_table = np.zeros(N)
    near_table[at(12.85):at(16.3)] = 1
    near_table = lp(near_table, 20)
    rr = np.random.default_rng(42)
    for k in range(260):
        s = rr.uniform(12.6, 16.6)
        if rr.random() < (0.2 + 0.8 * min(1, max(0, (s - 12.6) / 2))) * min(1, max(0, (s - 12.5))):
            add(fx, tink(k) * near_table[at(s)] * 0.55 * (0.4 + rr.random()), s)
    # diorama: soft low swells with each ring
    for s in np.arange(16.8, 24.9, 1.6 / 4.2 * 2):
        x = np.sin(2 * np.pi * 52 * t_arr(.8)) * np.sin(np.pi * np.linspace(0, 1, at(.8))) * 0.12
        add(fx, x, s)
    # mini-house shudder rattle
    add(fx, burst(1.2, 200, 2000, 0.3, 77, 0.08), 20.6)

    # ---- scene 4: tractor: wind only; a drip plinks
    add(fx, tink(0, f=2300) * 0.35, 28.62)
    add(fx, creak(0.5, 12, 250, 0.12), 26.2)  # loose panel tick
    # fence: knocks travelling along the posts (perspective: louder in the fence close-up)
    xs = np.linspace(-14, 18.8, 15)
    for i, x in enumerate(xs):
        tp = 29.6 + (x + 9) / 4.64
        if tp < 29.0 or tp > 36.5:
            continue
        g = 0.55 if tp < 33.4 else 0.3
        dist = abs(x + 11) / 25
        for k in range(4):
            add(fx, knock(rng.uniform(170, 320), 300 + i * 10 + k, g * (1 - 0.4 * dist) * (0.8 ** k)), tp + k * 0.09 + rng.uniform(0, .03))
        add(fx, creak(0.45, 14, 320 + i, g * 0.35), tp + 0.05)

    # ---- scene 5: hatch metal (perspective: full on hatch shots, faint elsewhere)
    hatch_on = np.zeros(N)
    for a, b, g in [(36.6, 46.0, 1.0), (46.0, 48.8, 0.15), (48.8, 56.6, 0.06), (56.6, 56.95, 1.0)]:
        hatch_on[at(a):at(b)] = g
    hatch_on = lp(hatch_on, 25)
    tremble = np.zeros(N)
    tr = bp(noise(DUR, 61), 900, 4000) * np.abs(n1(t * 30, 62)) * 0.25
    tremble += tr * sramp(t, 41.6, 42.0) * (1 - sramp(t, 56.85, 56.95))
    grind = np.zeros(N)
    gr = metal_grind(56.92 - 42.25, 63)
    add(grind, gr, 42.25)
    fx += (tremble + grind * 0.9) * hatch_on
    add(fx, creak(0.9, 7, 70, 0.7), 41.55)   # first groan of the handle
    # dirt trickle
    for k in range(40):
        add(fx, burst(0.05, 2000, 7000, 0.01, 700 + k, 0.08) * hatch_on[at(42 + k * .3)], 42 + k * 0.3 + rng.uniform(0, .2))
    # hero: held breath, then shaky exhale
    hb = np.zeros(N)
    for s in np.arange(46.1, 48.7, 0.82):
        x = np.sin(2 * np.pi * 50 * t_arr(.18)) * np.exp(-t_arr(.18) * 22)
        add(hb, x * 0.35, s)
        add(hb, x * 0.22, s + 0.2)
    fx += hb
    add(fx, breath(0.9, 260, inhale=False) * 0.28, 47.9)

    # ---- scene 6: radio
    rad = np.zeros(N)
    st = static(56.6 - 49.0, 81, 1.2)
    add(rad, st, 49.03)
    # sharp crackle on "crackled"
    add(rad, hp(noise(0.25, 82), 1500) * exp_env(at(.25), .05) * 0.6, 49.03)
    rad_gain = np.ones(N)
    rad_gain[at(51.6):at(54.0)] = 0.6   # wider shot
    rad_gain = lp(rad_gain, 20)
    duck_voice = 1 - 0.55 * sramp(t, TL["lines"]["r01"] - 0.1, TL["lines"]["r01"]) * (1 - sramp(t, TL["lines"]["r01"] + 1.5, TL["lines"]["r01"] + 1.8))
    fx += rad * rad_gain * duck_voice * 0.26 * (1 - sramp(t, 56.58, 56.62))
    # footsteps on old floorboards
    for i, s in enumerate(np.arange(51.75, 53.8, 0.48)):
        add(fx, knock(rng.uniform(110, 150), 900 + i, 0.18), s)
        add(fx, creak(0.3, 10, 910 + i, 0.12), s + 0.03)

    # ---- scene 7: silence, lift, impact
    add(fx, creak(0.35, 5, 990, 0.9), 57.92)
    add(fx, impact() * 0.6, 57.98)
    fx *= (1 - black * sramp(t, 58.4, 60.4) * 0.0)
    return amb, fx


def main():
    os.makedirs(BUILD, exist_ok=True)
    voice = np.zeros(N)
    cues = []
    clips = narration_clips()
    starts = TL["lines"]
    order = [lid for lid, _ in NARRATION]
    for i, lid in enumerate(order):
        c, dur = clips[lid]
        s = starts[lid]
        add(voice, c * 1.0, s - 0.06)
        nxt = starts[order[i + 1]] if i + 1 < len(order) else starts["r01"]
        if s + dur > nxt - 0.05:
            print(f"WARNING {lid} overlaps next line ({s + dur:.2f} > {nxt:.2f})")
        cues.append((s, s + dur, dict(NARRATION)[lid]))
    rv, rdur = radio_voice()
    radio = np.zeros(N)
    add(radio, rv, starts["r01"] - 0.04)
    cues.append((starts["r01"], starts["r01"] + rdur, "(radio, whispering) " + RADIO[1]))

    vnorm = voice / (np.max(np.abs(voice)) + 1e-9) * 0.85
    radio = radio / (np.max(np.abs(radio)) + 1e-9) * 0.62
    music = score()
    amb, fx = design()
    # sidechain ducking under the narrator
    env = envelope_follow(vnorm + radio, att=0.03, rel=0.4)
    duck = 1 - 0.6 * np.clip(env / 0.25, 0, 1)
    duck_fx = 1 - 0.45 * np.clip(env / 0.25, 0, 1)
    mix = vnorm + radio + music * duck * 0.8 + amb * duck * 0.5 + fx * duck_fx * 0.55
    # gentle bus limiter
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / max(peak, 1e-9) * 1.3) / np.tanh(1.3) * 0.89
    stereo = np.stack([mix, mix], axis=1)
    sf.write(os.path.join(BUILD, "soundtrack_raw.wav"), stereo, SR, subtype="PCM_24")
    for name, x in [("stem_voice", vnorm + radio), ("stem_music", music), ("stem_fx", amb + fx)]:
        sf.write(os.path.join(BUILD, name + ".wav"), np.clip(x, -1, 1), SR, subtype="PCM_16")
    write_srt(cues)
    json.dump([[a, b, c] for a, b, c in cues], open(os.path.join(BUILD, "cues.json"), "w"), indent=1)
    print("soundtrack ok", len(mix) / SR, "s")


def srt_time(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues):
    os.makedirs(os.path.dirname(OUT_SRT), exist_ok=True)
    with open(OUT_SRT, "w") as f:
        for i, (a, b, text) in enumerate(cues, 1):
            text = text.replace("Here's what we know: ", "Here's what we know:\n")
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b + 0.15)}\n{text}\n\n")


if __name__ == "__main__":
    main()

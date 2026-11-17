"""Soundtrack for the vertical short: narration + soft piano/pad score + ambiences + gentle SFX."""
import os
import subprocess
import zlib

import numpy as np
from scipy.signal import resample_poly

from cinecode import tts
from cinecode.audio import bp, hp, lp, noise
from .make_voice import line_path

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "numbers")


def T(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.01, r=0.2):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    if nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def mf(m):
    return 440 * 2 ** ((m - 69) / 12)


def piano(m, d=2.5, vel=0.5):
    t = T(d)
    f = mf(m)
    x = np.zeros_like(t)
    for k, (h, dec) in enumerate(((1, 1.0), (2, 0.45), (3, 0.25), (4, 0.12))):
        x += np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * k)) * dec * np.exp(-t * (1.1 + k * 1.3))
    x *= env(len(t), 0.004, 0.3)
    return x * vel * 0.35


def softpad(m, d):
    t = T(d)
    x = np.zeros_like(t)
    for det in (-0.06, 0.0, 0.05):
        ff = mf(m) * 2 ** (det / 12)
        x += np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(2 * np.pi * ff * 2 * t)
    return x * env(len(t), 1.2, 1.5) * 0.06


def add(buf, x, t, g=1.0):
    s = int(t * SR)
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(len(buf), s + len(x))
    if e > s:
        buf[s:e] += x[: e - s] * g


# ------------------------------------------------------------------ score
MINOR = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]   # Am F C G
LIFT = [(48, [55, 60, 64]), (55, [55, 59, 62]), (57, [57, 60, 64]), (53, [53, 57, 60])]    # C G Am F


def score(total, lift_at, end_soft):
    buf = np.zeros(int((total + 4) * SR))
    rng = np.random.default_rng(3)
    bar = 4.0
    t = 0.0
    i = 0
    while t < total:
        prog = LIFT if t >= lift_at else MINOR
        root, ch = prog[i % 4]
        lvl = 1.0
        add(buf, softpad(root - 12, bar + 1.5), t, 0.9)
        for n in ch:
            add(buf, softpad(n, bar + 1.5), t, 0.5)
        # gentle broken-chord piano
        pattern = [0, 2, 1, 2] if t < lift_at else [0, 1, 2, 1, 2, 1]
        step = bar / len(pattern)
        for k, idx in enumerate(pattern):
            add(buf, piano(ch[idx] + 12, 2.6, 0.35 + 0.1 * rng.random()), t + k * step + rng.random() * 0.02)
        add(buf, piano(root - 12, 3.5, 0.45), t)
        # sparse melody
        if i % 2 == 1 and t > 8:
            mel = ch[2] + 24 if rng.random() < 0.5 else ch[1] + 24
            add(buf, piano(mel, 3.0, 0.22), t + 2.0)
        t += bar
        i += 1
    buf = buf[: int(total * SR)]
    # long fade at the end
    n = int(end_soft * SR)
    buf[-n:] *= np.linspace(1, 0, n) ** 1.5
    buf[: int(2 * SR)] *= np.linspace(0, 1, int(2 * SR))
    return buf


# ------------------------------------------------------------------ SFX / ambience
def amb(kind, d):
    n = int(d * SR)
    rng = np.random.default_rng(zlib.crc32(kind.encode()) % 1000)
    w = rng.standard_normal(n)
    if kind == "amb_room":
        x = lp(w, 300) * 0.05
    elif kind == "amb_street":
        x = lp(w, 700) * 0.08 + bp(rng.standard_normal(n), 300, 2500) * 0.015 * (1 + np.sin(T(d) * 0.7))
    elif kind == "amb_subway":
        x = lp(w, 160) * 0.22 + bp(rng.standard_normal(n), 800, 2000) * 0.01
        x += np.sin(2 * np.pi * 55 * T(d)) * 0.02
        clack = np.zeros(n)
        for k in np.arange(0.3, d, 0.9):
            add_ = lp(rng.standard_normal(int(0.06 * SR)), 900) * np.exp(-np.arange(int(0.06 * SR)) / SR * 50) * 0.25
            s = int(k * SR)
            clack[s:s + len(add_)] += add_[: max(0, min(len(add_), n - s))]
        x += clack
    elif kind in ("amb_shop", "amb_office", "amb_cafe"):
        x = lp(w, 500) * 0.06
        murm = bp(rng.standard_normal(n), 250, 1200) * 0.03 * (0.6 + 0.4 * np.sin(T(d) * 1.3))
        x += murm
    elif kind == "amb_void":
        x = lp(w, 120) * 0.05
    elif kind == "amb_night":
        x = lp(w, 250) * 0.05
    elif kind == "amb_city":
        x = lp(w, 400) * 0.08 + bp(rng.standard_normal(n), 400, 900) * 0.01
    elif kind == "rain":
        x = hp(lp(w, 6000), 1200) * 0.06
        drops = (rng.random(n) < 0.0008) * rng.random(n)
        x += lp(drops, 4000) * 0.4
    elif kind == "crickets":
        t = T(d)
        x = np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 28 * t) > 0.6) * (np.sin(2 * np.pi * 0.8 * t) > 0) * 0.02
    elif kind == "clock":
        x = np.zeros(n)
        for k in np.arange(0.2, d, 1.0):
            tk = lp(rng.standard_normal(int(0.02 * SR)), 3000) * np.exp(-np.arange(int(0.02 * SR)) / SR * 200) * 0.2
            s = int(k * SR)
            x[s:s + len(tk)] += tk[: max(0, min(len(tk), n - s))]
    elif kind == "flashback":
        x = lp(w, 800) * 0.04 + np.sin(2 * np.pi * 880 * T(d)) * np.exp(-T(d) * 0.8) * 0.03
    elif kind == "kids":
        x = bp(rng.standard_normal(n), 600, 2500) * 0.02 * (0.5 + 0.5 * np.sin(T(d) * 2.1)) * np.exp(-T(d) * 0.2)
    else:
        x = np.zeros(n)
    return x * env(n, 0.4, 0.5)


def P(*xs):
    """Sum signals of different lengths."""
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[:len(x)] += x
    return out


def bell_tone(f, d=1.6, g=0.3):
    t = T(d)
    x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 8)
    return x * np.exp(-t * 2.2) * env(len(t), 0.003, 0.2) * g


def sfx(name):
    rng = np.random.default_rng(zlib.crc32(name.encode()) % 997)
    if name == "num_tick":
        return bell_tone(1568 * (1 + 0.06 * rng.standard_normal()), 0.6, 0.12)
    if name == "chime_soft":
        return P(bell_tone(1046, 2.0, 0.18), bell_tone(1568, 2.0, 0.08))
    if name == "num_reveal":
        return P(bell_tone(1318, 2.2, 0.2), bell_tone(659, 2.2, 0.12))
    if name == "num_reveal_low":
        return P(bell_tone(392, 2.6, 0.25), bell_tone(784, 2.0, 0.08))
    if name == "num_drop":
        return P(bell_tone(523, 2.2, 0.2), bell_tone(494, 2.2, 0.15), sfx("thump") * 0.6)
    if name == "zero_hit":
        t = T(3.5)
        sub = np.sin(2 * np.pi * (48 + 20 * np.exp(-t * 3)) * t) * np.exp(-t * 1.2) * 0.5
        return P(sub, bell_tone(220, 3.5, 0.15), bell_tone(262, 3.5, 0.08))
    if name == "thump":
        t = T(0.6)
        return np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 7) * 0.5
    if name == "low_note":
        t = T(3.0)
        return np.sin(2 * np.pi * 73.4 * t) * env(len(t), 0.3, 1.5) * 0.18
    if name == "empty_tone":
        t = T(2.5)
        return (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * env(len(t), 0.5, 1.5) * 0.05
    if name == "swell":
        t = T(3.0)
        return lp(np.random.default_rng(1).standard_normal(len(t)), 900) * (t / 3) ** 2 * env(len(t), 0.01, 0.4) * 0.25
    if name == "shimmer":
        out = np.zeros(int(2.5 * SR))
        for k, m in enumerate((84, 88, 91, 96)):
            add(out, bell_tone(mf(m), 2.0, 0.06), k * 0.12)
        return out
    if name in ("count_up", "count_down", "count_up_big"):
        d = 1.3 if name != "count_up_big" else 1.4
        out = np.zeros(int((d + 1.5) * SR))
        steps = 14
        for k in range(steps):
            fr = k / steps
            f = 900 + (900 * fr if name != "count_down" else -500 * fr)
            add(out, bell_tone(f, 0.25, 0.06), d * (fr ** 0.7))
        if name == "count_up_big":
            add(out, P(bell_tone(1046, 2.0, 0.18), bell_tone(1318, 2.0, 0.12), bell_tone(1568, 2.0, 0.1)), d)
        return out
    if name == "doors":
        t = T(1.2)
        return (bp(rng.standard_normal(len(t)), 300, 3000) * np.exp(-t * 3) * 0.15 +
                np.sin(2 * np.pi * 660 * t) * (t < 0.25) * 0.05 + np.sin(2 * np.pi * 550 * t) * ((t > 0.3) & (t < 0.55)) * 0.05)
    if name == "bell":
        return P(bell_tone(2093, 1.5, 0.1), bell_tone(2637, 1.2, 0.06))
    if name == "buzz":
        t = T(0.6)
        return np.sin(2 * np.pi * 140 * t) * (np.sin(2 * np.pi * 25 * t) > 0) * env(len(t), 0.01, 0.05) * 0.12
    if name == "pickup":
        return bell_tone(1200, 0.3, 0.08)
    if name == "knock":
        out = np.zeros(int(0.9 * SR))
        for k in (0.0, 0.22, 0.4):
            add(out, lp(rng.standard_normal(int(0.08 * SR)), 600) * np.exp(-T(0.08) * 60) * 0.6, k)
        return out
    if name == "door_open":
        t = T(1.0)
        return P(bp(rng.standard_normal(len(t)), 200, 900) * np.exp(-t * 2.5) * 0.12, sfx("thump") * 0.2)
    if name == "door_close":
        return P(sfx("thump") * 0.9, lp(rng.standard_normal(int(0.3 * SR)), 1500) * np.exp(-T(0.3) * 25) * 0.15)
    if name == "phone_hum":
        t = T(2.0)
        return np.sin(2 * np.pi * 220 * t) * env(len(t), 0.5, 1.0) * 0.03
    if name == "pop_soft":
        t = T(0.25)
        return np.sin(2 * np.pi * (600 + 400 * np.exp(-t * 30)) * t) * np.exp(-t * 25) * 0.12
    if name == "steps":
        out = np.zeros(int(1.5 * SR))
        for k in (0.0, 0.5, 1.0):
            add(out, lp(rng.standard_normal(int(0.1 * SR)), 400) * np.exp(-T(0.1) * 40) * 0.3, k)
        return out
    if name == "scroll":
        out = np.zeros(int(1.6 * SR))
        for k in range(12):
            add(out, hp(rng.standard_normal(int(0.01 * SR)), 3000) * 0.05, k * 0.11 * (1 + k * 0.04))
        return out
    if name == "select":
        return bell_tone(988, 1.2, 0.14)
    if name == "whoosh_soft":
        t = T(0.9)
        return bp(rng.standard_normal(len(t)), 300, 1500) * np.sin(np.pi * t / 0.9) ** 2 * 0.1
    if name == "key":
        return hp(rng.standard_normal(int(0.03 * SR)), 2500) * np.exp(-T(0.03) * 120) * 0.12
    if name == "send":
        t = T(0.4)
        return np.sin(2 * np.pi * (500 + 900 * t / 0.4) * t) * np.exp(-t * 9) * 0.15
    if name == "receive":
        return P(bell_tone(1318, 1.0, 0.16), bell_tone(1760, 1.0, 0.1))
    if name == "dial":
        t = T(1.8)
        return (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * (t < 1.0) * env(len(t), 0.02, 0.85) * 0.03
    raise KeyError(name)


AMB = {"amb_room", "amb_street", "amb_subway", "amb_shop", "amb_office", "amb_void", "amb_night", "amb_city",
       "amb_cafe", "rain", "crickets", "clock", "flashback", "kids"}


def mixdown(shots, film_end, total, cues):
    n = int((total + 0.5) * SR)
    voice = np.zeros(n)
    fx = np.zeros(n)
    for sh in shots:
        for lid in sh.lines:
            a = tts.read_wav(line_path(lid))
            a = resample_poly(a, 2, 1)
            add(voice, a, sh.t0 + sh.T[lid][0])
        for (lt, name, vol) in sh.sfx():
            if name in AMB:
                x = amb(name, sh.dur - lt + 0.4)
            else:
                x = sfx(name)
            add(fx, x, sh.t0 + lt, vol)
    # end card: a last soft chime
    add(fx, sfx("chime_soft"), film_end + 0.2, 0.5)
    lift = next(s.t0 for s in shots if type(s).__name__ == "S21Coffee")
    music = np.zeros(n)
    add(music, score(total + 0.3, lift, 6.0), 0.0)
    # duck music under narration
    venv = np.abs(voice)
    k = int(0.25 * SR)
    venv = np.convolve(venv, np.ones(k) / k, mode="same")
    duck = 1.0 - 0.45 * np.clip(venv / 0.03, 0, 1)
    music *= duck
    mix = voice * 1.0 + music * 0.55 + fx * 0.8
    mix = np.tanh(mix * 1.1) / 1.1
    os.makedirs(BUILD, exist_ok=True)
    raw = os.path.join(BUILD, "mix_raw.wav")
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(raw, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-ar", "48000", "-ac", "2", out], check=True)
    from .frame import srt
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    srt(cues, os.path.join(ROOT, "output", "The_Number_Above_Their_Head.en.srt"))
    print("wrote", out)

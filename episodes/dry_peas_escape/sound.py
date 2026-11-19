"""Episode-specific procedural SFX, prison ambience and music-bed mapping (registered into cinecode.audio)."""
import functools

import numpy as np

from cinecode import audio as A
from cinecode.audio import SR, add, bp, exp_env, hp, lp, noise, norm, sweep, t_arr


def pea_tick():
    d = 0.07
    x = bp(noise(d, 101), 1800, 6000) * exp_env(int(d * SR), 0.008)
    x += np.sin(2 * np.pi * 2300 * t_arr(d)) * exp_env(int(d * SR), 0.01) * 0.3
    return norm(x, 0.6)


def pour():
    d = 1.2
    t = t_arr(d)
    x = bp(noise(d, 102), 500, 3500)
    gurgle = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t + np.sin(2 * np.pi * 2.3 * t) * 3)
    e = np.minimum(1, t * 10) * np.minimum(1, (d - t) * 4)
    return norm(x * gurgle * e, 0.5)


def pat():
    d = 0.12
    x = lp(noise(d, 103), 900) * exp_env(int(d * SR), 0.02)
    return norm(x, 0.7)


def sizzle():
    d = 1.6
    t = t_arr(d)
    x = hp(noise(d, 104), 3000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 13 * t)))
    return norm(x * np.minimum(1, t * 6) * np.minimum(1, (d - t) * 3), 0.35)


def whoosh_soft():
    return A.sfx_whoosh(0.5, 250, 1600) * 0.6


def keys():
    d = 0.9
    t = t_arr(d)
    x = np.zeros_like(t)
    r = np.random.default_rng(105)
    for k in range(9):
        st = r.uniform(0, 0.6)
        f = r.uniform(2500, 5200)
        seg = np.sin(2 * np.pi * f * t_arr(0.18)) * exp_env(int(0.18 * SR), 0.03)
        add(x, seg * r.uniform(0.3, 0.8), st)
    return norm(x, 0.5)


def laugh_big():
    x = A.sfx_laugh(3.0)
    d = 3.0
    t = t_arr(d)
    # a lower "ho-ho" belly laugh on top
    f = 140 + 30 * np.sin(2 * np.pi * 0.7 * t)
    ho = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    ho = lp(ho, 900) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 4.2 * t))) * np.minimum(1, (d - t) * 1.2)
    return norm(x[: len(ho)] * 0.6 + ho * 0.5, 0.8)


def lick():
    d = 0.25
    t = t_arr(d)
    x = bp(noise(d, 106), 1200, 5000) * np.sin(np.pi * t / d) ** 2
    return norm(x, 0.4)


def record_stop():
    d = 0.7
    x = sweep(900, 60, d, "saw") * np.linspace(1, 0, int(d * SR))
    return norm(lp(x, 2500), 0.5)


def timelapse():
    d = 2.1
    t = t_arr(d)
    x = np.zeros_like(t)
    for k in range(14):
        add(x, A.sfx_whoosh(0.18, 600, 3000) * 0.3, k * 0.15)
    return norm(x, 0.45)


def murmur_soft():
    return A.sfx_crowd_murmur(3.2) * 0.6


def coin():
    d = 0.5
    t = t_arr(d)
    x = sum(np.sin(2 * np.pi * f * t) * a * np.exp(-t / tau)
            for f, a, tau in [(2637, 1.0, 0.12), (3520, 0.6, 0.08), (5274, 0.3, 0.05)])
    return norm(x, 0.5)


def tiptoe():
    d = 0.08
    return norm(bp(noise(d, 107), 1500, 5000) * exp_env(int(d * SR), 0.01), 0.35)


def grab():
    d = 0.3
    x = bp(noise(d, 108), 1500, 6000) * exp_env(int(d * SR), 0.05)
    for k in range(5):
        add(x, pea_tick() * 0.4, 0.03 + k * 0.035)
    return norm(x, 0.5)


def plop():
    d = 0.35
    x = sweep(300, 1200, 0.08) * exp_env(int(0.08 * SR), 0.03)
    out = np.zeros(int(d * SR))
    add(out, x, 0)
    for k in range(4):
        add(out, sweep(500 + k * 120, 1600, 0.06) * exp_env(int(0.06 * SR), 0.02) * 0.6, 0.05 + k * 0.05)
    return norm(out, 0.5)


def wind_low():
    d = 3.0
    t = t_arr(d)
    return norm(bp(noise(d, 109), 120, 700) * np.sin(np.pi * t / d), 0.3)


def bucket_grab():
    return A.sfx_clank() * 0.7


def snore():
    d = 1.4
    t = t_arr(d)
    f = 80 + 20 * np.sin(np.pi * t / d)
    x = lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.6 + noise(d, 110) * 0.4, 700)
    e = np.sin(np.pi * np.clip(t / (d * 0.7), 0, 1)) ** 2
    return norm(x * e, 0.45)


def creak_glass():
    d = 1.0
    t = t_arr(d)
    x = np.zeros_like(t)
    r = np.random.default_rng(111)
    for k in range(10):
        add(x, hp(noise(0.03, 120 + k), 3000) * exp_env(int(0.03 * SR), 0.006) * r.uniform(0.3, 1), r.uniform(0, 0.95))
    return norm(x, 0.45)


def bang():
    d = 1.4
    t = t_arr(d)
    x = lp(noise(d, 112), 1800) * exp_env(len(t), 0.12)
    x += np.sin(2 * np.pi * (60 * t + 40 * (1 - np.exp(-t * 20)) / 20)) * exp_env(len(t), 0.2)
    # glass shards
    r = np.random.default_rng(113)
    for k in range(40):
        f = r.uniform(3000, 9000)
        seg = np.sin(2 * np.pi * f * t_arr(0.12)) * exp_env(int(0.12 * SR), 0.02)
        add(x, seg * r.uniform(0.05, 0.25), 0.03 + r.uniform(0, 0.7))
    return norm(x, 0.95)


def rumble():
    d = 2.2
    t = t_arr(d)
    x = lp(noise(d, 114), 140, 4) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    return norm(x * np.minimum(1, t * 3) * np.minimum(1, (d - t) * 2), 0.8)


def crackle():
    d = 1.4
    x = np.zeros(int(d * SR))
    r = np.random.default_rng(115)
    for k in range(26):
        st = r.uniform(0, d - 0.05)
        seg = bp(noise(0.04, 130 + k), 400, 4000) * exp_env(int(0.04 * SR), 0.008)
        add(x, seg * r.uniform(0.3, 1), st)
    return norm(x, 0.6)


def swell():
    d = 1.6
    t = t_arr(d)
    x = sweep(90, 260, d) * np.minimum(1, t * 2) * np.minimum(1, (d - t) * 4)
    add(x, crackle() * 0.4, 0.0)
    return norm(x, 0.5)


def wall_burst():
    d = 2.2
    t = t_arr(d)
    x = lp(noise(d, 116), 900) * exp_env(len(t), 0.35)
    x += np.sin(2 * np.pi * (45 * t + 30 * (1 - np.exp(-t * 15)) / 15)) * exp_env(len(t), 0.4) * 0.8
    r = np.random.default_rng(117)
    for k in range(30):
        add(x, A.sfx_thud(r.uniform(60, 140), 0.25) * r.uniform(0.1, 0.35), r.uniform(0.1, 1.6))
    return norm(x, 0.95)


def pea_rain():
    d = 2.5
    x = np.zeros(int(d * SR))
    r = np.random.default_rng(118)
    for k in range(120):
        add(x, pea_tick() * r.uniform(0.15, 0.6), r.uniform(0, d - 0.1))
    t = t_arr(d)
    return norm(x * np.minimum(1, (d - t) * 1.5), 0.55)


for _name, _fn in list(globals().items()):
    if callable(_fn) and _fn.__module__ == __name__ and not _name.startswith("_") and _name not in (
            "prison_amb", "music_bed", "register"):
        A.SFX[_name] = _fn


@functools.lru_cache(maxsize=None)
def prison_amb():
    d = 12.0
    t = t_arr(d)
    x = lp(noise(d, 140), 180) * 0.35 + bp(noise(d, 141), 200, 900) * 0.05
    r = np.random.default_rng(142)
    for k in range(9):
        add(x, A.sfx_drip() * 0.18, r.uniform(0, d - 0.3))
    for k in range(2):
        add(x, keys() * 0.06, r.uniform(1, d - 1))
    return A._xfade_loop(x)


def music_bed(name, dur):
    if name == "night":
        name = "suspense"
    return A.track(name, dur)


def amb_bed(name, dur):
    loop = prison_amb()
    n = int(dur * SR)
    return np.tile(loop, n // len(loop) + 2)[:n]

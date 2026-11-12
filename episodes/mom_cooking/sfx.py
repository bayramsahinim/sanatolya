"""Extra procedural sound effects + the 'stone' music loop for this Short (registered into cinecode.audio)."""
import functools
import zlib

import numpy as np

from cinecode import audio as A
from cinecode.audio import (SR, bp, env_adsr, exp_env, fade, hp, lp, midi_f, noise, norm, sweep, t_arr)


def _seeded(fn):
    """Allow get_sfx('name') plus a seed param via name#seed."""
    return fn


def game(seed=0):
    r = np.random.default_rng(seed)
    out = []
    for k in range(2):
        f = r.choice([660, 784, 880, 988, 1175, 1319])
        d = 0.045
        out.append(np.sign(np.sin(2 * np.pi * f * t_arr(d))) * env_adsr(int(d * SR), 0.002, 0.01, 0.7, 0.01))
    return norm(np.concatenate(out), 0.5)


def plate():
    t = t_arr(0.35)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in ((2350, 14), (3720, 18), (5200, 24)))
    return norm(x, 0.6)


def eyeroll():
    d = 0.5
    t = t_arr(d)
    f = 500 + 500 * np.sin(np.pi * t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
    return norm(x, 0.35)


def raspberry():
    d = 0.55
    t = t_arr(d)
    buzz = np.sign(np.sin(2 * np.pi * (95 + 25 * np.sin(2 * np.pi * 7 * t)) * t))
    x = lp(buzz, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * t)) + bp(noise(d, 3), 300, 2500) * 0.4
    return norm(fade(x * env_adsr(len(t), 0.02, 0.1, 0.8, 0.15), 0.01, 0.05), 0.55)


def rumble(d=2.0):
    t = t_arr(d)
    x = lp(noise(d, 7), 110, 4) * 3 + np.sin(2 * np.pi * 38 * t) * 0.5
    x += bp(noise(d, 8), 200, 900) * 0.25 * (np.random.default_rng(9).random(len(t)) > 0.9995)
    e = np.clip(t / 0.12, 0, 1) * np.exp(-np.clip(t - 1.0, 0, None) * 2.5)
    return norm(x * e, 0.85)


def crack():
    d = 0.6
    t = t_arr(d)
    x = hp(noise(d, 11), 1500) * np.exp(-t * 30)
    for k, st in enumerate((0.0, 0.05, 0.11, 0.2)):
        A.add(x, hp(noise(0.03, 12 + k), 800) * exp_env(int(0.03 * SR), 0.008), st)
    x += lp(noise(d, 16), 200) * np.exp(-t * 6) * 0.8
    return norm(x, 0.8)


def trumpet():
    d = 1.15
    t = t_arr(d)
    f0 = np.interp(t, [0, 0.12, 0.7, d], [260, 520, 470, 330])
    f = f0 * (1 + 0.025 * np.sin(2 * np.pi * 7 * t))
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    x = bp(saw, 500, 3000) * 0.8 + bp(saw, 1100, 1800) * 0.6 + bp(noise(d, 21), 600, 2400) * 0.15
    x = np.tanh(x * 2.5)
    return norm(fade(x * env_adsr(len(t), 0.05, 0.1, 0.85, 0.3), 0.01, 0.08), 0.8)


def eye_open():
    d = 0.18
    return norm(sweep(300, 1400, d) * exp_env(int(d * SR), 0.06), 0.4)


def zip_():
    d = 0.35
    t = t_arr(d)
    x = bp(noise(d, 31), 1500, 7000) * np.sin(np.pi * t / d) ** 2
    x += sweep(900, 2600, d) * 0.15 * np.sin(np.pi * t / d)
    return norm(x, 0.7)


def patter(seed=0):
    d = 0.05
    x = bp(noise(d, 40 + seed % 7), 900, 5000) * exp_env(int(d * SR), 0.01)
    return norm(x, 0.45)


def stomp():
    d = 0.6
    t = t_arr(d)
    x = np.sin(2 * np.pi * (42 + 30 * np.exp(-t * 12)) * t) * np.exp(-t * 6)
    x += lp(noise(d, 50), 300) * np.exp(-t * 14) * 0.6
    return norm(x, 0.9)


def zoom():
    d = 0.45
    t = t_arr(d)
    x = bp(noise(d, 55), 600, 5000) * (t / d) ** 1.5 + sweep(300, 1600, d) * 0.12
    return norm(fade(x, 0.01, 0.04), 0.6)


def tap(seed=0):
    d = 0.08
    t = t_arr(d)
    x = np.sin(2 * np.pi * (1300 + 60 * (seed % 3)) * t) * np.exp(-t * 70) + hp(noise(d, 60 + seed), 2000) * np.exp(-t * 90) * 0.4
    return norm(x, 0.45)


def thunk():
    d = 0.25
    t = t_arr(d)
    x = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 26) + lp(noise(d, 66), 900) * np.exp(-t * 35) * 0.5
    return norm(x, 0.6)


def squawk(seed=0):
    d = 0.16
    t = t_arr(d)
    f = np.interp(t, [0, d], [1100 + 80 * (seed % 3), 700])
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return norm(bp(saw, 800, 3500) * env_adsr(len(t), 0.005, 0.03, 0.7, 0.05), 0.5)


def skid():
    d = 0.45
    t = t_arr(d)
    x = bp(noise(d, 70), 800, 4000) * np.exp(-t * 4) + sweep(1800, 700, d, "saw") * 0.08 * np.exp(-t * 3)
    return norm(fade(x, 0.005, 0.05), 0.6)


def rub(seed=0):
    d = 0.1
    t = t_arr(d)
    x = bp(noise(d, 80 + seed % 5), 1200, 4200) * np.sin(np.pi * t / d)
    x += np.sin(2 * np.pi * (1500 + 200 * (seed % 2)) * t) * 0.15 * np.sin(np.pi * t / d)
    return norm(x, 0.45)


def ignite():
    d = 0.9
    t = t_arr(d)
    x = lp(noise(d, 90), 900) * np.clip(t / 0.06, 0, 1) * np.exp(-t * 3.5)
    x += np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 8)) * t) * np.exp(-t * 7) * 0.6
    return norm(x, 0.85)


def crackle(d=1.6):
    x = np.zeros(int(d * SR))
    r = np.random.default_rng(95)
    for k in range(70):
        A.add(x, hp(noise(0.008, 100 + k), 2500) * r.uniform(0.2, 1.0), r.random() * (d - 0.02))
    x += lp(noise(d, 96), 500) * 0.15
    return norm(fade(x, 0.05, 0.4), 0.5)


def burn():
    d = 0.9
    t = t_arr(d)
    sizzle = hp(noise(d, 110), 3000) * np.exp(-t * 3) * 0.7
    poof = lp(noise(d, 111), 600) * np.exp(-t * 9)
    deflate = sweep(220, 70, 0.6, "saw")
    deflate = lp(deflate, 900) * np.exp(-t_arr(0.6) * 3) * 0.35
    x = sizzle + poof
    A.add(x, deflate, 0.2)
    return norm(fade(x, 0.003, 0.1), 0.8)


def wind():
    d = 1.4
    t = t_arr(d)
    x = bp(noise(d, 120), 300, 1600) * np.sin(np.pi * t / d) ** 2
    return norm(x, 0.55)


def smash():
    d = 0.35
    t = t_arr(d)
    x = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 14) + hp(noise(d, 130), 1500) * np.exp(-t * 25) * 0.6
    return norm(x, 0.8)


def choir():
    d = 1.9
    t = t_arr(d)
    x = np.zeros_like(t)
    for m in (64, 68, 71, 76):
        f = midi_f(m)
        for det in (-0.004, 0.0, 0.005):
            ph = np.cumsum(f * (1 + det) * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t))) / SR
            x += 2 * (ph % 1) - 1
    x = bp(x, 550, 900) * 1.0 + bp(x, 1050, 1350) * 0.6 + bp(x, 2400, 2800) * 0.2
    e = np.clip(t / 0.35, 0, 1) * np.clip((d - t) / 0.6, 0, 1)
    return norm(x * e, 0.6)


def slurp():
    d = 0.4
    t = t_arr(d)
    f = np.interp(t, [0, d], [500, 1400])
    x = bp(noise(d, 140), 400, 2400) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f / 40) / SR * 40))
    return norm(x * np.sin(np.pi * t / d), 0.5)


NEW = {
    "game": game, "plate": plate, "eyeroll": eyeroll, "raspberry": raspberry, "rumble": rumble,
    "crack": crack, "trumpet": trumpet, "eye_open": eye_open, "zip": zip_, "patter": patter, "stomp": stomp,
    "zoom": zoom, "tap": tap, "thunk": thunk, "squawk": squawk, "skid": skid, "rub": rub, "ignite": ignite,
    "crackle": crackle, "burn": burn, "wind": wind, "smash": smash, "choir": choir, "slurp": slurp,
}
SEEDED = {"game", "patter", "tap", "squawk", "rub"}


@functools.lru_cache(maxsize=None)
def get(name, seed=0):
    if name in NEW:
        fn = NEW[name]
        x = fn(seed) if name in SEEDED else fn()
    else:
        x = A.SFX[name]()
    return np.asarray(x, dtype=np.float32)


@functools.lru_cache(maxsize=None)
def music_loop(name):
    if name == "stone":
        rng = np.random.default_rng(zlib.crc32(b"stone-age"))
        return A._quirky(rng, root=50, bpm=118, scale="mixo", bars=8, drum=True, bright=0.75)
    return A._loop(name)
